# Adoption contracts

The exact shapes [Adoption](module.md) returns and accepts. Each output is the `output` of a
[run result](../../glossary.json#concept.run-result); the worker proposes the parts it
claims, and the host steps check them before passing them on.

Two things the host writes itself, so that no worker has to repeat text exactly. A worker's
decision names each option by a short identity of its own and its choice by that identity, or
names none when an answer settles the decision; the host records the options' texts and the chosen
option's text, or the answer, with who decided it. And a worker gives its tools absolute paths, so a
path it writes that begins with the worktree's own absolute path is written relative to the
worktree before anything checks it.

Both outputs also carry, beside the fields below, the `workflow` object of the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output), which repeats
their [decision points](../../glossary.json#concept.decision-point), decisions, deviations and, for a survey, its proposed checks in the shape
every workflow reads, as [req.adoption.step-output](requirements.md#req.adoption.step-output) says;
the convention, not these contracts, defines its fields.

## Decomposition proposal

The `output` of a `survey`. `remaining_entries` is computed by the host, never by the worker.

```concorde-contract
{
  "id": "contract.adoption.decomposition",
  "version": 6,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "module",
      "summary",
      "children",
      "externals",
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
      "externals": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "path",
            "used_by",
            "reason"
          ],
          "properties": {
            "path": {
              "type": "string",
              "minLength": 1
            },
            "used_by": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "reason": {
              "type": "string",
              "minLength": 1
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
            "env": {
              "type": "object",
              "additionalProperties": {
                "type": "string",
                "minLength": 1
              }
            },
            "when": {
              "enum": [
                "always",
                "readiness"
              ]
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
                "main-agent",
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
  "semantics": "The decomposition a survey proposes for module. children are the Modules to create: a new identity, a unique title, a purpose paragraph, the entries each binds (existing paths the surveyed Module's realizations cover, a directory ending in /) and the Modules it uses with the reason. remaining_entries are the entries the surveyed Module keeps once every child's entries and every external are removed, computed by the host with the rule of Adoption's shared records that the scaffold applies again: an entry no child entry or external touches stays; an entry a child entry or an external covers goes; and a directory entry that contains a child's entry or an external is replaced by the entries below it that nothing took, a subdirectory staying one entry when nothing inside it was taken and a file being listed exactly. Files the directory exclusion rule skips were never bound and are not listed. checks are proposed checks, in the shape of configured checks, for the surveyed Module or a child, each with the reason it was found; nothing configures them but the developer. decisions are the choices the worker took where the code left several open, written by the host: the worker names each option by an identity of its own and its choice by that identity, and the host records the options' texts, the chosen option's text as chosen and decided_by worker, or, for a decision an answer settles, the answer as chosen and that answer's answered_by, main-agent or developer, as decided_by; the worker never copies an option's text. Every path in children's entries, externals, check inputs and open questions' evidence is relative to the worktree: the host writes a path that begins with the worktree's absolute path, or its real path, relative to it before checking the proposal. open_questions are behaviours whose intent the worker could not tell; the worker wrote no promise about them. A proposed check may carry an env of variable names to strings, and its argv names the project's own interpreter as {python}; its inputs are canonical project-relative paths. externals are third-party code the project vendors, each with its path among the surveyed Module's paths, the Module that uses it and the reason: the scaffold takes them out of the parent's entries and makes each an external inclusion of its user, never a Module, so nobody describes or reviews it as the project's code. A proposed check may carry when: readiness for a full suite that runs only when readiness is decided. A behaviour or field change increments the version.",
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
    "externals": [],
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
          "{python}",
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

## Spec description

The `output` of a `code_to_spec` run. The document lists and `validation` are the host's
observations; `summary`, `promises`, `decisions`, `open_questions` and `deviations` are the worker's
claims, checked for consistency only, with each decision written by the host from the worker's
choice.

```concorde-contract
{
  "id": "contract.adoption.spec-description",
  "version": 4,
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
      "linked_tests",
      "unlinked_tests",
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
            },
            "tests": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
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
                "main-agent",
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
      "linked_tests": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "scenario",
            "test"
          ],
          "properties": {
            "scenario": {
              "type": "string",
              "minLength": 1
            },
            "test": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "unlinked_tests": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "scenario",
            "test",
            "reason"
          ],
          "properties": {
            "scenario": {
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
            "test": {
              "type": "string",
              "minLength": 1
            },
            "reason": {
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
  "semantics": "What one code_to_spec run described for modules. changed_documents are the documents whose reading or metadata changed, created_documents the prepared stubs the worker filled, removed_stubs the prepared stubs the host removed because the worker left them unchanged or proposed their deletion. promises are the promises the worker wrote, each with source code when it describes behaviour read in code or answer when it states intent a developer answer gave, and then question naming the answered question. decisions and open_questions have the shapes of the decomposition proposal, and the host writes the decisions from the worker's claims as it does there; no open question is written as a promise. The host writes a path in a promise's tests or an open question's evidence that begins with the worktree's absolute path, or its real path, relative to the worktree. deviations list every answered question whose stated intent differs from the observed code. validation holds in new_errors the structural errors the run counts as its own, those new since the baseline and every error located in a document a described Module owns even when the baseline had it, and in preexisting_errors the count of the other errors, which existed before the run; no error is counted in both. A scenario promise may name, in tests, the existing tests it was taken from (path::name or path::Class::name); linked_tests are the tests the host then marked with a verifies decorator, and unlinked_tests every link it left undone with the reason. A behaviour or field change increments the version.",
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
    "linked_tests": [],
    "unlinked_tests": [],
    "validation": {
      "new_errors": [],
      "preexisting_errors": 0
    }
  }
}
```

## Answers

The file `--answers` names. Every answer names a decision (`d.`) or
[open question](../../glossary.json#concept.open-question) (`q.`) of an admitted earlier run.

```concorde-contract
{
  "id": "contract.adoption.answers",
  "version": 3,
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
            "answer",
            "answered_by"
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
            },
            "answered_by": {
              "enum": [
                "main-agent",
                "developer"
              ]
            }
          }
        }
      }
    }
  },
  "semantics": "The answers to decisions and open questions of an earlier survey or code_to_spec run, admitted with --input, listing every answer given so far for that step. id names the decision or question, question repeats its text so the file is readable on its own, answer is the chosen option or the answerer's own words, and answered_by says who settled it: main-agent for an answer the main agent gave within its authority, developer for one the developer gave. A later run follows every answer: a survey or code_to_spec run takes an answered choice as a decision decided_by that answer's answered_by, and a code_to_spec run writes every answered question as a promise with source answer naming it, and records a deviation as well when the code does otherwise; a deviation never replaces the promise. A behaviour or field change increments the version.",
  "example": {
    "answers": [
      {
        "id": "q.payment-retry",
        "question": "retrying a declined payment",
        "answer": "retry both once; not retrying a timeout is a bug",
        "answered_by": "developer"
      },
      {
        "id": "d.db-helper",
        "question": "Does the shared database helper get a Module of its own?",
        "answer": "stay with the root",
        "answered_by": "main-agent"
      }
    ]
  }
}
```

## Errors

The codes of the run's own link in a result that is not `ok`, level `operation`. Worker, Workers
and Spec core links below it keep their own codes.

| Code | Run | Status | Reason | Raised when |
| --- | --- | --- | --- | --- |
| `invalid_request` | survey | `failed` | `input` | a survey is bound to other than one [Module](../../glossary.json#concept.module) |
| `invalid_answers` | survey, code_to_spec | `failed` | `input` | the answers file cannot be read, breaks `contract.adoption.answers` or answers one identity twice |
| `specs_unloadable` | both | `failed` | `scope` | the worktree's Specs cannot be loaded; the cause is Spec core's error |
| `grant_unavailable` | survey, code_to_spec | `failed` | `scope` | Spec core cannot compute the `code-to-spec` grant; the cause is its error |
| `unknown_modules` | code_to_spec | `failed` | `input` | a bound Module is not registered, listed with the registered ones |
| `inconsistent_proposal` | survey | `failed` | `capability` | the proposal does not fit the worktree, has a decision whose choice names none of its options or that neither chooses nor follows an answer, or does not follow an answer; every problem is listed |
| `new_structural_errors` | code_to_spec | `blocked` | `decision` | the description adds structural errors; one cause per finding |
| `inconsistent_description` | code_to_spec | `failed` | `capability` | the description names another Module, repeats an identity, has a decision whose choice names none of its options or that neither chooses nor follows an answer, or leaves out an answered decision or question; every problem is listed |

A worker that ended `blocked` or `failed`, a launch error, a timeout and an audit violation keep
the codes of the [standard worker sequence](../workers.md#errors-of-the-worker-sequence).
