/**
 * Concorde's extension for a pi main session.
 *
 * It lets the main agent run Operations and execution commands the way Concorde expects in pi:
 * `concorde_run` starts `concorde run <operation>` or `concorde <command>` as a detached process in
 * the task's worktree, whose workspace binding the run reads, and returns at once; every run of the
 * project, whoever started it (this tool, a command run with bash, another session), is found in
 * the current tasks' workspace folders and `.concorde/unbound/` and followed through its progress
 * files and shown in pi-subagents' FleetView as an external job. Each run has at most one owner
 * main session, the one whose `concorde_run` started it, and only the owner is woken with a
 * message when it finishes: the runs of other sessions, of task sessions and of commands run by
 * hand are shown, never reported. The runs a session owns are kept as custom entries of its
 * session file, so a resumed session keeps owning them. The runs and rounds a session owns are its
 * background work, which `bg_wait` and the drain of a `pi -p` session wait for. `/concorde` lists
 * the runs. The extension only launches and observes: the Execution runner, not this extension,
 * runs and records every run. Without pi-subagents it still launches, wakes and lists; only the
 * FleetView entries and `bg_wait` are missing.
 *
 * `concorde_task_session` starts, answers or stops a pi task session through `concorde task
 * session`, starting it with `--main` naming this session, which the session's trace node keeps as
 * the owner of every round of that task session; each round is followed the same way, through the
 * progress file its supervisor keeps and the outcome the round's trace node holds, and wakes its
 * owner, and only its owner, when it ends.
 * Inside a task session itself (`CONCORDE_TASK_SESSION` set), which may load this extension as a
 * project resource, it only marks commands as started from pi and stays otherwise inactive.
 */

import { execFile, spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
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
  chainText,
  concordeCommand,
  discoveredRuns,
  glossaryText,
  lockedInodes,
  OWNED_RUN_ENTRY,
  ownedWork,
  ownership,
  primaryRoot,
  recordedRuns,
  REPORTED_ENTRY,
  resultText,
  roundId,
  roundOutcome,
  roundOwner,
  runError,
  runnerAlive,
  type RunStatus,
  type RunView,
  sessionRounds,
  type SessionStatus,
  sessionText,
  sessionView,
  taskWorktree,
  view,
  wakes,
  workersOf,
  worktreeRoot,
} from "./pi_runs.ts";

const SOURCE = "concorde";
const POLL_MS = 2000;

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
  // Its end has been given to this session, by a wake or in the tool's own result.
  reported: boolean;
  // Started by this session's `concorde_run`: this session owns it, is woken when it ends and
  // counts it as its background work.
  owned: boolean;
}

interface TrackedRound {
  status: SessionStatus;
  shown: RunView | null;
  registered: boolean;
  reported: boolean;
  // A round of a task session started for this session, the owner its task record names.
  owned: boolean;
}

interface CommandOutcome {
  code: number;
  value: Record<string, unknown> | null;
  text: string;
}

/** Preserve every command error link in the text shown to the main agent. */
export function refusalText(outcome: CommandOutcome): string {
  const error = outcome.value?.error as Record<string, unknown> | undefined;
  if (!error) return outcome.text || `exit status ${outcome.code}`;
  const lines: string[] = [];
  const walk = (link: Record<string, unknown>, depth: number) => {
    const unhandled = link.unhandled as Record<string, string> | undefined;
    lines.push(
      `${"  ".repeat(depth)}${link.actor}: ${link.code}: ${link.detail}` +
        (unhandled
          ? ` (not handled: ${unhandled.reason}: ${unhandled.explanation})`
          : ""),
    );
    for (const option of (link.options as string[]) ?? [])
      lines.push(`${"  ".repeat(depth + 1)}option: ${option}`);
    for (const cause of (link.causes as Record<string, unknown>[]) ?? [])
      walk(cause, depth + 1);
  };
  walk(error, 0);
  return lines.join("\n");
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

export default function (pi: ExtensionAPI) {
  // Every command this session starts, through bash or a tool, tells Concorde that the main
  // session is pi, so task sessions start on pi; workers take their backend from the worktree's
  // worker configuration.
  process.env.CONCORDE_CLIENT = "pi";
  // Every session of the project, main or task session, works with the project's terms: the
  // glossary of the session's own worktree is read afresh for each prompt, so a merged or task
  // change of a definition reaches the session at once.
  pi.on("before_agent_start", async (event, ctx) => {
    const terms = glossaryText(worktreeRoot(ctx.cwd));
    if (!terms) return;
    return { systemPrompt: `${event.systemPrompt}\n\n${terms}` };
  });
  // A task session is no main session: it neither launches background runs nor watches the
  // project's runs and rounds.
  if (process.env.CONCORDE_TASK_SESSION) return;
  const tracked = new Map<string, Tracked>();
  const rounds = new Map<string, TrackedRound>();
  // The runner processes `concorde_run` has started: their runs are its to answer. While a launch
  // has not been announced yet, no run is discovered, so a run the tool is about to answer is
  // never reported twice.
  const launching = new Set<number>();
  let pendingLaunches = 0;
  let root = process.cwd();
  // When the view began following: a run started since then is reported even if it ended
  // between two looks, one finished before it only listed.
  let since = Date.now();
  // pi-subagents' name of the session, under which FleetView files its runs.
  let sessionId = "";
  // The session's own identity, which names it as the owner of the task sessions it starts.
  let mainId = "";
  // The runs and rounds whose end this session was given, kept in its session file.
  let given = new Set<string>();
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
      const owned = !!mainId && roundOwner(root, status) === mainId;
      if (known) known.status = status;
      // A round is followed while it runs; a round of this session's own that ended while the
      // session was closed is followed too, so that its end is given once.
      else if (status.phase === "running" || (owned && !given.has(id)))
        rounds.set(id, {
          status,
          shown: null,
          registered: false,
          reported: given.has(id),
          owned,
        });
    }
    for (const [id, entry] of rounds) {
      if (entry.status.phase !== "finished") {
        // The progress file holds only the current round; each round's node holds its outcome.
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
      if (wakes({ id, ...entry, finished: shown.finished })) {
        markGiven(id, entry);
        wake("concorde-task-session", sessionText(root, entry.status), {
          task: entry.status.task,
          round: entry.status.round,
          status: shown.status,
        });
      }
    }
  }

  /** Record that the end of a run or round this session owns has been given to it. */
  function markGiven(id: string, entry: { reported: boolean }): void {
    entry.reported = true;
    if (given.has(id)) return;
    given.add(id);
    try {
      pi.appendEntry(REPORTED_ENTRY, { id });
    } catch {
      // A session that cannot record it may be given the end again after a restart.
    }
  }

  function refresh(ctx?: ExtensionContext): void {
    const operations = new Map(
      recordedRuns(root).map((item) => [item.run_id, item]),
    );
    // One look at the kernel's lock table serves every run of this refresh.
    const locked = lockedInodes();
    // Runs started elsewhere, by bash or another session, are followed and shown like the tool's
    // own, but they wake nobody here.
    if (pendingLaunches === 0)
      for (const operation of discoveredRuns(
        [...operations.values()],
        new Set(tracked.keys()),
        since,
        launching,
        (run) => runnerAlive(root, run, locked),
      ))
        track(operation);
    for (const [id, entry] of tracked) {
      const operation = operations.get(id) ?? entry.operation;
      entry.operation = operation;
      const shown = view(
        root,
        operation,
        workersOf(root, operation),
        operation.phase === "finished" || runnerAlive(root, operation, locked),
      );
      publish(id, entry, shown);
      entry.shown = shown;
      if (wakes({ id, ...entry, finished: shown.finished })) {
        markGiven(id, entry);
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
    wake("concorde-run", resultText(shown, runError(root, shown.id)), {
      runId: shown.id,
      status: shown.status,
      result: shown.reportPath,
    });
  }

  function track(operation: RunStatus, reported = false, owned = false): void {
    const known = tracked.get(operation.run_id);
    if (known) {
      if (owned) known.owned = true;
      if (reported) known.reported = true;
      return;
    }
    tracked.set(operation.run_id, {
      operation,
      shown: null,
      registered: false,
      reported,
      owned,
    });
  }

  pi.on("session_start", async (_event, ctx) => {
    root = primaryRoot(ctx.cwd);
    since = Date.now();
    // pi-subagents names a session by its file, or by its identity when it is not persisted;
    // FleetView and bg_wait show only records under that same name.
    sessionId =
      ctx.sessionManager.getSessionFile() ?? ctx.sessionManager.getSessionId();
    mainId = ctx.sessionManager.getSessionId();
    // A new or replaced session starts from what its own session file says it owns.
    tracked.clear();
    rounds.clear();
    const kept = ownership(ctx.sessionManager.getEntries());
    given = kept.reported;
    subagents = await loadSubagents();
    for (const operation of recordedRuns(root)) {
      const owned = kept.runs.has(operation.run_id);
      // Its own runs whose end it was not given yet are followed even when they ended while the
      // session was closed, so the owner is given each end once.
      if (owned && !given.has(operation.run_id)) track(operation, false, true);
      else if (operation.phase !== "finished" && runnerAlive(root, operation))
        track(operation, given.has(operation.run_id), owned);
    }
    disposeProvider = subagents.registerBackgroundWorkProvider?.({
      name: SOURCE,
      // Only what this session started is its work: a `pi -p` session drains it before it exits,
      // and must not wait for the runs of other sessions it merely shows.
      listActiveWork: () =>
        ownedWork(
          [
            ...[...tracked.values()].map((entry) => ({
              id: entry.operation.run_id,
              owned: entry.owned,
              finished: entry.shown?.finished ?? false,
            })),
            ...[...rounds.entries()].map(([id, entry]) => ({
              id,
              owned: entry.owned,
              finished: entry.shown?.finished ?? false,
            })),
          ],
          sessionId,
        ),
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
      "finishes, within your current turn if you are still in one. Do not poll it. When " +
      "another run of the task still holds its workspace, add --wait <seconds> to the " +
      "arguments to queue this run behind it instead of being refused with workspace_busy. " +
      "To block " +
      "until every Concorde run you started with this tool ends, call bg_wait without an id; " +
      "bg_wait with an id " +
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
      // `--detach` starts the runner as a process of its own, which writes its output to
      // `host.out` in the run's own trace node, and prints the announced run once its progress
      // file exists; a failure before any run exists comes back here directly.
      const words = [
        ...prefix,
        ...(COMMANDS.includes(params.operation) ? [] : ["run"]),
        params.operation,
        ...(params.arguments ?? []),
        "--detach",
      ];
      pendingLaunches += 1;
      const ended = await new Promise<{
        code: number;
        stdout: string;
        stderr: string;
      }>((resolve) => {
        const child = spawn(command, words, {
          cwd: worktree,
          stdio: ["ignore", "pipe", "pipe"],
          env: { ...process.env, CONCORDE_CLIENT: "pi" },
          signal,
        });
        let stdout = "";
        let stderr = "";
        child.stdout?.on("data", (chunk) => (stdout += chunk));
        child.stderr?.on("data", (chunk) => (stderr += chunk));
        child.on("error", (error) =>
          resolve({ code: -1, stdout, stderr: stderr + String(error) }),
        );
        child.on("close", (code) =>
          resolve({ code: code ?? -1, stdout, stderr }),
        );
      }).finally(() => (pendingLaunches -= 1));
      let announced: Record<string, unknown> | null = null;
      try {
        announced = JSON.parse(ended.stdout);
      } catch {
        announced = null;
      }
      if (
        ended.code !== 0 ||
        !announced ||
        typeof announced.run_id !== "string"
      ) {
        const error = announced?.error as Record<string, unknown> | undefined;
        throw new Error(
          `concorde ${params.operation} did not start its run (exit status ${ended.code})` +
            (error
              ? `:\n${chainText(error)}`
              : `: ${(ended.stderr || ended.stdout).trim().slice(-4000) || "(no output)"}`),
        );
      }
      const runId = announced.run_id as string;
      const folder = announced.trace as string;
      let progress: RunStatus | null = null;
      try {
        progress = JSON.parse(
          readFileSync(join(folder, "status.json"), "utf-8"),
        );
      } catch {
        progress = null;
      }
      if (!progress)
        throw new Error(
          `concorde ${params.operation} announced run ${runId}, whose progress file ` +
            `${announced.progress} cannot be read`,
        );
      const operation = { ...progress, folder };
      // A run that has already finished, such as one refused at once, is answered here and
      // never reported again.
      const shown = view(
        root,
        operation,
        workersOf(root, operation),
        operation.phase === "finished" || runnerAlive(root, operation),
      );
      try {
        pi.appendEntry(OWNED_RUN_ENTRY, { id: runId });
      } catch {
        // Without the entry the session owns the run until it ends or pi closes.
      }
      track(operation, shown.finished, true);
      if (shown.finished) markGiven(runId, tracked.get(runId)!);
      refresh(ctx);
      const started = `Started ${params.operation} ${params.task ? `in the worktree of task ${params.task}` : "unbound"} as run ${runId} (runner process ${announced.host_pid}).`;
      return {
        content: [
          {
            type: "text",
            text: shown.finished
              ? `${started} It has already finished; there is nothing to wait for.\n${resultText(shown, runError(root, runId))}`
              : `${started} You will be woken with its result; its result will be ` +
                `${shown.reportPath}.`,
          },
        ],
        details: {
          runId,
          pid: announced.host_pid,
          finished: shown.finished,
        },
      };
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
      "recorded. The tool returns at once. The session you start it from owns every round of " +
      "that task session, whoever answers it, and only the owner is woken with each round's " +
      "outcome when it ends. Do not poll it. Start task sessions only for tasks that may run " +
      "in parallel, and stay in the primary worktree while any runs.",
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
        // A new task session is started for this session, which owns its rounds.
        ...(params.answer === undefined && !params.stop && mainId
          ? ["--main", mainId]
          : []),
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
        // The owner stopping its own round is given the outcome here; a round another session
        // stops still wakes its owner.
        if (mainId && roundOwner(root, status) === mainId)
          markGiven(id, rounds.get(id) ?? { reported: false });
        return {
          content: [{ type: "text", text: sessionText(root, status) }],
          details: { session: value.id, round: last.round },
        };
      }
      const owner = roundOwner(root, status);
      const owned = !!mainId && owner === mainId;
      const known = rounds.get(id);
      if (known) known.owned = owned;
      else
        rounds.set(id, {
          status,
          shown: null,
          registered: false,
          reported: false,
          owned,
        });
      refresh(ctx);
      const started =
        `Started round ${last.round} of the task session of ${params.task} (session ` +
        `${value.id}, supervisor process ${last.supervisor_pid}). It runs in the background; `;
      return {
        content: [
          {
            type: "text",
            text: owned
              ? `${started}you will be woken with its outcome when it ends.`
              : `${started}its owner is ${owner ? `the main session ${owner}` : "no main session"}, ` +
                "which alone is woken when it ends, so you will not be woken: the run view " +
                `shows it, and concorde task show ${params.task} gives its outcome once it has ended.`,
          },
        ],
        details: { session: value.id, round: last.round, owner },
      };
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
            operation.phase === "finished" || runnerAlive(root, operation),
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
