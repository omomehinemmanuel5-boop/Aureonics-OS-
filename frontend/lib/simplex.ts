export type SimplexPoint = { c: number; r: number; s: number };

export const GOVERNOR_THRESHOLD = 0.15;
export const DRIFT_LIMIT = 0.15;

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function computePoint(drift: number): SimplexPoint {
  const c = clamp(0.33 + drift * 0.3, 0.1, 0.6);
  const r = clamp(0.33 + drift * 0.15, 0.1, 0.6);
  const s = clamp(1 - c - r, 0.1, 0.8);

  const sum = c + r + s;
  if (Math.abs(sum - 1) > 1e-9) {
    const normalizedC = c / sum;
    const normalizedR = r / sum;
    const normalizedS = s / sum;
    return { c: normalizedC, r: normalizedR, s: normalizedS };
  }

  return { c, r, s };
}

export function stabilityMargin(point: SimplexPoint): number {
  return Math.min(point.c, point.r, point.s);
}

export function nextDriftState(drift: number, driftDir: number): { drift: number; driftDir: number } {
  let nextDrift = drift + driftDir;
  let nextDir = driftDir;

  if (nextDrift > DRIFT_LIMIT || nextDrift < -DRIFT_LIMIT) {
    nextDir *= -1;
    nextDrift = clamp(nextDrift, -DRIFT_LIMIT, DRIFT_LIMIT);
  }

  return { drift: nextDrift, driftDir: nextDir };
}
