import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

const siteDir = resolve(__dirname, '../..');

describe('accessible presentation contract', () => {
  it('provides semantic landmarks and named provenance', async () => {
    const [config, rootPage, provenance, graph] = await Promise.all([
      readFile(resolve(siteDir, 'docusaurus.config.ts'), 'utf8'),
      readFile(resolve(siteDir, 'src/pages/index.tsx'), 'utf8'),
      readFile(resolve(siteDir, 'src/components/ContentProvenance.tsx'), 'utf8'),
      readFile(resolve(siteDir, 'src/components/ScopedGraph.tsx'), 'utf8'),
    ]);
    expect(config).toContain("label: 'Module Specs'");
    expect(config).toContain("label: 'Graph'");
    expect(rootPage).toContain('httpEquiv="refresh"');
    expect(rootPage).toContain('<Link to={root.route}>');
    expect(provenance).toContain('aria-label="Content provenance"');
    expect(graph).toContain('aria-label="Interactive architecture graph"');
  });

  it('keeps visible keyboard focus and a narrow-layout breakpoint', async () => {
    const css = await readFile(resolve(siteDir, 'src/css/custom.css'), 'utf8');
    expect(css).toContain(':focus-visible');
    expect(css).toContain('@media (max-width: 640px)');
  });
});
