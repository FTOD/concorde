# Decision log: plan-review

Goal: Add an optional plan_review Operation: a read-only reviewer worker (review-code grant, model set in workers.json, gpt-6.1-sol here) reviews a plan the task session wrote; the task session answers each finding and re-runs with --input until the verdict is accepted or escalates what it cannot settle

## Brief (main agent, 2026-09-30)

Developer's decisions this task carries out:

- Add a new Operation `plan_review`, optional: nothing requires it before `task-validation` or
  `delivery`; a task session runs it when it chooses or its brief asks for it.
- The plan is written by the **task session itself** (it may start from an `understand --plan`
  output, but the reviewed plan is the task session's own). `plan_review` reviews that plan
  against the goal, the bound Modules' Specs and the code.
- The reviewer is one worker, worker id `reviewer`, with a **read-only `review-code` grant**
  (reads Specs and code contents, writes nothing). No new task type, no Protocol change.
- The reviewer's model comes only from `.concorde/workers.json`; on this branch set
  `operations.plan_review.workers.reviewer.model` to `gpt-6.1-sol` (already in `enabled_models`
  and in the developer's model map). Never hard-code a model.
- The discussion is **several runs led by the task session**, not a loop inside the Operation:
  each round is one `plan_review` run; the task session answers every finding of the previous
  round (accepted, or rejected with its reason), revises the plan and runs again with
  `--input <previous plan_review run>`, so the reviewer sees the earlier findings and answers.
  It ends when the verdict is accepted; disagreements the task session cannot settle within its
  task are escalated to the main agent.

Main agent's decisions (ordinary scope):

- Provider: Understanding (`module.understanding`), which owns the plan; add `plan_review` to the
  Operation catalog in `module.operations` and fix its sentence "A plan is one answer `understand`
  gives, not a separate Operation" so it says the plan stays `understand`'s answer and its review
  is `plan_review`. Update the main-session guidance (`module.main-session`, `prompts/`) so main
  agents and task sessions know the Operation and when to use it.
- One task for Spec and implementation (instead of the two I first mentioned to the developer):
  both touch the same Modules in sequence.

Left to the task session: the output contract (findings shape, verdict values — follow
`code_review`/`spec_review` where it fits), how the plan is passed (e.g. `--plan <file>`) and where
the plan file lives, whether the Operation is bound-only or also unbound, the round/`--input`
admission rules, scenarios and tests. If a needed change falls outside the bound Modules (e.g.
Workers or Harness), escalate rather than widening silently.

## Task session decisions (2026-09-30)

Decisions taken without the developer, within what the brief left to the task session:

- **Bound only.** `plan_review` needs a workspace binding (`binding: required`): the plan is the
  task session's, reviewed against its workspace's goal, and an unbound run has no goal. The main
  agent keeps `understand --plan` for questions before a task exists.
- **How the plan is passed.** `--plan <file>`, a UTF-8 Markdown or text file, relative paths
  resolved against the worktree the run works on. The host reads it before the worker launches,
  refuses a missing, unreadable, non-UTF-8 or empty file (`plan_unreadable`, reason `input`), keeps
  an exact copy as `plan.md` in the run's trace node and records its digest, so the review is bound
  to the plan it examined whatever happens to the file later. The worker receives the plan in its
  brief (task context), never through its grant.
- **Where the plan lives.** Anywhere the task session chooses; the guidance suggests a file in the
  task worktree (writable by its Edit/Write tools) that it deletes before `task-validation`, since
  delivery commits every uncommitted change and the run keeps its own copy. A Git-ignored plan
  location would need the installer's ignore list (Distribution), outside this task's Modules, so it
  is not added; reported as a possible follow-up.
- **Answers are arguments, not a file.** `--accept <finding> "<how the revised plan settles it>"` and
  `--reject <finding> "<why>"`, repeatable, answer the previous review's findings. With a
  `plan_review` input every finding of it must be answered exactly once and no answer may name
  another id; without one no answer is allowed; more than one `plan_review` input is refused. All
  of these fail before the worker launches with `round_mismatch` (reason `input`), listing every
  problem. Other admitted inputs (such as the `understand` run the plan started from) are material
  for the reviewer.
- **Output contract** `contract.understanding.plan-review`, following `code_review`: the host adds
  `plan` (file, kept copy, digest), `iteration` (1, or the previous review's plus one), `previous`
  (its run id or null) and the `answers` as given; the reviewer supplies `summary`, `responses`
  (one per previous finding: `settled` or `maintained`, with a comment) and `findings` (`id`
  `F<n>`, `severity` blocking/advisory, `kind` goal/violation/spec-gap/code/scope/sequence,
  `module` bound Module or null, `basis` or null, `locations`, `description`, `suggestion`,
  `previous` = the maintained finding it continues or null). Verdict `accepted` exactly when no
  finding is blocking, else `changes_required` (Spec review's word `accepted`, since the goal names
  it). Host checks, failing the run with reason `capability`: `unresolved_basis` (a basis that does
  not resolve in the bound Modules' Spec context, or a `violation` without one) and
  `inconsistent_review` (responses not exactly one per previous finding, a maintained response not
  continued by exactly one finding, a `previous` naming no maintained finding, a `module` that is
  not bound).
- **Word choice.** Each run of the discussion is an *iteration*, not a *round*: "round" already means
  a worker round and "resume round" is a glossary term. No glossary entry is added: plan review and
  iteration are used in their common sense.
- **One realization.** The code lives in `src/concorde/understanding/plan_review.py` and the prompt
  in `prompts/workers/plan-review.md`; the existing realization, retitled "Understanding
  Operations", binds both, rather than a second realization overlapping `src/concorde/understanding/`.
- **No checks, no resume round, no diff.** The reviewer reads the current code through its
  `review-code` grant; the host runs no configured check, since a plan changes no code.
- **A settled disagreement.** A rejection that reports the main agent's or the developer's decision
  settles the finding for the reviewer unless the revised plan contradicts it; the guidance has the
  task session escalate a finding the reviewer maintains after it rejected it once and still holds
  its rejection, rather than iterate on it again.

### Corrections and further decisions (task session, 2026-09-30)

- The refusal code named `round_mismatch` above is `iteration_mismatch` in the Spec and code, for
  the same reason "iteration" replaced "round".
- No Understanding requirement states that `plan_review` is optional: that is a promise about other
  Modules (Validation, Delivery), which Understanding cannot make. It is stated in Understanding's
  and Operations' text and as the main-session requirement
  `req.main-session.task-session-plan-review` for the guidance.
- The basis resolver is duplicated in `plan_review.py` (about 25 lines) rather than imported from
  Code review's `operation.py`, so that Understanding takes no dependency on Code review.
- `plan_review` never runs unbound; the runner refuses it with `binding_required` (tested).
- Not changed, outside the task's Modules: the user documents `docs/README.md` and
  `docs/using-concorde.md` (bound by `module.concorde`) list the Operations without `plan_review`.
  Reported to the main agent as a follow-up, not escalated as a decision.
- Live smoke test on gpt-6.1-sol (pi), plan for a hypothetical `--focus` follow-up, bound to
  module.understanding: iteration 1 `r-20260930T083206-plan_review-d565aba2` ended `ok`,
  `changes_required`, one correct blocking `sequence` finding (the read-only `test` Operation
  cannot write the planned test); iteration 2 `r-20260930T083354-plan_review-cf876cd4` with
  `--input` and `--accept F1` ended `ok`, F1 `settled`, verdict `accepted`. The scratch plan file
  was deleted before validation.

## Closed: merged, 2026-09-30T08:42:26Z
