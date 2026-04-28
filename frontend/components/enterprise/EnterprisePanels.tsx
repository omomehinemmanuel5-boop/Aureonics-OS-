import React from "react";

export function EnterprisePanels() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Panel title="Audit Log Viewer" description="Review immutable traces and export CSV/PDF records for compliance reviews." />
      <Panel title="Governance Metrics" description="Track risk reduction score, meaning preserved score, and intervention trends." />
      <Panel title="Policy Editor" description="Create and tune enterprise policies with RBAC-restricted controls." />
      <Panel title="API Key Management" description="Issue scoped API keys per environment with org-level rotation controls." />
    </div>
  );
}

function Panel({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-slate-300">{description}</p>
    </div>
  );
}
