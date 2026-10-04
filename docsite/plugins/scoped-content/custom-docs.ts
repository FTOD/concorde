import { existsSync, readdirSync, realpathSync, statSync } from "node:fs";
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

/** Whether `path` is `directory` itself or lies below it. */
function inside(directory: string, path: string): boolean {
  const rel = relative(directory, path);
  return (
    rel === "" || (rel !== ".." && !rel.startsWith("../") && !isAbsolute(rel))
  );
}

/**
 * Refuses a documentation directory that contains a registered Spec document: one lying below it,
 * or one that a symbolic link inside it, to the document or to a directory holding it, reaches.
 */
export function refuseRegisteredSpecs(
  directory: string,
  registry: ScopedRegistry,
  collection: string,
): void {
  const registered = registry.pages.map((page) => ({
    sourcePath: page.sourcePath,
    real: realpathSync(resolve(registry.projectRoot, page.sourcePath)),
  }));
  const refuse = (sourcePath: string): never => {
    throw new Error(
      `${collection} includes registered Spec ${sourcePath}; keep it separate from Module Specs.`,
    );
  };
  for (const page of registered)
    if (inside(directory, page.real)) refuse(page.sourcePath);
  const walk = (current: string): void => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = resolve(current, entry.name);
      if (entry.isDirectory()) {
        walk(path);
        continue;
      }
      if (!entry.isSymbolicLink()) continue;
      let real: string;
      try {
        real = realpathSync(path);
      } catch {
        continue; // A dangling link publishes nothing.
      }
      for (const page of registered)
        if (inside(real, page.real)) refuse(page.sourcePath);
    }
  };
  walk(directory);
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
