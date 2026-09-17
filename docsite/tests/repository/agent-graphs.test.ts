import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it } from "vitest";
import ts from "typescript";
import { loadScopedRegistry } from "../../plugins/scoped-content/model";

const root = resolve(__dirname, "../../..");
function specLinks(source: string): string[] {
  const file = ts.createSourceFile(
    "page.tsx",
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const constants = new Map<string, ts.Expression>();
  const paths = new Set<string>();
  function index(node: ts.Node) {
    if (
      ts.isVariableDeclaration(node) &&
      ts.isIdentifier(node.name) &&
      node.initializer
    )
      constants.set(node.name.text, node.initializer);
    ts.forEachChild(node, index);
  }
  index(file);
  function value(node: ts.Node, seen = new Set<string>()): string | undefined {
    if (ts.isStringLiteralLike(node)) return node.text;
    if (
      ts.isIdentifier(node) &&
      constants.has(node.text) &&
      !seen.has(node.text)
    )
      return value(constants.get(node.text)!, new Set([...seen, node.text]));
    if (
      ts.isBinaryExpression(node) &&
      node.operatorToken.kind === ts.SyntaxKind.PlusToken
    ) {
      const left = value(node.left, seen),
        right = value(node.right, seen);
      if (left !== undefined && right !== undefined) return left + right;
    }
    return undefined;
  }
  function visit(node: ts.Node) {
    const path = value(node);
    if (path?.startsWith("/specs/") && !path.endsWith("/")) paths.add(path);
    ts.forEachChild(node, visit);
  }
  visit(file);
  return [...paths];
}

it("extracts Step.spec and quoted, expression, concatenated and base-URL Spec links", () => {
  expect(
    specLinks(`const base = '/specs/example/';
    const step = {spec: '/specs/example/step#scenario.example.step'};
    const route = useBaseUrl('/specs/example/routing');
    <><Link to="/specs/example/quoted"/><Link to={'/specs/example/expression'}/>
      <Link to={base + 'contract#promise'}/><Link to={step.spec}/><a href={route}/></>`).sort(),
  ).toEqual([
    "/specs/example/contract#promise",
    "/specs/example/expression",
    "/specs/example/quoted",
    "/specs/example/routing",
    "/specs/example/step#scenario.example.step",
  ]);
});

// verifies: scenario.views.agent-graphs
it("every authored Spec link names a published document and section", () => {
  const source = readFileSync(
    resolve(root, "docsite/concorde-only/page.tsx"),
    "utf8",
  );
  const registry = loadScopedRegistry(root);
  const paths = specLinks(source);
  expect(paths).toEqual(
    expect.arrayContaining([
      "/specs/concorde/specify-loop/scenarios#scenario.development.specify-loop",
      "/specs/concorde/dev-loop/scenarios#scenario.development.dev-loop-ready",
      "/specs/concorde/development/interfaces#wire-contracts",
      "/specs/concorde/query-routing/module#usage",
      "/specs/concorde/review/scenarios#scenario.development.standalone-review",
    ]),
  );
  for (const path of paths) {
    const [route, fragment] = path.split("#");
    const page = registry.pages.find((p) => p.route === route);
    expect(page, path).toBeDefined();
    if (fragment) {
      const headings = page!.content
        .split("\n")
        .filter((line) => /^#+ /.test(line));
      expect(
        page!.content.includes(fragment) ||
          headings.some(
            (heading) =>
              heading
                .toLowerCase()
                .replace(/^#+ /, "")
                .replace(/[^a-z0-9 -]/g, "")
                .replace(/ /g, "-") === fragment,
          ),
        path,
      ).toBe(true);
    }
  }
  expect(
    existsSync(resolve(root, "src/concorde/development/loop_graph.py")),
  ).toBe(true);
});
