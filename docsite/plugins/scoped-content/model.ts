/** Module publication model for Spec Protocol 15. Registered documents are the only sources. */
import { createHash } from "node:crypto";
import { lstatSync, readFileSync } from "node:fs";
import { posix, resolve } from "node:path";
import matter from "gray-matter";
import {
  contracts,
  definitionHeadings,
  fenceRanges,
  identityPattern,
  metadata,
  moduleBlock,
  parseJson,
  prose,
  readingMeanings,
  requireReading,
  requireThat,
  uniqueStrings,
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
/** A metadata-declared realization. */
export interface PublishedNode {
  id: string;
  type: "realization";
  title: string;
  meaning: string;
  owner: string;
  document: string;
}
/** One entry of the project glossary: a concept, owned by a registered Module and explained in a
 * `module` document that owner owns. */
export interface GlossaryConcept {
  id: string;
  title: string;
  owner: string;
  definition: string;
  /** `<reading path>#<anchor>`, naming a `module` document the owner owns. */
  explanation: string;
  retired?: { reason: string };
  external_conflict?: string;
  narrows?: string[];
  supersedes?: string;
  contrasts?: { target: string; reason: string }[];
  relates?: { verb: string; target: string }[];
}
/** The project's one glossary file, declared by the `glossary` field of a Module without a
 * parent's `module` block. */
export interface Glossary {
  /** Project-relative path to the glossary JSON file. */
  path: string;
  /** The Module that declared it. */
  owner: string;
  /** The materialized page's staged Markdown path, relative to the staged `content/specs`. */
  stagedPath: string;
  route: string;
  concepts: GlossaryConcept[];
}
export interface ScopedRegistry {
  schema_version: 23;
  projectRoot: string;
  registryPath: string;
  /** The first Module without a parent: the site root's entry into the Specs without user documents. */
  rootModule: string;
  sourceDigest: string;
  modules: ModuleRecord[];
  nodes: PublishedNode[];
  pages: Page[];
  /** The project glossary, or `null` when no Module declares one. */
  glossary: Glossary | null;
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
/** The project-owned site identity, the last input of the source digest when it exists. */
const SITE_IDENTITY = "docsite/site.json";
function siteIdentityExists(root: string): boolean {
  try {
    lstatSync(resolve(root, SITE_IDENTITY));
    return true;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return false;
    throw error;
  }
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
  "glossary",
] as const;
const REQUIRED_RECORD_FIELDS = [
  "contains",
  "entry",
  "id",
  "includes",
  "owns",
  "participates",
  "title",
  "uses",
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
        REQUIRED_RECORD_FIELDS.every((k) => Object.hasOwn(m, k)) &&
        Object.keys(m).every((k) =>
          [...REQUIRED_RECORD_FIELDS, "glossary"].includes(k),
        ),
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
  const glossaryModules = modules.filter((m) => m.glossary !== undefined);
  requireThat(
    glossaryModules.length <= 1,
    `At most one Module may declare a glossary: ${glossaryModules.map((m) => m.id).join(", ")}`,
  );
  const glossaryModule = glossaryModules[0];
  if (glossaryModule)
    requireThat(
      !parent.has(glossaryModule.id),
      `Only a Module without a parent may declare a glossary: ${glossaryModule.id}`,
    );

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
  const stripRoot = [...owner.keys()].every((path) =>
    path.startsWith("specs/"),
  );
  const routes = new Set<string>();
  // The project glossary: one JSON file of concept entries, declared by the `glossary` field of
  // the Module without a parent. A project without concepts needs no glossary.
  let glossary: Glossary | null = null;
  if (glossaryModule) {
    const glossaryPath = glossaryModule.glossary!;
    const glossaryText = safeRead(root, glossaryPath);
    inputs.push([glossaryPath, hash(glossaryText)]);
    const parsed = parseJson(glossaryText, glossaryPath);
    requireThat(
      parsed &&
        typeof parsed === "object" &&
        Object.keys(parsed).sort().join(",") === "concepts,schema_version" &&
        parsed.schema_version === 1 &&
        Array.isArray(parsed.concepts),
      `Invalid glossary schema: ${glossaryPath}`,
    );
    const concepts: GlossaryConcept[] = [];
    const conceptTitles = new Set<string>();
    let previousId: string | undefined;
    for (const raw of parsed.concepts) {
      requireThat(
        raw &&
          typeof raw === "object" &&
          !Array.isArray(raw) &&
          ["id", "title", "owner", "definition", "explanation"].every((k) =>
            Object.hasOwn(raw, k),
          ) &&
          Object.keys(raw).every((k) =>
            [
              "id",
              "title",
              "owner",
              "definition",
              "explanation",
              "retired",
              "external_conflict",
              "narrows",
              "supersedes",
              "contrasts",
              "relates",
            ].includes(k),
          ),
        `Invalid glossary concept fields: ${String(raw?.id)} (${glossaryPath})`,
      );
      requireThat(
        typeof raw.id === "string" && identityPattern.test(raw.id),
        `Invalid concept identity: ${String(raw.id)} (${glossaryPath})`,
      );
      define(raw.id, glossaryPath);
      requireThat(
        previousId === undefined || previousId < raw.id,
        `Glossary concepts must be sorted by id: ${raw.id} (${glossaryPath})`,
      );
      previousId = raw.id;
      requireThat(
        typeof raw.title === "string" && raw.title.trim(),
        `Concept title required: ${raw.id} (${glossaryPath})`,
      );
      requireThat(
        !conceptTitles.has(raw.title),
        `Duplicate concept title: ${raw.title} (${glossaryPath})`,
      );
      conceptTitles.add(raw.title);
      requireThat(
        typeof raw.owner === "string" && byId.has(raw.owner),
        `Concept owner is not a registered Module: ${raw.id} -> ${String(raw.owner)} (${glossaryPath})`,
      );
      requireThat(
        typeof raw.definition === "string" && raw.definition.trim(),
        `Concept definition required: ${raw.id} (${glossaryPath})`,
      );
      const hashIndex =
        typeof raw.explanation === "string" ? raw.explanation.indexOf("#") : -1;
      requireThat(
        hashIndex > 0,
        `Invalid concept explanation: ${raw.id} -> ${String(raw.explanation)} (${glossaryPath})`,
      );
      const explanationPath = raw.explanation.slice(0, hashIndex);
      const explanationAnchor = raw.explanation.slice(hashIndex + 1);
      requireThat(
        owner.get(explanationPath) === raw.owner,
        `Concept explanation is not a module document owned by ${raw.owner}: ${raw.id} -> ${raw.explanation} (${glossaryPath})`,
      );
      const explained = cache.get(explanationPath)!;
      requireThat(
        explained.unit.document.role === "module",
        `Concept explanation must address a module document: ${raw.id} -> ${raw.explanation} (${glossaryPath})`,
      );
      requireThat(
        readingMeanings(explained.content, explanationPath)
          .get(explanationAnchor)
          ?.trim(),
        `Missing readable meaning ${raw.explanation}: ${raw.id} (${glossaryPath})`,
      );
      if (raw.retired !== undefined)
        requireThat(
          raw.retired &&
            typeof raw.retired === "object" &&
            Object.keys(raw.retired).join(",") === "reason" &&
            typeof raw.retired.reason === "string" &&
            raw.retired.reason.trim(),
          `Invalid retired reason: ${raw.id} (${glossaryPath})`,
        );
      if (raw.external_conflict !== undefined)
        requireThat(
          typeof raw.external_conflict === "string" &&
            raw.external_conflict.trim(),
          `Invalid external_conflict: ${raw.id} (${glossaryPath})`,
        );
      if (raw.narrows !== undefined)
        requireThat(
          uniqueStrings(raw.narrows) && raw.narrows.length,
          `Invalid narrows: ${raw.id} (${glossaryPath})`,
        );
      if (raw.supersedes !== undefined)
        requireThat(
          typeof raw.supersedes === "string" && raw.supersedes.trim(),
          `Invalid supersedes: ${raw.id} (${glossaryPath})`,
        );
      if (raw.contrasts !== undefined) {
        requireThat(
          Array.isArray(raw.contrasts) && raw.contrasts.length,
          `Invalid contrasts: ${raw.id} (${glossaryPath})`,
        );
        for (const c of raw.contrasts)
          requireThat(
            c &&
              typeof c === "object" &&
              Object.keys(c).sort().join(",") === "reason,target" &&
              typeof c.target === "string" &&
              c.target.trim() &&
              typeof c.reason === "string" &&
              c.reason.trim(),
            `Invalid contrasts entry: ${raw.id} (${glossaryPath})`,
          );
      }
      if (raw.relates !== undefined) {
        requireThat(
          Array.isArray(raw.relates) && raw.relates.length,
          `Invalid relates: ${raw.id} (${glossaryPath})`,
        );
        for (const r of raw.relates)
          requireThat(
            r &&
              typeof r === "object" &&
              Object.keys(r).sort().join(",") === "target,verb" &&
              typeof r.verb === "string" &&
              r.verb.trim() &&
              typeof r.target === "string" &&
              r.target.trim(),
            `Invalid relates entry: ${raw.id} (${glossaryPath})`,
          );
      }
      concepts.push({
        id: raw.id,
        title: raw.title,
        owner: raw.owner,
        definition: raw.definition,
        explanation: raw.explanation,
        ...(raw.retired !== undefined ? { retired: raw.retired } : {}),
        ...(raw.external_conflict !== undefined
          ? { external_conflict: raw.external_conflict }
          : {}),
        ...(raw.narrows !== undefined ? { narrows: raw.narrows } : {}),
        ...(raw.supersedes !== undefined ? { supersedes: raw.supersedes } : {}),
        ...(raw.contrasts !== undefined ? { contrasts: raw.contrasts } : {}),
        ...(raw.relates !== undefined ? { relates: raw.relates } : {}),
      });
    }
    // A fragment-only term link inside a definition must name a declared concept.
    for (const concept of concepts)
      for (const match of concept.definition.matchAll(/\]\(#([^\s)]+)\)/g))
        requireThat(
          concepts.some((c) => c.id === match[1]),
          `Unknown glossary term in the definition of ${concept.id}: #${match[1]} (${glossaryPath})`,
        );
    const glossaryStagedPath = (
      stripRoot ? glossaryPath.slice("specs/".length) : glossaryPath
    ).replace(/\.json$/, ".md");
    const glossaryRoute = "/specs/" + glossaryStagedPath.replace(/\.md$/, "");
    requireThat(
      !routes.has(glossaryRoute),
      `Duplicate page route: ${glossaryRoute}`,
    );
    routes.add(glossaryRoute);
    glossary = {
      path: glossaryPath,
      owner: glossaryModule.id,
      stagedPath: glossaryStagedPath,
      route: glossaryRoute,
      concepts,
    };
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
        // A concept relies_on names the document holding its extended explanation, since the
        // concept itself is a glossary entry, not a node any Module's owned documents define.
        const concept = glossary?.concepts.find((c) => c.id === id);
        if (concept) {
          requireThat(
            concept.owner === target.id,
            `relies_on names no node of ${target.id}: ${id}`,
          );
          return concept.explanation.slice(0, concept.explanation.indexOf("#"));
        }
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
  const pages: Page[] = [];
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
  // The site identity shapes every page, so a candidate built from an older one is stale too.
  if (siteIdentityExists(root)) {
    inputs.push([SITE_IDENTITY, hash(safeRead(root, SITE_IDENTITY))]);
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
    glossary,
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
/** The `[start, end)` ranges of `content` that a link rewrite must leave untouched: fenced code
 * blocks (multi-line, from the authoritative `fenceRanges`) and inline code spans (computed per
 * line, then placed at their absolute offset in `content`). Kept separate from line splitting so
 * a link label that is soft-wrapped across lines is still one match. */
function opaqueRanges(content: string): Array<[number, number]> {
  const ranges: Array<[number, number]> = fenceRanges(content).map(
    (f): [number, number] => [f.start, f.end],
  );
  let offset = 0;
  for (const line of content.split("\n")) {
    for (const [start, end] of inlineCodeRanges(line))
      ranges.push([offset + start, offset + end]);
    offset += line.length + 1;
  }
  return ranges;
}
/** Rewrite registered relative links of Markdown written at `sourcePath` to canonical routes.
 * Links inside fenced code and inline code spans are text and stay unchanged; a link label may
 * itself be soft-wrapped across lines, since the match is against the whole document, not a line.
 * With `anchorFragments`, a bare `#fragment` is addressed to the source page too, for text
 * shown on another page. */
export function rewriteMarkdownLinks(
  registry: ScopedRegistry,
  sourcePath: string,
  content: string,
  anchorFragments = false,
): string {
  const opaque = opaqueRanges(content);
  return content.replace(
    /(!?\[[^\]]*\])\(([^\s)]+)\)/g,
    (whole, label: string, url: string, offset: number) => {
      if (opaque.some(([start, end]) => offset >= start && offset < end))
        return whole;
      if (/^(?:[a-z]+:|\/)/i.test(url)) return whole;
      if (url.startsWith("#") && !anchorFragments) return whole;
      const fragmentIndex = url.indexOf("#");
      const beforeFragment =
        fragmentIndex < 0 ? url : url.slice(0, fragmentIndex);
      const queryIndex = beforeFragment.indexOf("?");
      const path =
        queryIndex < 0 ? beforeFragment : beforeFragment.slice(0, queryIndex);
      const suffix = url.slice(path.length);
      const source = path
        ? posix.normalize(posix.join(posix.dirname(sourcePath), path))
        : sourcePath;
      // A term link's path addresses the glossary file; its fragment, when present, is a
      // concept identity the glossary must declare. A bare link to the glossary file, with no
      // fragment, addresses the glossary page itself.
      if (registry.glossary && source === registry.glossary.path) {
        if (fragmentIndex >= 0) {
          const fragment = url.slice(fragmentIndex + 1);
          requireThat(
            registry.glossary.concepts.some((c) => c.id === fragment),
            `Unknown glossary term: ${sourcePath} -> ${url}`,
          );
        }
        return `${label}(${registry.glossary.route}${suffix})`;
      }
      const target = registry.pages.find((p) => p.sourcePath === source);
      requireThat(target, `Unregistered local link: ${sourcePath} -> ${url}`);
      return `${label}(${target.route}${suffix})`;
    },
  );
}
export function rewriteLinks(registry: ScopedRegistry, page: Page): string {
  return rewriteMarkdownLinks(registry, page.sourcePath, page.content);
}
