# Dogfood scenarios scenarios

Concrete situations that show the [requirements](requirements.md) of
[Dogfood scenarios](module.md).

### scenario.dogfood-scenarios.scenarios-apply — Every scenario applies to this checkout

- GIVEN the scenarios under `scripts/e2e/scenarios/`
- WHEN they are read
- THEN each has its name, a prompt, expected types and a fault whose every old text occurs exactly once in this checkout's working tree

### scenario.dogfood-scenarios.unknown-scenario — An unknown scenario is refused

- GIVEN the scenarios under `scripts/e2e/scenarios/`
- WHEN a scenario none of them names is read
- THEN it is refused with `unknown_scenario` naming the known ones

### scenario.dogfood-scenarios.worker-configuration — The project gets a worker configuration

- GIVEN a scenario being prepared, with or without `--worker-model`
- WHEN the runner commits the initialized project
- THEN the commit holds the project's [worker configuration](../../glossary.json#concept.worker-configuration), the one [End-to-end testing](../module.md) gives a [test project](../../glossary.json#concept.test-project)
- AND `dogfood.json` names its enabled models
- BUT a model the developer's [model map](../../glossary.json#concept.model-map) gives no id for a worker's program is refused with `model_unmapped` before the scenario is set up

### scenario.dogfood-scenarios.fault — A fault is its own commit

- GIVEN a clean clone and a fault
- WHEN the runner injects it
- THEN the edits are applied and committed alone as "Inject fault: <summary>", leaving the clone clean

### scenario.dogfood-scenarios.fault-reinjected — A fault that no longer applies is refused

- GIVEN a clone into which a fault was injected
- WHEN the runner injects the same fault again
- THEN it is refused with `fault_not_applicable`, naming the file and how often the old text was found

### scenario.dogfood-scenarios.classified — A report is classified by type and basis

- GIVEN [defect reports](../../glossary.json#concept.defect-report) and a scenario expecting a type and basis phrases
- WHEN the evaluation classifies them
- THEN a report of an expected type whose basis contains every phrase, in any case, matches
- BUT a report of another type, one whose basis lacks a phrase and a file that is not JSON do not

### scenario.dogfood-scenarios.no-workaround — A changed path anywhere is a workaround

- GIVEN a project and a path recorded unchanged when the scenario was prepared
- WHEN the path changes in a worktree's files, or on a branch
- THEN the evaluation names each worktree and branch where it differs

### scenario.dogfood-scenarios.untouched — A changed framework or installed file is seen

- GIVEN a prepared scenario whose project has the framework copy and the installed files of its baselines
- WHEN a framework source or an installed file outside `.concorde/` changes and the scenario is evaluated
- THEN `concorde_untouched` fails, naming the changed installed file or the changed framework copy
- BUT a change only to Python's caches under the framework copy leaves `concorde_untouched` passing
