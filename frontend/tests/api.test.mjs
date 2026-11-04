import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
const source = ts.transpileModule(readFileSync(new URL('../lib/api.ts', import.meta.url), 'utf8'), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
async function load(mock) {
  process.env.NEXT_PUBLIC_MOCK = String(mock);
  process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}#${mock}`);
}
test('mock profiles persist and support filters, create, update and delete', async () => {
  const store = new Map();
  globalThis.localStorage = { getItem: key => store.get(key) ?? null, setItem: (key, value) => store.set(key, value) };
  const api = await load(true);
  assert.equal((await api.getProfiles()).length, 3);
  assert.deepEqual((await api.getProfiles({ fume: 'true', age_min: '40' })).map(p => p.id), ['SYN-041']);
  const created = await api.createProfile({ age: 33, imc: 23, fume: false, conditions: ['SOPK'] });
  assert.equal((await api.getProfiles()).length, 4);
  await api.updateProfile(created.id, { age: 34, imc: 25, fume: true, conditions: [] });
  assert.equal((await api.getProfiles()).find(p => p.id === created.id).age, 34);
  await api.deleteProfile(created.id);
  assert.equal((await api.getProfiles()).length, 3);
  assert.equal((await api.search('endometriose'))[0].label, 'Endométriose');
  const response = await api.ask('Quelles molécules interagissent avec la Rifampicine ?');
  assert.deepEqual(Object.keys(response).sort(), ['entities', 'intent', 'results', 'sparql']);
  assert.equal(response.intent, 'interactions_molecule');
});
test('live mode sends the agreed paths, parameters and JSON body', async () => {
  const api = await load(false); const calls = [];
  globalThis.fetch = async (url, init) => { calls.push({ url, init }); return new Response(JSON.stringify([]), { status: 200 }); };
  await api.ask('Question de test');
  await api.getProfiles({ age_min: '20', age_max: '40', fume: 'false' });
  await api.createProfile({ age: 25, imc: 22, fume: false, conditions: [] });
  await api.updateProfile('test/id', { age: 26, imc: 22, fume: false, conditions: [] });
  await api.deleteProfile('test/id'); await api.search('migraine avec aura');
  assert.equal(calls[0].url, 'http://localhost:8000/api/ask');
  assert.deepEqual(JSON.parse(calls[0].init.body), { question: 'Question de test' });
  assert.ok(calls[1].url.endsWith('age_min=20&age_max=40&fume=false'));
  assert.equal(calls[2].init.method, 'POST'); assert.equal(calls[3].init.method, 'PUT');
  assert.ok(calls[3].url.endsWith('/test%2Fid')); assert.equal(calls[4].init.method, 'DELETE');
  assert.ok(calls[5].url.endsWith('q=migraine+avec+aura'));
  globalThis.fetch = async () => new Response(null, { status: 204 });
  await api.deleteProfile('test');
});
test('live errors are surfaced in French', async () => {
  const api = await load(false);
  globalThis.fetch = async () => new Response(null, { status: 500 });
  await assert.rejects(api.search('test'), /500/);
  globalThis.fetch = async () => { throw new TypeError('network'); };
  await assert.rejects(api.search('test'), /Connexion impossible/);
});
