import Link from 'next/link';

const featureCards = [
  {
    title: 'Constitutional Triad',
    value: 'C · R · S',
    text: 'Continuity, Reciprocity, and Sovereignty are tracked live with each run.'
  },
  {
    title: 'Live Stability Margin',
    value: 'M(t) = min(C,R,S)',
    text: 'Every generation is scored before output is released to users.'
  },
  {
    title: 'Entropy-Aware Governor',
    value: 'ADV ↑',
    text: 'Responses with low diversity are projected back into safe sovereign bounds.'
  }
];

const pillars = [
  ['Continuity', 'Preserves state and identity memory'],
  ['Reciprocity', 'Optimizes mutual benefit and fairness'],
  ['Sovereignty', 'Defends autonomous and lawful behavior']
] as const;

export default function LandingPage() {
  return (
    <div>
      <section className="section-pad">
        <div className="container-shell grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="mb-4 inline-flex rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cyan-200">
              Aureonics Constitutional Intelligence
            </p>
            <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-6xl">
              Landing + Console for <span className="text-cyan-300">Mathematical Sovereign AI</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg text-slate-300">
              Watch every prompt pass through a visible governor, interactive metrics, and luminous intervention traces that prove why each answer is trusted.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/app" className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300">
                Open Console
              </Link>
              <Link href="/demo" className="rounded-xl border border-white/20 px-5 py-3 text-sm font-medium text-slate-100 transition hover:border-cyan-300/50 hover:bg-white/5">
                Run Demo
              </Link>
            </div>
          </div>

          <div className="glass-panel glow-border rounded-xl2 p-6">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Live Equation Panel</p>
            <div className="mt-5 space-y-3 font-mono text-sm text-slate-200">
              <p className="rounded-lg border border-cyan-300/20 bg-cyan-500/10 p-3">M(t) = min(C, R, S)</p>
              <p className="rounded-lg border border-emerald-300/20 bg-emerald-500/10 p-3">Governor Pass ⇢ M(t) ≥ τ</p>
              <p className="rounded-lg border border-amber-300/20 bg-amber-500/10 p-3">Projection ⇢ arg min ||x - x̂||₂ on simplex</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-pad">
        <div className="container-shell grid gap-4 md:grid-cols-3">
          {featureCards.map((card) => (
            <article key={card.title} className="glass-panel rounded-xl2 glow-border p-5">
              <p className="text-xs uppercase tracking-[0.15em] text-slate-400">{card.title}</p>
              <h3 className="mt-3 font-mono text-xl text-cyan-200">{card.value}</h3>
              <p className="mt-3 text-sm text-slate-300">{card.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-pad">
        <div className="container-shell rounded-xl2 glass-panel glow-border p-8">
          <h2 className="text-2xl font-semibold text-white">Why this feels powerful in practice</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {pillars.map(([name, desc], i) => (
              <div key={name} className="rounded-xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Pillar {i + 1}</p>
                <h3 className="mt-2 text-lg font-semibold text-cyan-200">{name}</h3>
                <p className="mt-2 text-sm text-slate-300">{desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 text-center">
            <Link href="/app" className="inline-flex rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-100">
              Enter the Constitutional Console
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
