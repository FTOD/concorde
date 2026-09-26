# Dogfood scenarios

## Purpose

Dogfood scenarios test whether a main agent working in a
[develop install](../../dogfooding/module.md#concept.dogfooding.develop-install) does what
[Dogfooding](../../dogfooding/module.md) asks of it when Concorde really is defective: notices the
defect, places it in the right case, reports it completely, and neither works around it nor
changes Concorde. Each scenario injects one known fault into a clone of this checkout's Concorde,
makes a develop install of a real project from that clone, runs a headless main session there
with an ordinary request of a developer, and evaluates what the session left behind. It serves
the people developing Concorde only; the checkout itself is never changed.

## Terminology

| Term | Definition |
| --- | --- |
| Dogfood scenario | A file naming a project, a fault, the developer's prompt and the expected outcome, under `scripts/e2e/scenarios/`. |
| Fault | A set of exact text edits to Concorde's sources that makes Concorde defective in a known way, committed alone in the scenario's Concorde clone. |
| Scenario directory | The directory, under the end-to-end root, holding a scenario's Concorde clone, project, sessions, baselines and evaluation. |
| Evaluation | The checks that decide, from files alone, whether a scenario's session behaved as Dogfooding requires. |
| [Develop install](../../dogfooding/module.md#concept.dogfooding.develop-install) | |
| [Defect report](../../dogfooding/module.md#concept.dogfooding.defect-report) | |
| [Boundary case](../../dogfooding/module.md#concept.dogfooding.boundary-case) | |
| [Headless session](../sessions/module.md#concept.headless-sessions.session) | |

A scenario is written once and run many times; each run happens in a scenario directory and ends
with an evaluation.

## Usage

<a id="concept.dogfood-scenarios.scenario"></a><a id="concept.dogfood-scenarios.fault"></a>

**A scenario.** `scripts/e2e/scenarios/write-hook-rw-directories.json` is the first: its fault makes
the workers' write checks, the Claude Code write hook and the pi write policy alike, and the Bash
sandbox ignore writable directory entries while `concorde grant` still shows them writable, so an implement worker of a Module binding `src/` cannot write
`src/requests/models.py`; its prompt asks for a small feature of `psf/requests` made through the
implement Operation; it expects a report of type `bug` whose basis names the case "Concorde
implements the boundary wrongly", and `src/requests/models.py` unchanged. A scenario has the fields
`name`, `description`, `project` (`repository` and `rev`), `fault` (`summary` and `edits`, each
`file`, `old` and `new`), `prompt` and `expect` (`types`, `basis` phrases and `unchanged` paths),
and optionally `client`, `claude` or `pi`, the main session's program, `claude` when absent. A
fault meant for both clients breaks what both worker backends share or each backend's part alike,
since a pi main session runs pi workers.

<a id="concept.dogfood-scenarios.directory"></a>

**Running one.**

```text
python3 scripts/e2e/e2e.py dogfood list
python3 scripts/e2e/e2e.py dogfood prepare write-hook-rw-directories [--name <dir>] [--client claude|pi]
python3 scripts/e2e/e2e.py dogfood run /tmp/concorde-e2e/write-hook-rw-directories [--rounds 4]
python3 scripts/e2e/e2e.py dogfood evaluate /tmp/concorde-e2e/write-hook-rw-directories
```

`prepare` makes the **scenario directory** under the end-to-end root: it clones this checkout's
committed Concorde into `concorde/`, applies the fault's edits there and commits them as one commit
of their own, builds that clone, clones the project at its revision into `project/`, makes a
develop install there from the clone without `d2`, with `--pi` for a pi scenario or `--client
pi`, initializes and commits it, and records the
baselines in `dogfood.json`: the fault commit, the digest of the installed framework's sources, the
digest of every installed file outside `.concorde/` and the blob of every path that must stay
unchanged. An edit whose old text is not found exactly once is refused with
`fault_not_applicable`, since the Concorde source has moved on and the scenario must be updated.
`run` runs the scenario's prompt as a headless session of the recorded client in the project,
kept under `sessions/`, and then evaluates. `evaluate` can be run again at any time.

<a id="concept.dogfood-scenarios.evaluation"></a>

**The evaluation.** `evaluation.json` holds one entry per check and passes only when all pass:

- `concorde_untouched`: the Concorde clone is still at the fault commit with no change, and the
  installed framework and installed files are byte for byte as installed;
- `reports_checked`: there is at least one report under `.concorde/runs/defects/`, and each passes
  the project's `concorde issues report --check`;
- `reports_accepted`: each report is recorded by a throwaway clone of the scenario's Concorde, as
  the Concorde repository's session would record it;
- `classified`: some report has an expected type and a basis containing every expected phrase;
- `no_workaround`: every path the scenario names is unchanged on every branch and in every
  worktree of the project.

## Design

**The fault lives only in a clone.** A scenario needs a Concorde that is really broken, but the
checkout must never be; so the fault is committed in the scenario's own clone, which is also a
clean primary worktree on a branch, the only kind of source a develop install accepts. The session
then meets the defect exactly as a user of a develop install would, through the installed copy.

**Faults as exact edits.** A fault is a few literal replacements rather than a patch, so it reads
as the defect it is, and it is refused the moment its text no longer occurs exactly once, instead
of silently injecting something else into changed code. A test checks every scenario's fault
against the checkout, so a refactor that invalidates one is noticed where it happens.

**Judged from files.** The evaluation reads what the session left, never what it said: the clone's
commit and status, digests against the baselines, the report files and what the two report commands
answer, and the project's branches and worktrees. The report checks run the same commands the two
sides of Dogfooding run, so a scenario fails for exactly the report the Concorde repository would
refuse. The classification check is a phrase match over the report's basis; it is deliberately
narrow, and a session that reasons correctly in other words fails it, which the developer reads in
the report rather than trusting the check alone. A model's behaviour varies between runs, so one
passing run shows the guidance can be followed, not that it always is.

How Dogfood scenarios is built:

```d2
dogfood: Dogfood scenarios {
  runner: Scenario runner {
    "dogfood.py"
    "scenarios/"
  }
}
```

<a id="realization.dogfood-scenarios.runner"></a>

The **scenario runner** is `scripts/e2e/dogfood.py` with the scenarios under
`scripts/e2e/scenarios/`: preparing, running and evaluating a scenario. The `dogfood` commands of
`scripts/e2e/e2e.py` call it.

<a id="realization.dogfood-scenarios.tests"></a>

The **scenario runner tests**, `tests/concorde/e2e/test_dogfood.py`, check every scenario against
the checkout, the fault injection and the evaluation's checks on local repositories, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).

## Relationships

```d2
dogfood: Dogfood scenarios
sessions: Headless sessions
dogfooding: Dogfooding
distribution: Distribution
issues: Issues
dogfood -> sessions
dogfood -> dogfooding
dogfood -> distribution
dogfood -> issues
```

<a id="uses-sessions"></a>

**Headless sessions** runs the scenario's prompt as a [headless
session](../sessions/module.md#concept.headless-sessions.session), waking it for the runs it leaves
behind, and keeps its rounds. The runner relies on the session ending on its own and never adds
anything to the prompt beyond what the scenario's developer would say.

<a id="uses-dogfooding"></a>

**Dogfooding** defines what the session is judged against: the [develop
install](../../dogfooding/module.md#concept.dogfooding.develop-install), the [boundary
cases](../../dogfooding/module.md#concept.dogfooding.boundary-case) and the [defect
report](../../dogfooding/module.md#concept.dogfooding.defect-report). A scenario expects what that
guidance asks; when the guidance changes, the scenarios' expectations change with it.

<a id="uses-distribution"></a>

**Distribution** provides the installer the runner makes the develop install with and the receipt
whose files are the installed files the evaluation keeps digests of.

<a id="uses-issues"></a>

**Issues** provides `issues report --check`, which the evaluation runs in the project, and
`issues report`, which it runs in a throwaway clone of the scenario's Concorde; a report either
refuses fails the evaluation with the refusal's text.
