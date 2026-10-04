# Spec review Operation

The exact step sequence, arguments, Issue reports and result of the `spec_review`
[Operation](../../glossary.json#concept.operation) of [Spec review](module.md).

## Invocation

```text
concorde run spec_review [--modules <id>[,<id>...]] [--check-findings]
```

The review works on the worktree it starts in. With a
[workspace binding](../../glossary.json#concept.workspace-binding) there, it reviews that
[workspace](../../glossary.json#concept.workspace). In that case, `--modules` defaults to the
binding's Modules. Without one, it is an [unbound run](../../glossary.json#concept.unbound-run), for
instance on the primary worktree. In that case, it judges the
[Specs](../../glossary.json#concept.spec) as merged there. `--modules` names one or more registered
Modules of that worktree. `--check-findings` adds the checker. The reviewer and the checker are the
Operation's two workers. Their [worker ids](../../glossary.json#concept.worker-id) are `reviewer`
and `checker`. The [worker configuration](../../glossary.json#concept.worker-configuration) may give
each its own backend, model and level. The Operation takes no other argument. It needs no user
consent.

## Step sequence {#host-sequence}

The Operation runs these steps for each named [Module](../../glossary.json#concept.module).
Modules are independent. None of their reviewers writes. Their reviews could therefore run at the
same time. This version runs them one after another. Step 1 validates the worktree once for all
Modules.

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the workspace's Specs and validate the Module | Operation (Spec core) | loading error: the Operation fails; structural error in the Module's own documents or about the Module or a node it defines: the Module is `incomplete`, with the findings as host evidence |
| 2 | Compute the `review-spec` grant for the Module with the workspace as root and freeze it with its [context identity](../../glossary.json#concept.context-identity) | Operation (Spec core) | the Module is `incomplete` |
| 3 | Read the Module's [earlier Issues](#earlier-issues) from the project's Issues, then generate the reviewer's settings, tool list and brief from the grant, the Reviewer brief and those Issues | Operation (Issues, Workers) | Issues that cannot be read: the Module is `incomplete` (`issues_unreadable`); otherwise the Operation fails |
| 4 | Launch the reviewer and wait for its [worker result](../../glossary.json#concept.worker-result) with findings; when a finding's path is not one of the workspace, the reviewer is resumed once with those paths to correct, and its last result counts | Operation (Workers) | `blocked`, `failed`, timeout or an invalid result: the Module is `incomplete` |
| 5 | Audit that the worktree has no change | Operation (Workers) | any change: the Module is `incomplete`, with the audit violations as host evidence |
| 6 | With `--check-findings` and at least one finding, launch the checker under the same grant with the reviewer's numbered findings as task material, then audit again | Operation (Workers) | as steps 4 and 5; the reviewer's findings stay unchecked |
| 7 | Normalize the findings and settle which earlier Issue each names and which it resolves | Operation | none: a finding whose path is not in the workspace is rejected alone, listed under the Module's `rejected` with the reason and as `invalid-output` evidence, and the other findings go on |
| 8 | [Report](#reporting-findings) every finding the checker did not dispute as an Issue, in the order of the findings | Operation (Issues) | a refusal of the Issue store: the Module is `incomplete` (`issues_unreported`) and its later findings are not reported |
| 9 | Derive the Module's outcome from the Issues that stand | Operation | none |
| 10 | Write a [run record](../../glossary.json#concept.run-record) per worker | Operation (Workers) | the Operation fails |

After every Module is done, the Operation derives the verdict. It then returns the run's output.
Because no reviewer or checker changes a file, no step runs
[configured checks](../../glossary.json#concept.configured-check). The only
[resume round](../../glossary.json#concept.resume-round) is the one that asks a reviewer to correct
the paths of its findings. When a Module's review stopped before step 8, it reports no Issue.

Normalizing a finding means applying these rules:

- An absolute path inside the workspace becomes relative to it.
- When the path is a registered document or its metadata file, `module` becomes the Module that
  owns the cited document.
- When both conditions hold, the finding becomes a `suggestion`:
  - The finding has a blocking tier.
  - Its path is outside the reviewed Module's own documents and their metadata files.

  The `finding-scope` host evidence names the finding.

A checker status applies to the finding at its position. A status is ignored in either case:

- It is for an unknown position.
- It is a second status for the same finding.

A finding without a status keeps `check` null.

### Earlier Issues

A Module's **earlier Issues** are the open [Issues](../../glossary.json#concept.issue) of the
project that meet both conditions:

- Their owner is the Module.
- A `spec_review` or `spec_panel` run made one of their reports.

The Operation reads them from the primary worktree of the worktree the run started in. It reads
them in the order of their identities. A worker receives each as its latest report states it, with
these fields:

- Its identity.
- Its severity.
- Its tier.
- Its title.
- Its description.
- Its evidence.

Settling them follows the worker's claims under these rules. A finding whose `earlier` names an
earlier Issue is that Issue's new report. In either of these cases, a finding keeps no `earlier`
and becomes a new Issue:

- Its `earlier` names any other Issue.
- It names an Issue another finding of the review already named.

In those cases, the name is listed under `ignored`. When a resolution names an earlier Issue that
no finding names, it lists the Issue as `resolved` with its reason. When a resolution names any of
these, it is listed under `ignored`:

- Any other Issue.
- An Issue a finding names.
- An Issue already resolved.

Every earlier Issue that is neither named nor resolved is `carried`. A finding the checker
disputed names no Issue. It is reported nowhere. An earlier Issue it named is carried.

### Reporting findings

In bound and unbound runs alike, the Operation reports each finding through the Issue store as one
[Issue report](../../glossary.json#concept.issue-report). It never reports through a worker. When a
finding names an earlier Issue, the Operation appends it to that Issue. It uses the
[revision](../../glossary.json#concept.issue-revision) it reads just before the append. Any other
finding creates a new Issue. The report is:

| Field | Value |
| --- | --- |
| `report_key` | `<module>/<n>`: the reviewed Module and the finding's position among its findings |
| `tier` | the finding's tier |
| `severity` | the finding's severity |
| `type`, `subtype` | `gap` and `missing-contract` for the dimension `context`, `gap` and `spec-conflict` for `consistency`, `bug` and `null` for every other dimension |
| `title` | the finding's title |
| `description` | the finding's problem, then its suggested repair |
| `impact` | the finding's impact |
| `basis` | the Operation and run, the document, anchor and line judged, the dimension and the quoted evidence; for a panel also the chair's note and the labels merged |
| `owner_target_id` | the finding's `module` |
| `evidence` | the cited document, described by its anchor or line |
| `issue_id`, `expected_revision` | for an append only: the earlier Issue and its revision |

The Operation supplies the report's provenance:

- `invocation_id` is the run identity.
- `agent` is `operation`.
- `operation` is the Operation's name.
- `phase` is `report`.
- `target_id` is the reviewed Module.
- `context_id` is the context identity of the grant the finding was judged under.
- For an unbound run, `change_id` is `null`. Otherwise, it is the workspace.
- When Git cannot tell, `head` is `null`. Otherwise, it is the commit the reviewed worktree's `HEAD`
  names.

The store commits each report on the primary branch before it answers. A refusal stops the
Module's reporting. Examples include:

- A busy [merge lock](../../glossary.json#concept.merge-lock) after the store's wait.
- An unfinished merge.
- A stale revision.
- A closed earlier Issue.

In that case, the Module is `incomplete` with `issues_unreported`. The cause of that error is the
store's error. The Operation reports no further finding of that Module. It never records the refusal
as an Issue. It goes on with the next Module. A finding left unreported keeps no `earlier`, since
nothing was appended to the earlier Issue it named. That Issue is `carried`. The Operation never
closes or reopens an Issue.

### Without the issues part

Where the issues part is not installed, steps 3 and 8 do nothing with Issues:

- No earlier Issues are read or offered. Thus, every Module's `earlier_issues` is null.
- Every finding the checker did not dispute stays in the result with `issue` null.
- The result's summary says that the findings were not recorded as Issues.

Step 9 then derives the Module's outcome from those findings exactly as from the Issues they
would become. When one of a blocking tier stands, the outcome is `changes_required`.

### Step output

Whether or not Issues are installed, the run's output also carries one `notes` item of kind
`review`. It follows the [step output convention](../../workflows/contracts.md#contract.workflows.step-output).
The item holds the verdict and each Module's outcome with its count of blocking findings. This
lets a workflow report the review without knowing this payload.

## Result status

| Verdict | Status | Error |
| --- | --- | --- |
| `accepted` or `changes_required` | `ok` | none |
| `incomplete`, and some incomplete Module failed: a worker failed, a launch error, a timeout, an invalid result, an audit violation, a grant that could not be computed, Issues that could not be read or written, or a finding path outside the workspace | `failed` | `review_incomplete`, one cause per incomplete Module |
| `incomplete` otherwise: a structural error or a `blocked` worker | `blocked` | `review_incomplete`, one cause per incomplete Module |

A loading error in step 1 is `failed` with no output. The same applies to any other failure the
step table calls a failure of the Operation. The Execution runner turns it into a `failed` result
with `host-error` evidence. In every other case, the result's `output` is the review payload,
including for `blocked` and `failed`. Thus, the findings of the Modules that were reviewed are
never lost. The result's error is the Operation's `review_incomplete` link with the reason
`decision`. Its causes are the error of every incomplete Module, in the order of the Modules, never
only the first.

The error of an incomplete Module is the Operation's link for that Module. Its actor names the
Module. Its form depends on the error:

- For a worker run, it has Workers' link as its cause. When the worker ended `blocked` or `failed`,
  the worker's own link is below Workers' link.
- For a structural error, it is `structural_errors` with one cause per failing rule, file and
  message.
- For Issues that could not be read or written, it is `issues_unreadable` or `issues_unreported`
  with the Issue store's error as its cause.
- For an unknown Module, it is `unknown_module`.

The summary names every incomplete Module with its own summary. It counts the blocking Issues
that stand. The `worker` field holds the last worker result.

## Reviewer result

A reviewer ends with the ordinary worker result plus `findings`, an array of findings. It
optionally includes `resolved`, an array of `{issue, reason}` naming each earlier Issue the Specs
no longer have and why. The checker ends with the worker result plus `checks`, one
`{finding, status, reason}` per finding it received. Here, `finding` is the finding's position in
the numbered list the checker received, starting at 1. The `status` is `confirmed` or `disputed`.
When they could do their work, both end `ok`. When a worker is `blocked` or `failed`, it still
returns an empty `findings` or `checks` array.

A finding is `{module, path, anchor, line, dimension, severity, tier, title, problem, impact,
evidence, suggestion}`. When it is an earlier Issue's problem, it also has `earlier`, naming that
Issue. The fields have these meanings:

- `module` is the reviewed Module, or the provider whose selected document the finding concerns.
- `path` is a document member in the grant.
- `anchor` and `line` are optional.
- `dimension` is one of the Module quality dimensions `readability`, `obligations`, `design`,
  `views`, `terminology` and `context`.
- `severity` is one of `critical`, `high`, `medium` and `low`.
- `tier` is one of `suggestion`, `obvious-fix`, `preferred-fix` and `decision-needed`.

Whatever its severity, a finding about another Module's document is always a `suggestion`.

## Review payload

The [run result](../../glossary.json#concept.run-result) carries this payload as its `output`:

```concorde-contract
{
  "id": "contract.spec-review.payload",
  "version": 7,
  "schema": {
    "type": "object",
    "required": [
      "verdict",
      "modules",
      "workflow"
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
      "workflow": {
        "type": "object"
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
            "rejected",
            "earlier_issues"
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
                "additionalProperties": false,
                "required": [
                  "module",
                  "path",
                  "dimension",
                  "severity",
                  "tier",
                  "title",
                  "problem",
                  "impact",
                  "evidence",
                  "suggestion",
                  "check",
                  "issue"
                ],
                "properties": {
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
                      "critical",
                      "high",
                      "medium",
                      "low"
                    ]
                  },
                  "tier": {
                    "enum": [
                      "suggestion",
                      "obvious-fix",
                      "preferred-fix",
                      "decision-needed"
                    ]
                  },
                  "title": {
                    "type": "string",
                    "minLength": 1
                  },
                  "problem": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "earlier": {
                    "type": "string",
                    "pattern": "^I-[0-9a-f]{32}$"
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
                  },
                  "issue": {
                    "anyOf": [
                      {
                        "type": "null"
                      },
                      {
                        "type": "string",
                        "pattern": "^I-[0-9a-f]{32}$"
                      }
                    ]
                  }
                }
              }
            },
            "rejected": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "finding",
                  "reason"
                ],
                "properties": {
                  "finding": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "module",
                      "path",
                      "dimension",
                      "severity",
                      "tier",
                      "title",
                      "problem",
                      "impact",
                      "evidence",
                      "suggestion"
                    ],
                    "properties": {
                      "module": {
                        "type": "string",
                        "minLength": 1
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
                          "critical",
                          "high",
                          "medium",
                          "low"
                        ]
                      },
                      "tier": {
                        "enum": [
                          "suggestion",
                          "obvious-fix",
                          "preferred-fix",
                          "decision-needed"
                        ]
                      },
                      "title": {
                        "type": "string",
                        "minLength": 1
                      },
                      "problem": {
                        "type": "string",
                        "minLength": 1
                      },
                      "impact": {
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
                  },
                  "reason": {
                    "type": "string",
                    "minLength": 1
                  }
                }
              }
            },
            "earlier_issues": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "carried",
                    "resolved",
                    "ignored"
                  ],
                  "properties": {
                    "carried": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "issue",
                          "severity",
                          "tier",
                          "title"
                        ],
                        "properties": {
                          "issue": {
                            "type": "string",
                            "pattern": "^I-[0-9a-f]{32}$"
                          },
                          "severity": {
                            "anyOf": [
                              {
                                "enum": [
                                  "critical",
                                  "high",
                                  "medium",
                                  "low"
                                ]
                              },
                              {
                                "type": "null"
                              }
                            ]
                          },
                          "tier": {
                            "anyOf": [
                              {
                                "enum": [
                                  "suggestion",
                                  "obvious-fix",
                                  "preferred-fix",
                                  "decision-needed"
                                ]
                              },
                              {
                                "type": "null"
                              }
                            ]
                          },
                          "title": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    },
                    "resolved": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "issue",
                          "reason"
                        ],
                        "properties": {
                          "issue": {
                            "type": "string",
                            "pattern": "^I-[0-9a-f]{32}$"
                          },
                          "reason": {
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
                          "issue",
                          "reason"
                        ],
                        "properties": {
                          "issue": {
                            "type": "string",
                            "minLength": 1
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
  "semantics": "The outcome of one Spec review. Each Module's outcome is incomplete when it could not be reviewed or its Issues could not be read or all written, changes_required when an Issue of a blocking tier (obvious-fix, preferred-fix, decision-needed) stands for it, reported by this review or an earlier Issue it carried, and accepted otherwise; the verdict is incomplete if any Module is incomplete, else changes_required if any Module requires changes, else accepted. Findings, severities, tiers and checker statuses are worker claims; check is null when no checker ran. context_identity is null only when no grant could be computed. Each finding's issue is the Issue the Operation reported it to, and null when the checker disputed it or it was not reported because the Issue store refused an earlier report; earlier, present only when the Operation appended the finding to an earlier Issue it offered, names that Issue. rejected lists the reviewer's findings whose path is not one of the workspace, each as the reviewer returned it but for the earlier Issue it named, with the Operation's reason: they are reported nowhere, count for no outcome and leave the earlier Issue they named carried, while the reviewer's other findings stand. earlier_issues is null when the Module's earlier Issues were never read; otherwise carried lists the earlier Issues no finding named and no resolution resolved, which still stand, with their severity, tier and title; resolved lists the earlier Issues the reviewer found the Specs no longer have, with its reason, for the task to close, since the Operation closes none; ignored lists the names of Issues a finding or resolution gave that were not offered or already settled, with why. workflow is the object of Workflows' step output convention, which defines its fields: one review note whose data holds the verdict and each Module's outcome with its count of blocking findings that stand. A behaviour or field change increments the version.",
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
            "severity": "medium",
            "tier": "obvious-fix",
            "title": "A requirement joins two obligations",
            "problem": "The requirement states two obligations in one sentence.",
            "impact": "A test cannot tell which obligation a failure breaks.",
            "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
            "suggestion": "Split the notification into its own requirement.",
            "check": {
              "status": "confirmed",
              "reason": "Both obligations are independently testable."
            },
            "issue": "I-0123456789abcdef0123456789abcdef"
          }
        ],
        "rejected": [],
        "earlier_issues": {
          "carried": [],
          "resolved": [
            {
              "issue": "I-fedcba9876543210fedcba9876543210",
              "reason": "Usage now defines the retry limit before using it."
            }
          ],
          "ignored": []
        }
      }
    ],
    "workflow": {
      "decision_points": [],
      "decisions": [],
      "deviations": [],
      "notes": [
        {
          "kind": "review",
          "text": "spec_review verdict changes_required: module.checkout changes_required",
          "data": {
            "verdict": "changes_required",
            "modules": [
              {
                "module": "module.checkout",
                "outcome": "changes_required",
                "blocking": 1
              }
            ]
          }
        }
      ],
      "blocking": null,
      "data": {}
    }
  }
}
```

The Operation adds the run result's own evidence. Each item names the Module and worker it
concerns. The evidence includes:

- The grant and context identity of every worker.
- The `worker-model` item naming each worker's worker id, backend, model and level
  ([worker settings](../workers.md#worker-backend-and-model)).
- The audits.
- The transcript paths.
- The structural findings of step 1 (kind `structural`).
- The scope corrections of step 7 (kind `finding-scope`).
- Every rejected finding (kind `invalid-output`).
- Every Issue it reported to (kind `issue`).

For an Issue, the evidence item gives:

- The Issue.
- Whether the report created or appended to it.
- Its receipt's report identity.

The worker run identities are in the result's `worker_runs`, reviewer before checker, in Module
order.
