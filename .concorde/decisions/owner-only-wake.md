# Decision log: owner-only-wake

Goal: Every run and task-session round has exactly one owner main session, which alone is woken when it ends; every other main session (Claude Code or pi) may see its state but is never woken; verified by a live e2e case with two Claude Code and two pi main sessions

## Brief (main agent, 2026-09-29)

### Problem observed by the developer
The pi main session's Concorde extension (`src/concorde/main_session/pi_extension.ts`, `pi_runs.ts`)
follows every run of the shared run store (the primary worktree's `.concorde/runs/`) and every pi
task-session round under `.concorde/tasks/*.session/`, whoever started it, and **wakes the main
agent** (`wake(..., triggerTurn: true, deliverAs: "steer")`) whenever any of them ends. `owned` is
only used for `bg_wait`/drain (`ownedWork`). So a pi main session is woken by runs of other main
sessions, of task sessions (their runs in task worktrees record into the primary run store) and of
bash commands. The Specs require this today: `specs/concorde/coordination/main-session/requirements.md:190`
(follow and report every run, whoever started it) and `module.md:144-164`.

### Developer's decisions (carry them out)
1. **Show everything, wake only the owner.** A main session may display every run and task-session
   round of the project, but only its **owner** is woken when it ends. Every run and every
   task-session round has **exactly one** owner main session.
2. **Same rule for Claude Code.** Several Claude Code and pi main sessions may work on one project at
   the same time; the owner is unique and only it is woken.
3. **How a non-owner Claude Code main session "sees" state: on-demand query only.** Nothing is pushed
   into a Claude Code session (no hook injection, no statusline). A non-owner Claude Code main
   session sees a state change by querying with a `concorde` command (an existing one such as
   `task list`/`task show`, or a run-listing command if none shows runs; your call, see below). pi
   main sessions keep the run view (FleetView, `/concorde`, status bar) showing all runs and rounds.
4. **Test: a live end-to-end case in the e2e / headless-sessions tooling**, not a configured check
   (real `claude -p` / `pi -p` sessions cost tokens). It opens several main sessions on one test
   project at once, starting with **2 Claude Code + 2 pi**, has one of them own a run (and, if
   feasible, a task-session round), and verifies that only the unique owner is woken while the other
   three can see the status change (pi: run view shows it; Claude Code: the query shows it) without
   being woken. Also add deterministic tests for the owner determination and the wake filter, which
   run as ordinary checks.

### Left to the task session to decide (record each decision here)
- How ownership is determined and recorded, so it is unique and survives across sessions: e.g. the
  launching session for a run started with `concorde_run` or background Bash, the `--main` session a
  task session was started for (Claude Code already SendMessages only its `--main`; check a pi task
  session's rounds are owned by the pi main session that started it, including rounds started by
  `answer`). Decide what owns runs a task session starts inside its task worktree (they belong to the
  task session, whose main agent is woken by the round, not by each run) and runs started with bash
  by nobody's tool (owned by no main session: shown, never wake anyone), unless you find a reason
  otherwise.
- Whether an owner identity must be written into run progress files or task records, and by whom
  (keep the two halves decoupled: Execution knows nothing of tasks or main sessions; prefer the
  Coordination side / the extension recording ownership).
- The exact query command for Claude Code and its output shape.
- The Spec wording (main-session requirements and scenarios, module text, glossary definition of
  `concept.run-view` if it changes; glossary changes go by the term's owner Module).
- How the e2e case drives four concurrent sessions and observes "woken" vs "not woken" (e.g. from each
  session's transcript/events: a wake message/turn appears only for the owner).

Escalate together anything that would change what another Module promises beyond these, or that
conflicts with the decisions above. Deliver with `task-validation` and `delivery` and report.

## Task session decisions (2026-09-29)

1. **Who owns what.** A run's owner is the main session whose own tool started it: in pi its
   `concorde_run`, in Claude Code its background Bash. Every round of a task session belongs to
   the main session the task session was started for (`--main`, which the task record already keeps
   as `sessions[].main`), whoever answered the round. Runs a task session starts in its worktree
   belong to that task session: they wake no main session, and the round's report carries them to
   its owner. A run started by a command run by hand, and a round of a pi task session started
   without `--main`, have no owner main session: they are shown and wake nobody. I read the
   developer's "exactly one owner" as: never more than one, and exactly one for every run and
   round a main session starts with its tools. Reason: this is the brief's suggested default, and
   waking a main session for each run of its task session would duplicate the round's report.
2. **Where ownership is recorded.** Execution records nothing about main sessions (the halves stay
   decoupled). The pi run view writes the runs its `concorde_run` started, and every end it has
   given the session, as custom entries (`concorde-owned-run`, `concorde-reported`) of that pi
   session's own session file; a resumed session reads them back, keeps owning its runs and is
   given, once, the end of an owned run or round that ended while it was closed. For rounds the
   extension now starts pi task sessions with `--main <pi session id>`, so the task record names
   the owner; `task show` shows it. Claude Code needs no record: background Bash and SendMessage to
   `--main` already reach only the owner.
3. **A non-owner answering a pi task session** is allowed and does not move ownership; its tool
   result says who the owner is and that it will not be woken. Reason: refusing would change what
   `concorde task session --answer` promises; moving ownership would make it depend on who answered
   last.
4. **Query for a non-owner Claude Code session: the existing `concorde task show <task>`**: it
   lists the task workspace's runs with their status and the task's sessions with their owner
   (`main`) and pi rounds with their outcome. No new command: a run-listing command belongs to
   Execution, outside this task's Modules. An unbound run is therefore visible to a non-owner Claude
   Code session only through its files in the run store; left as an open point.
5. **Live e2e case**: drives each main session as a long-lived process, Claude Code with
   `claude -p --input-format stream-json` (verified by hand: a background command ending while the
   session is idle starts a new turn, a real wake) and pi with `pi --mode rpc`, so a wake is the
   program's own and not the driver's stand-in. The owned run is made to outlive its launch by the
   e2e tool holding the task's workspace lock until every session has seen the run running.

## Task session results and further decisions (2026-09-29)

6. **Headless driver stand-in follows ownership for pi.** `session start --client pi` now wakes a
   pi session only for the runs its `concorde_run` recorded in its session file and for rounds of
   task sessions whose `main` is its session identity. The Claude Code driver keeps waking for
   every run since the session began (a documented single-session stand-in): a Claude Code round's
   own background commands leave nothing on disk naming their owner.
7. **Owners case shape.** `python3 scripts/e2e/e2e.py owners <project> [--claude 2] [--pi 2]`
   plays three phases: an unowned run (started by the case), a run owned by the first pi session
   (`concorde_run`) and one owned by the first Claude Code session (background Bash). The case
   holds the task's workspace lock until every pi run view shows the run running, so the run
   outlives its launch; it judges wakes over a window in which it prompts nobody, then asks the
   non-owners what they see (pi `/concorde` and status bar; Claude Code `concorde task show`). A
   pi-owned task-session round is not played live: its ownership is covered by deterministic
   tests (run view, task record, headless driver), and a live round would need a nested
   sandbox-runtime task session. `prepare` gained `--pi`.
8. **Non-ok: the live 2 Claude Code + 2 pi run could not be made from this task session.** Inside
   this session's sandbox `~/.pi/agent` is read-only, and pi refuses to start a turn without
   taking a lock there: `Credential store read failed for openai-codex: EROFS: read-only file
   system, mkdir '/home/zhenyu/.pi/agent/auth.json.lock'` (and the same for `settings.json.lock`).
   I did not work around it (copying pi's credentials elsewhere would reach beyond the task).
   What ran live here: `owners <project> --claude 2 --pi 0 --claude-model claude-sonnet-5-5` on a
   prepared requests v2.31.0 project — **passed**: unowned run woke neither session; the run
   claude-1 started in background Bash woke claude-1 alone (`task_notification`), and claude-2
   found it `ok` with `concorde task show t1`. The pi phases ran only against stand-ins. The full
   run is left to the main agent (see the report).
9. **Delivered.** `task-validation` ok (ready); `delivery` ok: commit 51b110d2 with
   `.concorde/evidence/owner-only-wake/1.json`. Full suite before delivery: 763 passed, 4 skipped.
   `docs/using-concorde.md` (no Module) got one paragraph so the user document matches.
10. **Non-ok: the report did not reach the main session.** The main session `concorde-a3` named
    in the task record was not reachable with SendMessage (no agent of that name). I sent the
    report to `concorde-16` as the likeliest session, saying who it was meant for. concorde-16
    answered that it is not this task's main agent and passed the report on to the developer. The
    report's content is entries 1–9 above; the one open action is the live 2+2 `owners` run (entry 8).

## Main agent concorde-04 (2026-09-29)

11. The developer chose to have concorde-04 merge this task, since its main agent concorde-a3 is
    gone, and to merge it before `tracing`, whose new layout would hide tasks opened before it.
    The live 2 Claude Code + 2 pi `owners` run of entry 8 stays open.

## Closed: merged, 2026-09-29T08:29:44Z
