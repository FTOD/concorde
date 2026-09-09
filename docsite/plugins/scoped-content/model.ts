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
  diagrams: {source: string; kind: string; title: string; recipe?: 'system-overview'}[];
}
export interface Page {
  sourcePath: string; route: string; stagedPath: string; title: string; content: string; contentDigest: string;
  documentId: string; documentTargets: string[]; mainVisible: boolean; contextSection: 'target_spec' | 'shared_specs';
  memberships: {targetId: string; kind: Kind; primary: boolean}[];
  aliases: string[];
  kind: Kind;
  primaryOf: string | null;
  inlineOverview: boolean;
  architectureDiagrams?: {kind: string; title: string; source: string; sourceSha256: string; route: string}[];
}
export interface Edge {source: string; target: string; kind: 'scope_contains' | 'composes' | 'participates_in' | 'requires'; contract?: string}
export interface ScopedRegistry {
  schema_version: 15; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[]; edges: Edge[];
}
export const hash = (value: string | Buffer) => 'sha256:' + createHash('sha256').update(value).digest('hex');
function requireThat(value: unknown, message: string): asserts value {if (!value) throw new Error(message);}
/** The legacy `/specs/<target-id>/<source-path-hash>` route a document's membership was once published at, kept as a redirect. */
export function legacyAliasRoute(targetId: string, sourcePath: string): string {
  return `/specs/${targetId}/${hash(sourcePath).slice(7, 23)}`;
}
export function primaryDocument(target: Target): string {
  if (target.kind !== 'domain') return target.documents[0];
  const main = target.documents.filter(path => posix.basename(path) === 'ontology.md');
  requireThat(main.length === 1, `Domain must register exactly one ontology.md main Spec: ${target.id}`);
  return main[0];
}
function ontologyProse(source: string): string {
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
const ids = /^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$/;
interface DocumentContext {id:string; targets:string[]; main_visible:boolean}
function documentContext(source:string,path:string,expected:string[]):DocumentContext {
  const blocks=[...source.matchAll(/^```concorde-document\s*\n([\s\S]*?)^```\s*$/gm)];
  requireThat(blocks.length===1,`Exactly one concorde-document block required: ${path}`);
  const value=JSON.parse(blocks[0][1]) as Partial<DocumentContext>;
  requireThat(Object.keys(value).sort().join(',')==='id,main_visible,targets',`Invalid concorde-document fields: ${path}`);
  requireThat(typeof value.id==='string'&&ids.test(value.id),`Invalid document identity: ${path}`);
  requireThat(Array.isArray(value.targets)&&value.targets.length&&new Set(value.targets).size===value.targets.length&&
    value.targets.every(target=>typeof target==='string'&&ids.test(target)),`Invalid document targets: ${path}`);
  requireThat(typeof value.main_visible==='boolean',`Invalid document main_visible: ${path}`);
  requireThat(value.targets.length===expected.length&&value.targets.every(target=>expected.includes(target)),
    `Document targets differ from registry membership: ${path}`);
  return value as DocumentContext;
}
export function loadScopedRegistry(root: string): ScopedRegistry {
  const configText = safeRead(root, '.concorde/config.json'); const config = JSON.parse(configText);
  requireThat(config.profile_version === 8, 'Profile 8 configuration required');
  const registryText = safeRead(root, config.registry); const registry = JSON.parse(registryText);
  requireThat(registry.schema_version === 1 && Array.isArray(registry.targets), 'Spec registry schema 1 required');
  const targets = registry.targets as Target[]; const byId = new Map<string, Target>(); const allIds = new Set<string>();
  const documentTargets=new Map<string,string[]>();
  const edges: Edge[] = [];
  const inputs: [string, string][] = [['.concorde/config.json', hash(configText)], [config.registry, hash(registryText)]];
  for (const t of targets) {
    requireThat(ids.test(t.id) && !allIds.has(t.id), `Duplicate/invalid target identity: ${t.id}`); allIds.add(t.id);
    requireThat(['domain','service','module'].includes(t.kind) && typeof t.title === 'string' && t.title.trim(), `Invalid kind/title: ${t.id}`);
    requireThat(Array.isArray(t.documents) && t.documents.length && new Set(t.documents).size === t.documents.length, `Explicit nonempty unique collection required: ${t.id}`);
    for (const key of ['participates_in','implementation','features','apis','checks','diagrams'] as const) requireThat(Array.isArray(t[key]), `Missing ${key}: ${t.id}`);
    primaryDocument(t);
    const diagramSources = new Set<string>();
    for (const diagram of t.diagrams) {
      requireThat(diagram && ['source','kind','title'].every(key => typeof diagram[key as 'source'] === 'string') &&
        Object.keys(diagram).every(key => ['source','kind','title','recipe'].includes(key)), `Invalid diagram declaration: ${t.id}`);
      requireThat(diagram.source.endsWith('.json') && !/^(?:\.concorde|\.git|generated)\//.test(diagram.source),
        `Diagram source must be durable JSON: ${diagram.source}`);
      requireThat(['architecture','workflow','sequence','dataflow','lifecycle'].includes(diagram.kind) && diagram.title.trim(),
        `Invalid diagram kind/title: ${diagram.source}`);
      requireThat(!diagramSources.has(diagram.source), `Duplicate diagram source: ${diagram.source}`);
      diagramSources.add(diagram.source);
      requireThat(!('recipe' in diagram) || diagram.recipe === 'system-overview' && diagram.kind === 'architecture',
        `System overview must be an architecture diagram: ${t.id}`);
    }
    if (t.kind === 'domain') requireThat(t.diagrams.filter(d => d.recipe === 'system-overview').length === 1,
      `Domain must declare exactly one System overview: ${t.id}`);
    requireThat(t.scope_parent === null || typeof t.scope_parent === 'string', 'scope_parent must be explicit');
    requireThat(t.component_parent === null || typeof t.component_parent === 'string', 'component_parent must be explicit');
    requireThat(t.kind === 'domain' ? t.component_parent === null && !t.implementation.length && !t.participates_in.length : t.scope_parent === null, `Independent architecture dimensions violated: ${t.id}`);
    requireThat(t.kind === 'module' ? !t.features.length : !t.apis.length, `Module APIs and Service/Domain Features are distinct: ${t.id}`);
    for(const path of t.documents){
      requireThat(typeof path === 'string' && path.endsWith('.md') && !/^(?:\.concorde|\.git)\//.test(path),
        `Spec documents must be durable Markdown: ${path}`);
      const references=documentTargets.get(path)??[];
      references.push(t.id);documentTargets.set(path,references);
    }
    byId.set(t.id,t);
  }
  requireThat(byId.has(registry.entry_target), 'Unknown entry target');
  const documentContexts=new Map<string,DocumentContext>();const documentIds=new Map<string,string>();
  for(const [path,references] of documentTargets){
    const context=documentContext(safeRead(root,path),path,references);const previous=documentIds.get(context.id);
    requireThat(!previous||previous===path,`Duplicate document identity ${context.id}: ${previous} and ${path}`);
    requireThat(!allIds.has(context.id),`Document identity collides with target: ${context.id}`);
    allIds.add(context.id);documentIds.set(context.id,path);documentContexts.set(path,context);
  }
  // A project whose Specs are not entirely rooted at specs/ keeps full paths; Concorde's own
  // repository (and every project that follows its convention) gets a readable specs/-relative route.
  const stripSpecsRoot = [...documentTargets.keys()].every(path => path.startsWith('specs/'));
  const contentCache = new Map<string, {raw: string; content: string}>();
  const membershipsByPath = new Map<string, {targetId: string; kind: Kind; primary: boolean}[]>();
  const diagramAttachments: {targetId: string; diagram: NonNullable<Page['architectureDiagrams']>[number]}[] = [];
  for (const t of targets) {
    if (t.kind === 'domain') {
      const main = primaryDocument(t); const declaration = documentContexts.get(main)!;
      requireThat(declaration.targets.length === 1 && declaration.targets[0] === t.id,
        `Domain main Spec must be local: ${main}`);
      requireThat(declaration.main_visible, `Domain ontology.md must be main_visible: ${main}`);
      const prose = ontologyProse(safeRead(root, main));
      requireThat(/^## Ontology\s*$/m.test(prose), `Domain main Spec requires an Ontology section: ${main}`);
    }
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
      let cached = contentCache.get(path);
      if (!cached) {
        const raw = safeRead(root,path); const content = matter(raw).content; requireThat(content.trim(), `Empty Spec: ${path}`);
        cached = {raw, content}; contentCache.set(path, cached);
      }
      inputs.push([path,hash(cached.raw)]);
      const memberships = membershipsByPath.get(path) ?? [];
      memberships.push({targetId: t.id, kind: t.kind, primary: path === primaryDocument(t)});
      membershipsByPath.set(path, memberships);
    }
    for (const focus of [...t.features,...t.apis]) {
      requireThat(ids.test(focus.id) && !allIds.has(focus.id), `Duplicate/invalid focus: ${focus.id}`); allIds.add(focus.id);
      requireThat(t.documents.includes(focus.document) && (contentCache.get(focus.document)?.content.includes(focus.id) ?? false), `Foreign or undefined local focus: ${focus.id}`);
    }
    for (const d of t.diagrams) {
      const raw = safeRead(root,d.source); const source = JSON.parse(raw);
      requireThat(source.diagram_type === d.kind && source.meta?.title === d.title, `Diagram declaration differs: ${d.source}`);
      if (d.recipe === 'system-overview') requireThat(source.meta?.quality_profile === 'showcase',
        `System overview must request showcase validation: ${d.source}`);
      inputs.push([d.source,hash(raw)]);
      const output = posix.normalize(posix.join(posix.dirname(d.source),source.meta.output ?? ''));
      requireThat(output.startsWith('generated/diagrams/') && output.endsWith('.html'), `Diagram output must be HTML under generated/diagrams/: ${d.source}`);
      diagramAttachments.push({targetId:t.id,diagram:{kind:d.kind,title:d.title,source:d.source,sourceSha256:hash(raw).slice(7),route:'/diagrams/'+hash(d.source).slice(7,23)+'.html'}});
    }
  }
  // One Page per distinct registered physical document: a shared Spec is published once, in the
  // order its sourcePath was first registered, and carries every declared membership alongside it.
  const pages: Page[] = []; const pageByPath = new Map<string, Page>(); const routeOwners = new Map<string, string>();
  const allAliases = new Set<string>();
  for (const [path, memberships] of membershipsByPath) {
    const {raw, content} = contentCache.get(path)!;
    const context = documentContexts.get(path)!;
    const relative = stripSpecsRoot ? path.slice('specs/'.length) : path;
    const route = `/specs/${relative.replace(/\.md$/, '')}`;
    const stagedPath = relative;
    requireThat(!stagedPath.startsWith('projections/'), `Staged path reserved for the Projections group: ${path}`);
    requireThat(!routeOwners.has(route), `Duplicate canonical route ${route}: ${routeOwners.get(route)} and ${path}`);
    routeOwners.set(route, path);
    const primaryMembership = memberships.find(m => m.primary);
    const kind = (primaryMembership ?? memberships[0]).kind;
    const primaryOf = primaryMembership?.targetId ?? null;
    const fallbackTitleOwner = byId.get((primaryMembership ?? memberships[0]).targetId)!;
    const title = /^#\s+(.+)$/m.exec(content)?.[1] ?? fallbackTitleOwner.title;
    const aliases = memberships.map(m => legacyAliasRoute(m.targetId, path));
    for (const alias of aliases) allAliases.add(alias);
    const page: Page = {
      sourcePath: path, route, stagedPath, title, content, contentDigest: hash(raw),
      documentId: context.id, documentTargets: context.targets, mainVisible: context.main_visible,
      contextSection: context.targets.length > 1 ? 'shared_specs' : 'target_spec',
      memberships, aliases, kind, primaryOf,
      inlineOverview: kind === 'domain' && primaryOf !== null && /^## Architecture overview\s*$/m.test(ontologyProse(content)),
    };
    pages.push(page); pageByPath.set(path, page);
  }
  for (const route of routeOwners.keys()) requireThat(!allAliases.has(route), `Canonical route collides with a legacy alias route: ${route}`);
  for (const attachment of diagramAttachments) {
    const page = pageByPath.get(primaryDocument(byId.get(attachment.targetId)!))!;
    (page.architectureDiagrams ??= []).push(attachment.diagram);
  }
  const providers = new Map<string,{owner:string;schema:string}>();
  const required: {owner:string;peer:string;key:string;schema:string}[] = [];
  // Contract links are navigation/consistency edges, never context inheritance.
  for (const t of targets) for (const path of t.documents) for (const match of contentCache.get(path)!.content.matchAll(/^```concorde-contract\s*\n([\s\S]*?)^```\s*$/gm)) {
    const c = JSON.parse(match[1]); const key = `${c.id}@${c.version}`; const schema = stable(c.schema);
    if (c.role === 'provided') {requireThat(!providers.has(key), `Duplicate contract provider: ${key}`);providers.set(key,{owner:t.id,schema});}
    else if (c.role === 'required') required.push({owner:t.id,peer:c.peer,key,schema});
    else throw new Error(`Invalid contract role: ${key}`);
  }
  for (const c of required) {
    if (c.peer.startsWith('external:')) continue;
    const p = providers.get(c.key);requireThat(p?.owner === c.peer && p.schema === c.schema, `Incompatible shared contract: ${c.key}`);
    edges.push({source:c.owner,target:c.peer,kind:'requires',contract:c.key});
  }
  return {schema_version:15,projectRoot:root,registryPath:config.registry,entryTarget:registry.entry_target,sourceDigest:hash(JSON.stringify(inputs)),targets,pages,edges};
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
