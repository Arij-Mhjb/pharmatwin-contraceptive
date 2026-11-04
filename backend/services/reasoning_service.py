from backend.config import get_settings
from backend.services.sparql_templates import P

RULES = {
 "ProfilSOPK": "?p ptc:aCondition ptc:SOPK",
 "ProfilEndometriose": "?p ptc:aCondition ptc:Endometriose",
 "ProfilAlerteOestrogene": "?p ptc:aCondition ?c. ?c rdf:type/rdfs:subClassOf* ptc:ConditionContreIndiqueCHC",
}
def refresh_profile_inference(client, profile_iri: str):
    s=get_settings(); allowed=s.namespace
    if not profile_iri.startswith(allowed): raise ValueError("Profile IRI outside ontology namespace")
    client.run_update(P+f"WITH <{s.inferred_graph}> DELETE {{ <{profile_iri}> rdf:type ?t }} WHERE {{ <{profile_iri}> rdf:type ?t FILTER(?t IN (ptc:ProfilSOPK,ptc:ProfilEndometriose,ptc:ProfilAlerteOestrogene)) }}")
    for cls, pattern in RULES.items():
        ask=P+f"ASK FROM <{s.ontology_graph}> FROM <{s.profiles_graph}> WHERE {{ BIND(<{profile_iri}> AS ?p) {pattern} }}"
        if client.run_select(ask):
            client.run_update(P+f"INSERT DATA {{ GRAPH <{s.inferred_graph}> {{ <{profile_iri}> rdf:type ptc:{cls} }} }}")
