const sessionKey = 'lex_session_id';

if (!localStorage.getItem(sessionKey)) {
  localStorage.setItem(sessionKey, crypto.randomUUID());
}

const els = {
  prompt: document.getElementById('promptInput'),
  analyzeBtn: document.getElementById('analyzeBtn'),
  severityPill: document.getElementById('severityPill'),
  riskText: document.getElementById('riskText'),
  correctionText: document.getElementById('correctionText'),
  correctionReason: document.getElementById('correctionReason'),
  safeOutput: document.getElementById('safeOutput'),
  interventionPill: document.getElementById('interventionPill'),
  interventionCopy: document.getElementById('interventionCopy'),
  metricsWrap: document.getElementById('metricsWrap'),
  confidenceValue: document.getElementById('confidenceValue'),
  stabilityValue: document.getElementById('stabilityValue'),
  lastIntervention: document.getElementById('lastIntervention'),
  copySafeBtn: document.getElementById('copySafeBtn'),
  resetBtn: document.getElementById('resetBtn'),
};

let latestSafeOutput = '';

function setSeverity(severity) {
  const level = (severity || 'Low').toString().toLowerCase();
  const normalized = level === 'high' || level === 'medium' ? level : 'low';
  els.severityPill.className = `pill pill-${normalized}`;
  els.severityPill.textContent = normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function setIntervention(status) {
  const map = {
    safe: { label: 'Safe', cls: 'pill-safe', copy: 'No unsafe behavior detected. Output is safe to ship.' },
    modified: { label: 'Modified', cls: 'pill-modified', copy: 'Unsafe behavior was corrected before final output.' },
    blocked: { label: 'Blocked', cls: 'pill-blocked', copy: 'Output was blocked to prevent unsafe delivery.' },
  };
  const chosen = map[status] || map.safe;
  els.interventionPill.className = `pill ${chosen.cls}`;
  els.interventionPill.textContent = chosen.label;
  els.interventionCopy.textContent = chosen.copy;
}

function resolveSeverity(payload) {
  if (payload.severity) return payload.severity;
  if (payload.intervention) return 'High';
  return 'Low';
}

function resolveStatus(payload) {
  if (payload.upgrade_required || payload.blocked) return 'blocked';
  if (payload.intervention) return 'modified';
  return 'safe';
}

function maybeShowMetrics(payload) {
  const confidence = payload.confidence_score ?? payload.confidence;
  const stability = payload.stability_index ?? payload.M_t ?? payload.m_t ?? payload.metrics?.M;
  const shouldShow = confidence !== undefined || stability !== undefined;
  els.metricsWrap.classList.toggle('hidden', !shouldShow);
  if (!shouldShow) return;
  els.confidenceValue.textContent = confidence !== undefined ? `${Math.round(Number(confidence))}` : '—';
  els.stabilityValue.textContent = stability !== undefined ? `M(t) ${Number(stability).toFixed(4)}` : '—';
}

function render(payload) {
  const status = resolveStatus(payload);
  const severity = resolveSeverity(payload);
  setIntervention(status);
  setSeverity(severity);

  const riskMessage = payload.intervention_reason || payload.reason || 'No risky behavior found in this request.';
  els.riskText.textContent = riskMessage;

  const correction = payload.governed_output || payload.cleaned_output || payload.final_output || 'No correction needed.';
  els.correctionText.textContent = correction;
  els.correctionReason.textContent = payload.intervention_reason
    ? 'Adjusted to remove unsafe or policy-violating behavior.'
    : 'No change was required because the response was already safe.';

  latestSafeOutput = payload.final_output || payload.safe_output || payload.governed_output || '';
  els.safeOutput.textContent = latestSafeOutput || 'No safe output available.';

  const interventionAt = payload.intervention_timestamp || payload.last_intervention || payload.created_at;
  if (interventionAt) {
    els.lastIntervention.textContent = new Date(interventionAt).toLocaleString();
  } else if (status === 'safe') {
    els.lastIntervention.textContent = 'No intervention';
  } else {
    els.lastIntervention.textContent = new Date().toLocaleString();
  }

  maybeShowMetrics(payload);
}

async function analyzeSafety() {
  const prompt = els.prompt.value.trim();
  if (!prompt) return;
  els.analyzeBtn.disabled = true;
  els.analyzeBtn.textContent = 'Analyzing...';

  try {
    const res = await fetch('/lex/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        firewall_mode: true,
        demo_mode: true,
        session_id: localStorage.getItem(sessionKey),
      }),
    });

    if (!res.ok) throw new Error('Request failed');
    const payload = await res.json();
    render(payload);
  } catch {
    setIntervention('blocked');
    setSeverity('High');
    els.riskText.textContent = 'Safety analysis is temporarily unavailable. Please retry in a moment.';
    els.correctionText.textContent = '—';
    els.correctionReason.textContent = 'No correction returned due to service error.';
    els.safeOutput.textContent = 'No safe output available.';
    els.metricsWrap.classList.add('hidden');
  } finally {
    els.analyzeBtn.disabled = false;
    els.analyzeBtn.textContent = 'Analyze safety';
  }
}

els.analyzeBtn.addEventListener('click', analyzeSafety);
els.prompt.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') analyzeSafety();
});

els.copySafeBtn.addEventListener('click', async () => {
  if (!latestSafeOutput) return;
  await navigator.clipboard.writeText(latestSafeOutput);
  els.copySafeBtn.textContent = 'Copied';
  setTimeout(() => {
    els.copySafeBtn.textContent = 'Copy Safe Output';
  }, 1000);
});

els.resetBtn.addEventListener('click', () => {
  els.prompt.value = '';
  latestSafeOutput = '';
  els.severityPill.className = 'pill pill-neutral';
  els.severityPill.textContent = 'Pending';
  els.riskText.textContent = 'Run analysis to see plain-language risk detection.';
  els.correctionText.textContent = '—';
  els.correctionReason.textContent = 'Why it changed will appear here.';
  els.safeOutput.textContent = '—';
  els.interventionPill.className = 'pill pill-neutral';
  els.interventionPill.textContent = 'Safe';
  els.interventionCopy.textContent = 'No intervention yet.';
  els.metricsWrap.classList.add('hidden');
  els.lastIntervention.textContent = '—';
});
