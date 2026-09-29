# Decision log: typed-value-json-schema

Goal: Make Spec core's typed-value checker follow JSON Schema: an object schema without additionalProperties is open, and the type number is known; then give the merge trace's waited_seconds its type number as its contract says
# typed-value-json-schema: brief (main agent, 2026-09-29)

The developer asked for this follow-up of task `tracing`, whose session found it (history:
`.concorde/history/tracing/decisions.md`, "Spec core's typed-value checker ..."):
- Spec core's typed-value checker (`concept.typed-value`, `src/concorde/spec/typed_data.py` or
  `schema.py`) treats `{"type": "object"}` as a closed object.
- It does not know `"type": "number"`.

Tracing therefore spelled open objects as `{"type": "object", "additionalProperties": {}}`, and
registered the merge trace's `waited_seconds` with no type, although the Tasks contract says it is
a number.

## Goal
- Make the checker follow JSON Schema for the subset it supports: an object with no
  `additionalProperties` is open, and `number` accepts integers and non-integral numbers but not
  booleans.
- Check every schema already registered in the project: any that relied on the implicit closing
  must now say `additionalProperties: false` explicitly, so no contract becomes looser than it
  promises.
- Give `waited_seconds` its `number` type (module.tasks).
- The explicit `additionalProperties: {}` spellings may stay.
- Update module.spec's Spec where it describes the checker's schema subset.

## Left to the session
How to find the schemas that relied on implicit closing, and any schema outside module.spec or
module.tasks that needs `additionalProperties: false` to keep its promise. Such a change is a direct
consequence of the goal. Record it here.

# Task session decisions (2026-09-29)

- **Finding schemas that relied on implicit closing.** Imported every Module that registers a
  typed type (14 types) plus the other schemas `check_schema` is called with directly (Issues'
  `REPORT`, `RECORD`, `PROVENANCE`, `RECEIPT`; Spec core's `context_record_schema()`), and walked
  them for `"type": "object"` without `additionalProperties`. Result: all 58 object schemas already
  spell it (46 `false`, 12 `{}`), so no schema had to gain `additionalProperties: false`; no
  contract becomes looser.
- **Checker follows JSON Schema for the whole subset it evaluates, not only objects and number.**
  Beyond the two named points, `check_schema` now also: evaluates `minimum`/`maximum` (4 registered
  schemas used `minimum` and it was silently ignored; `waited_seconds` needs it), `maxItems`,
  `maxLength`, boolean schemas; applies each keyword to the value's actual kind whether or not the
  schema names a `type`; compares `const`/`enum` with JSON type (`true` is not `1`); and matches
  `pattern` anywhere (JSON Schema's `search`) instead of `fullmatch`. Reason: the goal asks the
  checker to follow JSON Schema, and a second checker disagreeing with the offline subset
  (`schema.validate`) on the same schema is a trap.
- **Pattern anchoring outside module.spec/module.tasks.** The only registered pattern relying on
  `fullmatch`, Issues' `ISSUE_ID` (`src/concorde/issues/shapes.py`, module.issues), is now anchored
  `^I-[0-9a-f]{32}$`, exactly as the Issues contract (`specs/concorde/issues/interface.md`) already
  spells it. A direct consequence of the goal that keeps the promise; no Spec change there.
- **Kept a deliberate deviation:** a string whose schema sets `minLength` must not be whitespace
  only (Concorde's `STRING`); relaxing it would loosen existing contracts. Now stated in
  module.spec's contracts.
- **`register` refuses keywords the checker does not evaluate** (`$defs`, `oneOf`, `allOf`, a list
  of types; local `$ref` was already refused) with `invalid_input`, so no registered type promises
  more than its values are checked for. No current registration uses them.
- **Spec changes (module.spec):** contracts.md "Typed values" states the JSON Schema checking rules
  and the refused keywords; req.spec.typed-closed reworded (the envelope stays closed, data is
  checked as JSON Schema would, registration refuses unevaluated keywords; id and title kept); the
  typed-value-reject scenario says "closed object schema"; new scenario
  `scenario.spec.typed-value-json-schema` with its test; module.md's realization no longer calls the
  checker "closed".
- **module.tasks:** `waited_seconds` is `{"type": "number", "minimum": 0}` as contract.tasks.merge-trace
  says; the merge test checks the recorded node validates and that -0.5, "0.4", true and null are
  refused. The contract text itself needed no change.
- **Refinements after first pass:** `const`/`enum` compare numbers by value (`1` equals `1.0`) but a
  boolean equals only a boolean; the unevaluated-keyword refusal walks schema structure
  (`properties`, `items`, `additionalProperties`, `anyOf`), so a property merely named `oneOf` is
  admitted.
- **Sandbox masks:** untracked `.bashrc`, `.claude/settings.json` etc. seen in the worktree are the
  session sandbox's `/dev/null` bind mounts, not files; nothing was committed from them.
- **Verification:** `build --check` clean, `spec-validation` 0 errors/warnings, full suite 797
  passed / 4 skipped, `task-validation` ready (9 changed paths, 23 checks passed, 0 warnings).
- **Delivered:** delivery commit `f26e94cb4c5b3d65a2de98f73de34ca72780c440` on
  `concorde/typed-value-json-schema`, bundle `.concorde/evidence/typed-value-json-schema/1.json`,
  on top of `47ac9103`.

## Closed: merged, 2026-09-29T10:56:32Z
