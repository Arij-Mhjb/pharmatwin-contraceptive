from fastapi import APIRouter,Depends,HTTPException
from backend.models.profil import AskRequest
from backend.models.schemas import AskResponse
from backend.sparql_client import SparqlClient
from backend.services.nlp_adapter import translate, query_dataset_params
router=APIRouter(tags=["natural language"])
def client(): return SparqlClient()
@router.post("/ask",response_model=AskResponse)
def ask(payload:AskRequest,c=Depends(client)):
    try: result=translate(payload.question)
    except ValueError as e: raise HTTPException(400,str(e))
    if result["intent"]=="unsupported" or not result["sparql"]: return {**result,"results":[]}
    return {**result,"results":c.run_select(result["sparql"], dataset_params=query_dataset_params())}
