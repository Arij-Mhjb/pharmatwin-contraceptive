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
The copy command resets settings to demo mode; skip it if `.env.local` is
already configured as desired. Node 22 is supported in this workspace.

- `/`: ask a question or click one of six examples; inspect intent, entity
  badges, collapsible SPARQL and the results table.
- `/profils`: filter profiles by age/smoking, create/edit with a modal, and
  confirm deletion. Mock records persist in browser localStorage across reloads.
- `/search`: keyword search with loading, empty and error states.

## Demo and real backend

The supplied `.env.local` starts with:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MOCK=true
```

Mock mode is a UI demonstration: intent, entities, SPARQL and results are fake.
It does not invoke Python or reproduce all NLP behavior. No ontology IRIs are
embedded in the frontend; demo identifiers use `urn:mock:`. Only fictitious
profiles should be entered. Browser storage is not a shared database.

To use your teammate's backend, set `NEXT_PUBLIC_MOCK=false` and restart the
dev server (rebuild a static export). The FastAPI backend must allow CORS for
`http://127.0.0.1:3100` and/or `http://localhost:3100`, including JSON requests,
POST, PUT, DELETE and preflight OPTIONS. The frontend does not implement or
modify FastAPI. Network/HTTP errors appear in the interface.

All requests are centralized in `lib/api.ts`:

- `POST /api/ask`: `{question}` -> `{intent, entities, sparql, results}`.
  `results` is an array of objects; columns derive from its keys. Entity labels
  are optional, with `text` as a fallback. RDF binding `{value: ...}` cells are
  displayed as values.
- `GET /api/profils?age_min=&age_max=&fume=` -> array of profiles.
- `POST /api/profils` and `PUT /api/profils/{id}` use profile input JSON.
- `DELETE /api/profils/{id}` accepts 204 with no body or a JSON response.
- `GET /api/search?q=` -> array of result objects.

Because detailed profile JSON fields were not supplied, this UI uses:

```typescript
type Profile = {
  id: string;
  age: number;
  imc: number;
  fume: boolean;
  conditions: string[];
};
// Create/update payload: same fields without id.
```

Confirm those fields and list response envelopes with your teammate. Adapt
`lib/api.ts` if the backend uses different field names or wrapped arrays. All
domain labels/relationships returned by the actual ontology stay backend-owned.

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
