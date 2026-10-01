# Spec review scenarios

Concrete situations of [Spec review](module.md). The step sequence and the payload are in the
[Operation definition](operation.md), and those of the
Spec panel in its [definition](panel.md).

## Reviewing

### scenario.spec-review.accepted — A clear Spec is accepted and its suggestions recorded

- GIVEN a workspace whose [Module](../../glossary.json#concept.module) A validates without errors and has no earlier Issues
- AND a reviewer that finds only suggestions in A's documents
- WHEN the caller runs `spec_review` for Module A
- THEN the verdict is `accepted` and A's outcome carries the [context identity](../../glossary.json#concept.context-identity) of its `review-spec` grant
- AND each suggestion is returned and recorded as a new [Issue](../../glossary.json#concept.issue) of A with the tier `suggestion`, committed on the primary branch
- BUT no file of the workspace changes

### scenario.spec-review.changes-required — All blocking findings in one result

- GIVEN a Module A and a reviewer that reports two findings of blocking tiers about A's own documents: a requirement with two obligations, `obvious-fix`, and an entry that never shows a normal interaction, `decision-needed`
- WHEN the caller runs `spec_review` for Module A
- THEN the verdict is `changes_required`
- AND both problems are returned in the same result, each with its path, dimension, tier, evidence, suggestion and the Issue it was recorded as, whose report carries its tier, title, problem, impact and evidence

### scenario.spec-review.checker — The checker disputes a finding

- GIVEN a reviewer that reports one blocking finding the [Spec](../../glossary.json#concept.spec) does not support
- WHEN the caller runs `spec_review` with `--check-findings`
- THEN the checker marks that finding `disputed` with a reason
- AND the finding is still returned, naming no Issue, and no Issue is recorded for it
- BUT it does not make the verdict `changes_required`

### scenario.spec-review.several-modules — Each Module is reviewed on its own

- GIVEN Modules A and B without earlier Issues, where A uses B
- WHEN the caller runs `spec_review` for Modules A and B
- THEN one reviewer runs per Module, each under its own Module's `review-spec` grant
- AND a blocking problem A's reviewer notices in a B document becomes a `suggestion` naming B, recorded as an Issue owned by B
- AND the verdict combines both Modules' outcomes

### scenario.spec-review.unbound-reports — An unbound review reports to the project's Issues

- GIVEN the primary worktree, without a [workspace binding](../../glossary.json#concept.workspace-binding), whose Module A's Specs have one problem
- WHEN the caller runs `spec_review` for Module A there
- THEN the problem is recorded as an Issue of the project, whose report names the `spec_review` run and no task
- AND the primary worktree has no change but the Issue's commit

## Earlier Issues

### scenario.spec-review.earlier-issues — A repeated review builds on the earlier Issues

- GIVEN the project's open Issues I1 and I2 of `module.a`, of blocking tiers, and I3, a `suggestion`, all reported by earlier Spec reviews, and I4, open and owned by `module.a` but reported by a [task session](../../glossary.json#concept.task-session)
- WHEN a reviewer, given I1, I2 and I3 but not I4, reports the problem of I2 changed but still blocking, one new suggestion, and I3 and an unknown I9 resolved
- THEN I2 receives the changed finding as a new report, the new suggestion is recorded as a new Issue, and I1, I3 and I4 are unchanged
- AND the result lists I1 as carried with its tier and title, I3 as resolved with the reason and I9 as ignored
- AND the outcome is `changes_required`, since the carried I1 and the reported I2 are of blocking tiers

### scenario.spec-review.last-blocker-resolved — Resolving the last blocking Issue accepts the Module

- GIVEN the open Issue I1 of `module.a`, of a blocking tier, reported by an earlier Spec review, and no other earlier Issue
- WHEN a reviewer, given that Issue, reports no finding and I1 resolved with a reason
- THEN the outcome and the verdict are `accepted`
- AND the result lists I1 as resolved with that reason
- BUT I1 stays open, for the task to close

### scenario.spec-review.issues-refused — A refusal of the Issue store stops the reporting

- GIVEN a Module A whose reviewer reports two findings
- AND a task's merge into the primary branch that is unfinished
- WHEN the Operation reports A's findings
- THEN the store refuses the first report and no Issue is recorded
- AND A's outcome and the verdict are `incomplete`, and the result's error has, for A, the Operation's `issues_unreported` link whose cause is the Issue store's `merge_incomplete` refusal
- AND both findings are still returned, naming no Issue
- BUT the refusal is recorded as no Issue

## Stopping

### scenario.spec-review.structural-errors — A structurally invalid Spec is not reviewed

- GIVEN a Module A whose Specs fail a [structural check](../../glossary.json#concept.structural-check)
- WHEN the caller runs `spec_review` for Module A
- THEN no reviewer is launched for A
- AND A's outcome is `incomplete`, with the structural findings as host evidence
- AND the verdict is `incomplete`

### scenario.spec-review.worker-blocked — A reviewer that cannot finish

- GIVEN a Spec review of Module A whose reviewer ends `blocked`
- WHEN the [Operation](../../glossary.json#concept.operation) collects its result
- THEN A's outcome is `incomplete` and the verdict is `incomplete`
- AND the result's error is the Operation's `review_incomplete` link whose cause for A ends in the reviewer's own link with its detail, attempts and options unchanged

### scenario.spec-review.audit-change — A reviewer that changed a file

- GIVEN a reviewer after which the worktree has a changed file
- WHEN the Operation audits the worktree
- THEN the Module's outcome is `incomplete`
- AND the audit violation is returned as host evidence

## Paneling

### scenario.spec-review.panel-merged — The chair merges independent reviews into one report

- GIVEN a panel of two reviewers and no architect for Module A
- AND reviewer 1 reports that a requirement holds two obligations, and reviewer 2 reports the same problem in other words and a wording suggestion
- WHEN the chair merges the two reports of the requirement, gives the merged finding the tier `obvious-fix`, and rejects the wording suggestion with a reason
- THEN the panel report has one finding whose sources are `r1.1` and `r2.1`, reported by 2 workers, and the rejection of `r2.2`
- AND the merged finding is recorded as one Issue of tier `obvious-fix`, and nothing is recorded for the rejection
- AND each reviewer's own findings are in the result, labelled
- AND A's outcome and the verdict are `changes_required`
- BUT no file of the workspace changes

### scenario.spec-review.panel-architects — Architects judge the Module among all the Modules

- GIVEN Modules A and B, where A uses B, and a panel of two reviewers and two architects for Module A
- AND architect 1 reports that A relies on a promise B does not make, naming B as related
- WHEN the panel runs
- THEN each architect runs under A's `review-architecture` grant, which reads B's Specs, and each reviewer under A's `review-spec` grant
- AND the chair, under A's `review-architecture` grant, receives the architect's finding labelled `a1.1` besides the reviewers' findings
- AND the report's finding merged from `a1.1` is recorded as an Issue owned by A whose report names B
- AND A's outcome carries both context identities

### scenario.spec-review.panel-no-architects — A panel without architects

- GIVEN a panel of two reviewers with `--architects 0` for Module A
- WHEN the panel runs
- THEN no architect is launched, the chair runs under A's `review-spec` grant, and A's architecture identity is null

### scenario.spec-review.panel-worker-models — Each worker runs on the model of its worker id

- GIVEN a [worker configuration](../../glossary.json#concept.worker-configuration) putting every worker on Claude Code, giving `spec_panel`'s default a model and level, `reviewer2` another model, `architect1` a third model and level, and the `chair` its own model and level
- WHEN the caller runs `spec_panel` with two reviewers and one architect
- THEN `reviewer1` runs on the Operation's model, `reviewer2` on its own model at the Operation's level, `architect1` on its own model and level, and the `chair` on its own
- AND each worker's [run record](../../glossary.json#concept.run-record) names its [worker id](../../glossary.json#concept.worker-id), and the host evidence names the model each worker used

### scenario.spec-review.panel-accounting — A report that loses a finding goes back to the chair

- GIVEN a panel whose reviewers report `r1.1` and `r2.1`
- AND a chair whose first report accounts only for `r1.1`
- WHEN the Operation checks the report
- THEN the chair runs a second time with its previous report and the problem "r2.1 is not accounted for"
- AND the second report, which accounts for both, is the panel report

### scenario.spec-review.panel-short — A worker that cannot finish stops the panel

- GIVEN a panel of two reviewers and one architect for Module A, of which reviewer 2 ends `blocked`
- WHEN the workers have ended
- THEN the chair does not run, no Issue is recorded, and A's outcome and the verdict are `incomplete`
- AND the result's error is the Operation's `panel_incomplete` link whose cause for A is `panel_short`, with reviewer 2's link, naming its worker id, and below it the reviewer's own link unchanged
