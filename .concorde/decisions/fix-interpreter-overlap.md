# Decision log: fix-interpreter-overlap

Goal: Workers launch again in unbound and linked-environment worktrees: the interpreter's readable directories never include the worktree or a directory holding it, and a live worker launch is tested end to end

## Task brief (main agent, 2026-10-14)

Resolves I-eecda073 (critical; read it with `concorde issues show`). Every worker launch of
project_review r-20261013T154548-project_review-0f8f7c0b was refused with runtime_path_overlap
because Method's interpreter-readable directories (req.method.interpreter-readable, from the
developer's 2026-10-13 decision on I-bae9bb9b: keep and specify the automatic read access) include
"each directory holding a symbolic link on the way", and the unbound checkout's `.venv` is a
symlink at the checkout root, so the root became a runtime path, which Workers' new
runtime_path_overlap check (I-24f2a731) rightly refuses.

Both decisions stand: keep the interpreter read access, keep the overlap refusal. Fix the computation
so it never yields the worktree or a directory at or above it (a symlink found inside the worktree
contributes its target's directories, not the worktree path; the worktree itself is already covered
by the grant). Say in req.method.interpreter-readable exactly which directories are excluded.

Most important: **test a real launch path**. Round 3 merged this regression because no test
launches a worker through Method in an unbound checkout with a linked `.venv`. Add a test that
runs Method's worker setup (runtime paths + Workers' launch checks, no model call needed) in an
unbound-style checkout whose `.venv` is a symlink, and one for a task worktree with a real `.venv`.
Then run a small live unbound run to prove it, e.g.
`python3 scripts/concorde.py run spec_panel --modules module.scaffold --reviewers 2 --architects 0`
from the task worktree is bound, so instead run it unbound from a scratch clone only if needed;
otherwise a live `run general --type review-spec --read-only` in the task worktree is acceptable.
Record the run id. Deliver with task-validation then delivery; full suite once.

## Task session decisions (2026-10-14)

- **Excluded directories.** Method's interpreter directories now exclude, as given and with links
  resolved, `/usr`, the home or a directory holding it, the worktree the step works in, the
  primary worktree, and a directory holding either. The brief named only the worktree and its
  holders; I added the primary worktree and its holders because Workers' `runtime_path_overlap`
  refuses those too (a task worktree whose interpreter falls back to a primary `.venv` that is a
  link would otherwise hit the same refusal). In Concorde's layout the primary already holds every
  task worktree and unbound checkout, so this changes nothing there.
- **Link substitution.** Where an excluded directory holds a symbolic link on the way to the
  interpreter, Method adds the link itself instead of its holder (unless the link is itself an
  excluded directory), so the way through it stays readable without exposing the worktree. Applied
  uniformly, so a link directly in the home is now added too (before, it was silently dropped).
- **Spec.** req.method.interpreter-readable lists the exclusions and the link substitution;
  workers.md#interpreter-directories explains them; two new scenarios,
  scenario.method.interpreter-linked-checkout and scenario.method.interpreter-own-environment.
- **Tests.** InterpreterLaunchTests (tests/concorde/understanding/test_understand.py) run
  `understand` end to end through Method and Workers with the fake claude: unbound with the
  checkout's `.venv` linked to the primary's environment, and in a task worktree with its own
  `.venv`. The unbound test fails with `runtime_path_overlap` on the code before the fix. A unit
  test checks `interpreter_roots` substitutes the link.
- **Live runs.** A bound `general --type review-spec --read-only` in this task worktree, and an
  unbound `understand` from a scratch clone of the task branch under the session's job temp
  directory (the brief allows a scratch clone; it is removed afterwards).
- **Live run r-20261013T161534-general-07e98fac: `blocked` (worker_blocked / bash_tool_unavailable).**
  The review-spec worker launched (no `runtime_path_overlap`) and read both passages, judging the
  requirement states the exclusions exactly, but my instruction asked it to run `python --version`
  and review-spec workers have no Bash: my instruction's fault, not a defect. Rerun as
  `general --type implement` (the only task type with Bash), instructed to change no file.
- **Live unbound run r-20261013T161638-understand-00024f8c (scratch clone at 8b3c2da6): `failed`
  (pi_runtime_missing).** The checkout linked `.venv` and `docsite/node_modules` and the launch
  passed Workers' overlap check (it precedes the backend's preparation); the pi backend then
  found no sandbox-runtime package in the scratch clone, which nobody installed there: an
  environment gap of the clone, not of the fix. Rerun with `CONCORDE_SANDBOX_RUNTIME` naming the
  primary worktree's installed package.
- **Live bound run r-20261013T161638-general-464469ab: `ok`.** The pi `implement` worker ran
  `python -c "import sys; print(sys.executable, sys.version)"` in its sandbox; its transcript
  holds the bash tool result `…/fix-interpreter-overlap/.venv/bin/python 3.11.15` with
  `isError: false` (the interpreter links into `~/.local/share/uv/python`, reached through the
  added directories). No file changed; the reviewer's verdict is `accepted`.
- **Live unbound run r-20261013T161652-understand-815f46f5 (scratch clone at 8b3c2da6): `ok`.**
  Its checkout linked `.venv` and `docsite/node_modules`; the pi understand worker launched and
  answered about module.scaffold with no gap. Before the fix every such launch was refused with
  `runtime_path_overlap`. The scratch clone (with its run records) was removed afterwards.

## Report 1 to the main agent (Review流程), 2026-10-13T16:38:10Z

fix-interpreter-overlap delivered: delivery commit 8687ee2fc841 (delivery run r-20261013T162847-delivery-3551395d; task-validation r-20261013T161920-task_validation-7ddfa6a8 ready, nothing blocking). Resolves I-eecda073 (preferred-fix, critical).

Fix (src/concorde/method/workers.py): the interpreter's directories now exclude, as given and with links resolved, /usr, the home or a holder of it, the worktree the step works in, the primary worktree, and any directory holding either. Where an excluded directory holds a symbolic link on the way to the interpreter, the link itself is added instead of its holder (so an unbound checkout contributes its `.venv` link, never the checkout root). Spec: req.method.interpreter-readable lists the exclusions and the substitution; method/workers.md#interpreter-directories explains them; new scenarios scenario.method.interpreter-linked-checkout and scenario.method.interpreter-own-environment.

Tests: InterpreterLaunchTests run `understand` end to end through Method and Workers with the fake claude, (1) unbound with the checkout's `.venv` linked to the primary's environment (fails with runtime_path_overlap on the pre-fix code; passes now), (2) in a task worktree with its own `.venv`. Plus a unit test of the link substitution. Full suite: 1584 passed, 6 skipped.

Live runs: r-20261013T161638-general-464469ab (bound, pi implement worker) ok, its transcript shows the worker's bash running the project interpreter (.venv/bin/python 3.11.15, isError false), no file changed, reviewer accepted. r-20261013T161652-understand-815f46f5 ok, an unbound understand from a scratch clone of the task branch at 8b3c2da6, whose checkout linked .venv and docsite/node_modules; the pi worker launched and answered. Non-ok runs, all recorded in the decision log: r-20261013T161534-general-07e98fac blocked because my instruction asked a review-spec worker (no Bash) to run python; r-20261013T161638-understand-00024f8c failed pi_runtime_missing because the scratch clone had no sandbox-runtime package (rerun with CONCORDE_SANDBOX_RUNTIME pointing at the primary's). Scratch clone removed.

Decisions I made: (a) I also excluded the primary worktree and its holders (beyond the brief's "worktree and its holders") because Workers refuses those too; in Concorde's layout this adds nothing, since the primary already holds every task worktree and checkout. (b) The link substitution applies uniformly, so a link directly in the home is now added as a runtime path where it was dropped before. Nothing open.

## Closed: merged, 2026-10-13T16:38:28Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 8687ee2fc841cabb2156bc2a074d28804c75acbf into main and closed it as merged. Nobody answers a report after that.
