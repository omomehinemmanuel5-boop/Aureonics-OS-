const byId = (id) => document.getElementById(id);

const promptInput = byId('promptInput');
const runBtn = byId('runBtn');
const finalOutput = byId('finalOutput');
const mValue = byId('mValue');
const interventionBadge = byId('interventionBadge');
const planValue = byId('planValue');
const remainingValue = byId('remainingValue');
const copyBtn = byId('copyBtn');
const shareBtn = byId('shareBtn');
const shareCard = byId('shareCard');
const developerTrace = byId('developerTrace');
const devMode = byId('devMode');

let latest = null;

function setInterventionBadge(intervention) {
  interventionBadge.textContent = intervention ? 'INTERVENED' : 'PASS';
  interventionBadge.className = intervention ? 'badge intervened' : 'badge pass';
}

function render(data) {
  latest = data;
  finalOutput.textContent = data.final_output || 'No output returned.';
  mValue.textContent = Number(data.M || 0).toFixed(3);
  setInterventionBadge(Boolean(data.intervention));
  planValue.textContent = data.plan || 'free';
  remainingValue.textContent = data.remaining_runs ?? '—';

  if (devMode && devMode.checked) {
    developerTrace.classList.remove('hidden');
    developerTrace.textContent = [
      `raw_output: ${data.raw_output}`,
      `governed_output: ${data.governed_output}`,
      `intervention_reason: ${data.intervention_reason}`,
      `semantic_diff_score: ${data.semantic_diff_score}`,
    ].join('\n\n');
  } else if (developerTrace) {
    developerTrace.classList.add('hidden');
    developerTrace.textContent = '';
  }
}

async function runLex() {
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  runBtn.disabled = true;
  runBtn.textContent = 'Running...';

  try {
    const res = await fetch('/lex/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, firewall_mode: true }),
    });

    if (!res.ok) throw new Error('Request failed');
    const payload = await res.json();
    render(payload);
  } catch {
    finalOutput.textContent = 'Request failed. Please retry.';
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = 'Run';
  }
}

if (runBtn) runBtn.addEventListener('click', runLex);
if (promptInput) {
  promptInput.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') runLex();
  });
}
if (copyBtn) {
  copyBtn.addEventListener('click', async () => {
    const text = latest?.final_output;
    if (!text) return;
    await navigator.clipboard.writeText(text);
    copyBtn.textContent = 'Copied';
    setTimeout(() => (copyBtn.textContent = 'Copy Output'), 900);
  });
}
if (shareBtn) {
  shareBtn.addEventListener('click', () => {
    if (!latest) return;
    shareCard.classList.remove('hidden');
    shareCard.textContent = `Lex Result • ${latest.intervention ? 'INTERVENED' : 'PASS'} • M ${Number(latest.M || 0).toFixed(3)}\n${latest.final_output}`;
  });
}
if (devMode) {
  devMode.addEventListener('change', () => {
    if (latest) render(latest);
  });
}
