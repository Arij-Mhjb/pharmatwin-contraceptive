"""Complete profile CRUD; ontology examples remain read-only."""
from rdflib import Literal
from rdflib.namespace import XSD
from backend.config import get_settings
from backend.models.profil import ProfilCreate, ProfilUpdate
from backend.services.security import safe_local_id
from backend.nlp import ontology_map as m
from backend.nlp.templates import iri

P = f"PREFIX ptc: <{m.ONTOLOGY}> PREFIX rdf: <{m.RDF}> PREFIX rdfs: <{m.RDFS}> "

def _iri(local_id):
    return get_settings().namespace + safe_local_id(local_id)

def _dataset():
    s = get_settings()
    return f"FROM {iri(s.ontology_graph)} FROM {iri(s.profiles_graph)} FROM NAMED {iri(s.profiles_graph)}"

def list_profiles(client, age_min=None, age_max=None, fume=None, condition=None, profile_id=None):
    if age_min is not None and age_max is not None and age_min > age_max:
        raise ValueError("Minimum age exceeds maximum age")
    filters = []
    if age_min is not None: filters.append(f"?age >= {int(age_min)}")
    if age_max is not None: filters.append(f"?age <= {int(age_max)}")
    if fume is not None: filters.append(f"?fume = {str(fume).lower()}")
    if profile_id is not None: filters.append(f"?iri = {iri(_iri(profile_id))}")
    condition_filter = "" if not condition else f"?iri {iri(m.P_A_POUR_CONDITION)} ptc:{safe_local_id(condition)} ."
    filtering = "FILTER(" + " && ".join(filters) + ")" if filters else ""
    q = P + f"""SELECT ?iri ?identifiant ?age ?imc ?fume ?systolic ?diastolic ?condition ?conditionLabel ?editable
{_dataset()} WHERE {{
 {{ SELECT DISTINCT ?iri ?identifiant ?age ?imc ?fume WHERE {{
   ?iri {iri(m.D_IDENTIFIANT)} ?identifiant ; {iri(m.D_AGE)} ?age ; {iri(m.D_IMC)} ?imc ; {iri(m.D_FUME)} ?fume .
   {condition_filter} {filtering}
 }} ORDER BY ?identifiant LIMIT 200 }}
 OPTIONAL {{ ?iri {iri(m.D_PRESSION_SYSTOLIQUE)} ?systolic }}
 OPTIONAL {{ ?iri {iri(m.D_PRESSION_DIASTOLIQUE)} ?diastolic }}
 OPTIONAL {{ ?iri {iri(m.P_A_POUR_CONDITION)} ?condition . OPTIONAL {{ ?condition {iri(m.LABEL)} ?conditionLabel }} }}
 BIND(EXISTS {{ GRAPH {iri(get_settings().profiles_graph)} {{ ?iri {iri(m.D_IDENTIFIANT)} ?storedId }} }} AS ?editable)
}} ORDER BY ?identifiant ?condition"""
    grouped = {}
    for row in client.run_select(q):
        if "iri" not in row: continue
        resource = row["iri"]
        if not resource.startswith(get_settings().namespace): raise ValueError("Unexpected profile namespace")
        if resource not in grouped:
            grouped[resource] = dict(id=resource.removeprefix(get_settings().namespace), iri=resource,
                identifiant=row["identifiant"], age=row["age"], imc=row["imc"], fume=row["fume"],
                conditions=[], condition_labels={}, pression_systolique=row.get("systolic"),
                pression_diastolique=row.get("diastolic"), editable=row.get("editable", False))
        if row.get("condition"):
            local = row["condition"].removeprefix(get_settings().namespace)
            if local not in grouped[resource]["conditions"]: grouped[resource]["conditions"].append(local)
            grouped[resource]["condition_labels"][local] = row.get("conditionLabel", local)
    return list(grouped.values())

def ensure_conditions(client, ids):
    if not ids: return
    values = " ".join(iri(_iri(local)) for local in ids)
    rows = client.run_select(f"SELECT ?c FROM {iri(get_settings().ontology_graph)} WHERE {{ VALUES ?c {{ {values} }} ?c {iri(m.TYPE)}/{iri(m.SUBCLASS_OF)}* {iri(m.C_CONDITION)} }}")
    found = {row["c"] for row in rows}
    missing = [local for local in ids if _iri(local) not in found]
    if missing: raise ValueError("Unknown clinical conditions: " + ", ".join(missing))

FIELDS = {"age": (m.D_AGE, XSD.integer), "imc": (m.D_IMC, XSD.decimal), "fume": (m.D_FUME, XSD.boolean),
          "pression_systolique": (m.D_PRESSION_SYSTOLIQUE, XSD.integer), "pression_diastolique": (m.D_PRESSION_DIASTOLIQUE, XSD.integer)}

def create_profile(client, p: ProfilCreate):
    ensure_conditions(client, p.conditions)
    subject = iri(_iri(p.identifiant))
    if client.run_select(f"ASK {_dataset()} {{ {subject} ?p ?o }}"): raise ValueError("Profile already exists")
    triples = [f"{subject} {iri(m.TYPE)} {iri(m.C_PROFIL)}", f"{subject} {iri(m.D_IDENTIFIANT)} {Literal(p.identifiant).n3()}",
               f"{subject} {iri(m.LABEL)} {Literal('Profil simulé ' + p.identifiant, lang='fr').n3()}"]
    for field, (prop, datatype) in FIELDS.items():
        value = getattr(p, field)
        if value is not None: triples.append(f"{subject} {iri(prop)} {Literal(value, datatype=datatype).n3()}")
    triples.extend(f"{subject} {iri(m.P_A_POUR_CONDITION)} {iri(_iri(local))}" for local in p.conditions)
    client.run_update(f"INSERT DATA {{ GRAPH {iri(get_settings().profiles_graph)} {{ " + " . ".join(triples) + " . } }")
    return {"id": p.identifiant, "iri": _iri(p.identifiant)}

def update_profile(client, local_id, p: ProfilUpdate):
    current = list_profiles(client, profile_id=local_id)
    if not current: raise KeyError(local_id)
    if not current[0]["editable"]: raise ValueError("Ontology examples are read-only; create a new simulated profile")
    data = p.model_dump(exclude_unset=True)
    ProfilCreate.model_validate({**current[0], **data})
    if "conditions" in data: ensure_conditions(client, data["conditions"])
    subject = iri(_iri(local_id))
    deletes, inserts, optional = [], [], []
    for number, (field, value) in enumerate(data.items()):
        prop = m.P_A_POUR_CONDITION if field == "conditions" else FIELDS[field][0]
        pattern = f"{subject} {iri(prop)} ?old{number} ."
        deletes.append(pattern); optional.append("OPTIONAL { " + pattern + " }")
        if field == "conditions": inserts.extend(f"{subject} {iri(prop)} {iri(_iri(local))} ." for local in value)
        elif value is not None: inserts.append(f"{subject} {iri(prop)} {Literal(value, datatype=FIELDS[field][1]).n3()} .")
    if data: client.run_update(f"WITH {iri(get_settings().profiles_graph)} DELETE {{ {' '.join(deletes)} }} INSERT {{ {' '.join(inserts)} }} WHERE {{ {' '.join(optional)} }}")
    return {"id": local_id, "updated": True}

def delete_profile(client, local_id):
    subject = iri(_iri(local_id))
    profile_graph = get_settings().profiles_graph
    if not client.run_select(
        f"ASK {{ {subject} {iri(m.D_IDENTIFIANT)} ?id }}",
        dataset_params=[("default-graph-uri", profile_graph)],
    ):
        raise ValueError("Profile not found in editable user graph")
    updates = [f"WITH {iri(graph)} DELETE {{ {subject} ?p ?o }} WHERE {{ {subject} ?p ?o }}" for graph in (get_settings().profiles_graph, get_settings().inferred_graph)]
    client.run_update("; ".join(updates))
    return {"id": local_id, "deleted": True}
