/**
 * Concorde's extension for a pi main session.
 *
 * It lets the main agent run Operations the way Concorde expects in pi: `concorde_run` starts
 * `concorde run` as a detached process and returns at once; every run of the project is followed
 * through its progress files and shown in pi-subagents' FleetView as an external job, counted by
 * `bg_wait`, and reported back with a message that wakes the main agent when it finishes.
 * `/concorde` lists the runs. The extension only launches and observes: the Operation host, not
 * this extension, runs and records every Operation. Without pi-subagents it still launches, wakes
 * and lists; only the FleetView entries and `bg_wait` are missing.
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, openSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { Type } from "typebox";
import {
  getAgentDir,
  type ExtensionAPI,
  type ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import {
  alive,
  concordeCommand,
  operationRuns,
  type OperationStatus,
  primaryRoot,
  runsDirectory,
  type RunView,
  view,
  workersOf,
} from "./pi_runs.ts";

const SOURCE = "concorde";
const POLL_MS = 2000;
const START_WAIT_MS = 15000;

interface Subagents {
  registerExternalRun?: (run: Record<string, unknown>) => unknown;
  updateExternalRun?: (
    sessionId: string,
    id: string,
    update: Record<string, unknown>,
  ) => unknown;
  registerBackgroundWorkProvider?: (
    provider: Record<string, unknown>,
  ) => () => void;
}

/** pi-subagents' public APIs, when the package is installed in pi's own package directory. */
async function loadSubagents(): Promise<Subagents> {
  const api = join(
    getAgentDir(),
    "npm",
    "node_modules",
    "pi-subagents",
    "src",
    "api",
  );
  const found: Subagents = {};
  for (const [name, keys] of [
    ["external-runs", ["registerExternalRun", "updateExternalRun"]],
    ["background-work", ["registerBackgroundWorkProvider"]],
  ] as const) {
    for (const extension of [".js", ".ts"]) {
      const file = join(api, name + extension);
      if (!existsSync(file)) continue;
      try {
        const module = await import(pathToFileURL(file).href);
        for (const key of keys)
          (found as Record<string, unknown>)[key] = module[key];
      } catch {
        // pi-subagents is optional; the run view works without FleetView.
      }
      break;
    }
  }
  return found;
}

interface Tracked {
  operation: OperationStatus;
  shown: RunView | null;
  registered: boolean;
  reported: boolean;
}

export default function (pi: ExtensionAPI) {
  const tracked = new Map<string, Tracked>();
  let root = process.cwd();
  let sessionId = "";
  let subagents: Subagents = {};
  let timer: ReturnType<typeof setInterval> | undefined;
  let disposeProvider: (() => void) | undefined;

  function refresh(ctx?: ExtensionContext): void {
    const operations = new Map(
      operationRuns(root).map((item) => [item.run_id, item]),
    );
    for (const [id, entry] of tracked) {
      const operation = operations.get(id) ?? entry.operation;
      entry.operation = operation;
      const shown = view(
        root,
        operation,
        workersOf(root, operation),
        operation.phase === "finished" || alive(operation.host_pid),
      );
      const fields = {
        label: shown.label,
        state: shown.state,
        updatedAt: shown.updatedAt,
        currentAction: shown.currentAction,
        reportPath: shown.reportPath,
        ...(shown.preview ? { preview: shown.preview } : {}),
        ...(shown.endedAt ? { endedAt: shown.endedAt } : {}),
      };
      try {
        if (!entry.registered && subagents.registerExternalRun && sessionId) {
          subagents.registerExternalRun({
            id,
            sessionId,
            source: SOURCE,
            startedAt: shown.startedAt,
            ...fields,
          });
          entry.registered = true;
        } else if (entry.registered && subagents.updateExternalRun) {
          subagents.updateExternalRun(sessionId, id, fields);
        }
      } catch {
        // A rejected display record never changes the run.
      }
      entry.shown = shown;
      if (shown.finished && !entry.reported) {
        entry.reported = true;
        report(shown);
      }
    }
    const running = [...tracked.values()].filter(
      (entry) => entry.shown && !entry.shown.finished,
    ).length;
    if (ctx?.hasUI)
      ctx.ui.setStatus(
        "concorde",
        running ? `Concorde: ${running} running` : "",
      );
  }

  function report(shown: RunView): void {
    pi.sendMessage(
      {
        customType: "concorde-run",
        content:
          `Concorde run ${shown.id} (${shown.label}) finished ${shown.status}. ` +
          `${shown.preview ?? ""}\nRead the Operation result: ${shown.reportPath}`,
        display: true,
        details: {
          runId: shown.id,
          status: shown.status,
          result: shown.reportPath,
        },
      },
      { triggerTurn: true, deliverAs: "followUp" },
    );
  }

  function track(operation: OperationStatus, reported = false): void {
    if (!tracked.has(operation.run_id)) {
      tracked.set(operation.run_id, {
        operation,
        shown: null,
        registered: false,
        reported,
      });
    }
  }

  pi.on("session_start", async (_event, ctx) => {
    root = primaryRoot(ctx.cwd);
    sessionId = ctx.sessionManager.getSessionId();
    subagents = await loadSubagents();
    for (const operation of operationRuns(root)) {
      if (operation.phase !== "finished" && alive(operation.host_pid))
        track(operation);
    }
    disposeProvider = subagents.registerBackgroundWorkProvider?.({
      name: SOURCE,
      listActiveWork: () =>
        [...tracked.values()]
          .filter((entry) => !entry.shown?.finished)
          .map((entry) => ({ id: entry.operation.run_id, sessionId })),
    });
    timer = setInterval(() => refresh(ctx), POLL_MS);
    refresh(ctx);
  });

  pi.on("session_shutdown", async () => {
    if (timer) clearInterval(timer);
    disposeProvider?.();
  });

  pi.registerTool({
    name: "concorde_run",
    label: "Concorde run",
    description:
      "Start a Concorde Operation in the background: `concorde run <operation> --task <task> [arguments]`. " +
      "It returns at once with the run identity; the run appears in the run view, and you are " +
      "woken with its result when it finishes. Do not poll it.",
    promptSnippet:
      "Start a Concorde Operation in the background and be woken when it finishes",
    parameters: Type.Object({
      operation: Type.String({
        description: "The Operation, such as implement or validate",
      }),
      task: Type.String({ description: "The task identity" }),
      arguments: Type.Optional(
        Type.Array(Type.String(), {
          description: "Further arguments, such as --goal and its text",
        }),
      ),
    }),
    async execute(_id, params, signal, _onUpdate, ctx) {
      root = primaryRoot(ctx.cwd);
      const [command, ...prefix] = concordeCommand(ctx.cwd);
      mkdirSync(runsDirectory(root), { recursive: true });
      const log = join(runsDirectory(root), `launch-${Date.now()}.log`);
      const output = openSync(log, "a");
      const child = spawn(
        command,
        [
          ...prefix,
          "run",
          params.operation,
          "--task",
          params.task,
          ...(params.arguments ?? []),
        ],
        { cwd: ctx.cwd, detached: true, stdio: ["ignore", output, output] },
      );
      let exited: number | null = null;
      child.on("exit", (code) => (exited = code ?? -1));
      child.unref();
      const deadline = Date.now() + START_WAIT_MS;
      while (Date.now() < deadline && !signal?.aborted) {
        const operation = operationRuns(root).find(
          (item) => item.host_pid === child.pid,
        );
        if (operation) {
          track(operation);
          refresh(ctx);
          return {
            content: [
              {
                type: "text",
                text:
                  `Started ${params.operation} for task ${params.task} as run ${operation.run_id} ` +
                  `(host process ${child.pid}). You will be woken with its result; its result will be ` +
                  `${join(runsDirectory(root), operation.run_id, "result.json")}.`,
              },
            ],
            details: { runId: operation.run_id, pid: child.pid },
          };
        }
        if (exited !== null) break;
        await new Promise((resolve) => setTimeout(resolve, 200));
      }
      const text = existsSync(log)
        ? readFileSync(log, "utf-8").slice(-4000)
        : "";
      throw new Error(
        exited !== null
          ? `concorde run exited with status ${exited} before its run began: ${text || "(no output)"}`
          : `concorde run (process ${child.pid}) wrote no progress file within ${START_WAIT_MS / 1000}s; see ${log}`,
      );
    },
  });

  pi.registerCommand("concorde", {
    description: "List Concorde Operation runs of this project",
    handler: async (_args, ctx) => {
      const lines = operationRuns(root)
        .slice(-20)
        .map((operation) => {
          const shown = view(
            root,
            operation,
            workersOf(root, operation),
            operation.phase === "finished" || alive(operation.host_pid),
          );
          return `${shown.state.padEnd(9)} ${shown.label} (${shown.id}) — ${shown.finished ? (shown.preview ?? "") : shown.currentAction}`;
        });
      ctx.ui.notify(
        lines.length
          ? lines.join("\n")
          : "No Concorde runs in this project yet.",
        "info",
      );
    },
  });
}
