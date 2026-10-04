# The brownfield workflow

How [Method](module.md)'s [brownfield workflow](../glossary.json#concept.brownfield-workflow) runs:

- Its procedure.
- A run through one project.
- Each step's run and stopping rule.

The workflow machinery it runs on belongs to [Workflows](../workflows/module.md): steps, keys,
modes, the record and the report.

## The script

Method contributes the workflow's [workflow script](../glossary.json#concept.workflow-script),
`brownfield.js`. When its code loads, Method registers the workflow with Workflows' catalog. The
build renders the script with Workflows' Claude Code step adapter into the installed
`/concorde-brownfield` workflow.

Everything particular to this procedure lives with Method, never in Workflows. Its registration
names `delivery` as the procedure's last step. The script reads that step as `LAST_STEP`. The
[workflow result](../glossary.json#concept.workflow-result) is `ok` only when that step ended `ok`.
To order the `describe` steps, the script reads the Modules a scaffold created, with the `uses`
among them. Scaffold hands these to it in `data.created_modules` under the step output convention
([req.scaffold.step-output](scaffold/requirements.md#req.scaffold.step-output)). The script decides
whether to go on from these:

- A step's status.
- The workflow's mode.
- Whether a task validation declared its workspace not ready, through the convention's `blocking`
  ([req.validation.step-output](validation/requirements.md#req.validation.step-output)).

The script does not decide which items stop an interactive run either. The survey and the
code_to_spec runs declare their [decision points](../glossary.json#concept.decision-point) under
the [step output convention](../workflows/contracts.md#contract.workflows.step-output), as
[Adoption](adoption/module.md#decisions-and-open-questions) says. The Spec review reports its
verdict there as a note. Thus, without Workflows knowing any of these Operations, the workflow
result lists these:

- The decisions.
- The open questions.
- The proposed checks.
- The review's verdict.

## The procedure

The brownfield workflow's procedure as a flow, each dashed arrow a stop that goes straight to the
report:

```d2 illustrative
direction: down
survey: "survey"
scaffold: "scaffold"
describe: "describe:<id>\nproviders first, then <module>"
review: "spec_review"
validate: "validate\n(task-validation)"
delivery: "delivery --adoption"
report: "workflow report"
survey -> scaffold: "ok; no-ask, or every decision point answered"
survey -> report: "not ok; interactive with decision points not answered" {style.stroke-dash: 3}
scaffold -> describe: "ok"
scaffold -> report: "not ok" {style.stroke-dash: 3}
describe -> describe: "next Module; no-ask goes on even when not ok"
describe -> report: "interactive: not ok, or open questions not answered" {style.stroke-dash: 3}
describe -> review: "after <module>"
review -> validate: "ok, or no-ask"
review -> report: "interactive and not ok" {style.stroke-dash: 3}
validate -> delivery: "ok and ready"
validate -> report: "not ok, or not ready" {style.stroke-dash: 3}
delivery -> report
```

[Running the brownfield workflow](#running-the-brownfield-workflow) follows it through one project,
and [The brownfield procedure step by step](#the-brownfield-procedure-step-by-step) gives each
step's run and stopping rule.

## Running the brownfield workflow

For the [brownfield workflow](../glossary.json#concept.brownfield-workflow), where the coordination
part is installed, the [main agent](../glossary.json#concept.main-agent) opens a task from the
primary worktree. It starts the task's [task session](../glossary.json#concept.task-session).
Without that part, whoever prepares a bound workspace runs the workflow there the same way:

```text
concorde task open adopt --goal "describe the existing code in Specs" --modules module.shop
```

The task session then runs the installed Claude Code workflow `/concorde-brownfield` inside the
task worktree. It uses the arguments `{"module": "module.shop", "mode": "no-ask"}`. The arguments
name no workspace. Every command the workflow runs starts in that worktree, whose
[workspace binding](../glossary.json#concept.workspace-binding) names it. A worktree without a
binding runs no workflow: both workflow commands answer there with `binding_required`.

On the normal path that workflow runs eight steps in the `adopt` task worktree, one run after
another. The survey reads the code of `module.shop`. It proposes two children, `module.checkout`
and `module.inventory`, the first using the second. It also proposes the checks it found and
reports the decisions it took. The scaffold creates the two Modules with stub Specs. Three
code_to_spec runs then describe the Modules, providers first and the root last:

- `module.inventory`.
- `module.checkout`.
- `module.shop`.

Thus, the worker describing `module.checkout` reads the description of `module.inventory` rather
than its stub. A spec_review run reviews the three Modules. A `task-validation` run decides
whether the workspace is ready. Since it is, `delivery --adoption` makes the
[delivery commit](../glossary.json#concept.delivery-commit) on the task branch. The flag declares
that the workspace describes code which already existed. Linking the tests the scenarios were
taken from adds `verifies` decorators to test files. This counts as changed code. The flag exempts
those scenarios from Delivery's rule that changed code ships with a test for each scenario it
added or changed. [Delivery explains](delivery/module.md#running-delivery) this exemption. Every
other rule of delivery applies.

Each run is a step with its own key, listed in the workspace's
[workflow record](../glossary.json#concept.workflow-record):

- `survey`.
- `scaffold`.
- `describe:module.inventory`.
- `describe:module.checkout`.
- `describe:module.shop`.
- `spec_review`.
- `validate`.
- `delivery`.

Each step is a node `steps/<n>-<key>/` of the workflow's node, with its run's node inside it. The
workflow ends with its report, saved beside that record as `reports/1.json` with the Markdown
rendering `reports/1.md`. The report contains these:

- Status `ok`.
- Every decision and [open question](../glossary.json#concept.open-question) the runs reported.
- The review's verdict with each Module's count of blocking findings.
- The proposed checks.
- Every step that did not end `ok` with its [error chain](../glossary.json#concept.error-chain).

The task level copies the decisions into the task's
[decision log](../glossary.json#concept.decision-log). Merging the task stays its own step.

With `"mode": "interactive"` instead, when the survey took a decision nobody above the task
settled, the same workflow pauses right after the survey. One such decision is `d.db-helper`, where
the worker chose to keep the shared database helper with the root. The
[workflow result](../glossary.json#concept.workflow-result) has status `awaiting_decision`. It
lists `d.db-helper` with its options and recommendation. The record holds the one step `survey`.
Whoever started the workflow has the question settled. In Concorde, they escalate it to the main
agent. When its authority covers the question, the main agent settles it. Otherwise, it puts the
question to the developer. Whoever started the workflow starts it again with the answer under the
base key `survey`:

```json
{"module": "module.shop", "mode": "interactive",
 "answers": {"survey": [{"id": "d.db-helper",
   "question": "Does the shared database helper get a Module of its own?",
   "answer": "a Module of its own", "answered_by": "main-agent"}]}}
```

The answered survey is a new step, `survey@<digest>`, whose digest is taken from those answers. It
runs `survey --modules module.shop --answers <file> --input <first survey run>`. Thus, the new
survey follows the answer to the question the first one asked. It records its decision
`d.db-helper` as decided by `main-agent`, who gave the answer. It supersedes the step `survey`
together with every step recorded after it. Here there is none, since the workflow paused right
after the survey. The workflow then goes on from the scaffold as on the normal path. With the
same answers, a relaunch finds `survey@<digest>` again instead of running it once more.

After its scaffold ran, revising the survey is not a replay in the same workspace. For example,
this applies once a no-ask run's report shows a decision the developer would have taken otherwise.
Superseding the later steps forgets their records but undoes none of their writes. The scaffold
narrowed `module.shop` and registered its children. The descriptions stay. So the answered survey
refuses to run there. It ends `failed` with `fresh_workspace_required`, naming the Modules
`module.shop` contains since the workspace's base commit
([req.adoption.survey-after-scaffold](adoption/requirements.md#req.adoption.survey-after-scaffold)).
Like after any survey that did not end `ok`, the workflow ends with it. The procedure is a fresh
workspace:

- The main agent, or whoever prepares workspaces, opens a new task for `module.shop` from the
  primary worktree.
- Its task session starts the workflow there with the same answers under the base key `survey`.
- The survey of the new workspace follows those answers without the first workspace's run as
  input.

Nothing written in the first workspace is undone. The main agent decides whether its task is kept,
to compare or to take descriptions from, or closed unmerged. When its authority does not cover
that decision, the main agent puts it to the developer.

## The brownfield procedure step by step

| # | [Step key](../glossary.json#concept.step-key) | Run | Runs when | Ends the workflow when |
| --- | --- | --- | --- | --- |
| 1 | `survey` | Operation `survey --modules <module>` | always | not `ok`; interactive with [decision points](../glossary.json#concept.decision-point) not answered |
| 2 | `scaffold` | [execution command](../glossary.json#concept.execution-command) `scaffold --input <survey run>` | the survey is `ok` | not `ok` |
| 3 | `describe:<id>` | Operation `code_to_spec --modules <id>` | for each created [Module](../glossary.json#concept.module), providers before the Modules that use them, Modules that use each other in the scaffold's order, then `<module>` | interactive, and either not `ok` or with open questions not answered |
| 4 | `spec_review` | Operation `spec_review --modules <module and created Modules>` | always after 3 | interactive and not `ok` |
| 5 | `validate` | execution command `task-validation` | always after 4 | not `ok`, or readiness not ready |
| 6 | `delivery` | execution command `delivery --adoption` | validation ready | — |
| 7 | — | `concorde workflow report` | always, last | — |

Method's requirements specify the order, the stops and the last step:

- [req.method.brownfield-order](requirements.md#req.method.brownfield-order).
- [req.method.brownfield-providers-first](requirements.md#req.method.brownfield-providers-first).
- [req.method.brownfield-stops](requirements.md#req.method.brownfield-stops).
- [req.method.brownfield-last-step](requirements.md#req.method.brownfield-last-step).

A worktree without a binding runs no workflow at all, as Workflows requires
([req.workflows.bound-only](../workflows/requirements.md#req.workflows.bound-only)).

Created Modules are described providers first, by the `uses` the survey proposed among them.
Thus, a worker describing a consumer reads its providers' descriptions rather than their stubs.
Those `uses` may form cycles, which the Protocol allows. So the order condenses them into strongly
connected groups. Each time, the next group comes from those whose used groups are all described.
Among those groups, the one whose first Module the scaffold lists first is described next. Its
Modules are described in the scaffold's order. Within a group no order puts every provider first.
So a Module there may be described while a Module it uses still has its stub. Nothing is refused
for it. A `describe` step that did not end `ok` does not end a no-ask workflow. In that case:

- The Module keeps its stub or partial description.
- Task validation decides whether the workspace can still be delivered.
- The problem is reported.

Spec review findings are reported, not repaired, because repairing a
[Spec](../glossary.json#concept.spec) needs a decision.

