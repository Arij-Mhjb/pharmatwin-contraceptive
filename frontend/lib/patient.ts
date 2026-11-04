import { MOCK, request, type ProfileInput, type ConditionOption } from './api';
export type Term = { id: string; label: string; iri: string };
export type Source = Term & { title: string; url: string; level: string; synthetic: boolean };
export type Effect = Term & { description?: string; sources: Source[] };
export type Method = Term & { form: string; hormonal: boolean | null; molecules: Term[]; effects: Effect[]; benefits: Effect[]; contraindications: (Term & { conditions: Term[]; mec: number | null; sources: Source[] })[] };
export type Catalog = { methods: Method[]; conditions: ConditionOption[]; molecules: Term[]; benefits: Term[]; effects: Term[]; forms: string[]; notice: string };
export type PastUse = { method_id: string; period: string; experience: 'positive' | 'negative' | 'unknown'; notes: string };
export type Symptom = { name: string; date: string; severity: 'leger' | 'modere' | 'important'; notes: string };
export type PatientInput = { display_name: string; profile: ProfileInput; preferences: { forms: string[]; hormones: 'indifferent' | 'avoid' | 'accept'; benefits: string[]; avoid_effects: string[] }; current_method: string | null; medications: string[]; other_medications: string; other_conditions?: string; history: PastUse[]; symptoms: Symptom[]; history_complete: boolean };
export type Flag = { kind: string; reason: string; mec?: number | null; sources: Source[] };
export type Candidate = Method & { status: 'blocked' | 'review' | 'undetermined'; preference_score: number | null; flags: Flag[]; criteria: { label: string; matched: boolean | null; reason: string }[]; assessed_criteria: number; total_criteria: number; coverage: number };
export type Report = { id: string; patient_id: string; created_at: string; snapshot: PatientInput; labels?: Record<string, string>; candidates: Candidate[]; gaps: string[]; score_explanation: string; rules_version: string; ontology_sha256: string; clinical_validation: string };
export type PatientSummary = { id: string; display_name: string; updated_at: string };
function live<T>(path: string, init?: RequestInit): Promise<T> {
  if (MOCK) return Promise.reject(new Error('L’espace personnel utilise le vrai backend. Activez NEXT_PUBLIC_MOCK=false et démarrez FastAPI pour créer votre scénario.'));
  return request<T>('/api/patient' + path, init);
}
export const getCatalog = () => live<Catalog>('/catalog');
export const listPatients = () => live<PatientSummary[]>('/profiles');
export const getPatient = (id: string) => live<PatientInput>('/profiles/' + encodeURIComponent(id));
export const getReports = (id: string) => live<Report[]>('/profiles/' + encodeURIComponent(id) + '/reports');
export const assess = (id: string) => live<Report>('/profiles/' + encodeURIComponent(id) + '/assessments', { method: 'POST' });
export const savePatient = (id: string | null, body: PatientInput) => live<{ id: string; data: PatientInput }>('/profiles' + (id ? '/' + encodeURIComponent(id) : ''), { method: id ? 'PUT' : 'POST', body: JSON.stringify(body) });
export const addSymptom = (id: string, observation: Symptom) => live<PatientInput>('/profiles/' + encodeURIComponent(id) + '/symptoms', { method: 'POST', body: JSON.stringify({ observation }) });
export function emptyPatient(): PatientInput { return { display_name: '', profile: { identifiant: 'P-' + crypto.randomUUID().slice(0, 8), age: 25, imc: 22, fume: false, conditions: [], pression_systolique: null, pression_diastolique: null }, preferences: { forms: [], hormones: 'indifferent', benefits: [], avoid_effects: [] }, current_method: null, medications: [], other_medications: '', history: [], symptoms: [], history_complete: false }; }
