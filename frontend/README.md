# PharmaTwin front-end

Next.js App Router, TypeScript, Tailwind CSS. All application components are
client components. Static export (`output: 'export'`) means no runtime SSR,
authentication, server actions or Next.js API handlers are needed.

## Run (PowerShell, from the project root)

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open http://127.0.0.1:3100. Keep the terminal running; Ctrl+C stops the app.
The copy command selects live API mode; skip it if `.env.local` is
already configured as desired. Node 22 is supported in this workspace.

- `/`: client profile, preferences, explained comparisons, current contraception,
  follow-up journal and immutable printable/downloadable reports.
- `/explorer`: ask a question or click one of six examples; inspect intent,
  entity badges, collapsible SPARQL and the results table.
- `/profils`: filter profiles by age/smoking, create/edit with a modal, and
  confirm deletion. Mock records persist in browser localStorage across reloads.
- `/search`: keyword search with loading, empty and error states.

See PATIENT_JOURNEY.md for the complete client scenario, score definition,
backend model reuse, storage and current ontology limitations.

## Demo and real backend

The supplied `.env.local` starts with:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MOCK=false
```

Setting `NEXT_PUBLIC_MOCK=true` enables the technical UI demonstration: intent, entities, SPARQL and results are fake.
It does not invoke Python or reproduce all NLP behavior. No ontology IRIs are
embedded in the frontend; demo identifiers use `urn:mock:`. Only fictitious
profiles should be entered. Browser storage is not a shared database.

The patient workspace requires `NEXT_PUBLIC_MOCK=false`. After changing it restart the
dev server (rebuild a static export). The FastAPI backend must allow CORS for
`http://127.0.0.1:3100` and/or `http://localhost:3100`, including JSON requests,
POST, PUT, DELETE and preflight OPTIONS. The integrated backend now permits
those local origins by default. Network/HTTP errors appear in the interface.

All requests are centralized in `lib/api.ts`:

- `POST /api/ask`: `{question}` -> `{intent, entities, sparql, results}`.
  `results` is an array of objects; columns derive from its keys. Entity labels
  are optional, with `text` as a fallback. RDF binding `{value: ...}` cells are
  displayed as values.
- `GET /api/profils?age_min=&age_max=&fume=` -> array of profiles.
- `POST /api/profils` and `PUT /api/profils/{id}` use profile input JSON.
- `DELETE /api/profils/{id}` accepts 204 with no body or a JSON response.
- `GET /api/search?q=` -> `{query, results}`; the API helper unwraps `results`.
- `GET /api/ontology/conditions` -> clinical condition options (id, label, iri).

The integrated profile API uses:

```typescript
type Profile = {
  id: string;
  identifiant: string;
  age: number;
  imc: number;
  fume: boolean;
  conditions: string[];
  condition_labels?: Record<string, string>;
  pression_systolique?: number | null;
  pression_diastolique?: number | null;
  editable?: boolean;
};
// Creation requires identifiant; updates exclude it. Server returns an acknowledgement.
```

`id` is the RDF resource's local ID; `identifiant` is its display identifier.
The two can differ. Conditions are ontology IDs selected from readable labels,
not comma-separated text. Complete listing responses include existing conditions
and optional pressures so editing cannot silently erase missing fields. Empty
pressure fields send null to clear their values. Omitted API update fields are
preserved. Ontology examples are read-only; newly created profiles are editable.
Ask questions are 3–500 characters; search is 2–100. Profile validation mirrors
backend age, IMC and blood-pressure constraints.

## Start the live stack from a combined Git checkout

Docker Desktop must be running. The lightweight backend requirements use the
primary NLP module and do not download the optional Transformers models.

```powershell
docker compose up -d fuseki
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-live.txt
.\.venv\Scripts\python.exe -m spacy download fr_core_news_md
Copy-Item backend/.env.example .env
# Edit .env: set PHARMATWIN_FUSEKI_PASSWORD to your local Fuseki admin password.
.\.venv\Scripts\python.exe -m backend.scripts.load_ontology
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

In a second terminal, run the read-only smoke check before disabling mock mode:

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.check_live
# Optional: exercise create/edit/delete using only a disposable test profile.
.\.venv\Scripts\python.exe -m backend.scripts.check_live --crud
```

Then set `NEXT_PUBLIC_MOCK=false` in `frontend/.env.local` and run `npm run dev`
from `frontend/`. The backend queries the ontology, user-profile and inferred
named graphs through SPARQL protocol dataset parameters. The primary translator
keeps its portable queries and its entity-list response contract.

The updated backend tests include actual translator -> FastAPI response
validation -> RDFLib named-graph execution and profile lifecycle checks. The
external Fuseki transport alone is substituted in those isolated tests. A real
service check is separate (`check_live`) and requires a healthy container.

In this working folder the combined Git checkout is `.publish-repo/`, and the
editable frontend is also present at `frontend/`. To restart the configured
local backend from `frontend/`, use `./start-backend.ps1`. This helper also works
from a normal clone where frontend and backend are siblings. It starts the
existing database and FastAPI; it does not reload/overwrite ontology data.

## Checks and static output

```powershell
npm run typecheck
npm test
npm run build
```

The production static files are in `out/`. Tests exercise mock persistence,
filters/CRUD, real endpoint paths/payloads, deletion without a response body,
and error handling using stubbed network requests.

The scripts select Next.js's supported Webpack option because Turbopack's
PostCSS worker failed on this Windows host. The local dev port is 3100 because
Windows refused binding to port 3000 during verification.

Manual check: click an example, expand SPARQL, visit profiles, create a test
record, edit it, reload to check persistence, filter it, cancel then confirm
deletion, and search for `endometriose`. An unmatched keyword should show an
empty state. All UI labels are French and layouts adapt to narrow screens.
