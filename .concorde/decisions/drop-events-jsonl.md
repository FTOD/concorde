# Decision log: drop-events-jsonl

Goal: Remove the leftover events.jsonl (event stream of the removed pi task-session rounds) from Tracing's conversation records: Specs, retention code and tests

## Task brief (main agent, 2026-10-02)

**Developer's decision.** The developer asked to investigate the mismatch between Tracing's
conversation records, which name `events.jsonl`, and the code, which never writes such a file, and
to fix it.

**Finding (main agent).** `events.jsonl` was the event stream of a pi task session's rounds
(`sessions/<s>/rounds/<n>/events.jsonl`). Commit `fdc97452` ("Drop pi from the main-session
side") removed pi task sessions and their rounds but left the name behind. No producer writes it
today: a worker round's standard output (Claude Code `stream-json`, pi's JSON events) is only
parsed as it arrives, and the worker's transcript, which holds the same conversation, is kept as
`transcript.jsonl`. So nothing new needs to be recorded; the fix is to remove the leftover.

**Decision taken without the developer (main agent):** do not add a kept worker event stream;
remove the leftover. Reason: the stream duplicates the transcript, and the round's reported usage
and envelope fields are already kept in the round node's usage and content.

**Scope.** In module.tracing:
- `specs/concorde/tracing/contracts.md` (~line 525): conversation records are every file
  `transcript.jsonl` and every folder `transcript/`, transcripts of task sessions and worker runs;
  drop "their event streams" and `events.jsonl`.
- `specs/concorde/tracing/module.md` (~line 236, Retention): drop "and their event streams".
- `specs/concorde/tracing/scenarios.md` (`scenario.tracing.prune`): drop "and event streams".
- `src/concorde/tracing/retention.py`: docstring and `CONVERSATION_FILES`.
- `tests/concorde/tracing/test_tracing.py` (~line 340): drop the pi-round `events.jsonl` fixture.

**Left to the session.** Whether the generic examples "a transcript, an event stream or a log"
(`requirements.md:69`, `module.md:283`, `contracts.md:467`) still read right; they describe a kind
of file, not a produced one, so change them only if they now mislead. Whether the Tracing
configuration contract's version must change (it should not, the configuration's shape is
unchanged). Check nothing else in the repository (docs, docsite, e2e scripts) names
`events.jsonl` as a trace file.

Verify with build, spec-validation and the tracing tests, then task-validation and delivery.

## Task session decisions (2026-10-02)

- **Generic examples changed.** "a transcript, an event stream or a log" (`requirements.md`
  req.tracing.large-by-reference, `module.md` design, `contracts.md` node contract) now reads "a
  transcript or a log". Reason: no trace node keeps an event stream file any more, so the example
  suggested a file nobody writes; the requirement's meaning (large content is referenced) is
  unchanged.
- **Contract versions unchanged.** `contract.tracing.configuration` stays version 3: its shape is
  unchanged and its semantics defer to the layout's definition of conversation records; no
  current producer writes `events.jsonl`, so retention removes the same files of every history
  current Concorde writes.
- **Historical decision logs left alone.** `.concorde/decisions/{decision-logs-in-git,legacy-records-history,tracing}.md`
  name `events.jsonl`; they record past decisions and are not changed.
- **Observed: legacy files in the local history.** The primary worktree's untracked
  `.concorde/history/` holds 13 `events.jsonl` files (64 MB) from pi task-session rounds of
  2026-09-26..28. After this change retention no longer removes them; reported to the main agent
  as an optional one-off cleanup outside the task (rapid-iteration rule: no compatibility code).

## Report 1 to the main agent (concorde-5b), 2026-10-02T10:13:25Z

Delivered: c0088bc0 (concorde: deliver drop-events-jsonl) on concorde/drop-events-jsonl, on top of acccd5b6. Readiness ready: 6 changed paths, 20 checks passed, 0 warnings. Changes in module.tracing: conversation records are now every transcript.jsonl and every transcript/ folder (contracts.md layout, module.md Retention, scenario.tracing.prune, retention.py CONVERSATION_FILES and docstring); the pi-round events.jsonl fixture is gone from test_tracing.py. Decisions I took: (1) the generic examples 'a transcript, an event stream or a log' (req.tracing.large-by-reference, module.md design, contracts.md node contract) now read 'a transcript or a log', since no node keeps an event stream file any more; the requirement's meaning is unchanged. (2) contract.tracing.configuration stays version 3: shape unchanged, semantics defer to the layout, and no current producer writes events.jsonl. (3) Historical decision logs under .concorde/decisions/ that name events.jsonl are left as they are. Nothing else in docs, docsite or e2e scripts names events.jsonl. Open, for you (not blocking, outside the task): the primary worktree's untracked .concorde/history/ still holds 13 events.jsonl files (64 MB) from pi task-session rounds of 2026-09-26..28. Retention no longer removes them, so they stay unless deleted by hand, e.g. find .concorde/history -name events.jsonl -delete. No Issues resolved; no escalations.

## Closed: merged, 2026-10-02T10:13:39Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit c0088bc0f68f37b9d8fdafa36563378de4056ecf into main and closed it as merged. Nobody answers a report after that.
