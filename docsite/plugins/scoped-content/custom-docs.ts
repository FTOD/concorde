import { existsSync, realpathSync, statSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";
import type { PluginConfig } from "@docusaurus/types";
import type { NavbarItem } from "@docusaurus/theme-common";
import type { SiteIdentity } from "./site-identity";
import type { ScopedRegistry } from "./model";

/** Shape of the optional project-authored custom-docs/index.ts extension. */
export interface CustomDocsExtension {
  plugins?: PluginConfig[];
  navbarItems?: NavbarItem[];
}

/** Resolves a configured documentation directory relative to `docsite/`, failing when it is absent. */
export function collectionDirectory(
  siteDir: string,
  field: string,
  path: string,
): string {
  let directory: string;
  try {
    directory = realpathSync(resolve(siteDir, path));
  } catch {
    throw new Error(`${field} does not exist: ${path}`);
  }
  if (!statSync(directory).isDirectory())
    throw new Error(`${field} must name a directory: ${path}`);
  return directory;
}

/** Refuses a documentation directory that contains a registered Spec document. */
export function refuseRegisteredSpecs(
  directory: string,
  registry: ScopedRegistry,
  collection: string,
): void {
  for (const page of registry.pages) {
    const path = relative(
      directory,
      realpathSync(resolve(registry.projectRoot, page.sourcePath)),
    );
    if (
      path === "" ||
      (path !== ".." && !path.startsWith("../") && !isAbsolute(path))
    ) {
      throw new Error(
        `${collection} includes registered Spec ${page.sourcePath}; keep it separate from Module Specs.`,
      );
    }
  }
}

export function customDocsConfiguration(
  siteDir: string,
  identity: SiteIdentity,
  registry: ScopedRegistry,
) {
  const collections = identity.customDocs ?? [];
  for (const collection of collections) {
    const directory = collectionDirectory(
      siteDir,
      `customDocs ${collection.id}.path`,
      collection.path,
    );
    if (
      collection.sidebarPath &&
      !statSync(resolve(siteDir, collection.sidebarPath)).isFile()
    ) {
      throw new Error(
        `customDocs ${collection.id}.sidebarPath must name a file.`,
      );
    }
    refuseRegisteredSpecs(directory, registry, `customDocs ${collection.id}`);
  }
  const extensionPath = resolve(siteDir, "custom-docs/index.ts");
  const extension: CustomDocsExtension = existsSync(extensionPath)
    ? require(extensionPath).default
    : {};
  if (!extension || typeof extension !== "object" || Array.isArray(extension))
    throw new Error(
      "custom-docs/index.ts must export a CustomDocsExtension object.",
    );
  for (const field of ["plugins", "navbarItems"] as const) {
    if (extension[field] !== undefined && !Array.isArray(extension[field])) {
      throw new Error(`custom-docs/index.ts ${field} must be an array.`);
    }
  }
  return {
    plugins: [
      ...collections.map(
        (collection) =>
          [
            "@docusaurus/plugin-content-docs",
            {
              id: collection.id,
              path: collection.path,
              routeBasePath: collection.routeBasePath,
              sidebarPath: collection.sidebarPath
                ? resolve(siteDir, collection.sidebarPath)
                : undefined,
              include: ["**/*.md", "**/*.mdx"],
              numberPrefixParser: false,
              showLastUpdateAuthor: false,
              showLastUpdateTime: false,
            },
          ] as PluginConfig,
      ),
      ...(extension.plugins ?? []),
    ],
    navbarItems: [
      ...collections.map((collection) => ({
        to: "/" + collection.routeBasePath,
        label: collection.label,
        position: "left" as const,
      })),
      ...(extension.navbarItems ?? []),
    ],
    docsRouteBasePath: collections.map(
      (collection) => "/" + collection.routeBasePath,
    ),
    docsDir: collections.map((collection) => collection.path),
  };
}
