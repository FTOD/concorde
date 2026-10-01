# Decision log: session-without-sandbox

Goal: Drop the OS Bash sandbox from task sessions so that only changes outside the task worktree are guarded, check at delivery and merge that a task changed nothing outside its worktree, and give back to the task session the work moved to the main agent or the project MCP server only because of the sandbox

## Brief (main agent, 2026-10-01)

### Why

The main agent investigated, for the developer, what the task session's boundary restricts and why
task sessions keep hitting it. Concorde's settings (`src/concorde/tasks/session.py`, `settings()`
and `writable()`) only say which paths Bash may write, but Claude Code's Bash sandbox on Linux
(sandbox-runtime: bwrap + seccomp + proxy; see `references/sandbox-runtime/src/sandbox/`) also
imposes, mostly without a switch: a PID namespace per Bash call whose processes die with it; a
network namespace reached only through a proxy; AF_UNIX sockets blocked by seccomp (nested
sandbox-runtime inside a pi worker cannot listen: I-a7d8a756, every pi worker's find/ls/grep fail
with `listen EPERM ... srt-mux-*.sock` in runs a session starts); protected paths that can never be
written (`.git/config`, `.git/hooks`, `.mcp.json`, `.claude/settings*`, shell rc files, ...);
`/dev/null` and 0444 placeholder mounts visible on the host and in the shared `.git`; only paths
existing at start writable; home state read-only. Since 2026-09-25 this caused 14 problems; only 4
were fixed by changing the rules, the rest by workarounds. Commits to read: 13511b32, 40d9e79e,
0137dd22, 1e9bd0ed, 196d1b5b, e0eeda37, e24ee272/7c997504, 46ff8e2e, 01298edc, 6c9d3753, 110272aa,
b93641d4, f96128b8/ac0ec5ce, bf92c759; Issues I-84382b27, I-accf2963, I-35a33208, I-07659375,
I-c31a5ad1, I-30b3cd2e, I-7d540008, I-a7d8a756.

### The developer's decisions this task carries out

1. **A task session only must not change anything outside its task worktree; nothing else is
   restricted.** Network, processes, sockets, home state and every other permission stay open.
   Drop the OS Bash sandbox from the task session's settings. This is protection against
   mistakes, as the session boundary always was, not against a malicious session.
2. **Writes stay guarded:**
   - keep the PreToolUse write hook on Edit/Write (task worktree and decision log);
   - for Bash, rely on Claude Code's `auto` mode and the task-session guidance (change only the
     task worktree; Concorde's own records are written by `concorde` commands or the MCP tools);
   - add a check that a task changed nothing outside its worktree: at least the primary worktree
     (beyond Concorde's own records the commands write) and the other task worktrees, at
     delivery and/or `task merge`, refusing with an error chain that names what changed. Where
     the check lives and exactly what it compares is yours to settle (it must not flag what
     Concorde itself legitimately writes: task records, decision logs, locks, Issues and their
     commits, traces, run results).
3. **Give back to the task session what was moved away only because of the sandbox.** Review each
   workaround and, where the sandbox was its only reason, let the task session do it itself and
   simplify Concorde accordingly; keep a mechanism that has its own value, and say why. At least:
   - `init-references.py` run by the main agent before starting a session (CLAUDE.md, the
     development skill, `concorde-development`): the session can now do it itself;
   - `workflow_step` through the project MCP server because a detached run died with its Bash
     call: decide whether the step agents go back to `concorde workflow step` in background Bash or
     the MCP tool stays for its own merits (no polling, one wait), and state the reason;
   - "a task session writes Issues only through the MCP tools": the CLI is now fine too;
   - live probes (e.g. `claude agents`, pi credentials, uv tools) escalated to the main agent
     because home state was read-only;
   - the guidance and Specs that tell sessions about sandbox refusals, `.git/config` being
     read-only, `config.lock` placeholders, short TMPDIRs (`CLAUDE_CODE_TMPDIR`), `create_writable`.
   Mechanisms that also serve workers (workers keep their own grant-based sandbox; this task does
   not change the Harness for workers) or that are good design anyway (run lock liveness, skipping
   placeholder files in validation, `proxy_environment` for workers) stay unless clearly dead.
4. **I-a7d8a756** is resolved by this change (the task record's `resolves` names it; `task merge`
   closes it). Close-review the related open Issues listed above and say which this task makes
   moot; close those it resolves with evidence (the Issue tools), leave the rest.

### Left to the task session

How the settings look without the sandbox, the audit's place and shape, wording, and the order of
the simplifications. Escalate together anything that changes promises of Modules beyond those
bound here (task-session, harness, main-session, tasks, workflows, concorde), or any remaining
restriction you think should stay.

### Verification and delivery

Build, spec-validation, relevant tests and the full suite once at the end. Show live evidence that
a task session without the sandbox works: since your own session still starts with the old
boundary, verify by generating the new settings and, if practical, starting a throwaway session or
running the relevant commands outside a sandbox. Then `task-validation`, `delivery`, report.

## Task session decisions (2026-10-01)

### d1 — Where the outside-change audit lives and what it compares

Decided by the task session; the brief left this to it.

**Where.** In Tasks (`src/concorde/tasks/merge.py`), run by `concorde task merge` before it merges,
under the merge lock. Not in `delivery` or `task-validation`: those belong to module.delivery and
module.validation, which this task does not bind, and the brief's "at delivery and/or `task merge`"
admits the merge alone. The merge is also the gate into the primary branch, so a refusal there
protects the project rather than only informing one session.

**What it compares.** A change outside a task's worktree is attributable only where the state
outside is expected to be unchanged:

- The **primary worktree** is such a place: nothing changes there while tasks run except Concorde's
  own records, which are either paths Git does not version (the task folders, locks, runs, history
  and unbound runs, all in the installed `.gitignore`) or committed by the command that writes them
  (Issue records, decision-log copies). Its uncommitted and untracked paths are therefore judged
  whole, as `primary_dirty` already judged them.
- **Every other worktree of the repository that is not an open task's** — a closed task's worktree
  left behind, a worktree of no task — is also quiet, and nothing validates what is in it. These are
  judged the same way, and the new refusal `changed_outside` names each worktree with its paths.
- An **open task's worktree** is not judged: its own session changes it constantly and nothing in
  the filesystem says who wrote a change. A change made there is not lost either — it becomes that
  task's content, which its own validation, delivery and merge checks judge.

The audit judges working trees, not commits: the primary branch legitimately moves (other tasks
merge, Issues are recorded, the developer commits), so a commit there is no evidence of a task
having overstepped.

### d2 — `workflow_step` stays in the project MCP server

The brief asked for a decision. It stays. Its reasons beyond the sandbox, already recorded in
Workflows' rejected alternative, all hold without one: a step agent is a small relay model and the
background-Bash alternative asks it for a two-command choreography; Claude Code ends a background
command after at most two hours and ends a session's background commands when the session is
stopped, which would take the run down with it; and Claude Code wakes a step agent again when its
anchor ends, a turn for nothing. Only the "a sandboxed Bash call's PID namespace kills the detached
runner" reason goes; the Specs now give the reasons that stand.

### d1 revised — the audit's reach, and `primary_dirty` kept

Building the audit showed that its first shape would have refused merges for changes nobody could
attribute. A worktree is judged only where its state is one no task accounts for:

- The **primary worktree** keeps its existing refusal `primary_dirty`, whose message now also says
  that a task changes nothing outside its worktree, so the main agent checks whether the paths are a
  task's. A separate code was rejected: a dirty primary worktree is usually the developer's own
  work, and naming it "the task changed something outside" would be wrong; the existing refusal also
  carries its own reason, that undoing a merge must not touch anyone's work.
- The **worktree of a task that ended** and outlived it (the close normally removes it) is refused
  as `changed_outside`: no task will ever validate or deliver what is in it.
- The **worktree of a task that has delivered and waits** only **warns**. Its own session may have
  gone on working after delivering, which is legitimate and makes the task active again, so
  refusing this task's merge for it would block a task that has nothing to do with it.
- The **worktree of a task still working** is not judged at all. Its own session changes it
  constantly and nothing in the filesystem says who wrote a change; and a change written there is
  not lost, since it becomes that task's content, which its own `task-validation`, `delivery` and
  merge judge — its merge refuses an uncommitted change as `dirty_worktree`. So a cross-task write
  into a working worktree is caught, by that task rather than by the one that wrote it.
- Worktrees of no task, such as one a developer's own Claude Code session made, are not the
  project's to judge.

The limit is stated in the Specs rather than hidden: attribution across worktrees is not available,
so the audit promises what it can establish and no more.

### d2 confirmed — `workflow_step` stays, with its remaining reasons

Kept as decided, and the Specs now give the reasons that stand without a sandbox: a step may outlast
many relays; Claude Code ends a background command after two hours and when the session is stopped;
a two-command choreography around a background command is the kind of instruction a live run saw a
relay invent an outcome for; and a relay woken again when its anchor ends is a turn for nothing.

### d3 — what was given back, and what stayed

Given back to the task session: running `scripts/development/init-references.py` itself (the main
agent no longer prepares submodules), writing Issues from its shell with `concorde issues` beside
the MCP tools, probing its machine and its home state, and preparing its own worktree generally.
Dropped as dead with the sandbox: the writable-path list and `create_writable` in the session
starter, the network allowlist, and the note that a live session reads `failed` from inside a task
session's own process namespace.

Kept, with the reason restated: `workflow_step` (d2); Workers' proxy passing, which still serves a
sandboxed main agent's workers, though Task sessions no longer relies on it and its `relies_on` of
`req.workers.proxy-passed` is dropped; Validation's and Delivery's skipping of a sandbox's
placeholder files and `/dev/null` mounts, and the merge's same rule for the primary worktree, since
a main agent may still run in a sandbox; the run lock as the liveness signal; and
`init-references.py`'s refusal to register a submodule while `.git/config.lock` is held, which now
guards against another worktree's preparation rather than against a sandbox.

### d4 — Issues: resolved, recorded, left open

Resolved by this task (added to its `resolves`, which its merge closes):

- `I-a7d8a756745c54c5b48622f34892c1be` — pi workers' `find`, `ls` and `grep` failed with EPERM in
  runs a task session started, because sandbox-runtime cannot nest inside Claude Code's Bash
  sandbox. With no sandbox around the session's commands there is no nesting.
- `I-07659375748c56a69e1a60a0f571a7f5` — the background cleanup before `task-validation` was
  assumed and nowhere required. It is now `req.main-session.task-session-quiet-before-validation`,
  with the reason that stands without a sandbox: a run still running holds the workspace lock, and
  `delivery` commits every uncommitted change.
- `I-c31a5ad145245c73a613f761e9e867b7` — the blanket "every run in background Bash" rule did not
  exempt `workflow_step`. `req.main-session.task-session-background-runs` is now about the runs a
  session starts itself and names the step tool as the other path.

Recorded as new Issues, since their Modules are not bound to this task:

- `I-71f6993f0e9b59fa96d22123e5f57b82` (module.issues, obvious-fix) — the Issues entry gives the
  task session's Bash sandbox as the reason it uses the Issue tools; that reason is gone, and the
  one that stands is that the tools record the calling session.
- `I-07e549dde12655e095abcabcfb422fee` (module.execution, obvious-fix) — the detached-run passage
  names a task session's background Bash as a sandboxed call.
- `I-14aba3400a315638beb54fcae9787846` (module.distribution, suggestion) — the installer's
  step-permission comment still gives the sandbox as the reason.

Left open, since this task makes neither moot:

- `I-30b3cd2e488d5c6b99f026fab360af50` (module.execution) — Execution's independence claim omits
  its workflow transport dependency. `workflow_step` stays, so the dependency stays.
- `I-7d5400085d3c58a78ee14241a3fc797a` (module.execution) — the detached-namespace scenario asserts
  an undefined workflow error outcome. The scenario and the PID-namespace fact still hold for
  workers and for a main agent whose own session runs in a sandbox.

Already closed before this task: `I-84382b27` (preparing a task worktree while another session ran
a command), `I-accf2963` (ending a task unregistered the reference submodules) and `I-35a33208`
(validation reported the sandbox's placeholder files as unbound, whose fix stays, since a main agent
may still run in a sandbox).

### d5 — Live evidence of the new boundary

`concorde task session <task> --dry-run` was run for real in a throwaway project and wrote settings
holding only the MCP approvals and the PreToolUse write hook: no `sandbox` key, no deny rules.

A real `claude -p` was then started under settings generated by `session.settings` with the write
hook limited to a narrow directory of this task worktree, so that a path the hook refuses is one
this session's own sandbox still lets a command write. Under those settings the session's **Bash**
wrote that path (`probe-out/from-bash.txt` was created), while its **Write** tool was refused by the
hook with the hook's own reason naming the worktree, and the file was not created. That is the new
boundary at work: the shell open, the file-writing tools held to the task.

The first attempts at this probe ran in a throwaway project and every `claude -p` there answered
`Request timed out`, with or without the generated settings. The cause is not the settings: Claude
Code keys workspace trust on the Git repository root, and a headless session in an untrusted project
stalls, which is why `scripts/e2e/e2e.py trust` exists. Marking a project trusted writes the
developer's `~/.claude.json`, outside this task's worktree, so the probe was moved into this
worktree's own repository instead.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T11:00:50Z

Delivered: `080326c2df23891555485be31806ec2aade4201f` on `concorde/session-without-sandbox` (two verified commits below it, `2331ffdd` and `88a5f851`). `task-validation` and `delivery` both report `ready`, 24 checks, 0 warnings; `build` and `spec-validation` are clean and the whole suite passes (870 passed, 4 skipped). Nothing is open that blocks the merge, and no escalation.

WHAT CHANGED

1. The sandbox is gone from a task session's boundary. `settings()` now holds only the MCP approvals and the PreToolUse write hook; `writable()`, `create_writable()`, the package-cache list and the network allowlist are deleted. The Harness, Task sessions, Main session and the glossary say the new rule: a task session must change nothing outside its task worktree, and nothing else about it is restricted. New requirement `req.task-session.no-sandbox` replaces `req.task-session.shell-boundary`.

2. The merge audits what lies outside the task's worktree, before it merges, under the merge lock (`req.tasks.merge-nothing-outside`, new refusal `changed_outside`). Its reach is deliberately bounded, because nothing in the filesystem records who wrote a change:
   - the primary worktree must be clean, as before (`primary_dirty`), and its detail now also says a task changes nothing outside its worktree, since the paths may be a task's and not the developer's;
   - the worktree of a task that ENDED and outlived it is refused: no task will ever validate or deliver what is in it;
   - the worktree of a task that has DELIVERED and waits only WARNS: its own session may have written there after delivering, and refusing would block a task that has nothing to do with it;
   - the worktree of a task still WORKING is not judged at all — and a change written there is not lost, since it becomes that task's content, which its own validation, delivery and merge judge (`dirty_worktree`). So a cross-task write into a working worktree is caught, by that task rather than by the one that wrote it.
   The audit is at `task merge` only, not at `delivery`: Delivery and Validation are not among this task's Modules, and the brief admitted "delivery and/or task merge". Extending it to `delivery`, so a session sees it before delivering, is follow-up work that needs module.delivery or module.validation bound — say the word and it becomes a task.

3. What the sandbox had moved away is back with the task session: it runs `scripts/development/init-references.py` itself (the main agent no longer prepares submodules — CLAUDE.md, the development skill and the development Spec follow), writes Issues from its shell with `concorde issues` as well as through the MCP tools, probes its machine and its home state, and prepares its own worktree generally. Dead with the sandbox and deleted: the writable-path list, `create_writable`, the network allowlist, and the note that a live session reads `failed` from inside a task session's own process namespace.

DECISIONS I TOOK FOR YOU (all in the decision log, with reasons)

- `workflow_step` STAYS in the project MCP server. Its reasons beyond the sandbox all hold: a step may outlast many relays; Claude Code ends a background command after two hours and when the session is stopped; a two-command choreography around a background command is the kind of instruction a live run saw a relay invent an outcome for; and a relay woken again when its anchor ends is a turn for nothing. The Specs now give those reasons instead of the PID namespace.
- Kept with the reason restated: Workers' proxy passing (it still serves a sandboxed main agent's workers, though Task sessions no longer relies on it, and that `relies_on` is dropped); Validation's and Delivery's skipping of placeholder files, and the merge's same rule for the primary worktree, since a main agent may still run in a sandbox; the run lock as the liveness signal; and `init-references.py`'s refusal to register a submodule while `.git/config.lock` is held, which now guards against another worktree's preparation.
- `primary_dirty` kept for the primary worktree rather than renamed: a dirty primary worktree is usually the developer's own work, so calling it "the task changed something outside" would be wrong, and the refusal carries its own reason (undoing a merge must not touch anyone's work).

ISSUES

- Resolved by the task (`resolves`, which the merge closes): I-a7d8a756 (pi workers' EPERM, gone with the nesting), I-07659375 (the background cleanup before validation is now `req.main-session.task-session-quiet-before-validation`, with the workspace lock as its reason), I-c31a5ad1 (`req.main-session.task-session-background-runs` now covers the runs a session starts itself and names `workflow_step` as the other path).
- Recorded as new Issues, since their Modules are not bound here: I-71f6993f (module.issues, obvious-fix — the Issues entry still gives the sandbox as the reason a task session uses the Issue tools), I-07e549dd (module.execution, obvious-fix — the detached-run passage names a task session's background Bash as a sandboxed call), I-14aba340 (module.distribution, suggestion — the installer's step-permission comment).
- Left open, neither made moot: I-30b3cd2e (Execution's workflow transport dependency stays, since `workflow_step` stays) and I-7d540008 (the PID-namespace scenario still holds for workers and for a sandboxed main agent).

LIVE EVIDENCE

`concorde task session --dry-run` was run for real and wrote settings with no `sandbox` key and no deny rules. A real `claude -p` was then started under settings generated by the same code, with the write hook limited to a narrow directory of this worktree: its Bash wrote a path the hook refuses, while its Write tool was refused by the hook with the hook's own reason and created nothing. First attempts in a throwaway project all answered `Request timed out` — not the settings: Claude Code keys workspace trust on the repository root and a headless session in an untrusted project stalls, and marking one trusted writes the developer's `~/.claude.json`, outside this task.

## Closed: merged, 2026-10-01T11:01:36Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 080326c2df23891555485be31806ec2aade4201f into main and closed it as merged. Nobody answers a report after that.
