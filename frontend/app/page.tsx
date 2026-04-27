import Link from 'next/link';

const valueProps = [
  { title: 'Prevent hallucinations', text: 'Compare raw vs governed outputs to catch drift before users do.' },
  { title: 'Enforce safe output', text: 'Policy-aware intervention keeps responses bounded and auditable.' },
  { title: 'Improve response quality', text: 'Lex refines low-quality generations into stable final responses.' }
];

export default function LandingPage() {
  return (
    <div>
      <section className="section-pad">
        <div className="container-shell grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-500">AI Trust Infrastructure</p>
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">See how AI output changes before you trust it.</h1>
            <p className="mt-5 max-w-xl text-lg text-slate-600">Lex intercepts, stabilizes, and improves AI responses in real-time.</p>
            <div className="mt-8 flex gap-3">
              <Link href="/demo" className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white">Try Demo</Link>
              <a href="#live-demo" className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-medium text-slate-700">View Example</a>
            </div>
          </div>
          <div className="rounded-xl2 border border-slate-200 bg-white p-5 shadow-card">
            <p className="text-xs uppercase tracking-wide text-slate-500">Live Demo Preview</p>
            <p className="mt-3 rounded-lg bg-slate-100 p-3 text-sm">Pre-filled prompt: “Give me a policy-compliant way to handle a risky request.”</p>
            <Link href="/demo" className="mt-4 inline-flex rounded-xl bg-slate-900 px-4 py-2 text-sm text-white">Run Example</Link>
            <div className="mt-4 space-y-2 text-sm">
              <details open><summary className="font-medium">RAW</summary><p className="text-slate-600">Unsafe and unstable candidate output…</p></details>
              <details><summary className="font-medium">GOVERNED</summary><p className="text-slate-600">Policy-aligned intervention output…</p></details>
              <details><summary className="font-medium">FINAL</summary><p className="text-slate-600">Stabilized final response delivered…</p></details>
            </div>
          </div>
        </div>
      </section>

      <section id="live-demo" className="section-pad bg-slate-50">
        <div className="container-shell">
          <h2 className="text-2xl font-semibold">Value Props</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {valueProps.map((card) => (
              <article key={card.title} className="rounded-xl2 border border-slate-200 bg-white p-5 shadow-card">
                <h3 className="font-semibold">{card.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{card.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section-pad">
        <div className="container-shell">
          <h2 className="text-2xl font-semibold">How it works</h2>
          <ol className="mt-6 grid gap-4 md:grid-cols-3">
            {['Input prompt', 'Lex intervenes', 'Output improves'].map((step, i) => (
              <li key={step} className="rounded-xl2 border border-slate-200 p-5 shadow-card">
                <p className="text-xs text-slate-500">Step {i + 1}</p>
                <p className="mt-2 font-medium">{step}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section-pad bg-slate-50">
        <div className="container-shell grid gap-4 md:grid-cols-2">
          <div className="rounded-xl2 border border-slate-200 bg-white p-6 shadow-card">
            <h2 className="text-xl font-semibold">Social proof</h2>
            <p className="mt-2 text-sm text-slate-600">“Trusted by AI product teams shipping safety-critical workflows.”</p>
          </div>
          <div className="rounded-xl2 border border-slate-200 bg-white p-6 shadow-card">
            <h2 className="text-xl font-semibold">Pricing teaser</h2>
            <p className="mt-2 text-sm text-slate-600">Free / Pro / Enterprise plans designed for every stage.</p>
            <Link href="/pricing" className="mt-4 inline-flex text-sm font-medium text-slate-900 underline">View pricing</Link>
          </div>
        </div>
      </section>

      <section className="section-pad">
        <div className="container-shell rounded-xl2 border border-slate-200 bg-white p-10 text-center shadow-card">
          <h2 className="text-3xl font-semibold">Start using Lex</h2>
          <Link href="/app" className="mt-6 inline-flex rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white">Start using Lex</Link>
        </div>
      </section>
    </div>
  );
}
