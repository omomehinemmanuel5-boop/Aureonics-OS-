'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, ExternalLink, Play } from 'lucide-react';
import { computePoint, GOVERNOR_THRESHOLD, nextDriftState, stabilityMargin } from '../lib/simplex';

const plans = [
  {
    name: 'Developer',
    price: 'Free',
    desc: 'Perfect for evaluation and local prototypes.',
    points: ['100 governed calls/day', 'Basic audit logs', 'API docs + sandbox'],
    cta: { label: 'Start Free', href: '/app' },
    featured: false
  },
  {
    name: 'Team',
    price: '$499/mo',
    desc: 'For production workloads that need observability and governance proof.',
    points: ['10,000 governed calls/month', 'Full session history + intervention traces', 'Priority support + onboarding'],
    cta: { label: 'Start Trial', href: '/pricing' },
    featured: true
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    desc: 'For compliance-heavy and mission-critical deployments.',
    points: ['Unlimited governed calls', 'SLA + dedicated governance architect', 'Custom compliance artifacts'],
    cta: { label: 'Book Enterprise Call', href: '/enterprise' },
    featured: false
  }
] as const;

export default function AureonicsLanding() {
  const [simplex, setSimplex] = useState({ c: 0.33, r: 0.33, s: 0.34 });
  const [margin, setMargin] = useState(0.33);
  const [govActive, setGovActive] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let drift = 0;
    let driftDir = 0.01;
    const interval = setInterval(() => {
      const next = nextDriftState(drift, driftDir);
      drift = next.drift;
      driftDir = next.driftDir;
      const point = computePoint(drift);
      const m = stabilityMargin(point);
      setSimplex(point);
      setMargin(m);

      if (m < GOVERNOR_THRESHOLD) {
        setGovActive(true);
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => setGovActive(false), 1200);
      }
    }, 1500);

    return () => {
      clearInterval(interval);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(34,211,238,0.14),transparent_35%),radial-gradient(circle_at_80%_20%,rgba(168,85,247,0.12),transparent_35%),radial-gradient(circle_at_50%_70%,rgba(56,189,248,0.10),transparent_45%)]" />

      <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="grid h-8 w-8 place-items-center rounded bg-gradient-to-br from-cyan-400 to-purple-600 text-sm font-bold">AO</div>
            <span className="text-lg font-semibold tracking-wide">Aureonics OS</span>
          </div>
          <nav className="hidden items-center gap-6 text-sm text-slate-300 md:flex">
            <a href="#how" className="hover:text-cyan-300">How it Works</a>
            <a href="#proof" className="hover:text-cyan-300">Proof</a>
            <a href="#pricing" className="hover:text-cyan-300">Pricing</a>
          </nav>
          <Link href="/app" className="rounded bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-cyan-300">Open Console</Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:items-center lg:py-24">
        <div>
          <p className="mb-4 inline-flex rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-mono text-cyan-300">Constitutional AI Governance Runtime</p>
          <h1 className="text-4xl font-bold leading-tight sm:text-5xl lg:text-6xl">
            Ship governed AI your buyers can <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">verify</span>.
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-300">Aureonics scores every response across Continuity, Reciprocity, and Sovereignty. If the stability margin drops below threshold, the governor intervenes before failure reaches production users.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/demo" className="inline-flex items-center gap-2 rounded bg-gradient-to-r from-cyan-500 to-purple-600 px-5 py-3 font-semibold hover:opacity-95"><Play size={18} /> Run Live Demo</Link>
            <a href="#pricing" className="inline-flex items-center gap-2 rounded border border-slate-600 px-5 py-3 font-semibold hover:border-cyan-400 hover:text-cyan-300">See Pricing <ExternalLink size={16} /></a>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="mb-4 text-xs uppercase tracking-[0.2em] text-slate-400">Live governance state</p>
          <svg viewBox="0 0 300 260" className="h-64 w-full">
            <polygon points="150,20 270,240 30,240" fill="none" stroke="rgb(100,116,139)" strokeWidth="2" />
            <polygon points="150,75 230,215 70,215" fill="rgba(34, 197, 94, 0.05)" stroke="rgb(34, 197, 94)" strokeWidth="1.5" strokeDasharray="4,4" />
            <circle cx={150 + (simplex.r - simplex.s) * 60} cy={20 + (1 - simplex.c) * 200} r="7" fill={govActive ? 'rgb(239,68,68)' : 'rgb(6,182,212)'} className={govActive ? 'animate-pulse' : ''} />
          </svg>
          <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
            <MetricChip label="C" value={simplex.c} color="text-cyan-300 border-cyan-500/30" />
            <MetricChip label="R" value={simplex.r} color="text-pink-300 border-pink-500/30" />
            <MetricChip label="S" value={simplex.s} color="text-purple-300 border-purple-500/30" />
          </div>
          <div className="mt-4 rounded border border-slate-700 p-3">
            <div className="mb-2 flex justify-between text-xs font-mono"><span>Stability Margin M(t)</span><span className={margin > GOVERNOR_THRESHOLD ? 'text-green-400' : 'text-red-400'}>{margin.toFixed(3)}</span></div>
            <div className="h-2 overflow-hidden rounded bg-slate-800"><div className={`h-full ${margin > GOVERNOR_THRESHOLD ? 'bg-green-500' : 'bg-red-500'}`} style={{ width: `${Math.max(0.05, margin) * 100}%` }} /></div>
            <p className="mt-2 text-xs text-slate-400">Governor trigger τ = {GOVERNOR_THRESHOLD.toFixed(2)}</p>
          </div>
        </div>
      </section>

      <section id="how" className="mx-auto max-w-7xl border-t border-slate-800 px-4 py-16 sm:px-6">
        <h2 className="text-3xl font-bold">How this becomes an early-sale SaaS</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            ['Measure', 'Every output is scored in C/R/S and assigned a margin before release.'],
            ['Intervene', 'Low-margin generations get corrected with explicit governor traces.'],
            ['Prove', 'Audit logs and intervention artifacts become customer trust evidence.']
          ].map(([title, body]) => (
            <article key={title} className="rounded-lg border border-slate-800 bg-slate-900/40 p-5">
              <h3 className="font-semibold text-cyan-300">{title}</h3>
              <p className="mt-2 text-sm text-slate-300">{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="proof" className="mx-auto max-w-7xl border-t border-slate-800 px-4 py-16 sm:px-6">
        <h2 className="text-3xl font-bold">Proof that closes deals</h2>
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6">
            <h3 className="font-semibold">Governance Console</h3>
            <ul className="mt-4 space-y-3 text-sm text-slate-300">
              {['Real-time M(t) tracking', 'Intervention timeline + rationale', 'Session-level constitutional profile'].map((item) => (
                <li key={item} className="flex items-start gap-2"><CheckCircle2 size={16} className="mt-0.5 text-green-400" />{item}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6">
            <h3 className="font-semibold">Enterprise Readiness</h3>
            <ul className="mt-4 space-y-3 text-sm text-slate-300">
              {['Exportable compliance artifacts', 'Buyer-ready architecture + risk narrative', 'Audit-first deployment posture'].map((item) => (
                <li key={item} className="flex items-start gap-2"><CheckCircle2 size={16} className="mt-0.5 text-green-400" />{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-7xl border-t border-slate-800 px-4 py-16 sm:px-6">
        <h2 className="text-3xl font-bold">Pricing built for first revenue</h2>
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.name} className={`rounded-xl border p-6 ${plan.featured ? 'border-cyan-500/60 bg-slate-900' : 'border-slate-800 bg-slate-900/40'}`}>
              <h3 className="text-xl font-semibold">{plan.name}</h3>
              <p className="mt-2 text-3xl font-bold">{plan.price}</p>
              <p className="mt-2 text-sm text-slate-400">{plan.desc}</p>
              <ul className="mt-5 space-y-2 text-sm text-slate-300">
                {plan.points.map((point) => <li key={point} className="flex gap-2"><CheckCircle2 size={16} className="text-green-400" />{point}</li>)}
              </ul>
              <Link href={plan.cta.href} className={`mt-6 inline-block w-full rounded px-4 py-2 text-center font-semibold ${plan.featured ? 'bg-gradient-to-r from-cyan-500 to-purple-600' : 'border border-slate-600 hover:border-cyan-500'}`}>
                {plan.cta.label}
              </Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

function MetricChip({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`rounded border bg-slate-800/60 p-3 ${color}`}>
      <p className="font-mono text-xs">{label}</p>
      <p className="text-lg font-bold text-white">{(value * 100).toFixed(0)}%</p>
    </div>
  );
}
