/** Publication of Concorde's own registered Specs. Content is not pinned; structure is. */
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { scopedSidebar } from "../../plugins/scoped-content/materialize";
import { loadScopedRegistry, roots } from "../../plugins/scoped-content/model";
import { renderPage } from "../../plugins/scoped-content/render";

const root = resolve(__dirname, "../../..");
interface SidebarItem {
  id?: string;
  link?: { id: string };
  items?: SidebarItem[];
}
const docs = (items: SidebarItem[]): string[] =>
  items.flatMap((item) => [
    ...(item.id ? [item.id] : []),
    ...(item.link ? [item.link.id] : []),
    ...docs(item.items ?? []),
  ]);

describe("Concorde's registered Specs", () => {
  // verifies: scenario.views.load-registry
  it("load deterministically from one root that composes every Module", () => {
    const a = loadScopedRegistry(root),
      b = loadScopedRegistry(root);
    expect(a.sourceDigest).toBe(b.sourceDigest);
    expect(a).toEqual(b);
    expect(roots(a).map((m) => m.id)).toEqual(["module.concorde"]);
    expect(a.rootModule).toBe("module.concorde");
    expect(new Set(a.modules.map((m) => m.id)).size).toBe(a.modules.length);
  });

  // verifies: scenario.views.publish-candidate
  it("publish every registered document once and nothing unregistered", () => {
    const registry = loadScopedRegistry(root);
    expect(registry.pages.map((p) => p.sourcePath)).toEqual(
      registry.modules.flatMap((m) => m.owns),
    );
    expect(
      registry.pages.some(
        (p) =>
          p.sourcePath === "README.md" ||
          p.sourcePath.startsWith(".concorde/") ||
          p.sourcePath.startsWith("protocol/"),
      ),
    ).toBe(false);
    const ids = [
      ...docs(scopedSidebar(registry)),
      ...docs(scopedSidebar(registry, "implementation")),
    ];
    expect(ids.sort()).toEqual(
      registry.pages.map((p) => p.stagedPath.replace(/\.md$/, "")).sort(),
    );
  });

  // verifies: scenario.views.materialize
  it("render every page with resolvable registered links", () => {
    const registry = loadScopedRegistry(root);
    for (const page of registry.pages)
      expect(() => renderPage(registry, page), page.sourcePath).not.toThrow();
  });
});
