/** Derived reading: the staged Markdown of one page. Nothing here is written back to sources.
 *
 * - every stable identity becomes an addressable anchor;
 * - requirement and scenario headings show their titles and keep their identity as the anchor;
 * - import rows of Terminology tables show the imported definition, marked with its owner;
 * - D2 blocks are rendered to images separately, by `diagrams.ts`. */
import {
  DEFINITION_HEADING,
  OPENING_ANCHORS,
  parseJson,
  readingMeanings,
  tableCells,
} from "./reading-format";
import {
  rewriteLinks,
  rewriteMarkdownLinks,
  type Page,
  type ScopedRegistry,
} from "./model";

export const ILLUSTRATIVE_LABEL =
  '<p class="diagram-illustrative"><strong>Illustrative, non-normative.</strong> This diagram explains; it declares no relationship.</p>';
const anchor = (id: string) => `<a id="${id}"></a>`;
const FENCE = /^ {0,3}(`{3,}|~{3,})(.*)$/;
function closes(line: string, fence: string): boolean {
  const marker = FENCE.exec(line);
  return Boolean(
    marker &&
    marker[1][0] === fence[0] &&
    marker[1].length >= fence.length &&
    !marker[2].trim(),
  );
}

/** Heading and contract anchors that need only the reading itself. */
export function injectAnchors(content: string): string {
  let fence: string | undefined;
  const out: string[] = [];
  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (fence) {
      if (closes(line, fence)) fence = undefined;
      out.push(line);
      continue;
    }
    const marker = FENCE.exec(line);
    if (marker) {
      fence = marker[1];
      const info = marker[2].trim();
      if (/^concorde-contract$/.test(info)) {
        const body: string[] = [];
        for (let j = i + 1; j < lines.length && !closes(lines[j], fence); j++)
          body.push(lines[j]);
        try {
          const parsed = parseJson(body.join("\n"), "contract anchor");
          if (typeof parsed?.id === "string") out.push(anchor(parsed.id), "");
        } catch {
          /* an unreadable fence is reported by the registry loader, not here */
        }
      }
      out.push(line);
      continue;
    }
    const heading = /^(#{2,5})([ \t]+)(.*)$/.exec(line);
    const definition = heading
      ? DEFINITION_HEADING.exec(
          heading[3]
            .replace(/[ \t]+#+[ \t]*$/, "")
            .replace(/\s+\{#[^{}]+\}\s*$/, "")
            .trim(),
        )
      : null;
    out.push(
      heading && definition
        ? `${heading[1]}${heading[2]}${definition[2]} {#${definition[1]}}`
        : line,
    );
  }
  return out.join("\n");
}

/** Enrich import rows and anchor defining rows of the Terminology table. */
function renderTerminology(
  registry: ScopedRegistry,
  page: Page,
  content: string,
  anchored: Set<string>,
): string {
  const concepts = registry.nodes.filter((n) => n.type === "concept");
  const local = concepts.filter((n) => n.document === page.sourcePath);
  let fence: string | undefined;
  let inSection = false;
  let row = 0;
  return content
    .split("\n")
    .map((line) => {
      if (fence) {
        if (closes(line, fence)) fence = undefined;
        return line;
      }
      const marker = FENCE.exec(line);
      if (marker) {
        fence = marker[1];
        return line;
      }
      const heading = /^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$/.exec(line);
      if (heading) {
        if (heading[1].length <= 2) inSection = heading[2] === "Terminology";
        row = 0;
        return line;
      }
      if (!inSection || !line.trim().startsWith("|")) return line;
      if (row++ < 2) return line;
      const [term = "", definition = "", ...rest] = tableCells(line);
      const link = /^\[[^\]]+\]\([^\s)]*#(concept\.[^\s)#]+)\)$/.exec(term);
      if (link) {
        const concept = concepts.find((n) => n.id === link[1]);
        if (!concept || definition) return line;
        const owner = registry.modules.find((m) => m.id === concept.owner)!;
        const entry = registry.pages.find((p) => p.primaryOf === owner.id)!;
        const imported = `*Imported from [${owner.title}](${entry.route}).*`;
        // The definition was written on its owner's page; address its links from there.
        const cell = concept.definition
          ? `${rewriteMarkdownLinks(registry, concept.document, concept.definition, true)} ${imported}`
          : imported;
        return `| ${[term, cell, ...rest].join(" | ")} |`;
      }
      const concept = local.find((n) => n.title === term);
      if (!concept || anchored.has(concept.id)) return line;
      anchored.add(concept.id);
      return `| ${[anchor(concept.id) + term, definition, ...rest].join(" | ")} |`;
    })
    .join("\n");
}

/** Place anchors for metadata-declared nodes whose identity the reading does not carry. */
function anchorAtMeanings(
  content: string,
  pending: Map<string, string[]>,
): string {
  if (!pending.size) return content;
  let fence: string | undefined;
  return content
    .split("\n")
    .flatMap((line) => {
      if (fence) {
        if (closes(line, fence)) fence = undefined;
        return [line];
      }
      const marker = FENCE.exec(line);
      if (marker) {
        fence = marker[1];
        return [line];
      }
      const standalone = /^\s*(?:<a id="[^"]+"><\/a>[ \t]*)+\s*$/.test(line);
      const opening = standalone ? null : OPENING_ANCHORS.exec(line);
      const ids =
        standalone || opening
          ? [...(opening?.[0] ?? line).matchAll(/<a id="([^"]+)"><\/a>/g)].map(
              (m) => m[1],
            )
          : [/^#{1,6}[ \t].*\{#([^{}]+)\}[ \t]*$/.exec(line)?.[1]].filter(
              (id): id is string => Boolean(id),
            );
      const extra = ids.flatMap((id) => pending.get(id) ?? []);
      ids.forEach((id) => pending.delete(id));
      if (!extra.length) return [line];
      if (standalone) return [line.trimEnd() + extra.map(anchor).join("")];
      if (opening)
        return [
          opening[0] +
            extra.map(anchor).join("") +
            line.slice(opening[0].length),
        ];
      return [line, "", extra.map(anchor).join("")];
    })
    .join("\n");
}

/** Module and document identities at the top of the page, after its title. */
function anchorPage(content: string, ids: string[]): string {
  if (!ids.length) return content;
  const lines = content.split("\n");
  const first = lines.findIndex((line) => line.trim());
  const at = first >= 0 && /^#[ \t]/.test(lines[first]) ? first + 1 : 0;
  lines.splice(at, 0, ...(at ? [""] : []), ids.map(anchor).join(""), "");
  return lines.join("\n");
}

export function renderPage(registry: ScopedRegistry, page: Page): string {
  let content = rewriteLinks(registry, page);
  const anchored = new Set(
    readingMeanings(page.content, page.sourcePath).keys(),
  );
  if (page.readingCollection === "module")
    content = renderTerminology(registry, page, content, anchored);
  const pending = new Map<string, string[]>();
  for (const node of registry.nodes)
    if (node.document === page.sourcePath && !anchored.has(node.id)) {
      const meaning = node.meaning.slice(1);
      pending.set(meaning, [...(pending.get(meaning) ?? []), node.id]);
      anchored.add(node.id);
    }
  content = anchorAtMeanings(content, pending);
  const top = [page.primaryOf, page.documentId].filter(
    (id): id is string => Boolean(id) && !anchored.has(id!),
  );
  return anchorPage(injectAnchors(content), top);
}
