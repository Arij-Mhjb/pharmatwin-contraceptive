# Patient-centered direction and integration review

## Live-integration update

The patient-first teaching scenario has since been implemented locally. See
PATIENT_JOURNEY.md: profile/history/preferences, graph-backed comparisons,
current contraception, observations, saved dated reports and export. It reuses
the existing backend models and vocabulary. Formal ontology enrichment and
clinical validation remain future work; preference fit is not medical clearance.

The integration differences listed below are now resolved in the local changes:
entity-list responses (including normalization of the optional fallback), search
response unwrapping, complete profile records with conditions/pressures and
resource IDs, condition selection by ontology ID, partial-update preservation,
aligned form limits, CORS for port 3100, and named dataset parameters for ask.
Ontology example profiles are read-only; user profiles support CRUD. Optional
Fuseki authentication is configured through ignored local environment settings.

Verification: 85 backend/NLP tests passed, frontend API tests/typecheck and
production build passed, the real Fuseki smoke test passed, and browser API mode
returned three actual molecule results. A uniquely named disposable profile was
created, updated with condition/pressure preservation, and removed in live tests.
The matching engine, preference/history/symptom extensions and saved reports
below are still pending. The original findings are retained as review history.

Reviewed 2026-11-04 against GitHub main commit 433fb28, which already merges
the colleague's feature/complete-semantic-backend branch (PR #1). The local
`.publish-repo` checkout was fast-forwarded to that commit without conflicts.
The initial review did not change colleague-owned code or the ontology. The
subsequently authorized integration fixes update backend contracts and frontend
adapters; they do not alter the ontology or add personalized recommendations.

## Product objective

The main journey should be: describe my situation -> compare contraceptive
options -> understand why each option is listed/flagged -> save a dated report
-> record changes and follow up. Natural-language ontology exploration becomes
a supporting feature, not the home page's primary task.

Offer options to discuss with a qualified clinician, not an automatic diagnosis
or prescription or a claim of a medically best pill. Unknown medical facts must
stay unknown; an absent contraindication triple is not evidence of eligibility.
Symptoms reported during use must not automatically be attributed to the method.

## What exists

The pushed Turtle graph is isomorphic to the user's corrected OWL file: 1,228
triples, 45 named classes, 22 object properties, 24 data properties, 80 named
individuals. It already includes clinical conditions, risk factors,
contraindication records, evidence sources, molecules, interactions, benefits,
adverse effects, current contraceptive links and basic follow-up observations.
Irregular cycles are represented as a clinical condition. Heavy bleeding is
represented as an adverse-effect individual, not as a complete dated patient
symptom-history model. Existing observations use basic type/value/cycle fields.

Backend routes already include ask, profile CRUD, contraceptive list/detail,
keyword/semantic search, ontology access and health. Its reasoner adds selected
profile class assertions. There is no personalized recommendation endpoint,
preference-ranking engine, symptom journal API or saved report API in this commit.

## Integration differences requiring resolution

1. `backend/models/schemas.py`: AskResponse.entities is dict. Our translator and
   frontend use a list of entity objects. Validating our response against this
   model fails with Pydantic's dict_type error. The route currently invokes our
   translator first, so the fallback AI's different entity envelope does not
   resolve this mismatch.
2. `backend/routes/search.py`: response is `{query, results}`; frontend currently
   expects a bare array. Adapt the frontend boundary.
3. Profile creation requires `identifiant`. Condition inputs are ontology local
   identifiers, not arbitrary human-readable strings. The UI currently supplies
   labels. A label/identifier picker must replace the comma-separated input.
4. Profile listing returns iri, identifiant, age, imc and fume, without conditions
   or blood pressures. The current edit modal must not overwrite missing fields
   with empty values. Add a complete detail response or extend the list payload.
5. Create/update return acknowledgements rather than full profiles. Adapt frontend
   types and refresh behavior. IDs used for updates must identify the resource,
   which is not necessarily identical to its human-readable identifiant.
6. API question validation is 3–500 characters, while the UI/translator currently
   permit up to 4,000. Profile age/IMC bounds differ too. Align UI validation.
7. Default backend CORS permits localhost:3000; this Windows preview uses
   127.0.0.1:3100. Configure the matching origin before live integration.
8. Our NLP queries do not specify named FROM graphs. The backend loads ontology,
   profiles and inferred facts into separate graphs. Verify or configure a union
   default dataset, or add explicit graph selection at the query boundary.
   Otherwise correct queries may return empty results. This was identified by
   code inspection, not a live Fuseki test.

## Ontology extensions to discuss in Protégé

These are proposed concepts, not claims that those terms exist today. Final
IRIs/class/property bindings must remain in ontology_map.py and generated lexicon.

- Preferences/goals: pill-only versus broader methods, hormonal preference,
  daily routine constraints, bleeding goals and ranked priorities. Distinguish
  preference from a medical contraindication.
- Contraceptive-use episode: method, start/end dates, discontinuation reason,
  reported tolerance and adherence, linked to the simulated profile. Preserve
  past episodes rather than replacing a single current-method link.
- Symptom observation: reported symptom, onset/date, duration, severity, cycle,
  optional unit/value and reporting source. Separate self-report from confirmed
  clinical condition. Sleep problems/fatigue can be recorded without inferring
  a diagnosis or an unverified contraceptive relationship.
- Assessment/evaluation: profile snapshot, candidate method, eligibility state,
  matched medical rules, unmet data requirements, preference fit and explanation.
  Preference points must not offset a medically unsuitable option.
- Evidence-backed rule: applicability conditions, method, guideline source and
  version, review status, and eligibility category where supported. A source link
  alone does not establish that a rule was validated for this situation.
- Report: date, assessment/profile snapshot, ontology/rules version, considered
  options, exclusions/concerns, source references and unresolved questions.
  Reports must be immutable snapshots; later updates create a new report.

Some operational details can live in application storage, while the ontology
defines their meaning and evidence relationships. Not every UI field needs a
new OWL class. The current demo ontology is not a complete prescribing database.

## Matching and presentation behavior

First evaluate medical eligibility using validated, applicable rules. Clearly
separate insufficient information, methods needing clinical review, and methods
with a supported contraindication. Only then compare preferences among options
that can be discussed. Explain ties and gaps instead of inventing a unique best
match or a numerical probability of safety. Do not average MEC categories.

Each report should show: entered data and unknowns; why each option is included;
flags and their reasons; preference trade-offs; potential benefits/side effects;
evidence links; rule/data version; and information to discuss with a clinician.
For current contraception show associated effects separately from the user's
observed symptoms. Reporting a symptom alone does not establish causality.

Proposed patient navigation: Mon profil, Mes options, Ma contraception,
Mon suivi, Mes bilans. Keep the technical SPARQL explorer as an advanced view.

## Suggested delivery order

1. Resolve the existing API contract and dataset differences with the colleague.
2. Agree on the minimal profile, preference, use-history and symptom concepts.
3. Implement and test a deterministic evidence-backed assessment API, including
   missing-data cases, contraindications and explanations. No LLM is needed.
4. Build the patient-centered flow against that API, with explicitly simulated
   results until the real engine is connected.
5. Add saved assessment snapshots and follow-up changes, then integration tests
   running actual translator -> FastAPI response validation -> graph execution.

Within current ownership, frontend and backend/nlp changes are ours; assessment
routes/storage and ontology editing need coordination with their owners.

## Clinical design references

- WHO Medical eligibility criteria for contraceptive use, sixth edition (2025):
  https://www.who.int/publications/i/item/9789240115583
- CDC U.S. MEC (2024), including person-centered contraceptive counseling:
  https://www.cdc.gov/contraception/hcp/usmec/index.html
- CDC U.S. Selected Practice Recommendations (2024), reproductive autonomy and
  individual preferences: https://www.cdc.gov/mmwr/volumes/73/rr/rr7303a1.htm/

These support the eligibility/preference distinction; proposed scores, fields
and endpoints above are product recommendations, not validated clinical rules.
