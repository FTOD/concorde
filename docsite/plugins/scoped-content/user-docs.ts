import { readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";
import type { PluginConfig } from "@docusaurus/types";
import { collectionDirectory, refuseRegisteredSpecs } from "./custom-docs";
import type { SiteIdentity } from "./site-identity";
import type { ScopedRegistry } from "./model";

/** The docs instance that publishes user documents at the site root. */
export const USER_DOCS_PLUGIN_ID = "user";
/** The files Docusaurus publishes at a directory's own route; one of them is the home page. */
const ROOT_PAGES = ["README.md", "README.mdx", "index.md", "index.mdx"];

/**
 * Admits the project's user documents and configures them as the first tab, published at `/` with
 * a sidebar generated from their directory structure. Returns undefined when none are configured.
 */
export function userDocsConfiguration(
  siteDir: string,
  identity: SiteIdentity,
  registry: ScopedRegistry,
) {
  const userDocs = identity.userDocs;
  if (!userDocs) return undefined;
  const directory = collectionDirectory(
    siteDir,
    "userDocs.path",
    userDocs.path,
  );
  refuseRegisteredSpecs(directory, registry, "userDocs");
  const entries = readdirSync(directory);
  if (!ROOT_PAGES.some((name) => entries.includes(name))) {
    throw new Error(
      `userDocs.path ${userDocs.path} has no root page; add README.md or index.md, which becomes the site's home page.`,
    );
  }
  // User documents share the site root with the Spec tabs, search and every custom collection.
  const reserved = new Map<string, string>([
    ["specs", "the Spec tabs"],
    ["search", "search"],
  ]);
  for (const collection of identity.customDocs ?? []) {
    reserved.set(
      collection.routeBasePath.split("/")[0],
      `customDocs ${collection.id}`,
    );
  }
  for (const entry of entries) {
    const isDirectory = statSync(resolve(directory, entry)).isDirectory();
    if (!isDirectory && !/\.mdx?$/.test(entry)) continue;
    const route = entry.replace(/\.mdx?$/, "");
    const owner = reserved.get(route);
    if (owner)
      throw new Error(
        `userDocs ${userDocs.path}/${entry} would publish under /${route}, which ${owner} uses; rename it.`,
      );
  }
  return {
    plugin: [
      "@docusaurus/plugin-content-docs",
      {
        id: USER_DOCS_PLUGIN_ID,
        path: userDocs.path,
        routeBasePath: "/",
        include: ["**/*.md", "**/*.mdx"],
        numberPrefixParser: false,
        showLastUpdateAuthor: false,
        showLastUpdateTime: false,
      },
    ] as PluginConfig,
    navbarItem: {
      type: "docSidebar" as const,
      docsPluginId: USER_DOCS_PLUGIN_ID,
      sidebarId: "defaultSidebar",
      label: userDocs.label,
      position: "left" as const,
    },
    docsRouteBasePath: "/",
    docsDir: userDocs.path,
  };
}
