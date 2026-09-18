import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it } from "vitest";
import { scopedSidebar } from "../../plugins/scoped-content/materialize";
import {
  loadScopedRegistry,
  rewriteLinks,
} from "../../plugins/scoped-content/model";

const root = resolve(__dirname, "../../..");
const consolidated = [
  ["delivery", "delivery"],
  ["implementation", "implementation"],
  ["spec-authoring", "authoring"],
  ["review", "review"],
  ["validation", "validation"],
  ["query-routing", "query-and-routing"],
  ["topology", "topology"],
  ["dev-loop", "development"],
  ["specify-loop", "specify-loop"],
];

// Editorial cases for this checkout, not a rule forbidding single-topic Modules.
// verifies: scenario.views.publish-reference-link
it("publishes consolidated explanations as Module entries while retaining precise specs", () => {
  const registry = loadScopedRegistry(root);
  const reading = scopedSidebar(registry)[0].items!;
  const implementation = scopedSidebar(registry, "implementation")[0].items!;
  const providers = reading.find((item) => item.label === "Operations")!.items!;
  const providerDetails = implementation.find(
    (item) => item.label === "Operations",
  )!.items!;
  for (const [directory, retiredTopic] of consolidated) {
    const target = registry.targets.find(
      (t) => t.id === `module.${directory}`,
    )!;
    const source = `specs/concorde/${directory}/module.md`;
    const entry = registry.pages.find((p) => p.sourcePath === source)!;
    expect(entry.readingCollection).toBe("module");
    expect(
      target.documents.filter(
        (path) =>
          registry.pages.find((p) => p.sourcePath === path)
            ?.readingCollection === "module",
      ),
    ).toEqual([source]);
    expect(providers.find((item) => item.label === target.title)).toEqual({
      type: "doc",
      id: `concorde/${directory}/module`,
      label: target.title,
    });
    const details = providerDetails.find(
      (item) => item.label === target.title,
    )!;
    expect(details.type).toBe("category");
    expect(details.items!.map((item) => item.id)).toEqual(
      expect.arrayContaining([
        `concorde/${directory}/requirements`,
        `concorde/${directory}/scenarios`,
        `concorde/${directory}/execution-reference`,
      ]),
    );
    const retired = `specs/concorde/${directory}/${retiredTopic}.md`;
    expect(registry.pages.some((p) => p.sourcePath === retired)).toBe(false);
    for (const suffix of ["", ".json"]) {
      expect(existsSync(resolve(root, retired + suffix))).toBe(false);
    }
  }
  // Include same-directory links from precise specs, not only sidebar and graph links.
  for (const page of registry.pages) {
    expect(() => rewriteLinks(registry, page), page.sourcePath).not.toThrow();
  }
  // The shared canonical vocabulary lives in the Framework entry's Terminology table.
  const concepts = "specs/concorde/concepts.md";
  expect(registry.pages.some((p) => p.sourcePath === concepts)).toBe(false);
  expect(reading).not.toContainEqual(
    expect.objectContaining({ id: "concorde/concepts" }),
  );
  for (const suffix of ["", ".json"]) {
    expect(existsSync(resolve(root, concepts + suffix))).toBe(false);
  }
});
