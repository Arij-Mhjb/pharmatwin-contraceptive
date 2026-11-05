from fastapi import APIRouter, Depends, HTTPException
from backend.models.patient import PatientInput, SymptomInput
from backend.models.profil import ProfilUpdate
from backend.sparql_client import SparqlClient
from backend import crud
from backend.services.reasoning_service import refresh_profile_inference
from backend.services.assessment_service import AssessmentService
from backend.services import patient_store as store
from rdflib import Literal
from backend.config import get_settings
from backend.nlp import ontology_map as m
from backend.nlp.templates import iri
from backend.routes.auth import current_user, current_session
import json

router = APIRouter(prefix="/patient", tags=["patient workspace — local demo"])
def client(): return SparqlClient()
def assessment(): return AssessmentService()

def authorize(user, patient_id):
    if user["role"] != "admin" and not store.owns_patient(user["id"], patient_id):
        raise HTTPException(404, "Profil personnel introuvable")

def load(patient_id, user):
    authorize(user, patient_id)
    try: return store.patient(patient_id)
    except KeyError: raise HTTPException(404, "Profil personnel introuvable")

def sync_observations(c, data):
    """Reuse existing current-method/Observation vocabulary in the user graph.

    Typed dates, severity and notes remain in the validated application snapshot;
    the generic observation value preserves them without inventing clinical rules.
    """
    subject = iri(crud._iri(data.profile.identifiant))
    graph = iri(get_settings().profiles_graph)
    c.run_update(f"WITH {graph} DELETE {{ {subject} {iri(m.P_UTILISE_CONTRACEPTIF)} ?old }} WHERE {{ {subject} {iri(m.P_UTILISE_CONTRACEPTIF)} ?old }}")
    c.run_update(f"WITH {graph} DELETE {{ {subject} {iri(m.P_A_OBSERVATION)} ?ob . ?ob ?p ?v }} WHERE {{ {subject} {iri(m.P_A_OBSERVATION)} ?ob . ?ob ?p ?v }}")
    triples = []
    if data.current_method: triples.append(f"{subject} {iri(m.P_UTILISE_CONTRACEPTIF)} {iri(m.ONTOLOGY[data.current_method])} .")
    for index, symptom in enumerate(data.symptoms):
        observation = iri(crud._iri(data.profile.identifiant + '_OBS_' + str(index)))
        triples.extend([f"{subject} {iri(m.P_A_OBSERVATION)} {observation} .", f"{observation} {iri(m.TYPE)} {iri(m.C_OBSERVATION)} .",
            f"{observation} {iri(m.D_TYPE_OBSERVATION)} {Literal(symptom.name).n3()} .",
            f"{observation} {iri(m.D_VALEUR_OBSERVATION)} {Literal(json.dumps(symptom.model_dump(mode='json'), ensure_ascii=False)).n3()} ."])
    if triples: c.run_update(f"INSERT DATA {{ GRAPH {graph} {{ {' '.join(triples)} }} }}")

@router.get("/catalog")
def catalog(service=Depends(assessment), _=Depends(current_user)): return service.catalog()

@router.get("/profiles")
def patients(user=Depends(current_user)): return store.patients(user["id"], include_unowned=user["role"] == "admin")

@router.get("/profiles/{patient_id}")
def patient(patient_id: str, user=Depends(current_user)): return load(patient_id, user)

@router.post("/profiles", status_code=201)
def create(data: PatientInput, c=Depends(client), service=Depends(assessment), user=Depends(current_session)):
    try:
        service.validate(data)
        result = crud.create_profile(c, data.profile)
        refresh_profile_inference(c, result["iri"])
        sync_observations(c, data)
        store.save_patient(result["id"], data.model_dump(mode="json"))
        store.claim_patient(user["id"], result["id"])
        return {"id": result["id"], "data": data.model_dump(mode="json")}
    except ValueError as e: raise HTTPException(422, str(e))

@router.put("/profiles/{patient_id}")
def update(patient_id: str, data: PatientInput, c=Depends(client), service=Depends(assessment), user=Depends(current_session)):
    load(patient_id, user)
    if data.profile.identifiant != patient_id: raise HTTPException(422, "L’identifiant ne peut pas être changé")
    try:
        service.validate(data)
        crud.update_profile(c, patient_id, ProfilUpdate(**data.profile.model_dump(exclude={"identifiant"})))
        refresh_profile_inference(c, crud._iri(patient_id))
        sync_observations(c, data)
        store.save_patient(patient_id, data.model_dump(mode="json"))
        return {"id": patient_id, "data": data.model_dump(mode="json")}
    except (ValueError, KeyError) as e: raise HTTPException(422, str(e))

@router.post("/profiles/{patient_id}/symptoms")
def symptom(patient_id: str, data: SymptomInput, c=Depends(client), user=Depends(current_session)):
    current = PatientInput.model_validate(load(patient_id, user))
    if len(current.symptoms) >= 100: raise HTTPException(422, "Limite de 100 observations atteinte")
    current.symptoms.append(data.observation)
    sync_observations(c, current)
    store.save_patient(patient_id, current.model_dump(mode="json"))
    return current.model_dump(mode="json")

@router.post("/profiles/{patient_id}/assessments", status_code=201)
def assess(patient_id: str, service=Depends(assessment), user=Depends(current_session)):
    data = PatientInput.model_validate(load(patient_id, user))
    return store.save_report(patient_id, service.assess(data))

@router.get("/profiles/{patient_id}/reports")
def reports(patient_id: str, user=Depends(current_user)):
    load(patient_id, user)
    return store.reports(patient_id)
