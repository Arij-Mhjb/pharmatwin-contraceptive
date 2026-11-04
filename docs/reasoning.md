# Reasoning

Asserted triples remain in the ontology/profile graphs. Inferred `rdf:type` assertions are stored separately in the inferred graph. Machine-learning similarities are never stored as logical facts.

HermiT remains the reference OWL 2 DL validator: open the source in Protégé, run **Reasoner → HermiT → Start reasoner**, then export inferred axioms to `pharmatwin_inferred.ttl`. Jena is not presented as a complete OWL 2 DL reasoner.

For dynamic profiles, the backend implements the profile-local consequences of the actual equivalent-class axioms for SOPK, endometriosis and estrogen alerts. Each create/update deletes the affected old class assertions and recomputes them; delete removes profile and inferred triples. This deliberately limited materialization avoids stale classifications. Run `PYTHONPATH=. python backend/scripts/verify_reasoning.py` to verify the defining axioms.
