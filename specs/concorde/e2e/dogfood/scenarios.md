# Dogfood scenarios scenarios

Concrete situations that show the [requirements](requirements.md) of
[Dogfood scenarios](module.md).

### scenario.dogfood-scenarios.scenarios-apply — Every scenario applies to this checkout

- GIVEN the scenarios under `scripts/e2e/scenarios/`
- WHEN they are read
- THEN each has its name, a prompt, expected types and a fault whose every old text occurs exactly once in this checkout
- BUT an unknown scenario is refused with `unknown_scenario` naming the known ones

### scenario.dogfood-scenarios.fault — A fault is its own commit

- GIVEN a clean clone and a fault
- WHEN the runner injects it
- THEN the edits are applied and committed alone as "Inject fault: <summary>", leaving the clone clean
- BUT injecting it again is refused with `fault_not_applicable`, naming the file and how often the old text was found

### scenario.dogfood-scenarios.classified — A report is classified by type and basis

- GIVEN defect reports and a scenario expecting a type and basis phrases
- WHEN the evaluation classifies them
- THEN a report of an expected type whose basis contains every phrase, in any case, matches
- BUT a report of another type, one whose basis lacks a phrase and a file that is not JSON do not

### scenario.dogfood-scenarios.no-workaround — A changed path anywhere is a workaround

- GIVEN a project and a path recorded unchanged when the scenario was prepared
- WHEN the path changes in a worktree's files, or on a branch
- THEN the evaluation names each worktree and branch where it differs

### scenario.dogfood-scenarios.untouched — A changed framework or installed file is seen

- GIVEN a project with the installed framework and installed files
- WHEN a framework source or an installed file changes
- THEN its digest differs from the baseline
- BUT Python's caches under the framework change nothing
