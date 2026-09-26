/**
 * The pure part of Concorde's pi run view: read the progress files of Operation runs and their
 * workers, pair them, and describe each run for pi-subagents' FleetView; and the same for the
 * rounds of pi task sessions.
 *
 * An Operation run's `status.json` is written by the Operation host; each worker run it launches
 * writes its own `status.json` with the same `host_pid`, which is how a worker is found for its
 * Operation. A task session's round is described by the `status.json` its supervisor keeps under
 * `.concorde/tasks/<task>.session/`, and its outcome by the task record. This module imports only
 * Node's own modules so the host's tests can run it under Node.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, realpathSync } from "node:fs";
import { dirname, join } from "node:path";

export interface OperationStatus {
  kind: "operation";
  run_id: string;
  operation: string;
  task: string | null;
  modules: string[];
  phase: "running" | "finished";
  step: string | null;
  status: "ok" | "blocked" | "failed" | null;
  summary?: string;
  host_pid: number;
  started_at: string;
  updated_at: string;
}

export interface WorkerStatus {
  run_id: string;
  task_type: string;
  backend: string;
  phase: string;
  round: number;
  last_action: { tool: string; target: string; at: string } | null;
  status: string | null;
  host_pid: number;
  started_at: string;
  updated_at: string;
}

export type RunState = "running" | "completed" | "failed" | "stopped";

export interface RunView {
  id: string;
  label: string;
  state: RunState;
  finished: boolean;
  status: string | null;
  currentAction: string;
  preview?: string;
  reportPath: string;
  startedAt: number;
  updatedAt: number;
  endedAt?: number;
}

const TEXT = 160;

function readJson(path: string): Record<string, unknown> | null {
  try {
    return JSON.parse(readFileSync(path, "utf-8"));
  } catch {
    return null;
  }
}

/** The primary worktree of the repository `cwd` belongs to, where every run is recorded. */
export function primaryRoot(cwd: string): string {
  try {
    const common = execFileSync(
      "git",
      ["rev-parse", "--path-format=absolute", "--git-common-dir"],
      {
        cwd,
        encoding: "utf-8",
        stdio: ["ignore", "pipe", "ignore"],
      },
    ).trim();
    return dirname(realpathSync(common));
  } catch {
    return cwd;
  }
}

export function runsDirectory(root: string): string {
  return join(root, ".concorde", "runs");
}

function statuses(root: string): Record<string, unknown>[] {
  const directory = runsDirectory(root);
  if (!existsSync(directory)) return [];
  const found: Record<string, unknown>[] = [];
  for (const name of readdirSync(directory)) {
    const value = readJson(join(directory, name, "status.json"));
    if (value) found.push(value);
  }
  return found;
}

/** Every Operation run with a progress file, oldest first. */
export function operationRuns(root: string): OperationStatus[] {
  return (
    statuses(root).filter(
      (value) => value.kind === "operation",
    ) as unknown as OperationStatus[]
  ).sort((a, b) => a.started_at.localeCompare(b.started_at));
}

/** The worker runs an Operation run launched: same host process, started after it; oldest first. */
export function workersOf(
  root: string,
  operation: OperationStatus,
): WorkerStatus[] {
  return (
    statuses(root).filter(
      (value) => value.kind !== "operation",
    ) as unknown as WorkerStatus[]
  )
    .filter(
      (worker) =>
        worker.host_pid === operation.host_pid &&
        worker.started_at >= operation.started_at,
    )
    .sort((a, b) => a.started_at.localeCompare(b.started_at));
}

/** Whether a process is alive; a process owned by another user counts as alive. */
export function alive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return (error as { code?: string }).code === "EPERM";
  }
}

function clip(text: string, limit = TEXT): string {
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

/** One run as FleetView shows it. `hostAlive` is whether the host process still runs. */
export function view(
  root: string,
  operation: OperationStatus,
  workers: WorkerStatus[],
  hostAlive: boolean,
): RunView {
  const worker = workers.at(-1);
  const finished = operation.phase === "finished";
  let state: RunState = "running";
  let status = operation.status;
  let preview: string | undefined;
  if (finished) {
    state =
      status === "ok"
        ? "completed"
        : status === "blocked"
          ? "stopped"
          : "failed";
    preview = `${status}: ${operation.summary ?? ""}`;
  } else if (!hostAlive) {
    state = "failed";
    status = "failed";
    preview = `failed: the Operation host (process ${operation.host_pid}) ended without finishing the run`;
  }
  let action = operation.step ?? (finished ? "finished" : "starting");
  if (!finished && worker && worker.phase !== "finished") {
    action += ` · ${worker.task_type} worker (${worker.backend}) round ${worker.round} · ${worker.phase}`;
    if (worker.last_action) {
      action +=
        `: ${worker.last_action.tool} ${worker.last_action.target}`.trimEnd();
    }
  }
  return {
    id: operation.run_id,
    label: clip(`${operation.task ?? "no task"} · ${operation.operation}`),
    state,
    finished: finished || !hostAlive,
    status,
    currentAction: clip(action),
    preview: preview ? clip(preview, 4096) : undefined,
    reportPath: join(runsDirectory(root), operation.run_id, "result.json"),
    startedAt: Date.parse(operation.started_at),
    updatedAt: Date.parse(
      worker && worker.updated_at > operation.updated_at
        ? worker.updated_at
        : operation.updated_at,
    ),
    endedAt: finished ? Date.parse(operation.updated_at) : undefined,
  };
}

/** What the main agent is told about a finished run: its status, summary and result file. */
export function resultText(shown: RunView): string {
  return (
    `Concorde run ${shown.id} (${shown.label}) finished ${shown.status}. ` +
    `${shown.preview ?? ""}\nRead the Operation result: ${shown.reportPath}`
  );
}

/** The `concorde` command of a project: its installed command, a source checkout, or PATH. */
/**
 * The worktree of `task` from its record in the primary worktree `root`, when the record names
 * one that exists: every Concorde command of a task runs there, with that worktree's own copy.
 */
export function taskWorktree(root: string, task: string): string | null {
  if (!/^[a-z0-9][a-z0-9-]{0,47}$/.test(task)) return null;
  const record = readJson(join(root, ".concorde", "tasks", `${task}.json`));
  const worktree = record?.worktree;
  return typeof worktree === "string" && existsSync(worktree) ? worktree : null;
}

export function concordeCommand(root: string): string[] {
  const installed = join(root, ".concorde", "bin", "concorde");
  if (existsSync(installed)) return [installed];
  const source = join(root, "scripts", "concorde.py");
  if (existsSync(source)) return ["python3", source];
  return ["concorde"];
}

/** A round of a pi task session, from the progress file its supervisor keeps. */
export interface SessionStatus {
  kind: "task-session";
  task: string;
  session_id: string;
  round: number;
  phase: "running" | "finished";
  status: "delivered" | "escalated" | "failed" | "stopped" | null;
  summary: string | null;
  supervisor_pid: number;
  last_action: { tool: string; target: string; at: string } | null;
  started_at: string;
  updated_at: string;
}

function tasksDirectory(root: string): string {
  return join(root, ".concorde", "tasks");
}

/** The current round of every pi task session of the project, oldest first. */
export function sessionRounds(root: string): SessionStatus[] {
  const directory = tasksDirectory(root);
  if (!existsSync(directory)) return [];
  const found: SessionStatus[] = [];
  for (const name of readdirSync(directory)) {
    if (!name.endsWith(".session")) continue;
    const value = readJson(join(directory, name, "status.json"));
    if (value?.kind === "task-session")
      found.push(value as unknown as SessionStatus);
  }
  return found.sort((a, b) => a.started_at.localeCompare(b.started_at));
}

/** The identity FleetView files a round under. */
export function roundId(status: {
  task: string;
  session_id: string;
  round: number;
}): string {
  return `${status.task}:${status.session_id}:${status.round}`;
}

/** One round as FleetView shows it. `supervisorAlive` is whether its supervisor still runs. */
export function sessionView(
  root: string,
  status: SessionStatus,
  supervisorAlive: boolean,
): RunView {
  const finished = status.phase === "finished";
  let state: RunState = "running";
  let outcome: string | null = status.status;
  let preview: string | undefined;
  if (finished) {
    state =
      outcome === "delivered"
        ? "completed"
        : outcome === "escalated" || outcome === "stopped"
          ? "stopped"
          : "failed";
    preview = `${outcome}: ${status.summary ?? ""}`;
  } else if (!supervisorAlive) {
    state = "failed";
    outcome = "failed";
    preview = `failed: the supervisor (process ${status.supervisor_pid}) ended without recording the round`;
  }
  let action = finished ? "finished" : `round ${status.round}`;
  if (!finished && status.last_action) {
    action +=
      ` · ${status.last_action.tool} ${status.last_action.target}`.trimEnd();
  }
  return {
    id: roundId(status),
    label: clip(`${status.task} · task session round ${status.round}`),
    state,
    finished: finished || !supervisorAlive,
    status: outcome,
    currentAction: clip(action),
    preview: preview ? clip(preview, 4096) : undefined,
    reportPath: join(tasksDirectory(root), `${status.task}.json`),
    startedAt: Date.parse(status.started_at),
    updatedAt: Date.parse(status.updated_at),
    endedAt: finished ? Date.parse(status.updated_at) : undefined,
  };
}

function recordedRound(
  root: string,
  status: { task: string; session_id: string; round: number },
): Record<string, unknown> | null {
  const record = readJson(join(tasksDirectory(root), `${status.task}.json`));
  const session = (
    (record?.sessions as Record<string, unknown>[] | undefined) ?? []
  ).find((item) => item.id === status.session_id);
  return (
    ((session?.rounds as Record<string, unknown>[] | undefined) ?? []).find(
      (item) => item.round === status.round,
    ) ?? null
  );
}

/** The outcome the task record holds for a round, or null while it is running or unknown. */
export function roundOutcome(
  root: string,
  status: { task: string; session_id: string; round: number },
): { status: NonNullable<SessionStatus["status"]>; summary: string } | null {
  const round = recordedRound(root, status);
  if (!round || round.status === "running") return null;
  const report = round.report as Record<string, unknown> | null;
  const error = round.error as Record<string, unknown> | null;
  return {
    status: round.status as NonNullable<SessionStatus["status"]>,
    summary: String(report?.summary ?? error?.detail ?? ""),
  };
}

/** An error link and its causes as indented text, one line per link. */
export function chainText(link: Record<string, unknown>, depth = 0): string {
  const unhandled = link.unhandled as Record<string, string> | undefined;
  const lines = [
    `${"  ".repeat(depth)}${link.actor}: ${link.code}: ${link.detail}` +
      (unhandled ? ` (not handled: ${unhandled.explanation})` : ""),
  ];
  for (const option of (link.options as string[]) ?? [])
    lines.push(`${"  ".repeat(depth + 1)}option: ${option}`);
  for (const cause of (link.causes as Record<string, unknown>[]) ?? [])
    lines.push(chainText(cause, depth + 1));
  return lines.join("\n");
}

/** What the main agent is told when a round ends: the outcome the task record holds. */
export function sessionText(root: string, status: SessionStatus): string {
  const head = `Task session of ${status.task}, round ${status.round}`;
  const round = recordedRound(root, status);
  if (!round || round.status === "running")
    return (
      `${head} ended without recording its outcome (supervisor process ` +
      `${status.supervisor_pid}). Run concorde task show ${status.task}; the next ` +
      "concorde task session command records the round as failed with its logs."
    );
  const report = (round.report as Record<string, unknown> | null) ?? null;
  const lines = [`${head} ended ${round.status}.`];
  if (report?.summary) lines.push(`Summary: ${report.summary}`);
  for (const [key, title] of [
    ["decisions", "Decisions it made"],
    ["open", "Still open"],
  ] as const) {
    const items = (report?.[key] as string[] | undefined) ?? [];
    if (items.length)
      lines.push(`${title}:\n${items.map((item) => `- ${item}`).join("\n")}`);
  }
  if (round.status === "delivered")
    lines.push(
      `Delivery commit: ${report?.commit}. Merge it with concorde task merge ${status.task} when the work is complete.`,
    );
  if (round.status === "escalated")
    lines.push(
      `Escalations: ${((report?.escalations as number[]) ?? []).join(", ")}; read their chains with ` +
        `concorde task show ${status.task}. Answer with concorde_task_session (answer), or ` +
        "escalate to the developer with your own link on top.",
    );
  if (round.status === "failed" && round.error)
    lines.push(
      `Error chain:\n${chainText(round.error as Record<string, unknown>)}`,
    );
  if (round.status === "stopped") lines.push("The round was stopped.");
  lines.push(
    `Task record: ${join(tasksDirectory(root), `${status.task}.json`)}`,
  );
  return lines.join("\n");
}
