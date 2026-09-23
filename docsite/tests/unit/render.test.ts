import { rmSync } from "node:fs";
import { afterEach, beforeEach, expect, it } from "vitest";
import { loadScopedRegistry } from "../../plugins/scoped-content/model";
import { materializeScoped } from "../../plugins/scoped-content/materialize";
import {
  ILLUSTRATIVE_LABEL,
  renderPage,
} from "../../plugins/scoped-content/render";
import {
  bankProject,
  put,
  read,
  table,
  updateMetadata,
  type Project,
} from "../protocol-fixture";

let project: Project;
const render = (path: string) => {
  const registry = loadScopedRegistry(project.root);
  return renderPage(
    registry,
    registry.pages.find((p) => p.sourcePath === path)!,
  );
};
const anchors = (text: string) =>
  [...text.matchAll(/<a id="([^"]+)"><\/a>|\{#([^{}]+)\}/g)].map(
    (m) => m[1] ?? m[2],
  );
beforeEach(() => {
  project = bankProject();
});
afterEach(() => rmSync(project.root, { recursive: true, force: true }));

// verifies: scenario.views.id-anchors
it("exposes every stable identity of a page exactly once", () => {
  const entry = render("specs/transfer/module.md");
  const ids = anchors(entry);
  for (const id of [
    "module.transfer",
    "document.transfer.module",
    "concept.transfer.hold",
    "realization.transfer.service",
    "transfer-service",
    "contains-ledger",
  ])
    expect(
      ids.filter((anchor) => anchor === id),
      id,
    ).toHaveLength(1);
  // Page identities follow the title so the title stays the page heading.
  expect(entry.startsWith("# Transfer\n\n")).toBe(true);
  expect(entry).toContain(
    '<a id="transfer-service"></a><a id="realization.transfer.service"></a>',
  );
  const details = render("specs/transfer/requirements.md");
  expect(anchors(details)).toEqual([
    "document.transfer.requirements",
    "req.transfer.single",
    "scenario.transfer.submit",
    "contract.transfer.submit",
  ]);
  expect(details).toContain(
    "### One transfer per submission {#req.transfer.single}",
  );
  expect(details).toContain(
    "### Successful submission {#scenario.transfer.submit}",
  );
  expect(details).toContain(
    '<a id="contract.transfer.submit"></a>\n\n```concorde-contract',
  );
  expect(details).not.toContain('id="module.transfer"');
});

// verifies: scenario.views.id-anchors
it("anchors a concept at its defining row when its explanation uses another anchor", () => {
  const path = "specs/transfer/module.md";
  put(
    project,
    path,
    read(project, path).replace(
      '<a id="concept.transfer.hold"></a>',
      '<a id="holds-explained"></a>',
    ),
  );
  updateMetadata(project, path, (m) => {
    m.defines[0].meaning = "#holds-explained";
  });
  const entry = render(path);
  expect(entry).toContain(
    '| <a id="concept.transfer.hold"></a>Hold | Money withheld until a transfer settles. |',
  );
  expect(
    anchors(entry).filter((id) => id === "concept.transfer.hold"),
  ).toHaveLength(1);
});

// verifies: scenario.views.id-anchors
it("keeps an entry without a title heading addressable", () => {
  const path = "specs/ledger/module.md";
  put(project, path, read(project, path).replace("# Ledger\n\n", ""));
  expect(
    render(path).startsWith(
      '<a id="module.ledger"></a><a id="document.ledger.module"></a>\n\n## Purpose',
    ),
  ).toBe(true);
});

// verifies: scenario.views.import-definition
it("shows an imported definition with its owner and never writes it into the source", async () => {
  const path = "specs/audit/module.md";
  const source = read(project, path);
  const audit = render(path);
  expect(audit).toContain(
    "| [Hold](/specs/transfer/module#concept.transfer.hold) | Money withheld until a transfer settles. *Imported from [Transfer](/specs/transfer/module).* |",
  );
  await materializeScoped(loadScopedRegistry(project.root));
  expect(
    read(project, "docsite/.generated/content/specs/audit/module.md"),
  ).toContain("*Imported from [Transfer](/specs/transfer/module).*");
  expect(read(project, path)).toBe(source);
});

// verifies: scenario.views.import-definition
it("addresses links inside an imported definition from its owner's page", () => {
  const transfer = "specs/transfer/module.md";
  put(
    project,
    transfer,
    read(project, transfer).replace(
      "Money withheld until a transfer settles.",
      "Money withheld until a [transfer](requirements.md#scenario.transfer.submit) settles; see [usage](#usage).",
    ),
  );
  expect(render("specs/audit/module.md")).toContain(
    "Money withheld until a [transfer](/specs/transfer/requirements#scenario.transfer.submit) settles; see [usage](/specs/transfer/module#usage). *Imported from [Transfer](/specs/transfer/module).*",
  );
});

// verifies: scenario.views.import-definition
it("renders written definition cells and definitionless concepts as written", () => {
  const audit = "specs/audit/module.md";
  put(
    project,
    audit,
    read(project, audit).replace(
      "| [Hold](../transfer/module.md#concept.transfer.hold) |  |",
      "| [Hold](../transfer/module.md#concept.transfer.hold) | A copied definition. |",
    ),
  );
  expect(render(audit)).toContain(
    "| [Hold](/specs/transfer/module#concept.transfer.hold) | A copied definition. |",
  );
  const transfer = "specs/transfer/module.md";
  put(
    project,
    transfer,
    read(project, transfer).replace(
      table(["Hold", "Money withheld until a transfer settles."]),
      "Holds are explained below.",
    ),
  );
  put(
    project,
    audit,
    read(project, audit).replace(" A copied definition. ", " "),
  );
  expect(render(audit)).toContain(
    "| [Hold](/specs/transfer/module#concept.transfer.hold) | *Imported from [Transfer](/specs/transfer/module).* |",
  );
});

// verifies: scenario.views.illustrative-label
it("labels illustrative Mermaid as non-normative and leaves checked flowcharts as written", () => {
  const path = "specs/bank/module.md";
  const illustrative =
    "```mermaid illustrative\nsequenceDiagram\n    accTitle: A transfer over time\n    accDescr: Conceptual overview.\n    Owner->>Transfer: submit\n```";
  put(project, path, read(project, path) + "\n" + illustrative + "\n");
  const bank = render(path);
  expect(bank).toContain(
    ILLUSTRATIVE_LABEL +
      "\n\n```mermaid\nsequenceDiagram\n    accTitle: A transfer over time",
  );
  expect(bank).toContain(
    "```mermaid\nflowchart LR\n    Bank -->|contains| Transfer\n```",
  );
  expect(bank.match(/diagram-illustrative/g)).toHaveLength(1);
  expect(ILLUSTRATIVE_LABEL).toContain("Illustrative, non-normative.");
});

// verifies: scenario.views.illustrative-label
it("rejects an unmarked Mermaid block that is not a flowchart", () => {
  const path = "specs/bank/module.md";
  const original = read(project, path);
  put(
    project,
    path,
    original + "\n```mermaid\nsequenceDiagram\n    A->>B: go\n```\n",
  );
  expect(() => loadScopedRegistry(project.root)).toThrow(
    /neither a flowchart nor marked illustrative/,
  );
  put(
    project,
    path,
    original +
      "\n````markdown\n```mermaid\nsequenceDiagram\n    A->>B: quoted\n```\n````\n" +
      "\n```mermaid\n%% A comment first\ngraph TD\n    A -->|go| B\n```\n",
  );
  expect(() => loadScopedRegistry(project.root)).not.toThrow();
});
