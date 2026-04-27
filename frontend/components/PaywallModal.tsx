'use client';

import Link from 'next/link';

export function PaywallModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-md rounded-xl2 bg-white p-6 shadow-card">
        <h2 className="text-lg font-semibold">Free Tier Limit Reached</h2>
        <p className="mt-2 text-sm text-slate-600">Upgrade to Pro to continue running governed outputs.</p>
        <div className="mt-5 flex gap-3">
          <Link href="/pricing" className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white">
            Upgrade Now
          </Link>
          <button onClick={onClose} className="rounded-xl border border-slate-300 px-4 py-2 text-sm">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
