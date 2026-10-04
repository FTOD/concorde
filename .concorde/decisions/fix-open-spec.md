# Decision log: fix-open-spec

Goal: Fix the open Issues of the spec part (Spec tooling, Spec core, Spec MCP server, Views)

## Brief (main agent, 2026-10-04)

### Context

The developer asked (2026-10-04) to try to resolve the project's open Issues, after the parts
refactor merged into `main` (decision logs of parts-*, fix-* and parts-review* in
`.concorde/decisions/`). Every open Issue was reviewed and classified then; none is high or
critical. Nine tasks run in parallel, one per part or group of parts: fix-open-spec,
fix-open-method, fix-open-execution, fix-open-coordination, fix-open-worker-harness,
fix-open-kernel, fix-open-workflows, fix-open-root-distribution, fix-open-issues-e2e.

### How to work

- Your Issues are listed below with severity and tier; read each with `concorde issues show`
  (the latest report is the verified one). Work on them most severe first.
- **obvious-fix and preferred-fix**: fix them (preferred-fix: record which fix you chose and why).
  **decision-needed**: the main agent's decisions are below; carry them out. **suggestion**: fix it
  when it is cheap and clearly improves the Spec or code; otherwise leave it open.
- After fixing an Issue, add it to this task with `concorde task resolve <task> <issue>`: the
  merge closes exactly the Issues the task resolves, so add none you did not fix. Close an Issue
  that does not hold yourself (`not-actionable`, with the reason) or as `duplicate`. If a fix needs
  a decision with major impact, or another group's files beyond a small edit, escalate it with any
  others together rather than deciding it.
- Work directly in the Specs, code and tests; no Operation or review is needed. Keep edits of files
  other groups may touch small (glossary, registry mirror, shared tests, guidance composition); on a
  merge conflict the main agent asks you to merge `main` in.
- Introduce no regression: every part still works installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency check passes, guidance reads
  correctly whichever parts are installed (`tests/concorde/distribution/test_guidance_parts.py`).
  Rapid-iteration rule: no shims or compatibility paths.
- Verify with `build --check`, `spec-validation` and the full suite, then `task-validation` and
  `delivery`, and report: resolved, closed as not holding, left open (and why).

### Your 50 Issues

- I-5108bf6842cb57019a01f333d3cc8984 (medium, preferred-fix, module.spec-mcp): Malformed tool calls can terminate the MCP session
- I-c18683973e1f5eacbd01314d57ef731e (medium, preferred-fix, module.views): Scaffold identity ignores the origin of linked worktrees
- I-2a6a5560c7485b349e27fa0096bb53b5 (medium, preferred-fix, module.views): A custom collection named user collides with user documents
- I-6a01a1319ab756af9f03017d19742ef6 (medium, preferred-fix, module.spec): Grant directory entries ignore the exclusion rule and hide shared files
- I-44d15d2fb9dc5fde92288a591cb5dbb3 (medium, obvious-fix, module.spec): Initialization apply does not check the proposal as a typed value
- I-926dc4e0b14159dfa505d9a1d655be2c (medium, obvious-fix, module.spec): Malformed entry metadata aborts validation with a raw exception
- I-69ef9269a7aa56ac88fcac20806c443e (medium, obvious-fix, module.spec): Consumer loading admits CHK.node.owner and several-entry failures
- I-4d613f5dda3f5613937fae325038cd4e (medium, obvious-fix, module.spec): Paths under .concorde/ and generated/ can still be bound and granted
- I-bf144cd28b5652fa8fe3925f41a56290 (low, preferred-fix, module.views): Apply does not check the whole proposal shape; a null result wrapper fails instead of invalid
- I-ec29fe04a0fc58b2aa445bbe2c7b2459 (low, preferred-fix, module.views): Apply skips the package-descriptor check and reports a broken template without reinstall guidance
- I-520bf707e8da51c6b75786fc8d243f1c (low, preferred-fix, module.views): npm run validate does not check diagrams, though the pipeline says it performs staging step 2
- I-e9ee4d2c0e0d54a6954a8418e2a0851a (low, preferred-fix, module.views): Realization anchors are not placed at headings with closing hashes or implicit definition anchors
- I-51ade85df9ef576c8dc42408f4644590 (low, preferred-fix, module.views): Diagram diagnostics report staged rather than source line numbers
- I-063ea7d038d05cac805780fa50d43013 (low, preferred-fix, module.views): Collection admission does not see a symlink to a registered Spec inside the collection
- I-d056cbfec683560f98000126d373c331 (low, preferred-fix, module.spec): Some repository queries read the disk after construction instead of the snapshot
- I-2734c5c8c6405310a05971d5c03b4935 (low, preferred-fix, module.spec): Schema equality and uniqueness do not follow JSON value equality
- I-e76d51bb57705f4393e0b78f80c755e1 (low, preferred-fix, module.spec): Some load errors keep their underlying error only as message text
- I-618d6b0e729f536585e1527d3927e709 (low, preferred-fix, module.spec): The no-code-read rule for impact indexes contradicts covered-by
- I-02c637e225095eeca1f148edd16e7429 (low, preferred-fix, module.spec-tooling): The init command's file and envelope mapping is not specified
- I-6e8a224047bc591c88e13ac42a926548 (low, obvious-fix, module.spec-mcp): Falsy non-object tool arguments are accepted as empty arguments
- I-c7bbcafbc49f52c88d26747b8ca4181e (low, obvious-fix, module.spec-mcp): A repeated initialized notification retries a failed root resolution
- I-34e0959ec3715dd4bcd573f2ebb101b3 (low, obvious-fix, module.views): Scaffold apply binds a file created in a microsecond window as replaceable
- I-4e88501344a758e8a11c21eb8a784b5f (low, obvious-fix, module.views): Propose answers failed instead of invalid for an unsafe template or missing workflow
- I-c249f488221b5786acd0b9706482f26e (low, obvious-fix, module.views): Proposal mismatch error truncates differing paths and reports zero for reorder/duplicate
- I-3dcc89af66c8582caea672cfdc86623c (low, obvious-fix, module.views): Apply answers failed instead of conflict for a dangling destination symlink
- I-73d284cd59cb5e819568e3c74e4f8cbc (low, obvious-fix, module.views): A glossary outside specs/ gets a truncated route when every reading is under specs/
- I-38723f1eb6cd5fb19c071e4d1081066a (low, obvious-fix, module.views): A concorde-contract fence with words after the language gets no contract anchor
- I-f953adaa40e651d285d36c6c3c3791e8 (low, obvious-fix, module.views): URL checks accept http(s) strings with no host
- I-de6d2d8188bb5cd7a11e050d7b8c055b (low, obvious-fix, module.views): Packaged README documents the wrong site manifest version
- I-3b2eaad80ecc5947b66a9db74007af7a (low, obvious-fix, module.spec): Typed-value checking ignores keywords beside a satisfied anyOf
- I-455cef9545b7562eb5786ff45ed3e563 (low, obvious-fix, module.spec): Strict JSON decoding accepts numbers that overflow to infinity
- I-59c41a499c195720a94fe2b48ba19fd7 (low, obvious-fix, module.spec): Registering a schema mistakes a property named $ref for a type reference
- I-1638b12dbcdb569fa25ad4923c906cbd (low, obvious-fix, module.spec): An unreadable bound test file stops the coverage scan
- I-f6f5efe549bf5e2d9c8d42c0ff03f032 (low, obvious-fix, module.spec): The validation digest leaves out documents that failed admission
- I-897b8a3b31675ca4ad04b7181eba5a26 (low, obvious-fix, module.spec): Changed-definition queries ignore metadata member paths
- I-16374e6f72c15cd58ba37fe9db01d027 (low, obvious-fix, module.spec): A contract counts as changed when another contract in its section changes
- I-b09ddbb7803355daa51cc08645700c33 (low, obvious-fix, module.spec): Glossary definitions' term links with a path escape CHK.term.link
- I-38625962614a5531aba67d3ca7f645d9 (low, obvious-fix, module.spec): CHK.term.unlinked misses plurals of one-word titles
- I-04cf71ad312055c3adc0e4e3365eb341 (low, obvious-fix, module.spec): Front matter accepts duplicate keys in inline maps and list items
- I-f4f8623ddbb8512280eb5e65c1662371 (low, obvious-fix, module.spec): Front matter refuses scalars containing &, * or !
- I-8b4ae648be9c503e86197d8c8524d9c1 (low, obvious-fix, module.spec): apply_files raises raw exceptions on a malformed change list
- I-93a6384060e15bf2958ece4c3268a16b (low, obvious-fix, module.spec): The allowed-files requirement omits the glossary initialization creates
- I-79689f151c2b59c9846289567030e5dd (low, obvious-fix, module.spec): The no-widening requirement omits ProjectSpecification
- I-bb482e2f485c5ced913148722e1f1aa3 (low, obvious-fix, module.spec): The unsupported_profile message names profile 18 while the loader needs 19
- I-fb4f8251da3555f4b9475cce8b3de048 (low, obvious-fix, module.spec): Initialization's source digest has an undocumented installed field
- I-71b30f64a6055ca8aa0667bb3fb0e5e1 (low, obvious-fix, module.spec-tooling): The parent's 'keeps the published site' omits Views' rollback-failure exception
- I-a9919d0a86ec55be8c4ec2defe38fe4a (low, suggestion, module.spec): Grant and context records share mutable glossary entries with the repository
- I-78b3560a865b536da946e9f26969a455 (low, suggestion, module.spec-tooling): The overview hides MCP and docsite command entry points
- I-9f262a85bb8952d9acd0df23e51ab38d (low, suggestion, module.spec-tooling): Clarify which explicit operations can update Specs
- I-3617d25ed8ba5a46bc9b2a8a26cc4ae5 (low, suggestion, module.spec-tooling): Introduce the roles of named collaborators on first use

## Task session decisions (2026-10-04)

Work split: the task session fixed the 26 module.spec Issues itself and had two subagents of its
own session fix the 16 module.views Issues and the 8 module.spec-mcp / module.spec-tooling Issues
in the same worktree; the task session reviewed their diffs.

### Choices for preferred-fix Issues

- I-6a01a131 (grant directory entries): Grant.level and grant compaction now cover a path by a
  directory entry only where `bound_by` binds it (exclusion rule), so an excluded file keeps its
  own entry and level. Chosen over refusing such grants because the contract already defines
  directory coverage under the exclusion rule. The worker harness still reads directory entries
  as raw prefixes (write hook, write audit): outside this task's Modules, recorded as Issue
  I-451c2b0615c8547b97b979ed493814a1 for module.harness.
- I-2734c5c8 (JSON equality): one recursive `json_equal` (and `unique`) in spec/schema.py, used
  for const, enum and uniqueItems by both checkers.
- I-d056cbfe (snapshot): new `loaded_bytes(path)` serves the loaded member and glossary bytes;
  `context_identity(project_specification=True)` hashes them; external listings and digests are
  computed together once per entry and cached.
- I-e76d51bb (load error causes): a loading finding keeps the error behind it; the load error's
  finding-derived cause carries it as its own cause (Spec errors as they are, OS errors as
  system_error, non-UTF-8 text as invalid_spec, other undecodable values as invalid_json); the
  registry decode error carries its cause too.
- I-618d6b0e (covered-by vs no-code-read): kept covered-by an impact index and stated it as the
  one exception in req.spec.indexes-derived and req.spec.no-implementation-read.
- Views and spec-mcp/spec-tooling preferred-fix choices: see their entries below.

### Other decisions

- I-69ef9269: the several-entries check moved from validation (Checks.documents, removed) into
  loading as a fatal problem (`_entries`), so validation reports it once, from the load findings.
- I-4d613f5d: `unbindable(path)` (under .concorde/, .git/ or generated/) is applied by bound_by,
  expand_entry, implementation_scope and therefore shared_files; validation keeps reporting the
  declaration (CHK.binds.no-spec).
- I-f6f5efe5: validation's source_digest now covers every registered member as read, admitted or
  not (`member_bytes`); contracts.md wording updated. A valid result's digest is unchanged.
- I-38625962 (plural of one-word titles): the fix surfaced 30 new CHK.term.unlinked warnings in
  the Specs, 24 in other groups' documents. Fixed them all with one-line edits: a term link on the
  first use for real uses (Module/Modules, Spec/Specs), and code spans for section names that
  matched only by accident (`Parts`, `Purpose`, `Not yet specified`, `Collaborations`, and the
  skill sections `Runs`, `Read results`, `Unbound runs`). spec-validation: 0 errors, 0 warnings.
  Files of other groups touched this way: coordination, e2e, execution, method (adoption,
  delivery, scaffold, spec-review, specification), worker-harness, workflows Specs.
- The Kernel's own schema copy (src/concorde/kernel/schema.py) was not touched (not this task's
  Module).

### Spec MCP server and Spec tooling (subagent, reviewed)

- I-5108bf68 (preferred-fix): validate params and tool name before use, plus a per-message
  catch-all in `run()` answering JSON-RPC -32603 with the error record, so no message ends the
  session; new scenario.spec-mcp.malformed-call; contracts.md invalid_input row widened.
- I-6e8a2240: `arguments` default to {} only when absent; an explicit null optional is refused.
- I-c7bbcafb: the root is resolved at most once per session.
- I-02c637e2 (preferred-fix): the init adapter (file format, envelope status and exit codes,
  adapter refusals) described in spec-tooling/module.md Part entries (`#init-command`), linked
  from Distribution's command table (one-line edit of a Distribution file).
- I-71b30f64, I-78b3560a, I-9f262a85, I-3617d25e: spec-tooling/module.md wording.

### Views (subagent, reviewed)

- I-c1868397 (preferred-fix): origin read through Git (`rev-parse --show-toplevel`, `config
  --get remote.origin.url`) instead of parsing .git/config, so linked worktrees work.
- I-bf144cd2 (preferred-fix): explicit checks of the whole proposal shape (closed top level,
  conflicts records, exact site identity) rather than a schema validator.
- I-ec29fe04 (preferred-fix): apply calls verify_package_root; template errors answer invalid 002
  with reinstall guidance; no initialization re-check on apply (the Spec ties it to propose).
- I-2a6a5560 (preferred-fix): user-docs plugin id is `user_docs`, which no custom id can be.
- I-063ea7d0 (preferred-fix): collection admission also walks the collection for symlinks to
  registered readings (no following of symlinked directories).
- I-e9ee4d2c (preferred-fix): anchorAtMeanings finds a heading identity as readingMeanings does.
- I-51ade85d (preferred-fix): Page.contentLine plus matching the n-th d2 block of the source
  reading gives source line numbers.
- I-520bf707 (preferred-fix): `npm run validate` now runs the diagram checks without writing
  (renderDiagrams with stagedFile null), rather than narrowing the Spec; ~11 s on Concorde.
- Obvious fixes I-34e0959e, I-4e885013, I-c249f488, I-3dcc89af, I-73d284cd, I-38723f1e,
  I-f953adaa, I-de6d2d81 as their Issues suggest.
- task-validation r-20261004T022145-task_validation-42497cac: blocked, the new tests/concorde/spec/test_frontmatter.py and test_loading.py were unbound; bound them in Spec core's test realization.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:45:04Z

fix-open-spec delivered: delivery commit 634c5d72 on concorde/fix-open-spec (task-validation ready; build --check, spec-validation 0 errors / 0 warnings, full suite 1109 passed, 5 skipped).

Resolved (all 50, added with task resolve): 26 module.spec, 16 module.views, 3 module.spec-mcp, 5 module.spec-tooling (the 4 suggestions included). None closed as not holding, none left open, no escalation.

Preferred-fix choices (details in the decision log):
- I-6a01a131: Grant.level and compaction cover a path by a directory entry only where bound_by binds it, so an excluded file keeps its own entry and level.
- I-2734c5c8: one recursive json_equal/unique for const, enum and uniqueItems in both checkers.
- I-d056cbfe: loaded_bytes() for review-architecture context identity; external listing and digest cached together.
- I-e76d51bb: load findings keep their underlying error as a nested cause.
- I-618d6b0e: covered-by stays an impact index, stated as the exception.
- I-5108bf68: params and tool name are checked, plus a per-message catch-all that answers JSON-RPC -32603.
- I-02c637e2: the init adapter is described in spec-tooling/module.md (#init-command).
- Views: origin is read through git (linked worktrees); whole-proposal shape checks; user-docs plugin id is user_docs; npm run validate now runs diagram checks without writing; source line numbers for diagrams; heading anchors as readingMeanings finds them; symlink walk in collection admission.

Decisions taken without the developer that touch other groups:
1. The plural fix for one-word terms (I-38625962) surfaced 30 new CHK.term.unlinked warnings, 24 in other groups' Specs. I fixed them with one-line edits: a term link on the first real use (Module(s)/Spec(s)), and code spans for section names that matched by accident (`Parts`, `Purpose`, `Not yet specified`, `Collaborations`, `Runs`, …). The files touched are in coordination, e2e, execution, method (adoption, delivery, scaffold, spec-review, specification), worker-harness and workflows. These are possible merge-conflict spots.
2. One-line link from distribution/module.md's command table to #init-command.
3. CHK.document.entry for several entries moved from validation into loading (fatal), and validation's Checks.documents was removed.

New Issue recorded, outside this task's Modules: I-451c2b0615c8547b97b979ed493814a1 (module.harness, medium, preferred-fix). The write hook and write audit read grant directory entries as raw prefixes and check rw first, so an excluded file of another Module below a writable directory entry is still writable although the grant now lists it ro. It belongs to the worker-harness group.

Open: nothing.

## Closed: merged, 2026-10-04T02:45:22Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 634c5d72c2e7b6ee25ce858dc5b72d227a6651b7 into main and closed it as merged. Nobody answers a report after that.
