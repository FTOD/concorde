# Decision log: validation-sandbox-paths

Goal: Make Validation leave out the empty read-only placeholder files Claude Code's Bash sandbox mounts in a worktree, as it already does for its /dev/null mounts, so they never block task-validation or delivery

## Brief (main agent, 2026-09-30)

### The defect
`src/concorde/validation/measurement.py` `special_paths` / `changed_paths` leave out unignored new
paths Git cannot version, which covers the `/dev/null` character-device mounts Claude Code's Bash
sandbox places over paths such as `.bashrc`, `.claude/settings.json`, `.idea` in the working
directory. But the sandbox runtime first creates each absent path on the host as an empty
read-only (0444) regular file and removes it only when no sandbox of that Claude Code process is
alive (`references/sandbox-runtime/src/sandbox/linux-sandbox-utils.ts`, `cleanupBwrapMountPoints`,
which also documents how to recognise such a placeholder: an empty regular file with no write bits
and one link). When a task session keeps any background sandboxed command alive, its later
commands, including `task-validation` and `delivery`, see these 18 placeholders as regular files
and Validation reports each as an `unbound_finding`, blocking delivery. Seen in task
`restructure-spec-tooling`, run r-20260929T182153-task_validation-e443e799 (readiness.json in that
task's `workspace/runs/…`).

### What to do
Make Validation leave out these placeholders too, precisely: only paths that are sandbox mount
points (e.g. a mount point per `/proc/self/mountinfo`, or the runtime's own signature: empty,
regular, no write bits, one link) and never an ordinary new file a task created. Prefer the most
precise signal; explain the choice. Update Validation's Spec (requirements/scenarios about which
changed paths are measured) and tests. Record the defect as an Issue owned by
`module.validation` and close it on this branch with the fix as evidence.

## Task session decisions (2026-09-30)

- **Signal chosen: the sandbox runtime's own placeholder signature, not `/proc/self/mountinfo`.**
  An untracked path is left out when it is an empty regular file with no write bit and exactly
  one link (`isStaleBwrapMountPoint` in `references/sandbox-runtime/.../linux-sandbox-utils.ts`;
  bubblewrap creates it with `ensure_file(dest, 0444)`). A mount point in mountinfo exists only
  inside the sandbox that mounted it, so it would miss a validation run on the host (e.g. the main
  agent's merge checks) or in another sandbox, which is exactly where the placeholder shows as a
  regular file. An ordinary new file has write bits (0666 & ~umask), content or another link and is
  still measured; the test covers an empty writable file, a read-only file with content and a
  read-only empty file with a second link.
- The rule lives in `measurement._special`, which `changed_paths`, `has_uncommitted` and
  `special_paths` share, so Delivery's staging exclusion and uncommitted-change test follow it
  without a change to Delivery's code. The public name `special_paths` was kept for that reason.
- Spec: new `scenario.validation.sandbox-placeholder`; contracts' input-measurement rule and
  module.md's "What is measured and checked" updated with the placeholder and the reason for the
  signal. The scenario is verified by
  `test_a_sandbox_placeholder_is_not_measured`, which fails on the old measurement and passes now.
- Issue I-35a3320838875b92862657294c6b2567 recorded (owner `module.validation`) and closed
  `resolved` on this branch. Its evidence paths are files of the worktree, since the observed
  readiness lies in the primary worktree's `.concorde/history/`, which the report command cannot
  check; the run id and that path are named in the report's description.
- **Not changed (outside the task's Modules):** Delivery's Spec (`specs/concorde/execution/commands/delivery/contracts.md`
  and `module.md`) still says the delivery commit leaves out only "untracked paths Git cannot
  version". Its behaviour now also leaves out placeholders, because it uses Validation's rule;
  the wording is escalated to the main agent.

## Escalated to the main agent, 2026-09-29T18:47:34Z

- **task-session** task session (task validation-sandbox-paths): `delivery_spec_wording`
  Validation now also leaves out the sandbox placeholder files (untracked, empty, regular, no write bit, one link), and Delivery follows that rule in its staging and uncommitted-change test because it calls Validation's special_paths/has_uncommitted. Delivery's own Spec still describes the exclusion as only 'an untracked path Git cannot version (neither a regular file, a symbolic link nor a directory)' in specs/concorde/execution/commands/delivery/contracts.md (delivery commit contents) and 'untracked paths Git cannot version, such as a sandbox's /dev/null mounts' in delivery/module.md. Behaviour and tests are complete in this task; only that wording lags.
  Not handled here (scope): module.delivery is not among this task's Modules (only module.validation), so changing its Spec goes beyond the task.
  Options: Allow this task to reword Delivery's two sentences to defer to Validation's input-measurement rule (the paths it leaves out), then deliver again; Leave it to a follow-up task on module.delivery; Leave Delivery's wording as it is
  Recommendation: Allow this task to reword the two sentences: a two-line change that states what Delivery already does, verified by the existing tests

```json
{
  "level": "task-session",
  "actor": "task session (task validation-sandbox-paths)",
  "code": "delivery_spec_wording",
  "detail": "Validation now also leaves out the sandbox placeholder files (untracked, empty, regular, no write bit, one link), and Delivery follows that rule in its staging and uncommitted-change test because it calls Validation's special_paths/has_uncommitted. Delivery's own Spec still describes the exclusion as only 'an untracked path Git cannot version (neither a regular file, a symbolic link nor a directory)' in specs/concorde/execution/commands/delivery/contracts.md (delivery commit contents) and 'untracked paths Git cannot version, such as a sandbox's /dev/null mounts' in delivery/module.md. Behaviour and tests are complete in this task; only that wording lags.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "module.delivery is not among this task's Modules (only module.validation), so changing its Spec goes beyond the task."
  },
  "options": [
    "Allow this task to reword Delivery's two sentences to defer to Validation's input-measurement rule (the paths it leaves out), then deliver again",
    "Leave it to a follow-up task on module.delivery",
    "Leave Delivery's wording as it is"
  ],
  "recommendation": "Allow this task to reword the two sentences: a two-line change that states what Delivery already does, verified by the existing tests",
  "causes": []
}
```
- task-validation r-20260929T184714-task_validation-356bf071: `ok`, ready, no blocking finding,
  7 checks passed. Delivery r-20260929T184818-delivery-b010e0c2: `ok`, delivery commit ea2af0b3
  (empty; the 18 sandbox mounts in the worktree were left out). Delivered before the answer to
  escalation 1, since the fix does not depend on it; if the rewording is allowed, the task delivers
  again.

## Main agent's answer to escalation 1 (2026-09-30)

Decided without the developer (ordinary scope): option 1. This task rewords the two sentences of
Delivery's Spec (`delivery/contracts.md`, delivery commit contents; `delivery/module.md`) to defer
to Validation's input-measurement rule, changing nothing else of module.delivery. No running task
holds module.delivery (`stale-statements` holds workers, execution, commands and task-session and
was told not to change Delivery). Also accepted the placeholder signature over mountinfo.
- Escalation 1 answered by the main agent (option 1): Delivery's two sentences in
  `delivery/contracts.md` and `delivery/module.md` now defer to Validation's input measurement;
  nothing else of module.delivery changed. The contracts sentence links to
  `../validation/contracts.md#input-measurement`.
- task-validation r-20260929T185040-task_validation-54a73da2: `ok`, ready, 7 checks passed.
  Delivery r-20260929T185126-delivery-6e3b9198: `ok`, delivery commit 1e5e34e0.

## Closed: merged, 2026-09-29T18:52:41Z
