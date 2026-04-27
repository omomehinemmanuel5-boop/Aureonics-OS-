import { LexResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_LEX_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function runLex(prompt: string): Promise<LexResponse> {
  const response = await fetch(`${API_BASE}/lex/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, bridge: true })
  });

  if (!response.ok) {
    throw new Error(`Lex request failed with status ${response.status}`);
  }

  return (await response.json()) as LexResponse;
}
