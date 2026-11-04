'use client';

import { useEffect, useRef, useState } from 'react';
import { createProfile, deleteProfile, getConditions, getProfiles, updateProfile, type ConditionOption, type Profile, type ProfileInput } from '@/lib/api';
import { ErrorBox, Modal } from '@/components/ui';

export default function Profiles() {
  const [rows, setRows] = useState<Profile[]>([]);
  const [options, setOptions] = useState<ConditionOption[]>([]);
  const [filters, setFilters] = useState({ age_min: '', age_max: '', fume: '' });
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<Profile | 'new' | null>(null);
  const [deleting, setDeleting] = useState<Profile | null>(null);
  const [saving, setSaving] = useState(false);
  const [modalError, setModalError] = useState('');
  const [notice, setNotice] = useState('');
  const generation = useRef(0);
  async function load(values = filters) {
    const id = ++generation.current;
    setBusy(true); setError('');
    try {
      const [profiles, conditions] = await Promise.all([getProfiles(values), getConditions()]);
      if (id === generation.current) { setRows(profiles); setOptions(conditions); }
    } catch (e) {
      if (id === generation.current) setError(e instanceof Error ? e.message : 'Chargement impossible.');
    } finally { if (id === generation.current) setBusy(false); }
  }
  useEffect(() => { void load({ age_min: '', age_max: '', fume: '' }); return () => { generation.current++; }; }, []);
  async function save(input: ProfileInput) {
    setSaving(true); setModalError('');
    try {
      if (editing === 'new') await createProfile(input);
      else if (editing) await updateProfile(editing.id, input);
      setEditing(null); setNotice('Profil enregistré.'); await load();
    } catch (e) { setModalError(e instanceof Error ? e.message : 'Enregistrement impossible.'); }
    finally { setSaving(false); }
  }
  async function remove() {
    if (!deleting) return;
    setSaving(true); setModalError('');
    try { await deleteProfile(deleting.id); setDeleting(null); setNotice('Profil supprimé.'); await load(); }
    catch (e) { setModalError(e instanceof Error ? e.message : 'Suppression impossible.'); }
    finally { setSaving(false); }
  }
  return <>
    <section className="page-heading"><span className="eyebrow">UN TERRAIN D’EXPLORATION SYNTHÉTIQUE</span><h1>Des profils simulés.<br /><span>Des liens à comprendre.</span></h1><p>Créez et gérez des profils fictifs pour explorer le graphe de connaissances.</p></section>
    <section className="panel">
      <div className="section-top"><div><h2>Profils patientes</h2><p className="muted">Les exemples de l’ontologie sont en lecture seule. Créez un profil pour tester vos modifications.</p></div><button className="primary" disabled={busy || !!error} onClick={() => { setModalError(''); setEditing('new'); }}>+ Nouveau profil</button></div>
      <form className="filters" onSubmit={e => { e.preventDefault(); if (filters.age_min && filters.age_max && +filters.age_min > +filters.age_max) { setError('L’âge minimum doit être inférieur ou égal au maximum.'); return; } void load(); }}>
        <label>Âge minimum<input type="number" min="12" max="100" value={filters.age_min} onChange={e => setFilters({ ...filters, age_min: e.target.value })} /></label>
        <label>Âge maximum<input type="number" min="12" max="100" value={filters.age_max} onChange={e => setFilters({ ...filters, age_max: e.target.value })} /></label>
        <label>Tabagisme<select value={filters.fume} onChange={e => setFilters({ ...filters, fume: e.target.value })}><option value="">Tous</option><option value="true">Fumeur</option><option value="false">Non-fumeur</option></select></label>
        <button className="secondary" disabled={busy}>Appliquer</button><button type="button" className="text-button" onClick={() => { const empty = { age_min: '', age_max: '', fume: '' }; setFilters(empty); void load(empty); }}>Réinitialiser</button>
      </form>
      {error && <ErrorBox message={error} />}<p role="status" className="muted">{notice}</p>
      {busy ? <div className="empty" role="status">Chargement des profils…</div> : <div className="overflow-x-auto"><table><thead><tr>{['Identifiant', 'Âge', 'IMC', 'Tabagisme', 'Conditions', 'Actions'].map(c => <th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map(p => <tr key={p.id}>
        <td><strong>{p.identifiant || p.id}</strong></td><td>{p.age} ans</td><td>{p.imc}</td><td><span className="badge neutral">{p.fume ? 'Fumeur' : 'Non-fumeur'}</span></td>
        <td>{p.conditions.map(id => p.condition_labels?.[id] || options.find(c => c.id === id)?.label || id).join(', ') || '—'}</td>
        <td className="whitespace-nowrap">{p.editable === false ? <span className="muted">Exemple · lecture seule</span> : <><button className="text-button" aria-label={`Modifier ${p.id}`} onClick={() => { setModalError(''); setEditing(p); }}>Modifier</button><button className="text-button danger-text" aria-label={`Supprimer ${p.id}`} onClick={() => { setModalError(''); setDeleting(p); }}>Supprimer</button></>}</td>
      </tr>)}</tbody></table>{!rows.length && <div className="empty">Aucun profil ne correspond aux filtres.</div>}</div>}
    </section>
    {editing && <Modal title={editing === 'new' ? 'Créer un profil simulé' : `Modifier ${editing.identifiant}`} close={() => { if (!saving) setEditing(null); }}><ProfileForm initial={editing === 'new' ? undefined : editing} options={options} saving={saving} error={modalError} save={save} cancel={() => setEditing(null)} /></Modal>}
    {deleting && <Modal title="Supprimer ce profil ?" close={() => { if (!saving) setDeleting(null); }}><p className="my-6">Le profil <strong>{deleting.identifiant}</strong> sera supprimé. Cette action ne peut pas être annulée.</p>{modalError && <ErrorBox message={modalError} />}<div className="modal-actions"><button className="secondary" disabled={saving} onClick={() => setDeleting(null)}>Annuler</button><button className="danger" disabled={saving} onClick={() => void remove()}>{saving ? 'Suppression…' : 'Supprimer le profil'}</button></div></Modal>}
  </>;
}

function ProfileForm({ initial, options, saving, error, save, cancel }: { initial?: Profile; options: ConditionOption[]; saving: boolean; error: string; save: (value: ProfileInput) => Promise<void>; cancel: () => void }) {
  const [identifiant, setIdentifiant] = useState(initial?.identifiant ?? '');
  const [age, setAge] = useState(String(initial?.age ?? 25));
  const [imc, setImc] = useState(String(initial?.imc ?? 22));
  const [fume, setFume] = useState(initial?.fume ?? false);
  const [conditions, setConditions] = useState(initial?.conditions ?? []);
  const [systolic, setSystolic] = useState(String(initial?.pression_systolique ?? ''));
  const [diastolic, setDiastolic] = useState(String(initial?.pression_diastolique ?? ''));
  const [validation, setValidation] = useState('');
  const choices = [...options, ...conditions.filter(id => !options.some(c => c.id === id)).map(id => ({ id, label: initial?.condition_labels?.[id] || id }))];
  return <form onSubmit={e => {
    e.preventDefault(); setValidation('');
    if (systolic && diastolic && +diastolic >= +systolic) { setValidation('La pression diastolique doit être inférieure à la systolique.'); return; }
    void save({ identifiant, age: +age, imc: +imc, fume, conditions, pression_systolique: systolic ? +systolic : null, pression_diastolique: diastolic ? +diastolic : null });
  }}><fieldset disabled={saving}>
    <label>Identifiant du profil<input autoFocus required minLength={2} maxLength={50} pattern="[A-Za-z0-9_-]{2,50}" disabled={!!initial} value={identifiant} onChange={e => setIdentifiant(e.target.value)} placeholder="Ex. TEST-001" /><small>Lettres, chiffres, tirets et underscores uniquement.</small></label>
    <div className="form-grid my-4"><label>Âge<input type="number" min="12" max="100" step="1" required value={age} onChange={e => setAge(e.target.value)} /></label><label>IMC<input type="number" min="8.1" max="79.9" step="0.1" required value={imc} onChange={e => setImc(e.target.value)} /></label></div>
    <div className="form-grid"><label>Pression systolique (mmHg)<input type="number" min="50" max="260" value={systolic} onChange={e => setSystolic(e.target.value)} /></label><label>Pression diastolique (mmHg)<input type="number" min="30" max="180" value={diastolic} onChange={e => setDiastolic(e.target.value)} /></label></div>
    <label className="checkbox-label"><input type="checkbox" checked={fume} onChange={e => setFume(e.target.checked)} /> Profil fumeur</label>
    <label>Conditions simulées<select multiple size={6} value={conditions} onChange={e => setConditions(Array.from(e.target.selectedOptions, option => option.value))}>{choices.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}</select><small>Maintenez Ctrl (ou Cmd) pour sélectionner plusieurs conditions. Les identifiants sont transmis automatiquement.</small></label>
  </fieldset>{(error || validation) && <ErrorBox message={validation || error} />}<div className="modal-actions"><button type="button" className="secondary" disabled={saving} onClick={cancel}>Annuler</button><button className="primary" disabled={saving}>{saving ? 'Enregistrement…' : 'Enregistrer'}</button></div></form>;
}
