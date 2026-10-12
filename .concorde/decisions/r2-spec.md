# Decision log: r2-spec

Goal: Fix the critical, high and obvious-fix open Issues of Spec core, Spec MCP and Spec tooling found by the complete project_review

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 27 Issues in its `resolves`,
owned by its Modules, found by the complete project_review
r-20261008T063808-project_review-9851e69f (unbound; reports under
`.concorde/unbound/r-20261008T063808-project_review-9851e69f/` of the primary worktree) or
earlier. Read each with `concorde issues show`. Other open Issues of these Modules are out of
scope: do not fix them, even when nearby, unless a fix in scope needs it.

By tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest
  meanwhile. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- Work critical first, then high.
- An Issue that does not hold, is a duplicate or is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix needing a change outside the task's Modules: escalate, unless it is a small mechanical
  follow-on (a link, a fixture, a registry refresh).

Eleven other round-2 tasks run in parallel, each on other Modules (r2-*). If a merge conflict
comes back, the main agent asks you to merge the primary branch in. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-08T13:38:02Z

- **task-session** task session (task r2-spec): `mcp_session_contract_undecided`
  Issue I-050dd722944750458f95c16d26973e49 (high, decision-needed, module.spec-mcp): the Spec MCP contract states no supported MCP revision, no initialize negotiation and no outcome when root discovery cannot complete. Current code (src/concorde/spec/mcp/server.py): SUPPORTED_VERSIONS = 2025-06-18, 2025-03-26, 2024-11-05; initialize answers the client's protocolVersion when supported, otherwise the newest (the MCP rule: the client disconnects if it cannot accept it). A client without the roots capability gets no_root on every call; a roots/list error reply or malformed reply counts as zero roots (no_root). A client that never answers roots/list blocks the session: later requests are queued and only answered once the reply or end of input arrives.
  Not handled here (decision): The fix changes Spec MCP's public promise (the Issue's tier is decision-needed and the brief reserves those).
  Options: A: specify the current behaviour as the promise: the three revisions, answer-requested-else-newest negotiation, no roots capability / error reply / malformed reply => no_root naming why, an unanswered roots/list leaves later requests waiting until the reply or end of input; add scenarios for each; B: as A, but bound the wait: if roots/list is unanswered after a fixed time (e.g. 10 s) the session gives up with no_root and answers queued requests; C: as A, but never wait: answer every request that arrives before the roots/list reply with no_root (the root resolves later)
  Recommendation: A: it matches the code, Claude Code (the only client) always answers roots/list and usually sets CLAUDE_PROJECT_DIR anyway, and it adds no clock to a deterministic server; the change is Spec + scenarios + tests only

```json
{
  "level": "task-session",
  "actor": "task session (task r2-spec)",
  "code": "mcp_session_contract_undecided",
  "detail": "Issue I-050dd722944750458f95c16d26973e49 (high, decision-needed, module.spec-mcp): the Spec MCP contract states no supported MCP revision, no initialize negotiation and no outcome when root discovery cannot complete. Current code (src/concorde/spec/mcp/server.py): SUPPORTED_VERSIONS = 2025-06-18, 2025-03-26, 2024-11-05; initialize answers the client's protocolVersion when supported, otherwise the newest (the MCP rule: the client disconnects if it cannot accept it). A client without the roots capability gets no_root on every call; a roots/list error reply or malformed reply counts as zero roots (no_root). A client that never answers roots/list blocks the session: later requests are queued and only answered once the reply or end of input arrives.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The fix changes Spec MCP's public promise (the Issue's tier is decision-needed and the brief reserves those)."
  },
  "options": [
    "A: specify the current behaviour as the promise: the three revisions, answer-requested-else-newest negotiation, no roots capability / error reply / malformed reply => no_root naming why, an unanswered roots/list leaves later requests waiting until the reply or end of input; add scenarios for each",
    "B: as A, but bound the wait: if roots/list is unanswered after a fixed time (e.g. 10 s) the session gives up with no_root and answers queued requests",
    "C: as A, but never wait: answer every request that arrives before the roots/list reply with no_root (the root resolves later)"
  ],
  "recommendation": "A: it matches the code, Claude Code (the only client) always answers roots/list and usually sets CLAUDE_PROJECT_DIR anyway, and it adds no clock to a deterministic server; the change is Spec + scenarios + tests only",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T13:38:11Z

- **task-session** task session (task r2-spec): `installed_file_grant_undecided`
  Issue I-ce2f62b6d51959178be266617caf2de6 (high, decision-needed, module.spec): req.spec.grant-installed-read-only caps an installed file's exact entry at ro, but when a realization binds it through a directory entry (already the CHK.binds.installed validation error, which is not a fatal loading failure) the grant keeps the directory rw, the installed file's exact entry is lowered to ro and then dropped by the reduction rule (an exact path covered by a directory of equal or higher level), so the installed file ends up writable through the directory. src/concorde/spec/grants.py:252-268 does exactly this.
  Not handled here (decision): Choosing between refusing the grant and another protection changes what Spec core promises (grant refusals are part of its contract).
  Options: A: refuse the grant with a new SpecError code installed_file (like shared_file) when an rw directory entry would cover an installed file, naming each directory and installed file; add it to the refusal table and a scenario; B: keep the directory rw but keep the installed file as an exact ro entry the reduction never drops (most specific entry wins); needs every enforcement point (deny rules, write hook, permission extension, write audit) to honour a more specific lower entry, which is outside this task's Modules; C: lower the whole directory entry to ro when it covers an installed file
  Recommendation: A: it mirrors shared_file, stays within Spec core, can never leave an installed file writable, and the state it refuses is already a validation error that the project must fix anyway

```json
{
  "level": "task-session",
  "actor": "task session (task r2-spec)",
  "code": "installed_file_grant_undecided",
  "detail": "Issue I-ce2f62b6d51959178be266617caf2de6 (high, decision-needed, module.spec): req.spec.grant-installed-read-only caps an installed file's exact entry at ro, but when a realization binds it through a directory entry (already the CHK.binds.installed validation error, which is not a fatal loading failure) the grant keeps the directory rw, the installed file's exact entry is lowered to ro and then dropped by the reduction rule (an exact path covered by a directory of equal or higher level), so the installed file ends up writable through the directory. src/concorde/spec/grants.py:252-268 does exactly this.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing between refusing the grant and another protection changes what Spec core promises (grant refusals are part of its contract)."
  },
  "options": [
    "A: refuse the grant with a new SpecError code installed_file (like shared_file) when an rw directory entry would cover an installed file, naming each directory and installed file; add it to the refusal table and a scenario",
    "B: keep the directory rw but keep the installed file as an exact ro entry the reduction never drops (most specific entry wins); needs every enforcement point (deny rules, write hook, permission extension, write audit) to honour a more specific lower entry, which is outside this task's Modules",
    "C: lower the whole directory entry to ro when it covers an installed file"
  ],
  "recommendation": "A: it mirrors shared_file, stays within Spec core, can never leave an installed file writable, and the state it refuses is already a validation error that the project must fix anyway",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T13:38:17Z

Early escalation of the task's two decision-needed Issues, as the brief asks; I continue with the 25 others meanwhile. (1) I-050dd722 (Spec MCP session/compatibility contract): options A specify current behaviour (revisions 2025-06-18/2025-03-26/2024-11-05, requested-else-newest negotiation, no roots capability or bad roots/list reply => no_root, unanswered roots/list waits), B add a timeout, C answer no_root while waiting; I recommend A. (2) I-ce2f62b6 (an rw directory entry can make an installed file writable): options A refuse the grant with a new code installed_file like shared_file, B keep an exact ro entry under the rw directory (needs enforcement changes outside the task), C lower the directory to ro; I recommend A. Full chains are escalations 1 and 2.

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-08T13:38:34Z

Escalations 1-2 (main agent): 1 A — specify the current Spec MCP session behaviour (supported revisions, requested-else-newest negotiation, no_root when root discovery cannot complete, an unanswered roots/list blocking until the reply or end of input) with scenarios. 2 A — refuse the grant with a new code installed_file (as shared_file), naming the directory and the installed file, with a scenario; this tightens the boundary and needs no Harness/Workers change.

## Escalated to the main agent, 2026-10-08T13:41:08Z

- **task-session** task session (task r2-spec): `protocol_text_not_readable`
  Issue I-324c4851a (high, preferred-fix, module.spec), found to need a boundary decision: Spec core's requirements and contracts delegate their normative rules to the Protocol's chapters (req.spec.every-check -> protocol/checks.md; required syntax -> protocol/format.md; boundary sets and grants -> protocol/boundaries.md, protocol/context.md, protocol/model.yaml). Those files are Spec core's own realization (realization.spec.protocol-text binds protocol/), so specify and review-spec tasks of module.spec get them by name only (ImplementationContext is names); only implement/test/review-code tasks read them, as code. The rendered project copy (.concorde/protocol/kinds/module.md) holds Required format, Writing guidance, Sentence style and Evaluating a Spec, but not Checks, Boundaries or Context. The Protocol offers no relation that makes a Module's own bound files readable Spec context: includes of kind document need a registered document, and includes of kind external must not overlap a realization entry (CHK.external.no-overlap) and are described as pinned third-party material.
  Not handled here (decision): Every fix either moves a boundary (which files a worker may read or write) or changes the Protocol or Distribution's bundle; the development skill reserves loosening a boundary or changing the Protocol for the developer.
  Options: A: unbind the normative chapters (protocol/checks.md, format.md, boundaries.md, context.md, model.yaml) from realization.spec.protocol-text and declare them as includes of kind external of module.spec: every module.spec task reads them; no worker can change them any more (developers and task sessions edit them directly, as they already do for Protocol changes); stretches 'external' beyond third-party material; B: change the Protocol so an includes may name a path the Module itself binds, granting it read in the spec channel (Protocol version bump, protocol-manifest rebind, Spec core code and checks); C: have Distribution's build render Checks, Boundaries and Context into the project Protocol copy and include that copy (.concorde/protocol/) as external of module.spec (changes module.distribution, outside this task, and every project's copy); D: leave the boundary as is and close the Issue as not-actionable: Spec core's Spec tasks are developer-led and the Protocol text is read directly
  Recommendation: A: smallest change, inside this task's Modules, no Protocol change; Protocol text is already changed only under the developer's direction, so losing worker write access costs nothing. If 'external' must stay third-party only, B is the principled alternative, as its own task.

```json
{
  "level": "task-session",
  "actor": "task session (task r2-spec)",
  "code": "protocol_text_not_readable",
  "detail": "Issue I-324c4851a (high, preferred-fix, module.spec), found to need a boundary decision: Spec core's requirements and contracts delegate their normative rules to the Protocol's chapters (req.spec.every-check -> protocol/checks.md; required syntax -> protocol/format.md; boundary sets and grants -> protocol/boundaries.md, protocol/context.md, protocol/model.yaml). Those files are Spec core's own realization (realization.spec.protocol-text binds protocol/), so specify and review-spec tasks of module.spec get them by name only (ImplementationContext is names); only implement/test/review-code tasks read them, as code. The rendered project copy (.concorde/protocol/kinds/module.md) holds Required format, Writing guidance, Sentence style and Evaluating a Spec, but not Checks, Boundaries or Context. The Protocol offers no relation that makes a Module's own bound files readable Spec context: includes of kind document need a registered document, and includes of kind external must not overlap a realization entry (CHK.external.no-overlap) and are described as pinned third-party material.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Every fix either moves a boundary (which files a worker may read or write) or changes the Protocol or Distribution's bundle; the development skill reserves loosening a boundary or changing the Protocol for the developer."
  },
  "options": [
    "A: unbind the normative chapters (protocol/checks.md, format.md, boundaries.md, context.md, model.yaml) from realization.spec.protocol-text and declare them as includes of kind external of module.spec: every module.spec task reads them; no worker can change them any more (developers and task sessions edit them directly, as they already do for Protocol changes); stretches 'external' beyond third-party material",
    "B: change the Protocol so an includes may name a path the Module itself binds, granting it read in the spec channel (Protocol version bump, protocol-manifest rebind, Spec core code and checks)",
    "C: have Distribution's build render Checks, Boundaries and Context into the project Protocol copy and include that copy (.concorde/protocol/) as external of module.spec (changes module.distribution, outside this task, and every project's copy)",
    "D: leave the boundary as is and close the Issue as not-actionable: Spec core's Spec tasks are developer-led and the Protocol text is read directly"
  ],
  "recommendation": "A: smallest change, inside this task's Modules, no Protocol change; Protocol text is already changed only under the developer's direction, so losing worker write access costs nothing. If 'external' must stay third-party only, B is the principled alternative, as its own task.",
  "causes": []
}
```

## Report 2 to the main agent (Review流程), 2026-10-08T13:41:15Z

One more decision found while working (escalation 3): preferred-fix Issue I-324c4851 (make the Protocol's normative chapters readable Spec context of Spec core) cannot be fixed without moving a boundary or changing the Protocol. Options: A unbind protocol/{checks,format,boundaries,context}.md and model.yaml from realization.spec.protocol-text and include them as external of module.spec (workers then read but never write them); B Protocol change letting includes name a Module's own bound path; C Distribution renders those chapters into the project copy, included as external; D close as not-actionable. I recommend A. (The escalation's text mistypes the identity as I-324c4851a; it is I-324c4851b... i.e. I-324c4851e5 prefix I-324c4851.) Also decided myself: I-761c1984 (repository queries read live filesystem state) is fixed by scoping req.spec.snapshot-reconstruct to the loaded Specs, as I-ab67e7e7's panel repair asks, rather than reading all external material at construction. I continue with the rest.

It carries escalation(s) 3.

## Task session decisions (r2-spec, 2026-10-08)

- **I-761c1984 (preferred-fix)**: fixed by scoping req.spec.snapshot-reconstruct and
  req.spec.deterministic-order to the loaded Specs (configuration, registry, documents, glossary),
  stating that bound-file listings, external material and the installation record are read when
  queried, rather than capturing them at construction. Reason: capturing pinned external material
  at construction reads every byte of `references/` on each repository construction; I-ab67e7e7's
  panel repair asks for exactly this scoping; `recheck_context` already detects changed sources.
- **I-133c29e9 / I-a0a8f1dd (preferred-fix)**: selected the provider contracts with `includes` of
  kind document (with reasons): Spec core includes document.kernel.contracts and
  document.distribution.contracts; Spec MCP includes document.spec.contracts and
  document.spec.errors. Reason: the provider contracts documents define no nodes a `relies_on`
  could name; `includes` with a reason is the project's existing idiom (root, Views,
  project-review).
- **I-04fabcf2 (preferred-fix)**: the entry now says only records handed between parts, such as
  the initialization proposal, are typed values; configuration, registry, grant and validation
  result keep their own formats.
- **I-ab67e7e7 (preferred-fix)**: each exception moved into the obligation it limits
  (transaction rollback qualified by refused restores; covered-by excepted inside
  req.spec.no-implementation-read and req.spec.indexes-derived; snapshot/repeat scoped as above;
  highest level chosen first, then shared_file, installed_file and the installed cap); rollback
  scenarios now state that restores succeed.
- **I-5f267a1e (preferred-fix)**: req.spec.grant-one-worktree is now a worktree-origin constraint
  listing every source (adds glossary, bound paths, pinned external material, installation record).
- **I-909c1a9e**: new requirement req.spec.typed-schema-admitted for schema admission.
- **I-ce2f62b6 (main agent: option A)**: new SpecError code `installed_file`, Spec text,
  diagram, scenario.spec.grant-installed-directory and a test.
- **I-050dd722 (main agent: option A)**: Spec MCP session contract states the three revisions,
  negotiation and every root-discovery outcome; three new scenarios (roots-unavailable,
  roots-pending, initialize-revision) with tests. While doing it, root resolution now names each
  failure case in `no_root` (no capability, error reply, no roots list, count, non-file root, input
  ended).
- **I-f17a827f follow-on**: the restore-failure message and req.spec.transaction-restore-reported
  now say the unrestored file holds the new content "or what replaced its destination", since an
  unsafe destination (a symbolic link put in its place) is now a refused restore too.
- **I-78c73ffd follow-on**: contracts.md#verification-declarations now says the TypeScript scan is
  lexical and ignores calls in comments and string literals; a `// verifies:` inside a block
  comment or string is no longer a declaration.
- **I-a9d196a9 note**: `  - a:` followed by `    b: 1` now parses as `{a: {}, b: 1}` (YAML's
  reading, with {} for null) instead of `{a: {b: 1}}`; all tracked front matter parses identically.
- Code fixes were made by helper agents of this session on disjoint files and reviewed by me before
  each commit.
- **Full suite (2026-10-08, after commit 46a39414c)**: 1387 passed, 5 skipped, 1 failed:
  tests/concorde/tasks/test_store.py::TaskStoreTests::test_close_a_merged_task ("Tuples differ:
  ('ok', 'merged', '2026-10-08T13:54:11Z') != ..."), outside this task's Modules; the whole file
  passed (50/50) when rerun alone, so it looks load-dependent. Reported to the main agent rather
  than filed, since the one-line evidence does not establish the cause. `build --check`: success.

## Answer to report(s) 2 of the task session, 2026-10-12T14:26:33Z

Escalation 3 protocol_text_not_readable (developer, 2026-10-12): option B — a Protocol change letting a Module's includes name its own bound paths as read-only Spec context. It becomes its own follow-up task after this one merges; do not build it here and do not apply A. I-324c4851 is in this task's resolves and cannot be removed, so the main agent reopens it after the merge. I-761c1984: your scoping of req.spec.snapshot-reconstruct is accepted. Deliver the rest.

## Task session, 2026-10-12 (after the answer to report 2)

- Escalation 3 / I-324c4851: per the answer, nothing of option A or B is built here; the branch
  leaves realization.spec.protocol-text and module.spec's includes unchanged. The other 26
  resolved Issues are each named in a task commit.
- `task-validation` r-20261012T142709-task_validation-fec9d737 on 46a39414c: ready, 28 checks
  passed, no blocking findings, 10 structural warnings, all on lines that predate the task's base
  (spec/scenarios.md sentence lengths from 179b304a3, workers' Specs outside the task's Modules).

## Report 3 to the main agent (Review流程), 2026-10-12T14:45:24Z

r2-spec delivered: delivery commit 4815e740b on concorde/r2-spec (run r-20261012T143612-delivery-44d39236, ok), after task-validation r-20261012T142709-task_validation-fec9d737: ready, 28 checks passed, no blocking findings; its 10 structural warnings are all on lines older than the task's base. Resolved: 26 of the 27 Issues in resolves, each named in a task commit. Not fixed: I-324c4851. As you answered, neither option A nor option B is built here; it stays for the follow-up Protocol task (option B), and you reopen it after the merge. Decisions I took (details in the decision log): I-761c1984 scoped req.spec.snapshot-reconstruct to the loaded Specs (you accepted this). I-133c29e9/I-a0a8f1dd: the provider contracts are selected through includes of kind document. I-04fabcf2: only records handed between parts are typed values. I-ab67e7e7: each exception moved into the obligation it limits. I-5f267a1e: the grant-one-worktree requirement lists every source. I-909c1a9e: new requirement req.spec.typed-schema-admitted. I-ce2f62b6 (your option A): new grant refusal code installed_file. I-050dd722 (your option A): the MCP session contract states the revisions, the negotiation and the no_root cases, with 3 new scenarios. Side effects: (1) the TypeScript verification scan now ignores comments and strings; (2) the front-matter parse of a list item followed by a deeper key now follows YAML. On 2026-10-08 the full suite had 1 failure outside the task, tasks/test_store.py::test_close_a_merged_task; it passed when rerun alone, so it looks load-dependent. Nothing else is open.

## Closed: merged, 2026-10-12T14:45:37Z

The merge answered report(s) 3 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 4815e740b2a07b890813c367991c44f044c18434 into main and closed it as merged. Nobody answers a report after that.
