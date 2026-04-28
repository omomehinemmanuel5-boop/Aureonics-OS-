import { LexResponse } from '@/lib/types';

export function MetricsBar({ result }: { result: LexResponse | null }) {
  if (!result) return null;

  const entropy = result.metrics?.entropy ?? Math.round((Number(result.semantic_diff_score) || 0) * 100);
  const meaning = result.metrics?.meaning ?? Math.round((Number(result.M) || 0) * 100);
  const predictedRisk = result.metrics?.predicted_risk ?? (result.intervention ? 80 : 25);
  const actualIntervention = result.metrics?.actual_intervention ?? entropy;

  return (
    <div className="w-full border-y border-[#c8a84b]/20 bg-black/40 px-6 py-4 backdrop-blur-md">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-widest text-white/40">System Status</span>
        <span
          className={`rounded-full border px-2 py-[2px] font-mono text-[11px] ${
            result.intervention
              ? 'border-[#e85555]/30 bg-[#e85555]/10 text-[#e85555]'
              : 'border-[#2ec98a]/30 bg-[#2ec98a]/10 text-[#2ec98a]'
          }`}
        >
          {result.intervention ? 'INTERVENED' : 'STABLE'}
        </span>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-[#c8a84b]/60">Entropy Sacrificed</span>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-xl text-[#c8a84b]">{entropy}%</span>
            <div className="h-1 w-12 overflow-hidden rounded-full bg-[#c8a84b]/10">
              <div style={{ width: `${Math.min(100, Math.max(0, entropy))}%` }} className="h-full bg-[#c8a84b]" />
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[10px] uppercase tracking-widest text-white/40">Meaning Preserved</span>
          <div className="flex flex-row-reverse items-baseline gap-2">
            <span className="font-mono text-xl text-white/90">{meaning}%</span>
            <div className="h-1 w-12 overflow-hidden rounded-full bg-white/10">
              <div style={{ width: `${Math.min(100, Math.max(0, meaning))}%` }} className="h-full bg-white/60" />
            </div>
          </div>
        </div>
      </div>

      <details className="mt-3">
        <summary className="cursor-pointer text-[10px] uppercase tracking-widest text-white/30">View Analysis</summary>
        <div className="mt-2 space-y-1 font-mono text-[11px] text-white/60">
          <div>Predicted Risk: {predictedRisk}%</div>
          <div>Actual Intervention: {actualIntervention}%</div>
          <div>Governance Work Done: {actualIntervention}%</div>
        </div>
      </details>
    </div>
  );
}
