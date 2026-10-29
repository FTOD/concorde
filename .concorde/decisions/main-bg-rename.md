# Decision log: main-bg-rename

Goal: Find out how Claude Code moves an interactive main session to the background (session id, ListAgents name, SessionStart hook and its source, CLAUDE_CODE_SESSION_ID), then propose fixes so that a main agent whose session was moved or renamed is always told of its tasks and a task session never waits for a rebind unnoticed; implement only the option the developer chooses

## Task brief (main agent, 2026-10-29)

**Why.** Issue I-b998085ed82e51698e42fff508daa3ac (module.main-session, high, decision-needed) was
reopened on 2026-10-29 as a recurrence; read its second report first. Summary:
- On 2026-10-28 at 07:38:07Z, Claude Code moved the developer's interactive main session
  `concorde-74` (session id `449096d7-605d-4744-8283-a5930bb77a33`) into a background session.
  The new session has session id `5ef40d9f-bd72-42ca-b799-583895bb433f`. Its ListAgents name is its
  automatic title `项目中途停止状态检查`.
- The transcripts are in `~/.claude/projects/-home-scratch-zbai-gpu-concorde/`. The old one ends at
  07:38:07Z. The new one starts with the copied history and an attachment
  `{"type": "session_cron_carry"}` at that time. `claude agents --json` lists the new session as
  `kind: background`, started at 07:38:08Z.
- Neither transcript holds any output of the SessionStart hook (`.claude/settings.json`, matcher
  `startup|resume|compact`, `concorde task main-hook`). There was none at the move, and none when the
  session re-read its instruction files on 2026-10-29T01:48Z. Yet task checks-bwrap-compat was not
  ended then. Unknown whether the hook did not run or its output was not recorded.
- Task checks-bwrap-compat delivered at 2026-10-28T07:51:55Z. Its report to `concorde-74` reached
  nobody, and it waited 18 hours on `concorde task wait checks-bwrap-compat --rebound concorde-74`
  until the developer noticed.

**History of this problem.** Read these before proposing anything:
- I-2dd7448e (2026-09-29, module.task-session). Fixed by task main-session-rebind: reports are
  recorded in the task record, `task rebind`, `task wait --rebound`.
- I-b998085e's first report (2026-10-08). Fixed by task main-rename-hook: the SessionStart hook.
- I-73dcba12 (r4-coordination, `.concorde/decisions/r4-coordination.md`): the recorded main session
  id and the `(this session)` marking. That task verified with headless probes that a resume and a
  compaction keep `CLAUDE_CODE_SESSION_ID`, and that a fresh session, `--fork-session` and `/clear`
  get a new one. A move to the background was never examined.
- Both earlier occurrences also show a restart followed by an automatic title. A move to the
  background may be how main sessions usually get renamed.

**The developer's decision (2026-10-29).** Investigate first, then propose. Do not implement
anything before the developer has chosen.

**Phase 1, investigation.** Establish with evidence, from Claude Code's documentation and from
experiments:
- How an interactive session gets moved to the background: which commands, keys or events
  (daemon, `--bg`, closing the terminal, Remote Control).
- What happens to the session id, the transcript, `CLAUDE_CODE_SESSION_ID` in the new session's
  Bash, the ListAgents name and its `[ref]`.
- Whether SessionStart hooks run for the moved session, and with which `source` and `session_id`.
  Also whether they run when a background session is attached or reloaded later, as when
  instruction files were re-read at 01:48Z.
- Whether any other hook event fires that Concorde could use, such as UserPromptSubmit.
- Whether the new session can learn its former session id or name, for example from the carried
  transcript or the hook input.
- Whether the main agent can give its session a stable name, for example a rename that survives
  the move.

Experiment rules:
- Use throwaway sessions only, in throwaway directories under `/home/scratch.zbai_gpu/tmp`.
- Never touch, stop, move or message the developer's sessions, which are this main agent, its task
  sessions and `scripts-47`.
- Use a cheap model (haiku) for probes.
- If an experiment needs a human at an interactive terminal, describe it exactly and escalate it
  instead of guessing.
- Record every finding with its evidence in this log.

**Phase 2, proposal.** Escalate the options together to the main agent with
`concorde task escalate --by task-session` and a report, each with its trade-offs and your
recommendation. The goal is two guarantees:
- A main agent whose session was moved or renamed is told of its tasks not ended, at the latest at
  the developer's next prompt.
- A task session never waits for a rebind unnoticed.
Directions the main agent has seen so far, which you are not bound to:
- Extend the hook events, for example a cheap UserPromptSubmit check in the primary worktree, or
  SessionStart sources if the move has one.
- Let the hook or the guidance recognise a former session from the moved session.
- A bound or escalation path for `task wait --rebound`.
Keep within the three Modules of this task. Name any other Module a proposal touches.

**Phase 3, after the developer's choice.** Implement it, with the Spec first. Add tests. Then run
`task-validation` and `delivery` from the task worktree.

**Environment notes.**
- uv, node/npm, pi, rg, fd and d2 are under `/home/scratch.zbai_gpu/opt`, linked into
  `~/.local/bin`.
- Keep large files off `$HOME`, which has a 5 GB quota.
- The worker configuration now uses gpt-6.1-sol on pi and claude-opus-5-5 on Claude Code
  (`cb86b1cb9`).

## Task session: phase 1 findings, part 1 (2026-10-29T02:10Z)

Claude Code 2.1.312. Probes ran in the throwaway directory `/home/scratch.zbai_gpu/tmp/bgprobe`
(git repository, `.claude/settings.json` with logging hooks for SessionStart without matcher,
UserPromptSubmit, Stop, SessionEnd, PreCompact; script `$CLAUDE_JOB_DIR/tmp/probe/log_hook.py`
appends each hook input and the hook's `CLAUDE*` environment to `logs/hooks.jsonl` and prints a
`PROBE-HOOK` line). Interactive sessions ran with `--model haiku` in a private tmux server
(`tmux -L bgprobe`) started with a clean environment. A first probe started from this session's
environment inherited `CLAUDE_CODE_CHILD_SESSION=1`, `CLAUDE_JOB_DIR` and this session's name in
its prompt box; it was killed and discarded.

1. **What moved the developer's main session.** `~/.claude/daemon.log`:
   `[2026-10-28T07:38:07.726Z] [bg] bg claimed-spare 5ef40d9f (slash)`. The roster
   `~/.claude/daemon/roster.json` gives the dispatch of 5ef40d9f: `source: "slash"`,
   `launch: {mode: "resume", sessionId: ".../449096d7-....jsonl", fork: true,
   restoresTranscript: true}`, `seed.name: "项目中途停止状态检查"`. So the developer typed the
   `/background` slash command. The daemon handed the conversation to a spare process it had
   pre-started at 06:42:08 (`bg spare spawned host pid=251270`). In the Claude Code bundle, the
   REPL's backgrounding launches the background session with `--resume <transcript>
   --fork-session`, and when the session has no name (`name === undefined`) it generates one
   ("auto" name source). The old transcript ends with
   `{"type": "continued-in", "sessionId": <old>, "continuedInSessionId": <new>}`.
2. **Reproduced.** Interactive probe session `5cbd5048-…`, ListAgents name `bgprobe-70 [dfc178]`
   (an unnamed interactive session's name is `<directory>-<two digits>`, like `concorde-74`).
   After one prompt, `/background` printed `backgrounded · 036d1b06` and the daemon logged
   `bg claimed-spare 036d1b06 (slash)`. `claude agents --json` lists `036d1b06`, kind
   `background`, session id `036d1b06-7b3a-428d-a72b-651c50732075`, name `Session ID and
   ListAgents probe`, which is the session's `ai-title`. The new transcript starts with
   `ai-title` and `agent-name` records of that title. The old transcript ends with
   `session_cron_carry` (02:07:34.273Z) and `continued-in` → `036d1b06-…` (02:07:34.324Z).
3. **Hooks at the move** (`logs/hooks.jsonl`):
   - Old session: `SessionEnd` with `reason: "prompt_input_exit"` at 02:07:34.
   - New session: `SessionStart` with **`source: "fork"`** at 02:07:35, `session_id` the new id,
     `transcript_path` the new transcript, and `CLAUDE_CODE_SESSION_ID` the new id in the hook's
     environment. The input also has `seconds_since_last_response`, `context_tokens`,
     `prompt_cache_likely_expired` and `estimated_cache_write_usd`, and no former session id or
     name.
   - So the move does run SessionStart, but with the source `fork`. Concorde's matcher
     `startup|resume|compact` excludes it. That is why neither of the developer's transcripts holds
     the hook's output: a SessionStart hook that prints records an attachment
     `{"type": "hook_success", "hookEvent": "SessionStart", "hookName": "SessionStart:<source>",
     "content": …}` in the transcript (seen in the probe at startup).
4. **The former session id is recoverable.** The old transcript's `continued-in` record names the
   new session id and is written before the new session's SessionStart runs. Both transcripts lie
   in the same project directory `~/.claude/projects/<slug of cwd>/`. The hook input gives
   `transcript_path`, so a hook can find, in that directory, the transcript whose last
   `continued-in` names its own `session_id`.
5. **UserPromptSubmit** ran for every prompt, interactive (session `5cbd5048`) and after
   `claude attach` in the background session (session `036d1b06`, 02:08:42).

## Task session: phase 1 findings, part 2 (2026-10-29T02:20Z)

6. **The `fork` hook's output reaches the model.** After `claude attach 036d1b06` and a prompt,
   the moved session's transcript holds `hook_success` `SessionStart:fork` (02:07:35.097Z) before
   the prompt's `UserPromptSubmit` record, and the model quoted it from its context as
   "SessionStart:fork hook success: PROBE-HOOK …". So a hook that runs at `fork` is read at the
   developer's next prompt, which is the earliest point the moved session works anyway.
7. **Re-reading instruction files is no new start.** The developer's moved transcript holds an
   `instructions` attachment with `reason: "session_start"` at 2026-10-29T01:48:38Z, the first
   prompt after the move. The daemon log shows no restart of 5ef40d9f then. The re-read belongs to
   the session's start at 07:38 and is delivered with its first prompt, like the hook output in 6.
   No SessionStart ran at 01:48, and none was due.
8. **Stop and reattach.** `claude stop 036d1b06` ran SessionEnd (`reason: "other"`).
   `claude attach 036d1b06` then claimed a spare (`bg claimed-spare 036d1b06 (fleet)`) and ran
   SessionStart with `source: "resume"`, the same session id and the same name. The current
   matcher covers this case.
9. **Names.**
   - Unnamed interactive session: ListAgents `<directory>-<two digits>`; after `/background`, the
     automatic title.
   - `claude -n probe-main`: ListAgents `probe-main`; after `/background` the new session
     `a0f4d3ea-…` is listed as `probe-main`, and its SessionStart `fork` input carries
     `session_title: "probe-main"`.
   - `/rename probe-renamed` in an unnamed session: ListAgents and `claude agents` show
     `probe-renamed` at once; after `/background` the new session `bf9bfe4a-…` keeps it.
   - A SessionStart `startup` hook returning `hookSpecificOutput.sessionTitle` sets the prompt
     box's title only. ListAgents kept `bgprobe2-88`. After `/background` the new session was
     named by that title (`hooktitle-2acf`).
   - A **UserPromptSubmit** hook returning `hookSpecificOutput.sessionTitle` (only when the input
     has no `session_title`) renamed the interactive session at once: ListAgents showed
     `uptitle-7591 [ba2f2d]` in the same turn. After `/background` the new session `132f3c28-…`
     kept `uptitle-7591`.
   - The session id changes on every `/background`, named or not.
   - UserPromptSubmit and SessionStart inputs carry `session_title` once the session has a name or
     title. Without one they carry none.
10. **Claude Code drops a repeated SessionStart output on resume.** In the bundle, `tAe` drops a
    new SessionStart `hook_success` or `hook_additional_context` whose content equals one already
    in the loaded conversation. A hook text that repeats word for word (same source, same tasks)
    is therefore not added again.
11. **Forks that keep their parent.** In the bundle, the `continued-in` record is written only when
    the backgrounding does not keep its parent (`!keepParent`). A copy made while the parent goes on
    (`--fork-session`, the agent view's fork) also starts with SessionStart `fork`, but its parent's
    transcript gets no `continued-in`. So `continued-in` tells a move from a copy.
12. **Costs here.** `task main-hook` takes 0.23–0.52 s. `claude agents --json` takes 0.18–0.22 s.
13. **Not examined.** Remote Control and closing the terminal: the bundle shows no backgrounding on
    terminal close, and the developer's move was the slash command, so neither was probed.
    `PushNotification` from a background session was not probed, since a probe would notify the
    developer.
14. **Cleanup.** Probe background sessions 036d1b06, a0f4d3ea, 2fb6601f, bf9bfe4a and 132f3c28
    were stopped and removed with `claude stop`/`claude rm`. The private tmux server was killed.
    The probe directories and their transcripts are kept as evidence:
    `/home/scratch.zbai_gpu/tmp/bgprobe{,2}`, `~/.claude/projects/-home-scratch-zbai-gpu-tmp-bgprobe{,2}`.
    `claude purge <dir>` removes the transcripts. No developer session was touched.

**Cause of the recurrence.** `/background` makes a new session that starts with SessionStart
`fork`. The hook's matcher `startup|resume|compact` excludes that source; main-rename-hook left
`fork` out on purpose, because "a fork is a second session that must not take over the tasks".
Had the hook run, the new session id would have marked no task as this session. The moved session
also got the automatic title as its name, since the main session was unnamed.

## Escalated to the main agent, 2026-10-29T02:19:21Z

- **task-session** task session (task main-bg-rename): `fix_direction`
  Which fix (or combination) should this task implement for Issue I-b998085e (decision-needed)? Cause established by experiment (decision log, findings 1-14): `/background` forks the main session into a background session with a NEW session id. The new session runs SessionStart with source `fork`, and its output reaches the model at the developer's next prompt. Concorde's matcher `startup|resume|compact` excludes `fork`, which main-rename-hook left out on purpose ("a fork is a second session that must not take over the tasks"). The old transcript ends with Claude Code's record {"type":"continued-in","continuedInSessionId":<new id>}, written before the new SessionStart and only when the parent ends (a copy that keeps its parent gets none), so it tells a move from a copy. An unnamed session's ListAgents name (`<dir>-NN`) becomes the automatic title on the move. A session named with `claude -n`, `/rename` or a UserPromptSubmit hook's `sessionTitle` keeps its name across the move. The ListAgents [ref] changes either way. Stop+attach keeps id and name (source `resume`, already covered).
  | Options:
  | (A) Hook follows the move (module.tasks, module.main-session): matcher `startup|resume|compact|fork`. `task main-hook` follows `continued-in` records in the hook input's transcript directory: a task whose recorded `main_session` continues into this session id is marked "(this session, moved from <id>)", so the guidance's existing reconcile steps rebind it. A `fork` without such a record marks nothing new. The text carries the session id and time, since Claude Code drops a SessionStart output that repeats word for word. Covers every move at the next prompt. No per-prompt cost. Reverses the developer's 2026-10-08 choice to leave `fork` out. Relies on `continued-in`, an undocumented transcript record; if it changes, the hook falls back to today's behaviour. Needs module.distribution (Spec text, scenario and test assert the matcher) and module.concorde (the checkout's .claude/settings.json).
  | (B) Task session follows the main session by id (module.tasks, module.task-session): a resolver follows `continued-in` forward from the task record's `main_session` to the newest id and looks that id up in `claude agents --json` (documented "for scripting", ~0.2 s). `task report` prints the resolved name as `main` when it differs. `task wait --rebound` also returns when the recorded session lives on under another name. Covers moves and in-place renames from the task side; the report itself then alerts the main agent. Does not cover a main agent that started a new session or ended. Same reliance on `continued-in`.
  | (C) Concorde names the main session (module.tasks, module.main-session, module.distribution): a UserPromptSubmit hook in the primary worktree returns `sessionTitle` (e.g. `concorde-main-<4 hex>`) while the session has no name. Verified: ListAgents takes it at once, and it survives the move. Then `--main` never goes stale on a move, using only documented hook output. Trade-offs: replaces the automatic titles the developer reads in `claude agents` for every unnamed session there; a later `/rename` still makes `main` stale; the id still changes. Per-prompt cost ~10-20 ms with a standalone script. Variant C2: no hook; the guidance or `task session` asks the developer to name the main session (`/rename`).
  | (D) UserPromptSubmit check (module.tasks, module.main-session, module.distribution): `task main-hook` also runs at every prompt in the primary worktree and prints only when a task of this session (its id or, with A's resolver, a former id) names a `main` other than its current name from `claude agents --json`. Adds in-place `/rename` and any missed or dropped SessionStart output to A. Cost ~0.25 s per prompt, +0.2 s when the session owns tasks.
  | Guarantees: A gives "told at the next prompt" for moves; strictly covering an in-place `/rename` on the main side needs D. B gives "never waits unnoticed" for moves and renames while the main agent lives; a main agent that is gone needs the bound of escalation rebound_wait_bound.
  Not handled here (decision): The developer decided (2026-10-29) that this task proposes and implements only the option the developer chooses. Option A also reverses the developer's 2026-10-08 decision to leave `fork` out of the matcher. A and B change what module.tasks and module.main-session promise.
  Options: A + B (hook follows the move; task session follows the main session by id); A + B + D (also check at every prompt, for an in-place /rename); A only; B only; C (Concorde names the main session), with A's marking; C2 (ask the developer to name the main session) + B
  Recommendation: A + B. Together they fix the observed failure end to end on both sides: the moved main agent is told at its next prompt, and the task session's report reaches the moved or renamed main agent without waiting for a rebind. Neither costs anything per prompt, and neither renames the developer's sessions. Both fall back to today's behaviour if Claude Code changes `continued-in`. Leave D out for now: an in-place `/rename` loses no report with B, so D only adds latency to every prompt for that rare case. Leave C out: it overrides the developer's session titles.

```json
{
  "level": "task-session",
  "actor": "task session (task main-bg-rename)",
  "code": "fix_direction",
  "detail": "Which fix (or combination) should this task implement for Issue I-b998085e (decision-needed)? Cause established by experiment (decision log, findings 1-14): `/background` forks the main session into a background session with a NEW session id. The new session runs SessionStart with source `fork`, and its output reaches the model at the developer's next prompt. Concorde's matcher `startup|resume|compact` excludes `fork`, which main-rename-hook left out on purpose (\"a fork is a second session that must not take over the tasks\"). The old transcript ends with Claude Code's record {\"type\":\"continued-in\",\"continuedInSessionId\":<new id>}, written before the new SessionStart and only when the parent ends (a copy that keeps its parent gets none), so it tells a move from a copy. An unnamed session's ListAgents name (`<dir>-NN`) becomes the automatic title on the move. A session named with `claude -n`, `/rename` or a UserPromptSubmit hook's `sessionTitle` keeps its name across the move. The ListAgents [ref] changes either way. Stop+attach keeps id and name (source `resume`, already covered).\nOptions:\n(A) Hook follows the move (module.tasks, module.main-session): matcher `startup|resume|compact|fork`. `task main-hook` follows `continued-in` records in the hook input's transcript directory: a task whose recorded `main_session` continues into this session id is marked \"(this session, moved from <id>)\", so the guidance's existing reconcile steps rebind it. A `fork` without such a record marks nothing new. The text carries the session id and time, since Claude Code drops a SessionStart output that repeats word for word. Covers every move at the next prompt. No per-prompt cost. Reverses the developer's 2026-10-08 choice to leave `fork` out. Relies on `continued-in`, an undocumented transcript record; if it changes, the hook falls back to today's behaviour. Needs module.distribution (Spec text, scenario and test assert the matcher) and module.concorde (the checkout's .claude/settings.json).\n(B) Task session follows the main session by id (module.tasks, module.task-session): a resolver follows `continued-in` forward from the task record's `main_session` to the newest id and looks that id up in `claude agents --json` (documented \"for scripting\", ~0.2 s). `task report` prints the resolved name as `main` when it differs. `task wait --rebound` also returns when the recorded session lives on under another name. Covers moves and in-place renames from the task side; the report itself then alerts the main agent. Does not cover a main agent that started a new session or ended. Same reliance on `continued-in`.\n(C) Concorde names the main session (module.tasks, module.main-session, module.distribution): a UserPromptSubmit hook in the primary worktree returns `sessionTitle` (e.g. `concorde-main-<4 hex>`) while the session has no name. Verified: ListAgents takes it at once, and it survives the move. Then `--main` never goes stale on a move, using only documented hook output. Trade-offs: replaces the automatic titles the developer reads in `claude agents` for every unnamed session there; a later `/rename` still makes `main` stale; the id still changes. Per-prompt cost ~10-20 ms with a standalone script. Variant C2: no hook; the guidance or `task session` asks the developer to name the main session (`/rename`).\n(D) UserPromptSubmit check (module.tasks, module.main-session, module.distribution): `task main-hook` also runs at every prompt in the primary worktree and prints only when a task of this session (its id or, with A's resolver, a former id) names a `main` other than its current name from `claude agents --json`. Adds in-place `/rename` and any missed or dropped SessionStart output to A. Cost ~0.25 s per prompt, +0.2 s when the session owns tasks.\nGuarantees: A gives \"told at the next prompt\" for moves; strictly covering an in-place `/rename` on the main side needs D. B gives \"never waits unnoticed\" for moves and renames while the main agent lives; a main agent that is gone needs the bound of escalation rebound_wait_bound.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The developer decided (2026-10-29) that this task proposes and implements only the option the developer chooses. Option A also reverses the developer's 2026-10-08 decision to leave `fork` out of the matcher. A and B change what module.tasks and module.main-session promise."
  },
  "options": [
    "A + B (hook follows the move; task session follows the main session by id)",
    "A + B + D (also check at every prompt, for an in-place /rename)",
    "A only",
    "B only",
    "C (Concorde names the main session), with A's marking",
    "C2 (ask the developer to name the main session) + B"
  ],
  "recommendation": "A + B. Together they fix the observed failure end to end on both sides: the moved main agent is told at its next prompt, and the task session's report reaches the moved or renamed main agent without waiting for a rebind. Neither costs anything per prompt, and neither renames the developer's sessions. Both fall back to today's behaviour if Claude Code changes `continued-in`. Leave D out for now: an in-place `/rename` loses no report with B, so D only adds latency to every prompt for that rare case. Leave C out: it overrides the developer's session titles.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-29T02:19:45Z

- **task-session** task session (task main-bg-rename): `task_side_rebind`
  Only if option B of escalation 1 is chosen: when the resolver proves that the task's recorded main session continues under another live name (`continued-in` chain plus `claude agents --json` by session id), should the task session's command only use that name, or also rebind the task record? (print) `task report` and `task wait --rebound` print the resolved name as `main` (with the recorded one beside it) and append the evidence to the decision log. The task record keeps its `main` until the main agent runs `task rebind`, prompted by A's marking or by the report itself. (rebind) The same commands also rebind the task record to the resolved name and session id, recording `rebound_by: task-session` with the evidence. Then the record is right even if the main agent never rebinds, but the record gains a second writer of `main`.
  Not handled here (decision): Rebinding is the main agent's step in module.main-session's and module.tasks' Specs. Letting a task session's command rebind changes what those Modules promise.
  Options: print: use the resolved name, leave the rebind to the main agent; rebind: the task session's command also rebinds the record, with the evidence
  Recommendation: print. It keeps the rebind the main agent's step, as the Specs say, and it keeps one writer of `main`. Under A, the main agent's hook marks the moved tasks at its next prompt, so the record is put right then anyway.

```json
{
  "level": "task-session",
  "actor": "task session (task main-bg-rename)",
  "code": "task_side_rebind",
  "detail": "Only if option B of escalation 1 is chosen: when the resolver proves that the task's recorded main session continues under another live name (`continued-in` chain plus `claude agents --json` by session id), should the task session's command only use that name, or also rebind the task record? (print) `task report` and `task wait --rebound` print the resolved name as `main` (with the recorded one beside it) and append the evidence to the decision log. The task record keeps its `main` until the main agent runs `task rebind`, prompted by A's marking or by the report itself. (rebind) The same commands also rebind the task record to the resolved name and session id, recording `rebound_by: task-session` with the evidence. Then the record is right even if the main agent never rebinds, but the record gains a second writer of `main`.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Rebinding is the main agent's step in module.main-session's and module.tasks' Specs. Letting a task session's command rebind changes what those Modules promise."
  },
  "options": [
    "print: use the resolved name, leave the rebind to the main agent",
    "rebind: the task session's command also rebinds the record, with the evidence"
  ],
  "recommendation": "print. It keeps the rebind the main agent's step, as the Specs say, and it keeps one writer of `main`. Under A, the main agent's hook marks the moved tasks at its next prompt, so the record is put right then anyway.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-29T02:19:46Z

- **task-session** task session (task main-bg-rename): `rebound_wait_bound`
  How should `task wait --rebound` stop being an unbounded, unnoticed wait when no live session continues the main agent's session (it was ended or replaced by a new session, so neither A nor B helps)? Today the guidance runs `concorde task wait <task> --rebound <name>` with no timeout. checks-bwrap-compat waited 18 h that way. (E1) The guidance gives the wait a bound (`--timeout 1800`). On `wait_timeout` the task session records it in the decision log, sends one PushNotification to the developer (e.g. "Concorde task <task>: report <n> to main agent <name> undelivered; that session is gone"), and waits again with the same bound, notifying at most once per report. PushNotification is a Claude Code tool a background session has: a desktop notification, also pushed to the phone over Remote Control. Not verified: whether a background session's notification reaches the developer. A probe would notify the developer, so I did not run one. The developer can check by asking any background session to call PushNotification once. (E2) A bound and a decision-log entry per timeout, without a notification. The task stays visible only through `concorde task show` and the next main session's start hook, which lists tasks of absent main agents. (E3) No change.
  Not handled here (decision): E1 makes Concorde notify the developer directly, which is outward-facing behaviour of module.task-session and needs a check that only the developer can make, at their own screen or phone.
  Options: E1: bounded wait, then one PushNotification per undelivered report (after the developer confirms that background notifications reach them); E2: bounded wait with a decision-log entry, no notification; E3: no change
  Recommendation: E1, after the developer's one-call check. It is the only option under which a task session whose main agent is gone is still noticed before the developer happens to look. If the check fails, E2.

```json
{
  "level": "task-session",
  "actor": "task session (task main-bg-rename)",
  "code": "rebound_wait_bound",
  "detail": "How should `task wait --rebound` stop being an unbounded, unnoticed wait when no live session continues the main agent's session (it was ended or replaced by a new session, so neither A nor B helps)? Today the guidance runs `concorde task wait <task> --rebound <name>` with no timeout. checks-bwrap-compat waited 18 h that way. (E1) The guidance gives the wait a bound (`--timeout 1800`). On `wait_timeout` the task session records it in the decision log, sends one PushNotification to the developer (e.g. \"Concorde task <task>: report <n> to main agent <name> undelivered; that session is gone\"), and waits again with the same bound, notifying at most once per report. PushNotification is a Claude Code tool a background session has: a desktop notification, also pushed to the phone over Remote Control. Not verified: whether a background session's notification reaches the developer. A probe would notify the developer, so I did not run one. The developer can check by asking any background session to call PushNotification once. (E2) A bound and a decision-log entry per timeout, without a notification. The task stays visible only through `concorde task show` and the next main session's start hook, which lists tasks of absent main agents. (E3) No change.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "E1 makes Concorde notify the developer directly, which is outward-facing behaviour of module.task-session and needs a check that only the developer can make, at their own screen or phone."
  },
  "options": [
    "E1: bounded wait, then one PushNotification per undelivered report (after the developer confirms that background notifications reach them)",
    "E2: bounded wait with a decision-log entry, no notification",
    "E3: no change"
  ],
  "recommendation": "E1, after the developer's one-call check. It is the only option under which a task session whose main agent is gone is still noticed before the developer happens to look. If the check fails, E2.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-29T02:19:46Z

- **task-session** task session (task main-bg-rename): `scope_outside_modules`
  Options A, C and D change the hooks Coordination registers (`src/concorde/coordination/registration.json`, module.tasks). Two things outside this task's Modules state that registration word for word. (1) module.distribution: module.md ("Coordination registers one such hook for SessionStart, with the matcher startup|resume|compact"), scenario.distribution.install-hooks, contracts.md examples, and test_distribution's install-hooks test, which installs the real coordination part and asserts the matcher. A changed matcher fails that test until Distribution changes. (2) module.concorde: this checkout's tracked `.claude/settings.json` (realization.concorde.project-files) carries the matcher too. Options B, and the bound of escalation rebound_wait_bound, need neither Module. (a) Add module.distribution and module.concorde to this task: I update Distribution's Spec text, scenario, examples and test, and the checkout's .claude/settings.json, in the same delivery. (b) Keep this task to its three Modules: the main agent opens a module.distribution task after the merge, and makes `.claude/settings.json` a small change. The primary branch would fail test_distribution between the two merges, and the task's own delivery validation would fail too. So (b) requires delivering without that test passing.
  Not handled here (scope): The task's Modules are module.main-session, module.tasks and module.task-session. Writing module.distribution's and module.concorde's files goes beyond them. Only the main agent can widen a task's Modules.
  Options: (a) add module.distribution and module.concorde to this task; (b) keep three Modules; follow-up Distribution task and a small change for .claude/settings.json
  Recommendation: (a). The Distribution change is a one-word matcher update in text, scenario, examples and one test. Splitting it would leave the primary branch, and this task's own delivery checks, failing in between. main-rename-hook took option (a) for the same reason.

```json
{
  "level": "task-session",
  "actor": "task session (task main-bg-rename)",
  "code": "scope_outside_modules",
  "detail": "Options A, C and D change the hooks Coordination registers (`src/concorde/coordination/registration.json`, module.tasks). Two things outside this task's Modules state that registration word for word. (1) module.distribution: module.md (\"Coordination registers one such hook for SessionStart, with the matcher startup|resume|compact\"), scenario.distribution.install-hooks, contracts.md examples, and test_distribution's install-hooks test, which installs the real coordination part and asserts the matcher. A changed matcher fails that test until Distribution changes. (2) module.concorde: this checkout's tracked `.claude/settings.json` (realization.concorde.project-files) carries the matcher too. Options B, and the bound of escalation rebound_wait_bound, need neither Module. (a) Add module.distribution and module.concorde to this task: I update Distribution's Spec text, scenario, examples and test, and the checkout's .claude/settings.json, in the same delivery. (b) Keep this task to its three Modules: the main agent opens a module.distribution task after the merge, and makes `.claude/settings.json` a small change. The primary branch would fail test_distribution between the two merges, and the task's own delivery validation would fail too. So (b) requires delivering without that test passing.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "The task's Modules are module.main-session, module.tasks and module.task-session. Writing module.distribution's and module.concorde's files goes beyond them. Only the main agent can widen a task's Modules."
  },
  "options": [
    "(a) add module.distribution and module.concorde to this task",
    "(b) keep three Modules; follow-up Distribution task and a small change for .claude/settings.json"
  ],
  "recommendation": "(a). The Distribution change is a one-word matcher update in text, scenario, examples and one test. Splitting it would leave the primary branch, and this task's own delivery checks, failing in between. main-rename-hook took option (a) for the same reason.",
  "causes": []
}
```

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T02:20:10Z

Task main-bg-rename, phase 1 done: cause found and reproduced; four decisions for the developer (escalations 1-4). Nothing implemented; the worktree is unchanged.

FINDINGS (evidence in the decision log, findings 1-14; Claude Code 2.1.312; throwaway haiku sessions in /home/scratch.zbai_gpu/tmp/bgprobe{,2}, a private tmux server, clean environment; no developer session touched)
- The developer's move was the `/background` slash command: daemon.log `bg claimed-spare 5ef40d9f (slash)`, roster dispatch `launch: {mode: resume, fork: true}`. The background session is a `--resume <transcript> --fork-session` copy run by a spare process the daemon pre-started (06:42). Result: a new session id.
- The new session runs SessionStart with source `fork` (input: new session_id and transcript_path; CLAUDE_CODE_SESSION_ID is the new id; no former id or name). The output reaches the model at the developer's next prompt (verified in the transcript and by the model quoting it). Concorde's matcher `startup|resume|compact` excludes `fork`, which main-rename-hook left out on purpose. This is the whole reason no hook output appeared. The 01:48Z instruction re-read was that first prompt after the move, not a new start.
- The old session runs SessionEnd `prompt_input_exit`. Its transcript ends with `{"type":"continued-in","continuedInSessionId":<new id>}`, written before the new SessionStart, and only when the parent ends (a copy that keeps its parent gets none). So a hook can recover the former session id. The former name is not recorded, but the task record already holds it.
- Names: an unnamed session's ListAgents name `<dir>-NN` becomes the automatic title on the move. A session named with `claude -n`, `/rename` or a UserPromptSubmit hook's `hookSpecificOutput.sessionTitle` keeps its name across the move; a SessionStart-set title does not rename the interactive session. The ListAgents [ref] changes on the move either way.
- Stop + `claude attach` keeps the id and name and runs SessionStart `resume` (already covered).
- UserPromptSubmit runs at every prompt, interactive or attached.
- Claude Code drops a SessionStart output identical to an earlier one when resuming.
- Costs: task main-hook 0.23-0.52 s; `claude agents --json` about 0.2 s.

DECISIONS FOR THE DEVELOPER (all four escalated together)

1. `fix_direction`: which fix?
- (A) Hook follows the move.
- (B) Task session follows the main session by id.
- (C) Concorde names the main session.
- (D) UserPromptSubmit check.
- Recommendation: A + B.
Rendered chain:
- **task-session** task session (task main-bg-rename): `fix_direction` — see escalation 1 in the task record for the full chain (options A–D with trade-offs; reverses the 2026-10-08 choice to leave `fork` out).

2. `task_side_rebind` (only with B): should the task session's commands only use the resolved name (print), or also rebind the record? Recommendation: print.
Rendered chain:
- **task-session** task session (task main-bg-rename): `task_side_rebind` — escalation 2.

3. `rebound_wait_bound`: how a wait whose main agent is gone becomes noticed?
- E1: bounded `task wait --rebound` plus one PushNotification per undelivered report.
- E2: bound plus a decision-log entry only.
- E3: no change.
- Recommendation: E1, after the developer checks once that a background session's PushNotification reaches them. I did not probe it, since a probe would notify the developer.
Rendered chain:
- **task-session** task session (task main-bg-rename): `rebound_wait_bound` — escalation 3.

4. `scope_outside_modules`: A, C and D change Coordination's registered hooks, which module.distribution's Spec, scenario, examples and install-hooks test assert word for word, and which module.concorde's tracked .claude/settings.json carries. Recommendation: (a) add module.distribution and module.concorde to this task.
Rendered chain:
- **task-session** task session (task main-bg-rename): `scope_outside_modules` — escalation 4.

DECISIONS I TOOK
- Probed in tmux with a clean environment. The first probe inherited this session's environment; I killed and discarded it.
- Read Claude Code's bundled code only to locate the backgrounding and hook logic. The claims above rest on the probes.
- Did not probe Remote Control, terminal close or PushNotification.
- Removed the five probe background sessions (claude stop/rm). Kept the probe directories and transcripts as evidence (`claude purge <dir>` removes them).

OPEN
- The four answers. After them: Spec first, then code and tests, then task-validation and delivery.
- Until the fix merges: before you start anything that may move this session, name it with `/rename`. A named session keeps its name across `/background`.

It carries escalation(s) 1, 2, 3, 4.

## Answer to report(s) 1 of the task session, 2026-10-29T02:32:23Z

Answers to report 1 (escalations 1-4).

1. fix_direction: decided by the developer: A + B. This reverses the developer's 2026-10-08 choice
to leave `fork` out, and only for a move: a fork without a `continued-in` record from the task's
recorded main session marks nothing. The main agent checked your key evidence. The old transcript
449096d7… ends with {"type":"continued-in","continuedInSessionId":"5ef40d9f-bd72-42ca-b799-583895bb433f"}.
Both A and B must fall back to today's behaviour when the record is missing or its form changes.

2. task_side_rebind: decided by the main agent: print. A rebind stays the main agent's step, as the
Specs say, and `main` keeps one writer.

3. rebound_wait_bound: decided by the developer: E1 if a background session's notification reaches
them, else E2. The check failed. The main agent, itself a background session now, called
PushNotification once. The tool answered "Terminal notification sent. Mobile push not sent (Remote
Control inactive)", and the developer, who uses the Claude Code CLI, did not receive it. So
implement E2: bound `task wait --rebound` (your 1800 s is fine) and record a decision-log entry at
each timeout, then wait again. Send no notification.

4. scope_outside_modules: decided by the main agent: (a). In this task, change module.distribution's
Spec text, scenario, examples and install-hooks test, and the checkout's tracked
`.claude/settings.json` (module.concorde). The task's Modules stay as opened. Name those Modules
with --modules where a run needs them, and list them in your delivery report.

Next: the Spec first, then code and tests. Then run task-validation and delivery from the task
worktree, and report. Escalate anything else together.

## Task session: phase 3 plan after the answers to report 1 (2026-10-29T02:40Z)

Implementing A + B (print) + E2 with scope (a), as answered. Decisions of mine, within the task:

- **Where the following lives.** A new module `src/concorde/coordination/tasks/moves.py` (module.tasks)
  reads Claude Code's records: `continued_in(transcript)` takes the last `continued-in` record of a
  transcript's tail when no `user` or `assistant` record follows it (a session resumed after its
  move continues in itself again, as Claude Code's own `/resume` filter reads it); `chain(id)` follows
  those records from a session id, with a bound of 16 moves and a loop guard; `listed()` reads
  `claude agents --json` (active sessions only, by `sessionId`). Every reader returns nothing on a
  missing file, an unreadable or other-shaped record, a missing `claude` or a failed listing, so A and
  B fall back to today's behaviour, as the answer requires. Transcripts are found with the existing
  `session.find_transcript` (project folder of the primary worktree, else a unique match).
- **A.** The hook marks a task `(this session, moved from <id>)` when its `main_session` continues,
  through `continued-in` records in the hook input's transcript folder, into the starting session.
  The text starts with the UTC time and the session id, so Claude Code never drops it as a repeat.
  Coordination's matcher becomes `startup|resume|compact|fork`.
- **B (print).** `concorde task report` follows the record's `main_session` before it records the
  report. When the session it continues as is listed under a name other than the record's `main`,
  it prints that name as `main`, the record's as `recorded_main`, and the session ids as `followed`,
  and the decision-log heading and body name both. The record's report entry keeps the record's
  `main`, so the record schema does not change. `--rebound` also returns once the record's main
  session continues as a listed session under a name other than the one given. It wakes on writes
  of the record and of the followed sessions' transcripts (two inotify watches awaited together
  through `Changes.wait(0)` and `Changes.descriptor`), never by a timer.
- **E2.** `concorde task wait --rebound` without `--timeout` waits at most 1800 s, so no task
  session waits unbounded even when its command omits it. The task-session guidance tells the
  session, at each `wait_timeout`, to append an entry to the decision log naming the undelivered
  report and the main it waited for, and to start the wait again. The command itself stays
  read-only, since main agents run the same wait.

## Task session: phase 3 implementation decisions (2026-10-29T03:00Z)

Committed as 0ab9ae442 on the task branch. Decisions of mine beyond the plan above:

- **Only the newest session owns a moved task.** For a chain `sess-a → sess-m → sess-n`, the hook
  marks the task for `sess-n` only. A session that itself moved on owns nothing, so a resumed
  middle session never takes the task (scenario.tasks.main-hook-move).
- **The hook's instruction names the new mark.** Its line about a task marked `(this session)` now
  says `(this session, moved from <id>)` counts the same, besides the skill's "When your session
  name changed".
- **Requirements split one obligation each**, as `spec-validation` requires: main-session-followed,
  main-session-unfollowed, main-hook-unique, report-followed, report-followed-shown,
  rebound-wait-follows, rebound-wait-wakes, rebound-wait-bounded (module.tasks) and
  task-session-wait-bounded (module.main-session).
- **`register_wait` of the project MCP server is unchanged.** Its in-server rebound wait still
  waits for the record alone. A task session gets no channel, so `register_wait` hands it the
  `concorde task wait --rebound` command, which follows. A main agent waits for another main
  agent's rebind, where following adds nothing.
- **Tests never ask the developer's `claude`.** The new `tests/concorde/tasks/test_moves.py` runs a
  fake `claude` that prints a list the test writes. `tests/concorde/project_mcp/test_server.py`
  gives its server a fake `claude` that lists no session and an empty `CLAUDE_CONFIG_DIR`, since
  `task_report` now follows the record's session id (that file is module.main-session's).
- **Checked on the real incident (read only).** Following `449096d7-…` (concorde-74) in this
  machine's transcripts gives `["449096d7-…", "5ef40d9f-…"]` and the name `项目中途停止状态检查` from
  `claude agents --json`. So checks-bwrap-compat's report of 2026-10-28 would have reached the moved
  main agent at once. The hook run on the primary worktree with the moved session's input lists
  this task as `(this session)`.
- Out of this task's Modules, as answered with (a): module.distribution (module.md, scenarios.md,
  contracts.md examples, test_distribution's install-hooks test) and module.concorde (the root
  Spec's project-files item and `.claude/settings.json`).

## Report 2 to the main agent (项目中途停止状态检查), 2026-10-29T03:10:31Z

Task main-bg-rename, report 2: delivered. Delivery commit ed8e407500e8bcf00a416e991cac3d2133ed9c9e on concorde/main-bg-rename (run r-20261029T030136-delivery-61c15441). The change commit is 0ab9ae442. task-validation said ready at that head. The task resolves Issue I-b998085e.

WHAT IT DOES (as you answered: A + B print + E2, scope (a))
- A: Coordination's SessionStart matcher is now `startup|resume|compact|fork`, both in the registration and in this checkout's .claude/settings.json. `task main-hook` marks a task `(this session, moved from <id>)` when its recorded `main_session` continues, through Claude Code's `continued-in` records in the hook input's transcript folder, into the starting session as the newest of that chain. A fork without such a record marks nothing new. The text starts with `Concorde (<UTC time>, session <id>)`, so Claude Code never drops it as a repeat. Its instruction counts the new mark as (this session).
- B (print): `task report` (CLI and MCP `task_report`) follows the record's `main_session` through those records and then `claude agents --json`. When the newest session is listed under another name, it prints that name as `main`, with `recorded_main` and `followed` (the session ids) beside it. The decision-log heading and body name both. The record is unchanged, and the rebind stays yours. `task wait --rebound` also returns that followed name. It wakes on writes of the record and of the followed transcripts (inotify, no polling).
- E2: `task wait --rebound` waits at most 1800 s without --timeout. The task-session guidance tells the session to append a decision-log entry at each `wait_timeout` and to wait again. No notification.
- Fallback: without a session id, a transcript, a record of the known form or the list, nothing is followed, and the behaviour is as before.
- Checked read-only on the real incident: following 449096d7… (concorde-74) gives 5ef40d9f… named 项目中途停止状态检查. So checks-bwrap-compat's report would have reached you at once.

MODULES OUTSIDE THE TASK'S THREE (scope (a))
- module.distribution: module.md, scenarios.md (install-hooks), the contracts.md examples, and test_distribution's install-hooks test, all for the matcher.
- module.concorde: the root Spec's project-files item and .claude/settings.json.

VERIFICATION
- The full suite passes: 1640 passed, 6 skipped.
- build --check, spec-validation and registry --check pass. The prompt style check shows no problem.
- New tests are in tests/concorde/tasks/test_moves.py and verify scenario.tasks.main-hook-move, report-follows-move, wait-rebound-follows and the 1800 s bound.

DECISIONS I TOOK (all in the decision log)
- The new module is src/concorde/coordination/tasks/moves.py.
- Only the newest session of a move chain owns the task.
- The requirements are split, one obligation each, as spec-validation requires.
- The project MCP server's in-server `register_wait` rebound wait is unchanged. A task session has no channel, so it gets the `concorde task wait --rebound` command, which follows.
- Tests never call the developer's `claude`. tests/concorde/project_mcp/test_server.py (module.main-session) now gives its server a fake `claude` and an empty CLAUDE_CONFIG_DIR.

FOR THE MERGE AND AFTER
- Merge with `task merge main-bg-rename --check "python3 scripts/concorde.py build" --check "python3 scripts/concorde.py spec-validation"`.
- The checkout's .claude/settings.json takes effect for new main sessions after the merge. Installed projects get the new matcher at their next `concorde update`: the installer removes the old recorded group and adds the new one.
- The probe directories /home/scratch.zbai_gpu/tmp/bgprobe{,2} and their transcripts remain. `claude purge <dir>` removes them when no longer needed.
- Open: an in-place `/rename` of the main session is followed by task sessions (B), but the main agent itself is not told before a report arrives. Option D, a per-prompt check, was left out as you decided.

## Closed: merged, 2026-10-29T03:11:04Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit ed8e407500e8bcf00a416e991cac3d2133ed9c9e into main and closed it as merged. Nobody answers a report after that.
