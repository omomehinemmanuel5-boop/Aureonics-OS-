'use client';

import { LexDiffChunk } from '@/lib/types';

export function DiffView({ diff }: { diff?: LexDiffChunk[] }) {
  if (!diff || diff.length === 0) {
    return <p className="text-xs text-slate-400">No governance diff available for this run.</p>;
  }

  return (
    <div className="rounded-lg border border-white/10 bg-black/20 p-3 text-sm leading-relaxed text-slate-100">
      {diff.map((chunk, idx) => {
        const cls =
          chunk.type === 'removed'
            ? 'text-rose-300 line-through decoration-rose-400/80'
            : chunk.type === 'added'
            ? 'text-emerald-300'
            : 'text-slate-200';
        return (
          <span key={`${chunk.type}-${idx}`} className={`${cls} break-words`}>
            {chunk.text}{' '}
          </span>
        );
      })}
    </div>
  );
}
