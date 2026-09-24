/** D2 diagrams. A reading's `d2` block holds only the semantics of a picture: which Modules and
 * nodes appear, what nests in what, and which edges point where. Rendering adds the look: each
 * shape and edge gets one class of the house style, chosen from what its label names, and the
 * `d2` program (github.com/d2lang/d2) renders the result to an SVG staged next to the page. A block
 * marked `d2 illustrative` renders the same way under the non-normative label. */
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { writeFile } from "node:fs/promises";
import { dirname, posix, resolve } from "node:path";
import {
  children,
  type ModuleRecord,
  type Page,
  type ScopedRegistry,
} from "./model";
import {
  DiagramSourceError,
  edgeReference,
  parseDiagramSource,
  reference,
  type SourceShape,
} from "./diagram-source";
import { DIAGRAM_STYLE } from "./diagram-style";
import { fenceRanges, isIllustrative } from "./reading-format";
import { ILLUSTRATIVE_LABEL } from "./render";

const MODULE_KINDS = new Set(["owner", "module", "foreign"]);
const INSTALL_HINT =
  "run the Concorde installer, which places d2 at .concorde/tools/d2, or install the d2 program " +
  "from https://github.com/d2lang/d2/releases and put it on PATH, or set CONCORDE_D2 to its path";

/** The d2 program: `CONCORDE_D2`, else the one the Concorde installer placed, else `d2` on PATH. */
export function d2Program(projectRoot: string): string {
  if (process.env.CONCORDE_D2) return process.env.CONCORDE_D2;
  for (const name of ["d2", "d2.exe"]) {
    const installed = resolve(projectRoot, ".concorde/tools", name);
    if (existsSync(installed)) return installed;
  }
  return "d2";
}

function descendants(
  registry: ScopedRegistry,
  module: ModuleRecord,
): Set<string> {
  const ids = new Set<string>();
  const visit = (m: ModuleRecord) =>
    children(registry, m).forEach((child) => {
      ids.add(child.id);
      visit(child);
    });
  visit(module);
  return ids;
}

/** The class of each shape, from what its label names relative to the page's owner. A shape
 * nested in a realization is one of its files: the realization becomes a table and the file one
 * of its rows. */
function classify(
  registry: ScopedRegistry,
  page: Page,
  shapes: SourceShape[],
): Map<string, string> {
  const owner = registry.modules.find((m) => m.id === page.owner)!;
  const inside = descendants(registry, owner);
  const kinds = new Map<string, string>();
  const key = (path: string[]) => JSON.stringify(path);
  for (const shape of [...shapes].sort(
    (a, b) => a.path.length - b.path.length,
  )) {
    const parent = key(shape.path.slice(0, -1));
    if (kinds.get(parent)?.startsWith("realization")) {
      kinds.set(parent, "realization-files");
      continue;
    }
    const module = registry.modules.find((m) => m.title === shape.label);
    const node = registry.nodes.find(
      (n) => n.owner === owner.id && n.title === shape.label,
    );
    if (module)
      kinds.set(
        key(shape.path),
        module.id === owner.id
          ? "owner"
          : inside.has(module.id)
            ? "module"
            : "foreign",
      );
    else if (node) kinds.set(key(shape.path), node.type);
    else if (shape.label.includes(" / "))
      kinds.set(key(shape.path), "foreign-node");
  }
  return kinds;
}

/** Run `d2` on `input` and return the SVG it writes to stdout. */
function runD2(
  input: string,
  where: string,
  projectRoot: string,
): Promise<string> {
  const program = d2Program(projectRoot);
  const args = [
    "--layout=elk",
    "--theme=0",
    "--dark-theme=200",
    "--pad=16",
    "--no-xml-tag",
    "--omit-version",
    "-",
    "-",
  ];
  return new Promise((resolvePromise, reject) => {
    const child = spawn(program, args, { stdio: ["pipe", "pipe", "pipe"] });
    const out: Buffer[] = [];
    const err: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => out.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => err.push(chunk));
    child.on("error", (error: NodeJS.ErrnoException) =>
      reject(
        new Error(
          error.code === "ENOENT"
            ? `Cannot render the D2 diagram at ${where}: the program '${program}' was not found; ${INSTALL_HINT}.`
            : `Cannot render the D2 diagram at ${where}: starting '${program}' failed: ${error.message}`,
        ),
      ),
    );
    child.on("close", (code) => {
      if (code === 0) resolvePromise(Buffer.concat(out).toString("utf8"));
      else
        reject(
          new Error(
            `Cannot render the D2 diagram at ${where}: '${program} ${args.join(" ")}' exited with ` +
              `code ${code}: ${Buffer.concat(err).toString("utf8").trim()}`,
          ),
        );
    });
    child.stdin.end(input);
  });
}

/** The D2 input for a checked diagram: the house style, the block exactly as written, and one
 * class declaration per shape and edge, chosen from what each one names. An edge between two
 * Modules is `uses` only when it carries no label of its own; a labelled edge, like any edge
 * touching a concept, realization or foreign node, is `relates`. Exported so the classification
 * can be asserted without running the `d2` program. */
export function styledDiagramInput(
  registry: ScopedRegistry,
  page: Page,
  source: string,
): string {
  const parsed = parseDiagramSource(source);
  const kinds = classify(registry, page, parsed.shapes);
  const classes = parsed.shapes.flatMap((shape) => {
    const kind = kinds.get(JSON.stringify(shape.path));
    return kind ? [`${reference(shape.path)}.class: ${kind}`] : [];
  });
  for (const edge of parsed.edges) {
    const uses =
      edge.label === undefined &&
      [edge.src, edge.dst].every((path) =>
        MODULE_KINDS.has(kinds.get(JSON.stringify(path)) ?? ""),
      );
    classes.push(`${edgeReference(edge)}.class: ${uses ? "uses" : "relates"}`);
  }
  return `${DIAGRAM_STYLE}\n${source}\n${[...classes, ...grids(parsed, kinds)].join("\n")}\n`;
}

/** Many unconnected children would lay out as one long row, so a container of at least
 * `GRID_FROM` children, none of which an edge touches, arranges them in a near-square grid. A
 * realization's file rows are a table and keep their own layout. */
const GRID_FROM = 5;
function grids(
  parsed: ReturnType<typeof parseDiagramSource>,
  kinds: Map<string, string>,
): string[] {
  const key = (path: string[]) => JSON.stringify(path);
  const touched = new Set(
    parsed.edges.flatMap((edge) =>
      [edge.src, edge.dst].flatMap((path) =>
        path.map((_, n) => key(path.slice(0, n + 1))),
      ),
    ),
  );
  return parsed.shapes.flatMap((shape) => {
    if (kinds.get(key(shape.path)) === "realization-files") return [];
    const inner = parsed.shapes.filter(
      (child) =>
        child.path.length === shape.path.length + 1 &&
        key(child.path.slice(0, -1)) === key(shape.path),
    );
    if (
      inner.length < GRID_FROM ||
      inner.some((child) => touched.has(key(child.path)))
    )
      return [];
    return [
      `${reference(shape.path)}.grid-columns: ${Math.ceil(Math.sqrt(inner.length))}`,
    ];
  });
}

async function renderBlock(
  registry: ScopedRegistry,
  page: Page,
  source: string,
  line: number,
  illustrative: boolean,
): Promise<string> {
  // An illustrative block may use the whole D2 language and asserts nothing, so it renders as
  // written.
  if (illustrative)
    return runD2(source, `${page.sourcePath}:${line}`, registry.projectRoot);
  let input: string;
  try {
    input = styledDiagramInput(registry, page, source);
  } catch (error) {
    if (error instanceof DiagramSourceError)
      throw new Error(
        `The D2 diagram at ${page.sourcePath}:${line + error.line} is outside the semantic ` +
          `subset: ${error.reason}`,
      );
    throw error;
  }
  return runD2(input, `${page.sourcePath}:${line}`, registry.projectRoot);
}

/** Replace every `d2` block of a staged page with an image of its rendering. */
export async function renderDiagrams(
  registry: ScopedRegistry,
  page: Page,
  content: string,
  stagedFile: string,
): Promise<string> {
  const fences = fenceRanges(content).filter((f) => f.language === "d2");
  let out = "";
  let cursor = 0;
  for (const [index, fence] of fences.entries()) {
    const line = content.slice(0, fence.start).split("\n").length;
    const illustrative = isIllustrative(fence.info);
    const svg = await renderBlock(
      registry,
      page,
      fence.body,
      line,
      illustrative,
    );
    const digest = createHash("sha256").update(svg).digest("hex").slice(0, 12);
    const name = `${posix.basename(page.stagedPath, ".md")}.diagram-${index + 1}-${digest}.svg`;
    await writeFile(resolve(dirname(stagedFile), name), svg);
    out += content.slice(cursor, fence.start);
    out += `${illustrative ? `${ILLUSTRATIVE_LABEL}\n\n` : ""}![Diagram ${index + 1} of ${page.title}](./${name})`;
    cursor = fence.end;
  }
  return out + content.slice(cursor);
}
