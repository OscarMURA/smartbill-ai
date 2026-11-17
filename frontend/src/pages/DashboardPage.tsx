import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, Bot, CheckCircle2,
  ChevronDown, CircleHelp, FileText, Home, Menu, ReceiptText, RefreshCw, ShieldCheck, Sparkles,
  TrendingUp, X,
} from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Area, AreaChart } from 'recharts';
import { getDashboard } from '../lib/api';
import type { DashboardOut } from '../types/dashboard';
import type { InvoiceOut } from '../types/api';
import InvoiceUploader from '../components/InvoiceUploader';
import InvoiceChat from '../components/InvoiceChat';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';

const PUBLIC_DEMO = import.meta.env.VITE_PUBLIC_DEMO === 'true';

const cop = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 });
const month = (period: string) => {
  const date = new Date(`${period}-01T12:00:00`);
  return Number.isNaN(date.getTime()) ? period : new Intl.DateTimeFormat('es-CO', { month: 'short' }).format(date).replace('.', '');
};
const periodLabel = (value: string | null) => value || 'Período sin identificar';

export default function DashboardPage({ publicDemo = PUBLIC_DEMO, userEmail, onLogout }: { publicDemo?: boolean; userEmail?: string | null; onLogout?: () => void }) {
  const demoCollectionId = 'e96781c4-81e0-4dc1-a7fb-203c00000001';
  const [section, setSection] = useState<'overview' | 'invoices'>('overview');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collectionId, setCollectionId] = useState<string | undefined>(() => publicDemo ? demoCollectionId : undefined);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string>();
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<DashboardOut, Error>({
    queryKey: ['dashboard', collectionId ?? null], queryFn: ({ signal }) => getDashboard(signal, collectionId),
  });
  const invoices = data?.invoices ?? [];
  const latest = invoices[invoices.length - 1];
  const analysis = data?.latest_analysis;
  const average = analysis?.historical_average_m3 ?? null;
  const select = (next: 'overview' | 'invoices') => { setSection(next); setMobileOpen(false); };

  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`} aria-label="Navegación principal">
      <div className="brand"><span className="brand-mark"><Activity size={20} strokeWidth={2.4} /></span><span>smartbill<span className="brand-ai">.ai</span></span></div>
      <div className="workspace-label">ESPACIO DE TRABAJO</div>
      <nav className="side-nav">
        <Button variant="ghost" className={`nav-item ${section === 'overview' ? 'active' : ''}`} onClick={() => select('overview')} aria-current={section === 'overview' ? 'page' : undefined}><Home size={18}/><span>Resumen</span></Button>
        <Button variant="ghost" className={`nav-item ${section === 'invoices' ? 'active' : ''}`} onClick={() => select('invoices')} aria-current={section === 'invoices' ? 'page' : undefined}><ReceiptText size={18}/><span>Facturas</span>{invoices.length > 0 && <span className="nav-count">{invoices.length}</span>}</Button>
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-help"><span className="help-icon"><CircleHelp size={17}/></span><div><strong>¿Necesitas ayuda?</strong><p>Consulta cómo leer tu factura.</p></div><ArrowRight size={15}/></div>
        <div className="profile"><div className="avatar">{userEmail ? userEmail.slice(0, 2).toUpperCase() : 'SB'}</div><div className="profile-copy"><strong>{userEmail ?? 'Demo pública'}</strong><span>{userEmail ? 'Cuenta personal' : 'Datos sintéticos'}</span></div>{onLogout && userEmail && <button className="logout-button" onClick={onLogout}>Salir</button>}</div>
      </div>
    </aside>
    {mobileOpen && <button className="mobile-scrim" aria-label="Cerrar menú" onClick={() => setMobileOpen(false)} />}
    <main className="main-area">
      <header className="topbar">
        <button className="icon-button menu-button" aria-label={mobileOpen ? 'Cerrar menú' : 'Abrir menú'} onClick={() => setMobileOpen(v => !v)}>{mobileOpen ? <X size={20}/> : <Menu size={20}/>}</button>
        <div className="breadcrumbs"><span>Mi hogar</span><span className="crumb-slash">/</span><strong>{section === 'overview' ? 'Resumen' : 'Facturas'}</strong></div>
        <div className="topbar-right"><Badge variant="outline" className="demo-pill"><span className="status-dot"/> {publicDemo ? 'DEMO SINTÉTICA' : 'ESPACIO PRIVADO'}</Badge>{userEmail ? <button className="logout-top" onClick={onLogout}>Cerrar sesión</button> : <button className="avatar top-avatar" aria-label="Datos sintéticos de demostración">SB</button>}</div>
      </header>
      <div className="content-wrap">
        {isError ? <ErrorState message={error?.message} onRetry={() => void refetch()} loading={isFetching}/> : isLoading ? <LoadingState/> : !data ? <EmptyState publicDemo={publicDemo} onViewInvoices={() => select('invoices')}/> : section === 'invoices' ? <InvoicesPage invoices={invoices} collectionId={collectionId} onBack={() => select('overview')} selectedInvoiceId={selectedInvoiceId} onSelectInvoice={setSelectedInvoiceId} publicDemo={publicDemo || PUBLIC_DEMO} onUploadComplete={invoice => { setCollectionId(invoice.collection_id); setSelectedInvoiceId(invoice.id); setSection('invoices'); }}/> : invoices.length === 0 ? <EmptyState publicDemo={publicDemo} onViewInvoices={() => select('invoices')}/> : <>
          <div className="page-heading">
            <div><p className="eyebrow">TU ENERGÍA, MÁS CLARA</p><h1>Hola, este es tu resumen</h1><p className="subheading">Entiende cómo cambia tu consumo de gas, período a período.</p></div>
            <Button className="button button-primary" onClick={() => select('invoices')}><FileText size={17}/> Ver facturas</Button>
          </div>
          <section className="kpi-grid" aria-label="Indicadores principales">
            <KpiCard label="Consumo del período" value={latest?.consumption_m3 == null ? '—' : `${decimal.format(latest.consumption_m3)} m³`} detail={periodLabel(latest?.billing_period ?? null)} icon={<Activity size={18}/>} tone="blue"/>
            <KpiCard label="Total facturado" value={latest?.total_cop == null ? '—' : cop.format(latest.total_cop)} detail={periodLabel(latest?.billing_period ?? null)} icon={<ReceiptText size={18}/>} tone="green"/>
            <KpiCard label="Variación mensual" value={analysis?.variation_percentage == null ? '—' : `${analysis.variation_percentage > 0 ? '+' : ''}${decimal.format(analysis.variation_percentage)}%`} detail={analysis?.previous_consumption_m3 == null ? 'Sin período anterior' : `vs. ${decimal.format(analysis.previous_consumption_m3)} m³ anteriores`} icon={analysis?.variation_percentage != null && analysis.variation_percentage < 0 ? <ArrowDownRight size={18}/> : <ArrowUpRight size={18}/>} tone={analysis?.status === 'high_variation' ? 'amber' : 'blue'}/>
            <KpiCard label="Promedio histórico" value={average == null || !Number.isFinite(average) ? '—' : `${decimal.format(average)} m³`} detail={`${data.series.filter(item => item.consumption_m3 !== null).length} períodos disponibles`} icon={<BarChart3 size={18}/>} tone="purple"/>
          </section>
          <section className="chart-grid">
            <Card role="article" className="panel chart-panel">
              <div className="panel-heading"><div><div className="panel-title-row"><h2>Consumo de gas</h2><span className="unit-chip">m³</span></div><p>Tu consumo en cada período facturado</p></div><button className="period-select" aria-label="Período mostrado">Últimos períodos <ChevronDown size={15}/></button></div>
              <div className="chart-legend"><span className="legend-dot consumption-dot"/> Consumo mensual</div>
              <div className="chart-box" role="img" aria-label="Gráfico de consumo mensual en metros cúbicos">
                <ResponsiveContainer width="100%" height="100%"><AreaChart data={data.series.map(point => ({ ...point, label: month(point.period) }))} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                  <defs><linearGradient id="consumptionFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#2563eb" stopOpacity={0.16}/><stop offset="100%" stopColor="#2563eb" stopOpacity={0}/></linearGradient></defs>
                  <CartesianGrid stroke="#edf0f4" vertical={false}/><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#768397', fontSize: 12 }}/><YAxis axisLine={false} tickLine={false} tick={{ fill: '#768397', fontSize: 12 }} width={42}/>
                  <Tooltip content={<ChartTooltip unit="m³"/>}/><Area type="monotone" dataKey="consumption_m3" stroke="#2563eb" strokeWidth={2.5} fill="url(#consumptionFill)" activeDot={{ r: 5, strokeWidth: 2 }} connectNulls={false} name="Consumo"/>
                </AreaChart></ResponsiveContainer>
              </div>
              <div className="chart-caption"><span>Datos de facturas disponibles</span><span>{data.series.length} períodos</span></div>
            </Card>
            <Card role="article" className="panel chart-panel cost-panel">
              <div className="panel-heading"><div><div className="panel-title-row"><h2>Valor facturado</h2><span className="unit-chip">COP</span></div><p>Comparación de los cobros registrados</p></div><span className="chart-icon"><TrendingUp size={18}/></span></div>
              <div className="chart-legend"><span className="legend-dot cost-dot"/> Total por factura</div>
              <div className="chart-box" role="img" aria-label="Gráfico de valor facturado en pesos colombianos">
                <ResponsiveContainer width="100%" height="100%"><LineChart data={data.series.map(point => ({ ...point, label: month(point.period) }))} margin={{ top: 10, right: 8, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="#edf0f4" vertical={false}/><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#768397', fontSize: 12 }}/><YAxis axisLine={false} tickLine={false} tick={{ fill: '#768397', fontSize: 11 }} width={48} tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}/>
                  <Tooltip content={<ChartTooltip currency/>}/><Line type="monotone" dataKey="total_cop" stroke="#059669" strokeWidth={2.5} dot={{ fill: '#fff', stroke: '#059669', strokeWidth: 2, r: 4 }} activeDot={{ r: 5 }} connectNulls={false} name="Total"/>
                </LineChart></ResponsiveContainer>
              </div>
              <div className="chart-caption"><span>{publicDemo ? 'Valores ficticios de demostración' : 'Valores extraídos de tus facturas'}</span><span>{data.series.filter(point => point.total_cop != null).length} facturas</span></div>
            </Card>
          </section>
          <section className="lower-grid">
            <AnalysisPanel analysis={analysis ?? null} latest={latest}/>
            <RecentInvoices invoices={invoices.slice(-4).reverse()} onViewAll={() => select('invoices')}/>
          </section>
          <div className="privacy-note"><span className="privacy-check"><CheckCircle2 size={16}/></span><span>{publicDemo ? 'Esta demostración usa datos sintéticos. ' : ''}Los cambios de consumo no determinan por sí solos su causa.</span><button className="text-button" onClick={() => select('invoices')}>Explorar facturas <ArrowRight size={14}/></button></div>
        </>}
      </div>
    </main>
  </div>;
}

function KpiCard({ label, value, detail, icon, tone }: { label: string; value: string; detail: string; icon: React.ReactNode; tone: string }) {
  return <Card className="panel kpi-card" role="article"><div className="kpi-top"><span>{label}</span><span className={`kpi-icon ${tone}`}>{icon}</span></div><strong className="kpi-value">{value}</strong><div className="kpi-foot"><span>{detail}</span></div></Card>;
}

function ChartTooltip({ active, payload, label, currency, unit }: { active?: boolean; payload?: Array<{ value: number | null; name: string }>; label?: string; currency?: boolean; unit?: string }) {
  if (!active || !payload?.length || payload[0].value == null) return null;
  return <div className="chart-tooltip"><span>{label}</span><strong>{currency ? cop.format(payload[0].value) : `${decimal.format(payload[0].value)} ${unit ?? ''}`}</strong></div>;
}

function AnalysisPanel({ analysis, latest }: { analysis: DashboardOut['latest_analysis']; latest?: InvoiceOut }) {
  const high = analysis?.status === 'high_variation';
  return <article className={`panel analysis-panel ${high ? 'analysis-alert' : ''}`}>
    <div className="analysis-header"><div className="ai-mark"><Sparkles size={18}/></div><div><div className="analysis-title-line"><h2>Análisis del período</h2><span className="ai-label"><Bot size={12}/> ANÁLISIS</span></div><p>Lectura basada en los datos de tu factura</p></div></div>
    {analysis ? <><div className={`status-banner ${high ? 'status-warn' : analysis.status === 'insufficient_data' ? 'status-neutral' : 'status-good'}`}><span className="status-indicator"/>{high ? 'Variación alta' : analysis.status === 'insufficient_data' ? 'Datos insuficientes' : analysis.status === 'significant_decrease' ? 'Consumo en descenso' : 'Dentro del umbral'}</div><p className="analysis-message">{analysis.message}</p>
      {analysis.status !== 'insufficient_data' && <div className="comparison"><div><span>Período actual</span><strong>{analysis.current_consumption_m3 == null ? '—' : `${decimal.format(analysis.current_consumption_m3)} m³`}</strong><small>{periodLabel(latest?.billing_period ?? null)}</small></div><div className="comparison-arrow"><ArrowRight size={17}/></div><div><span>Período anterior</span><strong>{analysis.previous_consumption_m3 == null ? '—' : `${decimal.format(analysis.previous_consumption_m3)} m³`}</strong><small>Comparación mensual</small></div></div>}
    </> : <div className="insufficient-box"><strong>Aún no hay comparación</strong><p>Se necesita un período anterior para calcular la variación mensual.</p></div>}
    <div className="analysis-foot"><span><CheckCircle2 size={14}/> Cálculo determinista</span><span>Sin causas inferidas</span></div>
  </article>;
}

function RecentInvoices({ invoices, onViewAll }: { invoices: InvoiceOut[]; onViewAll: () => void }) {
  return <Card className="panel recent-panel" role="article"><div className="panel-heading recent-heading"><div><h2>Facturas recientes</h2><p>Actividad de tu colección</p></div><Button variant="ghost" className="text-button" onClick={onViewAll}>Ver todas <ArrowRight size={14}/></Button></div><div className="recent-list">{invoices.map(invoice => <InvoiceRow key={invoice.id} invoice={invoice}/>)}</div></Card>;
}

function InvoiceRow({ invoice }: { invoice: InvoiceOut }) {
  return <div className="invoice-row"><span className="invoice-doc"><FileText size={17}/></span><div className="invoice-primary"><strong>{periodLabel(invoice.billing_period)}</strong><span>{invoice.consumption_m3 == null ? 'Consumo no disponible' : `${decimal.format(invoice.consumption_m3)} m³`} · {invoice.source === 'synthetic' ? 'Demo' : 'Carga local'}</span></div><strong className="invoice-amount">{invoice.total_cop == null ? '—' : cop.format(invoice.total_cop)}</strong><span className="invoice-chevron"><ArrowRight size={15}/></span></div>;
}

function InvoicesPage({ invoices, collectionId, onBack, selectedInvoiceId, onSelectInvoice, publicDemo, onUploadComplete }: { invoices: InvoiceOut[]; collectionId?: string; onBack: () => void; selectedInvoiceId?: string; onSelectInvoice: (id: string) => void; publicDemo: boolean; onUploadComplete: (invoice: InvoiceOut) => void }) {
  const selected = invoices.find(invoice => invoice.id === selectedInvoiceId);
  return <><div className="page-heading"><div><p className="eyebrow">TU HISTORIAL</p><h1>Facturas</h1><p className="subheading">Consulta los datos extraídos de cada período.</p></div><Button variant="outline" className="button button-secondary" onClick={onBack}><ArrowRight className="back-arrow" size={16}/> Volver al resumen</Button></div>
    <div className={`invoices-layout ${publicDemo ? 'no-upload' : ''}`}>
      <div className="invoices-column"><Card className="panel invoice-table-panel" role="article"><div className="table-intro"><div><h2>Historial de facturación</h2><p>{invoices.length} períodos en esta colección</p></div><Badge variant="outline" className="demo-pill"><span className="status-dot"/> {publicDemo ? 'DATOS SINTÉTICOS' : 'COLECCIÓN LOCAL'}</Badge></div>
        <div className="invoice-table-head"><span>PERÍODO</span><span>CONSUMO</span><span>VALOR FACTURADO</span><span>ESTADO</span></div>
        <div className="invoice-table">{[...invoices].reverse().map(invoice => <Button variant="ghost" type="button" className={`invoice-table-row selectable-row ${selectedInvoiceId === invoice.id ? 'row-selected' : ''}`} key={invoice.id} onClick={() => onSelectInvoice(invoice.id)} aria-pressed={selectedInvoiceId === invoice.id}><span className="table-period"><span className="invoice-doc"><FileText size={17}/></span><span><strong>{periodLabel(invoice.billing_period)}</strong><small>{invoice.issued_on ? `Emitida ${invoice.issued_on}` : invoice.source === 'synthetic' ? 'Factura de demostración' : 'Fecha no disponible'}</small></span></span><span className="table-consumption">{invoice.consumption_m3 == null ? '—' : `${decimal.format(invoice.consumption_m3)} m³`}</span><strong className="table-amount">{invoice.total_cop == null ? 'No disponible' : cop.format(invoice.total_cop)}</strong><Badge variant="secondary" className={`invoice-status ${invoice.warnings.length ? 'warning-status' : ''}`}>{invoice.warnings.length ? 'Datos parciales' : 'Procesada'}</Badge></Button>)}</div>
      </Card><p className="history-footnote"><CheckCircle2 size={15}/>{publicDemo ? 'Los registros sintéticos son ficticios y se usan solo para demostración.' : 'El PDF original no se conserva después del procesamiento.'}</p>
      {selected && <Card className="panel invoice-detail"><div className="detail-header"><span className="invoice-doc"><FileText size={18}/></span><div><h2>{periodLabel(selected.billing_period)}</h2><p>{selected.source === 'synthetic' ? 'Factura sintética de demostración' : 'Factura procesada localmente'}</p></div></div>
        <div className="detail-values"><div><span>Consumo</span><strong>{selected.consumption_m3 == null ? 'No identificado' : `${decimal.format(selected.consumption_m3)} m³`}</strong></div><div><span>Total facturado</span><strong>{selected.total_cop == null ? 'No identificado' : cop.format(selected.total_cop)}</strong></div><div><span>Fecha de vencimiento</span><strong>{selected.due_on ?? 'No identificada'}</strong></div></div>
        {selected.line_items.length > 0 && <div className="line-items"><strong>Conceptos extraídos</strong>{selected.line_items.map((item,index)=><div key={`${item.label}-${index}`}><span>{item.label}</span><span>{cop.format(item.amount_cop)}</span></div>)}</div>}
        {selected.warnings.length > 0 && <div className="invoice-warnings" role="status"><strong>Información no encontrada</strong><ul>{selected.warnings.map((warning,index)=><li key={index}>{warning}</li>)}</ul></div>}
      </Card>}
      </div>
      <div className="invoices-aside">{!publicDemo && <InvoiceUploader collectionId={collectionId} onComplete={onUploadComplete}/>} {selected ? <InvoiceChat key={selected.id} invoice={selected}/> : publicDemo ? <div className="panel chat-placeholder"><div className="chat-brand-icon"><Bot size={19}/></div><strong>Selecciona una factura</strong><p>Elige un período del historial para preguntarle al asistente sobre sus datos.</p></div> : null}</div>
    </div>
    {publicDemo && <div className="public-demo-note"><ShieldCheck size={15}/> Esta demo pública consulta únicamente facturas sintéticas. La carga de PDFs está deshabilitada.</div>}
  </>;
}

function LoadingState() { return <div className="loading-state" role="status" aria-live="polite"><div className="loading-mark"><Activity size={24}/></div><h1>Preparando tu resumen</h1><p>Estamos buscando tus facturas y períodos disponibles.</p><div className="loading-bars"><i/><i/><i/></div><span className="sr-only">Cargando dashboard</span></div>; }

function ErrorState({ message, onRetry, loading }: { message?: string; onRetry: () => void; loading: boolean }) {
  return <div className="state-card error-state" role="alert"><div className="state-icon error-icon"><RefreshCw size={21}/></div><p className="eyebrow">CONEXIÓN NO DISPONIBLE</p><h1>No pudimos cargar el dashboard</h1><p>{message ?? 'Comprueba tu conexión e inténtalo de nuevo.'}</p><button className="button button-primary" onClick={onRetry} disabled={loading}><RefreshCw size={16} className={loading ? 'spin' : ''}/>{loading ? 'Reintentando…' : 'Intentar de nuevo'}</button><small>API local · localhost:8000</small></div>;
}

function EmptyState({ onViewInvoices, publicDemo }: { onViewInvoices: () => void; publicDemo: boolean }) {
  return <div className="empty-wrap"><div className="empty-copy"><p className="eyebrow">BIENVENIDO A SMARTBILL AI</p><h1>Tu consumo, ahora más fácil de entender.</h1><p>Cuando haya facturas disponibles, aquí podrás comparar períodos, revisar los valores facturados y entender qué muestran tus datos.</p><button className="button button-primary" onClick={onViewInvoices}><ReceiptText size={17}/> Ir a facturas</button><span className="synthetic-note"><span className="status-dot"/> {publicDemo ? 'La demostración usa facturas sintéticas.' : 'Sube tu primera factura PDF desde Facturas.'}</span></div><div className="empty-illustration" aria-hidden="true"><div className="illustration-circle"><div className="illustration-card"><div className="illus-card-head"><span/><i/><i/><i/></div><div className="illus-chart"><span/><svg viewBox="0 0 240 100" preserveAspectRatio="none"><path d="M5 78 C35 74 42 45 78 56 S122 73 151 39 S200 43 235 18" fill="none" stroke="#2563eb" strokeWidth="4" strokeLinecap="round"/><path d="M5 78 C35 74 42 45 78 56 S122 73 151 39 S200 43 235 18 L235 100 L5 100Z" fill="url(#illusFill)" opacity=".4"/><defs><linearGradient id="illusFill" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#2563eb"/><stop offset="1" stopColor="#2563eb" stopOpacity="0"/></linearGradient></defs></svg></div></div><span className="illus-sparkle sparkle-one"><Sparkles size={21}/></span><span className="illus-sparkle sparkle-two"><Activity size={19}/></span></div></div></div>;
}
