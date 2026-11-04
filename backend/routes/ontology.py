from fastapi import APIRouter, HTTPException
from functools import lru_cache
from backend.services.ontology_service import OntologyService
from backend.services.security import safe_local_id
router=APIRouter(prefix="/ontology",tags=["ontology"])
@lru_cache
def service(): return OntologyService()
@router.get("/classes")
def classes(): return service().classes()
@router.get("/properties")
def properties(): return service().properties()
@router.get("/individuals")
def individuals(): return service().individuals()
@router.get("/stats")
def stats(): return service().stats()
@router.get("/conditions")
def conditions(): return service().conditions()
@router.get("/class/{id}")
def resource(id:str):
    try: r=service().resource(safe_local_id(id))
    except ValueError as e: raise HTTPException(400,str(e))
    if not r: raise HTTPException(404,"Ontology resource not found")
    return r
