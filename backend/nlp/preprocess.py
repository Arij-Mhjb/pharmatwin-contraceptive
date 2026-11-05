"""French spaCy preprocessing, with no ontology-specific vocabulary.

Install spaCy and its French model before calling preprocess(). The pipeline is
loaded lazily once per process so importing this module does not load the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING
import unicodedata

if TYPE_CHECKING:
    from spacy.language import Language
    from spacy.tokens import Doc

DEFAULT_MODEL = "fr_core_news_sm"


def normalize(text: str) -> str:
    """Lowercase, fold accents/ligatures, and collapse whitespace.

    Use on lemmas and comparison keys, not before spaCy analysis: the model
    needs original accents, and original text is needed for entity offsets.
    """
    text = text.lower().replace("œ", "oe").replace("æ", "ae")
    text = text.replace("’", "'").replace("‘", "'")
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    return " ".join(text.split())


@lru_cache(maxsize=2)
def get_nlp(model: str = DEFAULT_MODEL) -> Language:
    """Return a cached pipeline with tagger/morphology and lemmas enabled."""
    try:
        import spacy
    except ImportError as exc:
        raise RuntimeError(
            'spaCy is required. Run: python -m pip install "spacy>=3.8,<4"'
        ) from exc
    try:
        return spacy.load(model, disable=["parser", "ner"])
    except OSError as exc:
        raise RuntimeError(
            f"French model {model!r} is unavailable. "
            f"Run: python -m spacy download {model}"
        ) from exc


@dataclass(frozen=True)
class PreprocessedQuestion:
    """Both full lemma sequence for matching and keywords for intent scoring."""

    text: str
    doc: Doc
    tokens: tuple[str, ...]
    lemmas: tuple[str, ...]
    keywords: tuple[str, ...]


def preprocess(
    question: str, *, nlp: Language | None = None, model: str = DEFAULT_MODEL
) -> PreprocessedQuestion:
    """Analyze original French text and normalize resulting token lemmas.

    Full lemmas retain stop words for multiword entity matching. Keywords omit
    stop words except negation, which can affect a question's meaning. Punctuation
    and whitespace are excluded from both sequences. Inject a pipeline with
    ``nlp=`` to share it with PhraseMatcher or to test this function.
    """
    if not isinstance(question, str):
        raise TypeError("question must be a string")
    pipeline = nlp if nlp is not None else get_nlp(model)
    doc = pipeline(question)
    tokens: list[str] = []
    lemmas: list[str] = []
    keywords: list[str] = []
    for token in doc:
        if token.is_space or token.is_punct:
            continue
        lemma = normalize(token.lemma_ or token.text)
        tokens.append(token.text)
        lemmas.append(lemma)
        if not token.is_stop or lemma in {"ne", "n'", "pas", "sans", "ni", "non"}:
            keywords.append(lemma)
    return PreprocessedQuestion(question, doc, tuple(tokens), tuple(lemmas), tuple(keywords))
