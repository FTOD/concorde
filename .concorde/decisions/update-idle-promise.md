# Decision log: update-idle-promise

Goal: Narrow Distribution's promise that the installer never replaces the Framework copy under a running run to what its idle check decides, and state that the developer must not start Concorde while an install or update runs

## Brief (main agent, 2026-09-30)

The developer's decision (2026-09-30, answering review-distribution's question on spec review finding
module.distribution f.6, which bound review f.1 repeats): **narrow the promise** (option C). No
framework lock and no versioned copies.

review-distribution confirmed the race is real. install.py checks active_runs() (held run locks) once,
in step 1. After that come d2, npm ci, the replacement of .concorde/framework and uv venv. A run
started in that window, in any worktree, may find no interpreter or load mixed code. A runner still
starting at the check is not seen, because it takes its run lock only after importing its code.
Long-lived processes such as `concorde project-mcp` are never checked.

Do:
- Change Distribution's Spec (entry, requirements, scenarios, the `concorde_busy` text) so that it
  promises only what the check decides: an install or update is refused with `concorde_busy` when a
  run's runner holds its run lock at the check. It no longer claims that the Framework copy is never
  replaced under a running program.
- State the limit plainly: the developer must not start a run, task-validation, delivery or any other
  `concorde` command, in any worktree of the project, while an install or update runs; a run started
  then may fail or load mixed code. Also say that long-lived processes such as each session's project
  MCP server keep running on the old code until they restart.
- Put a one-line warning where the developer runs `concorde update`: the update's own output or help
  text, and the main-session guidance if it describes updates. Either is a small change.
- No behaviour change beyond that text. Record choices here.

Process: `uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`; format, `build --check`,
`spec-validation`, the relevant tests (the full suite once if you touch code); task-validation and
delivery; report with SendMessage.

## Task session decisions (2026-09-30)

- Kept the identities `req.distribution.idle-install` and `scenario.distribution.install-busy` /
  `install-after-runs-end` (tests declare them) and narrowed only their titles and text: the
  installer refuses when a runner holds its run lock at its one check, and says it does not keep a
  run from starting after it. No new requirement for the warning: it is a stated limit and help
  text, not a promise of the installer.
- The limit is stated once, in Distribution's entry under "Installing into a project" (the
  `concorde_busy` paragraph), and referenced from update step 1 and from the Execution
  collaboration paragraph. It names runs, `task-validation`, `delivery` and every other `concorde`
  command in any worktree, and the long-lived project MCP server and Spec MCP server, which keep the
  code they loaded until they restart.
- The warning where the developer runs the update: argparse descriptions of `concorde update
  --help` and `install-concorde.py --help`. The update's JSON output (the receipt) was left
  unchanged, since adding a field would change its output beyond text. The main-session guidance
  does not describe updates, so it is unchanged.
- Not changed, outside this task's Module: `prompts/dogfooding/skill.md` ("Take the fix", owned by
  module.dogfooding) already says to run `concorde update` while nothing runs, but not to start
  nothing until it ends. Reported to the main agent as an optional follow-up.
- Review memory findings f.1 / f.6 of module.distribution left open in `.concorde/reviews/`: the
  next Spec review resolves them against the changed text.
- Formatting: `uvx ruff format` needed `UV_TOOL_DIR` under `$TMPDIR` because the sandbox keeps
  `~/.local/share/uv/tools` read-only; both files were already formatted.
- The `concorde_busy` message now also says to start no concorde command until the install or update ends. Final input: build --check, spec-validation success; full suite 804 passed, 4 skipped.
- task-validation: ok, ready, no blocking findings. delivery: ok, delivery commit fed76d7a.

## Closed: merged, 2026-09-30T03:50:10Z
