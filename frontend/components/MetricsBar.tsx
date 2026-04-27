import { LexResponse } from '@/lib/types';

export function MetricsBar({ result }: { result: LexResponse | null }) {
  if (!result) return null;

  const safety = Math.min(1, Math.max(0, Number(result.M) || 0));

  return (
    <div className="grid gap-3 md:grid-cols-5">
      <Metric label="Intervention" value={result.intervention ? 'PROJECTED' : 'CLEAR'} accent="text-amber-200" progress={result.intervention ? 0.84 : 0.22} />
      <Metric label="Stability M(t)" value={result.M.toFixed(4)} accent="text-emerald-200" progress={safety} />
      <Metric label="Semantic Δ" value={result.semantic_diff_score.toFixed(4)} accent="text-cyan-200" progress={Math.min(1, result.semantic_diff_score)} />
      <Metric label="Governor Reason" value={result.intervention_reason} accent="text-violet-200" progress={0.7} />
      <Metric label="Constitutional Gate" value={safety >= 0.05 ? 'PASS' : 'HOLD'} accent={safety >= 0.05 ? 'text-emerald-200' : 'text-rose-200'} progress={safety >= 0.05 ? 1 : 0.2} />
    </div>
  );
}

function Metric({ label, value, accent, progress }: { label: string; value: string; accent: string; progress: number }) {
  return (
    <div className="rounded-xl2 glass-panel border border-white/10 p-4 shadow-card">
      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-400">{label}</p>
      <p className={`mt-2 text-sm font-medium ${accent}`}>{value}</p>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-violet-300 to-emerald-300" style={{ width: `${Math.round(progress * 100)}%` }} />
      </div>
    </div>
  );
}
