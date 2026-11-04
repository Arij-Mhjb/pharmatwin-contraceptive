from pathlib import Path
from rdflib import Graph,RDF,OWL,URIRef
g=Graph().parse(Path(__file__).resolve().parents[2]/"ontology/pharmatwin.ttl")
for name in ("ProfilSOPK","ProfilEndometriose","ProfilAlerteOestrogene"):
 iri=URIRef("https://pharmatwin.ai/contraceptive#"+name); print(name,"defined=",(iri,RDF.type,OWL.Class) in g,"equivalent axioms=",len(list(g.objects(iri,OWL.equivalentClass))))
