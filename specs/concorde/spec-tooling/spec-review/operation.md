# Spec review Operation

The exact host sequence, arguments and result of the `spec_review` Operation of
[Spec review](module.md). It is designed and not yet implemented.

## Invocation

```text
concorde run spec_review --task <task-id> --modules <id>[,<id>...] [--check-findings]
```

`--modules` names one or more registered Modules of the task worktree. `--check-findings` adds the
checker. The Operation takes no other argument and needs no user consent.

## Host sequence {#host-sequence}

The host runs these steps for each named Module; Modules are independent, and their reviewers may
run at the same time because none of them writes.

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the task worktree's Specs and validate the Module | host (Spec core) | loading error: the Operation fails; structural error: the Module is `incomplete`, with the findings as host evidence |
| 2 | Compute the `review-spec` grant for the Module with the task worktree as root and freeze it with its context identity | host (Spec core) | the Module is `incomplete` |
| 3 | Generate the reviewer's settings, tool list and brief from the grant and the Reviewer brief | host (Workers) | the Operation fails |
| 4 | Launch the reviewer and wait for its worker result with findings | host (Workers) | `blocked`, `failed` or timeout: the Module is `incomplete` |
| 5 | Audit that the worktree has no change | host (Workers) | any change: the Module is `incomplete`, with the audit violations as host evidence |
| 6 | With `--check-findings`, launch the checker under the same grant with the reviewer's findings as task material, then audit again | host (Workers) | as steps 4 and 5; the reviewer's findings stay unchecked |
| 7 | Derive the Module's outcome from its findings | host | — |
| 8 | Write a run record per worker | host (Workers) | the Operation fails |

After every Module is done, the host derives the verdict and returns the Operation result. No step
runs configured checks and no step resumes a worker, because a review changes no file.

## Reviewer result

A reviewer ends with the ordinary worker result plus `findings`, an array of findings. The checker
ends with the worker result plus `checks`, one `{finding, status, reason}` per finding it received,
where `finding` is the finding's position and `status` is `confirmed` or `disputed`.

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

The host adds the Operation result's own evidence: the grant and context identity of every worker,
audit violations, run record paths and the structural findings of step 1.
