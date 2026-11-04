import pytest
from backend.services.security import validate_select,safe_local_id,sparql_string
@pytest.mark.parametrize("q",["DELETE WHERE {?s ?p ?o}","SELECT * WHERE { SERVICE <http://evil> {?s ?p ?o}}","LOAD <x>"])
def test_rejects_unsafe(q):
    with pytest.raises(ValueError):validate_select(q)
def test_accepts_select():assert validate_select("SELECT * WHERE {?s ?p ?o} LIMIT 1")
def test_id_injection():
    with pytest.raises(ValueError):safe_local_id("x> . ?s ?p ?o")
def test_literal_escape():assert '\\"' in sparql_string('a"b')
