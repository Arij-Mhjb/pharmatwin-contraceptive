'use client';
import { Suspense } from 'react'; import { AuthForm } from '@/components/auth-form';
export default function SignUpPage() { return <Suspense fallback={<div className="panel empty">Chargement…</div>}><AuthForm mode="signup" /></Suspense>; }
