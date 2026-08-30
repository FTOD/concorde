---
name: reflections-triage
description: Two-tier triage of specs/concorde/reflections.md — Fable 5 investigators write one modification plan per open entry (newest first), cheaper implementers execute approved plans in isolated worktrees, the maintainer merges. Sub-commands - status | investigate [N | R-NNN ...] | implement | merge.
user-invocable: true
disable-model-invocation: true
---

# Reflections triage

You are the orchestrator, running in the maintainer's main checkout. You never write plans or code
yourself here — you dispatch agents, record their results, and merge.

- Config: `.claude/reflections.config.json` — `investigators` (concurrent Fable 5 investigators),
  `implementers` (concurrent implementers), `order`, `skip`, `require_approval`, `plans_dir`.
- Helper: `python3 .claude/skills/reflections-triage/scripts/reflections-queue.py` (`--help`).
- Agents: `reflection-investigator` (`.claude/agents/`, Fable 5, main checkout, writes one plan file)
  and `reflection-implementer` (Sonnet, `isolation: worktree`, runs `speckit-fast-loop`).
- Plans live in `plans_dir` (gitignored). Frontmatter `status` lifecycle:
  `proposed → (approved | hold | rejected) → implemented | ineligible | failed → merged`.
  The maintainer may edit `status` by hand between stages.

## `$ARGUMENTS`

| Input | Action |
|---|---|
| empty or `status` | Print the queue table (`reflections-queue.py`) and a one-line count of plans per status. Stop. |
| `investigate` | One wave: the next `investigators` unplanned open entries in configured order. |
| `investigate N` | N entries, dispatched in waves of `investigators`. |
| `investigate R-041 R-040 …` | Exactly those entries (re-investigates if a plan exists — confirm first). |
| `implement` | Dispatch implementers for ready plans. |
| `merge` | Merge implemented branches into the current branch. |

## investigate

1. Queue: `reflections-queue.py --next N` (or `--entry <ID>` for explicit ids). Empty queue → say so, stop.
2. Dispatch one wave: at most `investigators` `Agent` calls **in a single message**, each
   `subagent_type: reflection-investigator`, prompt:
   `Investigate reflection entry <ID> (<title>). Follow your agent instructions; write .claude/reflection-plans/<ID>.md.`
   Wait for every completion notification of the wave before starting the next wave.
3. After each wave run `reflections-queue.py --plans` and confirm each dispatched entry now has a
   plan with a `route`. If one is missing, re-dispatch that entry once; then report it as failed.
4. Report per entry: `<ID> · <route> · <one-line summary from the agent>`. Remind the maintainer
   that plans are in `plans_dir` and that `status: approved | hold | rejected` can be set before
   `implement`. Entries routed `specify`, `dismiss`, or `blocked` are never implemented by this
   pipeline — they are the maintainer's decisions.

## implement

1. Ready plans (`--plans`): `route == fast-loop` and `status` in `{proposed, approved}` — only
   `approved` when `require_approval` is true.
2. Safety, per distinct `implement_in` directory: `git status --porcelain -- <dir>` must be empty
   (otherwise the maintainer has work in flight there — skip the whole group and say why). Also skip
   a plan whose listed `files:` have uncommitted changes in the main checkout.
3. Group ready plans by `implement_in`, keep configured order inside each group. Dispatch at most
   `implementers` concurrent `Agent` calls (`subagent_type: reflection-implementer`), one per group,
   all calls of a wave in one message. The prompt must contain: the feature directory and id,
   `touches_docsite` (true if any plan says so), and the **full text of every plan file** in order —
   the worktree cannot see `plans_dir`, it is gitignored.
4. On each report: `reflections-queue.py --set <ID> status=<implemented|ineligible|failed> branch=<branch> commit=<sha>`
   (omit keys the report lacks). Collect every `reflections-to-append` block.
5. Report a table (id · status · branch · commit) plus the collected reflections. Do not merge.

## merge

1. Precondition: `git status --porcelain` shows no modified tracked files. If it does, stop and ask
   the maintainer to commit or stash — never stash or reset their work yourself.
2. For each distinct `branch` among plans with `status: implemented`, one at a time:
   `git merge --no-ff <branch> -m "merge reflections: <ids on that branch>"`.
   On conflict: `git merge --abort`, report the conflicting files and the branch, stop.
3. After all merges: `uv run python -m unittest discover -s tests/concorde -p "test_*.py"`; if any
   merged plan has `touches_docsite: true`, also `npm run check --prefix docsite`. On failure, report
   the output and stop — do not revert automatically.
4. Cleanup for merged branches: `git worktree remove <worktree path>` then `git branch -d <branch>`;
   `reflections-queue.py --set <ID> status=merged` for each plan on that branch.
5. Report: merged ids and commits; the entries the maintainer may now mark `resolved` in
   `specs/concorde/reflections.md`, each with a suggested `Note` line citing the commit; and the
   collected reflections-to-append. Never edit the reflection log yourself.
