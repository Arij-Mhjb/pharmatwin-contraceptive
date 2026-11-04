from fastapi import APIRouter,Depends,HTTPException,Query
from backend.sparql_client import SparqlClient
from backend.config import get_settings
from backend.services.security import sparql_string
router=APIRouter(prefix="/search",tags=["search"])
def client(): return SparqlClient()
@router.get("")
def keyword(q:str=Query(min_length=2,max_length=100),c=Depends(client)):
    s=get_settings();needle=sparql_string(q)
    query=f'''PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?iri ?label ?type FROM <{s.ontology_graph}> WHERE {{?iri rdfs:label ?label. OPTIONAL{{?iri a ?type}} FILTER(CONTAINS(LCASE(STR(?label)),LCASE({needle})))}} LIMIT 50'''
    return {"query":q,"results":c.run_select(query)}
@router.get("/semantic")
def semantic(q:str=Query(min_length=2,max_length=100)):
    try:
        from backend.ai.ontology_index import OntologyIndex
        return {"query":q,"results":OntologyIndex().search(q,10)}
    except Exception as e: raise HTTPException(503,"Local AI model unavailable; run the model download command") from e
