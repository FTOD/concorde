import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { EventEmitter } from "node:events";
import { createRequire } from "node:module";
import { runInNewContext } from "node:vm";
import { resolve } from "node:path";
import { transpileModule, ModuleKind } from "typescript";
import { evaluate } from "@mdx-js/mdx";
import * as jsxRuntime from "react/jsx-runtime";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeEach, expect, it } from "vitest";
import type { LoadContext } from "@docusaurus/types";
import {
  loadScopedRegistry,
  requireScoped,
  rewriteLinks,
} from "../plugins/scoped-content/model";
import { materializeScoped } from "../plugins/scoped-content/materialize";
import scopedContent, { validateScopedBuild } from "../plugins/scoped-content";
import { customDocsConfiguration } from "../plugins/scoped-content/custom-docs";
import { parseSiteIdentity } from "../plugins/scoped-content/site-identity";
import { promoteCandidate } from "../scripts/build";
import {
  preparePublication,
  productionGeneratedDirectory,
} from "../scripts/prepare-publication";
import {
  bankProject,
  put as putFile,
  read,
  readJson,
  updateMetadata,
  type Project,
} from "./protocol-fixture";

let project: Project, root: string;
const put = (path: string, text: string) => putFile(project, path, text);
const load = () => loadScopedRegistry(root);
const plugin = (baseUrl = "/") =>
  scopedContent(
    { siteDir: resolve(root, "docsite"), baseUrl } as LoadContext,
    {},
  );
/** Stand in for Docusaurus: one HTML file per registered route. */
function render(outDir: string, html: (route: string) => string) {
  for (const page of load().pages) {
    const file = resolve(outDir, page.route.slice(1) + ".html");
    mkdirSync(resolve(file, ".."), { recursive: true });
    writeFileSync(file, html(page.route));
  }
}
beforeEach(() => {
  project = bankProject();
  root = project.root;
});
afterEach(() => rmSync(root, { recursive: true, force: true }));

// verifies: scenario.views.materialize scenario.views.validate-candidate-mismatch
it("writes a manifest after the build and validates the candidate against current sources", async () => {
  const registry = load();
  await materializeScoped(registry);
  const hooks = plugin();
  await hooks.loadContent!();
  const outDir = resolve(root, "candidate");
  render(outDir, () => "<main>Rendered page</main>");
  await hooks.postBuild!({
    outDir,
    routesPaths: registry.pages.map((p) => p.route),
  } as any);
  await expect(validateScopedBuild(root, outDir)).resolves.toBeUndefined();
  const manifest = readJson(project, "candidate/build-manifest.json");
  expect(manifest.schema_version).toBe(23);
  expect(manifest.sourceDigest).toBe(registry.sourceDigest);
  expect(manifest.pages[4]).toEqual({
    sourcePath: "specs/audit/module.md",
    route: "/specs/audit/module",
    contentDigest: registry.pages[4].contentDigest,
    metadataPath: "specs/audit/module.md.json",
    metadataDigest: registry.pages[4].metadataDigest,
    readingCollection: "module",
    owner: "module.audit",
    includedBy: [
      {
        moduleId: "module.bank",
        reasons: [{ relation: "contains", id: "module.audit" }],
      },
      {
        moduleId: "module.audit",
        reasons: [{ relation: "owns", id: "module.audit" }],
      },
    ],
  });
  expect(existsSync(resolve(outDir, "architecture-graph.json"))).toBe(false);
  // A metadata-only change makes both the staging and the manifest stale.
  updateMetadata(project, "specs/transfer/requirements.md", (m) => {
    m.extensions = { "tool.note": true };
  });
  await expect(hooks.loadContent!()).rejects.toThrow(
    /Materialized Spec source identity differs/,
  );
  await expect(validateScopedBuild(root, outDir)).rejects.toThrow(
    /Build Manifest 23/,
  );
});

// verifies: scenario.views.validate-candidate-mismatch
it("rejects every altered inventory without repairing it", async () => {
  const registry = load();
  await materializeScoped(registry);
  const hooks = plugin();
  await hooks.loadContent!();
  const outDir = resolve(root, "candidate");
  mkdirSync(outDir);
  await hooks.postBuild!({
    outDir,
    routesPaths: registry.pages.map((p) => p.route),
  } as any);
  const path = resolve(outDir, "build-manifest.json");
  const original = readFileSync(path, "utf8");
  const manifest = JSON.parse(original);
  const variants = [
    "{invalid json",
    JSON.stringify({ ...manifest, schema_version: 21 }),
    JSON.stringify({ ...manifest, sourceDigest: "sha256:" + "0".repeat(64) }),
    JSON.stringify({ ...manifest, pages: manifest.pages.slice(1) }),
    JSON.stringify({ ...manifest, pages: [...manifest.pages].reverse() }),
    ...[
      "sourcePath",
      "route",
      "contentDigest",
      "metadataPath",
      "metadataDigest",
      "readingCollection",
      "owner",
      "includedBy",
    ].map((field) => {
      const changed = JSON.parse(original);
      changed.pages[0][field] = Array.isArray(changed.pages[0][field])
        ? []
        : "changed";
      return JSON.stringify(changed);
    }),
  ];
  for (const bytes of variants) {
    writeFileSync(path, bytes);
    await expect(validateScopedBuild(root, outDir)).rejects.toThrow();
    expect(readFileSync(path, "utf8")).toBe(bytes);
  }
  rmSync(path);
  await expect(validateScopedBuild(root, outDir)).rejects.toThrow();
  expect(existsSync(path)).toBe(false);
});

// verifies: scenario.views.publish-preserves-previous-on-failure
it("postBuild refuses missing routes and changed sources before writing the manifest", async () => {
  const registry = load();
  await materializeScoped(registry);
  const hooks = plugin();
  await hooks.loadContent!();
  const outDir = resolve(root, "candidate");
  mkdirSync(outDir);
  const routesPaths = registry.pages.map((p) => p.route);
  await expect(
    hooks.postBuild!({ outDir, routesPaths: routesPaths.slice(1) } as any),
  ).rejects.toThrow(/not rendered/);
  expect(existsSync(resolve(outDir, "build-manifest.json"))).toBe(false);
  const source = "specs/transfer/requirements.md";
  put(source, read(project, source) + "\nChanged during build.\n");
  await expect(
    hooks.postBuild!({ outDir, routesPaths } as any),
  ).rejects.toThrow(/source changed/);
  expect(existsSync(resolve(outDir, "build-manifest.json"))).toBe(false);
});

// verifies: scenario.views.materialize scenario.views.build-site
it("rejects missing or stale staging identities before writing the manifest", async () => {
  const registry = load();
  await materializeScoped(registry);
  const hooks = plugin();
  await hooks.loadContent!();
  const outDir = resolve(root, "candidate");
  mkdirSync(outDir);
  const identity = "docsite/.generated/scoped-materialization.json";
  for (const bytes of [
    null,
    "{malformed",
    JSON.stringify({ schema_version: 1, sourceDigest: registry.sourceDigest }),
    JSON.stringify({
      schema_version: 2,
      sourceDigest: "sha256:" + "0".repeat(64),
    }),
  ]) {
    if (bytes === null) rmSync(resolve(root, identity));
    else put(identity, bytes);
    await expect(
      hooks.postBuild!({
        outDir,
        routesPaths: registry.pages.map((page) => page.route),
      } as any),
    ).rejects.toThrow();
    expect(existsSync(resolve(outDir, "build-manifest.json"))).toBe(false);
  }
});

// verifies: scenario.views.materialize
it("rejects sources changed between staging and plugin loading", async () => {
  const original = load();
  await materializeScoped(original);
  expect((await plugin().loadContent!())?.sourceDigest).toBe(
    original.sourceDigest,
  );
  put(
    "specs/ledger/module.md",
    read(project, "specs/ledger/module.md") + "\nNew.\n",
  );
  await expect(plugin().loadContent!()).rejects.toThrow(
    /Materialized Spec source identity differs/,
  );
  put(
    "specs/ledger/module.md",
    read(project, "specs/ledger/module.md") + "\n[Missing](missing.md)\n",
  );
  await expect(materializeScoped(load())).rejects.toThrow(/Unregistered/);
  await expect(plugin().loadContent!()).rejects.toThrow(/ENOENT/);
});

// verifies: scenario.views.inline-diagrams
it("global data carries page metadata and the root Module without bodies", async () => {
  const registry = load();
  let data: any;
  await plugin().contentLoaded!({
    content: registry,
    actions: { setGlobalData: (value: unknown) => (data = value) },
  } as any);
  expect(data.schema_version).toBe(23);
  expect(data.rootModule).toBe("module.bank");
  expect(data.pages).toEqual(
    registry.pages.map(({ content: _content, ...page }) => page),
  );
  for (const key of ["nodes", "edges", "modules", "targets"])
    expect(data).not.toHaveProperty(key);
});

// verifies: scenario.views.rebuild-removes-stale-pages
it("checked directory replacement removes obsolete output on consecutive promotions", async () => {
  const obsolete = [
    "graph.html",
    "architecture-graph.json",
    "specs/old/page.html",
  ];
  for (const path of obsolete) put("published/" + path, "previous output");
  for (let iteration = 0; iteration < 2; iteration++) {
    const registry = load();
    await materializeScoped(registry);
    const hooks = plugin();
    await hooks.loadContent!();
    const outDir = resolve(root, "candidate");
    render(outDir, (route) => route);
    await hooks.postBuild!({
      outDir,
      routesPaths: registry.pages.map((page) => page.route),
    } as any);
    await validateScopedBuild(root, outDir);
    await promoteCandidate(
      outDir,
      resolve(root, "published"),
      resolve(root, "backup"),
    );
    await validateScopedBuild(root, resolve(root, "published"));
    for (const path of obsolete)
      expect(existsSync(resolve(root, "published", path))).toBe(false);
    for (const page of registry.pages)
      expect(read(project, "published/" + page.route.slice(1) + ".html")).toBe(
        page.route,
      );
  }
});

// verifies: scenario.views.cross-module-link scenario.views.publish-reference-link
it("validates cross-Module links and anchors in rendered output", async () => {
  const audit = "specs/audit/module.md";
  put(
    audit,
    read(project, audit) +
      "\n[Source reference](../transfer/requirements.md#scenario.transfer.submit)\n\n" +
      "[Query reference](../transfer/requirements.md?view=compact#scenario.transfer.submit)\n\n" +
      "[Retained form][rule]\n\n[rule]: /specs/transfer/requirements#scenario.transfer.submit\n",
  );
  const registry = load();
  await materializeScoped(registry);
  const staged = read(
    project,
    "docsite/.generated/content/specs/audit/module.md",
  );
  expect(staged).toContain(
    "[Source reference](/specs/transfer/requirements#scenario.transfer.submit)",
  );
  expect(staged).toContain(
    "[Query reference](/specs/transfer/requirements?view=compact#scenario.transfer.submit)",
  );
  const hooks = plugin();
  await hooks.loadContent!();
  const outDir = resolve(root, "candidate");
  render(
    outDir,
    () =>
      '<h1 id="scenario.transfer.submit">Submit</h1><a id="concept.transfer.hold"></a>',
  );
  await hooks.postBuild!({
    outDir,
    routesPaths: registry.pages.map((page) => page.route),
  } as any);
  const referring = registry.pages.find((p) => p.sourcePath === audit)!;
  const referrer = "candidate/" + referring.route.slice(1) + ".html";
  // Render the reference-style link the rewrite leaves untouched with the installed MDX renderer.
  const rewritten = rewriteLinks(registry, referring);
  expect(rewritten).toContain("[Retained form][rule]");
  const rendered = await evaluate(rewritten, { ...jsxRuntime });
  put(referrer, renderToStaticMarkup(createElement(rendered.default)));
  expect(read(project, referrer)).toContain(">Retained form</a>");
  await expect(validateScopedBuild(root, outDir)).resolves.toBeUndefined();
  put(
    referrer,
    '<a href="/specs/transfer/requirements?view=full#scenario.transfer.submit">Read</a>',
  );
  await expect(validateScopedBuild(root, outDir)).resolves.toBeUndefined();
  for (const destination of [
    "/specs/transfer/requirements#missing",
    "/specs/module.transfer/0123456789abcdef",
  ]) {
    put(referrer, `<a href="${destination}">Read</a>`);
    await expect(validateScopedBuild(root, outDir)).rejects.toThrow(
      /Unresolved internal navigation/,
    );
  }
});

// verifies: scenario.views.build-site scenario.views.publish-preserves-previous-on-failure scenario.views.validate-candidate-mismatch scenario.views.rebuild-removes-stale-pages
it.each(["/", "/%E6%96%87%E6%A1%A3/"])(
  "the real build script keeps the published site on failure and replaces it on success (%s)",
  async (baseUrl) => {
    const identity = readJson(project, "docsite/site.json");
    put("docsite/site.json", JSON.stringify({ ...identity, baseUrl }));
    const navigation = (route: string) =>
      baseUrl.toLowerCase() + route.slice(1);
    const nativeRequire = createRequire(import.meta.url);
    const buildPath = resolve(__dirname, "../scripts/build.ts");
    const compiled = transpileModule(readFileSync(buildPath, "utf8"), {
      compilerOptions: { module: ModuleKind.CommonJS },
    }).outputText;
    const target = "/specs/transfer/requirements#scenario.transfer.submit";
    let destination = navigation(target);
    let renderCount = 0;
    let failure: "none" | "source" | "manifest" = "none";
    // Execute the actual build module with this fixture as its site directory. Only the
    // Docusaurus child is replaced: preparation, postBuild, validation and promotion run live.
    const fixtureModule = { exports: {} as { buildSite: () => Promise<void> } };
    const spawn = () => {
      const child = new EventEmitter();
      queueMicrotask(async () => {
        try {
          const registry = load();
          const outDir = resolve(root, "docsite/.generated/candidate");
          render(
            outDir,
            () =>
              `<h1 id="scenario.transfer.submit">Submit</h1><a href="${destination}">Read</a>`,
          );
          const hooks = plugin(baseUrl);
          await hooks.loadContent!();
          await hooks.postBuild!({
            outDir,
            routesPaths: registry.pages.map(
              (page) => baseUrl + page.route.slice(1),
            ),
          } as any);
          if (failure === "source")
            put(
              "specs/transfer/requirements.md",
              read(project, "specs/transfer/requirements.md") +
                "\nChanged after postBuild.\n",
            );
          if (failure === "manifest") {
            const path = resolve(outDir, "build-manifest.json");
            const manifest = JSON.parse(readFileSync(path, "utf8"));
            writeFileSync(
              path,
              JSON.stringify({ ...manifest, schema_version: 17 }),
            );
          }
          renderCount++;
          child.emit("exit", 0);
        } catch (error) {
          child.emit("error", error);
        }
      });
      return child;
    };
    runInNewContext(compiled, {
      module: fixtureModule,
      exports: fixtureModule.exports,
      __dirname: resolve(root, "docsite/scripts"),
      process,
      require: (id: string) => {
        if (id === "node:child_process") return { spawn };
        if (id === "../plugins/scoped-content/model") return { requireScoped };
        if (id === "../plugins/scoped-content") return { validateScopedBuild };
        if (id === "./prepare-publication")
          return { preparePublication, productionGeneratedDirectory };
        return nativeRequire(id);
      },
    });
    const snapshot = (directory: string): Record<string, Buffer> => {
      const result: Record<string, Buffer> = {};
      const walk = (path: string) => {
        for (const entry of readdirSync(resolve(directory, path), {
          withFileTypes: true,
        })) {
          const name = path + entry.name;
          if (entry.isDirectory()) walk(name + "/");
          else result[name] = readFileSync(resolve(directory, name));
        }
      };
      walk("");
      return result;
    };
    await fixtureModule.exports.buildSite();
    const published = resolve(root, "docsite/build");
    const obsolete = [
      "graph.html",
      "architecture-graph.json",
      "specs/old/page.html",
    ];
    for (const path of obsolete)
      put("docsite/build/" + path, "previous output");
    const previous = snapshot(published);
    expect(Object.keys(previous)).toContain("build-manifest.json");
    const unchanged = () => {
      expect(snapshot(published)).toEqual(previous);
      expect(existsSync(resolve(root, "docsite/.generated/candidate"))).toBe(
        false,
      );
      expect(
        existsSync(resolve(root, "docsite/.generated/previous-build")),
      ).toBe(false);
    };
    for (const bad of ["/missing", "/specs/transfer/requirements#missing"]) {
      destination = navigation(bad);
      await expect(fixtureModule.exports.buildSite()).rejects.toThrow(
        /Unresolved internal navigation.*to /,
      );
      unchanged();
    }
    destination = navigation(target);
    const source = read(project, "specs/transfer/requirements.md");
    for (const invalid of ["source", "manifest"] as const) {
      failure = invalid;
      await expect(fixtureModule.exports.buildSite()).rejects.toThrow(
        /Build Manifest 23/,
      );
      unchanged();
      put("specs/transfer/requirements.md", source);
    }
    failure = "none";
    for (let repeat = 0; repeat < 2; repeat++) {
      await fixtureModule.exports.buildSite();
      await expect(
        validateScopedBuild(root, published),
      ).resolves.toBeUndefined();
      for (const path of obsolete)
        expect(existsSync(resolve(published, path))).toBe(false);
      expect(
        readFileSync(resolve(published, "specs/bank/module.html"), "utf8"),
      ).toContain(destination);
    }
    expect(renderCount).toBe(7);
  },
);

// verifies: scenario.views.custom-docs
it("rejects registered Spec sources in a custom collection", () => {
  const identity = parseSiteIdentity({
    schema_version: 1,
    title: "Bank",
    url: "https://example.com",
    baseUrl: "/",
    organizationName: "bank",
    projectName: "bank",
    customDocs: [
      {
        id: "guides",
        label: "Guides",
        path: "../specs",
        routeBasePath: "guides",
      },
    ],
  });
  expect(() =>
    customDocsConfiguration(resolve(root, "docsite"), identity, load()),
  ).toThrow(/includes registered Spec/);
});

// verifies: scenario.views.custom-docs
it("adds collection and executable tabs without changing registered context inputs", () => {
  const before = load();
  put("docsite/custom-docs/guides/index.md", "---\nslug: /\n---\n# Handbook");
  put(
    "docsite/custom-docs/sidebar.js",
    'module.exports = {guides: ["index"]};',
  );
  put(
    "docsite/custom-docs/index.ts",
    'module.exports.default = {plugins: ["example-plugin"], navbarItems: [{to: "/app", label: "App", position: "left"}]};',
  );
  const identity = parseSiteIdentity({
    ...readJson(project, "docsite/site.json"),
    customDocs: [
      {
        id: "guides",
        label: "Handbook",
        path: "./custom-docs/guides",
        routeBasePath: "handbook",
        sidebarPath: "custom-docs/sidebar.js",
      },
    ],
  });
  const custom = customDocsConfiguration(
    resolve(root, "docsite"),
    identity,
    before,
  );
  expect(custom.plugins).toEqual([
    [
      "@docusaurus/plugin-content-docs",
      expect.objectContaining({
        id: "guides",
        routeBasePath: "handbook",
        sidebarPath: resolve(root, "docsite/custom-docs/sidebar.js"),
      }),
    ],
    "example-plugin",
  ]);
  expect(custom.navbarItems.map((item) => item.label)).toEqual([
    "Handbook",
    "App",
  ]);
  expect(custom.docsRouteBasePath).toEqual(["/handbook"]);
  expect(custom.docsDir).toEqual(["./custom-docs/guides"]);
  put(
    "docsite/site.json",
    JSON.stringify({
      ...readJson(project, "docsite/site.json"),
      customDocs: identity.customDocs,
    }),
  );
  expect(load()).toEqual(before);
});

// verifies: scenario.views.custom-docs
it.each(["missing", "file", "sidebar"])(
  "rejects unavailable collection input %s",
  (kind) => {
    put("docsite/guide-file.md", "# A file");
    put("docsite/guides/index.md", "---\nslug: /\n---\n# Guide");
    const identity = parseSiteIdentity({
      ...readJson(project, "docsite/site.json"),
      customDocs: [
        {
          id: "guides",
          label: "Guides",
          path:
            kind === "missing"
              ? "missing"
              : kind === "file"
                ? "guide-file.md"
                : "guides",
          routeBasePath: "guides",
          ...(kind === "sidebar" ? { sidebarPath: "missing-sidebar.ts" } : {}),
        },
      ],
    });
    expect(() =>
      customDocsConfiguration(resolve(root, "docsite"), identity, load()),
    ).toThrow();
  },
);

// verifies: scenario.views.custom-docs
it.each(["[]", '{plugins: "bad"}', "{navbarItems: {}}"])(
  "rejects malformed executable extension %s",
  (value) => {
    put(
      "docsite/custom-docs/index.ts",
      "module.exports.default = " + value + ";",
    );
    const identity = parseSiteIdentity(readJson(project, "docsite/site.json"));
    expect(() =>
      customDocsConfiguration(resolve(root, "docsite"), identity, load()),
    ).toThrow(/custom-docs\/index.ts/);
  },
);
