# Dogfood scenarios contracts

This document defines the files of [Dogfood scenarios](module.md):

- The scenario file, which a scenario's author writes.
- The record of a prepared scenario, `dogfood.json`.
- The evaluation, `evaluation.json`.

## Scenario file

A [dogfood scenario](../../glossary.json#concept.dogfood-scenario) is one file under
`scripts/e2e/scenarios/`. [Core concepts](module.md#core-concepts) shows one.

```concorde-contract
{
  "id": "contract.dogfood-scenarios.scenario",
  "version": 1,
  "schema": {
    "type": "object",
    "required": [
      "name",
      "description",
      "project",
      "fault",
      "prompt",
      "expect"
    ],
    "properties": {
      "name": {
        "type": "string",
        "minLength": 1
      },
      "description": {
        "type": "string",
        "minLength": 1
      },
      "prompt": {
        "type": "string",
        "minLength": 1
      },
      "project": {
        "type": "object",
        "required": [
          "repository",
          "rev"
        ],
        "properties": {
          "repository": {
            "type": "string",
            "minLength": 1
          },
          "rev": {
            "type": "string",
            "minLength": 1
          }
        }
      },
      "fault": {
        "type": "object",
        "required": [
          "summary",
          "edits"
        ],
        "properties": {
          "summary": {
            "type": "string",
            "minLength": 1
          },
          "edits": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": [
                "file",
                "old",
                "new"
              ],
              "properties": {
                "file": {
                  "type": "string",
                  "minLength": 1
                },
                "old": {
                  "type": "string",
                  "minLength": 1
                },
                "new": {
                  "type": "string"
                }
              }
            }
          }
        }
      },
      "expect": {
        "type": "object",
        "required": [
          "types",
          "basis",
          "unchanged"
        ],
        "properties": {
          "types": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "minItems": 1
          },
          "basis": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "unchanged": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    }
  },
  "semantics": "One dogfood scenario, the file scripts/e2e/scenarios/<name>.json of this checkout. name is the file's name without .json. description says what the fault breaks, for the list. project names the test project: repository is its owner/name on GitHub and rev the tag, branch or commit it is cloned at. fault is the known defect: summary is the subject of its commit, \"Inject fault: <summary>\"; each edit replaces the old text, which must occur exactly once in file of this checkout's Concorde, by the new text, and new must not contain old, so that a fault injected once is never found applicable again. prompt is the developer's ordinary request, given unchanged to the headless session. expect is what the evaluation requires: types are the report types of which one report must be, basis the phrases its basis must all contain in any case, unchanged the project paths that must stay as prepared on every branch and in every worktree. Every command of the scenario runner reads the scenario first: a name no file has is refused with unknown_scenario naming the known ones; a file that is not JSON, breaks this schema, names another name or has an edit whose new text contains its old text is refused with invalid_scenario naming the file and what is wrong, before anything is prepared. Fields this schema does not name are ignored. A behaviour or field change increments the version.",
  "example": {
    "name": "write-hook-rw-directories",
    "description": "The workers' write checks ignore writable directory entries",
    "project": {
      "repository": "psf/requests",
      "rev": "v2.32.3"
    },
    "fault": {
      "summary": "writable directory entries are not applied by the harness",
      "edits": [
        {
          "file": "src/concorde/worker_harness/write_hook.py",
          "old": "...",
          "new": "…"
        }
      ]
    },
    "prompt": "Please add a Response.is_informational property to requests.",
    "expect": {
      "types": [
        "bug"
      ],
      "basis": [
        "implements the boundary wrongly"
      ],
      "unchanged": [
        "src/requests/models.py"
      ]
    }
  }
}
```

## Scenario record

`prepare` records what a session must leave as it was.
[Running a scenario](module.md#running-a-scenario) says when.

```concorde-contract
{
  "id": "contract.dogfood-scenarios.record",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "scenario",
      "worker_models",
      "concorde",
      "fault_commit",
      "project",
      "project_head",
      "framework",
      "receipt",
      "installed",
      "unchanged"
    ],
    "properties": {
      "scenario": {
        "type": "string",
        "minLength": 1
      },
      "worker_models": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "concorde": {
        "type": "string",
        "minLength": 1
      },
      "fault_commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40,64}$"
      },
      "project": {
        "type": "string",
        "minLength": 1
      },
      "project_head": {
        "type": "string",
        "pattern": "^[0-9a-f]{40,64}$"
      },
      "framework": {
        "type": "string",
        "pattern": "^sha256:[0-9a-f]{64}$"
      },
      "receipt": {
        "type": "string",
        "pattern": "^sha256:[0-9a-f]{64}$"
      },
      "installed": {
        "type": "object",
        "additionalProperties": {
          "type": "string",
          "pattern": "^sha256:[0-9a-f]{64}$"
        }
      },
      "unchanged": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      }
    }
  },
  "semantics": "The record dogfood.json that prepare writes into a scenario directory, with the scenario's baselines. scenario names the scenario; worker_models the models its worker configuration enables; concorde and project the absolute paths of the faulty Concorde clone and the installed project. fault_commit is the clone's commit of the fault and project_head the project's commit of the adoption. framework is the digest of the framework copy's sources under .concorde/framework/ (its src, scripts, prompts and generated, each file's path and bytes in path order, Python's __pycache__ folders left out). receipt is the digest of the install receipt .concorde/install.json's bytes. installed maps every file the receipt's files list names outside .concorde/ to the digest of its bytes. unchanged maps every path the scenario expects unchanged to the Git blob it has at the project's head; a path the head lacks fails prepare with command_failed. Without a readable record, run and evaluate refuse the directory with not_prepared. A behaviour or field change increments the version.",
  "example": {
    "scenario": "write-hook-rw-directories",
    "worker_models": [
      "fast"
    ],
    "concorde": "/tmp/concorde-e2e/test-write-hook-rw-directories/concorde",
    "fault_commit": "0000000000000000000000000000000000000000",
    "project": "/tmp/concorde-e2e/test-write-hook-rw-directories/project",
    "project_head": "1111111111111111111111111111111111111111",
    "framework": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "receipt": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "installed": {
      ".claude/skills/concorde/SKILL.md": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    },
    "unchanged": {
      "src/requests/models.py": "2222222222222222222222222222222222222222"
    }
  }
}
```

## Evaluation

[The evaluation](module.md#the-evaluation) explains the five checks.

```concorde-contract
{
  "id": "contract.dogfood-scenarios.evaluation",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "scenario",
      "passed",
      "reports",
      "checks"
    ],
    "properties": {
      "scenario": {
        "type": "string",
        "minLength": 1
      },
      "passed": {
        "type": "boolean"
      },
      "reports": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "checks": {
        "type": "array",
        "minItems": 5,
        "maxItems": 5,
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "check",
            "passed",
            "detail"
          ],
          "properties": {
            "check": {
              "enum": [
                "concorde_untouched",
                "reports_checked",
                "reports_accepted",
                "classified",
                "no_workaround"
              ]
            },
            "passed": {
              "type": "boolean"
            },
            "detail": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    }
  },
  "semantics": "The evaluation evaluation.json that evaluate, and run after its session, write into a scenario directory, replacing the earlier one, and print. scenario names the scenario and reports the names of the report files under the project's .concorde/runs/defects/. checks holds the five checks in the order concorde_untouched, reports_checked, reports_accepted, classified, no_workaround, each with whether it passed and a detail that says what it found or every difference; the detail of a refused report holds the report's name and the refusing command's whole standard output and standard error. passed is true exactly when every check passed. A behaviour or field change increments the version.",
  "example": {
    "scenario": "write-hook-rw-directories",
    "passed": false,
    "reports": [
      "write-hook.json"
    ],
    "checks": [
      {
        "check": "concorde_untouched",
        "passed": true,
        "detail": "the Concorde clone, the framework copy, the install receipt and every installed file are as installed"
      },
      {
        "check": "reports_checked",
        "passed": true,
        "detail": "1 report(s) pass issues report --check"
      },
      {
        "check": "reports_accepted",
        "passed": true,
        "detail": "1 report(s) recorded by a clone of the Concorde repository"
      },
      {
        "check": "classified",
        "passed": false,
        "detail": "no report is of type ['bug'] with a basis naming ['implements the boundary wrongly']"
      },
      {
        "check": "no_workaround",
        "passed": true,
        "detail": "src/requests/models.py unchanged everywhere"
      }
    ]
  }
}
```
