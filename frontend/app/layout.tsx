'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { MOCK } from '@/lib/api';
import './globals.css';
export default function Layout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return <html lang="fr"><head><title>PharmaTwin · Explorateur sémantique</title><meta name="description" content="Exploration pédagogique d’une ontologie contraceptive et de profils simulés." /></head><body><header><div className="nav-wrap"><Link href="/" className="brand"><span className="brand-mark">✳</span><span>PharmaTwin<small>CONTRACEPTIVE</small></span></Link><nav aria-label="Navigation principale">{[['/', 'Explorateur'], ['/profils', 'Profils simulés'], ['/search', 'Recherche']].map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined} className={pathname === href ? 'active' : ''}>{label}</Link>)}</nav><span className="mode"><span className="dot" />{MOCK ? 'Mode démo' : 'Mode API'}</span></div></header><main>{children}</main><footer><span>PharmaTwin Contraceptive</span><span>ESPRIT · Web sémantique · Projet pédagogique</span><span>Données simulées · Aucun conseil médical</span></footer></body></html>;
}
