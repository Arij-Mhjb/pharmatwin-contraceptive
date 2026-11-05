'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Protected } from '@/components/auth';
import { ErrorBox } from '@/components/ui';
import { request } from '@/lib/api';

type Term = { id: string; iri: string; label: string | null };
type Axiom = { subject: string; predicate: string; object: string; expression: unknown };
type Inventory = { stats: Record<string, number>; classes: Term[]; object_properties: Term[]; datatype_properties: Term[]; individuals: Term[]; axioms: Axiom[] };
const sections = [['classes','Classes'],['object_properties','ObjectProperty'],['datatype_properties','DataProperty'],['individuals','Individus'],['axioms','Axiomes']] as const;
const short = (value: string) => value.split('#').pop() || value;

export default function OntologyPage() { return <Protected><OntologyExplorer /></Protected>; }
function OntologyExplorer() {
  const [inventory,setInventory] = useState<Inventory|null>(null);
  const [section,setSection] = useState<typeof sections[number][0]>('classes');
  const [query,setQuery] = useState(''); const [error,setError] = useState('');
  const [selected,setSelected] = useState<Term|null>(null);
  const [detail,setDetail] = useState<{statements:{predicate:string;object:string}[]}|null>(null);
  useEffect(()=>{ void request<Inventory>('/api/ontology/inventory').then(setInventory).catch(e=>setError(String(e))); },[]);
  async function inspect(term:Term) {setSelected(term);setDetail(null);try{setDetail(await request('/api/ontology/class/'+encodeURIComponent(term.id)));}catch(e){setError(String(e));}}
  const rows = inventory && section !== 'axioms' ? inventory[section].filter(t=>(t.id+' '+t.label).toLowerCase().includes(query.toLowerCase())) : [];
  return <section><div className="page-heading"><span className="eyebrow">LABORATOIRE WEB SÉMANTIQUE</span><h1>Inspecter la connaissance.</h1><p>Explorez les classes, relations, attributs, individus et axiomes réellement chargés depuis l’ontologie.</p><Link href="/explorer" className="secondary">Tester une question en français ↗</Link></div>{error&&<ErrorBox message={error}/>}{!inventory&&!error&&<p role="status" className="panel empty">Lecture de l’ontologie…</p>}{inventory&&<><div className="admin-metrics">{Object.entries(inventory.stats).map(([name,count])=><article key={name}><div><strong>{count}</strong><small>{name.replaceAll('_',' ')}</small></div></article>)}</div><section className="panel"><div className="section-top"><nav aria-label="Catégories ontologiques">{sections.map(([id,label])=><button key={id} className={section===id?'primary':'secondary'} onClick={()=>{setSection(id);setSelected(null);setDetail(null);}}>{label} ({inventory[id].length})</button>)}</nav></div><label>Filtrer les ressources<input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ex. ProfilSOPK, migraine, âge…"/></label>{section==='axioms'?<div>{inventory.axioms.filter(a=>JSON.stringify(a).toLowerCase().includes(query.toLowerCase())).map((a,i)=><details key={i}><summary>{short(a.subject)} · {short(a.predicate)} → {typeof a.expression==='string'?short(a.expression):'Expression OWL structurée'}</summary><pre>{JSON.stringify(a.expression,null,2)}</pre></details>)}</div>:<div className="search-results">{rows.map(term=><button key={term.iri} className="panel text-left" onClick={()=>void inspect(term)}><b>{term.label||term.id}</b><p className="muted">{term.id}</p></button>)}</div>}{selected&&<section className="panel" aria-live="polite"><div className="section-top"><h2>{selected.label||selected.id}</h2><button className="secondary" onClick={()=>{setSelected(null);setDetail(null);}}>Fermer</button></div><p className="muted">{selected.iri}</p>{detail?<div className="overflow-x-auto"><table><thead><tr><th>Prédicat</th><th>Objet</th></tr></thead><tbody>{detail.statements.map((s,i)=><tr key={i}><td>{short(s.predicate)}</td><td>{short(s.object)}</td></tr>)}</tbody></table></div>:<p>Chargement des triplets…</p>}</section>}</section></>}</section>;
}
