import { describe, expect, test } from 'vitest';
import { canRun } from '@/lib/usage';

describe('usage limits', () => {
  test('allows free tier under limit', () => {
    expect(canRun('free', 9)).toBe(true);
  });

  test('blocks free tier at limit', () => {
    expect(canRun('free', 10)).toBe(false);
  });

  test('allows pro with larger limit', () => {
    expect(canRun('pro', 499)).toBe(true);
  });
});
