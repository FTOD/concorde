import { describe, it, expect } from "vitest";
import {
  contracts,
  definitionHeadings,
  metadata,
  parseJson,
  readingMeanings,
  requireReading,
  terminologyRows,
} from "../../plugins/scoped-content/reading-format";

const entry =
  "# Example\n\n## Purpose\n\nProvide one result.\n\n## Terminology\n\n" +
  "| Term | Definition |\n| --- | --- |\n| Result | The returned value. |\n" +
  "| [Request](../provider/module.md#concept.provider.request) |  |\n" +
  "| Pipe \\| term | A cell with an escaped \\| pipe. |\n\n" +
  "## Usage\n\nSubmit one request.\n\n## Design\n\n" +
  '<a id="concept.example.result"></a><a id="realization.example.service"></a>\n\nThe service produces the result.\n\n' +
  "## Relationships\n\n```mermaid\nflowchart LR\n    Service[Example service] -->|produces| Result\n```\n";
const declaration = {
  schema_version: 3,
  document: {
    id: "document.example.module",
    owner: "module.example",
    role: "module",
  },
  module: {
    title: "Example",
    owns: ["example/module.md"],
    contains: [],
    uses: [
      {
        target: "module.provider",
        meaning: "#uses-provider",
        relies_on: ["concept.provider.request"],
      },
    ],
    includes: [
      { kind: "external", target: "references/sdk/", reason: "SDK fields" },
    ],
    participates: [],
  },
  defines: [
    {
      id: "concept.example.result",
      type: "concept",
      title: "Result",
      meaning: "#concept.example.result",
    },
    {
      id: "realization.example.service",
      type: "realization",
      title: "Example service",
      meaning: "#realization.example.service",
      entries: ["src/example/"],
      pending: [],
    },
  ],
  relations: [
    {
      type: "relates",
      source: "realization.example.service",
      verb: "produces",
      target: "concept.example.result",
    },
  ],
  extensions: { "concorde.operations": [] },
};
const parse = (value: unknown, entryDocument = true) =>
  metadata(
    JSON.stringify(value),
    "example/module.md.json",
    "module.example",
    entryDocument,
  );

describe("Protocol 11 reading and document metadata", () => {
  it("reads schema-3 metadata with the entry's module block", () => {
    expect(parse(declaration)).toEqual(declaration);
    const { module: _block, ...topic } = declaration;
    expect(parse(topic, false)).toEqual(topic);
  });
  // verifies: scenario.views.reject-reading-collection
  it("rejects other schemas, roles, owners and misplaced module blocks", () => {
    const { module: _block, ...topic } = declaration;
    for (const [value, isEntry] of [
      [{ ...declaration, schema_version: 2 }, true],
      [{ ...declaration, entities: [] }, true],
      [
        {
          ...declaration,
          document: { ...declaration.document, role: "topic" },
        },
        true,
      ],
      [
        {
          ...declaration,
          document: { id: "document.example.module", owner: "module.example" },
        },
        true,
      ],
      [
        {
          ...declaration,
          document: { ...declaration.document, owner: "module.other" },
        },
        true,
      ],
      [
        {
          ...declaration,
          document: { ...declaration.document, id: "Invalid ID" },
        },
        true,
      ],
      [topic, true],
      [declaration, false],
      [{ ...declaration, module: { ...declaration.module, owns: [] } }, true],
      [
        { ...declaration, module: { ...declaration.module, parent: null } },
        true,
      ],
      [
        {
          ...declaration,
          defines: [{ ...declaration.defines[0], type: "entity" }],
        },
        true,
      ],
      [
        {
          ...declaration,
          defines: [{ ...declaration.defines[1], entries: [] }],
        },
        true,
      ],
      [
        {
          ...declaration,
          defines: [{ ...declaration.defines[0], meaning: "other.md#x" }],
        },
        true,
      ],
      [{ ...declaration, relations: [{ type: "imports" }] }, true],
      [{ ...declaration, extensions: [] }, true],
    ] as const)
      expect(() => parse(value, isEntry)).toThrow();
  });
  // verifies: scenario.views.reject-reading-collection
  it("keeps definitions and Graph Specs out of module-role reading", () => {
    expect(() =>
      requireReading(entry, "example/module.md", true, "module"),
    ).not.toThrow();
    expect(() =>
      requireReading(entry, "example/module.md", true, "implementation"),
    ).toThrow(/module.md must have document.role module/);
    const fragments = [
      "\n### req.example.once — One result\n\nExample SHALL return one result.\n",
      "\n### scenario.example.once — One result\n\n- GIVEN input\n- WHEN called\n- THEN one result\n",
      '\n```concorde-contract\n{"id":"contract.example.result"}\n```\n',
      "\n```mermaid\nflowchart LR\n    %% graph: example\n    a -->|b| c\n```\n",
    ];
    for (const fragment of fragments) {
      expect(() =>
        requireReading(entry + fragment, "example/module.md", true, "module"),
      ).toThrow(/belong in an implementation-role document/);
      expect(() =>
        requireReading(
          "# Topic\n" + fragment,
          "example/topic.md",
          false,
          "module",
        ),
      ).toThrow(/belong in an implementation-role document/);
      expect(() =>
        requireReading(
          "# Details\n" + fragment,
          "example/details.md",
          false,
          "implementation",
        ),
      ).not.toThrow();
      expect(() =>
        requireReading(
          entry + "\n````markdown\n" + fragment + "\n````\n",
          "example/module.md",
          true,
          "module",
        ),
      ).not.toThrow();
    }
  });
  it("reads grouped anchors, definition headings and contract fences", () => {
    const meanings = readingMeanings(entry, "example/module.md");
    expect(meanings.get("concept.example.result")).toBe(
      meanings.get("realization.example.service"),
    );
    expect(meanings.get("concept.example.result")).toBe(
      "The service produces the result.",
    );
    const details =
      "# Details\n\n## req.example.once – One result {#req.example.once}\n\nExample SHALL return one result.\n\n" +
      "### scenario.example.once - One result\n\n- WHEN called\n- THEN one result\n\n" +
      '```concorde-contract\n{"id":"contract.example.result","version":2,"schema":{},"semantics":"x","example":1}\n```\n' +
      "\n````markdown\n### req.example.quoted — Not a definition\n````\n";
    expect(definitionHeadings(details)).toEqual([
      "req.example.once",
      "scenario.example.once",
    ]);
    expect(contracts(details, "example/details.md")).toEqual([
      { id: "contract.example.result", version: 2 },
    ]);
    expect(() =>
      readingMeanings(
        "## req.example.once — One {#req.example.other}\n",
        "example/details.md",
      ),
    ).toThrow(/Definition anchor differs/);
    expect(() =>
      contracts(
        '```concorde-contract\n{"version":1}\n```\n',
        "example/details.md",
      ),
    ).toThrow(/Invalid canonical contract/);
  });
  it("reads defining and import rows of the Terminology table", () => {
    expect(terminologyRows(entry)).toEqual([
      { term: "Result", definition: "The returned value." },
      {
        term: "[Request](../provider/module.md#concept.provider.request)",
        definition: "",
        link: {
          text: "Request",
          href: "../provider/module.md#concept.provider.request",
          fragment: "concept.provider.request",
        },
      },
      {
        term: "Pipe \\| term",
        definition: "A cell with an escaped \\| pipe.",
      },
    ]);
    expect(
      terminologyRows(
        entry.replace(/\| Term[\s\S]*?\n\n## Usage/, "No terms.\n\n## Usage"),
      ),
    ).toEqual([]);
  });
  it("rejects diagrams that are neither checked flowcharts nor marked illustrative", () => {
    for (const diagram of [
      "```mermaid\nsequenceDiagram\n    A->>B: go\n```",
      "```mermaid\nstateDiagram-v2\n    [*] --> A\n```",
      "```mermaid illustrated\nsequenceDiagram\n    A->>B: go\n```",
    ])
      expect(() =>
        requireReading(
          entry + "\n" + diagram + "\n",
          "example/module.md",
          true,
          "module",
        ),
      ).toThrow(/neither a flowchart nor marked illustrative/);
    expect(() =>
      requireReading(
        entry +
          "\n```mermaid illustrative\nsequenceDiagram\n    A->>B: go\n```\n",
        "example/module.md",
        true,
        "module",
      ),
    ).not.toThrow();
  });
  it("rejects duplicate nested keys and overflowing JSON numbers", () => {
    expect(() =>
      parseJson('{"document":{"id":"a","id":"b"}}', "metadata"),
    ).toThrow(/Duplicate JSON key/);
    expect(() => parseJson('{"example":1e999}', "metadata")).toThrow(
      /Non-finite/,
    );
  });
});
