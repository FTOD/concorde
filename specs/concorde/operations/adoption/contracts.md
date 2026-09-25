# Adoption contracts

The exact shapes [Adoption](module.md) returns and accepts. Each output is the `output` of an
[Operation result](../module.md#concept.operations.result); the worker proposes the parts it
claims, and the host checks them before passing them on.

## Decomposition proposal

The `output` of a `survey`. `remaining_entries` is computed by the host, never by the worker.

```concorde-contract
{
  "id": "contract.adoption.decomposition",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "module",
      "summary",
      "children",
      "remaining_entries",
      "checks",
      "decisions",
      "open_questions"
    ],
    "properties": {
      "module": {
        "type": "string",
        "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
      },
      "summary": {
        "type": "string",
        "minLength": 1
      },
      "children": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "title",
            "purpose",
            "entries",
            "uses"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "title": {
              "type": "string",
              "minLength": 1
            },
            "purpose": {
              "type": "string",
              "minLength": 1
            },
            "entries": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "uses": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "target",
                  "reason"
                ],
                "properties": {
                  "target": {
                    "type": "string",
                    "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
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
      "remaining_entries": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "checks": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "module",
            "argv",
            "timeout_seconds",
            "inputs",
            "reason"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^check\\.[a-z0-9-]+(?:\\.[a-z0-9-]+)*$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "argv": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "timeout_seconds": {
              "type": "integer",
              "minimum": 1
            },
            "inputs": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "reason": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "decisions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "module",
            "question",
            "options",
            "chosen",
            "reason",
            "decided_by"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^d\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "minItems": 2,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "chosen": {
              "type": "string",
              "minLength": 1
            },
            "reason": {
              "type": "string",
              "minLength": 1
            },
            "decided_by": {
              "enum": [
                "worker",
                "developer"
              ]
            }
          }
        }
      },
      "open_questions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "module",
            "subject",
            "observed",
            "evidence",
            "why_uncertain",
            "options",
            "recommendation"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^q\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "subject": {
              "type": "string",
              "minLength": 1
            },
            "observed": {
              "type": "string",
              "minLength": 1
            },
            "evidence": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "why_uncertain": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "recommendation": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    }
  },
  "semantics": "The decomposition a survey proposes for module. children are the Modules to create: a new identity, a unique title, a purpose paragraph, the entries each binds (existing paths the surveyed Module's realizations cover, a directory ending in /) and the Modules it uses with the reason. remaining_entries are the entries the surveyed Module keeps once every child's entries are removed, computed by the host with the scaffold's rule. checks are proposed checks, in the shape of configured checks, for the surveyed Module or a child, each with the reason it was found; nothing configures them but the developer. decisions are the choices the worker took where the code left several open, each with decided_by worker, or developer when it follows an answer. open_questions are behaviours whose intent the worker could not tell; the worker wrote no promise about them. A behaviour or field change increments the version.",
  "example": {
    "module": "module.shop",
    "summary": "The shop has a checkout service and an inventory service that share one database helper; they become two Modules and the helper stays with the root.",
    "children": [
      {
        "id": "module.checkout",
        "title": "Checkout",
        "purpose": "Checkout turns a customer's basket into one paid order.",
        "entries": [
          "src/checkout/",
          "tests/checkout/"
        ],
        "uses": [
          {
            "target": "module.inventory",
            "reason": "checkout reserves stock through the inventory client before charging"
          }
        ]
      },
      {
        "id": "module.inventory",
        "title": "Inventory",
        "purpose": "Inventory keeps stock levels and holds stock for pending orders.",
        "entries": [
          "src/inventory/",
          "tests/inventory/"
        ],
        "uses": []
      }
    ],
    "remaining_entries": [
      "README.md",
      "pyproject.toml",
      "src/db.py"
    ],
    "checks": [
      {
        "id": "check.checkout.tests",
        "module": "module.checkout",
        "argv": [
          "python",
          "-m",
          "pytest",
          "tests/checkout"
        ],
        "timeout_seconds": 300,
        "inputs": [
          "src/checkout",
          "tests/checkout"
        ],
        "reason": "pyproject.toml configures pytest and tests/checkout tests only the checkout package"
      }
    ],
    "decisions": [
      {
        "id": "d.db-helper",
        "module": "module.shop",
        "question": "Does the shared database helper get a Module of its own?",
        "options": [
          "a Module of its own",
          "stay with the root"
        ],
        "chosen": "stay with the root",
        "reason": "it is 40 lines of connection setup with no behaviour of its own",
        "decided_by": "worker"
      }
    ],
    "open_questions": []
  }
}
```

## Scaffold record

The `output` of a `scaffold`, entirely observed by the host.

```concorde-contract
{
  "id": "contract.adoption.scaffold-record",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "parent",
      "survey_run",
      "created",
      "parent_entries_before",
      "parent_entries_after",
      "files_written"
    ],
    "properties": {
      "parent": {
        "type": "string",
        "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
      },
      "survey_run": {
        "type": "string",
        "minLength": 1
      },
      "created": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "title",
            "entry",
            "entries"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "title": {
              "type": "string",
              "minLength": 1
            },
            "entry": {
              "type": "string",
              "minLength": 1
            },
            "entries": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        }
      },
      "parent_entries_before": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "parent_entries_after": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "files_written": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      }
    }
  },
  "semantics": "What one scaffold did. parent is the surveyed Module and survey_run the admitted survey. created lists every Module created, with its entry path and the entries its realization binds. parent_entries_before and parent_entries_after are the union of the parent's realization entries before and after. The scaffold never configures the proposal's checks. files_written lists every file the transaction wrote. A behaviour or field change increments the version.",
  "example": {
    "parent": "module.shop",
    "survey_run": "r-20260925T101500-survey-1a2b3c4d",
    "created": [
      {
        "id": "module.checkout",
        "title": "Checkout",
        "entry": "specs/shop/checkout/module.md",
        "entries": [
          "src/checkout/",
          "tests/checkout/"
        ]
      },
      {
        "id": "module.inventory",
        "title": "Inventory",
        "entry": "specs/shop/inventory/module.md",
        "entries": [
          "src/inventory/",
          "tests/inventory/"
        ]
      }
    ],
    "parent_entries_before": [
      "README.md",
      "pyproject.toml",
      "src/",
      "tests/"
    ],
    "parent_entries_after": [
      "README.md",
      "pyproject.toml",
      "src/db.py"
    ],
    "files_written": [
      ".concorde/specs.json",
      "specs/shop/checkout/module.md",
      "specs/shop/checkout/module.md.json",
      "specs/shop/inventory/module.md",
      "specs/shop/inventory/module.md.json",
      "specs/shop/module.md",
      "specs/shop/module.md.json"
    ]
  }
}
```

## Spec description

The `output` of a `code_to_spec` run. The document lists and `validation` are the host's
observations; `summary`, `promises`, `decisions`, `open_questions` and `deviations` are the worker's
claims, checked for consistency only.

```concorde-contract
{
  "id": "contract.adoption.spec-description",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "modules",
      "summary",
      "changed_documents",
      "created_documents",
      "removed_stubs",
      "promises",
      "decisions",
      "open_questions",
      "deviations",
      "validation"
    ],
    "properties": {
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "string",
          "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
        }
      },
      "summary": {
        "type": "string",
        "minLength": 1
      },
      "changed_documents": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "created_documents": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "removed_stubs": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "promises": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "module",
            "kind",
            "id",
            "description",
            "source",
            "question"
          ],
          "properties": {
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "kind": {
              "enum": [
                "requirement",
                "scenario",
                "contract",
                "concept",
                "realization",
                "relation",
                "explanation"
              ]
            },
            "id": {
              "anyOf": [
                {
                  "type": "string",
                  "minLength": 1
                },
                {
                  "type": "null"
                }
              ]
            },
            "description": {
              "type": "string",
              "minLength": 1
            },
            "source": {
              "enum": [
                "code",
                "answer"
              ]
            },
            "question": {
              "anyOf": [
                {
                  "type": "string",
                  "pattern": "^q\\.[a-z0-9-]+$"
                },
                {
                  "type": "null"
                }
              ]
            }
          }
        }
      },
      "decisions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "module",
            "question",
            "options",
            "chosen",
            "reason",
            "decided_by"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^d\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "minItems": 2,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "chosen": {
              "type": "string",
              "minLength": 1
            },
            "reason": {
              "type": "string",
              "minLength": 1
            },
            "decided_by": {
              "enum": [
                "worker",
                "developer"
              ]
            }
          }
        }
      },
      "open_questions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "module",
            "subject",
            "observed",
            "evidence",
            "why_uncertain",
            "options",
            "recommendation"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^q\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "subject": {
              "type": "string",
              "minLength": 1
            },
            "observed": {
              "type": "string",
              "minLength": 1
            },
            "evidence": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "why_uncertain": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "recommendation": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "deviations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "module",
            "question",
            "intended",
            "observed"
          ],
          "properties": {
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "question": {
              "type": "string",
              "pattern": "^q\\.[a-z0-9-]+$"
            },
            "intended": {
              "type": "string",
              "minLength": 1
            },
            "observed": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "validation": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "new_errors",
          "preexisting_errors"
        ],
        "properties": {
          "new_errors": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "rule_id",
                "path",
                "message"
              ],
              "properties": {
                "rule_id": {
                  "type": "string",
                  "minLength": 1
                },
                "path": {
                  "anyOf": [
                    {
                      "type": "string",
                      "minLength": 1
                    },
                    {
                      "type": "null"
                    }
                  ]
                },
                "message": {
                  "type": "string",
                  "minLength": 1
                }
              }
            }
          },
          "preexisting_errors": {
            "type": "integer",
            "minimum": 0
          }
        }
      }
    }
  },
  "semantics": "What one code_to_spec run described for modules. changed_documents are the documents whose reading or metadata changed, created_documents the prepared stubs the worker filled, removed_stubs the stubs it left unchanged and the host removed. promises are the promises the worker wrote, each with source code when it describes behaviour read in code or answer when it states intent a developer answer gave, and then question naming the answered question. decisions and open_questions have the shapes of the decomposition proposal; no open question is written as a promise. deviations list every answered question whose stated intent differs from the observed code. validation holds the structural errors this run introduced and the count of errors that existed before it. A behaviour or field change increments the version.",
  "example": {
    "modules": [
      "module.checkout"
    ],
    "summary": "Described checkout's submit flow, its order record and its three failure responses; one retry behaviour is left open.",
    "changed_documents": [
      "specs/shop/checkout/module.md",
      "specs/shop/checkout/module.md.json",
      "specs/shop/checkout/scenarios.md"
    ],
    "created_documents": [
      "specs/shop/checkout/scenarios.md"
    ],
    "removed_stubs": [
      "specs/shop/checkout/contracts.md",
      "specs/shop/checkout/requirements.md"
    ],
    "promises": [
      {
        "module": "module.checkout",
        "kind": "scenario",
        "id": "scenario.checkout.submit",
        "description": "a valid basket becomes one order and its number is returned",
        "source": "code",
        "question": null
      }
    ],
    "decisions": [
      {
        "id": "d.order-term",
        "module": "module.checkout",
        "question": "Is the stored record called an order or a purchase?",
        "options": [
          "Order",
          "Purchase"
        ],
        "chosen": "Order",
        "reason": "the table, the class and the API all say order; purchase appears once in a log message",
        "decided_by": "worker"
      }
    ],
    "open_questions": [
      {
        "id": "q.payment-retry",
        "module": "module.checkout",
        "subject": "retrying a declined payment",
        "observed": "a declined payment is retried once after two seconds, but a timed-out one is not",
        "evidence": [
          "src/checkout/payment.py"
        ],
        "why_uncertain": "no comment, test or configuration says whether the difference is intended",
        "options": [
          "retry declined payments once, never timeouts",
          "retry both",
          "retry neither"
        ],
        "recommendation": "ask whether a timeout should be retried; the current behaviour may be an oversight"
      }
    ],
    "deviations": [],
    "validation": {
      "new_errors": [],
      "preexisting_errors": 0
    }
  }
}
```

## Answers

The file `--answers` names. Every answer names a decision (`d.`) or open question (`q.`) of an
admitted earlier run.

```concorde-contract
{
  "id": "contract.adoption.answers",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "answers"
    ],
    "properties": {
      "answers": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "question",
            "answer"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^[dq]\\.[a-z0-9-]+$"
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "answer": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    }
  },
  "semantics": "The developer's answers to decisions and open questions of an earlier survey or code_to_spec run, admitted with --input, listing every answer given so far for that step. id names the decision or question, question repeats its text so the file is readable on its own, and answer is the chosen option or the developer's own words. A later run follows every answer: a survey takes the answered choice as a decision decided_by developer, and a code_to_spec run writes an answered question as a promise with source answer, or records a deviation when the code does otherwise. A behaviour or field change increments the version.",
  "example": {
    "answers": [
      {
        "id": "q.payment-retry",
        "question": "retrying a declined payment",
        "answer": "retry both once; not retrying a timeout is a bug"
      },
      {
        "id": "d.db-helper",
        "question": "Does the shared database helper get a Module of its own?",
        "answer": "stay with the root"
      }
    ]
  }
}
```

## Errors

The codes of the Operation's own link in a result that is not `ok`. Worker, Workers and Spec core
links below it keep their own codes.

| Code | Operation | Status | Reason | Raised when |
| --- | --- | --- | --- | --- |
| `invalid_request` | survey, scaffold | `failed` | `input` | a survey is bound to other than one Module; a scaffold has no `--input`, several, or one that is not a survey, or the survey's output breaks its contract |
| `invalid_answers` | survey, code_to_spec | `failed` | `input` | the answers file cannot be read, breaks `contract.adoption.answers` or answers one identity twice |
| `specs_unloadable` | all three | `failed` | `scope` | the worktree's Specs cannot be loaded; the cause is Spec core's error |
| `grant_unavailable` | survey, code_to_spec | `failed` | `scope` | Spec core cannot compute the `code-to-spec` grant; the cause is its error |
| `unknown_modules` | code_to_spec | `failed` | `input` | a bound Module is not registered, listed with the registered ones |
| `inconsistent_proposal` | survey | `failed` | `capability` | the proposal does not fit the worktree or does not follow an answer; every problem is listed |
| `stale_proposal` | scaffold | `blocked` | `decision` | the proposal no longer fits the worktree, a file it would create exists, or a file changed while it was written; every mismatch is listed |
| `scaffold_invalid` | scaffold | `failed` | `capability` | the scaffold's files would add structural errors; one cause per finding, and nothing is kept |
| `new_structural_errors` | code_to_spec | `blocked` | `decision` | the description adds structural errors; one cause per finding |
| `inconsistent_description` | code_to_spec | `failed` | `capability` | the description names another Module, repeats an identity, chooses outside its options or does not follow an answer; every problem is listed |

A worker that ended `blocked` or `failed`, a launch error, a timeout and an audit violation keep
the codes of the [standard worker sequence](../host.md).
