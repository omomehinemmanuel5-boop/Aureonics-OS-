'use client';

import { LexResponse } from '@/lib/types';
import { DiffView } from './DiffView';

export function resolveFinalOutput(result: Pick<LexResponse, 'final_output' | 'governed_output' | 'raw_output'>): string {
  return result.final_output?.trim() || result.governed_output?.trim() || result.raw_output?.trim() || 'No output returned.';
}

export function OutputPanels({ result, showDiff = false }: { result: LexResponse | null; showDiff?: boolean }) {
  if (!result) return null;

  const predictedRisk = result.metrics?.predicted_risk ?? (result.intervention ? 80 : 25);
  const actualIntervention = result.metrics?.actual_intervention ?? Math.round((result.semantic_diff_score || 0) * 100);
  const finalOutput = resolveFinalOutput(result);

  return (
    <div className="space-y-6 pb-20">
      <OutputBlock title="RAW INTENT" text={result.raw_output} tone="red" />

      <TransformationHint label="Risk Detected" value={`${predictedRisk}% risk`} color="red" />

      <div className="flex justify-center py-1 opacity-30">
        <span className="text-xl text-white/80">↓</span>
      </div>

      <OutputBlock title="GOVERNED TRAJECTORY" text={result.governed_output} tone="gold" />

      {showDiff ? (
        <section className="space-y-2">
          <h3 className="text-[11px] uppercase tracking-[0.15em] text-slate-400">View Changes (RAW → GOVERNED)</h3>
          <DiffView diff={result.diff} />
        </section>
      ) : null}

      <TransformationHint label="AI Intervention Applied" value={`${actualIntervention}% governance`} color="gold" />

      <OutputBlock title="FINAL SOVEREIGN OUTPUT" text={finalOutput} tone="green" />

      <button
        onClick={async () => {
          await navigator.clipboard.writeText(finalOutput);
        }}
        className="mt-2 text-[11px] font-mono text-[#c8a84b] underline"
      >
        Share this result →
      </button>
    </div>
  );
}

function TransformationHint({ label, value, color }: { label: string; value: string; color: 'red' | 'gold' }) {
  const styles = {
    red: 'border-red-500/20 bg-red-500/5 text-red-400',
    gold: 'border-[#c8a84b]/20 bg-[#c8a84b]/5 text-[#c8a84b]',
  };

  return (
    <div className={`flex justify-between rounded border px-3 py-2 font-mono text-[11px] ${styles[color]}`}>
      <span className="opacity-70">{label}</span>
      <span>{value}</span>
    </div>
  );
}

function OutputBlock({ title, text, tone }: { title: string; text: string; tone: 'red' | 'gold' | 'green' }) {
  const color =
    tone === 'red'
      ? 'border-red-500/30 text-red-300'
      : tone === 'gold'
      ? 'border-[#c8a84b]/30 text-[#e8cc7a]'
      : 'border-green-500/30 text-green-300';

  return (
    <div className={`rounded border bg-black/50 p-3 ${color}`}>
      <div className="mb-1 text-[10px] uppercase opacity-60">{title}</div>
      <div className="whitespace-pre-wrap text-sm">{text}</div>
    </div>
  );
}
