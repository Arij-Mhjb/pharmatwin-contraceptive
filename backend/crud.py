from backend.config import get_settings
from backend.models.profil import ProfilCreate, ProfilUpdate
from backend.services.security import safe_local_id, sparql_string
P="PREFIX ptc: <https://pharmatwin.ai/contraceptive#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> "
def _iri(id): return get_settings().namespace+safe_local_id(id)
def list_profiles(client, age_min=None, age_max=None, fume=None, condition=None):
 s=get_settings(); filters=[]
 if age_min is not None: filters.append(f"?age >= {int(age_min)}")
 if age_max is not None: filters.append(f"?age <= {int(age_max)}")
 if fume is not None: filters.append(f"?fume = {'true' if fume else 'false'}")
 cond="" if not condition else f"?iri ptc:aCondition ptc:{safe_local_id(condition)}."
 fil="FILTER("+" && ".join(filters)+")" if filters else ""
 q=P+f"SELECT DISTINCT ?iri ?identifiant ?age ?imc ?fume FROM <{s.ontology_graph}> FROM <{s.profiles_graph}> WHERE {{?iri ptc:identifiantProfil ?identifiant;ptc:age ?age;ptc:imc ?imc;ptc:fume ?fume. {cond}{fil}}} ORDER BY ?identifiant LIMIT 200"
 return client.run_select(q)
def ensure_conditions(client, ids):
 if not ids:return
 s=get_settings(); values=" ".join(f"ptc:{safe_local_id(x)}" for x in ids)
 rows=client.run_select(P+f"SELECT ?c FROM <{s.ontology_graph}> WHERE {{ VALUES ?c {{ {values} }} ?c rdf:type/rdfs:subClassOf* ptc:ConditionClinique }}")
 found={x["c"] for x in rows}; missing=[x for x in ids if _iri(x) not in found]
 if missing: raise ValueError("Unknown clinical conditions: "+", ".join(missing))
def create_profile(client,p:ProfilCreate):
 ensure_conditions(client,p.conditions); s=get_settings(); iri=_iri(p.identifiant)
 if client.run_select(P+f"ASK FROM <{s.ontology_graph}> FROM <{s.profiles_graph}> {{<{iri}> ?p ?o}}"): raise ValueError("Profile already exists")
 triples=[f"<{iri}> rdf:type ptc:ProfilPatiente",f"<{iri}> ptc:identifiantProfil {sparql_string(p.identifiant)}",f"<{iri}> ptc:age \"{p.age}\"^^xsd:integer",f"<{iri}> ptc:imc \"{p.imc}\"^^xsd:decimal",f"<{iri}> ptc:fume \"{str(p.fume).lower()}\"^^xsd:boolean",f"<{iri}> rdfs:label {sparql_string('Profil simulé '+p.identifiant)}@fr"]
 if p.pression_systolique: triples.append(f"<{iri}> ptc:pressionSystolique \"{p.pression_systolique}\"^^xsd:integer")
 if p.pression_diastolique: triples.append(f"<{iri}> ptc:pressionDiastolique \"{p.pression_diastolique}\"^^xsd:integer")
 triples += [f"<{iri}> ptc:aCondition ptc:{safe_local_id(c)}" for c in p.conditions]
 client.run_update(P+f"INSERT DATA {{ GRAPH <{s.profiles_graph}> {{ {' . '.join(triples)} . }} }}"); return {"id":p.identifiant,"iri":iri}
def update_profile(client,id,p:ProfilUpdate):
 s=get_settings(); iri=_iri(id); existing=client.run_select(P+f"ASK FROM <{s.profiles_graph}> {{<{iri}> ptc:identifiantProfil ?x}}")
 if not existing: raise KeyError(id)
 data=p.model_dump(exclude_unset=True); conditions=data.pop("conditions",None)
 if conditions is not None:
  ensure_conditions(client,conditions)
  client.run_update(P+f"WITH <{s.profiles_graph}> DELETE {{<{iri}> ptc:aCondition ?o}} WHERE {{<{iri}> ptc:aCondition ?o}}")
  if conditions:
   client.run_update(P+f"INSERT DATA {{GRAPH <{s.profiles_graph}>{{"+" . ".join(f"<{iri}> ptc:aCondition ptc:{safe_local_id(c)}" for c in conditions)+"}}}")
 mapping={"age":("age","integer"),"imc":("imc","decimal"),"fume":("fume","boolean"),"pression_systolique":("pressionSystolique","integer"),"pression_diastolique":("pressionDiastolique","integer")}
 for key,val in data.items():
  prop,dt=mapping[key]; lit=str(val).lower() if isinstance(val,bool) else str(val); client.run_update(P+f"WITH <{s.profiles_graph}> DELETE {{<{iri}> ptc:{prop} ?o}} INSERT {{<{iri}> ptc:{prop} \"{lit}\"^^xsd:{dt}}} WHERE {{OPTIONAL{{<{iri}> ptc:{prop} ?o}}}}")
 return {"id":id,"updated":True}
def delete_profile(client,id):
 s=get_settings(); iri=_iri(id); client.run_update(P+f"WITH <{s.profiles_graph}> DELETE {{<{iri}> ?p ?o}} WHERE {{<{iri}> ?p ?o}}; WITH <{s.inferred_graph}> DELETE {{<{iri}> ?p ?o}} WHERE {{<{iri}> ?p ?o}}"); return {"id":id,"deleted":True}
