# Decision log: audit-kernel

Goal: Audit the restyled requirements against Protocol 16.4's requirement rules with the general worker, and fix every drift from their original meaning: Kernel, Tracing, Distribution, Issues and Workflows


## Task brief (main agent, 2026-10-05)

### Background

Six restyle tasks rewrote every Spec with raw `pi -p` on 2026-10-04. Their base commit was
d4423f70; read `.concorde/decisions/restyle-*.md`. An experiment then showed that some of their
rewrites drift in ways the reviews of that time accepted as compliant. The cause was the Sentence
style rules of that time, applied to requirements. Protocol 16.4 (task `style-requirements`) now
fixes this. `protocol/style.md` has the rules "Requirements" and "The links between facts", and
`protocol/evaluation.md` names five drifts:

1. one obligation split into a list of separate rules;
2. a condition, exception or failure clause moved out of the SHALL statement;
3. a condition moved away from what it limits, for example a fronted "Only after X, …";
4. a changed or added subject, an actor the original did not name;
5. a dropped link word (since, because, so that, only, each, every, never, at most, unless and
   the like).

A drift that changes what a requirement requires, or who bears it, is blocking.

### The developer's decision (2026-10-05)

Audit the already-rewritten requirements against the new rules, then fix what the audit finds.

### Scope

Every requirement in the `requirements.md` files of your Modules, listed below. Leave scenarios
and contracts out, unless a requirement fix forces a matching wording change there.

### How

1. **Use the new general worker for the audit.** Run `concorde run general --type review-spec
   --read-only --modules <module> --instruction-file <file>` from your task worktree, one run per
   Module's requirements.md. This one Operation runs the worker and the independent reviewer on
   gpt-6.1-sol at reasoning medium, isolated by the harness.
   - Only one run per workspace at a time, so the runs are sequential within your task.
   - The instruction file must give the five drift patterns, the 16.4 rules, and the ORIGINAL
     text of that requirements.md at d4423f70 (`git show d4423f70:<path>`). The worker cannot
     read Git history.
   - Ask for one finding per requirement id, giving the pattern, the original wording, the current
     wording, and whether it is blocking.
   - Keep the instruction file outside tracked paths, or delete it before you commit.
2. **The baseline is the original meaning at d4423f70**, apart from changes made on purpose
   since then. Check `git log d4423f70.. -- <file>`. For example, `fix-status-locks` changed
   `req.tasks.derived-state`, and `general-worker` changed the Operations Spec. Those are not
   drift.
3. **Check every finding yourself before you act on it.** Worker and reviewer output are claims.
   Also scan for what the audit may miss: statements followed by rule lists, "Only after"
   openings, and requirements whose SHALL count changed.
4. **Fix each confirmed drift**, either by hand or with `concorde run general --type specify
   --instruction-file <file>`, which has its own reviewer. Each fix restores the original meaning
   in a form that follows 16.4. One SHALL sentence may now be long, so prefer restoring the
   original obligation in one statement over a split.
5. **Watch every run closely**, including its result, its host evidence and the trace. This is
   the general worker's first real use. If the general Operation itself misbehaves:
   - Record it as an Issue on `module.general-work`.
   - Tell the main agent in your report.
   - Fix it only if your task owns that Module, which only `audit-method` does.

### Verification and report

Run spec-validation (0 errors), build --check and the tests that assert requirement text, then
the full pytest once. Commit verified steps, then run `task-validation` and `delivery`. Use at most
2 pi gateway lanes in total; the general runs already go one at a time.

In your report, give:

- the requirements audited;
- the findings by pattern, split into confirmed and rejected, with the reason for each rejection;
- the fixes made;
- the requirements you found the audit missed;
- how the general worker behaved (duration, verdicts and any problem).

Record every decision you take without the developer, and every non-`ok` result, in this log.

### Your Modules

module.kernel,module.tracing,module.distribution,module.issues,module.workflows

## Task session (2026-10-05)

- Decision: `git log d4423f70.. -- <file>` shows only the restyle commit for each of the five
  requirements.md files (680ab945 Kernel/Tracing, 01a7094e Distribution, 5f7eadf0 Issues,
  b987f038 Workflows), so the baseline for every requirement is its d4423f70 text.
- Decision: the five audit instruction files live in the session's job tmp directory, outside the
  worktree. Each gives the five drift patterns, the 16.4 sections "The links between facts", "The
  actor and the active voice", "Requirements" and "Lists for three or more", the evaluation drift
  list, and the d4423f70 text, and asks for one entry per requirement id.
- Decision (classification rule): a list below a statement is a drift (pattern 1) when its items
  are actions or rules of their own (imperatives such as "Move…", "Keep…", or two cases each with
  its own action). A list of objects, values, conditions or details of the one obligation is the
  16.4 form and is not a drift. Only confirmed drifts are fixed, so the task does not restyle again.

### General audit runs (review-spec, --read-only, gpt-6.1-sol medium, worker + reviewer)

| Module | run | duration | verdict | reviewer findings |
| --- | --- | --- | --- | --- |
| kernel | r-20261005T055408-general-3fed4561 | 3m12s | accepted | 0 |
| tracing | r-20261005T055729-general-a5b9e93f | 5m16s | changes_required | 4 (3 blocking: false positives on reader-read-only and holder-named, reported-usage repair form; 1 advisory on written-at-start) |
| distribution | r-20261005T060245-general-4fd43938 | 10m16s | changes_required | 1 blocking: worker missed the actor change in installer-keeps-installation-bound |
| issues | r-20261005T061301-general-2fa16069 | 6m45s | accepted | 0 |
| workflows | r-20261005T061946-general-a98e7a66 | 7m30s | accepted | 0 |

Every run was `ok`, with one round per worker, a write audit with 0 changes and no violations, and
the grant lowered to read. `changes_required` is the reviewer's verdict on the worker's audit
answer. It is not a run failure, and I settled each reviewer finding below. The only stderr is pi's
benign "No project session found … creating a new session" warning. The general Operation showed
no misbehaviour, so the task records no Issue on module.general-work.

### Decisions on the findings (task session, 2026-10-05)

- Rule adopted: 16.4 lets a list stand below a requirement statement only for three or more
  conditions. A statement followed by a one-item or two-item list is therefore pattern 2 (its
  conditions or details left the sentence), and the fix restores the d4423f70 statement.
  Statements whose list items are full rules ("It uses…", "Move…", "Only when…, it uses…") are
  pattern 1. A list of three or more conditions, objects or values below one statement is the 16.4
  form and is not a drift.
- Rejected worker findings, which are lists of the objects of one obligation and not separate rules
  (I agree with the Tracing reviewer here): tracing.reader-read-only, tracing.roots-registered,
  tracing.holder-named (each condition sits next to its own object),
  distribution.build-check-read-only, workflows.step-lock and workflows.no-task.
- The reviewer's F4 on the tracing.reported-usage repair is rejected. The original sentence has two
  values and a "never" limit, not three conditions, and a requirement statement has no length
  bound. The original statement is restored verbatim.
- Accepted reviewer finding: distribution.installer-keeps-installation-bound is pattern 2 plus 4,
  and blocking. "It thereby binds" makes the installer the binder, while the binding is Spec core's.
  The original "so that every file … is bound" is restored.
- Found by me and missed by the audit: workflows.steps-are-runs and
  workflows.no-operation-knowledge are pattern 3. A limit of one part ("in the workspace the step
  runs in", "under the step output convention") was fronted before the subject. The audit also
  missed a lost blank line before the heading after workflows.no-ask-continues, and the fronted
  "Only when" inside a list item of tracing.created-or-found.
- tracing.history-unchanged: the original joined the retention limit to the SHALL statement with a
  semicolon. Since prose may hold no semicolon, the fix joins it with "except that retention only
  removes …", which keeps the limit inside the statement and keeps "only".
- kernel.busy-lock-named: the statement is restored in its original passive form, with no actor.
  The exception paragraph is restored to its original passive sentence, and its "so that" is carried
  into a second sentence ("It is refused so that …"), because the sentence would be 45 words.
- Descriptive pattern 4 fixed: distribution.installer-mcp-kept ("is not written") and
  distribution.failed-write-reported ("The installed files are bound").
- Scenarios and contracts are unchanged. Every fix restores the original wording, so none of them
  needed a matching change.

## Main agent note (2026-10-05): requirements outside requirements.md

audit-execution found that several Modules keep requirements in other documents, which the restyle
also rewrote. In its Modules these were `checks/{boundary,service,timing}.md`,
`workers/{launch,pi}.md` and `spec/errors.md`. Your scope is every requirement of your Modules,
wherever it is defined. Find them with a search for `### req.`.

Two drifts slipped past the general audit there. Both were found by the session's own pass:

- "while the process runs" had become "during execution";
- a limit had been moved away from the route it limited.

Its lessons:

- Restore the original subject, even a passive one. Choosing an actor is a Spec change.
- A list of the objects or properties of ONE obligation is fine. Only a list of separate rules is
  a split.

### Task session on the main agent's note (2026-10-05)

- Searched for `#… req.` in every document. The `owns` of module.kernel, module.tracing,
  module.distribution, module.issues and module.workflows hold only their four documents each, and
  none of them except requirements.md defines a requirement. The `req.concorde.*` entries in
  specs/concorde/development.md belong to module.concorde. My scope therefore holds no requirement
  outside requirements.md.
- Original passive subjects are restored (kernel.registration-stable, kernel.busy-lock-named). I
  rechecked all 72 statements that still differ from d4423f70, and none of them changes or adds an
  actor or drops a limiting word.
- About the note's object-list lesson: some of my fixes restored two-item lists of objects
  (for example issues.archive-reported, workflows.report-from-records and
  distribution.installer-own-permissions). Each of them returns the exact d4423f70 statement, so no
  meaning changes. I keep them and report them as form restorations, not as drifts.

## Report 1 to the main agent (concorde-f8), 2026-10-05T06:46:26Z

audit-kernel delivered: ffe43fdd ("concorde: deliver audit-kernel") on concorde/audit-kernel, fix commit d4efa3ef. Checks: spec-validation 0 errors (12 warnings, none in these Modules), build --check clean, full pytest 1270 passed / 5 skipped, task-validation ready (r-20261005T063049-task_validation-79a6c12f), delivery r-20261005T063830-delivery-7540b6f8.

AUDITED: every requirement of the five Modules: kernel 14, tracing 21, distribution 57, issues 36, workflows 44 (172). Per your note, no `### req.` of these Modules lies outside requirements.md: their `owns` hold four documents each, and development.md's req.concorde.* belong to module.concorde. Baseline: d4423f70. Only the restyle commit touched these files since then.

GENERAL WORKER (review-spec --read-only, one run per Module, sequential, gpt-6.1-sol medium):
kernel 3m12s accepted; tracing 5m16s changes_required (4 reviewer findings); distribution 10m16s changes_required (1); issues 6m45s accepted; workflows 7m30s accepted. Every run ok, one round per worker, write audit 0 changes and no violations, grant lowered to read. The only stderr is pi's benign "No project session found … creating a new session". The reviewer added real value: it caught a missed actor change (distribution.installer-keeps-installation-bound) and three false positives in the Tracing answer. No misbehaviour of the general Operation, so no Issue on module.general-work.

FINDINGS CONFIRMED AND FIXED (62 requirements, all restored to the d4423f70 statement in 16.4 form, plus one lost blank line):
- Pattern 4, actor added or subject changed: kernel.registration-stable and kernel.busy-lock-named (blocking: passive original, "the Kernel" added); distribution.installer-keeps-installation-bound (blocking, also pattern 2: "It thereby binds" made the installer the binder); tracing.own-usage, reported-usage, observed-metadata (field to node) and locks-apart (non-blocking); descriptive text of distribution.installer-mcp-kept and failed-write-reported.
- Pattern 1, rules split into lists or a second SHALL: kernel.binding-whole (second SHALL), kernel.transaction-restored; tracing.relative-paths, created-or-found (also 3: "Only when…" inside an item), conversations-shorter; distribution.prompt-includes, composed-from-registrations, glossary-import, receipt-complete, installer-d2-first, mcp-channel-override, own-python; issues.caller-provenance, status-folder, archive, uncommitted-recovered, commit-alone; workflows.answers-input, lost-first, script-repeats.
- Pattern 2, condition, exception or detail moved out of the statement: kernel.refusals-coded; tracing.history-unchanged (now joined with "except that retention only removes…", since prose holds no semicolon); distribution.skills-rendered, include-once, mcp-current-code, mcp-tools-changed; issues.own-check, main-agent-actor.
- Pattern 3, fronted limit: distribution.registration-only ("Only through…"); workflows.steps-are-runs and no-operation-knowledge.
- Pattern 5: kernel.busy-lock-named "so that" weakened to "The reason is that"; restored.
- Form restorations: a one-item or two-item list below a statement became the original single sentence again. No meaning changed. They are tracing.written-at-start, retention-explicit; distribution.absent-part-named, composed-guidance, guidance-absent-parts, installer-own-permissions, installer-project-mcp, installer-fresh-guidance, installer-programs-first, installer-docsite-template-first, mcp-call-failed; issues.report-evidence-present, own-failures, archive-reported, no-write-during-merge; workflows.restart-generation, workspace-retired, bounded-wait, interactive-stops, report-from-records, lost-step, relay-asked-again. Your note treats object lists as no split, and some of these are object lists. Each returns the exact original statement, so I kept them.

REJECTED: object lists of one obligation, not separate rules: tracing.reader-read-only, roots-registered, holder-named; distribution.build-check-read-only; workflows.step-lock, no-task. Also rejected: the Tracing reviewer's F4, which asked to list reported-usage's two values and its "never" limit. The original statement is restored verbatim.

MISSED BY THE AUDIT, found by my own pass: workflows.steps-are-runs and no-operation-knowledge (pattern 3), the lost blank line after workflows.no-ask-continues, and the fronted "Only when" in tracing.created-or-found. The reviewer, not the worker, found the installer-keeps-installation-bound actor change. I rechecked every one of the 72 statements that still differ from d4423f70. None changes an actor or drops a limiting word.

Scenarios and contracts are unchanged. No test asserts this text. Every decision, with the run table, is in the decision log. Nothing is open and nothing needs escalation.

## Closed: merged, 2026-10-05T06:46:48Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit ffe43fdd8e3faa8d02b618737ac81a3ea98da1ad into main and closed it as merged. Nobody answers a report after that.
