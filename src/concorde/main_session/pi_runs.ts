/**
 * The pure part of Concorde's pi run view: read the progress files of Operation runs and their
 * workers, pair them, and describe each run for pi-subagents' FleetView.
 *
 * An Operation run's `status.json` is written by the Operation host; each worker run it launches
 * writes its own `status.json` with the same `host_pid`, which is how a worker is found for its
 * Operation. This module imports only Node's own modules so the host's tests can run it under Node.
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
    label: clip(`${operation.task ?? "?"} · ${operation.operation}`),
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

/** The `concorde` command of a project: its installed command, a source checkout, or PATH. */
export function concordeCommand(root: string): string[] {
  const installed = join(root, ".concorde", "bin", "concorde");
  if (existsSync(installed)) return [installed];
  const source = join(root, "scripts", "concorde.py");
  if (existsSync(source)) return ["python3", source];
  return ["concorde"];
}
