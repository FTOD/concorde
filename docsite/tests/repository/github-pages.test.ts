import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {loadSiteIdentity} from '../../plugins/concorde-content/site-identity';
import {canonicalRoute} from '../../plugins/concorde-content/routes';

const siteDir = resolve(__dirname, '../..');
const projectRoot = resolve(siteDir, '..');

describe('Concorde repository GitHub Pages deployment', () => {
  it('reproduces the Concorde repository identity in docsite/site.json', () => {
    const identity = loadSiteIdentity(siteDir);
    expect(identity.title).toBe('Concorde');
    expect(identity.url).toBe('https://ftod.github.io');
    expect(identity.baseUrl).toBe('/concorde/');
    expect(identity.organizationName).toBe('FTOD');
    expect(identity.projectName).toBe('concorde');
    expect(identity.repository).toBe('https://github.com/FTOD/concorde');
    expect(canonicalRoute('/concorde/architecture/module.concorde', identity.baseUrl)).toBe('/architecture/module.concorde');
    expect(canonicalRoute('/concorde/', identity.baseUrl)).toBe('/');
  });

  it('deploys via a workflow byte-identical to the packaged scaffold template', async () => {
    const [workflow, scaffold] = await Promise.all([
      readFile(resolve(projectRoot, '.github/workflows/deploy-docsite.yml'), 'utf8'),
      readFile(resolve(siteDir, 'scaffold/deploy-docsite.yml'), 'utf8'),
    ]);
    expect(workflow).toBe(scaffold);
  });

  it('builds with project-local Archify and deploys only the verified output', async () => {
    const workflow = await readFile(resolve(projectRoot, '.github/workflows/deploy-docsite.yml'), 'utf8');
    expect(workflow).toContain('name: Deploy project docsite');
    expect(workflow).toContain('branches: [main]');
    expect(workflow).toMatch(/name: Check out repository[\s\S]*?fetch-depth: 0/);
    expect(workflow.match(/uses: actions\/checkout@v6/g)).toHaveLength(1);
    expect(workflow).not.toContain('repository: tt-a1i/archify');
    expect(workflow).not.toMatch(/Build verified docsite\n\s+env:/);
    expect(workflow).toContain('run: npm ci --prefix docsite');
    expect(workflow).toContain('run: npm --prefix docsite run build');
    expect(workflow).toContain('path: docsite/build');
    expect(workflow).toContain('uses: actions/deploy-pages@v4');
  });
});
