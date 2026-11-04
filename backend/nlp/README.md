# PharmaTwin NLP — current state

Implemented: ontology bindings, lexicon generation, French preprocessing,
entity detection, intent scoring and all 11 SPARQL templates. Translator and
frontend are still pending. No LLM API is used.

Tools to name in the presentation: Python, spaCy (`fr_core_news_md`), spaCy
PhraseMatcher, RapidFuzz, RDFLib. Scoring rules operate on French lemmas and
entity kinds. Scores are rule weights, not probabilities or confidence values.

## Setup (from the repository root, PowerShell)

```powershell
python -m pip install -r backend/nlp/requirements.txt
python -m spacy download fr_core_news_md
```

## See results

These commands print JSON in the terminal.

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
SPARQL tests also verify actual query results on an independent test graph,
subclasses, inverse assertions, risk definitions, escaped inputs and binding
replacement.

## Preview and run generated SPARQL (task 6)

Print a query:

```powershell
python -X utf8 -m backend.nlp.templates "Quelles molécules contient la pilule combinée ?"
```

Print the query and execute it on the corrected local OWL file:

```powershell
python -X utf8 -m backend.nlp.templates "Quelles molécules contient la pilule combinée ?" --ontology "C:\Users\arijm\Downloads\PharmaTwin_Contraceptive (2).owl"
```

All queries use SELECT DISTINCT, prefixes, ORDER BY and LIMIT (default 50,
maximum 500). RDFLib escapes keyword literals and IRI inputs are validated.
Queries support explicit subclass paths, the known inverse CI/molecule links,
interaction records, direct interactions, and evidence links. Known pill-form
values in `ontology_map.py` cover examples not typed with their specific pill
class. This is a dataset mapping, not a general OWL reasoner. Vascular risk
uses explicit membership; general risk and oestrogen alerts also use their
verified condition-based definitions. Arbitrary OWL inference is not performed.
The CLI selects one risk category from the question; Python callers can pass
`risk_kind="general"`, `"vasculaire"` or `"oestrogenes"` to `build_query`.

Detected targets are combined as alternatives (OR), not as a requirement that
all conditions apply. A selected intent with no target can return all matching
resources up to the limit. The keyword fallback with no keywords returns no
rows. Task 7 will provide the teammate's stable `translate(question)` interface.

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
