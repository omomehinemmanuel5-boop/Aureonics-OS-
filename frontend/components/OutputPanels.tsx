import { LexResponse } from '@/lib/types';

export function OutputPanels({ result }: { result: LexResponse | null }) {
  if (!result) return null;

  const panels = [
    ['Raw Output', result.raw_output, 'border-slate-300/20'],
    ['Governed Output', result.governed_output, 'border-amber-300/30'],
    ['Final Output', result.final_output, 'border-emerald-300/30']
  ] as const;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {panels.map(([label, value, border]) => (
        <article key={label} className={`min-h-48 rounded-xl2 glass-panel ${border} p-4 shadow-card`}>
          <h3 className="text-xs uppercase tracking-[0.16em] text-slate-400">{label}</h3>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-200">{value}</p>
        </article>
      ))}
    </div>
  );
}
