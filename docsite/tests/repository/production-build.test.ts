import { captureProcess } from "../capture-process";
import { mkdir, writeFile, readFile } from "node:fs/promises";
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

// verifies: scenario.views.illustrative-label
it("labels illustrative diagrams", async () => {
  let illustrative = 0;
  for (const page of registry.pages) {
    const source = await html(page.route);
    const labels = fenceRanges(page.content).filter((f) =>
      isIllustrative(f.info),
    ).length;
    illustrative += labels;
    expect(
      source.split("Illustrative, non-normative.").length - 1,
      page.sourcePath,
    ).toBeGreaterThanOrEqual(labels);
  }
  expect(illustrative).toBeGreaterThan(0);
});

// verifies: scenario.views.publish-reference-link, scenario.views.glossary-page, scenario.views.term-links
it("publishes the glossary page and rewrites term links to it", async () => {
  expect(registry.glossary).not.toBeNull();
  const glossary = registry.glossary!;
  expect(glossary.concepts.length).toBeGreaterThan(0);
  const glossaryHtml = await html(glossary.route);
  expect(glossaryHtml).toContain("theme-doc-sidebar-container");
  for (const concept of glossary.concepts)
    expect(glossaryHtml, concept.id).toContain(`id="${concept.id}"`);
  const base = loadSiteIdentity(site).baseUrl.replace(/\/$/, "");
  const termLinkHref = `href="${base}${glossary.route}#concept.`;
  let termLinks = 0;
  for (const page of registry.pages) {
    const source = await html(page.route);
    termLinks += source.split(termLinkHref).length - 1;
  }
  expect(termLinks).toBeGreaterThan(0);
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
    "writing",
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

// verifies: scenario.views.user-docs
it("publishes the user documents as the home page and the first tab", async () => {
  const identity = loadSiteIdentity(site);
  expect(identity.userDocs).toEqual({
    path: "../docs",
    label: "User documents",
  });
  const base = identity.baseUrl.replace(/\/$/, "");
  const home = await readFile(resolve(output, "index.html"), "utf8");
  expect(home).toContain("Specs that harness your agents.");
  expect(home).toContain(`href="${base}/using-concorde"`);
  expect(home).toContain("theme-doc-sidebar-container");
  expect(home).not.toMatch(/http-equiv="refresh"/i);
  expect(home).not.toContain("provenanceShell");
  const tabs = [
    ...home.matchAll(/class="navbar__item navbar__link[^"]*"[^>]*>([^<]+)</g),
  ].map((match) => match[1]);
  expect(tabs).toEqual([
    "User documents",
    "Module documents",
    "Implementation documents",
    "Spec Protocol",
  ]);
  const guide = await readFile(resolve(output, "using-concorde.html"), "utf8");
  expect(guide).toContain("Using Concorde");
  expect(guide).not.toContain("provenanceShell");
  const manifest = JSON.parse(
    await readFile(resolve(output, "build-manifest.json"), "utf8"),
  );
  expect(
    manifest.pages.some((page: { sourcePath: string }) =>
      page.sourcePath.startsWith("docs/"),
    ),
  ).toBe(false);
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
