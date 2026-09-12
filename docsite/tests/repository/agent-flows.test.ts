import {readFileSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {expect, it} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';

const root = resolve(__dirname, '../../..');
it('scenario.views.agent-flows: every authored Spec link names a published document and section', () => {
  const source = readFileSync(resolve(root, 'docsite/concorde-only/page.tsx'), 'utf8');
  const registry = loadScopedRegistry(root);
  const paths = [
    ...[...source.matchAll(/development \+ '([^']+)'/g)].map(m => '/specs/concorde/development/' + m[1]),
    ...[...source.matchAll(/to="(\/specs\/[^\"]+)"/g)].map(m => m[1]),
  ];
  expect(paths.length).toBeGreaterThan(10);
  for (const path of paths) {
    const [route, fragment] = path.split('#');
    const page = registry.pages.find(p => p.route === route);
    expect(page, path).toBeDefined();
    if (fragment) {
      const headings = page!.content.split('\n').filter(line => /^#+ /.test(line));
      expect(page!.content.includes(fragment) || headings.some(heading => heading.toLowerCase()
        .replace(/^#+ /, '').replace(/[^a-z0-9 -]/g, '').replace(/ /g, '-') === fragment), path).toBe(true);
    }
  }
  expect(existsSync(resolve(root, 'src/concorde/development/loop_graph.py'))).toBe(true);
});
