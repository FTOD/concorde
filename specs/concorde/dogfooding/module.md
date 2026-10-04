# Dogfooding

## Purpose

Dogfooding lets the developer use Concorde on a real project while also developing Concorde.
It turns what goes wrong there into fixes of Concorde. It provides:

- The **[develop
install](../glossary.json#concept.develop-install)**, which runs the Concorde of an independent
[Concorde repository](../glossary.json#concept.concorde-repository) the developer also changes.
- The guidance that makes the project's [main agent](../glossary.json#concept.main-agent) watch
  Concorde. It makes the main agent tell Concorde's defects from the project's own problems.
  It makes the main agent hand each defect over as an [Issue
report](../glossary.json#concept.issue-report).
- The rules by which the Concorde repository takes such a report and fixes it.

The developer and the main agents on both sides rely on it. It never changes Concorde from the
project. The project's main agent only observes and reports. Every fix is ordinary work in the
Concorde repository, under that repository's own procedures:

- tasks
- checks
- merges

It does not move a fix into the project on its own either. The project takes it with an ordinary
update. For a developer who only uses Concorde, a normal install has none of this.

## Core concepts

### Develop installs and the Concorde repository

<a id="concept.develop-install"></a><a id="concept.concorde-repository"></a>

A **[develop install](../glossary.json#concept.develop-install)** installs Concorde into a project
from the clean primary worktree of a
**[Concorde repository](../glossary.json#concept.concorde-repository)**.
The Concorde repository is the independent Git repository of Concorde that the developer also
changes. It is where the Concorde defects the project reports are fixed.
The develop install's receipt records the mode `develop`.
The main agent's guidance carries Dogfooding's section.
Otherwise, it is an ordinary install of the [parts](../glossary.json#concept.part) the developer
chooses. Its main agent reports defects as Issues. So Dogfooding's guidance is useful only where the
coordination and issues parts are installed. The section is composed into the guidance only there.

### Concorde defects and boundary cases

<a id="concept.concorde-defect"></a><a id="concept.boundary-case"></a>

For every problem, the project's main agent asks whose it is. A problem of the project is ordinary
work there. This includes problems of its:

- Specs
- code
- checks
- configuration

A **[Concorde defect](../glossary.json#concept.concorde-defect)** is one that would happen in any
project using Concorde the same way. It is a Concorde defect in either of these cases:

- Concorde implements its design wrongly.
- Concorde's design cannot serve what a correct project legitimately needs.

When a [boundary](../glossary.json#concept.boundary) blocks work, a refusal can concern:

- a read
- a write
- a tool

Such a refusal is where the two are most easily confused.
It is also where loosening the boundary is most often wrong, although that fix is tempting.
The guidance therefore makes the main agent place every refusal in one of four
**[boundary cases](../glossary.json#concept.boundary-case)** before it acts
([requirements](requirements.md#req.dogfooding.boundary-classified)):

| Case | How it is told | Where it goes | Who decides |
| --- | --- | --- | --- |
| The boundary is right; the work overreaches | The task's goal does not need that access | Nowhere: the work is done another way, or a task opens for the other [Module](../glossary.json#concept.module) | The main agent |
| The project's Specs draw the boundary wrongly | The grant is what the Protocol derives from the Specs, but the Specs misdescribe the Modules' ownership, uses or references | The project: an Issue there (`gap`) and a task that corrects the Specs | The developer, when the correction changes relations between Modules |
| Concorde implements the boundary wrongly | The grant or harness actually applied differs from what the Protocol derives from the Specs | A [defect report](../glossary.json#concept.defect-report) of type `bug` to the Concorde repository | The Concorde repository fixes it |
| Concorde's design blocks a correct boundary | The Specs are right and the grant is what the Protocol derives, yet legitimate work needs the access | A defect report of type `limitation` to the Concorde repository | The developer, before Concorde's design or Protocol changes |

The case is decided from three pieces of evidence. A report of a blocked boundary always carries
these pieces ([requirements](requirements.md#req.dogfooding.boundary-evidence)):

- The [Spec](../glossary.json#concept.spec) text and Protocol rule the boundary is derived from.
- The [grant](../glossary.json#concept.grant) actually computed (`concorde grant` and the run's host
  evidence).
- The refused action with its message.

Only the last two cases reach the Concorde repository
([requirements](requirements.md#req.dogfooding.concorde-cases-only)). Only for the third case may
the Concorde repository fix the defect without asking the developer.

### Defect reports

<a id="concept.defect-report"></a>

A **[defect report](../glossary.json#concept.defect-report)** is an
[Issue report](../glossary.json#concept.issue-report) the project's main agent writes about a
Concorde defect. Like every Issue report, it carries a [tier](../glossary.json#concept.issue-tier):
who may fix the defect in the Concorde repository. It also carries a
[severity](../glossary.json#concept.issue-severity): how much it matters to work using Concorde.
Since the Concorde repository decides which of its Modules is at fault, the report's owner is
`null`.
Its `origin` names the project and the Concorde commit the defect was seen on.
Its `error_chain` is the failure's whole [error chain](../glossary.json#concept.error-chain) with the
main agent's own link on top.

## Overview

### A defect's path

A Concorde defect crosses two repositories and three actors:

- The project's main agent reports it.
- The developer carries it to a session in the Concorde repository. The developer decides what
  only the developer may.
- That session fixes it.

The project then takes the fix with an update. The sections below explain each step:

```d2 illustrative
direction: down
project: The project {
  agent: Project main agent {
    observe: Observe a run closely
    classify: Whose problem is it?
    own: Ordinary work in the project
    write: Write the defect report, check it with concorde issues report --check
    log: Record it in the decision log, leave the blocked work open
    update: concorde update, then concorde spec-validation
    resume: "Have the open tasks' sessions merge the primary branch,\ntake up the blocked work"
    observe -> classify
    classify -> own: the project's own
    classify -> write: a Concorde defect
    write -> log
    update -> resume
  }
  framework: .concorde/framework/
}
developer: Developer {
  handoff: Hand the report's path to a session in the Concorde repository
  decide: Decide whether Concorde's design changes
  tell: Tell the project's main agent the fix is merged
}
concorde: Concorde repository {
  session: Concorde-repository session {
    record: Open a task for the Module at fault, record the report as an Issue
    assign: Append a report naming the Module at fault
    fix: Fix the defect generally, close the Issue with the fix
    merge: Deliver and merge the task
    record -> assign -> fix -> merge
  }
  primary: Primary worktree
}
project.agent.log -> developer.handoff: defect report
developer.handoff -> concorde.session.record
concorde.session.assign -> developer.decide: a design limitation {style.stroke-dash: 3}
developer.decide -> concorde.session.fix: decision {style.stroke-dash: 3}
concorde.session.merge -> concorde.primary: the fix
concorde.primary -> project.framework: install --develop, concorde update
concorde.primary -> developer.tell: merged
developer.tell -> project.agent.update
```

## Using a develop install

### Making a develop install

When the build is fresh and every change is committed, the developer runs this command in the
Concorde repository's primary worktree:

```text
python3 scripts/install-concorde.py <project> --develop
```

The installer first checks these conditions
([requirements](requirements.md#req.dogfooding.clean-primary-source)):

- It runs from the root of the repository's primary worktree.
- It runs on a branch.
- The worktree has no uncommitted or untracked change.

Because a task worktree disappears once its branch is merged, the installer refuses a task
worktree of the Concorde repository.
Because uncommitted changes would install a Concorde no commit records, the installer refuses them.
It then installs as a normal install does.
It copies the framework into the project.
It adds Dogfooding's guidance to the installed skill and `CLAUDE.md` block.
The receipt `.concorde/install.json` records:

- `mode:
"develop"`
- the repository as `source`
- the installed commit as `source_commit`

The project's own task worktrees therefore work exactly as in a normal install.
Only the main agent's guidance differs.

Under any of these conditions, the installer refuses a develop install without writing anything
([requirements](requirements.md#req.dogfooding.refusal-names-reason)):

- The checkout is not a Git worktree's root (`develop_source_not_repository`).
- The checkout is a linked worktree (`develop_source_not_primary`, naming the primary worktree).
  Where Git records no path for the primary worktree, the refusal names the Git directory instead.
- The checkout has a detached `HEAD` (`develop_source_detached`).
- The checkout has uncommitted changes (`develop_source_dirty`, naming them).
- Git cannot answer these questions about the checkout (`develop_source_unreadable`, with Git's own
  message).

Turning a develop install into a normal one, or the reverse, is a new install with or without
`--develop`.

### What the project's main agent does

Besides its work on the project, the project's main agent watches Concorde.
It closely observes each of these:

- every run of an [Operation](../glossary.json#concept.operation) or [execution
command](../glossary.json#concept.execution-command)
- every [workflow](../glossary.json#concept.workflow)
- every [worker](../glossary.json#concept.worker) run

Rather than trusting its status, the main agent closely observes:

- the result
- the [error chain](../glossary.json#concept.error-chain)
- the host evidence
- the [run
record](../glossary.json#concept.run-record)
- the changes it made

When a run ended `ok` but did something wrong, the main agent treats it like a failure.
The main agent never changes any of these
([requirements](requirements.md#req.dogfooding.never-change-concorde)):

- the Concorde repository
- the framework copy under `.concorde/framework/`
- any file the installer placed

The main agent never works around a defect in the project
([requirements](requirements.md#req.dogfooding.no-workaround)). It reports the defect
([requirements](requirements.md#req.dogfooding.defect-reported)).

### Reporting a defect

The main agent writes a **defect report** as JSON under `.concorde/runs/defects/<report_key>.json`.
The defect report is an [Issue report](../glossary.json#concept.issue-report).
Git ignores that path.
Since the Concorde repository decides which of its Modules is at fault, the report's owner is
`null`.
Its evidence paths are relative to the project. Its `origin` names:

- the project's absolute path
- the project's `HEAD`
- the `source_commit` of the receipt
- the task

Its `error_chain` is the failure's whole
[error chain](../glossary.json#concept.error-chain) with the main agent's own link on top.
Because the fix lies in a repository it never changes, that link's reason is `scope`.
In a task, `concorde task escalate … --reason scope --run <run>` builds and records exactly that link.
Because an `ok` run that still did something wrong reported no error, there is no chain to extend.
The main agent's link, without causes, is the whole chain.
The link cites the run.
When it names no run in a task, `concorde task escalate` records that link
([requirements](requirements.md#req.dogfooding.ok-run-defect)).
Outside a task, the main agent writes its link by hand in the shape of the Framework's
[error contract](../kernel/tracing/contracts.md#contract.tracing.error).
For a failure, its only cause is the failure's own error: the refusal's error or that of the run's
result.
For an `ok` run, it has no cause. The guidance lists every field the
[Issue report contract](../issues/interface.md#contract.issues.report) requires.
The guidance includes an example.
The guidance has the main agent check the report with `concorde issues report --check --file <path>`
([requirements](requirements.md#req.dogfooding.report-checked)).
That command runs the same checks as the Concorde repository when it records the report.
So an incomplete report is repaired where it was written rather than refused after the hand-off. In a task, the main agent does the following:

- It records the report in the task's [decision log](../glossary.json#concept.decision-log).
- It tells the developer where the report is.
- It keeps the runs the report names.
- It leaves the blocked work open.
- It turns to other work.

For a defect seen outside a task, the main agent opens no task for Concorde's sake
([requirements](requirements.md#req.dogfooding.defect-outside-task)).
Such a defect can occur in an [unbound run](../glossary.json#concept.unbound-run) or a refused command.
The main agent keeps its report only under `.concorde/runs/defects/`.
It names the report to the developer. For example:

```json
{
  "report_key": "grant-misses-used-module-tests",
  "tier": "obvious-fix",
  "severity": "high",
  "type": "bug",
  "subtype": null,
  "title": "The test grant omits the tests of a used Module",
  "description": "A test worker of task retry-limit was refused reading tests/billing/ ...",
  "impact": "The test Operation of any Module that uses another cannot run the other's tests.",
  "basis": "Case: Concorde implements the boundary wrongly. The Protocol's Boundaries chapter ...",
  "owner_target_id": null,
  "evidence": [
    {"path": ".concorde/runs/r-20261001T101500-test-1a2b3c4d/",
     "description": "host evidence with the computed grant and the refused read"}
  ],
  "origin": {
    "project": "/home/dev/payments",
    "head": "5d41402abc4b2a76b9719d911017c592ae1b3c1f",
    "concorde_commit": "098eb928f11c433960c35234c121d58c41f95833",
    "task": "retry-limit"
  },
  "error_chain": {"level": "main-agent", "actor": "main agent (task retry-limit)", "...": "..."}
}
```

### A defect of the Issue system

The main agent never writes a defect of Concorde's Issue system itself as a defect report
([requirements](requirements.md#req.dogfooding.issue-system-defect)). Such defects include crashes
or wrong results of these components:

- The Issue store.
- `concorde issues`.
- The [project MCP server](../glossary.json#concept.project-mcp-server)'s Issue tools.

They include `concorde issues report --check` refusing a correct report.
A defect report is an Issue report. The Concorde repository records it with its own Issue system.
Since the system that failed cannot be trusted to record its failure, nobody records that failure
as an Issue ([Issues](../issues/module.md#failures-of-the-issue-system)).
Such a defect travels as every other failure does, as its
[error chain](../glossary.json#concept.error-chain). The main agent puts its own link, reason
`scope`, on top of the failure's chain. In a task, it uses `concorde task escalate`.
That command also records the chain in the task. The main agent names the failure with one of
these options:

- `--run` names the run whose result carries it.
- `--error-file` names the failing command's `{"error": ...}` output.

Outside a task, the main agent writes its link by hand.
It writes that chain to `.concorde/runs/defects/<name>.error.json`.
It names the file to the developer. A refusal whose reason is `environment`, such as a busy merge
lock, is no defect. For such a refusal, the main agent waits and writes again.
The developer hands the chain to the Concorde repository as a failure.
The main agent there takes it up as any error chain the developer shows it.
It opens a task for the Issues Module.
It escalates in that task with `--error-file` naming the chain so the chain stays whole in that
task's record. It records no Issue.

### Fixing it in the Concorde repository

The developer hands the report's path to a session in the Concorde repository.
That session follows the repository's own agent instructions. It takes these steps:

- It records the report as an Issue of the repository. The repository checks its evidence in the
  origin project.
- It opens a task for the Module it judges at fault. The task names the Issue as one it resolves.
- It then appends a report to that Issue
  ([requirements](requirements.md#req.dogfooding.owner-assigned)). The report names the Module at
  fault as its `owner_target_id`. The report uses the Issue's
  `issue_id` and current `expected_revision`. Because the defect report's owner is `null`, this
  assigns ownership. The Issue's owner is its latest report's.

It fixes the defect generally, never only for the reporting project. It delivers the task as usual.
It merges the task as usual. The merge closes the Issue with the merge commit as evidence.
For a report of a Concorde design limitation, the developer decides before any of these changes
([requirements](requirements.md#req.dogfooding.design-limits-decided)):

- Concorde's design changes.
- The Protocol changes.
- A boundary loosens.

If a report turns out to be the project's own problem or overreaching work, the session closes it
`not-actionable` with the reason.

### Taking the fix

The project's main agent learns that the fix is merged in either way:

- From the developer.
- By listing the Concorde repository's Issues with `concorde issues list --root <source>`.

Once the fix is merged, the main agent runs `concorde update` from the project's primary worktree.
While a run of an Operation or execution command still runs in the project, the update refuses.
The update takes these steps:

- It re-checks that the Concorde repository's primary worktree is clean.
- It installs from that worktree again in develop mode
  ([requirements](requirements.md#req.dogfooding.develop-kept)).
- It records the commit it installed
  ([requirements](requirements.md#req.dogfooding.update-commit-recorded)).

Like every update, it leaves the project unvalidated until `concorde spec-validation` passes.
While the update runs, the main agent starts nothing in the project because its check does not stop
what starts afterward ([Distribution](../distribution/module.md#installing-into-a-project)).
When the update asks for it, the main agent then has the open tasks' sessions merge the primary
branch into their task branches.
The main agent takes up the blocked work.

## How it is built

### Around it

<a id="uses-distribution"></a>

**Distribution** provides the installer and `concorde update`.
Dogfooding relies on it for these actions:

- Call the develop source check before writing anything.
- On the check's refusal, refuse.
- Add the develop guidance to what it places.
- Record the mode and the source commit in the receipt.
- Keep develop mode on update.
- While Concorde runs in the project, refuse an update.

Distribution uses Dogfooding in turn for the check and the guidance.

<a id="uses-main-session"></a>

**Main session** owns the [main-session
guidance](../glossary.json#concept.main-session-guidance).
Dogfooding's section is added to that guidance. Dogfooding relies on these aspects of that guidance:

- Its method.
- Its tasks.
- Its decision logs.
- Its escalations.
- Its Issues.

Dogfooding adds only what a develop install needs on top.
It never changes what a normal install's main agent is told.

<a id="uses-issues"></a>

**Issues** provides the [Issue](../glossary.json#concept.issue) records and the
[Issue report](../glossary.json#concept.issue-report) shape with its `origin` and
`error_chain`. Dogfooding relies on the report command checking these:

- A report's evidence in its origin project.
- Its error chain against the Framework's
  [error contract](../kernel/tracing/contracts.md#contract.tracing.error).

When an incomplete defect report reaches the Concorde repository, these checks ensure that the
command refuses it.
The refusal names the field that is wrong.

<a id="uses-tasks"></a>

**Tasks** provides these:

- The [task](../glossary.json#concept.task) in which a defect is seen.
- Its [decision log](../glossary.json#concept.decision-log).
- `concorde task escalate`, which builds the main agent's link on top of a run's error chain for
  the report.

<a id="uses-spec"></a>

**Spec core** computes the [grant](../glossary.json#concept.grant) a boundary case is decided
against. `concorde grant` shows what the Protocol derives from the Specs.
The main agent compares that with what a run actually applied.

### Why it is built this way

**Two repositories, not a submodule.** Concorde could have been placed in the project as a Git
submodule and edited in place. It is not, for these reasons:

- A project's task worktrees would each get their own submodule checkout, unbuilt and without
  Concorde's environment.
- Because a submodule is checked out detached, commits made in it are easily lost.
- Concorde changes made from the project would bypass the Concorde repository's own procedures.
  Those changes would race the other sessions that merge there.

Those procedures include:

- Its tasks.
- Its validation.
- Its [merge lock](../glossary.json#concept.merge-lock).

With two repositories, the project keeps the ordinary copied framework, so nothing about its
worktrees changes. Concorde is changed only where its own rules apply.

**The project's main agent reports, it does not repair.** Because loosening a boundary is always
the quickest way on, the agent that it stops is least able to judge it fairly.
Keeping every change of Concorde elsewhere removes the temptation:

- In a different session.
- In a different repository.
- Under that repository's checks.

Before anyone changes the boundary, the boundary cases make the report say why it is wrong.
The same reasoning reserves the design-limitation case for the developer.
Fixing an implementation bug brings the code back to its design.
Changing the design changes what every project's boundaries mean.

**Issues carry the defect.** A defect report is an ordinary Issue report rather than a format of
its own. It has two optional fields: the origin and the error chain.
The Concorde repository uses the Issue machinery it already has for these actions:

- Records it.
- Solves it.
- Closes it.

The error chain stays the structured value every level of Concorde passes on.

The report is written in the project. It is recorded in the Concorde repository, where these
facts hold:

- The Module at fault is known.
- The fix is made.
- The closure merges with it.

The project never writes into the Concorde repository.
To be installed from, the Concorde repository's primary worktree must stay clean.
The one defect Issues cannot carry is a defect of the Issue system itself.
Because that system cannot be trusted to record it, the defect travels as its bare error chain.
That chain is the value every report would have carried anyway.

**Only a clean primary worktree is a source.** Since every later update installs from the receipt's
`source`, that source must outlive any single task. For the same reason, it must name a line of
development.
To let the Concorde repository tell whether the defect is already fixed at its head, `source_commit`
names exactly the Concorde a defect was seen on.

**One observation rule.** Watching runs closely is asked of the Concorde repository's own agents
too. The repository's agent instructions are its `concorde-development` skill.
Its `CLAUDE.md` tells every session to load that skill beside the `concorde` skill.
The root Module, not Dogfooding, binds the skill's source and that file.
Both sides receive the same sentence so they never differ on what observing a run means
([requirements](requirements.md#req.dogfooding.one-observation-rule)).
The sentence is kept once as a prompt fragment with these uses:

- The develop guidance includes it.
- The development skill includes it.
- The Dogfooding tests find it word for word in the rendered skill.

### The parts

<a id="realization.dogfooding.source-check"></a>

The **develop source check**, `src/concorde/dogfooding/develop.py`, decides whether a checkout may
be installed from in develop mode. It returns these:

- Its repository.
- Its branch.
- Its commit.

It reads the rendered develop guidance. It runs only Git queries.
Because it writes nothing, the installer calls it before writing anything.

<a id="realization.dogfooding.guidance"></a>

The **develop guidance** is written under `prompts/dogfooding/` in these files:

- `skill.md`, the section added to the installed skill.
- `claude-md.md`, the paragraph added to the `CLAUDE.md` block.
- `common/observe-runs.md`, the observation rule both sides share.

Distribution's build renders them into `generated/dogfooding/`.

<a id="realization.dogfooding.tests"></a>

The **Dogfooding tests**, under `tests/concorde/dogfooding/`, take these actions:

- Make develop installs from temporary Concorde repositories.
- Refuse the sources the requirements exclude.
- Update a develop install.
- Check the rendered guidance and the Concorde repository's agent instructions.

These actions verify the [requirements](requirements.md) and [scenarios](scenarios.md).
