# Controlled SPARQL

The API uses three named graphs:

- `https://pharmatwin.ai/graph/ontology`
- `https://pharmatwin.ai/graph/profiles`
- `https://pharmatwin.ai/graph/inferred`

Profile mutations target only the profiles graph. The `/api/ask` route accepts no user SPARQL: it selects an approved template and validates that only `SELECT` or `ASK` is present. Update operations and remote `SERVICE` clauses are rejected.
