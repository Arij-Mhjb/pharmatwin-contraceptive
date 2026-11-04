'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { MOCK } from '@/lib/api';
import './globals.css';
import './patient.css';

export default function Layout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return <html lang="fr"><head><title>PharmaTwin · Mon espace contraception</title><meta name="description" content="Un parcours pédagogique pour comprendre et comparer les options contraceptives selon un profil fictif et ses préférences." /></head><body>
    <header><div className="nav-wrap"><Link href="/" className="brand"><span className="brand-mark">✳</span><span>PharmaTwin<small>CONTRACEPTIVE</small></span></Link>
      <nav aria-label="Navigation principale">{[['/', 'Mon espace'], ['/explorer', 'Comprendre'], ['/search', 'Recherche']].map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined} className={pathname === href ? 'active' : ''}>{label}</Link>)}</nav>
      <span className="mode"><span className="dot" />{MOCK ? 'Mode démo' : 'Mode API'}</span></div></header>
    <main>{children}</main>
    <footer><span>PharmaTwin Contraceptive</span><span>ESPRIT · Web sémantique · Profils fictifs</span><Link href="/profils">Espace technique : profils</Link><span>Aucun conseil médical</span></footer>
  </body></html>;
}
