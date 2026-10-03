# Spec panel Operation

The exact step sequence, panel graph, accounting rule, arguments and result of the `spec_panel`
Operation of [Spec review](module.md).

## Invocation

```text
concorde run spec_panel [--modules <id>[,<id>...]] [--reviewers <2-5>] [--architects <0-2>]
```

The panel works on the worktree it starts in, as [Spec review](operation.md#invocation) does: the
bound [workspace](../../glossary.json#concept.workspace), whose Modules `--modules` defaults to, or,
without a binding, an [unbound run](../../glossary.json#concept.unbound-run) that judges the Specs
as merged there. `--modules` names one or more registered Modules of that worktree. `--reviewers` is
the number of reviewers on each [Module](../../glossary.json#concept.module)'s panel, 3 by default,
and `--architects` the number of architects, 2 by default. Each reviewer is the worker
`reviewer<seat>`, `reviewer1` to `reviewer5`, each architect the worker `architect<seat>`,
`architect1` or `architect2`, and the chair the worker `chair`; by these
[worker ids](../../glossary.json#concept.worker-id) the
[worker configuration](../../glossary.json#concept.worker-configuration) gives each
worker its own backend, model and thinking level, and workers on different models make their
reviews more independent still. The [Operation](../../glossary.json#concept.operation) takes no
other argument and needs no user consent.

The panel runs as a LangGraph graph, one of Concorde's Python dependencies. An Execution runner
whose interpreter cannot import it, such as an install made with `--without-dependencies`, fails the
run with `langgraph_unavailable` before any worker is launched.

## Host sequence

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the workspace's Specs and validate every named Module, as step 1 of [Spec review](operation.md#host-sequence) | Operation (Spec core) | as there: a loading error fails the run, a structural error makes the Module `incomplete` |
| 2 | For each Module that passed, read its [earlier Issues](operation.md#earlier-issues) as step 3 of Spec review does | Operation (Issues) | as there: the Module is `incomplete` (`issues_unreadable`) |
| 3 | For each Module whose earlier Issues were read, run the panel graph below. Every reviewer runs under the Module's `review-spec` grant, every architect under its `review-architecture` grant, and the chair under the `review-architecture` grant when the panel has an architect and the `review-spec` grant otherwise; each worker receives the Panel brief and the earlier Issues, is resumed once only when a finding's path is not one of the workspace, with those paths to correct, and is followed by an audit that nothing changed | Operation (Workers) | a worker that ends `blocked` or `failed`, times out, returns an invalid result, changes a file stops that Module's panel, and so does a chair report still unaccounted after its last attempt: the Module is `incomplete` |
| 4 | For each Module whose panel completed, settle the earlier Issues the chair's findings name and resolve, as step 7 of Spec review does, and report every finding of the chair's report as an [Issue](../../glossary.json#concept.issue), as step 8 of Spec review does, in the order of the report | Operation (Issues) | as there: the Module is `incomplete` (`issues_unreported`) |
| 5 | Derive every Module's outcome and the verdict from the Issues that stand | Operation | none |

Modules are paneled one after another; the reviewers and architects of one Module run at the same
time. A panel changes no file of the workspace: its only writes are its [Issue reports](../../glossary.json#concept.issue-report), which the
primary worktree keeps. A Module whose panel stopped reports no Issue and keeps the reviews it had
and its **stop**: the status, summary and error link that stopped it.

Where the issues part is not installed, steps 2 and 4 read and report no Issues, exactly as
[Spec review does without them](operation.md#without-the-issues-part): every merged finding keeps
`issue` null, `earlier_issues` is null, step 5 derives each outcome from the blocking findings of the
chair's report, and the result says that the findings were not recorded as Issues. The run's output
carries the same `review` note under the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output) as a Spec
review's.

## The panel graph

```d2 illustrative
direction: right
review: "review\n(reviewer 1 … N and architect 1 … M,\nin parallel)"
gather: "gather\n(Operation)"
chair: "chair\n(chair worker, then the Operation's accounting)"
review -> gather
gather -> chair: every worker finished
chair -> chair: "a label unaccounted\nand an attempt remains"
```

- **review** runs once per seat, all seats at the same time: reviewer `n` reviews the Module on its
  own, by the Module quality criteria, and architect `n` judges it on its own, by the architecture
  quality criteria, each seeing no other review. The Operation normalizes their findings as [Spec
  review](operation.md#host-sequence) does and labels a reviewer's `r<n>.1`, `r<n>.2` and so on and
  an architect's `a<n>.1`, `a<n>.2` and so on. A finding whose path is not one of the workspace is
  rejected alone, unlabelled, and kept with the reason among that worker's `rejected`. It keeps
  each worker's resolutions as its claims.
- **gather** waits for every seat. When any worker did not finish, it stops the Module with
  `panel_short`, whose causes are every such worker's error link; the chair does not run, because
  a report must never silently lack a review.
- **chair** receives every labelled finding and every claimed resolution, grouped by worker, with
  the earlier Issues, and returns the report: merged findings, each with the labels it merges as
  `sources`, a `note` and the severity and tier the chair gives it, rejections, each with a label and a reason,
  and the earlier Issues it finds resolved, each with a reason. The Operation normalizes the merged
  findings as well; a merged finding whose path is not one of the workspace is reported nowhere,
  and each of its labels becomes a rejection with the Operation's reason.
- **accounting**, part of the chair node, is the Operation's check that the report accounts for
  every label exactly once: in one finding's `sources` or as one rejection, and names no other
  label. The result is host evidence of kind `panel-accounting`.

Control moves by these rules:

1. The reviewers and architects start together; `gather` runs once all of them have ended.
2. After `gather`, the chair runs when every worker finished; otherwise the graph ends.
3. After the chair, the graph ends when its turn stopped or its report is complete. When a label is
   unaccounted for, named twice or unknown, the chair runs once more, with its previous report and
   every accounting problem; after that second attempt a report still incomplete stops the Module
   with `report_unaccounted`, whose detail names every problem.

A Module's panel therefore takes `--reviewers` reviewer runs, `--architects` architect runs and,
when every one of them finished, one or two chair runs. The graph's
state is the reviews, the host evidence, the Module's
[context identities](../../glossary.json#concept.context-identity) for the two [task types](../../glossary.json#concept.task-type), the
chair's latest report, its accounting problems, the chair attempts and the Module's stop, all plain
JSON values; the reviews and the evidence are appended to by the parallel workers in whatever order
they end, and the Operation sorts the reviews by role and seat.

## Panel result

Every worker ends with the ordinary [worker result](../../glossary.json#concept.worker-result),
whose `output` depends on its role:

| Role | `output` |
| --- | --- |
| `reviewer` | `{"findings": [...], "resolved": [...]}` |
| `architect` | `{"findings": [...], "resolved": [...]}` |
| `chair` | `{"findings": [...], "rejected": [...], "resolved": [...]}` |

A reviewer finding has the shape of a Spec review [reviewer finding](operation.md#reviewer-result).
An architect finding has the same shape, except that its `dimension` is one of the architecture
quality dimensions `responsibilities`, `ownership`, `interfaces`, `dependencies`,
`failure-containment` and `consistency`, or `context`, and that it may add `related`, the other
registered Modules the problem concerns. A chair finding has either shape and adds `sources`, a
non-empty list of labels, and `note`, what the chair verified and why it chose the severity and tier. A
rejection is `{source, reason}` and a resolution `{issue, reason}`, both optional lists but for
`findings`. A result that does not match its role's shape is an **invalid result** and stops the
Module; a report that matches but accounts badly goes back to the chair as rule 3 says.

The chair may change a merged finding's wording, evidence, suggestion, severity and tier, and names the
earlier Issue it is when any of its sources named one. It may not add a problem that no reviewer or
architect reported: every report finding has sources. Each worker's findings stay in the payload as
the Operation normalized them, so the chair's changes can be compared with them.

## Result status

| Verdict | Status | Error |
| --- | --- | --- |
| `accepted` or `changes_required` | `ok` | none |
| `incomplete`, and some incomplete Module failed: a worker that failed, a launch error, a timeout, an invalid result, an audit violation, a finding path outside the workspace, an unaccounted report, Issues that could not be read or written, an unknown Module or a grant that could not be computed | `failed` | `panel_incomplete`, one cause per incomplete Module |
| `incomplete` otherwise: a structural error or a `blocked` reviewer, architect or chair | `blocked` | `panel_incomplete`, one cause per incomplete Module |

A loading error in step 1 and `langgraph_unavailable` are `failed` with no output. In every other
case the result's `output` is the panel payload, including the reviews of a Module whose panel
stopped. The error of an incomplete Module is the Operation's link for it: `panel_short` over the
links of the workers that did not finish, each naming its worker id, `report_unaccounted`,
`issues_unreadable` or `issues_unreported` over the Issue store's error, or the link of a chair turn
that stopped; below a worker's link are Workers' link and the worker's own. The summary counts the
report's findings of a blocking tier and suggestions, the worker findings they were merged from,
the rejections and the blocking Issues that stand. The host evidence adds, besides the evidence of
Spec review's steps and the accounting, the panel graph as Mermaid text (kind `graph`), written once
per run in the [run directory](../../glossary.json#concept.run-directory).

## Panel payload

```concorde-contract
{
  "id": "contract.spec-review.panel-payload",
  "version": 6,
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
            "architecture_identity",
            "reviews",
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
            "architecture_identity": {
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
            "reviews": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "worker",
                  "role",
                  "seat",
                  "status",
                  "findings",
                  "rejected",
                  "resolved"
                ],
                "properties": {
                  "worker": {
                    "enum": [
                      "reviewer1",
                      "reviewer2",
                      "reviewer3",
                      "reviewer4",
                      "reviewer5",
                      "architect1",
                      "architect2"
                    ]
                  },
                  "role": {
                    "enum": [
                      "reviewer",
                      "architect"
                    ]
                  },
                  "seat": {
                    "type": "integer",
                    "minimum": 1
                  },
                  "status": {
                    "enum": [
                      "ok",
                      "blocked",
                      "failed"
                    ]
                  },
                  "findings": {
                    "type": "array",
                    "items": {
                      "$ref": "#/$defs/labelled"
                    }
                  },
                  "rejected": {
                    "type": "array",
                    "items": {
                      "$ref": "#/$defs/unusable"
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
            },
            "findings": {
              "type": "array",
              "items": {
                "$ref": "#/$defs/reported"
              }
            },
            "rejected": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "source",
                  "reason"
                ],
                "properties": {
                  "source": {
                    "type": "string",
                    "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
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
    },
    "$defs": {
      "labelled": {
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
          "label"
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
              "context",
              "responsibilities",
              "ownership",
              "interfaces",
              "dependencies",
              "failure-containment",
              "consistency"
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
            "minLength": 1
          },
          "related": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "label": {
            "type": "string",
            "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
          }
        }
      },
      "reported": {
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
          "sources",
          "note",
          "workers",
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
              "context",
              "responsibilities",
              "ownership",
              "interfaces",
              "dependencies",
              "failure-containment",
              "consistency"
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
          "related": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "sources": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
            }
          },
          "note": {
            "type": "string",
            "minLength": 1
          },
          "workers": {
            "type": "integer",
            "minimum": 1
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
      },
      "unusable": {
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
                  "context",
                  "responsibilities",
                  "ownership",
                  "interfaces",
                  "dependencies",
                  "failure-containment",
                  "consistency"
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
              "related": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              }
            }
          },
          "reason": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "The outcome of one Spec panel. For each Module, reviews holds every worker's own findings and claimed resolutions, reviewers then architects, each in seat order, with its worker id, role and seat, each finding labelled r<seat>.<n> for a reviewer and a<seat>.<n> for an architect by the Operation; a worker that did not finish has its status and whatever it returned before stopping, usually nothing; rejected holds a worker's findings whose path is not one of the workspace, unlabelled, each as returned but for the earlier Issue it named, with the Operation's reason. findings is the chair's report: each merged finding lists in sources the labels it merges, with the chair's note, severity and tier, workers counts the distinct workers among those labels, issue is the Issue the Operation reported it to, null when the Issue store refused an earlier report, and earlier, present only when it was appended to an earlier Issue the Operation offered, names that Issue. rejected holds the labels the chair judged not to hold, each with its reason, and the labels of a merged finding whose path is not one of the workspace, with the Operation's reason, all reported nowhere. In a complete report every label appears exactly once, in one finding's sources or as one rejection. earlier_issues, null when the Module's earlier Issues were never read, lists the earlier Issues carried, those the chair found resolved, for the task to close, and the names ignored, as in the Spec review payload. context_identity is the Module's review-spec grant identity and architecture_identity its review-architecture grant identity, null when no architect ran or no grant could be computed. A Module's outcome is incomplete when its panel stopped or its Issues could not be read or all written, changes_required when an Issue of a blocking tier stands for it, reported now or carried, and accepted otherwise; the verdict is the highest outcome in the order accepted, changes_required, incomplete. Findings, severities, tiers, merges, notes, rejections and resolutions are worker claims; the Operation labels, normalizes, counts, checks the accounting and reports the Issues. workflow is the object of Workflows' step output convention, which defines its fields: one review note whose data holds the verdict and each Module's outcome with its count of blocking findings that stand. A behaviour or field change increments the version.",
  "example": {
    "verdict": "changes_required",
    "modules": [
      {
        "module": "module.checkout",
        "outcome": "changes_required",
        "context_identity": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "architecture_identity": "sha256:1f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "reviews": [
          {
            "worker": "reviewer1",
            "role": "reviewer",
            "seat": 1,
            "status": "ok",
            "findings": [
              {
                "module": "module.checkout",
                "path": "specs/checkout/requirements.md",
                "anchor": "req.checkout.single-order",
                "dimension": "obligations",
                "severity": "medium",
                "tier": "obvious-fix",
                "title": "A requirement joins two obligations",
                "problem": "The requirement states two obligations.",
                "impact": "A test cannot tell which obligation a failure breaks.",
                "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
                "suggestion": "Split the notification into its own requirement.",
                "label": "r1.1"
              }
            ],
            "rejected": [],
            "resolved": []
          },
          {
            "worker": "architect1",
            "role": "architect",
            "seat": 1,
            "status": "ok",
            "findings": [
              {
                "module": "module.checkout",
                "path": "specs/checkout/module.md",
                "anchor": "uses-inventory",
                "dimension": "interfaces",
                "severity": "high",
                "tier": "decision-needed",
                "title": "Checkout relies on Inventory's internal reservation table",
                "problem": "Checkout reads Inventory's reservation rows instead of a promise of Inventory.",
                "impact": "A change of Inventory's storage silently breaks Checkout.",
                "evidence": "Checkout reads the reservations table to confirm stock.",
                "suggestion": "Rely on an Inventory promise to confirm a reservation.",
                "related": [
                  "module.inventory"
                ],
                "label": "a1.1"
              }
            ],
            "rejected": [],
            "resolved": []
          }
        ],
        "findings": [
          {
            "module": "module.checkout",
            "path": "specs/checkout/module.md",
            "anchor": "uses-inventory",
            "dimension": "interfaces",
            "severity": "high",
            "tier": "decision-needed",
            "title": "Checkout relies on Inventory's internal reservation table",
            "problem": "Checkout reads Inventory's reservation rows instead of a promise of Inventory.",
            "impact": "A change of Inventory's storage silently breaks Checkout.",
            "evidence": "Checkout reads the reservations table to confirm stock.",
            "suggestion": "Rely on an Inventory promise to confirm a reservation.",
            "related": [
              "module.inventory"
            ],
            "sources": [
              "a1.1"
            ],
            "note": "Inventory's Spec promises no reservation query; which promise to add is a design choice.",
            "workers": 1,
            "issue": "I-0123456789abcdef0123456789abcdef"
          }
        ],
        "rejected": [
          {
            "source": "r1.1",
            "reason": "The requirement was split in the current Specs; the quoted sentence is not there."
          }
        ],
        "earlier_issues": {
          "carried": [],
          "resolved": [],
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
          "text": "spec_panel verdict changes_required: module.checkout changes_required",
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
