import { describe, expect, it } from 'vitest';
import { POST } from '@/app/api/checkout/route';

function req(body: unknown) {
  return new Request('http://localhost/api/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

describe('checkout api route', () => {
  it('returns manual invoice payload for valid pro plan', async () => {
    const response = await POST(req({ plan: 'pro', buyerEmail: 'ceo@acme.com', companyName: 'Acme' }) as never);
    expect(response.status).toBe(200);
    const data = (await response.json()) as Record<string, unknown>;

    expect(data.checkout_mode).toBe('manual_invoice');
    expect(data.plan).toBe('pro');
    expect(data.amount_usd).toBe(15);
    expect(typeof data.invoice_id).toBe('string');
    expect((data.invoice_id as string).startsWith('LEX-PRO-')).toBe(true);
    expect(Array.isArray(data.payment_instructions)).toBe(true);
  });

  it('rejects invalid plans', async () => {
    const response = await POST(req({ plan: 'free' }) as never);
    expect(response.status).toBe(400);
    const data = (await response.json()) as Record<string, unknown>;
    expect(data.error).toBe('Invalid plan requested');
  });
});
