# Worker result contract

The exact answer every worker ends with. The [entry](module.md#concept.workers.worker-result)
explains its role; [the run mechanics](launch.md#rounds) say how the host reacts to it. Its
`error` is the worker's link of the Framework's [error chain](../../contracts.md#contract.concorde.error).

```concorde-contract
{
  "id": "contract.workers.worker-result",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "status",
      "summary",
      "error",
      "proposed_deletions",
      "output"
    ],
    "properties": {
      "status": {
        "enum": [
          "ok",
          "blocked",
          "failed"
        ]
      },
      "summary": {
        "type": "string",
        "minLength": 1
      },
      "error": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "code",
              "detail",
              "evidence",
              "attempts",
              "unhandled",
              "options",
              "recommendation"
            ],
            "properties": {
              "code": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9_]*$"
              },
              "detail": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "kind",
                    "ref",
                    "detail"
                  ],
                  "properties": {
                    "kind": {
                      "enum": [
                        "file",
                        "command",
                        "output",
                        "spec"
                      ]
                    },
                    "ref": {
                      "type": "string",
                      "minLength": 1
                    },
                    "detail": {
                      "type": "string"
                    }
                  }
                }
              },
              "attempts": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              },
              "unhandled": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "reason",
                  "explanation"
                ],
                "properties": {
                  "reason": {
                    "enum": [
                      "permission",
                      "decision",
                      "scope",
                      "capability",
                      "exhausted",
                      "environment",
                      "input"
                    ]
                  },
                  "explanation": {
                    "type": "string",
                    "minLength": 1
                  }
                }
              },
              "options": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              },
              "recommendation": {
                "type": "string"
              }
            }
          }
        ]
      },
      "proposed_deletions": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "output": {
        "type": "object"
      }
    }
  },
  "semantics": "The structured result a worker returns through --json-schema at the end of every round. status ok means the worker finished its task; blocked means it cannot continue without a decision above it, such as a Spec gap or a missing grant, and failed means it tried and could not finish. summary says what was done. error is null exactly when status is ok; for blocked and failed it is the worker's own link of the error chain, the contract.concorde.error link without level, actor and causes: code names the error, detail describes it completely with the exact messages, evidence items point at a file, command, output or Spec (kind) by a path or identity (ref) with a short explanation (detail), attempts lists what was tried, unhandled gives the reason and the specific explanation why the worker could not handle it, and options and recommendation are what it offers. The error is the worker's claim, never host evidence; Workers adds the level worker, the actor and no causes when it puts it in the chain. proposed_deletions lists absolute paths in the task worktree the worker wants deleted; the host deletes only those in the grant's rw list after a clean audit. output is the Operation-specific part of the answer, such as an assessment, a code change summary or review findings; the Operation supplies its schema, which the host embeds at this key in the schema it passes to --json-schema, and it is an empty object for Operations without one. A result whose error does not match its status is invalid. The host keeps the result verbatim in the run record.",
  "example": {
    "status": "blocked",
    "summary": "Added discount rules to the cart; the rounding rule is not specified.",
    "error": {
      "code": "spec_gap",
      "detail": "req.shop.discount-total in specs/shop/requirements.md states the discounted total but not whether discounts are rounded per line or per order; src/shop/discounts.py needs one of the two to compute invoice lines.",
      "evidence": [
        {
          "kind": "spec",
          "ref": "req.shop.discount-total",
          "detail": "states the total but not the rounding"
        }
      ],
      "attempts": [
        "Searched the Module's requirements and scenarios for rounding",
        "Read the invoice scenario, which shows only whole-order totals"
      ],
      "unhandled": {
        "reason": "decision",
        "explanation": "what the shop Module promises about rounding is the Spec's to state; inferring it from code is forbidden"
      },
      "options": [
        "Round per line",
        "Round per order"
      ],
      "recommendation": "Round per order, as the invoice scenario implies."
    },
    "proposed_deletions": [],
    "output": {}
  }
}
```
