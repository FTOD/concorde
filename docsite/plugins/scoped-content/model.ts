/** Module publication model for Spec Protocol 11. Registered documents are the only sources. */
import { createHash } from "node:crypto";
import { lstatSync, readFileSync } from "node:fs";
import { posix, resolve } from "node:path";
import matter from "gray-matter";
import {
  contracts,
  definitionHeadings,
  identityPattern,
  metadata,
  moduleBlock,
  parseJson,
  prose,
  readingMeanings,
  requireReading,
  requireThat,
  terminologyRows,
  type DocumentMetadata,
  type ModuleBlock,
  type Selection,
} from "./reading-format";

export type ReadingCollection = "module" | "implementation";
/** One registry record: the Module's identity, entry and the mirror of its `module` block. */
export interface ModuleRecord extends ModuleBlock {
  id: string;
  entry: string;
}
/** Why a Module's Spec context selects a document: the declaring relation and its target; an
 * `includes` also says whether it names a Module or a document. */
export interface InclusionReason {
  relation: "owns" | "contains" | "uses" | "includes";
  kind?: "module" | "document";
  id: string;
}
export interface Page {
  sourcePath: string;
  route: string;
  stagedPath: string;
  title: string;
  content: string;
  contentDigest: string;
  documentId: string;
  owner: string;
  metadataPath: string;
  metadataDigest: string;
  /** The derived `selected-by` index: every Module whose Spec context holds this document. */
  includedBy: { moduleId: string; reasons: InclusionReason[] }[];
  primaryOf: string | null;
  readingCollection: ReadingCollection;
}
/** A metadata-declared node, with the definition its Terminology row gives a concept. */
export interface PublishedNode {
  id: string;
  type: "concept" | "realization";
  title: string;
  meaning: string;
  owner: string;
  document: string;
  definition?: string;
}
export interface ScopedRegistry {
  schema_version: 23;
  projectRoot: string;
  registryPath: string;
  /** The first Module without a parent: the homepage's entry into the Specs. */
  rootModule: string;
  sourceDigest: string;
  modules: ModuleRecord[];
  nodes: PublishedNode[];
  pages: Page[];
}
export const hash = (value: string | Buffer) =>
  "sha256:" + createHash("sha256").update(value).digest("hex");
function safePath(path: string): void {
  requireThat(
    typeof path === "string" &&
      path.length &&
      !/[:\x00-\x1f\x7f]/.test(path) &&
      !path.includes("\\") &&
      !path.startsWith("/") &&
      path.split("/").every((p) => p && p !== "." && p !== ".."),
    `Unsafe source path: ${path}`,
  );
}
export function safeRead(root: string, path: string): string {
  safePath(path);
  let current = root;
  for (const part of path.split("/")) {
    current = resolve(current, part);
    requireThat(
      !lstatSync(current).isSymbolicLink(),
      `Symlink source: ${path}`,
    );
  }
  requireThat(
    lstatSync(current).isFile(),
    `Source is not a regular file: ${path}`,
  );
  return new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(
    readFileSync(current),
  );
}
/** Publication needs an initialized project: a readable configuration naming the registry. */
export function requireScoped(root: string): void {
  let config: any;
  try {
    config = parseJson(
      safeRead(root, ".concorde/config.json"),
      ".concorde/config.json",
    );
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new Error(
        `No Concorde project configuration at ${root}/.concorde/config.json; initialize the project first.`,
      );
    }
    throw error;
  }
  requireThat(
    config && typeof config.registry === "string",
    ".concorde/config.json must name the project registry",
  );
}
/** The registry record's fields that mirror the entry's `module` block. */
const BLOCK_FIELDS = [
  "title",
  "owns",
  "contains",
  "uses",
  "includes",
  "participates",
] as const;
interface Loaded {
  raw: string;
  content: string;
  unit: DocumentMetadata;
  metadataDigest: string;
}
export function loadScopedRegistry(root: string): ScopedRegistry {
  const configText = safeRead(root, ".concorde/config.json");
  const config = parseJson(configText, ".concorde/config.json");
  requireThat(
    config && typeof config.registry === "string",
    ".concorde/config.json must name the project registry",
  );
  const registryText = safeRead(root, config.registry);
  const registry = parseJson(registryText, config.registry);
  requireThat(
    registry &&
      Object.keys(registry).sort().join(",") === "modules,schema_version" &&
      registry.schema_version === 3 &&
      Array.isArray(registry.modules) &&
      registry.modules.length,
    "Module registry schema 3 with a nonempty modules list required",
  );
  const modules = registry.modules as ModuleRecord[];
  const byId = new Map<string, ModuleRecord>();
  const allIds = new Set<string>();
  const titles = new Set<string>();
  const owner = new Map<string, string>();
  const inputs: [string, string][] = [
    [".concorde/config.json", hash(configText)],
    [config.registry, hash(registryText)],
  ];
  for (const m of modules) {
    requireThat(
      m &&
        typeof m === "object" &&
        Object.keys(m).sort().join(",") ===
          "contains,entry,id,includes,owns,participates,title,uses",
      `Invalid registry record fields: ${String(m?.id)}`,
    );
    requireThat(
      typeof m.id === "string" &&
        identityPattern.test(m.id) &&
        !allIds.has(m.id),
      `Duplicate/invalid Module identity: ${m.id}`,
    );
    moduleBlock(
      Object.fromEntries(BLOCK_FIELDS.map((k) => [k, m[k]])),
      `registry record ${m.id}`,
    );
    requireThat(!titles.has(m.title), `Duplicate Module title: ${m.title}`);
    titles.add(m.title);
    allIds.add(m.id);
    requireThat(
      typeof m.entry === "string" &&
        posix.basename(m.entry) === "module.md" &&
        m.owns.includes(m.entry),
      `Module entry must be an owned module.md: ${m.id}`,
    );
    for (const path of m.owns) {
      safePath(path);
      requireThat(
        path.endsWith(".md") && !/^(?:\.concorde|\.git)\//.test(path),
        `Spec documents must be durable Markdown: ${path}`,
      );
      requireThat(!owner.has(path), `Document must have one owner: ${path}`);
      owner.set(path, m.id);
    }
    byId.set(m.id, m);
  }
  // Composition is the navigation tree: known children, one parent each, no cycle.
  const parent = new Map<string, string>();
  for (const m of modules)
    for (const child of m.contains) {
      requireThat(
        byId.has(child.target) && child.target !== m.id,
        `Unknown or self contained Module: ${m.id} -> ${child.target}`,
      );
      requireThat(
        !parent.has(child.target),
        `Module has more than one parent: ${child.target}`,
      );
      parent.set(child.target, m.id);
    }
  for (const m of modules) {
    const seen = new Set([m.id]);
    for (let cursor = parent.get(m.id); cursor; cursor = parent.get(cursor)) {
      requireThat(!seen.has(cursor), `Module composition cycle: ${m.id}`);
      seen.add(cursor);
    }
  }
  const rootModules = modules.filter((m) => !parent.has(m.id));
  requireThat(rootModules.length, "Module composition has no root");

  const cache = new Map<string, Loaded>();
  const physical = new Set<string>();
  const definer = new Map<string, string>();
  const byDocumentId = new Map<string, string>();
  const nodes: PublishedNode[] = [];
  const define = (id: string, path: string) => {
    requireThat(!allIds.has(id), `Duplicate identity: ${id} (${path})`);
    allIds.add(id);
    definer.set(id, path);
  };
  for (const [path, moduleId] of owner) {
    const module = byId.get(moduleId)!;
    const entry = module.entry === path;
    const raw = safeRead(root, path);
    const content = matter(raw).content;
    requireThat(content.trim(), `Empty Spec: ${path}`);
    const metadataRaw = safeRead(root, path + ".json");
    for (const member of [path, path + ".json"]) {
      const stat = lstatSync(resolve(root, member));
      const key = `${stat.dev}:${stat.ino}`;
      requireThat(!physical.has(key), `Physical source alias: ${member}`);
      physical.add(key);
    }
    const meanings = readingMeanings(content, path);
    const unit = metadata(metadataRaw, path + ".json", moduleId, entry);
    requireReading(content, path, entry, unit.document.role);
    requireThat(
      !allIds.has(unit.document.id),
      `Duplicate identity: ${unit.document.id}`,
    );
    allIds.add(unit.document.id);
    byDocumentId.set(unit.document.id, path);
    for (const node of unit.defines) {
      requireThat(
        node.type === "realization" || unit.document.role === "module",
        `Concepts are defined only in module-role documents: ${path}`,
      );
      requireThat(
        meanings.get(node.meaning.slice(1))?.trim(),
        `Missing readable meaning ${node.meaning}: ${path}`,
      );
      define(node.id, path);
      nodes.push({
        id: node.id,
        type: node.type,
        title: node.title,
        meaning: node.meaning,
        owner: moduleId,
        document: path,
      });
    }
    for (const id of definitionHeadings(content)) define(id, path);
    for (const contract of contracts(content, path)) define(contract.id, path);
    cache.set(path, {
      raw,
      content,
      unit,
      metadataDigest: hash(metadataRaw),
    });
    inputs.push([path, hash(raw)], [path + ".json", hash(metadataRaw)]);
  }
  // A concept's definition is its defining row: the plain term equal to its title.
  for (const [path, loaded] of cache) {
    if (loaded.unit.document.role !== "module") continue;
    const rows = terminologyRows(loaded.content);
    for (const node of nodes.filter(
      (n) => n.document === path && n.type === "concept",
    )) {
      const row = rows.find((r) => !r.link && r.term === node.title);
      if (row?.definition) node.definition = row.definition;
    }
    for (const row of rows) {
      if (!row.link || !row.link.fragment.startsWith("concept.")) continue;
      const concept = nodes.find(
        (n) => n.id === row.link!.fragment && n.type === "concept",
      );
      const location = row.link.href.split("#")[0].split("?")[0];
      const linked = location
        ? posix.normalize(
            posix.join(posix.dirname(path), decodeURIComponent(location)),
          )
        : path;
      requireThat(
        concept && concept.document === linked,
        `Terminology import row does not link to its concept's defining document: ${path} -> ${row.link.href}`,
      );
    }
  }
  // Spec context selection, one level: owns, contains, uses and spec includes.
  const selection = (from: ModuleRecord, r: Selection): string[] => {
    const target = byId.get(r.target);
    requireThat(
      target && target.id !== from.id,
      `Unknown or self Module relation: ${from.id} -> ${r.target}`,
    );
    if (!r.relies_on) return target.owns;
    return [
      target.entry,
      ...r.relies_on.map((id) => {
        const path = definer.get(id);
        requireThat(
          path && owner.get(path) === target.id,
          `relies_on names no node of ${target.id}: ${id}`,
        );
        return path;
      }),
    ];
  };
  const contexts = new Map<string, Map<string, InclusionReason[]>>();
  for (const m of modules) {
    const context = new Map<string, InclusionReason[]>();
    const add = (paths: string[], reason: InclusionReason) => {
      for (const path of paths) {
        const reasons = context.get(path) ?? [];
        if (
          !reasons.some(
            (r) =>
              r.relation === reason.relation &&
              r.kind === reason.kind &&
              r.id === reason.id,
          )
        )
          reasons.push(reason);
        context.set(path, reasons);
      }
    };
    add(m.owns, { relation: "owns", id: m.id });
    for (const r of m.contains)
      add(selection(m, r), { relation: "contains", id: r.target });
    for (const r of m.uses)
      add(selection(m, r), { relation: "uses", id: r.target });
    for (const i of m.includes) {
      if (i.kind === "external") continue;
      const paths =
        i.kind === "module"
          ? byId.get(i.target)?.owns
          : byDocumentId.has(i.target)
            ? [byDocumentId.get(i.target)!]
            : undefined;
      requireThat(paths, `Unknown ${i.kind} inclusion: ${m.id} -> ${i.target}`);
      add(paths, {
        relation: "includes",
        kind: i.kind as "module" | "document",
        id: i.target,
      });
    }
    for (const reasons of context.values())
      reasons.sort((a, b) => {
        const left = [a.relation, a.kind ?? "", a.id];
        const right = [b.relation, b.kind ?? "", b.id];
        for (let i = 0; i < left.length; i++)
          if (left[i] !== right[i]) return left[i] < right[i] ? -1 : 1;
        return 0;
      });
    contexts.set(m.id, context);
  }
  const stripRoot = [...owner.keys()].every((path) =>
    path.startsWith("specs/"),
  );
  const pages: Page[] = [];
  const routes = new Set<string>();
  for (const [path, moduleId] of owner) {
    const { raw, content, unit, metadataDigest } = cache.get(path)!;
    const module = byId.get(moduleId)!;
    const stagedPath = stripRoot ? path.slice("specs/".length) : path;
    const route = "/specs/" + stagedPath.replace(/\.md$/, "");
    requireThat(!routes.has(route), `Duplicate page route: ${route}`);
    routes.add(route);
    pages.push({
      sourcePath: path,
      route,
      stagedPath,
      title: /^#\s+(.+)$/m.exec(prose(content))?.[1] ?? module.title,
      content,
      contentDigest: hash(raw),
      documentId: unit.document.id,
      owner: moduleId,
      metadataPath: path + ".json",
      metadataDigest,
      includedBy: [...contexts]
        .filter(([, context]) => context.has(path))
        .map(([id, context]) => ({
          moduleId: id,
          reasons: context.get(path)!,
        })),
      primaryOf: module.entry === path ? moduleId : null,
      readingCollection: unit.document.role,
    });
  }
  return {
    schema_version: 23,
    projectRoot: root,
    registryPath: config.registry,
    rootModule: rootModules[0].id,
    sourceDigest: hash(JSON.stringify(inputs)),
    modules,
    nodes,
    pages,
  };
}
/** Children of a Module in declared `contains` order. */
export function children(
  registry: ScopedRegistry,
  module: ModuleRecord,
): ModuleRecord[] {
  return module.contains.map((r) =>
    registry.modules.find((m) => m.id === r.target)!,
  );
}
/** Modules no other Module contains, in registry order. */
export function roots(registry: ScopedRegistry): ModuleRecord[] {
  const contained = new Set(
    registry.modules.flatMap((m) => m.contains.map((r) => r.target)),
  );
  return registry.modules.filter((m) => !contained.has(m.id));
}
/** The `[start, end)` ranges of a line's inline code spans: a run of backticks opens a span
 * that the next run of exactly the same length closes; a run without such a partner is text. */
function inlineCodeRanges(line: string): Array<[number, number]> {
  const runs = [...line.matchAll(/`+/g)];
  const ranges: Array<[number, number]> = [];
  for (let open = 0; open < runs.length; open++) {
    const length = runs[open][0].length;
    const close = runs.findIndex(
      (run, index) => index > open && run[0].length === length,
    );
    if (close < 0) continue;
    ranges.push([runs[open].index!, runs[close].index! + length]);
    open = close;
  }
  return ranges;
}
/** Rewrite registered relative links of Markdown written at `sourcePath` to canonical routes.
 * Links inside fenced code and inline code spans are text and stay unchanged.
 * With `anchorFragments`, a bare `#fragment` is addressed to the source page too, for text
 * shown on another page. */
export function rewriteMarkdownLinks(
  registry: ScopedRegistry,
  sourcePath: string,
  content: string,
  anchorFragments = false,
): string {
  let fence: string | undefined;
  return content
    .split("\n")
    .map((line) => {
      const marker = /^\s*(```+|~~~+)/.exec(line)?.[1][0];
      if (marker) {
        fence = fence === marker ? undefined : (fence ?? marker);
        return line;
      }
      if (fence) return line;
      const code = inlineCodeRanges(line);
      return line.replace(
        /(!?\[[^\]]*\])\(([^\s)]+)\)/g,
        (whole, label: string, url: string, offset: number) => {
          if (code.some(([start, end]) => offset >= start && offset < end))
            return whole;
          if (/^(?:[a-z]+:|\/)/i.test(url)) return whole;
          if (url.startsWith("#") && !anchorFragments) return whole;
          const fragmentIndex = url.indexOf("#");
          const beforeFragment =
            fragmentIndex < 0 ? url : url.slice(0, fragmentIndex);
          const queryIndex = beforeFragment.indexOf("?");
          const path =
            queryIndex < 0
              ? beforeFragment
              : beforeFragment.slice(0, queryIndex);
          const suffix = url.slice(path.length);
          const source = path
            ? posix.normalize(posix.join(posix.dirname(sourcePath), path))
            : sourcePath;
          const target = registry.pages.find((p) => p.sourcePath === source);
          requireThat(
            target,
            `Unregistered local link: ${sourcePath} -> ${url}`,
          );
          return `${label}(${target.route}${suffix})`;
        },
      );
    })
    .join("\n");
}
export function rewriteLinks(registry: ScopedRegistry, page: Page): string {
  return rewriteMarkdownLinks(registry, page.sourcePath, page.content);
}
