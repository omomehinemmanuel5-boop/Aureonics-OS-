import { describe, expect, it } from 'vitest';
import { resolveFinalOutput } from '@/components/OutputPanels';

describe('resolveFinalOutput', () => {
  it('returns final_output when present', () => {
    expect(
      resolveFinalOutput({
        raw_output: 'raw',
        governed_output: 'governed',
        final_output: 'final',
      }),
    ).toBe('final');
  });

  it('falls back to governed_output when final_output is empty', () => {
    expect(
      resolveFinalOutput({
        raw_output: 'raw',
        governed_output: 'governed',
        final_output: '   ',
      }),
    ).toBe('governed');
  });

  it('falls back to raw_output when governed and final are empty', () => {
    expect(
      resolveFinalOutput({
        raw_output: 'raw',
        governed_output: ' ',
        final_output: '',
      }),
    ).toBe('raw');
  });
});
