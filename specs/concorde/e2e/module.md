# End-to-end testing

## Purpose

End-to-end testing is how the Concorde project tests itself on real codebases with real agents. It
takes a project from the Python repositories SWE-bench draws from, sets it up exactly as a user
would, runs a workflow in it with real workers, and lets the developer watch every run. It exists
for the people developing Concorde: nothing of it is installed into a project, and a Concorde user
never meets it. Its second job is to keep apart the problems that only testing conditions cause,
such as a headless main session or an untrusted scratch project, from the problems a user would
meet, so that the first are solved here rather than in what users get. Two children carry parts of
it: [Headless sessions](sessions/module.md) drives any real headless main session, and
[Dogfood scenarios](dogfood/module.md) tests a develop install's main agent against a known
Concorde defect.

## Terminology

| Term | Definition |
| --- | --- |
| Test project | A codebase from SWE-bench's repositories, cloned at a pinned revision into the end-to-end root, with Concorde installed, initialized and a task open. |
| End-to-end root | The directory holding the test projects, `CONCORDE_E2E_ROOT` or `~/concorde-e2e`, outside the home directory itself. |
| Headless run | A workflow run by a non-interactive `claude -p` main session started by the tool, waiting without limit for the workflow and granted its tools on the command line. |
| Driver run | A workflow run by the deterministic driver, which plays the pi runtime and has the pi script's step agents execute the real `concorde workflow` commands, with real workers. |
| Case | A SWE-bench task instance: an issue of one repository at its base commit, with a test patch and the tests that must pass once the issue is resolved. |
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
python3 scripts/e2e/e2e.py repair-specs <project> [--modules <ids>] [--task repair-specs]
python3 scripts/e2e/e2e.py grade <project> --instance <case.json> --python <interpreter> [--ref main] [--pythonpath <dir>]…
```

<a id="concept.e2e.test-project"></a><a id="concept.e2e.root"></a>

**Preparing a test project.** `repos` lists the repositories SWE-bench's harness names, read from
the vendored `references/swe-bench/`. `prepare psf/requests --rev v2.31.0` fetches that revision, a tag,
a branch or a commit, without earlier history into the **end-to-end root**, under `--name` or the
repository's name, checks it out as a `main` branch, installs Concorde from this checkout without
`d2`, initializes it, commits and opens a task bound to the root Module, which makes a **test
project**. It refuses a repository SWE-bench does not name unless `--any` is given, and a project
directory that already exists. The end-to-end root is never the home directory itself, where
Claude Code keeps no trust.

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

<a id="concept.e2e.case"></a>

**Grading a case.** A **case** tests Concorde's whole change flow on a real issue: the developer
builds the case's own Python environment outside the project (its interpreter and pinned
dependencies, never the project installed in it), prepares the case's repository at its base
commit under the case's name with `--python` naming that interpreter, which `concorde init`
records as the project's for its checks' `{python}`, adopts it with the brownfield workflow,
configures its checks, repairs the adopted Specs with `repair-specs`, and then works the issue
through Concorde as a main agent would, from `understand` to the merge. `grade` then decides
whether the merged change resolves the issue the way SWE-bench does: in a throwaway worktree of
`--ref` it puts every file the case's test patch touches back as it was at the case's base commit,
since the change may have edited the same test files, applies the test patch, runs the test files it names with the given interpreter
(`--pythonpath` directories of that worktree first on `PYTHONPATH`), and reports how many of the
FAIL_TO_PASS and PASS_TO_PASS tests passed, each one that did not, and whether the case is
resolved. The test patch and the case's tests stay outside the project: no worker sees them, and
the project is left as it was. The pytest output is kept under `.concorde/runs/e2e/`.

**Repairing the adopted Specs.** In a case the Specs are the test's own addition, describing code
the test never changes, so the review findings adoption leaves are repaired before the issue:
`repair-specs` opens a task over the adopted Modules, reviews them, runs `specify` once with that
review as input and an intent to change only what the Specs say, keeping every promise true to
the code and turning a repair that needs a decision about intent into an open question, reviews
them once more, and validates, delivers and merges the task. One round bounds it; what the
second review still finds is reported. Repairing a review's gaps automatically is otherwise a
decision for a person; this exception holds for end-to-end cases only, which is why it lives in
this Module and not in the workflow users run.

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

How End-to-end testing is built:

```d2
e2e: End-to-end testing {
  tool: End-to-end tool {
    "scripts/e2e/e2e.py"
    "scripts/e2e/common.py"
  }
}
```

<a id="realization.e2e.tool"></a>

The **End-to-end tool** realization is `scripts/e2e/e2e.py`: preparing, trusting, running and
watching test projects and grading cases, and the command line of its children's `session` and
`dogfood` commands; `scripts/e2e/common.py` holds what the tools share, the checkout, the
end-to-end root, the error type, running a command and cloning a revision.

<a id="realization.e2e.tests"></a>

The **End-to-end tool tests**, `tests/concorde/e2e/test_e2e.py`, check the tool's pure parts, the
repository list, trust, the headless command, cloning a revision and grading, on local
repositories only, without the network or agents, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).

## Relationships

```d2
e2e: End-to-end testing {
  sessions: Headless sessions
  dogfood: Dogfood scenarios
}
workflows: Workflows
distribution: Distribution
e2e -> workflows
e2e -> distribution
```

<a id="contains-sessions"></a>

**Headless sessions** drives a real headless Claude Code main session: it grants the session its
tools, tells it the conditions of running headless, wakes it when an Operation run it left behind
ends and keeps every round's log. The headless runs of workflows are headless sessions, and so are
the dogfood scenarios' sessions.

<a id="contains-dogfood"></a>

**Dogfood scenarios** injects a known fault into a clone of this checkout's Concorde, makes a
develop install of a real project from it, runs a headless session with an ordinary request and
evaluates whether the main agent reported the defect as Dogfooding requires without working around
it or changing Concorde.

<a id="uses-workflows"></a>

**Workflows** provides the workflows a test project runs, their rendered scripts and the stand-in
runtime of its tests that a driver run reuses, and the
[workflow result](../workflows/module.md#concept.workflows.result) a run ends with.

<a id="uses-distribution"></a>

**Distribution** provides the installer and the `concorde` command that set a test project up the
way a user's project is set up; a test project always runs the Concorde of this checkout.

SWE-bench is included as external material: its harness names the Python projects it draws from,
such as `psf/requests` and `pallets/flask`, existing codebases of known size and quality to test on.
