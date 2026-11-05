'use client';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import * as api from '@/lib/auth';
import type { User } from '@/lib/auth';

type Auth = { user: User | null; loading: boolean; refresh: () => Promise<User | null>; logout: () => Promise<void> };
const Context = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null); const [loading, setLoading] = useState(true);
  async function refresh() { try { const result = await api.session(); setUser(result.user); return result.user; } catch { setUser(null); return null; } finally { setLoading(false); } }
  async function logout() { await api.signOut(); setUser(null); window.location.href = '/signin'; }
  useEffect(() => { void refresh(); }, []);
  return <Context.Provider value={{ user, loading, refresh, logout }}>{children}</Context.Provider>;
}

export function useAuth() { const value = useContext(Context); if (!value) throw new Error('AuthProvider manquant'); return value; }

export function Protected({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const { user, loading } = useAuth(); const router = useRouter(); const pathname = usePathname();
  useEffect(() => { if (!loading && !user) router.replace(`/signin?next=${encodeURIComponent(pathname)}`); else if (!loading && user && !user.onboarding_complete && pathname !== '/onboarding') router.replace('/onboarding'); else if (!loading && admin && user?.role !== 'admin') router.replace('/dashboard'); }, [user, loading, admin, pathname, router]);
  if (loading) return <div className="panel empty">Vérification de votre session sécurisée…</div>;
  if (!user || (admin && user.role !== 'admin') || (!user.onboarding_complete && pathname !== '/onboarding')) return null;
  return <>{children}</>;
}
