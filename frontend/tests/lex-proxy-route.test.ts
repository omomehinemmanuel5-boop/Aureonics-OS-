import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { NextRequest } from 'next/server';

import { POST } from '../app/api/lex/run/route';

describe('lex proxy route', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    delete process.env.LEX_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_LEX_API_BASE_URL;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('forwards request body and propagates upstream status/content-type', async () => {
    process.env.LEX_API_BASE_URL = 'https://backend.example.com';
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 201,
        headers: { 'Content-Type': 'application/json; charset=utf-8' }
      })
    );

    const req = new NextRequest('http://localhost/api/lex/run', {
      method: 'POST',
      body: JSON.stringify({ prompt: 'hello', bridge: true }),
      headers: { 'Content-Type': 'application/json' }
    });

    const res = await POST(req);

    expect(fetchMock).toHaveBeenCalledWith('https://backend.example.com/lex/run', expect.objectContaining({ method: 'POST' }));
    expect(res.status).toBe(201);
    expect(res.headers.get('Content-Type')).toContain('application/json');
    await expect(res.json()).resolves.toEqual({ ok: true });
  });

  it('returns 502 JSON when upstream is unreachable', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('connection refused'));

    const req = new NextRequest('http://localhost/api/lex/run', {
      method: 'POST',
      body: JSON.stringify({ prompt: 'hello', bridge: true }),
      headers: { 'Content-Type': 'application/json' }
    });

    const res = await POST(req);

    expect(res.status).toBe(502);
    await expect(res.json()).resolves.toMatchObject({
      error: 'Failed to reach Lex backend'
    });
  });
});
