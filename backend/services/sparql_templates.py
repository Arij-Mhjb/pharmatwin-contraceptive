P = "PREFIX ptc: <https://pharmatwin.ai/contraceptive#>\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\nPREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
UNION = "FROM <https://pharmatwin.ai/graph/ontology> FROM <https://pharmatwin.ai/graph/profiles> FROM <https://pharmatwin.ai/graph/inferred>"
def profiles_by_class(class_id: str):
    return P + f"SELECT DISTINCT ?iri ?label ?identifiant {UNION} WHERE {{ ?iri rdf:type ptc:{class_id}; ptc:identifiantProfil ?identifiant. OPTIONAL {{?iri rdfs:label ?label}} }} LIMIT 100"
TEMPLATES = {
 "list_profiles": P + f"SELECT DISTINCT ?iri ?identifiant ?age ?imc ?fume {UNION} WHERE {{ ?iri ptc:identifiantProfil ?identifiant; ptc:age ?age; ptc:imc ?imc; ptc:fume ?fume. }} LIMIT 100",
 "profiles_estrogen_alert": profiles_by_class("ProfilAlerteOestrogene"),
 "profiles_sopk": profiles_by_class("ProfilSOPK"),
 "profiles_endometriosis": profiles_by_class("ProfilEndometriose"),
 "list_contraceptives": P + f"SELECT DISTINCT ?iri ?label {UNION} WHERE {{ ?iri rdf:type/rdfs:subClassOf* ptc:Contraceptif. OPTIONAL {{?iri rdfs:label ?label}} }} LIMIT 100",
 "evidence_sources": P + f"SELECT DISTINCT ?iri ?label ?title {UNION} WHERE {{ ?iri rdf:type/rdfs:subClassOf* ptc:Etude. OPTIONAL {{?iri rdfs:label ?label}} OPTIONAL {{?iri ptc:titreSource ?title}} }} LIMIT 100",
}
