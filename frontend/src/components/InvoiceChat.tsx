import { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Bot, Check, LoaderCircle, MessageCircle, Send, Sparkles, UserRound } from 'lucide-react';
import { ApiRequestError, sendChatMessage } from '../lib/api';
import type { ChatResponse, InvoiceOut } from '../types/api';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card } from './ui/card';

type Message = { role: 'user'; text: string } | { role: 'assistant'; text: string; response: ChatResponse };
const suggestions = ['¿Cuánto consumí?', '¿Qué conceptos aparecen?', '¿Por qué cambió mi consumo?'];

export default function InvoiceChat({ invoice }: { invoice: InvoiceOut }) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const mutation = useMutation({ mutationFn: (text: string) => sendChatMessage({ invoice_id: invoice.id, question: text }) });

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'nearest' }); }, [messages.length, mutation.isPending]);
  useEffect(() => { setMessages([]); setQuestion(''); mutation.reset(); }, [invoice.id]);

  const ask = (raw: string) => {
    const text = raw.trim();
    if (!text || mutation.isPending) return;
    setMessages(previous => [...previous, { role: 'user', text }]);
    setQuestion('');
    mutation.mutate(text, { onSuccess: response => setMessages(previous => [...previous, { role: 'assistant', text: response.answer, response }]) });
  };

  return <Card className="chat-panel panel" role="region" aria-labelledby="chat-title">
    <header className="chat-header"><div className="chat-brand-icon"><Bot size={19}/></div><div className="chat-heading"><h2 id="chat-title">Pregunta sobre esta factura</h2><p>Respuestas basadas en los datos estructurados.</p></div><span className="chat-session-pill"><span/> Sesión actual</span></header>
    <div className="chat-context"><MessageCircle size={14}/><span>Consultando: <strong>{invoice.billing_period || 'período sin identificar'}</strong></span></div>
    <div className="chat-messages" aria-live="polite" aria-relevant="additions text">
      {messages.length === 0 ? <div className="chat-welcome"><span className="welcome-spark"><Sparkles size={18}/></span><strong>¿Qué quieres entender?</strong><p>Pregúntame por el consumo, los cobros o la variación de esta factura.</p><div className="suggestions">{suggestions.map(item => <Button variant="outline" className="suggestion-chip" key={item} type="button" onClick={() => ask(item)}>{item}</Button>)}</div></div> : messages.map((message, index) => <div className={`chat-message ${message.role}`} key={`${message.role}-${index}`}><span className="message-avatar">{message.role === 'assistant' ? <Bot size={15}/> : <UserRound size={15}/>}</span><div className="message-content"><div className="message-bubble">{message.text}</div>{message.role === 'assistant' && <div className="message-meta"><Badge variant="outline" className={`mode-tag ${message.response.mode}`}><span className="status-dot"/>{message.response.mode === 'demo' ? 'Modo demostración' : 'DigitalOcean'}</Badge>{message.response.evidence.length > 0 && <details className="evidence-details"><summary><Check size={12}/> Evidencia</summary><ul>{message.response.evidence.map((evidence, evidenceIndex) => <li key={evidenceIndex}>{evidence}</li>)}</ul></details>}</div>}</div></div>)}
      {mutation.isPending && <div className="chat-message assistant"><span className="message-avatar"><Bot size={15}/></span><div className="message-bubble typing"><LoaderCircle size={14} className="spin"/> Revisando los datos…</div></div>}
      <div ref={bottomRef}/>
    </div>
    {mutation.isError && <div className="chat-error" role="alert"><span>{mutation.error instanceof ApiRequestError && mutation.error.status === 503 ? 'El servicio de respuesta no está disponible ahora.' : mutation.error instanceof Error ? mutation.error.message : 'No se pudo enviar la pregunta.'}</span><Button variant="link" type="button" onClick={() => { const lastQuestion = [...messages].reverse().find(message => message.role === 'user'); if (lastQuestion) mutation.mutate(lastQuestion.text, { onSuccess: response => setMessages(previous => [...previous, { role: 'assistant', text: response.answer, response }]) }); }}>Reintentar</Button></div>}
    <form className="chat-form" onSubmit={event => { event.preventDefault(); ask(question); }}><label className="sr-only" htmlFor={`question-${invoice.id}`}>Tu pregunta sobre esta factura</label><textarea id={`question-${invoice.id}`} value={question} maxLength={2000} rows={1} placeholder="Escribe tu pregunta…" onChange={event => setQuestion(event.currentTarget.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); ask(question); } }} disabled={mutation.isPending}/><Button type="submit" className="send-button" aria-label="Enviar pregunta" disabled={!question.trim() || mutation.isPending}><Send size={16}/></Button></form>
    <p className="chat-disclaimer">Cada respuesta indica si se generó en modo demostración o con DigitalOcean Inference. Las respuestas no determinan la causa del consumo.</p>
  </Card>;
}
