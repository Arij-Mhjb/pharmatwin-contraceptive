import numpy as np
from backend.services.ontology_service import OntologyService
from .semantic_embeddings import encode
class OntologyIndex:
 def __init__(self, service=None):
  service=service or OntologyService(); self.items=service.classes()+service.individuals()
  self.texts=[" ".join(filter(None,[x.get("label"),x.get("id")])) for x in self.items]; self.matrix=encode(self.texts) if self.texts else np.empty((0,0))
 def search(self,q,k=10):
  if not self.items:return []
  scores=(encode([q])@self.matrix.T)[0]; idx=np.argsort(scores)[::-1][:k]
  return [{**self.items[int(i)],"score":round(float(scores[i]),4)} for i in idx]
