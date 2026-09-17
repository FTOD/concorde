/** Protocol 8 reading, document roles and metadata admission. Publication layout is deliberately absent. */
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
export function fenceRanges(
  content: string,
): { language: string; start: number; end: number; body: string }[] {
  const result: {
    language: string;
    start: number;
    end: number;
    body: string;
  }[] = [];
  let open:
    | { marker: string; language: string; start: number; body: number }
    | undefined;
  let offset = 0;
  for (const line of content.split("\n")) {
    const marker = /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);
    if (marker) {
      if (!open)
        open = {
          marker: marker[1],
          language: marker[2].trim(),
          start: offset,
          body: offset + line.length + 1,
        };
      else if (
        marker[1][0] === open.marker[0] &&
        marker[1].length >= open.marker.length &&
        !marker[2].trim()
      ) {
        result.push({
          language: open.language,
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
export function declarations(
  content: string,
  language: string,
  path: string,
): any[] {
  return fenceRanges(content)
    .filter((f) => f.language === language)
    .map((f) => parseJson(f.body, path));
}
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
    const definition =
      /^((?:req|scenario)\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)\s+[—–-]\s+\S/.exec(
        heading.text,
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
export function requireReading(
  content: string,
  path: string,
  primary: boolean,
  role: "module" | "implementation" = "module",
): Map<string, string> {
  const headings = headingList(content),
    fences = fenceRanges(content);
  const retired = ["Usage & Contract", "Architecture & Realization"];
  requireThat(
    !headings.some((h) => retired.includes(h.text)),
    `Retired reader parts require explicit migration: ${path}`,
  );
  requireThat(
    !fences.some((f) =>
      [
        "concorde-document",
        "concorde-entities",
        "concorde-dependencies",
        "concorde-contract-binding",
        "concorde-capabilities",
        "concorde-agents",
      ].includes(f.language),
    ),
    `Machine declarations belong in document metadata: ${path}`,
  );
  if (primary) {
    const names = ["Purpose", "Usage", "Design", "Relationships"];
    requireThat(
      headings
        .filter((h) => h.level === 2)
        .slice(0, 4)
        .map((h) => h.text)
        .join(",") === names.join(",") &&
        names.every(
          (name) => headings.filter((h) => h.text === name).length === 1,
        ),
      `Reading entry requires unique level-2 Purpose, Usage, Design, Relationships in order: ${path}`,
    );
    requireThat(
      !headings.some((h) => h.text === "Entities"),
      `Entities is not a reading inventory chapter: ${path}`,
    );
    for (const name of names) {
      const section = headings.find((h) => h.text === name)!;
      const end =
        headings.find((h) => h.start > section.start && h.level <= 2)?.start ??
        content.length;
      const body = prose(content)
        .slice(section.body, end)
        .replace(/^\s*(?:<a id="[^"]+"><\/a>\s*)+$/gm, "");
      requireThat(
        body
          .split("\n")
          .some(
            (line) => line.trim() && !/^\s*(?:#|\||[-*+] |\d+[.)] )/.test(line),
          ),
        `${name} requires explanatory prose: ${path}`,
      );
      if (name === "Purpose")
        requireThat(
          !/^\s*(?:#|\||[-*+] |\d+[.)] )/m.test(body) &&
            !fences.some((f) => f.start > section.start && f.end <= end),
          `Purpose requires plain prose: ${path}`,
        );
    }
  }
  requireThat(
    !primary || role === "module",
    `module.md must have document.role module: ${path}`,
  );
  requireThat(
    role === "implementation" ||
      (!headings.some((h) => /^(?:req|scenario)\./.test(h.text)) &&
        !fences.some((f) => f.language === "concorde-contract")),
    `Formal definitions belong in an implementation-role document, not a Module entry or topic: ${path}`,
  );
  requireDefinitions(content, path);
  return readingMeanings(content, path);
}
function requireDefinitions(content: string, path: string): void {
  const text = prose(content),
    headings = headingList(content);
  requireThat(
    !/^\s*(?:[-*+]|\d+[.)])\s+req\./m.test(text),
    `Requirements must be heading sections: ${path}`,
  );
  for (let index = 0; index < headings.length; index++) {
    const heading = headings[index];
    if (!/^(?:req|scenario)\./.test(heading.text)) continue;
    requireThat(
      heading.level >= 2 &&
        heading.level <= 5 &&
        /^(?:req|scenario)\.[a-z0-9]+(?:[.-][a-z0-9-]+)*\s+[—–-]\s+\S/.test(
          heading.text,
        ),
      `Malformed definition heading: ${path}`,
    );
    const next = headings[index + 1];
    requireThat(
      !next || next.level <= heading.level,
      `Definition sections cannot have nested headings: ${path}`,
    );
    const body = text.slice(heading.body, next?.start ?? text.length).trim();
    if (heading.text.startsWith("req.")) {
      const statement = body.split(/\n\s*\n/)[0];
      requireThat(
        statement &&
          !/^\s*(?:[-*+]|\d+[.)]|\|)/.test(statement) &&
          (statement.match(/\bSHALL(?: NOT)?\b/g) ?? []).length === 1,
        `Requirement needs one SHALL statement: ${path}`,
      );
    } else {
      let order = -1;
      const seen = new Set<string>();
      for (const line of body.split("\n")) {
        const item = /^\s*(?:[-*+]|\d+[.)])\s+(.*)/.exec(line);
        if (!item) continue;
        const step = /^(GIVEN|WHEN|THEN|AND|BUT)\s+\S/.exec(item[1]);
        requireThat(step, `Scenario lists contain steps only: ${path}`);
        const keyword = step[1];
        if (keyword === "AND" || keyword === "BUT") {
          requireThat(
            order >= 0,
            `Scenario starts with a continuation: ${path}`,
          );
          continue;
        }
        const position = ["GIVEN", "WHEN", "THEN"].indexOf(keyword);
        requireThat(
          position >= order && (order >= 0 || position < 2),
          `Scenario step order is invalid: ${path}`,
        );
        order = position;
        seen.add(keyword);
      }
      requireThat(
        seen.has("WHEN") && seen.has("THEN"),
        `Scenario needs WHEN and THEN steps: ${path}`,
      );
    }
  }
}
export interface Entity {
  id: string;
  title: string;
  kind: string;
  meaning: string;
  files?: string[];
  pending?: string[];
  target_id?: string;
}
export interface Dependency {
  target_id: string;
  meaning: string;
}
export interface Binding {
  id: string;
  version: number;
  role: "provided" | "required";
  peer: string;
  meaning: string;
}
export interface UnitMetadata {
  schema_version: 2;
  document: { id: string; owner: string; role: "module" | "implementation" };
  entities: Entity[];
  dependencies: Dependency[];
  bindings: Binding[];
  extensions?: Record<string, unknown>;
}
export function metadata(
  text: string,
  path: string,
  owner: string,
  meanings: Map<string, string>,
): UnitMetadata {
  const value = parseJson(text, path);
  const fields = (v: any, required: string[], optional: string[] = []) =>
    requireThat(
      v &&
        typeof v === "object" &&
        !Array.isArray(v) &&
        required.every((k) => Object.hasOwn(v, k)) &&
        Object.keys(v).every((k) => [...required, ...optional].includes(k)),
      `Invalid metadata fields: ${path}`,
    );
  fields(
    value,
    ["schema_version", "document", "entities", "dependencies", "bindings"],
    ["extensions"],
  );
  fields(value.document, ["id", "owner", "role"]);
  requireThat(
    value.schema_version === 2 &&
      typeof value.document.id === "string" &&
      identityPattern.test(value.document.id) &&
      value.document.owner === owner,
    `Invalid metadata version/identity/owner; migrate explicitly to Protocol 8 schema 2: ${path}`,
  );
  requireThat(
    value.document.role === "module" ||
      value.document.role === "implementation",
    `Invalid document.role: ${path}`,
  );
  requireThat(
    !value.extensions ||
      !Object.hasOwn(value.extensions, "concorde.publication"),
    `Retired concorde.publication extension; migrate to document.role: ${path}`,
  );
  if (value.extensions !== undefined)
    requireThat(
      value.extensions &&
        !Array.isArray(value.extensions) &&
        typeof value.extensions === "object" &&
        Object.keys(value.extensions).length &&
        Object.keys(value.extensions).every((k) => identityPattern.test(k)),
      `Invalid metadata extensions: ${path}`,
    );
  const meaning = (ref: unknown) =>
    requireThat(
      typeof ref === "string" &&
        ref.startsWith("#") &&
        meanings.get(ref.slice(1))?.trim(),
      `Missing readable meaning ${String(ref)}: ${path}`,
    );
  for (const name of ["entities", "dependencies", "bindings"])
    requireThat(Array.isArray(value[name]), `Invalid ${name} array: ${path}`);
  for (const e of value.entities) {
    fields(
      e,
      ["id", "title", "kind", "meaning"],
      ["files", "pending", "target_id"],
    );
    requireThat(
      typeof e.id === "string" &&
        identityPattern.test(e.id) &&
        !/^(req|scenario)\./.test(e.id) &&
        typeof e.title === "string" &&
        e.title.trim() &&
        typeof e.kind === "string" &&
        e.kind.trim() &&
        e.meaning === `#${e.id}`,
      `Invalid entity: ${path}`,
    );
    meaning(e.meaning);
    if (e.files !== undefined)
      requireThat(
        uniqueStrings(e.files) && e.files.length,
        `Invalid entity files: ${path}`,
      );
    if (e.pending !== undefined)
      requireThat(
        uniqueStrings(e.pending) &&
          e.pending.every((p: string) => e.files?.includes(p)),
        `Invalid pending subset: ${path}`,
      );
    if (e.target_id !== undefined)
      requireThat(
        typeof e.target_id === "string" &&
          identityPattern.test(e.target_id) &&
          e.target_id !== owner &&
          e.files === undefined &&
          e.pending === undefined,
        `Invalid Module entity: ${path}`,
      );
  }
  for (const d of value.dependencies) {
    fields(d, ["target_id", "meaning"]);
    requireThat(
      typeof d.target_id === "string" && identityPattern.test(d.target_id),
      `Invalid provider: ${path}`,
    );
    meaning(d.meaning);
  }
  for (const b of value.bindings) {
    fields(b, ["id", "version", "role", "peer", "meaning"]);
    requireThat(
      typeof b.id === "string" &&
        identityPattern.test(b.id) &&
        Number.isInteger(b.version) &&
        b.version > 0 &&
        ["provided", "required"].includes(b.role) &&
        typeof b.peer === "string" &&
        b.peer !== owner &&
        (b.peer.startsWith("external:")
          ? b.peer.slice(9).trim()
          : identityPattern.test(b.peer)),
      `Invalid participant binding: ${path}`,
    );
    meaning(b.meaning);
  }
  return value;
}
/** The same bounded flowchart forms as the Protocol validator; behavioral Flow fences are separate. */
export function relationshipLabels(content: string, path: string): Set<string> {
  const headings = headingList(content),
    section = headings.find(
      (h) => h.level === 2 && h.text === "Relationships",
    )!;
  const end =
    headings.find((h) => h.start > section.start && h.level <= 2)?.start ??
    content.length;
  const fences = fenceRanges(content).filter(
    (f) => f.language === "mermaid" && f.start > section.start && f.end <= end,
  );
  requireThat(
    fences.length,
    `Relationships requires a Mermaid flowchart: ${path}`,
  );
  const labels = new Set<string>();
  const openers = [
    "(((",
    "[[",
    "[(",
    "((",
    "{{",
    "[/",
    "[\\",
    "[",
    "(",
    "{",
    ">",
  ];
  const closers = [")))", "]]", ")]", "))", "}}", "/]", "\\]", "]", ")", "}"];
  for (const fence of fences) {
    requireThat(
      /^\s*(flowchart|graph)\b/.test(fence.body),
      `Relationships requires a flowchart: ${path}`,
    );
    const nodes = new Map<string, string>();
    for (let line of fence.body.split("\n")) {
      line = line.trim();
      if (
        !line ||
        /^(?:%%|(?:flowchart|graph|subgraph|end|classDef|class|style|linkStyle|direction|click|accTitle|accDescr)(?=[\s:]|$))/.test(
          line,
        )
      )
        continue;
      let position = 0,
        haveNode = false,
        awaitingNode = false;
      while (position < line.length) {
        if (/[ \t]/.test(line[position])) {
          position++;
          continue;
        }
        if (line[position] === "&") {
          requireThat(haveNode, `Invalid node group: ${path}`);
          position++;
          awaitingNode = true;
          continue;
        }
        const tail = line.slice(position);
        const inline =
          /^(?:--[ \t]+([^-]+?)[ \t]+-->|-\.[ \t]+([^.]+?)[ \t]+\.->|==[ \t]+([^=]+?)[ \t]+==>)/.exec(
            tail,
          );
        const edge =
          /^(?:x--x|o--o|<-->|-->|---|-\.->|-\.-|==>|===|--x|--o|<--|<==)(?:[ \t]*\|([^|]*)\|)?/.exec(
            tail,
          );
        if (inline || edge) {
          const match = (inline ?? edge)!;
          requireThat(
            haveNode &&
              !awaitingNode &&
              (inline
                ? inline.slice(1).some((v) => v?.trim())
                : edge![1]?.trim()),
            `Unlabeled or invalid relationship edge: ${path}`,
          );
          position += match[0].length;
          awaitingNode = true;
          continue;
        }
        const node = /^[A-Za-z0-9_]+/.exec(tail);
        requireThat(node, `Invalid relationship node: ${path}`);
        const id = node[0];
        requireThat(
          ![
            "flowchart",
            "graph",
            "subgraph",
            "end",
            "classDef",
            "class",
            "style",
            "linkStyle",
            "direction",
            "click",
            "accTitle",
            "accDescr",
          ].includes(id),
          `Reserved Mermaid node identifier ${id}: ${path}`,
        );
        position += id.length;
        const opener = openers.find((o) => line.startsWith(o, position));
        if (opener) {
          position += opener.length;
          let label: string;
          if (line[position] === '"') {
            const close = line.indexOf('"', position + 1);
            requireThat(close >= 0, `Unclosed node label: ${path}`);
            label = line.slice(position + 1, close);
            position = close + 1;
          } else {
            const ends = closers
              .map((c) => line.indexOf(c, position))
              .filter((i) => i >= 0);
            requireThat(ends.length, `Unclosed node: ${path}`);
            const close = Math.min(...ends);
            label = line.slice(position, close);
            position = close;
          }
          const closer = closers.find((c) => line.startsWith(c, position));
          requireThat(closer, `Unclosed node shape: ${path}`);
          position += closer.length;
          nodes.set(id, label.split(/<br\s*\/?>/)[0].trim());
        } else if (!nodes.has(id)) nodes.set(id, id);
        const style = /^:::\w+/.exec(line.slice(position));
        if (style) position += style[0].length;
        haveNode = true;
        awaitingNode = false;
      }
      requireThat(!awaitingNode, `Missing relationship endpoint: ${path}`);
    }
    requireThat(nodes.size, `Empty relationship diagram: ${path}`);
    for (const label of nodes.values()) labels.add(label);
  }
  return labels;
}
