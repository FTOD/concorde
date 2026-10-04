/** Derived reading: the staged Markdown of one page. Nothing here is written back to sources.
 *
 * - every stable identity becomes an addressable anchor;
 * - requirement and scenario headings show their titles and keep their identity as the anchor;
 * - every term link is rewritten to the rendered glossary page, by `rewriteLinks`;
 * - a Module's entry page gains a derived list of the terms it owns, linking to the glossary;
 * - D2 blocks are rendered to images separately, by `diagrams.ts`. */
import {
  DEFINITION_HEADING,
  OPENING_ANCHORS,
  parseJson,
  readingMeanings,
} from "./reading-format";
import { rewriteLinks, type Page, type ScopedRegistry } from "./model";

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
      // The language is the info string's first word, as for the loader and Spec core.
      if (marker[2].trim().split(/\s+/)[0] === "concorde-contract") {
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

/** A derived list of the terms a Module owns, linking to their glossary entries. Never written
 * into the source; shown only on the Module's own entry page. */
function appendTerms(
  registry: ScopedRegistry,
  page: Page,
  content: string,
): string {
  if (!page.primaryOf || !registry.glossary) return content;
  const owned = registry.glossary.concepts
    .filter((c) => c.owner === page.primaryOf)
    .sort((a, b) => (a.title < b.title ? -1 : a.title > b.title ? 1 : 0));
  if (!owned.length) return content;
  const items = owned.map(
    (c) => `- [${c.title}](${registry.glossary!.route}#${c.id})`,
  );
  return `${content}\n\n## Terms\n\n${items.join("\n")}\n`;
}

/** The identity a heading line carries, read as `readingMeanings` reads it: its explicit
 * `{#id}` once any closing hashes are removed, else its requirement or scenario identity. */
function headingIdentity(line: string): string | undefined {
  const heading = /^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$/.exec(line);
  if (!heading) return undefined;
  const text = heading[2].trim();
  const explicit = /\s+\{#([^{}]+)\}$/.exec(text);
  return (
    explicit?.[1] ??
    DEFINITION_HEADING.exec(text.replace(/\s+\{#[^{}]+\}$/, ""))?.[1]
  );
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
          : [headingIdentity(line)].filter((id): id is string => Boolean(id));
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
  content = appendTerms(
    registry,
    page,
    anchorPage(injectAnchors(content), top),
  );
  return content;
}
