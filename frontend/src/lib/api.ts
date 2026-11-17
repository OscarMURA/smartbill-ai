import type { DashboardOut } from '../types/dashboard';
import type { ApiError, ChatRequest, ChatResponse, InvoiceOut } from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export interface AuthUser { id: number | string; email: string; csrf_token: string }
let csrfToken: string | null = null;
export function setCsrfToken(token: string | null) { csrfToken = token; }

export async function register(email: string, password: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE}/api/auth/register`, { method: 'POST', credentials: 'include', headers: { Accept: 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<AuthUser>;
}
export async function login(email: string, password: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE}/api/auth/login`, { method: 'POST', credentials: 'include', headers: { Accept: 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<AuthUser>;
}
export async function getMe(): Promise<AuthUser> {
  const response = await fetch(`${API_BASE}/api/auth/me`, { credentials: 'include', headers: { Accept: 'application/json' } });
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<AuthUser>;
}
export async function logout(): Promise<void> {
  const response = await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include', headers: { Accept: 'application/json', ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}) } });
  if (!response.ok) throw await parseError(response);
}

export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(message: string, status: number, code = 'request_failed') {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.code = code;
  }
}

export async function getDashboard(signal?: AbortSignal, collectionId?: string): Promise<DashboardOut> {
  let response: Response;
  try {
    const query = collectionId ? `?collection_id=${encodeURIComponent(collectionId)}` : '';
    response = await fetch(`${API_BASE}/api/dashboard${query}`, { signal, credentials: 'include', headers: { Accept: 'application/json' } });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiRequestError('No pudimos conectar con SmartBill AI. Revisa que el servidor esté activo.', 0, 'network_error');
  }
  if (!response.ok) {
    let payload: ApiError | null = null;
    try { payload = await response.json() as ApiError; } catch { /* El servidor puede responder sin JSON. */ }
    throw new ApiRequestError(payload?.error?.message ?? `No se pudo cargar el dashboard (${response.status}).`, response.status, payload?.error?.code);
  }
  return response.json() as Promise<DashboardOut>;
}

async function parseError(response: Response): Promise<ApiRequestError> {
  let payload: ApiError | null = null;
  try { payload = await response.json() as ApiError; } catch { /* Respuesta no JSON */ }
  return new ApiRequestError(payload?.error?.message ?? `La solicitud falló (${response.status}).`, response.status, payload?.error?.code);
}

export async function uploadInvoice(file: File, collectionId?: string): Promise<InvoiceOut> {
  const form = new FormData();
  form.append('file', file);
  if (collectionId) form.append('collection_id', collectionId);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/invoices/upload`, { method: 'POST', body: form, credentials: 'include', headers: { Accept: 'application/json', ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}) } });
  } catch {
    throw new ApiRequestError('No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.', 0, 'network_error');
  }
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<InvoiceOut>;
}

export async function sendChatMessage(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST', signal, credentials: 'include', headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}) }, body: JSON.stringify(request),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiRequestError('No pudimos conectar con el asistente. Revisa que el servidor esté activo.', 0, 'network_error');
  }
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<ChatResponse>;
}
