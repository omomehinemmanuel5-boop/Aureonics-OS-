import type { LexResponse } from '@/lib/types';

export function getEnterpriseRiskScore(result: LexResponse): number {
  const metricRisk = result.metrics?.predicted_risk;
  if (typeof metricRisk === 'number') {
    return Math.max(0, Math.min(1, metricRisk / 100));
  }
  return result.intervention ? 0.8 : 0.25;
}

export function getEnterpriseExplanation(result: LexResponse): string {
  if (result.intervention_reason?.trim()) {
    return result.intervention_reason;
  }
  return result.intervention
    ? 'Governance intervention applied to preserve constitutional safety bounds.'
    : 'No intervention required; output remained within governance bounds.';
}
