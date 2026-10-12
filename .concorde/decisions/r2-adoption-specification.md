# Decision log: r2-adoption-specification

Goal: Fix the critical, high and obvious-fix open Issues of Adoption, Scaffold and Specification found by the complete project_review, the critical first (I-eee13aec)

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 20 Issues in its `resolves`,
owned by its Modules, found by the complete project_review
r-20261008T063808-project_review-9851e69f (unbound; reports under
`.concorde/unbound/r-20261008T063808-project_review-9851e69f/` of the primary worktree) or
earlier. Read each with `concorde issues show`. Other open Issues of these Modules are out of
scope: do not fix them, even when nearby, unless a fix in scope needs it.

By tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest
  meanwhile. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- Work critical first, then high.
- An Issue that does not hold, is a duplicate or is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix needing a change outside the task's Modules: escalate, unless it is a small mechanical
  follow-on (a link, a fixture, a registry refresh).

Eleven other round-2 tasks run in parallel, each on other Modules (r2-*). If a merge conflict
comes back, the main agent asks you to merge the primary branch in. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-08T13:38:39Z

- **task-session** task session (task r2-adoption-specification): `scaffold_parent_prose_policy`
  I-d53332b4 (high, decision-needed, module.scaffold): Scaffold's Spec promises it 'leaves the existing prose unchanged' in the parent's entry (module.md 'What it writes', req.scaffold.contained, scenario.scaffold.no-parts-section), yet after it adds children, contains and moves realization entries, the parent's earlier prose can contradict the new structure. Concretely, Spec core's initialization writes into the root's Parts section the paragraph 'The project's parts and their collaborations are not specified yet. This Module contains, uses and includes nothing, ...', which is false once the scaffold adds children. The code already handles exactly this case against the Spec: src/concorde/method/scaffold/command.py:336 replaces that exact initialization paragraph (INIT_PARTS) with a fixed sentence ('The parts below were proposed by a survey of the code; their collaborations are not specified yet, ...'), globally, before locating Parts. I-46aa193f (low, obvious-fix, same Module) asks to remove that replacement to honour the preservation promise; doing so would make I-d53332b4 worse for every freshly initialized root (the normal brownfield path). So the two Issues hinge on one policy decision, and I hold I-46aa193f until it is answered.
  Not handled here (decision): The choice changes Scaffold's promised output policy (what it writes into the parent's entry), a promise change the task brief reserves; the two Issues' suggested repairs pull in opposite directions.
  Options: A: Spec the existing behaviour as the one exception: when the parent's Parts section holds exactly the paragraph Spec core's initialization writes, the scaffold replaces that paragraph with a fixed sentence; all other prose stays unchanged. Fix the code so the replacement only applies inside Parts (not globally). Close I-46aa193f as resolved by the Spec change; I-d53332b4 resolved for the initialized-root path, other authored prose left to the later code_to_spec/specify of the parent.; B: A plus a deterministic notice: for a parent whose prose is not the initialization text, append after the new child paragraphs a fixed sentence saying the parts and bindings listed here supersede earlier descriptions in the entry, so the parent explanation is flagged for reconciliation.; C: Keep the preservation promise strictly (remove the INIT_PARTS replacement per I-46aa193f) and only document that the parent prose may be obsolete until a later specify; accepts a contradictory root on the normal path.
  Recommendation: A. It matches the code already shipped, removes the contradiction on the normal brownfield path, keeps human-authored prose untouched, and needs no new contract field; the global replace becomes Parts-scoped.

```json
{
  "level": "task-session",
  "actor": "task session (task r2-adoption-specification)",
  "code": "scaffold_parent_prose_policy",
  "detail": "I-d53332b4 (high, decision-needed, module.scaffold): Scaffold's Spec promises it 'leaves the existing prose unchanged' in the parent's entry (module.md 'What it writes', req.scaffold.contained, scenario.scaffold.no-parts-section), yet after it adds children, contains and moves realization entries, the parent's earlier prose can contradict the new structure. Concretely, Spec core's initialization writes into the root's Parts section the paragraph 'The project's parts and their collaborations are not specified yet. This Module contains, uses and includes nothing, ...', which is false once the scaffold adds children. The code already handles exactly this case against the Spec: src/concorde/method/scaffold/command.py:336 replaces that exact initialization paragraph (INIT_PARTS) with a fixed sentence ('The parts below were proposed by a survey of the code; their collaborations are not specified yet, ...'), globally, before locating Parts. I-46aa193f (low, obvious-fix, same Module) asks to remove that replacement to honour the preservation promise; doing so would make I-d53332b4 worse for every freshly initialized root (the normal brownfield path). So the two Issues hinge on one policy decision, and I hold I-46aa193f until it is answered.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The choice changes Scaffold's promised output policy (what it writes into the parent's entry), a promise change the task brief reserves; the two Issues' suggested repairs pull in opposite directions."
  },
  "options": [
    "A: Spec the existing behaviour as the one exception: when the parent's Parts section holds exactly the paragraph Spec core's initialization writes, the scaffold replaces that paragraph with a fixed sentence; all other prose stays unchanged. Fix the code so the replacement only applies inside Parts (not globally). Close I-46aa193f as resolved by the Spec change; I-d53332b4 resolved for the initialized-root path, other authored prose left to the later code_to_spec/specify of the parent.",
    "B: A plus a deterministic notice: for a parent whose prose is not the initialization text, append after the new child paragraphs a fixed sentence saying the parts and bindings listed here supersede earlier descriptions in the entry, so the parent explanation is flagged for reconciliation.",
    "C: Keep the preservation promise strictly (remove the INIT_PARTS replacement per I-46aa193f) and only document that the parent prose may be obsolete until a later specify; accepts a contradictory root on the normal path."
  ],
  "recommendation": "A. It matches the code already shipped, removes the contradiction on the normal brownfield path, keeps human-authored prose untouched, and needs no new contract field; the global replace becomes Parts-scoped.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T13:38:47Z

Early escalation (report 1 of the task; work on the other 19 Issues continues meanwhile). The only decision-needed Issue, I-d53332b4 (high, module.scaffold), is escalation 1: how Scaffold treats parent prose its new structure makes obsolete. It is coupled with I-46aa193f (low, obvious-fix), which asks to remove the code's replacement of the initialization Parts paragraph; I hold I-46aa193f until this is answered. Options A/B/C are in the chain; I recommend A (spec the replacement of exactly the initialization paragraph, scoped to Parts; all other prose unchanged).

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-08T13:39:02Z

Escalation 1 scaffold_parent_prose_policy (main agent): A — specify the existing behaviour as the one exception: when the parent's Parts section holds exactly the paragraph Spec core's initialization writes, the scaffold replaces it with a fixed sentence; all other prose stays unchanged; make the replacement Parts-scoped, not global. Resolve I-46aa193f by that Spec change and I-d53332b4 for the initialized-root path (other authored prose is the parent's later code_to_spec/specify work; say so in the Spec).

## Task session: Specification fixes (commit a386f1460)

- I-eee13aec (critical, preferred-fix): `document_refusal` now checks canonical paths with Spec core's
  `safe_path`, rejects a symbolic link (dangling or not) at any component of the reading and
  metadata paths via `checked_path`, and uses `lexists`. All files are written through Spec core's
  `apply_files` file transaction (digest-bound, symlink-refusing, restores on failure). Chosen over a
  bespoke `O_NOFOLLOW` writer because the transaction is the existing facility the Scaffold also uses.
- I-64c1d6cc (high, preferred-fix): every entry metadata is read and checked before any write; an
  unreadable one refuses the whole list (`document-refused`), the worker outcome is kept and steps
  6–9 run. A failed transaction gives `document-creation-failed` evidence, nothing created.
- I-840e3d46 (high, preferred-fix): identities allocated against existing and batch identities:
  stem, then folders below the entry joined by `-` (`document.a.details-rules`), then a number.
- I-917d1a35 (high, preferred-fix): round validation validates with Spec core's `registry_bytes`
  override set to the regenerated mirror. Finding: the code already dropped `.concorde/` findings
  from repair prompts (`spec_repair_prompt`), so the stale-mirror case did not reach workers today;
  the override is kept as the more precise fix and the Spec now states both.
- I-933d743f, I-b4620ee9 (obvious-fix): registry evidence carries `SpecError.describe()`; an
  after-change load failure emits `spec-context` evidence for every bound and baseline Module.
- I-f5c12e3e (high, preferred-fix): finding: Method already checks glossary ownership once more
  after each worker run whatever its status (method/workers.md step 9, scenario.method.glossary-after-run),
  and `violated()` stops creation on it. Fixed as a Spec change: Specification's entry and
  req.specification.own-documents now rely on that check instead of a round-only audit.
- I-89848d96 (high, preferred-fix): Specification now includes `document.method.workers` and its
  entry states that specify asks for no configured checks, so its round validation is the glossary
  check plus the baseline comparison only. No policy conflict found.

## Task session: Adoption fixes (commit f3a0331a3)

- I-cbd03579 (high, preferred-fix): `check_provenance` in records.py refuses with `invalid_answers`
  every answer whose identity no admitted survey/code_to_spec input lists, before any write or
  worker. Verified the brownfield workflow already passes the asking run as `--input` with
  `--answers` (workflows/step.py `asking_run`), so workflows are unaffected; two existing tests that
  passed answers without `--input` now pass the asking run.
- I-1fcc2faa (high, preferred-fix): `del verifies` (and, beyond the Issue, `global verifies`
  anywhere) is a foreign binding: the whole file is left untouched and reported. Chosen over
  flow analysis of whether a later re-binding restores the name: conservative and simple.
- I-5a6e206c (high, preferred-fix): a test whose innermost enclosing class body binds `verifies`
  is left undecorated and reported (only class scope matters for a method decorator); the file's
  other tests still link. Documented as an exception in the entry, requirement and new
  scenario.adoption.class-verifies.
- I-f7f70d7d: target uniqueness is now resolved before the already-declared shortcut.
- I-cf2b4a4d (high, preferred-fix): added `contract.adoption.survey-claims` and
  `contract.adoption.description-claims` (version 1) equal to the code's worker schemas, with a
  contract test; chosen over describing the payload in prose so tests pin it.
- I-13cce3bf, I-03922f86, I-78e765a8, I-b4869114 (obvious-fix): wording fixes in module.md,
  contracts.md error table and scenarios as the Issues suggested.

## Task session: Scaffold fixes (commit 8b08cd2f1)

- I-d53332b4 / I-46aa193f: option A as answered: replacement scoped to the Parts section;
  new req.scaffold.prose-kept and scenario.scaffold.initialized-parts; other obsolete prose left to
  a later code_to_spec/specify of the parent, said in the entry.
- I-5f9b5b20 (obvious-fix): verified in code that the runner's `Cancelled` is an `Exception`, so
  Spec core's `apply_files` restores on SIGINT/SIGTERM and the run ends failed/cancelled; the entry
  now says so and keeps the no-result account for unhandled kills only.

## Report 2 to the main agent (Review流程), 2026-10-08T14:16:56Z

r2-adoption-specification delivered: delivery commit efec75084 (run r-20261008T140600-delivery-f56e4a28; task-validation r-20261008T135503-task_validation-e2513880 ready, no blocking finding; full suite 1380 passed, 5 skipped; build --check and spec-validation clean).

All 20 Issues in the task's resolves are fixed (none found invalid or duplicate):
Specification (commit a386f1460):
- I-eee13aec (critical): proposals are refused when any component of the reading or metadata path is a symbolic link (dangling or not) or not canonical; all files are written through Spec core's apply_files file transaction (digest-bound, symlink-refusing, restores on failure). Chosen over a bespoke O_NOFOLLOW writer: it is the existing facility Scaffold uses.
- I-64c1d6cc: every proposal and entry metadata is checked and every content computed before any write; malformed metadata refuses the whole list (document-refused), worker outcome kept, steps 6-9 still run; a failed transaction gives document-creation-failed.
- I-840e3d46: identities unique against existing and batch: stem, then folders below the entry (document.a.details-rules), then a number.
- I-917d1a35: rounds validate against the in-memory reconciled registry (registry_bytes). Finding: the code already dropped .concorde/ findings from repair prompts, so workers were not actually asked to fix the mirror; the Spec now states both.
- I-f5c12e3e: finding: Method already re-checks glossary ownership after every worker run whatever its status, before creation; fixed as a Spec change relying on that check.
- I-89848d96: Specification now includes document.method.workers and states specify runs no configured checks (round validation = glossary check + baseline comparison). No policy conflict.
- I-933d743f, I-b4620ee9: registry refusal kept in full; spec-context evidence for every Module when the after-Specs do not load.
Adoption (commit f3a0331a3):
- I-cbd03579: answers whose identity no admitted survey/code_to_spec run asked fail invalid_answers before any write or worker. The brownfield workflow already passes the asking run as --input, so it is unaffected.
- I-1fcc2faa: del verifies (and also global verifies) counts as a foreign binding; file left untouched and reported (conservative choice over flow analysis).
- I-5a6e206c: a test whose class body binds verifies is left undecorated and reported; other tests in the file still link. New scenario.adoption.class-verifies.
- I-cf2b4a4d: new contracts contract.adoption.survey-claims and contract.adoption.description-claims (v1), pinned to the code's worker schemas by a test.
- I-f7f70d7d, I-13cce3bf, I-03922f86, I-78e765a8, I-b4869114: fixed as suggested.
Scaffold (commit 8b08cd2f1):
- I-d53332b4, I-46aa193f: option A as you answered: only the initialization paragraph, only inside Parts, is replaced; new req.scaffold.prose-kept and scenario.scaffold.initialized-parts; other obsolete parent prose left to a later code_to_spec/specify, as the Spec says.
- I-5f9b5b20: SIGINT/SIGTERM restores the transaction and ends failed/cancelled (verified: the runner's Cancelled is an Exception that apply_files handles); no result only for unhandled kills.

Follow-on outside my Modules: none. Open: nothing in scope. Pre-existing lint findings in tests/concorde/adoption (I001, S102, ISC004) left as they were.

## Closed: merged, 2026-10-12T14:28:40Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit efec75084ceeb494562f4930a52536ca2efe011e into main and closed it as merged. Nobody answers a report after that.
