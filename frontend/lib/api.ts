import { LexResponse } from './types';

const API_TIMEOUT_MS = 15000;

function getRunEndpoint() {
  const apiBase = process.env.NEXT_PUBLIC_LEX_API_BASE_URL;
  if (apiBase) {
    return `${apiBase.replace(/\/$/, '')}/lex/run`;
  }

  return '/api/lex/run';
}

export async function runLex(prompt: string): Promise<LexResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  const response = await fetch(getRunEndpoint(), {
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
