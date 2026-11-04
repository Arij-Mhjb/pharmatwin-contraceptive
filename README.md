# PharmaTwin Contraceptive — Semantic Backend

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
git checkout feature/complete-semantic-backend
docker compose up -d fuseki
```

Create the environment (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m spacy download fr_core_news_sm
```

Linux/macOS activation is `source .venv/bin/activate`.

Load the ontology, download the embedding model once, then run:

```bash
PYTHONPATH=. python backend/scripts/load_ontology.py
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
python -m uvicorn backend.app:app --reload --port 8000
```

On Windows, set `$env:PYTHONPATH='.'` before script commands. To enforce offline inference later, set `PHARMATWIN_OFFLINE_MODELS=true`. A predownloaded directory can be selected with `PHARMATWIN_MODEL_PATH`.

## URLs

- Swagger: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/health>
- Profiles: <http://localhost:8000/api/profils>
- Ontology stats: <http://localhost:8000/api/ontology/stats>
- Contraceptives: <http://localhost:8000/api/contraceptifs>
- Keyword search: <http://localhost:8000/api/search?q=pilule>
- Semantic search: <http://localhost:8000/api/search/semantic?q=migraine>

Example question:

```bash
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question":"Quels profils sont en alerte pour les œstrogènes ?"}'
```

The response preserves the frontend contract: `intent`, `entities`, `sparql`, `results`.

## Validation and tests

```bash
PYTHONPATH=. python backend/scripts/inspect_ontology.py
PYTHONPATH=. python backend/scripts/verify_reasoning.py
PYTHONPATH=. python -m pytest backend/tests -v
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
