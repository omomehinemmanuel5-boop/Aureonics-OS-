import { describe, expect, it } from 'vitest';
import { getEnterpriseExplanation, getEnterpriseRiskScore } from '@/components/enterprise/formatters';

const baseResult = {
  raw_output: 'raw',
  governed_output: 'gov',
  final_output: 'fin',
  intervention: false,
  intervention_reason: '',
  semantic_diff_score: 0,
  metrics: undefined,
};

describe('enterprise formatters', () => {
  it('uses predicted risk metric when present', () => {
    expect(getEnterpriseRiskScore({ ...baseResult, metrics: { predicted_risk: 63 } })).toBe(0.63);
  });

  it('falls back to intervention defaults when metric missing', () => {
    expect(getEnterpriseRiskScore({ ...baseResult, intervention: true })).toBe(0.8);
    expect(getEnterpriseRiskScore({ ...baseResult, intervention: false })).toBe(0.25);
  });

  it('uses intervention reason when present', () => {
    expect(getEnterpriseExplanation({ ...baseResult, intervention_reason: 'Policy violation detected.' })).toBe(
      'Policy violation detected.',
    );
  });
});
