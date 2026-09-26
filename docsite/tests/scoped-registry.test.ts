import {
  existsSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, expect, it } from "vitest";
import {
  loadScopedRegistry,
  rewriteLinks,
} from "../plugins/scoped-content/model";
import {
  materializeScoped,
  scopedSidebar,
} from "../plugins/scoped-content/materialize";
import {
  bankProject,
  entryBody,
  module,
  put,
  putDocument,
  read,
  readJson,
  updateMetadata,
  writeRegistry,
  type Project,
} from "./protocol-fixture";

interface SidebarItem {
  type: string;
  label: string;
  id?: string;
  link?: { type: "doc"; id: string };
  collapsed?: boolean;
  items?: SidebarItem[];
}
let project: Project;
const load = () => loadScopedRegistry(project.root);
const record = (id: string) => project.modules.find((m) => m.id === id)!;
const page = (path: string) => load().pages.find((p) => p.sourcePath === path)!;
const docs = (items: SidebarItem[]): string[] =>
  items.flatMap((item) => [
    ...(item.id ? [item.id] : []),
    ...(item.link ? [item.link.id] : []),
    ...docs(item.items ?? []),
  ]);
beforeEach(() => {
  project = bankProject();
});
afterEach(() => rmSync(project.root, { recursive: true, force: true }));

// verifies: scenario.views.load-registry
it("loads Modules, composition and one page per registered document", () => {
  const registry = load();
  expect(registry.schema_version).toBe(23);
  expect(registry.rootModule).toBe("module.bank");
  expect(registry.modules.map((m) => m.id)).toEqual([
    "module.bank",
    "module.transfer",
    "module.ledger",
    "module.audit",
  ]);
  expect(registry.pages.map((p) => p.sourcePath)).toEqual([
    "specs/bank/module.md",
    "specs/transfer/module.md",
    "specs/transfer/requirements.md",
    "specs/ledger/module.md",
    "specs/audit/module.md",
  ]);
  const transfer = registry.pages[1];
  expect(transfer).toMatchObject({
    route: "/specs/transfer/module",
    stagedPath: "transfer/module.md",
    documentId: "document.transfer.module",
    owner: "module.transfer",
    primaryOf: "module.transfer",
    readingCollection: "module",
    metadataPath: "specs/transfer/module.md.json",
  });
  expect(registry.pages[2]).toMatchObject({
    primaryOf: null,
    readingCollection: "implementation",
  });
  expect(registry.nodes.map((n) => [n.id, n.owner, n.definition])).toEqual([
    [
      "concept.transfer.hold",
      "module.transfer",
      "Money withheld until a transfer settles.",
    ],
    ["realization.transfer.service", "module.transfer", undefined],
    ["realization.ledger.book", "module.ledger", undefined],
  ]);
  expect(loadScopedRegistry(project.root)).toEqual(registry);
});

// verifies: scenario.views.load-registry
it("derives which Modules select each document from owns, contains, uses and includes", () => {
  const selectedBy = (path: string) =>
    Object.fromEntries(
      page(path).includedBy.map(({ moduleId, reasons }) => [moduleId, reasons]),
    );
  expect(selectedBy("specs/transfer/module.md")).toEqual({
    "module.bank": [{ relation: "contains", id: "module.transfer" }],
    "module.transfer": [{ relation: "owns", id: "module.transfer" }],
    "module.audit": [{ relation: "uses", id: "module.transfer" }],
  });
  // relies_on narrows the Audit selection to the entry and the documents defining its nodes.
  expect(Object.keys(selectedBy("specs/transfer/requirements.md"))).toEqual([
    "module.bank",
    "module.transfer",
  ]);
  // Selection is one level: Bank does not reach Ledger through Transfer.
  expect(Object.keys(selectedBy("specs/ledger/module.md"))).toEqual([
    "module.transfer",
    "module.ledger",
  ]);
  record("module.audit").uses[0].relies_on = ["scenario.transfer.submit"];
  record("module.audit").includes = [
    { kind: "module", target: "module.ledger", reason: "settled entries" },
    { kind: "external", target: "references/", reason: "not published" },
  ];
  writeRegistry(project);
  expect(selectedBy("specs/transfer/requirements.md")["module.audit"]).toEqual([
    { relation: "uses", id: "module.transfer" },
  ]);
  expect(selectedBy("specs/ledger/module.md")["module.audit"]).toEqual([
    { relation: "includes", kind: "module", id: "module.ledger" },
  ]);
  record("module.audit").uses[0].relies_on = ["req.ledger.unknown"];
  writeRegistry(project);
  expect(load).toThrow(/relies_on names no node of module.transfer/);
  record("module.audit").uses[0].relies_on = ["realization.ledger.book"];
  writeRegistry(project);
  expect(load).toThrow(/relies_on names no node/);
});

// verifies: scenario.views.load-registry
it("requires registry schema 3 and a module block exactly in each entry", () => {
  const registry = readJson(project, ".concorde/specs.json");
  for (const invalid of [
    { ...registry, schema_version: 5 },
    { schema_version: 3, modules: [] },
    { ...registry, project_id: "project.bank" },
    {
      schema_version: 3,
      modules: [{ ...registry.modules[0], parent: null }],
    },
  ]) {
    put(project, ".concorde/specs.json", JSON.stringify(invalid));
    expect(load).toThrow();
  }
  writeRegistry(project);
  updateMetadata(project, "specs/audit/module.md", (m) => {
    delete m.module;
  });
  expect(load).toThrow(/requires a module block/);
  writeRegistry(project);
  updateMetadata(project, "specs/transfer/requirements.md", (m) => {
    m.module = {};
  });
  expect(load).toThrow(/Only a Module entry declares a module block/);
});

// verifies: scenario.views.load-registry
it("rejects schema-2 metadata, foreign owners and invalid node records", () => {
  const path = "specs/ledger/module.md";
  const cases: ((m: any) => void)[] = [
    (m) => (m.schema_version = 2),
    (m) => (m.entities = []),
    (m) => (m.document.owner = "module.transfer"),
    (m) => (m.document.extra = true),
    (m) => (m.defines[0].type = "entity"),
    (m) => delete m.defines[0].entries,
    (m) => (m.defines[0].meaning = "../transfer/module.md#x"),
    (m) => (m.defines[0].meaning = "#missing-anchor"),
    (m) => (m.relations = [{ type: "uses", source: "a", target: "b" }]),
    (m) => delete m.relations,
  ];
  const original = read(project, path + ".json");
  for (const change of cases) {
    put(project, path + ".json", original);
    updateMetadata(project, path, change);
    expect(load).toThrow();
  }
  put(project, path + ".json", original);
  expect(load).not.toThrow();
});

// verifies: scenario.views.load-registry
it("rejects duplicate identities, owners and titles", () => {
  updateMetadata(project, "specs/ledger/module.md", (m) => {
    m.defines[0].id = "concept.transfer.hold";
  });
  expect(load).toThrow(/Duplicate identity: concept.transfer.hold/);
  updateMetadata(project, "specs/ledger/module.md", (m) => {
    m.defines[0].id = "realization.ledger.book";
    m.document.id = "document.transfer.module";
  });
  expect(load).toThrow(/Duplicate identity: document.transfer.module/);
  updateMetadata(project, "specs/ledger/module.md", (m) => {
    m.document.id = "document.ledger.module";
  });
  record("module.audit").owns.push("specs/ledger/module.md");
  writeRegistry(project);
  expect(load).toThrow(/Document must have one owner/);
  record("module.audit").owns.pop();
  record("module.audit").title = "Ledger";
  writeRegistry(project);
  expect(load).toThrow(/Duplicate Module title/);
});

// verifies: scenario.views.load-registry
it("follows an acyclic contains tree and treats every uncontained Module as a root", () => {
  record("module.bank").contains.pop();
  writeRegistry(project);
  expect(load().rootModule).toBe("module.bank");
  expect(scopedSidebar(load()).map((item) => item.label)).toEqual([
    "Bank",
    "Audit",
  ]);
  record("module.audit").contains = [
    { target: "module.ledger", meaning: "#uses-transfer" },
  ];
  writeRegistry(project);
  expect(load).toThrow(/more than one parent: module.ledger/);
  record("module.audit").contains = [
    { target: "module.bank", meaning: "#uses-transfer" },
  ];
  record("module.bank").contains.push({
    target: "module.audit",
    meaning: "#contains-audit",
  });
  writeRegistry(project);
  expect(load).toThrow(/cycle/);
  record("module.audit").contains = [
    { target: "module.missing", meaning: "#uses-transfer" },
  ];
  writeRegistry(project);
  expect(load).toThrow(/Unknown or self contained Module/);
});

// verifies: scenario.views.reject-reading-collection
it("rejects invalid roles, a non-module entry and definitions outside implementation documents", () => {
  const topic = "specs/transfer/requirements.md";
  for (const role of [null, "unknown", "topic", 1])
    for (const path of [topic, "specs/transfer/module.md"]) {
      const original = read(project, path + ".json");
      updateMetadata(project, path, (m) => (m.document.role = role));
      expect(load).toThrow(/Invalid document.role/);
      put(project, path + ".json", original);
    }
  updateMetadata(project, "specs/ledger/module.md", (m) => {
    m.document.role = "implementation";
  });
  expect(load).toThrow(/module.md must have document.role module/);
  updateMetadata(project, "specs/ledger/module.md", (m) => {
    m.document.role = "module";
  });
  updateMetadata(project, topic, (m) => (m.document.role = "module"));
  expect(load).toThrow(/belong in an implementation-role document/);
  updateMetadata(project, topic, (m) => {
    m.document.role = "implementation";
    m.defines.push({
      id: "concept.transfer.submission",
      type: "concept",
      title: "Submission",
      meaning: "#req.transfer.single",
    });
  });
  expect(load).toThrow(/Concepts are defined only in module-role documents/);
  updateMetadata(project, topic, (m) => m.defines.pop());
});

// verifies: scenario.views.reject-reading-collection
it("requires the four entry sections exactly once, in any order, and no Relationships section", () => {
  const path = "specs/ledger/module.md";
  const original = read(project, path);
  for (const invalid of [
    original.replace("## Purpose", "### Purpose"),
    original.replace("## Usage", "## Use"),
    original + "\n## Design\n\nAgain.\n",
  ]) {
    put(project, path, invalid);
    expect(load).toThrow(
      /Purpose, Terminology, Usage, Design, each exactly once/,
    );
  }
  put(project, path, original + "\n## Relationships\n\nThe parts.\n");
  expect(load).toThrow(/relationships belong in its Design/);
  put(
    project,
    path,
    original.replace(
      /## Usage([\s\S]*)## Design([\s\S]*)$/,
      "## Design$2## Usage$1",
    ),
  );
  expect(load).not.toThrow();
  put(project, path, original + "\n## Open questions\n\nNone.\n");
  expect(load).not.toThrow();
});

// verifies: scenario.views.reject-reading-collection
it("requires import rows to link their concept's defining document", () => {
  const path = "specs/audit/module.md";
  const original = read(project, path);
  for (const href of [
    "../transfer/requirements.md#concept.transfer.hold",
    "../transfer/module.md#concept.transfer.missing",
  ]) {
    put(
      project,
      path,
      original.replace("../transfer/module.md#concept.transfer.hold", href),
    );
    expect(load).toThrow(/Terminology import row/);
  }
});

// verifies: scenario.views.reading-collections
it("builds both reading paths from the contains tree without repeating a document", () => {
  const registry = load();
  const reading = scopedSidebar(registry) as SidebarItem[];
  expect(reading).toEqual([
    {
      type: "category",
      label: "Bank",
      link: { type: "doc", id: "bank/module" },
      collapsed: false,
      items: [
        {
          type: "category",
          label: "Transfer",
          link: { type: "doc", id: "transfer/module" },
          collapsed: true,
          items: [{ type: "doc", id: "ledger/module", label: "Ledger" }],
        },
        { type: "doc", id: "audit/module", label: "Audit" },
      ],
    },
  ]);
  const implementation = scopedSidebar(registry, "implementation");
  expect(implementation).toEqual([
    {
      type: "category",
      label: "Bank",
      collapsed: false,
      items: [
        {
          type: "category",
          label: "Transfer",
          collapsed: true,
          items: [
            { type: "doc", id: "transfer/requirements", label: "requirements" },
          ],
        },
      ],
    },
  ]);
  const ids = [...docs(reading), ...docs(implementation)];
  expect(ids.sort()).toEqual(
    registry.pages.map((p) => p.stagedPath.replace(/\.md$/, "")).sort(),
  );
});

// verifies: scenario.views.reading-collections
it("orders topics by owns and children by contains, labelling topics by file name", () => {
  const topic = "specs/transfer/elsewhere/notes.md";
  record("module.transfer").owns.splice(1, 0, topic);
  record("module.bank").contains.reverse();
  putDocument(project, topic, {
    owner: "module.transfer",
    body: "# An unrelated heading\n\nNotes on transfers.\n",
  });
  writeRegistry(project);
  const sidebar = scopedSidebar(load());
  expect(sidebar[0].items!.map((item) => item.label)).toEqual([
    "Audit",
    "Transfer",
  ]);
  expect(sidebar[0].items![1].items).toEqual([
    { type: "doc", id: "transfer/elsewhere/notes", label: "notes" },
    { type: "doc", id: "ledger/module", label: "Ledger" },
  ]);
});

// verifies: scenario.views.reading-collections
it("changing a document's role moves it between reading paths without changing its route", () => {
  const path = "specs/transfer/requirements.md";
  const before = load();
  updateMetadata(project, path, (m) => (m.document.role = "module"));
  put(project, path, "# Transfer requirements\n\nExplanation only.\n");
  const after = load();
  expect(after.sourceDigest).not.toBe(before.sourceDigest);
  expect(after.pages.map((p) => p.route)).toEqual(
    before.pages.map((p) => p.route),
  );
  expect(scopedSidebar(after, "implementation")).toEqual([]);
  expect(docs(scopedSidebar(after))).toContain("transfer/requirements");
});

// verifies: scenario.views.publish-reference-link
it("rewrites registered links to canonical routes and leaves code examples intact", () => {
  const path = "specs/audit/module.md";
  put(
    project,
    path,
    read(project, path) +
      "\nSee [the rule](../transfer/requirements.md#req.transfer.single) and [Bank](../bank/module.md?view=compact).\n\n```md\n[Example](unknown.md)\n```\n",
  );
  const registry = load();
  const audit = registry.pages.find((p) => p.sourcePath === path)!;
  const rewritten = rewriteLinks(registry, audit);
  expect(rewritten).toContain(
    "[the rule](/specs/transfer/requirements#req.transfer.single)",
  );
  expect(rewritten).toContain("[Bank](/specs/bank/module?view=compact)");
  expect(rewritten).toContain("[Example](unknown.md)");
  audit.content += "\n[Wrong](unknown.md?view=compact#x)";
  expect(() => rewriteLinks(registry, audit)).toThrow(
    "Unregistered local link: specs/audit/module.md -> unknown.md?view=compact#x",
  );
});

// verifies: scenario.views.materialize
it("source lookup preserves query and fragment suffixes", async () => {
  const links = [
    [
      "../transfer/requirements.md?view=compact#scenario.transfer.submit",
      "/specs/transfer/requirements?view=compact#scenario.transfer.submit",
    ],
    ["?view=compact", "/specs/audit/module?view=compact"],
    ["?view=compact#purpose", "/specs/audit/module?view=compact#purpose"],
    [
      "../transfer/module.md?next=a?b#usage",
      "/specs/transfer/module?next=a?b#usage",
    ],
    ["../transfer/module.md?#", "/specs/transfer/module?#"],
    [
      "https://example.com/page?view=compact#x",
      "https://example.com/page?view=compact#x",
    ],
    [
      "mailto:reader@example.com?subject=Read",
      "mailto:reader@example.com?subject=Read",
    ],
    ["/specs/transfer/module#usage", "/specs/transfer/module#usage"],
    ["#purpose?detail", "#purpose?detail"],
  ];
  const unchanged =
    "[Reference][rule]\n\n[rule]: ../transfer/requirements.md#req.transfer.single";
  const path = "specs/audit/module.md";
  put(
    project,
    path,
    read(project, path) +
      "\n" +
      links.map(([url], i) => `[Link ${i}](${url})`).join("\n") +
      "\n\n" +
      unchanged +
      "\n",
  );
  const original = readFileSync(resolve(project.root, path));
  const registry = load();
  await materializeScoped(registry);
  const staged = read(
    project,
    "docsite/.generated/content/specs/audit/module.md",
  );
  for (const [, destination] of links)
    expect(staged).toContain(`](${destination})`);
  expect(staged).toContain(unchanged);
  expect(readFileSync(resolve(project.root, path))).toEqual(original);
});

// verifies: scenario.views.materialize
it("an unregistered link fails materialization and leaves no identity", async () => {
  await materializeScoped(load());
  const path = "specs/audit/module.md";
  put(
    project,
    path,
    read(project, path) + "\n[Unknown](unknown.md?view=compact)\n",
  );
  await expect(materializeScoped(load())).rejects.toThrow(
    /Unregistered local link/,
  );
  expect(
    existsSync(
      resolve(project.root, "docsite/.generated/scoped-materialization.json"),
    ),
  ).toBe(false);
});

// verifies: scenario.views.materialize
it("stages every page with front matter and writes both sidebars", async () => {
  const registry = load();
  await materializeScoped(registry);
  const staged = (path: string) =>
    read(project, "docsite/.generated/content/specs/" + path);
  expect(staged("transfer/module.md")).toContain("title: Transfer\n");
  expect(staged("transfer/module.md")).toContain(
    "displayed_sidebar: moduleDocumentsSidebar",
  );
  expect(staged("transfer/requirements.md")).toContain("title: requirements\n");
  expect(staged("transfer/requirements.md")).toContain(
    "displayed_sidebar: implementationDocumentsSidebar",
  );
  for (const page of registry.pages)
    expect(staged(page.stagedPath)).toContain("toc_max_heading_level: 3\n");
  // Realization bindings stay in metadata; reading gains no file inventory.
  expect(staged("ledger/module.md")).not.toContain("src/ledger.ts");
  const sidebars = readJson(project, "docsite/.generated/specs-sidebar.json");
  expect(sidebars.moduleDocumentsSidebar).toEqual(scopedSidebar(registry));
  expect(sidebars.implementationDocumentsSidebar).toEqual(
    scopedSidebar(registry, "implementation"),
  );
  expect(
    readJson(project, "docsite/.generated/scoped-materialization.json"),
  ).toEqual({ schema_version: 2, sourceDigest: registry.sourceDigest });
});

it("omits the implementation sidebar when no document has that role", async () => {
  const path = "specs/transfer/requirements.md";
  record("module.transfer").owns.pop();
  writeRegistry(project);
  rmSync(resolve(project.root, path));
  rmSync(resolve(project.root, path + ".json"));
  await materializeScoped(load());
  expect(
    readJson(project, "docsite/.generated/specs-sidebar.json"),
  ).not.toHaveProperty("implementationDocumentsSidebar");
});

it("binds source identity to both members, the registry and the owns order", () => {
  const first = load().sourceDigest;
  const path = "specs/transfer/requirements.md";
  updateMetadata(project, path, (m) => (m.extensions = { "tool.note": 1 }));
  const metadataOnly = load();
  expect(metadataOnly.sourceDigest).not.toBe(first);
  expect(metadataOnly.pages[2].contentDigest).toBe(page(path).contentDigest);
  record("module.transfer").owns.reverse();
  writeRegistry(project);
  expect(load().sourceDigest).not.toBe(metadataOnly.sourceDigest);
});

it("rejects missing metadata, duplicate JSON keys, symlinks and malformed UTF-8", () => {
  const path = "specs/ledger/module.md";
  const metadata = read(project, path + ".json");
  rmSync(resolve(project.root, path + ".json"));
  expect(load).toThrow();
  put(
    project,
    path + ".json",
    metadata.replace(
      '"schema_version": 3',
      '"schema_version": 3, "schema_version": 3',
    ),
  );
  expect(load).toThrow(/Duplicate JSON key/);
  put(project, path + ".json", metadata);
  const reading = readFileSync(resolve(project.root, path));
  writeFileSync(
    resolve(project.root, path),
    Buffer.concat([reading, Buffer.from([255])]),
  );
  expect(load).toThrow();
  rmSync(resolve(project.root, path));
  symlinkSync(
    resolve(project.root, "specs/audit/module.md"),
    resolve(project.root, path),
  );
  expect(load).toThrow(/Symlink/);
});

it("never discovers unregistered Markdown", () => {
  put(project, "specs/ignored.md", "UNREGISTERED");
  put(project, "specs/ignored.md.json", "{}");
  const registry = load();
  expect(registry.pages).toHaveLength(5);
  expect(registry.pages.some((p) => p.content.includes("UNREGISTERED"))).toBe(
    false,
  );
});

it("strips the specs/ route prefix only when every document is under it", () => {
  const outside = "docs/outside.md";
  project.modules.push(module("module.outside", "Outside", "docs/module.md"));
  record("module.outside").owns.push(outside);
  record("module.bank").contains.push({
    target: "module.outside",
    meaning: "#contains-audit",
  });
  putDocument(project, "docs/module.md", {
    owner: "module.outside",
    body: entryBody("Outside"),
  });
  putDocument(project, outside, {
    owner: "module.outside",
    body: "# Outside\n\nNot under specs.\n",
  });
  writeRegistry(project);
  const registry = load();
  expect(registry.pages.find((p) => p.sourcePath === outside)!.route).toBe(
    "/specs/docs/outside",
  );
  expect(
    registry.pages.find((p) => p.sourcePath === "specs/bank/module.md")!.route,
  ).toBe("/specs/specs/bank/module");
});
