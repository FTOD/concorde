import { errorFeedback, failure, executionError } from "../execution-error.mjs";
import { errorDisplay } from "../error-display.mjs";
/**
 * Concorde session extension.
 *
 * The developer's own Pi session loads this extension through the shim the build renders under
 * `generated/session/pi/` (source) or `.pi/extensions/` (installed). The shim supplies the project root and the catalog: every public Concorde
 * Operation with its description, guidance and request schema, the launcher to run and the
 * interpreters to try. The extension is the Pi projection of the public Operations, the
 * only supported Concorde client integration:
 *
 * - it registers one `concorde` tool. Action `describe` returns an Operation's guidance and
 *   request schema; action `run` wraps the caller's input in the typed invocation envelope, runs
 *   the launcher with that envelope on stdin in the project root and returns the launcher's JSON
 *   result;
 * - when the turn is aborted it sends the launcher SIGTERM, which the launcher turns into a
 *   cancellation of its running worker, and kills the launcher's whole process group after a
 *   grace period;
 * - it appends a short Concorde section to the system prompt naming the tool and the Operations.
 *
 * Everything the launcher checks (typed request, configuration, worktree lifecycle, permissions)
 * stays with the launcher: this extension grants nothing and knows no internal Operation.
 */
import { spawn, spawnSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type {
  AgentToolResult,
  ExtensionAPI,
} from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { toolSpan } from "./concorde-observe.ts";
import { nativeContext } from "./concorde-native-context.ts";
import { selectionPath as explicitSelectionPath } from "./concorde-selection.ts";

export interface SessionOperation {
  /** The public Operation's external name, for example `concorde-plan`. */
  name: string;
  kind: "host" | "agent-entry" | "workflow";
  description: string;
  /** The rendered Operation guidance for this Operation, without launcher mechanics. */
  guidance: string;
  /** The schema version of `<name>-request`, the `input` the tool wraps. */
  request_version: number;
  /** The self-contained JSON Schema of the typed request. */
  request_schema: Record<string, unknown>;
}

export interface SessionCatalog {
  schema_version: 2;
  /** Project-relative path of the launcher, `scripts/run-operation.py` in a checkout. */
  launcher: string;
  /** Project-relative interpreters tried in order; private selection has no ambient fallback.
   * Consumer bootstrap alone may fall back to ambient Python before managed-runtime admission.
   */
  interpreters: string[];
  /** True in Concorde's own source checkout, where a graph runs only on explicit request. */
  explicit_request_only: boolean;
  operations: SessionOperation[];
}

interface ToolParameters {
  operation: string;
  action: "run" | "describe" | "result";
  input?: Record<string, unknown>;
  mode?: "execute" | "describe-policy";
}

const INVOCATION_TYPE = "concorde-operation-invocation";
const INVOCATION_VERSION = 3;
/** How long a terminated launcher may cancel its worker before its process group is killed. */
const GRACE_MS = 5000;
/** The launcher's JSON result is returned whole up to this size; larger results go to a file. */
const RESULT_LIMIT = 48 * 1024;

export function sessionPrompt(catalog: SessionCatalog): string {
  const lines = [
    "## Concorde",
    "",
    "This project uses the Concorde Framework. Its public Operations run only through the " +
      "`concorde` tool: never run the launcher script or an internal stage operation yourself, " +
      'task-authorized edits in your own workspace may include `.concorde` files; preserve scope, evidence and concurrency safety. Call `concorde` with action "describe" ' +
      "before the first use of an Operation to read its guidance and request schema, then " +
      'action "run" with the request data as `input`. Results are typed JSON envelopes whose ' +
      "`status` is succeeded, described, blocked or failed and whose `errors` explain a stop; " +
      "report Spec gaps and blocked steps as returned instead of working around them.",
  ];
  if (catalog.explicit_request_only) {
    lines.push(
      "",
      "This is Concorde's own source checkout: run an Operation only when the user explicitly " +
        "asks for it by name. Source maintenance belongs to a fresh catalog-free candidate writer, " +
        "and, when main selects independent testing, a fresh sibling tester using only the exact candidate Pi entry/catalog and runtime; never rewrite its governing integration. " +
        "A tester may use isolated deterministic fixture drivers with that exact runtime against explicitly granted disposable data, never against governing source.",
    );
  }
  lines.push(
    "",
    "Context-solve/tasks/implement action run PREPARES an exact native Agent call; plan, Spec/code reviews and Issue solving PREPARE named async native workflows. " +
      "Call subagent with its exact returned call object. Direct Agent results expose details.concorde_native.accepted; plan action result exposes details.accepted " +
      "after independent Host reconciliation means acceptance. Poll the same workflow operation with action result. Native structured output and gate success are proposals/staging only.",
  );
  lines.push("", "Operations:");
  for (const operation of catalog.operations) {
    lines.push(`- ${operation.name}: ${operation.description}`);
  }
  return lines.join("\n") + "\n";
}

function describe(operation: SessionOperation): string {
  // The guidance opens with the Operation's own heading; the description precedes it.
  return (
    `${operation.description}\n\n${operation.guidance.trimEnd()}\n\n` +
    `## Request schema (\`input\` is its \`data\`, schema_version ${operation.request_version})\n\n` +
    "```json\n" +
    JSON.stringify(operation.request_schema, null, 2) +
    "\n```\n"
  );
}

function interpreter(
  root: string,
  catalog: SessionCatalog,
  privateSelection = false,
): string {
  for (const candidate of catalog.interpreters) {
    const resolved = path.resolve(root, candidate);
    if (fs.existsSync(resolved)) return resolved;
  }
  if (privateSelection)
    throw new Error(
      "private Pi runtime is missing; no ambient interpreter fallback",
    );
  return process.platform === "win32" ? "python" : "python3";
}

function usageLine(stderr: string): string | null {
  for (const line of stderr.split("\n")) {
    if (!line.startsWith('{"usage":')) continue;
    try {
      const total = JSON.parse(line).usage?.total ?? {};
      const figure = (key: string) =>
        typeof total[key] === "number" ? total[key] : "?";
      return (
        `usage: input ${figure("input_tokens")}, output ${figure("output_tokens")}, ` +
        `cost ${figure("cost_usd")} USD, ${figure("wall_seconds")} s`
      );
    } catch {
      return null;
    }
  }
  return null;
}

interface LauncherRun {
  code: number | null;
  stdout: string;
  stderr: string;
  aborted: boolean;
}

function runLauncher(
  argv: string[],
  cwd: string,
  envelope: unknown,
  signal: AbortSignal | undefined,
  selectionPath?: string,
): Promise<LauncherRun> {
  return new Promise((resolve, reject) => {
    const child = spawn(argv[0], argv.slice(1), {
      cwd,
      env: selectionPath
        ? { ...process.env, CONCORDE_SESSION_SELECTION: selectionPath }
        : process.env,
      stdio: ["pipe", "pipe", "pipe"],
      detached: process.platform !== "win32",
    });
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];
    let aborted = false;
    let killer: NodeJS.Timeout | undefined;
    const terminate = () => {
      aborted = true;
      // The launcher turns SIGTERM into the cancellation of its running worker and reports
      // it; the whole group is killed only when that does not finish within the grace period.
      try {
        child.kill("SIGTERM");
      } catch {}
      killer = setTimeout(() => {
        try {
          if (process.platform === "win32" || child.pid === undefined)
            child.kill("SIGKILL");
          else process.kill(-child.pid, "SIGKILL");
        } catch {}
      }, GRACE_MS);
    };
    if (signal?.aborted) terminate();
    else signal?.addEventListener("abort", terminate, { once: true });
    child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
    child.on("error", (error) => {
      if (killer) clearTimeout(killer);
      signal?.removeEventListener("abort", terminate);
      reject(error);
    });
    child.on("close", (code) => {
      if (killer) clearTimeout(killer);
      signal?.removeEventListener("abort", terminate);
      resolve({
        code,
        stdout: Buffer.concat(stdout).toString("utf8"),
        stderr: Buffer.concat(stderr).toString("utf8"),
        aborted,
      });
    });
    child.stdin.on("error", () => {});
    child.stdin.end(JSON.stringify(envelope));
  });
}

function launcherFailure(run: LauncherRun, operation: string) {
  let response: any;
  try {
    response = JSON.parse(run.stdout);
  } catch {}
  const feedback = failure(
    `${operation} ${run.aborted ? "was cancelled" : "failed"}`,
    {
      layer: "session-launcher",
      category: run.aborted
        ? "cancelled"
        : response
          ? "host-refusal"
          : "transport",
      attempt: response?.invocation_id ?? null,
      causes: response
        ? [
            errorFeedback({
              response: response.result ? response : { result: response },
            }),
          ]
        : [],
      diagnostics: JSON.stringify({
        exitCode: run.code,
        stderr: run.stderr,
        stdout: response ? undefined : run.stdout,
      }),
    },
  );
  const error = executionError(feedback);
  error.message =
    (run.aborted ? `${operation} was cancelled\n` : "") +
    errorDisplay(response ? { ...response, failure: feedback } : feedback) +
    (usageLine(run.stderr) ? `\n${usageLine(run.stderr)}` : "");
  return error;
}

function bounded(text: string, label: string): string {
  if (Buffer.byteLength(text, "utf8") <= RESULT_LIMIT) return text;
  const file = path.join(
    fs.mkdtempSync(path.join(os.tmpdir(), "concorde-result-")),
    `${label}.json`,
  );
  fs.writeFileSync(file, text, { encoding: "utf8", mode: 0o600, flag: "wx" });
  return (
    Buffer.from(text, "utf8").subarray(0, RESULT_LIMIT).toString("utf8") +
    `\n\n[Result truncated to ${RESULT_LIMIT} bytes; the complete result is saved at ${file}]`
  );
}

/**
 * Bind the extension to one project: `root` is the project directory that holds the launcher,
 * `catalog` the operations the build rendered for it.
 */
export function concordeSession(
  root: string,
  catalog: SessionCatalog,
  entryPath?: string,
) {
  root = path.resolve(root);
  if (process.env.CONCORDE_WORKER_POLICY)
    throw new Error("terminal workers cannot load the Concorde session tool");
  if (catalog.schema_version !== 2)
    throw new Error("unsupported Concorde session catalog version");
  // Selection is launch provenance, not permission or proof that a model used this tool.
  // Capture it once: replacing/rebuilding selection during this session requires a fresh tester.
  const selectionPath = explicitSelectionPath();
  if (entryPath && catalog.explicit_request_only && !selectionPath)
    throw new Error(
      "private Pi entry requires explicit candidate selection; no ambient fallback",
    );
  let selectedIdentity: string | undefined;
  const verifySelection = () => {
    if (!selectionPath) return;
    if (
      explicitSelectionPath() !== selectionPath ||
      process.env.CONCORDE_STUDIO_URL
    )
      throw new Error(
        "private Pi selection cannot change or redirect to Studio",
      );
    const python = catalog.interpreters
      .map((item) => path.resolve(root, item))
      .find((item) => fs.existsSync(item));
    if (!python)
      throw new Error(
        "private Pi selection requires the candidate Python environment; no ambient fallback",
      );
    const result = spawnSync(
      python,
      [
        path.join(root, "scripts/concorde.py"),
        "--project-root",
        root,
        "select-session",
        "--verify",
        selectionPath,
      ],
      { encoding: "utf8", maxBuffer: 8 * 1024 * 1024, timeout: 30000 },
    );
    if (result.error || result.status !== 0)
      throw launcherFailure(
        {
          code: result.status,
          stdout: result.stdout ?? "",
          stderr: result.stderr ?? String(result.error ?? ""),
          aborted: false,
        },
        "private Pi selection verification",
      );
    const selected = JSON.parse(result.stdout).result;
    if (
      selected.mode === "maintenance" ||
      selected.candidate !== root ||
      selected.pi_entry?.path !== entryPath ||
      JSON.stringify(JSON.parse(selected.pi_entry.catalog.content)) !==
        JSON.stringify(catalog) ||
      selected.runtime.path !== path.resolve(root, catalog.launcher)
    )
      throw new Error(
        "private Pi entry/catalog/runtime does not match selection",
      );
    const identity = JSON.stringify(selected);
    if (selectedIdentity !== undefined && selectedIdentity !== identity)
      throw new Error("private Pi selection changed; start a fresh session");
    selectedIdentity = identity;
  };
  verifySelection();
  const operations = new Map(
    catalog.operations.map((item) => [item.name, item]),
  );
  const names = catalog.operations.map((item) => item.name);
  return function extension(pi: ExtensionAPI): void {
    const fixtureRoot = process.env.CONCORDE_NATIVE_PROJECT_ROOT;
    if (fixtureRoot && !(catalog.explicit_request_only && selectionPath))
      throw new Error(
        "Native fixture data requires exact private candidate selection",
      );
    const projectRoot = fixtureRoot ? path.resolve(fixtureRoot) : root;
    const prepareContext = nativeContext(pi, {
      root: projectRoot,
      python: interpreter(root, catalog, Boolean(selectionPath)),
      launcher: path.resolve(root, catalog.launcher),
      verify: verifySelection,
      prepare: async (value, signal) => {
        const run = await runLauncher(
          [
            interpreter(root, catalog, Boolean(selectionPath)),
            path.resolve(root, catalog.launcher),
            "--native-context",
            "prepare",
          ],
          projectRoot,
          value,
          signal,
          selectionPath,
        );
        if (run.aborted || run.code !== 0)
          throw launcherFailure(run, "Native preparation");
        try {
          return JSON.parse(run.stdout);
        } catch {
          throw launcherFailure(
            run,
            "Native preparation returned malformed output",
          );
        }
      },
    });
    pi.on("tool_result", (event) => {
      if (event.toolName !== "concorde") return;
      const value = event.details as any;
      if (
        value?.failure ||
        ["failed", "stale", "rejected", "cancelled"].includes(value?.state) ||
        ["failed", "stopped"].includes(value?.native_state) ||
        ["blocked", "failed"].includes(value?.result?.status)
      )
        return { isError: true };
    });
    pi.on("before_agent_start", async (event) => ({
      systemPrompt:
        event.systemPrompt.trimEnd() + "\n\n" + sessionPrompt(catalog),
    }));

    pi.registerTool({
      name: "concorde",
      label: "Concorde",
      description:
        'Run a public Concorde Operation or describe one. Action "describe" returns the ' +
        'Operation\'s guidance and the JSON Schema of its request. Action "run" sends `input`, ' +
        "the request data, to the Operation and returns its typed result envelope. Context-solve/tasks/implement prepare exact native Agent calls; plan and reviews prepare async native workflows and exposes action result. Inspect Host accepted plus the typed business outcome, not proposals or launch receipts. `mode` " +
        '"describe-policy" previews the context and permissions an execute run would use ' +
        "without running an agent. A run may take a long time and blocks this turn; aborting " +
        "it cancels the running worker. Results larger than 48 KiB are saved to a file.",
      promptSnippet: "Run or describe a public Concorde Operation",
      parameters: Type.Unsafe<ToolParameters>({
        type: "object",
        properties: {
          operation: {
            type: "string",
            enum: names,
            description: "The public Concorde Operation.",
          },
          action: {
            type: "string",
            enum: ["run", "describe", "result"],
            description: "describe the Operation, or run it with `input`.",
          },
          input: {
            type: "object",
            additionalProperties: true,
            description:
              'The Operation\'s request data for action "run"; describe shows its schema.',
          },
          mode: {
            type: "string",
            enum: ["execute", "describe-policy"],
            description: 'Run mode for action "run"; execute unless given.',
          },
        },
        required: ["operation", "action"],
        additionalProperties: false,
      }),
      async execute(
        _toolCallId,
        params,
        signal,
        _onUpdate,
        ctx,
      ): Promise<AgentToolResult<Record<string, unknown>>> {
        const finishSelection = toolSpan(pi, "pi.tool_selection");
        try {
          verifySelection();
          finishSelection("ok");
        } catch (error) {
          finishSelection("error");
          throw error;
        }
        const operation = operations.get(params.operation);
        if (operation === undefined)
          throw new Error(
            `unknown Concorde Operation ${params.operation}; choose one of ${names.join(", ")}`,
          );
        if (params.action === "describe") {
          return {
            content: [{ type: "text", text: describe(operation) }],
            details: {
              operation: operation.name,
              action: "describe",
            },
          };
        }
        if (params.action === "result") {
          if (
            ![
              "concorde-plan",
              "concorde-spec-review",
              "concorde-code-review",
              "concorde-issues",
            ].includes(operation.name)
          )
            throw new Error(
              "Result polling is only for the native planning workflow",
            );
          const value = await prepareContext.result(operation.name);
          return {
            content: [
              {
                type: "text",
                text:
                  value.failure ||
                  ["rejected", "failed", "cancelled", "stale"].includes(
                    value.state,
                  )
                    ? errorDisplay(value)
                    : bounded(JSON.stringify(value), operation.name),
              },
            ],
            details: value,
          };
        }
        const input = params.input;
        if (
          input === undefined ||
          input === null ||
          typeof input !== "object" ||
          Array.isArray(input)
        )
          throw new Error(
            `action "run" needs \`input\`, the ${operation.name}-request data; call describe first`,
          );
        const mode = params.mode ?? "execute";
        const envelope = {
          type_id: INVOCATION_TYPE,
          schema_version: INVOCATION_VERSION,
          operation_id: operation.name,
          mode,
          configuration: null,
          input: {
            type_id: `${operation.name}-request`,
            schema_version: operation.request_version,
            data: input,
          },
        };
        if (
          [
            "concorde-context-solve",
            "concorde-plan",
            "concorde-tasks",
            "concorde-implement",
            "concorde-spec-review",
            "concorde-code-review",
          ].includes(operation.name) ||
          (operation.name === "concorde-issues" && input.action === "solve")
        ) {
          const value = await prepareContext(envelope, ctx, signal);
          if (value.state === "rejected") throw new Error(errorDisplay(value));
          return {
            content: [
              {
                type: "text",
                text:
                  value.failure ||
                  ["rejected", "failed", "cancelled", "stale"].includes(
                    value.state,
                  )
                    ? errorDisplay(value)
                    : bounded(JSON.stringify(value), operation.name),
              },
            ],
            details: value,
          };
        }
        const argv = [
          interpreter(root, catalog, Boolean(selectionPath)),
          path.resolve(root, catalog.launcher),
          operation.name,
        ];
        const finishLauncher = toolSpan(pi, "pi.launcher");
        let run: LauncherRun;
        try {
          run = await runLauncher(argv, root, envelope, signal, selectionPath);
          let rootInvocation: string | null = null;
          try {
            rootInvocation = JSON.parse(run.stdout).invocation_id;
          } catch {}
          finishLauncher(
            run.aborted ? "cancelled" : run.code === 0 ? "ok" : "error",
            rootInvocation,
          );
        } catch (error) {
          finishLauncher(signal?.aborted ? "cancelled" : "error");
          throw error;
        }
        const usage = usageLine(run.stderr);
        let response: any;
        try {
          response = JSON.parse(run.stdout);
        } catch {}
        if (
          run.aborted ||
          run.code !== 0 ||
          !response ||
          ["blocked", "failed"].includes(response.status)
        )
          throw launcherFailure(run, operation.name);
        return {
          content: [
            {
              type: "text",
              text:
                bounded(run.stdout.trim(), operation.name) +
                (usage ? `\n${usage}` : ""),
            },
          ],
          details: {
            operation: operation.name,
            action: "run",
            mode,
            exit_code: run.code,
          },
        };
      },
    });
  };
}
