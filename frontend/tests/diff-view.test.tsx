import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { DiffView } from '@/components/DiffView';

describe('DiffView', () => {
  it('renders fallback when diff is missing', () => {
    const html = renderToStaticMarkup(<DiffView diff={undefined} />);
    expect(html).toContain('No governance diff available for this run.');
  });

  it('renders removed, added and unchanged chunks with expected classes', () => {
    const html = renderToStaticMarkup(
      <DiffView
        diff={[
          { type: 'unchanged', text: 'safe baseline' },
          { type: 'removed', text: 'unsafe command' },
          { type: 'added', text: 'approved workflow' },
        ]}
      />,
    );

    expect(html).toContain('safe baseline');
    expect(html).toContain('unsafe command');
    expect(html).toContain('approved workflow');
    expect(html).toContain('line-through');
    expect(html).toContain('text-emerald-300');
  });
});
