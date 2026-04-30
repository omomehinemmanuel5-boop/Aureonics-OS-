import { describe, expect, it, vi } from 'vitest';

import robots from '../app/robots';
import sitemap from '../app/sitemap';
import { runLex } from '../lib/api';

describe('SEO metadata routes', () => {
  it('returns a sitemap with primary product routes', () => {
    const map = sitemap();
    const urls = map.map((entry) => entry.url);
    expect(urls).toContain('https://lex.aureonics.ai/');
    expect(urls).toContain('https://lex.aureonics.ai/app');
    expect(urls).toContain('https://lex.aureonics.ai/pricing');
  });

  it('returns robots directives with sitemap reference', () => {
    const rules = robots();
    expect(rules.sitemap).toBe('https://lex.aureonics.ai/sitemap.xml');
  });
});

describe('runLex API behavior', () => {
  it('uses explicit public API base URL when configured', async () => {
    process.env.NEXT_PUBLIC_LEX_API_BASE_URL = 'https://api.example.com';

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ final_output: 'ok' })
    });
    vi.stubGlobal('fetch', fetchMock);

    await runLex('hello');

    expect(fetchMock.mock.calls[0][0]).toBe('https://api.example.com/lex/run');
    delete process.env.NEXT_PUBLIC_LEX_API_BASE_URL;
  });

  it('sends no-store request and returns parsed response', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ final_output: 'ok' })
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await runLex('hello');
    expect(result.final_output).toBe('ok');
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/lex/run');
    expect(options.cache).toBe('no-store');
    expect(options.method).toBe('POST');
  });
});
