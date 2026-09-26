# Dogfooding scenarios

Concrete situations that show the [requirements](requirements.md) at work.

## Develop install

### scenario.dogfooding.develop-install — Install Concorde in develop mode

- GIVEN a Concorde repository whose primary worktree is on a branch, built and fully committed
- AND a project
- WHEN the developer runs the repository's installer on the project with `--develop`
- THEN Concorde is installed as a normal install would install it
- AND the receipt records mode `develop`, the repository as `source` and its `HEAD` as `source_commit`
- AND the installed skill ends with the section "Developing Concorde while using it" and the `CLAUDE.md` block with the develop paragraph

### scenario.dogfooding.normal-install — A normal install carries no develop guidance

- GIVEN the same Concorde repository and a project
- WHEN the developer installs without `--develop`
- THEN the receipt records mode `normal` and the source commit
- BUT neither the skill nor the `CLAUDE.md` block mentions developing Concorde

### scenario.dogfooding.refused-source — Refuse a source that is not a clean primary worktree

- GIVEN a Concorde checkout that is a linked task worktree, has a detached `HEAD` or has an uncommitted change
- WHEN the developer runs its installer on a project with `--develop`
- THEN the install is refused with `develop_source_not_primary`, `develop_source_detached` or `develop_source_dirty`, naming the primary worktree, the detached state or the changed paths
- BUT nothing is written into the project

### scenario.dogfooding.update-keeps-develop — Update a develop install

- GIVEN a develop install
- AND a new commit merged into the Concorde repository's primary worktree
- WHEN the project runs `concorde update`
- THEN Concorde is installed again in develop mode with the develop guidance
- AND the receipt's `source_commit` is the new commit

### scenario.dogfooding.update-dirty-source — An update from a dirty Concorde repository is refused

- GIVEN a develop install
- AND an uncommitted change in the Concorde repository's primary worktree
- WHEN the project runs `concorde update`
- THEN the update is refused with `develop_source_dirty` naming the change
- BUT the project's framework copy and receipt stay as they were

## Guidance

### scenario.dogfooding.guidance — The develop guidance states how to watch and report

- GIVEN the rendered develop guidance
- WHEN a develop install's main agent reads it
- THEN it is told to observe every run closely and to treat a wrong `ok` run like a failure
- AND never to change the Concorde repository, the framework copy or an installed file, nor to work around a Concorde defect
- AND to place a refused read, write or tool in one of the four boundary cases, with the evidence each needs, sending only the two Concorde cases to the Concorde repository
- AND to write a defect report under `.concorde/runs/defects/` with a `null` owner, its `origin` and the error chain with its own link on top built by `concorde task escalate`
- AND to take the fix with `concorde update` while nothing runs

## Concorde repository

### scenario.dogfooding.concorde-instructions — The Concorde repository knows how to take a report

- GIVEN the Concorde repository's agent instructions
- WHEN a session there is handed a defect report
- THEN the instructions tell it to record the report as an Issue in a task, fix the defect generally and close the Issue with the fix
- AND to wait for the developer's decision before a design limitation changes Concorde's design or Protocol or loosens a boundary
- AND they contain the same observation rule as the develop guidance
