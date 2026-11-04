"""Exercise actual FastAPI routes and SPARQL against isolated named RDF graphs.

Only the external Fuseki HTTP transport is replaced. The translator, response
models, graph queries, updates and profile inference are the production code.
"""
import importlib.util
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest
from fastapi.testclient import TestClient
from rdflib import Dataset, Graph, URIRef

from backend.app import app
from backend.config import get_settings
from backend.routes import ask, profils, search, contraceptifs, health, patient
from backend.sparql_client import SparqlClient


@pytest.fixture
def semantic_api(monkeypatch):
    import rdflib.plugins.sparql as sparql
    monkeypatch.setattr(sparql, "SPARQL_LOAD_GRAPHS", False)
    settings = get_settings()
    dataset = Dataset()
    dataset.graph(URIRef(settings.ontology_graph)).parse(settings.ontology_path, format="turtle")
    requests = []

    def transport(request):
        requests.append(request)
        params = parse_qs(request.content.decode())
        if "update" in params:
            dataset.update(params["update"][0])
            return httpx.Response(204)
        query = params["query"][0]
        graphs = request.url.params.get_list("default-graph-uri")
        if graphs:
            default = Graph()
            for name in graphs:
                for triple in dataset.graph(URIRef(name)):
                    default.add(triple)
            result = default.query(query)
        else:
            result = dataset.query(query)
        return httpx.Response(200, content=result.serialize(format="json"), headers={"Content-Type": "application/sparql-results+json"})

    real_client = SparqlClient(settings, transport=httpx.MockTransport(transport))
    prior = app.dependency_overrides.copy()
    for route in (ask, profils, search, contraceptifs, health, patient):
        app.dependency_overrides[route.client] = lambda: real_client
    monkeypatch.setenv("PHARMATWIN_LEXICON", str(Path(__file__).resolve().parents[1] / "nlp" / "lexicon.json"))
    try:
        with TestClient(app) as api:
            yield api, dataset, requests
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(prior)


def payload(**changes):
    return {"identifiant": "TEST-INTEGRATION", "age": 25, "imc": 22.5, "fume": False,
            "conditions": ["Endometriose", "SOPK"], "pression_systolique": 120, "pression_diastolique": 80, **changes}


def test_profile_round_trip_preserves_conditions_and_pressure(semantic_api):
    api, dataset, _ = semantic_api
    before = len(dataset.graph(URIRef(get_settings().ontology_graph)))
    created = api.post("/api/profils", json=payload())
    assert created.status_code == 201, created.text
    resource_id = created.json()["id"]
    rows = api.get("/api/profils").json()
    stored = next(row for row in rows if row["id"] == resource_id)
    assert stored["editable"] is True
    assert set(stored["conditions"]) == {"Endometriose", "SOPK"}
    assert stored["pression_systolique"] == 120
    assert api.put(f"/api/profils/{resource_id}", json={"age": 26}).status_code == 200
    changed = next(row for row in api.get("/api/profils").json() if row["id"] == resource_id)
    assert changed["age"] == 26
    assert changed["conditions"] == stored["conditions"]
    assert changed["pression_diastolique"] == 80
    assert api.put(f"/api/profils/{resource_id}", json={"pression_diastolique": 130}).status_code == 422
    assert api.put(f"/api/profils/{resource_id}", json={"pression_systolique": None}).status_code == 200
    cleared = next(row for row in api.get("/api/profils").json() if row["id"] == resource_id)
    assert cleared["pression_systolique"] is None
    assert api.delete(f"/api/profils/{resource_id}").status_code == 200
    assert not any(row["id"] == resource_id for row in api.get("/api/profils").json())
    assert not list(dataset.graph(URIRef(get_settings().inferred_graph)))
    assert len(dataset.graph(URIRef(get_settings().ontology_graph))) == before


def test_profile_filters_and_readonly_examples(semantic_api):
    api, _, _ = semantic_api
    assert api.post("/api/profils", json=payload()).status_code == 201
    assert api.get("/api/profils", params={"age_min": 90}).json() == []
    assert api.get("/api/profils", params={"age_min": 40, "age_max": 20}).status_code == 400
    seed = next(row for row in api.get("/api/profils").json() if not row["editable"])
    assert seed["id"] != seed["identifiant"]  # Resource IDs must not be confused with display IDs.
    assert api.put(f"/api/profils/{seed['id']}", json={"age": 30}).status_code == 422
    assert api.delete(f"/api/profils/{seed['id']}").status_code == 400
    assert api.post("/api/profils", json=payload(identifiant="OTHER", conditions=["not_a_condition"])).status_code == 422
    assert api.put("/api/profils/TEST-INTEGRATION", json={"conditions": ["bad id"]}).status_code == 422


def test_conditions_and_search_contract(semantic_api):
    api, _, _ = semantic_api
    conditions = api.get("/api/ontology/conditions").json()
    assert any(row["id"] == "Endometriose" and row["label"] == "Endométriose" for row in conditions)
    assert not any(row["id"] == "Rifampicine" for row in conditions)
    result = api.get("/api/search", params={"q": "pilule"})
    assert result.status_code == 200
    assert isinstance(result.json()["results"], list) and result.json()["results"]


def test_frontend_origin_preflight(semantic_api):
    api, _, _ = semantic_api
    response = api.options("/api/profils/TEST", headers={"Origin": "http://127.0.0.1:3100", "Access-Control-Request-Method": "PUT", "Access-Control-Request-Headers": "content-type"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3100"


@pytest.mark.skipif(importlib.util.find_spec("fr_core_news_md") is None, reason="Install the French NLP model to run actual-translator integration")
def test_actual_translator_uses_all_named_graphs(semantic_api):
    api, _, requests = semantic_api
    created = api.post("/api/profils", json=payload())
    assert created.status_code == 201
    for question in ["Quels profils ont une endométriose ?", "Quelles molécules contient la pilule combinée ?"]:
        result = api.post("/api/ask", json={"question": question})
        assert result.status_code == 200, result.text
        assert isinstance(result.json()["entities"], list)
        assert result.json()["results"]
        if "profils" in question:
            assert any(row["result"].endswith("#TEST-INTEGRATION") for row in result.json()["results"])
    expected = {get_settings().ontology_graph, get_settings().profiles_graph, get_settings().inferred_graph}
    assert any(set(request.url.params.get_list("default-graph-uri")) == expected for request in requests)
