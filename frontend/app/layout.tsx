'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { MOCK } from '@/lib/api';
import { AuthProvider, useAuth } from '@/components/auth';
import './globals.css';
import './patient.css';
import './auth.css';
import './advanced.css';

function Chrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, loading, logout } = useAuth();
  const publicPage = ['/', '/signin', '/signup'].includes(pathname);
  return <>
    <header><div className="nav-wrap"><Link href="/" className="brand"><span className="brand-mark">✳</span><span>PharmaTwin<small>CONTRACEPTIVE</small></span></Link>
      {!publicPage && user && <nav aria-label="Navigation principale">{[['/dashboard', 'Mon espace'], ['/explorer', 'Comprendre'], ['/search', 'Recherche'], ...(user.role === 'admin' ? [['/admin','Administration']] : [])].map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined} className={pathname === href ? 'active' : ''}>{label}</Link>)}</nav>}
      <div className="nav-account">{!loading && (user ? <><Link className="account-link" href="/account">{user.avatar_url ? <img src={user.avatar_url} alt="" /> : <span className="nav-avatar">{user.display_name.slice(0,1).toUpperCase()}</span>}<span>{user.display_name}</span></Link><button className="text-button" onClick={() => void logout()}>Déconnexion</button></> : <>{pathname !== '/signin' && <Link className="text-button" href="/signin">Connexion</Link>}{pathname !== '/signup' && <Link className="primary small" href="/signup">Créer un compte</Link>}</>)}<span className="mode"><span className="dot" />{MOCK ? 'Démo' : 'API'}</span></div></div></header>
    <main>{children}</main>
    <footer><span>PharmaTwin Contraceptive</span><span>ESPRIT · Web sémantique · Profils fictifs</span><Link href="/profils">Espace technique : profils</Link><span>Aucun conseil médical</span></footer>
  </>;
}
export default function Layout({ children }: { children: ReactNode }) { return <html lang="fr"><head><title>PharmaTwin · Mon espace contraception</title><meta name="description" content="Plateforme académique sécurisée pour explorer et comparer des options contraceptives avec des profils fictifs." /></head><body><AuthProvider><Chrome>{children}</Chrome></AuthProvider></body></html>; }
