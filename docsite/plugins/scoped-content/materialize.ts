import { mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, posix, resolve } from "node:path";
import matter from "gray-matter";
import {
  children,
  roots,
  type ModuleRecord,
  type Page,
  type ScopedRegistry,
} from "./model";
import { renderDiagrams } from "./diagrams";
import { renderGlossaryPage } from "./glossary";
import { renderPage } from "./render";
interface SidebarItem {
  type: string;
  label: string;
  id?: string;
  href?: string;
  link?: { type: "doc"; id: string };
  collapsed?: boolean;
  items?: SidebarItem[];
}
/** Navigation follows `contains` from each root; each `module`-role document appears once, under its
 * owner. Implementation documents are published but listed in no sidebar: their Module's entry
 * lists them. */
export function scopedSidebar(registry: ScopedRegistry): SidebarItem[] {
  const byPath = new Map(registry.pages.map((p) => [p.sourcePath, p]));
  const id = (page: Page) => page.stagedPath.replace(/\.md$/, "");
  const document = (page: Page): SidebarItem => ({
    type: "doc",
    id: id(page),
    label: posix.basename(page.sourcePath, ".md"),
  });
  const glossaryItem: SidebarItem | undefined = registry.glossary
    ? {
        type: "doc",
        id: registry.glossary.stagedPath.replace(/\.md$/, ""),
        label: "Glossary",
      }
    : undefined;
  const item = (module: ModuleRecord, depth = 0): SidebarItem[] => {
    const entry = byPath.get(module.entry)!;
    const items = [
      ...module.owns
        .filter((path) => path !== module.entry)
        .map((path) => byPath.get(path)!)
        .filter((page) => page.readingCollection === "module")
        .map(document),
      ...children(registry, module).flatMap((child) => item(child, depth + 1)),
      ...(glossaryItem && registry.glossary!.owner === module.id
        ? [glossaryItem]
        : []),
    ];
    return [
      items.length
        ? {
            type: "category",
            label: module.title,
            link: { type: "doc", id: id(entry) },
            collapsed: depth > 0,
            items,
          }
        : { type: "doc", id: id(entry), label: module.title },
    ];
  };
  return roots(registry).flatMap((module) => item(module));
}
export async function materializeScoped(registry: ScopedRegistry) {
  const generated = resolve(registry.projectRoot, "docsite/.generated");
  const identity = resolve(generated, "scoped-materialization.json");
  await rm(identity, { force: true });
  await rm(resolve(generated, "content"), { recursive: true, force: true });
  await rm(resolve(generated, "static"), { recursive: true, force: true });
  for (const page of registry.pages) {
    const path = resolve(generated, "content/specs", page.stagedPath);
    await mkdir(dirname(path), { recursive: true });
    const title = page.primaryOf
      ? registry.modules.find((module) => module.id === page.primaryOf)!.title
      : posix.basename(page.sourcePath, ".md");
    await writeFile(
      path,
      matter.stringify(
        await renderDiagrams(registry, page, renderPage(registry, page), path),
        {
          format: "md",
          slug: page.route.slice("/specs".length),
          title,
          sidebar_label: title,
          // An implementation page shows the Module tree for orientation without being listed in it.
          displayed_sidebar: "moduleDocumentsSidebar",
          toc_max_heading_level: 3,
        },
      ),
    );
  }
  if (registry.glossary) {
    const path = resolve(
      generated,
      "content/specs",
      registry.glossary.stagedPath,
    );
    await mkdir(dirname(path), { recursive: true });
    await writeFile(
      path,
      matter.stringify(renderGlossaryPage(registry), {
        format: "md",
        slug: registry.glossary.route.slice("/specs".length),
        title: "Glossary",
        sidebar_label: "Glossary",
        displayed_sidebar: "moduleDocumentsSidebar",
        toc_max_heading_level: 2,
      }),
    );
  }
  await writeFile(
    resolve(generated, "specs-sidebar.json"),
    JSON.stringify(
      { moduleDocumentsSidebar: scopedSidebar(registry) },
      null,
      2,
    ) + "\n",
  );
  await writeFile(
    identity,
    JSON.stringify({ schema_version: 2, sourceDigest: registry.sourceDigest }) +
      "\n",
  );
}
