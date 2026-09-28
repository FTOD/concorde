/** The rendered glossary page: one page listing every concept the project glossary declares,
 * grouped by where its owner sits in the composition tree. The concepts the declaring root Module
 * owns come first as the core terms; every other concept falls under the root's contained Module
 * whose subtree holds its owner, in `contains` order. An A–Z index of every term precedes the
 * groups. Derived from the glossary file at publication time; never written back to sources.
 * Every term link in reading is rewritten to an anchor on this page by `rewriteMarkdownLinks` in
 * `model.ts`; a fragment-only term link inside a definition already addresses the right anchor on
 * this same page, since a concept's heading carries its identity. */
import type { GlossaryConcept, ScopedRegistry } from "./model";

/** Titles in dictionary order: letter case ignored, then exact, so the order is total. */
const byTitle = (a: GlossaryConcept, b: GlossaryConcept) => {
  const [x, y] = [a.title.toLowerCase(), b.title.toLowerCase()];
  if (x !== y) return x < y ? -1 : 1;
  return a.title < b.title ? -1 : a.title > b.title ? 1 : 0;
};

/** The Module whose group lists the concepts `owner` owns: the root itself, the root's contained
 * Module on the path down to `owner`, or, for an owner outside the root's tree, its own topmost
 * ancestor. */
function groupOf(
  registry: ScopedRegistry,
  root: string,
  owner: string,
): string {
  const parent = new Map<string, string>();
  for (const m of registry.modules)
    for (const c of m.contains) parent.set(c.target, m.id);
  let current = owner;
  while (
    current !== root &&
    parent.has(current) &&
    parent.get(current) !== root
  )
    current = parent.get(current)!;
  return current;
}

export function renderGlossaryPage(registry: ScopedRegistry): string {
  const glossary = registry.glossary;
  if (!glossary)
    return "# Glossary\n\nThis project's Specs declare no concepts.\n";
  const moduleOf = (id: string) => registry.modules.find((m) => m.id === id)!;
  const entryRoute = (id: string) =>
    registry.pages.find((p) => p.primaryOf === id)!.route;
  const root = glossary.owner;
  const concepts = [...glossary.concepts].sort(byTitle);

  const order = [root, ...moduleOf(root).contains.map((c) => c.target)];
  const groups = new Map<string, GlossaryConcept[]>();
  for (const concept of concepts) {
    const group = groupOf(registry, root, concept.owner);
    if (!order.includes(group)) order.push(group);
    groups.set(group, [...(groups.get(group) ?? []), concept]);
  }

  const letters = new Map<string, GlossaryConcept[]>();
  for (const concept of concepts) {
    const letter = concept.title[0].toUpperCase();
    letters.set(letter, [...(letters.get(letter) ?? []), concept]);
  }
  const index = [...letters]
    .map(
      ([letter, entries]) =>
        `**${letter}** · ` +
        entries.map((c) => `[${c.title}](#${c.id})`).join(" · "),
    )
    .join("\n\n");

  const entry = (concept: GlossaryConcept) => {
    const owner = moduleOf(concept.owner);
    const hashIndex = concept.explanation.indexOf("#");
    const explanationPath = concept.explanation.slice(0, hashIndex);
    const explanationAnchor = concept.explanation.slice(hashIndex + 1);
    const explained = registry.pages.find(
      (p) => p.sourcePath === explanationPath,
    )!;
    const lines = [
      `### ${concept.title} {#${concept.id}}`,
      "",
      concept.definition,
      "",
      `Owned by [${owner.title}](${entryRoute(owner.id)}). ` +
        `[Explained in ${owner.title}](${explained.route}#${explanationAnchor}).`,
    ];
    if (concept.retired) lines.push("", `*Retired: ${concept.retired.reason}*`);
    if (concept.external_conflict)
      lines.push(
        "",
        `*Conflicts with an external usage: ${concept.external_conflict}*`,
      );
    return lines.join("\n");
  };

  const sections = order
    .filter((group) => groups.has(group))
    .map((group) => {
      const module = moduleOf(group);
      const link = `[${module.title}](${entryRoute(group)})`;
      const heading =
        group === root
          ? `## Core terms {#terms.${group}}\n\nTerms ${link} itself owns, used throughout the project's Specs.`
          : `## ${module.title} {#terms.${group}}\n\nTerms owned by ${link} or a Module it contains.`;
      return [heading, ...groups.get(group)!.map(entry)].join("\n\n");
    });

  return (
    "# Glossary\n\n" +
    "One canonical definition per concept the project's Specs declare, each owned by one Module: " +
    "the core terms first, then the terms of each part of the project. The index lists every " +
    "term by name.\n\n" +
    "## Index {#terms.index}\n\n" +
    index +
    "\n\n" +
    sections.join("\n\n") +
    "\n"
  );
}
