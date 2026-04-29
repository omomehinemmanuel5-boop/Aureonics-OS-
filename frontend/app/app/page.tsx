import { DemoWorkbench } from '@/components/DemoWorkbench';

export default function AppDashboardPage() {
  return (
    <section className="section-pad">
      <div className="container-shell space-y-6">
        <div className="rounded-xl2 glass-panel glow-border p-4 text-sm text-slate-300">
          <span className="font-semibold text-cyan-200">Constitutional Console:</span> run prompts, inspect raw/governed/final outputs, and view stability math in real time with no sign-in or trial gate.
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Aureonics Sovereign Console</h1>
        <p className="text-slate-300">Interactive glowing controls + mathematical traces to explain every intervention decision.</p>
        <DemoWorkbench mode="app" />
      </div>
    </section>
  );
}
