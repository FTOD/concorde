# Decision log: fix-views

Goal: Fix every open Issue of Views found by the first full project_review, critical first (concurrent scaffold overwrite, publication cleanup deleting Spec sources, backup cleanup corrupting the site)

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) to fix the project's known open Issues. This task resolves every
open Issue owned by its Modules (listed in the task record's `resolves`), found by the first full
project_review, r-20261008T024839-project_review-a7857ff6 (unbound). Read each with
`concorde issues show`; the review's panel and code-review reports are in
`.concorde/unbound/r-20261008T024839-project_review-a7857ff6/` of the primary worktree.

How to handle them, by tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest while
  waiting. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it turns out wrong; then leave it open and say why in the log.
- Fix by **severity**, critical and high first.
- An Issue that turns out not to hold, or that is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix that needs a change outside the task's Modules: escalate it rather than widening the task,
  unless it is a small mechanical follow-on (a link, a test fixture).

Other tasks running in parallel: worker-transient-retry (workers, project-review, method),
main-rename-hook (main-session, coordination, tasks) and the other Issue-fixing tasks of today
(views, dogfood/e2e, task-session, operations/commands, delivery). Deliver with `task-validation`
then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-08T06:21:14Z

- **task-session** task session (task fix-views): `scaffold_concurrency_mechanism`
  Issue I-dc13ba09568359dc996712f45d43516a (high, decision-needed), with the critical preferred-fix I-c920fa478c6d5f6c9bf3734c3aa57066 depending on it. Views promises (req.views.scaffold-creation-only, scenario.views.scaffold-concurrent-create) that apply never replaces a file, even one another process creates during apply. Apply goes through Spec core's apply_files (src/concorde/spec/changes.py, owned by module.spec), which checks absence and then os.replace()s a temp file over the destination: a file created in that window is overwritten, and its rollback unlinks the destination even if it is no longer the file it wrote. Kernel and Spec core contracts say their transaction overwrites a concurrent change. So the promise is false today.
  Not handled here (decision): Choosing the mechanism either changes another Module (module.spec, outside this task) or narrows what Views promises to its users; both are beyond the task session's authority.
  Options: A: Views creates the scaffold files itself, without Spec core's transaction: each file is written to a temp file and published with os.link (create-if-absent, fails if the destination exists); rollback unlinks only paths whose (device, inode) is still the file it created. Views' Specs say so; Spec core is unchanged. Residual race: a file replaced between the identity check and the unlink during rollback, which the Spec states.; B: Add a create-only mode to Spec core's apply_files (same link-based publication and identity-checked rollback), used by the scaffold. Needs a module.spec change in another task or a widened task.; C: Narrow the promise: apply requires the caller to own the destinations exclusively during apply; scenario.views.scaffold-concurrent-create is revised to a detected-before-write case only.
  Recommendation: A: it makes the promise true now within module.views, keeps Spec core's transaction contract as it is, and is a small, testable change; I would then fix I-c920 with it and add the regression test that creates the destination just before publication.

```json
{
  "level": "task-session",
  "actor": "task session (task fix-views)",
  "code": "scaffold_concurrency_mechanism",
  "detail": "Issue I-dc13ba09568359dc996712f45d43516a (high, decision-needed), with the critical preferred-fix I-c920fa478c6d5f6c9bf3734c3aa57066 depending on it. Views promises (req.views.scaffold-creation-only, scenario.views.scaffold-concurrent-create) that apply never replaces a file, even one another process creates during apply. Apply goes through Spec core's apply_files (src/concorde/spec/changes.py, owned by module.spec), which checks absence and then os.replace()s a temp file over the destination: a file created in that window is overwritten, and its rollback unlinks the destination even if it is no longer the file it wrote. Kernel and Spec core contracts say their transaction overwrites a concurrent change. So the promise is false today.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing the mechanism either changes another Module (module.spec, outside this task) or narrows what Views promises to its users; both are beyond the task session's authority."
  },
  "options": [
    "A: Views creates the scaffold files itself, without Spec core's transaction: each file is written to a temp file and published with os.link (create-if-absent, fails if the destination exists); rollback unlinks only paths whose (device, inode) is still the file it created. Views' Specs say so; Spec core is unchanged. Residual race: a file replaced between the identity check and the unlink during rollback, which the Spec states.",
    "B: Add a create-only mode to Spec core's apply_files (same link-based publication and identity-checked rollback), used by the scaffold. Needs a module.spec change in another task or a widened task.",
    "C: Narrow the promise: apply requires the caller to own the destinations exclusively during apply; scenario.views.scaffold-concurrent-create is revised to a detected-before-write case only."
  ],
  "recommendation": "A: it makes the promise true now within module.views, keeps Spec core's transaction contract as it is, and is a small, testable change; I would then fix I-c920 with it and add the regression test that creates the destination just before publication.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:21:14Z

- **task-session** task session (task fix-views): `preview_isolation_scope`
  Issue I-3673fa07fa125b4e82d88013628f0b55 (high, decision-needed). req.views.production-preview-isolation says a production build SHALL NOT clear or overwrite the preview's generated files, but both modes stage into the same docsite/.generated/{content,static,specs-sidebar.json,scoped-materialization.json}; only Docusaurus's generated directories (.docusaurus vs .generated/docusaurus-production) are separate. A build beside a running preview deletes and rewrites the preview's staged pages (from the same sources, so a running preview briefly sees missing pages and hot-reloads).
  Not handled here (decision): Which guarantee Views gives to users of npm run start/build is a promise change of the Module.
  Options: A: Narrow the requirement to Docusaurus's generated directories and document beside the commands that both modes share the staged pages, so a build beside a preview rewrites them from the current sources (the preview may reload or briefly fail while staging runs).; B: Full isolation: each mode stages into its own directory (e.g. .generated/preview/ and .generated/production/), with the Docusaurus config, sidebar and staging record chosen by mode; the requirement stays as it is and becomes true.
  Recommendation: B: the code change is path plumbing in materialize, prepare-publication, docusaurus.config.ts, sidebars.specs.ts and the content plugin, and it makes the existing promise hold instead of weakening it; A is acceptable if you prefer the smaller change.

```json
{
  "level": "task-session",
  "actor": "task session (task fix-views)",
  "code": "preview_isolation_scope",
  "detail": "Issue I-3673fa07fa125b4e82d88013628f0b55 (high, decision-needed). req.views.production-preview-isolation says a production build SHALL NOT clear or overwrite the preview's generated files, but both modes stage into the same docsite/.generated/{content,static,specs-sidebar.json,scoped-materialization.json}; only Docusaurus's generated directories (.docusaurus vs .generated/docusaurus-production) are separate. A build beside a running preview deletes and rewrites the preview's staged pages (from the same sources, so a running preview briefly sees missing pages and hot-reloads).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Which guarantee Views gives to users of npm run start/build is a promise change of the Module."
  },
  "options": [
    "A: Narrow the requirement to Docusaurus's generated directories and document beside the commands that both modes share the staged pages, so a build beside a preview rewrites them from the current sources (the preview may reload or briefly fail while staging runs).",
    "B: Full isolation: each mode stages into its own directory (e.g. .generated/preview/ and .generated/production/), with the Docusaurus config, sidebar and staging record chosen by mode; the requirement stays as it is and becomes true."
  ],
  "recommendation": "B: the code change is path plumbing in materialize, prepare-publication, docusaurus.config.ts, sidebars.specs.ts and the content plugin, and it makes the existing promise hold instead of weakening it; A is acceptable if you prefer the smaller change.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:21:14Z

- **task-session** task session (task fix-views): `user_docs_root_page_ambiguity`
  Issue I-8aa56cf196225e59beb091d3d0edfe13 (medium, decision-needed). The site-identity contract admits user documents whose directory contains a root page README.md, README.mdx, index.md or index.mdx, but does not say what happens when several exist. Today the code (user-docs.ts) only checks that one exists; Docusaurus then maps each to the route / and, since onDuplicateRoutes is 'throw', the build fails with a generic duplicate-route error not naming userDocs.
  Not handled here (decision): Exactly-one admission and a precedence rule are different promises to site authors.
  Options: A: Exactly one root page: admission refuses a directory with more than one, naming userDocs and every candidate (matches today's effective outcome, with a clear diagnostic).; B: Precedence (e.g. README.md > README.mdx > index.md > index.mdx), excluding the others from publication.
  Recommendation: A: it keeps the outcome the site already has, adds a precise refusal and scenario, and avoids silently unpublished pages.

```json
{
  "level": "task-session",
  "actor": "task session (task fix-views)",
  "code": "user_docs_root_page_ambiguity",
  "detail": "Issue I-8aa56cf196225e59beb091d3d0edfe13 (medium, decision-needed). The site-identity contract admits user documents whose directory contains a root page README.md, README.mdx, index.md or index.mdx, but does not say what happens when several exist. Today the code (user-docs.ts) only checks that one exists; Docusaurus then maps each to the route / and, since onDuplicateRoutes is 'throw', the build fails with a generic duplicate-route error not naming userDocs.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Exactly-one admission and a precedence rule are different promises to site authors."
  },
  "options": [
    "A: Exactly one root page: admission refuses a directory with more than one, naming userDocs and every candidate (matches today's effective outcome, with a clear diagnostic).",
    "B: Precedence (e.g. README.md > README.mdx > index.md > index.mdx), excluding the others from publication."
  ],
  "recommendation": "A: it keeps the outcome the site already has, adds a precise refusal and scenario, and avoids silently unpublished pages.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:21:14Z

- **task-session** task session (task fix-views): `diagram_source_exclusivity`
  Issue I-98ce7a93f92850b9ac7c1df230943ef1 (medium, decision-needed, spec-challenge). req.views.diagram-source-identity says a diagram's image is derived only from the fence and the house style and changes only when its document or the house style changes, while req.views.diagram-look requires styling by what each shape resolves to (the page's Module, a descendant, another Module, a concept, a realization), which docsite/plugins/scoped-content/diagrams.ts resolves against the registry, metadata and glossary. Changing another Module's composition can thus change a diagram's look with its document unchanged.
  Not handled here (decision): It changes the wording of a Views requirement (what the promise covers); the code stays as it is.
  Options: A: Reword req.views.diagram-source-identity: the fence is the only source of a diagram's shapes, nesting, labels and edges; their look comes from the house style applied to what each label resolves to in the loaded registry, metadata and glossary, so the image changes only when its fence, the house style or that resolution changes.; B: Drop semantic styling (req.views.diagram-look) so the fence alone decides the image.
  Recommendation: A: it keeps semantic styling, which the Protocol's shared visual language relies on, and states the real dependency.

```json
{
  "level": "task-session",
  "actor": "task session (task fix-views)",
  "code": "diagram_source_exclusivity",
  "detail": "Issue I-98ce7a93f92850b9ac7c1df230943ef1 (medium, decision-needed, spec-challenge). req.views.diagram-source-identity says a diagram's image is derived only from the fence and the house style and changes only when its document or the house style changes, while req.views.diagram-look requires styling by what each shape resolves to (the page's Module, a descendant, another Module, a concept, a realization), which docsite/plugins/scoped-content/diagrams.ts resolves against the registry, metadata and glossary. Changing another Module's composition can thus change a diagram's look with its document unchanged.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "It changes the wording of a Views requirement (what the promise covers); the code stays as it is."
  },
  "options": [
    "A: Reword req.views.diagram-source-identity: the fence is the only source of a diagram's shapes, nesting, labels and edges; their look comes from the house style applied to what each label resolves to in the loaded registry, metadata and glossary, so the image changes only when its fence, the house style or that resolution changes.",
    "B: Drop semantic styling (req.views.diagram-look) so the fence alone decides the image."
  ],
  "recommendation": "A: it keeps semantic styling, which the Protocol's shared visual language relies on, and states the real dependency.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T06:21:26Z

fix-views report 1 — early escalation of the four decision-needed Issues (escalations 1-4). I am continuing with every other Issue meanwhile; the critical I-c920 (scaffold overwrite) waits on escalation 1.

1. scaffold_concurrency_mechanism — I-dc13ba09 (high) + blocks critical I-c920fa47. Apply goes through Spec core's apply_files, which os.replace()s over a destination created after its absence check, so "never replaces" is false. Options: A) Views publishes each scaffold file itself with os.link (create-if-absent) and rolls back only files whose (device, inode) it created — within module.views, Spec core unchanged; B) add a create-only mode to Spec core's apply_files (module.spec, outside this task); C) narrow the promise to exclusive caller access. Recommendation: A.

2. preview_isolation_scope — I-3673fa07 (high). Both modes stage into the same docsite/.generated/ content; only Docusaurus caches are separate, so a build beside a preview rewrites the preview's staged pages. Options: A) narrow the requirement to Docusaurus's generated directories and document the shared staging; B) stage each mode into its own directory so the requirement holds. Recommendation: B (path plumbing only); A acceptable.

3. user_docs_root_page_ambiguity — I-8aa56cf1 (medium). Several root pages (README.md + index.md...) are not specified; today Docusaurus fails on the duplicate route with a generic error. Options: A) exactly one root page, admission refuses naming userDocs and every candidate; B) precedence order. Recommendation: A.

4. diagram_source_exclusivity — I-98ce7a93 (medium, spec-challenge). "Image derived only from the fence and house style" contradicts semantic styling by what labels resolve to in the registry/glossary. Options: A) reword: the fence is the only source of shapes, nesting, labels and edges; their look comes from the house style applied to what labels resolve to, so the image changes with the fence, house style or that resolution; B) drop semantic styling. Recommendation: A.

It carries escalation(s) 1, 2, 3, 4.

## Answer to report(s) 1 of the task session, 2026-10-08T06:21:59Z

Escalations 1-4 (main agent): 1 A — Views publishes each scaffold file itself with os.link create-if-absent and rolls back only files whose (device, inode) it created; Spec core unchanged; then fix critical I-c920fa47 with it. 2 B — stage each mode into its own directory so the isolation requirement holds. 3 A — exactly one root page; admission refuses naming userDocs and every candidate. 4 A — reword: the fence is the only source of shapes, nesting, labels and edges; their look comes from the house style applied to what labels resolve to; keep semantic styling.

## Task session decisions (2026-10-08)

- **I-e7826df5 (critical, backup cleanup)**: chose to move the backup removal out of the promotion's rollback. A failed removal now keeps the promoted site, writes a warning naming the backup to stderr and lets the build succeed (the next build deletes the leftover backup first). Reason: a halfway recursive deletion has already destroyed part of the backup, so restoring it would replace a complete site with an incomplete one; failing the build after a good promotion would misreport a published site as failed. New requirement `req.views.promoted-site-kept`, scenario `scenario.views.backup-cleanup-failure`, with a real-filesystem test that makes the removal fail after deleting part of the backup.
- **I-a45fefab (high, first publication / pre-backup failure)**: the code already skipped the backup when no destination exists and restored only a backup it made; the Spec did not say so. Rewrote Promotion in pipeline.md as numbered steps with first publication and each failure point, extended `req.views.promote-atomic`, added `scenario.views.first-publication` and a test.
- **I-eff31701 (critical, cleanup deleting sources)**: loading now refuses (before any command clears anything) every source — configuration, registry, both document members, glossary, site identity — that lies lexically or physically inside `docsite/.generated/`, `docsite/build/` or `docsite/.docusaurus/`, and an output directory that is a symbolic link. Placed in `loadScopedRegistry`, since every command (start, validate, build, the Docusaurus config) loads before it clears. New `req.views.outputs-disjoint`, `scenario.views.outputs-disjoint`, tests in `docsite/tests/unit/publication-outputs.test.ts`.
- **I-3673fa07 (main agent answer: B)**: each mode stages into its own directory, `docsite/.generated/preview/` and `docsite/.generated/production/`; the Docusaurus process learns its mode from `CONCORDE_PUBLICATION_MODE`. `sidebars.specs.ts` now reads the mode's sidebar JSON at run time instead of a static import, so it no longer needs a staged file to type-check. The old shared `.generated/{content,static}` paths are simply no longer written; nothing removes leftovers from earlier versions (they are ignored output).
- **I-073de3b4 (UTF-8 diagnostics)**: `safeRead` wraps the decoder's error as `Source is not valid UTF-8: <path>` with the cause kept; tests assert the path for a reading and a metadata file.
- **I-17779 (exclusive build)**: stated beside `npm run build` in the entry and as "One build at a time" in the build-command contract (new anchor `build-commands`).
- **I-5116d71f (suggestion, vertical lists)**: its literal repair (a vertical list inside the GIVEN step) is impossible, since the Protocol allows only GIVEN/WHEN/THEN/AND/BUT steps as list items of a scenario (spec-validation `CHK.scenario.steps`). Applied it adapted: the two refusal scenarios now point to the pipeline's loading list, which already lists every refused input one per item, and name a few examples in prose. This also clears the two sentence-length warnings.
- **I-588f5769 (single sidebar)**: the staging scenario now says the one Module documents sidebar, displayed but unlisted on implementation pages.
- **I-c920fa47 + I-dc13ba09 (main agent answer: A)**: new `src/concorde/spec/views/creation.py`. Each scaffold file is written to a temporary file beside its destination, fsynced, and `os.link`ed into place (fails on any existing entry, even a dangling link); on a filesystem refusing hard links (EPERM/ENOTSUP/EOPNOTSUPP/EXDEV/EMLINK) it falls back to `O_CREAT|O_EXCL`, equally exclusive but showing the file before its last byte. Rollback removes a created file only while its (st_dev, st_ino) is still the one fstat gave at creation; the residual window (a replacement between that lstat and the unlink) is stated in the entry. Spec core's `apply_files` is no longer used by the scaffold and is unchanged; the Views entry, contracts' Apply and `scenario.views.scaffold-concurrent-create` now describe this, and the relation `realization.views.scaffold` → `module.spec` changed from "writes files through" to "reads the root title and result shape from". The concurrency regression creates the destination inside the `os.link` call, just before the publication.
- **I-a0acb2fe (apply without readable configuration)**: `apply_docsite` now runs propose's initialization check (`CONCORDE-DOCSITE-001`) first; new `scenario.views.scaffold-uninitialized` and a test with the configuration removed and corrupted.
- **I-b51fa600 (select provider contracts)**: Views now `includes` the documents `document.spec.contracts` and `document.spec.errors` (whole documents, since the envelope, error record, safe paths and configuration are spread over several sections) and its entry links the envelope and error record. The transaction interface the Issue also named is no longer used by Views after I-c920.
- **I-7392c394 (Distribution's package layout)**: Views now `uses` module.distribution relying on `req.distribution.installer-docsite-template`, explained at `#uses-distribution` as a data and installation contract, not an import; the "Around it" diagram gains `views -> distribution`. The descriptor's `docsite` package root has no identity in Distribution's Specs, so it is named in prose only (`CHK.relies-on.linked` forbids linking an unlisted node). `.concorde/specs.json` refreshed with `registry --write`.
- **I-170adc72 (indirect directory links)**: `refuseRegisteredSpecs` now follows every symbolic link to a directory and walks each reached directory once (a visited set of real paths, so cycles end); tests for customDocs and userDocs with `guides/shared -> elsewhere`, `elsewhere/spec.md -> registered source`.
- **I-d95bcf63 (extension bypass)**: two checks. (1) A docs plugin among `custom-docs/index.ts`'s `plugins` (named `@docusaurus/plugin-content-docs`, `docusaurus-plugin-content-docs` or `content-docs`; path defaulting to Docusaurus's `docs`) gets the collections' admission. (2) postBuild refuses any rendered route under `/specs` that is neither a registered page's nor the glossary's. Function-valued plugins cannot be inspected, so (2) is the guard for them. Verified on Concorde's own site build before delivery (see below).
- **I-0d02521d (template inventory)**: split the exclusions into components excluded anywhere (`node_modules`, `build`, `.generated`, `.docusaurus`, `coverage`) and root subtrees (`tests/repository`, `custom-docs`), as the contract already says; fixture proves nested `plugins/custom-docs/helper.ts` and `plugins/tests/repository/…` stay in the inventory. No Spec change.
- **I-f3d65277 (heading levels)**: Spec core (`syntax.py`) and the publisher's loader take definition headings at levels 1–6, while the renderer anchored only 2–5. Chose to anchor every level the loader admits (renderer regex `#{1,6}`), keeping publisher and validator in agreement, rather than narrowing loading to the Protocol's "level-2 to level-5" wording (that would make the publisher refuse links the validator accepts). Pipeline text updated; test covers levels 1–6. Note for later: the Protocol says scenarios are level-2 to level-5 headings while Spec core accepts 1–6; that discrepancy is Spec core's/the Protocol's, not this task's.
- **I-d1f31171 (multiline code spans)**: code spans are matched per block of text (a blank or fenced line ends a block) instead of per line; tests for a wrapped span, a doubled-backtick span and spans that must not cross a blank line or a fence.
- **I-8aa56cf1 (main agent answer: A)**: user documents admission refuses more than one root page, naming every one.
- **I-98ce7a93 (main agent answer: A)**: `req.views.diagram-source-identity` reworded: the fence is the only source of shapes, nesting, labels and edges; the look comes from the house style applied to what labels resolve to.
- **I-48d3ddee**: the entry now explains the global `specs/` prefix rule, that registering one document outside `specs/` changes every route, and that a move changes a route only when the rule gives another.
- **I-a1717b2a**: the entry now says the freshness check covers exactly the source digest's inputs and not user-document or custom-doc contents (no contract change).
- **I-c2ca5be6**: the pipeline now defines the exact serialization (compact `JSON.stringify`, escaping, UTF-8, no final newline) with a fixed example and its digest; `sourceDigestOf` is exported and a unit test checks the example, plus non-ASCII paths.
- **I-b56f6cc9 (suggestion)**: applied — both preview requirements name the preview supervisor as the actor.
- **I-54743dd4 (test fixtures)**: new `tests/concorde/views/built_package.py`: the scaffold tests install from this checkout when its build is fresh, else from a copy built once per process in a scratch directory (under a second). Reproduced the 30 failures in an unbuilt copy and confirmed they pass with the helper. `run-checks.py` now runs the whole `tests/concorde/views` directory, so `test_scaffold_apply_outcomes.py` and any later file are included.
- Correction to the entries above: the template-inventory Issue is I-0d02521678d0526ba2b3b0f5cc01b029 (not "I-0d02521d") and the heading-level Issue is I-f3d6527b43985c58a3b8528116751840 (not "I-f3d65277").
- Real `npm run build` of Concorde's own site succeeded on commit f4d49fff's parent sources (per-mode staging, /specs route check, output disjointness): 'Verified site promoted'. Two earlier attempts failed with 'Spec source changed during publication' because this session edited Specs while they ran — the freshness check working as specified, not a defect.

## Report 2 to the main agent (Review流程), 2026-10-08T07:24:55Z

fix-views report 2 — delivered. Delivery commit b2ab5708 (run r-20261008T071542-delivery-f60db84b) on concorde/fix-views; task-validation r-20261008T070655-task_validation-876cc52f ready, no blocking findings. Full suite 1319 passed / 5 skipped; build --check and spec-validation clean; Concorde's own `npm run build` promoted.

All 25 Issues in `resolves` are fixed (the merge closes them):
- Critical: I-e7826df5 backup cleanup now runs after the promotion and outside its rollback; a failed removal keeps the promoted site, warns naming the backup, build succeeds. I-eff31701 loading refuses any source lexically or physically inside docsite/.generated, docsite/build or docsite/.docusaurus, and an output dir that is a symlink, before anything is cleared. I-c920fa47 + I-dc13ba09 (your answer A) new src/concorde/spec/views/creation.py: temp file + os.link (O_EXCL fallback without hard links), rollback removes only files whose device/inode is still ours; Spec core unchanged.
- Your answers: I-3673fa07 B (preview stages into .generated/preview, build into .generated/production, mode passed as CONCORDE_PUBLICATION_MODE); I-8aa56cf1 A (exactly one root page); I-98ce7a93 A (requirement reworded).
- Preferred-fix choices: I-a45fefab Spec-only (code already handled first publication); I-d95bcf63 extension docs plugins get collection admission + postBuild refuses routes under /specs not owned by a registered page or the glossary; I-170adc72 link walk follows linked dirs with a visited set; I-f3d6527b anchor headings of every level the loader (and Spec core) admits, 1–6, rather than narrowing loading; I-d1f31171 code spans matched per text block; I-54743dd4 tests build a scratch package when the checkout has none, run-checks runs the whole tests/concorde/views; I-b51fa600 includes document.spec.contracts and document.spec.errors; I-17779, I-48d3ddee, I-a1717b2a, I-c2ca5be6 (exact serialization + example digest) Spec wording.
- Obvious-fix: I-073de3b4, I-0d025216, I-588f5769, I-7392c394 (uses module.distribution relying on req.distribution.installer-docsite-template; .concorde/specs.json refreshed), I-a0acb2fe.
- Suggestions: I-b56f6cc9 applied. I-5116d71f applied adapted: the Protocol forbids non-step list items in a scenario, so the refusal scenarios point to the pipeline's vertical list instead.

Notes: realization.views.scaffold → module.spec relation verb changed to "reads the root title and result shape from". Observed, not acted on: the Protocol says definition headings are level 2–5 while Spec core accepts 1–6 (Spec core / Protocol matter). Nothing open for the developer. Details in the decision log.

## Closed: merged, 2026-10-08T07:25:14Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b2ab57084eea19a66aaa6cff3eb7f57b35ffdf5b into main and closed it as merged. Nobody answers a report after that.
