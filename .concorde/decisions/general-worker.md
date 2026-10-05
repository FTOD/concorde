# Decision log: general-worker

Goal: Add a general Operation to Concorde that runs one isolated worker on a free-form instruction under a chosen task type's grant, with a second independent review worker


## Task brief (main agent, 2026-10-05)

### Why

Six restyle tasks ran pi directly from their task sessions to rewrite Specs, because no Concorde
Operation fits free-form bounded work. The main agent's experiment showed that this direct pi
inherited the developer's whole user configuration. It loaded pi-lens, which applied part of a
multi-edit; pi-mcp-adapter; 21 tools; and the checkout's `CLAUDE.md`, which made pi believe it was
a Concorde main agent and read the skills and the glossary. Concorde's own worker harness already
isolates pi: it uses its own agent dir, no user packages, no context files, and a grant.

### The developer's decision (2026-10-05)

Add a **general worker** to Concorde: an Operation that runs one worker on a free-form instruction
under Concorde's harness, so that ad-hoc AI work gets the same isolation, grant and record as any
Operation. Two points are fixed:

- **Keep a second, independent review.** After the worker, a separate reviewer worker with no
  shared context judges the change against the instruction. For a rewrite this means meaning
  preservation. It lists its findings in the run result. The reviewer only reports and never fixes;
  the caller decides.
- **Use reasoning `medium`.** In `.concorde/workers.json`, give the new Operation's workers the
  project model `gpt-6.1-sol` with reasoning `medium`. The developer chose gpt-6.1-sol for the
  rewriting work and has ample GPT capacity. Commit that config change on this task branch.

### Left for the session to design (record each decision)

- **The Operation's name and its worker ids**, for example `general` with `worker` and `reviewer`.
- **Which part and Module provide it.** The Method part provides the other Operations, so a Method
  child Module may fit. Follow the Specs' rules for a new Module (registry, glossary, part
  registration).
- **How the caller picks the grant.** For example, `--type <task type>` among the Protocol task
  types, for the workspace's bound Modules, or a restricted subset. Writes must stay within the
  grant like every worker. The Operation must be able to run unbound for reading types.
- **The command line and input.** For example, `concorde run general --type specify --instruction
  "<text>"` or `--instruction-file`. Decide whether the instructions are given in the system prompt
  or the brief, and how the reviewer receives the before and after state.
- **The output contract and the evidence.** Follow the existing Operations, the standard worker
  sequence and the run result.
- **Guidance.** Update the main-agent and task-session guidance, so that sessions use this
  Operation instead of calling pi or claude directly for bounded AI work. Add the "isolate, do not
  call pi raw" lesson to the development skill if it fits there.

Escalate together any design choice that changes what an existing Module promises.

### Verification

Specs first, then code and tests, spec-validation, build --check and the full pytest. Then do one
real end-to-end run in the task worktree: a small rewrite of one document with `--type specify`
and its review. Record that run's result and report it. Deliver as usual.

## Task session: design decisions (2026-10-05)

- **Name and worker ids.** The Operation is `general`; its workers are `worker` (does the work) and
  `reviewer` (judges it). Reason: the brief's example; short, and the ids match the existing
  convention (`worker` for the one doing worker, `reviewer` as in `plan_review`).
- **Provider.** A new child Module of Method, `module.general-work` ("General work"), at
  `specs/concorde/method/general-work/`, code in `src/concorde/method/general_work/`, prompts
  `prompts/workers/general.md` and `prompts/workers/general-review.md`. Reason: Method provides
  every Operation through one child Module per responsibility; free-form work fits none of the
  existing children (Understanding reads only, Specification/Implementation have fixed prompts).
  No new glossary term: "general" needs no definition beyond the Module's own Spec (glossary
  admission criterion).
- **Grant choice.** `--type <task type>` (required, one of the eight Protocol task types) for the
  run's Modules (`--modules`, else the binding's), computed through the standard worker sequence.
  `--read-only` withholds every writable level (as `survey` does), which lets any type run unbound.
  Writing types without `--read-only` need a bound workspace (the existing `unbound_write`
  refusal). The definition is `binding: optional`.
- **Catalog task type.** `general`'s definition declares no fixed task type: each run names it.
  Operations' Spec gets one clause ("or, for an Operation whose runs each name it, none");
  `declared_workers` selects Operations by kind instead of by a non-null task type. This is a
  widening of Operations' definition that no existing Operation is affected by; module.operations
  is one of this task's Modules. Flagged in the report.
- **Input.** `--instruction "<text>"` or `--instruction-file <path>`, exactly one. The instruction
  goes in the brief (task instructions after Concorde's general worker prompt), never the system
  prompt; an exact copy is kept as `instruction.md` in the run's trace node with its digest.
- **Reviewer.** Launched only when the worker ended `ok` and its audit was clean. It runs under the
  same task type's grant with every writable level withheld, so it reads what the worker could read
  and changes nothing. It shares no session with the worker. The host gives it the instruction,
  the change as the host observed it (a unified diff between two Git trees of the worktree, taken
  before and after the worker with a temporary index and `git write-tree`), a copy of every
  changed file's earlier content under `before/` in the run's trace node (readable), and the
  worker's answer marked as a claim to check. Findings: id, severity (blocking/advisory), kind
  (instruction, meaning, scope, error, claim), locations, description, suggestion. The Operation
  derives the verdict (`changes_required` exactly when a finding is blocking). It never fixes.
- **Output.** `contract.general-work.result`: type, read_only, instruction (file, copy, digest),
  the worker's answer, the observed change (files with added/modified/deleted, diff path, before
  directory), and the review (summary, findings, verdict). The run is `ok` with any verdict; a
  reviewer that ends blocked/failed ends the run so, with the change named in host evidence.
- **No checks, no resume rounds.** The worker gets no configured checks and no structural
  validation; validating the result is the caller's (`spec-validation`, `task-validation`), and
  the reviewer is the second reading. Reason: keep the Operation general and minimal.
- **Guidance outside the task's Modules**, done because the brief asks for it: the development
  skill's lesson (module.concorde), the worker-id list in the worker-harness guidance
  (module.worker-harness) and the Operation tables in `docs/` (module.concorde). Each is a
  one-line or one-row addition.

## Task session: verification and end-to-end run (2026-10-05)

- Specs first (new Module `module.general-work`, Method table and child, Operations' definition
  clause), then code, tests (13 new, `tests/concorde/general_work/`), guidance and docs.
  `spec-validation` success, `build --check` no differences, full pytest: 1267 passed, 5 skipped.
  Committed as 62ab8f12.
- A worker's `output` must satisfy its schema even when it ends `blocked`; the general worker
  prompt therefore asks it to still fill `answer`. (Found by the blocked-worker test.)
- **Live run** `r-20261005T044022-general-dce11173` in this worktree:
  `run general --modules module.operations --type specify --instruction-file <restyle the opening
  paragraph of specs/concorde/execution/operations/requirements.md, keep the meaning>`.
  Status `ok`. Worker: pi, gpt-6.1-sol as local-openai/gpt-6.1-sol, reasoning medium, tools
  read/grep/find/ls/edit/write/concorde_result only (no user packages), 38 s, audit 1 changed, no
  violation. Observed change: that one file, modified. Reviewer: same model, tools
  read/grep/find/ls/concorde_result, 16 s, audit clean, 0 findings, verdict `accepted` ("every
  original statement, condition, link label, link target and requirement-list item is
  preserved"). Checked by hand: the meaning is kept.
- Decision: the live run's change was reverted, not kept. It was a demonstration; it put each
  sentence on its own line, two lines over 100 columns, against the file's wrapping, which the
  instruction did not mention. Nothing in the task needed that paragraph changed.

## Report 1 to the main agent (concorde-f8), 2026-10-05T04:56:55Z

general-worker delivered: delivery commit 151aa5bd on concorde/general-worker (work commit 62ab8f12). task-validation ready; spec-validation success; build --check clean; full pytest 1267 passed, 5 skipped.

What it adds: `concorde run general --type <task type> (--instruction "<text>" | --instruction-file <file>) [--read-only] [--modules …]`. New Method child Module `module.general-work` (specs/concorde/method/general-work/, src/concorde/method/general_work/, prompts/workers/general.md + general-review.md, tests/concorde/general_work/). Steps: keep the instruction (copy + digest in the trace node) → record the worktree as a Git tree (temporary index + write-tree; HEAD/index untouched) → worker under the --type grant (writes withheld with --read-only) → record the tree again, keep change.diff and before/ copies → reviewer, a separate read-only worker under the same type, given the instruction, the diff, the earlier files and the worker's answer as a claim → verdict derived (changes_required iff a blocking finding; kinds instruction/meaning/scope/error/claim). The reviewer only reports. Output contract: contract.general-work.result. Unbound runs: allowed for reading types or with --read-only; a writing type unbound fails `unbound_write` before any worker. No checks/resume rounds; validation stays the caller's. Findings stay in the run result, never Issues.

workers.json: operations.general.default = gpt-6.1-sol, reasoning medium (on the task branch).

Live end-to-end run r-20261005T044022-general-dce11173 (--type specify, module.operations, restyle the opening paragraph of operations/requirements.md keeping its meaning): ok. Both workers on pi local-openai/gpt-6.1-sol, reasoning medium. Worker tools read/grep/find/ls/edit/write/concorde_result only (none of the user's packages), 38 s, audit 1 changed, no violation. Reviewer tools read-only, 16 s, 0 findings, verdict accepted. I checked by hand: the meaning is kept. I reverted that demo change: it put each sentence on its own line (two lines >100 columns), and the task did not need it.

Decisions I made (all in the decision log):
1. Names: Operation `general`, worker ids `worker` and `reviewer`, Module `module.general-work` ("General work"). No new glossary term.
2. Operations' promise widened by one clause: a definition's task type may be "none when each run names it" (the catalog lists that). `declared_workers` now selects Operations by kind. No existing Operation is affected. module.operations is a task Module. Veto it if you want this escalated instead.
3. The instruction goes in the brief after Concorde's general prompt, never in the system prompt.
4. The reviewer uses the same type's grant, read-only, plus the kept diff and before/ files as readable host material.
5. Guidance edits outside the task's Modules, made because the brief asked for them: the development skill's "never run pi/claude yourself, use run general" lesson (module.concorde); `general` in the worker-id list of the worker-harness guidance (module.worker-harness); a row in the Operation tables of docs/README.md and docs/using-concorde.md (module.concorde; prettier re-padded the using-concorde table). Method's own guidance (skill "Free-form work" + command line, task-session bullet) is within module.method.
6. A worker's output must satisfy its schema even when it is blocked, so the general prompt asks it to still fill `answer`.

Open: nothing blocks the merge. Possible follow-ups: an opt-in `--checks` (configured checks with resume rounds) for implement-type general runs, and Coordination's main-session Specs do not yet state a requirement for the new guidance bullet (module.main-session was outside this task). No Issues resolved by this task.

## Main agent (2026-10-05): decisions on the delivery report

- Decision 2 is accepted without escalation. It widens Operations' promise so that a definition's
  task type may be "none when each run names it". The clause is additive, no existing Operation is
  affected, and the developer asked for a general worker whose task type is chosen per run, which
  needs this clause.
- The follow-ups are noted for later and not opened now: an opt-in `--checks` for implement-type
  general runs, and a main-session Spec requirement for the new guidance bullet.

## Closed: merged, 2026-10-05T04:57:16Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 151aa5bde1323daf7c280421d071394526f320fa into main and closed it as merged. Nobody answers a report after that.
