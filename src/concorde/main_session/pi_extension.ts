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

import { execFile, spawn } from "node:child_process";
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
  taskWorktree,
  view,
  workersOf,
} from "./pi_runs.ts";
import {
  type CommandOutcome,
  commandFor,
  currentModel,
  DONE,
  levelRows,
  type Listing,
  modelRows,
  refusalText,
  scopeRows,
} from "./pi_models.ts";

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

/** Run a `concorde` command of the worktree and read the one JSON value it prints. */
function concorde(cwd: string, args: string[]): Promise<CommandOutcome> {
  const [command, ...prefix] = concordeCommand(cwd);
  return new Promise((resolve) => {
    execFile(
      command,
      [...prefix, ...args],
      {
        cwd,
        maxBuffer: 16 * 1024 * 1024,
        env: { ...process.env, CONCORDE_CLIENT: "pi" },
      },
      (error, stdout, stderr) => {
        let value: Record<string, unknown> | null = null;
        try {
          value = JSON.parse(stdout);
        } catch {
          value = null;
        }
        const code =
          error && typeof error.code === "number" ? error.code : error ? 1 : 0;
        resolve({ code, value, text: `${stdout}${stderr}`.trim() });
      },
    );
  });
}

/**
 * The worker model picker: choose, per scope (every task type, or one), a pi model and a
 * reasoning level from what `concorde workers models` lists, and apply each choice with
 * `concorde workers set` or `unset`. Returns what it changed, or throws the command's refusal.
 */
async function pickWorkerModels(
  ctx: ExtensionContext,
  task: string | null,
): Promise<string[]> {
  const cwd = task
    ? (taskWorktree(primaryRoot(ctx.cwd), task) ?? ctx.cwd)
    : ctx.cwd;
  const where = task ? ["--task", task] : [];
  const changes: string[] = [];
  for (;;) {
    const listed = await concorde(cwd, [
      "workers",
      "models",
      "--backend",
      "pi",
      ...where,
    ]);
    if (listed.code !== 0 || !listed.value)
      throw new Error(
        `concorde workers models failed:\n${refusalText(listed)}`,
      );
    const listing = listed.value as unknown as Listing;
    const scopes = scopeRows(listing);
    const scopeLabel = await ctx.ui.select(
      `Worker models (${task ? `task ${task}` : "this worktree"}, ${listing.config})`,
      scopes.map((row) => row.label),
    );
    const scope = scopes.find((row) => row.label === scopeLabel)?.scope;
    if (!scope || scope === DONE) return changes;
    const models = modelRows(listing, scope);
    const modelLabel = await ctx.ui.select(
      `Model for ${scope === "default" ? "every task type" : scope}`,
      models.map((row) => row.label),
    );
    const picked = models.find((row) => row.label === modelLabel);
    if (!picked) continue;
    let level: string | null = null;
    if (picked.action !== "unset") {
      const model = picked.model ?? currentModel(listing, scope);
      level =
        (await ctx.ui.select(
          `Reasoning level for ${model ?? "pi's default model"}`,
          levelRows(listing, model),
        )) ?? null;
      if (level === null) continue;
    }
    const args = commandFor(scope, picked.action, picked.model, level, task);
    if (!args) continue;
    const applied = await concorde(cwd, args);
    if (applied.code !== 0)
      throw new Error(
        `concorde ${args.join(" ")} failed:\n${refusalText(applied)}`,
      );
    changes.push(args.slice(1).join(" "));
    ctx.ui.notify(`Worker models: ${args.slice(1).join(" ")}`, "info");
  }
}

export default function (pi: ExtensionAPI) {
  // Workers run on the main session's agent program; every command this session starts, through
  // bash or a tool, tells Concorde that it is pi.
  process.env.CONCORDE_CLIENT = "pi";
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
    // pi-subagents names a session by its file, or by its identity when it is not persisted;
    // FleetView and bg_wait show only records under that same name.
    sessionId =
      ctx.sessionManager.getSessionFile() ?? ctx.sessionManager.getSessionId();
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
      "woken with its result when it finishes. Do not poll it. To block until every running " +
      "Concorde run ends, call bg_wait without an id; bg_wait with an id sees only subagent runs.",
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
      // The task worktree's own copy knows the task's Specs and checks; an unknown task is
      // refused by the command of the session's own worktree.
      const worktree = taskWorktree(root, params.task) ?? ctx.cwd;
      const [command, ...prefix] = concordeCommand(worktree);
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
        {
          cwd: worktree,
          detached: true,
          stdio: ["ignore", output, output],
          env: { ...process.env, CONCORDE_CLIENT: "pi" },
        },
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

  pi.registerTool({
    name: "concorde_configure_workers",
    label: "Configure worker models",
    description:
      "Open the developer's picker for the models Concorde's pi workers use: a default and " +
      "optional overrides per task type, each a model and a reasoning level from the models pi " +
      "lists. Use it when the developer asks to choose or change worker models. Without a task " +
      "it changes this worktree's configuration, which new tasks inherit; with a task it " +
      "changes only that task's copy. The developer makes every choice in the dialog.",
    promptSnippet:
      "Let the developer choose the models of Concorde's pi workers",
    parameters: Type.Object({
      task: Type.Optional(
        Type.String({
          description:
            "A task whose own configuration to change; only when the developer asks for it",
        }),
      ),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      if (!ctx.hasUI)
        throw new Error(
          "the worker model picker needs pi's interactive interface; run concorde workers " +
            "models and concorde workers set instead",
        );
      const changes = await pickWorkerModels(ctx, params.task ?? null);
      return {
        content: [
          {
            type: "text",
            text: changes.length
              ? `The developer changed the worker models: ${changes.join("; ")}. Run concorde workers show for the result.`
              : "The developer changed nothing.",
          },
        ],
        details: { changes },
      };
    },
  });

  pi.registerCommand("concorde-models", {
    description:
      "Choose the models Concorde's workers use (optionally a task identity, to change only that task)",
    handler: async (args, ctx) => {
      try {
        const changes = await pickWorkerModels(ctx, args.trim() || null);
        ctx.ui.notify(
          changes.length
            ? `Worker models changed: ${changes.join("; ")}`
            : "Worker models unchanged.",
          "info",
        );
      } catch (error) {
        ctx.ui.notify(String((error as Error).message ?? error), "error");
      }
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
