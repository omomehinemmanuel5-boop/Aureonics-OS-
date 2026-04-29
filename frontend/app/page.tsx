'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ExternalLink, Play } from 'lucide-react';
import { computePoint, GOVERNOR_THRESHOLD, nextDriftState, stabilityMargin } from '../lib/simplex';

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
        timeoutRef.current = setTimeout(() => setGovActive(false), 1000);
      }
    }, 1500);

    return () => {
      clearInterval(interval);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <div className="min-h-screen overflow-hidden bg-slate-950 text-white">
      <div className="fixed inset-0 opacity-20">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 via-transparent to-purple-500/20" />
        <div className="absolute left-1/4 top-0 h-96 w-96 animate-pulse rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 h-96 w-96 animate-pulse rounded-full bg-purple-500/10 blur-3xl [animation-delay:1s]" />
      </div>

      <nav className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-gradient-to-br from-cyan-400 to-purple-600 text-sm font-bold">AO</div>
            <span className="text-xl font-bold tracking-tight">Aureonics OS</span>
          </div>
          <div className="flex items-center gap-4 text-sm sm:gap-6">
            <a href="#research" className="text-slate-300 transition hover:text-white">Research</a>
            <a href="#product" className="text-slate-300 transition hover:text-white">Product</a>
            <a href="#pricing" className="text-slate-300 transition hover:text-white">Pricing</a>
            <a aria-label="Aureonics GitHub repository" href="https://github.com/omomehinemmanuel5-boop/Aureonics-OS-" target="_blank" rel="noopener noreferrer" className="text-slate-400 transition hover:text-cyan-400">
              <span aria-hidden="true">↗</span>
            </a>
          </div>
        </div>
      </nav>

      <section className="relative z-10 mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:gap-16 lg:py-24">
        <div>
          <div className="mb-6 inline-block rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 font-mono text-sm text-cyan-300">Constitutional AI Runtime</div>
          <h1 className="mb-6 text-4xl font-bold leading-tight sm:text-5xl lg:text-6xl">
            AI that <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">reasons,</span> checks itself, then ships.
          </h1>
          <p className="mb-8 text-lg leading-relaxed text-slate-300 sm:text-xl">Every request measured across three constitutional dimensions. When the system drifts, the governor intervenes before users see instability.</p>
          <div className="flex flex-wrap gap-4">
            <Link href="/app" className="flex items-center gap-2 rounded bg-gradient-to-r from-cyan-500 to-purple-600 px-6 py-3 font-semibold transition hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/50">
              <Play size={18} /> Launch Console
            </Link>
            <a href="/research" className="flex items-center gap-2 rounded border border-slate-600 px-6 py-3 font-semibold transition hover:border-cyan-500 hover:text-cyan-400">
              Read the Paper <ExternalLink size={18} />
            </a>
          </div>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-8 backdrop-blur">
          <div className="flex flex-col gap-6">
            <svg viewBox="0 0 300 260" className="h-64 w-full">
              <polygon points="150,20 270,240 30,240" fill="none" stroke="rgb(100,116,139)" strokeWidth="2" />
              <polygon points="150,75 230,215 70,215" fill="rgba(34, 197, 94, 0.05)" stroke="rgb(34, 197, 94)" strokeWidth="1.5" strokeDasharray="4,4" />
              <circle cx={150 + (simplex.r - simplex.s) * 60} cy={20 + (1 - simplex.c) * 200} r="6" fill={govActive ? 'rgb(239, 68, 68)' : 'rgb(6, 182, 212)'} className={govActive ? 'animate-pulse' : ''} />
              {govActive && <line x1={150 + (simplex.r - simplex.s) * 60} y1={20 + (1 - simplex.c) * 200} x2="150" y2="130" stroke="rgb(239, 68, 68)" strokeWidth="2" strokeDasharray="4,4" opacity="0.6" />}
              <text x="150" y="15" textAnchor="middle" className="fill-cyan-400 text-xs" fontSize="12" fontWeight="bold">CONTINUITY</text>
              <text x="275" y="250" textAnchor="start" className="fill-purple-400 text-xs" fontSize="12" fontWeight="bold">SOVEREIGNTY</text>
              <text x="10" y="250" textAnchor="end" className="fill-pink-400 text-xs" fontSize="12" fontWeight="bold">RECIPROCITY</text>
            </svg>

            <div className="grid grid-cols-3 gap-4 text-sm">
              {([
                { label: 'C', value: simplex.c, box: 'border-cyan-500/30', text: 'text-cyan-400' },
                { label: 'R', value: simplex.r, box: 'border-pink-500/30', text: 'text-pink-400' },
                { label: 'S', value: simplex.s, box: 'border-purple-500/30', text: 'text-purple-400' }
              ] as const).map((item) => (
                <div key={item.label} className={`rounded border ${item.box} bg-slate-800/50 p-3`}>
                  <div className={`font-mono text-xs ${item.text}`}>{item.label}</div>
                  <div className="text-lg font-bold">{(item.value * 100).toFixed(0)}%</div>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-700 pt-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="font-mono text-xs text-slate-400">Stability Margin M(t)</span>
                <span className={`font-mono text-sm font-bold ${margin > GOVERNOR_THRESHOLD ? 'text-green-400' : 'text-red-400'}`}>{margin.toFixed(3)}</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded bg-slate-800">
                <div className={`h-full transition-all duration-300 ${margin > GOVERNOR_THRESHOLD ? 'bg-green-500' : 'bg-red-500'}`} style={{ width: `${Math.max(margin, 0.05) * 100}%` }} />
              </div>
              <div className="mt-2 text-xs text-slate-400">τ = 0.15 (Constitutional threshold)</div>
            </div>
          </div>
        </div>
      </section>

      <section id="research" className="relative z-10 mx-auto max-w-7xl border-t border-slate-800 px-4 py-16 sm:px-6 lg:py-24">
        <h2 className="mb-4 text-4xl font-bold">The Framework</h2>
        <p className="mb-16 text-lg text-slate-400">Aureonics is not a brand term. It&apos;s a measurable, geometric model of adaptive stability.</p>
      </section>

      <footer className="relative z-10 border-t border-slate-800 px-6 py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 text-sm text-slate-400 sm:flex-row sm:items-center">
          <div>© 2026 Aureonics. Measurable. Constitutional. Governed.</div>
          <div className="flex gap-6">
            <a href="/docs" className="transition hover:text-cyan-400">Docs</a>
            <a href="/pricing" className="transition hover:text-cyan-400">Pricing</a>
            <a href="https://github.com/omomehinemmanuel5-boop/Aureonics-OS-" className="flex items-center gap-1 transition hover:text-cyan-400">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
