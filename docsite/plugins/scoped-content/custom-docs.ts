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
 * or one that a symbolic link inside it reaches, to the document or to a directory holding it,
 * however many links lie on the way. Every directory a link reaches is walked once.
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
  const reaches = (real: string) => {
    for (const page of registered)
      if (inside(real, page.real)) refuse(page.sourcePath);
  };
  const visited = new Set<string>();
  const walk = (current: string): void => {
    const real = realpathSync(current);
    if (visited.has(real)) return;
    visited.add(real);
    reaches(real);
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = resolve(current, entry.name);
      if (entry.isDirectory()) {
        walk(path);
        continue;
      }
      if (!entry.isSymbolicLink()) continue;
      let target: string;
      try {
        target = realpathSync(path);
      } catch {
        continue; // A dangling link publishes nothing.
      }
      reaches(target);
      if (statSync(target).isDirectory()) walk(target);
    }
  };
  walk(directory);
}

/** The names under which Docusaurus resolves its docs plugin. */
const DOCS_PLUGINS = new Set([
  "@docusaurus/plugin-content-docs",
  "docusaurus-plugin-content-docs",
  "content-docs",
]);

/** The docs instances an extension adds, each with its id and its directory, which defaults to
 * Docusaurus's `docs`, and its sidebar file when it names one. */
function extensionDocs(
  plugins: PluginConfig[],
): { id: string; path: string; sidebarPath?: string }[] {
  const docs = [];
  for (const plugin of plugins) {
    const [name, options] = Array.isArray(plugin) ? plugin : [plugin, {}];
    if (typeof name !== "string" || !DOCS_PLUGINS.has(name)) continue;
    const option = (key: string) =>
      options && typeof options === "object" && key in options
        ? (options as Record<string, unknown>)[key]
        : undefined;
    const sidebarPath = option("sidebarPath");
    docs.push({
      id: option("id") === undefined ? "default" : String(option("id")),
      path: option("path") === undefined ? "docs" : String(option("path")),
      ...(typeof sidebarPath === "string" ? { sidebarPath } : {}),
    });
  }
  return docs;
}

/**
 * Applies the collections' admission to every docs instance an extension adds: its directory must
 * exist and contain no registered Spec document.
 */
function refuseExtensionDocs(
  siteDir: string,
  plugins: PluginConfig[],
  registry: ScopedRegistry,
): void {
  for (const { id, path } of extensionDocs(plugins)) {
    refuseRegisteredSpecs(
      collectionDirectory(
        siteDir,
        `custom-docs/index.ts docs plugin ${id}.path`,
        path,
      ),
      registry,
      `custom-docs/index.ts docs plugin ${id}`,
    );
  }
}

/** Loads the optional `custom-docs/index.ts` extension, refusing one of the wrong shape. */
function loadExtension(siteDir: string): CustomDocsExtension {
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
  return extension;
}

/**
 * The authored inputs publication reads besides the registered sources, each relative to `docsite/`
 * with the field that names it: the user documents, every custom docs collection and every docs
 * instance of the extension, with their sidebar files.
 */
export function authoredInputs(
  siteDir: string,
  identity: SiteIdentity,
): { path: string; field: string }[] {
  return [
    ...(identity.userDocs
      ? [{ path: identity.userDocs.path, field: "userDocs.path" }]
      : []),
    ...(identity.customDocs ?? []).flatMap((collection) => [
      { path: collection.path, field: `customDocs ${collection.id}.path` },
      ...(collection.sidebarPath
        ? [
            {
              path: collection.sidebarPath,
              field: `customDocs ${collection.id}.sidebarPath`,
            },
          ]
        : []),
    ]),
    ...extensionDocs(loadExtension(siteDir).plugins ?? []).flatMap(
      ({ id, path, sidebarPath }) => [
        { path, field: `custom-docs/index.ts docs plugin ${id}.path` },
        ...(sidebarPath
          ? [
              {
                path: sidebarPath,
                field: `custom-docs/index.ts docs plugin ${id}.sidebarPath`,
              },
            ]
          : []),
      ],
    ),
  ];
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
  const extension = loadExtension(siteDir);
  refuseExtensionDocs(siteDir, extension.plugins ?? [], registry);
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
