import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.routes import health, profils, search, ask, contraceptifs
from backend.services import auth_store

class FakeSparql:
    def __init__(self, rows=None): self.rows=rows or []; self.queries=[]; self.updates=[]
    def run_select(self,q,**kwargs): self.queries.append(q); return self.rows
    def run_update(self,q): self.updates.append(q)

@pytest.fixture
def fake(): return FakeSparql([{"ok":1}])
@pytest.fixture
def client(fake, monkeypatch, tmp_path):
    monkeypatch.setattr(__import__('backend.config', fromlist=['get_settings']).get_settings(), "patient_store_path", tmp_path / "test.sqlite3")
    for router in (health,profiles if False else profils,search,ask,contraceptifs):
        app.dependency_overrides[router.client]=lambda:fake
    with TestClient(app) as api:
        auth_store.create_user("admin@test.local", "TestAdmin2026!", "Test Admin", role="admin", onboarding=True)
        assert api.post("/api/auth/signin", json={"email": "admin@test.local", "password": "TestAdmin2026!"}).status_code == 200
        api.headers.update({"X-CSRF-Token": api.cookies["pharmatwin_csrf"]})
        yield api
    app.dependency_overrides.clear()
