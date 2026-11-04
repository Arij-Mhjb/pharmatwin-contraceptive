"""Task 7 integration and graceful degradation checks."""

import json
import os
import unittest
from unittest.mock import patch

from rdflib import Graph, Literal, URIRef
from rdflib.plugins.sparql.parser import parseQuery

from backend.nlp import ontology_map as m
from backend.nlp.translator import EMPTY_QUERY, translate


class TranslatorTests(unittest.TestCase):
    def check_contract(self, result):
        self.assertEqual(set(result), {"intent", "entities", "sparql"})
        self.assertIsInstance(result["entities"], list)
        json.dumps(result, ensure_ascii=False)
        parseQuery(result["sparql"])

    def test_normal_translation(self):
        result = translate("Quelles molécules interagissent avec la Rifampicine ?")
        self.check_contract(result)
        self.assertEqual(result["intent"], "interactions_molecule")
        self.assertIn("Rifampicine", [e["label"] for e in result["entities"]])
        self.assertNotIn("PLACEHOLDER", result["sparql"])

    def test_unknown_input_and_invalid_types(self):
        for question in ["Bonjour", "", "   ", None, 42, {}, [], "?!"]:
            with self.subTest(question=question):
                result = translate(question)
                self.check_contract(result)
                self.assertEqual(result["intent"], "recherche_libre")
                if not isinstance(question, str) or not question.strip():
                    self.assertEqual(list(Graph().query(result["sparql"])), [])

    def test_missing_nlp_resources_falls_back_with_accents(self):
        graph = Graph()
        resource = URIRef("urn:test:condition")
        graph.add((resource, m.LABEL, Literal("Endométriose", lang="fr")))
        with patch("backend.nlp.translator._extractor", side_effect=RuntimeError("model unavailable")):
            with self.assertLogs("backend.nlp.translator", level="WARNING"):
                result = translate("endometriose")
        self.check_contract(result)
        self.assertEqual(result["intent"], "recherche_libre")
        self.assertEqual(result["entities"], [])
        self.assertEqual({r.result for r in graph.query(result["sparql"])}, {resource})

    def test_template_error_falls_back(self):
        with patch("backend.nlp.templates.build_query", side_effect=ValueError("bad binding")):
            with self.assertLogs("backend.nlp.translator", level="WARNING"):
                result = translate("Rifampicine")
        self.check_contract(result)
        self.assertEqual(result["intent"], "recherche_libre")

    def test_missing_configured_lexicon(self):
        with patch.dict(os.environ, {"PHARMATWIN_LEXICON": "does-not-exist/lexicon.json"}):
            with self.assertLogs("backend.nlp.translator", level="WARNING"):
                result = translate("Rifampicine")
        self.check_contract(result)
        self.assertEqual(result["intent"], "recherche_libre")
        self.assertEqual(result["entities"], [])

    def test_emergency_empty_query(self):
        with patch("backend.nlp.templates.build_query", side_effect=ValueError), patch(
            "backend.nlp.templates.recherche_libre", side_effect=ValueError
        ):
            with self.assertLogs("backend.nlp.translator", level="WARNING"):
                result = translate("")
        self.check_contract(result)
        self.assertEqual(result["sparql"], EMPTY_QUERY)
        self.assertEqual(list(Graph().query(result["sparql"])), [])

    def test_risk_variant_is_not_inferred_from_alert_alone(self):
        vascular = translate("Montre-moi les profils avec facteur de risque vasculaire.")
        estrogen = translate("Quels profils sont en alerte pour les œstrogènes ?")
        general = translate("Quels profils sont en alerte ?")
        for result in (vascular, estrogen, general):
            self.check_contract(result)
            self.assertEqual(result["intent"], "profils_a_risque")
        self.assertIn(str(m.C_PROFIL_RISQUE_VASCULAIRE), vascular["sparql"])
        self.assertIn(str(m.C_PROFIL_ALERTE_OESTROGENE), estrogen["sparql"])
        self.assertNotIn(str(m.C_PROFIL_ALERTE_OESTROGENE), general["sparql"])


if __name__ == "__main__":
    unittest.main()
