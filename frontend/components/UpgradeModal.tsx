'use client';

type UpgradeModalProps = {
  onClose?: () => void;
};

export function UpgradeModal({ onClose }: UpgradeModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-6 text-white shadow-2xl">
        <h2 className="text-2xl font-semibold">You’ve reached your limit</h2>
        <p className="mt-3 text-sm text-slate-300">
          You’ve used your 10 free runs today. Upgrade to continue using governed AI outputs.
        </p>

        <div className="mt-6 grid gap-3">
          <a
            href="https://wa.me/YOUR_NUMBER"
            target="_blank"
            rel="noreferrer"
            className="w-full rounded-xl bg-emerald-500 px-4 py-3 text-center font-medium text-black transition hover:bg-emerald-400"
          >
            Upgrade via WhatsApp
          </a>
          <a
            href="mailto:you@lexaureon.com"
            className="w-full rounded-xl border border-white/20 px-4 py-3 text-center font-medium transition hover:bg-white/10"
          >
            Upgrade via Email
          </a>
          {onClose ? (
            <button onClick={onClose} className="text-xs text-slate-400 underline underline-offset-4">
              Close
            </button>
          ) : null}
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">Early access — $10</p>
      </div>
    </div>
  );
}
