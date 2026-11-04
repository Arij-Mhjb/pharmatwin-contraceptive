"""Deterministic graph-backed comparison, never a prescribing/diagnostic model.

Percentages measure explicitly selected preferences only. Missing graph links
remain unknown; neither scores nor absent links establish medical eligibility.
All ontology bindings are imported from ontology_map. No LLM/API is called.
"""
from hashlib import sha256
from rdflib import URIRef
from rdflib.namespace import OWL
from backend.nlp import ontology_map as m
from backend.services.ontology_service import OntologyService

VERSION = "preferences-v1"

class AssessmentService:
    def __init__(self, service=None):
        self.service = service or OntologyService()
        self.g = self.service.graph
        self._catalog = None

    def is_type(self, resource, cls):
        return any(cls == t or cls in self.g.transitive_objects(t, m.SUBCLASS_OF) for t in self.g.objects(resource, m.TYPE))

    def term(self, resource):
        return {"id": str(resource).removeprefix(str(m.ONTOLOGY)), "label": str(next(self.g.objects(resource, m.LABEL), resource)), "iri": str(resource)}

    def terms(self, cls):
        return sorted([self.term(s) for s in self.g.subjects(m.TYPE, OWL.NamedIndividual) if self.is_type(s, cls)], key=lambda x: x["label"])

    def sources(self, claim):
        results = []
        for source in self.g.objects(claim, m.P_JUSTIFIE_PAR):
            level = str(next(self.g.objects(source, m.D_SOURCE_NIVEAU), "Non précisé"))
            results.append({**self.term(source), "title": str(next(self.g.objects(source, m.D_SOURCE_TITRE), "")),
                            "url": str(next(self.g.objects(source, m.D_SOURCE_URL), "")), "level": level,
                            "synthetic": "synthétique" in level.lower() or "fictif" in level.lower()})
        return results

    def methods(self):
        result = []
        for term in self.terms(m.C_CONTRACEPTIF):
            subject = URIRef(term["iri"])
            effects = set(self.g.objects(subject, m.P_EFFET))
            benefits = set(self.g.objects(subject, m.P_BENEFICE)) | {e for e in effects if self.is_type(e, m.C_BENEFICE)}
            cis = set(self.g.objects(subject, m.P_CONTRE_INDICATION)) | set(self.g.subjects(m.P_CONCERNE_CONTRACEPTIF, subject))
            molecules = set(self.g.objects(subject, m.P_CONTIENT_MOLECULE)) | set(self.g.objects(subject, m.P_CONTIENT_OESTROGENE)) | set(self.g.objects(subject, m.P_CONTIENT_PROGESTATIF)) | set(self.g.subjects(m.P_EST_CONTENU_DANS, subject))
            hormonal = True if self.is_type(subject, m.C_HORMONAL) else False if self.is_type(subject, m.C_NON_HORMONAL) else None
            result.append({**term, "form": str(next(self.g.objects(subject, m.D_FORME), "Non renseignée")), "hormonal": hormonal,
                "molecules": [self.term(x) for x in sorted(molecules, key=str)],
                "effects": [{**self.term(x), "description": str(next(self.g.objects(x, m.D_DESCRIPTION_EFFET), "")), "sources": self.sources(x)} for x in sorted(effects, key=str) if self.is_type(x, m.C_EFFET)],
                "benefits": [{**self.term(x), "sources": self.sources(x)} for x in sorted(benefits, key=str)],
                "contraindications": [{**self.term(ci), "conditions": [self.term(x) for x in self.g.objects(ci, m.P_CONCERNE_CONDITION)], "mec": next((int(x) for x in self.g.objects(ci, m.D_MEC)), None), "sources": self.sources(ci)} for ci in sorted(cis, key=str)]})
        return result

    def catalog(self):
        if self._catalog is not None: return self._catalog
        methods = self.methods()
        self._catalog = {"methods": methods, "conditions": self.service.conditions(), "molecules": self.terms(m.C_MOLECULE),
                "benefits": self.terms(m.C_BENEFICE), "effects": self.terms(m.C_EFFET), "forms": sorted({x["form"] for x in methods}),
                "notice": "Prototype pédagogique local : utilisez uniquement des profils fictifs. Les connaissances cliniques de cette ontologie ne sont pas validées pour la prescription."}
        return self._catalog

    def validate(self, data):
        catalog = self.catalog()
        for selected, allowed, name in [([data.current_method] if data.current_method else [], catalog["methods"], "contraception actuelle"),
            ([h.method_id for h in data.history], catalog["methods"], "historique"),
            (data.medications, catalog["molecules"], "médicament"), (data.preferences.benefits, catalog["benefits"], "bénéfice"),
            (data.preferences.avoid_effects, catalog["effects"], "effet")]:
            if set(selected) - {item["id"] for item in allowed}: raise ValueError(f"Identifiant inconnu : {name}")
        if set(data.preferences.forms) - set(catalog["forms"]): raise ValueError("Forme inconnue")

    def assess(self, data):
        self.validate(data)
        profile, prefs = data.profile, data.preferences
        candidates = []
        for method in self.catalog()["methods"]:
            flags, criteria = [], []
            for ci in method["contraindications"]:
                matching = [c for c in ci["conditions"] if c["id"] in profile.conditions]
                if matching:
                    flags.append({"kind": "contraindication", "reason": f"{ci['label']} — condition renseignée : {', '.join(c['label'] for c in matching)}.", "mec": ci["mec"], "sources": ci["sources"]})
            molecules = {x["id"] for x in method["molecules"]}
            for drug in data.medications:
                drug_iri = m.ONTOLOGY[drug]
                for mol in molecules:
                    mol_iri = m.ONTOLOGY[mol]
                    if (drug_iri, m.P_INTERAGIT, mol_iri) in self.g or (mol_iri, m.P_INTERAGIT, drug_iri) in self.g:
                        flags.append({"kind": "interaction", "reason": "Interaction moléculaire modélisée avec " + self.term(drug_iri)["label"], "sources": []})
                for interaction in set(self.g.subjects(m.P_CONCERNE_MOLECULE, drug_iri)):
                    related = {self.term(x)["id"] for x in self.g.objects(interaction, m.P_CONCERNE_MOLECULE)}
                    if (related - {drug}) & molecules or (drug not in molecules and URIRef(method["iri"]) in self.g.objects(interaction, m.P_MODIFIE_EFFICACITE)):
                        flags.append({"kind": "interaction", "reason": self.term(interaction)["label"], "sources": self.sources(interaction)})
            def criterion(label, matched, reason): criteria.append({"label": label, "matched": matched, "reason": reason})
            if prefs.forms: criterion("Forme souhaitée", method["form"] in prefs.forms, method["form"])
            if prefs.hormones != "indifferent": criterion("Préférence hormonale", None if method["hormonal"] is None else method["hormonal"] == (prefs.hormones == "accept"), "Hormonal" if method["hormonal"] else "Non hormonal" if method["hormonal"] is False else "Non renseigné")
            for goal in prefs.benefits:
                found = next((x for x in method["benefits"] if x["id"] == goal), None)
                criterion(self.term(m.ONTOLOGY[goal])["label"], True if found else None, "Bénéfice associé dans le graphe" if found else "Bénéfice non documenté pour cette méthode")
            for unwanted in prefs.avoid_effects:
                found = next((x for x in method["effects"] if x["id"] == unwanted), None)
                criterion("Éviter : " + self.term(m.ONTOLOGY[unwanted])["label"], False if found else None, "Effet possible documenté, sans prédiction individuelle" if found else "Absence de données, et non absence de risque")
            past = [h for h in data.history if h.method_id == method["id"] and h.experience != "unknown"]
            if past: criterion("Votre expérience passée", all(h.experience == "positive" for h in past), "Tolérance déclarée par vous, sans attribution médicale de causalité")
            known = [c for c in criteria if c["matched"] is not None]
            blocked = any(f["kind"] == "contraindication" for f in flags)
            score = round(100 * sum(c["matched"] is True for c in known) / len(known)) if known and not flags else None
            candidates.append({**method, "flags": flags, "status": "blocked" if blocked else "review" if flags else "undetermined", "preference_score": score,
                "criteria": criteria, "assessed_criteria": len(known), "total_criteria": len(criteria), "coverage": round(100 * len(known) / len(criteria)) if criteria else 0})
        candidates.sort(key=lambda c: (c["status"] != "undetermined", -(c["preference_score"] if c["preference_score"] is not None else -1), -c["coverage"], c["label"]))
        gaps = ["Le graphe n’est pas un référentiel exhaustif d’admissibilité. Aucune option n’est déclarée médicalement autorisée.",
                "Âge, IMC, tension et tabagisme sont enregistrés, mais les règles détaillées correspondantes ne sont pas toutes modélisées.",
                "Les symptômes déclarés ne sont ni un diagnostic ni la preuve qu’un contraceptif en est la cause."]
        if not data.history_complete: gaps.append("Votre histoire médicale et médicamenteuse reste à compléter.")
        if profile.pression_systolique is None or profile.pression_diastolique is None: gaps.append("Tension artérielle non renseignée ou incomplète.")
        if data.other_medications: gaps.append("Des médicaments en texte libre ne peuvent pas être évalués automatiquement.")
        if data.other_conditions: gaps.append("Des antécédents hors du vocabulaire de l’ontologie sont enregistrés mais non évalués automatiquement.")
        if not data.preferences.model_dump()["forms"] and not data.preferences.benefits and not data.preferences.avoid_effects and prefs.hormones == "indifferent" and not data.history:
            gaps.append("Aucune préférence discriminante : aucun pourcentage n’est calculé.")
        catalog = self.catalog()
        labels = {term["id"]: term["label"] for group in ("conditions", "methods", "molecules", "benefits", "effects") for term in catalog[group]}
        return {"snapshot": data.model_dump(mode="json"), "labels": labels, "candidates": candidates, "gaps": gaps,
                "score_explanation": "Affinité de préférences = critères satisfaits / critères documentés × 100, à poids égaux. Les critères inconnus sont exclus du dénominateur et affichés dans la couverture. Ce n’est ni une probabilité de sécurité, ni d’efficacité, ni une recommandation de prescription. Les options signalées ne reçoivent pas de pourcentage.",
                "rules_version": VERSION, "ontology_sha256": sha256(self.service.settings.ontology_path.read_bytes()).hexdigest(),
                "clinical_validation": "Ontologie pédagogique : connaissances non validées pour une utilisation clinique."}
