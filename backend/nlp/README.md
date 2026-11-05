# PharmaTwin NLP — current state

Implemented: ontology bindings, lexicon generation, French preprocessing,
entity detection, intent scoring, all 11 SPARQL templates and the stable
translator interface. Tasks 1–8, including the French translator regression
suite, are implemented. The frontend is still pending. No LLM API is used.

Tools to name in the presentation: Python, spaCy (`fr_core_news_sm`), spaCy
PhraseMatcher, RapidFuzz, RDFLib. Scoring rules operate on French lemmas and
entity kinds. Scores are rule weights, not probabilities or confidence values.

## Setup (from the repository root, PowerShell)

```powershell
python -m pip install -r backend/nlp/requirements.txt
python -m spacy download fr_core_news_sm
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

The current suite has 13 entity question cases, 30 intent question cases,
a custom-lexicon replacement check, and the task 8 translator tests below.
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
rows.

## Translator and FastAPI integration (task 7)

```python
from backend.nlp.translator import translate

response = translate("Quels sont les effets indésirables de la pilule combinée ?")
# Exactly three keys: intent (str), entities (list), sparql (str).
# Your FastAPI handler executes response["sparql"] and adds its results.
```

The translator performs no HTTP calls and no query execution. It lazily caches
the NLP model and lexicon for repeated requests. Restart the backend after
regenerating a lexicon at the same path. It reads `PHARMATWIN_LEXICON` before
loading an extractor, with corrected `lexicon.json` as the default.

See the JSON response:

```powershell
python -X utf8 -m backend.nlp.translator "Quelles molécules interagissent avec la Rifampicine ?"
```

Optional local query execution for development:

```powershell
python -X utf8 -m backend.nlp.translator "Quelles molécules contient la pilule combinée ?" --ontology "C:\Users\arijm\Downloads\PharmaTwin_Contraceptive (2).owl"
```

Unknown questions use label keyword searching, with case/accent normalization
and escaped literals. Non-string and empty inputs return an empty search query.
Questions are limited to their first 4,000 characters. Missing model/lexicon,
invalid lexical IRIs or query-building errors are logged and produce a keyword
fallback with empty entities; if even that fails, a constant empty SELECT query
is returned. No stack traces are put in the response. Infrastructure failures
in optional CLI file reading/query execution remain visible to the developer.

## French question regression suite (task 8)

```powershell
python -X utf8 -m unittest discover -s backend/nlp/tests -p test_translator.py -v
```

This runs 49 separately named tests: 38 French questions covering all 11 intents,
four coverage/query-execution checks, and seven failure/contract tests. Each
French question checks its expected intent, required entity labels, response
format, SPARQL syntax, ordering/limit and absence of placeholder bindings.
Expected labels are a subset: generic nouns may also be recognized as entities.
Case-specific descriptions display the French question in verbose output.

The corpus includes the professor's six example questions, missing accents,
typos (`migrain avec aura`, `rifampicin`), SOPK, risk and alert variants, evidence,
class listing, and unknown vocabulary. It calls the public `translate(question)`
function using the corrected generated lexicon rather than testing only intent
classification. The cases are in `FRENCH_CASES` in `tests/test_translator.py`.

Query-execution checks use independent in-memory RDF data to verify filtering,
interaction direction, and keyword results. Failure tests cover missing
model/lexicon, template failure, empty/invalid inputs and emergency fallback.
These tests do not need FastAPI, an internet connection, or the local OWL file;
they need the installed French spaCy model and committed corrected lexicon.
They do not establish medical correctness or general OWL inference.

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
