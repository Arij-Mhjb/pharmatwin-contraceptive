from backend.services.ontology_service import OntologyService
import json
s=OntologyService();print(json.dumps(s.stats(),indent=2,ensure_ascii=False));print("Classes:");print("\n".join(x["iri"] for x in s.classes()))
