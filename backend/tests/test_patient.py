"""Patient journey and preference-scoring invariants against actual ontology."""
from pathlib import Path
from rdflib import URIRef
import pytest
from backend.models.patient import PatientInput
from backend.services.assessment_service import AssessmentService
from backend.config import get_settings
from backend.nlp import ontology_map as m
from backend.tests.test_integration import semantic_api


def data(**changes):
    body = {"display_name": "Nour — scénario fictif", "profile": {"identifiant": "PATIENT-TEST", "age": 28, "imc": 24, "fume": False, "conditions": []},
        "preferences": {"forms": ["pilule combinée"]}, "current_method": "PiluleCombinee_EE_DRSP", "history_complete": True}
    return {**body, **changes}


def test_contraindication_cannot_be_overruled_by_preferences():
    body = data(); body["profile"]["conditions"] = ["MigraineAvecAura"]
    report = AssessmentService().assess(PatientInput(**body))
    combined = [c for c in report["candidates"] if c["form"] == "pilule combinée"]
    assert len(combined) == 2
    assert all(c["status"] == "blocked" and c["preference_score"] is None for c in combined)
    assert all(c["flags"] and c["flags"][0]["sources"] for c in combined)
    assert report["candidates"][0]["status"] == "undetermined"
    assert all(c["status"] != "safe" for c in report["candidates"])


def test_score_is_explainable_and_unknowns_are_not_safety():
    report = AssessmentService().assess(PatientInput(**data(preferences={"forms": ["pilule combinée"], "hormones": "avoid"})))
    combined = next(c for c in report["candidates"] if c["form"] == "pilule combinée")
    assert combined["preference_score"] == 50
    assert combined["coverage"] == 100 and combined["assessed_criteria"] == 2
    assert combined["status"] == "undetermined"
    assert report["labels"]["MigraineAvecAura"] == "Migraine avec aura"
    assert "sécurité" in report["score_explanation"]
    none = AssessmentService().assess(PatientInput(**data(preferences={})))
    assert all(c["preference_score"] is None for c in none["candidates"])


def test_missing_benefit_stays_unknown():
    service = AssessmentService()
    goal = service.catalog()["benefits"][0]["id"]
    report = service.assess(PatientInput(**data(preferences={"benefits": [goal]})))
    assert any(c["criteria"][0]["matched"] is None and c["coverage"] == 0 and c["preference_score"] is None for c in report["candidates"])


def test_interaction_and_past_experience():
    service = AssessmentService()
    report = service.assess(PatientInput(**data(medications=["Rifampicine"])))
    dsg = next(c for c in report["candidates"] if c["id"] == "PiluleProgestative_DSG")
    assert dsg["status"] == "review" and dsg["preference_score"] is None
    self_drug = service.assess(PatientInput(**data(medications=["Desogestrel"])))
    assert next(c for c in self_drug["candidates"] if c["id"] == "PiluleProgestative_DSG")["status"] != "review"
    past = service.assess(PatientInput(**data(preferences={}, history=[{"method_id": "PiluleProgestative_DSG", "experience": "negative"}])))
    assert next(c for c in past["candidates"] if c["id"] == "PiluleProgestative_DSG")["preference_score"] == 0


def test_unrecognized_input_is_not_silently_scored():
    with pytest.raises(ValueError): AssessmentService().assess(PatientInput(**data(current_method="not-real")))
    report = AssessmentService().assess(PatientInput(**data(other_conditions="Antécédent fictif hors vocabulaire")))
    assert any("hors du vocabulaire" in gap for gap in report["gaps"])


def test_full_patient_journey_persistence_and_immutable_reports(semantic_api, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "patient_store_path", tmp_path / "patient.sqlite3")
    api, dataset, _ = semantic_api
    catalog = api.get("/api/patient/catalog").json()
    assert len(catalog["methods"]) == 7
    created = api.post("/api/patient/profiles", json=data())
    assert created.status_code == 201, created.text
    patient_id = created.json()["id"]
    assert api.get("/api/patient/profiles").json()[0]["id"] == patient_id
    first = api.post(f"/api/patient/profiles/{patient_id}/assessments").json()
    assert len(first["candidates"]) == 7 and first["snapshot"]["symptoms"] == []
    observation = {"name": "Troubles du sommeil", "date": "2026-11-04", "severity": "modere", "notes": "Observation fictive"}
    response = api.post(f"/api/patient/profiles/{patient_id}/symptoms", json={"observation": observation})
    assert response.status_code == 200, response.text
    subject = URIRef(get_settings().namespace + patient_id)
    user_graph = dataset.graph(URIRef(get_settings().profiles_graph))
    assert (subject, m.P_UTILISE_CONTRACEPTIF, m.ONTOLOGY["PiluleCombinee_EE_DRSP"]) in user_graph
    assert list(user_graph.objects(subject, m.P_A_OBSERVATION))
    second = api.post(f"/api/patient/profiles/{patient_id}/assessments").json()
    assert second["snapshot"]["symptoms"] == [observation]
    reports = api.get(f"/api/patient/profiles/{patient_id}/reports").json()
    assert len(reports) == 2
    assert next(r for r in reports if r["id"] == first["id"])["snapshot"]["symptoms"] == []
    # Sleep symptoms are recorded without becoming a diagnosis/contraindication.
    assert [(c["id"], c["status"]) for c in first["candidates"]] == [(c["id"], c["status"]) for c in second["candidates"]]
    updated = data(); updated["profile"]["conditions"] = ["MigraineAvecAura"]
    response = api.put(f"/api/patient/profiles/{patient_id}", json=updated)
    assert response.status_code == 200, response.text
    third = api.post(f"/api/patient/profiles/{patient_id}/assessments").json()
    assert any(c["status"] == "blocked" for c in third["candidates"])
    assert api.get(f"/api/patient/profiles/{patient_id}").json()["profile"]["conditions"] == ["MigraineAvecAura"]
    assert third["ontology_sha256"] == first["ontology_sha256"]


def test_no_benefits_from_preference_score_can_hide_clinical_flags():
    report = AssessmentService().assess(PatientInput(**data(profile={"identifiant": "TEST-CANCER", "age": 35, "imc": 24, "conditions": ["CancerSeinActuel"]})))
    assert all(c["status"] == "blocked" and c["preference_score"] is None for c in report["candidates"] if c["hormonal"] is True)
