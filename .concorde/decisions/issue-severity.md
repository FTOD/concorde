# Decision log: issue-severity

Goal: Give every Issue report a severity (critical, high, medium, low) beside its tier, have every reporter record it, and let issue list filter by severity and sort by it so work starts from the most severe Issues

## Brief (main agent, 2026-10-01)

The developer wants Issues to carry a severity so that fixing can start from the most important
problems, and wants task sessions to record it when they report an Issue. The developer decided:

1. **Name and levels.** A new report field `severity`, one of `critical`, `high`, `medium`, `low`
   (most severe first). It says how much the problem matters (its impact), not who may fix it:
   it is orthogonal to the existing `tier`, which stays unchanged. Like the tier, the latest
   report of an Issue supplies its current severity, and a later report may change it.
2. **Every reporter records it.** Every new report carries a severity: the main agent and task
   sessions (main-session guidance and task-session prompt), the review workers and chairs whose
   findings become Issues (`spec_review`, `spec_panel`, `code_review`: their finding schemas,
   prompts and the code that turns findings into Issue reports), and Dogfooding's defect reports.
   Records written before severity existed stay valid and hold reports without one; such an Issue
   has no severity until a report with one is appended (as was done for tiers).
3. **Listing.** `concorde issues list` gains `--severity` (filter, like `--tier`) and
   `--sort severity`, and the project MCP server's `issue_list` gains the same as `severity` and
   `sort`. Sorting by severity puts the most severe first; equal severities are ordered by tier,
   `decision-needed` first down to `suggestion`, then by time. Issues without a severity sort
   last. Without `--sort`, `list` keeps its current order. Each `list` row shows the severity.

Left to the task session: whether the record schema version must change, the exact wording in each
Spec and prompt, a short guide for choosing a severity (e.g. critical = wrong results, data loss,
or a broken core flow with no workaround; low = cosmetic), the glossary entry
`concept.issue-severity` owned by `module.issues` (it meets the admission criterion: several
Modules use it), and the order of the work. Use `specify` before `implement` or do the work
directly, whichever is more reliable. Escalate anything that would change another promise of
these Modules beyond the above.

## Task session decisions (2026-10-01)

- **Work done directly, not through `specify`/`implement`.** The change touches seven Modules'
  Specs, prompts, three Operations' schemas and their contracts in lockstep, and each piece has a
  deterministic test, so doing it directly was more reliable than bounded worker runs.
- **Versions.** The report contract `contract.issues.report` (typed value
  `concorde-issue-report`) goes from version 2 to 3 (new required field `severity`). New Issue
  records get `schema_version` 4; version 3 records (written before severities) may hold reports
  without a severity and version 2 records reports without a tier or severity; the store never
  rewrites a record's version, as was done for tiers. The review payload contracts change too:
  `contract.spec-review.payload` 4→5, `contract.spec-review.panel-payload` 3→4,
  `contract.code-review.review` 3→4 (findings require `severity`; `earlier_issues.carried` entries
  carry `severity`, null for an Issue without one).
- **Sort order, "then by time".** Ties of equal severity and tier are ordered by the
  `created_at` of the Issue's first report (oldest first), then by identity. An Issue without a
  severity sorts after every Issue with one, and within a severity an Issue without a tier comes
  after the tiered ones. `sort` takes only `severity`; any other value is refused (`usage` in the
  CLI, `invalid_input` in the tool, `invalid_issue` in the store).
- **Rows.** Every `list` row gains `severity` (null without one) beside `tier`.
- **Reviewers.** Reviewer and architect findings and the panel chair's merged findings require a
  `severity`; the chair may change it like the tier. Earlier Issues offered to reviewers include
  their severity, and reviewers are told to report an earlier Issue again when they would give it
  another severity. Moving a blocking finding about another Module's document down to a suggestion
  leaves its severity as it is.
- **Severity guide** (Issues module entry, guidance and prompts): critical = wrong results,
  lost/corrupted data, security exposure or a core flow broken with no workaround; high = a main
  flow broken or wrong although a workaround exists, or a promise that leads the work relying on
  it to act wrongly; medium = a secondary flow or edge case, or a gap that slows work without
  misleading it; low = cosmetic. Stated as independent of the tier.
- **Wording clash.** The reviewer checklist said "Blocking and advisory are the criteria's
  severity"; it is reworded so that "severity" means only the Issue severity. The Protocol's own
  "Severity" section (blocking/advisory, owned by module.spec) is outside this task: recorded as
  Issue I-d24569b23b345cd3b8e89ae8b3944c17 (decision-needed). It was recorded without a severity
  because the primary branch's Issue store does not know the field yet.
- **Dogfooding.** Dogfooding's Spec example of a defect report lacked a tier, which was already
  stale; it now carries both tier and severity, and Dogfooding declares that it relies on
  `concept.issue-tier` and `concept.issue-severity`.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T13:24:19Z

issue-severity delivered: delivery commit ed0a2427 on concorde/issue-severity. Task-validation said ready, and the full test suite passed (874 passed, 4 skipped). Spec-validation passes with no findings. No escalations.

What changed:
- Issues: every report now requires `severity` (critical/high/medium/low), separate from the tier. The latest report supplies the Issue's severity. The report contract goes from v2 to v3 and new records get schema_version 4. Records of v3 (no severity) and v2 (no tier, no severity) stay valid and are never rewritten.
- `concorde issues list` gains `--severity` (repeatable) and `--sort severity`, and `issue_list` gains `severity` and `sort`. The severity sort puts the most severe first, then by tier from decision-needed down to suggestion, then oldest first report, then identity. Issues without a severity come last. Without `sort` the order is unchanged (by identity). Every row now shows `severity`.
- spec_review, spec_panel and code_review: reviewer, architect and chair findings require `severity`, and it is carried into the Issue report. `earlier_issues.carried` entries and the earlier Issues offered to reviewers include their severity. Contract versions: spec-review payload 4→5, panel payload 3→4, code-review review 3→4.
- Guidance and prompts now ask every reporter for a severity, with a one-line guide per level: main-session skill (with a table, plus "choose what to fix first from issue_list status open sort severity"), task-session prompt, reviewer checklist, review-code, panel chair and checker, and the Dogfooding defect report (field and example).
- Specs updated for module.issues (new Severities section with anchor concept.issue-severity, requirements req.issues.severity-required and req.issues.list-by-severity, scenarios), main-session (req.main-session.issues-severity, scenario and test), spec-review, code-review, dogfooding and concorde. New glossary entry concept.issue-severity is owned by module.issues and contrasts with concept.issue-tier. docs/using-concorde.md is updated too.

Decisions I made on my own (all in the decision log):
- I did the work directly rather than through Operations.
- The version bumps listed above.
- Ties on severity and tier are broken by the first report's created_at, oldest first.
- The wording of the severity guide.
- A blocking finding on another Module's document is moved down to a suggestion; its severity stays as it was.
- Dogfooding's stale Spec example now has tier and severity.

Still open:
- I recorded Issue I-d24569b23b345cd3b8e89ae8b3944c17 (module.spec, decision-needed): the Protocol's own "Severity" section (protocol/evaluation.md) uses "severity" for blocking/advisory, which clashes with the new term. I reworded the reviewer checklist inside this task; the Protocol is not in this task's Modules. It has no severity yet because the primary branch's store does not know the field until this merge.
- After the merge, the project MCP server sessions need restarting so their `issue_list` and `issue_report` load the new code.
- This task resolves no Issues.

## Closed: merged, 2026-10-01T13:24:20Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit ed0a2427d6990d4330dbf2ee7fd10444e4247c47 into main and closed it as merged. Nobody answers a report after that.
