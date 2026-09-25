import { writeFile, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { LoadContext, Plugin } from "@docusaurus/types";
import { loadScopedRegistry, type ScopedRegistry } from "./model";
import { canonicalRoute, normalizeRoute } from "./routes";
import { loadSiteIdentity } from "./site-identity";
import { validateInternalLinks } from "./internal-links";
import { parseJson } from "./reading-format";
async function requireMaterialized(registry: ScopedRegistry): Promise<void> {
  const identity = parseJson(
    await readFile(
      resolve(
        registry.projectRoot,
        "docsite/.generated/scoped-materialization.json",
      ),
      "utf8",
    ),
    "scoped-materialization.json",
  );
  if (
    identity.schema_version !== 2 ||
    identity.sourceDigest !== registry.sourceDigest
  )
    throw new Error(
      "Materialized Spec source identity differs; prepare publication again",
    );
}
function manifestPages(registry: ScopedRegistry) {
  return registry.pages.map(
    ({
      sourcePath,
      route,
      contentDigest,
      metadataPath,
      metadataDigest,
      readingCollection,
      owner,
      includedBy,
    }) => ({
      sourcePath,
      route,
      contentDigest,
      metadataPath,
      metadataDigest,
      readingCollection,
      owner,
      includedBy,
    }),
  );
}
export async function validateScopedBuild(root: string, directory: string) {
  const registry = loadScopedRegistry(root);
  const manifest = parseJson(
    await readFile(resolve(directory, "build-manifest.json"), "utf8"),
    "build-manifest.json",
  );
  if (
    manifest.schema_version !== registry.schema_version ||
    manifest.sourceDigest !== registry.sourceDigest ||
    JSON.stringify(manifest.pages) !== JSON.stringify(manifestPages(registry))
  )
    throw new Error(
      `Stale or incomplete Build Manifest ${registry.schema_version}`,
    );
  await validateInternalLinks(
    directory,
    loadSiteIdentity(resolve(root, "docsite")),
    registry.pages.map((page) => page.route),
  );
}
export default function scopedContent(
  context: LoadContext,
  options: unknown,
): Plugin<ScopedRegistry> {
  const root = resolve(
    (options as { projectRoot?: string })?.projectRoot ??
      resolve(context.siteDir, ".."),
  );
  let loaded: ScopedRegistry;
  return {
    name: "concorde-content",
    async loadContent() {
      loaded = loadScopedRegistry(root);
      await requireMaterialized(loaded);
      return loaded;
    },
    async contentLoaded({ content, actions }) {
      actions.setGlobalData({
        schema_version: content.schema_version,
        rootModule: content.rootModule,
        pages: content.pages.map((page) =>
          Object.fromEntries(
            Object.entries(page).filter(([key]) => key !== "content"),
          ),
        ),
        siteIdentity: loadSiteIdentity(context.siteDir),
      });
    },
    async postBuild({ outDir, routesPaths }) {
      const current = loadScopedRegistry(root);
      if (current.sourceDigest !== loaded.sourceDigest)
        throw new Error("Spec source changed during publication");
      await requireMaterialized(loaded);
      const routes = new Set(
        routesPaths.map((p) =>
          normalizeRoute(canonicalRoute(p, context.baseUrl)),
        ),
      );
      if (loaded.pages.some((p) => !routes.has(normalizeRoute(p.route))))
        throw new Error("Registered Spec page was not rendered");
      await writeFile(
        resolve(outDir, "build-manifest.json"),
        JSON.stringify(
          {
            schema_version: loaded.schema_version,
            sourceDigest: loaded.sourceDigest,
            pages: manifestPages(loaded),
          },
          null,
          2,
        ) + "\n",
      );
    },
  };
}
