import { rmSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  loadScopedRegistry,
  rewriteLinks,
} from "../../plugins/scoped-content/model";
import {
  materializeScoped,
  scopedSidebar,
} from "../../plugins/scoped-content/materialize";
import { renderGlossaryPage } from "../../plugins/scoped-content/glossary";
import { renderPage } from "../../plugins/scoped-content/render";
import {
  bankProject,
  glossaryFile,
  glossaryPath,
  put,
  read,
  writeRegistry,
  type Project,
} from "../protocol-fixture";

let project: Project;
const load = () => loadScopedRegistry(project.root);
const record = (id: string) => project.modules.find((m) => m.id === id)!;
beforeEach(() => {
  project = bankProject();
});
afterEach(() => rmSync(project.root, { recursive: true, force: true }));

describe("loading the project glossary", () => {
  // verifies: scenario.views.load-registry
  it("loads the concept the root Module's glossary declares", () => {
    const registry = load();
    expect(registry.glossary).toMatchObject({
      path: glossaryPath,
      owner: "module.bank",
      stagedPath: "bank/glossary.md",
      route: "/specs/bank/glossary",
    });
    expect(registry.glossary!.concepts).toEqual([
      {
        id: "concept.transfer.hold",
        title: "Hold",
        owner: "module.transfer",
        definition: "Money withheld until a transfer settles.",
        explanation: "specs/transfer/module.md#concept.transfer.hold",
      },
    ]);
    // Concepts are glossary entries now: `nodes` holds only metadata-declared realizations.
    expect(registry.nodes.map((n) => [n.id, n.type])).toEqual([
      ["realization.transfer.service", "realization"],
      ["realization.ledger.book", "realization"],
    ]);
  });

  // verifies: scenario.views.load-registry
  it("is null when no Module declares one", () => {
    delete record("module.bank").glossary;
    delete record("module.audit").uses[0].relies_on;
    writeRegistry(project);
    expect(load().glossary).toBeNull();
  });
});

describe("refused glossaries", () => {
  // verifies: scenario.views.load-registry-refused
  it("refuses malformed glossary JSON", () => {
    put(project, glossaryPath, "{not json");
    expect(load).toThrow(/Invalid JSON in specs\/bank\/glossary\.json/);
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses a missing glossary file", () => {
    rmSync(resolve(project.root, glossaryPath));
    expect(load).toThrow(/specs\/bank\/glossary\.json/);
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses an invalid glossary schema", () => {
    for (const invalid of [
      JSON.stringify({ schema_version: 2, concepts: [] }),
      JSON.stringify({ schema_version: 1, concepts: {} }),
      JSON.stringify({ schema_version: 1, concepts: [], extra: true }),
    ]) {
      put(project, glossaryPath, invalid);
      expect(load).toThrow(/Invalid glossary schema/);
    }
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses a duplicate concept id", () => {
    put(
      project,
      glossaryPath,
      glossaryFile([
        {
          id: "concept.transfer.hold",
          title: "Hold",
          owner: "module.transfer",
          definition: "Money withheld until a transfer settles.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
        {
          id: "concept.transfer.hold",
          title: "Hold again",
          owner: "module.transfer",
          definition: "A second entry.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
      ]),
    );
    expect(load).toThrow(/Duplicate identity: concept\.transfer\.hold/);
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses a concept owner that is not a registered Module", () => {
    put(
      project,
      glossaryPath,
      glossaryFile([
        {
          id: "concept.transfer.hold",
          title: "Hold",
          owner: "module.unknown",
          definition: "Money withheld until a transfer settles.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
      ]),
    );
    expect(load).toThrow(/Concept owner is not a registered Module/);
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses a duplicate concept title", () => {
    put(
      project,
      glossaryPath,
      glossaryFile([
        {
          id: "concept.transfer.a",
          title: "Hold",
          owner: "module.transfer",
          definition: "First.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
        {
          id: "concept.transfer.b",
          title: "Hold",
          owner: "module.transfer",
          definition: "Second.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
      ]),
    );
    expect(load).toThrow(/Duplicate concept title: Hold/);
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses concepts out of id order", () => {
    put(
      project,
      glossaryPath,
      glossaryFile([
        {
          id: "concept.transfer.z",
          title: "Zed",
          owner: "module.transfer",
          definition: "Last alphabetically but written first.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
        {
          id: "concept.transfer.hold",
          title: "Hold",
          owner: "module.transfer",
          definition: "Money withheld until a transfer settles.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
      ]),
    );
    expect(load).toThrow(/Glossary concepts must be sorted by id/);
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses an explanation that is not a module document the owner owns", () => {
    for (const explanation of [
      "specs/audit/module.md#uses-transfer",
      "specs/transfer/requirements.md#req.transfer.single",
      "specs/transfer/module.md#no-such-anchor",
    ]) {
      put(
        project,
        glossaryPath,
        glossaryFile([
          {
            id: "concept.transfer.hold",
            title: "Hold",
            owner: "module.transfer",
            definition: "Money withheld until a transfer settles.",
            explanation,
          },
        ]),
      );
      expect(load).toThrow();
    }
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses a glossary declared by a Module with a parent", () => {
    delete record("module.bank").glossary;
    record("module.transfer").glossary = glossaryPath;
    writeRegistry(project);
    expect(load).toThrow(
      /Only a Module without a parent may declare a glossary: module\.transfer/,
    );
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses more than one Module declaring a glossary", () => {
    record("module.audit").glossary = "specs/audit/glossary.json";
    writeRegistry(project);
    expect(load).toThrow(/At most one Module may declare a glossary/);
  });

  // verifies: scenario.views.load-registry-refused
  it("refuses a fragment-only term link inside a definition naming an unknown concept", () => {
    put(
      project,
      glossaryPath,
      glossaryFile([
        {
          id: "concept.transfer.hold",
          title: "Hold",
          owner: "module.transfer",
          definition: "See [wire](#concept.transfer.unknown).",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
        },
      ]),
    );
    expect(load).toThrow(/Unknown glossary term in the definition/);
  });
});

describe("term links", () => {
  // verifies: scenario.views.publish-reference-link, scenario.views.term-links
  it("rewrites a term link to the glossary page anchor", () => {
    const registry = load();
    const audit = registry.pages.find(
      (p) => p.sourcePath === "specs/audit/module.md",
    )!;
    expect(rewriteLinks(registry, audit)).toContain(
      "[holds](/specs/bank/glossary#concept.transfer.hold)",
    );
  });

  // verifies: scenario.views.publish-reference-link, scenario.views.term-links
  it("rewrites a bare link to the glossary file, without a fragment, to the glossary page", () => {
    const registry = load();
    const bank = registry.pages.find(
      (p) => p.sourcePath === "specs/bank/module.md",
    )!;
    expect(rewriteLinks(registry, bank)).toContain(
      "[glossary](/specs/bank/glossary)",
    );
  });

  it("refuses a term link to a concept the glossary does not declare", () => {
    const path = "specs/audit/module.md";
    put(
      project,
      path,
      read(project, path).replace(
        "concept.transfer.hold",
        "concept.transfer.unknown",
      ),
    );
    const registry = load();
    const audit = registry.pages.find((p) => p.sourcePath === path)!;
    expect(() => rewriteLinks(registry, audit)).toThrow(
      /Unknown glossary term: specs\/audit\/module\.md -> \.\.\/bank\/glossary\.json#concept\.transfer\.unknown/,
    );
  });
});

describe("the glossary page", () => {
  // verifies: scenario.views.glossary-page
  it("lists every concept with its owner and explanation", () => {
    const registry = load();
    const page = renderGlossaryPage(registry);
    expect(page).toContain("### Hold {#concept.transfer.hold}");
    expect(page).toContain("Money withheld until a transfer settles.");
    expect(page).toContain("Owned by [Transfer](/specs/transfer/module).");
    expect(page).toContain(
      "[Explained in Transfer](/specs/transfer/module#concept.transfer.hold).",
    );
  });

  // verifies: scenario.views.glossary-page
  it("groups the root's terms first, then each contained Module's subtree, after an A-Z index", () => {
    const registry = load();
    const hold = registry.glossary!.concepts[0];
    const concept = (id: string, title: string, owner: string) => ({
      ...hold,
      id,
      title,
      owner,
    });
    registry.glossary!.concepts = [
      concept("concept.audit.trail", "Trail", "module.audit"),
      concept("concept.bank.account", "account", "module.bank"),
      concept("concept.ledger.entry", "Entry", "module.ledger"),
      hold,
      concept("concept.transfer.batch", "Batch", "module.transfer"),
    ];
    const page = renderGlossaryPage(registry);
    const at = (text: string) => {
      expect(page).toContain(text);
      return page.indexOf(text);
    };
    const order = [
      at("## Index {#terms.index}"),
      at(
        "**A** · [account](#concept.bank.account)\n\n**B** · [Batch](#concept.transfer.batch)",
      ),
      at("**E** · [Entry](#concept.ledger.entry)\n\n**H** · [Hold]"),
      at("## Core terms {#terms.module.bank}"),
      at("### account {#concept.bank.account}"),
      at("## Transfer {#terms.module.transfer}"),
      at(
        "Terms owned by [Transfer](/specs/transfer/module) or a Module it contains.",
      ),
      at("### Batch {#concept.transfer.batch}"),
      // Ledger sits under Transfer, so its term joins Transfer's group, sorted by title.
      at("### Entry {#concept.ledger.entry}"),
      at("### Hold {#concept.transfer.hold}"),
      at("## Audit {#terms.module.audit}"),
      at("### Trail {#concept.audit.trail}"),
    ];
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(page).toContain("Owned by [Ledger](/specs/ledger/module).");
    expect(page).not.toContain("## Ledger");
  });

  it("shows a retired concept's reason and an external conflict note", () => {
    put(
      project,
      glossaryPath,
      glossaryFile([
        {
          id: "concept.transfer.hold",
          title: "Hold",
          owner: "module.transfer",
          definition: "Money withheld until a transfer settles.",
          explanation: "specs/transfer/module.md#concept.transfer.hold",
          retired: { reason: "superseded by Reservation" },
          external_conflict: "a different meaning in the payment SDK",
        },
      ]),
    );
    const page = renderGlossaryPage(load());
    expect(page).toContain("*Retired: superseded by Reservation*");
    expect(page).toContain(
      "*Conflicts with an external usage: a different meaning in the payment SDK*",
    );
  });

  // verifies: scenario.views.materialize
  it("is materialized as its own staged page and added to the navigation", async () => {
    const registry = load();
    await materializeScoped(registry);
    const staged = read(
      project,
      "docsite/.generated/content/specs/bank/glossary.md",
    );
    expect(staged).toContain("title: Glossary");
    expect(staged).toContain("### Hold {#concept.transfer.hold}");
    expect(staged).toContain("toc_max_heading_level: 2");
    const sidebar = scopedSidebar(registry);
    expect(sidebar[0].items).toEqual(
      expect.arrayContaining([
        { type: "doc", id: "bank/glossary", label: "Glossary" },
      ]),
    );
  });
});

describe("terms shown on a Module's entry page", () => {
  // verifies: scenario.views.glossary-page
  it("lists the terms a Module owns, linking to the glossary", () => {
    const registry = load();
    const transfer = registry.pages.find(
      (p) => p.sourcePath === "specs/transfer/module.md",
    )!;
    const rendered = renderPage(registry, transfer);
    expect(rendered).toContain("## Terms");
    expect(rendered).toContain(
      "- [Hold](/specs/bank/glossary#concept.transfer.hold)",
    );
  });

  it("omits the Terms section for a Module that owns no concepts", () => {
    const registry = load();
    const audit = registry.pages.find(
      (p) => p.sourcePath === "specs/audit/module.md",
    )!;
    expect(renderPage(registry, audit)).not.toContain("## Terms");
  });
});
