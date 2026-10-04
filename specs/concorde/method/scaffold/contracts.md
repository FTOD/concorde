# Scaffold contracts

The exact shape [Scaffold](module.md) returns, the `output` of its
[run result](../../glossary.json#concept.run-result), and the codes of its errors. The
proposal it applies is Adoption's
[decomposition proposal](../adoption/contracts.md#contract.adoption.decomposition).

The output also carries, beside the record's fields, the `workflow` object of the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output), whose `data`
hands a [workflow script](../../glossary.json#concept.workflow-script) what it needs to describe the created [Modules](../../glossary.json#concept.module), as
[req.scaffold.step-output](requirements.md#req.scaffold.step-output) says: `created_modules`, the
list of the created Modules in the record's order, each `{"id": "<module>", "uses":
["<module>", …]}` with the `uses` the survey proposed among the created Modules alone. It declares
no [decision point](../../glossary.json#concept.decision-point), decision or note; the convention, not this contract, defines the object.

## Scaffold record

The `output` of `scaffold`, entirely observed by its steps.

```concorde-contract
{
  "id": "contract.scaffold.record",
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "parent",
      "survey_run",
      "created",
      "externals",
      "parent_entries_before",
      "parent_entries_after",
      "files_written",
      "workflow"
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
      },
      "workflow": {
        "type": "object"
      }
    }
  },
  "semantics": "What one scaffold did. parent is the surveyed Module and survey_run the admitted survey. created lists every Module created, with its entry path and the entries its realization binds. parent_entries_before and parent_entries_after are the union of the parent's realization entries, in every document of the parent, before and after. The scaffold never configures the proposal's checks. files_written lists every file the transaction wrote. externals are the vendored paths the scaffold made external inclusions of their users. workflow is the object of Workflows' step output convention, which defines its fields: its data holds created_modules, each created Module in the record's order with the uses the survey proposed among the created Modules (req.scaffold.step-output). A behaviour or field change increments the version.",
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
    "externals": [],
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
    ],
    "workflow": {
      "decision_points": [],
      "decisions": [],
      "deviations": [],
      "notes": [],
      "blocking": null,
      "data": {
        "created_modules": [
          {
            "id": "module.checkout",
            "uses": [
              "module.inventory"
            ]
          },
          {
            "id": "module.inventory",
            "uses": []
          }
        ]
      }
    }
  }
}
```

## Errors

The codes of the run's own link, level `command`, in a result that is not `ok` because one of the
scaffold's steps stopped it. Spec core links below it keep their own codes. A run the runner
refuses before the first step, such as an
[unbound run](../../glossary.json#concept.unbound-run) (`binding_required`) or one with an input
it does not admit (`input_not_admissible`), carries the runner's `refused` link instead, listed in
the [runner's errors](../../execution/runner.md#errors).

| Code | Status | Reason | Raised when |
| --- | --- | --- | --- |
| `invalid_request` | `failed` | `input` | the scaffold has no `--input`, several, or one that is not a survey, or the survey's output breaks its contract |
| `specs_unloadable` | `failed` | `scope` | the worktree's [Specs](../../glossary.json#concept.spec) cannot be loaded; the cause is Spec core's error |
| `stale_proposal` | `blocked` | `decision` | the proposal no longer fits the worktree (a child's folder already exists, among others) or a file it would create exists, each mismatch listed and a cause of its own, a `component` link of code `proposal_mismatch`; or a file changed while it was written, every file restored and Spec core's error the cause |
| `scaffold_invalid` | `failed` | `capability` | the scaffold's files would add structural errors; one cause per finding, and nothing is kept |
| `write_failed` | `failed` | `environment` | the [file transaction](../../glossary.json#concept.file-transaction) failed for another reason, such as the operating system refusing a write, or could not restore a file it wrote, whatever made it fail; the detail and the `unrestored` evidence name every file that still holds the scaffold's content, the detail says every other file is as before, the options say to remove or restore the named files, and Spec core's error is the cause |
