# Decision log: r3-method-work

Goal: Fix the remaining open Issues of Implementation, Understanding, General work, Validation and Delivery (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (28, listed in `resolves`; 8 of them decision-needed), all medium or
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

## Escalated to the main agent, 2026-10-13T11:35:03Z

- **task-session** task session (task r3-method-work): `obsolete_marker_clearing`
  I-384dfb31058e52a1adb6add139ce13fd (Delivery) and I-6c2794f49dbc5d04a4c95e3769847d2b (Implementation): Delivery's module.md says the delivery commit 'contains the cleared markers' and, when every step was committed, 'only any cleared markers'; Implementation's module.md (uses-spec) says 'Spec core also loads the realizations whose markers step 9 clears' (implement has 8 steps). These are leftovers of the pending realization entries and Delivery's pending-confirmation step, which the developer dropped on 2026-09-30 (realizations bind only files that exist; delivery has no pending-confirmation step). No code clears any marker (grep of src/concorde/method/delivery and implementation finds none); the delivery contract already says a delivery with everything committed changes nothing.
  Not handled here (decision): Both Issues are decision-needed: the panel could not tell whether marker clearing is obsolete or intended, and removing it changes the Modules' stated promise.
  Options: Remove both references (the entry's commit content and the Implementation collaboration sentence); the delivery commit contains every uncommitted change, nothing when every step was committed. Matches the developer's 2026-09-30 decision and the code; changes no behaviour.; Define markers, their owner and the clearing step canonically (would reintroduce the pending state the developer removed).
  Recommendation: Remove both references: settled by the developer's 2026-09-30 decision to drop pending entries; no behaviour or promise users rely on changes.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-method-work)",
  "code": "obsolete_marker_clearing",
  "detail": "I-384dfb31058e52a1adb6add139ce13fd (Delivery) and I-6c2794f49dbc5d04a4c95e3769847d2b (Implementation): Delivery's module.md says the delivery commit 'contains the cleared markers' and, when every step was committed, 'only any cleared markers'; Implementation's module.md (uses-spec) says 'Spec core also loads the realizations whose markers step 9 clears' (implement has 8 steps). These are leftovers of the pending realization entries and Delivery's pending-confirmation step, which the developer dropped on 2026-09-30 (realizations bind only files that exist; delivery has no pending-confirmation step). No code clears any marker (grep of src/concorde/method/delivery and implementation finds none); the delivery contract already says a delivery with everything committed changes nothing.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Both Issues are decision-needed: the panel could not tell whether marker clearing is obsolete or intended, and removing it changes the Modules' stated promise."
  },
  "options": [
    "Remove both references (the entry's commit content and the Implementation collaboration sentence); the delivery commit contains every uncommitted change, nothing when every step was committed. Matches the developer's 2026-09-30 decision and the code; changes no behaviour.",
    "Define markers, their owner and the clearing step canonically (would reintroduce the pending state the developer removed)."
  ],
  "recommendation": "Remove both references: settled by the developer's 2026-09-30 decision to drop pending entries; no behaviour or promise users rely on changes.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:03Z

- **task-session** task session (task r3-method-work): `check_results_lost_with_trace`
  I-4ffb920155935ccba050ad15a6cb3a5e and I-6c19e8432809559eb90271a37b1ae512 (Validation, same problem): when a call of Check execution fails after some checks finished, Validation reads those checks' results back from their trace nodes (command.py _finished). Check execution permits a refused trace.json write ('never changes the check or the call') and returns no results on a failed call; its CheckError only names the refused writes in trace_failures. So a finished check whose final trace write was refused has no recoverable result. The readiness is not wrong: the failed call already adds a blocking 'check' finding for its Modules, with Check execution's link (which carries trace_failures) as cause, so the workspace is never ready in this case.
  Not handled here (decision): Decision-needed: either Validation narrows its failure promise or Check execution (module.checks, owned by task r3-execution) changes its error contract to carry completed results.
  Options: A (within Validation): narrow the promise: the readiness lists the results of the finished checks whose trace node records their end; a finished check whose trace write was refused has no result there, and the blocking finding's cause names the refused write. Add a scenario. Spec only; code already behaves so.; B (Check execution + Validation): CheckError carries the completed check results independently of the trace; Validation takes them from the error. Changes module.checks' contract and code, outside this task.
  Recommendation: A: the readiness is blocked anyway, so no readiness decision depends on the lost result; it narrows only an edge-case failure promise, which no user relies on, and needs no change outside the task.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-method-work)",
  "code": "check_results_lost_with_trace",
  "detail": "I-4ffb920155935ccba050ad15a6cb3a5e and I-6c19e8432809559eb90271a37b1ae512 (Validation, same problem): when a call of Check execution fails after some checks finished, Validation reads those checks' results back from their trace nodes (command.py _finished). Check execution permits a refused trace.json write ('never changes the check or the call') and returns no results on a failed call; its CheckError only names the refused writes in trace_failures. So a finished check whose final trace write was refused has no recoverable result. The readiness is not wrong: the failed call already adds a blocking 'check' finding for its Modules, with Check execution's link (which carries trace_failures) as cause, so the workspace is never ready in this case.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Decision-needed: either Validation narrows its failure promise or Check execution (module.checks, owned by task r3-execution) changes its error contract to carry completed results."
  },
  "options": [
    "A (within Validation): narrow the promise: the readiness lists the results of the finished checks whose trace node records their end; a finished check whose trace write was refused has no result there, and the blocking finding's cause names the refused write. Add a scenario. Spec only; code already behaves so.",
    "B (Check execution + Validation): CheckError carries the completed check results independently of the trace; Validation takes them from the error. Changes module.checks' contract and code, outside this task."
  ],
  "recommendation": "A: the readiness is blocked anyway, so no readiness decision depends on the lost result; it narrows only an edge-case failure promise, which no user relies on, and needs no change outside the task.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:03Z

- **task-session** task session (task r3-method-work): `failed_worker_change_evidence`
  I-5b1c38ac5a8b52c08e836ad06eddf090 (General work): req.general-work.change-observed says the Operation reports the change from Git trees recorded before the worker launches and after it ends, unconditionally; the flow stops at step 3 when the worker does not end ok, before step 4 records the after-tree, and the code does the same (record_after is skipped). The before-tree is already kept as 'tree-before' evidence of every run, and the worker harness's write audit in the run record names the paths the worker changed.
  Not handled here (decision): Decision-needed: either the promise is narrowed to the worker's ok ending or the Operation gains observation on failure, which changes its flow and failure evidence.
  Options: A: qualify the requirement to a worker that ends ok; say that a blocked or failed run keeps the before-tree as evidence (so the caller can diff the worktree against it) and the worker's write audit, but no diff or earlier content. Spec only; matches the code.; B: observe the change whatever the worker's ending (step 4 as a finalization), keep diff and earlier content for a failed run, with the worker's error taking precedence over change_unobservable. Code + Spec change.
  Recommendation: A: a failed general run is not reviewed, so the diff and earlier content only serve the reviewer; the before-tree evidence already lets the task session see the partial change. Narrows a promise the code never kept; no user relies on it.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-method-work)",
  "code": "failed_worker_change_evidence",
  "detail": "I-5b1c38ac5a8b52c08e836ad06eddf090 (General work): req.general-work.change-observed says the Operation reports the change from Git trees recorded before the worker launches and after it ends, unconditionally; the flow stops at step 3 when the worker does not end ok, before step 4 records the after-tree, and the code does the same (record_after is skipped). The before-tree is already kept as 'tree-before' evidence of every run, and the worker harness's write audit in the run record names the paths the worker changed.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Decision-needed: either the promise is narrowed to the worker's ok ending or the Operation gains observation on failure, which changes its flow and failure evidence."
  },
  "options": [
    "A: qualify the requirement to a worker that ends ok; say that a blocked or failed run keeps the before-tree as evidence (so the caller can diff the worktree against it) and the worker's write audit, but no diff or earlier content. Spec only; matches the code.",
    "B: observe the change whatever the worker's ending (step 4 as a finalization), keep diff and earlier content for a failed run, with the worker's error taking precedence over change_unobservable. Code + Spec change."
  ],
  "recommendation": "A: a failed general run is not reviewed, so the diff and earlier content only serve the reviewer; the before-tree evidence already lets the task session see the partial change. Narrows a promise the code never kept; no user relies on it.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:03Z

- **task-session** task session (task r3-method-work): `canonical_json_escaping`
  I-5d4fc8f1293b5f6ab1fbb15979810c0a (Validation): the input measurement says 'The canonical JSON has sorted keys, no insignificant whitespace and UTF-8', which leaves string escaping open (literal é vs \u00e9). The implementation (measurement.py canonical) is json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False): every character literal as UTF-8 except the quote, the backslash and U+0000-U+001F, escaped as \b \f \n \r \t or else \u00XX in lowercase hex; keys sorted by code point.
  Not handled here (decision): Decision-needed: fixing canonical bytes affects digest compatibility.
  Options: A: state the rule the implementation already follows (above), with an example of a non-ASCII path; no digest changes, so no compatibility consequence.; B: adopt RFC 8785 (JCS). Its string escaping is identical, but it sorts keys by UTF-16 code units, which differs from the code-point order only for keys with characters outside the BMP; would change code and could change such digests.
  Recommendation: A: it documents existing behaviour, changes no digest and no promise users rely on.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-method-work)",
  "code": "canonical_json_escaping",
  "detail": "I-5d4fc8f1293b5f6ab1fbb15979810c0a (Validation): the input measurement says 'The canonical JSON has sorted keys, no insignificant whitespace and UTF-8', which leaves string escaping open (literal é vs \\u00e9). The implementation (measurement.py canonical) is json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False): every character literal as UTF-8 except the quote, the backslash and U+0000-U+001F, escaped as \\b \\f \\n \\r \\t or else \\u00XX in lowercase hex; keys sorted by code point.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Decision-needed: fixing canonical bytes affects digest compatibility."
  },
  "options": [
    "A: state the rule the implementation already follows (above), with an example of a non-ASCII path; no digest changes, so no compatibility consequence.",
    "B: adopt RFC 8785 (JCS). Its string escaping is identical, but it sorts keys by UTF-16 code units, which differs from the code-point order only for keys with characters outside the BMP; would change code and could change such digests."
  ],
  "recommendation": "A: it documents existing behaviour, changes no digest and no promise users rely on.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:35:03Z

- **task-session** task session (task r3-method-work): `placeholder_signature_collision`
  I-a0f78e4439545e03b176d80509e2c648 (Validation): the measurement leaves out an untracked 'sandbox placeholder', an empty regular file with no write bit and a single link, and claims 'A file a task creates has a write bit, content or another link'. A task can create an empty read-only single-link file; it is then excluded (not measured, not an unbound path, not committed by Delivery). Provenance cannot be established after the fact: the signature is the one Claude Code's sandbox runtime itself uses. The rule applies only to untracked paths, so staging the file (git add) makes it measured.
  Not handled here (decision): Decision-needed: choose between an intentional exclusion and a provenance discriminator; it changes the measurement's promise.
  Options: A: keep the exclusion for every untracked file with that signature, whatever its origin; drop the claim that a task's file never matches; state the limitation and that a task includes such a file by staging it (git add) or giving it content or a write bit; add a scenario. Spec only.; B: require real sandbox provenance; no reliable discriminator exists in the filesystem, so it would need a record kept by the sandbox, outside Concorde's control.
  Recommendation: A: an empty read-only file is rare task content, the remedy is simple, and only the wording of the promise changes.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-method-work)",
  "code": "placeholder_signature_collision",
  "detail": "I-a0f78e4439545e03b176d80509e2c648 (Validation): the measurement leaves out an untracked 'sandbox placeholder', an empty regular file with no write bit and a single link, and claims 'A file a task creates has a write bit, content or another link'. A task can create an empty read-only single-link file; it is then excluded (not measured, not an unbound path, not committed by Delivery). Provenance cannot be established after the fact: the signature is the one Claude Code's sandbox runtime itself uses. The rule applies only to untracked paths, so staging the file (git add) makes it measured.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Decision-needed: choose between an intentional exclusion and a provenance discriminator; it changes the measurement's promise."
  },
  "options": [
    "A: keep the exclusion for every untracked file with that signature, whatever its origin; drop the claim that a task's file never matches; state the limitation and that a task includes such a file by staging it (git add) or giving it content or a write bit; add a scenario. Spec only.",
    "B: require real sandbox provenance; no reliable discriminator exists in the filesystem, so it would need a record kept by the sandbox, outside Concorde's control."
  ],
  "recommendation": "A: an empty read-only file is rare task content, the remedy is simple, and only the wording of the promise changes.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:35:28Z

r3-method-work: early report of the decision-needed Issues (8 in resolves), escalated together as #1-#5. Work on the other 20 Issues continues meanwhile.

#1 obsolete_marker_clearing — I-384dfb31 (Delivery) + I-6c2794f4 (Implementation). Recommend: remove both "cleared markers" references; leftovers of pending entries the developer dropped on 2026-09-30; no code clears markers; no behaviour or user-relied promise changes.
#2 check_results_lost_with_trace — I-4ffb9201 + I-6c19e843 (Validation, same problem). Recommend A: narrow Validation's failure promise (results of finished checks are those whose trace node records their end; the failed call's blocking finding and cause name the refused write). Readiness is blocked anyway. Option B changes module.checks' error contract (r3-execution's Module).
#3 failed_worker_change_evidence — I-5b1c38ac (General work). Recommend A: qualify req.general-work.change-observed to a worker that ends ok; failed/blocked runs keep the before-tree evidence and the write audit. Matches the code. Option B adds observation on failure (code change).
#4 canonical_json_escaping — I-5d4fc8f1 (Validation). Recommend A: state the escaping the code already uses (literal UTF-8, escape only quote, backslash, U+0000-U+001F); no digest changes. B (RFC 8785) could change digests for non-BMP keys.
#5 placeholder_signature_collision — I-a0f78e44 (Validation). Recommend A: keep the exclusion whatever the origin, drop the false claim, state the limitation and the remedy (git add, content or write bit), add a scenario. Wording only.

Not escalated: I-734716da (General work, decision-needed "admitted input to reviewer") no longer holds: req.general-work.review-material already lists "The material of every admitted input", scenario.general-work.review-inputs covers it and operation.py reviewer_instructions passes inputs_material. It stays in resolves.

None of the recommendations changes a promise users rely on or an earlier developer decision (#1 follows the 2026-09-30 decision).

It carries escalation(s) 1, 2, 3, 4, 5.

## Answer to report(s) 1 of the task session, 2026-10-13T11:35:49Z

Escalations 1-5 (main agent), each your recommendation: 1 remove both 'cleared markers' references (follows the developer's 2026-09-30 decision dropping pending entries). 2 A — narrow Validation's failure promise; the failed call's blocking finding and cause name the refused write. 3 A — qualify req.general-work.change-observed to a worker that ends ok. 4 A — state the escaping the code already uses. 5 A — keep the exclusion, drop the false claim, state the limitation and remedy, add a scenario. I-734716da: no longer holds, fine; the merge closes it.

## Task session decisions: Implementation (2026-10-13)

- I-15ad4a0c (preferred-fix): code_change takes the latest round that has a write audit (audits are cumulative), so a resume round that never launched keeps the earlier edits; chosen over recomputing from Git because the audit already spans every round. Scenario resume-not-launched, unit-tested on code_change.
- I-8959cf01 (preferred-fix): refused_deletions semantics now covers every host refusal under Workers' rules (outside worktree, outside rw, a non-file entry such as a directory); the code already passed all of them; the evidence label no longer says "outside the writable paths". Deletion scenario extended with a directory.
- I-fd57ff99 (preferred-fix): empty checks list = no check ran in the work stage (none, readiness-only, or selective without verifying test) or the run stopped earlier; the evidence note now says "no configured check ran". New scenario no-check-runs.
- I-90000ed1 (preferred-fix): step 8 composes the code change only from a valid worker result (what the code did); without one the run has no output, its run record keeps the audits. New scenario no-result.
- I-c8c58270 (preferred-fix): req.implementation.worker-status qualified by host-failure precedence deferred to Workers' rounds table and proposed deletions; status cases list deletion_failed. New scenario blocked-with-violation.
- I-6c2794f4: marker-clearing sentence removed (main agent's answer to escalation #1).
- I-2a727a1e: no longer holds (Implementation already uses module.method and includes document.method.workers since ec19285e2); added the missing link of "mapping of worker and audit outcomes" to workers.md#errors-of-the-worker-sequence.

## Task session decisions: Understanding (2026-10-13)

- I-113301bd (preferred-fix): a document basis with `#anchor` resolves only when the document has that anchor: a readable anchor (Spec core's reading anchors: `<a id>`, requirement/scenario identities) or a heading anchor (explicit `{#…}` or the GitHub-style slug of the heading text, since Specs link headings that way, e.g. workers.md#errors-of-the-worker-sequence). Document-only bases still resolve. Requirement, contract semantics and scenario state it; regression cases with a valid heading anchor, no anchor and a nonexistent anchor.
- I-28ea306c (suggestion, applied): req.understanding.consistent, plan-review-answers and plan-review-responses now put the condition first; the before-launch timing kept.
- I-60427fc0: no longer holds: module.md.json includes document.method.workers (and uses module.method) since earlier rounds.

## Task session decisions: General work (2026-10-13)

- I-a9e2845c (preferred-fix): General work gives both workers its own rule for a promise the Spec does not state (worker: say so in `answer`, `blocked` when it cannot work without it; reviewer: judge as the files are, name the gap in `summary`) in place of the task type's rule, which for code-to-spec assigns that type's job and for review-code demands a `spec-gap` finding the reviewer schema forbids. Grant, glossary terms and boundary rules unchanged. Implemented as an optional `unstated` keyword of Method's `run_worker`/`compose` (src/concorde/method/workers.py, module.method): a small mechanical follow-on outside the task's Modules, default behaviour unchanged for every other Operation; Method's workers.md left as is (its step 2 still describes the rule's intent: never infer, report). New req.general-work.instruction-is-the-job and scenario type-sets-boundary-only, tested for code-to-spec and review-code.
- I-5b1c38ac: answer A (main agent): req.general-work.change-observed qualified to a worker that ends ok with a clean audit; a non-ok worker keeps `tree-before` evidence and the run record's write audits; worker-blocked scenario and test extended.
- I-a8359661 (preferred-fix): req.general-work.independent-review also requires the after-tree; change_unobservable stops before review; new scenario after-unobservable, tested by making the second tree recording fail.
- I-c00dc02c (suggestion, applied): "General work adds no validation of its own to a round"; Method's glossary-ownership validation still runs and fails the run.
- I-734716da, I-91f6b50d: no longer hold (review-material requirement already lists admitted inputs as a vertical list; scenario review-inputs; reviewer_instructions passes inputs_material).

## Task session decisions: Validation (2026-10-13)

- I-4f979733 (preferred-fix): chose one schema for both representations over a second contract: `workflow` is no longer required (contract version 10 -> 11, READINESS_SCHEMA in step); semantics says task-validation's output always carries it and readiness.json never does; the test validates the saved readiness against the schema.
- I-d95b87f7 (preferred-fix): req.validation.workspace restated as one invariant on where every structural validation and configured check a run performs happens; whether each runs stays with the flow.
- I-5d4fc8f1 (answer A): contract states the canonical JSON rules the code (json.dumps sort_keys, compact separators, ensure_ascii=False) already applies, with a `café.txt` example, its bytes and its input digest sha256:4add383e…ef84, computed with measurement.canonical; no digest changes.
- I-a0f78e44 (answer A): contract and entry say every untracked empty read-only single-link file is left out whatever its origin, and how a task makes it count (stage it, give it content or a write bit); new scenario placeholder-signature with a test.
- I-4ffb9201, I-6c19e843 (answer A): entry, contract semantics and new scenario check-trace-refused state that a finished check whose final trace write was refused has no result in the readiness while the failed call still blocks; test refuses the end write of the first check and fails the second with a CheckError. Found that an OSError ending the call carries no trace failures at all: already tracked by I-16ce84493550517d812608c43e8b81e6 (module.checks, task r3-execution), so the Spec says the cause names "the refused writes that Check execution's error carries".

## Task session decisions: Delivery (2026-10-13)

- I-384dfb31: "cleared markers" removed from the entry (answer to escalation #1); a fully committed workspace's delivery commit changes nothing, as the contract already said.
- I-31ff3dc0 (preferred-fix): req.delivery.atomic now promises an attempted restoration of each recorded part with every failed part named (entries first; the others not attempted when the entries cannot be read back); req.delivery.failed-paths-named is conditioned on a successful re-measurement and otherwise says so with the measurement's cause. New scenario restore-failed (declared on the existing undo test) and a unit test for the unmeasurable case.
- I-34f093e4 (preferred-fix): the commit contract, the overview, the commit-as-record paragraph, the step table and the diagram label now say the rejected commit is taken off only when safe, otherwise it stays with the error saying why (req.delivery.rejected-removed/-reported).
- I-8eb18029 (preferred-fix): scenario.delivery.deliver gets "AND a repository with no hook that changes a commit message"; new scenario hook-trailer declared on the existing trailer test, which now also checks the output commit.
- I-b977d0b4 (suggestion, applied): new implementation document specs/concorde/method/delivery/git.md (document.delivery.git, owned by module.delivery, registry refreshed) holds the exact record/restore commands and the commit-identification reasoning; the entry keeps rationale, guards and observable outcomes and links there.
- I-222aae59: no longer holds since 370312a08 (the gate scans every bound test file's verification declarations; test test_a_scenario_of_a_module_without_files_needs_a_test verifies scenario.delivery.unrealized-scenarios).

## Report 2 to the main agent (Review流程), 2026-10-13T12:15:59Z

r3-method-work delivered: delivery commit be969a4cde0ea50b2df5c4202399ad7afaba58a3 on concorde/r3-method-work (sequence 1). task-validation ready with all 28 checks passed; full suite 1481 passed, 5 skipped. Resolves all 28 Issues in resolves; your answers to escalations #1-#5 are carried out (#1 remove markers; #2-#5 option A).

Fixed by tier:
- Implementation: I-15ad4a0c code_change takes the latest audited round, so a resume round that never launched keeps the earlier edits. I-8959cf01 refused_deletions covers every host refusal, a directory included. I-fd57ff99 an empty checks list means no check ran in the work stage or the run stopped; the evidence now says "no configured check ran". I-90000ed1 a code change is composed only from a valid worker result; otherwise no output. I-c8c58270 worker-status is overridden by host failures (Workers' rounds table, deletion_failed). I-6c2794f4 marker sentence removed. New scenarios blocked-with-violation, resume-not-launched, no-result and no-check-runs, all tested.
- Understanding: I-113301bd a basis "doc#anchor" must name an anchor the document has (readable anchors or heading anchors), with a regression test. I-28ea306c failure requirements now state the condition first.
- General work: I-a9e2845c both workers get General work's own rule for unstated promises instead of the task type's job-specific rule (code-to-spec job, review-code spec-gap finding). This needs a new optional `unstated` keyword in Method's run_worker/compose (src/concorde/method/workers.py, module.method): a small mechanical follow-on outside the task's Modules. Default behaviour is unchanged; Method's workers.md is untouched. I-5b1c38ac (A), I-a8359661 the review needs the after-tree (change_unobservable scenario), I-c00dc02c wording.
- Validation: I-4f979733 `workflow` is optional in the readiness schema (contract v11), so one schema covers both the output and readiness.json. I-d95b87f7 req.validation.workspace is now a where-invariant. I-5d4fc8f1 (A) states the existing escaping rule, with an example and its digest. I-a0f78e44 (A), with a placeholder-signature scenario. I-4ffb9201/I-6c19e843 (A), with a check-trace-refused scenario.
- Delivery: I-384dfb31 markers removed. I-31ff3dc0 atomic: attempted restorations, failed parts named, unmeasurable worktree said so. I-34f093e4 the contract defers removal to the guarded requirement. I-8eb18029 the normal scenario excludes message hooks, plus a hook-trailer scenario. I-b977d0b4 (suggestion, applied) the exact Git procedures move to a new implementation document, specs/concorde/method/delivery/git.md (document.delivery.git, registry refreshed).

No longer hold (stay in resolves): I-2a727a1e and I-60427fc0 (Method's workers.md was already included; I added one link), I-734716da and I-91f6b50d (already fixed in General work), I-222aae59 (the gate already reads verification declarations; tested).

Observed, not fixed here: an OSError ending a Check execution call carries no refused trace writes. It is already tracked as I-16ce84493550517d812608c43e8b81e6 (module.checks, task r3-execution). Validation's Spec says the cause names "the refused writes that Check execution's error carries".

Open: nothing. Every decision is in the decision log.

## Closed: merged, 2026-10-13T14:45:28Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit be969a4cde0ea50b2df5c4202399ad7afaba58a3 into main and closed it as merged. Nobody answers a report after that.
