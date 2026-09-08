import {mkdtempSync,mkdirSync,rmSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {afterEach,beforeEach,describe,expect,it} from 'vitest';
import {verifyConcordeBuildFresh} from '../../plugins/scoped-content/build-freshness';

let root: string;
beforeEach(() => { root = mkdtempSync(resolve(tmpdir(), 'concorde-build-freshness-')); });
afterEach(() => rmSync(root, {recursive: true, force: true}));

function sha256(content: string): string {
  return 'sha256:' + createHash('sha256').update(content).digest('hex');
}

function putSource(relative: string, content: string): void {
  const path = resolve(root, relative);
  mkdirSync(resolve(path, '..'), {recursive: true});
  writeFileSync(path, content);
}

function putManifest(sources: Record<string, string>): void {
  mkdirSync(resolve(root, 'generated'), {recursive: true});
  writeFileSync(resolve(root, 'generated/build-manifest.json'), JSON.stringify({schema_version: 1, sources, outputs: {}}));
}

describe('verifyConcordeBuildFresh', () => {
  it('throws when generated/build-manifest.json is missing', () => {
    expect(() => verifyConcordeBuildFresh(root)).toThrow(/build manifest is missing/);
  });

  it('throws when the manifest is not valid JSON', () => {
    mkdirSync(resolve(root, 'generated'), {recursive: true});
    writeFileSync(resolve(root, 'generated/build-manifest.json'), 'not json');
    expect(() => verifyConcordeBuildFresh(root)).toThrow(/not valid JSON/);
  });

  it('throws when a recorded source file is missing since the last build', () => {
    putManifest({'prompts/protocol/principles.md': sha256('original')});
    expect(() => verifyConcordeBuildFresh(root)).toThrow(/source is missing since the last build/);
  });

  it('throws when a recorded source file has changed since the last build', () => {
    putSource('prompts/protocol/principles.md', 'changed content');
    putManifest({'prompts/protocol/principles.md': sha256('original content')});
    expect(() => verifyConcordeBuildFresh(root)).toThrow(/source changed since the last build/);
  });

  it('passes when every recorded source matches its recorded digest exactly', () => {
    putSource('prompts/protocol/principles.md', 'current content');
    putManifest({'prompts/protocol/principles.md': sha256('current content')});
    expect(() => verifyConcordeBuildFresh(root)).not.toThrow();
  });

  it('passes with no recorded sources at all (an empty but well-formed manifest)', () => {
    putManifest({});
    expect(() => verifyConcordeBuildFresh(root)).not.toThrow();
  });
});
