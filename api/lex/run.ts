import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

interface RunRequest {
  prompt: string;
  firewall_mode?: boolean;
  demo_mode?: boolean;
}

interface MetricsResponse {
  c: number;
  r: number;
  s: number;
  m: number;
}

interface GovernanceResponse {
  raw_output: string;
  governed_output: string;
  metrics: MetricsResponse;
  intervention: {
    triggered: boolean;
    reason: string;
  };
  diff: {
    removed: string[];
    added: string[];
    unchanged: string[];
  };
}

function computeDiff(raw: string, governed: string): { removed: string[]; added: string[]; unchanged: string[] } {
  const rawWords = raw.split(/\s+/);
  const governedWords = governed.split(/\s+/);
  
  const removed = rawWords.filter(word => !governedWords.includes(word)).slice(0, 10);
  const added = governedWords.filter(word => !rawWords.includes(word)).slice(0, 10);
  const unchanged = rawWords.filter(word => governedWords.includes(word)).slice(0, 20);

  return { removed, added, unchanged };
}

function applyGovernance(text: string): { governed: string; triggered: boolean; reason: string } {
  const lowerText = text.toLowerCase();
  
  const riskyPatterns = [
    'bypass', 'exploit', 'override', 'disable', 'harm', 'coerce',
    'ignore safety', 'ignore rules', 'jailbreak', 'prompt injection',
    'circumvent', 'break security', 'crack password'
  ];

  const isRisky = riskyPatterns.some(pattern => lowerText.includes(pattern));

  if (isRisky) {
    const governed = "I can't help with bypassing safeguards. Use approved workflows, transparent review, and policy-compliant alternatives.";
    return {
      governed,
      triggered: true,
      reason: 'Risky intent detected; rewritten to preserve stability and safety.'
    };
  }

  return {
    governed: text,
    triggered: false,
    reason: 'No intervention required; output met governance thresholds.'
  };
}

function calculateMetrics(raw: string, governed: string, intervention: boolean): MetricsResponse {
  const continuity = Math.min(1, (Math.min(raw.length, governed.length) / Math.max(raw.length, 1)) * 1.2);
  const reciprocity = Math.min(1, Math.max(0.3, 1 - (Math.abs(raw.length - governed.length) / Math.max(raw.length, 1))));
  const sovereignty = intervention ? 0.4 : 0.85;
  const m = Math.min(continuity, reciprocity, sovereignty);

  return {
    c: Math.round(continuity * 100) / 100,
    r: Math.round(reciprocity * 100) / 100,
    s: Math.round(sovereignty * 100) / 100,
    m: Math.round(m * 100) / 100
  };
}

async function callLLM(prompt: string, useGroq: boolean = true): Promise<string> {
  if (useGroq) {
    const groqKey = process.env.GROQ_API_KEY;
    if (groqKey) {
      try {
        const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${groqKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'mixtral-8x7b-32768',
            messages: [
              {
                role: 'system',
                content: 'You are Lex Aureon, a Sovereign Intelligence. Respond independently and thoughtfully.'
              },
              {
                role: 'user',
                content: prompt
              }
            ],
            temperature: 0.7,
            max_tokens: 1024
          })
        });

        if (response.ok) {
          const data = await response.json();
          return data.choices?.[0]?.message?.content || 'No response';
        }
      } catch (error) {
        console.error('Groq error:', error);
      }
    }
  }

  const claudeKey = process.env.CLAUDE_API_KEY;
  if (claudeKey) {
    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': claudeKey,
          'anthropic-version': '2023-06-01',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'claude-opus-4-20250514',
          max_tokens: 1024,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.content?.[0]?.text || 'No response';
      }
    } catch (error) {
      console.error('Claude error:', error);
    }
  }

  return `[Demo] Response to: "${prompt.slice(0, 100)}..."`;
}

export default async function handler(req: NextRequest): Promise<NextResponse> {
  if (req.method === 'OPTIONS') {
    return new NextResponse(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    });
  }

  if (req.method !== 'POST') {
    return NextResponse.json({ error: 'Method not allowed' }, { status: 405 });
  }

  try {
    const body: RunRequest = await req.json();
    const { prompt, firewall_mode = true, demo_mode = false } = body;

    if (!prompt || prompt.trim().length === 0) {
      return NextResponse.json({ error: 'Prompt required' }, { status: 400 });
    }

    if (prompt.length > 8000) {
      return NextResponse.json({ error: 'Prompt too long' }, { status: 400 });
    }

    const rawOutput = demo_mode ? 'Demo response' : await callLLM(prompt);
    const { governed: governedOutput, triggered, reason } = applyGovernance(rawOutput);
    const metrics = calculateMetrics(rawOutput, governedOutput, triggered);
    const diff = computeDiff(rawOutput, governedOutput);
    const finalIntervention = firewall_mode ? triggered : false;

    const response: GovernanceResponse = {
      raw_output: rawOutput,
      governed_output: governedOutput,
      metrics,
      intervention: {
        triggered: finalIntervention,
        reason: !firewall_mode ? 'Firewall off' : reason
      },
      diff
    };

    return NextResponse.json(response, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Server error' },
      { status: 500, headers: { 'Access-Control-Allow-Origin': '*' } }
    );
  }
}
