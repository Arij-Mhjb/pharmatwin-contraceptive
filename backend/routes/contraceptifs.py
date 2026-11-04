from fastapi import APIRouter,Depends,HTTPException
from backend.sparql_client import SparqlClient
from backend.config import get_settings
from backend.services.security import safe_local_id
router=APIRouter(prefix="/contraceptifs",tags=["contraceptives"])
def client(): return SparqlClient()
PREFIX="PREFIX ptc:<https://pharmatwin.ai/contraceptive#> PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> "
@router.get("")
def all(c=Depends(client)):
    s=get_settings(); return c.run_select(PREFIX+f"SELECT DISTINCT ?iri ?label FROM <{s.ontology_graph}> WHERE{{?iri rdf:type/rdfs:subClassOf* ptc:Contraceptif. OPTIONAL{{?iri rdfs:label ?label}}}} LIMIT 100")
@router.get("/{id}")
def one(id:str,c=Depends(client)):
    try: id=safe_local_id(id)
    except ValueError as e: raise HTTPException(400,str(e))
    s=get_settings(); rows=c.run_select(PREFIX+f"SELECT ?predicate ?object ?label FROM <{s.ontology_graph}> WHERE{{ptc:{id} ?predicate ?object. OPTIONAL{{?object rdfs:label ?label}}}} LIMIT 200")
    if not rows: raise HTTPException(404,"Contraceptive not found")
    return {"id":id,"statements":rows}
