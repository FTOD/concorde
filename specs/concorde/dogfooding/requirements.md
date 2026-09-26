# Dogfooding requirements

The Module-wide obligations of [Dogfooding](module.md). The [scenarios](scenarios.md) show them in
concrete situations.

## Develop install

### req.dogfooding.clean-primary-source — Only a clean primary worktree is installed from

A develop install, and every update of one, SHALL be refused before anything is written unless the
Concorde it installs from is the root of the primary worktree of its Git repository, on a branch,
with no uncommitted or untracked change.

The refusal names the reason: not a worktree's root, a linked worktree (with the primary worktree's
path), a detached `HEAD`, or the uncommitted paths.

### req.dogfooding.develop-kept — An update keeps develop mode

`concorde update` of a develop install SHALL install in develop mode again and record the commit it
installed as the receipt's `source_commit`.

## Guidance

### req.dogfooding.never-change-concorde — The project never changes Concorde

The develop guidance SHALL tell the project's main agent never to change the Concorde repository,
the framework copy or any file the installer placed, and never to work around a Concorde defect in
the project, but to report it.

### req.dogfooding.boundary-classified — A blocked boundary is placed in a case first

The develop guidance SHALL require the main agent to place every refused read, write or tool in one
of the four boundary cases, to support the case with the Spec and Protocol source of the boundary,
the grant actually computed and the refused action, and to send only the two Concorde cases to the
Concorde repository.

### req.dogfooding.defect-report — A defect report is complete

The develop guidance SHALL require a defect report to be an Issue report with a `null` owner, its
`origin` and the failure's whole error chain with the main agent's own link on top.

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
