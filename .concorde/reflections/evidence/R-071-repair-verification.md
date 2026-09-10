# R-071 maintenance repair verification — 2026-09-10

This is new repair evidence, independent of the prior CI repair and its manual merge.
The source candidate is `change.beb86850-1357-4441-b3f9-b2d7d60c921e`, branch
`concorde/beb86850-1357-4441-b3f9-b2d7d60c921e`, initially based on committed
`012db63f77f745aaa15409ed53ec1f9d9253865f`, in
`/tmp/concorde-worktree-i7fy_c71/project`.

## Behavior and regression evidence

An existing change ID now requires valid local change state before worktree preparation.
Unbound development candidates continue actual coordinator routing after a fresh-host handoff;
the presence of a change ID or a target hint cannot replace selection. Bound resumes restore
omitted owner fields, resolve the current Module contract and reject explicit intent conflicts
before launching an Agent. Trusted internal component routes retain their own task context
without rewriting the root owner. Standalone review without a change ID keeps its independent
routing behavior. Missing or inconsistent owner and workspace fields return structured errors.

The regression calls the public host on a committed temporary consumer primary, receives a real
host-created Git worktree handoff, and resumes using a new host and executor. Before the fix, all
four `specify × run_reviews` combinations failed with `execution_failed: 'target_id'` before
routing or graph execution. After the fix, each reaches ready with one successful route selection
(the fixture performs one discovery expansion first), the requested author/review stages and the
original task and constraints. Other cases cover restored focus, omitted constraints, conflicting
target/task/focus/constraints, missing/foreign change, wrong path/branch/primary, malformed or
missing owner/base fields and trusted child target mismatch.

[Run evidence and exact commands](R-071-repair-runs.json) record:

- Final complete Python suite: **659 tests, 0 failures, 0 errors, 8 skipped**, using the project's
  runner over 45 modules. The skipped cases require the opt-in Studio server.
- Expanded Development review and Harness lifecycle regression run: **78 tests passed**; the
  final complete suite also includes the last missing-identity-field matrix.
- Spec validation: **success**, no errors or advisory findings; 39 scenario-coverage warnings
  remain. Structural validation does not prove semantic completeness.
- `build --check`: **success**. No prompts, Skills, capability definitions or wire contracts were
  changed, so no generated sources were edited or stale-build check bypassed.
- The initial full run exposed an obsolete missing-change assertion and error-field literals
  misidentified by the package error-code collector. Both were corrected; the final suite includes
  the installer/package regressions that previously failed.

## Independent review

[Review evidence](R-071-repair-review.json) records two fresh independent read-only reviewers:
one read the complete eight-document Development contract, the other the complete nine-document
Harness contract. Both reviewed their admitted shared implementation and final diff, including
the final identity-field update, with **no blocking findings**. Content SHA256 values bind the
review to the exact reviewed sources. Harness additionally ran 26 owner and 18 identity-field
pure-memory probes. These are external maintenance reviews, not invented Framework review records.

## Formal lifecycle and remaining scope

The original host-created change contains no authored target plans. The existing deterministic
`concorde-validate` direct-candidate contract is therefore applicable: bind the selected validation
target to the original recorded task/constraints, validate current Specs, execute every configured
project check and let the host decide readiness. The invocation uses the public launcher with
`run_checks:true`; its actual result and `.concorde/worktree.json` are the authoritative lifecycle
evidence. External tests and reviews above do not themselves set ready. No target, ready, review,
gap or lifecycle record was edited to manufacture admission or completion.

The final response reports the actual validation outcome after this evidence and the source
commit are complete. This document deliberately does not predeclare that future invocation's
result. It can be inspected in the retained worktree at
`.concorde/runs/R-071-maintenance-validation.json` alongside the host's per-check logs.

R-071 remains a tracked container for **R-071/F1** topology recovery, **R-071/F2** hidden-path
semantics and **R-071/F3** richer gap/routing diagnostics, as listed in the pending record. The
core resume defect is repaired; those broader items are not claimed solved. The user's scope is
an independent branch commit and retained worktree, with no merge, push, delivery or cleanup.
