# Spec debate Operation

The exact host sequence, debate graph, stance rules, arguments and result of the `spec_debate`
Operation of [Spec review](module.md).

## Invocation

```text
concorde run spec_debate [--task <task-id>] --modules <id>[,<id>...] [--rounds <1-5>]
```

`--modules` names one or more registered Modules of the task worktree. `--rounds` is the most
challenge turns a Module's debate may take, 2 by default. Without `--task` the debate runs [without
a task](../../operations/module.md#concept.operations.no-task) on the primary worktree and judges
the Specs as merged there. The `reviewer` and the `challenger` are the Operation's two worker
roles, so the worker model configuration may give each its own model. The Operation needs no user
consent.

The Operation runs its debate as a LangGraph graph, a library Concorde's runtime does not otherwise
need. The host imports it only when a debate starts; a host whose Python cannot import it fails the
run with `langgraph_unavailable` before any worker is launched, naming the development
environment's interpreter that can. This is the pilot's limit, not a promise: an installed project
has no such interpreter yet.

## Host sequence

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the task worktree's Specs and validate every named Module, as step 1 of [Spec review](operation.md#host-sequence) | host (Spec core) | as there: a loading error fails the run, a structural error makes the Module `incomplete` |
| 2 | For each Module that passed, run the debate graph below; each turn launches one worker under the Module's `review-spec` grant with the debate brief, one round and no resume, and audits that nothing changed | host (Workers) | a turn that ends `blocked`, `failed`, times out, returns an invalid result or changes a file stops that Module's debate: the Module is `incomplete` |
| 3 | Derive every Module's outcome and the verdict from the settled items | host | none |

Modules are debated one after another. A debate writes nothing: no Spec, and unlike `spec_review`
no review memory.

## The debate graph

```d2 illustrative
direction: down
propose: "propose\n(reviewer)"
challenge: "challenge\n(challenger)"
respond: "respond\n(reviewer)"
settle: "settle\n(host)"
propose -> challenge
challenge -> respond: an item awaits the reviewer
challenge -> settle: nothing awaits the reviewer
respond -> challenge: "an item awaits the challenger\nand challenge turns remain"
respond -> settle: otherwise
```

- **propose**: the reviewer's first turn reviews the Module and returns findings; each becomes an
  item proposed by the reviewer.
- **challenge**: the challenger answers every item awaiting it. On its first turn it also returns
  the findings the reviewer missed, which become items it proposed; a later challenge turn returns
  none.
- **respond**: the reviewer answers every item awaiting it, including the challenger's.
- **settle**: every item still open becomes `contested`.

A turn that stops, as step 2 describes, ends the graph at once and leaves the items as they are.

An item **awaits** a debater when it is open and the other debater set its current position. The
graph's state is the list of items, the number of turns taken, the number of challenge turns, the
Module's context identity, the host evidence gathered so far and the Module's stop, all plain JSON
values. The graph runs within a step limit of twice `--rounds` plus four, which the edges above
never reach.

## Stances

Every item holds its current position, which debater set it, and each debater's own last position.
A position is a finding or "does not hold". A response names an item and takes one stance:

| Stance | Effect on the item |
| --- | --- |
| `agree` | The item settles on the current position: `agreed` when it is a finding, `withdrawn` when it is "does not hold". |
| `amend` | The response's finding becomes the responder's position and the current one; the item then awaits the other debater. An amendment equal to the current finding settles the item as `agreed`. |
| `object` | The responder's own last position becomes the current one again, or "does not hold" when it has none yet; the item then awaits the other debater. When that is already the current position, the item settles as `agree` would. |

The host applies the stances and judges none. A response for an item that is not awaiting the
responder, a second response for the same item and an `amend` without a finding move nothing, and
an awaited item left unanswered stays open; each is host evidence of kind `debate-response`. Every
finding a debater proposes, amends or adds is normalized as [Spec
review](operation.md#host-sequence) normalizes findings: paths relative to the task worktree,
`module` set to the owner of the cited document, and a blocking finding outside the debated
Module's own documents re-filed as advisory with `finding-scope` evidence. A finding whose path is
not in the task worktree stops the Module's debate with `unusable_finding`.

## Result status

| Verdict | Status | Error |
| --- | --- | --- |
| `accepted`, `undecided` or `changes_required` | `ok` | none |
| `incomplete`, and some incomplete Module failed | `failed` | `debate_incomplete`, one cause per incomplete Module |
| `incomplete` otherwise | `blocked` | `debate_incomplete`, one cause per incomplete Module |

A loading error in step 1 is `failed` with no output. In every other case the result's `output` is
the debate payload, including the items of a Module whose debate stopped. The error of an
incomplete Module is the Operation's link for it; for a stopped turn its actor names the Module and
the turn, and below it are Workers' link and the worker's own. The summary counts the agreed
blocking findings, the contested items and the withdrawn ones. The host evidence adds, besides the
evidence of Spec review's steps, the debate graph as Mermaid text (kind `graph`), written once per
run in the run directory.

## Debate payload

```concorde-contract
{
  "id": "contract.spec-review.debate-payload",
  "version": 1,
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
          "undecided",
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
            "turns",
            "items"
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
                "undecided",
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
            "turns": {
              "type": "integer",
              "minimum": 0
            },
            "items": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "id",
                  "proposer",
                  "state",
                  "finding",
                  "positions",
                  "history"
                ],
                "properties": {
                  "id": {
                    "type": "string",
                    "pattern": "^d\\.[1-9][0-9]*$"
                  },
                  "proposer": {
                    "enum": [
                      "reviewer",
                      "challenger"
                    ]
                  },
                  "state": {
                    "enum": [
                      "agreed",
                      "withdrawn",
                      "contested",
                      "open"
                    ]
                  },
                  "finding": {
                    "anyOf": [
                      {
                        "type": "null"
                      },
                      {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "module",
                          "path",
                          "dimension",
                          "severity",
                          "problem",
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
                          }
                        }
                      }
                    ]
                  },
                  "positions": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "reviewer": {
                        "anyOf": [
                          {
                            "type": "null"
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "module",
                              "path",
                              "dimension",
                              "severity",
                              "problem",
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
                              }
                            }
                          }
                        ]
                      },
                      "challenger": {
                        "anyOf": [
                          {
                            "type": "null"
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "module",
                              "path",
                              "dimension",
                              "severity",
                              "problem",
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
                              }
                            }
                          }
                        ]
                      }
                    }
                  },
                  "history": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "turn",
                        "role",
                        "stance"
                      ],
                      "properties": {
                        "turn": {
                          "type": "integer",
                          "minimum": 1
                        },
                        "role": {
                          "enum": [
                            "reviewer",
                            "challenger"
                          ]
                        },
                        "stance": {
                          "enum": [
                            "propose",
                            "agree",
                            "amend",
                            "object"
                          ]
                        },
                        "reason": {
                          "type": "string",
                          "minLength": 1
                        },
                        "finding": {
                          "type": "object",
                          "additionalProperties": false,
                          "required": [
                            "module",
                            "path",
                            "dimension",
                            "severity",
                            "problem",
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
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "semantics": "The outcome of one Spec debate. Each item is a finding one debater proposed and the stances both took on it, in turn order. state is agreed when one side accepted the other's current finding, withdrawn when one side accepted that the finding does not hold, contested when the debate ended with the two sides' positions different, and open only when the Module's debate stopped before it could settle. finding is the agreed finding and null otherwise; positions holds each debater's last position, a finding or null for 'does not hold', and leaves out a debater that never took one. A Module's outcome is incomplete when its debate stopped, changes_required when an agreed finding is blocking, undecided when a contested item has a blocking position on either side, and accepted otherwise; the verdict is the highest outcome in the order accepted, undecided, changes_required, incomplete. turns counts the worker turns the Module's debate ran. Findings, stances and reasons are worker claims; the host only records them and derives states and outcomes. A behaviour or field change increments the version.",
  "example": {
    "verdict": "changes_required",
    "modules": [
      {
        "module": "module.checkout",
        "outcome": "changes_required",
        "context_identity": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "turns": 3,
        "items": [
          {
            "id": "d.1",
            "proposer": "reviewer",
            "state": "agreed",
            "finding": {
              "module": "module.checkout",
              "path": "specs/checkout/requirements.md",
              "anchor": "req.checkout.single-order",
              "dimension": "obligations",
              "severity": "blocking",
              "problem": "The requirement states two obligations in one sentence.",
              "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
              "suggestion": "Split the notification into its own requirement."
            },
            "positions": {
              "reviewer": {
                "module": "module.checkout",
                "path": "specs/checkout/requirements.md",
                "anchor": "req.checkout.single-order",
                "dimension": "obligations",
                "severity": "blocking",
                "problem": "The requirement states two obligations in one sentence.",
                "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
                "suggestion": "Split the notification into its own requirement."
              }
            },
            "history": [
              {
                "turn": 1,
                "role": "reviewer",
                "stance": "propose"
              },
              {
                "turn": 2,
                "role": "challenger",
                "stance": "agree",
                "reason": "Both obligations are independently testable."
              }
            ]
          },
          {
            "id": "d.2",
            "proposer": "challenger",
            "state": "contested",
            "finding": null,
            "positions": {
              "challenger": {
                "module": "module.checkout",
                "path": "specs/checkout/module.md",
                "anchor": "usage",
                "dimension": "readability",
                "severity": "blocking",
                "problem": "Usage never shows what happens when payment is declined.",
                "evidence": "Checkout creates the order once payment succeeds.",
                "suggestion": "Add the declined-payment path after the normal path."
              },
              "reviewer": null
            },
            "history": [
              {
                "turn": 2,
                "role": "challenger",
                "stance": "propose"
              },
              {
                "turn": 3,
                "role": "reviewer",
                "stance": "object",
                "reason": "The declined path is scenario.checkout.declined, which Usage links."
              }
            ]
          }
        ]
      }
    ]
  }
}
```
