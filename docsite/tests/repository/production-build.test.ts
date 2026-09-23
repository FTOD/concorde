import { captureProcess } from "../capture-process";
import { access, mkdir, writeFile, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { beforeAll, it, expect } from "vitest";
import {
  loadScopedRegistry,
  type ScopedRegistry,
} from "../../plugins/scoped-content/model";
import { validateScopedBuild } from "../../plugins/scoped-content";
import {
  contracts,
  definitionHeadings,
  fenceRanges,
  isIllustrative,
  terminologyRows,
} from "../../plugins/scoped-content/reading-format";
import { loadSiteIdentity } from "../../plugins/scoped-content/site-identity";

const site = resolve(__dirname, "../.."),
  root = resolve(site, ".."),
  output = resolve(site, "build");
const obsolete = [
  "graph.html",
  "architecture-graph.json",
  "assets/obsolete-graph.js",
];
let registry: ScopedRegistry;
const html = (route: string) =>
  readFile(resolve(output, route.replace(/^\//, "") + ".html"), "utf8");
function build() {
  const result = captureProcess(
    process.execPath,
    ["--import", "tsx", "scripts/build.ts"],
    { cwd: site, timeout: 240000 },
  );
  expect(result.error).toBeUndefined();
  expect(result.signal).toBeNull();
  expect(result.status, result.stdout + "\n" + result.stderr).toBe(0);
}
beforeAll(async () => {
  await mkdir(resolve(output, "assets"), { recursive: true });
  for (const path of obsolete)
    await writeFile(resolve(output, path), "obsolete output");
  build();
  registry = loadScopedRegistry(root);
}, 240000);

// verifies: scenario.views.publish-candidate
it("publishes the current registry and verifies the promoted manifest", async () => {
  await validateScopedBuild(root, output);
  const base = loadSiteIdentity(site).baseUrl.replace(/\/$/, "");
  for (const page of registry.pages) {
    const source = await html(page.route);
    expect(source, page.sourcePath).toContain(page.sourcePath);
    expect(source).toContain(page.metadataDigest);
    expect(source).toContain("theme-doc-sidebar-container");
    if (!page.primaryOf) continue;
    const sections = [
      "purpose",
      "terminology",
      "usage",
      "design",
      "relationships",
    ];
    for (let i = 1; i < sections.length; i++)
      expect(source.indexOf(`id="${sections[i - 1]}"`)).toBeLessThan(
        source.indexOf(`id="${sections[i]}"`),
      );
  }
  const entry = registry.pages.find(
    (p) => p.primaryOf === registry.rootModule,
  )!;
  expect(await readFile(resolve(output, "index.html"), "utf8")).toContain(
    `href="${base}${entry.route}"`,
  );
  const manifest = JSON.parse(
    await readFile(resolve(output, "build-manifest.json"), "utf8"),
  );
  expect(manifest.schema_version).toBe(registry.schema_version);
  expect(manifest.pages).toHaveLength(registry.pages.length);
  expect(manifest.pages.some((p: { route: string }) => p.route === "/")).toBe(
    false,
  );
});

// verifies: scenario.views.reading-collections
it("publishes both reading collections with links between entry and implementation pages", async () => {
  const entryHtml = await html(
    registry.pages.find((p) => p.primaryOf === registry.rootModule)!.route,
  );
  const navbar = entryHtml.match(/<nav\b[\s\S]*?<\/nav>/)![0];
  expect(navbar).toContain("Module documents");
  expect(navbar).toContain("Implementation documents");
  expect(navbar).toContain("Spec Protocol");
  const base = loadSiteIdentity(site).baseUrl.replace(/\/$/, "");
  for (const module of registry.modules) {
    const details = registry.pages.filter(
      (p) => p.owner === module.id && p.readingCollection === "implementation",
    );
    if (!details.length) continue;
    const entry = registry.pages.find((p) => p.primaryOf === module.id)!;
    const source = await html(entry.route);
    expect(source).toContain('aria-label="Module specification reading paths"');
    for (const page of details) {
      expect(source).toContain(`href="${base}${page.route}"`);
      const detail = await html(page.route);
      expect(detail).toContain(`href="${base}${entry.route}"`);
      expect(detail).toContain(
        "Both reading paths belong to the same complete Module specification.",
      );
    }
  }
});

// verifies: scenario.views.id-anchors
it("exposes every stable identity as an anchor on its page", async () => {
  for (const page of registry.pages) {
    const source = await html(page.route);
    const ids = [
      page.documentId,
      ...(page.primaryOf ? [page.primaryOf] : []),
      ...registry.nodes
        .filter((n) => n.document === page.sourcePath)
        .map((n) => n.id),
      ...definitionHeadings(page.content),
      ...contracts(page.content, page.sourcePath).map((c) => c.id),
    ];
    for (const id of ids)
      expect(source, `${page.sourcePath} ${id}`).toContain(`id="${id}"`);
  }
});

// verifies: scenario.views.import-definition scenario.views.illustrative-label
it("shows imported definitions and labels illustrative diagrams", async () => {
  let imports = 0,
    illustrative = 0;
  for (const page of registry.pages) {
    const source = await html(page.route);
    const rows =
      page.readingCollection === "module"
        ? terminologyRows(page.content).filter(
            (row) =>
              row.link?.fragment.startsWith("concept.") && !row.definition,
          )
        : [];
    imports += rows.length;
    expect(
      source.split("Imported from").length - 1,
      page.sourcePath,
    ).toBeGreaterThanOrEqual(rows.length);
    const labels = fenceRanges(page.content).filter((f) =>
      isIllustrative(f.info),
    ).length;
    illustrative += labels;
    expect(
      source.split("Illustrative, non-normative.").length - 1,
      page.sourcePath,
    ).toBeGreaterThanOrEqual(labels);
  }
  expect(imports).toBeGreaterThan(0);
  expect(illustrative).toBeGreaterThan(0);
});

// verifies: scenario.views.operation-graphs-in-owner-specs
it("publishes Graph Specs only inside their owners' implementation pages", async () => {
  await expect(access(resolve(output, "agent-graphs.html"))).rejects.toThrow();
  const home = await readFile(resolve(output, "index.html"), "utf8");
  expect(home).not.toContain("agent-graphs");
  for (const page of registry.pages)
    if (/^\s*%%\s*graph:/m.test(page.content))
      expect(page.readingCollection, page.sourcePath).toBe("implementation");
});

// verifies: scenario.views.protocol-docs-tab
it("publishes the Protocol as its own collection without Spec provenance", async () => {
  const overview = await readFile(resolve(output, "protocol.html"), "utf8");
  expect(overview).toContain("Spec Protocol");
  expect(overview).not.toContain("provenanceShell");
  for (const chapter of [
    "principles",
    "model",
    "relations",
    "context",
    "boundaries",
    "module",
    "format",
    "checks",
    "views",
    "templates/module",
    "templates/scenario",
  ]) {
    const page = await readFile(
      resolve(output, `protocol/${chapter}.html`),
      "utf8",
    );
    expect(page, chapter).toContain("theme-doc-sidebar-container");
    expect(page, chapter).not.toContain("provenanceShell");
  }
});

// verifies: scenario.views.publish-homepage
it("publishes the configured homepage at the root and links the Specs", async () => {
  const identity = loadSiteIdentity(site);
  const homepage = identity.homepage!;
  const base = identity.baseUrl.replace(/\/$/, "");
  const home = await readFile(resolve(output, "index.html"), "utf8");
  const text = (value: string) =>
    value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  expect(home).toContain(text(homepage.title));
  expect(home).toContain('id="get-started"');
  for (const table of homepage.reference?.tables ?? [])
    expect(home).toContain(text(table.title));
  expect(home).toContain(`href="${base}/protocol"`);
  expect(home).toContain('name="description"');
  expect(home).not.toMatch(/http-equiv="refresh"/i);
  expect(home).not.toContain("provenanceShell");
});

// verifies: scenario.views.inline-diagrams
it("omits graph routes and artifacts", async () => {
  for (const path of [...obsolete, "graph/index.html"])
    await expect(readFile(resolve(output, path))).rejects.toThrow();
});

// verifies: scenario.views.rebuild-removes-stale-pages
it("a second checked build preserves absence and reading", async () => {
  build();
  await validateScopedBuild(root, output);
  for (const path of obsolete)
    await expect(readFile(resolve(output, path))).rejects.toThrow();
  const entry = registry.pages.find(
    (p) => p.primaryOf === registry.rootModule,
  )!;
  expect(await html(entry.route)).toContain("Module documents");
}, 240000);
