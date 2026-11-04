'use client';
import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import type { Row } from '@/lib/api';
export function ErrorBox({ message }: { message: string }) { return <div role="alert" className="error">{message}</div>; }
export function display(value: unknown): string { if (value == null) return '—'; if (typeof value === 'object') { const object = value as Record<string, unknown>; if ('value' in object) return String(object.value); return JSON.stringify(value); } return String(value); }
export function Results({ rows }: { rows: Row[] }) {
  const columns = Array.from(new Set(rows.flatMap(row => Object.keys(row))));
  if (!rows.length) return <div className="empty">Aucun résultat pour cette recherche.</div>;
  return <div className="overflow-x-auto"><table><thead><tr>{columns.map(c => <th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{columns.map(c => <td key={c}>{display(row[c])}</td>)}</tr>)}</tbody></table></div>;
}
export function Modal({ title, children, close }: { title: string; children: ReactNode; close: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => dialog?.close(); }, []);
  return <dialog ref={ref} onCancel={event => { event.preventDefault(); close(); }} aria-labelledby="modal-title" onClick={event => { if (event.target === event.currentTarget) close(); }}><div className="flex items-center justify-between gap-4"><h2 id="modal-title">{title}</h2><button className="icon-button" onClick={close} aria-label="Fermer">×</button></div>{children}</dialog>;
}
