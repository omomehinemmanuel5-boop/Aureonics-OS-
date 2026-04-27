'use client';

import { useMemo, useState } from 'react';
import { runLex } from '@/lib/api';
import { LexResponse } from '@/lib/types';
import { canRun, getOrCreateUser, persistUser } from '@/lib/usage';
import { PromptBox } from './PromptBox';
import { OutputPanels } from './OutputPanels';
import { MetricsBar } from './MetricsBar';
import { PaywallModal } from './PaywallModal';

type DemoWorkbenchProps = {
  mode: 'demo' | 'app';
};

export function DemoWorkbench({ mode }: DemoWorkbenchProps) {
  const [prompt, setPrompt] = useState('Outline risks of blindly trusting AI outputs in customer support.');
  const [result, setResult] = useState<LexResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [copyStatus, setCopyStatus] = useState('');
  const user = useMemo(() => getOrCreateUser(), []);

  const onRun = async () => {
    const freshUser = getOrCreateUser();
    if (!canRun(freshUser.plan, freshUser.usage_count)) {
      setPaywallOpen(true);
      return;
    }

    setIsRunning(true);
    setCopyStatus('');
    try {
      const payload = await runLex(prompt);
      setResult(payload);
      const updated = { ...freshUser, usage_count: freshUser.usage_count + 1 };
      persistUser(updated);
    } catch (error) {
      setCopyStatus(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setIsRunning(false);
    }
  };

  const summary = result
    ? `Prompt: ${prompt.slice(0, 110)}\nLex Result: ${result.intervention ? 'INTERVENED' : 'PASS'}\nOutput improved by ${Math.round(
        result.semantic_diff_score * 100
      )}%`
    : '';

  const shareCardText = result
    ? `Lex intercepted AI instability.\nPrompt snippet: ${prompt.slice(0, 100)}\nIntervention: ${
        result.intervention ? 'Yes' : 'No'
      }\nImprovement summary: M=${result.M}, diff=${result.semantic_diff_score}`
    : '';

  return (
    <div className="space-y-6">
      <div className="rounded-xl2 border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        Usage: {getOrCreateUser().usage_count} / {user.plan === 'free' ? 10 : user.plan === 'pro' ? 500 : 100000} runs today ({user.plan.toUpperCase()} plan)
      </div>

      <PromptBox prompt={prompt} setPrompt={setPrompt} onRun={onRun} isRunning={isRunning} buttonText={mode === 'demo' ? 'Run Example' : 'Run Governed Output'} />
      <MetricsBar result={result} />
      <OutputPanels result={result} />

      {mode === 'demo' && result ? (
        <section className="rounded-xl2 border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-lg font-semibold">🔥 Share Card Block</h2>
          <p className="mt-2 text-sm text-slate-600">Lex intercepted AI instability.</p>
          <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-700">{shareCardText}</pre>
          <button
            onClick={async () => {
              await navigator.clipboard.writeText(shareCardText);
              setCopyStatus('Share card copied.');
            }}
            className="mt-3 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white"
          >
            Copy to clipboard
          </button>
        </section>
      ) : null}

      {result ? (
        <section className="rounded-xl2 border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-lg font-semibold">Share Result</h2>
          <button
            onClick={async () => {
              await navigator.clipboard.writeText(summary);
              setCopyStatus('Result copied.');
            }}
            className="mt-3 rounded-xl border border-slate-300 px-4 py-2 text-sm"
          >
            Share Result
          </button>
        </section>
      ) : null}

      {copyStatus ? <p className="text-sm text-slate-600">{copyStatus}</p> : null}
      <PaywallModal open={paywallOpen} onClose={() => setPaywallOpen(false)} />
    </div>
  );
}
