import { LexResponse } from '@/lib/types';

export function OutputPanels({ result }: { result: LexResponse | null }) {
  if (!result) return null;

  const panels = [
    ['Raw Output', result.raw_output],
    ['Governed Output', result.governed_output],
    ['Final Output', result.final_output]
  ] as const;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {panels.map(([label, value]) => (
        <article key={label} className="min-h-40 rounded-xl2 border border-slate-200 bg-white p-4 shadow-card">
          <h3 className="text-sm font-semibold text-slate-900">{label}</h3>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{value}</p>
        </article>
      ))}
    </div>
  );
}
