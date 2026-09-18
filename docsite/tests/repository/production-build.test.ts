import { captureProcess } from "../capture-process";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { beforeAll, it, expect } from "vitest";
import { loadScopedRegistry } from "../../plugins/scoped-content/model";
import { validateScopedBuild } from "../../plugins/scoped-content";
const site = resolve(__dirname, "../.."),
  root = resolve(site, ".."),
  output = resolve(site, "build");
beforeAll(async () => {
  await mkdir(resolve(output, "assets"), { recursive: true });
  for (const path of [
    "graph.html",
    "architecture-graph.json",
    "assets/obsolete-graph.js",
  ])
    await writeFile(resolve(output, path), "obsolete graph output");
  const result = captureProcess(
    process.execPath,
    ["--import", "tsx", "scripts/build.ts"],
    { cwd: site, timeout: 120000 },
  );
  expect(result.error).toBeUndefined();
  expect(result.signal).toBeNull();
  expect(result.status, result.stdout + "\n" + result.stderr).toBe(0);
}, 120000);
// verifies: scenario.views.publish-candidate
it("publishes the current exact registry and verifies the promoted manifest", async () => {
  await validateScopedBuild(root, output);
  const r = loadScopedRegistry(root);
  for (const page of r.pages) {
    const html = await readFile(
      resolve(output, page.route.slice(1) + ".html"),
      "utf8",
    );
    expect(html).toContain(page.sourcePath);
  }
  const home = await readFile(resolve(output, "index.html"), "utf8");
  expect(home).toContain(
    r.pages.find((p) => p.primaryOf === r.entryTarget)!.route,
  );
  const entry = r.pages.find((p) => p.primaryOf === r.entryTarget)!;
  const html = await readFile(
    resolve(output, entry.route.slice(1) + ".html"),
    "utf8",
  );
  expect(html).toContain("theme-doc-sidebar-container");
  expect(html).not.toContain(">Specs by source path<");
  expect(html).not.toContain(">Specs by target<");
  const navbar = html.match(/<nav\b[\s\S]*?<\/nav>/)![0];
  expect(navbar).toContain("Spec Protocol");
  expect(html).not.toContain(">Module composition<");
  expect(html).not.toContain(">Projections<");
  expect(navbar).toContain("Module Specs");
  expect(navbar).toContain("Implementation Specs");
  expect(navbar).toContain("Agent Graphs");
  expect(navbar).not.toContain(">Graph<");
  expect(html).toContain('id="purpose"');
  expect(html).not.toContain('id="scenarios"');
  expect(html).not.toContain('id="req.concorde.routing-no-access"');
  expect(html).not.toContain("<iframe");
  for (const module of r.targets) {
    const page = r.pages.find((p) => p.primaryOf === module.id)!;
    const source = await readFile(
      resolve(output, page.route.slice(1) + ".html"),
      "utf8",
    );
    const sections = [
      "purpose",
      "terminology",
      "usage",
      "design",
      "relationships",
    ];
    for (const name of sections) expect(source).toContain(`id="${name}"`);
    for (let i = 1; i < sections.length; i++)
      expect(source.indexOf(`id="${sections[i - 1]}"`)).toBeLessThan(
        source.indexOf(`id="${sections[i]}"`),
      );
    for (const removed of [
      "usage--contract",
      "architecture--realization",
      "entities",
      "files",
    ])
      expect(source).not.toContain(`id="${removed}"`);
    expect(source).toContain(page.metadataPath);
    expect(source).toContain(page.metadataDigest);
  }
});

// verifies: scenario.views.reading-collections
it("publishes every Module as two reading paths and retains Views topics", async () => {
  const registry = loadScopedRegistry(root);
  const owned = registry.pages.filter((page) => page.owner === "module.views");
  expect(
    owned
      .filter((page) => page.readingCollection === "module")
      .map((page) => page.documentId),
  ).toEqual([
    "document.views.module",
    "document.views.publication",
    "document.views.pipeline",
  ]);
  expect(
    owned.filter((page) => page.readingCollection === "implementation"),
  ).toHaveLength(4);
  for (const target of registry.targets) {
    const documents = registry.pages.filter((page) => page.owner === target.id);
    expect(
      documents.some((page) => page.readingCollection === "implementation"),
    ).toBe(true);
    for (const page of documents.filter(
      (page) => page.readingCollection === "module",
    )) {
      expect(page.content).not.toMatch(/^#{2,5}\s+(?:req|scenario)\./m);
      expect(page.content).not.toContain("```concorde-contract");
    }
  }
  const entry = await readFile(
    resolve(output, "specs/concorde/views/module.html"),
    "utf8",
  );
  expect(entry).not.toContain('id="req.views.registry-derived-pages"');
  expect(entry).not.toContain('id="requirements"');
  expect(entry).toContain('aria-label="Module specification reading paths"');
  for (const page of owned.filter(
    (page) => page.readingCollection === "implementation",
  )) {
    expect(entry).toContain(`href="/concorde${page.route}"`);
    const html = await readFile(
      resolve(output, page.route.slice(1) + ".html"),
      "utf8",
    );
    expect(html).toContain('href="/concorde/specs/concorde/views/module"');
    expect(html).toContain(
      "Both reading paths belong to the same complete Module specification.",
    );
    expect(html).toContain(page.metadataDigest);
  }
  const requirements = await readFile(
    resolve(output, "specs/concorde/views/requirements.html"),
    "utf8",
  );
  expect(requirements).toContain('id="req.views.registry-derived-pages"');
  const publication = await readFile(
    resolve(output, "specs/concorde/views/scenarios.html"),
    "utf8",
  );
  expect(publication).toContain('id="scenario.views.reading-collections"');
  const manifest = JSON.parse(
    await readFile(resolve(output, "build-manifest.json"), "utf8"),
  );
  expect(manifest.schema_version).toBe(21);
  expect(
    manifest.pages.filter(
      (page: { readingCollection: string }) =>
        page.readingCollection === "implementation",
    ),
  ).toHaveLength(
    registry.pages.filter((page) => page.readingCollection === "implementation")
      .length,
  );
});

// verifies: scenario.views.agent-graphs
it("publishes executable graphs with keyboard navigation and source fingerprints", async () => {
  const html = await readFile(resolve(output, "agent-graphs.html"), "utf8");
  expect(html).toContain("The development loop");
  expect(html).toContain("Full Dev Loop invocation");
  expect(html).toContain('aria-label="All graphs"');
  expect(html).toContain('href="#specify"');
  expect(html).toContain('href="#operation-concorde-review"');
  expect(html).toContain('href="#graph-discovery"');
  expect(html).not.toContain(
    "Dedicated query and topology LangGraph factories are not implemented",
  );
  expect(html).toContain("loop_graph.py");
  expect(html).toContain("sha256:");
  expect(html).toMatch(/role="region"[^>]*tabindex="0"/i);
  expect(html).toContain('href="#stage-tasks"');
  expect(html).toContain("All transitions");
});
// verifies: scenario.views.protocol-docs-tab
it("publishes the independent standard with chapter navigation and no Spec wrapper", async () => {
  const overview = await readFile(resolve(output, "protocol.html"), "utf8");
  expect(overview).toContain("Spec Protocol");
  expect(overview).toContain("Spec management");
  expect(overview).toContain("Required format");
  expect(overview).toContain("Templates");
  expect(overview).not.toContain("provenanceShell");
  expect(overview).not.toContain("feature.concorde.evolve-protocol");
  for (const chapter of [
    "principles",
    "module",
    "spec-management",
    "spec-management/spec-and-context",
    "format",
    "templates/module",
    "templates/scenario",
  ]) {
    const html = await readFile(
      resolve(output, `protocol/${chapter}.html`),
      "utf8",
    );
    expect(html).toContain("theme-doc-sidebar-container");
    expect(html).not.toContain("provenanceShell");
  }
});
// verifies: scenario.views.publish-homepage
it("publishes the configured introduction at the root while preserving direct Spec navigation", async () => {
  const home = await readFile(resolve(output, "index.html"), "utf8");
  expect(home).toContain("Specify responsibilities. Compose Operations.");
  expect(home).toContain("Call complete Operations.");
  expect(home).toContain('id="get-started"');
  expect(home).toContain('id="reference-title"');
  expect(home.indexOf('id="reference-title"')).toBeGreaterThan(
    home.indexOf('id="get-started"'),
  );
  expect(home).toContain("Model-backed Operations");
  expect(home).toContain("Public Operations");
  expect(home).toContain("Shared execution services");
  expect(home).toContain("Launchers and supporting tools");
  expect(home).toContain("concorde-issues");
  expect(home).not.toContain("concorde-reflections-triage");
  expect(home).toContain("concorde-specify-loop");
  expect(home).toContain("26 Operations");
  expect(home).not.toContain("3 Agents with 12 task modes");
  expect(home).toContain('scope="col"');
  expect(home).toMatch(/role="region"[^>]*tabindex="0"/i);
  expect(home).toContain('href="/concorde/specs/concorde/module"');
  expect(home).not.toContain('href="/concorde/graph"');
  expect(home).toContain('href="/concorde/protocol"');
  expect(home).toContain('name="description"');
  expect(home).not.toMatch(/http-equiv="refresh"/i);
  expect(home).not.toContain("provenanceShell");
  const manifest = JSON.parse(
    await readFile(resolve(output, "build-manifest.json"), "utf8"),
  );
  expect(
    manifest.pages.some((page: { route: string }) => page.route === "/"),
  ).toBe(false);
});
// verifies: scenario.views.publish-legacy-redirect
it("preserves every legacy membership route as a redirect stub to its canonical page", async () => {
  const r = loadScopedRegistry(root);
  for (const page of r.pages)
    for (const alias of page.aliases) {
      const stub = await readFile(
        resolve(output, alias.slice(1) + ".html"),
        "utf8",
      );
      expect(stub).toContain(page.route);
      expect(stub).toContain("refresh");
    }
});
// verifies: scenario.views.publish-without-graph
it("omits graph routes and artifacts", async () => {
  for (const path of [
    "graph.html",
    "graph/index.html",
    "architecture-graph.json",
    "assets/obsolete-graph.js",
  ])
    await expect(readFile(resolve(output, path))).rejects.toThrow();
});
it("does not publish retired unregistered projections", async () => {
  for (const name of ["instructions", "wire"])
    await expect(
      readFile(resolve(output, "specs/projections/" + name + ".html")),
    ).rejects.toThrow();
});

// verifies: scenario.views.publish-repeat-without-graph
it("a second checked build preserves absence and reading", async () => {
  const result = captureProcess(
    process.execPath,
    ["--import", "tsx", "scripts/build.ts"],
    { cwd: site, timeout: 120000 },
  );
  expect(result.error).toBeUndefined();
  expect(result.signal).toBeNull();
  expect(result.status, result.stdout + "\n" + result.stderr).toBe(0);
  await validateScopedBuild(root, output);
  for (const path of [
    "graph.html",
    "architecture-graph.json",
    "assets/obsolete-graph.js",
  ])
    await expect(readFile(resolve(output, path))).rejects.toThrow();
  const r = loadScopedRegistry(root);
  const page = r.pages.find((p) => p.primaryOf === r.entryTarget)!;
  expect(
    await readFile(resolve(output, page.route.slice(1) + ".html"), "utf8"),
  ).toContain("Module Specs");
}, 120000);
