"""Task 8: French question regressions, query execution and failure handling.

Question cases assert human-readable labels, never ontology IRIs. Required
labels are a subset because generic nouns such as 'molécule' can also match.
Each case becomes a separate named test in unittest's verbose output.
"""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from rdflib import Graph, Literal, URIRef
from rdflib.plugins.sparql.parser import parseQuery

from backend.nlp import ontology_map as m
from backend.nlp.translator import EMPTY_QUERY, translate


FRENCH_CASES = [
    ("Quelles sont les contre-indications de la pilule combinée ?", "contre_indications_contraceptif", ("Pilule combinée",)),
    ("Contre indications de la pilule progestative seule", "contre_indications_contraceptif", ("Pilule progestative seule",)),
    ("Quelles contre-indications pour la pilule combinee ?", "contre_indications_contraceptif", ("Pilule combinée",)),
    ("Quels sont les effets indésirables de la pilule combinée ?", "effets_indesirables_contraceptif", ("Pilule combinée",)),
    ("Quels effets secondaires de la pilule progestative seule ?", "effets_indesirables_contraceptif", ("Pilule progestative seule",)),
    ("Quels effets de la pilule combinee ?", "effets_indesirables_contraceptif", ("Pilule combinée",)),
    ("Quelles molécules contient la pilule combinée ?", "molecules_contraceptif", ("Pilule combinée",)),
    ("Composition de la pilule combinée", "molecules_contraceptif", ("Pilule combinée",)),
    ("Que contient la pilule progestative seule ?", "molecules_contraceptif", ("Pilule progestative seule",)),
    ("Quelles molecules contient la pilule combinee ?", "molecules_contraceptif", ("Pilule combinée",)),
    ("Quelles molécules interagissent avec la Rifampicine ?", "interactions_molecule", ("Rifampicine",)),
    ("Interactions de la drospirénone", "interactions_molecule", ("Drospirénone",)),
    ("Avec quoi interagit le désogestrel ?", "interactions_molecule", ("Désogestrel",)),
    ("Quelles interactions avec la rifampicin ?", "interactions_molecule", ("Rifampicine",)),
    ("Quels contraceptifs sont contre-indiqués avec une migraine avec aura ?", "contraceptifs_contre_indiques_condition", ("Migraine avec aura",)),
    ("Quels contraceptifs sont contre indiqués avec une insuffisance rénale ?", "contraceptifs_contre_indiques_condition", ("Insuffisance rénale",)),
    ("Quels contraceptifs sont contre-indiqués avec une migrain avec aura ?", "contraceptifs_contre_indiques_condition", ("Migraine avec aura",)),
    ("Quels contraceptifs sont contre-indiqués avec un cancer du sein actuel ?", "contraceptifs_contre_indiques_condition", ("Cancer du sein actuel",)),
    ("Quels profils ont une endométriose ?", "profils_par_condition", ("Endométriose",)),
    ("Montre les profils avec SOPK", "profils_par_condition", ("SOPK",)),
    ("Profils avec migraine avec aura", "profils_par_condition", ("Migraine avec aura",)),
    ("Quels profils avec endometriose ?", "profils_par_condition", ("Endométriose",)),
    ("Quels profils présentent un cancer du sein actuel ?", "profils_par_condition", ("Cancer du sein actuel",)),
    ("Montre-moi les profils avec facteur de risque vasculaire.", "profils_a_risque", ("Profil avec facteur de risque vasculaire",)),
    ("Quels profils sont en alerte pour les œstrogènes ?", "profils_a_risque", ("Œstrogène",)),
    ("Liste les profils à risque", "profils_a_risque", ()),
    ("Quels bénéfices de la pilule combinée ?", "benefices_contraceptif", ("Pilule combinée",)),
    ("Quels effets bénéfiques de la pilule progestative seule ?", "benefices_contraceptif", ("Pilule progestative seule",)),
    ("Avantages de la pilule combinée", "benefices_contraceptif", ("Pilule combinée",)),
    ("Quelle étude justifie la contre-indication oncologique ?", "sources_preuve", ("Contre-indication oncologique",)),
    ("Sources de preuve sur la pilule combinée", "sources_preuve", ("Pilule combinée",)),
    ("Quelles références pour la drospirénone ?", "sources_preuve", ("Drospirénone",)),
    ("Liste les contraceptifs hormonaux", "lister_classe", ("Contraceptif hormonal",)),
    ("Affiche les molécules", "lister_classe", ("Molécule",)),
    ("Contraceptif hormonal", "lister_classe", ("Contraceptif hormonal",)),
    ("Bonjour", "recherche_libre", ()),
    ("Rifampicine", "recherche_libre", ("Rifampicine",)),
    ("Recherche le mot astronomie", "recherche_libre", ()),
]


class FrenchQuestionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexicon_path = Path(__file__).resolve().parents[1] / "lexicon.json"

    def setUp(self):
        env = patch.dict(os.environ, {"PHARMATWIN_LEXICON": str(self.lexicon_path)})
        env.start()
        self.addCleanup(env.stop)


def _make_question_test(question, expected_intent, expected_labels):
    def test(self):
        response = translate(question)
        self.assertEqual(set(response), {"intent", "entities", "sparql"})
        self.assertEqual(response["intent"], expected_intent, question)
        self.assertIsInstance(response["entities"], list)
        actual_labels = {entity["label"] for entity in response["entities"]}
        self.assertTrue(set(expected_labels) <= actual_labels,
                        f"{question}: expected {expected_labels}, got {sorted(actual_labels)}")
        if expected_intent == "recherche_libre" and not expected_labels:
            self.assertEqual(response["entities"], [])
        for entity in response["entities"]:
            self.assertTrue({"text", "label", "iri", "kind"} <= entity.keys())
            self.assertIn(entity["text"], question)
            self.assertNotIn("PLACEHOLDER", entity["iri"])
        query = response["sparql"]
        parseQuery(query)
        self.assertNotIn("PLACEHOLDER", query)
        self.assertIn("ORDER BY", query)
        self.assertIn("LIMIT 50", query)
        json.dumps(response, ensure_ascii=False)
    test.__doc__ = question
    return test


for _number, _case in enumerate(FRENCH_CASES, 1):
    setattr(FrenchQuestionTests, f"test_question_{_number:02d}_{_case[1]}",
            _make_question_test(*_case))


class TranslatorExecutionTests(unittest.TestCase):
    """Check query meaning on independent data, not only SPARQL syntax."""

    def setUp(self):
        lexicon_path = Path(__file__).resolve().parents[1] / "lexicon.json"
        env = patch.dict(os.environ, {"PHARMATWIN_LEXICON": str(lexicon_path)})
        env.start()
        self.addCleanup(env.stop)
        self.lexicon = json.loads(lexicon_path.read_text(encoding="utf-8"))

    def test_all_intents_covered(self):
        from backend.nlp.intent import INTENTS
        self.assertGreaterEqual(len(FRENCH_CASES), 25)
        self.assertEqual({case[1] for case in FRENCH_CASES}, set(INTENTS))

    def test_interaction_query_returns_partner_not_target(self):
        target = URIRef(self.lexicon["Rifampicine"]["iri"])
        partner = URIRef("urn:test:partner")
        graph = Graph()
        graph.add((target, m.TYPE, m.C_MOLECULE))
        graph.add((partner, m.TYPE, m.C_MOLECULE))
        # Only the incoming direction is asserted.
        graph.add((partner, m.P_INTERAGIT, target))
        response = translate("Quelles molécules interagissent avec la Rifampicine ?")
        self.assertEqual({row.result for row in graph.query(response["sparql"])}, {partner})

    def test_profile_condition_filter_excludes_unrelated_profile(self):
        condition = URIRef(self.lexicon["Endométriose"]["iri"])
        matching = URIRef("urn:test:matching-profile")
        unrelated = URIRef("urn:test:unrelated-profile")
        graph = Graph()
        for profile in (matching, unrelated):
            graph.add((profile, m.TYPE, m.C_PROFIL))
        graph.add((matching, m.P_A_POUR_CONDITION, condition))
        graph.add((unrelated, m.P_A_POUR_CONDITION, URIRef("urn:test:other-condition")))
        response = translate("Quels profils ont une endométriose ?")
        self.assertEqual({row.result for row in graph.query(response["sparql"])}, {matching})

    def test_unknown_words_match_only_relevant_labels(self):
        matching, unrelated = URIRef("urn:test:astronomy"), URIRef("urn:test:other")
        graph = Graph()
        graph.add((matching, m.LABEL, Literal("Astronomie", lang="fr")))
        graph.add((unrelated, m.LABEL, Literal("Autre sujet", lang="fr")))
        response = translate("astronomie")
        self.assertEqual(response["intent"], "recherche_libre")
        self.assertEqual({row.result for row in graph.query(response["sparql"])}, {matching})


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
