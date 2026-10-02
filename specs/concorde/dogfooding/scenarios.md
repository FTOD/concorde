# Dogfooding scenarios

Concrete situations that show the [requirements](requirements.md) at work.

## Develop install

### scenario.dogfooding.develop-install — Install Concorde in develop mode

- GIVEN a [Concorde repository](../glossary.json#concept.concorde-repository) whose primary worktree is on a branch, built and fully committed
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

### scenario.dogfooding.refused-source — Refuse a linked worktree as the source

- GIVEN a built Concorde checkout that is a linked worktree of a Concorde repository, such as a task worktree, on a branch and fully committed
- WHEN the developer runs its installer on a project with `--develop`
- THEN the install is refused with `develop_source_not_primary`, naming the repository's primary worktree
- BUT nothing is written into the project

The source is checked in this order: the root of a Git worktree, the primary worktree, a branch,
no uncommitted change. A checkout that fails several checks is refused by the first, so a linked
worktree whose `HEAD` is detached is refused as a linked worktree.

### scenario.dogfooding.refused-not-root — Refuse a source that is not a worktree's root

- GIVEN a built Concorde checkout that is not the root of a Git worktree, such as a copy outside any Git repository or a directory inside another repository's worktree
- WHEN the developer runs its installer on a project with `--develop`
- THEN the install is refused with `develop_source_not_repository`, saying that the checkout is in no Git worktree or naming the worktree it lies inside
- BUT nothing is written into the project

### scenario.dogfooding.refused-detached — Refuse a primary worktree with a detached HEAD

- GIVEN the built, fully committed primary worktree of a Concorde repository whose `HEAD` is detached
- WHEN the developer runs its installer on a project with `--develop`
- THEN the install is refused with `develop_source_detached`, naming the detached `HEAD`
- BUT nothing is written into the project

### scenario.dogfooding.refused-dirty — Refuse a primary worktree with uncommitted changes

- GIVEN the built primary worktree of a Concorde repository, on a branch, with an uncommitted or untracked change
- WHEN the developer runs its installer on a project with `--develop`
- THEN the install is refused with `develop_source_dirty`, naming the changed paths
- BUT nothing is written into the project

### scenario.dogfooding.update-keeps-develop — Update a develop install

- GIVEN a [develop install](../glossary.json#concept.develop-install)
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
- WHEN a develop install's [main agent](../glossary.json#concept.main-agent) reads it
- THEN it is told to observe every run closely and to treat a wrong `ok` run like a failure
- AND never to change the Concorde repository, the framework copy or an installed file, nor to work around a [Concorde defect](../glossary.json#concept.concorde-defect)
- AND to place a refused read, write or tool in one of the four [boundary cases](../glossary.json#concept.boundary-case), with the evidence each needs, sending only the two Concorde cases to the Concorde repository
- AND to write a [defect report](../glossary.json#concept.defect-report) under `.concorde/runs/defects/` with every required field, among them `report_key` and `subtype`, a `null` owner, its `origin` and the [error chain](../glossary.json#concept.error-chain) with its own link on top built by `concorde task escalate`
- AND for a run that ended `ok` and still did something wrong to make its own link, without causes, the whole chain, citing the run: in a task built by `concorde task escalate` naming no run, and outside a task written by hand in the shape of the [error contract](../kernel/tracing/contracts.md#contract.tracing.error)
- AND for a defect seen outside a task to keep the report only under `.concorde/runs/defects/` and name it to the developer, opening no task for it
- AND to check it with `concorde issues report --check` before handing it over
- BUT for a defect of the Issue system itself to write no defect report and to hand over instead its [error chain](../glossary.json#concept.error-chain) with its own link on top, under `.concorde/runs/defects/`, while a refusal whose reason is `environment` is no defect but a wait
- AND to take the fix with `concorde update` while nothing runs, and to start nothing until the update ends

## Concorde repository

### scenario.dogfooding.concorde-instructions — The Concorde repository knows how to take a report

- GIVEN the Concorde repository's agent instructions, its `concorde-development` skill
- WHEN a session there is handed a defect report
- THEN the instructions tell it to record the report as an [Issue](../glossary.json#concept.issue) in a task opened for the [Module](../glossary.json#concept.module) it judges at fault
- AND to append a report to that Issue naming that Module as its `owner_target_id`
- AND to fix the defect generally and close the Issue with the fix
- AND to escalate to the developer before a design limitation changes Concorde's design or Protocol or loosens a boundary
- AND they contain the same observation rule as the develop guidance
