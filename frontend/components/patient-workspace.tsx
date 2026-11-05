'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ErrorBox } from '@/components/ui';
import { CandidateCard, MethodDetails, ReportView } from '@/components/report';
import { addSymptom, assess, emptyPatient, getCatalog, getPatient, getReports, listPatients, savePatient, type Catalog, type PatientInput, type PatientSummary, type Report, type Symptom } from '@/lib/patient';

const ACTIVE = 'pharmatwin-active-patient';
const tabs = [['profile', '01', 'Mon profil'], ['options', '02', 'Mes options'], ['current', '03', 'Ma contraception'], ['followup', '04', 'Mon suivi'], ['reports', '05', 'Mes bilans']];

export default function PatientWorkspace() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [people, setPeople] = useState<PatientSummary[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [data, setData] = useState<PatientInput | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [tab, setTab] = useState('profile');
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [generation, setGeneration] = useState(0);

  async function open(id: string | null) {
    setBusy(true); setError(''); setNotice('');
    try {
      const patient = id ? await getPatient(id) : emptyPatient();
      const saved = id ? await getReports(id) : [];
      setData(patient); setActive(id); setReports(saved); setReport(saved[0] ?? null); setTab('profile');
      if (id) localStorage.setItem(ACTIVE, id); else localStorage.removeItem(ACTIVE);
      setGeneration(g => g + 1);
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function initialize() {
    setBusy(true); setError('');
    try {
      const [choices, savedPeople] = await Promise.all([getCatalog(), listPatients()]);
      setCatalog(choices); setPeople(savedPeople);
      const previous = localStorage.getItem(ACTIVE);
      await open(previous && savedPeople.some(p => p.id === previous) ? previous : null);
    } catch (e) { setError(message(e)); setBusy(false); }
  }
  useEffect(() => { void initialize(); }, []);

  async function saveAndCompare(input: PatientInput) {
    setData(input); // Preserve the form if a network or validation error occurs.
    setBusy(true); setError(''); setNotice('');
    try {
      const saved = await savePatient(active, input);
      setActive(saved.id); setData(saved.data); localStorage.setItem(ACTIVE, saved.id);
      setPeople(await listPatients());
      const evaluation = await assess(saved.id);
      setReport(evaluation); setReports(await getReports(saved.id)); setTab('options');
      setNotice('Votre profil est enregistré. Un nouveau bilan daté a été créé.');
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function compare() {
    if (!active) return;
    setBusy(true); setError('');
    try { const result = await assess(active); setReport(result); setReports(await getReports(active)); setTab('options'); setNotice('Nouveau bilan enregistré à partir du profil sauvegardé.'); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function observe(observation: Symptom) {
    if (!active) return;
    setBusy(true); setError('');
    try {
      const updated = await addSymptom(active, observation); setData(updated);
      const result = await assess(active); setReport(result); setReports(await getReports(active));
      setNotice('Observation enregistrée et nouveau bilan créé. Le symptôme n’est pas automatiquement attribué à votre contraception.');
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }

  const current = catalog?.methods.find(m => m.id === data?.current_method);
  const currentAssessment = reports[0]?.candidates.find(m => m.id === data?.current_method);
  return <>
    <section className="patient-hero no-print"><div><span className="eyebrow">VOTRE HISTOIRE. VOS PRÉFÉRENCES. VOTRE CHOIX.</span><h1>Une contraception<br /><span>qui vous ressemble.</span></h1><p>Racontez votre situation, comparez les options et comprenez les raisons.<br />Un espace pour préparer une décision éclairée avec un professionnel.</p></div><aside className="journey-note"><span>✳</span><strong>Vous êtes au centre.</strong><p>Votre santé et votre expérience comptent autant que vos préférences.</p><small>Plateforme académique · Profils fictifs uniquement · Espace associé à votre compte</small></aside></section>
    {error && <><ErrorBox message={error} />{!catalog && <button className="secondary" onClick={() => void initialize()}>Réessayer la connexion</button>}</>}
    {catalog && <>
      <div className="workspace-bar no-print"><label>Mon espace local<select value={active ?? ''} disabled={busy} onChange={e => void open(e.target.value || null)}><option value="">Créer un nouveau profil</option>{people.map(p => <option key={p.id} value={p.id}>{p.display_name}</option>)}</select></label><span className="muted">{active ? `Bonjour ${data?.display_name}. Vos bilans sont conservés sur ce serveur local.` : 'Commencez par créer votre profil. Aucun nom réel n’est nécessaire.'}</span></div>
      <nav className="workspace-tabs no-print" aria-label="Mon parcours">{tabs.map(([id, number, label]) => <button key={id} disabled={busy || (!active && id !== 'profile')} className={tab === id ? 'selected' : ''} onClick={() => { setTab(id); if (id === 'options') setReport(reports[0] ?? null); setNotice(''); }}><small>{number}</small>{label}</button>)}</nav>
      <p role="status" className="success no-print">{notice}</p>
      {busy && <div role="status" className="panel empty no-print">{active ? 'Mise à jour de votre espace…' : 'Préparation de votre espace…'}</div>}
      {!busy && data && tab === 'profile' && <ProfileWizard key={`${active}-${generation}`} initial={data} catalog={catalog} saved={!!active} onSave={saveAndCompare} />}
      {!busy && tab === 'options' && <><div className="section-top no-print"><div><h2>Vos préférences, expliquées</h2><p className="muted">Les options sans signal retrouvé sont triées par affinité. Leur admissibilité médicale reste à vérifier.</p></div><button className="secondary" onClick={() => void compare()}>Actualiser mon bilan</button></div>{report ? <><p className="notice">{report.score_explanation}</p><details className="panel"><summary>Ce que ce bilan ne peut pas déterminer</summary><ul className="gap-list">{report.gaps.map(g => <li key={g}>{g}</li>)}</ul></details>{report.candidates.map((candidate, i) => <CandidateCard key={candidate.id} candidate={candidate} index={i} />)}<button className="primary my-6" onClick={() => setTab('reports')}>Voir et télécharger mon bilan ↗</button></> : <button className="primary" onClick={() => void compare()}>Comparer mes options</button>}</>}
      {!busy && tab === 'current' && <><section className="panel"><span className="eyebrow">COMPRENDRE VOTRE MÉTHODE ACTUELLE</span><h2>{current?.label ?? 'Aucune contraception actuelle renseignée'}</h2>{current ? <><p>Les effets ci-dessous sont des associations du graphe, pas une prédiction de ce que vous ressentirez.</p>{currentAssessment?.flags.map((f, i) => <div key={i} className="error">{f.reason}</div>)}<MethodDetails method={current} /><Link className="primary inline-block" href={`/explorer?q=${encodeURIComponent('Quels sont les effets indésirables de ' + current.label + ' ?')}`}>Poser une question sur cette méthode ↗</Link></> : <button className="secondary my-4" onClick={() => setTab('profile')}>Renseigner ma contraception</button>}</section><section className="panel"><h2>Votre vécu reste distinct des effets possibles</h2><p>Le manque de sommeil, la fatigue ou les changements de règles peuvent être consignés dans votre suivi. Un lien temporel ne prouve pas une cause.</p><button className="secondary" onClick={() => setTab('followup')}>Ajouter une observation</button></section></>}
      {!busy && data && tab === 'followup' && <><section className="panel"><span className="eyebrow">VOTRE VÉCU, AU FIL DU TEMPS</span><h2>Comment vous sentez-vous ?</h2><p className="muted">Une observation est une information déclarée, pas un diagnostic. Chaque ajout crée un nouveau bilan sans modifier les anciens.</p><SymptomForm onSave={observe} /></section><section className="panel"><h2>Mon journal</h2>{data.symptoms.length ? [...data.symptoms].reverse().map((s, i) => <article className="journal-entry" key={i}><span className="badge neutral">{s.date}</span><h3>{s.name}</h3><p>Intensité déclarée : {s.severity}</p>{s.notes && <p>{s.notes}</p>}</article>) : <p className="empty">Votre première observation apparaîtra ici.</p>}</section></>}
      {!busy && tab === 'reports' && <><div className="section-top no-print"><div><h2>Mes bilans conservés</h2><p className="muted">Chaque bilan garde le profil, les préférences, les observations et la version des données utilisés à cette date.</p></div><label>Choisir un bilan<select value={report?.id ?? ''} onChange={e => setReport(reports.find(r => r.id === e.target.value) ?? null)}>{reports.map(r => <option key={r.id} value={r.id}>{new Date(r.created_at).toLocaleString('fr-FR')}</option>)}</select></label></div>{report ? <ReportView report={report} /> : <p className="panel empty">Enregistrez votre profil et comparez vos options pour créer un bilan.</p>}</>}
    </>}
    {!catalog && busy && <div className="panel empty" role="status">Connexion à votre espace et à l’ontologie…</div>}
    <section className="patient-help no-print"><div><span className="eyebrow">ENVIE DE COMPRENDRE ?</span><h2>Vos questions ont aussi leur place.</h2><p>Molécules, conditions de santé, effets possibles ou sources : explorez les connaissances en français.</p></div><Link className="secondary" href="/explorer">Poser ma question ↗</Link></section>
  </>;
}

function message(error: unknown) { return error instanceof Error ? error.message : 'Une erreur est survenue. Réessayez.'; }
function Pick({ label, options, values, onChange }: { label: string; options: { id: string; label: string }[]; values: string[]; onChange: (value: string[]) => void }) {
  return <fieldset className="choice-field"><legend>{label}</legend><div className="choice-grid">{options.map(option => <label className={`choice ${values.includes(option.id) ? 'chosen' : ''}`} key={option.id}><input type="checkbox" checked={values.includes(option.id)} onChange={e => onChange(e.target.checked ? [...values, option.id] : values.filter(v => v !== option.id))} /><span>{option.label}</span></label>)}</div></fieldset>;
}

function ProfileWizard({ initial, catalog, saved, onSave }: { initial: PatientInput; catalog: Catalog; saved: boolean; onSave: (data: PatientInput) => Promise<void> }) {
  const [draft, setDraft] = useState<PatientInput>(() => structuredClone(initial));
  const [step, setStep] = useState(0); const [error, setError] = useState('');
  const profile = draft.profile; const prefs = draft.preferences;
  function updateProfile(patch: Partial<PatientInput['profile']>) { setDraft({ ...draft, profile: { ...profile, ...patch } }); }
  return <section className="panel onboarding"><div className="section-top"><div><span className="eyebrow">{saved ? 'ACTUALISER MON PROFIL' : 'FAISONS CONNAISSANCE'}</span><h2>{['Ma situation', 'Mon expérience et mes traitements', 'Ce qui compte pour moi'][step]}</h2></div><span className="badge neutral">Étape {step + 1} / 3</span></div><div className="wizard-progress" aria-hidden="true">{[0, 1, 2].map(i => <span className={i <= step ? 'filled' : ''} key={i} />)}</div><p className="muted">Utilisez un scénario fictif pour ce mini-projet. Vos données sont enregistrées uniquement lorsque vous validez la dernière étape.</p><form onSubmit={e => {
    e.preventDefault(); setError('');
    if (profile.pression_systolique != null && profile.pression_diastolique != null && profile.pression_diastolique >= profile.pression_systolique) { setError('La tension diastolique doit être inférieure à la systolique.'); return; }
    if (step < 2) setStep(step + 1); else void onSave(draft);
  }}>
    {step === 0 && <><label>Comment souhaitez-vous être appelée ?<input required maxLength={60} value={draft.display_name} onChange={e => setDraft({ ...draft, display_name: e.target.value })} placeholder="Un prénom fictif ou un pseudonyme" /></label><div className="form-grid my-6"><label>Âge<input required type="number" min={12} max={100} value={profile.age} onChange={e => updateProfile({ age: +e.target.value })} /></label><label>IMC<input required type="number" min={8.1} max={79.9} step="0.1" value={profile.imc} onChange={e => updateProfile({ imc: +e.target.value })} /></label><label>Tension systolique (facultatif)<input type="number" min={50} max={260} value={profile.pression_systolique ?? ''} onChange={e => updateProfile({ pression_systolique: e.target.value ? +e.target.value : null })} /></label><label>Tension diastolique (facultatif)<input type="number" min={30} max={180} value={profile.pression_diastolique ?? ''} onChange={e => updateProfile({ pression_diastolique: e.target.value ? +e.target.value : null })} /></label></div><label>Tabagisme<select value={String(profile.fume)} onChange={e => updateProfile({ fume: e.target.value === 'true' })}><option value="false">Non</option><option value="true">Oui</option></select></label><Pick label="Conditions et antécédents connus (si renseignés dans votre scénario)" options={catalog.conditions} values={profile.conditions} onChange={conditions => updateProfile({ conditions })} /><label>Autres antécédents ou conditions hors de la liste<textarea maxLength={1000} rows={2} value={draft.other_conditions ?? ""} onChange={e => setDraft({ ...draft, other_conditions: e.target.value })} /><small>Conservés dans le bilan, mais non évalués automatiquement.</small></label></>}
    {step === 1 && <><label>Ma contraception actuelle<select value={draft.current_method ?? ''} onChange={e => setDraft({ ...draft, current_method: e.target.value || null })}><option value="">Aucune / non renseignée</option>{catalog.methods.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}</select></label><Pick label="Médicaments / molécules pris actuellement" options={catalog.molecules} values={draft.medications} onChange={medications => setDraft({ ...draft, medications })} /><label>Autres traitements non présents dans la liste<textarea rows={2} maxLength={500} value={draft.other_medications} onChange={e => setDraft({ ...draft, other_medications: e.target.value })} /><small>Le texte libre est conservé dans le bilan mais ne peut pas être évalué automatiquement.</small></label><div className="section-top mt-6"><h3>Mes expériences passées</h3><button className="secondary" type="button" disabled={draft.history.length >= 30} onClick={() => setDraft({ ...draft, history: [...draft.history, { method_id: catalog.methods[0].id, period: '', experience: 'unknown', notes: '' }] })}>+ Ajouter une expérience</button></div>{draft.history.map((h, i) => <div className="history-entry" key={i}><label>Contraception<select value={h.method_id} onChange={e => setDraft({ ...draft, history: draft.history.map((v, n) => n === i ? { ...v, method_id: e.target.value } : v) })}>{catalog.methods.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}</select></label><div className="form-grid my-4"><label>Période<input maxLength={80} placeholder="Ex. 2023–2024" value={h.period} onChange={e => setDraft({ ...draft, history: draft.history.map((v, n) => n === i ? { ...v, period: e.target.value } : v) })} /></label><label>Mon expérience<select value={h.experience} onChange={e => setDraft({ ...draft, history: draft.history.map((v, n) => n === i ? { ...v, experience: e.target.value as typeof h.experience } : v) })}><option value="unknown">Pas d’avis / non renseignée</option><option value="positive">Plutôt positive</option><option value="negative">Plutôt négative</option></select></label></div><label>Ce que j’ai ressenti / raison de l’arrêt<textarea maxLength={500} rows={2} value={h.notes} onChange={e => setDraft({ ...draft, history: draft.history.map((v, n) => n === i ? { ...v, notes: e.target.value } : v) })} /></label><button className="text-button danger-text" type="button" onClick={() => setDraft({ ...draft, history: draft.history.filter((_, n) => n !== i) })}>Retirer cette expérience du formulaire</button></div>)}</>}
    {step === 2 && <><Pick label="Les formes que je préfère" options={catalog.forms.map(form => ({ id: form, label: form }))} values={prefs.forms} onChange={forms => setDraft({ ...draft, preferences: { ...prefs, forms } })} /><label>Ma préférence concernant les hormones<select value={prefs.hormones} onChange={e => setDraft({ ...draft, preferences: { ...prefs, hormones: e.target.value as typeof prefs.hormones } })}><option value="indifferent">Pas de préférence</option><option value="avoid">Je préfère une méthode non hormonale</option><option value="accept">Je préfère une méthode hormonale</option></select></label><Pick label="Les bénéfices documentés que je souhaite comparer" options={catalog.benefits} values={prefs.benefits} onChange={benefits => setDraft({ ...draft, preferences: { ...prefs, benefits } })} /><Pick label="Les effets possibles qui me préoccupent" options={catalog.effects} values={prefs.avoid_effects} onChange={avoid_effects => setDraft({ ...draft, preferences: { ...prefs, avoid_effects } })} /><label className="checkbox-label"><input type="checkbox" checked={draft.history_complete} onChange={e => setDraft({ ...draft, history_complete: e.target.checked })} /> J’ai renseigné les antécédents et traitements connus dans mon scénario.</label><p className="notice">Votre pourcentage indiquera uniquement la correspondance des préférences documentées. Une contre-indication ou une interaction reste visible et ne peut pas être compensée par ce score.</p></>}
    {error && <ErrorBox message={error} />}<div className="modal-actions"><button type="button" className="secondary" disabled={step === 0} onClick={() => setStep(step - 1)}>Précédent</button><button className="primary">{step === 2 ? 'Enregistrer et comparer mes options ↗' : 'Continuer ↗'}</button></div>
  </form></section>;
}

function SymptomForm({ onSave }: { onSave: (value: Symptom) => Promise<void> }) {
  const [symptom, setSymptom] = useState<Symptom>({ name: 'Troubles du sommeil', date: new Date().toLocaleDateString('en-CA'), severity: 'leger', notes: '' });
  return <form onSubmit={e => { e.preventDefault(); void onSave(symptom); }}><div className="form-grid my-6"><label>Observation<select value={symptom.name} onChange={e => setSymptom({ ...symptom, name: e.target.value })}>{['Troubles du sommeil', 'Fatigue', 'Règles abondantes', 'Cycles irréguliers', 'Changement d’humeur', 'Autre observation'].map(name => <option key={name}>{name}</option>)}</select></label><label>Date<input required type="date" value={symptom.date} onChange={e => setSymptom({ ...symptom, date: e.target.value })} /></label><label>Intensité ressentie<select value={symptom.severity} onChange={e => setSymptom({ ...symptom, severity: e.target.value as Symptom['severity'] })}><option value="leger">Légère</option><option value="modere">Modérée</option><option value="important">Importante</option></select></label></div><label>Ce que je souhaite noter<textarea maxLength={500} rows={3} value={symptom.notes} onChange={e => setSymptom({ ...symptom, notes: e.target.value })} placeholder="Depuis quand ? À quel moment du cycle ? Quel impact dans la journée ?" /></label><div className="modal-actions"><button className="primary">Enregistrer et actualiser mon bilan ↗</button></div></form>;
}
