import {
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  symlinkSync,
} from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, expect, it } from "vitest";
import { loadScopedRegistry } from "../../plugins/scoped-content/model";
import { materializeScoped } from "../../plugins/scoped-content/materialize";
import { preparePublication } from "../../scripts/prepare-publication";
import {
  bankProject,
  put,
  putDocument,
  read,
  readJson,
  writeRegistry,
  type Project,
} from "../protocol-fixture";

let project: Project;
beforeEach(() => {
  project = bankProject();
});
afterEach(() => rmSync(project.root, { recursive: true, force: true }));

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
  walk("");
  return result;
}

// verifies: scenario.views.outputs-disjoint
it.each([
  "docsite/.generated/production/content/notes.md",
  "docsite/.generated/preview/notes.md",
  "docsite/build/notes.md",
  "docsite/.docusaurus/notes.md",
])(
  "refuses a registered document inside the output %s and leaves its bytes",
  async (path) => {
    const ledger = project.modules.find((m) => m.id === "module.ledger")!;
    ledger.owns.push(path);
    putDocument(project, path, {
      owner: "module.ledger",
      body: "# Notes\n\nKept.\n",
    });
    writeRegistry(project);
    const before = read(project, path);
    await expect(
      preparePublication(project.root, { mode: "build" }),
    ).rejects.toThrow(/notes\.md lies inside the publication output/);
    expect(read(project, path)).toBe(before);
    expect(read(project, path + ".json")).toContain("module.ledger");
  },
);

// verifies: scenario.views.outputs-disjoint
it("refuses an output directory that is a symbolic link before clearing anything", async () => {
  const before = snapshot(resolve(project.root, "specs"));
  mkdirSync(resolve(project.root, "docsite"), { recursive: true });
  symlinkSync(
    resolve(project.root, "specs"),
    resolve(project.root, "docsite/.generated"),
  );
  for (const mode of ["preview", "build"] as const)
    await expect(preparePublication(project.root, { mode })).rejects.toThrow(
      /docsite\/\.generated\/ is a symbolic link/,
    );
  expect(snapshot(resolve(project.root, "specs"))).toEqual(before);
});

const configure = (fields: Record<string, unknown>) =>
  put(
    project,
    "docsite/site.json",
    JSON.stringify({ ...readJson(project, "docsite/site.json"), ...fields }),
  );

// verifies: scenario.views.outputs-disjoint
it.each([
  [
    "a user documents directory",
    () => configure({ userDocs: { path: ".generated/production/content" } }),
    /userDocs\.path \.generated\/production\/content lies inside the publication output docsite\/\.generated\//,
  ],
  [
    "a custom docs directory",
    () =>
      configure({
        customDocs: [
          {
            id: "guides",
            label: "Guides",
            path: "./.generated/preview/content",
            routeBasePath: "guides",
          },
        ],
      }),
    /customDocs guides\.path \.\/\.generated\/preview\/content lies inside/,
  ],
  [
    "a custom docs sidebar file",
    () =>
      configure({
        customDocs: [
          {
            id: "guides",
            label: "Guides",
            path: "../guides",
            routeBasePath: "guides",
            sidebarPath: ".generated/production/content/sidebar.ts",
          },
        ],
      }),
    /customDocs guides\.sidebarPath \.generated\/production\/content\/sidebar\.ts lies inside/,
  ],
  [
    "an extension's docs plugin directory",
    () =>
      put(
        project,
        "docsite/custom-docs/index.ts",
        'module.exports.default = {plugins: [["@docusaurus/plugin-content-docs", {id: "extra", path: ".docusaurus/content", routeBasePath: "extra"}]]};',
      ),
    /custom-docs\/index\.ts docs plugin extra\.path \.docusaurus\/content lies inside the publication output docsite\/\.docusaurus\//,
  ],
])(
  "refuses %s inside a publication output before clearing it",
  async (_name, configureInput, message) => {
    for (const directory of [
      "docsite/.generated/production/content",
      "docsite/.generated/preview/content",
      "docsite/.docusaurus/content",
    ])
      put(project, `${directory}/sidebar.ts`, "authored\n");
    configureInput();
    const before = snapshot(resolve(project.root, "docsite"));
    for (const mode of ["preview", "build"] as const)
      await expect(preparePublication(project.root, { mode })).rejects.toThrow(
        message,
      );
    expect(snapshot(resolve(project.root, "docsite"))).toEqual(before);
  },
);

// verifies: scenario.views.outputs-disjoint
it("refuses a user documents directory that physically lies inside an output", async () => {
  put(project, "docsite/.generated/production/content/index.md", "# Home\n");
  symlinkSync(
    resolve(project.root, "docsite/.generated/production/content"),
    resolve(project.root, "docs"),
  );
  configure({ userDocs: { path: "../docs" } });
  await expect(
    preparePublication(project.root, { mode: "build" }),
  ).rejects.toThrow(
    /userDocs\.path \.\.\/docs lies inside the publication output/,
  );
  expect(read(project, "docsite/.generated/production/content/index.md")).toBe(
    "# Home\n",
  );
});

// verifies: scenario.views.outputs-disjoint
it.each([
  ["docsite/.generated/production", "build"],
  ["docsite/.generated/preview", "preview"],
  ["docsite/.generated/production/content", "build"],
  ["docsite/.generated/candidate", "build"],
  ["docsite/.generated/previous-build", "preview"],
  ["docsite/.generated/docusaurus-production", "preview"],
] as const)(
  "refuses a symbolic link at %s below a real output before clearing anything",
  async (path, mode) => {
    // Behind the link, a cleanup of `content/` would reach `specs/content/`.
    putDocument(project, "specs/content/notes.md", {
      owner: "module.ledger",
      body: "# Notes\n\nKept.\n",
    });
    const before = snapshot(resolve(project.root, "specs"));
    mkdirSync(resolve(project.root, path, ".."), { recursive: true });
    symlinkSync(resolve(project.root, "specs"), resolve(project.root, path));
    await expect(preparePublication(project.root, { mode })).rejects.toThrow(
      `Publication output ${path}/ is a symbolic link`,
    );
    expect(snapshot(resolve(project.root, "specs"))).toEqual(before);
  },
);

// verifies: scenario.views.outputs-disjoint
it("refuses a staged sidebar that is a symbolic link to a source", async () => {
  const path = "specs/ledger/module.md.json";
  const before = read(project, path);
  mkdirSync(resolve(project.root, "docsite/.generated/production"), {
    recursive: true,
  });
  symlinkSync(
    resolve(project.root, path),
    resolve(project.root, "docsite/.generated/production/specs-sidebar.json"),
  );
  await expect(
    preparePublication(project.root, { mode: "build" }),
  ).rejects.toThrow(
    "Publication output docsite/.generated/production/specs-sidebar.json is a symbolic link",
  );
  expect(read(project, path)).toBe(before);
});

// verifies: scenario.views.outputs-disjoint
it("refuses a docsite that physically holds the registered documents", () => {
  rmSync(resolve(project.root, "docsite"), { recursive: true, force: true });
  // `docsite/build` is then `specs/build`: a document there would be cleared by promotion.
  symlinkSync(resolve(project.root, "specs"), resolve(project.root, "docsite"));
  const ledger = project.modules.find((m) => m.id === "module.ledger")!;
  ledger.owns.push("specs/build/notes.md");
  putDocument(project, "specs/build/notes.md", {
    owner: "module.ledger",
    body: "# Notes\n\nKept.\n",
  });
  writeRegistry(project);
  expect(() => loadScopedRegistry(project.root)).toThrow(
    /specs\/build\/notes\.md lies inside the publication output docsite\/build/,
  );
});

// verifies: scenario.views.production-preview-isolation
it("a production staging leaves the preview's staged files unchanged", async () => {
  const registry = loadScopedRegistry(project.root);
  await materializeScoped(registry, "preview");
  const preview = resolve(project.root, "docsite/.generated/preview");
  const staged = snapshot(preview);
  expect(Object.keys(staged)).toContain("scoped-materialization.json");
  expect(Object.keys(staged)).toContain("specs-sidebar.json");
  await preparePublication(project.root, { mode: "build" });
  expect(snapshot(preview)).toEqual(staged);
  expect(
    Object.keys(
      snapshot(resolve(project.root, "docsite/.generated/production")),
    ),
  ).toEqual(Object.keys(staged));
});
