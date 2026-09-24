# Spec review Operation

The exact host sequence, arguments and result of the `spec_review` Operation of
[Spec review](module.md).

## Invocation

```text
concorde run spec_review --task <task-id> --modules <id>[,<id>...] [--check-findings]
```

`--modules` names one or more registered Modules of the task worktree. `--check-findings` adds the
checker. The Operation takes no other argument and needs no user consent.

## Host sequence {#host-sequence}

The host runs these steps for each named Module. Modules are independent and none of their
reviewers writes, so their reviews could run at the same time; this version runs them one after
another. Step 1 validates the task worktree once for all Modules.

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the task worktree's Specs and validate the Module | host (Spec core) | loading error: the Operation fails; structural error in the Module's own documents or about the Module or a node it defines: the Module is `incomplete`, with the findings as host evidence |
| 2 | Compute the `review-spec` grant for the Module with the task worktree as root and freeze it with its context identity | host (Spec core) | the Module is `incomplete` |
| 3 | Generate the reviewer's settings, tool list and brief from the grant and the Reviewer brief | host (Workers) | the Operation fails |
| 4 | Launch the reviewer and wait for its worker result with findings; there is one round and no resume | host (Workers) | `blocked`, `failed`, timeout or an invalid result: the Module is `incomplete` |
| 5 | Audit that the worktree has no change | host (Workers) | any change: the Module is `incomplete`, with the audit violations as host evidence |
| 6 | With `--check-findings` and at least one finding, launch the checker under the same grant with the reviewer's numbered findings as task material, then audit again | host (Workers) | as steps 4 and 5; the reviewer's findings stay unchecked |
| 7 | Normalize the findings and derive the Module's outcome from them | host | a finding whose path is not in the task worktree: the Module is `incomplete`, with `invalid-output` evidence |
| 8 | Write a run record per worker | host (Workers) | the Operation fails |

After every Module is done, the host derives the verdict and returns the Operation result. No step
runs configured checks and no step resumes a worker, because a review changes no file.

Normalizing a finding means: an absolute path inside the task worktree becomes relative to it;
`module` becomes the Module that owns the cited document when the path is a registered document or
its metadata file; and a `blocking` finding whose path is not one of the reviewed Module's own
documents or their metadata files becomes `advisory`, with `finding-scope` host evidence naming it.
A checker status applies to the finding at its position; a status for an unknown position or a
second status for the same finding is ignored, and a finding without a status keeps `check` null.

## Result status

| Verdict | Status | Error |
| --- | --- | --- |
| `accepted` or `changes_required` | `ok` | none |
| `incomplete`, and some incomplete Module failed: a worker failed, a launch error, a timeout, an invalid result, an audit violation or a grant that could not be computed | `failed` | `review_incomplete`, one cause per incomplete Module |
| `incomplete` otherwise: a structural error or a `blocked` worker | `blocked` | `review_incomplete`, one cause per incomplete Module |

A loading error in step 1 is `failed` with no output. In every other case the result's `output` is
the review payload, including for `blocked` and `failed`, so the findings of the Modules that were
reviewed are never lost. The result's error is the Operation's `review_incomplete` link with the
reason `decision`; its causes are the error of every incomplete Module, in the order of the
Modules, never only the first. The error of an incomplete Module is the Operation's link for that
Module, whose actor names the Module: for a worker run it has the Workers harness's link, and below
it the worker's own when the worker ended `blocked` or `failed`, as its cause; for a structural
error it is `structural_errors` with one cause per failing rule, file and message; for an unknown
Module it is `unknown_module`. The summary names every incomplete Module with its own summary and
counts the blocking findings that stand. The `worker` field holds the last worker result.

## Reviewer result

A reviewer ends with the ordinary worker result plus `findings`, an array of findings. The checker
ends with the worker result plus `checks`, one `{finding, status, reason}` per finding it received,
where `finding` is the finding's position in the numbered list the checker received, starting at
1, and `status` is `confirmed` or `disputed`. Both end `ok` when they could do their work; a
`blocked` or `failed` worker still returns an empty `findings` or `checks` array.

A finding is `{module, path, anchor, line, dimension, severity, problem, evidence, suggestion}`.
`module` is the reviewed Module, or the provider whose selected document the finding concerns;
`path` is a document member in the grant; `anchor` and `line` are optional; `dimension` is one of
`readability`, `obligations`, `design`, `views`, `terminology` and `context`; `severity` is
`blocking` or `advisory`. A finding about another Module's document is always `advisory`.

## Review payload

The Operation result carries this payload:

```concorde-contract
{
  "id": "contract.spec-review.payload",
  "version": 1,
  "schema": {
    "type": "object",
    "required": ["verdict", "modules"],
    "additionalProperties": false,
    "properties": {
      "verdict": {"enum": ["accepted", "changes_required", "incomplete"]},
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "required": ["module", "outcome", "context_identity", "findings"],
          "additionalProperties": false,
          "properties": {
            "module": {"type": "string", "minLength": 1},
            "outcome": {"enum": ["accepted", "changes_required", "incomplete"]},
            "context_identity": {"anyOf": [{"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}, {"type": "null"}]},
            "findings": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["module", "path", "dimension", "severity", "problem", "evidence", "suggestion", "check"],
                "additionalProperties": false,
                "properties": {
                  "module": {"type": "string", "minLength": 1},
                  "path": {"type": "string", "format": "project-path"},
                  "anchor": {"type": "string", "minLength": 1},
                  "line": {"type": "integer", "minimum": 1},
                  "dimension": {"enum": ["readability", "obligations", "design", "views", "terminology", "context"]},
                  "severity": {"enum": ["blocking", "advisory"]},
                  "problem": {"type": "string", "minLength": 1},
                  "evidence": {"type": "string", "minLength": 1},
                  "suggestion": {"type": "string", "minLength": 1},
                  "check": {"anyOf": [
                    {"type": "null"},
                    {"type": "object", "required": ["status", "reason"], "additionalProperties": false,
                     "properties": {"status": {"enum": ["confirmed", "disputed"]}, "reason": {"type": "string", "minLength": 1}}}
                  ]}
                }
              }
            }
          }
        }
      }
    }
  },
  "semantics": "The outcome of one Spec review. Each Module's outcome is incomplete when it could not be reviewed, changes_required when a blocking finding about its own documents is not disputed, and accepted otherwise; the verdict is incomplete if any Module is incomplete, else changes_required if any Module requires changes, else accepted. Findings are reviewer claims; check is null when no checker ran. context_identity is null only when no grant could be computed.",
  "example": {
    "verdict": "changes_required",
    "modules": [
      {
        "module": "module.checkout",
        "outcome": "changes_required",
        "context_identity": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "findings": [
          {
            "module": "module.checkout",
            "path": "specs/checkout/requirements.md",
            "anchor": "req.checkout.single-order",
            "dimension": "obligations",
            "severity": "blocking",
            "problem": "The requirement states two obligations in one sentence.",
            "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
            "suggestion": "Split the notification into its own requirement.",
            "check": {"status": "confirmed", "reason": "Both obligations are independently testable."}
          }
        ]
      }
    ]
  }
}
```

The host adds the Operation result's own evidence, each item naming the Module and worker it
concerns: the grant and context identity of every worker, the audits, the transcript paths, the
structural findings of step 1 (kind `structural`), the scope corrections of step 7 (kind
`finding-scope`) and any unusable finding (kind `invalid-output`). The worker run identities are in
the result's `worker_runs`, reviewer before checker, in Module order.
