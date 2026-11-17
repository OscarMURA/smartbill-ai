import { ArrowDown, ArrowRight, BarChart3, Check, FileSearch2, LockKeyhole, Sparkles } from 'lucide-react';
import './LandingPage.css';

export default function LandingPage() {
  return <main className="landing">
    <header className="landing-header">
      <a className="landing-brand" href="/" aria-label="SmartBill AI, inicio">
        <span className="landing-brand-mark"><FileSearch2 size={19} strokeWidth={2.2}/></span>
        <span>SmartBill <em>AI</em></span>
      </a>
      <nav className="landing-nav" aria-label="Navegación principal">
        <a href="#como-funciona">Cómo funciona</a>
        <a href="#privacidad">Privacidad</a>
      </nav>
      <div className="landing-actions"><a className="landing-login" href="/login">Iniciar sesión</a><a className="landing-nav-cta" href="/registro">Crear cuenta <ArrowRight size={15}/></a></div>
    </header>

    <section className="landing-hero">
      <div className="landing-hero-copy">
        <p className="landing-kicker"><span/> CLARIDAD PARA TUS FACTURAS DE GAS</p>
        <h1>Entiende tu factura.<br/><span>Decide con claridad.</span></h1>
        <p className="landing-lede">Reúne tus facturas, compara el consumo entre períodos y revisa qué conceptos componen el valor que pagas.</p>
        <div className="landing-hero-ctas"><a className="landing-button landing-button-primary" href="/demo">Explorar demo <ArrowRight size={17}/></a><a className="landing-button landing-button-secondary" href="/registro">Crear cuenta</a></div>
        <p className="landing-reassurance"><LockKeyhole size={15}/> Tu espacio privado empieza con tu cuenta.</p>
      </div>
      <div className="landing-visual" aria-label="Ilustración de una factura y comparación de consumo" role="img">
        <div className="landing-orbit"/>
        <div className="landing-fact-card">
          <div className="landing-fact-top"><span className="landing-doc-icon"><FileSearch2 size={18}/></span><span><b>Resumen de factura</b><small>Vista de ejemplo</small></span><span className="landing-fact-menu">···</span></div>
          <div className="landing-period">CONSUMO · m³</div>
          <div className="landing-number">18,4 <small>m³</small></div>
          <div className="landing-chart"><div className="landing-gridlines"><i/><i/><i/></div><svg viewBox="0 0 420 126" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="landingFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#4c8ce4" stopOpacity=".19"/><stop offset="1" stopColor="#4c8ce4" stopOpacity="0"/></linearGradient></defs><path d="M0 91 C38 84 47 55 83 62 S128 81 162 58 S212 48 245 69 S292 83 326 42 S380 49 420 22 L420 126 L0 126Z" fill="url(#landingFill)"/><path d="M0 91 C38 84 47 55 83 62 S128 81 162 58 S212 48 245 69 S292 83 326 42 S380 49 420 22" fill="none" stroke="#2866a8" strokeWidth="3" strokeLinecap="round"/></svg></div>
          <div className="landing-chart-labels"><span>ENE</span><span>FEB</span><span>MAR</span><span>ABR</span><span>MAY</span><span>JUN</span></div>
          <div className="landing-fact-foot"><span><span className="landing-mini-dot"/> Comparación mensual</span><span>Datos de ejemplo</span></div>
        </div>
        <div className="landing-insight"><span><BarChart3 size={16}/></span><div><small>Lectura del período</small><b>Consulta la variación</b></div><Check size={16}/></div>
        <div className="landing-spark" aria-hidden="true"><Sparkles size={19}/></div>
      </div>
      <a className="landing-scroll" href="#beneficios"><span>Descubre cómo te ayuda</span><ArrowDown size={15}/></a>
    </section>

    <section className="landing-benefits" id="beneficios">
      <div className="landing-section-intro"><p className="landing-kicker">MENOS BÚSQUEDA, MÁS CONTEXTO</p><h2>Una lectura más clara de cada período.</h2><p>SmartBill AI organiza la información de tus facturas para que puedas consultarla sin perderte entre documentos.</p></div>
      <div className="landing-benefit-grid">
        <article className="landing-benefit"><span className="landing-benefit-icon"><FileSearch2 size={20}/></span><h3>Encuentra lo importante</h3><p>Consulta consumo, fechas y valores identificados en tus facturas desde un solo historial.</p></article>
        <article className="landing-benefit"><span className="landing-benefit-icon green"><BarChart3 size={20}/></span><h3>Compara tus períodos</h3><p>Observa cómo cambia el consumo y el total facturado a lo largo del tiempo.</p></article>
        <article className="landing-benefit"><span className="landing-benefit-icon violet"><Sparkles size={20}/></span><h3>Pregunta por los datos</h3><p>Explora los datos extraídos de una factura con ayuda de un asistente.</p></article>
      </div>
    </section>

    <section className="landing-how" id="como-funciona">
      <div className="landing-how-copy"><p className="landing-kicker">ASÍ DE SENCILLO</p><h2>De la factura a una mejor lectura.</h2><p>Empieza con una demostración o crea tu espacio para trabajar con tus propias facturas.</p><a className="landing-inline-link" href="/demo">Ver la demo sintética <ArrowRight size={16}/></a></div>
      <ol className="landing-steps"><li><span>01</span><div><h3>Explora o crea tu cuenta</h3><p>Conoce SmartBill AI con datos de ejemplo o inicia tu espacio privado.</p></div></li><li><span>02</span><div><h3>Agrega tus facturas</h3><p>Sube una factura para consultar los datos que se identifican en ella.</p></div></li><li><span>03</span><div><h3>Revisa y compara</h3><p>Consulta tu historial, compara períodos y pregunta sobre una factura.</p></div></li></ol>
    </section>

    <section className="landing-privacy" id="privacidad"><div className="landing-privacy-icon"><LockKeyhole size={21}/></div><div><p className="landing-kicker">TU INFORMACIÓN, EN SU ESPACIO</p><h2>La demo es pública. Tus facturas, privadas.</h2><p>La demostración usa registros sintéticos. Las facturas que agregues a tu cuenta pertenecen a tu espacio y requieren iniciar sesión para consultarlas.</p></div><a href="/registro">Crear mi cuenta <ArrowRight size={16}/></a></section>

    <section className="landing-independent"><span className="landing-independent-mark">i</span><p><strong>Proyecto independiente.</strong> SmartBill AI es un proyecto independiente y no está afiliado, respaldado ni representa a GdO (Gases de Occidente).</p></section>

    <section className="landing-final"><p className="landing-kicker">EMPIEZA A ENTENDER TUS FACTURAS</p><h2>Una factura a la vez.</h2><p>Explora los datos de muestra o crea tu cuenta para consultar tus propias facturas.</p><div><a className="landing-button landing-button-primary" href="/demo">Explorar demo <ArrowRight size={17}/></a><a className="landing-final-link" href="/registro">Crear cuenta</a></div></section>

    <footer className="landing-footer"><a className="landing-brand" href="/" aria-label="SmartBill AI, inicio"><span className="landing-brand-mark"><FileSearch2 size={17}/></span><span>SmartBill <em>AI</em></span></a><span>Herramienta independiente para entender tus facturas de gas.</span><a href="/login">Iniciar sesión</a></footer>
  </main>;
}
