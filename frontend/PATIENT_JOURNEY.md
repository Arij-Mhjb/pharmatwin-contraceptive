# Patient-first PharmaTwin scenario

The home page is now the client workspace, not the technical ontology explorer.
This is a local, unauthenticated teaching prototype for fictitious profiles;
the browser profile selector is not a secure login or a private multi-user account.

## Try the complete scenario

Run the existing local FastAPI/Fuseki backend and frontend in API mode, as in
README.md. Open http://127.0.0.1:3100/.

1. Choose a new local profile, enter a fictitious pseudonym, age, IMC, smoking,
   optional blood pressure and known conditions.
2. Select current contraception, medications, and past contraceptive experiences.
   Treatments outside the graph can be recorded as text, but are explicitly
   marked unevaluated.
3. Select preferred forms, hormonal preference, desired documented benefits and
   adverse effects that matter to the scenario. Save and compare.
4. Mes options shows percentages, criterion explanations, information coverage,
   contraindication/interaction flags, and expandable composition/effects/sources.
5. Ma contraception shows the current method's information and model flags. Its
   question link opens the existing French NLP explorer with a prefilled question.
6. Mon suivi records dated symptoms, severity and notes (sleep, fatigue, heavy or
   irregular periods, mood, or another observation). Each saved entry triggers
   a new assessment/report. It does not automatically establish a diagnosis or
   attribute a symptom to contraception.
7. Mes bilans lets the client select earlier reports, print/save through the
   browser's PDF dialog, or download a JSON snapshot. Updating the profile or
   adding an observation never overwrites old reports.

The fictitious Lina profile used in browser QA has migraine with aura, a preferred
progestative pill/hormonal form, concern about heavy bleeding and a reported
negative past copper-IUD experience. The model flags its combined-pill examples,
while explaining the distinct preference scores and missing information for
other options. This is a software test scenario, not a clinical recommendation.

## Existing backend components reused

- `ProfilCreate`, `ProfilUpdate`, existing profile CRUD and Fuseki named graphs.
- Existing profile-class reasoning after profile creation/updates.
- `OntologyService` and the corrected ontology for candidates, labels,
  compositions, benefits, adverse effects, contraindications and sources.
- `backend/nlp/translator.py`, spaCy `fr_core_news_md`, PhraseMatcher,
  RapidFuzz, intent rules and RDFLib/SPARQL for the question explorer.

The optional embedding similarity model is not used as a medical matching
percentage. Sentence similarity is not contraceptive eligibility. No LLM API
is used. New application models compose the existing clinical profile model
with preferences, past use and self-reported observations.

## What the percentage means

It measures preference fit only: satisfied criteria / documented criteria × 100.
Each selected form/hormone preference, desired benefit, adverse-effect concern,
and applicable past experience contributes one criterion. Unknown graph links
are excluded from the denominator; coverage shows known / total criteria.
No selected criteria means no percentage. Ties are valid; the application does
not invent a uniquely best option.

An explicit model contraindication or interaction suppresses the percentage and
places that method after unflagged candidates. Preferences cannot cancel a
clinical flag. An unflagged method is still labelled medically undetermined.
No probability of safety, effectiveness, tolerability, or individual adverse
effects is estimated. The graph's clinical coverage is incomplete and its
knowledge is explicitly pedagogical, not clinically validated.

Clinical design background (not validation of this software's scoring):
https://www.cdc.gov/contraception/hcp/usmec/how-to-use.html
https://www.who.int/publications/i/item/9789240115583

## Data and ontology boundary

Clinical conditions remain in the existing user-profile RDF graph. Current
contraception uses the existing current-method property. Journal entries use
the existing profile-to-observation relation, Observation class and type/value
fields. All bindings are in `backend/nlp/ontology_map.py`.

Application preferences, past-use episodes and complete dated observations are
validated by Pydantic and persisted in SQLite at `backend/data/patient.sqlite3`.
Reports contain immutable JSON snapshots, candidate explanations, evidence,
display labels, UTC timestamps, an ontology SHA-256 and a rules version. The
database is ignored by Git. No new clinical ontology axiom was invented and the
corrected OWL/Turtle source was not modified.

Further ontology enrichment can add formal preference/use-history/date concepts
and validated eligibility rules. Missing age/IMC/blood-pressure/smoking rules
are disclosed rather than inferred from unverified thresholds.

## New API endpoints

- `GET /api/patient/catalog`
- `GET|POST /api/patient/profiles`
- `GET|PUT /api/patient/profiles/{id}`
- `POST /api/patient/profiles/{id}/symptoms`
- `POST /api/patient/profiles/{id}/assessments`
- `GET /api/patient/profiles/{id}/reports`

The workspace requires the real backend. Mock mode continues to support the
technical explorer/search/profile demo, but does not fabricate personal scores.

## Verification

```powershell
# From the combined checkout:
.\.venv\Scripts\python.exe -m pytest backend/tests backend/nlp/tests -q
# From frontend:
npm test
npm run build
```

Patient tests verify contraindications overriding preferences, exact preference
arithmetic, unknown data, interactions (including no self-interaction), negative
past experience, persisted observations and immutable report snapshots. They
reuse the actual API routes and SPARQL against isolated RDF named graphs.
