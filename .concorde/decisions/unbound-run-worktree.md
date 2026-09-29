# Decision log: unbound-run-worktree

Goal: Run every unbound run in its own throwaway detached worktree instead of the primary worktree, so that main sessions merging into the primary worktree meanwhile can neither disturb it nor make the worker audit fail (an unbound spec_panel failed its HEAD/index audit when a task was merged during the run): the runner creates a detached worktree of the primary worktree's HEAD in a private temporary directory (git worktree add --detach), runs the Operation and its workers there, audits that worktree, keeps the run store and worker model configuration of the primary worktree, and removes the worktree however the run ends; configured checks of an unbound code_review may use the primary worktree's ignored environments (.venv, node_modules) read-only; the result names the commit it examined. Update Execution's (and Workers'/Operations'/Main session's where they describe unbound runs) Specs and tests

## Escalated to the main agent, 2026-09-28T16:43:51Z

- **task-session** task session (task unbound-run-worktree): `out_of_module_wording`
  Unbound runs now work in an unbound checkout of the starting worktree's HEAD (implemented, tested, Execution/Workers/Operations/Main-session Specs updated). Four one-phrase passages in module.concorde, module.spec-review and module.code-review still say an unbound run reads the worktree 'as it stands'; they should say it examines that worktree's HEAD (committed state, the commit named in the result). May this task correct them?
  Not handled here (scope): the passages belong to Modules outside this task's Modules (module.execution, module.workers, module.operations, module.main-session)
  Options: correct the four passages in this task; leave them for a follow-up task
  Recommendation: correct the four passages in this task: wording only, no promise beyond what Execution now promises
  Caused by:
  - **component** Spec texts of module.concorde, module.spec-review and module.code-review: `stale_unbound_wording`
    After this task, an unbound run examines an unbound checkout of the HEAD of the worktree it starts in, not that worktree as it stands. Four passages of Modules outside this task's Modules now describe the old behaviour: specs/concorde/module.md:105 (module.concorde) 'an unbound run that reads that worktree as it stands'; specs/concorde/spec-tooling/spec-review/module.md:37 (module.spec-review) 'an unbound run that judges the Specs as they stand there'; specs/concorde/spec-tooling/spec-review/requirements.md:13 (module.spec-review) 'an unbound run keeps its run store in the worktree it reviews'; specs/concorde/execution/operations/code-review/module.md:27 (module.code-review) 'required for an unbound run, which judges the worktree it starts in, such as the primary worktree, since that commit'.
    Not handled here (scope): the passages belong to Modules this task is not bound to, so a task session may not change them without the main agent
    Evidence (passage): specs/concorde/module.md:105 reads that worktree as it stands
    Evidence (passage): specs/concorde/spec-tooling/spec-review/module.md:37 judges the Specs as they stand there
    Evidence (passage): specs/concorde/spec-tooling/spec-review/requirements.md:13 keeps its run store in the worktree it reviews
    Evidence (passage): specs/concorde/execution/operations/code-review/module.md:27 judges the worktree it starts in ... since that commit
    Options: let this task correct the four passages (wording only, linking the new glossary term Unbound checkout); leave them for a follow-up task
    Recommendation: let this task correct the four passages

```json
{
  "level": "task-session",
  "actor": "task session (task unbound-run-worktree)",
  "code": "out_of_module_wording",
  "detail": "Unbound runs now work in an unbound checkout of the starting worktree's HEAD (implemented, tested, Execution/Workers/Operations/Main-session Specs updated). Four one-phrase passages in module.concorde, module.spec-review and module.code-review still say an unbound run reads the worktree 'as it stands'; they should say it examines that worktree's HEAD (committed state, the commit named in the result). May this task correct them?",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "the passages belong to Modules outside this task's Modules (module.execution, module.workers, module.operations, module.main-session)"
  },
  "options": [
    "correct the four passages in this task",
    "leave them for a follow-up task"
  ],
  "recommendation": "correct the four passages in this task: wording only, no promise beyond what Execution now promises",
  "causes": [
    {
      "level": "component",
      "actor": "Spec texts of module.concorde, module.spec-review and module.code-review",
      "code": "stale_unbound_wording",
      "detail": "After this task, an unbound run examines an unbound checkout of the HEAD of the worktree it starts in, not that worktree as it stands. Four passages of Modules outside this task's Modules now describe the old behaviour: specs/concorde/module.md:105 (module.concorde) 'an unbound run that reads that worktree as it stands'; specs/concorde/spec-tooling/spec-review/module.md:37 (module.spec-review) 'an unbound run that judges the Specs as they stand there'; specs/concorde/spec-tooling/spec-review/requirements.md:13 (module.spec-review) 'an unbound run keeps its run store in the worktree it reviews'; specs/concorde/execution/operations/code-review/module.md:27 (module.code-review) 'required for an unbound run, which judges the worktree it starts in, such as the primary worktree, since that commit'.",
      "evidence": [
        {
          "kind": "passage",
          "ref": "specs/concorde/module.md:105",
          "detail": "reads that worktree as it stands"
        },
        {
          "kind": "passage",
          "ref": "specs/concorde/spec-tooling/spec-review/module.md:37",
          "detail": "judges the Specs as they stand there"
        },
        {
          "kind": "passage",
          "ref": "specs/concorde/spec-tooling/spec-review/requirements.md:13",
          "detail": "keeps its run store in the worktree it reviews"
        },
        {
          "kind": "passage",
          "ref": "specs/concorde/execution/operations/code-review/module.md:27",
          "detail": "judges the worktree it starts in ... since that commit"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "scope",
        "explanation": "the passages belong to Modules this task is not bound to, so a task session may not change them without the main agent"
      },
      "options": [
        "let this task correct the four passages (wording only, linking the new glossary term Unbound checkout)",
        "leave them for a follow-up task"
      ],
      "recommendation": "let this task correct the four passages",
      "causes": []
    }
  ]
}
```

## 2026-09-29 — main agent: answer to escalation #1 (out_of_module_wording)

- Approved option (a): the task corrects four one-phrase passages outside its Modules (root
  module.md, spec-review module.md and requirements.md, code-review module.md) that still say an
  unbound run reads the worktree "as it stands". Reason: wording only, consistent with what
  Execution now promises and with the developer's decision that unbound runs work in their own
  checkout; a follow-up task would leave the Specs contradictory in between.

## Decisions of the task session (2026-09-29)

1. **Where the checkout lives and how it is named.** Options: the mkdtemp directory itself as the
   worktree; a `worktree` subdirectory; a subdirectory named after the run identity. Chosen:
   `tempfile.mkdtemp(prefix="concorde-unbound-")/<run-id>`, so the checkout lands under
   the system's temporary directory (TMPDIR), which is private (mode 0700), and Git's
   administrative entry is named after the run and can be traced. Git hooks are disabled for the
   runner's Git calls (`-c core.hooksPath=/dev/null`), because this is the runner's checkout, not
   a developer's.
2. **External references vendored as submodules.** A detached checkout leaves submodules empty,
   so an unbound review of Workers, Harness, Main session and other Modules would have lost their
   pinned external references (`references/pi`, …). Options: symlink the origin's submodule
   checkouts, which Git reports as a typechange and which the Harness's deny rules handle poorly
   (and changing Harness is outside this task); clone again with init-references, which needs the
   network and the read-only `.git/config`; or run `git worktree add --detach --no-checkout` from
   the origin's submodule repository with the origin's sparse patterns, then `read-tree -mu HEAD`.
   Chosen: the last one, which uses Git's own mechanism, works offline and leaves `git status`
   clean. A submodule the origin has not checked out stays empty, with `submodule-absent`
   evidence.
3. **Ignored environments.** Options: link only for code_review; link every runtime path. Chosen:
   link each relative `workers.runtime` path (default `.venv`, `node_modules`) that exists in the
   origin and that Git ignores in the checkout, as a symbolic link, for every unbound run. That
   single existing notion, "runtime paths", avoids a code_review special case. A path Git does not
   ignore is never linked (`environment-not-linked`). Checks read the link inside their read-only
   boundary.
4. **How the result names the commit.** Options: host evidence only; a typed field. Chosen: a
   typed `commit` field of the run result, null for bound runs, which follows the rule that
   structural facts are fields. The run-result contract therefore goes from version 1 to 2, and
   `checkout` evidence names the commit and path as well. The progress file also gets `commit`,
   and its `worktree` becomes the checkout once it exists.
5. **When the checkout is removed.** Before the result is composed, so that a removal Git refuses
   becomes `checkout-not-removed` evidence in the result. An ExitStack callback on the same
   idempotent close covers an unexpected exception. A SIGKILL leaves the directory to temporary
   file cleaning and the worktree entry to Git's pruning, which the Spec states.
6. **Error link of a refused checkout.** A new refusal `checkout_unavailable` (reason
   `environment`, cause actor `Execution (unbound checkout)`), raised when HEAD names no commit or
   Git refuses. The runner never falls back to the origin. The unbound actor now reads
   `(unbound, <origin> at <commit>)`.
7. **New glossary term.** I added `concept.unbound-checkout` (owner module.execution) because the
   Specs and the refusal actor use the checkout as a noun. `concept.unbound-run` is redefined to
   work in it.
8. **Worker model configuration.** It is read from the worktree the run started in
   (`RunContext.started_in`). `.concorde/config.json` limits are read from the checkout, since that
   file is tracked and belongs to the examined commit.

## Escalation sent

Escalation #1 `out_of_module_wording`: four passages in module.concorde, module.spec-review and
module.code-review still describe unbound runs reading the worktree "as it stands". I asked the
main agent whether this task may correct them and recommended correcting them. The rest of the
work continues without waiting for the answer.

## Main agent's answer to escalation #1

Approved option (a): correct the four passages in this task, wording only, linking "Unbound
checkout", stating what is read (the checkout of HEAD) and where the run store stays (the
worktree the run started in), and adding no promise beyond Execution's. The four passages were
corrected in specs/concorde/module.md, spec-review/module.md, spec-review/requirements.md and
code-review/module.md.

## Non-ok results

- Full suite (`.venv/bin/python -m pytest`) on the final input: 644 passed, 4 skipped, 1 failed:
  `tests/concorde/e2e/test_cases.py::CaseTests::test_grading_runs_the_case_tests_on_a_throwaway_tree`
  (`{'test_calc.py::test_add': 'FAILED'} != {'test_calc.py::test_add': 'not run'}`). It fails
  identically in a detached checkout of the unchanged base commit, so it is pre-existing and
  unrelated to this task (the e2e case grading, not Execution). Left as is and reported. The
  configured checks in task-validation r-20260928T164540-task_validation-355bfce0 all passed.
- Smoke run of the real `concorde run understand` in an unbound scratch worktree ended
  `host_error`. That was expected, because the scratch copy had no build (`generated/` missing).
  It confirmed the checkout, the `commit` field, the linked `.venv`, `submodule-absent` evidence and
  complete removal.

## Closed: merged, 2026-09-28T16:57:21Z
