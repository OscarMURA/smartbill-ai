import { createContext, useContext } from 'react';
import type { AuthUser } from '../lib/api';

export type AuthContextValue = { user: AuthUser | null; ready: boolean; authenticate: (user: AuthUser) => void; signOut: () => Promise<void> };
export const AuthContext = createContext<AuthContextValue | null>(null);
export const useAuth = () => { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider missing'); return value; };
