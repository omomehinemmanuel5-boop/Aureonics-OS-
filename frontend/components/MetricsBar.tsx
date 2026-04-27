import { LexResponse } from '@/lib/types';

export function MetricsBar({ result }: { result: LexResponse | null }) {
  if (!result) return null;

  const entropySacrifice = Math.max(0, Math.min(1, Number(result.semantic_diff_score) || 0));
  const preservedMeaning = Math.max(0, 1 - entropySacrifice);

  return (
    <div className="grid gap-3 md:grid-cols-4">
      <Metric label="Governor" value={result.intervention ? 'INTERVENED' : 'NO INTERVENTION'} accent={result.intervention ? 'text-amber-200' : 'text-emerald-200'} progress={result.intervention ? 0.86 : 0.24} />
      <Metric label="Raw → Governed" value={result.intervention ? 'Trajectory redirected' : 'Trajectory preserved'} accent="text-cyan-200" progress={result.intervention ? 0.78 : 0.18} />
      <Metric label="Meaning Preserved" value={`${Math.round(preservedMeaning * 100)}%`} accent="text-violet-200" progress={preservedMeaning} />
      <Metric label="Entropy Sacrificed" value={`${Math.round(entropySacrifice * 100)}%`} accent="text-rose-200" progress={entropySacrifice} />
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
