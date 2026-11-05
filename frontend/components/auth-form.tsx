'use client';
import Link from 'next/link';
import { useState, type FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ErrorBox } from './ui';
import { signIn, signUp } from '@/lib/auth';
import { useAuth } from './auth';

export function AuthForm({ mode }: { mode: 'signin' | 'signup' }) {
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const router = useRouter(); const params = useSearchParams(); const { refresh } = useAuth();
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); const form = new FormData(event.currentTarget);
    try {
      if (mode === 'signup') await signUp({ display_name: String(form.get('display_name')), email: String(form.get('email')), password: String(form.get('password')) });
      else await signIn({ email: String(form.get('email')), password: String(form.get('password')) });
      const user = await refresh(); router.replace(user?.onboarding_complete ? (params.get('next') || '/dashboard') : '/onboarding');
    } catch (e) { setError(e instanceof Error ? e.message : 'Impossible de continuer.'); } finally { setBusy(false); }
  }
  return <section className="auth-shell"><div className="auth-copy"><span className="eyebrow">{mode === 'signup' ? 'CRÉER UN COMPTE' : 'BON RETOUR'}</span><h1>{mode === 'signup' ? 'Votre espace académique, vraiment personnel.' : 'Reprendre votre parcours.'}</h1><p>{mode === 'signup' ? 'Vos scénarios simulés et vos bilans seront associés à votre compte, séparés de ceux des autres utilisateurs.' : 'Accédez à vos profils fictifs, vos observations et vos rapports conservés.'}</p><ul><li>Mot de passe haché côté serveur</li><li>Session révocable en base</li><li>Actions protégées contre les requêtes croisées</li></ul></div><form className="auth-card" onSubmit={submit}>{mode === 'signup' && <label>Nom affiché<input name="display_name" autoComplete="name" minLength={2} maxLength={80} required placeholder="Ex. Étudiante démo" /></label>}<label>Adresse e-mail<input name="email" type="email" autoComplete="email" required placeholder="vous@exemple.test" /></label><label>Mot de passe<input name="password" type="password" autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} minLength={10} maxLength={128} required /></label>{mode === 'signup' && <p className="field-help">10 caractères minimum, avec majuscule, minuscule et chiffre.</p>}{error && <ErrorBox message={error} />}<button className="primary wide" disabled={busy}>{busy ? 'Vérification…' : mode === 'signup' ? 'Créer mon compte ↗' : 'Se connecter ↗'}</button><p className="auth-switch">{mode === 'signup' ? <>Déjà un compte ? <Link href="/signin">Se connecter</Link></> : <>Pas encore de compte ? <Link href="/signup">Créer un compte</Link></>}</p></form></section>;
}
