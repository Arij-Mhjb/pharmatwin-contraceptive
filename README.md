# PharmaTwin Contraceptive — Secure academic platform

Functional FastAPI backend for an ESPRIT Semantic Web project combining the supplied OWL 2 ontology, Apache Jena Fuseki/TDB2, controlled SPARQL, local multilingual embeddings and French NLP. It is an academic knowledge-engineering prototype, **not** a diagnosis, prescription, or personalized medical recommendation system.

## What is implemented

- Original RDF/XML preserved and graph-equivalent Turtle export (1,228 triples)
- Persistent Fuseki dataset with separate ontology, profiles and inferred graphs
- Typed profile CRUD with safe SPARQL updates and condition validation
- Ontology, contraceptive and Unicode keyword-search APIs
- Local Sentence Transformers semantic search and ontology entity linking
- spaCy French preprocessing and embedding-based intent recognition
- Controlled question-to-SPARQL templates; no arbitrary generated updates
- Optional `backend.nlp.translator.translate(question)` integration without modifying `backend/nlp/`
- Dynamic refresh for SOPK, endometriosis and estrogen-alert classifications
- Unit tests, security tests, Docker Compose and GitHub Actions
- Public landing page, real sign-up/sign-in and guided onboarding
- Opaque database sessions, HttpOnly cookies, CSRF protection and scrypt password hashing
- User-owned simulated profiles, immutable reports and role-based administration
- Account security settings and a unified authenticated Next.js 16 dashboard
- Advanced client cockpit with journey metrics, recent reports and quick actions
- Admin control center with platform KPIs, audit activity and recent scenarios
- Persistent profile-photo upload (JPEG, PNG or WebP, validated and size-limited)
- Responsive editorial design with attributed Unsplash photography

## Architecture

```text
French question → spaCy → MiniLM embeddings → intent/entity linking
                → validated SPARQL template → Fuseki → flat JSON
```

OWL reasoning supplies logical class membership. ML supplies similarity rankings and intent/entity candidates. SPARQL retrieves or mutates explicitly permitted RDF data. These mechanisms are deliberately distinct.

## Quick start

```bash
git clone https://github.com/Arij-Mhjb/pharmatwin-contraceptive.git
cd pharmatwin-contraceptive
docker compose up --build -d
```

Create the environment (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/nlp/requirements.txt
python -m spacy download fr_core_news_sm
```

Linux/macOS activation is `source .venv/bin/activate`.

Load the ontology, download the embedding model once, then run:

```bash
PYTHONPATH=. python backend/scripts/load_ontology.py
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
python -m uvicorn backend.app:app --reload --port 8000
```

For the Docker workflow, `docker compose up --build` performs these initialization
steps automatically: it waits for Fuseki, persists the embedding model in a named
volume, imports the ontology idempotently, and starts the API in offline-model mode.
Set `FUSEKI_ADMIN_PASSWORD` before launch to replace the development password.

Set `PHARMATWIN_ADMIN_EMAIL` and `PHARMATWIN_ADMIN_PASSWORD` to replace the
local bootstrap administrator. A production deployment must also set
`PHARMATWIN_COOKIE_SECURE=true` and expose the platform through HTTPS.

## Test accounts and end-to-end journey

Docker Compose creates this **local development-only** administrator by default:

```text
Email: admin@pharmatwin.local
Password: DemoAdmin2026!
```

To exercise the full journey from <http://localhost:3001>:

1. Select **Créer un compte** and use an unused test address such as `etudiant@example.test`.
2. Use a password of at least 10 characters with uppercase, lowercase and a digit, for example `Parcours2026!`.
3. Accept the academic-use onboarding and enter the dashboard.
4. Create a fictitious scenario. `Migraine avec aura` plus a preference for `pilule combinée` demonstrates that a clinical flag cannot be hidden by the preference score.
5. Save it to create a report, add a follow-up observation, create a second report, then compare the immutable dated snapshots.
6. Ask `Quels sont les effets indésirables de la pilule combinée ?` and search for `migraine`.
7. Open **Compte & sécurité** to renew the password and revoke all sessions.
8. Sign in with the administrator above to inspect RBAC and the technical profile workspace.

Only fictitious information should be entered. This is an academic platform, not a medical device.

On Windows, set `$env:PYTHONPATH='.'` before script commands. To enforce offline inference later, set `PHARMATWIN_OFFLINE_MODELS=true`. A predownloaded directory can be selected with `PHARMATWIN_MODEL_PATH`.

## URLs

- Swagger: <http://localhost:8000/docs>
- Client web: <http://localhost:3001>
- Health: <http://localhost:8000/api/health>
- Authentication session: <http://localhost:8000/api/auth/session>
- Profiles (administrator): <http://localhost:8000/api/profils>
- Ontology stats: <http://localhost:8000/api/ontology/stats>
- Contraceptives: <http://localhost:8000/api/contraceptifs>
- Keyword search: <http://localhost:8000/api/search?q=pilule>
- Semantic search: <http://localhost:8000/api/search/semantic?q=migraine>

Authenticated API calls require the database session cookie. Browser mutations
also send the CSRF cookie value in the `X-CSRF-Token` header. Use the web client
or Swagger UI for interactive testing.

Example question after signing in:

```bash
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question":"Quels profils sont en alerte pour les œstrogènes ?"}'
```

The response preserves the frontend contract: `intent`, `entities`, `sparql`, `results`.

## Validation and tests

```bash
PYTHONPATH=. python backend/scripts/inspect_ontology.py
PYTHONPATH=. python backend/scripts/verify_reasoning.py
PYTHONPATH=. python -m pytest backend -v
PYTHONPATH=. python backend/ai/evaluation.py
```

CI uses lightweight unit tests and deliberately avoids redownloading large model weights. The model evaluation command executes the real local model and reports measured predictions and latency.

## Reasoning lifecycle

The original ontology schema is immutable at runtime. Profile CRUD writes only to the profile graph. On create/update, the service deletes the affected inferred assertions and rematerializes only the consequences faithfully represented by the supplied equivalent-class axioms. HermiT in Protégé remains the reference for full OWL 2 DL validation and export. See [reasoning](docs/reasoning.md).

## Repository map

```text
ontology/          RDF/XML source, Turtle and inferred export
backend/routes/    FastAPI routes
backend/services/  ontology, NLP adapter, templates and reasoning
backend/ai/        local model loading, intent, linking and index
backend/scripts/   conversion, inspection, import and verification
backend/tests/     unit/API/security tests
docs/              inventory, queries, AI, reasoning and API docs
```

The teammate-owned `backend/nlp/` directory is not created, changed or overwritten by this implementation. If supplied later, its public `translate(question: str) -> dict` interface has priority; validated local AI is the fallback.

## Troubleshooting

- `503 Fuseki query failed`: verify `docker compose ps` and the dataset URL.
- Model unavailable: run the one-time Sentence Transformers download command.
- spaCy model missing: run `python -m spacy download fr_core_news_sm`; the application can tokenize with a blank French pipeline but full lemmatization requires the model.
- Re-import is safe: the Graph Store PUT replaces only the configured ontology graph.

Further details: [ontology inventory](docs/ontology_inventory.md), [API](docs/api.md), [AI models](docs/ai_models.md), [SPARQL](docs/queries.md), and [setup](docs/setup.md).
