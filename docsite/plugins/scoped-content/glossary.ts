/** The rendered glossary page: one page listing every concept the project glossary declares,
 * sorted by title. Derived from the glossary file at publication time; never written back to
 * sources. Every term link in reading is rewritten to an anchor on this page by
 * `rewriteMarkdownLinks` in `model.ts`; a fragment-only term link inside a definition already
 * addresses the right anchor on this same page, since a concept's heading carries its identity. */
import type { ScopedRegistry } from "./model";

export function renderGlossaryPage(registry: ScopedRegistry): string {
  const glossary = registry.glossary;
  if (!glossary)
    return "# Glossary\n\nThis project's Specs declare no concepts.\n";
  const concepts = [...glossary.concepts].sort((a, b) =>
    a.title < b.title ? -1 : a.title > b.title ? 1 : 0,
  );
  const sections = concepts.map((concept) => {
    const owner = registry.modules.find((m) => m.id === concept.owner)!;
    const entry = registry.pages.find((p) => p.primaryOf === owner.id)!;
    const hashIndex = concept.explanation.indexOf("#");
    const explanationPath = concept.explanation.slice(0, hashIndex);
    const explanationAnchor = concept.explanation.slice(hashIndex + 1);
    const explained = registry.pages.find(
      (p) => p.sourcePath === explanationPath,
    )!;
    const lines = [
      `## ${concept.title} {#${concept.id}}`,
      "",
      concept.definition,
      "",
      `Owned by [${owner.title}](${entry.route}). ` +
        `[Explained in ${owner.title}](${explained.route}#${explanationAnchor}).`,
    ];
    if (concept.retired) lines.push("", `*Retired: ${concept.retired.reason}*`);
    if (concept.external_conflict)
      lines.push(
        "",
        `*Conflicts with an external usage: ${concept.external_conflict}*`,
      );
    return lines.join("\n");
  });
  return (
    "# Glossary\n\n" +
    "One canonical definition per concept the project's Specs declare, each owned by one Module.\n\n" +
    sections.join("\n\n") +
    "\n"
  );
}
