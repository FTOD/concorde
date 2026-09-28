# Spec panel Operation

The exact step sequence, panel graph, accounting rule, arguments and result of the `spec_panel`
Operation of [Spec review](module.md).

## Invocation

```text
concorde run spec_panel [--modules <id>[,<id>...]] [--reviewers <2-5>]
```

The panel works on the worktree it starts in, as [Spec review](operation.md#invocation) does: the
bound [workspace](../../glossary.json#concept.workspace), whose Modules `--modules` defaults to, or,
without a binding, an [unbound run](../../glossary.json#concept.unbound-run) that judges the Specs
as merged there. `--modules` names one or more registered Modules of that worktree. `--reviewers` is
the number of reviewers on each [Module](../../glossary.json#concept.module)'s panel, 3 by default.
Each reviewer is the worker `reviewer<seat>`, `reviewer1` to `reviewer5`, and the chair the worker
`chair`; by these [worker ids](../../glossary.json#concept.worker-id) the
[worker model configuration](../../glossary.json#concept.worker-model-configuration) gives each
reviewer and the chair its own backend, model and thinking level, and three reviewers on three
different models make their reviews more independent still. The
[Operation](../../glossary.json#concept.operation) takes no other argument and needs no user
consent.

The panel runs as a LangGraph graph, one of Concorde's Python dependencies. An Execution runner
whose interpreter cannot import it, such as an install made with `--without-dependencies`, fails the
run with `langgraph_unavailable` before any worker is launched.

## Host sequence

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the workspace's Specs and validate every named Module, as step 1 of [Spec review](operation.md#host-sequence) | Operation (Spec core) | as there: a loading error fails the run, a structural error makes the Module `incomplete` |
| 2 | For each Module that passed, run the panel graph below; every worker runs under the Module's `review-spec` grant with the Panel brief, is waited for without being resumed, and is followed by an audit that nothing changed | Operation (Workers) | a worker that ends `blocked` or `failed`, times out, returns an invalid result, changes a file or names a finding path outside the workspace stops that Module's panel, and so does a chair report still unaccounted after its last attempt: the Module is `incomplete` |
| 3 | Derive every Module's outcome and the verdict from its report | Operation | none |

Modules are paneled one after another; the reviewers of one Module run at the same time. A panel
writes nothing: no [Spec](../../glossary.json#concept.spec), and unlike `spec_review` no
[review memory](../../glossary.json#concept.review-memory). A Module whose panel stopped keeps the
reviews it had and its **stop**: the status, summary and error link that stopped it.

## The panel graph

```d2 illustrative
direction: right
reviewers: "reviewer 1 … reviewer N\n(in parallel)"
gather: "gather\n(Operation)"
chair: "chair"
account: "accounting\n(Operation)"
reviewers -> gather
gather -> chair: every reviewer finished
chair -> account
account -> chair: "a label unaccounted\nand an attempt remains"
```

- **review** runs once per seat, all seats at the same time: reviewer `n` reviews the Module on its
  own, seeing no other review. The Operation normalizes its findings as [Spec
  review](operation.md#host-sequence) does and labels them `r<n>.1`, `r<n>.2` and so on.
- **gather** waits for every seat. When any reviewer did not finish, it stops the Module with
  `panel_short`, whose causes are every such reviewer's error link; the chair does not run, because
  a report must never silently lack a reviewer.
- **chair** receives every labelled finding, grouped by reviewer, and returns the report: merged
  findings, each with the labels it merges as `sources` and a `note`, and rejections, each with a
  label and a reason. The Operation normalizes the merged findings as well.
- **accounting**, part of the chair node, is the Operation's check that the report accounts for
  every label exactly once: in one finding's `sources` or as one rejection, and names no other
  label. The result is host evidence of kind `panel-accounting`.

Control moves by these rules:

1. The reviewers start together; `gather` runs once all of them have ended.
2. After `gather`, the chair runs when every reviewer finished; otherwise the graph ends.
3. After the chair, the graph ends when its turn stopped or its report is complete. When a label is
   unaccounted for, named twice or unknown, the chair runs once more, with its previous report and
   every accounting problem; after that second attempt a report still incomplete stops the Module
   with `report_unaccounted`, whose detail names every problem.

A Module's panel therefore takes `--reviewers` reviewer runs and one or two chair runs. The graph's
state is the reviews, the host evidence, the Module's
[context identity](../../glossary.json#concept.context-identity), the chair's latest report, its
accounting problems, the chair attempts and the Module's stop, all plain JSON values; the reviews
and the evidence are appended to by the parallel reviewers in whatever order they end, and the
Operation sorts the reviews by seat.

## Panel result

Every worker ends with the ordinary [worker result](../../glossary.json#concept.worker-result),
whose `output` depends on its role:

| Role | `output` |
| --- | --- |
| `reviewer` | `{"findings": [...]}` |
| `chair` | `{"findings": [...], "rejected": [...]}` |

A reviewer finding has the shape of a Spec review [reviewer finding](operation.md#reviewer-result)
without `earlier`. A chair finding adds `sources`, a non-empty list of labels, and `note`, what the
chair verified and why it chose the severity. A rejection is `{source, reason}`. A result that does
not match its role's shape is an **invalid result** and stops the Module; a report that matches but
accounts badly goes back to the chair as rule 3 says.

The chair may change a merged finding's wording, evidence, suggestion and severity. It may not add a
problem that no reviewer reported: every report finding has sources. Each reviewer's findings stay
in the payload as the Operation normalized them, so the chair's changes can be compared with them.

## Result status

| Verdict | Status | Error |
| --- | --- | --- |
| `accepted` or `changes_required` | `ok` | none |
| `incomplete`, and some incomplete Module failed: a worker that failed, a launch error, a timeout, an invalid result, an audit violation, a finding path outside the workspace, an unaccounted report, an unknown Module or a grant that could not be computed | `failed` | `panel_incomplete`, one cause per incomplete Module |
| `incomplete` otherwise: a structural error or a `blocked` reviewer or chair | `blocked` | `panel_incomplete`, one cause per incomplete Module |

A loading error in step 1 and `langgraph_unavailable` are `failed` with no output. In every other
case the result's `output` is the panel payload, including the reviews of a Module whose panel
stopped. The error of an incomplete Module is the Operation's link for it: `panel_short` over the
links of the reviewers that did not finish, each naming its seat, `report_unaccounted`, or the link
of a chair turn that stopped; below a worker's link are Workers' link and the worker's own. The
summary counts the report's blocking and advisory findings, the reviewer findings they were merged
from, and the rejections. The host evidence adds, besides the evidence of Spec review's steps and
the accounting, the panel graph as Mermaid text (kind `graph`), written once per run in the run
directory.

## Panel payload

```concorde-contract
{
  "id": "contract.spec-review.panel-payload",
  "version": 2,
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
            "reviews",
            "findings",
            "rejected"
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
            "reviews": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "reviewer",
                  "worker",
                  "status",
                  "findings"
                ],
                "properties": {
                  "reviewer": {
                    "type": "integer",
                    "minimum": 1
                  },
                  "worker": {
                    "enum": [
                      "reviewer1",
                      "reviewer2",
                      "reviewer3",
                      "reviewer4",
                      "reviewer5"
                    ]
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
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "module",
                        "path",
                        "dimension",
                        "severity",
                        "problem",
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
                        "label": {
                          "type": "string",
                          "pattern": "^r[1-9][0-9]*\\.[1-9][0-9]*$"
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
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "module",
                  "path",
                  "dimension",
                  "severity",
                  "problem",
                  "evidence",
                  "suggestion",
                  "sources",
                  "note",
                  "reviewers"
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
                  "sources": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "string",
                      "pattern": "^r[1-9][0-9]*\\.[1-9][0-9]*$"
                    }
                  },
                  "note": {
                    "type": "string",
                    "minLength": 1
                  },
                  "reviewers": {
                    "type": "integer",
                    "minimum": 1
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
                  "source",
                  "reason"
                ],
                "properties": {
                  "source": {
                    "type": "string",
                    "pattern": "^r[1-9][0-9]*\\.[1-9][0-9]*$"
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
      }
    }
  },
  "semantics": "The outcome of one Spec panel. For each Module, reviews holds every reviewer's own findings in seat order, each reviewer with its seat and its worker id reviewer<seat>, each labelled r<seat>.<n> by the Operation; a reviewer that did not finish has its status and whatever findings it returned before stopping, usually none. findings is the chair's report: each merged finding lists in sources the labels it merges, with the chair's note, and reviewers counts the distinct reviewers among those labels. rejected holds the labels the chair judged not to hold, each with its reason. In a complete report every label appears exactly once, in one finding's sources or as one rejection. A Module's outcome is incomplete when its panel stopped, changes_required when a report finding is blocking, and accepted otherwise; the verdict is the highest outcome in the order accepted, changes_required, incomplete. Findings, merges, notes and rejections are worker claims; the Operation labels, normalizes, counts and checks the accounting. A behaviour or field change increments the version.",
  "example": {
    "verdict": "changes_required",
    "modules": [
      {
        "module": "module.checkout",
        "outcome": "changes_required",
        "context_identity": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "reviews": [
          {
            "reviewer": 1,
            "status": "ok",
            "findings": [
              {
                "module": "module.checkout",
                "path": "specs/checkout/requirements.md",
                "anchor": "req.checkout.single-order",
                "dimension": "obligations",
                "severity": "blocking",
                "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
                "suggestion": "Split the notification into its own requirement.",
                "problem": "The requirement states two obligations.",
                "label": "r1.1"
              }
            ],
            "worker": "reviewer1"
          },
          {
            "reviewer": 2,
            "status": "ok",
            "findings": [
              {
                "module": "module.checkout",
                "path": "specs/checkout/requirements.md",
                "anchor": "req.checkout.single-order",
                "dimension": "obligations",
                "severity": "blocking",
                "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
                "suggestion": "Split the notification into its own requirement.",
                "problem": "Two duties share one SHALL sentence.",
                "label": "r2.1"
              },
              {
                "module": "module.checkout",
                "path": "specs/checkout/module.md",
                "dimension": "readability",
                "severity": "advisory",
                "problem": "Usage names the retry limit before defining it.",
                "evidence": "Retries stop at the limit.",
                "suggestion": "Define the retry limit first.",
                "label": "r2.2"
              }
            ],
            "worker": "reviewer2"
          }
        ],
        "findings": [
          {
            "module": "module.checkout",
            "path": "specs/checkout/requirements.md",
            "anchor": "req.checkout.single-order",
            "dimension": "obligations",
            "severity": "blocking",
            "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
            "suggestion": "Split the notification into its own requirement.",
            "problem": "The requirement states two obligations in one sentence.",
            "sources": [
              "r1.1",
              "r2.1"
            ],
            "note": "Both quote the same sentence, which has two SHALL clauses.",
            "reviewers": 2
          }
        ],
        "rejected": [
          {
            "source": "r2.2",
            "reason": "Usage defines the retry limit in the sentence before."
          }
        ]
      }
    ]
  }
}
```
