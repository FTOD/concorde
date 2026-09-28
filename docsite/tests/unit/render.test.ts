import { rmSync } from "node:fs";
import { afterEach, beforeEach, expect, it } from "vitest";
import { loadScopedRegistry } from "../../plugins/scoped-content/model";
import {
  ILLUSTRATIVE_LABEL,
  renderPage,
} from "../../plugins/scoped-content/render";
import { bankProject, put, read, type Project } from "../protocol-fixture";

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
it("keeps an entry without a title heading addressable", () => {
  const path = "specs/ledger/module.md";
  put(project, path, read(project, path).replace("# Ledger\n\n", ""));
  expect(
    render(path).startsWith(
      '<a id="module.ledger"></a><a id="document.ledger.module"></a>\n\n## Purpose',
    ),
  ).toBe(true);
});

// verifies: scenario.views.illustrative-label
it("leaves d2 blocks untouched by renderPage, which never renders diagrams itself", () => {
  const path = "specs/bank/module.md";
  const illustrative =
    "```d2 illustrative\ndirection: right\nOwner -> Transfer: submit\n```";
  put(project, path, read(project, path) + "\n" + illustrative + "\n");
  const bank = render(path);
  // Diagram rendering, and the illustrative label it adds, belong to renderDiagrams; renderPage
  // passes every d2 fence through as written, checked or illustrative alike.
  expect(bank).toContain(illustrative);
  expect(bank).toContain("```d2\nbank: Bank {\n  transfer: Transfer\n}\n```");
  expect(bank).not.toContain(ILLUSTRATIVE_LABEL);
  expect(ILLUSTRATIVE_LABEL).toContain("Illustrative, non-normative.");
});

// verifies: scenario.views.load-registry-refused
it("rejects any Mermaid block, wherever it is marked", () => {
  const path = "specs/bank/module.md";
  const original = read(project, path);
  for (const mermaid of [
    "```mermaid\nsequenceDiagram\n    A->>B: go\n```",
    "```mermaid illustrative\nsequenceDiagram\n    A->>B: go\n```",
    "```mermaid\nflowchart LR\n    A --> B\n```",
  ]) {
    put(project, path, original + "\n" + mermaid + "\n");
    expect(() => loadScopedRegistry(project.root)).toThrow(
      /Mermaid block .* is not part of reading; rewrite it as a `d2` block or a `d2 illustrative` block/,
    );
  }
  put(
    project,
    path,
    original +
      "\n````markdown\n```mermaid\nsequenceDiagram\n    A->>B: quoted\n```\n````\n",
  );
  expect(() => loadScopedRegistry(project.root)).not.toThrow();
});
