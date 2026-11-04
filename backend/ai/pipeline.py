from functools import lru_cache
from .intent_classifier import IntentClassifier
from .entity_linker import EntityLinker
from .model_loader import get_spacy_model
from backend.services.sparql_templates import TEMPLATES, P, UNION
from backend.services.security import validate_select
@lru_cache(maxsize=1)
def components(): return IntentClassifier(),EntityLinker(),get_spacy_model()
def translate(question:str)->dict:
 classifier,linker,nlp=components(); _=nlp(question); pred=classifier.predict(question); intent=pred["intent"]
 entities=linker.link(question)
 if intent=="unsupported": return {"intent":intent,"entities":{},"sparql":""}
 sparql=TEMPLATES.get(intent)
 if not sparql and entities:
  iri=entities[0]["iri"]
  relation={"contraceptive_molecules":"contientMolecule","contraceptive_effects":"peutProduire","contraceptive_contraindications":"aContreIndication","molecule_interactions":"interagitAvecMolecule"}.get(intent)
  if relation: sparql=P+f"SELECT DISTINCT ?iri ?label {UNION} WHERE {{ <{iri}> ptc:{relation}|^ptc:{relation} ?iri. OPTIONAL {{?iri rdfs:label ?label}} }} LIMIT 100"
 if not sparql: return {"intent":"unsupported","entities":{},"sparql":""}
 return {"intent":intent,"entities":{"matches":entities[:3]},"sparql":validate_select(sparql)}
