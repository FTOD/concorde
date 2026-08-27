import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import config from '../../docusaurus.config';
import {canonicalRoute} from '../../plugins/concorde-content/routes';

const projectRoot = resolve(__dirname, '../../..');

describe('Concorde repository GitHub Pages deployment', () => {
  it('builds links for the FTOD project site', () => {
    expect(config.url).toBe('https://ftod.github.io');
    expect(config.baseUrl).toBe('/concorde/');
    expect(config.organizationName).toBe('FTOD');
    expect(config.projectName).toBe('concorde');
    expect(canonicalRoute('/concorde/docs/quick-start', config.baseUrl)).toBe('/docs/quick-start');
    expect(canonicalRoute('/concorde/', config.baseUrl)).toBe('/');
  });

  it('builds with project-local Archify and deploys only the verified output', async () => {
    const workflow = await readFile(resolve(projectRoot, '.github/workflows/deploy-docsite.yml'), 'utf8');
    expect(workflow).toContain('branches: [main]');
    expect(workflow).toMatch(/name: Check out Concorde[\s\S]*?fetch-depth: 0/);
    expect(workflow.match(/uses: actions\/checkout@v6/g)).toHaveLength(1);
    expect(workflow).not.toContain('repository: tt-a1i/archify');
    expect(workflow).not.toMatch(/Build verified docsite\n\s+env:/);
    expect(workflow).toContain('run: npm ci --prefix docsite');
    expect(workflow).toContain('run: npm --prefix docsite run build');
    expect(workflow).toContain('path: docsite/build');
    expect(workflow).toContain('uses: actions/deploy-pages@v4');
  });
});
