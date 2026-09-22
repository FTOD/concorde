# Evidence plugin counts subtest failures differently from pytest 9

## Observation (independent tester 9229121b, 2026-09-22, candidate 3f97db60)

`tests/concorde/support/pytest_timing.py` (the local evidence plugin introduced by
`change.b0b2efdc-1909-42cd-8bba-0fd533eb358d`) writes a JSON summary whose `totals` treat a
test with a failed `subTest` as one failed unit: for one run it reported 1039 passed / 3 failed
while the pytest 9 terminal line said `3 failed, 1040 passed, 16 skipped, 1 error` because
pytest 9 lists the SUBFAILED entry separately and counts the parent as passed (1060 lines for
1059 collected tests). Neither is a test regression; the two counts simply follow different
conventions, and the `units` array of the summary already carries the parent as `error`
with the subtest failure nested.

## Agreed behavior

Pick one convention and state it in the plugin docstring and in the summary itself (e.g. a
`counting` field), so a reader comparing the JSON `totals` with the pytest terminal line does
not conclude that a test went missing. The plugin's per-unit convention (parent unit fails
when any subtest fails, units sum to the collected count) is the more useful one for evidence;
keep it and document the difference from pytest's terminal summary, or additionally emit
pytest's own counts side by side. Add or extend the plugin's Spec test
(`tests/concorde/distribution/test_outer_agents.py::OuterAgentsTests::test_runner_fingerprints_and_legacy_cli`,
`scenario.distribution.test-timing`) with a subtest-failing fixture if cheap.

## Non-goals

Changing how tests use `subTest`, or replacing pytest's subtest reporting.

## References

- Tester report: `/tmp/pi-subagents-uid-1000/async-subagent-runs/9229121b-fcf4-48a2-be8e-1c63ca64f549`
- Related note: `.concorde/todos/slow-test-semantic-audit.md`
