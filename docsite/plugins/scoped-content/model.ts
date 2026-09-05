/** Profile 8 is an explicit publication registry, never a filename-discovery convention. */
import {createHash} from 'node:crypto';
import {lstatSync, readFileSync} from 'node:fs';
import {posix, resolve} from 'node:path';
import matter from 'gray-matter';

export type Kind = 'domain' | 'service' | 'module';
export interface Focus {id: string; title: string; document: string}
export interface Target {
  id: string; kind: Kind; title: string; documents: string[];
  scope_parent: string | null; component_parent: string | null; participates_in: string[];
  implementation: string[]; features: Focus[]; apis: Focus[]; checks: string[];
  diagrams: {source: string; kind: string; title: string}[];
}
export interface Page {
  targetId: string; kind: Kind; title: string; sourcePath: string; contentDigest: string;
  route: string; stagedPath: string; content: string;
  architectureDiagrams?: {kind: string; title: string; source: string; sourceSha256: string; route: string}[];
}
export interface Edge {source: string; target: string; kind: 'scope_contains' | 'composes' | 'participates_in' | 'requires'; contract?: string}
export interface ScopedRegistry {
  schema_version: 14; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[]; edges: Edge[];
}
export const hash = (value: string | Buffer) => 'sha256:' + createHash('sha256').update(value).digest('hex');
function requireThat(value: unknown, message: string): asserts value {if (!value) throw new Error(message);}
export function safeRead(root: string, path: string): string {
  requireThat(typeof path === 'string' && path.length && !path.includes('\\') && !path.startsWith('/') &&
    path.split('/').every(p => p && p !== '.' && p !== '..'), `Unsafe source path: ${path}`);
  let current = root;
  for (const part of path.split('/')) {
    current = resolve(current, part);
    requireThat(!lstatSync(current).isSymbolicLink(), `Symlink source: ${path}`);
  }
  requireThat(lstatSync(current).isFile(), `Source is not a regular file: ${path}`);
  return readFileSync(current, 'utf8');
}
export function isScoped(root: string): boolean {
  try {return JSON.parse(safeRead(root, '.concorde/config.json')).profile_version === 8;}
  catch (error) {if ((error as NodeJS.ErrnoException).code === 'ENOENT') return false; throw error;}
}
const ids = /^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$/;
export function loadScopedRegistry(root: string): ScopedRegistry {
  const configText = safeRead(root, '.concorde/config.json'); const config = JSON.parse(configText);
  requireThat(config.profile_version === 8, 'Profile 8 configuration required');
  const registryText = safeRead(root, config.registry); const registry = JSON.parse(registryText);
  requireThat(registry.schema_version === 1 && Array.isArray(registry.targets), 'Spec registry schema 1 required');
  const targets = registry.targets as Target[]; const byId = new Map<string, Target>(); const allIds = new Set<string>();
  const pages: Page[] = []; const edges: Edge[] = [];
  const inputs: [string, string][] = [['.concorde/config.json', hash(configText)], [config.registry, hash(registryText)]];
  for (const t of targets) {
    requireThat(ids.test(t.id) && !allIds.has(t.id), `Duplicate/invalid target identity: ${t.id}`); allIds.add(t.id);
    requireThat(['domain','service','module'].includes(t.kind) && typeof t.title === 'string' && t.title.trim(), `Invalid kind/title: ${t.id}`);
    requireThat(Array.isArray(t.documents) && t.documents.length && new Set(t.documents).size === t.documents.length, `Explicit nonempty unique collection required: ${t.id}`);
    for (const key of ['participates_in','implementation','features','apis','checks','diagrams'] as const) requireThat(Array.isArray(t[key]), `Missing ${key}: ${t.id}`);
    requireThat(t.scope_parent === null || typeof t.scope_parent === 'string', 'scope_parent must be explicit');
    requireThat(t.component_parent === null || typeof t.component_parent === 'string', 'component_parent must be explicit');
    requireThat(t.kind === 'domain' ? t.component_parent === null && !t.implementation.length && !t.participates_in.length : t.scope_parent === null, `Independent architecture dimensions violated: ${t.id}`);
    requireThat(t.kind === 'module' ? !t.features.length : !t.apis.length, `Module APIs and Service/Domain Features are distinct: ${t.id}`);
    byId.set(t.id,t);
  }
  requireThat(byId.has(registry.entry_target), 'Unknown entry target');
  for (const t of targets) {
    for (const [key, kind] of [['scope_parent','scope_contains'],['component_parent','composes']] as const) {
      const parent = t[key]; const seen = new Set([t.id]); let cursor = parent;
      while (cursor) {
        const node = byId.get(cursor); requireThat(node, `Unknown parent: ${cursor}`);
        requireThat(!seen.has(cursor), `Hierarchy cycle: ${t.id}`); seen.add(cursor);
        requireThat(key === 'scope_parent' ? node.kind === 'domain' : node.kind !== 'domain', `Wrong parent dimension: ${t.id}`);
        cursor = node[key];
      }
      if (parent) edges.push({source:parent,target:t.id,kind});
    }
    for (const scope of t.participates_in) {requireThat(byId.get(scope)?.kind === 'domain', `Unknown participating scope: ${scope}`); edges.push({source:t.id,target:scope,kind:'participates_in'});}
    for (const path of t.documents) {
      requireThat(path.endsWith('.md'), `Spec member must be Markdown: ${path}`);
      const raw = safeRead(root,path); const content = matter(raw).content; requireThat(content.trim(), `Empty Spec: ${path}`);
      const title = /^#\s+(.+)$/m.exec(content)?.[1] ?? t.title; const key = hash(path).slice(7,23);
      pages.push({targetId:t.id,kind:t.kind,title,sourcePath:path,contentDigest:hash(raw),route:`/specs/${t.id}/${key}`,stagedPath:`${t.id}/${key}.md`,content});
      inputs.push([path,hash(raw)]);
    }
    for (const focus of [...t.features,...t.apis]) {
      requireThat(ids.test(focus.id) && !allIds.has(focus.id), `Duplicate/invalid focus: ${focus.id}`); allIds.add(focus.id);
      requireThat(t.documents.includes(focus.document) && pages.some(p => p.targetId === t.id && p.sourcePath === focus.document && p.content.includes(focus.id)), `Foreign or undefined local focus: ${focus.id}`);
    }
    for (const d of t.diagrams) {
      const raw = safeRead(root,d.source); const source = JSON.parse(raw);
      requireThat(source.diagram_type === d.kind && source.meta?.title === d.title, `Diagram declaration differs: ${d.source}`);
      inputs.push([d.source,hash(raw)]);
      const output = posix.normalize(posix.join(posix.dirname(d.source),source.meta.output ?? ''));
      requireThat(output.startsWith('generated/') && output.endsWith('.html'), `Diagram output must be generated HTML: ${d.source}`);
      const page = pages.find(p=>p.targetId===t.id)!;
      (page.architectureDiagrams ??= []).push({kind:d.kind,title:d.title,source:d.source,sourceSha256:hash(raw).slice(7),route:'/diagrams/'+hash(d.source).slice(7,23)+'.html'});
    }
  }
  const providers = new Map<string,{owner:string;schema:string}>();
  const required: {owner:string;peer:string;key:string;schema:string}[] = [];
  // Contract links are navigation/consistency edges, never context inheritance.
  for (const page of pages) for (const match of page.content.matchAll(/^```concorde-contract\s*\n([\s\S]*?)^```\s*$/gm)) {
    const c = JSON.parse(match[1]); const key = `${c.id}@${c.version}`; const schema = stable(c.schema);
    if (c.role === 'provided') {requireThat(!providers.has(key), `Duplicate contract provider: ${key}`);providers.set(key,{owner:page.targetId,schema});}
    else if (c.role === 'required') required.push({owner:page.targetId,peer:c.peer,key,schema});
    else throw new Error(`Invalid contract role: ${key}`);
  }
  for (const c of required) {
    if (c.peer.startsWith('external:')) continue;
    const p = providers.get(c.key);requireThat(p?.owner === c.peer && p.schema === c.schema, `Incompatible shared contract: ${c.key}`);
    edges.push({source:c.owner,target:c.peer,kind:'requires',contract:c.key});
  }
  return {schema_version:14,projectRoot:root,registryPath:config.registry,entryTarget:registry.entry_target,sourceDigest:hash(JSON.stringify(inputs)),targets,pages,edges};
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
      const matches = registry.pages.filter(p=>p.sourcePath===source);const target = matches.find(p=>p.targetId===page.targetId) ?? (matches.length===1?matches[0]:undefined);
      requireThat(target, `Unregistered or ambiguous local link: ${page.sourcePath} -> ${url}`);
      return `${label}(${target.route}${anchor?'#'+anchor:''})`;
    });
  }).join('\n');
}
