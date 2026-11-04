import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
const compile = file => ts.transpileModule(readFileSync(new URL(file, import.meta.url), 'utf8'), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
const encoded = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
async function client(mock) {
  process.env.NEXT_PUBLIC_MOCK = String(mock);
  process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  const api = encoded(compile('../lib/api.ts')) + '#' + mock;
  return import(encoded(compile('../lib/patient.ts').replace("'./api'", JSON.stringify(api))) + '#' + mock);
}
test('patient flow uses real backend routes and preserves profile and preference payloads', async () => {
  const api = await client(false); const calls = [];
  globalThis.fetch = async (url, init) => { calls.push({ url, init }); return new Response(JSON.stringify({ id: 'P-TEST' }), { status: 200 }); };
  const profile = api.emptyPatient();
  profile.display_name = 'Profil fictif'; profile.profile.conditions = ['SOPK'];
  profile.preferences.hormones = 'avoid';
  await api.getCatalog(); await api.listPatients(); await api.savePatient(null, profile);
  await api.savePatient('P-TEST', profile); await api.assess('P-TEST');
  await api.addSymptom('P-TEST', { name: 'Fatigue', date: '2026-11-04', severity: 'leger', notes: '' });
  await api.getReports('P-TEST');
  assert.ok(calls[0].url.endsWith('/api/patient/catalog'));
  assert.equal(calls[2].init.method, 'POST'); assert.equal(calls[3].init.method, 'PUT');
  assert.deepEqual(JSON.parse(calls[2].init.body).profile.conditions, ['SOPK']);
  assert.equal(JSON.parse(calls[3].init.body).preferences.hormones, 'avoid');
  assert.ok(calls[4].url.endsWith('/assessments'));
  assert.equal(JSON.parse(calls[5].init.body).observation.name, 'Fatigue');
  assert.ok(calls[6].url.endsWith('/reports'));
});
test('mock mode does not fabricate personalized percentages', async () => {
  const api = await client(true);
  await assert.rejects(api.getCatalog(), /vrai backend/);
});
