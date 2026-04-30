import { LexResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_LEX_API_BASE_URL ?? 'http://127.0.0.1:8000';
const API_TIMEOUT_MS = 15000;

export async function runLex(prompt: string): Promise<LexResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  const response = await fetch(`${API_BASE}/lex/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, bridge: true }),
    cache: 'no-store',
    signal: controller.signal
  }).finally(() => clearTimeout(timeout));

  if (!response.ok) {
    throw new Error(`Lex request failed with status ${response.status}`);
  }

  return (await response.json()) as LexResponse;
}
