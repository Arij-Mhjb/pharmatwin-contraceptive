"""Ontology-independent French entity matching with spaCy and RapidFuzz.

Run: python -m backend.nlp.entities "Quels effets de la pilule combinee ?"
The sample lexicon is for development only; it is never a production default.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from rapidfuzz.fuzz import ratio
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc

from .preprocess import get_nlp, normalize

SAMPLE_LEXICON = Path(__file__).with_name("lexicon_sample.json")
DEFAULT_LEXICON = Path(__file__).with_name("lexicon.json")
KINDS = {"class", "individual", "objectProperty", "dataProperty"}


class EntityExtractor:
    """Load a replaceable label -> {iri, kind} lexicon once per extractor."""

    def __init__(self, lexicon_path=None, *, threshold: float = 85, nlp=None):
        if not 0 <= threshold <= 100:
            raise ValueError("threshold must be between 0 and 100")
        path = Path(lexicon_path or os.environ.get("PHARMATWIN_LEXICON", DEFAULT_LEXICON))
        self.lexicon = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(self.lexicon, dict):
            raise ValueError("Lexicon must be a JSON object")
        for label, entry in self.lexicon.items():
            if not label.strip() or not isinstance(entry, dict) or entry.get("kind") not in KINDS or not isinstance(entry.get("iri"), str) or not entry["iri"]:
                raise ValueError(f"Invalid lexicon entry: {label!r}")
        self.nlp = nlp if nlp is not None else get_nlp()
        self.threshold = threshold
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="ORTH")
        self.patterns = []
        self.labels = list(self.lexicon)
        for index, (label, doc) in enumerate(zip(self.labels, self.nlp.pipe(self.labels))):
            words = self._words(doc, lemma=True)
            surface = self._words(doc, lemma=False)
            if words:
                self.matcher.add(str(index), [Doc(self.nlp.vocab, words=words)])
                self.patterns.append((label, words, surface))

    @staticmethod
    def _words(doc, *, lemma):
        return [normalize((t.lemma_ or t.text) if lemma else t.text)
                for t in doc if not t.is_space and not t.is_punct]

    def extract(self, question: str) -> list[dict[str, str]]:
        if not isinstance(question, str):
            raise TypeError("question must be a string")
        if not question.strip():
            return []
        doc = self.nlp(question)
        tokens = [t for t in doc if not t.is_space and not t.is_punct]
        if not tokens:
            return []
        lemmas = self._words(doc, lemma=True)
        surfaces = self._words(doc, lemma=False)
        candidates = []
        for match, start, end in self.matcher(Doc(self.nlp.vocab, words=lemmas)):
            label = self.labels[int(self.nlp.vocab.strings[match])]
            candidates.append((100.0, start, end, label))
        # Same-length token windows avoid matching a single generic token to a
        # longer medical phrase. Surface comparison handles missing accents even
        # when they cause the French model to produce a different lemma.
        for label, words, surface in self.patterns:
            size = len(words)
            for start in range(len(tokens) - size + 1):
                end = start + size
                if any(t.is_punct for t in doc[tokens[start].i:tokens[end - 1].i + 1]):
                    continue
                score = max(ratio(" ".join(words), " ".join(lemmas[start:end])),
                            ratio(" ".join(surface), " ".join(surfaces[start:end])))
                # Short acronyms must match exactly, avoiding DIU -> 'du'.
                minimum = 100 if len("".join(surface)) <= 3 else self.threshold
                if score >= minimum:
                    candidates.append((score, start, end, label))
        # Prefer exact matches, then the longest phrase; suppress nested spans.
        selected, occupied = [], set()
        for score, start, end, label in sorted(candidates, key=lambda c: (-c[0], -(c[2]-c[1]), c[1], c[3])):
            positions = set(range(start, end))
            if positions & occupied:
                continue
            occupied.update(positions)
            selected.append((start, end, label))
        return [
            {"text": question[tokens[start].idx:tokens[end-1].idx + len(tokens[end-1])],
             "label": label, **self.lexicon[label]}
            for start, end, label in sorted(selected)
        ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--lexicon", type=Path, default=None,
                        help="Defaults to PHARMATWIN_LEXICON or corrected lexicon.json")
    args = parser.parse_args()
    print(json.dumps(EntityExtractor(args.lexicon).extract(args.question), ensure_ascii=False, indent=2))
