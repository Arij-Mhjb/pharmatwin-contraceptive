from .ontology_index import OntologyIndex
class EntityLinker:
 def __init__(self,index=None): self.index=index or OntologyIndex()
 def link(self,text,threshold=.45): return [x for x in self.index.search(text,5) if x["score"]>=threshold]
