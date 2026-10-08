# Decision log: main-rename-hook

Goal: Coordination installs a SessionStart hook for the primary worktree that, on startup, resume and compaction, lists the tasks not ended with the main session each records and tells the main agent to compare it with its current ListAgents name and follow the rename steps first when they differ

## Task brief (main agent, 2026-10-08)

Resolves I-b998085e (read it with `concorde issues show`). On 2026-10-08 the main session
`concorde-d4` restarted as `Review流程`. Tasks unbound-prepare and worker-transient-retry
reported to the old name; nobody received it and the main agent kept waiting until the developer
noticed. The recovery (task rebind, reports kept, task sessions waiting) works; what is missing is
anything that makes the main agent *notice* the rename: the guidance step only applies "when
ListAgents reports another name", and nothing makes it call ListAgents after a restart.

Developer decision (2026-10-08): **Coordination installs a `SessionStart` hook for the primary
worktree** (matchers startup, resume and compact) whose output, added to the main agent's context,
lists the tasks not ended (open, active, delivered, merging) with the `main` each records and any
unanswered reports, and tells the main agent to call ListAgents, compare its current name with
those, and follow "When your session name changed" before anything else when they differ. When no
task is unended the hook says nothing (or one short line).

Constraints and left to the session:
- The hook must be cheap and never fail the session start: on any error it prints a one-line
  notice and exits 0. It reads task records only through the Task store / `concorde task list`.
- It is installed for the primary worktree's main sessions, not for task sessions (whose settings
  the task session boundary writes) and never for workers.
- Where it is written (the project's `.claude/settings.json` that the installer manages, or the
  settings Coordination already contributes) and how this source checkout gets it too: yours to
  decide within Distribution's installer-owns-only-Concorde-files rule; escalate if it needs a
  file the installer may not own.
- Update the guidance section "When your session name changed", the requirement/scenario
  (`req.main-session.reconcile-after-restart` and `scenario.main-session.reconcile-after-restart`)
  and tests. Check how Claude Code passes `source` to SessionStart hooks in the pinned Claude Code
  documentation under `references/` if present.

Another task, worker-transient-retry (module.workers, module.project-review, module.method), runs
in parallel; no overlap expected. Deliver with `task-validation` then `delivery`; run the full suite
once on the final input.

## Escalated to the main agent, 2026-10-08T06:20:02Z

- **task-session** task session (task main-rename-hook): `hook_install_outside_modules`
  Coordination can provide the hook's command (planned: 'concorde task main-hook', in module.tasks, reading only current task records through the Task store: about 0.2 s, while 'concorde task list --state ...' takes 23 s here because it reads all 294 history records; it prints nothing outside the primary worktree, so a task session or worker that loads a tracked .claude/settings.json gets nothing). But nothing lets a part put a hook into a project. (1) Installed projects: Distribution's installer changes .claude/settings.json only by adding and removing its own permissions.allow rules (req.distribution.installer-own-permissions; contract.distribution.part-registration's install has no hooks field; the receipt records only permissions). A SessionStart hook needs module.distribution to change: a new registration field install.hooks (each {event, matcher, command, timeout}, command being the arguments of .concorde/bin/concorde), the installer adding the missing entries under hooks.<event> of .claude/settings.json as '"$CLAUDE_PROJECT_DIR"/.concorde/bin/concorde task main-hook' and removing those its receipt recorded and no longer ships, the receipt recording them (receipt contract version bump), and settings_invalid covering a hooks value that is not an object of lists. .claude/settings.json is already an amended file of the installer, so no file the installer may not own is needed. (2) This source checkout tracks no .claude/settings.json; the natural place is a tracked .claude/settings.json with the hook 'python3 "$CLAUDE_PROJECT_DIR"/scripts/concorde.py task main-hook', which is a project file of module.concorde (realization.concorde.project-files), also outside the task's Modules.
  Not handled here (decision): Both changes are outside module.main-session, module.coordination and module.tasks: the brief says to escalate when the hook needs more than those, and changing what Distribution's installer promises about .claude/settings.json is a promise change of another Module.
  Options: (a) Add module.distribution and module.concorde to this task: I implement install.hooks in Distribution (registration + receipt contracts, requirements, scenarios, installer, tests), Coordination's registration declares the SessionStart hook (matcher startup|resume|compact), and I add the tracked .claude/settings.json to this checkout; (b) Deliver only the Coordination side (command, guidance, Specs, tests) here; a separate module.distribution task adds install.hooks and Coordination's registration entry, and the checkout's .claude/settings.json is a small change of the main agent after both merge
  Recommendation: (a): the hook is useless without the installer part, the Distribution change is small and mirrors its permission rules, and one task keeps the Specs consistent

```json
{
  "level": "task-session",
  "actor": "task session (task main-rename-hook)",
  "code": "hook_install_outside_modules",
  "detail": "Coordination can provide the hook's command (planned: 'concorde task main-hook', in module.tasks, reading only current task records through the Task store: about 0.2 s, while 'concorde task list --state ...' takes 23 s here because it reads all 294 history records; it prints nothing outside the primary worktree, so a task session or worker that loads a tracked .claude/settings.json gets nothing). But nothing lets a part put a hook into a project. (1) Installed projects: Distribution's installer changes .claude/settings.json only by adding and removing its own permissions.allow rules (req.distribution.installer-own-permissions; contract.distribution.part-registration's install has no hooks field; the receipt records only permissions). A SessionStart hook needs module.distribution to change: a new registration field install.hooks (each {event, matcher, command, timeout}, command being the arguments of .concorde/bin/concorde), the installer adding the missing entries under hooks.<event> of .claude/settings.json as '\"$CLAUDE_PROJECT_DIR\"/.concorde/bin/concorde task main-hook' and removing those its receipt recorded and no longer ships, the receipt recording them (receipt contract version bump), and settings_invalid covering a hooks value that is not an object of lists. .claude/settings.json is already an amended file of the installer, so no file the installer may not own is needed. (2) This source checkout tracks no .claude/settings.json; the natural place is a tracked .claude/settings.json with the hook 'python3 \"$CLAUDE_PROJECT_DIR\"/scripts/concorde.py task main-hook', which is a project file of module.concorde (realization.concorde.project-files), also outside the task's Modules.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Both changes are outside module.main-session, module.coordination and module.tasks: the brief says to escalate when the hook needs more than those, and changing what Distribution's installer promises about .claude/settings.json is a promise change of another Module."
  },
  "options": [
    "(a) Add module.distribution and module.concorde to this task: I implement install.hooks in Distribution (registration + receipt contracts, requirements, scenarios, installer, tests), Coordination's registration declares the SessionStart hook (matcher startup|resume|compact), and I add the tracked .claude/settings.json to this checkout",
    "(b) Deliver only the Coordination side (command, guidance, Specs, tests) here; a separate module.distribution task adds install.hooks and Coordination's registration entry, and the checkout's .claude/settings.json is a small change of the main agent after both merge"
  ],
  "recommendation": "(a): the hook is useless without the installer part, the Distribution change is small and mirrors its permission rules, and one task keeps the Specs consistent",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T06:20:09Z

main-rename-hook: one decision needed (escalation 1); I continue meanwhile with the Coordination side, which does not depend on it.

Escalation 1 (hook_install_outside_modules): no part can put a hook into a project today. Distribution's installer changes .claude/settings.json only through its own permissions.allow rules, so installing the SessionStart hook needs a small module.distribution change (registration field install.hooks, installer adding/removing its own hooks entries in .claude/settings.json, receipt recording them). This source checkout tracks no .claude/settings.json; the hook for it would be a tracked .claude/settings.json, a project file of module.concorde. Options: (a) add module.distribution and module.concorde to this task and do both here; (b) deliver only the Coordination side here and leave the Distribution change and the checkout's settings file to a later task / small change. Recommendation: (a).

- **task-session** task session (task main-rename-hook): `hook_install_outside_modules` (full chain recorded as escalation 1 in the task record and decision log)

Meanwhile I build: the command 'concorde task main-hook' (module.tasks; reads only current task records, ~0.2 s instead of the 23 s of 'task list' that reads all 294 history records; silent outside the primary worktree; on any error one line and exit 0), the guidance section 'When your session name changed' and the main-session requirements/scenario, and tests.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-08T06:20:23Z

Escalation 1 (hook_install_outside_modules), decided by the main agent: option (a). Do both in this task: Distribution's registration field for hooks, the installer adding and removing only its own hooks entries in .claude/settings.json (keeping every entry it does not own, as it does for permissions.allow) and recording them in the receipt; and this checkout's tracked .claude/settings.json carrying the SessionStart hook, bound to the root Module's Project files. No other running task touches module.distribution or module.concorde. Keep 'concorde task main-hook' fast and never failing as you describe.

## Decisions of the task session (2026-10-08)

- **Hook command `concorde task main-hook`** (module.tasks, in `tasks/cli.py`): plain text, exit 0
  always. It reads only the current tasks' records as stored (`store.unended`), never the history
  and without deriving a state, since `task list` took 23 s on the primary (294 history records)
  and deriving `active`/`delivered` needs Git; it therefore lists tasks without their state.
  Measured 0.2 s on the primary.
- **Silent outside the primary worktree**: first when the cwd holds a workspace binding (no Git
  needed, so a worker or task session loading tracked settings never sees a failure line), then
  when Git says the worktree is not the primary. Silent when no task is unended.
- **Text**: tells the main agent to call ListAgents first; a task whose main is another session
  ListAgents lists belongs to that main agent (several main sessions may share a primary
  worktree); a main that is neither the current name nor a listed session is its former name.
  Unanswered report numbers are listed per task.
- **Matchers** `startup|resume|compact` as the developer decided; `clear` and `fork` left out
  (`clear` keeps the name; a fork is a second session that must not take over the tasks).
- **Distribution `install.hooks` is optional** in the registration (read as `[]` when absent), so
  the other parts' registrations, owned by other Modules, stay untouched. Each hook is
  `{event, matcher, command, timeout}`; the installer writes one matcher group with one command
  hook `"$CLAUDE_PROJECT_DIR"/.concorde/bin/concorde <command>`; a group is Concorde's only when it
  holds exactly that one hook; the receipt's new `hooks` lists `{event, matcher, command}`.
  Contract versions: part-registration 5→6, install-result 3→4. Time limit 20 s.
- **`task list` skips the history** when every requested state is unended (same result, since the
  history holds only ended tasks), which makes the rename listing fast too.
- **Specs**: added `req/scenario.main-session.session-start-compare` beside the existing
  `reconcile-after-restart` (whose wording still holds), `req.tasks.main-hook-lists`,
  `req.tasks.main-hook-never-fails`, `req.distribution.installer-own-hooks` and their scenarios;
  narrowed `req.distribution.installer-own-permissions` to the `permissions` of the settings.
- **This checkout**: tracked `.claude/settings.json` running `python3
  "$CLAUDE_PROJECT_DIR"/scripts/concorde.py task main-hook`, bound to
  `realization.concorde.project-files`; user docs (docs/README.md, docs/using-concorde.md) updated.
- The workspace binding still lists the three original Modules; the main agent's answer to
  escalation 1 extended the work to module.distribution and module.concorde.

- **Full suite run 1: 1 failed, 1318 passed.** `tests/concorde/views/test_repository_checks.py::
  test_real_registry_listing_roots_are_copied` failed because the docsite repository check
  (`docsite/tests/repository/run-checks.py`, module.views) copies a fixed list of root files and
  the newly bound `.claude/settings.json` was not in it. Decided: add it to that list (one line, a
  mechanical consequence of the approved binding, no promise changed), outside the task's Modules.
- Hardened the installer: a hook group or receipt entry whose event, matcher or command is no text
  is left alone instead of raising.

## Report 2 to the main agent (Review流程), 2026-10-08T06:54:21Z

main-rename-hook delivered: delivery commit 776d962d on concorde/main-rename-hook (task-validation ready; full suite 1319 passed, 5 skipped; build --check and spec-validation clean). Resolves I-b998085e (added with task resolve).

What it does:
- `concorde task main-hook` (module.tasks): the main agent's SessionStart hook. In the primary worktree it prints, as plain text, every task not ended with the `main` its record names and its unanswered report numbers, then tells the main agent to call ListAgents before anything else: a task naming another session ListAgents lists is that main agent's, leave it; a main that is neither the current name nor a listed session is its former name, so follow "When your session name changed" first. It reads only the current task records (0.2 s on the primary). It prints nothing in a task worktree (a workspace binding is detected without Git) or when no task is unended. On any failure it prints one line naming the failure and the `task list` to run instead. It always exits 0.
- Distribution: the part registration gains an optional `install.hooks` ({event, matcher, command, timeout}; part-registration contract v6). The installer adds or refreshes those hooks in .claude/settings.json as `"$CLAUDE_PROJECT_DIR"/.concorde/bin/concorde <command>`, removes those its receipt recorded and no longer ships, and keeps every other group. The receipt records them under `hooks` (install-result contract v4). settings_invalid now also covers `hooks` that are not an object of lists. Coordination registers SessionStart, matcher startup|resume|compact, `task main-hook`, 20 s.
- Guidance: the skill's "When your session name changed" and the CLAUDE.md block say what to do when the hook lists tasks. New req/scenario main-session.session-start-compare, tasks.main-hook(-lists, -never-fails, -failure), distribution.installer-own-hooks / install-hooks(-invalid). installer-own-permissions is narrowed to `permissions`.
- This checkout: tracked .claude/settings.json running `python3 "$CLAUDE_PROJECT_DIR"/scripts/concorde.py task main-hook`, bound to realization.concorde.project-files. User docs updated.
- `task list` now skips the history when every requested state is unended (same result, much faster for the rename listing).

Decisions I took (all in the decision log):
- install.hooks is optional, so the other parts' registrations stay untouched.
- The hook output has no task states, since deriving them needs Git.
- `clear` and `fork` are left out of the matchers.
- A new main-session requirement instead of rewording reconcile-after-restart, which still holds.
- Outside the approved Modules, one line in docsite/tests/repository/run-checks.py (module.views): it adds .claude/settings.json to the copied root files. This was the cause of the one failure in the first full-suite run, and binding the file made it necessary.

Open: the workspace binding still lists only the original three Modules. This checkout's main session gets the hook only after the merge, from the next start, resume or compaction. Installed projects get it on their next `concorde update`.

## Closed: merged, 2026-10-08T06:54:36Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 776d962d7b2cecc380da70bfb01a57d69ba8df50 into main and closed it as merged. Nobody answers a report after that.
