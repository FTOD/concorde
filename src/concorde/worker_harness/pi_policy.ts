/**
 * Path decisions of the Concorde permission extension for pi workers.
 *
 * Pure functions over the run's policy (see the Workers Module's pi run mechanics): how a tool's
 * path argument resolves, and whether a read, a write or a search root is allowed. They import only
 * Node's own modules so the host's tests can run them under Node without pi. Every function returns
 * `null` to allow, or the reason of a denial as the worker should read it.
 */

import {
  existsSync,
  lstatSync,
  readlinkSync,
  realpathSync,
  statSync,
} from "node:fs";
import {
  basename,
  dirname,
  isAbsolute,
  join,
  normalize,
  resolve,
  sep,
} from "node:path";
import { fileURLToPath } from "node:url";

export interface Policy {
  worktree: string;
  rw: string[];
  ro: string[];
  names: string[];
  hidden: string[];
  own: string[];
  runtime: string[];
  git: string[];
  primary: string;
  userHome: string;
  sandbox: { denyRead: string[]; allowRead: string[]; allowWrite: string[] };
  programs: { rg: string; fd: string };
  limits: { maxTurns: number; maxBudgetUsd: number | null };
  resultSchema: Record<string, unknown>;
}

const UNICODE_SPACES = /[  -   　]/g;

/** Resolve a tool's path argument the way pi's own tools resolve it. */
export function resolveLikePi(
  input: string,
  cwd: string,
  home: string,
): string {
  let value = input.replace(UNICODE_SPACES, " ");
  if (value.startsWith("@")) value = value.slice(1);
  if (value === "~") value = home;
  else if (value.startsWith("~/")) value = join(home, value.slice(2));
  if (value.startsWith("file://")) value = fileURLToPath(value);
  return isAbsolute(value) ? normalize(value) : resolve(cwd, value);
}

/**
 * The path with every symbolic link resolved, the final one included, as far as the links exist:
 * a link whose target does not exist yet resolves to that target, the file a write through it
 * would create.
 */
export function realOf(path: string, depth = 0): string {
  if (existsSync(path)) return realpathSync(path);
  const parent = dirname(path);
  if (parent === path) return path;
  const inParent = join(realOf(parent, depth), basename(path));
  let link = false;
  try {
    link = lstatSync(inParent).isSymbolicLink();
  } catch {
    link = false;
  }
  // A dangling link: follow it, giving up on a loop as the operating system would.
  if (link && depth < 40)
    return realOf(
      resolve(dirname(inParent), readlinkSync(inParent)),
      depth + 1,
    );
  return inParent;
}

function within(path: string, base: string): boolean {
  return (
    path === base || path.startsWith(base.endsWith(sep) ? base : base + sep)
  );
}

function relativeTo(path: string, base: string): string {
  return path === base ? "" : path.slice(base.length + 1);
}

function listed(relative: string, entries: string[]): boolean {
  return entries.some((entry) =>
    entry.endsWith("/")
      ? relative === entry.slice(0, -1) || relative.startsWith(entry)
      : relative === entry,
  );
}

/** The grant level of a path relative to the task worktree, or null when it has none. */
export function levelOf(
  policy: Policy,
  relative: string,
): "rw" | "ro" | "names" | null {
  if (listed(relative, policy.rw)) return "rw";
  if (listed(relative, policy.ro)) return "ro";
  if (listed(relative, policy.names)) return "names";
  return null;
}

/** Whether a worktree-relative path is the worktree's `.git`, a submodule's, or below one. */
function isGit(relative: string): boolean {
  return relative.split("/").includes(".git");
}

/** Whether an absolute path is one of the Git administrative paths or below one. */
function inGit(policy: Policy, path: string): boolean {
  return policy.git.some((base) => within(path, base));
}

/** Whether an absolute path is a runtime path or below one. */
function inRuntime(policy: Policy, path: string): boolean {
  return policy.runtime.some((base) => within(path, base));
}

function readOne(policy: Policy, path: string): string | null {
  if (inGit(policy, path)) return "Git metadata is not available to workers";
  const inWorktree = within(path, policy.worktree);
  const relative = inWorktree ? relativeTo(path, policy.worktree) : "";
  if (inWorktree && isGit(relative))
    return "Git metadata is not available to workers";
  // A runtime path is readable wherever it lies, inside the task worktree too.
  if (inRuntime(policy, path)) return null;
  if (inWorktree) {
    const level = levelOf(policy, relative);
    if (level === "rw" || level === "ro") return null;
    if (level === "names")
      return `only the name of ${relative} is visible to this task`;
    return `${relative || policy.worktree} is not in this task's grant`;
  }
  if (policy.hidden.some((base) => within(path, base)))
    return `${path} belongs to the host`;
  if (policy.own.some((base) => within(path, base))) return null;
  if (within(path, policy.userHome) || within(path, policy.primary))
    return `${path} is outside this task's boundary`;
  return null;
}

/** Decide a read of an absolute path: both the path and its real path must be allowed. */
export function readDecision(policy: Policy, path: string): string | null {
  const lexical = normalize(path);
  const denied = readOne(policy, lexical);
  if (denied) return denied;
  const real = realOf(lexical);
  return real === lexical ? null : readOne(policy, real);
}

function isLink(path: string): boolean {
  try {
    return lstatSync(path).isSymbolicLink();
  } catch {
    return false;
  }
}

/**
 * Decide a write of an absolute path, as the Claude Code backend's write hook does: every
 * symbolic link resolved, the final one included, so that a write is judged by the file it would
 * change, and only `rw` paths allowed.
 */
export function writeDecision(policy: Policy, path: string): string | null {
  const absolute = normalize(path);
  const resolved = realOf(absolute);
  const link = isLink(absolute);
  if (!within(resolved, policy.worktree) || resolved === policy.worktree) {
    return link
      ? `${path} is a symbolic link to ${resolved}, outside the task worktree`
      : `${path} is outside the task worktree`;
  }
  const relative = relativeTo(resolved, policy.worktree);
  if (isGit(relative) || inGit(policy, resolved))
    return "Git metadata is not available to workers";
  if (listed(relative, policy.rw)) return null;
  // A denial through a final link names the file judged and the link it was reached by.
  const named = link
    ? `${relative} (the target of the symbolic link ${path})`
    : relative;
  if (listed(relative, policy.ro)) return `${named} is read-only for this task`;
  if (listed(relative, policy.names))
    return `only the name of ${named} is visible to this task`;
  return (
    `${named} is not in this task's grant; a new file outside the bound directories is ` +
    "created and bound to a Module by the task level before a worker fills it, and a " +
    "file another Module binds needs that Module bound to the task"
  );
}

/** Whether some `ro` or `rw` entry lies at, below or above a worktree-relative directory. */
function readableBelow(policy: Policy, relative: string): boolean {
  const directory = relative === "" ? "" : relative + "/";
  return [...policy.rw, ...policy.ro].some(
    (entry) =>
      directory === "" ||
      entry.startsWith(directory) ||
      (entry.endsWith("/") && directory.startsWith(entry)),
  );
}

/**
 * Decide the root of a search or listing. A directory of the task worktree is allowed when a
 * readable path lies below it; the sandbox then hides everything else below it.
 */
export function searchDecision(policy: Policy, path: string): string | null {
  const lexical = normalize(path);
  for (const candidate of new Set([lexical, realOf(lexical)])) {
    let directory = false;
    try {
      directory = statSync(candidate).isDirectory();
    } catch {
      directory = false;
    }
    if (directory && within(candidate, policy.worktree)) {
      const relative = relativeTo(candidate, policy.worktree);
      if (isGit(relative) || inGit(policy, candidate))
        return "Git metadata is not available to workers";
      if (
        !readableBelow(policy, relative) &&
        !policy.runtime.some(
          (base) => within(base, candidate) || within(candidate, base),
        )
      )
        return `${relative || policy.worktree} holds nothing this task may read`;
      continue;
    }
    const denied = readOne(policy, candidate);
    if (denied) return denied;
  }
  return null;
}
