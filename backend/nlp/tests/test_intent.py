"""French intent regression cases using the corrected generated lexicon."""

import unittest

from backend.nlp.entities import EntityExtractor
from backend.nlp.intent import detect_intent
from backend.nlp.preprocess import preprocess


class IntentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = EntityExtractor()

    def test_questions(self):
        cases = [
            ("Quelles sont les contre-indications de la pilule combinée ?", "contre_indications_contraceptif", "Pilule combinée"),
            ("Contre indications de la pilule progestative seule", "contre_indications_contraceptif", "Pilule progestative seule"),
            ("Quels contraceptifs sont contre-indiqués avec une migraine avec aura ?", "contraceptifs_contre_indiques_condition", "Migraine avec aura"),
            ("Quels contraceptifs sont contre indiqués avec une insuffisance rénale ?", "contraceptifs_contre_indiques_condition", "Insuffisance rénale"),
            ("Quels sont les effets indésirables de la pilule combinée ?", "effets_indesirables_contraceptif", "Pilule combinée"),
            ("Effets secondaires du désogestrel", "effets_indesirables_contraceptif", "Désogestrel"),
            ("Quels effets de la pilule combinee ?", "effets_indesirables_contraceptif", "Pilule combinée"),
            ("Quelles molécules contient la pilule combinée ?", "molecules_contraceptif", "Pilule combinée"),
            ("Composition de la pilule combinée", "molecules_contraceptif", "Pilule combinée"),
            ("Que contient la pilule progestative seule ?", "molecules_contraceptif", "Pilule progestative seule"),
            ("Quelles molécules interagissent avec la Rifampicine ?", "interactions_molecule", "Rifampicine"),
            ("Interactions de la drospirénone", "interactions_molecule", "Drospirénone"),
            ("Avec quoi interagit le désogestrel ?", "interactions_molecule", "Désogestrel"),
            ("Quels profils ont une endométriose ?", "profils_par_condition", "Endométriose"),
            ("Montre les profils avec SOPK", "profils_par_condition", "SOPK"),
            ("Profils avec migraine avec aura", "profils_par_condition", "Migraine avec aura"),
            ("Montre-moi les profils avec facteur de risque vasculaire.", "profils_a_risque", None),
            ("Quels profils sont en alerte pour les œstrogènes ?", "profils_a_risque", None),
            ("Liste les profils à risque", "profils_a_risque", None),
            ("Quels bénéfices de la pilule combinée ?", "benefices_contraceptif", "Pilule combinée"),
            ("Quels effets bénéfiques de la pilule progestative seule ?", "benefices_contraceptif", "Pilule progestative seule"),
            ("Avantages de la pilule combinée", "benefices_contraceptif", "Pilule combinée"),
            ("Quelle étude justifie la contre-indication oncologique ?", "sources_preuve", "Contre-indication oncologique"),
            ("Sources de preuve sur la pilule combinée", "sources_preuve", "Pilule combinée"),
            ("Quelles références pour la drospirénone ?", "sources_preuve", "Drospirénone"),
            ("Liste les contraceptifs hormonaux", "lister_classe", "Contraceptif hormonal"),
            ("Affiche les molécules", "lister_classe", "Molécule"),
            ("Bonjour", "recherche_libre", None),
            ("", "recherche_libre", None),
            ("Rifampicine", "recherche_libre", "Rifampicine"),
        ]
        for question, intent, label in cases:
            with self.subTest(question=question):
                entities = self.extractor.extract(question)
                data = preprocess(question, nlp=self.extractor.nlp)
                self.assertEqual(detect_intent(data, entities), intent)
                if label:
                    self.assertIn(label, [e["label"] for e in entities])


if __name__ == "__main__":
    unittest.main()
