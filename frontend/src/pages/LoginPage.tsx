import { FormEvent, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Activity, ArrowLeft, LoaderCircle, LockKeyhole, Mail } from 'lucide-react';
import { login } from '../lib/api';
import { useAuth } from '../auth/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const auth = useAuth(); const navigate = useNavigate(); const location = useLocation();
  async function submit(event: FormEvent) { event.preventDefault(); setError(''); setBusy(true); try { auth.authenticate(await login(email.trim(), password)); const from = (location.state as { from?: string } | null)?.from; navigate(from === '/app' ? '/app' : '/app', { replace: true }); } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.'); } finally { setBusy(false); } }
  return <main className="auth-page"><div className="auth-top"><Link className="auth-brand" to="/"><span className="auth-brand-mark"><Activity size={19}/></span>smartbill<span>.ai</span></Link><Link className="auth-back" to="/"><ArrowLeft size={16}/> Volver al inicio</Link></div><section className="auth-card"><div className="auth-icon"><LockKeyhole size={21}/></div><p className="auth-eyebrow">QUÉ BUENO VERTE</p><h1>Inicia sesión</h1><p className="auth-intro">Accede a tus facturas y a tu análisis personal.</p><form onSubmit={submit} noValidate>
    {error && <div className="auth-error" role="alert">{error}</div>}
    <label htmlFor="login-email">Correo electrónico</label><div className="auth-input-wrap"><Mail size={17}/><input id="login-email" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="tu@correo.com"/></div>
    <label htmlFor="login-password">Contraseña</label><div className="auth-input-wrap"><LockKeyhole size={17}/><input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} placeholder="Tu contraseña"/></div>
    <button className="auth-submit" type="submit" disabled={busy}>{busy && <LoaderCircle className="auth-spin" size={17}/>} Iniciar sesión</button>
  </form><p className="auth-switch">¿Aún no tienes cuenta? <Link to="/registro">Crear cuenta</Link></p><p className="auth-footnote">Tus documentos y datos quedan asociados a tu cuenta.</p></section></main>;
}
