import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, it, expect } from "vitest";
import { loadScopedRegistry } from "../../plugins/scoped-content/model";
const root = resolve(__dirname, "../../..");
describe("Explicit Concorde self specification", () => {
  // verifies: scenario.views.publish-homepage
  it("documents Pi-only adoption and terminal workers in the project homepage", () => {
    const { homepage } = JSON.parse(
      readFileSync(resolve(root, "docsite/site.json"), "utf8"),
    );
    expect(homepage.quickstart.description).toContain(
      "Pi is the only supported client",
    );
    expect(homepage.quickstart.code).toContain("scripts/concorde.py build");
    expect(homepage.quickstart.code).toContain("scripts/install-concorde.py");
    expect(homepage.quickstart.code).toContain(
      "--target /absolute/path/to/project --preview",
    );
    expect(homepage.quickstart.code).not.toContain("--integration");
    expect(homepage.quickstart.code).not.toMatch(/npx\s+skills/);
    const tables = homepage.reference.tables as Array<{
      title: string;
      description: string;
      rows: string[][];
    }>;
    const workers = tables.find(
      (table) => table.title === "Callable Pi Agents",
    )!;
    expect(workers.description).toContain("No Agent delegates tasks");
    expect(workers.description).toContain("rather than domain stage schemas");
    expect(workers.rows.flat().join(" ")).toContain("maintenance-worker");
    expect(workers.rows.flat().join(" ")).toContain("tester");
    expect(JSON.stringify(homepage)).not.toContain("18 Operations");
    const services = tables.find(
      (table) => table.title === "Shared execution services",
    )!;
    const distribution = services.rows.find(
      ([name]) => name === "Distribution",
    )![1];
    expect(distribution).toContain("private Pi catalog");
    expect(distribution).toContain(
      "No standalone Skills are published or installed",
    );
    const launchers = tables.find(
      (table) => table.title === "Launchers and supporting tools",
    )!;
    const cli = launchers.rows.find(
      ([name]) => name === "python3 scripts/concorde.py <command>",
    )![1];
    expect(cli).toContain("select-session");
    expect(cli).not.toContain("skills,");
    for (const workflow of [
      ".github/workflows/deploy-docsite.yml",
      "docsite/scaffold/deploy-docsite.yml",
    ]) {
      const source = readFileSync(resolve(root, workflow), "utf8");
      expect(source).toContain(
        "Build Concorde (Pi catalog, worker instructions, Protocol assets)",
      );
      expect(source).toContain("run: python3 scripts/concorde.py build");
    }
  });
  it("publishes every registered document exactly once and no ambient control/README source", () => {
    const r = loadScopedRegistry(root);
    expect(r.pages.map((p) => p.sourcePath)).toEqual([
      ...new Set(r.targets.flatMap((t) => t.documents)),
    ]);
    expect(
      r.pages.some(
        (p) =>
          p.sourcePath === "README.md" || p.sourcePath.startsWith(".concorde/"),
      ),
    ).toBe(false);
    expect(r.targets.some((t) => t.id === "module.protocol")).toBe(false);
    expect(
      r.pages.some(
        (p) =>
          p.sourcePath.startsWith("protocol/") ||
          p.sourcePath.startsWith("specs/concorde/protocol/"),
      ),
    ).toBe(false);
  });
  it("distinguishes Operation dispatch from conditional worker execution", () => {
    const registry = loadScopedRegistry(root);
    const entry = registry.pages.find(
      (page) => page.primaryOf === "module.operations",
    )!;
    const relationships = entry.content
      .split("## Relationships\n")[1]
      .split("\n## Local collaboration agreements")[0];
    expect(relationships).toContain('dispatch["Operation dispatch"]');
    expect(relationships).toContain(
      "harness -->|admits requests for| dispatch",
    );
    expect(relationships).toContain(
      "dispatch -->|selects requested| operations",
    );
    expect(entry.content).toContain(
      "no provider completion silently invokes a development or Spec-authoring workflow",
    );
    expect(entry.content).toContain("State carries data, not");
    expect(entry.content).toContain("execution authority");
    expect(relationships).not.toContain("runs admitted work through");
  });
  it("contains independently complete public Operation and business scope descriptions", () => {
    const r = loadScopedRegistry(root);
    const host = r.pages
      .filter((p) => p.owner === "module.harness")
      .map((p) => p.content)
      .join("\n");
    expect(host).toContain("concorde-context-solve-request");
    expect(host).toContain("concorde-operation-invocation");
    const hostEntry = r.pages.find((p) => p.primaryOf === "module.harness")!;
    expect(hostEntry.content).not.toMatch(/^#{2,5} (?:req|scenario)\./m);
    expect(
      r.pages.find((p) => p.documentId === "document.harness.scenarios")!
        .content,
    ).toContain("scenario.harness.execute-operation");
    expect(
      r.pages.some((page) =>
        page.documentId.startsWith("document.specify-loop."),
      ),
    ).toBe(false);
    const planning = r.pages.find(
      (page) => page.documentId === "document.planning.scenarios",
    )!;
    expect(planning.readingCollection).toBe("implementation");
    expect(planning.content).toContain("scenario.planning.");
    for (const module of r.targets.filter((t) => t.kind === "module")) {
      expect(
        module.documents.some(
          (path) =>
            path.endsWith("/architecture.md") ||
            path.endsWith("/developer-experience.md"),
        ),
      ).toBe(false);
      const entry = r.pages.find((p) => p.primaryOf === module.id)!.content;
      const sections = [
        "Purpose",
        "Terminology",
        "Usage",
        "Design",
        "Relationships",
      ];
      for (const section of sections) expect(entry).toContain(`## ${section}`);
      for (let i = 1; i < sections.length; i++)
        expect(entry.indexOf(`## ${sections[i - 1]}`)).toBeLessThan(
          entry.indexOf(`## ${sections[i]}`),
        );
      expect(entry).not.toContain("## Usage & Contract");
      expect(entry).not.toContain("## Architecture & Realization");
      expect(entry).not.toContain("```concorde-entities");
      expect(entry).not.toContain("## Entities");
    }
  });
});
