from rdflib import Graph, RDF, RDFS, OWL, URIRef
from backend.config import get_settings
from backend.nlp import ontology_map as m

class OntologyService:
    def __init__(self, path=None):
        self.settings=get_settings(); self.graph=Graph(); self.graph.parse(path or self.settings.ontology_path, format="turtle")
    def _items(self, rdf_type):
        out=[]
        for iri in sorted(set(self.graph.subjects(RDF.type, rdf_type)), key=str):
            if isinstance(iri, URIRef): out.append({"iri":str(iri),"id":str(iri).rsplit("#",1)[-1],"label":next((str(x) for x in self.graph.objects(iri,RDFS.label)),None)})
        return out
    def classes(self): return self._items(OWL.Class)
    def conditions(self):
        allowed = {row[0] for row in self.graph.query(f"SELECT DISTINCT ?c WHERE {{ ?c <{m.TYPE}>/<{m.SUBCLASS_OF}>* <{m.C_CONDITION}> }}")}
        return [item for item in self.individuals() if URIRef(item["iri"]) in allowed]
    def properties(self): return self._items(OWL.ObjectProperty)+self._items(OWL.DatatypeProperty)
    def individuals(self): return self._items(OWL.NamedIndividual)
    def stats(self): return {"triples":len(self.graph),"classes":len(self.classes()),"object_properties":len(self._items(OWL.ObjectProperty)),"datatype_properties":len(self._items(OWL.DatatypeProperty)),"individuals":len(self.individuals())}
    def axioms(self):
        from rdflib import BNode
        def expression(node, seen=frozenset()):
            if not isinstance(node, BNode): return str(node)
            if node in seen: return "…"
            return {str(p): expression(o, seen | {node}) for p, o in self.graph.predicate_objects(node)}
        predicates = (RDFS.subClassOf, RDFS.domain, RDFS.range, OWL.equivalentClass, OWL.disjointWith, OWL.inverseOf)
        return [{"subject": str(s), "predicate": str(p), "object": str(o),
                 "expression": expression(o)}
                for p in predicates for s, o in sorted(self.graph.subject_objects(p), key=lambda pair: (str(pair[0]), str(pair[1])))]
    def inventory(self):
        return {"stats": self.stats(), "classes": self.classes(),
                "object_properties": self._items(OWL.ObjectProperty),
                "datatype_properties": self._items(OWL.DatatypeProperty),
                "individuals": self.individuals(), "axioms": self.axioms()}
    def resource(self, local_id):
        iri=URIRef(self.settings.namespace+local_id)
        if not any(True for _ in self.graph.predicate_objects(iri)): return None
        return {"iri":str(iri),"statements":[{"predicate":str(p),"object":str(o)} for p,o in self.graph.predicate_objects(iri)]}
