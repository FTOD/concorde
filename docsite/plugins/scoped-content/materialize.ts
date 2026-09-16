import { mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, posix, resolve } from "node:path";
import matter from "gray-matter";
import {
  injectAnchors,
  primaryDocument,
  rewriteLinks,
  type Page,
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
export function scopedSidebar(registry: ScopedRegistry): SidebarItem[] {
  const byPath = new Map(registry.pages.map((p) => [p.sourcePath, p]));
  const id = (page: Page) => page.stagedPath.replace(/\.md$/, "");
  const document = (page: Page): SidebarItem => ({
    type: "doc",
    id: id(page),
    label: posix.basename(page.sourcePath, ".md"),
  });
  const item = (target: Target, depth = 0): SidebarItem => {
    const main = byPath.get(primaryDocument(target))!;
    const items = [
      ...target.documents
        .filter((path) => path !== main.sourcePath)
        .map((path) => document(byPath.get(path)!)),
      ...registry.targets
        .filter((t) => t.parent === target.id)
        .map((child) => item(child, depth + 1)),
    ];
    // The Module itself opens module.md; there is no extra main-Spec child entry.
    return items.length
      ? {
          type: "category",
          label: target.title,
          link: { type: "doc", id: id(main) },
          collapsed: depth > 0,
          items,
        }
      : { type: "doc", id: id(main), label: target.title };
  };
  return registry.targets
    .filter((t) => !t.parent)
    .map((target) => item(target));
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
        displayed_sidebar: "moduleSpecsSidebar",
        toc_max_heading_level: page.primaryOf ? 2 : 3,
      }),
    );
  }
  await writeFile(
    resolve(generated, "specs-sidebar.json"),
    JSON.stringify(
      { moduleSpecsSidebar: publicationSidebar(registry) },
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
