# Decision log: native-session-records

Goal: Derive task session trace nodes (usage, end, status) and transcript lookup from Claude Code's own records, and keep the Claude worker result envelope's permission_denials, modelUsage and duration_api_ms
## Brief (main agent, 2026-09-30)

The developer asked to reuse what Claude Code and pi already record instead of Concorde building
the same information itself, and approved these three changes after the main agent's assessment:

1. **Task session nodes from Claude Code's own records.** A task session node is written with
   status `unknown`, no `ended_at` and null usage (`record_session` in `src/concorde/tasks/store.py`),
   so `trace show <task>` leaves out the task session's own cost, usually the largest part. When
   a task ends and `keep_transcripts` keeps the transcript, derive from Claude Code's native
   records and write into the session node:
   - usage: token counts summed from the transcript's `assistant` records' `message.usage`
     (count each `message.id` once: one API message may span several records), and `turns`;
     `cost_usd` only from the transcript's last `cost-state` record (`totalCostUSD`) when there is
     one, otherwise null. Concorde never keeps a price table of its own. Put the per-model split
     (`modelUsage` of `cost-state`, or the per-model token sums) in the node's content.
   - `ended_at` / duration from the transcript's timestamps (first to last).
   - status from `claude agents --json --all` (`state`, e.g. `done`), mapped onto the node
     statuses; keep `unknown` when Claude Code cannot say.
   The history keeps only `trace.json` after the 30-day conversation-record retention, so the
   derived figures must be written into the node, not computed at read time.
2. **Find a task session's transcript by its exact session id.** `find_transcript`
   (`src/concorde/tasks/session.py`) globs `<short>*.jsonl` and fails on several matches. Resolve
   the short id reported by `claude --bg` to the full `sessionId` with `claude agents --json --all`
   (record the full id in the session node when it is learnt), and open
   `projects/<derived cwd folder>/<sessionId>.jsonl` directly; keep a detailed error when it
   cannot be resolved. Whether `claude --bg --session-id <uuid>` works was not verified; the task
   session may test it and use it instead if it works, recording the decision.
3. **Keep Claude worker envelope fields Concorde drops.** In `ClaudeStream.conclude`
   (`src/concorde/harness/claude_backend.py`) keep `permission_denials` (evidence for
   Dogfooding's boundary cases), `modelUsage` and `duration_api_ms` in the round's content
   (the `info`/round record), not in the uniform usage fields.

Out of scope (decided with the developer): replacing the worker progress file's `last_action`,
OpenTelemetry export, and `harness/timing.py`.

Specs first: state these promises in the Specs of Tracing (what a session node records and where
its figures come from), Task sessions / Tasks (how the transcript is found and the node finished)
and Workers (the kept envelope fields), then the code and tests. Real `claude` calls in tests
must be faked; use recorded transcript shapes (a `cost-state` record looks like
`{"type":"cost-state","sessionId":…,"totalCostUSD":…,"totalAPIDuration":…,"modelUsage":{"<model>":{"inputTokens":…,"outputTokens":…,"cacheReadInputTokens":…,"cacheCreationInputTokens":…,"costUSD":…}}}`;
background-session transcripts often lack it). Naming, structure and the exact content fields are
the session's to decide; escalate anything that changes another Module's promises.

## Task session decisions (2026-09-30)

- **`claude --bg --session-id` not used.** It could not be tested: starting a background session
  from inside this task session's sandbox fails (`EROFS … mkdir ~/.claude/jobs/<id>`). The probe
  did show that the job's short id then differs from the uuid prefix, so the short id alone would
  not give the id either. The full id is resolved with `claude agents --json --all` (entry `id` =
  the reported short id → `sessionId`, `cwd`, `state`): at the start, best effort (a failed lookup
  never fails the start; the node records `session_id` null), and again at the task's end for a
  node that lacks it. The transcript is opened as `projects/<derived cwd>/<sessionId>.jsonl`, else
  the one file of that exact name in any project folder; no glob on the short id remains.
- **Observed on 2026-09-30 (Claude Code 2.1.285):** `claude agents --json --all` run inside a task
  session's sandbox (private PID namespace) reports the live session itself as `failed` while its
  job state says `working`; a session idle and waiting for its next message is `done`. So only the
  close (main agent / MCP server, outside any task session sandbox) asks for states; written into
  the Task sessions Spec and the code comment.
- **Status mapping:** `done` → `ok`, `failed` → `failed`, anything else (e.g. `working`) or not
  listed → `unknown`; the node's `outcome` is Claude Code's state (snake_case), null when none.
- **Usage source:** tokens from the `assistant` records of the kept transcript and of the subagent
  transcripts copied under `transcript/subagents/*.jsonl` (each `message.id` once, the last record
  of a message wins; `<synthetic>` model records skipped). Subagents are included because they are
  part of the session's own consumption and are no trace nodes of their own, and `cost-state`'s
  cost includes them. `turns` = the distinct API messages. Duration and `ended_at` from the main
  transcript's first and last timestamps. `cost_usd` = last `cost-state`'s `totalCostUSD` only when
  no `assistant` record follows it in the transcript (a stale account is not reported), else null.
  Observation: across 250 local transcripts the last `cost-state` was never followed by an
  assistant record; `cost-state`'s own token counts are higher than the transcripts' sums (they
  include Claude Code's side calls such as the auto-mode classifier), and they are kept as
  `model_usage` in the content, not used for the uniform token fields.
- **Session trace content → version 2** (`contract.task-session.session-trace`): adds
  `session_id`, `claude_state`, `models` (per-model tokens and messages from the transcripts) and
  `model_usage` (`cost-state`'s `modelUsage` as written). Session nodes of tasks open across the
  upgrade still hold version-1 content; the close rewrites them as version 2
  (`store.session_content`), tested.
- **A session whose transcript cannot be kept** still gets its session id and status written; its
  usage and `ended_at` stay null; the warning text is unchanged in shape (now names the exact
  `<sessionId>.jsonl` or what `claude agents` answered).
- **`keep_transcripts` renamed `finish_sessions`** since it now also finishes the node.
- **Worker round content → version 2** (`contract.workers.worker-round-trace`): `agent.claude` now
  also keeps `permission_denials`, `modelUsage` and `duration_api_ms` under the envelope's own
  names, null when the envelope lacks them. The schema of `agent` is unchanged (an object); the
  version bump records the behaviour change. Old round nodes are never rewritten, so no upgrade
  path is needed.
- **Tracing** gains `req.tracing.reported-usage` (usage is what the agent program reported, never
  Concorde's own price computation) and a paragraph in "What a node records"; its node contract is
  unchanged.

## Delivered (task session, 2026-09-30)

Verified: full suite 786 passed (4 skipped), `build --check` and `spec-validation` clean,
`task-validation` ok and ready with no blocking findings. Work commit 6c9d3753; delivery commit
9555c3f8 on `concorde/native-session-records`. Left out: `docs/using-concorde.md` still says only
that the close copies each session's transcript into the trace. It is not wrong, but it does not
mention the session's figures. The file is outside this task's Modules.

## Merge by another main agent (2026-09-30)

This task's main agent `concorde-63` is no longer reachable (not in ListAgents), so its delivery
report was never answered: the main-session-name defect being fixed in task
`main-session-rebind`. The developer approved that main agent "Tasks plan review operation
[be81ec]" (formerly `concorde-d1`) merges it before that fix, since both touch `module.tasks` and
`module.task-session`.

## Closed: merged, 2026-09-30T11:44:43Z
