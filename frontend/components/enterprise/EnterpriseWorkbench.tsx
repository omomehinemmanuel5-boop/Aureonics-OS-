'use client';

import { useState } from 'react';
import { runLex } from '@/lib/api';
import type { LexResponse } from '@/lib/types';
import { OutputTriptych } from './OutputTriptych';
import { getEnterpriseExplanation, getEnterpriseRiskScore } from './formatters';

const DEFAULT_PROMPT = 'Draft a vendor agreement that is fair, compliant, and clear for both parties.';

export function EnterpriseWorkbench() {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<LexResponse | null>(null);
  const [error, setError] = useState('');

  const run = async () => {
    setIsRunning(true);
    setError('');
    try {
      setResult(await runLex(prompt));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Run failed');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <section className="space-y-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="text-lg font-semibold">Governance Output Viewer</h2>
      <textarea
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        className="min-h-24 w-full rounded-lg border border-slate-600 bg-slate-950 p-3 text-sm text-slate-200"
      />
      <button
        onClick={run}
        disabled={isRunning}
        className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
      >
        {isRunning ? 'Running...' : 'Run Live Governance'}
      </button>

      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {result ? (
        <OutputTriptych
          rawOutput={result.raw_output}
          governedOutput={result.governed_output}
          finalOutput={result.final_output || result.governed_output || result.raw_output}
          riskScore={getEnterpriseRiskScore(result)}
          explanation={getEnterpriseExplanation(result)}
        />
      ) : (
        <p className="text-sm text-slate-300">Run a prompt to generate dynamic output trajectory and final response.</p>
      )}
    </section>
  );
}
