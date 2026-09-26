/** Small Spec Protocol 11 projects for publication tests. */
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import type { ModuleRecord } from "../plugins/scoped-content/model";
import type { NodeRecord } from "../plugins/scoped-content/reading-format";

export interface Project {
  root: string;
  modules: ModuleRecord[];
}
export function put(project: Project, path: string, text: string): void {
  mkdirSync(dirname(resolve(project.root, path)), { recursive: true });
  writeFileSync(resolve(project.root, path), text);
}
export function read(project: Project, path: string): string {
  return readFileSync(resolve(project.root, path), "utf8");
}
export function readJson(project: Project, path: string): any {
  return JSON.parse(read(project, path));
}
export function module(
  id: string,
  title: string,
  entry: string,
  more: Partial<ModuleRecord> = {},
): ModuleRecord {
  return {
    id,
    title,
    entry,
    owns: [entry],
    contains: [],
    uses: [],
    includes: [],
    participates: [],
    ...more,
  };
}
export const documentId = (owner: string, path: string) =>
  `document.${owner.split(".").at(-1)}.${path
    .split("/")
    .at(-1)!
    .replace(/\.md$/, "")}`;
/** Write one document pair. An entry's `module` block is filled by `writeRegistry`. */
export function putDocument(
  project: Project,
  path: string,
  options: {
    owner: string;
    role?: "module" | "implementation";
    body: string;
    defines?: NodeRecord[];
    relations?: Record<string, unknown>[];
    extensions?: Record<string, unknown>;
  },
): void {
  put(project, path, options.body);
  const entry = project.modules.find((m) => m.entry === path);
  put(
    project,
    path + ".json",
    JSON.stringify(
      {
        schema_version: 3,
        document: {
          id: documentId(options.owner, path),
          owner: options.owner,
          role: options.role ?? "module",
        },
        ...(entry ? { module: {} } : {}),
        defines: options.defines ?? [],
        relations: options.relations ?? [],
        ...(options.extensions ? { extensions: options.extensions } : {}),
      },
      null,
      2,
    ),
  );
}
/** Change document metadata fields in place. */
export function updateMetadata(
  project: Project,
  path: string,
  change: (metadata: any) => void,
): void {
  const metadata = readJson(project, path + ".json");
  change(metadata);
  put(project, path + ".json", JSON.stringify(metadata, null, 2));
}
/** Write the registry and mirror every record into its entry's `module` block. */
export function writeRegistry(project: Project): void {
  for (const m of project.modules) {
    if (!existsSync(resolve(project.root, m.entry + ".json"))) continue;
    updateMetadata(project, m.entry, (metadata) => {
      const { id: _id, entry: _entry, ...block } = m;
      metadata.module = block;
    });
  }
  put(
    project,
    ".concorde/specs.json",
    JSON.stringify({ schema_version: 3, modules: project.modules }, null, 2),
  );
}
export function entryBody(
  title: string,
  parts: {
    terminology?: string;
    usage?: string;
    design?: string;
    architecture?: string;
  } = {},
): string {
  return [
    `# ${title}`,
    "",
    "## Purpose",
    "",
    `${title} keeps one responsibility of the bank.`,
    "",
    "## Terminology",
    "",
    parts.terminology ?? "This Module defines no terms of its own.",
    "",
    "## Usage",
    "",
    parts.usage ?? `Call ${title} for its responsibility.`,
    "",
    "## Design",
    "",
    parts.design ?? `${title} keeps its state in one place.`,
    "",
    parts.architecture ?? `${title} collaborates as declared.`,
    "",
  ].join("\n");
}
export const table = (...rows: [string, string][]) =>
  [
    "| Term | Definition |",
    "| --- | --- |",
    ...rows.map(([t, d]) => `| ${t} | ${d} |`),
  ].join("\n");

/**
 * Bank (root) contains Transfer and Audit; Transfer contains Ledger; Audit uses Transfer,
 * relying on its Hold concept. Transfer owns an implementation document with a requirement, a
 * scenario and a contract.
 */
export function bankProject(): Project {
  const project: Project = {
    root: mkdtempSync(resolve(tmpdir(), "concorde-scoped-")),
    modules: [
      module("module.bank", "Bank", "specs/bank/module.md", {
        contains: [
          { target: "module.transfer", meaning: "#contains-transfer" },
          { target: "module.audit", meaning: "#contains-audit" },
        ],
      }),
      module("module.transfer", "Transfer", "specs/transfer/module.md", {
        owns: ["specs/transfer/module.md", "specs/transfer/requirements.md"],
        contains: [{ target: "module.ledger", meaning: "#contains-ledger" }],
      }),
      module("module.ledger", "Ledger", "specs/ledger/module.md"),
      module("module.audit", "Audit", "specs/audit/module.md", {
        uses: [
          {
            target: "module.transfer",
            meaning: "#uses-transfer",
            relies_on: ["concept.transfer.hold"],
          },
        ],
      }),
    ],
  };
  put(
    project,
    ".concorde/config.json",
    JSON.stringify({ profile_version: 16, registry: ".concorde/specs.json" }),
  );
  put(
    project,
    "docsite/site.json",
    JSON.stringify({
      schema_version: 1,
      title: "Bank",
      url: "https://localhost",
      baseUrl: "/",
      organizationName: "bank",
      projectName: "bank",
    }),
  );
  put(project, "src/ledger.ts", "export const ledger = true;\n");
  put(project, "src/transfer/index.ts", "export const transfer = true;\n");
  putDocument(project, "specs/bank/module.md", {
    owner: "module.bank",
    body: entryBody("Bank", {
      architecture:
        '```d2\nbank: Bank {\n  transfer: Transfer\n}\n```\n\n<a id="contains-transfer"></a><a id="contains-audit"></a>\n\nBank is composed of Transfer and Audit.',
    }),
  });
  putDocument(project, "specs/transfer/module.md", {
    owner: "module.transfer",
    body: entryBody("Transfer", {
      terminology: table(["Hold", "Money withheld until a transfer settles."]),
      usage:
        'Submit a transfer.\n\n<a id="concept.transfer.hold"></a>\n\nA hold keeps money from being spent twice.',
      design:
        '<a id="transfer-service"></a>\n\nThe transfer service records holds.\n\n<a id="contains-ledger"></a>\n\nLedger books settled transfers.',
    }),
    defines: [
      {
        id: "concept.transfer.hold",
        type: "concept",
        title: "Hold",
        meaning: "#concept.transfer.hold",
      },
      {
        id: "realization.transfer.service",
        type: "realization",
        title: "Transfer service",
        meaning: "#transfer-service",
        entries: ["src/transfer/"],
      },
    ],
    relations: [
      {
        type: "relates",
        source: "realization.transfer.service",
        verb: "records",
        target: "concept.transfer.hold",
      },
    ],
  });
  putDocument(project, "specs/transfer/requirements.md", {
    owner: "module.transfer",
    role: "implementation",
    body: [
      "# Transfer requirements",
      "",
      "### req.transfer.single — One transfer per submission",
      "",
      "Transfer SHALL create at most one transfer per admitted submission.",
      "",
      "### scenario.transfer.submit — Successful submission",
      "",
      "- GIVEN a funded account",
      "- WHEN the owner submits a transfer",
      "- THEN Transfer places one hold",
      "",
      "## Submission contract",
      "",
      "```concorde-contract",
      JSON.stringify({
        id: "contract.transfer.submit",
        version: 1,
        schema: { type: "integer" },
        semantics: "The submitted amount.",
        example: 5,
      }),
      "```",
      "",
    ].join("\n"),
  });
  putDocument(project, "specs/ledger/module.md", {
    owner: "module.ledger",
    body: entryBody("Ledger", {
      design:
        '<a id="realization.ledger.book"></a>\n\nThe book keeps settled entries.',
    }),
    defines: [
      {
        id: "realization.ledger.book",
        type: "realization",
        title: "Book",
        meaning: "#realization.ledger.book",
        entries: ["src/ledger.ts"],
      },
    ],
  });
  putDocument(project, "specs/audit/module.md", {
    owner: "module.audit",
    body: entryBody("Audit", {
      terminology: table([
        "[Hold](../transfer/module.md#concept.transfer.hold)",
        "",
      ]),
      architecture:
        '<a id="uses-transfer"></a>\n\nAudit reads the holds Transfer places.',
    }),
  });
  writeRegistry(project);
  return project;
}
