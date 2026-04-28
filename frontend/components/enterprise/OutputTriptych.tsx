import React from "react";

type Props = {
  rawOutput: string;
  governedOutput: string;
  finalOutput: string;
  riskScore: number;
  explanation: string;
};

export function OutputTriptych({ rawOutput, governedOutput, finalOutput, riskScore, explanation }: Props) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="text-lg font-semibold">Governance Output Viewer</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <Panel title="RAW AI OUTPUT" value={rawOutput} />
        <Panel title="GOVERNED OUTPUT" value={governedOutput} />
        <Panel title="FINAL OUTPUT" value={finalOutput} />
      </div>
      <div className="mt-4 rounded-lg bg-slate-800 p-3 text-sm">
        <p><span className="font-semibold">Risk Score:</span> {riskScore.toFixed(2)}</p>
        <p><span className="font-semibold">Explanation:</span> {explanation}</p>
      </div>
    </section>
  );
}

function Panel({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-950 p-3">
      <h3 className="text-xs font-bold text-sky-300">{title}</h3>
      <p className="mt-2 whitespace-pre-wrap text-sm text-slate-200">{value}</p>
    </div>
  );
}
