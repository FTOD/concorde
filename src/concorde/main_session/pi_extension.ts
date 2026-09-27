/**
 * Concorde's extension for a pi main session.
 *
 * It lets the main agent run Operations and execution commands the way Concorde expects in pi:
 * `concorde_run` starts `concorde run <operation>` or `concorde <command>` as a detached process in
 * the task's worktree, whose workspace binding the run reads, and returns at once; every run of the
 * project is followed through its progress files and shown in pi-subagents' FleetView as an
 * external job, counted by `bg_wait`, and reported back with a message that wakes the main agent
 * when it finishes. `/concorde` lists the runs. The extension only launches and observes: the
 * Execution runner, not this extension, runs and records every run. Without pi-subagents it still launches, wakes
 * and lists; only the FleetView entries and `bg_wait` are missing.
 *
 * `concorde_task_session` starts, answers or stops a pi task session through `concorde task
 * session`; each round of a task session is followed the same way, through the progress file its
 * supervisor keeps and the outcome the task record holds, and wakes the main agent when it ends.
 * Inside a task session itself (`CONCORDE_TASK_SESSION` set), which may load this extension as a
 * project resource, it only marks commands as started from pi and stays otherwise inactive.
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
  primaryRoot,
  recordedRuns,
  resultText,
  roundId,
  roundOutcome,
  runsDirectory,
  type RunStatus,
  type RunView,
  sessionRounds,
  type SessionStatus,
  sessionText,
  sessionView,
  taskWorktree,
  view,
  workersOf,
} from "./pi_runs.ts";
import {
  type CommandOutcome,
  commandFor,
  currentModel,
  levelRows,
  type Listing,
  listingCommand,
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

// The execution commands, which run as `concorde <command>`; every other name is an Operation.
const COMMANDS = ["task-validation", "delivery", "scaffold"];

interface Tracked {
  operation: RunStatus;
  shown: RunView | null;
  registered: boolean;
  reported: boolean;
}

interface TrackedRound {
  status: SessionStatus;
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
 * The worker model picker: choose, per scope (every worker, one Operation's or one worker), a pi
 * model and a reasoning level from what `concorde configure-workers` lists in the chosen worktree
 * (a task's, or this one), and apply each choice with `concorde configure-workers` there. Returns
 * what it changed, or throws the command's refusal.
 */
async function pickWorkerModels(
  ctx: ExtensionContext,
  task: string | null,
): Promise<string[]> {
  const cwd = task
    ? (taskWorktree(primaryRoot(ctx.cwd), task) ?? ctx.cwd)
    : ctx.cwd;
  const changes: string[] = [];
  for (;;) {
    const listed = await concorde(cwd, listingCommand());
    const output = listed.value?.output;
    if (listed.code !== 0 || !output)
      throw new Error(
        `concorde ${listingCommand().join(" ")} failed:\n${refusalText(listed)}`,
      );
    const listing = output as unknown as Listing;
    const scopes = scopeRows(listing);
    const scopeLabel = await ctx.ui.select(
      `Worker models (${task ? `task ${task}` : "this worktree"}, ${listing.config})`,
      scopes.map((row) => row.label),
    );
    const scope = scopes.find((row) => row.label === scopeLabel)?.scope;
    if (!scope) return changes;
    const models = modelRows(listing, scope);
    const modelLabel = await ctx.ui.select(
      `Model for ${
        scope.operation === null
          ? "every worker"
          : `${scope.operation}${scope.worker ? ` ${scope.worker}` : ""}`
      }`,
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
    const args = commandFor(scope, picked.action, picked.model, level);
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
  // A task session is no main session: it neither launches background runs nor watches the
  // project's runs and rounds.
  if (process.env.CONCORDE_TASK_SESSION) return;
  const tracked = new Map<string, Tracked>();
  const rounds = new Map<string, TrackedRound>();
  let root = process.cwd();
  let sessionId = "";
  let subagents: Subagents = {};
  let timer: ReturnType<typeof setInterval> | undefined;
  let disposeProvider: (() => void) | undefined;

  /** Show one run or round in FleetView, registering it the first time. */
  function publish(
    id: string,
    entry: { registered: boolean },
    shown: RunView,
  ): void {
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
  }

  function refreshRounds(): void {
    for (const status of sessionRounds(root)) {
      const id = roundId(status);
      const known = rounds.get(id);
      if (known) known.status = status;
      else if (status.phase === "running")
        rounds.set(id, {
          status,
          shown: null,
          registered: false,
          reported: false,
        });
    }
    for (const [id, entry] of rounds) {
      if (entry.status.phase !== "finished") {
        // The progress file holds only the current round; the record holds every outcome.
        const ended = roundOutcome(root, entry.status);
        if (ended)
          entry.status = {
            ...entry.status,
            phase: "finished",
            status: ended.status,
            summary: ended.summary,
          };
      }
      const shown = sessionView(
        root,
        entry.status,
        entry.status.phase === "finished" || alive(entry.status.supervisor_pid),
      );
      publish(id, entry, shown);
      entry.shown = shown;
      if (shown.finished && !entry.reported) {
        entry.reported = true;
        wake("concorde-task-session", sessionText(root, entry.status), {
          task: entry.status.task,
          round: entry.status.round,
          status: shown.status,
        });
      }
    }
  }

  function refresh(ctx?: ExtensionContext): void {
    const operations = new Map(
      recordedRuns(root).map((item) => [item.run_id, item]),
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
      publish(id, entry, shown);
      entry.shown = shown;
      if (shown.finished && !entry.reported) {
        entry.reported = true;
        report(shown);
      }
    }
    refreshRounds();
    const running =
      [...tracked.values()].filter(
        (entry) => entry.shown && !entry.shown.finished,
      ).length +
      [...rounds.values()].filter(
        (entry) => entry.shown && !entry.shown.finished,
      ).length;
    if (ctx?.hasUI)
      ctx.ui.setStatus(
        "concorde",
        running ? `Concorde: ${running} running` : "",
      );
  }

  // A result that arrives while the main agent is in a turn is steered into that turn, after its
  // current tool calls, rather than held until the turn ends; when it is idle, it starts a turn.
  function wake(
    customType: string,
    content: string,
    details: Record<string, unknown>,
  ): void {
    pi.sendMessage(
      { customType, content, display: true, details },
      { triggerTurn: true, deliverAs: "steer" },
    );
  }

  function report(shown: RunView): void {
    wake("concorde-run", resultText(shown), {
      runId: shown.id,
      status: shown.status,
      result: shown.reportPath,
    });
  }

  function track(operation: RunStatus, reported = false): void {
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
    for (const operation of recordedRuns(root)) {
      if (operation.phase !== "finished" && alive(operation.host_pid))
        track(operation);
    }
    disposeProvider = subagents.registerBackgroundWorkProvider?.({
      name: SOURCE,
      listActiveWork: () => [
        ...[...tracked.values()]
          .filter((entry) => !entry.shown?.finished)
          .map((entry) => ({ id: entry.operation.run_id, sessionId })),
        ...[...rounds.entries()]
          .filter(([, entry]) => !entry.shown?.finished)
          .map(([id]) => ({ id, sessionId })),
      ],
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
      "Start a Concorde Operation (`concorde run <operation> [arguments]`) or execution command " +
      "(`concorde task-validation|delivery|scaffold [arguments]`) in the background, in the " +
      "worktree of the named task, whose workspace binding the run works on. Without a task, " +
      "an Operation that allows it (understand, survey, spec_review, spec_panel, code_review) " +
      "runs unbound on this worktree and changes no Spec or code. " +
      "It returns at once with the run identity, or with the result when the run has already " +
      "finished; the run appears in the run view, and you are woken with its result when it " +
      "finishes, within your current turn if you are still in one. Do not poll it. To block " +
      "until every running Concorde run ends, call bg_wait without an id; bg_wait with an id " +
      "sees only subagent runs.",
    promptSnippet:
      "Start a Concorde Operation or execution command in the background and be woken when it finishes",
    parameters: Type.Object({
      operation: Type.String({
        description:
          "The Operation, such as implement, or the execution command task-validation, delivery or scaffold",
      }),
      task: Type.Optional(
        Type.String({
          description:
            "The task whose worktree the run works in; omit it only for an unbound Operation",
        }),
      ),
      arguments: Type.Optional(
        Type.Array(Type.String(), {
          description: "Further arguments, such as --goal and its text",
        }),
      ),
    }),
    async execute(_id, params, signal, _onUpdate, ctx) {
      root = primaryRoot(ctx.cwd);
      // The task worktree's own copy knows the task's Specs and checks, and its workspace binding
      // tells the run what it works on.
      const worktree = params.task ? taskWorktree(root, params.task) : ctx.cwd;
      if (worktree === null)
        throw new Error(
          `task ${params.task} has no worktree in ${root}; run concorde task list to see the tasks`,
        );
      const [command, ...prefix] = concordeCommand(worktree);
      mkdirSync(runsDirectory(root), { recursive: true });
      const log = join(runsDirectory(root), `launch-${Date.now()}.log`);
      const output = openSync(log, "a");
      const child = spawn(
        command,
        [
          ...prefix,
          ...(COMMANDS.includes(params.operation) ? [] : ["run"]),
          params.operation,
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
        const operation = recordedRuns(root).find(
          (item) => item.host_pid === child.pid,
        );
        if (operation) {
          // A run that has already finished, such as one refused at once, is answered here and
          // never reported again.
          const shown = view(
            root,
            operation,
            workersOf(root, operation),
            operation.phase === "finished" || alive(operation.host_pid),
          );
          track(operation, shown.finished);
          refresh(ctx);
          const started = `Started ${params.operation} ${params.task ? `in the worktree of task ${params.task}` : "unbound"} as run ${operation.run_id} (runner process ${child.pid}).`;
          return {
            content: [
              {
                type: "text",
                text: shown.finished
                  ? `${started} It has already finished; there is nothing to wait for.\n${resultText(shown)}`
                  : `${started} You will be woken with its result; its result will be ` +
                    `${shown.reportPath}.`,
              },
            ],
            details: {
              runId: operation.run_id,
              pid: child.pid,
              finished: shown.finished,
            },
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
          ? `concorde ${params.operation} exited with status ${exited} before its run began: ${text || "(no output)"}`
          : `concorde ${params.operation} (process ${child.pid}) wrote no progress file within ${START_WAIT_MS / 1000}s; see ${log}`,
      );
    },
  });

  pi.registerTool({
    name: "concorde_task_session",
    label: "Concorde task session",
    description:
      "Start a task session for a task, answer its last round, or stop its running round " +
      "(`concorde task session <task> [--answer <text> | --stop] [--model <model>]`, run from " +
      "the primary worktree). A task session is a pi session with your configuration working in " +
      "the task worktree under Concorde's boundary; it works in rounds, each ending with a " +
      "report: delivered with the delivery commit, or escalated with the escalations it " +
      "recorded. The tool returns at once; you are woken with each round's outcome when it " +
      "ends. Do not poll it. Start task sessions only for tasks that may run in parallel, and " +
      "stay in the primary worktree while any runs.",
    promptSnippet:
      "Start, answer or stop a Concorde task session and be woken when its round ends",
    parameters: Type.Object({
      task: Type.String({ description: "The task identity" }),
      answer: Type.Optional(
        Type.String({
          description:
            "Your answer to the last round, which starts the next round with it as the prompt",
        }),
      ),
      stop: Type.Optional(
        Type.Boolean({ description: "Stop the running round" }),
      ),
      model: Type.Optional(
        Type.String({
          description: "A pi model for a new session; omit it for pi's default",
        }),
      ),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      root = primaryRoot(ctx.cwd);
      const args = [
        "task",
        "session",
        params.task,
        ...(params.answer !== undefined ? ["--answer", params.answer] : []),
        ...(params.stop ? ["--stop"] : []),
        ...(params.model ? ["--model", params.model] : []),
      ];
      const outcome = await concorde(root, args);
      if (outcome.code !== 0 || !outcome.value)
        throw new Error(
          `concorde ${args.join(" ")} failed:\n${refusalText(outcome)}`,
        );
      const value = outcome.value as {
        id: string;
        rounds: {
          round: number;
          status: string;
          supervisor_pid: number;
          started_at: string;
        }[];
      };
      const last = value.rounds[value.rounds.length - 1];
      const status: SessionStatus = {
        kind: "task-session",
        task: params.task,
        session_id: value.id,
        round: last.round,
        phase: last.status === "running" ? "running" : "finished",
        status:
          last.status === "running"
            ? null
            : (last.status as SessionStatus["status"]),
        summary: null,
        supervisor_pid: last.supervisor_pid,
        last_action: null,
        started_at: last.started_at,
        updated_at: last.started_at,
      };
      const id = roundId(status);
      if (params.stop) {
        const known = rounds.get(id);
        if (known) known.reported = true;
        return {
          content: [{ type: "text", text: sessionText(root, status) }],
          details: { session: value.id, round: last.round },
        };
      }
      if (!rounds.has(id))
        rounds.set(id, {
          status,
          shown: null,
          registered: false,
          reported: false,
        });
      refresh(ctx);
      return {
        content: [
          {
            type: "text",
            text:
              `Started round ${last.round} of the task session of ${params.task} (session ` +
              `${value.id}, supervisor process ${last.supervisor_pid}). It runs in the ` +
              "background; you will be woken with its outcome when it ends.",
          },
        ],
        details: { session: value.id, round: last.round },
      };
    },
  });

  pi.registerTool({
    name: "concorde_configure_workers",
    label: "Configure worker models",
    description:
      "Open the developer's picker for the models Concorde's pi workers use: a default and " +
      "optional overrides per Operation worker by its id, each a model and a reasoning level from " +
      "the models pi " +
      "lists. Use it when the developer asks to choose or change worker models. Without a task " +
      "it changes this worktree's configuration, which new tasks inherit; with a task it " +
      "changes only the copy in that task's worktree. The developer makes every choice in the " +
      "dialog.",
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
          "the worker model picker needs pi's interactive interface; run concorde " +
            "configure-workers instead",
        );
      const changes = await pickWorkerModels(ctx, params.task ?? null);
      return {
        content: [
          {
            type: "text",
            text: changes.length
              ? `The developer changed the worker models: ${changes.join("; ")}. Run concorde configure-workers for the result.`
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
    description:
      "List Concorde runs (Operations and execution commands) and task-session rounds of this project",
    handler: async (_args, ctx) => {
      const sessions = sessionRounds(root).map((status) => {
        const shown = sessionView(
          root,
          status,
          status.phase === "finished" || alive(status.supervisor_pid),
        );
        return `${shown.state.padEnd(9)} ${shown.label} — ${shown.finished ? (shown.preview ?? "") : shown.currentAction}`;
      });
      const lines = recordedRuns(root)
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
      const all = [...lines, ...sessions];
      ctx.ui.notify(
        all.length ? all.join("\n") : "No Concorde runs in this project yet.",
        "info",
      );
    },
  });
}
