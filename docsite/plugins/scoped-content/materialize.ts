import { mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, posix, resolve } from "node:path";
import matter from "gray-matter";
import {
  injectAnchors,
  primaryDocument,
  rewriteLinks,
  type Page,
  type ReadingCollection,
  type ScopedRegistry,
  type Target,
} from "./model";
interface SidebarItem {
  type: string;
  label: string;
  id?: string;
  href?: string;
  link?: { type: "doc"; id: string };
  collapsed?: boolean;
  items?: SidebarItem[];
}
export function scopedSidebar(
  registry: ScopedRegistry,
  collection: ReadingCollection = "module",
): SidebarItem[] {
  const byPath = new Map(registry.pages.map((p) => [p.sourcePath, p]));
  const id = (page: Page) => page.stagedPath.replace(/\.md$/, "");
  const document = (page: Page): SidebarItem => ({
    type: "doc",
    id: id(page),
    label: posix.basename(page.sourcePath, ".md"),
  });
  const item = (target: Target, depth = 0): SidebarItem[] => {
    const main = byPath.get(primaryDocument(target))!;
    const items = [
      ...target.documents
        .filter((path) => path !== main.sourcePath)
        .map((path) => byPath.get(path)!)
        .filter((page) => page.readingCollection === collection)
        .map(document),
      ...registry.targets
        .filter((t) => t.parent === target.id)
        .flatMap((child) => item(child, depth + 1)),
    ];
    // Detail navigation retains parentage, but never duplicates the Module entry.
    if (collection === "implementation")
      return items.length
        ? [
            {
              type: "category",
              label: target.title,
              collapsed: depth > 0,
              items,
            },
          ]
        : [];
    return [
      items.length
        ? {
            type: "category",
            label: target.title,
            link: { type: "doc", id: id(main) },
            collapsed: depth > 0,
            items,
          }
        : { type: "doc", id: id(main), label: target.title },
    ];
  };
  return registry.targets
    .filter((t) => !t.parent)
    .flatMap((target) => item(target));
}
/** Registry parentage is the only Module Spec navigation hierarchy. */
export const publicationSidebar = scopedSidebar;
export async function materializeScoped(registry: ScopedRegistry) {
  const generated = resolve(registry.projectRoot, "docsite/.generated");
  const identity = resolve(generated, "scoped-materialization.json");
  await rm(identity, { force: true });
  await rm(resolve(generated, "content"), { recursive: true, force: true });
  await rm(resolve(generated, "static"), { recursive: true, force: true });
  for (const page of registry.pages) {
    const path = resolve(generated, "content/specs", page.stagedPath);
    await mkdir(dirname(path), { recursive: true });
    const content = injectAnchors(rewriteLinks(registry, page));
    const title = page.primaryOf
      ? registry.targets.find((target) => target.id === page.primaryOf)!.title
      : posix.basename(page.sourcePath, ".md");
    await writeFile(
      path,
      matter.stringify(content, {
        format: "md",
        slug: page.route.slice("/specs".length),
        title,
        sidebar_label: title,
        displayed_sidebar:
          page.readingCollection === "implementation"
            ? "implementationSpecsSidebar"
            : "moduleSpecsSidebar",
        toc_max_heading_level: 3,
      }),
    );
  }
  await writeFile(
    resolve(generated, "specs-sidebar.json"),
    JSON.stringify(
      {
        moduleSpecsSidebar: publicationSidebar(registry),
        ...(registry.pages.some(
          (page) => page.readingCollection === "implementation",
        )
          ? {
              implementationSpecsSidebar: publicationSidebar(
                registry,
                "implementation",
              ),
            }
          : {}),
      },
      null,
      2,
    ) + "\n",
  );
  await writeFile(
    identity,
    JSON.stringify({ schema_version: 1, sourceDigest: registry.sourceDigest }) +
      "\n",
  );
}
