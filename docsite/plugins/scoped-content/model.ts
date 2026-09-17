/** Module publication model. Registered documents are the only sources. */
import { createHash } from "node:crypto";
import { existsSync, lstatSync, readFileSync } from "node:fs";
import { posix, resolve } from "node:path";
import matter from "gray-matter";
import { validateContractExample } from "./contract-schema";
import {
  requireThat,
  uniqueStrings,
  parseJson,
  prose,
  headingList,
  declarations,
  requireReading,
  terminologyBody,
  readingMeanings,
  metadata,
  relationshipLabels,
  type UnitMetadata,
} from "./reading-format";

export type Kind = "module";
export type ReadingCollection = "module" | "implementation";
export interface Target {
  id: string;
  kind: Kind;
  title: string;
  documents: string[];
  references: (
    | { kind: "module" | "document"; id: string }
    | { kind: "external"; path: string }
  )[];
  parent: string | null;
  uses: string[];
  files: string[];
  checks: string[];
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
  includedBy: {
    targetId: string;
    reasons: { kind: "owned" | "module" | "document"; id: string }[];
  }[];
  aliases: string[];
  kind: Kind;
  primaryOf: string | null;
  readingCollection: ReadingCollection;
}
export interface ScopedRegistry {
  schema_version: 21;
  projectRoot: string;
  registryPath: string;
  entryTarget: string;
  sourceDigest: string;
  targets: Target[];
  pages: Page[];
}
export const hash = (value: string | Buffer) =>
  "sha256:" + createHash("sha256").update(value).digest("hex");
const ids = /^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$/;
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
export function legacyAliasRoute(targetId: string, sourcePath: string): string {
  return `/specs/${targetId}/${hash(sourcePath).slice(7, 23)}`;
}
export function primaryDocument(target: Target): string {
  const main = target.documents.filter(
    (path) => posix.basename(path) === "module.md",
  );
  requireThat(
    main.length === 1,
    `Module must register exactly one module.md: ${target.id}`,
  );
  return main[0];
}
const DEFINITION_HEADING =
  /^(#{2,5})([ \t]+)((?:scenario|req)\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]+[—–-][ \t]+(.+?)[ \t]*$/;
/** Publish definition titles without identity prefixes while keeping stable explicit anchors.
 * Preserve entity meaning anchors and expose structured contract anchors for `path#id` links. */
export function injectAnchors(content: string): string {
  let fence: string | undefined;
  const out: string[] = [];
  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const marker = /^ {0,3}(`{3,}|~{3,})/.exec(line);
    if (marker) {
      if (!fence) {
        fence = marker[1];
        if (/^ {0,3}`{3,}concorde-(?:entities|contract)\s*$/.test(line)) {
          const body: string[] = [];
          let j = i + 1;
          while (j < lines.length && !/^ {0,3}`{3,}\s*$/.test(lines[j]))
            body.push(lines[j++]);
          try {
            const parsed = parseJson(body.join("\n"), "definition anchor");
            const entries = (Array.isArray(parsed) ? parsed : [parsed]) as {
              id?: unknown;
            }[];
            const anchors = entries
              .filter((e) => typeof e.id === "string")
              .map((e) => `<a id="${e.id as string}"></a>`);
            if (anchors.length) out.push(anchors.join(""), "");
          } catch {
            /* an unreadable block is reported by the registry loader, not here */
          }
        }
      } else if (
        marker[1][0] === fence[0] &&
        marker[1].length >= fence.length &&
        !line.slice(marker[0].length).trim()
      )
        fence = undefined;
      out.push(line);
      continue;
    }
    if (fence) {
      out.push(line);
      continue;
    }
    const heading = DEFINITION_HEADING.exec(
      line.replace(/[ \t]+#+[ \t]*$/, "").replace(/\s+\{#[^{}]+\}\s*$/, ""),
    );
    out.push(
      heading
        ? `${heading[1]}${heading[2]}${heading[4]} {#${heading[3]}}`
        : line,
    );
  }
  return out.join("\n");
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
/** The adapter publishes Profile 14 projects only; anything else is an explicit error. */
export function requireScoped(root: string): void {
  let profile: unknown;
  try {
    profile = parseJson(
      safeRead(root, ".concorde/config.json"),
      ".concorde/config.json",
    ).profile_version;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new Error(
        `No Concorde project configuration at ${root}/.concorde/config.json; initialize the project first.`,
      );
    }
    throw error;
  }
  if (profile !== 14)
    throw new Error(
      `Profile 14 is required to publish this project; .concorde/config.json declares profile_version ${String(profile)}.`,
    );
}
type DocumentContext = UnitMetadata["document"];
export function loadScopedRegistry(root: string): ScopedRegistry {
  const configText = safeRead(root, ".concorde/config.json");
  const config = parseJson(configText, ".concorde/config.json");
  requireThat(
    config.profile_version === 14,
    "Profile 14 configuration required",
  );
  const registryText = safeRead(root, config.registry);
  const registry = parseJson(registryText, config.registry);
  requireThat(
    Object.keys(registry).sort().join(",") ===
      "checks,entry_target,project_id,schema_version,targets",
    "Invalid registry fields",
  );
  requireThat(
    registry.schema_version === 5 &&
      Array.isArray(registry.targets) &&
      registry.targets.length,
    "Module registry schema 5 required",
  );
  const targets = registry.targets as Target[];
  const byId = new Map<string, Target>();
  const allIds = new Set<string>();
  const documentTargets = new Map<string, string[]>();
  const inputs: [string, string][] = [
    [".concorde/config.json", hash(configText)],
    [config.registry, hash(registryText)],
  ];
  for (const t of targets) {
    requireThat(
      Object.keys(t).sort().join(",") ===
        "checks,documents,files,id,kind,parent,references,title,uses",
      `Invalid Module fields: ${t.id}`,
    );
    requireThat(
      typeof t.id === "string" && ids.test(t.id) && !allIds.has(t.id),
      `Duplicate/invalid target identity: ${t.id}`,
    );
    allIds.add(t.id);
    requireThat(
      t.kind === "module" && typeof t.title === "string" && t.title.trim(),
      `Invalid kind/title: ${t.id}`,
    );
    requireThat(
      uniqueStrings(t.documents) && t.documents.length,
      `Explicit nonempty unique collection required: ${t.id}`,
    );
    for (const key of ["uses", "files", "checks"] as const)
      requireThat(uniqueStrings(t[key]), `Invalid ${key}: ${t.id}`);
    requireThat(
      t.parent === null || typeof t.parent === "string",
      `parent must be explicit: ${t.id}`,
    );
    primaryDocument(t);
    for (const path of t.documents) {
      safePath(path);
      requireThat(
        path.endsWith(".md") && !/^(?:\.concorde|\.git)\//.test(path),
        `Spec documents must be durable Markdown: ${path}`,
      );
      requireThat(
        !documentTargets.has(path),
        `Document must have one owner: ${path}`,
      );
      documentTargets.set(path, [t.id]);
    }
    byId.set(t.id, t);
  }
  requireThat(
    byId.get(registry.entry_target)?.kind === "module",
    "Entry target must be a Module",
  );
  // Finish structural admission before interpreting any Module's dependency prose.
  for (const module of targets) {
    const seen = new Set([module.id]);
    let cursor = module.parent;
    while (cursor !== null) {
      const parent = byId.get(cursor);
      requireThat(
        parent?.kind === "module",
        `Unknown Module parent: ${cursor}`,
      );
      requireThat(!seen.has(cursor), `Module composition cycle: ${module.id}`);
      seen.add(cursor);
      cursor = parent.parent;
    }
  }
  // A listing entry is a safe project path outside project-control directories: either an exact
  // file, or a directory prefix ending in `/` that binds the regular files below it. No entry
  // names a registered Spec document and no directory entry contains one. Unlike a document, one
  // entry may be listed by several Modules (schema 5 has no single implementation owner).
  for (const t of targets)
    for (const entry of t.files) {
      const directory = entry.endsWith("/");
      const path = directory ? entry.slice(0, -1) : entry;
      safePath(path);
      requireThat(
        !/^(?:\.concorde|\.git|\.agents|\.claude|\.codex|generated)\//.test(
          path + "/",
        ),
        `Unsafe file binding: ${entry}`,
      );
      if (directory)
        requireThat(
          ![...documentTargets.keys()]
            .flatMap((p) => [p, p + ".json"])
            .some((document) => document.startsWith(entry)),
          `A listed directory cannot contain a Spec document: ${entry}`,
        );
      else
        requireThat(
          ![...documentTargets.keys()].some(
            (p) => entry === p || entry === p + ".json",
          ),
          `Unsafe file binding: ${entry}`,
        );
      let cursor = root;
      for (const part of path.split("/")) {
        cursor = resolve(cursor, part);
        try {
          requireThat(
            !lstatSync(cursor).isSymbolicLink(),
            `Symlink file binding: ${entry}`,
          );
        } catch (error) {
          if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
        }
      }
      if (existsSync(cursor))
        requireThat(
          directory
            ? lstatSync(cursor).isDirectory()
            : lstatSync(cursor).isFile(),
          directory
            ? `Directory binding must name a directory: ${entry}`
            : `File binding must name a file: ${entry}`,
        );
    }
  const cache = new Map<
    string,
    {
      raw: string;
      content: string;
      declaration: DocumentContext;
      unit: UnitMetadata;
      metadataDigest: string;
      meanings: Map<string, string>;
    }
  >();
  const physical = new Set<string>();
  for (const [path, references] of documentTargets) {
    const raw = safeRead(root, path);
    const content = matter(raw).content;
    const metadataRaw = safeRead(root, path + ".json");
    for (const member of [path, path + ".json"]) {
      const stat = lstatSync(resolve(root, member));
      const key = `${stat.dev}:${stat.ino}`;
      requireThat(!physical.has(key), `Physical source alias: ${member}`);
      physical.add(key);
    }
    const meanings = readingMeanings(content, path);
    const unit = metadata(metadataRaw, path + ".json", references[0], meanings);
    requireReading(
      content,
      path,
      path === primaryDocument(byId.get(references[0])!),
      unit.document.role,
    );
    const declaration = unit.document;
    requireThat(
      !allIds.has(declaration.id),
      `Duplicate document identity: ${declaration.id}`,
    );
    allIds.add(declaration.id);
    requireThat(content.trim(), `Empty Spec: ${path}`);
    cache.set(path, {
      raw,
      content,
      declaration,
      unit,
      meanings,
      metadataDigest: hash(metadataRaw),
    });
    inputs.push([path, hash(raw)], [path + ".json", hash(metadataRaw)]);
  }
  for (const t of targets) {
    requireThat(
      documentTargets.get(primaryDocument(t))!.length === 1,
      `Module reading entry must be local: ${t.id}`,
    );
    const entityTitles = new Set<string>();
    const entries = new Set<string>();
    const providers = new Set<string>();
    const related = new Set([
      ...t.uses,
      ...targets
        .filter((child) => child.parent === t.id)
        .map((child) => child.id),
    ]);
    for (const path of t.documents) {
      for (const entity of cache.get(path)!.unit.entities) {
        requireThat(
          !allIds.has(entity.id) && !entityTitles.has(entity.title),
          `Duplicate entity identity/title: ${entity.id}`,
        );
        allIds.add(entity.id);
        entityTitles.add(entity.title);
        for (const entry of entity.files ?? []) {
          requireThat(
            !entries.has(entry),
            `Duplicate entity file entry: ${entry}`,
          );
          entries.add(entry);
          requireThat(
            t.files.includes(entry),
            `Entity file absent from registration: ${entry}`,
          );
          requireThat(
            entity.pending?.includes(entry) || existsSync(resolve(root, entry)),
            `Missing non-pending entry: ${entry}`,
          );
        }
        if (entity.target_id) {
          requireThat(
            related.has(entity.target_id) && !providers.has(entity.target_id),
            `Invalid or duplicate Module entity: ${entity.target_id}`,
          );
          providers.add(entity.target_id);
        }
      }
      for (const heading of headingList(cache.get(path)!.content)) {
        const id = /^((?:req|scenario)\.[a-z0-9.-]+)\s+[—–-]\s+/.exec(
          heading.text,
        )?.[1];
        if (id) {
          requireThat(!allIds.has(id), `Duplicate definition identity: ${id}`);
          allIds.add(id);
        }
      }
    }
    requireThat(
      entries.size === t.files.length,
      `Entity file union differs from registry: ${t.id}`,
    );
    requireThat(
      providers.size === related.size,
      `Missing child or dependency entity: ${t.id}`,
    );
    const labels = relationshipLabels(
      cache.get(primaryDocument(t))!.content,
      primaryDocument(t),
    );
    requireThat(
      [...labels].every((label) => entityTitles.has(label)),
      `Relationship diagram has unknown entities: ${t.id}`,
    );
    const seen = new Set([t.id]);
    let cursor = t.parent;
    while (cursor !== null) {
      const parent = byId.get(cursor);
      requireThat(
        parent?.kind === "module",
        `Unknown Module parent: ${cursor}`,
      );
      requireThat(!seen.has(cursor), `Module composition cycle: ${t.id}`);
      seen.add(cursor);
      cursor = parent.parent;
    }
    for (const peer of t.uses) {
      requireThat(
        peer !== t.id && byId.get(peer)?.kind === "module",
        `Unknown/self Module dependency: ${peer}`,
      );
    }
    const expected = new Set([
      ...t.uses,
      ...targets
        .filter((child) => child.parent === t.id)
        .map((child) => child.id),
    ]);
    const declared = new Set<string>();
    for (const path of t.documents)
      for (const d of cache.get(path)!.unit.dependencies) {
        requireThat(
          expected.has(d.target_id) && !declared.has(d.target_id),
          `Unrelated or duplicate Module dependency: ${d.target_id}`,
        );
        declared.add(d.target_id);
      }
    requireThat(
      declared.size === expected.size,
      `Missing local Module dependency promises: ${t.id}`,
    );
    const consumers = targets.filter((m) => m.uses.includes(t.id));
    if (consumers.length > 1)
      requireThat(
        consumers.every((m) => m.parent === t.parent),
        `Shared Module and consumers must be siblings: ${t.id}`,
      );
  }
  const byDocumentId = new Map(
    [...cache].map(([path, value]) => [value.declaration.id, path]),
  );
  const contexts = new Map<
    string,
    Map<string, { kind: "owned" | "module" | "document"; id: string }[]>
  >();
  for (const t of targets) {
    const context = new Map<
      string,
      { kind: "owned" | "module" | "document"; id: string }[]
    >(t.documents.map((path) => [path, [{ kind: "owned", id: t.id }]]));
    requireThat(
      Array.isArray(t.references),
      `Explicit references required: ${t.id}`,
    );
    const seen = new Set<string>();
    for (const ref of t.references) {
      if (ref && (ref as { kind?: unknown }).kind === "external") {
        // Existing vendored material is a separate read grant, never a published document unit.
        const external = ref as { kind: "external"; path?: unknown };
        requireThat(
          Object.keys(external).sort().join(",") === "kind,path" &&
            typeof external.path === "string" &&
            external.path.length > 0 &&
            !external.path.startsWith("/") &&
            !external.path.split("/").includes(".."),
          `Invalid external reference: ${t.id}`,
        );
        const entry = external.path,
          directory = entry.endsWith("/"),
          base = directory ? entry.slice(0, -1) : entry;
        safePath(base);
        requireThat(
          !/^(?:\.concorde|\.git|\.agents|\.claude|\.codex|generated)\//.test(
            `${base}/`,
          ),
          `Unsafe external reference: ${entry}`,
        );
        const covers = (binding: string, path: string) =>
          binding.endsWith("/") ? path.startsWith(binding) : binding === path;
        requireThat(
          ![...documentTargets.keys()]
            .flatMap((p) => [p, `${p}.json`])
            .some((p) => covers(entry, p)),
          `External reference includes a Spec member: ${entry}`,
        );
        requireThat(
          !t.files.some(
            (p) =>
              p === entry ||
              covers(p, base) ||
              covers(entry, p.replace(/\/$/, "")),
          ),
          `External reference overlaps implementation: ${entry}`,
        );
        let location = root;
        for (const part of base.split("/")) {
          location = resolve(location, part);
          requireThat(
            !lstatSync(location).isSymbolicLink(),
            `Symlink external reference: ${entry}`,
          );
        }
        requireThat(
          directory
            ? lstatSync(location).isDirectory()
            : lstatSync(location).isFile(),
          `External reference has wrong kind: ${entry}`,
        );
        const externalKey = `external:${external.path}`;
        requireThat(
          !seen.has(externalKey),
          `Duplicate reference: ${externalKey}`,
        );
        seen.add(externalKey);
        continue;
      }
      requireThat(
        ref &&
          Object.keys(ref).sort().join(",") === "id,kind" &&
          ["module", "document"].includes(ref.kind) &&
          typeof (ref as { id?: unknown }).id === "string" &&
          ids.test((ref as { id: string }).id),
        `Invalid reference: ${t.id}`,
      );
      const key = `${ref.kind}:${(ref as { id: string }).id}`;
      requireThat(!seen.has(key), `Duplicate reference: ${key}`);
      seen.add(key);
      const contextRef = ref as { kind: "module" | "document"; id: string };
      const paths =
        contextRef.kind === "module"
          ? byId.get(contextRef.id)?.documents
          : byDocumentId.has(contextRef.id)
            ? [byDocumentId.get(contextRef.id)!]
            : undefined;
      requireThat(
        paths &&
          !(contextRef.kind === "module"
            ? contextRef.id === t.id
            : t.documents.includes(paths[0])),
        `Unknown or self reference: ${key}`,
      );
      for (const path of paths)
        context.set(path, [...(context.get(path) ?? []), { ...contextRef }]);
    }
    for (const reasons of context.values())
      reasons.sort((a, b) =>
        a.kind < b.kind
          ? -1
          : a.kind > b.kind
            ? 1
            : a.id < b.id
              ? -1
              : a.id > b.id
                ? 1
                : 0,
      );
    contexts.set(t.id, context);
  }
  const stripRoot = [...documentTargets.keys()].every((path) =>
    path.startsWith("specs/"),
  );
  const pages: Page[] = [];
  const routes = new Set<string>();
  const aliases = new Set<string>();
  for (const [path, references] of documentTargets) {
    const { raw, content, declaration, metadataDigest, unit } =
      cache.get(path)!;
    const owner = byId.get(declaration.owner)!;
    const primary = primaryDocument(owner) === path;
    const readingCollection = unit.document.role;
    const includedBy = [...contexts]
      .filter(([, context]) => context.has(path))
      .map(([targetId, context]) => ({
        targetId,
        reasons: context.get(path)!,
      }));
    const stagedPath = stripRoot ? path.slice("specs/".length) : path;
    const route = "/specs/" + stagedPath.replace(/\.md$/, "");
    requireThat(!routes.has(route), `Duplicate page route: ${route}`);
    routes.add(route);
    const pageAliases = references.map((id) => legacyAliasRoute(id, path));
    pageAliases.forEach((alias) => aliases.add(alias));
    const page: Page = {
      sourcePath: path,
      route,
      stagedPath,
      title: /^#\s+(.+)$/m.exec(prose(content))?.[1] ?? owner.title,
      content,
      contentDigest: hash(raw),
      documentId: declaration.id,
      owner: declaration.owner,
      metadataPath: path + ".json",
      metadataDigest,
      includedBy,
      aliases: pageAliases,
      kind: owner.kind,
      primaryOf: primary ? owner.id : null,
      readingCollection,
    };
    pages.push(page);
  }
  for (const route of routes)
    requireThat(
      !aliases.has(route),
      `Canonical route collides with an alias: ${route}`,
    );
  const definitions = new Map<string, { version: number; path: string }>();
  const bindings: {
    id: string;
    version: number;
    role: string;
    peer: string;
    owner: string;
    path: string;
  }[] = [];
  for (const t of targets)
    for (const path of t.documents) {
      for (const c of declarations(
        cache.get(path)!.content,
        "concorde-contract",
        path,
      )) {
        requireThat(
          Object.keys(c).sort().join(",") ===
            "example,id,schema,semantics,version" &&
            typeof c.id === "string" &&
            ids.test(c.id) &&
            Number.isInteger(c.version) &&
            c.version > 0 &&
            typeof c.semantics === "string" &&
            c.semantics.trim(),
          `Invalid canonical definition: ${path}`,
        );
        requireThat(
          !definitions.has(c.id) && !allIds.has(c.id),
          `Duplicate canonical definition: ${c.id}`,
        );
        validateContractExample(c.schema, c.example, path);
        definitions.set(c.id, { version: c.version, path });
      }
      for (const c of cache.get(path)!.unit.bindings) {
        requireThat(
          !bindings.some(
            (b) =>
              b.owner === t.id &&
              b.id === c.id &&
              b.role === c.role &&
              b.peer === c.peer,
          ),
          `Duplicate binding: ${c.id}`,
        );
        bindings.push({ ...c, owner: t.id, path });
      }
    }
  for (const t of targets)
    for (const path of t.documents) {
      const source = cache.get(path)!;
      for (const row of terminologyBody(source.content).split("\n")) {
        if (!row.trim().startsWith("|")) continue;
        const cell = row
          .trim()
          .replace(/^\||\|$/g, "")
          .split("|")[0]
          .trim();
        const termLink = /^\[([^\]]+)\]\(([^\s)]+)\)$/.exec(cell);
        if (!termLink) continue;
        const [_, term, href] = termLink;
        const location = href.split("#")[0];
        const linked = location
          ? posix.normalize(
              posix.join(posix.dirname(path), decodeURIComponent(location)),
            )
          : path;
        requireThat(
          !/^(?:[a-z]+:|\/)/i.test(href) &&
            href.endsWith("#terminology") &&
            contexts.get(t.id)!.has(linked),
          `Terminology definition outside admitted context or not a table: ${path} -> ${href}`,
        );
        const names = terminologyBody(cache.get(linked)!.content)
          .split("\n")
          .filter((line) => line.trim().startsWith("|"))
          .map((line) =>
            line
              .trim()
              .replace(/^\||\|$/g, "")
              .split("|")[0]
              .trim()
              .replace(/^[*` ]+|[*` ]+$/g, "")
              .toLowerCase(),
          );
        requireThat(
          names.includes(term.toLowerCase()),
          `Terminology link has no canonical definition of ${term}: ${href}`,
        );
      }
      for (const agreement of [
        ...source.unit.dependencies,
        ...source.unit.bindings,
      ]) {
        const explanation = source.meanings.get(agreement.meaning.slice(1))!;
        for (const match of explanation.matchAll(
          /!?\[[^\]]*\]\(([^\s)]+)\)/g,
        )) {
          const href = match[1];
          if (/^(?:[a-z]+:|\/)/i.test(href)) continue;
          const location = href.split("#")[0].split("?")[0];
          const linked = location
            ? posix.normalize(
                posix.join(posix.dirname(path), decodeURIComponent(location)),
              )
            : path;
          requireThat(
            contexts.get(t.id)!.has(linked),
            `Required definition outside context: ${path} -> ${href}`,
          );
        }
      }
    }
  for (const b of bindings) {
    const definition = definitions.get(b.id);
    requireThat(
      definition?.version === b.version &&
        contexts.get(b.owner)!.has(definition.path),
      `Missing context definition: ${b.id}`,
    );
    if (b.peer.startsWith("external:") && b.peer.length > 9) continue;
    requireThat(
      bindings.some(
        (p) =>
          p.owner === b.peer &&
          p.peer === b.owner &&
          p.id === b.id &&
          p.version === b.version &&
          p.role !== b.role,
      ),
      `Missing complementary binding: ${b.id}`,
    );
  }
  return {
    schema_version: 21,
    projectRoot: root,
    registryPath: config.registry,
    entryTarget: registry.entry_target,
    sourceDigest: hash(JSON.stringify(inputs)),
    targets,
    pages,
  };
}
export function rewriteLinks(registry: ScopedRegistry, page: Page): string {
  let fence: string | undefined;
  return page.content
    .split("\n")
    .map((line) => {
      const marker = /^\s*(```+|~~~+)/.exec(line)?.[1][0];
      if (marker) {
        fence = fence === marker ? undefined : (fence ?? marker);
        return line;
      }
      if (fence) return line;
      return line.replace(
        /(!?\[[^\]]*\])\(([^\s)]+)\)/g,
        (whole, label: string, url: string) => {
          if (/^(?:[a-z]+:|#|\/)/i.test(url)) return whole;
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
            ? posix.normalize(posix.join(posix.dirname(page.sourcePath), path))
            : page.sourcePath;
          const target = registry.pages.find((p) => p.sourcePath === source);
          requireThat(
            target,
            `Unregistered local link: ${page.sourcePath} -> ${url}`,
          );
          return `${label}(${target.route}${suffix})`;
        },
      );
    })
    .join("\n");
}
