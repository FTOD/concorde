import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { existsSync } from "node:fs";
import { expect, it } from "vitest";
import {
  filterNavigation,
  graphNavigation,
  selectionFromHash,
} from "../../concorde-only/navigation";
import type { GraphData } from "../../concorde-only/types";

const root = resolve(__dirname, "../../..");
const data: GraphData = JSON.parse(
  execFileSync(
    process.env.CONCORDE_PYTHON ||
      (existsSync(resolve(root, ".venv/bin/python"))
        ? resolve(root, ".venv/bin/python")
        : "python3"),
    [resolve(root, "docsite/concorde-only/graphs.py")],
    { encoding: "utf8" },
  ),
);
const groups = graphNavigation(data);
const entries = groups.flatMap((group) => group.entries);

// verifies: scenario.views.agent-graphs
it("every exported Operation and shared Graph has a unique selectable link", () => {
  expect(new Set(entries.map((entry) => entry.id)).size).toBe(entries.length);
  for (const [kind, graphSet] of [
    ["operation", data.operations],
    ["graph", data.graphs],
  ] as const) {
    expect(
      entries
        .filter((entry) => entry.kind === kind)
        .map((entry) => entry.key)
        .sort(),
    ).toEqual(Object.keys(graphSet).sort());
  }
  for (const entry of entries)
    expect(selectionFromHash(`#${entry.id}`, groups)).toBe(entry.id);
  expect(entries.find((entry) => entry.key === "concorde-dev-loop")?.id).toBe(
    "development",
  );
  expect(entries.find((entry) => entry.key === "concorde-specify")?.id).toBe(
    "operation-concorde-specify",
  );
});

// verifies: scenario.views.agent-graphs
it("search finds both the enclosing loop and its composed Operation", () => {
  const matches = filterNavigation(groups, "specify").flatMap(
    (group) => group.entries,
  );
  expect(matches.map((entry) => entry.key)).toEqual([
    "concorde-specify-loop",
    "concorde-specify",
  ]);
  expect(
    filterNavigation(groups, "  OPERATIONS specify  ")
      .flatMap((group) => group.entries)
      .map((entry) => entry.key),
  ).toEqual(["concorde-specify-loop", "concorde-specify"]);
  expect(filterNavigation(groups, "no-such-graph")).toEqual([]);
  expect(filterNavigation(groups, "")).toEqual(groups);
});

// verifies: scenario.views.agent-graphs
it("old detail links select their containing graph and malformed links fall back safely", () => {
  for (const hash of ["#spec-stage-review_spec", "#specify-studio"])
    expect(selectionFromHash(hash, groups)).toBe("specify");
  for (const hash of [
    "#stage-tasks",
    "#handoffs",
    "#stages",
    "#studio",
    "#unknown",
    "#%",
  ]) {
    expect(selectionFromHash(hash, groups)).toBe("development");
  }
  for (const hash of [
    "#stage-graph-concorde-specify",
    "#internal-stage-concorde-specify",
  ])
    expect(selectionFromHash(hash, groups)).toBe("operation-concorde-specify");
  expect(selectionFromHash("#graph-catalog", groups)).toBe(
    groups[1].entries[0].id,
  );
});
