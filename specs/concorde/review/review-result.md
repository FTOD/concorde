# Review-result interface

`concorde-review-result@2` has exactly the typed envelope fields `type_id`, integer
`schema_version: 2` and `data`. The closed payload contains the fields below. `S` is a nonblank
string, `N` is `S|null`, and `D` is `sha256:` followed by 64 lowercase hexadecimal digits.

| Field | Type or allowed values |
| --- | --- |
| `context_id` | `D` or null |
| `input_digest` | `D` |
| `review_mode` | `spec` or `code` |
| `status` | `no_findings`, `findings`, `incomplete`, `skipped` or `not_run` |
| `representative_tasks` | unique `S[]` |
| `issues` | `IssueJudgment[]` |
| `answer`, `target_id` | `S` |
| `focus_id` | `N` |
| `revision` | closed object with spec_digest, nullable implementation_digest, baseline and head |
| `semantic_completeness` | exactly `not_proven` |

Each closed `IssueJudgment` has `issue_id`, `report_id`, `path`, `severity: blocking|advisory` and
`affected_task`. The first three fields are the host-issued immutable report receipt. The review
worker must have reported or explicitly received that observation; guessed identities, foreign
observations and duplicate Issue judgments are invalid. There is no parallel `gaps` array, no
copied question/contract tuple and no free-text equality join. The canonical problem, evidence and
ownership live in the Issue observation; severity is this review's judgment about its admitted task.

The result's target_id identifies the reviewed Module. An Issue can identify a different known
contract owner from that Module's admitted references. Reporting scope and definition ownership do
not merge. Evidence locations are checked when the report is accepted; a receipt adds no source
access. Reviewers never copy raw code, patches or logs into reports. A typed result is not proof
of completion or freshness: the host also checks coverage, bound identities, source/configuration
bytes and actual worker completion. Old version-1 results are rejected rather than silently reused.

Blocking judgments derive task-local blocker references with `blocked_step=affected_task`. Missing
or conflicting necessary contracts can stop for Spec repair; implementation defects can enter the
existing bounded code-repair edge. Reporting an advisory Issue does not stop the review or its
caller. An interrupted review remains incomplete even when its already acknowledged reports survive.

For admitted tasks/implementation repair, Harness freezes the exact review result together with a
`concorde-issue-context` containing only the selected observations' contract-level description,
impact and basis. It does not expose the rest of the Issue store or a prior conversation. Disposition
changes cannot rewrite the observation a review judged, and closing an Issue does not make a stale
review current. Required review gates still bind the reviewed Spec/code inputs and independent
completion evidence, not a problem's open/closed flag.
