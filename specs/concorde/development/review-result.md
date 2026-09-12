```concorde-document
{
  "id": "document.development.review-result",
  "owner": "module.development",
  "main_visible": true
}
```

# Review-result interface

`concorde-review-result@1` has exactly the typed envelope fields `type_id`, integer
`schema_version: 1` (not boolean), and `data`. Its closed payload has all these required fields.
Here `S` is a nonblank string, `N` is `S|null`, and `D` is `sha256:` plus exactly 64 lowercase
hexadecimal digits:

| Field | Type or allowed values |
| --- | --- |
| `context_id` | `D|null` |
| `input_digest` | `D` |
| `review_mode` | `"spec"|"code"` |
| `status` | `"no_findings"|"findings"|"incomplete"|"skipped"|"not_run"` |
| `representative_tasks` | unique `S[]` |
| `findings` | `Finding[]` |
| `gaps` | `ReviewGap[]` |
| `answer`, `target_id` | `S` |
| `focus_id` | `N` |
| `revision` | closed object with `spec_digest: D`, `implementation_digest: D|null`, `baseline: N`, `head: N`, all required |
| `semantic_completeness` | exactly `"not_proven"` |

A closed `Finding` requires `id: S`, `severity: "blocking"|"advisory"`, `target_id: S`,
`document: S`, `contract: S`, `location`, `problem: S`, and `affected_task: S`. The closed
`location` requires `path` (a safe project-relative path) and `line` (positive integer or null).
A closed `ReviewGap` requires `question: S`, `blocked_step: S`, and `needed_contract: S`, with
optional `target_id: S` and `context_id: D`. These optional wire fields do not weaken the review
host's requirement to bind blocking gaps to the reviewed target and context. Arrays may be empty
unless the review host's status/coverage rules require contents. Unknown fields, invalid versions,
unsafe paths and shape mismatches raise `TypedDataError` during typed validation. String baseline
and head fields identify revisions; the wire shape itself does not prove their freshness.

The context service validates allowed typed stage-input values and freezes their exact bytes into
the snapshot. Repair admission additionally belongs to the Development host: it binds the current
code review and revision, admits that declared result only to `tasks`/`implementation` repair
contexts, and removes write authority during review. A structurally valid review result alone
neither authorizes a repair nor proves review completion, currentness or semantic completeness.

The result's `target_id` identifies the selected Module whose task was reviewed. Each finding's
`target_id` identifies the sole owner of its contract definition, which may be a referenced
provider. `document` must be in the selected context; `affected_task` and gaps retain the
consumer's blocked step and snapshot. Repairing the provider definition requires its owner's
separate authoring boundary. A gap's `needed_contract` identifies that definition/owner when known;
capture never transfers ownership. The existing version-1 payload shape is retained, but acceptance
and freshness must use Protocol 5 ownership/reference semantics under a version-2 context wrapper;
old review evidence cannot be reused across the Protocol binding change.

This record is an output of Development review and an input to Harness repair admission. It has
no independent mutation effect. Invalid shapes fail typed admission; stale identity or an
inadmissible repair stops the affected transition without retrying under wider permissions.
An unchanged valid result is idempotent metadata, not a command to replay a repair. The retained wire shape now uses owner-aware admission and complete context freshness checks.
