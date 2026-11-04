"""Stable FastAPI integration: ``from backend.nlp.translator import translate``.

This function creates SPARQL; it never executes queries or calls an LLM/API.
The corrected lexicon is the default. Set PHARMATWIN_LEXICON to replace it.
"""

from __future__ import annotations

from functools import lru_cache
import logging
import os
import re

from .preprocess import normalize

logger = logging.getLogger(__name__)

# No ontology bindings or data are needed for this last-resort empty query.
EMPTY_QUERY = ("SELECT DISTINCT ?result ?label WHERE { FILTER(false) }\n"
               "ORDER BY STR(?label) STR(?result)\nLIMIT 50")


@lru_cache(maxsize=4)
def _extractor(lexicon_path: str | None):
    # Lazy import permits keyword fallback even if spaCy/RapidFuzz is absent.
    from .entities import EntityExtractor
    return EntityExtractor(lexicon_path)


def _keywords(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[^\W_]+", normalize(text), re.UNICODE)))[:12]


def translate(question) -> dict:
    """Return exactly {intent, entities, sparql}, including on recoverable errors.

    Non-string/empty inputs produce an empty keyword query. Input is limited to
    4,000 characters to bound NLP work. Extractors/models are cached; restart the
    backend (or clear _extractor.cache_clear()) after replacing a lexicon file.
    Runtime errors are logged; they are not returned as user-facing stack traces.
    """
    text = question[:4000].strip() if isinstance(question, str) else ""
    intent, entities = "recherche_libre", []
    keywords = _keywords(text)
    try:
        from .templates import build_query
        if text:
            from .intent import detect_intent, detect_risk_kind
            from .preprocess import preprocess
            extractor = _extractor(os.environ.get("PHARMATWIN_LEXICON"))
            data = preprocess(text, nlp=extractor.nlp)
            entities = extractor.extract(text)
            intent = detect_intent(data, entities)
            # Preserve surface words as well as lemmas for lexical searching.
            keywords = list(dict.fromkeys((*data.keywords, *_keywords(text))))[:12]
            if intent != "profils_a_risque" and not any(
                entity.get("kind") in {"class", "individual"} for entity in entities
            ):
                intent = "recherche_libre"
            sparql = build_query(intent, entities, keywords=keywords,
                                 risk_kind=detect_risk_kind(text))
        else:
            sparql = build_query(intent, keywords=())
        return {"intent": intent, "entities": entities, "sparql": sparql}
    except Exception:
        logger.warning("NLP translation failed; returning keyword fallback", exc_info=True)
        try:
            from .templates import recherche_libre
            sparql = recherche_libre(keywords=keywords)
        except Exception:
            logger.error("Keyword query unavailable; returning empty query", exc_info=True)
            sparql = EMPTY_QUERY
        return {"intent": "recherche_libre", "entities": [], "sparql": sparql}


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Translate a French question into SPARQL")
    parser.add_argument("question")
    parser.add_argument("--ontology", help="Optionally run the query against a local OWL/TTL file")
    args = parser.parse_args()
    response = translate(args.question)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    if args.ontology:
        from rdflib import Graph
        rows = list(Graph().parse(args.ontology).query(response["sparql"]))
        print(f"\nResults: {len(rows)}")
        for row in rows:
            print(" | ".join(str(value) if value is not None else "" for value in row))
