import { request } from './api';

export type User = { id: string; email: string; display_name: string; role: 'user' | 'admin'; status: 'active' | 'disabled'; onboarding_complete: boolean; created_at: string; last_login_at: string | null; avatar_url: string | null };
export type AdminOverview = { counts: { users: number; active_users: number; admins: number; sessions: number; patients: number; reports: number }; audit: { action: string; target_type: string; target_id: string | null; created_at: string; actor: string }[]; recent_patients: { id: string; display_name: string; updated_at: string; owner_name: string; owner_email: string | null }[] };
export const session = () => request<{ user: User }>('/api/auth/session');
export const signUp = (body: { email: string; password: string; display_name: string }) => request<{ user: User }>('/api/auth/signup', { method: 'POST', body: JSON.stringify(body) });
export const signIn = (body: { email: string; password: string }) => request<{ user: User }>('/api/auth/signin', { method: 'POST', body: JSON.stringify(body) });
export const signOut = () => request<void>('/api/auth/signout', { method: 'POST' });
export const finishOnboarding = (display_name: string) => request<{ user: User }>('/api/auth/onboarding', { method: 'PUT', body: JSON.stringify({ display_name, academic_use_accepted: true }) });
export const changePassword = (current_password: string, new_password: string) => request<void>('/api/auth/password', { method: 'PUT', body: JSON.stringify({ current_password, new_password }) });
export const updateAvatar = (data_url: string | null) => request<{ user: User }>('/api/auth/avatar', { method: 'PUT', body: JSON.stringify({ data_url }) });
export const listUsers = () => request<User[]>('/api/admin/users');
export const getAdminOverview = () => request<AdminOverview>('/api/admin/overview');
export const updateUser = (id: string, body: { role?: User['role']; status?: User['status'] }) => request<User>(`/api/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
