/** Module/Implementation publication model. Registered documents are the only sources. */
import {createHash} from 'node:crypto';
import {existsSync, lstatSync, readFileSync} from 'node:fs';
import {posix, resolve} from 'node:path';
import matter from 'gray-matter';

export type Kind = 'module' | 'implementation';
export interface Focus {id: string; title: string; document: string}
/** Publication nodes include Modules and separately registered Implementation Specs. */
export interface Target {
  id: string; kind: Kind; title: string; documents: string[];
  parent: string | null; uses: string[]; implementations: string[];
  features: Focus[]; interfaces: Focus[]; checks: string[];
  diagrams: {source: string; kind: string; title: string; recipe?: 'system-overview'}[];
  files?: string[];
}
export interface Page {
  sourcePath: string; route: string; stagedPath: string; title: string; content: string; contentDigest: string;
  documentId: string; documentTargets: string[]; mainVisible: boolean; contextSection: 'target_spec' | 'shared_specs';
  memberships: {targetId: string; kind: Kind; primary: boolean}[]; aliases: string[];
  kind: Kind; primaryOf: string | null; inlineOverview: boolean;
  architectureDiagrams?: {kind: string; title: string; source: string; sourceSha256: string; route: string}[];
}
export interface Edge {source: string; target: string; kind: 'composes' | 'uses' | 'implemented_by' | 'requires'; contract?: string}
export interface ScopedRegistry {
  schema_version: 16; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[]; edges: Edge[];
}
export const hash = (value: string | Buffer) => 'sha256:' + createHash('sha256').update(value).digest('hex');
function requireThat(value: unknown, message: string): asserts value {if (!value) throw new Error(message);}
const ids = /^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$/;
function uniqueStrings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(v => typeof v === 'string' && v.trim()) && new Set(value).size === value.length;
}
function safePath(path: string): void {
  requireThat(typeof path === 'string' && path.length && !path.includes('\\') && !path.startsWith('/') &&
    path.split('/').every(p => p && p !== '.' && p !== '..'), `Unsafe source path: ${path}`);
}
export function legacyAliasRoute(targetId: string, sourcePath: string): string {
  return `/specs/${targetId}/${hash(sourcePath).slice(7, 23)}`;
}
export function primaryDocument(target: Target): string {
  if (target.kind === 'implementation') return target.documents[0];
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
export function safeRead(root: string, path: string): string {
  safePath(path); let current = root;
  for (const part of path.split('/')) {
    current = resolve(current, part);
    requireThat(!lstatSync(current).isSymbolicLink(), `Symlink source: ${path}`);
  }
  requireThat(lstatSync(current).isFile(), `Source is not a regular file: ${path}`);
  return readFileSync(current, 'utf8');
}
export function isScoped(root: string): boolean {
  try {return JSON.parse(safeRead(root, '.concorde/config.json')).profile_version === 9;}
  catch (error) {if ((error as NodeJS.ErrnoException).code === 'ENOENT') return false; throw error;}
}
interface DocumentContext {id: string; targets: string[]; main_visible: boolean}
function documentContext(source: string, path: string, expected: string[]): DocumentContext {
  const blocks = [...source.matchAll(/^```concorde-document\s*\n([\s\S]*?)^```\s*$/gm)];
  requireThat(blocks.length === 1, `Exactly one concorde-document block required: ${path}`);
  const value = JSON.parse(blocks[0][1]) as Partial<DocumentContext>;
  requireThat(Object.keys(value).sort().join(',') === 'id,main_visible,targets', `Invalid concorde-document fields: ${path}`);
  requireThat(typeof value.id === 'string' && ids.test(value.id), `Invalid document identity: ${path}`);
  requireThat(uniqueStrings(value.targets) && value.targets.length && value.targets.every(t => ids.test(t)), `Invalid document targets: ${path}`);
  requireThat(typeof value.main_visible === 'boolean', `Invalid main_visible: ${path}`);
  requireThat(value.targets.length === expected.length && value.targets.every(t => expected.includes(t)), `Document targets differ from registry membership: ${path}`);
  return value as DocumentContext;
}
export function loadScopedRegistry(root: string): ScopedRegistry {
  const configText = safeRead(root, '.concorde/config.json'); const config = JSON.parse(configText);
  requireThat(config.profile_version === 9, 'Profile 9 configuration required');
  const registryText = safeRead(root, config.registry); const registry = JSON.parse(registryText);
  requireThat(Object.keys(registry).sort().join(',') === 'checks,entry_target,implementations,project_id,schema_version,targets', 'Invalid registry fields');
  requireThat(registry.schema_version === 2 && Array.isArray(registry.targets) && registry.targets.length &&
    Array.isArray(registry.implementations), 'Module/Implementation registry schema 2 required');
  const modules = registry.targets as Target[];
  const implementations: Target[] = registry.implementations.map((raw: {id: string; title: string; documents: string[]; files: string[]}) => {
    requireThat(Object.keys(raw).sort().join(',') === 'documents,files,id,title', 'Implementation requires id/title/documents/files');
    requireThat(uniqueStrings(raw.files) && raw.files.length, `Explicit implementation files required: ${raw.id}`);
    return {...raw, kind: 'implementation', parent: null, uses: [], implementations: [], features: [], interfaces: [], checks: [], diagrams: []};
  });
  const targets = [...modules, ...implementations]; const byId = new Map<string, Target>(); const allIds = new Set<string>();
  const documentTargets = new Map<string, string[]>(); const edges: Edge[] = [];
  const inputs: [string, string][] = [['.concorde/config.json', hash(configText)], [config.registry, hash(registryText)]];
  for (const t of targets) {
    if (!implementations.includes(t)) requireThat(Object.keys(t).sort().join(',') === 'checks,diagrams,documents,features,id,implementations,interfaces,kind,parent,title,uses', `Invalid Module fields: ${t.id}`);
    requireThat(typeof t.id === 'string' && ids.test(t.id) && !allIds.has(t.id), `Duplicate/invalid target identity: ${t.id}`); allIds.add(t.id);
    requireThat((implementations.includes(t) || t.kind === 'module') && typeof t.title === 'string' && t.title.trim(), `Invalid kind/title: ${t.id}`);
    requireThat(uniqueStrings(t.documents) && t.documents.length, `Explicit nonempty unique collection required: ${t.id}`);
    for (const key of ['uses','implementations','checks'] as const) requireThat(uniqueStrings(t[key]), `Invalid ${key}: ${t.id}`);
    for (const key of ['features','interfaces','diagrams'] as const) requireThat(Array.isArray(t[key]), `Missing ${key}: ${t.id}`);
    requireThat(t.parent === null || typeof t.parent === 'string', `parent must be explicit: ${t.id}`);
    primaryDocument(t);
    for (const path of t.documents) {
      safePath(path); requireThat(path.endsWith('.md') && !/^(?:\.concorde|\.git)\//.test(path), `Spec documents must be durable Markdown: ${path}`);
      const refs = documentTargets.get(path) ?? []; refs.push(t.id); documentTargets.set(path, refs);
    }
    byId.set(t.id, t);
  }
  requireThat(byId.get(registry.entry_target)?.kind === 'module', 'Entry target must be a Module');
  // Finish structural admission before interpreting any Module's dependency prose.
  for (const module of modules) {
    const seen = new Set([module.id]); let cursor = module.parent;
    while (cursor !== null) {
      const parent = byId.get(cursor); requireThat(parent?.kind === 'module', `Unknown Module parent: ${cursor}`);
      requireThat(!seen.has(cursor), `Module composition cycle: ${module.id}`); seen.add(cursor); cursor = parent.parent;
    }
  }

  const fileOwners = new Map<string, string>();
  const diagramPaths = new Set(modules.flatMap(module => module.diagrams.map(diagram => diagram.source)));
  for (const t of implementations) for (const path of t.files!) {
    safePath(path);
    requireThat(!/^(?:\.concorde|\.git|\.agents|\.claude|\.codex|generated)\//.test(path) && !documentTargets.has(path) && !diagramPaths.has(path), `Unsafe implementation binding: ${path}`);
    requireThat(!fileOwners.has(path), `Implementation file has multiple owners: ${path}`); fileOwners.set(path, t.id);
    let cursor = root;
    for (const part of path.split('/')) {
      cursor = resolve(cursor, part);
      try {requireThat(!lstatSync(cursor).isSymbolicLink(), `Symlink implementation binding: ${path}`);}
      catch (error) {if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;}
    }
    if (existsSync(cursor)) requireThat(lstatSync(cursor).isFile(), `Implementation binding must name a file: ${path}`);
  }
  const cache = new Map<string, {raw: string; content: string; declaration: DocumentContext}>();
  for (const [path, references] of documentTargets) {
    const raw = safeRead(root, path); const content = matter(raw).content; const declaration = documentContext(content, path, references);
    requireThat(!allIds.has(declaration.id), `Duplicate document identity: ${declaration.id}`); allIds.add(declaration.id);
    requireThat(content.trim(), `Empty Spec: ${path}`);
    if (references.some(id => byId.get(id)!.kind === 'implementation')) requireThat(references.length === 1, `Implementation Spec documents cannot be shared with another Spec: ${path}`);
    cache.set(path, {raw, content, declaration}); inputs.push([path, hash(raw)]);
  }
  for (const t of targets) {
    if (t.kind === 'module') {
      requireThat(documentTargets.get(primaryDocument(t))!.length === 1, `Module reading entry must be local: ${t.id}`);
      requireThat(/^#{1,3} Architecture\s*$/m.test(t.documents.map(path => prose(cache.get(path)!.content)).join('\n')), `Module Spec requires Architecture: ${t.id}`);
      requireThat(!t.features.length || t.interfaces.length, `Module features require usage interfaces: ${t.id}`);
    }
    const seen = new Set([t.id]); let cursor = t.parent;
    while (cursor !== null) {
      const parent = byId.get(cursor); requireThat(parent?.kind === 'module', `Unknown Module parent: ${cursor}`);
      requireThat(!seen.has(cursor), `Module composition cycle: ${t.id}`); seen.add(cursor); cursor = parent.parent;
    }
    if (t.parent) edges.push({source: t.parent, target: t.id, kind: 'composes'});
    for (const peer of t.uses) {
      requireThat(peer !== t.id && byId.get(peer)?.kind === 'module', `Unknown/self Module dependency: ${peer}`);
      edges.push({source: t.id, target: peer, kind: 'uses'});
    }
    for (const implementation of t.implementations) {
      requireThat(byId.get(implementation)?.kind === 'implementation', `Unknown Implementation Spec: ${implementation}`);
      edges.push({source: t.id, target: implementation, kind: 'implemented_by'});
    }
    for (const focus of [...t.features, ...t.interfaces]) {
      requireThat(Object.keys(focus).sort().join(',') === 'document,id,title' && typeof focus.title === 'string' && focus.title.trim(), `Invalid feature/interface: ${t.id}`);
      requireThat(ids.test(focus.id) && !allIds.has(focus.id), `Duplicate/invalid focus: ${focus.id}`); allIds.add(focus.id);
      requireThat(t.documents.includes(focus.document) && cache.get(focus.document)!.content.includes(focus.id), `Foreign or undefined focus: ${focus.id}`);
    }
    if (t.kind === 'module') {
      const expected = new Set([...t.uses, ...modules.filter(child => child.parent === t.id).map(child => child.id)]);
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
      const consumers = modules.filter(m => m.uses.includes(t.id));
      if (consumers.length > 1) requireThat(consumers.every(m => m.parent === t.parent), `Shared Module and consumers must be siblings: ${t.id}`);
    }
  }
  const stripRoot = [...documentTargets.keys()].every(path => path.startsWith('specs/'));
  const pages: Page[] = []; const pageByPath = new Map<string, Page>(); const routes = new Set<string>(); const aliases = new Set<string>();
  for (const [path, references] of documentTargets) {
    const {raw, content, declaration} = cache.get(path)!;
    const memberships = references.map(id => {const t = byId.get(id)!; return {targetId: id, kind: t.kind, primary: primaryDocument(t) === path};});
    const primary = memberships.find(m => m.primary); const owner = byId.get((primary ?? memberships[0]).targetId)!;
    const stagedPath = stripRoot ? path.slice('specs/'.length) : path; const route = '/specs/' + stagedPath.replace(/\.md$/, '');
    requireThat(!stagedPath.startsWith('projections/') && !routes.has(route), `Duplicate or reserved page route: ${route}`); routes.add(route);
    const pageAliases = references.map(id => legacyAliasRoute(id, path)); pageAliases.forEach(alias => aliases.add(alias));
    const page: Page = {sourcePath: path, route, stagedPath, title: /^#\s+(.+)$/m.exec(content)?.[1] ?? owner.title,
      content, contentDigest: hash(raw), documentId: declaration.id, documentTargets: declaration.targets,
      mainVisible: declaration.main_visible, contextSection: references.length > 1 ? 'shared_specs' : 'target_spec',
      memberships, aliases: pageAliases, kind: owner.kind, primaryOf: primary?.targetId ?? null,
      inlineOverview: false};
    pages.push(page); pageByPath.set(path, page);
  }
  for (const route of routes) requireThat(!aliases.has(route), `Canonical route collides with an alias: ${route}`);
  for (const t of modules) {
    const declared = new Set<string>();
    for (const d of t.diagrams) {
      requireThat(d && Object.keys(d).every(k => ['source','kind','title','recipe'].includes(k)) && ['architecture','workflow','sequence','dataflow','lifecycle'].includes(d.kind) && typeof d.title === 'string' && d.title.trim(), `Invalid diagram declaration: ${t.id}`);
      safePath(d.source); requireThat(d.source.endsWith('.json') && !/^(?:\.concorde|\.git|generated)\//.test(d.source) && !declared.has(d.source), `Invalid/duplicate diagram source: ${d.source}`); declared.add(d.source);
      requireThat(!d.recipe || d.recipe === 'system-overview' && d.kind === 'architecture', `Invalid diagram recipe: ${d.source}`);
      const raw = safeRead(root, d.source); const value = JSON.parse(raw);
      requireThat(value.diagram_type === d.kind && value.meta?.title === d.title, `Diagram declaration differs: ${d.source}`);
      if (d.recipe) requireThat(value.meta?.quality_profile === 'showcase', `System overview requires showcase validation: ${d.source}`);
      const output = posix.normalize(posix.join(posix.dirname(d.source), value.meta?.output ?? ''));
      requireThat(output.startsWith('generated/diagrams/') && output.endsWith('.html'), `Invalid diagram output: ${d.source}`);
      inputs.push([d.source, hash(raw)]);
      (pageByPath.get(primaryDocument(t))!.architectureDiagrams ??= []).push({kind: d.kind, title: d.title, source: d.source, sourceSha256: hash(raw).slice(7), route: '/diagrams/' + hash(d.source).slice(7,23) + '.html'});
    }
  }
  const providers = new Map<string, {owner: string; schema: string}>(); const required: {owner: string; peer: string; key: string; schema: string}[] = [];
  for (const t of modules) for (const path of t.documents) for (const match of cache.get(path)!.content.matchAll(/^```concorde-contract\s*\n([\s\S]*?)^```\s*$/gm)) {
    const c = JSON.parse(match[1]); const key = `${c.id}@${c.version}`; const schema = stable(c.schema);
    if (c.role === 'provided') {requireThat(!providers.has(key), `Duplicate provider: ${key}`); providers.set(key, {owner: t.id, schema});}
    else if (c.role === 'required') required.push({owner: t.id, peer: c.peer, key, schema});
    else throw new Error(`Invalid contract role: ${key}`);
  }
  for (const c of required) {
    if (c.peer.startsWith('external:')) continue;
    const provider = providers.get(c.key); requireThat(provider?.owner === c.peer && provider.schema === c.schema, `Incompatible shared contract: ${c.key}`);
    edges.push({source: c.owner, target: c.peer, kind: 'requires', contract: c.key});
  }
  return {schema_version: 16, projectRoot: root, registryPath: config.registry, entryTarget: registry.entry_target, sourceDigest: hash(JSON.stringify(inputs)), targets, pages, edges};
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
      const [path,anchor] = url.split('#'); const source = posix.normalize(posix.join(posix.dirname(page.sourcePath),path));
      const target = registry.pages.find(p=>p.sourcePath===source);
      requireThat(target, `Unregistered local link: ${page.sourcePath} -> ${url}`);
      return `${label}(${target.route}${anchor?'#'+anchor:''})`;
    });
  }).join('\n');
}
