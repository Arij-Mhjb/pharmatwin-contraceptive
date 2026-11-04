"""Explainable French intent scoring using spaCy lemmas, without any LLM.

No ontology IRI or class/property name is used here. Domain words below describe
the user's question, not the ontology schema. More than one request in a question
is reduced to the highest scoring intent; this is a single-intent classifier.
"""

from __future__ import annotations

import argparse
import json

from .preprocess import PreprocessedQuestion, normalize, preprocess

INTENTS = (
    "contre_indications_contraceptif",
    "effets_indesirables_contraceptif",
    "molecules_contraceptif",
    "interactions_molecule",
    "contraceptifs_contre_indiques_condition",
    "profils_par_condition",
    "profils_a_risque",
    "benefices_contraceptif",
    "sources_preuve",
    "lister_classe",
    "recherche_libre",
)


def score_intents(question: str | PreprocessedQuestion, entities=()) -> dict[str, int]:
    """Return auditable scores. Entity kinds give a small listing signal only.

    A class/individual kind alone cannot tell us whether an entity is a molecule,
    condition or contraceptive; directional question wording supplies that signal.
    """
    data = preprocess(question) if isinstance(question, str) else question
    words = set(data.lemmas)
    text = normalize(data.text)
    scores = {name: 0 for name in INTENTS}
    profile = bool(words & {"profil", "patiente", "patient"})
    risk = bool(words & {"risque", "alerte", "vasculaire"})
    contraindication = ("contre-indiqu" in text or "contre indiqu" in text
                       or "contre-indication" in text or "contre indication" in text)
    # A request for contraceptives given a condition reverses the query direction
    # compared with asking for the contraindications of a named contraceptive.
    asks_contraceptives = bool(words & {"contraceptif", "methode"}) and any(
        marker in text for marker in ("quels contraceptifs", "quelles methodes", "liste les contraceptifs", "contraceptifs sont")
    )
    if contraindication:
        scores["contre_indications_contraceptif"] += 6
        if asks_contraceptives:
            scores["contraceptifs_contre_indiques_condition"] += 10
    if "effet" in words:
        scores["effets_indesirables_contraceptif"] += 5
    if words & {"indesirable", "secondaire"}:
        scores["effets_indesirables_contraceptif"] += 4
    if words & {"molecule", "composition", "contenir", "composer"}:
        scores["molecules_contraceptif"] += 5
    if words & {"interaction", "interagir"} or "interag" in text:
        scores["interactions_molecule"] += 11
    if profile:
        scores["profils_par_condition"] += 6
        if risk:
            scores["profils_a_risque"] += 12
    if words & {"benefice", "benefique", "avantage", "amelioration"}:
        scores["benefices_contraceptif"] += 10
    if words & {"etude", "source", "preuve", "justifier", "reference", "publication"}:
        scores["sources_preuve"] += 15
    listing = bool(words & {"lister", "liste", "afficher", "montrer"}) or text.startswith(("affiche ", "montre ", "liste "))
    if listing and any(e.get("kind") == "class" for e in entities):
        scores["lister_classe"] += 3
        if not (profile or contraindication or risk or words & {"interaction", "interagir", "effet", "composition", "contenir", "composer"}):
            scores["lister_classe"] += 4
    # A bare named class is also a useful listing request. An arbitrary individual
    # alone stays a keyword search rather than being treated as a class.
    entity_words = set()
    for entity in entities:
        entity_words.update(normalize(entity.get("text", "")).split())
    if entities and all(e.get("kind") == "class" for e in entities):
        if set(normalize(data.text).strip(" ?.! ").split()) <= entity_words:
            scores["lister_classe"] += 3
    return scores


def detect_intent(question: str | PreprocessedQuestion, entities=()) -> str:
    scores = score_intents(question, entities)
    best = max(scores, key=scores.get)
    return best if scores[best] else "recherche_libre"


def detect_risk_kind(question: str) -> str:
    """Select a risk query variant from wording, independent of the schema."""
    text = normalize(question)
    if "oestrog" in text:
        return "oestrogenes"
    if "vasculaire" in text:
        return "vasculaire"
    return "general"


if __name__ == "__main__":
    from .entities import EntityExtractor

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--lexicon", default=None)
    args = parser.parse_args()
    extractor = EntityExtractor(args.lexicon)
    data = preprocess(args.question, nlp=extractor.nlp)
    entities = extractor.extract(args.question)
    print(json.dumps({"intent": detect_intent(data, entities), "entities": entities,
                      "keywords": data.keywords, "scores": score_intents(data, entities)},
                     ensure_ascii=False, indent=2))
