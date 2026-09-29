# Decision log: drop-pending-entries

Goal: Remove pending realization entries from the Spec Protocol and Concorde: the task session prepares the workers' environment, creating each new file and binding it to its Module before the worker that fills it runs

## Brief (main agent, 2026-09-30)

### Developer's decision
Asked whether a grant should mark which of its entries are pending (Spec core's entry said this was
"not settled"), the developer said no marker is needed and that a new file should be created by the
task session, not by a worker. Decision: **the task session prepares the environment for workers**.
This reverses the developer's earlier Protocol 3.0 design (pending entries declared by the plan
phase, created by `implement`, confirmed and cleared by delivery).

- Remove `pending` realization entries from the Spec Protocol (`protocol/model.md`, `model.yaml`,
  `format.md`, `boundaries.md`, `context.md`, `relations.md`, `checks.md`, templates, migration
  notes; version bump; `protocol-manifest --write --bind-project`) and from Concorde. A realization
  binds only files that exist (directory entries ending in `/` still let a worker create files
  inside a bound directory).
- When work needs a new file outside a bound directory, the task session creates it — with a
  minimal valid skeleton where an empty file would be invalid for its format — and binds it to the
  right Module as an ordinary entry, before it launches the worker that fills it (or fills it
  itself). Say this in the task session's guidance (`prompts/main-session/task-session.md`), the
  main agent's skill where relevant (`prompts/main-session/skill.md`) and Task sessions' Spec.
- `specify` no longer declares files for later creation; `understand`'s plan no longer lists
  pending files (it may still name the files a change will need, for the task session to create);
  `implement` writes only bound files; Validation/Delivery lose the pending-confirmation step
  (`src/concorde/validation/confirmations.py`, delivery's confirmation, related findings); grants,
  Spec MCP answers, scaffold/adoption output, Views rendering and the `execution/context.py`
  error advice ("run specify to declare the path as a pending file") change accordingly — the
  advice should now say the task level binds the path.
- Remove Spec core's "whether it should is not settled" sentence (the question is settled).
- Also: `prompts/main-session/skill.md:94` and `prompts/main-session/task-session.md:32` say
  `delivery` "commits the result on the task branch"; make them name the delivery commit (only it
  marks the task delivered; the task level may commit verified steps).

### Careful
Many "pending" occurrences are unrelated (workflow pending decision points, pending escalations,
Issue text, `workflows` contracts). Change only realization-pending. The project's own metadata
(`*.md.json`) may hold `"pending": []` arrays — remove the field everywhere. Grep `tests/` too.
No backward compatibility (rapid-iteration rule): no migration shim for old `pending` fields, just
make the validator reject or ignore them as the new Protocol says (decide, log).

### Left to the session
Exact wording, the Protocol version number, how checks change, test changes, and which of the
bound Modules actually need edits (log any Module you did not need). Stop every background command
you started before task-validation and delivery. Report a short summary per Module.

## Task session (2026-09-30)

Decisions taken without the developer:

- **Protocol version 16.0.0** (major): removing the `pending` field makes Protocol-15 metadata that
  carries it invalid. Migration notes gain a "Version 16" section; README, principles, model.yaml,
  manifest and `PROTOCOL_VERSION` follow; "Protocol 15" in code docstrings/messages became 16.
- **Old `pending` fields are rejected, not ignored**: the realization record's closed shape no
  longer allows `pending`, so it fails `CHK.document.schema` as an unknown field (new scenario
  `scenario.spec.pending-rejected`). `CHK.binds.pending-subset` is removed; `CHK.binds.exists`
  applies to every entry and gained a remediation ("create the file before binding it, or remove
  the entry"). The project's own 19 metadata files only had `"pending": []`, now removed.
- **Protocol wording for new files**: a new file outside every bound directory is created and bound
  together, with the least content its format needs, "by the work that prepares the task" (the
  Protocol does not name Concorde's task session); `implement` may still create files below bound
  directories.
- **Validation**: `confirmations` (readiness field, `sort_findings` step, `validation/confirmations.py`)
  removed; steps renumbered 1–8; requirements `req.validation.confirmations`, `confirm-exact`,
  `confirm-digest`, `confirm-valid` and their scenarios removed. Readiness contract version 5 → 6.
  Spec core's general `document_overrides` API is kept (still a documented Spec core API).
- **Delivery**: step 7 now only records the index (`keep_index`); `confirmations_refused` and undo's
  `metadata_unrestored` gone; output loses `confirmed` (contract version 4 → 5);
  `scenario.delivery.confirmations` removed; `req.delivery.exact-content` now says the commit holds
  exactly the uncommitted changes the readiness examined.
- **Workers**: no pre-creation of `rw` paths and no removal of empty ones; run record loses
  `pending_created`/`pending_removed`; worker-run-trace typed value and contract version 1 → 2;
  `req.workers.pending-cleanup` replaced by `req.workers.no-precreation`, scenario
  `workers.pending-precreated` by `workers.no-precreation`.
- **implement**: no `remove_unused`/`clear_pending`; code change loses `pending_cleared` (contract
  2 → 3); new `req.implementation.no-spec-edits` replaces `pending-precreated`/`pending-markers`;
  scenarios `pending-file`/`unused-pending` replaced by `implementation.prepared-file`.
- **specify**: Spec change loses `pending_declared` (contract 2 → 3);
  `req.specification.declare-not-create` becomes `no-implementation-files`; scenario
  `declare-pending` becomes `specification.missing-entry` (binding a missing file is a new
  `CHK.binds.exists` error, run `blocked`). The worker prompt tells it never to bind a file that
  does not exist and to name a needed new file in its summary.
- **understand**: the plan's `pending` (module, realization, path, reason) becomes `new_files`
  (module, path, reason) — the files the change needs, for the task session to create and bind;
  assessment contract 3 → 4.
- **Denial and error advice**: the write hook / pi policy reason and the `audit_violation` advice now
  say the task level creates the file and binds it to a Module (advice: "the task level's
  decision").
- **Guidance**: task-session guidance gains "Prepare the workers' environment"; the main agent's
  skill says the task session prepares the workers' environment; both now say `delivery` creates
  the delivery commit, which alone marks the task delivered. New
  `req.main-session.task-session-prepares-workers` with scenario and a guidance test; Task sessions'
  entry says the same. Spec core's "not settled" sentence replaced.
- **Glossary**: definitions of Delivery commit, Readiness and Spec change no longer mention
  confirmations/pending entries.
- **Modules needing no edit**: module.views (Spec; only the docsite parser code changed), 
  module.scaffold (Spec; only code dropped the pending filter), module.adoption (nothing),
  module.concorde (root entry unchanged; only its metadata's empty `pending` arrays removed).
- Test updates were done by a helper subagent inside this session, limited to `tests/`.
- Verification: full suite 782 passed / 1 failed / 4 skipped; the one failure
  (`test_docsite_scaffold::test_changed_package_bytes_are_rejected_as_stale_004`, `shutil.Error`
  Permission denied on `docsite/.claude/*`) was caused by sandbox placeholder files left by a
  shell command run with `docsite/` as cwd, not by the change; after removing the leftover empty
  directory the test file passes (21 passed). `spec-validation` success with 0 findings;
  `task-validation` ready, every check passed; `delivery` ok, delivery commit 35a7a677.

## Main agent on the session's report (2026-09-30)

Accepted: Protocol 16.0.0, rejection of leftover `pending` fields (rapid-iteration rule, no shim),
contract version bumps, and the Protocol not naming Concorde's task session. The one full-suite
failure (test_docsite_scaffold, Permission denied on sandbox placeholders under docsite/.claude
from a command run inside docsite/) is an environment artefact; the test file passed after the
leftover directory was removed. Merging.

## Closed: merged, 2026-09-29T19:37:38Z
