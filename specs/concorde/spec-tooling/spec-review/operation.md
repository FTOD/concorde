# Spec review Operation

The exact step sequence, arguments and result of the `spec_review`
[Operation](../../glossary.json#concept.operation) of [Spec review](module.md).

## Invocation

```text
concorde run spec_review [--modules <id>[,<id>...]] [--check-findings] [--force]
```

The review works on the worktree it starts in. With a
[workspace binding](../../glossary.json#concept.workspace-binding) there, it reviews that
[workspace](../../glossary.json#concept.workspace), and `--modules` defaults to the binding's
Modules. Without one it is an [unbound run](../../glossary.json#concept.unbound-run), for instance
on the primary worktree, and judges the Specs as merged there. `--modules` names one or more
registered Modules of that worktree. `--check-findings` adds the checker, and `--force` reviews a
[Module](../../glossary.json#concept.module) again although its
[review memory](../../glossary.json#concept.review-memory) already judged its current
[context identity](../../glossary.json#concept.context-identity). The reviewer and the checker are
the Operation's two workers, with the [worker ids](../../glossary.json#concept.worker-id) `reviewer`
and `checker`, so the
[worker configuration](../../glossary.json#concept.worker-configuration) may give each
its own backend, model and level. The Operation takes no other argument and needs no user consent.

## Step sequence {#host-sequence}

The Operation runs these steps for each named Module. Modules are independent and none of their
reviewers writes, so their reviews could run at the same time; this version runs them one after
another. Step 1 validates the worktree once for all Modules.

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the workspace's Specs and validate the Module | Operation (Spec core) | loading error: the Operation fails; structural error in the Module's own documents or about the Module or a node it defines: the Module is `incomplete`, with the findings as host evidence |
| 2 | Compute the `review-spec` grant for the Module with the workspace as root and freeze it with its context identity | Operation (Spec core) | the Module is `incomplete` |
| 3 | Read the Module's review memory, an empty one when its file does not exist yet. When the memory records the grant's context identity as reviewed and `--force` is not given, launch no worker: skip to step 7, where the memory decides and `unchanged_since` names the run that judged these Specs. Otherwise generate the reviewer's settings, tool list and brief from the grant, the Reviewer brief and the memory's open findings | Operation (Workers) | an unusable memory, one that is not valid JSON, does not match the memory contract or belongs to another Module: the Module is `incomplete` (`review_memory_unusable`); otherwise the Operation fails |
| 4 | Launch the reviewer and wait for its [worker result](../../glossary.json#concept.worker-result) with findings; there is one round and no resume | Operation (Workers) | `blocked`, `failed`, timeout or an invalid result: the Module is `incomplete` |
| 5 | Audit that the worktree has no change | Operation (Workers) | any change: the Module is `incomplete`, with the audit violations as host evidence |
| 6 | With `--check-findings` and at least one finding, launch the checker under the same grant with the reviewer's numbered findings as task material, then audit again | Operation (Workers) | as steps 4 and 5; the reviewer's findings stay unchecked |
| 7 | Normalize the findings, merge them and the resolutions into the review memory (written only by a bound run), and derive the Module's outcome from the memory's open findings | Operation | a finding whose path is not in the workspace: the Module is `incomplete`, with `invalid-output` evidence |
| 8 | Write a [run record](../../glossary.json#concept.run-record) per worker | Operation (Workers) | the Operation fails |

After every Module is done, the Operation derives the verdict and returns the run's output. No step
runs [configured checks](../../glossary.json#concept.configured-check) and no step resumes a worker,
because no reviewer or checker changes a file. A Module whose review is `incomplete` writes no
review memory.

Normalizing a finding means: an absolute path inside the workspace becomes relative to it;
`module` becomes the Module that owns the cited document when the path is a registered document or
its metadata file; and a `blocking` finding whose path is not one of the reviewed Module's own
documents or their metadata files becomes `advisory`, with `finding-scope` host evidence naming it.
A checker status applies to the finding at its position; a status for an unknown position or a
second status for the same finding is ignored, and a finding without a status keeps `check` null.

## Result status

| Verdict | Status | Error |
| --- | --- | --- |
| `accepted` or `changes_required` | `ok` | none |
| `incomplete`, and some incomplete Module failed: a worker failed, a launch error, a timeout, an invalid result, an audit violation, a grant that could not be computed, an unusable review memory or a finding path outside the workspace | `failed` | `review_incomplete`, one cause per incomplete Module |
| `incomplete` otherwise: a structural error or a `blocked` worker | `blocked` | `review_incomplete`, one cause per incomplete Module |

A loading error in step 1 is `failed` with no output, and so is any other failure the step table
calls a failure of the Operation: the Execution runner turns it into a `failed` result with
`host-error` evidence. In every other case the result's `output` is
the review payload, including for `blocked` and `failed`, so the findings of the Modules that were
reviewed are never lost. The result's error is the Operation's `review_incomplete` link with the
reason `decision`; its causes are the error of every incomplete Module, in the order of the
Modules, never only the first. The error of an incomplete Module is the Operation's link for that
Module, whose actor names the Module: for a worker run it has Workers' link, and below
it the worker's own when the worker ended `blocked` or `failed`, as its cause; for a structural
error it is `structural_errors` with one cause per failing rule, file and message; for an unknown
Module it is `unknown_module`. The summary names every incomplete Module with its own summary and
counts the blocking findings that stand. The `worker` field holds the last worker result.

## Reviewer result

A reviewer ends with the ordinary worker result plus `findings`, an array of findings, and
optionally `resolved`, an array of `{id, reason}` naming each open earlier finding of the review
memory that the Specs no longer have and why. A finding that updates an open earlier finding
carries that finding's id as `earlier`; an earlier finding the reviewer neither updates nor
resolves stays open unchanged. A resolution that names no open earlier finding, or one this review
already resolved, is ignored and listed under `ignored` in the payload's `memory`; a finding whose
`earlier` names no open earlier finding, or one this review already updated or resolved, is kept
as a new finding. The checker
ends with the worker result plus `checks`, one `{finding, status, reason}` per finding it received,
where `finding` is the finding's position in the numbered list the checker received, starting at
1, and `status` is `confirmed` or `disputed`. Both end `ok` when they could do their work; a
`blocked` or `failed` worker still returns an empty `findings` or `checks` array.

A finding is `{module, path, anchor, line, dimension, severity, problem, evidence, suggestion}`,
plus `earlier` when it updates an earlier finding.
`module` is the reviewed Module, or the provider whose selected document the finding concerns;
`path` is a document member in the grant; `anchor` and `line` are optional; `dimension` is one of
`readability`, `obligations`, `design`, `views`, `terminology` and `context`; `severity` is
`blocking` or `advisory`. A finding about another Module's document is always `advisory`.

## Review payload

The [run result](../../glossary.json#concept.run-result) carries this payload as its `output`:

```concorde-contract
{
  "id": "contract.spec-review.payload",
  "version": 3,
  "schema": {
    "type": "object",
    "required": [
      "verdict",
      "modules"
    ],
    "additionalProperties": false,
    "properties": {
      "verdict": {
        "enum": [
          "accepted",
          "changes_required",
          "incomplete"
        ]
      },
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "required": [
            "module",
            "outcome",
            "context_identity",
            "findings",
            "memory"
          ],
          "additionalProperties": false,
          "properties": {
            "module": {
              "type": "string",
              "minLength": 1
            },
            "outcome": {
              "enum": [
                "accepted",
                "changes_required",
                "incomplete"
              ]
            },
            "context_identity": {
              "anyOf": [
                {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                {
                  "type": "null"
                }
              ]
            },
            "findings": {
              "type": "array",
              "items": {
                "type": "object",
                "required": [
                  "module",
                  "path",
                  "dimension",
                  "severity",
                  "problem",
                  "evidence",
                  "suggestion",
                  "check",
                  "id"
                ],
                "additionalProperties": false,
                "properties": {
                  "id": {
                    "anyOf": [
                      {
                        "type": "null"
                      },
                      {
                        "type": "string",
                        "pattern": "^f\\.[1-9][0-9]*$"
                      }
                    ]
                  },
                  "earlier": {
                    "type": "string",
                    "pattern": "^f\\.[1-9][0-9]*$"
                  },
                  "module": {
                    "type": "string",
                    "minLength": 1
                  },
                  "path": {
                    "type": "string",
                    "format": "project-path"
                  },
                  "anchor": {
                    "type": "string",
                    "minLength": 1
                  },
                  "line": {
                    "type": "integer",
                    "minimum": 1
                  },
                  "dimension": {
                    "enum": [
                      "readability",
                      "obligations",
                      "design",
                      "views",
                      "terminology",
                      "context"
                    ]
                  },
                  "severity": {
                    "enum": [
                      "blocking",
                      "advisory"
                    ]
                  },
                  "problem": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "string",
                    "minLength": 1
                  },
                  "suggestion": {
                    "type": "string",
                    "minLength": 1
                  },
                  "check": {
                    "anyOf": [
                      {
                        "type": "null"
                      },
                      {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "status",
                          "reason"
                        ],
                        "properties": {
                          "status": {
                            "enum": [
                              "confirmed",
                              "disputed"
                            ]
                          },
                          "reason": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    ]
                  }
                }
              }
            },
            "memory": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "new",
                    "updated",
                    "resolved",
                    "carried",
                    "ignored",
                    "unchanged_since"
                  ],
                  "properties": {
                    "unchanged_since": {
                      "anyOf": [
                        {
                          "type": "null"
                        },
                        {
                          "type": "string",
                          "minLength": 1
                        }
                      ]
                    },
                    "new": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "updated": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "resolved": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "id",
                          "reason"
                        ],
                        "properties": {
                          "id": {
                            "type": "string",
                            "pattern": "^f\\.[1-9][0-9]*$"
                          },
                          "reason": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    },
                    "carried": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "id",
                          "path",
                          "dimension",
                          "severity",
                          "problem",
                          "evidence",
                          "suggestion"
                        ],
                        "properties": {
                          "id": {
                            "type": "string",
                            "pattern": "^f\\.[1-9][0-9]*$"
                          },
                          "path": {
                            "type": "string",
                            "minLength": 1
                          },
                          "anchor": {
                            "type": "string",
                            "minLength": 1
                          },
                          "line": {
                            "type": "integer",
                            "minimum": 1
                          },
                          "dimension": {
                            "type": "string",
                            "minLength": 1
                          },
                          "severity": {
                            "enum": [
                              "blocking",
                              "advisory"
                            ]
                          },
                          "problem": {
                            "type": "string",
                            "minLength": 1
                          },
                          "evidence": {
                            "type": "string",
                            "minLength": 1
                          },
                          "suggestion": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    },
                    "ignored": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "id",
                          "reason"
                        ],
                        "properties": {
                          "id": {
                            "type": "string",
                            "pattern": "^f\\.[1-9][0-9]*$"
                          },
                          "reason": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    }
                  }
                }
              ]
            }
          }
        }
      }
    }
  },
  "semantics": "The outcome of one Spec review. Each Module's outcome is incomplete when it could not be reviewed, changes_required when a blocking finding about its own documents is not disputed, and accepted otherwise; the verdict is incomplete if any Module is incomplete, else changes_required if any Module requires changes, else accepted. Findings are reviewer claims; check is null when no checker ran. context_identity is null only when no grant could be computed. Each Module's outcome is the state of its review memory after this review: any open blocking finding, reported now or carried from an earlier review, requires changes. Each reported finding has the memory id it was kept under, or null when a checker disputed it; earlier names the earlier finding it updates. memory lists the ids this review added and updated, the earlier findings it resolved with their reasons, the open earlier findings it carried unchanged in full, and resolutions it ignored because they named no open finding; it is null exactly when the Module's outcome is incomplete. unchanged_since names the review whose memory decided a Module whose Specs, by context identity, are the ones that review judged, so that no reviewer was launched again; it is null when a reviewer ran. A behaviour or field change increments the version.",
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
            "check": {
              "status": "confirmed",
              "reason": "Both obligations are independently testable."
            },
            "id": "f.1"
          }
        ],
        "memory": {
          "new": [
            "f.1"
          ],
          "updated": [],
          "resolved": [],
          "carried": [],
          "ignored": [],
          "unchanged_since": null
        }
      }
    ]
  }
}
```

### Review memory

<a id="contract.spec-review.memory"></a>

```concorde-contract
{
  "id": "contract.spec-review.memory",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "module",
      "findings"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "module": {
        "type": "string",
        "minLength": 1
      },
      "reviewed": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "context_identity",
          "run"
        ],
        "properties": {
          "context_identity": {
            "type": "string",
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "run": {
            "type": "string",
            "minLength": 1
          }
        }
      },
      "findings": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "status",
            "path",
            "dimension",
            "severity",
            "problem",
            "evidence",
            "suggestion",
            "first_run",
            "last_run",
            "resolution"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^f\\.[1-9][0-9]*$"
            },
            "status": {
              "enum": [
                "open",
                "resolved"
              ]
            },
            "path": {
              "type": "string",
              "minLength": 1
            },
            "anchor": {
              "type": "string",
              "minLength": 1
            },
            "line": {
              "type": "integer",
              "minimum": 1
            },
            "dimension": {
              "type": "string",
              "minLength": 1
            },
            "severity": {
              "enum": [
                "blocking",
                "advisory"
              ]
            },
            "problem": {
              "type": "string",
              "minLength": 1
            },
            "evidence": {
              "type": "string",
              "minLength": 1
            },
            "suggestion": {
              "type": "string",
              "minLength": 1
            },
            "first_run": {
              "type": "string",
              "minLength": 1
            },
            "last_run": {
              "type": "string",
              "minLength": 1
            },
            "resolution": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "string",
                  "minLength": 1
                }
              ]
            }
          }
        }
      }
    }
  },
  "semantics": "The review memory of one Module, .concorde/reviews/spec/<module>.json, tracked with the project: every finding the Spec reviews of the Module kept, each with a stable id f.<n> never reused, its content as last reported, status open or resolved, the runs that first and last reported or resolved it, and the resolution reason once resolved. Only a spec_review in a bound workspace writes it, merging its review into it; an unbound review reads it. reviewed records the context identity of the Specs the last completed review judged and its run: while the Module's context identity is the same, a review is not run again unless forced. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "module": "module.checkout",
    "reviewed": {
      "context_identity": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "run": "r-20260926T113000-spec_review-4e5f6a7b"
    },
    "findings": [
      {
        "id": "f.1",
        "status": "resolved",
        "path": "specs/checkout/requirements.md",
        "anchor": "req.checkout.single-order",
        "dimension": "obligations",
        "severity": "blocking",
        "problem": "The requirement holds two obligations.",
        "evidence": "The checkout SHALL hold stock and SHALL create one order.",
        "suggestion": "Split it into two requirements.",
        "first_run": "r-20260926T101500-spec_review-0a1b2c3d",
        "last_run": "r-20260926T113000-spec_review-4e5f6a7b",
        "resolution": "The requirement was split into two."
      },
      {
        "id": "f.2",
        "status": "open",
        "path": "specs/checkout/module.md",
        "dimension": "readability",
        "severity": "advisory",
        "problem": "Usage names the retry limit before defining it.",
        "evidence": "Retries stop at the limit.",
        "suggestion": "Define the retry limit first.",
        "first_run": "r-20260926T113000-spec_review-4e5f6a7b",
        "last_run": "r-20260926T113000-spec_review-4e5f6a7b",
        "resolution": null
      }
    ]
  }
}
```

The Operation adds the run result's own evidence, each item naming the Module and worker it
concerns: the grant and context identity of every worker, the `worker-model` item naming each
worker's worker id, backend, model and level
([worker settings](../../execution/operations/workers.md#worker-backend-and-model)), the audits,
the transcript paths, the
structural findings of step 1 (kind `structural`), the scope corrections of step 7 (kind
`finding-scope`) and any unusable finding (kind `invalid-output`). The worker run identities are in
the result's `worker_runs`, reviewer before checker, in Module order.
