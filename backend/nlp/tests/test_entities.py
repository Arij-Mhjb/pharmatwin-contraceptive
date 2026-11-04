"""Integration checks against the installed French spaCy model."""

import json
from pathlib import Path
import tempfile
import unittest

from backend.nlp.entities import EntityExtractor, SAMPLE_LEXICON


class EntityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = EntityExtractor(SAMPLE_LEXICON)

    def test_french_questions(self):
        cases = [
            ("Quels effets de la pilule combinée ?", ["pilule combinée"]),
            ("Quels effets de la pilule combinee ?", ["pilule combinée"]),
            ("Avec une migrain avec aura ?", ["migraine avec aura"]),
            ("Et pour l'endometriose ?", ["endométriose"]),
            ("Interactions avec la Rifampicine", ["rifampicine"]),
            ("Quels profils pour les œstrogènes ?", ["œstrogène"]),
            ("Un contraceptif non hormonal", ["contraceptif non hormonal"]),
            ("Un progestatif anti-androgénique", ["progestatif anti-androgénique"]),
            ("SOPK et hypertension", ["SOPK", "hypertension"]),
            ("Le DIU", ["DIU"]),
            ("Montre du texte sans rapport", []),
            ("Bonjour", []),
            ("", []),
        ]
        for question, expected in cases:
            with self.subTest(question=question):
                entities = self.extractor.extract(question)
                self.assertEqual([e["label"] for e in entities], expected)
                for entity in entities:
                    self.assertIn(entity["text"], question)
                    self.assertIn(entity["kind"], {"class", "individual", "objectProperty", "dataProperty"})

    def test_replaceable_lexicon(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "lexicon.json"
            path.write_text(json.dumps({"aspirine": {"iri": "urn:test:aspirine", "kind": "individual"}}), encoding="utf-8")
            extractor = EntityExtractor(path, nlp=self.extractor.nlp)
            self.assertEqual(extractor.extract("aspirine")[0]["iri"], "urn:test:aspirine")
            self.assertEqual(extractor.extract("rifampicine"), [])


if __name__ == "__main__":
    unittest.main()
