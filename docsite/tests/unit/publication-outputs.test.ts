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
  putDocument,
  read,
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
