from fastapi import APIRouter, Depends
from backend.sparql_client import SparqlClient
router = APIRouter(tags=["health"])
def client(): return SparqlClient()
@router.get("/health")
def health(c: SparqlClient = Depends(client)):
    c.run_select("SELECT (1 AS ?ok) WHERE {}")
    return {"status": "healthy", "fuseki": "connected"}
