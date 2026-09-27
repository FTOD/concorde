# Spec review scenarios

Concrete situations of [Spec review](module.md). The host sequence and the payload are in the
[Operation definition](operation.md), and those of the Spec panel in its
[definition](panel.md).

## Reviewing

### scenario.spec-review.accepted — A clear Spec is accepted

- GIVEN a task worktree whose Module A validates without errors
- AND a reviewer that finds only advisory problems in A's documents
- WHEN the main agent runs `spec_review` for Module A
- THEN the verdict is `accepted` and A's outcome carries the context identity of its `review-spec` grant
- AND the advisory findings are returned
- BUT no file of the task worktree changes

### scenario.spec-review.changes-required — All blocking findings in one result

- GIVEN a Module A whose requirements document has a requirement with two obligations and whose Usage never shows a normal path
- WHEN the main agent runs `spec_review` for Module A
- THEN the verdict is `changes_required`
- AND both problems are returned as blocking findings in the same result, each with its path, dimension, evidence and suggestion

### scenario.spec-review.checker — The checker disputes a finding

- GIVEN a reviewer that reports one blocking finding the Spec does not support
- WHEN the main agent runs `spec_review` with `--check-findings`
- THEN the checker marks that finding `disputed` with a reason
- AND the finding is still returned
- BUT it does not make the verdict `changes_required`

### scenario.spec-review.several-modules — Each Module is reviewed on its own

- GIVEN Modules A and B, where A uses B
- WHEN the main agent runs `spec_review` for Modules A and B
- THEN one reviewer runs per Module, each under its own Module's `review-spec` grant
- AND a problem A's reviewer notices in a B document is an advisory finding naming B
- AND the verdict combines both Modules' outcomes

## Stopping

### scenario.spec-review.structural-errors — A structurally invalid Spec is not reviewed

- GIVEN a Module A whose Specs fail a structural check
- WHEN the main agent runs `spec_review` for Module A
- THEN no reviewer is launched for A
- AND A's outcome is `incomplete`, with the structural findings as host evidence
- AND the verdict is `incomplete`

### scenario.spec-review.worker-blocked — A reviewer that cannot finish

- GIVEN a reviewer that ends `blocked` because it needs a document outside its grant
- WHEN the host collects its result
- THEN A's outcome is `incomplete` and the verdict is `incomplete`
- AND the result's error is the Operation's `review_incomplete` link whose cause for A ends in the reviewer's own link with its detail, attempts and options unchanged

### scenario.spec-review.memory — A repeated review builds on the memory

- GIVEN a task whose review memory of `module.a` holds the open blocking findings `f.1` and `f.2` and the open advisory `f.3`
- WHEN a reviewer, given those earlier findings, reports `f.2` changed, one new advisory finding, and `f.3` and an unknown `f.9` resolved
- THEN the memory keeps `f.2` with its new content, adds the new finding as `f.4`, marks `f.3` resolved with the reason and keeps `f.1` open
- AND the result lists `f.4` as new, `f.2` as updated, `f.3` as resolved, `f.1` as carried in full and `f.9` as ignored
- AND the outcome is `changes_required`, since `f.1` still stands
- BUT once every earlier blocking finding is resolved, the outcome is `accepted`

### scenario.spec-review.unchanged — Unchanged Specs are not reviewed again

- GIVEN a review memory of `module.a` recording the context identity of its current Specs as reviewed by run `r-earlier`, with the open blocking finding `f.1`
- WHEN a Spec review of `module.a` runs
- THEN no reviewer is launched, the outcome is `changes_required` from the memory, and the result names `r-earlier` as the review it is unchanged since
- AND a completed review records the context identity it judged and its run in the memory
- BUT with `--force` the reviewer runs whatever the memory records

### scenario.spec-review.audit-change — A reviewer that changed a file

- GIVEN a reviewer after which the worktree has a changed file
- WHEN the host audits the worktree
- THEN the Module's outcome is `incomplete`
- AND the audit violation is returned as host evidence

## Paneling

### scenario.spec-review.panel-merged — The chair merges independent reviews into one report

- GIVEN a panel of two reviewers for Module A
- AND reviewer 1 reports that a requirement holds two obligations, and reviewer 2 reports the same problem in other words and an advisory wording problem
- WHEN the chair merges the two reports of the requirement and rejects the wording problem with a reason
- THEN the panel report has one blocking finding whose sources are `r1.1` and `r2.1`, reported by 2 reviewers, and the rejection of `r2.2`
- AND each reviewer's own findings are in the result, labelled
- AND A's outcome and the verdict are `changes_required`
- BUT no file of the task worktree changes

### scenario.spec-review.panel-worker-models — Each reviewer runs on the model of its seat

- GIVEN a worker model configuration giving `spec_panel`'s reviewers one model and level, reviewer 2 another model, and the chair its own model and level
- WHEN the main agent runs `spec_panel` with two reviewers
- THEN reviewer 1 runs on the role's model, reviewer 2 on its own model at the role's level, and the chair on its own
- AND each worker's run record names its role and number, and the host evidence names the model each reviewer used

### scenario.spec-review.panel-accounting — A report that loses a finding goes back to the chair

- GIVEN a panel whose reviewers report `r1.1` and `r2.1`
- AND a chair whose first report accounts only for `r1.1`
- WHEN the host checks the report
- THEN the chair runs a second time with its previous report and the problem "r2.1 is not accounted for"
- AND the second report, which accounts for both, is the panel report

### scenario.spec-review.panel-short — A reviewer that cannot finish stops the panel

- GIVEN a panel of two reviewers for Module A, of which reviewer 2 ends `blocked` because it needs a document outside its grant
- WHEN the reviewers have ended
- THEN the chair does not run, and A's outcome and the verdict are `incomplete`
- AND the result's error is the Operation's `panel_incomplete` link whose cause for A is `panel_short`, with reviewer 2's link, naming its seat, and below it the reviewer's own link unchanged
