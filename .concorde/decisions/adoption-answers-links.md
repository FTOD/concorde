# Decision log: adoption-answers-links

Goal: Developer-approved panel-review decisions for Adoption: (adoption F5) every answered code_to_spec question needs a promise with source answer, plus a deviation when the code differs (tighten records.answer_problems, the requirement and contract.adoption.answers with a version bump); (adoption F20) test linking leaves a test file untouched and reports the link in unlinked_tests when the file already binds a top-level verifies that is not Concorde's helper or a recognised verifies decorator, with a scenario and a test.

## Decisions taken without the developer (task session)

- **F5: what the host can check.** The host cannot judge whether the code differs from an
  answer, so `answer_problems` now requires, for every `q.` answer, a promise with source `answer`
  naming it; a deviation no longer satisfies the check on its own. The deviation half of the rule
  stays the worker's obligation (req.adoption.deviation-reported, already in the worker prompt).
  Options: (a) promise required, deviation unchecked; (b) also reject deviations naming no
  answered question. Chose (a): (b) would fail a rerun without `--answers` that legitimately
  re-reports a known deviation, and the goal asked only to tighten the promise rule.
- **F5: signature.** Dropped the now unused `deviations` parameter of `answer_problems` rather
  than keep it inert (rapid-iteration rule: no compatibility shims).
- **F5: version.** `contract.adoption.answers` 1 → 2 (its semantics changed); the schema is
  unchanged, so no answers file becomes invalid.
- **F20: which bindings count.** "Top-level" is read as module level: bindings inside top-level
  `if`/`try`/`with`/loops count too, never those in function or class bodies. Compatible bindings
  are Concorde's no-op helper recognised by shape (`def verifies(*names)` returning a one-argument
  identity lambda, optional docstring, any formatting or comment) and `from
  concorde.spec.verification import verifies` without renaming, the only import path that exports
  Concorde's decorator. Everything else (other imports, `import ... as verifies`, assignments,
  other defs, classes) is foreign. Reason: a decorator in such a file would call the project's own
  `verifies`, with unknown effect on the tests.
- **F20: already-declared links.** A link the file already declares is still reported in
  `linked_tests` even when the binding is foreign, since nothing is written and the scanner sees
  the declaration; only links needing a new decorator are refused.
- **F20: reason text.** The `unlinked_tests` reason names the file and the binding's line.
- Also documented the rule in module.md's Design paragraph on test linking beside the requirement
  and the new scenario `scenario.adoption.foreign-verifies`.

## Non-ok results

- `uvx ruff` first failed on the sandbox's read-only `~/.local/share/uv/tools`; ran it with
  `UV_TOOL_DIR=~/.cache/uv-tools` instead. One Bash call failed on a transient bwrap mount error
  (`.git/config.lock` vanished); a retry passed.
- `ruff check` (default rules) reports two findings in `tests/concorde/adoption` that predate this
  task (S102 `exec` in test_adoption.py, I001 import order in test_links.py); left as they are,
  outside the goal. The project's rule is formatting, which passes.

## Closed: merged, 2026-09-28T17:24:52Z
