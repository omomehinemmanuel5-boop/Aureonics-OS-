import { DemoWorkbench } from '@/components/DemoWorkbench';

export default function DemoPage() {
  return (
    <section className="section-pad">
      <div className="container-shell space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">Live Demo Funnel</h1>
        <p className="text-slate-600">Run a prompt through Lex and see RAW → GOVERNED → FINAL with intervention transparency.</p>
        <DemoWorkbench mode="demo" />
      </div>
    </section>
  );
}
