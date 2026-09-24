/**
 * Refused publications: the real build script and the real Docusaurus configuration run against a
 * fixture project; only the Docusaurus child process is replaced by a stand-in that evaluates the
 * site configuration and renders one HTML file per registered route.
 */
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { EventEmitter } from "node:events";
import { createRequire } from "node:module";
import { runInNewContext } from "node:vm";
import { resolve } from "node:path";
import { transpileModule, ModuleKind } from "typescript";
import { afterEach, beforeEach, expect, it } from "vitest";
import type { LoadContext } from "@docusaurus/types";
import generatedCache from "../plugins/generated-cache";
import scopedContent, { validateScopedBuild } from "../plugins/scoped-content";
import * as customDocs from "../plugins/scoped-content/custom-docs";
import * as model from "../plugins/scoped-content/model";
import * as siteIdentity from "../plugins/scoped-content/site-identity";
import * as userDocs from "../plugins/scoped-content/user-docs";
import { materializeScoped } from "../plugins/scoped-content/materialize";
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
  writeRegistry,
  type Project,
} from "./protocol-fixture";

let project: Project, root: string;
const put = (path: string, text: string) => putFile(project, path, text);
const load = () => model.loadScopedRegistry(root);
const nativeRequire = createRequire(import.meta.url);
const compile = (path: string) =>
  transpileModule(readFileSync(resolve(__dirname, path), "utf8"), {
    compilerOptions: { module: ModuleKind.CommonJS },
  }).outputText;

/** Evaluate the real `docusaurus.config.ts` as if it lived in the fixture's docsite directory. */
function siteConfiguration(): any {
  const loaded = { exports: {} as { default?: any } };
  const modules: Record<string, unknown> = {
    "./plugins/scoped-content/custom-docs": customDocs,
    "./plugins/generated-cache": { __esModule: true, default: generatedCache },
    "./plugins/scoped-content": { __esModule: true, default: scopedContent },
    "./plugins/scoped-content/model": model,
    "./plugins/scoped-content/site-identity": siteIdentity,
    "./plugins/scoped-content/user-docs": userDocs,
  };
  runInNewContext(compile("../docusaurus.config.ts"), {
    module: loaded,
    exports: loaded.exports,
    __dirname: resolve(root, "docsite"),
    URL,
    process,
    require: (id: string) => modules[id] ?? nativeRequire(id),
  });
  return loaded.exports.default;
}

/** Everything a stand-in Docusaurus child may render in addition to the Spec pages. */
let extraPages: Record<string, string> = {};
let spawned = 0;
/** Load the real build script with the fixture as its site directory. */
function buildScript(): () => Promise<void> {
  const loaded = { exports: {} as { buildSite: () => Promise<void> } };
  const spawn = () => {
    spawned++;
    const child = new EventEmitter();
    queueMicrotask(async () => {
      try {
        const config = siteConfiguration();
        const registry = load();
        const outDir = resolve(root, "docsite/.generated/candidate");
        const pages: Record<string, string> = { ...extraPages };
        for (const page of registry.pages)
          pages[page.route.slice(1) + ".html"] = `<h1>${page.sourcePath}</h1>`;
        for (const [path, html] of Object.entries(pages)) {
          mkdirSync(resolve(outDir, path, ".."), { recursive: true });
          writeFileSync(resolve(outDir, path), html);
        }
        const hooks = scopedContent(
          {
            siteDir: resolve(root, "docsite"),
            baseUrl: config.baseUrl,
          } as LoadContext,
          {},
        );
        await hooks.loadContent!();
        await hooks.postBuild!({
          outDir,
          routesPaths: registry.pages.map((page) => page.route),
        } as any);
        child.emit("exit", 0);
      } catch (error) {
        child.emit("error", error);
      }
    });
    return child;
  };
  runInNewContext(compile("../scripts/build.ts"), {
    module: loaded,
    exports: loaded.exports,
    __dirname: resolve(root, "docsite/scripts"),
    process,
    require: (id: string) => {
      if (id === "node:child_process") return { spawn };
      if (id === "../plugins/scoped-content/model") return model;
      if (id === "../plugins/scoped-content") return { validateScopedBuild };
      if (id === "./prepare-publication")
        return { preparePublication, productionGeneratedDirectory };
      return nativeRequire(id);
    },
  });
  return loaded.exports.buildSite;
}

function snapshot(directory: string): Record<string, string> {
  const result: Record<string, string> = {};
  const walk = (path: string) => {
    for (const entry of readdirSync(resolve(directory, path), {
      withFileTypes: true,
    })) {
      const name = path + entry.name;
      if (entry.isDirectory()) walk(name + "/");
      else result[name] = readFileSync(resolve(directory, name), "utf8");
    }
  };
  if (existsSync(directory)) walk("");
  return result;
}

const published = () => resolve(root, "docsite/build");
const staged = () => resolve(root, "docsite/.generated/content");
const identity = () =>
  resolve(root, "docsite/.generated/scoped-materialization.json");

beforeEach(() => {
  project = bankProject();
  root = project.root;
  extraPages = {};
  spawned = 0;
});
afterEach(() => rmSync(root, { recursive: true, force: true }));

/** Publish once, then leave no staging behind, so a refusal can be seen to stage nothing. */
async function publishedSite(): Promise<Record<string, string>> {
  await buildScript()();
  rmSync(resolve(root, "docsite/.generated"), { recursive: true, force: true });
  const previous = snapshot(published());
  expect(Object.keys(previous)).toContain("build-manifest.json");
  spawned = 0;
  return previous;
}

function expectNothingStagedOrPromoted(previous: Record<string, string>) {
  expect(existsSync(staged())).toBe(false);
  expect(existsSync(identity())).toBe(false);
  expect(existsSync(resolve(root, "docsite/.generated/candidate"))).toBe(false);
  expect(snapshot(published())).toEqual(previous);
}

// verifies: scenario.views.load-registry-refused
it.each([
  [
    "an unsafe path",
    () => {
      project.modules[3].owns.push("../outside.md");
      writeRegistry(project);
    },
    /\.\.\/outside\.md/,
  ],
  [
    "a symbolic link",
    () => {
      const path = resolve(root, "specs/ledger/module.md");
      rmSync(path);
      symlinkSync(resolve(root, "specs/audit/module.md"), path);
    },
    /specs\/ledger\/module\.md/,
  ],
  [
    "duplicate JSON keys",
    () =>
      put(
        "specs/ledger/module.md.json",
        read(project, "specs/ledger/module.md.json").replace(
          '"schema_version": 3',
          '"schema_version": 3, "schema_version": 3',
        ),
      ),
    /specs\/ledger\/module\.md\.json/,
  ],
  [
    "a duplicate identity",
    () =>
      updateMetadata(project, "specs/ledger/module.md", (m) => {
        m.defines[0].id = "concept.transfer.hold";
      }),
    /Duplicate identity: concept\.transfer\.hold \(specs\/ledger\/module\.md\)/,
  ],
  [
    "a composition cycle",
    () => {
      project.modules[3].contains = [
        { target: "module.bank", meaning: "#uses-transfer" },
      ];
      writeRegistry(project);
    },
    /composition cycle: module\.(bank|audit)/,
  ],
  [
    "a Mermaid block",
    () =>
      put(
        "specs/ledger/module.md",
        read(project, "specs/ledger/module.md") +
          "\n```mermaid\nsequenceDiagram\n    A->>B: hi\n```\n",
      ),
    /specs\/ledger\/module\.md/,
  ],
  [
    "a relies_on identity its target does not define",
    () => {
      project.modules[3].uses[0].relies_on = ["req.transfer.unknown"];
      writeRegistry(project);
    },
    /module\.transfer: req\.transfer\.unknown/,
  ],
  [
    "an import row that does not link its concept's defining document",
    () =>
      put(
        "specs/audit/module.md",
        read(project, "specs/audit/module.md").replace(
          "../transfer/module.md#concept.transfer.hold",
          "../transfer/requirements.md#concept.transfer.hold",
        ),
      ),
    /specs\/audit\/module\.md/,
  ],
])(
  "refuses to publish %s and stages or promotes nothing",
  async (_label, corrupt, source) => {
    const previous = await publishedSite();
    corrupt();
    await expect(buildScript()()).rejects.toThrow(source);
    expect(spawned).toBe(0);
    expectNothingStagedOrPromoted(previous);
  },
);

// verifies: scenario.views.diagram-subset-refused
it("refuses a checked D2 diagram that sets its own look and promotes nothing", async () => {
  // The diagram's own subset violation surfaces while staging, after other pages may already be
  // written, so this checks the weaker promise the scenario makes: no candidate is promoted and
  // the published site is unchanged, not that nothing at all was staged.
  const previous = await publishedSite();
  put(
    "specs/bank/module.md",
    read(project, "specs/bank/module.md") +
      '\n```d2\nfoo: Foo {\n  style.fill: "#fff"\n}\n```\n',
  );
  await expect(buildScript()()).rejects.toThrow(
    /specs\/bank\/module\.md.*outside the semantic subset|outside the semantic subset.*specs\/bank\/module\.md/s,
  );
  expect(spawned).toBe(0);
  expect(existsSync(resolve(root, "docsite/.generated/candidate"))).toBe(false);
  expect(snapshot(published())).toEqual(previous);
});

// verifies: scenario.views.reading-collections-single
it("shows only the Module documents tab when no document is an implementation document", () => {
  const tabs = () =>
    siteConfiguration()
      .themeConfig.navbar.items.filter(
        (item: any) => item.type === "docSidebar",
      )
      .map((item: any) => [item.label, item.sidebarId]);
  expect(tabs()).toEqual([
    ["Module documents", "moduleDocumentsSidebar"],
    ["Implementation documents", "implementationDocumentsSidebar"],
  ]);
  updateMetadata(project, "specs/transfer/requirements.md", (m) => {
    m.document.role = "module";
  });
  put("specs/transfer/requirements.md", "# Transfer requirements\n\nPlain.\n");
  expect(tabs()).toEqual([["Module documents", "moduleDocumentsSidebar"]]);
});

// verifies: scenario.views.user-docs
it("lists user documents first, then the Spec tabs, then custom docs, and gives them the root", () => {
  put("docs/README.md", "# Bank\n");
  put("docsite/guides/index.md", "---\nslug: /\n---\n# Guides\n");
  put(
    "docsite/site.json",
    JSON.stringify({
      ...readJson(project, "docsite/site.json"),
      userDocs: { path: "../docs" },
      customDocs: [
        {
          id: "guides",
          label: "Guides",
          path: "guides",
          routeBasePath: "guides",
        },
      ],
    }),
  );
  const config = siteConfiguration();
  expect(
    config.themeConfig.navbar.items
      .filter((item: any) => item.position === "left")
      .map((item: any) => item.label),
  ).toEqual([
    "User documents",
    "Module documents",
    "Implementation documents",
    "Guides",
  ]);
  // The root redirect page steps aside so the user documents' root page is the home page.
  expect(config.presets[0][1].pages.exclude).toContain("index.tsx");
  expect(
    config.plugins.find((plugin: any) => plugin?.[1]?.id === "user")[1],
  ).toMatchObject({ path: "../docs", routeBasePath: "/" });
});

// verifies: scenario.views.publish-homepage-default
it("keeps the root redirect page when no user documents are configured", () => {
  const config = siteConfiguration();
  expect(config.presets[0][1].pages).toEqual({});
  expect(config.plugins.some((plugin: any) => plugin?.[1]?.id === "user")).toBe(
    false,
  );
});

// verifies: scenario.views.user-docs-refused
it("user documents without a root page fail the build and promote nothing", async () => {
  const previous = await publishedSite();
  put("docs/guide.md", "# Guide\n");
  put(
    "docsite/site.json",
    JSON.stringify({
      ...readJson(project, "docsite/site.json"),
      userDocs: { path: "../docs" },
    }),
  );
  await expect(buildScript()()).rejects.toThrow(
    /userDocs\.path \.\.\/docs has no root page/,
  );
  expect(existsSync(resolve(root, "docsite/.generated/candidate"))).toBe(false);
  expect(snapshot(published())).toEqual(previous);
});

// verifies: scenario.views.materialize-failure
it("a staging that fails part-way leaves no identity and the build refuses it", async () => {
  const registry = load();
  await materializeScoped(registry);
  expect(existsSync(identity())).toBe(true);
  // The last registered page now fails to render, after earlier pages were already rewritten.
  const last = registry.pages.at(-1)!.sourcePath;
  put(last, read(project, last) + "\n[Unknown](unknown.md)\n");
  const partial = load();
  await expect(materializeScoped(partial)).rejects.toThrow(
    /Unregistered local link/,
  );
  expect(
    existsSync(resolve(staged(), "specs", partial.pages[0].stagedPath)),
  ).toBe(true);
  expect(
    existsSync(resolve(staged(), "specs", partial.pages.at(-1)!.stagedPath)),
  ).toBe(false);
  expect(existsSync(identity())).toBe(false);
  // A later build step reading the staged content refuses the partial staging.
  const hooks = scopedContent(
    { siteDir: resolve(root, "docsite"), baseUrl: "/" } as LoadContext,
    {},
  );
  await expect(hooks.loadContent!()).rejects.toThrow(
    /scoped-materialization\.json/,
  );
});

// verifies: scenario.views.custom-docs-refused
it.each([
  [
    "a registered Spec document",
    () => ({ path: "../specs", routeBasePath: "guides" }),
    /customDocs guides includes registered Spec/,
  ],
  [
    "a route that conflicts with a Spec page",
    () => {
      put("docsite/guides/index.md", "# Guides\n");
      return { path: "guides", routeBasePath: "specs" };
    },
    /customDocs\[0\]\.routeBasePath/,
  ],
  [
    "missing content",
    () => ({ path: "missing-guides", routeBasePath: "guides" }),
    /customDocs guides\.path .*missing-guides/,
  ],
])(
  "a custom docs collection with %s fails the build and promotes nothing",
  async (_label, collection, message) => {
    const previous = await publishedSite();
    put(
      "docsite/site.json",
      JSON.stringify({
        ...readJson(project, "docsite/site.json"),
        customDocs: [{ id: "guides", label: "Guides", ...collection() }],
      }),
    );
    await expect(buildScript()()).rejects.toThrow(message);
    expect(existsSync(resolve(root, "docsite/.generated/candidate"))).toBe(
      false,
    );
    expect(snapshot(published())).toEqual(previous);
  },
);

// verifies: scenario.views.custom-docs-refused
it("a custom docs page with a broken internal link fails the build naming the link", async () => {
  const previous = await publishedSite();
  put("docsite/guides/index.md", "# Guides\n");
  put(
    "docsite/site.json",
    JSON.stringify({
      ...readJson(project, "docsite/site.json"),
      customDocs: [
        {
          id: "guides",
          label: "Guides",
          path: "guides",
          routeBasePath: "guides",
        },
      ],
    }),
  );
  extraPages = {
    "guides.html": '<h1>Guides</h1><a href="/guides/missing">Next</a>',
  };
  await expect(buildScript()()).rejects.toThrow(
    /Unresolved internal navigation from .*guides.* to \/guides\/missing/,
  );
  expect(existsSync(resolve(root, "docsite/.generated/candidate"))).toBe(false);
  expect(snapshot(published())).toEqual(previous);
});
