export type Entity = { text: string; label?: string; iri: string; kind: string };
export type Row = Record<string, unknown>;
export type AskResponse = { intent: string; entities: Entity[]; sparql: string; results: Row[] };
export type ConditionOption = { id: string; label: string; iri?: string };
export type Profile = { id: string; identifiant: string; age: number; imc: number; fume: boolean; conditions: string[]; condition_labels?: Record<string, string>; pression_systolique?: number | null; pression_diastolique?: number | null; editable?: boolean };
export type ProfileInput = Pick<Profile, 'identifiant' | 'age' | 'imc' | 'fume' | 'conditions' | 'pression_systolique' | 'pression_diastolique'>;
export const MOCK = process.env.NEXT_PUBLIC_MOCK === 'true';
const BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const KEY = 'pharmatwin-profiles-v1';
const seed: Profile[] = [
  { id: 'SYN-025', identifiant: 'SYN-025', age: 25, imc: 21.4, fume: false, conditions: ['Endometriose'] },
  { id: 'SYN-028', identifiant: 'SYN-028', age: 28, imc: 24.8, fume: false, conditions: ['SOPK', 'MigraineAvecAura'] },
  { id: 'SYN-041', identifiant: 'SYN-041', age: 41, imc: 31.2, fume: true, conditions: ['Hypertension'] },
];
function profiles(): Profile[] {
  const saved = localStorage.getItem(KEY);
  if (!saved) return structuredClone(seed);
  try { return JSON.parse(saved) as Profile[]; } catch { throw new Error('Les profils locaux sont illisibles. Effacez les données du site pour réinitialiser la démo.'); }
}
function save(rows: Profile[]) { localStorage.setItem(KEY, JSON.stringify(rows)); }
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = path === '/api/ask' || path.endsWith('/catalog') || path.endsWith('/assessments') ? 60000 : 15000;
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const csrf = typeof document === 'undefined' ? '' : document.cookie.split('; ').find(row => row.startsWith('pharmatwin_csrf='))?.split('=')[1] ?? '';
    const mutating = !!init?.method && !['GET', 'HEAD', 'OPTIONS'].includes(init.method.toUpperCase());
    const response = await fetch(`${BASE}${path}`, { ...init, credentials: 'include', headers: { 'Content-Type': 'application/json', ...(mutating && csrf ? { 'X-CSRF-Token': decodeURIComponent(csrf) } : {}), ...init?.headers }, signal: controller.signal });
    if (!response.ok) {
      const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
      const detail = typeof payload?.detail === 'string' ? ` ${payload.detail}` : '';
      throw new Error(`Le serveur a répondu avec une erreur (${response.status}).${detail}`);
    }
    if (response.status === 204) return undefined as T;
    return await response.json() as T;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw new Error('Le serveur met trop de temps à répondre. Réessayez.');
    if (error instanceof TypeError) throw new Error('Connexion impossible. Vérifiez que le backend fonctionne et autorise cette origine (CORS).');
    throw error;
  } finally { clearTimeout(timer); }
}
const pause = () => new Promise(resolve => setTimeout(resolve, 350));
function folded(value: string) { return value.toLowerCase().replace(/œ/g, 'oe').normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
export async function ask(question: string): Promise<AskResponse> {
  if (!MOCK) return request('/api/ask', { method: 'POST', body: JSON.stringify({ question }) });
  await pause();
  const q = folded(question);
  const intent = /etude|source|preuve/.test(q) ? 'sources_preuve' : /profil/.test(q) ? (/risque|alerte/.test(q) ? 'profils_a_risque' : 'profils_par_condition') : /interag|interaction/.test(q) ? 'interactions_molecule' : /contre.indiqu|contre.indication/.test(q) ? 'contraceptifs_contre_indiques_condition' : /molecule|contient/.test(q) ? 'molecules_contraceptif' : /benefice/.test(q) ? 'benefices_contraceptif' : 'effets_indesirables_contraceptif';
  const label = q.includes('rifamp') ? 'Rifampicine' : q.includes('migraine') ? 'Migraine avec aura' : 'Pilule combinée';
  const results: Row[] = intent.startsWith('profils') ? profiles().map(p => ({ profil: p.id, age: p.age, conditions: p.conditions.join(', ') })) : intent === 'sources_preuve' ? [{ label: 'Source de démonstration', type: 'Résultat fictif' }] : intent === 'interactions_molecule' ? [{ label: 'Désogestrel', type: 'Molécule — exemple fictif' }] : intent === 'molecules_contraceptif' ? [{ label: 'Éthinylestradiol' }, { label: 'Drospirénone' }] : [{ label: 'Résultat pédagogique de démonstration', sujet: label }];
  return { intent, entities: [{ text: label, label, iri: 'urn:mock:entity', kind: 'class' }], sparql: '# DÉMONSTRATION : requête fictive, non générée par le module NLP.\nSELECT ?result ?label WHERE {\n  VALUES (?result ?label) {\n    (<urn:mock:result> "Exemple de résultat")\n  }\n}\nORDER BY ?label\nLIMIT 50', results };
}
export async function getProfiles(filters: { age_min?: string; age_max?: string; fume?: string } = {}): Promise<Profile[]> {
  const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v !== undefined && v !== '') as [string, string][]);
  if (!MOCK) return request(`/api/profils?${params}`);
  await pause();
  return profiles().filter(p => (!filters.age_min || p.age >= +filters.age_min) && (!filters.age_max || p.age <= +filters.age_max) && (!filters.fume || p.fume === (filters.fume === 'true')));
}
export async function createProfile(input: ProfileInput): Promise<{ id: string }> {
  if (!MOCK) return request('/api/profils', { method: 'POST', body: JSON.stringify(input) });
  if (profiles().some(p => p.id === input.identifiant)) throw new Error('Cet identifiant existe déjà.');
  const result = { ...input, id: input.identifiant, editable: true };
  save([...profiles(), result]); return result;
}
export async function updateProfile(id: string, input: ProfileInput): Promise<{ id: string }> {
  const { identifiant: _identifier, ...update } = input;
  if (!MOCK) return request(`/api/profils/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(update) });
  const result = { ...input, id }; save(profiles().map(p => p.id === id ? result : p)); return result;
}
export async function deleteProfile(id: string): Promise<void> {
  if (!MOCK) return request(`/api/profils/${encodeURIComponent(id)}`, { method: 'DELETE' });
  save(profiles().filter(p => p.id !== id));
}
export async function search(q: string): Promise<Row[]> {
  if (!MOCK) return (await request<{ query: string; results: Row[] }>(`/api/search?${new URLSearchParams({ q })}`)).results;
  await pause();
  return ['Pilule combinée', 'Migraine avec aura', 'Endométriose', 'Rifampicine', 'SOPK', 'Profil patiente simulé'].filter(label => folded(label).includes(folded(q))).map(label => ({ label, type: 'Terme de démonstration' }));
}

export async function getConditions(): Promise<ConditionOption[]> {
  if (!MOCK) return request('/api/ontology/conditions');
  return [{ id: 'Endometriose', label: 'Endométriose' }, { id: 'SOPK', label: 'SOPK' }, { id: 'MigraineAvecAura', label: 'Migraine avec aura' }, { id: 'Hypertension', label: 'Hypertension' }];
}
