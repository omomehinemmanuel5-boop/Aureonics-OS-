'use client';

import { useState } from 'react';
import { Plan } from '@/lib/plans';

type CheckoutResponse = {
  invoice_id?: string;
  next_action?: string;
  payment_instructions?: string[];
  error?: string;
};

export function CheckoutButton({ plan }: { plan: Exclude<Plan, 'free'> }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  return (
    <div className="mt-4 space-y-2">
      <button
        onClick={async () => {
          setLoading(true);
          setMessage(null);
          const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan }),
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
