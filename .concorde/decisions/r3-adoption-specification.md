# Decision log: r3-adoption-specification

Goal: Fix the remaining open Issues of Adoption, Scaffold and Specification (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (23, listed in `resolves`; 6 of them decision-needed), all medium or
low, found by project_review r-20261008T063808-project_review-9851e69f or reported since. Read each
with `concorde issues show`.

By tier:
- **decision-needed**: read them all first and escalate them **together in one report, early**,
  each with what you found, the options and your recommendation (say which options change a
  promise users rely on or an earlier developer decision). The main agent settles those within its
  authority and takes the rest to the developer in one batch. Continue with the rest meanwhile.
  An Issue the developer is asked about may stay open: you may deliver without it; the main agent
  reopens it after the merge if needed.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it is wrong or costs more than it is worth; then say why in the
  log and your report, and the main agent closes it as not-actionable.
- An Issue that no longer holds (many Modules changed in rounds 1-2), is a duplicate or is already
  fixed: say so with evidence; it stays in `resolves` and the merge closes it.
- Medium first, then low. A fix needing a change outside the task's Modules: escalate, unless it is
  a small mechanical follow-on (a link, a fixture, a registry refresh).

Eleven other round-3 tasks (r3-*) run in parallel on other Modules. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-13T11:35:21Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-1b341f43e8c553909c96236d99e89358 (Adoption, medium): the survey host refuses a child whose folder (the parent entry's folder plus the last segment of the child identity, records.py child_folder) already exists, even empty, but req.adoption.proposal-checked does not state that rule. Scaffold already promises the same rule and mapping (req.scaffold.no-overwrite, scenario.scaffold.target-folder-exists: an existing child folder is refused even when empty, since the scaffold creates files only in folders it creates).
  Not handled here (decision): the Issue is decision-needed; settling it fixes a promise of Adoption
  Options: A: state in req.adoption.proposal-checked the rule Scaffold already promises: a child's folder is the parent entry's folder plus the identity's last segment, and a proposal whose child folder already exists, even empty, fails (no behaviour change; aligns Adoption with Scaffold); B: let an empty existing folder be reused, in both survey and scaffold (changes req.scaffold.no-overwrite and scenario.scaffold.target-folder-exists, a promise users rely on, and the code)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-1b341f43e8c553909c96236d99e89358 (Adoption, medium): the survey host refuses a child whose folder (the parent entry's folder plus the last segment of the child identity, records.py child_folder) already exists, even empty, but req.adoption.proposal-checked does not state that rule. Scaffold already promises the same rule and mapping (req.scaffold.no-overwrite, scenario.scaffold.target-folder-exists: an existing child folder is refused even when empty, since the scaffold creates files only in folders it creates).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; settling it fixes a promise of Adoption"
  },
  "options": [
    "A: state in req.adoption.proposal-checked the rule Scaffold already promises: a child's folder is the parent entry's folder plus the identity's last segment, and a proposal whose child folder already exists, even empty, fails (no behaviour change; aligns Adoption with Scaffold)",
    "B: let an empty existing folder be reused, in both survey and scaffold (changes req.scaffold.no-overwrite and scenario.scaffold.target-folder-exists, a promise users rely on, and the code)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:21Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-4c3ae7f8c15e584bbddebfa227571ded (Adoption, medium): scenario.adoption.survey-after-scaffold lets a survey of module.checkout, created by the workspace's scaffold, run as usual, while the specs_unloadable row says the survey fails when the surveyed Module's entry metadata at the base commit cannot be read. The code (survey.py module_block_at) already treats metadata absent at the base commit as naming nothing and fails only when Git or JSON reading fails.
  Not handled here (decision): the Issue is decision-needed; settling it fixes a promise of Adoption
  Options: A: state that entry metadata absent at the base commit names nothing (a Module created since then, such as a scaffold's child), and that specs_unloadable covers only metadata that exists there but cannot be read; scenario unchanged (matches the code); B: refuse surveys of Modules created since the base commit (changes the scenario and the code; the brownfield workflow could then not survey a new child in the same task)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-4c3ae7f8c15e584bbddebfa227571ded (Adoption, medium): scenario.adoption.survey-after-scaffold lets a survey of module.checkout, created by the workspace's scaffold, run as usual, while the specs_unloadable row says the survey fails when the surveyed Module's entry metadata at the base commit cannot be read. The code (survey.py module_block_at) already treats metadata absent at the base commit as naming nothing and fails only when Git or JSON reading fails.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; settling it fixes a promise of Adoption"
  },
  "options": [
    "A: state that entry metadata absent at the base commit names nothing (a Module created since then, such as a scaffold's child), and that specs_unloadable covers only metadata that exists there but cannot be read; scenario unchanged (matches the code)",
    "B: refuse surveys of Modules created since the base commit (changes the scenario and the code; the brownfield workflow could then not survey a new child in the same task)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:21Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-90948979bffb52d5b66d94fa08122f2f (Specification, medium): contract.specification.spec-change requires summary (non-empty), promise_changes and proposed_documents, 'the worker's claims', but a failed or timed-out worker may give no valid answer. The code (operation.py observe) takes summary from the worker result's output, else the worker result's own summary, else 'The worker gave no account of its change.', and gives empty lists. The run result's worker field already carries the worker's claims or their absence.
  Not handled here (decision): the Issue is decision-needed; the representation of absent claims is part of the public output contract
  Options: A: keep contract version 3; state the fallback (summary from the worker's output, else the worker result's own summary, else a fixed host sentence; empty promise_changes and proposed_documents) and that the run result's worker field, not these fields, tells absent claims from empty ones; claims come from the last worker launch's final result only (matches the code); B: contract version 4 with nullable summary, promise_changes and proposed_documents when no valid worker answer exists (changes the output shape consumers rely on, plus code and tests)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-90948979bffb52d5b66d94fa08122f2f (Specification, medium): contract.specification.spec-change requires summary (non-empty), promise_changes and proposed_documents, 'the worker's claims', but a failed or timed-out worker may give no valid answer. The code (operation.py observe) takes summary from the worker result's output, else the worker result's own summary, else 'The worker gave no account of its change.', and gives empty lists. The run result's worker field already carries the worker's claims or their absence.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; the representation of absent claims is part of the public output contract"
  },
  "options": [
    "A: keep contract version 3; state the fallback (summary from the worker's output, else the worker result's own summary, else a fixed host sentence; empty promise_changes and proposed_documents) and that the run result's worker field, not these fields, tells absent claims from empty ones; claims come from the last worker launch's final result only (matches the code)",
    "B: contract version 4 with nullable summary, promise_changes and proposed_documents when no valid worker answer exists (changes the output shape consumers rely on, plus code and tests)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:21Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-95e60a5416905b09927d7f561874ab7f (Adoption, medium): after a scaffold, the entry says the survey runs again in a fresh workspace 'with the answers that revise it', but answers must name decisions of an admitted earlier run (req.adoption.answers-first) and Execution admits inputs only from the same workspace (req.execution.inputs-same-workspace), so the first workspace's survey cannot be admitted there. The fresh_workspace_required refusal's options also say 'with the same answers'.
  Not handled here (decision): the Issue is decision-needed; the recovery procedure is a promise of Adoption, and option C would change Execution, outside this task
  Options: A: specify the procedure within the existing contracts: in the fresh workspace run the survey anew carrying the revision in --goal, then answer that run's own decision points with --answers and --input naming it; update the entry, req.adoption.survey-after-scaffold and the refusal's options, and add a scenario; B: let --answers be used without an admitted run when they come from another workspace's survey (weakens req.adoption.answers-first, a provenance promise); C: let Execution admit a run of another workspace as --input (changes req.execution.inputs-same-workspace of module.execution)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-95e60a5416905b09927d7f561874ab7f (Adoption, medium): after a scaffold, the entry says the survey runs again in a fresh workspace 'with the answers that revise it', but answers must name decisions of an admitted earlier run (req.adoption.answers-first) and Execution admits inputs only from the same workspace (req.execution.inputs-same-workspace), so the first workspace's survey cannot be admitted there. The fresh_workspace_required refusal's options also say 'with the same answers'.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; the recovery procedure is a promise of Adoption, and option C would change Execution, outside this task"
  },
  "options": [
    "A: specify the procedure within the existing contracts: in the fresh workspace run the survey anew carrying the revision in --goal, then answer that run's own decision points with --answers and --input naming it; update the entry, req.adoption.survey-after-scaffold and the refusal's options, and add a scenario",
    "B: let --answers be used without an admitted run when they come from another workspace's survey (weakens req.adoption.answers-first, a provenance promise)",
    "C: let Execution admit a run of another workspace as --input (changes req.execution.inputs-same-workspace of module.execution)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:21Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-cb5c4b8d498c5ef2b69b9e56d1c3328d (Specification, medium): req.specification.created-documents says a created document is empty and the Operation writes nothing else into it, while the entry and scenario.specification.new-document say its one line links to the entry (../module.md). The code (operation.py create_documents) writes a heading '# <title from the file name>' and 'Part of the Spec of [<Module title>](<relative link to the entry>).', and metadata with id, owner, role and empty defines and relations. No structural check needs that content.
  Not handled here (decision): the Issue is decision-needed; it chooses between competing observable promises
  Options: A: the host writes a minimal stub, a title heading named after the file and one line linking to the entry, with its metadata; align requirement, entry, contract and scenario (matches the code and code_to_spec's stubs); B: the host creates a truly empty reading file and the second worker writes the heading and link (code and test change)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-cb5c4b8d498c5ef2b69b9e56d1c3328d (Specification, medium): req.specification.created-documents says a created document is empty and the Operation writes nothing else into it, while the entry and scenario.specification.new-document say its one line links to the entry (../module.md). The code (operation.py create_documents) writes a heading '# <title from the file name>' and 'Part of the Spec of [<Module title>](<relative link to the entry>).', and metadata with id, owner, role and empty defines and relations. No structural check needs that content.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; it chooses between competing observable promises"
  },
  "options": [
    "A: the host writes a minimal stub, a title heading named after the file and one line linking to the entry, with its metadata; align requirement, entry, contract and scenario (matches the code and code_to_spec's stubs)",
    "B: the host creates a truly empty reading file and the second worker writes the heading and link (code and test change)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:22Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-d192d63e6e415e3ba929b2ca8fbe9076 (Specification, medium): contract.specification.spec-change lists a changed project glossary among changed_documents but defines affected_modules only by Spec contexts that contain a changed document; SpecContext.paths holds only documents and glossary terms are carried separately, so a glossary-only change yields no affected Module.
  Not handled here (decision): the Issue is decision-needed; it fixes what affected_modules promises
  Options: A: affected_modules also lists every Module whose Spec context, before or after the change, carries a glossary entry the change added, changed or removed, and the owner of each such entry before or after (the Spec context's definition already includes the glossary entries of its terms); implement and test; B: add only the owners of the changed entries; C: exclude glossary effects and state so
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-d192d63e6e415e3ba929b2ca8fbe9076 (Specification, medium): contract.specification.spec-change lists a changed project glossary among changed_documents but defines affected_modules only by Spec contexts that contain a changed document; SpecContext.paths holds only documents and glossary terms are carried separately, so a glossary-only change yields no affected Module.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; it fixes what affected_modules promises"
  },
  "options": [
    "A: affected_modules also lists every Module whose Spec context, before or after the change, carries a glossary entry the change added, changed or removed, and the owner of each such entry before or after (the Spec context's definition already includes the glossary entries of its terms); implement and test",
    "B: add only the owners of the changed entries",
    "C: exclude glossary effects and state so"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:25Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-1b341f43e8c553909c96236d99e89358 (Adoption, medium): the survey host refuses a child whose folder (the parent entry's folder plus the last segment of the child identity, records.py child_folder) already exists, even empty, but req.adoption.proposal-checked does not state that rule. Scaffold already promises the same rule and mapping (req.scaffold.no-overwrite, scenario.scaffold.target-folder-exists: an existing child folder is refused even when empty, since the scaffold creates files only in folders it creates).
  Not handled here (decision): the Issue is decision-needed; settling it fixes a promise of Adoption
  Options: A: state in req.adoption.proposal-checked the rule Scaffold already promises: a child's folder is the parent entry's folder plus the identity's last segment, and a proposal whose child folder already exists, even empty, fails (no behaviour change; aligns Adoption with Scaffold); B: let an empty existing folder be reused, in both survey and scaffold (changes req.scaffold.no-overwrite and scenario.scaffold.target-folder-exists, a promise users rely on, and the code)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-1b341f43e8c553909c96236d99e89358 (Adoption, medium): the survey host refuses a child whose folder (the parent entry's folder plus the last segment of the child identity, records.py child_folder) already exists, even empty, but req.adoption.proposal-checked does not state that rule. Scaffold already promises the same rule and mapping (req.scaffold.no-overwrite, scenario.scaffold.target-folder-exists: an existing child folder is refused even when empty, since the scaffold creates files only in folders it creates).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; settling it fixes a promise of Adoption"
  },
  "options": [
    "A: state in req.adoption.proposal-checked the rule Scaffold already promises: a child's folder is the parent entry's folder plus the identity's last segment, and a proposal whose child folder already exists, even empty, fails (no behaviour change; aligns Adoption with Scaffold)",
    "B: let an empty existing folder be reused, in both survey and scaffold (changes req.scaffold.no-overwrite and scenario.scaffold.target-folder-exists, a promise users rely on, and the code)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:25Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-4c3ae7f8c15e584bbddebfa227571ded (Adoption, medium): scenario.adoption.survey-after-scaffold lets a survey of module.checkout, created by the workspace's scaffold, run as usual, while the specs_unloadable row says the survey fails when the surveyed Module's entry metadata at the base commit cannot be read. The code (survey.py module_block_at) already treats metadata absent at the base commit as naming nothing and fails only when Git or JSON reading fails.
  Not handled here (decision): the Issue is decision-needed; settling it fixes a promise of Adoption
  Options: A: state that entry metadata absent at the base commit names nothing (a Module created since then, such as a scaffold's child), and that specs_unloadable covers only metadata that exists there but cannot be read; scenario unchanged (matches the code); B: refuse surveys of Modules created since the base commit (changes the scenario and the code; the brownfield workflow could then not survey a new child in the same task)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-4c3ae7f8c15e584bbddebfa227571ded (Adoption, medium): scenario.adoption.survey-after-scaffold lets a survey of module.checkout, created by the workspace's scaffold, run as usual, while the specs_unloadable row says the survey fails when the surveyed Module's entry metadata at the base commit cannot be read. The code (survey.py module_block_at) already treats metadata absent at the base commit as naming nothing and fails only when Git or JSON reading fails.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; settling it fixes a promise of Adoption"
  },
  "options": [
    "A: state that entry metadata absent at the base commit names nothing (a Module created since then, such as a scaffold's child), and that specs_unloadable covers only metadata that exists there but cannot be read; scenario unchanged (matches the code)",
    "B: refuse surveys of Modules created since the base commit (changes the scenario and the code; the brownfield workflow could then not survey a new child in the same task)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:25Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-90948979bffb52d5b66d94fa08122f2f (Specification, medium): contract.specification.spec-change requires summary (non-empty), promise_changes and proposed_documents, 'the worker's claims', but a failed or timed-out worker may give no valid answer. The code (operation.py observe) takes summary from the worker result's output, else the worker result's own summary, else 'The worker gave no account of its change.', and gives empty lists. The run result's worker field already carries the worker's claims or their absence.
  Not handled here (decision): the Issue is decision-needed; the representation of absent claims is part of the public output contract
  Options: A: keep contract version 3; state the fallback (summary from the worker's output, else the worker result's own summary, else a fixed host sentence; empty promise_changes and proposed_documents) and that the run result's worker field, not these fields, tells absent claims from empty ones; claims come from the last worker launch's final result only (matches the code); B: contract version 4 with nullable summary, promise_changes and proposed_documents when no valid worker answer exists (changes the output shape consumers rely on, plus code and tests)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-90948979bffb52d5b66d94fa08122f2f (Specification, medium): contract.specification.spec-change requires summary (non-empty), promise_changes and proposed_documents, 'the worker's claims', but a failed or timed-out worker may give no valid answer. The code (operation.py observe) takes summary from the worker result's output, else the worker result's own summary, else 'The worker gave no account of its change.', and gives empty lists. The run result's worker field already carries the worker's claims or their absence.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; the representation of absent claims is part of the public output contract"
  },
  "options": [
    "A: keep contract version 3; state the fallback (summary from the worker's output, else the worker result's own summary, else a fixed host sentence; empty promise_changes and proposed_documents) and that the run result's worker field, not these fields, tells absent claims from empty ones; claims come from the last worker launch's final result only (matches the code)",
    "B: contract version 4 with nullable summary, promise_changes and proposed_documents when no valid worker answer exists (changes the output shape consumers rely on, plus code and tests)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:25Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-95e60a5416905b09927d7f561874ab7f (Adoption, medium): after a scaffold, the entry says the survey runs again in a fresh workspace 'with the answers that revise it', but answers must name decisions of an admitted earlier run (req.adoption.answers-first) and Execution admits inputs only from the same workspace (req.execution.inputs-same-workspace), so the first workspace's survey cannot be admitted there. The fresh_workspace_required refusal's options also say 'with the same answers'.
  Not handled here (decision): the Issue is decision-needed; the recovery procedure is a promise of Adoption, and option C would change Execution, outside this task
  Options: A: specify the procedure within the existing contracts: in the fresh workspace run the survey anew carrying the revision in --goal, then answer that run's own decision points with --answers and --input naming it; update the entry, req.adoption.survey-after-scaffold and the refusal's options, and add a scenario; B: let --answers be used without an admitted run when they come from another workspace's survey (weakens req.adoption.answers-first, a provenance promise); C: let Execution admit a run of another workspace as --input (changes req.execution.inputs-same-workspace of module.execution)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-95e60a5416905b09927d7f561874ab7f (Adoption, medium): after a scaffold, the entry says the survey runs again in a fresh workspace 'with the answers that revise it', but answers must name decisions of an admitted earlier run (req.adoption.answers-first) and Execution admits inputs only from the same workspace (req.execution.inputs-same-workspace), so the first workspace's survey cannot be admitted there. The fresh_workspace_required refusal's options also say 'with the same answers'.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; the recovery procedure is a promise of Adoption, and option C would change Execution, outside this task"
  },
  "options": [
    "A: specify the procedure within the existing contracts: in the fresh workspace run the survey anew carrying the revision in --goal, then answer that run's own decision points with --answers and --input naming it; update the entry, req.adoption.survey-after-scaffold and the refusal's options, and add a scenario",
    "B: let --answers be used without an admitted run when they come from another workspace's survey (weakens req.adoption.answers-first, a provenance promise)",
    "C: let Execution admit a run of another workspace as --input (changes req.execution.inputs-same-workspace of module.execution)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:25Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-cb5c4b8d498c5ef2b69b9e56d1c3328d (Specification, medium): req.specification.created-documents says a created document is empty and the Operation writes nothing else into it, while the entry and scenario.specification.new-document say its one line links to the entry (../module.md). The code (operation.py create_documents) writes a heading '# <title from the file name>' and 'Part of the Spec of [<Module title>](<relative link to the entry>).', and metadata with id, owner, role and empty defines and relations. No structural check needs that content.
  Not handled here (decision): the Issue is decision-needed; it chooses between competing observable promises
  Options: A: the host writes a minimal stub, a title heading named after the file and one line linking to the entry, with its metadata; align requirement, entry, contract and scenario (matches the code and code_to_spec's stubs); B: the host creates a truly empty reading file and the second worker writes the heading and link (code and test change)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-cb5c4b8d498c5ef2b69b9e56d1c3328d (Specification, medium): req.specification.created-documents says a created document is empty and the Operation writes nothing else into it, while the entry and scenario.specification.new-document say its one line links to the entry (../module.md). The code (operation.py create_documents) writes a heading '# <title from the file name>' and 'Part of the Spec of [<Module title>](<relative link to the entry>).', and metadata with id, owner, role and empty defines and relations. No structural check needs that content.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; it chooses between competing observable promises"
  },
  "options": [
    "A: the host writes a minimal stub, a title heading named after the file and one line linking to the entry, with its metadata; align requirement, entry, contract and scenario (matches the code and code_to_spec's stubs)",
    "B: the host creates a truly empty reading file and the second worker writes the heading and link (code and test change)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:26Z

- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-d192d63e6e415e3ba929b2ca8fbe9076 (Specification, medium): contract.specification.spec-change lists a changed project glossary among changed_documents but defines affected_modules only by Spec contexts that contain a changed document; SpecContext.paths holds only documents and glossary terms are carried separately, so a glossary-only change yields no affected Module.
  Not handled here (decision): the Issue is decision-needed; it fixes what affected_modules promises
  Options: A: affected_modules also lists every Module whose Spec context, before or after the change, carries a glossary entry the change added, changed or removed, and the owner of each such entry before or after (the Spec context's definition already includes the glossary entries of its terms); implement and test; B: add only the owners of the changed entries; C: exclude glossary effects and state so
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-adoption-specification)",
  "code": "decision_needed_issue",
  "detail": "I-d192d63e6e415e3ba929b2ca8fbe9076 (Specification, medium): contract.specification.spec-change lists a changed project glossary among changed_documents but defines affected_modules only by Spec contexts that contain a changed document; SpecContext.paths holds only documents and glossary terms are carried separately, so a glossary-only change yields no affected Module.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the Issue is decision-needed; it fixes what affected_modules promises"
  },
  "options": [
    "A: affected_modules also lists every Module whose Spec context, before or after the change, carries a glossary entry the change added, changed or removed, and the owner of each such entry before or after (the Spec context's definition already includes the glossary entries of its terms); implement and test",
    "B: add only the owners of the changed entries",
    "C: exclude glossary effects and state so"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Task session note, 2026-10-13

Escalations 7 to 12 are accidental duplicates of escalations 1 to 6 (the escalation script ran
twice). They carry nothing new. The report names only escalations 1 to 6. Escalations 1 to 6 are
the six decision-needed Issues: I-1b341f43 (1), I-4c3ae7f8 (2), I-90948979 (3), I-95e60a54 (4),
I-cb5c4b8d (5) and I-d192d63e (6).

## Report 1 to the main agent (Review流程), 2026-10-13T11:35:45Z

Early escalation of the six decision-needed Issues (escalations 1-6; 7-12 are accidental duplicates of 1-6, see the decision log). Every recommendation is option A, which matches the current code and changes no promise users rely on, except that A of escalation 6 (glossary in affected_modules) widens what affected_modules reports. Options that would change a promise or an earlier decision: 1B (req.scaffold.no-overwrite), 2B, 3B (output shape), 4B (answer provenance), 4C (Execution, outside this task). I go on with the 17 other Issues meanwhile and will deliver; an unanswered Issue may stay open.

Escalation 1:
- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-1b341f43e8c553909c96236d99e89358 (Adoption, medium): the survey host refuses a child whose folder (the parent entry's folder plus the last segment of the child identity, records.py child_folder) already exists, even empty, but req.adoption.proposal-checked does not state that rule. Scaffold already promises the same rule and mapping (req.scaffold.no-overwrite, scenario.scaffold.target-folder-exists: an existing child folder is refused even when empty, since the scaffold creates files only in folders it creates).
  Not handled here (decision): the Issue is decision-needed; settling it fixes a promise of Adoption
  Options: A: state in req.adoption.proposal-checked the rule Scaffold already promises: a child's folder is the parent entry's folder plus the identity's last segment, and a proposal whose child folder already exists, even empty, fails (no behaviour change; aligns Adoption with Scaffold); B: let an empty existing folder be reused, in both survey and scaffold (changes req.scaffold.no-overwrite and scenario.scaffold.target-folder-exists, a promise users rely on, and the code)
  Recommendation: A

Escalation 2:
- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-4c3ae7f8c15e584bbddebfa227571ded (Adoption, medium): scenario.adoption.survey-after-scaffold lets a survey of module.checkout, created by the workspace's scaffold, run as usual, while the specs_unloadable row says the survey fails when the surveyed Module's entry metadata at the base commit cannot be read. The code (survey.py module_block_at) already treats metadata absent at the base commit as naming nothing and fails only when Git or JSON reading fails.
  Not handled here (decision): the Issue is decision-needed; settling it fixes a promise of Adoption
  Options: A: state that entry metadata absent at the base commit names nothing (a Module created since then, such as a scaffold's child), and that specs_unloadable covers only metadata that exists there but cannot be read; scenario unchanged (matches the code); B: refuse surveys of Modules created since the base commit (changes the scenario and the code; the brownfield workflow could then not survey a new child in the same task)
  Recommendation: A

Escalation 3:
- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-90948979bffb52d5b66d94fa08122f2f (Specification, medium): contract.specification.spec-change requires summary (non-empty), promise_changes and proposed_documents, 'the worker's claims', but a failed or timed-out worker may give no valid answer. The code (operation.py observe) takes summary from the worker result's output, else the worker result's own summary, else 'The worker gave no account of its change.', and gives empty lists. The run result's worker field already carries the worker's claims or their absence.
  Not handled here (decision): the Issue is decision-needed; the representation of absent claims is part of the public output contract
  Options: A: keep contract version 3; state the fallback (summary from the worker's output, else the worker result's own summary, else a fixed host sentence; empty promise_changes and proposed_documents) and that the run result's worker field, not these fields, tells absent claims from empty ones; claims come from the last worker launch's final result only (matches the code); B: contract version 4 with nullable summary, promise_changes and proposed_documents when no valid worker answer exists (changes the output shape consumers rely on, plus code and tests)
  Recommendation: A

Escalation 4:
- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-95e60a5416905b09927d7f561874ab7f (Adoption, medium): after a scaffold, the entry says the survey runs again in a fresh workspace 'with the answers that revise it', but answers must name decisions of an admitted earlier run (req.adoption.answers-first) and Execution admits inputs only from the same workspace (req.execution.inputs-same-workspace), so the first workspace's survey cannot be admitted there. The fresh_workspace_required refusal's options also say 'with the same answers'.
  Not handled here (decision): the Issue is decision-needed; the recovery procedure is a promise of Adoption, and option C would change Execution, outside this task
  Options: A: specify the procedure within the existing contracts: in the fresh workspace run the survey anew carrying the revision in --goal, then answer that run's own decision points with --answers and --input naming it; update the entry, req.adoption.survey-after-scaffold and the refusal's options, and add a scenario; B: let --answers be used without an admitted run when they come from another workspace's survey (weakens req.adoption.answers-first, a provenance promise); C: let Execution admit a run of another workspace as --input (changes req.execution.inputs-same-workspace of module.execution)
  Recommendation: A

Escalation 5:
- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-cb5c4b8d498c5ef2b69b9e56d1c3328d (Specification, medium): req.specification.created-documents says a created document is empty and the Operation writes nothing else into it, while the entry and scenario.specification.new-document say its one line links to the entry (../module.md). The code (operation.py create_documents) writes a heading '# <title from the file name>' and 'Part of the Spec of [<Module title>](<relative link to the entry>).', and metadata with id, owner, role and empty defines and relations. No structural check needs that content.
  Not handled here (decision): the Issue is decision-needed; it chooses between competing observable promises
  Options: A: the host writes a minimal stub, a title heading named after the file and one line linking to the entry, with its metadata; align requirement, entry, contract and scenario (matches the code and code_to_spec's stubs); B: the host creates a truly empty reading file and the second worker writes the heading and link (code and test change)
  Recommendation: A

Escalation 6:
- **task-session** task session (task r3-adoption-specification): `decision_needed_issue`
  I-d192d63e6e415e3ba929b2ca8fbe9076 (Specification, medium): contract.specification.spec-change lists a changed project glossary among changed_documents but defines affected_modules only by Spec contexts that contain a changed document; SpecContext.paths holds only documents and glossary terms are carried separately, so a glossary-only change yields no affected Module.
  Not handled here (decision): the Issue is decision-needed; it fixes what affected_modules promises
  Options: A: affected_modules also lists every Module whose Spec context, before or after the change, carries a glossary entry the change added, changed or removed, and the owner of each such entry before or after (the Spec context's definition already includes the glossary entries of its terms); implement and test; B: add only the owners of the changed entries; C: exclude glossary effects and state so
  Recommendation: A

It carries escalation(s) 1, 2, 3, 4, 5, 6.

## Answer to report(s) 1 of the task session, 2026-10-13T11:36:08Z

Escalations 1-6 (main agent), each your recommendation A: 1 state Scaffold's existing-folder rule in req.adoption.proposal-checked. 2 metadata absent at the base names nothing; specs_unloadable covers existing but unreadable metadata. 3 keep contract v3, state the fallback and how the run result's worker field tells absent claims from empty ones. 4 in the fresh workspace run the survey anew with the revision in --goal, then answer that run's own decision points; update entry, requirement, refusal options, add a scenario. 5 the host writes a minimal stub (title heading + one link line + metadata); align requirement, entry, contract, scenario. 6 affected_modules also lists Modules whose Spec context carries a changed glossary entry, and each entry's owner before or after.

## Task session decisions, 2026-10-13

Escalations 1 to 6 were carried out as answered (option A each).

- I-9218b694 (preferred-fix): the scaffold host now creates each child folder with an exclusive
  `mkdir` before the file transaction; an existing one is `blocked`/`stale_proposal`, and only the
  folders this attempt created are removed. Chosen over a check inside Spec core's transaction,
  which is shared code of another Module. Regression test added.
- I-b391ca33 (preferred-fix): `narrowed_entries` takes a parent directory entry only when the
  child's directory entry does not skip the folders between them (same exclusion rule as files).
- I-f3bc1536 (preferred-fix): `parent_reading` finds Parts with Spec core's `sections()`, so
  anchored headings count and fenced headings do not.
- I-9a820811 and I-015516ae (preferred-fix): Scaffold's rollback statements and three scenarios now
  carry the "every file restored" premise; handled cancellation and a lost run are told apart.
- I-7be0f7e1 (preferred-fix): Scaffold includes `document.execution.runner` and relies on
  `req.execution.one-result`.
- I-b09819ab (preferred-fix): code_to_spec notes its stubs before writing them and tidies in a
  `finally` that also covers the preparation; regression test fails on the old code.
- I-edbe2823 (suggestion): applied in part. The exact test-editing mechanics moved to a new owned
  implementation document `specs/concorde/method/adoption/test-links.md`; the entry keeps a short
  account. The step tables stay in the entry, since every worker-backed Method Module keeps its
  step tables there and moving Adoption's alone would make it the odd one out.
- I-fa584adc: already fixed before this task (commit ec19285e2 added
  `document.method.workers` to Adoption's includes). Left in `resolves`.
- I-83934ba4 (preferred-fix): new req.specification.observed-baseline states the run-wide
  comparison as the code does it (union of every launch's audits plus the host's writes; affected
  Modules against the step-1 baseline).
- Follow-on outside the task's Modules (small, mechanical, from the answer to escalation 4 and 5):
  `specs/concorde/method/brownfield.md` (module.method) now describes the fresh-workspace
  revision without carrying answers across workspaces, and `prompts/workers/specify.md` says
  created documents are stubs. module.method is also in r3-reviews; a merge conflict there is
  possible but small.
- I mistakenly ran the escalation script twice, so escalations 7 to 12 duplicate 1 to 6.

## Report 2 to the main agent (Review流程), 2026-10-13T12:13:57Z

r3-adoption-specification delivered: delivery commit 125f48e88 (run r-20261013T120258-delivery-699703f1). task-validation r-20261013T115151-task_validation-ea49f524 ready with no blocking finding; full suite 1478 passed, 5 skipped; build --check and spec-validation clean.

All 23 Issues in resolves are handled:
- Escalations 1-6 carried out as answered (A): I-1b341f43 (folder rule in req.adoption.proposal-checked + survey test), I-4c3ae7f8 (absent base metadata names nothing; specs_unloadable narrowed), I-95e60a54 (fresh-workspace revision: survey anew with --goal, then answer its own decision points; new scenario.adoption.survey-revised-elsewhere + test; refusal options updated), I-90948979 (claims fallback stated in the contract, v3 kept), I-cb5c4b8d (created documents are minimal stubs), I-d192d63e (affected_modules counts changed glossary entries: code + new scenario.specification.glossary-change + test).
- Code fixes (preferred-fix): I-9218b694 scaffold creates child folders exclusively, a folder appearing after the recheck is stale_proposal; I-b391ca33 narrowing keeps an explicitly bound directory the child's rule skips; I-f3bc1536 Parts found with Spec core's sections() (anchored headings, fences); I-b09819ab stubs noted before writing and tidied after a failed preparation. Each has a regression test; the stub and glossary tests fail on the old code.
- Spec fixes: I-9a820811 + I-015516ae (rollback qualified by successful restore; handled cancellation vs lost run), I-7be0f7e1 (Scaffold includes document.execution.runner), I-9b2b52a4, I-efb88044, I-24f1fe8f (+ test asserts both repair rounds), I-83934ba4 (new req.specification.observed-baseline), I-22ad56b7, I-3c44d95f, I-5aeaff4f, I-735300d5.
- I-edbe2823 (suggestion) applied in part: the test-editing mechanics moved to a new owned document specs/concorde/method/adoption/test-links.md; the step tables stay in the entry because every worker-backed Method Module keeps them there. Close as not-actionable for the step-table part if you prefer it open.
- I-fa584adc no longer holds: commit ec19285e2 already added document.method.workers to Adoption's includes.

Decisions taken outside the task's Modules (small follow-ons of escalations 4 and 5): specs/concorde/method/brownfield.md (module.method) now describes the fresh-workspace revision without carrying answers across workspaces, and prompts/workers/specify.md says created documents are stubs. module.method is also in r3-reviews, so that file may conflict at merge (small).

Nothing open. Escalations 7-12 are accidental duplicates of 1-6 (noted in the decision log).

## Closed: merged, 2026-10-13T14:45:01Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 125f48e88420c04d3cc50e9d7cd83cc45f65432b into main and closed it as merged. Nobody answers a report after that.
