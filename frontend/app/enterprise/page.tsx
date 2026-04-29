import { EnterprisePanels } from "@/components/enterprise/EnterprisePanels";
import { EnterpriseWorkbench } from "@/components/enterprise/EnterpriseWorkbench";

export default function EnterpriseDashboardPage() {
  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8 text-slate-100">
      <header>
        <h1 className="text-3xl font-bold">Lex Aureon Enterprise Dashboard</h1>
        <p className="text-slate-300">AI Output Governance Infrastructure Layer for multi-tenant enterprise operations.</p>
      </header>

      <EnterpriseWorkbench />

      <EnterprisePanels />
    </main>
  );
}
