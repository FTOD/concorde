# Decision log: bind-skill-links

Goal: Bind the tracked .claude/skills/concorde and .claude/skills/concorde-development links to the root Module's Project files, so no tracked file is bound to no Module

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08): fix every known open Issue before the first full
`project_review`. This task resolves I-04b2460f (decision-needed, medium, on module.concorde):
the tracked links `.claude/skills/concorde` and `.claude/skills/concorde-development` are bound to
no Module.

Decided by the main agent: bind both links to the root Module's realization
`realization.concorde.project-files` (beside `CLAUDE.md` and `.mcp.json`, which they serve: they
expose the built skills to Claude Code in this checkout), and say so in the root's text where
Project files are described. Do not untrack them. Check that project_review's unowned-file rule
and Validation's accounting then count them as bound (a test or a quick check), and run
`registry --write` if the module block changes.

Deliver with `task-validation` then `delivery`; run the full suite once on the final input.

## Task session (2026-10-08)

- Prepared the worktree (init-references, uv sync, npm ci, build): all ok.
- Tried the brief's binding as written: added `.claude/skills/concorde` and
  `.claude/skills/concorde-development` to `realization.concorde.project-files` and ran
  `spec-validation`. Result `failed`: `invalid_field` "symlink paths are forbidden", no location.
  The Protocol forbids it: paths carry no symlink alias (format.md, `CHK.document.path`),
  `CHK.binds.exists` needs an exact entry to be a regular file, and `checked_path` refuses any
  symlink component (spec/contracts.md). Reverted; nothing committed.
- The unlocated error is a separate Spec tooling defect: recorded as Issue
  I-f9acf9f002fb534a8cbd1d077855bd81 (module.spec, obvious-fix, medium). Not fixed here: outside
  this task's Modules.
- Escalating the choice of how to settle I-04b2460f, since every option either reverses the main
  agent's "do not untrack" or changes another Module's promise.

## Escalated to the main agent, 2026-10-08T01:43:51Z

- **task-session** task session (task bind-skill-links): `symlink_cannot_be_bound`
  The brief's decision (bind `.claude/skills/concorde` and `.claude/skills/concorde-development` to realization.concorde.project-files) cannot validate. Both are tracked symbolic links into `generated/skills/`. The Spec Protocol forbids it: paths have no symlink alias (protocol/format.md, CHK.document.path), CHK.binds.exists needs an exact entry to be a regular file, directory entries never bind symlinks (Implementation exclusions), and `checked_path` refuses any symlink component. Tried it: spec-validation failed with `invalid_field` "symlink paths are forbidden". Meanwhile project_review's unowned rule and Validation's req.validation.unbound-paths still count a tracked symlink (Validation even measures it as `symlink:<link text>`), so for a tracked symlink the Issue can never be settled by binding. specs/concorde/development.md (owned by module.concorde) promises the links exist after a build (scenario.concorde.development-skills), not that they are tracked. Options: (A) untrack the links: add them to `.gitignore` and have the development preparation create them (e.g. a step of scripts/development/, the root's Development environment), updating development.md and CLAUDE.md; all within module.concorde, but reverses the brief's "do not untrack". (B) Exclude symbolic links from Validation's accounting and project_review's unowned rule, matching the Protocol's rule that symlinks are never bound; changes module.validation's promise and project_review, outside this task, and a task could then add an unreviewed symlink. (C) Extend the Protocol so an exact entry may bind a symlink as a link (its link text, never followed); Protocol and Spec tooling change, outside this task, largest. (D) Variant of A where `concorde build` creates the links (module.distribution, outside this task).
  Not handled here (decision): Option A reverses an explicit decision of the task brief; options B, C and D change promises of Modules outside this task (validation, project-review, spec, distribution). None is mine to take.
  Options: A: untrack the links; .gitignore them; the development preparation creates them (module.concorde only); B: Validation and project_review exclude symbolic links from the accounting (module.validation, project-review); C: Protocol lets an exact entry bind a symlink as a link (Protocol, module.spec); D: untrack; `concorde build` creates the links (module.distribution)
  Recommendation: A. It keeps every Protocol and Validation rule intact, stays within module.concorde, and matches what development.md already promises (links present after preparation/build, not tracked). The links are derived from generated/ anyway, which is itself not tracked content. If you prefer the build to create them (so a session told only to build finds them), take D and retarget the task to module.distribution.

```json
{
  "level": "task-session",
  "actor": "task session (task bind-skill-links)",
  "code": "symlink_cannot_be_bound",
  "detail": "The brief's decision (bind `.claude/skills/concorde` and `.claude/skills/concorde-development` to realization.concorde.project-files) cannot validate. Both are tracked symbolic links into `generated/skills/`. The Spec Protocol forbids it: paths have no symlink alias (protocol/format.md, CHK.document.path), CHK.binds.exists needs an exact entry to be a regular file, directory entries never bind symlinks (Implementation exclusions), and `checked_path` refuses any symlink component. Tried it: spec-validation failed with `invalid_field` \"symlink paths are forbidden\". Meanwhile project_review's unowned rule and Validation's req.validation.unbound-paths still count a tracked symlink (Validation even measures it as `symlink:<link text>`), so for a tracked symlink the Issue can never be settled by binding. specs/concorde/development.md (owned by module.concorde) promises the links exist after a build (scenario.concorde.development-skills), not that they are tracked. Options: (A) untrack the links: add them to `.gitignore` and have the development preparation create them (e.g. a step of scripts/development/, the root's Development environment), updating development.md and CLAUDE.md; all within module.concorde, but reverses the brief's \"do not untrack\". (B) Exclude symbolic links from Validation's accounting and project_review's unowned rule, matching the Protocol's rule that symlinks are never bound; changes module.validation's promise and project_review, outside this task, and a task could then add an unreviewed symlink. (C) Extend the Protocol so an exact entry may bind a symlink as a link (its link text, never followed); Protocol and Spec tooling change, outside this task, largest. (D) Variant of A where `concorde build` creates the links (module.distribution, outside this task).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Option A reverses an explicit decision of the task brief; options B, C and D change promises of Modules outside this task (validation, project-review, spec, distribution). None is mine to take."
  },
  "options": [
    "A: untrack the links; .gitignore them; the development preparation creates them (module.concorde only)",
    "B: Validation and project_review exclude symbolic links from the accounting (module.validation, project-review)",
    "C: Protocol lets an exact entry bind a symlink as a link (Protocol, module.spec)",
    "D: untrack; `concorde build` creates the links (module.distribution)"
  ],
  "recommendation": "A. It keeps every Protocol and Validation rule intact, stays within module.concorde, and matches what development.md already promises (links present after preparation/build, not tracked). The links are derived from generated/ anyway, which is itself not tracked content. If you prefer the build to create them (so a session told only to build finds them), take D and retarget the task to module.distribution.",
  "causes": []
}
```

## Report 1 to the main agent (concorde-d4), 2026-10-08T01:43:58Z

bind-skill-links: blocked on one decision (escalation 1); nothing committed, worktree clean.

The brief's binding of the two tracked skill links to realization.concorde.project-files cannot validate: the Spec Protocol forbids symlink paths in entries (format.md, CHK.document.path, CHK.binds.exists; checked_path refuses symlinks). I tried it: spec-validation failed with `invalid_field` "symlink paths are forbidden". Validation's accounting and project_review's unowned rule still count tracked symlinks, so binding can never settle I-04b2460f while the links stay tracked.

Escalation 1 (symlink_cannot_be_bound), options:
A: untrack the links, .gitignore them, the development preparation creates them (module.concorde only; reverses the brief's "do not untrack") — my recommendation.
B: Validation and project_review exclude symlinks from the accounting (module.validation, project-review).
C: Protocol lets an exact entry bind a symlink as a link (Protocol, module.spec).
D: untrack; `concorde build` creates the links (module.distribution).

Rendered chain:
- **task-session** task session (task bind-skill-links): `symlink_cannot_be_bound` — see escalation 1 in the decision log for the full detail, options and recommendation.

Decisions I made: reverted my trial edit rather than commit a failing Spec.

Also found and recorded (not fixed, outside this task's Modules): Issue I-f9acf9f002fb534a8cbd1d077855bd81 (module.spec, obvious-fix, medium) — a symlink realization entry makes spec-validation abort with an unlocated `invalid_field` error instead of reporting CHK.binds.exists at the entry (expand_entry calls checked_path unguarded).

Open: the choice above. With A, I would add the links to .gitignore, add link creation to the development preparation under scripts/development/, update development.md and CLAUDE.md, and resolve I-04b2460f.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-08T01:44:19Z

Escalation 1 (symlink_cannot_be_bound), decided by the main agent: option A. My brief's binding was my own decision, not the developer's, and the Protocol rightly forbids symlink entries. Untrack .claude/skills/concorde and .claude/skills/concorde-development (git rm --cached, keep them on disk), add them to .gitignore, have the development preparation create them (the first preparation step a task session runs, scripts/development/init-references.py or a script it already runs; idempotent, never overwriting a real directory), and update development.md and CLAUDE.md to say where the links come from. Then validate, deliver and resolve I-04b2460f. I-f9acf9f0 (module.spec) goes to task architecture-review-identity, which already works on module.spec.

## Task session, after the answer to report 1 (2026-10-08)

Carried out option A. Decisions taken without the developer:
- Link creation lives in `scripts/development/init-references.py` (the first preparation step, already
  in every task session's preparation and in CI before the tests), not in a new script, so the
  preparation list in the skill and CLAUDE.md keeps its four commands. It runs before the submodule
  work, so it runs even with no submodule declared.
- A link that points elsewhere is replaced (it is ours, not content); a real file or directory in its
  place is left untouched with a message on stderr, and the run still exits 0, so that a developer's
  own skill folder never breaks the preparation. `--check` reports the links and counts each
  unlinked one toward its exit 1.
- Link target is relative (`../../generated/skills/<name>`), as the tracked links were.
- Spec: development.md's skills paragraph says where the links come from;
  scenario.concorde.development-skills now says "after its preparation" and "Git tracks neither
  link"; new scenario.concorde.skill-links-prepared, verified by
  test_skill_links_are_made_and_a_real_directory_is_left. The init-references fixture repo now
  ignores the links as this checkout does, so its clean-status assertion still holds.
- Verified the unowned rule: `findings.unowned_paths` on the task branch returns [].
- Consequence for the merge: the merge deletes the two tracked links from the primary worktree (and
  from any worktree that later merges main); `python3 scripts/development/init-references.py`
  there makes them again.
- task-validation r-20261008T014723-task_validation-e0ad5201: blocked, 2 findings `unbound` on the
  two links. Cause: the links stayed on disk (ignored), and Validation measures a path deleted from
  the branch by its worktree content, so it "still exists". Recorded as Issue
  I-e8da75702b945d3ab7c83511efba298e (module.validation, decision-needed, medium); not fixed here.
  Workaround within the task: removed both links from this worktree's disk before validating and
  delivering; after delivery I make them again with init-references.py (then ignored and unchanged
  against the new base). Consequence: a task whose base still tracks the links, which merges main
  and then re-runs init-references.py, meets the same block until that Issue is settled.
- Because the configured check check.concorde.tests runs test_development_skills, which required
  the links on disk, the test now checks the initializer's link target (new `skill_target`) and that
  Git ignores and does not track the links, independently of the worktree's preparation; the link
  making itself is covered by scenario.concorde.skill-links-prepared.

## Report 2 to the main agent (concorde-d4), 2026-10-08T01:53:24Z

bind-skill-links report 2: delivered as f90b5d96172bfdac1943fc019da99a59556929ef on concorde/bind-skill-links (delivery run r-20261008T015210-delivery-74141a16; task-validation r-20261008T015128-task_validation-e5a31019 ready, no blocking finding). Resolves I-04b2460f56e15e09a2253c1831325d4a (in the task's resolves).

What changed (option A, as answered):
- .claude/skills/concorde and .claude/skills/concorde-development untracked and ignored (.gitignore).
- scripts/development/init-references.py, the first preparation step, now makes them before the submodule work: creates a missing link, replaces a link pointing elsewhere, leaves a real file or directory untouched with a message on stderr (exit stays 0); --check reports them and counts each unlinked one toward exit 1.
- development.md: skills paragraph says where the links come from; scenario.concorde.development-skills now "after its preparation" and "Git tracks neither link"; new scenario.concorde.skill-links-prepared with its test. CLAUDE.md and prompts/development/skill.md say the initializer makes the links.
- Verified: project_review's unowned rule (findings.unowned_paths) returns [] on the branch; build --check, spec-validation and the full suite (1286 passed, 5 skipped) pass on the final input.

Decisions I made (all in the decision log): link creation in init-references.py rather than a new script, so the preparation keeps its four commands; a real directory is left with a warning, not a failure; test_development_skills now checks the initializer's link target (new skill_target) and that Git ignores and does not track the links, instead of requiring the links on this worktree's disk, because check.concorde.tests runs it and Validation needs the links absent (next point).

Non-ok result: task-validation r-20261008T014723-task_validation-e0ad5201 was blocked with `unbound` on both links, because the ignored links were still on disk and Validation measures a path the branch deletes by its worktree content. I removed them from this worktree's disk for validation and delivery (they stay absent here). Recorded as Issue I-e8da75702b945d3ab7c83511efba298e (module.validation, decision-needed, medium), with options and my recommendation (measure such a path as deleted, as Delivery commits it).

For you at the merge: the merge deletes the two tracked links from the primary worktree's disk. Run `python3 scripts/development/init-references.py` there afterwards to make them again, or main-agent sessions there lose the skills. Any open task whose base still tracks the links meets the I-e8da7570 block if it merges main and then re-runs the initializer, until that Issue is settled; removing the links from its disk before validating works around it.

Open: nothing for this task. I-f9acf9f0 (module.spec) was left to architecture-review-identity as you said.

## Closed: merged, 2026-10-08T01:53:40Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit f90b5d96172bfdac1943fc019da99a59556929ef into main and closed it as merged. Nobody answers a report after that.
