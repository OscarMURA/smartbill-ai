import React, { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LandingPage from './pages/LandingPage';
import { getMe, logout as apiLogout, setCsrfToken, type AuthUser } from './lib/api';
import { AuthContext, type AuthContextValue, useAuth } from './auth/AuthContext';
import './index.css';
import './auth.css';

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 30_000 } } });
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);
  const location = useLocation();
  useEffect(() => { let active = true; if (location.pathname === '/demo' || location.pathname === '/') { setReady(true); return () => { active = false; }; } setReady(false); getMe().then(value => { if (active) { setUser(value); setCsrfToken(value.csrf_token); } }).catch(() => { if (active) { setUser(null); setCsrfToken(null); } }).finally(() => { if (active) setReady(true); }); return () => { active = false; }; }, [location.pathname]);
  const value = useMemo<AuthContextValue>(() => ({ user, ready, authenticate(next) { setUser(next); setCsrfToken(next.csrf_token); }, async signOut() { try { await apiLogout(); } finally { setUser(null); setCsrfToken(null); queryClient.clear(); } } }), [user, ready]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function ProtectedApp() {
  const auth = useAuth(); const location = useLocation();
  if (!auth.ready) return <div className="auth-loading" role="status">Verificando tu sesión…</div>;
  return auth.user ? <DashboardPage publicDemo={false} userEmail={auth.user.email} onLogout={() => void auth.signOut()}/> : <Navigate to="/login" replace state={{ from: location.pathname }}/>;
}
function Demo() { return <DashboardPage publicDemo userEmail={null} onLogout={() => undefined}/>; }
function GuestOnly({ children }: { children: React.ReactNode }) { const { user, ready } = useAuth(); if (!ready) return <div className="auth-loading" role="status">Verificando tu sesión…</div>; return user ? <Navigate to="/app" replace/> : <>{children}</>; }

function AppRoutes() {
  return <AuthProvider><Suspense fallback={<div className="auth-loading" role="status">Cargando SmartBill AI…</div>}><Routes>
    <Route path="/" element={<LandingPage/>}/>
    <Route path="/demo" element={<Demo/>}/>
    <Route path="/login" element={<GuestOnly><LoginPage/></GuestOnly>}/>
    <Route path="/registro" element={<GuestOnly><RegisterPage/></GuestOnly>}/>
    <Route path="/app" element={<ProtectedApp/>}/>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></Suspense></AuthProvider>;
}

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><AppRoutes/></BrowserRouter></QueryClientProvider></React.StrictMode>);
