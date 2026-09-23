/** Protocol 11 reading and metadata parsing for publication.
 *
 * Publication reads what it renders: document pairs, identities, anchors, Terminology tables,
 * definition headings, contract fences and Mermaid blocks. Structural conformance as a whole is
 * `concorde.py validate`; this module rejects only what would make a page wrong or unaddressable. */
export const identityPattern = /^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$/;
export function requireThat(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}
export function uniqueStrings(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.every((v) => typeof v === "string" && v.trim()) &&
    new Set(value).size === value.length
  );
}
export function parseJson(text: string, subject: string): any {
  try {
    const parsed = JSON.parse(text);
    const tokens =
      text.match(
        /"(?:\\.|[^"\\])*"|[{}[\],:]|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/g,
      ) ?? [];
    let position = 0;
    function value(): void {
      const token = tokens[position++];
      if (/^-?\d/.test(token))
        requireThat(
          Number.isFinite(Number(token)),
          `Non-finite JSON number: ${subject}`,
        );
      if (token === "{") {
        const keys = new Set<string>();
        while (tokens[position] !== "}") {
          const key = JSON.parse(tokens[position++]);
          requireThat(!keys.has(key), `Duplicate JSON key ${key}: ${subject}`);
          keys.add(key);
          position++;
          value();
          if (tokens[position] === ",") position++;
        }
        position++;
      } else if (token === "[") {
        while (tokens[position] !== "]") {
          value();
          if (tokens[position] === ",") position++;
        }
        position++;
      }
    }
    value();
    return parsed;
  } catch (error) {
    throw new Error(
      `Invalid JSON in ${subject}: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}
/** Replace fenced lines with blanks so offsets stay valid and fences stay opaque. */
export function prose(source: string): string {
  let fence: string | undefined;
  return source
    .split("\n")
    .map((line) => {
      const match = /^ {0,3}(`{3,}|~{3,})/.exec(line);
      if (match) {
        if (!fence) fence = match[1];
        else if (
          match[1][0] === fence[0] &&
          match[1].length >= fence.length &&
          !line.slice(match[0].length).trim()
        )
          fence = undefined;
        return " ".repeat(line.length);
      }
      return fence ? " ".repeat(line.length) : line;
    })
    .join("\n");
}
export function headingList(content: string) {
  return [
    ...prose(content).matchAll(/^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$/gm),
  ].map((m) => ({
    level: m[1].length,
    text: m[2].trim(),
    start: m.index!,
    body: m.index! + m[0].length,
  }));
}
export interface Fence {
  /** First word of the info string, such as `mermaid`. */
  language: string;
  /** The whole trimmed info string, such as `mermaid illustrative`. */
  info: string;
  start: number;
  end: number;
  body: string;
}
export function fenceRanges(content: string): Fence[] {
  const result: Fence[] = [];
  let open:
    { marker: string; info: string; start: number; body: number } | undefined;
  let offset = 0;
  for (const line of content.split("\n")) {
    const marker = /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);
    if (marker) {
      if (!open)
        open = {
          marker: marker[1],
          info: marker[2].trim(),
          start: offset,
          body: offset + line.length + 1,
        };
      else if (
        marker[1][0] === open.marker[0] &&
        marker[1].length >= open.marker.length &&
        !marker[2].trim()
      ) {
        result.push({
          language: open.info.split(/\s+/)[0] ?? "",
          info: open.info,
          start: open.start,
          end: offset + line.length,
          body: content.slice(open.body, offset).trimEnd(),
        });
        open = undefined;
      }
    }
    offset += line.length + 1;
  }
  requireThat(!open, "Unclosed Markdown fence");
  return result;
}
/** `mermaid illustrative` marks a picture excluded from the declared model. */
export function isIllustrative(info: string): boolean {
  const words = info.split(/\s+/);
  return words[0] === "mermaid" && words.slice(1).includes("illustrative");
}
/** Unmarked Mermaid is a checked flowchart and so must be a `flowchart` or `graph`. */
export function requireMarkedDiagrams(content: string, path: string): void {
  for (const fence of fenceRanges(content)) {
    if (fence.language !== "mermaid" || isIllustrative(fence.info)) continue;
    const body = fence.body
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("%%"));
    requireThat(
      /^(?:flowchart|graph)\b/.test(body[0] ?? ""),
      `Mermaid block is neither a flowchart nor marked illustrative: ${path}`,
    );
  }
}
export const DEFINITION_HEADING =
  /^((?:req|scenario)\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]+[—–-][ \t]+(\S.*)$/;
/** Requirement and scenario identities declared by headings, in reading order. */
export function definitionHeadings(content: string): string[] {
  return headingList(content)
    .map(
      (h) =>
        DEFINITION_HEADING.exec(h.text.replace(/\s+\{#[^{}]+\}$/, ""))?.[1],
    )
    .filter((id): id is string => Boolean(id));
}
/** Every readable anchor and the prose of its region. */
export function readingMeanings(
  content: string,
  path: string,
): Map<string, string> {
  const text = prose(content),
    headings = headingList(content);
  const anchors: { id: string; start: number; body: number; level?: number }[] =
    [];
  for (const heading of headings) {
    const explicit = /\s+\{#([^{}]+)\}$/.exec(heading.text);
    const definition = DEFINITION_HEADING.exec(
      heading.text.replace(/\s+\{#[^{}]+\}$/, ""),
    );
    requireThat(
      !explicit || !definition || explicit[1] === definition[1],
      `Definition anchor differs from ID: ${path}`,
    );
    const id = explicit?.[1] ?? definition?.[1];
    if (id)
      anchors.push({
        id,
        start: heading.start,
        body: heading.body,
        level: heading.level,
      });
  }
  for (const match of text.matchAll(
    /^\s*(?:<a id="[^"]+"><\/a>[ \t]*)+\s*$/gm,
  )) {
    for (const id of match[0].matchAll(/<a id="([^"]+)"><\/a>/g)) {
      anchors.push({
        id: id[1],
        start: match.index!,
        body: match.index! + match[0].length,
      });
    }
  }
  anchors.sort((a, b) => a.start - b.start);
  const result = new Map<string, string>();
  for (let i = 0; i < anchors.length; i++) {
    const anchor = anchors[i];
    requireThat(
      identityPattern.test(anchor.id) && !result.has(anchor.id),
      `Duplicate/invalid reading anchor ${anchor.id}: ${path}`,
    );
    const next =
      anchors.slice(i + 1).find((a) => a.start > anchor.start)?.start ??
      text.length;
    const headingEnd =
      headings.find(
        (h) =>
          h.start > anchor.start &&
          (anchor.level === undefined || h.level <= anchor.level),
      )?.start ?? text.length;
    const body = text
      .slice(anchor.body, Math.min(next, headingEnd))
      .replace(/^#{1,6} .+$/gm, "")
      .trim();
    result.set(anchor.id, body);
  }
  return result;
}
export function sectionBody(content: string, title: string): string {
  const headings = headingList(content);
  const section = headings.find((h) => h.level === 2 && h.text === title);
  if (!section) return "";
  const end =
    headings.find((h) => h.start > section.start && h.level <= 2)?.start ??
    content.length;
  return prose(content).slice(section.body, end).trim();
}
/** Split a Markdown table row on unescaped pipes. */
export function tableCells(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/(?<!\\)\|$/, "")
    .split(/(?<!\\)\|/)
    .map((cell) => cell.trim());
}
export interface TerminologyRow {
  term: string;
  definition: string;
  /** Present for an import row: the linked text and destination. */
  link?: { text: string; href: string; fragment: string };
}
/** The rows of a document's Terminology table, header and separator excluded. */
export function terminologyRows(content: string): TerminologyRow[] {
  const rows = sectionBody(content, "Terminology")
    .split("\n")
    .filter((line) => line.trim().startsWith("|"))
    .map(tableCells);
  if (rows.length < 2 || !rows[1].every((cell) => /^:?-{3,}:?$/.test(cell)))
    return [];
  return rows.slice(2).map(([term = "", definition = ""]) => {
    const link = /^\[([^\]]+)\]\(([^\s)]+)\)$/.exec(term);
    return {
      term,
      definition,
      ...(link
        ? {
            link: {
              text: link[1],
              href: link[2],
              fragment: link[2].includes("#")
                ? link[2].slice(link[2].indexOf("#") + 1)
                : "",
            },
          }
        : {}),
    };
  });
}
const ENTRY_SECTIONS = [
  "Purpose",
  "Terminology",
  "Usage",
  "Design",
  "Relationships",
];
export function requireReading(
  content: string,
  path: string,
  entry: boolean,
  role: "module" | "implementation",
): void {
  const headings = headingList(content),
    fences = fenceRanges(content);
  requireThat(
    !entry || role === "module",
    `module.md must have document.role module: ${path}`,
  );
  if (entry) {
    const top = headings.filter((h) => h.level === 2).map((h) => h.text);
    requireThat(
      top.slice(0, 5).join(",") === ENTRY_SECTIONS.join(",") &&
        ENTRY_SECTIONS.every(
          (name) => top.filter((text) => text === name).length === 1,
        ),
      `Module entry requires level-2 Purpose, Terminology, Usage, Design, Relationships once and in order: ${path}`,
    );
  }
  requireThat(
    role === "implementation" ||
      (definitionHeadings(content).length === 0 &&
        !fences.some((f) => f.language === "concorde-contract")),
    `Requirements, scenarios and contracts belong in an implementation-role document: ${path}`,
  );
  requireThat(
    role === "implementation" ||
      !fences.some(
        (f) => f.language === "mermaid" && /^\s*%%\s*graph:/m.test(f.body),
      ),
    `Graph Spec flowcharts belong in an implementation-role document: ${path}`,
  );
  requireMarkedDiagrams(content, path);
}
export interface Contract {
  id: string;
  version: number;
}
/** Canonical contracts declared by `concorde-contract` fences. */
export function contracts(content: string, path: string): Contract[] {
  return fenceRanges(content)
    .filter((f) => f.language === "concorde-contract")
    .map((f) => {
      const value = parseJson(f.body, path);
      requireThat(
        value &&
          typeof value === "object" &&
          typeof value.id === "string" &&
          identityPattern.test(value.id) &&
          Number.isInteger(value.version) &&
          value.version > 0,
        `Invalid canonical contract: ${path}`,
      );
      return { id: value.id, version: value.version };
    });
}

export interface NodeRecord {
  id: string;
  type: "concept" | "realization";
  title: string;
  meaning: string;
  entries?: string[];
  pending?: string[];
  retired?: { reason: string };
  external_conflict?: string;
}
export interface Selection {
  target: string;
  meaning: string;
  relies_on?: string[];
}
export interface Inclusion {
  kind: "module" | "document" | "external";
  target: string;
  reason: string;
}
export interface Participation {
  contract: string;
  version: number;
  role: "provided" | "required";
  peer: string;
  meaning: string;
}
export interface ModuleBlock {
  title: string;
  owns: string[];
  contains: Selection[];
  uses: Selection[];
  includes: Inclusion[];
  participates: Participation[];
}
export interface DocumentMetadata {
  schema_version: 3;
  document: { id: string; owner: string; role: "module" | "implementation" };
  module?: ModuleBlock;
  defines: NodeRecord[];
  relations: Record<string, unknown>[];
  extensions?: Record<string, unknown>;
}
function fields(
  value: any,
  required: string[],
  optional: string[],
  subject: string,
): void {
  requireThat(
    value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      required.every((k) => Object.hasOwn(value, k)) &&
      Object.keys(value).every((k) => [...required, ...optional].includes(k)),
    `Invalid metadata fields: ${subject}`,
  );
}
function selections(value: unknown, subject: string): void {
  requireThat(
    Array.isArray(value),
    `Invalid Module relation array: ${subject}`,
  );
  for (const r of value as any[]) {
    fields(r, ["target", "meaning"], ["relies_on"], subject);
    requireThat(
      typeof r.target === "string" &&
        identityPattern.test(r.target) &&
        typeof r.meaning === "string" &&
        r.meaning.includes("#") &&
        (r.relies_on === undefined ||
          (uniqueStrings(r.relies_on) && r.relies_on.length > 0)),
      `Invalid Module relation: ${subject}`,
    );
  }
}
/** The `module` block of an entry, also the shape of a registry record's mirrored fields. */
export function moduleBlock(value: any, subject: string): ModuleBlock {
  fields(
    value,
    ["title", "owns", "contains", "uses", "includes", "participates"],
    [],
    subject,
  );
  requireThat(
    typeof value.title === "string" && value.title.trim(),
    `Module title required: ${subject}`,
  );
  requireThat(
    uniqueStrings(value.owns) && value.owns.length,
    `Module owns must be a nonempty unique list: ${subject}`,
  );
  selections(value.contains, subject);
  selections(value.uses, subject);
  requireThat(Array.isArray(value.includes), `Invalid includes: ${subject}`);
  for (const i of value.includes) {
    fields(i, ["kind", "target", "reason"], [], subject);
    requireThat(
      ["module", "document", "external"].includes(i.kind) &&
        typeof i.target === "string" &&
        i.target.trim() &&
        (i.kind === "external" || identityPattern.test(i.target)) &&
        typeof i.reason === "string" &&
        i.reason.trim(),
      `Invalid includes: ${subject}`,
    );
  }
  requireThat(
    Array.isArray(value.participates),
    `Invalid participates: ${subject}`,
  );
  for (const p of value.participates) {
    fields(p, ["contract", "version", "role", "peer", "meaning"], [], subject);
    requireThat(
      typeof p.contract === "string" &&
        Number.isInteger(p.version) &&
        p.version > 0 &&
        ["provided", "required"].includes(p.role) &&
        typeof p.peer === "string" &&
        typeof p.meaning === "string",
      `Invalid participates: ${subject}`,
    );
  }
  return value;
}
/** Schema-3 document metadata; `owner` is the registry's owner of the reading path. */
export function metadata(
  text: string,
  path: string,
  owner: string,
  entry: boolean,
): DocumentMetadata {
  const value = parseJson(text, path);
  fields(
    value,
    ["schema_version", "document", "defines", "relations"],
    ["module", "extensions"],
    path,
  );
  requireThat(
    value.schema_version === 3,
    `Document metadata schema_version 3 required: ${path}`,
  );
  fields(value.document, ["id", "owner", "role"], [], path);
  requireThat(
    typeof value.document.id === "string" &&
      identityPattern.test(value.document.id),
    `Invalid document identity: ${path}`,
  );
  requireThat(
    value.document.owner === owner,
    `Document owner differs from the registry owner ${owner}: ${path}`,
  );
  requireThat(
    value.document.role === "module" ||
      value.document.role === "implementation",
    `Invalid document.role: ${path}`,
  );
  requireThat(
    entry === Object.hasOwn(value, "module"),
    entry
      ? `Module entry metadata requires a module block: ${path}`
      : `Only a Module entry declares a module block: ${path}`,
  );
  if (entry) moduleBlock(value.module, path);
  if (value.extensions !== undefined)
    requireThat(
      value.extensions &&
        typeof value.extensions === "object" &&
        !Array.isArray(value.extensions),
      `Invalid metadata extensions: ${path}`,
    );
  requireThat(
    Array.isArray(value.defines) && Array.isArray(value.relations),
    `defines and relations must be arrays: ${path}`,
  );
  for (const node of value.defines) {
    requireThat(
      node && (node.type === "concept" || node.type === "realization"),
      `A defines record is a concept or realization: ${path}`,
    );
    if (node.type === "concept")
      fields(
        node,
        ["id", "type", "title", "meaning"],
        ["retired", "external_conflict"],
        path,
      );
    else
      fields(
        node,
        ["id", "type", "title", "meaning", "entries"],
        ["pending"],
        path,
      );
    requireThat(
      typeof node.id === "string" &&
        identityPattern.test(node.id) &&
        typeof node.title === "string" &&
        node.title.trim() &&
        typeof node.meaning === "string" &&
        /^#[^#\s]+$/.test(node.meaning),
      `Invalid ${node.type} record ${String(node.id)}: ${path}`,
    );
    if (node.type === "realization")
      requireThat(
        uniqueStrings(node.entries) &&
          node.entries.length &&
          (node.pending === undefined || uniqueStrings(node.pending)),
        `Invalid realization entries: ${path}`,
      );
  }
  for (const relation of value.relations)
    requireThat(
      relation &&
        typeof relation === "object" &&
        ["narrows", "supersedes", "contrasts", "relates"].includes(
          relation.type,
        ),
      `Invalid metadata relation: ${path}`,
    );
  return value;
}
