'use client';

import { useState } from 'react';
import { Plan } from '@/lib/plans';

type CheckoutResponse = {
  invoice_id?: string;
  next_action?: string;
  payment_instructions?: string[];
  email_template?: string;
  error?: string;
};

export function CheckoutButton({ plan }: { plan: Exclude<Plan, 'free'> }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [buyerEmail, setBuyerEmail] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [seats, setSeats] = useState(1);

  return (
    <div className="mt-4 space-y-2">
      <input className="w-full rounded border px-2 py-1 text-xs" placeholder="Work email" value={buyerEmail} onChange={(e) => setBuyerEmail(e.target.value)} />
      <input className="w-full rounded border px-2 py-1 text-xs" placeholder="Company name" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
      <input className="w-full rounded border px-2 py-1 text-xs" type="number" min={1} max={1000} value={seats} onChange={(e) => setSeats(Number(e.target.value || '1'))} />
      <button
        onClick={async () => {
          setLoading(true);
          setMessage(null);
          const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan, buyerEmail, companyName, seats }),
          });

          const data = (await response.json()) as CheckoutResponse;

          if (!response.ok || data.error) {
            setMessage(data.error ?? 'Unable to create invoice request.');
          } else {
            const details = [
              `Invoice: ${data.invoice_id ?? 'pending'}`,
              data.next_action ?? 'Contact sales to complete payment.',
              ...(data.payment_instructions ?? []),
            ];
            setMessage(details.join(' '));
            if (data.email_template && navigator?.clipboard) {
              await navigator.clipboard.writeText(data.email_template);
            }
          }

          setLoading(false);
        }}
        disabled={loading}
        className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {loading ? 'Generating invoice…' : 'Get invoice'}
      </button>
      {message ? <p className="text-xs text-slate-600">{message}</p> : null}
    </div>
  );
}
