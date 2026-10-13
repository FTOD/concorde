# Decision log: r3-distribution

Goal: Fix the remaining open Issues of Distribution (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (17, listed in `resolves`; 4 of them decision-needed), all medium or
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

## Escalated to the main agent, 2026-10-13T11:34:37Z

- **task-session** task session (task r3-distribution): `mcp_protocol_compatibility`
  I-01908e4beef25f9189ade176f5aa466e (decision-needed, medium): a live project MCP server host keeps the protocol its session started with, while every call runs current code; the Specs define no compatibility rule between an old host and a new call process (call object, answer line, reroute, --tools). Found: contract.distribution.mcp-call has no version field and additionalProperties false; the host turns any answer it cannot read into the generic call_failed. The {"error": <link>} answer line is the one form every version so far understands.
  Not handled here (decision): Choosing a support window or restart policy changes the promise of the Project MCP server contract (Distribution's own, but a promise sessions rely on during an update).
  Options: A: the host sends its protocol version in the call object (absent means 1); the call process answers only its own version and otherwise refuses with a new refusal host_outdated (environment) whose remediation is to reconnect the server (/mcp) or restart the session; the {"error": <link>} answer line is frozen for all versions. Adds a field and a refusal to the contracts; changes no earlier developer decision.; B: the call code keeps supporting older host protocols for a stated window (for example one version back); more code and tests, every protocol change carries a compatibility branch.; C: Spec-only: state that an update changing the host protocol requires restarting every live session, and that a mismatch fails as call_failed; no code change, failure is generic.
  Recommendation: A: cheap, explicit, keeps the developer's current-code rule (every call answered by current code), and tells the session exactly how to recover.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-distribution)",
  "code": "mcp_protocol_compatibility",
  "detail": "I-01908e4beef25f9189ade176f5aa466e (decision-needed, medium): a live project MCP server host keeps the protocol its session started with, while every call runs current code; the Specs define no compatibility rule between an old host and a new call process (call object, answer line, reroute, --tools). Found: contract.distribution.mcp-call has no version field and additionalProperties false; the host turns any answer it cannot read into the generic call_failed. The {\"error\": <link>} answer line is the one form every version so far understands.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing a support window or restart policy changes the promise of the Project MCP server contract (Distribution's own, but a promise sessions rely on during an update)."
  },
  "options": [
    "A: the host sends its protocol version in the call object (absent means 1); the call process answers only its own version and otherwise refuses with a new refusal host_outdated (environment) whose remediation is to reconnect the server (/mcp) or restart the session; the {\"error\": <link>} answer line is frozen for all versions. Adds a field and a refusal to the contracts; changes no earlier developer decision.",
    "B: the call code keeps supporting older host protocols for a stated window (for example one version back); more code and tests, every protocol change carries a compatibility branch.",
    "C: Spec-only: state that an update changing the host protocol requires restarting every live session, and that a mismatch fails as call_failed; no code change, failure is generic."
  ],
  "recommendation": "A: cheap, explicit, keeps the developer's current-code rule (every call answered by current code), and tells the session exactly how to recover.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:38Z

- **task-session** task session (task r3-distribution): `prompt_front_matter_keys`
  I-79546f6419415e489f2bc8898e6e2baf (decision-needed, medium): the prompt parser (src/concorde/distribution/prompt_resolver.py:160) refuses every front-matter key but audience with CONCORDE-PROMPT-AUDIENCE-002; req.distribution.include-audience requires the audience but says nothing about other keys. No prompt under prompts/ uses another key today.
  Not handled here (decision): Deciding which front-matter keys a prompt may carry fixes the prompt authoring interface that the build promises.
  Options: A: document the current rule: audience is the only front-matter key, and any other key is refused (catches typos such as audiance). Spec change only; promise unchanged in practice.; B: accept and ignore any other key (lets authors add metadata; a mistyped key passes silently). Code and Spec change.; C: accept a fixed list of extra keys (for example description). Code and Spec change.
  Recommendation: A: it states the behaviour the build already has and keeps typos from passing.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-distribution)",
  "code": "prompt_front_matter_keys",
  "detail": "I-79546f6419415e489f2bc8898e6e2baf (decision-needed, medium): the prompt parser (src/concorde/distribution/prompt_resolver.py:160) refuses every front-matter key but audience with CONCORDE-PROMPT-AUDIENCE-002; req.distribution.include-audience requires the audience but says nothing about other keys. No prompt under prompts/ uses another key today.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Deciding which front-matter keys a prompt may carry fixes the prompt authoring interface that the build promises."
  },
  "options": [
    "A: document the current rule: audience is the only front-matter key, and any other key is refused (catches typos such as audiance). Spec change only; promise unchanged in practice.",
    "B: accept and ignore any other key (lets authors add metadata; a mistyped key passes silently). Code and Spec change.",
    "C: accept a fixed list of extra keys (for example description). Code and Spec change."
  ],
  "recommendation": "A: it states the behaviour the build already has and keeps typos from passing.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:38Z

- **task-session** task session (task r3-distribution): `prompt_include_parameters`
  I-8d91d03666ba50c9a52d83f027037bb7 (decision-needed, medium): req.distribution.prompt-includes does not state parameter scope across nested includes, substitution order, duplicate keys or unprovided names. The resolver already behaves as follows: a line's KEY=value bindings fill only the included prompt's own text, never the prompts it includes in turn; they are filled before that prompt's own include lines are read, so a prompt passes a value on explicitly with KEY={KEY} on its own include line; a {KEY} its include line does not bind is refused (CONCORDE-PROMPT-UNRESOLVED-001), so a root's own {KEY} is always refused; a duplicate key on one line is refused; a value is not substituted again; {{name}} becomes {name} only at the end, after every include is expanded; braces that are not {name} or {{name}} stay as they are; an unused binding is accepted.
  Not handled here (decision): Writing these semantics down fixes the include interface the build promises to prompt authors; the Issue's chair judged it a promise change.
  Options: A: specify the current behaviour exactly as listed (Spec only, plus a scenario or test for a nested include and an unbound name).; B: make bindings inherit through nested includes (a parent's KEY reaches its includes unless rebound); behaviour change in the resolver and the prompts relying on explicit passing.; C: as A, and also refuse an unused binding (catches a mistyped key on an include line); a small behaviour change, existing prompts must be checked.
  Recommendation: A: it documents what every rendered prompt already relies on; no prompt changes.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-distribution)",
  "code": "prompt_include_parameters",
  "detail": "I-8d91d03666ba50c9a52d83f027037bb7 (decision-needed, medium): req.distribution.prompt-includes does not state parameter scope across nested includes, substitution order, duplicate keys or unprovided names. The resolver already behaves as follows: a line's KEY=value bindings fill only the included prompt's own text, never the prompts it includes in turn; they are filled before that prompt's own include lines are read, so a prompt passes a value on explicitly with KEY={KEY} on its own include line; a {KEY} its include line does not bind is refused (CONCORDE-PROMPT-UNRESOLVED-001), so a root's own {KEY} is always refused; a duplicate key on one line is refused; a value is not substituted again; {{name}} becomes {name} only at the end, after every include is expanded; braces that are not {name} or {{name}} stay as they are; an unused binding is accepted.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Writing these semantics down fixes the include interface the build promises to prompt authors; the Issue's chair judged it a promise change."
  },
  "options": [
    "A: specify the current behaviour exactly as listed (Spec only, plus a scenario or test for a nested include and an unbound name).",
    "B: make bindings inherit through nested includes (a parent's KEY reaches its includes unless rebound); behaviour change in the resolver and the prompts relying on explicit passing.",
    "C: as A, and also refuse an unused binding (catches a mistyped key on an include line); a small behaviour change, existing prompts must be checked."
  ],
  "recommendation": "A: it documents what every rendered prompt already relies on; no prompt changes.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:38Z

- **task-session** task session (task r3-distribution): `parts_index_shape`
  I-b8ca0e70fe205a53992b6305ff179f35 (decision-needed, medium): the contract gives the parts index generated/parts.json only as a key list. The code (parts.index_of) writes {schema_version: 1, parts: {<part>: {module: <module id>, depends_on: [part names], commands: [command names], mcp_tools: [tool names]}}}, and parts.index reads an unreadable index or one without parts as empty, so an absent command or tool is then refused without naming its part. The index is written by Distribution's build and read only by Distribution. Linked: I-ff399ec53cc355e6a495d379cc1f558a (preferred-fix, mine) asks that runtime discovery read no registration of a part the receipt does not name; doing that needs the directory of each named part (worker harness lives in worker_harness/, workflow in workflows/), which the index can give.
  Not handled here (decision): The Issue's chair marked the representation choice decision-needed; it fixes a contract of Distribution's.
  Options: A: specify the index exactly as the code writes it (names, not registration objects) with a populated example, add a directory field per part (its directory under src/concorde/) used to read only installed parts' registrations, bump schema_version to 2, and treat an index of another version or an unreadable one as naming no owner.; B: specify the current shape only (no directory); fix I-ff399 instead by reading every registration file's part name but validating and loading only installed ones (still reads absent parts' files, so it only half meets 'loads no registration').; C: index carries full registration objects; larger file, duplicates registrations.
  Recommendation: A: one internal contract, exact, and it lets I-ff399 be fixed fully.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-distribution)",
  "code": "parts_index_shape",
  "detail": "I-b8ca0e70fe205a53992b6305ff179f35 (decision-needed, medium): the contract gives the parts index generated/parts.json only as a key list. The code (parts.index_of) writes {schema_version: 1, parts: {<part>: {module: <module id>, depends_on: [part names], commands: [command names], mcp_tools: [tool names]}}}, and parts.index reads an unreadable index or one without parts as empty, so an absent command or tool is then refused without naming its part. The index is written by Distribution's build and read only by Distribution. Linked: I-ff399ec53cc355e6a495d379cc1f558a (preferred-fix, mine) asks that runtime discovery read no registration of a part the receipt does not name; doing that needs the directory of each named part (worker harness lives in worker_harness/, workflow in workflows/), which the index can give.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue's chair marked the representation choice decision-needed; it fixes a contract of Distribution's."
  },
  "options": [
    "A: specify the index exactly as the code writes it (names, not registration objects) with a populated example, add a directory field per part (its directory under src/concorde/) used to read only installed parts' registrations, bump schema_version to 2, and treat an index of another version or an unreadable one as naming no owner.",
    "B: specify the current shape only (no directory); fix I-ff399 instead by reading every registration file's part name but validating and loading only installed ones (still reads absent parts' files, so it only half meets 'loads no registration').",
    "C: index carries full registration objects; larger file, duplicates registrations."
  ],
  "recommendation": "A: one internal contract, exact, and it lets I-ff399 be fixed fully.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:34:46Z

r3-distribution: early report of the four decision-needed Issues (escalations 1-4), as the brief asks. I continue meanwhile with the 13 others; I-ff399 (runtime reads absent parts' registrations) waits for escalation 4 since its full fix needs a directory field in the parts index.
1. I-01908 mcp_protocol_compatibility: no compatibility rule between a live old host and a new call process. Options A version field + host_outdated refusal (recommended), B support window, C Spec-only restart rule. A changes the internal MCP contracts (new field, new refusal), no earlier developer decision.
2. I-79546 prompt_front_matter_keys: parser refuses keys other than audience; Spec silent. Recommend A: document the current audience-only rule (no behaviour change).
3. I-8d91 prompt_include_parameters: scope/order/duplicates unspecified. Recommend A: specify the resolver's current semantics (bindings fill only the included prompt's own text, passed on explicitly; unbound {KEY} refused; duplicates refused; {{name}} unescaped last). No behaviour change.
4. I-b8ca parts_index_shape: index form not exact. Recommend A: specify the current shape plus a directory per part, schema_version 2; enables the full I-ff399 fix. Distribution-internal.
None of the recommended options changes an earlier developer decision; only 1A adds a user-visible refusal.

It carries escalation(s) 1, 2, 3, 4.

## Answer to report(s) 1 of the task session, 2026-10-13T11:35:00Z

Escalations 1-4 (main agent), each your recommendation: 1 A — a protocol version field between the live MCP host and the call process; a mismatch refuses host_outdated, telling the session to reconnect /mcp or restart (no support window: rapid-iteration rule); add it to the main-session guidance where the server is described. 2 A — document the audience-only front-matter rule. 3 A — specify the include resolver's current semantics. 4 A — current index shape plus a directory per part, schema_version 2; then fix I-ff399 fully.

## Task session decisions (r3-distribution)

- I-03db (preferred-fix): `scripts/concorde.py`, the one entry of the checkout and of the installed launcher, sets `sys.dont_write_bytecode` for `build --check` before importing Concorde and passes `-B` when it runs again on the checkout's `.venv`. `python -m concorde` (the MCP server's last fallback, never used for `build --check`) is left alone: by the time `__main__` runs, the package is imported already. Test: a cache-free package copy whose `.venv` makes the command run again stays file-for-file unchanged.
- I-a125 (preferred-fix): the reachability inventory counts a Markdown symbolic link under `prompts/` as a prompt (rather than refusing links separately), since no include may reach a prompt through a link; an orphan link therefore fails the build as unreachable, naming it.
- I-a58e (preferred-fix): `guidance.compose` keeps each render byte for byte and adds one newline after each render but the last (a missing final newline is supplied), which is one blank line between renders ending in a newline. Every current render starts without and ends with one newline, so the generated outputs are unchanged.
- I-5481 (preferred-fix): `update_main` refuses a receipt that is no object, or names a source that is no path, as `update_source_missing` (input), and an OS refusal to start the installer with the new `update_start_failed` (environment, added to the refusal table). Tests call `update_main` in process.
- I-01908 (escalation 1, answer A): protocol `2` named by every call object as `protocol` (absent = 1); the call process refuses any other with `host_outdated` (environment; options /mcp reconnect or restart) before loading any part's code. `--tools` output is declared append-only (only gains fields), so it needs no version. New req `req.distribution.mcp-host-protocol`, scenario `mcp-host-outdated`, contract `mcp-call` version 2, refusal row. Guidance: the main agent asked for the main-session guidance where the server is described; I put the paragraph in Distribution's own section `prompts/guidance/distribution/skill.md`, which is composed into that same skill, because `prompts/main-session/` belongs to module.main-session (task r3-task-session-main edits it in parallel) and the refusal is Distribution's.
- I-5d30 (preferred-fix): `Rethread` carries how the call is now served; the call continues on its new thread with its reroute used (`rerouted`), so a second reroute is `call_failed`.
- I-fcd7 (preferred-fix): the session's thread now works off a queue fed by a reader thread; a call on its own thread that its reroute no longer threads is queued back to the session's thread (after what is queued already). Contract wording changed from "the thread that reads the session" to "the session's thread, one at a time, in the order it arrives". `Calls.call`'s `threaded` default became false (the session thread), as production always passes it.
- I-1aa8 (preferred-fix): `listed` changes only on a tools/list answer; a separate `notified` digest coalesces notifications (once per set of tools not yet told since the last listing). Requirement `mcp-tools-changed` states that coalescing; scenario `mcp-tools-changed-once`.
- I-ccdf (suggestion, applied): the entry's "Current code" bullet keeps the rationale, routing guarantee, tools-changed and protocol/recovery, and links to the contract for commands, messages and routing.
- I-b8ca (escalation 4, answer A): parts index `schema_version` 2; each entry `{module, directory, depends_on, commands: [names], mcp_tools: [names]}` specified as a projection of the registration, with a JSON example (a test checks the example's form against the code's index).
- I-ff399 (preferred-fix, after escalation 4): where the receipt names the parts, `parts.installed` reads only their registrations through the index's `directory`, passes over a named part the index lacks (as the old filter did), and refuses a missing, unreadable or other-version index with `stale_build` instead of falling back to reading every registration (the installer always ships the index with the distribution part, so this only meets a broken copy; reinstalling repairs it). Fixture for the dropped-part install test now adds that part to the copy's own index, as a real older copy's index would.
- I-f26b (preferred-fix): the `framework` fixture writes the index from `parts.index_of(package_parts(...))`; `PartsTests` derive part names from the source registrations; `test_guidance_parts` renders each section through the prompt resolver. Verified by running the Distribution tests with `generated/` moved away: 69 passed.
- I-b345 (preferred-fix): rather than list thousands of Framework and environment files, the receipt's `files` names a directory Concorde owns whole once as its path ending with `/` (`.concorde/framework/`, which holds the own Python environment and prepared files under it; `.concorde/tools/pi-runtime/`), plus the d2 program and both tool records, plus prepared files outside the Framework copy. Earlier ownership is the earlier receipt's `files` plus the paths its `tools` names (so installs made before this change are reconciled too). An install removes earlier-owned paths it no longer owns (whole directories with rmtree, never through a symbolic link); a tool an installed part still needs that `--without-d2`/`--without-pi-runtime` only left out stays and stays owned, so the flags never delete a program in use. Spec Core's `installed_files` skips everything under `.concorde/`, so the directory entries do not reach binding. Install-result contract version 5.
- I-79546 (escalation 2, answer A): `req.distribution.include-audience` now refuses any front-matter key but `audience` and says why (a mistyped key never passes). No code change.
- I-8d91 (escalation 3, answer A): `req.distribution.prompt-includes` lists the resolver's existing value rules (own text only, filled before its own includes, passed on with KEY={KEY}, inserted as is, a key once per line, unused values passed over, an unfilled {KEY} reaching the output fails, {{name}} last, other braces kept). New scenario `build-include-values` with a test (nested pass-on, missing value, duplicate key, extra front-matter key).
- I-9a5f (suggestion, applied): the leftover scenario's GIVEN now states the bytes still match the previous manifest.
- I-f2b0 (suggestion, applied): the repeated follow-up became its own scenario `protocol-manifest-write-alone`, whose GIVEN records the preceding failed bind and whose WHEN runs `--write` once; the existing test verifies it too.
- I-01908 follow-up (my own correction): the protocol number stays `1`, not `2`. The wire format did not change (the field is only added and an absent field means 1), and with `2` every MCP server already running at the merge (the main agent's and every parallel task session's, which cannot use /mcp) would have been refused on every call. The next change a running server cannot read increments it.

## Report 2 to the main agent (Review流程), 2026-10-13T12:18:15Z

r3-distribution delivered: delivery commit 7bb4f44626ca3d735e92cf85be984d7cf22b6b1a (task-validation ready: 28 checks, no Distribution warnings; full suite 1481 passed, 5 skipped). Every one of the 17 Issues in `resolves` is fixed; none stays open.

Decision-needed, as answered (all A):
- I-01908: the call object names `protocol`; the call process refuses any other with `host_outdated` (environment, options /mcp or restart) before loading code. My own correction: the number stays 1 (an absent field means 1), because the wire format did not change and 2 would have refused every MCP server already running at the merge, yours and the parallel task sessions' included. The guidance paragraph is in Distribution's own section prompts/guidance/distribution/skill.md, which is composed into the same main-session skill: prompts/main-session/ is module.main-session's, and r3-task-session-main edits it in parallel.
- I-79546: audience-only front matter documented. I-8d91: the include-value rules documented, with a new scenario and test. I-b8ca: exact index contract, schema_version 2, `directory` per part.

Preferred-fix choices:
- I-ff399: a project reads only its installed parts' registrations through the index; an unusable index is refused with stale_build rather than guessed.
- I-b345: the receipt names whole owned directories once as `path/` (.concorde/framework/, .concorde/tools/pi-runtime/) plus the tool programs and records. An install removes the tools of parts it drops; a tool only left out by --without-* while a part needs it stays. Install-result contract v5.
- I-5d30/I-fcd7: a reroute keeps its one retry across a thread move, and a call no longer threaded goes back to the session's thread through a queue fed by a reader thread.
- I-1aa8: telling the session lists nothing; notifications are coalesced per set of tools.
- I-03db: build --check sets no-bytecode in scripts/concorde.py (and -B on re-exec).
- I-5481: new refusal update_start_failed.
- I-a125: an orphan prompt symlink is unreachable. I-a58e: guidance is byte for byte. I-f26b: fixtures derive the index and renders from the sources.

Suggestions applied: I-ccdf, I-9a5f, I-f2b0.

Open: nothing for the developer. Note: after the merge, an installed project needs `concorde update` for the index v2 (the update ships it with the code).

## Closed: merged, 2026-10-13T14:46:27Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 7bb4f44626ca3d735e92cf85be984d7cf22b6b1a into main and closed it as merged. Nobody answers a report after that.
