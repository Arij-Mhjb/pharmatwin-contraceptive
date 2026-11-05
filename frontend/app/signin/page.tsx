'use client';
import { Suspense } from 'react'; import { AuthForm } from '@/components/auth-form';
export default function SignInPage() { return <Suspense fallback={<div className="panel empty">Chargement…</div>}><AuthForm mode="signin" /></Suspense>; }
