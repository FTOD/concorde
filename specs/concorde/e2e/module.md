# End-to-end testing

## Purpose

End-to-end testing is how the Concorde project tests itself on real codebases with real agents. It
takes a project from the Python repositories SWE-bench draws from, sets it up exactly as a user
would, runs a workflow in it with real workers, and lets the developer watch every run. It exists
for the people developing Concorde: nothing of it is installed into a project, and a Concorde user
never meets it. Its second job is to keep apart the problems that only testing conditions cause,
such as a headless main session or an untrusted scratch project, from the problems a user would
meet, so that the first are solved here rather than in what users get. Three children carry parts
of it: [Headless sessions](sessions/module.md) drives any real headless main session,
[SWE-bench cases](cases/module.md) repairs and grades cases worked on real issues, and
[Dogfood scenarios](dogfood/module.md) tests a develop install's main agent against a known
Concorde defect.

## Terminology

| Term | Definition |
| --- | --- |
| Test project | A codebase from SWE-bench's repositories, cloned at a pinned revision into the end-to-end root, with Concorde installed, initialized and a task open. |
| End-to-end root | The directory holding the test projects, `CONCORDE_E2E_ROOT` or `concorde-e2e` in the system's temporary directory, `/tmp/concorde-e2e` on Linux. |
| Headless run | A workflow run by a non-interactive `claude -p` main session started by the tool, waiting without limit for the workflow and granted its tools on the command line. |
| Driver run | A workflow run by the deterministic driver, which plays the pi runtime and has the pi script's step agents execute the real `concorde workflow` commands, with real workers. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Workflow](../workflows/module.md#concept.workflows.workflow) | |
| [Workflow result](../workflows/module.md#concept.workflows.result) | |

A test project is where a headless run or a driver run happens; the end-to-end root is where test
projects live.

## Usage

The tool is one command of this checkout, `scripts/e2e/e2e.py`, printing one JSON object per
command and `{"error": …}` with the failed command and its output otherwise:

```text
python3 scripts/e2e/e2e.py repos
python3 scripts/e2e/e2e.py prepare <owner/name> --rev <tag|branch|commit> [--name <dir>] [--python <interpreter>] [--task <task>] [--any]
python3 scripts/e2e/e2e.py trust <project>…
python3 scripts/e2e/e2e.py run <project> [--via claude|driver] [--workflow brownfield] [--task <task>] [--mode no-ask|interactive] [--retry <key>]… [--restart <key>=<label>]…
python3 scripts/e2e/e2e.py watch <project>
```

Its children add `session` ([Headless sessions](sessions/module.md)), `repair-specs` and `grade`
([SWE-bench cases](cases/module.md)) and `dogfood` ([Dogfood scenarios](dogfood/module.md)).

<a id="concept.e2e.test-project"></a><a id="concept.e2e.root"></a>

**Preparing a test project.** `repos` lists the repositories SWE-bench's harness names, read from
the vendored `references/swe-bench/`. `prepare psf/requests --rev v2.31.0` fetches that revision, a tag,
a branch or a commit, without earlier history into the **end-to-end root**, under `--name` or the
repository's name, checks it out as a `main` branch, installs Concorde from this checkout without
`d2`, initializes it, commits and opens a task bound to the root Module, which makes a **test
project**. It refuses a repository SWE-bench does not name unless `--any` is given, and a project
directory that already exists. The end-to-end root defaults to the system's temporary
directory, never the developer's home: test projects are throwaway, and the home directory itself
is also where Claude Code keeps no trust.

**Trusting test projects.** Claude Code applies a project's `.claude/settings.json` allow rules,
which the installer writes for its workflows, only once that exact repository is trusted: trust is
keyed on the git repository root, a parent folder's trust does not count, and a headless session
never shows the trust dialog. `trust` marks each named project's repository root trusted in
Claude Code's configuration, `~/.claude.json` (or under `CLAUDE_CONFIG_DIR`), after backing the
file up once. It changes the developer's own configuration, so the developer runs it; a headless
run does not need it.

<a id="concept.e2e.headless-run"></a><a id="concept.e2e.driver-run"></a>

**Running a workflow.** `run` runs a workflow to its end in a test project and prints its
[workflow result](../workflows/module.md#concept.workflows.result), logging the session under
`.concorde/runs/e2e/`:

- A **headless run** (`--via claude`) runs, as a [headless
  session](sessions/module.md#concept.headless-sessions.session) kept under
  `.concorde/runs/e2e/<task>-claude/`, a main session asked to run the installed workflow and
  report. Two testing conditions are handled for it: `claude -p` otherwise stops a background
  workflow after ten idle minutes, so the session keeps `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`;
  and an untrusted project ignores its allow rules, so the workflow and its step commands are
  granted with `--allowedTools`.
- A **driver run** (`--via driver`) runs the project's rendered pi script under the stand-in
  runtime of the Workflows tests, whose step agents execute the real `concorde workflow step
  --stdin` and `report --stdin`. It has no model between steps, so it tests Concorde's side alone.

`--retry` and `--restart` pass the workflow's own arguments, for a run that continues a task.

**Watching.** `watch` lists every run of the project with its phase, step and outcome, and every
task's workflow steps with their runs and whether they were superseded.

## Design

End-to-end runs are not in the test suite. They clone from the network, spend real model tokens
and take tens of minutes, and their outcome depends on the model. The suite keeps the
deterministic acceptance test, which runs the same workflow with fake workers; this Module is
what the developer runs by hand, after a change to Adoption, Workflows or the worker harness, and
whose findings become ordinary tasks.

The headless run and the driver run answer different questions. The headless run is what a user's
main session does, Claude Code's workflow runtime and its step agents included. The driver run
removes the model from between the steps, so a failure there is Concorde's. When a headless run
fails, a driver run of the same task tells whether Concorde or the client runtime is at fault.

The testing conditions stay here. A user's main session is interactive and its project trusted,
so neither the wait ceiling nor the trust keying reaches the user-facing guidance; this Module
handles both for tests, and changes nothing a user gets.

<a id="realization.e2e.tool"></a>

The **End-to-end tool** realization is `scripts/e2e/e2e.py`: preparing, trusting, running and
watching test projects, and the command line of its children's `session`, `repair-specs`, `grade`
and `dogfood` commands; `scripts/e2e/common.py` holds what the tools share, the checkout, the
end-to-end root, the error type, running a command and cloning a revision.

<a id="realization.e2e.tests"></a>

The **End-to-end tool tests**, `tests/concorde/e2e/test_e2e.py`, check the tool's pure parts, the
repository list, trust, the headless command, cloning a revision and grading, on local
repositories only, without the network or agents, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).

### The children

Three children carry parts of End-to-end testing. Each reaches a different part of Concorde: a
headless session wakes on Operation runs, a case is set up through Distribution, and a dogfood
scenario drives headless sessions against a develop install that Dogfooding describes. The parent
itself runs the workflows a test project executes.

```d2
e2e: End-to-end testing {
  sessions: Headless sessions
  cases: SWE-bench cases
  dogfood: Dogfood scenarios
  dogfood -> sessions
}
operations: Operations
distribution: Distribution
dogfooding: Dogfooding
workflows: Workflows
e2e -> workflows
e2e.sessions -> operations
e2e.cases -> distribution
e2e.dogfood -> distribution
e2e.dogfood -> dogfooding
```

<a id="contains-sessions"></a>

**Headless sessions** drives a real headless Claude Code main session: it grants the session its
tools, tells it the conditions of running headless, wakes it when an Operation run it left behind
ends and keeps every round's log. The headless runs of workflows are headless sessions, and so are
the dogfood scenarios' sessions.

<a id="contains-cases"></a>

**SWE-bench cases** holds the steps that exist only for a case worked on a real issue: repairing
the Specs adoption left in one bounded round that changes Specs and never code, and grading the
merged change with the case's own tests in a throwaway worktree, the way SWE-bench grades it. A
case's project is a test project prepared here at the case's base commit.

<a id="contains-dogfood"></a>

**Dogfood scenarios** injects a known fault into a clone of this checkout's Concorde, makes a
develop install of a real project from it, runs a headless session with an ordinary request and
evaluates whether the main agent reported the defect as Dogfooding requires without working around
it or changing Concorde.

### Around it

End-to-end testing relies on two providers to set a test project up and run it.

<a id="uses-workflows"></a>

**Workflows** provides the workflows a test project runs, their rendered scripts and the stand-in
runtime of its tests that a driver run reuses, and the
[workflow result](../workflows/module.md#concept.workflows.result) a run ends with.

<a id="uses-distribution"></a>

**Distribution** provides the installer and the `concorde` command that set a test project up the
way a user's project is set up; a test project always runs the Concorde of this checkout.

SWE-bench is included as external material: its harness names the Python projects it draws from,
such as `psf/requests` and `pallets/flask`, existing codebases of known size and quality to test on.
