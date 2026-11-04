from pathlib import Path
from rdflib import Graph
root=Path(__file__).resolve().parents[2];src=root/"ontology/source/PharmaTwin_Contraceptive.owl";dst=root/"ontology/pharmatwin.ttl"
g=Graph();g.parse(src,format="xml");g.serialize(dst,format="turtle");print(f"{len(g)} triples -> {dst}")
