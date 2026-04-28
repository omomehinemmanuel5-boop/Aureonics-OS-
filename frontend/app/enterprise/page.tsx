import { EnterprisePanels } from "@/components/enterprise/EnterprisePanels";
import { OutputTriptych } from "@/components/enterprise/OutputTriptych";

export default function EnterpriseDashboardPage() {
  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8 text-slate-100">
      <header>
        <h1 className="text-3xl font-bold">Lex Aureon Enterprise Dashboard</h1>
        <p className="text-slate-300">AI Output Governance Infrastructure Layer for multi-tenant enterprise operations.</p>
      </header>

      <OutputTriptych
        rawOutput="The original model response appears here."
        governedOutput="Potentially unsafe data has been transformed by policy controls."
        finalOutput="Final, policy-compliant response delivered to downstream consumer."
        riskScore={0.72}
        explanation="Credential leakage pattern detected; redaction and safe rewrite applied."
      />

      <EnterprisePanels />
    </main>
  );
}
