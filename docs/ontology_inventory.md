# Ontology inventory

Generated from `ontology/source/PharmaTwin_Contraceptive.owl` on 2026-11-04 with RDFLib 7.1.1. The RDF/XML source and Turtle export are graph-isomorphic and contain **1,228 triples**.

| Element | Count |
|---|---:|
| Named classes | 45 |
| Object properties | 22 |
| Datatype properties | 24 |
| Named individuals | 80 |
| `rdfs:subClassOf` statements | 44 |
| `owl:equivalentClass` axioms | 7 |
| OWL restrictions | 17 |

Namespace: `https://pharmatwin.ai/contraceptive#` (`ptc`). Core profile classes include `ProfilPatiente`, `ProfilSOPK`, `ProfilEndometriose` and `ProfilAlerteOestrogene`. The complete, executable listing is produced by:

```bash
PYTHONPATH=. python backend/scripts/inspect_ontology.py
```

The ontology defines `aCondition`, `aObservation`, `contientMolecule`, `peutProduire`, `aContreIndication`, `interagitAvecMolecule`, `justifiePar`, and other domain relationships. API templates only use properties verified in this graph.
