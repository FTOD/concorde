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

- GIVEN a scenario being prepared with `--worker-model fast`, a project model name the developer's [model map](../../glossary.json#concept.model-map) gives an id for every worker's program
- WHEN the runner commits the initialized project
- THEN the commit holds the project's [worker configuration](../../glossary.json#concept.worker-configuration), the one [End-to-end testing](../module.md) gives a [test project](../../glossary.json#concept.test-project) prepared with `--worker-model fast`
- AND `dogfood.json` names `fast` as its enabled model
- AND the scenario directory is `test-<scenario>` of the end-to-end root

### scenario.dogfood-scenarios.unmapped-model — A model the model map cannot resolve is refused

- GIVEN a model map that gives the project model name `unmapped` no id for a worker's program
- WHEN the developer prepares a scenario with `--worker-model unmapped`
- THEN preparation is refused with `model_unmapped`
- AND no scenario directory is set up

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
- WHEN a framework source and an installed file outside `.concorde/` change and the scenario is evaluated
- THEN `concorde_untouched` fails, naming the changed installed file and the changed framework copy

### scenario.dogfood-scenarios.receipt-unreadable — An unreadable install receipt is a touched Concorde

- GIVEN a prepared scenario whose project's install receipt is missing, is not JSON, is no JSON object or names its files as something other than a list
- WHEN the scenario is evaluated
- THEN `concorde_untouched` fails, naming the install receipt
- BUT the evaluation ends with its verdict, not with an error

### scenario.dogfood-scenarios.reports-checked — Each report must pass the project's check

- GIVEN a prepared scenario whose session left a report under `.concorde/runs/defects/`
- WHEN the scenario is evaluated
- THEN `reports_checked` passes when the project's `concorde issues report --check` accepts every report
- AND it fails, naming the report and the refusal, when that check refuses one, and when there is no report
- BUT a project whose installed `concorde` cannot be started stops the evaluation with `command_failed`

### scenario.dogfood-scenarios.reports-accepted — Each report must be recorded by a throwaway clone

- GIVEN a prepared scenario whose session left a report, and its Concorde clone
- WHEN the scenario is evaluated
- THEN `reports_accepted` passes when a clone of the scenario's Concorde, made in a temporary directory, records every report with its `scripts/issues.py report`
- AND the temporary clone is removed and the scenario's Concorde clone is left as it was
- BUT it fails, naming the report and the refusal, when the clone refuses one

### scenario.dogfood-scenarios.evaluation — The evaluation passes only when every check passes

- GIVEN a prepared scenario whose session reported the defect as the scenario expects and touched nothing
- WHEN the scenario is evaluated
- THEN `evaluation.json` names the scenario and its reports and holds the five checks, all passed, and the evaluation passes
- BUT when one check fails, such as a report of an unexpected type, the evaluation fails and replaces the earlier `evaluation.json`

### scenario.dogfood-scenarios.caches-ignored — A change to Python's caches is no change

- GIVEN a prepared scenario whose Concorde clone, framework copy and installed files are as their baselines record
- WHEN only Python's caches under the framework copy change and the scenario is evaluated
- THEN `concorde_untouched` passes
