# PharmaTwin NLP — current state

Implemented: ontology bindings, lexicon generation, French preprocessing,
entity detection and intent scoring. Translator, SPARQL templates and frontend
are still pending. No LLM API is used.

Tools to name in the presentation: Python, spaCy (`fr_core_news_md`), spaCy
PhraseMatcher, RapidFuzz, RDFLib. Scoring rules operate on French lemmas and
entity kinds. Scores are rule weights, not probabilities or confidence values.

## Setup (from the repository root, PowerShell)

```powershell
python -m pip install -r backend/nlp/requirements.txt
python -m spacy download fr_core_news_md
```

## See results

These commands print JSON in the terminal. They do not execute SPARQL yet.

```powershell
python -X utf8 -m backend.nlp.entities "Quels effets de la pilule combinee avec une migrain avec aura ?"
python -X utf8 -m backend.nlp.intent "Quels contraceptifs sont contre-indiqués avec une migraine avec aura ?"
python -X utf8 -m backend.nlp.intent "Quels profils sont en alerte pour les œstrogènes ?"
```

The default is the corrected `lexicon.json`; an explicit `--lexicon` argument
overrides it. `PHARMATWIN_LEXICON` can also configure the default path.
To use development placeholders intentionally:

```powershell
python -X utf8 -m backend.nlp.entities "pilule combinée" --lexicon backend/nlp/lexicon_sample.json
```

## Check behavior

```powershell
python -X utf8 -m unittest discover -s backend/nlp/tests -v
```

The current suite has 13 entity question cases, 30 intent question cases, and
a custom-lexicon replacement check. It is not the pending translator test suite.

## Regenerate the lexicon after ontology changes

```powershell
python -X utf8 -m backend.nlp.build_lexicon "C:\Users\arijm\Downloads\PharmaTwin_Contraceptive (2).owl"
```

RDF/XML `.owl` and Turtle `.ttl` are supported. French and untagged `rdfs:label`
values are included, as are uppercase parenthesized acronym aliases derived
from those labels. Anonymous OWL expressions are skipped. Missing labels are
reported; conflicting labels stop generation instead of silently overwriting.
Class/property bindings still need verification in `ontology_map.py` after each
schema change. Generated lexical entries contain labels, IRIs and RDF kinds,
not medical-role annotations. Sample IRIs are only development data.

The ontology identifier is `https://pharmatwin.ai/contraceptive`; terms in the
provided corrected file use the namespace ending in `#`. A dereferenceable web
page is not required for the local OWL-based workflow.

Two unused property placeholders remain in `ontology_map.py` because the
corrected file does not declare them. Future risk queries must use the actual
profile classes and their OWL definitions, not those placeholder relationships.
