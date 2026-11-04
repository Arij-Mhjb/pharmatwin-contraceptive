import numpy as np
from .semantic_embeddings import encode
INTENTS={
"list_profiles":["liste tous les profils", "affiche les patientes simulées"],
"profiles_estrogen_alert":["profils en alerte aux œstrogènes", "risque lié aux estrogènes"],
"profiles_sopk":["patientes avec un SOPK", "profils ovaires polykystiques"],
"profiles_endometriosis":["profils atteints d'endométriose", "patientes avec endométriose"],
"list_contraceptives":["liste des contraceptifs", "quelles méthodes contraceptives"],
"contraceptive_molecules":["quelles molécules contient ce contraceptif", "composition de cette pilule"],
"contraceptive_effects":["effets associés à ce contraceptif", "effets indésirables de cette pilule"],
"contraceptive_contraindications":["contre-indications de ce contraceptif", "quand cette pilule est contre indiquée"],
"molecule_interactions":["interactions connues de cette molécule", "interaction médicamenteuse"],
"evidence_sources":["sources scientifiques disponibles", "preuves documentaires de cette relation"],
"ontology_search":["recherche migraine dans l'ontologie", "trouve le concept endométriose"],
}
class IntentClassifier:
 def __init__(self, threshold=.48):
  self.threshold=threshold; self.labels=[]; examples=[]
  for k, vals in INTENTS.items(): self.labels += [k]*len(vals); examples += vals
  self.matrix=encode(examples)
 def predict(self, question):
  scores=(encode([question])@self.matrix.T)[0]; i=int(np.argmax(scores)); score=float(scores[i])
  return {"intent":self.labels[i] if score>=self.threshold else "unsupported","confidence":score}
