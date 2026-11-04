"""Query execution tests, independent of a local ontology file or spaCy model."""

import unittest
from unittest.mock import patch

from rdflib import Graph, Literal, Namespace
from rdflib.plugins.sparql.parser import parseQuery

from backend.nlp import ontology_map as m
from backend.nlp.intent import INTENTS
from backend.nlp.templates import TEMPLATES, build_query


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.g = Graph()
        self.n = Namespace("urn:template-test:")
        n = self.n
        for child, parent in [(n.methodClass, m.C_CONTRACEPTIF), (n.conditionClass, m.C_CONDITION),
                              (n.ciClass, m.C_CONTRE_INDICATION), (m.C_CONDITION_CHC, m.C_CONDITION),
                              (m.C_PROFIL_RISQUE_VASCULAIRE, m.C_PROFIL)]:
            self.g.add((child, m.SUBCLASS_OF, parent))
        for resource, cls in [(n.method, n.methodClass), (n.condition, n.conditionClass),
                              (n.ci, n.ciClass), (n.adverse, m.C_EFFET), (n.benefit, m.C_BENEFICE),
                              (n.molecule, m.C_MOLECULE), (n.partner, m.C_MOLECULE),
                              (n.profile, m.C_PROFIL), (n.source, m.C_SOURCE)]:
            self.g.add((resource, m.TYPE, cls))
            self.g.add((resource, m.LABEL, Literal(str(resource).split(":")[-1])))
        # Only the inverse CI assertion is present: a reasoner is not required.
        for triple in [(n.ci, m.P_CONCERNE_CONTRACEPTIF, n.method),
                       (n.ci, m.P_CONCERNE_CONDITION, n.condition),
                       (n.method, m.P_EFFET, n.adverse), (n.method, m.P_EFFET, n.benefit),
                       (n.method, m.P_CONTIENT_PROGESTATIF, n.molecule),
                       (n.interaction, m.P_CONCERNE_MOLECULE, n.molecule),
                       (n.interaction, m.P_CONCERNE_MOLECULE, n.partner),
                       (n.profile, m.P_A_POUR_CONDITION, n.condition),
                       (n.ci, m.P_JUSTIFIE_PAR, n.source)]:
            self.g.add(triple)

    def entity(self, name, kind="individual"):
        return {"text": name, "label": name, "iri": str(self.n[name]), "kind": kind}

    def results(self, intent, entities=(), **options):
        return {row.result for row in self.g.query(build_query(intent, entities, **options))}

    def test_all_intents_have_parseable_bounded_queries(self):
        self.assertEqual(set(TEMPLATES), set(INTENTS))
        for intent in INTENTS:
            with self.subTest(intent=intent):
                query = build_query(intent)
                parseQuery(query)
                self.assertIn("PREFIX ", query)
                self.assertIn("ORDER BY", query)
                self.assertIn("LIMIT 50", query)
                self.assertNotIn("PLACEHOLDER", query)

    def test_semantic_results(self):
        n = self.n
        method = [self.entity("methodClass", "class")]
        cases = [
            ("contre_indications_contraceptif", method, {n.ci}),
            ("effets_indesirables_contraceptif", method, {n.adverse}),
            ("molecules_contraceptif", method, {n.molecule}),
            ("interactions_molecule", [self.entity("molecule")], {n.partner}),
            ("contraceptifs_contre_indiques_condition", [self.entity("condition")], {n.method}),
            ("profils_par_condition", [self.entity("condition")], {n.profile}),
            ("benefices_contraceptif", method, {n.benefit}),
            ("sources_preuve", [self.entity("ciClass", "class")], {n.source}),
            ("sources_preuve", method, {n.source}),
            ("lister_classe", method, {n.method}),
        ]
        for intent, entities, expected in cases:
            with self.subTest(intent=intent, entities=entities):
                self.assertEqual(self.results(intent, entities), expected)
        self.assertEqual(self.results("profils_par_condition", [self.entity("absent")]), set())

    def test_risk_definitions_without_reasoner(self):
        n = self.n
        self.g.add((n.condition, m.TYPE, m.C_FACTEUR_RISQUE))
        self.g.add((n.condition, m.TYPE, m.C_CONDITION_CHC))
        self.g.add((n.vascular, m.TYPE, m.C_PROFIL_RISQUE_VASCULAIRE))
        self.assertEqual(self.results("profils_a_risque"), {n.profile})
        self.assertEqual(self.results("profils_a_risque", risk_kind="oestrogenes"), {n.profile})
        self.assertEqual(self.results("profils_a_risque", risk_kind="vasculaire"), {n.vascular})

    def test_safe_keyword_fallback_and_empty_input(self):
        self.assertEqual(self.results("recherche_libre", keywords=["adverse"]), {self.n.adverse})
        self.assertEqual(self.results("unknown", keywords=["adverse"]), {self.n.adverse})
        self.assertEqual(self.results("recherche_libre"), set())
        query = build_query("recherche_libre", keywords=['\" } UNION { ?s ?p ?o } #', "line\nbreak"])
        self.assertEqual(list(self.g.query(query)), [])
        for bad in ['urn:x> } UNION { ?s ?p ?o', 'relative', 'urn:PLACEHOLDER']:
            with self.subTest(iri=bad), self.assertRaises(ValueError):
                build_query("lister_classe", [{"iri": bad, "kind": "class"}])
        for limit in [0, 501, True, "50"]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                build_query("recherche_libre", limit=limit)

    def test_mapping_is_replaceable(self):
        with patch.object(m, "P_EFFET", self.n.replacementEffect):
            query = build_query("effets_indesirables_contraceptif")
            self.assertIn(str(self.n.replacementEffect), query)
            self.assertEqual(list(self.g.query(query)), [])

    def test_unmaterialized_pill_class_uses_verified_form_mapping(self):
        for cls, forms in m.CLASS_FORM_VALUES.items():
            with self.subTest(cls=cls):
                self.g.add((self.n.method, m.D_FORME, Literal(forms[0])))
                entities = [{"iri": str(cls), "kind": "class"}]
                self.assertEqual(self.results("molecules_contraceptif", entities), {self.n.molecule})
                self.assertEqual(self.results("lister_classe", entities), {self.n.method})
                self.g.remove((self.n.method, m.D_FORME, None))


if __name__ == "__main__":
    unittest.main()
