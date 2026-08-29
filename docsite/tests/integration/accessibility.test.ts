import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

const siteDir = resolve(__dirname, '../..');

describe('accessible presentation contract', () => {
  it('provides semantic landmarks and named provenance', async () => {
    const [home, provenance, architectureView, featureDiagrams] = await Promise.all([
      readFile(resolve(siteDir, 'src/pages/index.tsx'), 'utf8'),
      readFile(resolve(siteDir, 'src/components/ContentProvenance.tsx'), 'utf8'),
      readFile(resolve(siteDir, 'src/components/ArchitectureView.tsx'), 'utf8'),
      readFile(resolve(siteDir, 'src/components/FeatureDiagrams.tsx'), 'utf8'),
    ]);
    expect(home).toContain('<main');
    expect(home).toContain('<header');
    expect(provenance).toContain('aria-label="Content provenance"');
    expect(architectureView).toContain('title={`Interactive architecture view for ${page.title}: ${diagram.title}`}');
    expect(architectureView).toContain('sandbox="allow-downloads allow-scripts"');
    expect(featureDiagrams).toContain('aria-labelledby="feature-diagrams-heading"');
    expect(featureDiagrams).toContain('sandbox="allow-downloads allow-scripts"');
    expect(featureDiagrams).toContain('Source: <code>{diagram.source}</code>');
  });

  it('keeps visible keyboard focus and a narrow-layout breakpoint', async () => {
    const css = await readFile(resolve(siteDir, 'src/css/custom.css'), 'utf8');
    expect(css).toContain(':focus-visible');
    expect(css).toContain('@media (max-width: 640px)');
  });
});
