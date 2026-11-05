from fastapi.testclient import TestClient
from backend.app import app
from backend.config import get_settings
from backend.services import auth_store, patient_store

def signup(api, email="user@example.test"):
    response = api.post("/api/auth/signup", json={"email": email, "password": "StrongPass2026!", "display_name": "Compte test"})
    assert response.status_code == 201, response.text
    api.headers.update({"X-CSRF-Token": api.cookies["pharmatwin_csrf"]})
    return response.json()["user"]

def test_signup_session_onboarding_and_signout(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "patient_store_path", tmp_path / "auth.sqlite3")
    with TestClient(app) as api:
        user = signup(api)
        assert user["role"] == "user" and not user["onboarding_complete"]
        assert api.get("/api/auth/session").status_code == 200
        onboarded = api.put("/api/auth/onboarding", json={"display_name": "Étudiante test", "academic_use_accepted": True})
        assert onboarded.status_code == 200 and onboarded.json()["user"]["onboarding_complete"]
        assert api.post("/api/auth/signout").status_code == 204
        assert api.get("/api/auth/session").status_code == 401

def test_avatar_upload_and_admin_overview(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "patient_store_path", tmp_path / "avatar.sqlite3")
    with TestClient(app) as api:
        user = signup(api, "avatar@example.test")
        image = "data:image/png;base64,iVBORw0KGgo="
        updated = api.put("/api/auth/avatar", json={"data_url": image})
        assert updated.status_code == 200 and updated.json()["user"]["avatar_url"] == image
        assert api.put("/api/auth/avatar", json={"data_url": "data:text/plain;base64,QQ=="}).status_code == 422
        auth_store.update_user(user["id"], user["id"], role="admin")
        overview = api.get("/api/admin/overview")
        assert overview.status_code == 200
        assert overview.json()["counts"]["users"] >= 1
        assert any(item["action"] == "avatar.updated" for item in overview.json()["audit"])

def test_csrf_password_policy_and_rbac(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "patient_store_path", tmp_path / "rbac.sqlite3")
    with TestClient(app) as api:
        user = signup(api)
        assert api.get("/api/admin/users").status_code == 403
        api.headers.pop("X-CSRF-Token")
        assert api.put("/api/auth/onboarding", json={"display_name": "X test", "academic_use_accepted": True}).status_code == 403
        weak = api.post("/api/auth/signup", json={"email": "weak@example.test", "password": "abcdefghij", "display_name": "Weak Test"})
        assert weak.status_code == 422

def test_patient_ownership_isolation(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "patient_store_path", tmp_path / "owners.sqlite3")
    with TestClient(app) as first:
        user = signup(first, "owner@example.test")
        patient_store.save_patient("PRIVATE", {"display_name": "Privé"})
        patient_store.claim_patient(user["id"], "PRIVATE")
        assert first.get("/api/patient/profiles/PRIVATE").status_code == 200
        with TestClient(app) as second:
            signup(second, "other@example.test")
            assert second.get("/api/patient/profiles/PRIVATE").status_code == 404
