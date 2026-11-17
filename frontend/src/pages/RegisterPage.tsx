import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, ArrowLeft, LoaderCircle, LockKeyhole, Mail } from 'lucide-react';
import { register } from '../lib/api';
import { useAuth } from '../auth/AuthContext';

export default function RegisterPage() {
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [confirm, setConfirm] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const auth = useAuth(); const navigate = useNavigate();
  async function submit(event: FormEvent) { event.preventDefault(); setError(''); if (password.length < 8) { setError('La contraseña debe tener al menos 8 caracteres.'); return; } if (password !== confirm) { setError('Las contraseñas no coinciden.'); return; } setBusy(true); try { auth.authenticate(await register(email.trim(), password)); navigate('/app', { replace: true }); } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo crear la cuenta.'); } finally { setBusy(false); } }
  return <main className="auth-page"><div className="auth-top"><Link className="auth-brand" to="/"><span className="auth-brand-mark"><Activity size={19}/></span>smartbill<span>.ai</span></Link><Link className="auth-back" to="/"><ArrowLeft size={16}/> Volver al inicio</Link></div><section className="auth-card"><div className="auth-icon"><Activity size={21}/></div><p className="auth-eyebrow">TU ESPACIO PERSONAL</p><h1>Crea tu cuenta</h1><p className="auth-intro">Guarda y consulta tus facturas de forma privada.</p><form onSubmit={submit} noValidate>
    {error && <div className="auth-error" role="alert">{error}</div>}
    <label htmlFor="register-email">Correo electrónico</label><div className="auth-input-wrap"><Mail size={17}/><input id="register-email" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="tu@correo.com"/></div>
    <label htmlFor="register-password">Contraseña</label><div className="auth-input-wrap"><LockKeyhole size={17}/><input id="register-password" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={e => setPassword(e.target.value)} placeholder="Mínimo 8 caracteres"/></div>
    <label htmlFor="register-confirm">Confirma tu contraseña</label><div className="auth-input-wrap"><LockKeyhole size={17}/><input id="register-confirm" type="password" autoComplete="new-password" required value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="Repite tu contraseña"/></div>
    <button className="auth-submit" type="submit" disabled={busy}>{busy && <LoaderCircle className="auth-spin" size={17}/>} Crear cuenta</button>
  </form><p className="auth-switch">¿Ya tienes cuenta? <Link to="/login">Iniciar sesión</Link></p><p className="auth-footnote">Al crear una cuenta, tus facturas locales se mantienen privadas.</p></section></main>;
}
