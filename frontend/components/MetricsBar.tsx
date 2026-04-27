import { LexResponse } from '@/lib/types';

export function MetricsBar({ result }: { result: LexResponse | null }) {
  if (!result) return null;

  return (
    <div className="grid gap-3 sm:grid-cols-4">
      <Metric label="Intervention" value={result.intervention ? 'INTERVENED' : 'PASS'} />
      <Metric label="M Score" value={String(result.M)} />
      <Metric label="Diff Score" value={String(result.semantic_diff_score)} />
      <Metric label="Reason" value={result.intervention_reason} />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl2 border border-slate-200 bg-white p-4 shadow-card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-medium text-slate-800">{value}</p>
    </div>
  );
}
