import type { GraphData } from "./types";

export type GraphEntry = {
  id: string;
  title: string;
  key: string;
  kind: "operation" | "graph" | "guide";
};
export type GraphGroup = { title: string; entries: GraphEntry[] };

export function operationAnchor(key: string): string {
  return key === "concorde-dev-loop"
    ? "development"
    : key === "concorde-specify-loop"
      ? "specify"
      : `operation-${key}`;
}

export function graphNavigation(data: GraphData): GraphGroup[] {
  const first = [
    "concorde-dev-loop",
    "concorde-specify-loop",
    "concorde-specify",
  ];
  const operations = [
    ...first,
    ...Object.keys(data.operations)
      .filter((name) => !first.includes(name))
      .sort(),
  ];
  return [
    {
      title: "Operations",
      entries: operations.map((key) => ({
        key,
        kind: "operation",
        title: key.replace(/^concorde-/, ""),
        id: operationAnchor(key),
      })),
    },
    {
      title: "Shared graphs",
      entries: Object.keys(data.graphs).map((key) => ({
        key,
        kind: "graph",
        title: key,
        id: `graph-${key.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
      })),
    },
    {
      title: "Guides",
      entries: [
        {
          id: "routing",
          key: "routing",
          title: "Routing & diagnosis",
          kind: "guide",
        },
        {
          id: "coverage",
          key: "coverage",
          title: "Implementation coverage",
          kind: "guide",
        },
      ],
    },
  ];
}

export function selectionFromHash(hash: string, groups: GraphGroup[]): string {
  let id: string;
  try {
    id = decodeURIComponent(hash.replace(/^#/, ""));
  } catch {
    return "development";
  }
  if (groups.some((group) => group.entries.some((entry) => entry.id === id)))
    return id;
  // Existing section and node-detail links still open their containing graph.
  if (id.startsWith("spec-stage-") || id === "specify-studio") return "specify";
  for (const prefix of ["stage-graph-", "internal-stage-"]) {
    if (id.startsWith(prefix)) {
      const operation = operationAnchor(id.slice(prefix.length));
      if (
        groups.some((group) =>
          group.entries.some((entry) => entry.id === operation),
        )
      )
        return operation;
    }
  }
  if (id === "graph-catalog")
    return groups.find((group) => group.title === "Shared graphs")!.entries[0]
      .id;
  return "development";
}

export function filterNavigation(
  groups: GraphGroup[],
  query: string,
): GraphGroup[] {
  const words = query.toLowerCase().trim().split(/\s+/);
  return groups
    .map((group) => ({
      ...group,
      entries: group.entries.filter((entry) =>
        words.every((word) =>
          `${entry.title} ${entry.key} ${group.title}`
            .toLowerCase()
            .includes(word),
        ),
      ),
    }))
    .filter((group) => group.entries.length > 0);
}
