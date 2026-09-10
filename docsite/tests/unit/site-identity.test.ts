import {mkdtemp, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {loadSiteIdentity, parseSiteIdentity, type SiteIdentity} from '../../plugins/scoped-content/site-identity';

const validValue = {
  schema_version: 1,
  title: 'Atlas',
  url: 'https://example.com',
  baseUrl: '/',
  organizationName: 'atlas-org',
  projectName: 'atlas',
  repository: 'https://github.com/atlas-org/atlas',
  tagline: 'A specified project',
};

const roots: string[] = [];
const homepage = {
  eyebrow: 'Project documentation', title: 'Build with a clear contract.', description: 'Explore the project.',
  features: {title: 'Capabilities', items: [{title: 'Contracts', description: 'Explicit promises.'}]},
  workflow: {title: 'Workflow', description: 'An inspectable path.', steps: [{title: 'Specify', description: 'Define the behavior.'}]},
  quickstart: {title: 'Get started', description: 'Install the project.', code: 'echo example'},
};
afterEach(async () => Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true}))));

async function siteDirWith(content: unknown): Promise<string> {
  const root = await mkdtemp(resolve(tmpdir(), 'concorde-site-identity-'));
  roots.push(root);
  await writeFile(resolve(root, 'site.json'), JSON.stringify(content), 'utf8');
  return root;
}

describe('site identity schema 1', () => {
  it('parses a complete valid identity', () => {
    expect(parseSiteIdentity(validValue)).toEqual<SiteIdentity>({
      schemaVersion: 1,
      title: 'Atlas',
      url: 'https://example.com',
      baseUrl: '/',
      organizationName: 'atlas-org',
      projectName: 'atlas',
      repository: 'https://github.com/atlas-org/atlas',
      tagline: 'A specified project',
    });
  });

  it('treats repository and tagline as optional', () => {
    const {repository: _repository, tagline: _tagline, ...minimal} = validValue;
    expect(parseSiteIdentity(minimal)).toEqual<SiteIdentity>({
      schemaVersion: 1, title: 'Atlas', url: 'https://example.com', baseUrl: '/',
      organizationName: 'atlas-org', projectName: 'atlas',
    });
  });

  it('loads a valid docsite/site.json from disk', async () => {
    const siteDir = await siteDirWith(validValue);
    expect(loadSiteIdentity(siteDir)).toMatchObject({title: 'Atlas', organizationName: 'atlas-org'});
  });

  it('only enables the independent standard collection through an explicit boolean', () => {
    expect(parseSiteIdentity(validValue).protocolDocs).toBeUndefined();
    expect(parseSiteIdentity({...validValue, protocolDocs: true}).protocolDocs).toBe(true);
    expect(parseSiteIdentity({...validValue, protocolDocs: false}).protocolDocs).toBe(false);
    expect(() => parseSiteIdentity({...validValue, protocolDocs: 'true'})).toThrow(/protocolDocs/);
  });

  it('keeps the landing page opt-in and preserves project-owned copy', () => {
    expect(parseSiteIdentity(validValue).homepage).toBeUndefined();
    expect(parseSiteIdentity({...validValue, homepage}).homepage).toEqual(homepage);
    expect(parseSiteIdentity({...validValue, homepage: {...homepage, title: '  Atlas  '}}).homepage?.title).toBe('Atlas');
  });

  it.each([
    ['null', null, /homepage must be an object/],
    ['empty title', {...homepage, title: ' '}, /homepage.title/],
    ['missing features', {...homepage, features: undefined}, /homepage.features/],
    ['empty features', {...homepage, features: {...homepage.features, items: []}}, /homepage.features.items/],
    ['invalid feature', {...homepage, features: {...homepage.features, items: [null]}}, /homepage.features.items\[0\]/],
    ['missing description', {...homepage, features: {...homepage.features, items: [{title: 'Feature'}]}}, /homepage.features.items\[0\].description/],
    ['invalid steps', {...homepage, workflow: {...homepage.workflow, steps: 'steps'}}, /homepage.workflow.steps/],
    ['empty code', {...homepage, quickstart: {...homepage.quickstart, code: ''}}, /homepage.quickstart.code/],
  ])('rejects an invalid homepage: %s', (_label, value, field) => {
    expect(() => parseSiteIdentity({...validValue, homepage: value})).toThrow(/docsite\/site.json/);
    expect(() => parseSiteIdentity({...validValue, homepage: value})).toThrow(field);
  });

  it('preserves optional reference tables as plain project-owned text', () => {
    const reference = {title: 'Reference', description: 'Available tools.', tables: [
      {title: 'Tools', description: 'Commands.', columns: ['Command', 'Purpose'], rows: [['<script>', 'Show <help> & usage']]},
    ]};
    expect(parseSiteIdentity({...validValue, homepage: {...homepage, reference}}).homepage?.reference).toEqual(reference);
    expect(parseSiteIdentity({...validValue, homepage}).homepage?.reference).toBeUndefined();
  });

  it.each([
    [null, /homepage.reference must be an object/],
    [{title: 'Reference', description: 'Tools.', tables: []}, /homepage.reference.tables/],
    ...[
      {columns: [], rows: [['command']]},
      {columns: ['Command'], rows: []},
      {columns: ['Command'], rows: [['command', 'extra']]},
      {columns: ['Command'], rows: [[' ']]},
      {columns: ['Command'], rows: ['command']},
      {columns: ['Command'], rows: [[42]]},
    ].map((table): [unknown, RegExp] => [{title: 'Reference', description: 'Tools.', tables: [
      {title: 'Tools', description: 'Commands.', ...table},
    ]}, /homepage.reference.tables\[0\]/]),
  ])('rejects malformed reference content %#', (reference, field) => {
    expect(() => parseSiteIdentity({...validValue, homepage: {...homepage, reference}})).toThrow(field);
  });

  it('reports a missing file by its project-relative name', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-site-identity-missing-'));
    roots.push(root);
    expect(() => loadSiteIdentity(root)).toThrow(/docsite\/site\.json/);
  });

  it('reports invalid JSON by the file name', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-site-identity-badjson-'));
    roots.push(root);
    await writeFile(resolve(root, 'site.json'), '{not json', 'utf8');
    expect(() => loadSiteIdentity(root)).toThrow(/docsite\/site\.json/);
  });

  it.each([
    ['schema_version', {...validValue, schema_version: 2}, /schema_version/],
    ['empty title', {...validValue, title: ''}, /title/],
    ['non-absolute url', {...validValue, url: 'example.com'}, /url/],
    ['baseUrl missing leading slash', {...validValue, baseUrl: 'atlas/'}, /baseUrl/],
    ['baseUrl missing trailing slash', {...validValue, baseUrl: '/atlas'}, /baseUrl/],
    ['non-string organizationName', {...validValue, organizationName: 42}, /organizationName/],
    ['non-string projectName', {...validValue, projectName: {}}, /projectName/],
    ['non-absolute repository', {...validValue, repository: 'not-a-url'}, /repository/],
  ])('rejects %s with a message naming docsite/site.json and the violated rule', (_label, value, rulePattern) => {
    expect(() => parseSiteIdentity(value)).toThrow(/docsite\/site\.json/);
    expect(() => parseSiteIdentity(value)).toThrow(rulePattern);
  });
});
