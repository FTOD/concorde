import { existsSync, rmSync } from "node:fs";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
  DiagramSourceError,
  edgeReference,
  parseDiagramSource,
  reference,
} from "../../plugins/scoped-content/diagram-source";
import {
  d2Program,
  renderDiagrams,
  styledDiagramInput,
} from "../../plugins/scoped-content/diagrams";
import { loadScopedRegistry } from "../../plugins/scoped-content/model";
import { materializeScoped } from "../../plugins/scoped-content/materialize";
import {
  ILLUSTRATIVE_LABEL,
  renderPage,
} from "../../plugins/scoped-content/render";
import { bankProject, put, read } from "../protocol-fixture";

function refused(source: string): DiagramSourceError {
  try {
    parseDiagramSource(source);
  } catch (error) {
    expect(error).toBeInstanceOf(DiagramSourceError);
    return error as DiagramSourceError;
  }
  throw new Error("expected parseDiagramSource to throw");
}

describe("D2 diagram source parsing", () => {
  it("nests shapes under a parent and keeps the nearest label per key", () => {
    const parsed = parseDiagramSource(
      ["bank: Bank {", "  transfer: Transfer", "  ledger", "}"].join("\n"),
    );
    expect(
      parsed.shapes.map((s) => ({ path: s.path, label: s.label })),
    ).toEqual([
      { path: ["bank"], label: "Bank" },
      { path: ["bank", "transfer"], label: "Transfer" },
      { path: ["bank", "ledger"], label: "ledger" },
    ]);
  });

  it("draws edges between dotted key paths and records a label", () => {
    const parsed = parseDiagramSource(
      [
        "bank: Bank {",
        "  transfer: Transfer",
        "}",
        "bank.transfer -> audit: reviews",
      ].join("\n"),
    );
    expect(parsed.edges).toHaveLength(1);
    const [edge] = parsed.edges;
    expect(edge.src).toEqual(["bank", "transfer"]);
    expect(edge.dst).toEqual(["audit"]);
    expect(edge.label).toBe("reviews");
    expect(edge.scope).toEqual([]);
    expect(edge.index).toBe(0);
    // A repeated edge between the same two ends is counted, as D2 does.
    const repeated = parseDiagramSource(["a -> b", "a -> b: again"].join("\n"));
    expect(repeated.edges.map((e) => e.index)).toEqual([0, 1]);
  });

  it("treats a quoted key as one segment even when it contains a dot", () => {
    const parsed = parseDiagramSource('"a.b": Weird Key\n"a.b" -> c');
    expect(parsed.shapes[0]).toMatchObject({
      path: ["a.b"],
      label: "Weird Key",
    });
    expect(parsed.edges[0].src).toEqual(["a.b"]);
    expect(parsed.edges[0].dst).toEqual(["c"]);
  });

  it("formats shape and edge references with quoted keys and per-scope indices", () => {
    expect(reference(["bank", "audit team"])).toBe('"bank"."audit team"');
    const parsed = parseDiagramSource(
      [
        "bank: Bank {",
        "  transfer: Transfer",
        "  ledger: Ledger",
        "  transfer -> ledger",
        "  transfer -> ledger: repeats",
        "}",
      ].join("\n"),
    );
    const [first, second] = parsed.edges;
    expect(edgeReference(first)).toBe('"bank".("transfer" -> "ledger")[0]');
    expect(edgeReference(second)).toBe('"bank".("transfer" -> "ledger")[1]');
  });

  it("refuses a style keyword, naming its line", () => {
    const error = refused('a: A {\n  style.fill: "red"\n}');
    expect(error.line).toBe(2);
    expect(error.reason).toMatch(/style/);
  });

  it("refuses the direction keyword", () => {
    const error = refused("direction: right");
    expect(error.line).toBe(1);
    expect(error.reason).toMatch(/direction/);
  });

  it("refuses an undirected arrow", () => {
    const error = refused("a <- b");
    expect(error.line).toBe(1);
    expect(error.reason).toMatch(/has no declared direction/);
  });

  it("refuses an unclosed block, pointing past the last line", () => {
    const error = refused("a: A {\n  b: B");
    expect(error.line).toBe(2);
    expect(error.reason).toMatch(/is not closed/);
  });
});

describe("scenario.views.diagram-style", () => {
  // verifies: scenario.views.diagram-style
  it("classifies shapes and edges from what their labels name, without running d2", () => {
    const project = bankProject();
    try {
      const registry = loadScopedRegistry(project.root);
      const page = registry.pages.find(
        (p) => p.sourcePath === "specs/transfer/module.md",
      )!;
      const source = [
        "transfer: Transfer {",
        "  ledger: Ledger",
        "}",
        "hold: Hold",
        "service: Transfer service {",
        "  entry: src/transfer/index.ts",
        "}",
        "transfer -> transfer.ledger",
        "transfer -> transfer.ledger: refers",
        "transfer.ledger -> hold",
        "service -> hold: records",
      ].join("\n");
      const input = styledDiagramInput(registry, page, source);
      // The source is carried through unchanged; only class declarations are appended.
      expect(input).toContain(source);
      // The page's own Module, a descendant Module, a concept and a realization each classify
      // from what they name, relative to the page's owner (Transfer).
      expect(input).toContain('"transfer".class: owner');
      expect(input).toContain('"transfer"."ledger".class: module');
      expect(input).toContain('"hold".class: concept');
      expect(input).toContain('"service".class: realization-files');
      // A file nested in a realization gets no class of its own: it becomes a table row.
      expect(input).not.toMatch(/"service"\."entry".*\.class:/);
      // An unlabelled edge between two Modules is "uses"...
      expect(input).toContain(
        '("transfer" -> "transfer"."ledger")[0].class: uses',
      );
      // ...but the identical edge with a label is "relates", even though both ends are Modules.
      expect(input).toContain(
        '("transfer" -> "transfer"."ledger")[1].class: relates',
      );
      // An edge that touches a concept or a realization is always "relates".
      expect(input).toContain(
        '("transfer"."ledger" -> "hold")[0].class: relates',
      );
      expect(input).toContain('("service" -> "hold")[0].class: relates');
    } finally {
      rmSync(project.root, { recursive: true, force: true });
    }
  });

  // verifies: scenario.views.diagram-style
  it("renders a checked diagram to a staged SVG the page references", async () => {
    const project = bankProject();
    try {
      const registry = loadScopedRegistry(project.root);
      const page = registry.pages.find(
        (p) => p.sourcePath === "specs/bank/module.md",
      )!;
      const staged = resolve(
        project.root,
        "docsite/.generated/content/specs/bank/module.md",
      );
      await mkdir(dirname(staged), { recursive: true });
      const out = await renderDiagrams(
        registry,
        page,
        renderPage(registry, page),
        staged,
      );
      const match =
        /!\[Diagram 1 of Bank\]\(\.\/(module\.diagram-1-[0-9a-f]{12}\.svg)\)/.exec(
          out,
        );
      expect(match).not.toBeNull();
      const svgPath = resolve(dirname(staged), match![1]);
      expect(existsSync(svgPath)).toBe(true);
      expect(await readFile(svgPath, "utf8")).toContain("<svg");
    } finally {
      await rm(project.root, { recursive: true, force: true });
    }
  });
});

describe("scenario.views.diagram-subset-refused", () => {
  // verifies: scenario.views.diagram-subset-refused
  it("fails naming the document and line when a checked block sets its own look", async () => {
    const project = bankProject();
    try {
      const path = "specs/bank/module.md";
      put(
        project,
        path,
        read(project, path) +
          '\n```d2\nfoo: Foo {\n  style.fill: "#fff"\n}\n```\n',
      );
      const registry = loadScopedRegistry(project.root);
      await expect(materializeScoped(registry)).rejects.toThrow(
        /specs\/bank\/module\.md:\d+ is outside the semantic subset: 'style'/,
      );
    } finally {
      await rm(project.root, { recursive: true, force: true });
    }
  });
});

describe("scenario.views.d2-missing", () => {
  const originalD2 = process.env.CONCORDE_D2;
  afterEach(() => {
    if (originalD2 === undefined) delete process.env.CONCORDE_D2;
    else process.env.CONCORDE_D2 = originalD2;
  });

  // verifies: scenario.views.d2-missing
  it("fails naming the diagram and how to install the program", async () => {
    const project = bankProject();
    try {
      process.env.CONCORDE_D2 = resolve(project.root, "no-such-d2-program");
      const registry = loadScopedRegistry(project.root);
      await expect(materializeScoped(registry)).rejects.toThrow(
        /Cannot render the D2 diagram at specs\/bank\/module\.md:\d+: the program '.*no-such-d2-program' was not found; run the Concorde installer, which places d2 at \.concorde\/tools\/d2, or install the d2 program from https:\/\/github\.com\/d2lang\/d2\/releases/,
      );
    } finally {
      await rm(project.root, { recursive: true, force: true });
    }
  });

  // verifies: scenario.views.d2-program
  it("prefers CONCORDE_D2, then the installer's copy, then d2 on PATH", async () => {
    const project = bankProject();
    try {
      delete process.env.CONCORDE_D2;
      expect(d2Program(project.root)).toBe("d2");
      const installed = resolve(project.root, ".concorde/tools/d2");
      await mkdir(dirname(installed), { recursive: true });
      await writeFile(installed, "");
      expect(d2Program(project.root)).toBe(installed);
      process.env.CONCORDE_D2 = "/opt/d2";
      expect(d2Program(project.root)).toBe("/opt/d2");
    } finally {
      await rm(project.root, { recursive: true, force: true });
    }
  });
});

describe("scenario.views.illustrative-label", () => {
  // verifies: scenario.views.illustrative-label
  it("labels an illustrative diagram and leaves a checked one unlabeled", async () => {
    const project = bankProject();
    try {
      const path = "specs/bank/module.md";
      put(
        project,
        path,
        read(project, path) +
          "\n```d2 illustrative\ndirection: right\nOwner -> Transfer: submit over time\n```\n",
      );
      const registry = loadScopedRegistry(project.root);
      const page = registry.pages.find((p) => p.sourcePath === path)!;
      const staged = resolve(
        project.root,
        "docsite/.generated/content/specs/bank/module.md",
      );
      await mkdir(dirname(staged), { recursive: true });
      const out = await renderDiagrams(
        registry,
        page,
        renderPage(registry, page),
        staged,
      );
      expect(out).toContain("![Diagram 1 of Bank]");
      expect(out).toContain(ILLUSTRATIVE_LABEL + "\n\n![Diagram 2 of Bank]");
      // Diagram 1 is checked, so nothing before it carries the illustrative label.
      expect(out.slice(0, out.indexOf("![Diagram 1 of Bank]"))).not.toContain(
        ILLUSTRATIVE_LABEL,
      );
    } finally {
      await rm(project.root, { recursive: true, force: true });
    }
  });
});
