/**
 * Decisions of the pi task session's boundary extension.
 *
 * Pure functions over the session's policy: whether a `write` or `edit` may change a path, and
 * whether a `concorde_report` call is a complete session report. Tasks copies this file beside
 * `boundary.ts` and `pi_policy.ts` (the Harness's path resolution, which it imports); they import
 * only Node's own modules, so the tests run them under Node without pi. Every function returns
 * `null` to allow, or the reason of a refusal as the session should read it.
 */

import { sep } from "node:path";
import { realOf } from "./pi_policy.ts";

export interface SessionPolicy {
  task: string;
  worktree: string;
  files: string[];
  sandbox: { allowWrite: string[] };
  reportSchema: Record<string, unknown>;
}

/** Whether a task session may write `path`, an absolute path resolved as pi resolves it. */
export function sessionWriteDecision(
  policy: SessionPolicy,
  path: string,
): string | null {
  const real = realOf(path);
  const root = realOf(policy.worktree);
  if (real === root || real.startsWith(root + sep)) return null;
  if (policy.files.some((file) => realOf(file) === real)) return null;
  return (
    `${path} is outside task ${policy.task}: a task session writes only its task worktree ` +
    `${policy.worktree} and its decision log ${policy.files.join(", ")}. A refusal means you ` +
    "left your task; escalate to the main agent if the task needs this change."
  );
}

// A strict end assertion also refuses a trailing newline, which `$` would admit.
const COMMIT = /^[0-9a-f]{40}([0-9a-f]{24})?(?![\s\S])/;

/** What makes a `concorde_report` call incomplete, or null when it is a session report. */
export function reportProblem(report: Record<string, unknown>): string | null {
  const fields = [
    "status",
    "summary",
    "commit",
    "escalations",
    "decisions",
    "open",
  ];
  if (
    !report ||
    typeof report !== "object" ||
    Array.isArray(report) ||
    fields.some((field) => !Object.hasOwn(report, field)) ||
    Object.keys(report).some((field) => !fields.includes(field))
  )
    return "a report has exactly `status`, `summary`, `commit`, `escalations`, `decisions` and `open`";
  if (typeof report.summary !== "string" || report.summary.length === 0)
    return "`summary` is a nonempty string";
  for (const field of ["decisions", "open"]) {
    const value = report[field];
    if (
      !Array.isArray(value) ||
      !value.every((item) => typeof item === "string" && item.length > 0)
    )
      return `\`${field}\` is an array of nonempty strings`;
  }
  const escalations = report.escalations;
  if (report.status === "delivered") {
    if (typeof report.commit !== "string" || !COMMIT.test(report.commit))
      return "a delivered report names the delivery commit as `commit`, its full hexadecimal identity";
    if (!Array.isArray(escalations) || escalations.length !== 0)
      return "a delivered report has `escalations: []`";
    return null;
  }
  if (report.status === "escalated") {
    if (
      !Array.isArray(escalations) ||
      escalations.length === 0 ||
      !escalations.every((item) => Number.isInteger(item) && item >= 1) ||
      new Set(escalations).size !== escalations.length
    )
      return (
        "an escalated report names in `escalations` the numbers of the escalations you " +
        "recorded with `concorde task escalate --by task-session`, each once"
      );
    if (report.commit !== null) return "an escalated report has `commit: null`";
    return null;
  }
  return "`status` is `delivered` or `escalated`";
}
