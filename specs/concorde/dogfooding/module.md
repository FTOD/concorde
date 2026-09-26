# Dogfooding

## Purpose

Dogfooding lets the developer use Concorde on a real project while also developing Concorde, and
turns what goes wrong there into fixes of Concorde. It provides the **develop install**, which
runs the Concorde of an independent Concorde repository the developer also changes; the guidance
that makes the project's main agent watch Concorde, tell Concorde's defects from the project's
own problems, and hand each defect over as an Issue report; and the rules by which the Concorde
repository takes such a report and fixes it.

The developer and the main agents on both sides rely on it. It never changes Concorde from the
project: the project's main agent only observes and reports, and every fix is ordinary work in the
Concorde repository, under that repository's own tasks, checks and merges. It does not move a fix
into the project on its own either; the project takes it with an ordinary update. A normal
install, for a developer who only uses Concorde, has none of this.

## Terminology

| Term | Definition |
| --- | --- |
| Develop install | An installation of Concorde into a project from the clean primary worktree of a Concorde repository the developer also changes, recorded as mode `develop` in the receipt and carrying Dogfooding's guidance. |
| Concorde repository | The independent Git repository of Concorde that a develop install is made and updated from, and in which the Concorde defects it reports are fixed. |
| Concorde defect | A failure or wrong behaviour that would happen in any project using Concorde the same way, as opposed to a problem of the project it was seen in. |
| Defect report | An Issue report the project's main agent writes about a Concorde defect, naming the project and Concorde commit it was seen on and carrying the whole error chain. |
| Boundary case | One of the four explanations of a refused read, write or tool: overreaching work, a wrong project Spec, a Concorde implementation bug or a Concorde design limitation. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [Installer](../distribution/module.md#concept.distribution.installer) | |
| [Main-session guidance](../agents/main-session/module.md#concept.main-session.guidance) | |
| [Issue](../issues/module.md#concept.issues.issue) | |
| [Issue report](../issues/module.md#concept.issues.report) | |
| [Task](../tasks/module.md#concept.tasks.task) | |
| [Decision log](../tasks/module.md#concept.tasks.decision-log) | |
| [Grant](../spec-tooling/spec/module.md#concept.spec.grant) | |

Two repositories take part: the project, where Concorde is used and defects are seen, and the
Concorde repository, where they are fixed. A defect report is the only thing that passes from the
first to the second, and an update the only thing that passes back.

## Usage

<a id="concept.dogfooding.develop-install"></a><a id="concept.dogfooding.concorde-repository"></a>

**Making a develop install.** In the Concorde repository's primary worktree, with the build fresh
and every change committed, the developer runs

```text
python3 scripts/install-concorde.py <project> --develop
```

The installer first checks that it runs from the root of the repository's primary worktree, on a
branch, with no uncommitted or untracked change
([requirements](requirements.md#req.dogfooding.clean-primary-source)); a task worktree of the
Concorde repository is refused because it disappears once its branch is merged, and uncommitted
changes because they would install a Concorde no commit records. It then installs as a normal
install does, copying the framework into the project, and adds Dogfooding's guidance to the
installed skill and `CLAUDE.md` block. The receipt `.concorde/install.json` records `mode:
"develop"`, the repository as `source` and the installed commit as `source_commit`. The project's
own task worktrees therefore work exactly as in a normal install; only the main agent's guidance
differs.

**What the project's main agent does.** Besides its work on the project, it watches Concorde. It
observes every Operation, workflow and worker run closely, the result, error chain, host evidence,
run record and the changes it made, rather than trusting its status, and treats a run that ended
`ok` but did something wrong like a failure. It never changes the Concorde repository, the
framework copy or any file the installer placed
([requirements](requirements.md#req.dogfooding.never-change-concorde)), and never works around a
defect in the project. For every problem it asks whose it is: a problem of the project, its Specs,
code, checks or configuration, is ordinary work there; a **Concorde defect** is one that would
happen in any project using Concorde the same way.

<a id="concept.dogfooding.concorde-defect"></a><a id="concept.dogfooding.boundary-case"></a>

**When a boundary blocks work.** A refused read, write or tool is the case where the two are most
easily confused, and where the tempting fix, loosening the boundary, is most often wrong. The
guidance therefore makes the main agent place every refusal in one of four **boundary cases**
before it acts ([requirements](requirements.md#req.dogfooding.boundary-classified)):

| Case | How it is told | Where it goes | Who decides |
| --- | --- | --- | --- |
| The boundary is right; the work overreaches | The task's goal does not need that access | Nowhere: the work is done another way, or a task opens for the other Module | The main agent |
| The project's Specs draw the boundary wrongly | The grant is what the Protocol derives from the Specs, but the Specs misdescribe the Modules' ownership, uses or references | The project: an Issue there (`gap`) and a task that corrects the Specs | The developer, when the correction changes relations between Modules |
| Concorde implements the boundary wrongly | The grant or harness actually applied differs from what the Protocol derives from the Specs | A defect report of type `bug` to the Concorde repository | The Concorde repository fixes it |
| Concorde's design blocks a correct boundary | The Specs are right and the grant is what the Protocol derives, yet legitimate work needs the access | A defect report of type `limitation` to the Concorde repository | The developer, before Concorde's design or Protocol changes |

The case is decided from three pieces of evidence, which a report of a blocked boundary always
carries: the Spec text and Protocol rule the boundary is derived from, the
[grant](../spec-tooling/spec/module.md#concept.spec.grant) actually computed (`concorde grant` and
the run's host evidence), and the refused action with its message. Only the last two cases reach
the Concorde repository, and only the third may be fixed there without asking the developer.

<a id="concept.dogfooding.defect-report"></a>

**Reporting a defect.** The main agent writes a **defect report**: an
[Issue report](../issues/module.md#concept.issues.report) as JSON under
`.concorde/runs/defects/<report_key>.json`, which Git ignores. Its owner is `null`, since the
Concorde repository decides which of its Modules is at fault; its evidence paths are relative to
the project; its `origin` names the project's absolute path, the project's `HEAD`, the
`source_commit` of the receipt and the task; and its `error_chain` is the failure's whole
[error chain](../vocabulary.md#concept.concorde.error-chain) with the main agent's own link on
top, whose reason is `scope`: the fix lies in a repository it never changes. In a task,
`concorde task escalate … --reason scope --run <run>` builds and records exactly that link. The
guidance lists every field the Issue report contract requires, with an example, and has the main
agent check the report with `concorde issues report --check --file <path>`, which runs the checks
the Concorde repository will run when it records the report, so an incomplete report is repaired
where it was written rather than refused after the hand-off. The main agent records the report in
the task's
[decision log](../tasks/module.md#concept.tasks.decision-log), tells the developer where it is,
keeps the runs it names, leaves the blocked work open and turns to other work. For example:

```json
{
  "report_key": "grant-misses-used-module-tests",
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

**Fixing it in the Concorde repository.** The developer hands the report's path to a session in
the Concorde repository. That session follows the repository's own agent instructions: it opens a
task for the Module it judges at fault, records the report there as an Issue with
`python3 scripts/issues.py report --file <path> --task <task>`, whose evidence is checked in the
origin project, fixes the defect generally, never only for the reporting project, closes the
Issue on the task branch with the fix as evidence, and delivers and merges the task as usual. A
report of a Concorde design limitation waits for the developer's decision before anything changes
Concorde's design or Protocol or loosens a boundary
([requirements](requirements.md#req.dogfooding.design-limits-decided)); one that turns out to be
the project's own problem or overreaching work is closed `not-actionable` with the reason.

**Taking the fix.** Once the fix is merged, which the project's main agent learns from the
developer or by listing the Concorde repository's Issues with `concorde issues list --root
<source>`, it runs `concorde update` from the project's primary worktree. The update refuses while
an Operation run or a pi task-session round is still running in the project, re-checks that the
Concorde repository's primary worktree is clean, installs from it again in develop mode
([requirements](requirements.md#req.dogfooding.develop-kept)) and, like every update, leaves the
project unvalidated until `concorde validate` passes. The main agent then merges the primary branch
into the open tasks when the update asks for it and takes up the blocked work.

A develop install is refused, writing nothing, when the checkout is not a Git worktree's root
(`develop_source_not_repository`), is a linked worktree (`develop_source_not_primary`, naming the
primary worktree), has a detached `HEAD` (`develop_source_detached`) or has uncommitted changes
(`develop_source_dirty`, naming them). Turning a develop install into a normal one, or the reverse,
is a new install with or without `--develop`.

## Design

### Around it

<a id="uses-distribution"></a>

**Distribution** provides the [installer](../distribution/module.md#concept.distribution.installer)
and `concorde update`. Dogfooding relies on it to call the develop source check before writing
anything and to refuse on its refusal, to add the develop guidance to what it places, to record the
mode and the source commit in the receipt, to keep develop mode on update and to refuse an update
while Concorde runs in the project. Distribution uses Dogfooding in turn for the check and the
guidance.

<a id="uses-main-session"></a>

**Main session** owns the [main-session
guidance](../agents/main-session/module.md#concept.main-session.guidance) Dogfooding's section is
added to. Dogfooding relies on that guidance's method, tasks, decision logs, escalations and
Issues, and adds only what a develop install needs on top; it never changes what a normal install's
main agent is told.

<a id="uses-issues"></a>

**Issues** provides the [Issue](../issues/module.md#concept.issues.issue) records and the
[Issue report](../issues/module.md#concept.issues.report) shape with its `origin` and
`error_chain`. Dogfooding relies on the report command checking a report's evidence in its origin
project and its error chain against the Framework's error contract, so a defect report that
reaches the Concorde repository incomplete is refused with the field that is wrong.

<a id="uses-tasks"></a>

**Tasks** provides the [task](../tasks/module.md#concept.tasks.task) in which a defect is seen and
its [decision log](../tasks/module.md#concept.tasks.decision-log), and `concorde task escalate`,
which builds the main agent's link on top of a run's error chain for the report.

<a id="uses-spec"></a>

**Spec core** computes the [grant](../spec-tooling/spec/module.md#concept.spec.grant) a boundary
case is decided against: `concorde grant` shows what the Protocol derives from the Specs, which the
main agent compares with what a run actually applied.

### Inside

**Two repositories, not a submodule.** Concorde could have been placed in the project as a Git
submodule and edited in place. It is not, because a project's task worktrees would each get their
own submodule checkout, unbuilt and without Concorde's environment; a submodule is checked out
detached, so commits made in it are easily lost; and changes to Concorde made from the project
would bypass the Concorde repository's own tasks, validation and merge lock, racing the other
sessions that merge there. With two repositories, the project keeps the ordinary copied framework,
so nothing about its worktrees changes, and Concorde is changed only where its own rules apply.

**The project's main agent reports, it does not repair.** The agent that is stopped by a boundary
is the one least able to judge that boundary fairly: loosening it is always the quickest way on.
Keeping every change of Concorde in a different session, in a different repository, under that
repository's checks, removes the temptation, and the boundary cases make the report say why the
boundary is wrong before anyone changes it. The same reasoning reserves the design-limitation case
for the developer: fixing an implementation bug brings the code back to its design, while changing
the design changes what every project's boundaries mean.

**Issues carry the defect.** A defect report is an ordinary Issue report with two optional
fields, the origin and the error chain, rather than a format of its own: the Concorde repository
records, solves and closes it with the Issue machinery it already has, and the error chain stays
the structured value every level of Concorde passes on. It is written in the project and recorded
in the Concorde repository, where the Module at fault is known, the fix is made and the closure
merges with it. The project never writes into the Concorde repository, whose primary worktree must
stay clean to be installed from.

**Only a clean primary worktree is a source.** The receipt's `source` is where every later update
installs from, so it must outlive any single task and name a line of development; `source_commit`
then names exactly the Concorde a defect was seen on, so the Concorde repository can tell whether
the defect is already fixed at its head.

**One observation rule.** Watching runs closely is asked of the Concorde repository's own agents
too. Both receive the same sentence, kept once as a prompt fragment and checked against the
repository's agent instructions ([requirements](requirements.md#req.dogfooding.one-observation-rule)),
so that the two sides never drift into different ideas of what observing a run means.

<a id="realization.dogfooding.source-check"></a>

The **develop source check**, `src/concorde/dogfooding/develop.py`, decides whether a checkout may
be installed from in develop mode and returns its repository, branch and commit, and reads the
rendered develop guidance. It runs only Git queries and writes nothing, so the installer calls it
before writing anything.

<a id="realization.dogfooding.guidance"></a>

The **develop guidance** is written under `prompts/dogfooding/`: `skill.md`, the section added to
the installed skill, `claude-md.md`, the paragraph added to the `CLAUDE.md` block, and
`common/observe-runs.md`, the observation rule both sides share. Distribution's build renders them
into `generated/dogfooding/`.

<a id="realization.dogfooding.tests"></a>

The **Dogfooding tests**, under `tests/concorde/dogfooding/`, make develop installs from temporary
Concorde repositories, refuse the sources the requirements exclude, update a develop install, and
check the rendered guidance and the Concorde repository's agent instructions, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).
