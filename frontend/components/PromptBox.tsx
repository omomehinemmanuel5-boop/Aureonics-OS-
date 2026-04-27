'use client';

type PromptBoxProps = {
  prompt: string;
  setPrompt: (value: string) => void;
  onRun: () => void;
  isRunning: boolean;
  buttonText?: string;
  chips?: string[];
  threatPreview?: { c: number; r: number; s: number };
};

export function PromptBox({
  prompt,
  setPrompt,
  onRun,
  isRunning,
  buttonText = 'Run Prompt',
  chips = [],
  threatPreview
}: PromptBoxProps) {
  const showThreat = threatPreview && (threatPreview.c !== 0 || threatPreview.r !== 0 || threatPreview.s !== 0);

  return (
    <div className="rounded-xl2 glass-panel glow-border p-5 shadow-card">
      <label htmlFor="prompt" className="mb-2 block text-xs uppercase tracking-[0.15em] text-slate-400">
        Sovereign Prompt Console
      </label>
      <textarea
        id="prompt"
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        className="h-32 w-full rounded-xl border border-white/10 bg-slate-950/70 p-3 text-sm text-slate-100 outline-none ring-0 transition focus:border-cyan-300/60"
      />

      {showThreat ? (
        <div className="mt-3 rounded-lg border border-amber-300/30 bg-amber-500/10 p-3 text-xs text-slate-200">
          <p className="mb-2 uppercase tracking-[0.16em] text-amber-200">Impact Preview</p>
          <div className="grid gap-2 sm:grid-cols-3">
            <ThreatItem label="ΔC" value={threatPreview.c} />
            <ThreatItem label="ΔR" value={threatPreview.r} />
            <ThreatItem label="ΔS" value={threatPreview.s} />
          </div>
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        {chips.map((chip) => (
          <button
            key={chip}
            onClick={() => setPrompt(chip)}
            className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-slate-300 transition hover:border-cyan-300/60 hover:text-cyan-200"
          >
            {chip}
          </button>
        ))}
      </div>

      <button
        onClick={onRun}
        disabled={isRunning || !prompt.trim()}
        className="mt-4 inline-flex rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isRunning ? 'Governor evaluating…' : buttonText}
      </button>
    </div>
  );
}

function ThreatItem({ label, value }: { label: string; value: number }) {
  const tone = value > 0 ? 'text-emerald-300' : value < 0 ? 'text-rose-300' : 'text-slate-400';
  const sign = value > 0 ? '+' : '';

  return (
    <p className="rounded border border-white/10 bg-black/20 p-2 font-mono text-xs">
      <span className="text-slate-400">{label}:</span> <span className={tone}>{sign}{value.toFixed(2)}</span>
    </p>
  );
}
