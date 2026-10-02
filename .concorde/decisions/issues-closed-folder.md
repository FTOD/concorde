# Decision log: issues-closed-folder

Goal: Keep closed Issue records in .concorde/issues/closed/ so .concorde/issues/ holds only open ones: closing moves a record there and reopening moves it back, each in one commit, with an archive action that moves misplaced closed records

## Brief (main agent, 2026-10-02)

The developer's request (2026-10-02): "我想在 issues 里面开一个单独的文件夹，就叫closed, 把closed 的归档.
这样在 issues/ 里直接看到的 .md 都是 open 的问题" — a separate folder `closed` inside the Issue
directory where closed Issues are archived, so that the `.md` files seen directly in
`.concorde/issues/` are the open Issues.

Decided by the main agent (details of the developer's request):
- An open Issue's record is `.concorde/issues/<id>.md`; a closed one's is
  `.concorde/issues/closed/<id>.md`. An identity lives in exactly one of the two places.
- Every closing disposition (resolved, duplicate, not-actionable), including the closes a task
  merge makes under its held lock, moves the record into `closed/` in the same commit as the
  disposition; `reopened` moves it back. The commit names both paths (still nothing else of the
  primary worktree), keeps the author identity and hooks, and the receipt and outputs give the
  record's current path.
- Reads by identity, `list`, `show`, appends (still refused for a closed Issue) and duplicate
  checks find a record in either place. Recovery of uncommitted leftovers covers both places and
  a write interrupted in the middle of a move.
- `check` reports, as errors, a record whose folder does not match its status and an identity
  present in both places, each naming the fix.
- A new action `concorde issues archive` (command only, like `recover`; no MCP tool) moves, under
  the merge lock and as one commit, every record whose folder does not match its status to the
  right folder, and prints what it moved. Task branches never change `.concorde/issues/`, so
  this task does not move the existing records: after the merge the main agent runs `archive` on
  the primary worktree once, moving today's 199 closed records.
- No backward compatibility beyond `archive` (rapid-iteration rule).

Also update the two mentions in docs/using-concorde.md (lines ~818 and ~913, module.concorde) and
anything else in module.issues' Specs and the main-session guidance that names the record path
(the receipt's `path` pattern in interface.md). The guidance texts belong to module.main-session:
if they need a change, escalate it instead.

Left to the task session (record each choice): the move mechanics (git mv or add/rm in one
commit), error codes, scenarios and tests (close moves, reopen moves back, merge close moves,
archive, check's two errors, recovery mid-move). Verify with build --check, spec-validation and
the full suite, then task-validation and delivery, and report.

## Task session decisions (2026-10-02)

- **Move mechanics.** A write publishes the record at its place (`.concorde/issues/<id>.md` open,
  `.concorde/issues/closed/<id>.md` closed) through the file transaction, then removes the path it
  is committed at, then `git add -f` of the new path and `git commit --only` of both paths; no
  `git mv`, since a disposition changes the content in the same commit. `archive` uses the same
  path with the bytes unchanged (revision stays), all moves in one file transaction and one commit
  `concorde: archive <n> Issue record(s)` with one `Concorde-Issue:` trailer per Issue.
- **Every write leaves the record in its place**, so an append to an open record misplaced in
  `closed/` moves it too: one invariant instead of special cases.
- **A changed old path during a move** (another program edited it between the read and the
  removal) is refused `stale_issue` and that change is kept: only the published file is put back.
- **Receipt.** Its `path` is where the record lies when the receipt is returned (a repeated report
  of an Issue closed since gets the `closed/` path); `resolve_report` accepts either path. The
  receipt contract's path pattern widened, so `contract.issues.receipt` and the typed value
  `concorde-issue-receipt` go to version 2.
- **Outputs.** `show` and `close`/`reopen` (and the library `dispose`) add `path`; `list` rows are
  unchanged, since review Operations consume their shape.
- **An Issue committed in both folders** is refused by reads and `list` with the existing
  `invalid_issue`, naming both paths (no new code); `archive` leaves both paths, and a misplaced
  record holding a hand change, in `left` with the reason.
- **Recovery mid-move.** The committed record an uncommitted record file must continue is the
  Issue's, at its own path or the other one. A committed record whose file is gone while the other
  folder holds an uncommitted valid continuation is a move's leftover: restored, and the new file
  removed. A deletion without such a copy stays `left` as before.
- **check.** Two new errors: `<path> holds <status> Issue <id>, whose record belongs at <place>;
  run concorde issues archive …` and `Issue <id> is recorded twice, as … and …` naming the repair
  (keep the record whose history begins with the other's, `git rm` the other in a commit of its
  own). A `closed` that is not a directory is an error too.
- **Specs.** New requirements `req.issues.status-folder` and `req.issues.archive`; amended
  `req.issues.closed-kept`, `req.issues.commit-alone`, `req.issues.uncommitted-recovered`. New
  scenarios `store-folders`, `store-folders-locked`, `store-interrupted-move`, `store-archive`,
  `store-archive-left`, `command-archive`, `store-check-misplaced`, verified by the new
  `tests/concorde/issues/test_closed_folder.py` (bound in `realization.issues.tests`) and
  `test_store_check.py`. docs/using-concorde.md updated (both mentions plus a line on
  check/archive).
- **No guidance change.** No main-session guidance text names the record path, so nothing to
  escalate for module.main-session.
- **Result `blocked`: task-validation `r-20261002T101615-task_validation-4b3b2ba6`.** Its one
  finding is `check.issues.store` failing with 199 errors: every record of this branch's copy of
  `.concorde/issues/` (all 199 closed, from the base commit) lies in the top folder, which the new
  check reports as misplaced. Everything else passes (build --check, spec-validation, full suite
  964 passed). The brief forbids this branch to move the records, so delivery needs a decision:
  escalated below.

## Escalated to the main agent, 2026-10-02T10:18:33Z

- **task-session** task session (task issues-closed-folder): `base_records_misplaced`
  The work is done and committed (ef3f84b3): closed Issues live in .concorde/issues/closed/, close/reopen (and the merge's locked close) move the record in the disposition's commit, reads find either folder, recovery puts back a half-done move, check reports a misplaced record and an Issue recorded twice as errors as the brief decided, and 'concorde issues archive' moves misplaced records in one commit. build --check, spec-validation and the full suite (964 passed) pass. But task-validation is blocked: check.issues.store runs on this task worktree's own copy of .concorde/issues/, whose 199 records (all closed, from the base commit) are all in the top folder, so the new check reports 199 misplaced records. The brief says the task branch does not move existing records and the main agent archives them after the merge, which this check makes impossible: delivery refuses while the check fails, and archive does not exist on the primary branch before the merge.
  Not handled here (decision): The brief explicitly forbids this branch to change .concorde/issues/ and fixes the check's severity as an error; resolving the block means overriding one of those two decisions, which are the main agent's.
  Options: A: this task branch moves its copy of the 199 closed records into closed/ in one commit of its own (exactly what archive does, bytes unchanged), a one-time exception to 'task branches never change .concorde/issues/'. The merge brings the moves as exact renames; records closed on primary since the base stay at the top and the post-merge archive moves them. Only risk: a reopen of one of these 199 on primary before the merge becomes a rename+modify that Git resolves into a misplaced open record in closed/, which archive also fixes.; B: a misplaced record becomes a note of check, not an error (an Issue recorded twice stays an error). Nothing blocks, primary's check passes before archive too, but the folder rule is no longer enforced by the configured check.; C: before the merge the main agent moves the closed records on primary by hand (git mv, one commit), then I merge primary into this branch and deliver. Keeps the branch rule but is a hand edit of records, and until the merge the primary's old code no longer sees those closed records (list/show/reopen miss them).
  Recommendation: A: it keeps the check strict as decided, is the same move archive makes, needs no hand edit on primary, and the post-merge archive still catches the records closed on primary since the base.
  Caused by:
  - **command** Command task-validation r-20261002T101615-task_validation-4b3b2ba6 (workspace issues-closed-folder): `not_deliverable`
    workspace issues-closed-folder is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/readiness.json)
    Not handled here (decision): task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses
    Evidence (blocking): check.issues.store module.issues check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log
    Options: repair each blocking finding in the workspace and run task-validation again; run specify for a Spec finding, implement for a code or check finding
    Recommendation: repair the first blocking finding: check check.issues.store: module.issues check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log
    Caused by:
    - **check** check.issues.store: `check_failed`
      the configured check check.issues.store of module.issues failed with exit code 1; its log /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log ends with:
      | 925a4390be53, whose record belongs at .concorde/issues/closed/I-e896126f3c1e59a498fd925a4390be53.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-f3b333425f6e5c6a830dfcf99b2540d9.md holds closed Issue I-f3b333425f6e5c6a830dfcf99b2540d9, whose record belongs at .concorde/issues/closed/I-f3b333425f6e5c6a830dfcf99b2540d9.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-f496abcfc8df5f95a0760c1039a38c49.md holds closed Issue I-f496abcfc8df5f95a0760c1039a38c49, whose record belongs at .concorde/issues/closed/I-f496abcfc8df5f95a0760c1039a38c49.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-f5a63d97cc4e560482741adc19aef8c0.md holds closed Issue I-f5a63d97cc4e560482741adc19aef8c0, whose record belongs at .concorde/issues/closed/I-f5a63d97cc4e560482741adc19aef8c0.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-f669262daad05dffac15e34a6c73a970.md holds closed Issue I-f669262daad05dffac15e34a6c73a970, whose record belongs at .concorde/issues/closed/I-f669262daad05dffac15e34a6c73a970.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-f758e1cc77915514a0f465a1d41df5fc.md holds closed Issue I-f758e1cc77915514a0f465a1d41df5fc, whose record belongs at .concorde/issues/closed/I-f758e1cc77915514a0f465a1d41df5fc.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-f9ff7a740a9e511a8ca350d7f442204a.md holds closed Issue I-f9ff7a740a9e511a8ca350d7f442204a, whose record belongs at .concorde/issues/closed/I-f9ff7a740a9e511a8ca350d7f442204a.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-fb37550899ad530888d19dc948efc230.md holds closed Issue I-fb37550899ad530888d19dc948efc230, whose record belongs at .concorde/issues/closed/I-fb37550899ad530888d19dc948efc230.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-fc326b9c1f095e6bac9723e4bcf9de65.md holds closed Issue I-fc326b9c1f095e6bac9723e4bcf9de65, whose record belongs at .concorde/issues/closed/I-fc326b9c1f095e6bac9723e4bcf9de65.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-fe1b32de932657b986ded6dcee104ef5.md holds closed Issue I-fe1b32de932657b986ded6dcee104ef5, whose record belongs at .concorde/issues/closed/I-fe1b32de932657b986ded6dcee104ef5.md; run `concorde issues archive` in the primary worktree, which moves it there",
      |     ".concorde/issues/I-fff7d5cfbb1556e79fe386bcf07f7165.md holds closed Issue I-fff7d5cfbb1556e79fe386bcf07f7165, whose record belongs at .concorde/issues/closed/I-fff7d5cfbb1556e79fe386bcf07f7165.md; run `concorde issues archive` in the primary worktree, which moves it there"
      |   ],
      |   "notes": []
      | }
      Not handled here (capability): a configured check only measures the code it runs against
      Evidence (log): /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log sha256:1cbba533132ac0bc4065ae9875396ea19ae8341b759ab196a4f644e19509bb19

```json
{
  "level": "task-session",
  "actor": "task session (task issues-closed-folder)",
  "code": "base_records_misplaced",
  "detail": "The work is done and committed (ef3f84b3): closed Issues live in .concorde/issues/closed/, close/reopen (and the merge's locked close) move the record in the disposition's commit, reads find either folder, recovery puts back a half-done move, check reports a misplaced record and an Issue recorded twice as errors as the brief decided, and 'concorde issues archive' moves misplaced records in one commit. build --check, spec-validation and the full suite (964 passed) pass. But task-validation is blocked: check.issues.store runs on this task worktree's own copy of .concorde/issues/, whose 199 records (all closed, from the base commit) are all in the top folder, so the new check reports 199 misplaced records. The brief says the task branch does not move existing records and the main agent archives them after the merge, which this check makes impossible: delivery refuses while the check fails, and archive does not exist on the primary branch before the merge.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The brief explicitly forbids this branch to change .concorde/issues/ and fixes the check's severity as an error; resolving the block means overriding one of those two decisions, which are the main agent's."
  },
  "options": [
    "A: this task branch moves its copy of the 199 closed records into closed/ in one commit of its own (exactly what archive does, bytes unchanged), a one-time exception to 'task branches never change .concorde/issues/'. The merge brings the moves as exact renames; records closed on primary since the base stay at the top and the post-merge archive moves them. Only risk: a reopen of one of these 199 on primary before the merge becomes a rename+modify that Git resolves into a misplaced open record in closed/, which archive also fixes.",
    "B: a misplaced record becomes a note of check, not an error (an Issue recorded twice stays an error). Nothing blocks, primary's check passes before archive too, but the folder rule is no longer enforced by the configured check.",
    "C: before the merge the main agent moves the closed records on primary by hand (git mv, one commit), then I merge primary into this branch and deliver. Keeps the branch rule but is a hand edit of records, and until the merge the primary's old code no longer sees those closed records (list/show/reopen miss them)."
  ],
  "recommendation": "A: it keeps the check strict as decided, is the same move archive makes, needs no hand edit on primary, and the post-merge archive still catches the records closed on primary since the base.",
  "causes": [
    {
      "level": "command",
      "actor": "Command task-validation r-20261002T101615-task_validation-4b3b2ba6 (workspace issues-closed-folder)",
      "code": "not_deliverable",
      "detail": "workspace issues-closed-folder is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/readiness.json)",
      "evidence": [
        {
          "kind": "blocking",
          "ref": "check.issues.store",
          "detail": "module.issues check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "decision",
        "explanation": "task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses"
      },
      "options": [
        "repair each blocking finding in the workspace and run task-validation again",
        "run specify for a Spec finding, implement for a code or check finding"
      ],
      "recommendation": "repair the first blocking finding: check check.issues.store: module.issues check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log",
      "causes": [
        {
          "level": "check",
          "actor": "check.issues.store",
          "code": "check_failed",
          "detail": "the configured check check.issues.store of module.issues failed with exit code 1; its log /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log ends with:\n925a4390be53, whose record belongs at .concorde/issues/closed/I-e896126f3c1e59a498fd925a4390be53.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-f3b333425f6e5c6a830dfcf99b2540d9.md holds closed Issue I-f3b333425f6e5c6a830dfcf99b2540d9, whose record belongs at .concorde/issues/closed/I-f3b333425f6e5c6a830dfcf99b2540d9.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-f496abcfc8df5f95a0760c1039a38c49.md holds closed Issue I-f496abcfc8df5f95a0760c1039a38c49, whose record belongs at .concorde/issues/closed/I-f496abcfc8df5f95a0760c1039a38c49.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-f5a63d97cc4e560482741adc19aef8c0.md holds closed Issue I-f5a63d97cc4e560482741adc19aef8c0, whose record belongs at .concorde/issues/closed/I-f5a63d97cc4e560482741adc19aef8c0.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-f669262daad05dffac15e34a6c73a970.md holds closed Issue I-f669262daad05dffac15e34a6c73a970, whose record belongs at .concorde/issues/closed/I-f669262daad05dffac15e34a6c73a970.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-f758e1cc77915514a0f465a1d41df5fc.md holds closed Issue I-f758e1cc77915514a0f465a1d41df5fc, whose record belongs at .concorde/issues/closed/I-f758e1cc77915514a0f465a1d41df5fc.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-f9ff7a740a9e511a8ca350d7f442204a.md holds closed Issue I-f9ff7a740a9e511a8ca350d7f442204a, whose record belongs at .concorde/issues/closed/I-f9ff7a740a9e511a8ca350d7f442204a.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-fb37550899ad530888d19dc948efc230.md holds closed Issue I-fb37550899ad530888d19dc948efc230, whose record belongs at .concorde/issues/closed/I-fb37550899ad530888d19dc948efc230.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-fc326b9c1f095e6bac9723e4bcf9de65.md holds closed Issue I-fc326b9c1f095e6bac9723e4bcf9de65, whose record belongs at .concorde/issues/closed/I-fc326b9c1f095e6bac9723e4bcf9de65.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-fe1b32de932657b986ded6dcee104ef5.md holds closed Issue I-fe1b32de932657b986ded6dcee104ef5, whose record belongs at .concorde/issues/closed/I-fe1b32de932657b986ded6dcee104ef5.md; run `concorde issues archive` in the primary worktree, which moves it there\",\n    \".concorde/issues/I-fff7d5cfbb1556e79fe386bcf07f7165.md holds closed Issue I-fff7d5cfbb1556e79fe386bcf07f7165, whose record belongs at .concorde/issues/closed/I-fff7d5cfbb1556e79fe386bcf07f7165.md; run `concorde issues archive` in the primary worktree, which moves it there\"\n  ],\n  \"notes\": []\n}",
          "evidence": [
            {
              "kind": "log",
              "ref": "/home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log",
              "detail": "sha256:1cbba533132ac0bc4065ae9875396ea19ae8341b759ab196a4f644e19509bb19"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "a configured check only measures the code it runs against"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        }
      ]
    }
  ]
}
```

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T10:19:03Z

Task issues-closed-folder — not delivered yet: one decision needed (escalation 1). The implementation is done and committed on concorde/issues-closed-folder (ef3f84b3).

What is done:
- Open Issue → .concorde/issues/<id>.md, closed → .concorde/issues/closed/<id>.md. close (every closing reason, including the task merge's locked close through dispose) moves the record into closed/ and reopen moves it back, each in the one commit of the disposition naming both paths, author identity and hooks kept; receipt, show, close/reopen outputs give the current path.
- Reads by identity, list, show, appends and duplicate checks find a record in either folder; an Issue committed in both is refused invalid_issue naming both paths. Recovery covers both folders and puts back a move a killed write left (restore + remove the new copy).
- check: misplaced record and Issue recorded twice are errors, each naming the fix. New `concorde issues archive` (command only, no MCP tool): under the merge lock, one commit, moves every misplaced record unchanged and prints {moved, left}.
- Specs (module.issues): req.issues.status-folder, req.issues.archive, amended closed-kept/commit-alone/uncommitted-recovered, 7 new scenarios; receipt contract and typed value concorde-issue-receipt bumped to version 2 (path pattern widened). docs/using-concorde.md updated (both mentions + check/archive). No main-session guidance names the record path, so nothing to escalate there.
- Verified: build --check clean, spec-validation 0 findings, full suite 964 passed.

Decisions I took (details in the decision log): move via file transaction + unlink + `git commit --only` of both paths (no git mv); every write leaves its record in its place (an append to a misplaced open record moves it); a concurrent change of the old path during a move is refused stale_issue and kept; list rows unchanged (no path) since review Operations consume their shape; no new error code (invalid_issue for an Issue in both folders).

The decision needed (escalation 1, `base_records_misplaced`): task-validation r-20261002T101615-task_validation-4b3b2ba6 is blocked only by check.issues.store, which runs on this worktree's own copy of .concorde/issues/: its 199 records (all closed, from the base) sit in the top folder, so the new check reports 199 misplaced records. The brief both forbids this branch to move them and makes misplacement an error, so delivery is impossible as briefed.
Options:
- A (recommended): this branch moves its copy of the 199 closed records into closed/ in one commit of its own (exactly archive's move, bytes unchanged) as a one-time exception. The merge brings exact renames; records closed on primary since the base stay at the top and your post-merge `archive` moves them. Only risk: a reopen of one of those 199 on primary before the merge becomes a rename+modify Git resolves into a misplaced open record in closed/, which archive fixes too.
- B: a misplaced record becomes a check note, not an error (recorded-twice stays an error). Nothing blocks, but the configured check no longer enforces the folder rule.
- C: you git mv the closed records on primary by hand before the merge, I merge primary in and deliver. Keeps the branch rule but is a hand edit of records, and primary's current code can't see those closed records until the merge.

Rendered chain (escalation 1; the check log tail is abridged here, it is whole in the decision log):
- **task-session** task session (task issues-closed-folder): `base_records_misplaced` — (detail, options and recommendation as above)
  Not handled here (decision): The brief explicitly forbids this branch to change .concorde/issues/ and fixes the check's severity as an error; resolving the block means overriding one of those two decisions, which are the main agent's.
  Caused by:
  - **command** Command task-validation r-20261002T101615-task_validation-4b3b2ba6 (workspace issues-closed-folder): `not_deliverable` — 1 blocking finding (readiness in /home/zhenyu/concorde/.concorde/tasks/issues-closed-folder/workspace/runs/r-20261002T101615-task_validation-4b3b2ba6/readiness.json)
    Caused by:
    - **check** check.issues.store: `check_failed` — exit code 1; log .../runs/r-20261002T101615-task_validation-4b3b2ba6/checks/check.issues.store/output.log (sha256:1cbba533…): 199 errors of the form ".concorde/issues/<id>.md holds closed Issue <id>, whose record belongs at .concorde/issues/closed/<id>.md; run `concorde issues archive` in the primary worktree, which moves it there"

Still open: nothing else; once you answer I deliver (or, for C, merge primary in first) and report the delivery commit. After the merge, run `python3 scripts/concorde.py issues archive` once on the primary worktree.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-02T10:19:39Z

Escalation 1 (base_records_misplaced): option A, decided by the main agent. As a one-time exception to the brief, move this branch's copy of the closed records into closed/ in one commit of its own, exactly archive's move with bytes unchanged, then run task-validation and delivery and report. No other task is open, so nobody reopens or writes those records on primary before the merge. After the merge the main agent runs archive once on the primary worktree and then issues check.
- **Escalation 1 answered: option A.** Moved the branch's 199 closed records into
  `.concorde/issues/closed/` with `git mv` in one commit of its own, bytes unchanged; the store
  check on the branch now reports 0 errors and 0 notes.

## Report 2 to the main agent (spec-review quality criteria), 2026-10-02T10:24:14Z

Task issues-closed-folder delivered: delivery commit ec2787c4 (run r-20261002T102158-delivery-221b8232) on concorde/issues-closed-folder, after task-validation r-20261002T101958-task_validation-a9ac1640 ok. Per your answer to escalation 1 (option A), a1fd72fb moves this branch's 199 closed records into .concorde/issues/closed/ with git mv, bytes unchanged, in a commit of its own; the branch's store check now reports 0 errors. The implementation commit is ef3f84b3; its decisions are in my previous report and the decision log. Resolves no Issue. After the merge, run python3 scripts/concorde.py issues archive and issues check once on the primary worktree to move the records closed on primary since the base.

## Closed: merged, 2026-10-02T10:24:27Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit ec2787c49ec72327253ed19a301f281a216a0265 into main and closed it as merged. Nobody answers a report after that.
