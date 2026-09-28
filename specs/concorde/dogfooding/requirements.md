# Dogfooding requirements

The Module-wide obligations of [Dogfooding](module.md). The [scenarios](scenarios.md) show them in
concrete situations.

## Develop install

### req.dogfooding.clean-primary-source — Only a clean primary worktree is installed from

A [develop install](../glossary.json#concept.develop-install), and every update of one, SHALL be
refused before anything is written unless the Concorde it installs from is the root of the primary
worktree of its Git repository, on a branch, with no uncommitted or untracked change.

### req.dogfooding.refusal-names-reason — A refused source names its reason

A refusal of a develop install, or of an update of one, by
[req.dogfooding.clean-primary-source](#req.dogfooding.clean-primary-source) SHALL name its reason:
not a worktree's root, a linked worktree (with the primary worktree's path), a detached `HEAD`, or
the uncommitted paths.

A refusal lists at most ten uncommitted paths and counts the rest.

### req.dogfooding.develop-kept — An update keeps develop mode

`concorde update` of a develop install SHALL install in develop mode again.

### req.dogfooding.update-commit-recorded — An update records the commit it installed

`concorde update` of a develop install SHALL record the commit it installed as the receipt's
`source_commit`.

## Guidance

### req.dogfooding.never-change-concorde — The project never changes Concorde

The develop guidance SHALL tell the project's [main agent](../glossary.json#concept.main-agent)
never to change the [Concorde repository](../glossary.json#concept.concorde-repository), the
framework copy under `.concorde/framework/` or any file the installer placed.

### req.dogfooding.no-workaround — The project never works around a Concorde defect

The develop guidance SHALL tell the project's main agent never to work around a
[Concorde defect](../glossary.json#concept.concorde-defect) in the project.

### req.dogfooding.defect-reported — The project reports a Concorde defect

The develop guidance SHALL tell the project's main agent to report every Concorde defect it finds.

### req.dogfooding.boundary-classified — A blocked boundary is placed in a case first

The develop guidance SHALL require the main agent to place every refused read, write or tool in one
of the four [boundary cases](../glossary.json#concept.boundary-case).

### req.dogfooding.boundary-evidence — A boundary case rests on three pieces of evidence

The develop guidance SHALL require the main agent to support the case of every refused read, write
or tool with the [Spec](../glossary.json#concept.spec) and Protocol source of the boundary, the
grant actually computed and the refused action.

### req.dogfooding.concorde-cases-only — Only the Concorde cases reach the Concorde repository

The develop guidance SHALL require the main agent to send only the two Concorde cases to the
Concorde repository.

### req.dogfooding.defect-report — A defect report is complete

The develop guidance SHALL require a [defect report](../glossary.json#concept.defect-report) to be
an [Issue report](../glossary.json#concept.issue-report) with every field its contract requires, a
`null` owner, its `origin` and the failure's whole
[error chain](../glossary.json#concept.error-chain) with the main agent's own link on top.

### req.dogfooding.report-checked — A defect report is checked before the hand-off

The develop guidance SHALL require a defect report to be checked with
`concorde issues report --check` before it is handed over.

## Concorde repository

### req.dogfooding.design-limits-decided — The developer decides design limitations

The Concorde repository's agent instructions SHALL require the developer's decision before a
report of a Concorde design limitation changes Concorde's design or Protocol or loosens a
boundary.

An implementation bug, whose fix brings Concorde back to its design, is fixed without that
decision.

### req.dogfooding.one-observation-rule — Both sides observe runs by the same rule

The develop guidance and the Concorde repository's agent instructions SHALL state the same rule for
observing runs, taken from the one shared prompt fragment.
