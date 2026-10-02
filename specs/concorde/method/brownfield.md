# The brownfield workflow

How [Method](module.md)'s [brownfield workflow](../glossary.json#concept.brownfield-workflow) runs:
its procedure, a run through one project, and each step's run and stopping rule. The workflow
machinery it runs on — steps, keys, modes, the record and the report — is
[Workflows](../workflows/module.md)'.

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

For the [brownfield workflow](../glossary.json#concept.brownfield-workflow), the [main agent](../glossary.json#concept.main-agent) opens
a task from the primary worktree and starts its [task session](../glossary.json#concept.task-session):

```text
concorde task open adopt --goal "describe the existing code in Specs" --modules module.shop
```

and the task session then, inside the task worktree, runs the installed Claude Code workflow
`/concorde-brownfield` with the arguments `{"module": "module.shop", "mode": "no-ask"}`. The
arguments name no workspace: every command the workflow runs starts in that worktree, whose
[workspace binding](../glossary.json#concept.workspace-binding) names it. A worktree without a
binding runs no workflow: both workflow commands answer there with `binding_required`.

On the normal path that workflow runs eight steps in the `adopt` task worktree, one run after
another. The survey reads the code of `module.shop` and proposes two children, `module.checkout`
and `module.inventory`, the first using the second, together with the checks it found and the
decisions it took. The scaffold creates the two Modules with stub Specs. Three code_to_spec runs
then describe `module.inventory`, `module.checkout` and last `module.shop`, providers first, so that
the worker describing `module.checkout` reads the description of `module.inventory` rather than its
stub. A spec_review run reviews the three Modules, a `task-validation` run decides whether the
workspace is ready, and, since it is, `delivery --adoption` makes the
[delivery commit](../glossary.json#concept.delivery-commit) on the task branch. Each run is a
step with its own key, `survey`, `scaffold`, `describe:module.inventory`, `describe:module.checkout`,
`describe:module.shop`, `spec_review`, `validate` and `delivery`, listed in the workspace's
[workflow record](../glossary.json#concept.workflow-record), each a node `steps/<n>-<key>/` of the workflow's node with its run's node inside it. The
workflow ends with its report, saved beside that record as `reports/1.json` with the
Markdown rendering `reports/1.md`: status `ok`, every decision and [open question](../glossary.json#concept.open-question) the runs
reported, the review's verdict and findings, the proposed checks and every step that
did not end `ok` with its [error chain](../glossary.json#concept.error-chain). The task level copies the decisions into the task's
[decision log](../glossary.json#concept.decision-log); merging the task stays its own step.

Started with `"mode": "interactive"` instead, the same workflow pauses right after the survey when
the survey took a decision nobody above the task has settled, such as `d.db-helper`, where the
worker chose to keep the shared database helper with the root. The [workflow result](../glossary.json#concept.workflow-result) has status
`awaiting_decision` and lists `d.db-helper` with its options and recommendation, and the record
holds the one step `survey`. Whoever started the workflow has the question settled, in Concorde by
escalating it to the main agent, which settles it when its authority covers it and otherwise puts
it to the developer, and starts it again with the
answer under the base key `survey`:

```json
{"module": "module.shop", "mode": "interactive",
 "answers": {"survey": [{"id": "d.db-helper",
   "question": "Does the shared database helper get a Module of its own?",
   "answer": "a Module of its own", "answered_by": "main-agent"}]}}
```

The answered survey is a new step, `survey@<digest>`, whose digest is taken from those answers. It
runs `survey --modules module.shop --answers <file> --input <first survey run>`, so the new survey
follows the answer to the question the first one asked and records its decision `d.db-helper` as
decided by `main-agent`, who gave the answer. It supersedes the step `survey` together
with every step recorded after it. Here there is none, since the workflow paused right after the
survey; had later steps been recorded, they would never be found again and would run anew. The
workflow then goes on from the scaffold as on the normal path, and a relaunch with the same answers
finds `survey@<digest>` again instead of running it once more.

## The brownfield procedure step by step

| # | [Step key](../glossary.json#concept.step-key) | Run | Runs when | Ends the workflow when |
| --- | --- | --- | --- | --- |
| 1 | `survey` | Operation `survey --modules <module>` | always | not `ok`; interactive with [decision points](../glossary.json#concept.decision-point) not answered |
| 2 | `scaffold` | [execution command](../glossary.json#concept.execution-command) `scaffold --input <survey run>` | the survey is `ok` | not `ok` |
| 3 | `describe:<id>` | Operation `code_to_spec --modules <id>` | for each created [Module](../glossary.json#concept.module), providers before the Modules that use them, then `<module>` | interactive, and either not `ok` or with open questions not answered |
| 4 | `spec_review` | Operation `spec_review --modules <module and created Modules>` | always after 3 | interactive and not `ok` |
| 5 | `validate` | execution command `task-validation` | always after 4 | not `ok`, or readiness not ready |
| 6 | `delivery` | execution command `delivery --adoption` | validation ready | — |
| 7 | — | `concorde workflow report` | always, last | — |

Created Modules are described providers first, by the `uses` the survey proposed among them, and
otherwise in the proposal's order, so that a worker describing a consumer reads its providers'
descriptions rather than their stubs. A `describe` step that did not end `ok` does not end a no-ask
workflow: the Module keeps its stub or partial description, task validation decides whether the
workspace can still be delivered, and the problem is reported. Spec review findings are reported,
not repaired, because repairing a [Spec](../glossary.json#concept.spec) needs a decision.

