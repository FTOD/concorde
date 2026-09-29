/**
 * The pure part of Concorde's pi run view: read the progress files of the runs recorded in the
 * project's run store (Operations and execution commands) and their workers, pair them, and
 * describe each run for pi-subagents' FleetView; and the same for the rounds of pi task sessions.
 *
 * A run is a trace node: `runs/<run-id>/` of a current task's workspace folder, `run/` of one of
 * its workflow's steps, or `.concorde/unbound/<run-id>/`. Its `status.json` is written by the
 * Execution runner; each worker run it launches is a node `workers/<worker run>/` inside it, with
 * its own `status.json`. Whether a runner still lives is read from its run lock
 * `.concorde/locks/runs/<run-id>.lock`, which exists and is held with `flock` exactly while the
 * runner runs, never from `host_pid`, which is only meaningful in the PID namespace the runner ran
 * in. A task session's round is described by the `status.json` its supervisor keeps in the
 * session's node `.concorde/tasks/<task>/sessions/<session>/`, and its outcome by the round's node
 * `rounds/<n>/`. This module imports only Node's own modules so the host's tests can run it under
 * Node.
 */

import { execFileSync } from "node:child_process";
import {
  existsSync,
  readdirSync,
  readFileSync,
  realpathSync,
  statSync,
} from "node:fs";
import { dirname, join } from "node:path";

export interface RunStatus {
  kind: "operation" | "command";
  run_id: string;
  name: string;
  workspace: string | null;
  modules: string[];
  phase: "running" | "finished";
  step: string | null;
  status: "ok" | "blocked" | "failed" | null;
  summary?: string;
  waiting_for?: string | null;
  host_pid: number;
  started_at: string;
  updated_at: string;
  /** The run's trace node folder, where the view found its progress file. */
  folder: string;
}

export interface WorkerStatus {
  run_id: string;
  operation_run_id: string | null;
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

/** The primary worktree of the repository `cwd` belongs to, whose records directory holds the
 * runs of every task's workspace. */
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

/** The worktree a session works in: Git's top level of its directory, or the directory itself. */
export function worktreeRoot(cwd: string): string {
  try {
    return execFileSync("git", ["rev-parse", "--show-toplevel"], {
      cwd,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return cwd;
  }
}

interface GlossaryEntry {
  id: string;
  title: string;
  owner: string;
  definition: string;
}

/**
 * The project's terms as a system-prompt section: every entry of the glossary the root Module
 * declares, sorted by title, with the rule to use each exactly as defined. `null` when the
 * worktree declares no glossary or it cannot be read; a malformed Spec is Spec validation's to
 * report, never a reason to stop a session.
 */
export function glossaryText(root: string): string | null {
  try {
    const registry = JSON.parse(
      readFileSync(join(root, ".concorde", "specs.json"), "utf-8"),
    );
    const declared = (registry.modules ?? []).find(
      (record: Record<string, unknown>) => typeof record.glossary === "string",
    );
    if (!declared) return null;
    const path: string = declared.glossary;
    const concepts: GlossaryEntry[] = JSON.parse(
      readFileSync(join(root, path), "utf-8"),
    ).concepts;
    const lines = [...concepts]
      .sort((a, b) => a.title.localeCompare(b.title))
      .map(
        (entry) =>
          `- **${entry.title}** (\`${entry.id}\`, ${entry.owner}): ` +
          entry.definition.replace(/\[([^\]]*)\]\(#[^)]*\)/g, "$1"),
      );
    return (
      "## Project terms\n\n" +
      `This project defines each of its terms once, in its glossary \`${path}\`. Use every ` +
      "term exactly with the meaning given here, with the developer and in task goals, " +
      "decision logs, escalations, commit messages and Specs. Do not coin a synonym for a " +
      "defined term or use one in another sense; when a word you need is missing or its " +
      "definition no longer fits, say so and change the glossary through a task.\n\n" +
      lines.join("\n") +
      "\n"
    );
  } catch {
    return null;
  }
}

function entries(directory: string): string[] {
  try {
    return readdirSync(directory).sort();
  } catch {
    return [];
  }
}

/** The locks directory of the project, where every run lock lies. */
export function locksDirectory(root: string): string {
  return join(root, ".concorde", "locks");
}

/**
 * The folder of every run of the project's current tasks and of its unbound runs: `runs/*` and
 * `workflow/steps/*\/run` of each task's workspace folder, and `.concorde/unbound/*`.
 */
export function runFolders(root: string): string[] {
  const base = join(root, ".concorde");
  const found: string[] = [];
  for (const task of entries(join(base, "tasks"))) {
    const workspace = join(base, "tasks", task, "workspace");
    for (const run of entries(join(workspace, "runs")))
      found.push(join(workspace, "runs", run));
    for (const step of entries(join(workspace, "workflow", "steps"))) {
      const run = join(workspace, "workflow", "steps", step, "run");
      if (existsSync(run)) found.push(run);
    }
  }
  for (const run of entries(join(base, "unbound")))
    found.push(join(base, "unbound", run));
  return found;
}

function isRun(value: Record<string, unknown>): boolean {
  return value.kind === "operation" || value.kind === "command";
}

/** Every run of an Operation or execution command with a progress file, oldest first. */
export function recordedRuns(root: string): RunStatus[] {
  const found: RunStatus[] = [];
  for (const folder of runFolders(root)) {
    const value = readJson(join(folder, "status.json"));
    if (value && isRun(value))
      found.push({ ...(value as unknown as RunStatus), folder });
  }
  return found.sort((a, b) => a.started_at.localeCompare(b.started_at));
}

/** The folder of the run `runId`, or null when the project holds none. */
export function runFolder(root: string, runId: string): string | null {
  for (const folder of runFolders(root)) {
    if (folder.endsWith(`/${runId}`)) return folder;
    if (readJson(join(folder, "status.json"))?.run_id === runId) return folder;
  }
  return null;
}

/**
 * The runs of the store the view does not follow yet but should, whoever started them: every
 * run still running with a live runner, and every run started since the view began at `since`
 * (milliseconds), even one that ended between two looks. Runs whose runner process is one the
 * view is launching itself are left to the tool that launches them, which answers a run that
 * ended at once in its own result.
 */
export function discoveredRuns(
  runs: RunStatus[],
  known: Set<string>,
  since: number,
  launching: Set<number>,
  isAlive: (run: RunStatus) => boolean,
): RunStatus[] {
  return runs.filter(
    (run) =>
      !known.has(run.run_id) &&
      !launching.has(run.host_pid) &&
      ((run.phase === "running" && isAlive(run)) ||
        Date.parse(run.started_at) >= since),
  );
}

/** One run or task-session round the view follows, as far as its background work goes. */
export interface Followed {
  id: string;
  /** Owned by this session: a run its own `concorde_run` started, or a round of a task session
   * started for it. */
  owned: boolean;
  finished: boolean;
}

/** The custom session entry naming a run this session's `concorde_run` started, which it owns. */
export const OWNED_RUN_ENTRY = "concorde-owned-run";
/** The custom session entry naming a run or round whose end this session has been given. */
export const REPORTED_ENTRY = "concorde-reported";

/**
 * What a session owns and has been given, from the custom entries the run view appended to its
 * session file: the runs its `concorde_run` started, and the runs and rounds whose end it was
 * given. Read when a session starts, so a resumed session keeps owning its runs and is given the
 * end of one that ended while it was closed, but never an end it was already given.
 */
export function ownership(
  entries: { type?: string; customType?: string; data?: unknown }[],
): { runs: Set<string>; reported: Set<string> } {
  const runs = new Set<string>();
  const reported = new Set<string>();
  for (const entry of entries) {
    if (entry.type !== "custom") continue;
    const id = (entry.data as { id?: unknown } | undefined)?.id;
    if (typeof id !== "string") continue;
    if (entry.customType === OWNED_RUN_ENTRY) runs.add(id);
    if (entry.customType === REPORTED_ENTRY) reported.add(id);
  }
  return { runs, reported };
}

/**
 * Whether a followed run or round wakes this session now: it has ended, this session owns it, and
 * its end has not been given yet. A run or round of another session, of a task session or of a
 * command run by hand is shown but never wakes this session.
 */
export function wakes(entry: Followed & { reported: boolean }): boolean {
  return entry.owned && entry.finished && !entry.reported;
}

/**
 * The background work this session owns, which pi-subagents' `bg_wait` and the auto-drain of a
 * `pi -p` session wait for: the runs and task-session rounds it owns that have not finished. A run
 * or round it only follows, started with bash or by another session, is shown but never its work,
 * so a `pi -p` session never waits for another session's runs before it exits.
 */
export function ownedWork(
  followed: Followed[],
  sessionId: string,
): { id: string; sessionId: string }[] {
  return followed
    .filter((entry) => entry.owned && !entry.finished)
    .map((entry) => ({ id: entry.id, sessionId }));
}

/** The worker runs a run launched, whose nodes lie in its folder's `workers/`; oldest first. */
export function workersOf(_root: string, operation: RunStatus): WorkerStatus[] {
  const directory = join(operation.folder, "workers");
  const found: WorkerStatus[] = [];
  for (const name of entries(directory)) {
    const value = readJson(join(directory, name, "status.json"));
    if (value) found.push(value as unknown as WorkerStatus);
  }
  return found.sort((a, b) => a.started_at.localeCompare(b.started_at));
}

/**
 * The inode numbers of the files and directories on which some process holds an exclusive
 * `flock`, from the kernel's lock table `/proc/locks`, whichever PID namespace the holder runs
 * in; null where the kernel offers no such table. Shared locks are left out: they are readers
 * probing a lock for an instant, never a runner. Only the inode number is compared, since the
 * device the table names differs from the one `stat` reports on some file systems, such as btrfs
 * subvolumes.
 */
export function lockedInodes(): Set<string> | null {
  let table: string;
  try {
    table = readFileSync("/proc/locks", "utf-8");
  } catch {
    return null;
  }
  const found = new Set<string>();
  for (const line of table.split("\n")) {
    // `1: FLOCK  ADVISORY  WRITE 4242 08:02:5767891 0 EOF`; a waiter's line has `->` after the
    // number and holds nothing.
    const fields = line.trim().split(/\s+/);
    if (fields[1] !== "FLOCK" || fields[3] !== "WRITE") continue;
    const inode = fields[5]?.split(":")[2];
    if (inode) found.add(inode);
  }
  return found;
}

/**
 * Whether the runner of `run` still lives: its run lock file `.concorde/locks/runs/<run-id>.lock`
 * exists and some process holds it with an exclusive `flock`, from before the run's first progress
 * file until after its result; the runner removes the file as it exits. A run whose result is
 * already written counts as alive, so a run that ended properly after its progress file was read
 * is not taken for one that died; its finished progress file is read on the next look. Where the
 * kernel shows no lock table, the recorded process identifier is the only sign left.
 */
export function runnerAlive(
  root: string,
  run: RunStatus,
  locked: Set<string> | null = lockedInodes(),
): boolean {
  if (existsSync(join(run.folder, "result.json"))) return true;
  const lock = join(locksDirectory(root), "runs", `${run.run_id}.lock`);
  if (!existsSync(lock)) return false;
  if (locked === null) return alive(run.host_pid);
  try {
    return locked.has(statSync(lock, { bigint: true }).ino.toString());
  } catch {
    return false;
  }
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
  operation: RunStatus,
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
    preview =
      "failed: the runner ended without finishing the run: it no longer holds its run lock " +
      "and wrote no result";
  }
  let action = operation.step ?? (finished ? "finished" : "starting");
  if (!finished && operation.waiting_for) {
    action = `waiting for the workspace lock held by ${operation.waiting_for}`;
  }
  if (!finished && worker && worker.phase !== "finished") {
    action += ` · ${worker.task_type} worker (${worker.backend}) round ${worker.round} · ${worker.phase}`;
    if (worker.last_action) {
      action +=
        `: ${worker.last_action.tool} ${worker.last_action.target}`.trimEnd();
    }
  }
  return {
    id: operation.run_id,
    label: clip(`${operation.workspace ?? "unbound"} · ${operation.name}`),
    state,
    finished: finished || !hostAlive,
    status,
    currentAction: clip(action),
    preview: preview ? clip(preview, 4096) : undefined,
    reportPath: join(operation.folder, "result.json"),
    startedAt: Date.parse(operation.started_at),
    updatedAt: Date.parse(
      worker && worker.updated_at > operation.updated_at
        ? worker.updated_at
        : operation.updated_at,
    ),
    endedAt: finished ? Date.parse(operation.updated_at) : undefined,
  };
}

/** The error chain a run's saved result carries, or null when it has none or none is saved. */
export function runError(
  root: string,
  runId: string,
): Record<string, unknown> | null {
  const folder = runFolder(root, runId);
  const error = folder ? readJson(join(folder, "result.json"))?.error : null;
  return error && typeof error === "object"
    ? (error as Record<string, unknown>)
    : null;
}

/**
 * What the main agent is told about a finished run: its status, summary and result file, and the
 * whole error chain of a result that carries one.
 */
export function resultText(
  shown: RunView,
  error: Record<string, unknown> | null = null,
): string {
  return (
    `Concorde run ${shown.id} (${shown.label}) finished ${shown.status}. ` +
    `${shown.preview ?? ""}\nRead the run result: ${shown.reportPath}` +
    (error ? `\nError chain:\n${chainText(error)}` : "")
  );
}

/**
 * The worktree of `task` from its record in the primary worktree `root`, when the record names
 * one that exists: every Concorde command of a task runs there, with that worktree's own copy.
 */
export function taskWorktree(root: string, task: string): string | null {
  if (!/^[a-z0-9][a-z0-9-]{0,47}$/.test(task)) return null;
  const record = readJson(join(root, ".concorde", "tasks", task, "task.json"));
  const worktree = record?.worktree;
  return typeof worktree === "string" && existsSync(worktree) ? worktree : null;
}

/**
 * An optional text argument of a tool as it was given: absent when it is missing, empty or only
 * whitespace, since a model may fill an optional field it means to leave out with an empty string.
 */
export function givenText(value: string | undefined): string | undefined {
  return value === undefined || value.trim() === "" ? undefined : value;
}

/**
 * The arguments of `concorde task session` for a call of the `concorde_task_session` tool. An
 * empty `answer` or `model` is left out as absent; a start, neither an answer nor a stop, names
 * the main session `mainId` with `--main` as the owner of the task session's rounds.
 */
export function taskSessionArgs(
  params: { task: string; answer?: string; stop?: boolean; model?: string },
  mainId: string,
): string[] {
  const answer = givenText(params.answer);
  const model = givenText(params.model);
  return [
    "task",
    "session",
    params.task,
    ...(answer !== undefined ? ["--answer", answer] : []),
    ...(params.stop ? ["--stop"] : []),
    ...(model !== undefined ? ["--model", model] : []),
    ...(answer === undefined && !params.stop && mainId
      ? ["--main", mainId]
      : []),
  ];
}

/** The `concorde` command of a project: its installed command, a source checkout, or PATH. */
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

/** The current round of every pi task session of the project's current tasks, oldest first. */
export function sessionRounds(root: string): SessionStatus[] {
  const directory = tasksDirectory(root);
  const found: SessionStatus[] = [];
  for (const task of entries(directory)) {
    for (const session of entries(join(directory, task, "sessions"))) {
      const value = readJson(
        join(directory, task, "sessions", session, "status.json"),
      );
      if (value?.kind === "task-session")
        found.push(value as unknown as SessionStatus);
    }
  }
  return found.sort((a, b) => a.started_at.localeCompare(b.started_at));
}

/** The node of a round of a pi task session. */
export function roundFolder(
  root: string,
  status: { task: string; session_id: string; round: number },
): string {
  return join(
    tasksDirectory(root),
    status.task,
    "sessions",
    status.session_id,
    "rounds",
    String(status.round),
  );
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
    reportPath: join(roundFolder(root, status), "trace.json"),
    startedAt: Date.parse(status.started_at),
    updatedAt: Date.parse(status.updated_at),
    endedAt: finished ? Date.parse(status.updated_at) : undefined,
  };
}

/** The content of a task session's node, `sessions/<session>/` of its task's folder. */
function recordedSession(
  root: string,
  status: { task: string; session_id: string },
): Record<string, unknown> | null {
  const node = readJson(
    join(
      tasksDirectory(root),
      status.task,
      "sessions",
      status.session_id,
      "trace.json",
    ),
  );
  const data = (node?.content as Record<string, unknown> | undefined)?.data;
  return data && typeof data === "object"
    ? (data as Record<string, unknown>)
    : null;
}

/**
 * The main session that owns every round of a task session, whoever answered it: the `main` the
 * session's trace node holds, given with `--main` when it was started, or null when it was
 * started without one, whose rounds wake no main session.
 */
export function roundOwner(
  root: string,
  status: { task: string; session_id: string },
): string | null {
  const main = recordedSession(root, status)?.main;
  return typeof main === "string" && main ? main : null;
}

/** A round as its node records it: its outcome as `status`, its report and error. */
function recordedRound(
  root: string,
  status: { task: string; session_id: string; round: number },
): Record<string, unknown> | null {
  const node = readJson(join(roundFolder(root, status), "trace.json"));
  const data = (node?.content as Record<string, unknown> | undefined)?.data as
    Record<string, unknown> | undefined;
  if (!node || !data) return null;
  return { status: data.outcome, report: data.report, error: node.error };
}

/** The outcome the round's node holds, or null while it is running or unknown. */
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

/** What the main agent is told when a round ends: the outcome the round's node holds. */
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
  lines.push(`Round node: ${roundFolder(root, status)}`);
  return lines.join("\n");
}
