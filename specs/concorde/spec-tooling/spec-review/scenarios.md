# Spec review scenarios

Concrete situations of [Spec review](module.md). The host sequence and the payload are in the
[Operation definition](operation.md), and those of the Spec debate in its
[definition](debate.md).

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

## Debating

### scenario.spec-review.debate-agreement — Findings both debaters agree on stand

- GIVEN a reviewer that reports one blocking and one advisory finding for Module A
- AND a challenger that agrees with the blocking finding, objects to the advisory one and adds a blocking finding the reviewer missed
- WHEN the reviewer, answering in turn, agrees with the objection and with the added finding
- THEN the two blocking findings are `agreed` and the advisory one is `withdrawn`
- AND A's outcome and the verdict are `changes_required`
- AND no second challenge turn runs, because nothing awaits the challenger
- BUT no file of the task worktree changes

### scenario.spec-review.debate-contested — A disagreement after the last turn is a decision point

- GIVEN a reviewer that reports one blocking finding for Module A and a challenger that objects to it
- AND both keep objecting on every later turn
- WHEN the main agent runs `spec_debate` for Module A with `--challenges 2`
- THEN the debate ends after two challenge turns and the reviewer's second answer
- AND the finding is `contested`, with the reviewer's finding and the challenger's "does not hold" as the two positions and every objection in its history
- AND A's outcome and the verdict are `undecided`

### scenario.spec-review.debate-amended — An agreed amendment is what stands

- GIVEN a reviewer that reports a blocking finding for Module A
- AND a challenger that amends it to an advisory finding
- WHEN the reviewer agrees with the amendment
- THEN the advisory finding is `agreed`
- AND A's outcome and the verdict are `accepted`

### scenario.spec-review.debate-incomplete — A debater that cannot finish

- GIVEN a reviewer that reports a finding for Module A and a challenger that ends `blocked` because it needs a document outside its grant
- WHEN the host collects the challenger's result
- THEN A's debate stops with its item still `open`, and A's outcome and the verdict are `incomplete`
- AND the result's error is the Operation's `debate_incomplete` link whose cause for A names the turn and ends in the challenger's own link, unchanged
