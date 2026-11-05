from fastapi import APIRouter, Depends, HTTPException, status
from backend.sparql_client import SparqlClient
from backend.models.profil import ProfilCreate, ProfilUpdate
from backend import crud
from backend.services.reasoning_service import refresh_profile_inference
from backend.config import get_settings
from backend.routes.auth import admin_session
router = APIRouter(prefix="/profils", tags=["profiles"])
def client(): return SparqlClient()
@router.get("")
def get_profiles(age_min:int|None=None, age_max:int|None=None, fume:bool|None=None, condition:str|None=None, c=Depends(client)):
    try: return crud.list_profiles(c, age_min, age_max, fume, condition)
    except ValueError as e: raise HTTPException(400, str(e))
@router.post("", status_code=status.HTTP_201_CREATED)
def create(p:ProfilCreate, c=Depends(client), _=Depends(admin_session)):
    try:
        out=crud.create_profile(c,p); refresh_profile_inference(c,out["iri"]); return out
    except ValueError as e: raise HTTPException(409 if "exists" in str(e) else 422, str(e))
@router.put("/{id}")
def update(id:str, p:ProfilUpdate, c=Depends(client), _=Depends(admin_session)):
    try:
        out=crud.update_profile(c,id,p); refresh_profile_inference(c,get_settings().namespace+id); return out
    except KeyError: raise HTTPException(404,"Profile not found")
    except ValueError as e: raise HTTPException(422,str(e))
@router.delete("/{id}")
def delete(id:str,c=Depends(client),_=Depends(admin_session)):
    try: return crud.delete_profile(c,id)
    except ValueError as e: raise HTTPException(400,str(e))
