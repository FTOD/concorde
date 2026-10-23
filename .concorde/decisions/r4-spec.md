# Decision log: r4-spec

Goal: Fix the critical and high open Issues of Spec core, Spec MCP and Spec tooling found by the fourth project_review

## Task brief (main agent, 2026-10-17)

Round 4. The fourth project_review (r-20261013T165054-project_review-b4db00b2, unbound; reports
under `.concorde/unbound/r-20261013T165054-project_review-b4db00b2/` of the primary worktree) left
734 open Issues after rounds 1-3 had brought them to 4: most new findings are stricter standards
rather than new defects. The developer decided (2026-10-17): **each round fixes only critical and
high Issues**, medium and low wait until real use runs into them, and project_review is tuned so
its Issues stay actionable (task r4-review-tuning). This task resolves the critical and high Issues
of its Modules listed in `resolves`. Read each with `concorde issues show`. Other open Issues of
these Modules are out of scope: do not fix them unless a fix in scope needs it.

By tier: **decision-needed** — read them first and escalate them all together in one report,
early, each with what you found, the options and your recommendation, saying which options change
a promise users rely on or an earlier developer decision; continue with the rest meanwhile.
**preferred-fix** — fix as you judge best and report the choice. **obvious-fix** — fix. Critical
first. An Issue that no longer holds or is a duplicate: say so with evidence; it stays in
`resolves`. A fix needing a change outside the task's Modules: escalate unless it is a small
mechanical follow-on. Eight other round-4 tasks (r4-*) run in parallel on other Modules. Deliver
with `task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-17T04:34:59Z

- **task-session** task session (task r4-spec): `mcp_query_shape_decision`
  Issue I-582fabaa7d075d918acacb37d56038d4 (decision-needed, high, module.spec-mcp): the Spec MCP server promises 'returns what Spec core computes, unchanged' (module.md, req.spec-mcp.spec-core-answers, scenario.spec-mcp.queries says results 'equal' Spec core's records), yet its tools return projections. What I found in the code (src/concorde/spec/mcp/tools.py): `module` returns the registry record's fields (title, entry, owns as `documents`, contains, uses, includes, participates) plus `realizations` from repository.realizations(); it is not Spec core's `SpecRepository.module()` record (which has parent, files, references). `context` returns {module, context_identity, sources, terms} from spec_context().value and drops `bound` (bound-inclusion files with digests) and the other value fields (registration, documents, references, reading_entry, query_id/kind). Values are never altered, only selected. No caller in the repo depends on the shapes beyond the tests and the main agent's own use.
  Not handled here (decision): Choosing the public result shape of the MCP tools and whether to narrow the 'unchanged Spec core result' promise changes what Spec MCP promises its callers (main agent and agents of other projects), which is a change of a Module's promise and so not mine to decide.
  Options: A (recommended): keep the documented envelopes, add `bound` to the `context` result, reword the promise to 'every value is Spec core's, unchanged, presented in the documented envelope' and give each field's source in Spec core (module: registry record + realizations; context: spec_context().value fields + context_identity), and align scenario.spec-mcp.queries to field-wise equality. Additive for callers; narrows only the wording of 'unchanged'.; B: return Spec core's records whole (`context` = the full spec_context().value with context_identity added; `module` = Spec core's Module record). Changes the public result shapes callers see.; C: keep shapes as they are without `bound`, and narrow the complete-Spec-context promise of `context`, saying callers get bound files through `boundary`. Narrows a promise users may rely on.
  Recommendation: A: it fixes the contradiction with no breaking change; the only promise touched is the wording of 'unchanged', which becomes precise rather than weaker, and `bound` restores the complete Spec context.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-spec)",
  "code": "mcp_query_shape_decision",
  "detail": "Issue I-582fabaa7d075d918acacb37d56038d4 (decision-needed, high, module.spec-mcp): the Spec MCP server promises 'returns what Spec core computes, unchanged' (module.md, req.spec-mcp.spec-core-answers, scenario.spec-mcp.queries says results 'equal' Spec core's records), yet its tools return projections. What I found in the code (src/concorde/spec/mcp/tools.py): `module` returns the registry record's fields (title, entry, owns as `documents`, contains, uses, includes, participates) plus `realizations` from repository.realizations(); it is not Spec core's `SpecRepository.module()` record (which has parent, files, references). `context` returns {module, context_identity, sources, terms} from spec_context().value and drops `bound` (bound-inclusion files with digests) and the other value fields (registration, documents, references, reading_entry, query_id/kind). Values are never altered, only selected. No caller in the repo depends on the shapes beyond the tests and the main agent's own use.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing the public result shape of the MCP tools and whether to narrow the 'unchanged Spec core result' promise changes what Spec MCP promises its callers (main agent and agents of other projects), which is a change of a Module's promise and so not mine to decide."
  },
  "options": [
    "A (recommended): keep the documented envelopes, add `bound` to the `context` result, reword the promise to 'every value is Spec core's, unchanged, presented in the documented envelope' and give each field's source in Spec core (module: registry record + realizations; context: spec_context().value fields + context_identity), and align scenario.spec-mcp.queries to field-wise equality. Additive for callers; narrows only the wording of 'unchanged'.",
    "B: return Spec core's records whole (`context` = the full spec_context().value with context_identity added; `module` = Spec core's Module record). Changes the public result shapes callers see.",
    "C: keep shapes as they are without `bound`, and narrow the complete-Spec-context promise of `context`, saying callers get bound files through `boundary`. Narrows a promise users may rely on."
  ],
  "recommendation": "A: it fixes the contradiction with no breaking change; the only promise touched is the wording of 'unchanged', which becomes precise rather than weaker, and `bound` restores the complete Spec context.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-17T04:35:05Z

r4-spec early escalation: the one decision-needed Issue of this task, I-582fabaa (Spec MCP query result shapes vs the 'unchanged Spec core result' promise), needs a decision — escalation 1 gives the findings, options A/B/C and my recommendation A (keep envelopes, add `bound` to `context`, state per-field sources; additive, no breaking change). Option B changes the public result shapes; C narrows the complete-Spec-context promise. I am continuing meanwhile with the seven preferred-fix Issues (file impact closure x2, receipt symlink read, shared-write rw check, external cache, diagram language inclusion, MCP wire standards/tools/list schemas).

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-17T04:35:17Z

Escalation 1 mcp_query_shape_decision (main agent): A — keep the documented envelopes, add bound to context, reword the promise to every value is Spec core's, unchanged, in the documented envelope, naming each field's Spec core source, and align scenario.spec-mcp.queries to field-wise equality.

## Task session decisions, 2026-10-17

- **I-05f0ba74, I-df0092f7 (file impact omits consumers).** Fixed together, since one is the code
  and the other the contract of the same gap. `impact(paths=...)` now adds to the binders every
  Module that uses one of them, directly or through further `uses`, through a new
  `SpecRepository.users(modules)` query (cycle-safe, sorted). `implemented_by` stays the direct
  binder lookup. Spec core contracts and `scenario.spec.impact-indexes` state the closure; the
  Spec MCP `impact` tool now answers files with Spec core's `impact`, so it gains the closure too
  (a small mechanical follow-on inside this task's Modules).
- **I-582fabaa (decision-needed).** Carried out option A as the main agent answered: `context`
  gains `bound`; module.md and `req.spec-mcp.spec-core-answers` say every value is Spec core's,
  unchanged, in the documented envelope; contracts.md gains a `#result-fields` table naming each
  field's Spec core source; `scenario.spec-mcp.queries` and its test compare field by field.
- **I-2856d8a6 (MCP wire standards).** Chose to make the local contract the complete wire rather
  than add pinned MCP/JSON-RPC standards as external inclusions: adding a reference submodule is a
  repository-wide change outside this task's Modules, and the server's wire is small. contracts.md
  now defines every message (initialize, initialized, ping, tools/list, tools/call, roots/list),
  the envelope rules, the six tools' input schemas in a JSON block (task_type enum, required
  fields, minLength), that descriptions are not contractual, and that unnamed arguments are
  ignored. The server's input schemas gained `minLength: 1` to match what it already enforced; a
  test checks the advertised schemas and order against the contract block.
- **I-33244534 (receipt through a symlink).** `installed_files` refuses with `unsafe_path` when
  `.concorde/install.json` or `.concorde` is a symbolic link, and otherwise reads through
  `read_file`; an absent record still means no installed file. Grant computation therefore
  refuses; validation reports the refusal as `CHK.binds.installed` at `.concorde/install.json`
  (chosen over a new rule identity, since that check is the one that cannot be evaluated without a
  trustworthy record). New `scenario.spec.grant-installed-link`.
- **I-c019efac (shared-write omits Spec paths).** The shared-file refusal now checks every `rw`
  entry of the combined grant, whichever set made it writable, against every unbound Module's
  realization entries, before installed-file lowering. `_shared_path` moved to `repository_base`
  as `shared_path` so grants and the binding-Modules index share it. New
  `scenario.spec.grant-shared-spec`.
- **I-df2438b7 (external material cached).** Removed the per-repository external cache; listing
  and digest are read together per query (`external_context` reads each entry once per call).
  Rewrote the snapshot test as `scenario.spec.snapshot-external`. Timing: a grant of
  module.workers takes ~1.3 s, spec-validation ~20 s as before.
- **I-7b107990 (diagram language not selected).** Added `protocol/views.md` as a bound inclusion
  of module.spec, and also `protocol/style.md`, which the CHK.style checks defer to in the same
  way (same gap, a one-line follow-on); registry refreshed.

## Non-ok result: delivery r-20261017T045717-delivery-6b6cd0a0 (2026-10-17)

`delivery` failed in its configured checks with `OSError: [Errno 28] No space left on device`
(check.workers.tests, check.views.tests, check.views.repository-regressions, and the trace write of
check.workflows.tests). The root filesystem had 1.4 GB free (879G, 833G used) while the parallel
round-4 tasks ran their checks; no failure points at this task's change. Before it,
`task-validation` was ready and the full suite passed on the same head e887d640c (1593 passed,
6 skipped). Decision: retry `delivery` once unchanged, since the cause is transient disk pressure
outside this task; escalate as `environment` if it fails again.

## Report 2 to the main agent (Review流程), 2026-10-17T05:14:01Z

r4-spec delivered: delivery commit 28b2523d207d9e480a745bd917ebee611c90e3e4 on concorde/r4-spec (task-validation ready; full suite 1593 passed, 6 skipped on e887d640c). All eight Issues fixed, and the task resolves all eight:
- I-05f0ba74 + I-df0092f7 (file impact omitted consumers): impact(paths) now adds every Module that uses a binder, directly or transitively (new SpecRepository.users, cycle-safe); contract and scenario.spec.impact-indexes updated; the Spec MCP impact tool now uses Spec core's impact for files.
- I-582fabaa (decision-needed): option A as you answered — `context` gains `bound`, the promise now says every value is Spec core's, unchanged, in the documented envelope, a #result-fields table names each field's source, and scenario.spec-mcp.queries plus its test compare field by field.
- I-2856d8a6 (preferred-fix): I chose a complete local wire contract over pinning MCP/JSON-RPC standards, since a new reference submodule is a repository-wide change outside this task's Modules and the wire is small. contracts.md now defines every message, the envelope rules and the six tools' input schemas (descriptions are informative, not contractual; unnamed arguments are ignored). A test checks the advertised schemas against that block, and the schemas gained minLength 1 to match what the server already enforced.
- I-33244534: the installation record is never read through a symlink. A symlinked record refuses the grant with unsafe_path, and validation reports it as CHK.binds.installed. New scenario.spec.grant-installed-link.
- I-c019efac: the shared-file refusal now checks every rw entry of the combined grant, Spec paths included. New scenario.spec.grant-shared-spec.
- I-df2438b7: removed the external-material cache, so listing and digest are read per query. New scenario.spec.snapshot-external.
- I-7b107990: bound inclusions of protocol/views.md plus protocol/style.md (same gap for CHK.style), registry refreshed.
Non-ok result: the first delivery (r-20261017T045717-delivery-6b6cd0a0) failed with ENOSPC (No space left on device) in configured checks. A retry unchanged succeeded. WARNING: the root filesystem has only about 414 MB free now (879G disk, 834G used), so other round-4 deliveries and your merge checks may fail the same way. Nothing in Concorde's own dirs is large (worktrees ~0.5-0.9 GB each, /tmp/claude-1000 4 GB). Nothing is left open in this task.

## Closed: merged, 2026-10-23T09:00:35Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 28b2523d207d9e480a745bd917ebee611c90e3e4 into main and closed it as merged. Nobody answers a report after that.
