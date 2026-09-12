/** Module publication model. Registered documents are the only sources. */
import {createHash} from 'node:crypto';
import {existsSync, lstatSync, readFileSync} from 'node:fs';
import {posix, resolve} from 'node:path';
import matter from 'gray-matter';

export type Kind = 'module';
export interface Target {
  id: string; kind: Kind; title: string; documents: string[];
  references: {kind: "module" | "document"; id: string}[];
  parent: string | null; uses: string[]; files: string[]; checks: string[];
}
export interface Page {
  sourcePath: string; route: string; stagedPath: string; title: string; content: string; contentDigest: string;
  documentId: string; owner: string; mainVisible: boolean;
  includedBy: {targetId: string; reasons: {kind: 'owned' | 'module' | 'document'; id: string}[]}[]; aliases: string[];
  kind: Kind; primaryOf: string | null;
}
export interface ScopedRegistry {
  schema_version: 19; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[];
}
export const hash = (value: string | Buffer) => 'sha256:' + createHash('sha256').update(value).digest('hex');
function requireThat(value: unknown, message: string): asserts value {if (!value) throw new Error(message);}
const ids = /^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$/;
function uniqueStrings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(v => typeof v === 'string' && v.trim()) && new Set(value).size === value.length;
}
function safePath(path: string): void {
  requireThat(typeof path === 'string' && path.length && !/[:\x00-\x1f\x7f]/.test(path) && !path.includes('\\') && !path.startsWith('/') &&
    path.split('/').every(p => p && p !== '.' && p !== '..'), `Unsafe source path: ${path}`);
}
export function legacyAliasRoute(targetId: string, sourcePath: string): string {
  return `/specs/${targetId}/${hash(sourcePath).slice(7, 23)}`;
}
export function primaryDocument(target: Target): string {
  const main = target.documents.filter(path => posix.basename(path) === 'module.md');
  requireThat(main.length === 1, `Module must register exactly one module.md: ${target.id}`);
  return main[0];
}
function prose(source: string): string {
  let fence: string | undefined;
  return source.split('\n').filter(line => {
    const match = /^ {0,3}(`{3,}|~{3,})/.exec(line);
    if (match) {
      if (!fence) fence = match[1];
      else if (match[1][0] === fence[0] && match[1].length >= fence.length && !line.slice(match[0].length).trim()) fence = undefined;
      return false;
    }
    return !fence;
  }).join('\n');
}
/** Every ATX heading outside fences, in document order, with its level and exact text. */
function headingList(content: string): {level: number; text: string}[] {
  return [...prose(content).matchAll(/^(#{1,6})[ \t]+(.+?)[ \t]*$/gm)].map(m => ({level: m[1].length, text: m[2]}));
}
/** Each required heading (level 1-3) MUST appear, by exact text, strictly after the previous one;
 * other headings may interleave, and further sections MAY follow the last one. */
function requireOrderedHeadings(content: string, required: string[], subject: string): void {
  const found = headingList(content).filter(h => h.level <= 3).map(h => h.text); let cursor = -1;
  for (const heading of required) {
    const index = found.indexOf(heading, cursor + 1);
    requireThat(index > cursor, `Module Spec requires ${required.join(', ')} headings in order: ${subject}`);
    cursor = index;
  }
}
/** The Ontology section (level 1-3) MUST hold the Entities and Relationships subsections, each
 * exactly once, in that order and deeper than the Ontology heading. */
function requireOntologySubsections(content: string, subject: string): void {
  const all = headingList(content);
  const index = all.findIndex(h => h.text === 'Ontology' && h.level <= 3);
  requireThat(index >= 0, `Module Spec requires an Ontology section: ${subject}`);
  const inside: string[] = [];
  for (const h of all.slice(index + 1)) {
    if (h.level <= all[index].level) break;
    if (h.text === 'Entities' || h.text === 'Relationships') inside.push(h.text);
  }
  requireThat(inside.join(',') === 'Entities,Relationships', `Ontology requires Entities, Relationships subsections in order: ${subject}`);
}
const DEFINITION_HEADING = /^(#{2,5})([ \t]+)((?:scenario|req)\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)([ \t]+[—–-][ \t]+.+?)[ \t]*$/;
/** Scenario and requirement headings carry their ID as an explicit anchor, and every entity ID
 * becomes an anchor right before the block that declares it, so `path#id` links resolve. */
export function injectAnchors(content: string): string {
  let fence: string | undefined; const out: string[] = []; const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]; const marker = /^ {0,3}(`{3,}|~{3,})/.exec(line);
    if (marker) {
      if (!fence) {
        fence = marker[1];
        if (/^ {0,3}`{3,}concorde-(?:entities|contract)\s*$/.test(line)) {
          const body: string[] = []; let j = i + 1;
          while (j < lines.length && !/^ {0,3}`{3,}\s*$/.test(lines[j])) body.push(lines[j++]);
          try {
            const parsed = JSON.parse(body.join('\n'));
            const entries = (Array.isArray(parsed) ? parsed : [parsed]) as {id?: unknown}[];
            const anchors = entries.filter(e => typeof e.id === 'string').map(e => `<a id="${e.id as string}"></a>`);
            if (anchors.length) out.push(anchors.join(''), '');
          } catch {/* an unreadable block is reported by the registry loader, not here */}
        }
      } else if (marker[1][0] === fence[0] && marker[1].length >= fence.length && !line.slice(marker[0].length).trim()) fence = undefined;
      out.push(line); continue;
    }
    if (fence) {out.push(line); continue;}
    const heading = DEFINITION_HEADING.exec(line);
    out.push(heading ? `${heading[1]}${heading[2]}${heading[3]}${heading[4]} {#${heading[3]}}` : line);
  }
  return out.join('\n');
}
export function safeRead(root: string, path: string): string {
  safePath(path); let current = root;
  for (const part of path.split('/')) {
    current = resolve(current, part);
    requireThat(!lstatSync(current).isSymbolicLink(), `Symlink source: ${path}`);
  }
  requireThat(lstatSync(current).isFile(), `Source is not a regular file: ${path}`);
  return new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(readFileSync(current));
}
/** The adapter publishes Profile 12 projects only; anything else is an explicit error. */
export function requireScoped(root: string): void {
  let profile: unknown;
  try {profile = JSON.parse(safeRead(root, '.concorde/config.json')).profile_version;}
  catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new Error(`No Concorde project configuration at ${root}/.concorde/config.json; initialize the project first.`);
    }
    throw error;
  }
  if (profile !== 12) throw new Error(`Profile 12 is required to publish this project; .concorde/config.json declares profile_version ${String(profile)}.`);
}
interface DocumentContext {id: string; owner: string; main_visible: boolean}
function documentContext(source: string, path: string, expected: string[]): DocumentContext {
  const blocks = [...source.matchAll(/^```concorde-document\s*\n([\s\S]*?)^```\s*$/gm)];
  requireThat(blocks.length === 1, `Exactly one concorde-document block required: ${path}`);
  const value = JSON.parse(blocks[0][1]) as Partial<DocumentContext>;
  requireThat(Object.keys(value).sort().join(',') === 'id,main_visible,owner', `Invalid concorde-document fields: ${path}`);
  requireThat(typeof value.id === 'string' && ids.test(value.id), `Invalid document identity: ${path}`);
  requireThat(typeof value.owner === 'string' && ids.test(value.owner), `Invalid document targets: ${path}`);
  requireThat(typeof value.main_visible === 'boolean', `Invalid main_visible: ${path}`);
  requireThat(expected.length === 1 && value.owner === expected[0], `Document owner differs from registry ownership: ${path}`);
  return value as DocumentContext;
}
export function loadScopedRegistry(root: string): ScopedRegistry {
  const configText = safeRead(root, '.concorde/config.json'); const config = JSON.parse(configText);
  requireThat(config.profile_version === 12, 'Profile 12 configuration required');
  const registryText = safeRead(root, config.registry); const registry = JSON.parse(registryText);
  requireThat(Object.keys(registry).sort().join(',') === 'checks,entry_target,project_id,schema_version,targets', 'Invalid registry fields');
  requireThat(registry.schema_version === 4 && Array.isArray(registry.targets) && registry.targets.length, 'Module registry schema 4 required');
  const targets = registry.targets as Target[];
  const byId = new Map<string, Target>(); const allIds = new Set<string>();
  const documentTargets = new Map<string, string[]>();
  const inputs: [string, string][] = [['.concorde/config.json', hash(configText)], [config.registry, hash(registryText)]];
  for (const t of targets) {
    requireThat(Object.keys(t).sort().join(',') === 'checks,documents,files,id,kind,parent,references,title,uses', `Invalid Module fields: ${t.id}`);
    requireThat(typeof t.id === 'string' && ids.test(t.id) && !allIds.has(t.id), `Duplicate/invalid target identity: ${t.id}`); allIds.add(t.id);
    requireThat(t.kind === 'module' && typeof t.title === 'string' && t.title.trim(), `Invalid kind/title: ${t.id}`);
    requireThat(uniqueStrings(t.documents) && t.documents.length, `Explicit nonempty unique collection required: ${t.id}`);
    for (const key of ['uses', 'files', 'checks'] as const) requireThat(uniqueStrings(t[key]), `Invalid ${key}: ${t.id}`);
    requireThat(t.parent === null || typeof t.parent === 'string', `parent must be explicit: ${t.id}`);
    primaryDocument(t);
    for (const path of t.documents) {
      safePath(path); requireThat(path.endsWith('.md') && !/^(?:\.concorde|\.git)\//.test(path), `Spec documents must be durable Markdown: ${path}`);
      requireThat(!documentTargets.has(path), `Document must have one owner: ${path}`);
      documentTargets.set(path, [t.id]);
    }
    byId.set(t.id, t);
  }
  requireThat(byId.get(registry.entry_target)?.kind === 'module', 'Entry target must be a Module');
  // Finish structural admission before interpreting any Module's dependency prose.
  for (const module of targets) {
    const seen = new Set([module.id]); let cursor = module.parent;
    while (cursor !== null) {
      const parent = byId.get(cursor); requireThat(parent?.kind === 'module', `Unknown Module parent: ${cursor}`);
      requireThat(!seen.has(cursor), `Module composition cycle: ${module.id}`); seen.add(cursor); cursor = parent.parent;
    }
  }
  // A listing entry is a safe project path outside project-control directories: either an exact
  // file, or a directory prefix ending in `/` that binds the regular files below it. No entry
  // names a registered Spec document and no directory entry contains one. Unlike a document, one
  // entry may be listed by several Modules (schema 4 has no single implementation owner).
  for (const t of targets) for (const entry of t.files) {
    const directory = entry.endsWith('/'); const path = directory ? entry.slice(0, -1) : entry;
    safePath(path);
    requireThat(!/^(?:\.concorde|\.git|\.agents|\.claude|\.codex|generated)\//.test(path + '/'), `Unsafe file binding: ${entry}`);
    if (directory) requireThat(![...documentTargets.keys()].some(document => document.startsWith(entry)),
      `A listed directory cannot contain a Spec document: ${entry}`);
    else requireThat(!documentTargets.has(entry), `Unsafe file binding: ${entry}`);
    let cursor = root;
    for (const part of path.split('/')) {
      cursor = resolve(cursor, part);
      try {requireThat(!lstatSync(cursor).isSymbolicLink(), `Symlink file binding: ${entry}`);}
      catch (error) {if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;}
    }
    if (existsSync(cursor)) requireThat(directory ? lstatSync(cursor).isDirectory() : lstatSync(cursor).isFile(),
      directory ? `Directory binding must name a directory: ${entry}` : `File binding must name a file: ${entry}`);
  }
  const cache = new Map<string, {raw: string; content: string; declaration: DocumentContext}>();
  for (const [path, references] of documentTargets) {
    const raw = safeRead(root, path); const content = matter(raw).content; const declaration = documentContext(content, path, references);
    requireThat(!allIds.has(declaration.id), `Duplicate document identity: ${declaration.id}`); allIds.add(declaration.id);
    requireThat(content.trim(), `Empty Spec: ${path}`);
    cache.set(path, {raw, content, declaration}); inputs.push([path, hash(raw)]);
  }
  for (const t of targets) {
    requireThat(documentTargets.get(primaryDocument(t))!.length === 1, `Module reading entry must be local: ${t.id}`);
    requireOrderedHeadings(cache.get(primaryDocument(t))!.content, ['Purpose', 'Requirements', 'Scenarios', 'Ontology'], t.id);
    requireOntologySubsections(cache.get(primaryDocument(t))!.content, t.id);
    const seen = new Set([t.id]); let cursor = t.parent;
    while (cursor !== null) {
      const parent = byId.get(cursor); requireThat(parent?.kind === 'module', `Unknown Module parent: ${cursor}`);
      requireThat(!seen.has(cursor), `Module composition cycle: ${t.id}`); seen.add(cursor); cursor = parent.parent;
    }
    for (const peer of t.uses) {
      requireThat(peer !== t.id && byId.get(peer)?.kind === 'module', `Unknown/self Module dependency: ${peer}`);
    }
    const expected = new Set([...t.uses, ...targets.filter(child => child.parent === t.id).map(child => child.id)]);
    const declared = new Set<string>();
    for (const path of t.documents) for (const match of cache.get(path)!.content.matchAll(/^```concorde-dependencies\s*\n([\s\S]*?)^```\s*$/gm)) {
      const entries = JSON.parse(match[1]); requireThat(Array.isArray(entries) && entries.length, `Invalid dependency declaration: ${path}`);
      for (const d of entries) {
        requireThat(Object.keys(d).sort().join(',') === 'relied_upon_promises,responsibility,selection_condition,target_id', `Invalid dependency fields: ${path}`);
        requireThat(expected.has(d.target_id) && !declared.has(d.target_id), `Unrelated or duplicate Module dependency: ${d.target_id}`);
        requireThat(typeof d.responsibility === 'string' && d.responsibility.trim() && typeof d.selection_condition === 'string' && d.selection_condition.trim() && uniqueStrings(d.relied_upon_promises) && d.relied_upon_promises.length, `Incomplete dependency promises: ${path}`);
        declared.add(d.target_id);
      }
    }
    requireThat(declared.size === expected.size, `Missing local Module dependency promises: ${t.id}`);
    const consumers = targets.filter(m => m.uses.includes(t.id));
    if (consumers.length > 1) requireThat(consumers.every(m => m.parent === t.parent), `Shared Module and consumers must be siblings: ${t.id}`);
  }
  const byDocumentId = new Map([...cache].map(([path, value]) => [value.declaration.id, path]));
  const contexts = new Map<string, Map<string, {kind: 'owned' | 'module' | 'document'; id: string}[]>>();
  for (const t of targets) {
    const context = new Map<string, {kind: 'owned' | 'module' | 'document'; id: string}[]>(
      t.documents.map(path => [path, [{kind: 'owned', id: t.id}]]));
    requireThat(Array.isArray(t.references), `Explicit references required: ${t.id}`);
    const seen = new Set<string>();
    for (const ref of t.references) {
      requireThat(ref && Object.keys(ref).sort().join(',') === 'id,kind' &&
        ['module', 'document'].includes(ref.kind) && typeof ref.id === 'string' && ids.test(ref.id), `Invalid reference: ${t.id}`);
      const key = `${ref.kind}:${ref.id}`;
      requireThat(!seen.has(key), `Duplicate reference: ${key}`); seen.add(key);
      const paths = ref.kind === 'module' ? byId.get(ref.id)?.documents :
        (byDocumentId.has(ref.id) ? [byDocumentId.get(ref.id)!] : undefined);
      requireThat(paths && !(ref.kind === 'module' ? ref.id === t.id : t.documents.includes(paths[0])), `Unknown or self reference: ${key}`);
      for (const path of paths) context.set(path, [...(context.get(path) ?? []), {...ref}]);
    }
    for (const reasons of context.values()) reasons.sort((a,b) => (a.kind < b.kind ? -1 : a.kind > b.kind ? 1 : a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
    contexts.set(t.id, context);
  }
  const stripRoot = [...documentTargets.keys()].every(path => path.startsWith('specs/'));
  const pages: Page[] = []; const routes = new Set<string>(); const aliases = new Set<string>();
  for (const [path, references] of documentTargets) {
    const {raw, content, declaration} = cache.get(path)!;
    const owner = byId.get(declaration.owner)!;
    const primary = primaryDocument(owner) === path;
    const includedBy = [...contexts].filter(([, context]) => context.has(path))
      .map(([targetId, context]) => ({targetId, reasons: context.get(path)!}));
    const stagedPath = stripRoot ? path.slice('specs/'.length) : path; const route = '/specs/' + stagedPath.replace(/\.md$/, '');
    requireThat(!routes.has(route), `Duplicate page route: ${route}`); routes.add(route);
    const pageAliases = references.map(id => legacyAliasRoute(id, path)); pageAliases.forEach(alias => aliases.add(alias));
    const page: Page = {sourcePath: path, route, stagedPath, title: /^#\s+(.+)$/m.exec(prose(content))?.[1] ?? owner.title,
      content, contentDigest: hash(raw), documentId: declaration.id, owner: declaration.owner,
      mainVisible: declaration.main_visible, includedBy, aliases: pageAliases, kind: owner.kind, primaryOf: primary ? owner.id : null};
    pages.push(page);
  }
  for (const route of routes) requireThat(!aliases.has(route), `Canonical route collides with an alias: ${route}`);
  const definitions = new Map<string, {version: number; path: string}>();
  const bindings: {id: string; version: number; role: string; peer: string; owner: string; path: string}[] = [];
  for (const t of targets) for (const path of t.documents) {
    for (const match of cache.get(path)!.content.matchAll(/^```concorde-contract\s*\n([\s\S]*?)^```\s*$/gm)) {
      const c = JSON.parse(match[1]);
      requireThat(Object.keys(c).sort().join(',') === 'example,id,schema,semantics,version' &&
        typeof c.id === 'string' && ids.test(c.id) && Number.isInteger(c.version) && c.version > 0 &&
        typeof c.semantics === 'string' && c.semantics.trim(), `Invalid canonical definition: ${path}`);
      requireThat(!definitions.has(c.id), `Duplicate canonical definition: ${c.id}`);
      definitions.set(c.id, {version: c.version, path});
    }
    for (const match of cache.get(path)!.content.matchAll(/^```concorde-contract-binding\s*\n([\s\S]*?)^```\s*$/gm)) {
      const c = JSON.parse(match[1]);
      requireThat(Object.keys(c).sort().join(',') === 'id,obligations,peer,relied_upon_guarantees,role,selection_condition,version' &&
        typeof c.id === 'string' && ids.test(c.id) && Number.isInteger(c.version) && c.version > 0 &&
        ['provided','required'].includes(c.role) && typeof c.peer === 'string' && c.peer.trim() &&
        typeof c.selection_condition === 'string' && c.selection_condition.trim() &&
        uniqueStrings(c.relied_upon_guarantees) && c.relied_upon_guarantees.length &&
        uniqueStrings(c.obligations) && c.obligations.length, `Invalid participant binding: ${path}`);
      requireThat(!bindings.some(b => b.owner === t.id && b.id === c.id && b.role === c.role && b.peer === c.peer), `Duplicate binding: ${c.id}`);
      bindings.push({...c, owner: t.id, path});
    }
  }
  for (const b of bindings) {
    const definition = definitions.get(b.id);
    requireThat(definition?.version === b.version && contexts.get(b.owner)!.has(definition.path), `Missing context definition: ${b.id}`);
    if (b.peer.startsWith('external:') && b.peer.length > 9) continue;
    requireThat(bindings.some(p => p.owner === b.peer && p.peer === b.owner && p.id === b.id &&
      p.version === b.version && p.role !== b.role), `Missing complementary binding: ${b.id}`);
  }
  return {schema_version: 19, projectRoot: root, registryPath: config.registry, entryTarget: registry.entry_target, sourceDigest: hash(JSON.stringify(inputs)), targets, pages};
}
function stable(value: unknown): string {
  if (Array.isArray(value)) return '['+value.map(stable).join(',')+']';
  if (value && typeof value === 'object') return '{'+Object.entries(value).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>JSON.stringify(k)+':'+stable(v)).join(',')+'}';
  return JSON.stringify(value);
}
export function rewriteLinks(registry: ScopedRegistry,page: Page): string {
  let fence: string | undefined;
  return page.content.split('\n').map(line=> {
    const marker = /^\s*(```+|~~~+)/.exec(line)?.[1][0];
    if (marker) {fence = fence === marker ? undefined : fence ?? marker;return line;}
    if (fence) return line;
    return line.replace(/(!?\[[^\]]*\])\(([^\s)]+)\)/g,(whole,label:string,url:string)=> {
      if (/^(?:[a-z]+:|#|\/)/i.test(url)) return whole;
      const fragmentIndex = url.indexOf('#');
      const beforeFragment = fragmentIndex < 0 ? url : url.slice(0,fragmentIndex);
      const queryIndex = beforeFragment.indexOf('?');
      const path = queryIndex < 0 ? beforeFragment : beforeFragment.slice(0,queryIndex);
      const suffix = url.slice(path.length);
      const source = path ? posix.normalize(posix.join(posix.dirname(page.sourcePath),path)) : page.sourcePath;
      const target = registry.pages.find(p=>p.sourcePath===source);
      requireThat(target, `Unregistered local link: ${page.sourcePath} -> ${url}`);
      return `${label}(${target.route}${suffix})`;
    });
  }).join('\n');
}
