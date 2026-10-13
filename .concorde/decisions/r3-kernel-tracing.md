# Decision log: r3-kernel-tracing

Goal: Fix the remaining open Issues of Kernel and Tracing (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (17, listed in `resolves`; 7 of them decision-needed), all medium or
low, found by project_review r-20261008T063808-project_review-9851e69f or reported since. Read each
with `concorde issues show`.

By tier:
- **decision-needed**: read them all first and escalate them **together in one report, early**,
  each with what you found, the options and your recommendation (say which options change a
  promise users rely on or an earlier developer decision). The main agent settles those within its
  authority and takes the rest to the developer in one batch. Continue with the rest meanwhile.
  An Issue the developer is asked about may stay open: you may deliver without it; the main agent
  reopens it after the merge if needed.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it is wrong or costs more than it is worth; then say why in the
  log and your report, and the main agent closes it as not-actionable.
- An Issue that no longer holds (many Modules changed in rounds 1-2), is a duplicate or is already
  fixed: say so with evidence; it stays in `resolves` and the merge closes it.
- Medium first, then low. A fix needing a change outside the task's Modules: escalate, unless it is
  a small mechanical follow-on (a link, a fixture, a registry refresh).

Eleven other round-3 tasks (r3-*) run in parallel on other Modules. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-13T11:33:47Z

- **task-session** task session (task r3-kernel-tracing): `child_folder_namespace`
  I-52c3229fb1275bb98e5176d2e38d6953 (Tracing, medium): reader.py skips child folders named answers, reports, runtime, __pycache__ and every dot-prefixed folder (NOT_NODES) when it looks for child nodes and when it searches identities; the node contract only says 'children are the trace nodes in the folders below this one'. None of those folders holds a trace.json today (they are Workflows' answers/reports, a task session's runtime, caches), so dropping the list changes no view of an existing trace; it only costs a walk of a few extra folders.
  Not handled here (decision): The Issue is decision-needed: it fixes which folder names producers may use below a node, a promise of the node contract.
  Options: A: discover children by trace.json alone in every real (non-symlink) folder; drop the name list; keep only the symlink skip (no reserved names, nothing to document beyond the existing contract); B: keep the exclusions and document them in the node contract as reserved names that never hold a node, refusing a node write placed below one
  Recommendation: A: it is what the contract already says, Tracing stays free of producer-specific names, and no current trace changes

```json
{
  "level": "task-session",
  "actor": "task session (task r3-kernel-tracing)",
  "code": "child_folder_namespace",
  "detail": "I-52c3229fb1275bb98e5176d2e38d6953 (Tracing, medium): reader.py skips child folders named answers, reports, runtime, __pycache__ and every dot-prefixed folder (NOT_NODES) when it looks for child nodes and when it searches identities; the node contract only says 'children are the trace nodes in the folders below this one'. None of those folders holds a trace.json today (they are Workflows' answers/reports, a task session's runtime, caches), so dropping the list changes no view of an existing trace; it only costs a walk of a few extra folders.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: it fixes which folder names producers may use below a node, a promise of the node contract."
  },
  "options": [
    "A: discover children by trace.json alone in every real (non-symlink) folder; drop the name list; keep only the symlink skip (no reserved names, nothing to document beyond the existing contract)",
    "B: keep the exclusions and document them in the node contract as reserved names that never hold a node, refusing a node write placed below one"
  ],
  "recommendation": "A: it is what the contract already says, Tracing stays free of producer-specific names, and no current trace changes",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:17Z

- **task-session** task session (task r3-kernel-tracing): `duration_source`
  I-83630d276a955c4980dc4d6ec611886e (Tracing, medium): req.tracing.reported-usage says usage holds only what the agent program reported, but the node contract counts 'the node's wall-clock duration' in usage, and the library (node.py:468) fills duration_seconds itself from started_at to ended_at when the producer gives none; Tasks, Workflows, merges and checks pass host-measured durations too. So duration is host-observed today for every node.
  Not handled here (decision): Either answer changes the wording of a requirement: what Concorde promises about where usage figures come from.
  Options: A: specify duration_seconds as the wall-clock time Concorde observed between the node's start and end (the library fills it when the producer gives none), and limit the agent-reported rule to tokens, cache tokens, cost and turns; B: apply the rule to duration too: null unless an agent program reported it; remove the library's fill-in and the producers' host timing
  Recommendation: A: it matches every producer and the reader's own duration, keeps the timings of runs, checks and merges, and is measured, not estimated

```json
{
  "level": "task-session",
  "actor": "task session (task r3-kernel-tracing)",
  "code": "duration_source",
  "detail": "I-83630d276a955c4980dc4d6ec611886e (Tracing, medium): req.tracing.reported-usage says usage holds only what the agent program reported, but the node contract counts 'the node's wall-clock duration' in usage, and the library (node.py:468) fills duration_seconds itself from started_at to ended_at when the producer gives none; Tasks, Workflows, merges and checks pass host-measured durations too. So duration is host-observed today for every node.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Either answer changes the wording of a requirement: what Concorde promises about where usage figures come from."
  },
  "options": [
    "A: specify duration_seconds as the wall-clock time Concorde observed between the node's start and end (the library fills it when the producer gives none), and limit the agent-reported rule to tokens, cache tokens, cost and turns",
    "B: apply the rule to duration too: null unless an agent program reported it; remove the library's fill-in and the producers' host timing"
  ],
  "recommendation": "A: it matches every producer and the reader's own duration, keeps the timings of runs, checks and merges, and is measured, not estimated",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:17Z

- **task-session** task session (task r3-kernel-tracing): `transaction_allowed_paths`
  I-8823a8cb2f1d5f5dbd8bae83c335d728 (Kernel, medium): the file transaction's 'paths it allows' has no defined form or matching rule. The code (files.py:114) takes a set of project-relative path strings and refuses a change whose path is not exactly one of them; no directory prefix, no pattern; an allowance that is not a canonical project path matches nothing. Callers (Issues and others) pass exact file paths.
  Not handled here (decision): Defining the allowance and its matching is a permission promise of the Kernel's contract; the Issue is decision-needed.
  Options: A: exact matching: the allowance is a set of canonical project-relative file paths; a change is allowed only when its path equals one; no directories or patterns; an entry that matches no change is ignored, never refused; B: directory prefixes: an allowance ending in / covers every file below it, exact otherwise; C: as A, but a malformed allowance entry refuses the transaction with invalid_proposal
  Recommendation: A: it is the current behaviour and the narrowest permission, and every caller already names exact files; add a scenario with an allowed file beside a forbidden neighbour

```json
{
  "level": "task-session",
  "actor": "task session (task r3-kernel-tracing)",
  "code": "transaction_allowed_paths",
  "detail": "I-8823a8cb2f1d5f5dbd8bae83c335d728 (Kernel, medium): the file transaction's 'paths it allows' has no defined form or matching rule. The code (files.py:114) takes a set of project-relative path strings and refuses a change whose path is not exactly one of them; no directory prefix, no pattern; an allowance that is not a canonical project path matches nothing. Callers (Issues and others) pass exact file paths.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Defining the allowance and its matching is a permission promise of the Kernel's contract; the Issue is decision-needed."
  },
  "options": [
    "A: exact matching: the allowance is a set of canonical project-relative file paths; a change is allowed only when its path equals one; no directories or patterns; an entry that matches no change is ignored, never refused",
    "B: directory prefixes: an allowance ending in / covers every file below it, exact otherwise",
    "C: as A, but a malformed allowance entry refuses the transaction with invalid_proposal"
  ],
  "recommendation": "A: it is the current behaviour and the narrowest permission, and every caller already names exact files; add a scenario with an allowed file beside a forbidden neighbour",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:17Z

- **task-session** task session (task r3-kernel-tracing): `trace_record_damage_and_versions`
  I-a8c3b519d21a5c6c90644c8b6be9ba33 (Tracing, medium): the reading contract defines no behaviour for missing, unreadable, malformed or unsupported trace.json, and no relation between the node contract's version (5) and the stored schema_version (1). Today: a requested folder without a readable record is refused node_unreadable (a workspace folder excepted); a folder below without trace.json is passed through (its own children become the parent's); a descendant whose trace.json cannot be parsed is not recognised as a node at all... actually it is (the child test is only 'trace.json is a file'), so view() raises node_unreadable and the whole show fails; a parseable record lacking id or kind raises a raw KeyError; schema_version is never checked; list fails the same way on one damaged top node. No migration exists.
  Not handled here (decision): Choosing refusal versus partial views, and the version policy, sets what trace show/list promise their users; the Issue is decision-needed.
  Options: A (strict): the requested node and every node below must have a readable, valid record of the supported schema_version, else show/list refuse with node_unreadable naming the folder and the reason; a folder without trace.json is no node and is passed through; only stored schema_version 1 is read, no migration; B (partial): the requested node must be readable (else node_unreadable); a damaged or unsupported record below, or a damaged top node in list, is shown as a node with status unreadable, its folder name as id, kind null, outcome naming why (missing_fields, malformed, unsupported_version), no usage; its children are still read; rolled_up counts only readable nodes, so an unreadable node in the tree marks the totals as incomplete; only stored schema_version 1 is read, no migration; the contract version and the stored schema_version are independent (schema_version changes only when the stored shape changes incompatibly)
  Recommendation: B: a trace reader is used to diagnose failures, so one damaged worker-round record must not hide a whole task or make trace list --history unusable for good; it adds the status value unreadable to the view contract, which is a contract change for its readers

```json
{
  "level": "task-session",
  "actor": "task session (task r3-kernel-tracing)",
  "code": "trace_record_damage_and_versions",
  "detail": "I-a8c3b519d21a5c6c90644c8b6be9ba33 (Tracing, medium): the reading contract defines no behaviour for missing, unreadable, malformed or unsupported trace.json, and no relation between the node contract's version (5) and the stored schema_version (1). Today: a requested folder without a readable record is refused node_unreadable (a workspace folder excepted); a folder below without trace.json is passed through (its own children become the parent's); a descendant whose trace.json cannot be parsed is not recognised as a node at all... actually it is (the child test is only 'trace.json is a file'), so view() raises node_unreadable and the whole show fails; a parseable record lacking id or kind raises a raw KeyError; schema_version is never checked; list fails the same way on one damaged top node. No migration exists.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing refusal versus partial views, and the version policy, sets what trace show/list promise their users; the Issue is decision-needed."
  },
  "options": [
    "A (strict): the requested node and every node below must have a readable, valid record of the supported schema_version, else show/list refuse with node_unreadable naming the folder and the reason; a folder without trace.json is no node and is passed through; only stored schema_version 1 is read, no migration",
    "B (partial): the requested node must be readable (else node_unreadable); a damaged or unsupported record below, or a damaged top node in list, is shown as a node with status unreadable, its folder name as id, kind null, outcome naming why (missing_fields, malformed, unsupported_version), no usage; its children are still read; rolled_up counts only readable nodes, so an unreadable node in the tree marks the totals as incomplete; only stored schema_version 1 is read, no migration; the contract version and the stored schema_version are independent (schema_version changes only when the stored shape changes incompatibly)"
  ],
  "recommendation": "B: a trace reader is used to diagnose failures, so one damaged worker-round record must not hide a whole task or make trace list --history unusable for good; it adds the status value unreadable to the view contract, which is a contract change for its readers",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:17Z

- **task-session** task session (task r3-kernel-tracing): `retention_partial_config`
  I-b956d670eb7554f89f6a3e6b35cffcfa (Tracing, medium): the retention schema (contract and retention.py) requires unbound_days and history_days, while the semantics say 'for a period it leaves out' the defaults apply (7 days, no removal, 30 days) and single out conversation_days as one 'which may be left out'. Today a file naming only conversation_days is refused config_invalid.
  Not handled here (decision): Either choice changes which tracing.json files are accepted, an input promise.
  Options: A: every period is optional; an omitted period takes its default; the schema requires only schema_version and retention; B: only conversation_days is optional; remove 'or for a period it leaves out' from the semantics
  Recommendation: A: it is what the prose promises the user, it refuses nothing accepted today, and the defaults are already defined per period

```json
{
  "level": "task-session",
  "actor": "task session (task r3-kernel-tracing)",
  "code": "retention_partial_config",
  "detail": "I-b956d670eb7554f89f6a3e6b35cffcfa (Tracing, medium): the retention schema (contract and retention.py) requires unbound_days and history_days, while the semantics say 'for a period it leaves out' the defaults apply (7 days, no removal, 30 days) and single out conversation_days as one 'which may be left out'. Today a file naming only conversation_days is refused config_invalid.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Either choice changes which tracing.json files are accepted, an input promise."
  },
  "options": [
    "A: every period is optional; an omitted period takes its default; the schema requires only schema_version and retention",
    "B: only conversation_days is optional; remove 'or for a period it leaves out' from the semantics"
  ],
  "recommendation": "A: it is what the prose promises the user, it refuses nothing accepted today, and the defaults are already defined per period",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:17Z

- **task-session** task session (task r3-kernel-tracing): `artifact_schema_recognition`
  I-e0329c202edd5f1e85f2d29ead8d65eb (Kernel, medium): the contract says the uniqueness rule applies when an array's items schema 'is the library's artifact schema' without defining it or the id's constraints. The code: ARTIFACT = a closed object of id (nonempty string), path (project-path) and digest (sha256 pattern), exported as schema.ARTIFACT; the rule fires when the items schema is structurally equal (JSON equality) to it (schema.py:463).
  Not handled here (decision): Fixing the artifact's id constraint and how the schema is recognised is a promise of the typed-value contract; the Issue is decision-needed.
  Options: A: document the current behaviour: id is a nonempty string; the artifact schema is the library's exported schema value, given in the contract; an items schema equal to it as JSON activates the rule, a schema that differs in any keyword does not; B: add an explicit marker (such as format artifact on the items schema) that activates the rule, independent of equality
  Recommendation: A: no behaviour changes, every producer already takes schema.ARTIFACT from the library, and equality is decidable; add the schema and an example to the contract

```json
{
  "level": "task-session",
  "actor": "task session (task r3-kernel-tracing)",
  "code": "artifact_schema_recognition",
  "detail": "I-e0329c202edd5f1e85f2d29ead8d65eb (Kernel, medium): the contract says the uniqueness rule applies when an array's items schema 'is the library's artifact schema' without defining it or the id's constraints. The code: ARTIFACT = a closed object of id (nonempty string), path (project-path) and digest (sha256 pattern), exported as schema.ARTIFACT; the rule fires when the items schema is structurally equal (JSON equality) to it (schema.py:463).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Fixing the artifact's id constraint and how the schema is recognised is a promise of the typed-value contract; the Issue is decision-needed."
  },
  "options": [
    "A: document the current behaviour: id is a nonempty string; the artifact schema is the library's exported schema value, given in the contract; an items schema equal to it as JSON activates the rule, a schema that differs in any keyword does not",
    "B: add an explicit marker (such as format artifact on the items schema) that activates the rule, independent of equality"
  ],
  "recommendation": "A: no behaviour changes, every producer already takes schema.ARTIFACT from the library, and equality is decidable; add the schema and an example to the contract",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:18Z

- **task-session** task session (task r3-kernel-tracing): `task_history_name_collision`
  I-e618904412f35ba2bdc28cd9c1beae3a (Tracing, medium): a task name and a history key can be the same text, and commonly are (a task foo closed to history/foo, then a new task foo opened). locate() tries the registered roots in registration order, and Tasks registers current tasks before the history, so the current task wins today; the closed one is reachable by its folder path history/foo. The contract states no precedence.
  Not handled here (decision): Choosing precedence or a refusal changes the public lookup promise of trace show; the Issue is decision-needed.
  Options: A: precedence: within each searched .concorde, a name is tried among the roots in the order they are registered (in Concorde: current tasks, history, unbound runs, lobby), so a current task wins; the other node is shown by its folder path (history/<key>); add a scenario with a reused task name; B: refuse an ambiguous name with a new code (ambiguous_node) naming every match and asking for a path
  Recommendation: A: it is the current behaviour, the live task is what a user means by its name, and the path form already selects the closed one

```json
{
  "level": "task-session",
  "actor": "task session (task r3-kernel-tracing)",
  "code": "task_history_name_collision",
  "detail": "I-e618904412f35ba2bdc28cd9c1beae3a (Tracing, medium): a task name and a history key can be the same text, and commonly are (a task foo closed to history/foo, then a new task foo opened). locate() tries the registered roots in registration order, and Tasks registers current tasks before the history, so the current task wins today; the closed one is reachable by its folder path history/foo. The contract states no precedence.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing precedence or a refusal changes the public lookup promise of trace show; the Issue is decision-needed."
  },
  "options": [
    "A: precedence: within each searched .concorde, a name is tried among the roots in the order they are registered (in Concorde: current tasks, history, unbound runs, lobby), so a current task wins; the other node is shown by its folder path (history/<key>); add a scenario with a reused task name",
    "B: refuse an ambiguous name with a new code (ambiguous_node) naming every match and asking for a path"
  ],
  "recommendation": "A: it is the current behaviour, the live task is what a user means by its name, and the path form already selects the closed one",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:34:29Z

r3-kernel-tracing, early escalation of all 7 decision-needed Issues (escalations 1-7; full chains with options in the decision log). Work on the 10 others continues meanwhile.
1 child_folder_namespace (I-52c3229f): reader skips answers/reports/runtime/__pycache__/dot folders. Rec A: find children by trace.json alone, drop the name list (contract already says so; no current trace changes).
2 duration_source (I-83630d27): duration is host-observed today everywhere. Rec A: specify duration_seconds as observed wall-clock time; agent-reported rule covers tokens, cost, turns only. Changes a requirement's wording.
3 transaction_allowed_paths (I-8823a8cb): Rec A: exact match of canonical project-relative file paths, no prefixes/patterns, unmatched entries ignored (current behaviour).
4 trace_record_damage_and_versions (I-a8c3b519): today one damaged descendant record fails the whole show (and list), a record lacking id raises KeyError. Rec B: show damaged/unsupported records as status unreadable nodes, totals over readable nodes only, stored schema_version 1 only, no migration. Adds a view status value (contract change for readers). Option A = strict refusal naming the folder.
5 retention_partial_config (I-b956d670): Rec A: all periods optional with their defaults (accepts more input, refuses nothing accepted today).
6 artifact_schema_recognition (I-e0329c20): Rec A: document current behaviour (id nonempty string, rule fires on an items schema JSON-equal to the library's schema.ARTIFACT).
7 task_history_name_collision (I-e6189044): Rec A: roots tried in registration order, so a current task wins over a same-named history key; history node by path history/<key> (current behaviour).
Only 2, 4 (and 5 in the accepting direction) change a promise users rely on; 1, 3, 6, 7 document current behaviour. No earlier developer decision is touched that I know of.

It carries escalation(s) 1, 2, 3, 4, 5, 6, 7.

## Answer to report(s) 1 of the task session, 2026-10-13T11:34:45Z

Escalations 1-7 (main agent), each your recommendation: 1 A (children by trace.json alone). 2 A (duration_seconds is the wall-clock time Concorde observed; agent-reported figures cover tokens, cost and turns). 3 A (exact canonical project-relative paths). 4 B — a damaged or unsupported record shows as a node with status unreadable that carries the reason (the read error, with path), totals over readable nodes only, only stored schema_version 1 is read; bump the view contract. 5 A (every retention period optional with its default). 6 A (document current artifact rule). 7 A (roots in registration order; a closed task by history/<key>).

## Task session decisions (2026-10-13)

Implementation of the main agent's answers 1-7 and of the preferred-fix and suggestion Issues:

- I-52c3229f (answer 1 A): reader.py drops NOT_NODES; children and identity search take every
  real folder holding trace.json. Tracing contracts say Tracing reserves no folder name; scenario
  `scenario.tracing.children-any-folder`.
- I-83630d27 (answer 2 A): req.tracing.reported-usage, the node contract's semantics and the entry
  say duration_seconds is the wall-clock time Concorde observed; tokens, cost and turns stay
  agent-reported. No code change (node.py already computes it). Node contract version kept at 5:
  the wording now states the behaviour the code always had.
- I-8823a8cb (answer 3 A): the transaction contract defines allowed paths as exact project-path
  file paths; scenario `scenario.kernel.transaction-exact-allowance` with test.
- I-a8c3b519 (answer 4 B): reader.view refuses the requested node with node_unreadable when its
  record is missing, unreadable, no JSON object, of a schema_version other than 1 or breaks
  NODE_SCHEMA; below it (and for list's top nodes) it shows a node with status `unreadable`, kind
  null, its folder name as id and a new view field `reason` (the read error naming the file);
  children are still read; totals count only readable nodes. View contract 2 -> 3 (kind nullable,
  status `unreadable`, field `reason`). I chose a separate `reason` field rather than reusing
  `error` (an error link) or `outcome` (a producer's snake_case code). Validation against
  NODE_SCHEMA on read (structure only, not the kind registration) so that an old record of a kind
  no part registers any more stays readable. Scenario `scenario.tracing.unreadable-node`.
- I-b956d670 (answer 5 A): configuration contract 3 -> 4 drops the required periods; scenario
  `scenario.tracing.prune-configured` (only history_days given; the unbound default applies).
- I-e0329c20 (answer 6 A): the Kernel contract states id is a nonempty string, gives the artifact
  schema literally and says the uniqueness rule applies to an items schema JSON-equal to it; a test
  checks the documented schema equals schema.ARTIFACT.
- I-e6189044 (answer 7 A): Reading traces states registration-order precedence and the
  `history/<key>` path; scenario `scenario.tracing.name-collision`.
- I-f63d2035 (preferred-fix): locate accepts a folder (absolute or relative) only inside a placed
  registered root of a searched .concorde, or inside the binding's workspace folder (which `show`
  already searches); otherwise unknown_node. Scenario `scenario.tracing.folder-in-roots`.
- I-f39407b5 (preferred-fix): retention removes the top folder's trace.json and the folder itself
  last, and writes the record back when the folder's rmdir fails, rather than shutil.rmtree. Test
  fails only the top folder's rmdir (verified to fail on the old code).
- I-8eede0bd (preferred-fix): write_marker cleans the temporary file inside the OSError handler;
  a refused cleanup becomes a second cause of the system_error; an interruption still cleans up.
- I-8c257662 (preferred-fix): contract, requirement and entry distinguish a kill during the writes
  from a kill during restoration; scenario `scenario.kernel.transaction-killed-restoring`, tested
  with a subprocess killed by os._exit during restoration.
- I-b3951e38 (preferred-fix): binding-whole names a non-absolute-real root as a contract break and
  leaves a valid but foreign root to binding-own-root, which now applies only to absolute real
  paths; binding-refused scenario gains the symbolic-link root case (already tested).
- I-52847f1a (preferred-fix): prune split into prune, prune-dry-run, prune-configured and
  prune-retried with explicit states and invocations; kind-registered split into the refused
  writes and kind-registered-written; show-task states no other node recorded usage.
- I-74365250 (preferred-fix): Tracing's uses of the Kernel relies also on
  req.kernel.registration-stable, registered-dialect and typed-checked, and includes
  document.kernel.contracts (the typed-value section has no identity of its own, so relies_on
  alone would not select it); the explanation links them.
- Suggestions applied: I-1485ff65 (active subjects in registration-stable and busy-lock-named),
  I-ec99c84f (conditions first in marker-refuses-commits and binding-whole), I-1dc98ddb (marker
  scenario split into separate steps and assertions).

## Report 2 to the main agent (Review流程), 2026-10-13T12:07:10Z

r3-kernel-tracing delivered: delivery commit dae9e74e2 (work commit 4dc6651e2). task-validation ready (28 checks passed; 10 warnings, all in other Modules' Specs: spec-tooling/spec and worker-harness/workers sentence length or unlinked terms). Full suite: 1482 passed, 5 skipped.
Resolves all 17 Issues (added with task resolve):
- Decision-needed, per answers 1-7: I-52c3229f (no reserved child folder names), I-83630d27 (duration is the time Concorde observed; reported-usage reworded), I-8823a8cb (exact allowed paths + scenario), I-a8c3b519 (status unreadable with a new view field reason; view contract 2->3; requested node still node_unreadable; list shows a damaged top node as unreadable), I-b956d670 (all periods optional; configuration contract 3->4), I-e0329c20 (artifact schema stated literally, rule fires by JSON equality), I-e6189044 (registration-order precedence, history/<key> path).
- Preferred-fix: I-f63d2035 (folder addresses accepted only inside placed registered roots or the binding's workspace folder), I-f39407b5 (retention writes the top record back when the final rmdir fails), I-8eede0bd (marker cleanup failure becomes a second cause of system_error), I-8c257662 (kill during restoration specified + subprocess test), I-b3951e38 (binding_invalid vs binding_misplaced split), I-52847f1a (prune split into 4 scenarios, kind-registered split, show-task fixture constrained), I-74365250 (Tracing relies on 3 Kernel typed-value requirements and includes document.kernel.contracts, because the typed-value section has no identity relies_on could select).
- Suggestions applied: I-1485ff65, I-ec99c84f, I-1dc98ddb.
My own choices (in the log): a separate view field reason, rather than reusing error or outcome; reader validation against NODE_SCHEMA without kind registration, so old records of unregistered kinds stay readable; node contract kept at version 5, since the duration wording now states existing behaviour.
Nothing open.

## Closed: merged, 2026-10-13T14:43:14Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit dae9e74e219257533a6e42b8dbe9efd4fbb6f6fe into main and closed it as merged. Nobody answers a report after that.
