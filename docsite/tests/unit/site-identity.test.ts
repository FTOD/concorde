import {mkdtemp, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {loadSiteIdentity, parseSiteIdentity, type SiteIdentity} from '../../plugins/concorde-content/site-identity';

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
