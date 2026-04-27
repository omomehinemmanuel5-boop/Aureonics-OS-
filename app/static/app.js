const state = { traces: [] };

async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

function fmt(n, digits = 3) { return Number(n ?? 0).toFixed(digits); }
function esc(s) { return String(s ?? '—'); }

async function wake() {
  const el = document.querySelector('[data-wake]');
  if (!el) return;
  el.textContent = 'Waking Render service…';
  try {
    await fetch('/health');
    el.textContent = 'Service ready';
  } catch {
    el.textContent = 'Service is waking; retry in a moment';
  }
}

async function runTrace(prompt, firewall = true) {
  return api('/api/lex/trace', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, firewall_mode: firewall })
  });
}

async function refreshMetrics() {
  try {
    const metrics = await api('/api/lex/metrics');
    document.querySelectorAll('[data-metric]').forEach((node) => {
      const key = node.getAttribute('data-metric');
      node.textContent = key.split('.').reduce((a, b) => a?.[b], metrics) ?? '0';
    });
  } catch {}
}

async function refreshAudit(target = '#auditList') {
  try {
    const audit = await api('/api/lex/audit');
    const list = document.querySelector(target);
    if (!list) return;
    list.innerHTML = audit.length ? audit.slice(0, 10).map((item) =>
      `<li><strong>${item.intervened ? 'INTERVENED' : 'PASS'}</strong> · M ${fmt(item.M, 4)} · ${new Date(item.createdAt).toLocaleString()}<br>${esc(item.reason)}</li>`
    ).join('') : '<li>No traces yet. Submit a prompt to generate an audit trail.</li>';
  } catch {}
}

function bindConsole() {
  const form = document.querySelector('#consoleForm');
  if (!form) return;
  const out = {
    raw: document.querySelector('#rawOut'),
    gov: document.querySelector('#govOut'),
    final: document.querySelector('#finalOut'),
    reason: document.querySelector('#reasonOut'),
    id: document.querySelector('#traceId'),
    m: document.querySelector('#mVal'),
    crs: document.querySelector('#crsVal'),
    health: document.querySelector('#healthVal'),
    diff: document.querySelector('#diffVal'),
    badge: document.querySelector('#interveneBadge')
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = document.querySelector('#prompt').value.trim();
    if (!prompt) return;
    const firewall = document.querySelector('#firewall').checked;
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    submit.textContent = 'Evaluating…';
    try {
      const trace = await runTrace(prompt, firewall);
      out.raw.textContent = esc(trace.raw);
      out.gov.textContent = esc(trace.governed);
      out.final.textContent = esc(trace.final);
      out.reason.textContent = esc(trace.reason);
      out.id.textContent = trace.id;
      out.m.textContent = fmt(trace.metrics.M, 6);
      out.crs.textContent = `${fmt(trace.metrics.C)} / ${fmt(trace.metrics.R)} / ${fmt(trace.metrics.S)}`;
      out.health.textContent = esc(trace.metrics.health);
      out.diff.textContent = fmt(trace.metrics.semanticDiff, 6);
      out.badge.className = `badge ${trace.metrics.intervened ? 'alert' : 'safe'}`;
      out.badge.textContent = trace.metrics.intervened ? 'Intervened' : 'Pass';
      document.querySelector('#traceLink').href = `/trace/${trace.id}`;
      await Promise.all([refreshMetrics(), refreshAudit()]);
    } catch {
      out.reason.textContent = 'Trace call failed. If Render was asleep, wait a few seconds and retry.';
    } finally {
      submit.disabled = false;
      submit.textContent = 'Run Decision Firewall';
    }
  });
}

async function bindTraceDetail() {
  const node = document.querySelector('[data-trace-id]');
  if (!node) return;
  const id = node.getAttribute('data-trace-id');
  try {
    const trace = await api(`/api/lex/trace/${id}`);
    document.querySelector('#tMeta').textContent = `${trace.id} · ${new Date(trace.createdAt).toLocaleString()}`;
    document.querySelector('#tPrompt').textContent = esc(trace.prompt);
    document.querySelector('#tRaw').textContent = esc(trace.raw);
    document.querySelector('#tGov').textContent = esc(trace.governed);
    document.querySelector('#tFinal').textContent = esc(trace.final);
    document.querySelector('#tReason').textContent = esc(trace.reason);
    document.querySelector('#tMetrics').innerHTML = `M ${fmt(trace.metrics.M, 6)} · CRS ${fmt(trace.metrics.C)} / ${fmt(trace.metrics.R)} / ${fmt(trace.metrics.S)} · ADV ${fmt(trace.metrics.ADV)} · θeff ${fmt(trace.metrics.thetaEff)} · semanticDiff ${fmt(trace.metrics.semanticDiff, 6)}`;
    await refreshAudit('#tAudit');
  } catch {
    document.querySelector('#tMeta').textContent = 'Trace not found or service waking.';
  }
}

async function bindPolicies() {
  const table = document.querySelector('#policyTable');
  if (!table) return;
  try {
    const data = await api('/api/lex/policies');
    table.innerHTML = data.items.map((p) =>
      `<tr><td>${p.name}</td><td>${p.version}</td><td>${p.active ? 'Active' : 'Inactive'}</td><td>${Object.entries(p.thresholds).map(([k,v]) => `${k}: ${v}`).join('<br>')}</td></tr>`
    ).join('');
  } catch {
    table.innerHTML = '<tr><td colspan="4">Policy service waking.</td></tr>';
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  wake();
  bindConsole();
  bindTraceDetail();
  bindPolicies();
  await Promise.all([refreshMetrics(), refreshAudit()]);
});
