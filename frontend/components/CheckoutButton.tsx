'use client';

import { useState } from 'react';
import { Plan } from '@/lib/plans';

export function CheckoutButton({ plan }: { plan: Exclude<Plan, 'free'> }) {
  const [loading, setLoading] = useState(false);

  return (
    <button
      onClick={async () => {
        setLoading(true);
        const response = await fetch('/api/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ plan })
        });
        const data = (await response.json()) as { url?: string; error?: string };
        if (data.url) window.location.href = data.url;
        setLoading(false);
      }}
      disabled={loading}
      className="mt-4 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
    >
      {loading ? 'Redirecting…' : 'Checkout'}
    </button>
  );
}
