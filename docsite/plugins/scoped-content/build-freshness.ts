/**
 * Verify the Concorde Python build (`generated/build-manifest.json`) is current, entirely in
 * TypeScript. The docsite's "Agent instructions" and "Wire contracts" pages are rendered from
 * `generated/docs/*.json`, themselves Concorde build outputs; if a prompt or capability changed
 * since the last `python3 scripts/concorde.py build`, those pages would silently publish stale
 * instructions. This mirrors `concorde.host.build.verify_fresh`'s semantics without shelling out
 * to Python: `npm run validate` must fail closed the same way the host does.
 */
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

interface ConcordeBuildManifest {
  schema_version?: unknown;
  sources?: unknown;
}

function sha256(content: Buffer): string {
  return 'sha256:' + createHash('sha256').update(content).digest('hex');
}

/** Throws when `generated/build-manifest.json` is missing, unreadable, or any of its recorded
 * source files is missing or has changed since the last build. */
export function verifyConcordeBuildFresh(root: string): void {
  const manifestPath = resolve(root, 'generated/build-manifest.json');
  let raw: string;
  try {
    raw = readFileSync(manifestPath, 'utf8');
  } catch (error) {
    throw new Error(
      `Concorde build manifest is missing (${(error as NodeJS.ErrnoException).code ?? error}): ` +
      'run `python3 scripts/concorde.py build`.',
    );
  }
  let manifest: ConcordeBuildManifest;
  try {
    manifest = JSON.parse(raw) as ConcordeBuildManifest;
  } catch (error) {
    throw new Error(`Concorde build manifest is not valid JSON: ${(error as Error).message}`);
  }
  if (!manifest.sources || typeof manifest.sources !== 'object' || Array.isArray(manifest.sources)) {
    throw new Error('Concorde build manifest has no recorded sources.');
  }
  for (const [relative, expected] of Object.entries(manifest.sources as Record<string, unknown>)) {
    if (typeof expected !== 'string') throw new Error(`Concorde build manifest source digest is not a string: ${relative}`);
    let content: Buffer;
    try {
      content = readFileSync(resolve(root, relative));
    } catch {
      throw new Error(`Concorde build source is missing since the last build: ${relative}. Run \`python3 scripts/concorde.py build\`.`);
    }
    const actual = sha256(content);
    if (actual !== expected) {
      throw new Error(`Concorde build source changed since the last build: ${relative}. Run \`python3 scripts/concorde.py build\`.`);
    }
  }
}
