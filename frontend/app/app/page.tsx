import Link from 'next/link';
import { DemoWorkbench } from '@/components/DemoWorkbench';

export default function AppDashboardPage() {
  return (
    <section className="section-pad">
      <div className="container-shell space-y-6">
        <div className="rounded-xl2 border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Free tier reached? <Link href="/pricing" className="underline">Upgrade to unlock higher daily runs.</Link>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Lex Dashboard</h1>
        <p className="text-slate-600">PromptBox + output panels + metrics for paying users.</p>
        <DemoWorkbench mode="app" />
      </div>
    </section>
  );
}
