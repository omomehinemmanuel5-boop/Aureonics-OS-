import { describe, expect, it } from 'vitest';
import { computePoint, GOVERNOR_THRESHOLD, nextDriftState, stabilityMargin } from '../lib/simplex';

describe('simplex dynamics helpers', () => {
  it('keeps simplex point normalized', () => {
    const point = computePoint(0.1);
    expect(point.c + point.r + point.s).toBeCloseTo(1, 8);
  });

  it('computes stability margin as minimum component', () => {
    const m = stabilityMargin({ c: 0.4, r: 0.22, s: 0.38 });
    expect(m).toBeCloseTo(0.22);
  });

  it('reverses drift direction at boundaries', () => {
    const { drift, driftDir } = nextDriftState(0.149, 0.01);
    expect(drift).toBeLessThanOrEqual(0.15);
    expect(driftDir).toBeLessThan(0);
  });

  it('indicates governor intervention below threshold', () => {
    const lowMarginPoint = { c: 0.12, r: 0.5, s: 0.38 };
    expect(stabilityMargin(lowMarginPoint)).toBeLessThan(GOVERNOR_THRESHOLD);
  });
});
