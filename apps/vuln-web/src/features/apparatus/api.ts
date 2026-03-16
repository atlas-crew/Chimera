import { API_BASE_URL } from '../../lib/config';

export interface ApparatusStatusResponse {
  enabled: boolean;
  configured: boolean;
  reachable: boolean;
  baseUrl: string;
  health: { status: string } | null;
  ghosts: {
    running?: boolean;
    rps?: number;
    duration?: number;
    stats?: Record<string, unknown> | null;
  } | null;
  error?: string;
  message?: string;
}

export interface ApparatusHistoryEntry {
  id?: string;
  method?: string;
  path?: string;
  statusCode?: number;
  timestamp?: string;
  latencyMs?: number;
}

export interface ApparatusHistoryResponse {
  count: number;
  entries: ApparatusHistoryEntry[];
}

export interface ApparatusGhostStartRequest {
  rps?: number;
  duration?: number;
  endpoints?: string[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof body === 'object' && body && 'message' in body
      ? String((body as { message: unknown }).message)
      : `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return body as T;
}

export function getApparatusStatus() {
  return request<ApparatusStatusResponse>('/api/v1/integrations/apparatus/status');
}

export function getApparatusHistory(limit = 10) {
  return request<ApparatusHistoryResponse>(`/api/v1/integrations/apparatus/history?limit=${limit}`);
}

export function startApparatusGhosts(payload: ApparatusGhostStartRequest) {
  return request<Record<string, unknown>>('/api/v1/integrations/apparatus/ghosts/start', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export function stopApparatusGhosts() {
  return request<Record<string, unknown>>('/api/v1/integrations/apparatus/ghosts/stop', {
    method: 'POST',
  });
}
