/** The semantic subset of D2 that a reading may write. A block names shapes (`key` or
 * `key: Label`), nests shapes in braces, and draws directed edges (`a -> b` or `a -> b: verb`);
 * keys may be quoted and edge endpoints may be dotted paths. Everything else, such as styles,
 * shapes, classes, layout, variables, imports, globs or other arrows, is how a diagram looks, which
 * belongs to the publisher, so it is refused with the line that holds it. */

export interface SourceShape {
  path: string[];
  label: string;
  line: number;
}
export interface SourceEdge {
  scope: string[];
  src: string[];
  dst: string[];
  label?: string;
  /** The position of this edge among the edges of `scope` with the same ends, as D2 counts. */
  index: number;
  line: number;
}
export interface DiagramSource {
  shapes: SourceShape[];
  edges: SourceEdge[];
}

/** Reserved D2 keywords: each changes the look or the structure beyond shapes and edges. */
const RESERVED = new Set([
  "label",
  "shape",
  "style",
  "class",
  "classes",
  "direction",
  "near",
  "icon",
  "tooltip",
  "link",
  "width",
  "height",
  "top",
  "left",
  "constraint",
  "vars",
  "layers",
  "scenarios",
  "steps",
  "grid-rows",
  "grid-columns",
  "grid-gap",
  "vertical-gap",
  "horizontal-gap",
  "source-arrowhead",
  "target-arrowhead",
  "filled",
  "multiple",
  "3d",
]);

export class DiagramSourceError extends Error {
  constructor(
    readonly line: number,
    readonly reason: string,
  ) {
    super(`line ${line} of the D2 block: ${reason}`);
  }
}

interface Statement {
  text: string;
  line: number;
  opens: boolean;
}

/** Split the source into statements at newlines, `;`, `{` and `}`, outside quotes. */
function statements(source: string): (Statement | { close: number })[] {
  const result: (Statement | { close: number })[] = [];
  let text = "";
  let line = 1;
  let start = 1;
  let quote = false;
  const flush = (opens: boolean) => {
    if (text.trim()) result.push({ text: text.trim(), line: start, opens });
    else if (opens)
      throw new DiagramSourceError(line, "a block opens without a shape");
    text = "";
  };
  for (let i = 0; i < source.length; i++) {
    const c = source[i];
    if (quote) {
      text += c;
      if (c === "\\") text += source[++i] ?? "";
      else if (c === '"') quote = false;
      else if (c === "\n")
        throw new DiagramSourceError(
          line,
          "a quoted key or label is not closed",
        );
      continue;
    }
    if (!text.trim()) start = line;
    if (c === '"') {
      quote = true;
      text += c;
    } else if (c === "#") {
      while (i + 1 < source.length && source[i + 1] !== "\n") i++;
    } else if (c === "\n" || c === ";") {
      flush(false);
      if (c === "\n") line++;
    } else if (c === "{") {
      flush(true);
    } else if (c === "}") {
      flush(false);
      result.push({ close: line });
    } else if (c === "|" || c === "`" || c === "$" || c === "[" || c === "]") {
      throw new DiagramSourceError(
        line,
        `'${c}' (block strings, substitutions or arrays) is not part of the semantic subset`,
      );
    } else text += c;
  }
  if (quote)
    throw new DiagramSourceError(line, "a quoted key or label is not closed");
  flush(false);
  return result;
}

/** Split `text` at every occurrence of `separator` outside quotes. */
function splitOutside(text: string, separator: string): string[] {
  const parts: string[] = [];
  let quote = false;
  let current = "";
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"' && text[i - 1] !== "\\") quote = !quote;
    if (!quote && text.startsWith(separator, i)) {
      parts.push(current);
      current = "";
      i += separator.length - 1;
    } else current += c;
  }
  parts.push(current);
  return parts;
}

function unquote(text: string, line: number): string {
  const trimmed = text.trim();
  if (trimmed.startsWith('"')) {
    if (!trimmed.endsWith('"') || trimmed.length < 2)
      throw new DiagramSourceError(line, `malformed quoted text ${trimmed}`);
    return trimmed.slice(1, -1).replace(/\\(.)/g, "$1");
  }
  return trimmed;
}

function keyPath(text: string, line: number): string[] {
  const segments = splitOutside(text.trim(), ".").map((s) => s.trim());
  for (const segment of segments) {
    if (!segment)
      throw new DiagramSourceError(line, `empty key in ${text.trim()}`);
    const bare = !segment.startsWith('"');
    if (bare && RESERVED.has(segment))
      throw new DiagramSourceError(
        line,
        `'${segment}' sets how the diagram looks; styling and layout belong to the publisher`,
      );
    if (bare && /[*&!()<>@]|^\.\.\./.test(segment))
      throw new DiagramSourceError(
        line,
        `'${segment}' uses globs, filters, references or imports, which are not part of the semantic subset`,
      );
  }
  return segments.map((s) => unquote(s, line));
}

/** Parse one D2 block of the semantic subset. */
export function parseDiagramSource(source: string): DiagramSource {
  const shapes = new Map<string, SourceShape>();
  const edges: SourceEdge[] = [];
  const counts = new Map<string, number>();
  const scope: string[][] = [[]];
  const declare = (path: string[], line: number, label?: string) => {
    for (let n = 1; n <= path.length; n++) {
      const key = JSON.stringify(path.slice(0, n));
      const existing = shapes.get(key);
      const own = n === path.length ? label : undefined;
      if (!existing)
        shapes.set(key, {
          path: path.slice(0, n),
          label: own ?? path[n - 1],
          line,
        });
      else if (own !== undefined) existing.label = own;
    }
  };
  for (const statement of statements(source)) {
    if ("close" in statement) {
      if (scope.length === 1)
        throw new DiagramSourceError(
          statement.close,
          "a block closes that was never opened",
        );
      scope.pop();
      continue;
    }
    const here = scope[scope.length - 1];
    const { text, line } = statement;
    for (const arrow of ["<->", "<-", "--"])
      if (splitOutside(text, arrow).length > 1)
        throw new DiagramSourceError(
          line,
          `'${arrow}' has no declared direction; draw every edge with '->'`,
        );
    const ends = splitOutside(text, "->");
    if (ends.length > 1) {
      if (statement.opens)
        throw new DiagramSourceError(
          line,
          "an edge block styles the edge; styling belongs to the publisher",
        );
      const last = splitOutside(ends[ends.length - 1], ":");
      if (last.length > 2)
        throw new DiagramSourceError(line, `malformed edge ${text}`);
      ends[ends.length - 1] = last[0];
      const label = last.length === 2 ? unquote(last[1], line) : undefined;
      const paths = ends.map((end) => keyPath(end, line));
      for (let i = 0; i + 1 < paths.length; i++) {
        const src = [...here, ...paths[i]];
        const dst = [...here, ...paths[i + 1]];
        declare(src, line);
        declare(dst, line);
        const key = JSON.stringify([here, paths[i], paths[i + 1]]);
        const index = counts.get(key) ?? 0;
        counts.set(key, index + 1);
        edges.push({
          scope: here,
          src,
          dst,
          label: label || undefined,
          index,
          line,
        });
      }
      continue;
    }
    const parts = splitOutside(text, ":");
    if (parts.length > 2)
      throw new DiagramSourceError(line, `malformed shape ${text}`);
    const path = [...here, ...keyPath(parts[0], line)];
    const label = parts.length === 2 ? unquote(parts[1], line) : undefined;
    if (label === "")
      throw new DiagramSourceError(line, `empty label in ${text}`);
    declare(path, line, label);
    if (statement.opens) scope.push(path);
  }
  if (scope.length > 1)
    throw new DiagramSourceError(
      source.split("\n").length,
      `the block of ${scope[scope.length - 1].join(".")} is not closed`,
    );
  return { shapes: [...shapes.values()], edges };
}

/** A D2 reference to a shape path, every key quoted. */
export function reference(path: string[]): string {
  return path.map((key) => JSON.stringify(key)).join(".");
}

/** A D2 reference to an edge, relative to the root. */
export function edgeReference(edge: SourceEdge): string {
  const relative = (path: string[]) => reference(path.slice(edge.scope.length));
  const inner = `(${relative(edge.src)} -> ${relative(edge.dst)})[${edge.index}]`;
  return edge.scope.length ? `${reference(edge.scope)}.${inner}` : inner;
}
