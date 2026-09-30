# Decision log: project-issues

Goal: Make Issues project-level records kept by the primary worktree and managed through the project MCP server, give every Issue report one of four tiers (suggestion; obvious fix; preferred fix, reported; decision needed), and keep defects of the Issue system itself out of the Issue system

## Brief (main agent, 2026-10-01)

This task is one of four that rebuild Concorde's reviews: the later tasks `panel-architects` and
`module-code-review` make the review Operations report every problem they find as an Issue through
what this task builds. Keep to the Modules bound here (issues, main-session, tasks).

### The developer's decisions this task carries out

1. **Issues become project-level records.** Today each Issue is a branch-local file
   `.concorde/issues/I-<hex>.md`, written only in a task worktree and reaching the primary branch
   when the task merges. The developer weighed keeping them branch-local (with an Operation that
   reconciles duplicates and identities at merge time) and chose project-level records instead,
   "to keep it simple": Issues are kept by the primary worktree, like tasks, so every session and
   every run sees the same Issues at once and every Issue has one project-wide identity from the
   moment it is reported. Consequences to specify:
   - where and how the records are kept durably (the recommended shape: in the primary worktree,
     each write committed on the primary branch under the merge lock, as a task close commits its
     decision log; settle it and say why);
   - writes may come from any worktree, including bound runs in task worktrees and runs whose
     Operation hosts write through the Issues library (never workers);
   - how a task that fixes an Issue closes it now that the closure no longer travels on the task
     branch (for example the task names the Issues it resolves and `task merge` closes them with
     the merge as evidence after its checks pass; settle it);
   - duplicate reports of one problem: a reporter reads the open Issues first and appends a report
     to the matching Issue instead of creating another; identities stay unique by construction;
   - remove what only served branch-local records (conflict resolution guidance in Issues and in
     the main-session guidance). This is a rapid-iteration phase: no migration of old behaviour is
     needed, but the existing records in `.concorde/issues/` must survive.
2. **Issues are managed through the project MCP server.** Add Issue tools to the project MCP server
   (`src/concorde/project_mcp/`): at least list, show, report, close, reopen and check, each the
   `concorde issues` command's own answer and refusal as the other tools are. The command stays.
   Update the main-session guidance (`prompts/main-session/`) accordingly.
3. **Every Issue report carries a tier**, which decides whether AI may handle it without the level
   above. Four tiers, weakest first:
   1. `suggestion` - no problem today, only a suggestion; this is what `advisory` means;
   2. an obvious problem whose fix is obvious: AI fixes it, nobody above is involved;
   3. a simple problem with several possible fixes, one clearly better: AI fixes it, and reports
      it to the level above;
   4. the problem is unclear, or it is clear but its fix is uncertain: the level above (main agent,
      then the developer) decides.
   Tiers 2 to 4 are `blocking`. Choose short stable names for tiers 2-4. A review Operation only
   reports; fixing is later work of a task session, which may fix tiers 2 and 3 itself and must
   escalate tier 4. Say so in the main-session guidance (main agent and task session). An Issue
   escalated upward is named by its unique identity, and every report carries a complete
   description and evidence (the schema already requires description, impact, basis, evidence;
   check that it stays so and that the tier is required).
4. **Defects of the Issue system itself never go through the Issue system**, or a broken Issue
   system could not report itself (a deadlock). A failure of the Issue store, its commands or its
   MCP tools is reported as an error chain: in a task's decision log and escalation, or in the
   run's result. Specify this and make the Issues code and guidance follow it.

### Not in this task

Do not add a glossary entry for the tier yet: `spec-quality-protocol` runs in parallel and also
edits `specs/concorde/glossary.json`; `panel-architects` adds the entry once review Modules use the
term. Explain the tier in the Issues Spec itself. Do not change review Operations
(`src/concorde/spec_review/`, `src/concorde/code_review/`): later tasks do.

### Left to the task session

Naming, file layout, the exact record schema and how the commit on the primary branch is taken,
within the decisions above. Escalate to the main agent, together, any choice that would change
another Module's promises beyond Issues, tasks and the main session.

### Verification and delivery

Run `build`, `spec-validation` and the relevant tests, then `task-validation` and `delivery`, and
report to the main agent.

## Task session decisions (2026-10-01)

1. **Where Issues are kept.** In the primary worktree's `.concorde/issues/`, each accepted write
   committed on the primary branch as a commit of that record alone (`git commit --only`), under
   the merge lock, and refused with `merge_incomplete` while a task merge is unfinished. Why: the
   existing records and any record a still-open old-code task branch writes merge in unchanged
   (no migration), records stay plain files versioned with the project like decision logs, and the
   merge lock is what keeps an Issue commit from landing between a merge commit and its checks. I
   weighed a dedicated Git ref (`refs/concorde/issues`, written with plumbing): it decouples Issues
   from merges and needs no sandbox change, but it moves the records off the primary branch against
   the brief's recommended shape and needs a migration; not chosen.
   - Every action (list, show, report, close, reopen) works on the primary worktree of the
     repository `--root` belongs to; `check` keeps checking the record files of `--root` itself, so
     a task worktree's configured check still proves the branch's code reads the committed records.
   - Library callers wait for the merge lock up to the Tasks default (300 s); the project MCP
     server's Issue tools never wait (refused `merge_busy` naming the holder, as `task_open`).
   - Consequence: a task session's Bash sandbox cannot write the primary worktree's
     `.concorde/issues/`, so task sessions write Issues through the project MCP server (outside the
     sandbox). Runs started from a task session's background Bash whose Operation hosts write Issues
     (the later review tasks) need the session boundary to make that directory writable, which is
     module.task-session's and module.harness's: reported as open, not changed here.
2. **Tiers.** Field `tier` on every report, required: `suggestion` (tier 1, advisory),
   `obvious-fix` (2), `preferred-fix` (3), `decision-needed` (4); 2-4 are blocking. The report
   contract goes to version 2. Records get `schema_version: 3`, in which every report has a tier;
   records of version 2, written before tiers, stay valid unchanged (their reports have no tier and
   the store never rewrites a report) and may receive tiered reports; an Issue's tier is its latest
   report's, `null` for an untiered one. The list row carries `tier`.
3. **Closing with a fix.** The task record gains `resolves`, the Issues the task fixes: set by
   `task open --resolves` and extended by `task resolve <task> <issue>...` (and the MCP tool
   `task_resolve`). `task merge`, after its checks passed and while it still holds the merge lock,
   closes each still-open one as `resolved` with the merge commit as evidence; a closure that fails
   is a warning of the merge carrying the Issues error link, never a failed merge.
4. **Provenance through the MCP server.** The server's Issue tools record the session as
   `main-agent` in the primary worktree and `task-session` in a task worktree, with that worktree's
   bound task as `change_id`; the CLI keeps `main-agent` and `--task`.
5. **Issue-system defects.** Every refusal of the Issues command/tools that is an environment
   failure says in its option to carry the error chain in the decision log/escalation or run
   result and never to report it as an Issue; the Spec and guidance state the rule.
6. **Dogfooding's defect report example.** The required tier made the example report of
   `prompts/dogfooding/skill.md` (module.dogfooding, not bound here) invalid, failing
   `test_the_guidance_says_how_to_watch_classify_and_report`. I added only the `tier` field and its
   one-line explanation there, a direct consequence of the developer's decision that changes no
   promise of Dogfooding. Left open for Dogfooding: a defect of Concorde's Issue system seen in a
   develop install is itself a defect report, i.e. an Issue report, which the "never through
   Issues" rule would route as an error chain instead.
7. **Mechanical updates outside the bound Modules.** Text that described Issues as written on the
   task branch and closed there would now tell sessions to do what the sandbox refuses, so I
   updated only its description of the Issues mechanism, changing no promise of its Module:
   `prompts/development/skill.md` and `specs/concorde/dogfooding/module.md` (defect flow: record the
   Issue in the primary worktree, name it with `--resolves`, the merge closes it) and
   `docs/using-concorde.md` (tiers, project-level records, `--resolves`). Listed for the main agent.
8. Slip, undone at once: a bare `git stash` I ran while comparing lint output stashed the worktree's changes; I applied that entry back by its SHA and dropped it, so nothing was lost (diff re-checked: 37 files).
9. **The Issue lock is gone.** Issue writes now take the merge lock, so `.concorde/locks/issues.lock`
   is no longer taken. I removed its row from Tracing's lock tables
   (`specs/concorde/tracing/contracts.md`, `module.md`), added Issue writes to the merge lock's row,
   dropped the dead `"issues"` entry of `LOCK_KINDS` in `src/concorde/tracing/layout.py`, and
   replaced "branch-local" in the root Module's summary of Issues (`specs/concorde/module.md`):
   module.tracing and module.concorde are not bound here; listed for the main agent.
   The test `tests/concorde/dogfooding/test_dogfooding.py` checked the old command line of the development skill; I updated its expected fragment.

## Report 1 to the main agent (spec-review quality criteria), 2026-09-30T20:04:53Z

project-issues delivered at bc00502085d938cdaf36311116085b8001f3f2f0 (work commit bdeaf30f). build --check, spec-validation (0 findings), the full suite (851 passed, 4 skipped), task-validation (ready) and delivery all ok.

What it does:
- Issues are project-level: kept in the primary worktree's .concorde/issues/; every write takes the merge lock, is refused (merge_incomplete) while a merge is unfinished, and commits its record alone on the primary branch (git commit --only, trailer Concorde-Issue). Every action but `check` works on the primary's records from any worktree; `check` still checks the worktree's own copy. The existing 8 records stay valid unchanged.
- Tiers: every report requires `tier` = suggestion | obvious-fix | preferred-fix | decision-needed (2-4 blocking), explained in the Issues Spec (#tiers), no glossary entry. Report contract v2; new records are schema_version 3; v2 records (pre-tier) stay valid and may take tiered reports. list rows carry `tier`.
- Closing with the fix: task record gains `resolves` (schema 5): `task open --resolves`, `concorde task resolve <task> <issue>...` / MCP `task_resolve`. `task merge`, after its checks, still under the merge lock, closes each still-open one as resolved with the merge commit as evidence (`resolved` in its answer); a closure that fails is a warning carrying the Issues error chain, never a failed merge.
- Project MCP server: issue_list, issue_show, issue_check, issue_report (report object or file; check), issue_close, issue_reopen, task_resolve; answers/refusals are the command's own (logic moved to src/concorde/issues/command.py, scripts/issues.py is a thin CLI). Writes never wait for the merge lock (merge_busy at once). Provenance: task-session + its task in a bound task worktree, main-agent otherwise.
- Issue-system failures (merge_busy, merge_incomplete, commit_failed, io_error, not_a_repository) are environment refusals whose options say to carry the error chain in the decision log/escalation/run result, never as an Issue; stated in the Issues Spec, main-session and task-session guidance.
- Removed the branch-local and merge-conflict guidance (Issues Spec, main-session Spec/guidance) and the per-worktree issues.lock.

Decisions I took (details in the decision log, entries 1-9):
1. Storage as the brief recommended (primary branch commits under the merge lock); I weighed a dedicated Git ref refs/concorde/issues and did not choose it (moves records off main, needs migration).
2. Tier names above; record schema v3 with v2 kept valid rather than rewriting reports.
3. Merge-time closure via task `resolves`.
4. Mechanical edits outside the bound Modules, changing no promise, because the old text would now direct sessions into sandbox refusals or failed tests: prompts/dogfooding/skill.md (tier in the defect-report example), prompts/development/skill.md and specs/concorde/dogfooding/module.md (defect flow: record in primary, --resolves, merge closes), docs/using-concorde.md, specs/concorde/module.md ("branch-local" wording), Tracing's lock tables and the dead "issues" entry of LOCK_KINDS in src/concorde/tracing/layout.py, and one expected fragment in tests/concorde/dogfooding/test_dogfooding.py. Glossary: only the definitions of concept.issue ("project-wide ... kept by the primary worktree ... each with its tier") and concept.merge-lock (adds "or writes an Issue") changed; no new entry.
5. A slip, undone at once: a bare `git stash` while comparing lint output; applied back by SHA and dropped, nothing lost.

Open, for you / later tasks (not blocking this merge):
- A task session's Bash sandbox cannot write the primary worktree's .concorde/issues/, so task sessions write Issues only through the MCP tools (the guidance says so). Runs a task session starts in background Bash whose Operation hosts write Issues (panel-architects, module-code-review) will need the session boundary to make that directory writable: that is module.task-session (src/concorde/tasks/session.py `writable`) and module.harness's session-boundary text, not bound here. Runs started through workflow_step run outside the sandbox and are unaffected.
- Dogfooding: a defect of Concorde's Issue system seen in a develop install is itself a defect report (an Issue report); the "never through Issues" rule would route it as an error chain instead. Dogfooding's Spec does not say so yet.
- The understanding contracts' illustrative example still says "branch-local Issue records" (module.understanding, an example only).
- Merging: this task changes the task record schema and the merge flow; `task merge` of this task itself runs the old primary code, so the merge-time closure applies from the next merge on.

## Closed: merged, 2026-09-30T20:05:24Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit bc00502085d938cdaf36311116085b8001f3f2f0 into main and closed it as merged. Nobody answers a report after that.
