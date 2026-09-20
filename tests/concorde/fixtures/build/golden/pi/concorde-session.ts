// Rendered by `python3 scripts/concorde.py build` from skills/, prompts/ and the
// operation contracts; do not edit. The Concorde session extension itself lives at
// pi/extensions/concorde-session.ts; this shim binds it to this project.
import { fileURLToPath } from "node:url";
import { concordeSession } from "../../../pi/extensions/concorde-session.ts";
import type { SessionCatalog } from "../../../pi/extensions/concorde-session.ts";

const CATALOG: SessionCatalog = {
  "explicit_request_only": true,
  "interpreters": [
    ".venv/bin/python",
    ".venv/Scripts/python.exe"
  ],
  "launcher": "scripts/run-operation.py",
  "operations": [
    {
      "description": "Operation: independently review or diagnose a Module's granted implementation against its Spec and return scoped read-only findings.",
      "guidance": "# concorde-code-review\n\nInvoke this operation to review or diagnose the selected implementation against its Spec. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nThe request requires target_id and task. The calling agent selects the Module explicitly;\noptional focus_id must name its scenario. Constraints and a current-worktree change_id may be\nsupplied. There is no implicit routing or review_mode selector. The host deterministically checks\nthe target and freezes its complete context before starting a fresh read-only reviewer.\n\nReview runs in the current worktree without creating a development change or requiring a preexisting\nIssue. It reads the complete selected Module contract and only its admitted implementation files,\nexternal references and scoped changes. Reviewers have no write, network or credential grants.\nThe host persists review reports separately from reviewer authority.\n\nA managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.\nDo not claim this compares against another branch or a merge base. Report the returned review\ncoverage, Issue judgments and limitations, preserving incomplete or failed outcomes. Findings do\nnot authorize repairs. describe-policy previews grants without launching agents or persisting\nreview results. A separate review intent cannot replace another task's required lifecycle review.\n",
      "name": "concorde-code-review",
      "request_schema": {
        "$defs": {
          "concorde-code-review-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-code-review-request"
          },
          "schema_version": {
            "const": 2,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-code-review-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 2
    },
    {
      "description": "Operation: apply the Pi worker model selection (model, thinking level, timeout and per-worker overrides); with accept_protocol, rebind the project to the installed Protocol copy.",
      "guidance": "# concorde-configure\n\nInvoke this operation to configure. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\nThis is a deterministic lifecycle operation: it runs no agent cognition and selects no context.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nUse the supplied target identity; if it is ambiguous, ask the user to identify it instead of\nsearching other Specs.\nThe user-facing session coordinates needs and may delegate a complete task to one fresh task\nchild, or handle a simple consumer-project task directly. Task children never delegate tasks or\nmove worktrees. They may run several public Operations on the same change through delivery;\nbounded Operation workers still obey the actual harness's depth and permission limits.\n\nA mutating Operation requested from a consumer primary normally runs in a host-created candidate;\nan Operation already in an assigned candidate reuses it. The requesting session stays where it\nstarted and receives path, branch and stable change_id. Uncommitted primary edits are not copied.\nDurable status and runs belong only to the primary coordinator, not duplicate candidate archives.\nTask-authorized `.concorde` edits in the owned workspace are not forbidden by directory name;\npreserve task scope, truthful evidence and concurrency safety, and obey actual worker grants.\n\nFor Concorde source maintenance, the main creates a candidate and a fresh Skill-free maintenance\nchild with inherited/discovered catalogs disabled. After the writer checks, commits and stops,\na separate fresh sibling test child receives only exact candidate-built Skills and runtime\nprovenance. Neither forks old Skill bodies or delegates tasks. The tester never rewrites governing\nSkills; failures return to maintenance and then a new tester. Maintenance may finish through\nordinary Git with explicit merge authorization, without Concorde delivery. Skill metadata alone\nis not evidence of loading or execution. Never fall back to global or primary Skills.\n\nReport Spec gaps or blocked execution as returned. Non-implementation workers never receive\nimplementation code or raw test logs.\n",
      "name": "concorde-configure",
      "request_schema": {
        "$defs": {
          "concorde-configure-request": {
            "additionalProperties": false,
            "properties": {
              "accept_protocol": {
                "type": "boolean"
              },
              "configuration": {
                "additionalProperties": false,
                "properties": {
                  "data": {
                    "$ref": "#/$defs/concorde-operation-configuration"
                  },
                  "schema_version": {
                    "const": 1,
                    "type": "integer"
                  },
                  "type_id": {
                    "const": "concorde-operation-configuration"
                  }
                },
                "required": [
                  "type_id",
                  "schema_version",
                  "data"
                ],
                "type": "object"
              }
            },
            "required": [
              "configuration"
            ],
            "type": "object"
          },
          "concorde-operation-configuration": {
            "additionalProperties": false,
            "properties": {
              "model": {
                "minLength": 1,
                "type": "string"
              },
              "thinking": {
                "enum": [
                  "off",
                  "minimal",
                  "low",
                  "medium",
                  "high",
                  "xhigh",
                  "max"
                ]
              },
              "timeout_seconds": {
                "type": "integer"
              },
              "workers": {
                "additionalProperties": {
                  "additionalProperties": false,
                  "properties": {
                    "model": {
                      "minLength": 1,
                      "type": "string"
                    },
                    "thinking": {
                      "enum": [
                        "off",
                        "minimal",
                        "low",
                        "medium",
                        "high",
                        "xhigh",
                        "max"
                      ]
                    },
                    "timeout_seconds": {
                      "type": "integer"
                    }
                  },
                  "required": [],
                  "type": "object"
                },
                "properties": {},
                "type": "object"
              }
            },
            "required": [],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-configure-request"
          },
          "schema_version": {
            "const": 2,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-configure-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 2
    },
    {
      "description": "Operation: assess whether the selected Module Spec supports the task.",
      "guidance": "# concorde-context-solve\n\nInvoke this operation to assess whether the selected Module Spec supports the task. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\n\nReturns sufficiency or attributed gaps without authoring Specs, planning or implementation.\n\nThe calling agent chooses whether and when to invoke other Operations. Report invalid or stale\ninputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews\nthe grant without launching a worker. Execution retains bounded context and authority.\n",
      "name": "concorde-context-solve",
      "request_schema": {
        "$defs": {
          "concorde-context-solve-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-context-solve-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-context-solve-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 1
    },
    {
      "description": "Operation: stage a verified change, remove its worktree, and explicitly merge from the primary session.",
      "guidance": "# concorde-deliver\n\nInvoke delivery from an agent whose initial working directory is either the selected source\nworktree or the primary Git worktree. A third-worktree or nested invocation cannot deliver this\nchange. Keep the session and its loaded Skills bound to their original participant.\n\nconfiguration (null to load initialized host settings, or a matching concorde-operation-configuration@1),\nand input (concorde-deliver-request@1). Supply the selected change_id from the primary worktree's\n`.concorde/status/` inventory or its saved delivery receipt. Optional target/task metadata\ncannot replace change ownership. No domain flags or positional arguments are accepted.\n\nDefault delivery verifies the candidate and its integration with the current primary commit,\nconfirms every entity entry marked `pending`, an exact file or a directory prefix, that now exists on\ndisk and clears its marker as part of the delivered commit (an entry still missing stays pending and\nis reported), creates\n`concorde/delivered/<change_id>` without checking it out, and removes the source worktree\nand its local state. Each change has an independent delivery branch. The primary worktree's\nchecked-out branch, index and project files are unchanged. `keep_worktree:true` explicitly retains\nthe source; ownership of the requesting session does not retain it automatically. After removal,\nend the source session without further project work. Further work requires a fresh P10 session.\nManaged AGENTS.md/CLAUDE.md blocks and local control state never enter the delivered tree.\n\nOnly when the user explicitly requests the final primary-branch merge, invoke a separate request\nwith `merge_primary:true` and the delivered change_id from the primary worktree's owning session.\nA generic delivery request does not authorize this flag. At most one agent may own writes in the\nprimary worktree; other agents work in their own linked worktrees. The host holds the shared\nrepository lock for delivery state changes and the entire primary merge, rechecks the current\nintegration and rejects conflicts or failed checks before changing the primary branch. Preserve\nlocal edits; a dirty primary blocks final merging but does not block default branch delivery.\nDo not start another primary writer or perform manual Git delivery around the host.\n\nReceipts retain delivery and primary merge evidence separately, including which files were\nconfirmed and which remain pending. Retry failed cleanup without\nanother branch merge. Retry an already completed primary merge without merging twice. After source\nremoval, retry from the primary session using the receipt's change_id. Conflicts or failed checks\npreserve the candidate or delivered branch for repair in a new change worktree. Report the returned\nbranch, outcome, cleanup status and whether final primary merging remains pending faithfully.\n",
      "name": "concorde-deliver",
      "request_schema": {
        "$defs": {
          "concorde-deliver-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "keep_worktree": {
                "type": "boolean"
              },
              "merge_primary": {
                "type": "boolean"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "change_id"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-deliver-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-deliver-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 1
    },
    {
      "description": "Operation: implement current accepted tasks inside the selected Module grant.",
      "guidance": "# concorde-implement\n\nInvoke this operation to implement current accepted tasks inside the selected Module grant. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\n\nRequires a current accepted plan and tasks. The programmer may change only registered implementation files, never Specs, metadata or registry. Component work and necessary contract changes return to the calling agent for separate selection; no child workflow or Spec authoring runs automatically. Completion is not review, validation, readiness or delivery.\n\nThe calling agent chooses whether and when to invoke other Operations. Report invalid or stale\ninputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews\nthe grant without launching a worker. Execution retains bounded context and authority.\n",
      "name": "concorde-implement",
      "request_schema": {
        "$defs": {
          "concorde-implement-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-implement-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-implement-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 1
    },
    {
      "description": "Operation: propose and apply explicit project initialization with a pinned Protocol and an honest registry stub.",
      "guidance": "# concorde-init\n\nInvoke this operation to init. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\nThis is a deterministic lifecycle operation: it runs no agent cognition and selects no context.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nUse the supplied target identity; if it is ambiguous, ask the user to identify it instead of\nsearching other Specs.\nThe user-facing session coordinates needs and may delegate a complete task to one fresh task\nchild, or handle a simple consumer-project task directly. Task children never delegate tasks or\nmove worktrees. They may run several public Operations on the same change through delivery;\nbounded Operation workers still obey the actual harness's depth and permission limits.\n\nA mutating Operation requested from a consumer primary normally runs in a host-created candidate;\nan Operation already in an assigned candidate reuses it. The requesting session stays where it\nstarted and receives path, branch and stable change_id. Uncommitted primary edits are not copied.\nDurable status and runs belong only to the primary coordinator, not duplicate candidate archives.\nTask-authorized `.concorde` edits in the owned workspace are not forbidden by directory name;\npreserve task scope, truthful evidence and concurrency safety, and obey actual worker grants.\n\nFor Concorde source maintenance, the main creates a candidate and a fresh Skill-free maintenance\nchild with inherited/discovered catalogs disabled. After the writer checks, commits and stops,\na separate fresh sibling test child receives only exact candidate-built Skills and runtime\nprovenance. Neither forks old Skill bodies or delegates tasks. The tester never rewrites governing\nSkills; failures return to maintenance and then a new tester. Maintenance may finish through\nordinary Git with explicit merge authorization, without Concorde delivery. Skill metadata alone\nis not evidence of loading or execution. Never fall back to global or primary Skills.\n\nReport Spec gaps or blocked execution as returned. Non-implementation workers never receive\nimplementation code or raw test logs.\n",
      "name": "concorde-init",
      "request_schema": {
        "$defs": {
          "concorde-init-request": {
            "additionalProperties": false,
            "properties": {
              "action": {
                "enum": [
                  "propose",
                  "apply"
                ]
              },
              "configuration": {
                "additionalProperties": false,
                "properties": {
                  "data": {
                    "$ref": "#/$defs/concorde-operation-configuration"
                  },
                  "schema_version": {
                    "const": 1,
                    "type": "integer"
                  },
                  "type_id": {
                    "const": "concorde-operation-configuration"
                  }
                },
                "required": [
                  "type_id",
                  "schema_version",
                  "data"
                ],
                "type": "object"
              },
              "name": {
                "minLength": 1,
                "type": "string"
              },
              "proposal": {
                "additionalProperties": false,
                "properties": {
                  "data": {
                    "$ref": "#/$defs/concorde-project-proposal"
                  },
                  "schema_version": {
                    "const": 1,
                    "type": "integer"
                  },
                  "type_id": {
                    "const": "concorde-project-proposal"
                  }
                },
                "required": [
                  "type_id",
                  "schema_version",
                  "data"
                ],
                "type": "object"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "action"
            ],
            "type": "object"
          },
          "concorde-operation-configuration": {
            "additionalProperties": false,
            "properties": {
              "model": {
                "minLength": 1,
                "type": "string"
              },
              "thinking": {
                "enum": [
                  "off",
                  "minimal",
                  "low",
                  "medium",
                  "high",
                  "xhigh",
                  "max"
                ]
              },
              "timeout_seconds": {
                "type": "integer"
              },
              "workers": {
                "additionalProperties": {
                  "additionalProperties": false,
                  "properties": {
                    "model": {
                      "minLength": 1,
                      "type": "string"
                    },
                    "thinking": {
                      "enum": [
                        "off",
                        "minimal",
                        "low",
                        "medium",
                        "high",
                        "xhigh",
                        "max"
                      ]
                    },
                    "timeout_seconds": {
                      "type": "integer"
                    }
                  },
                  "required": [],
                  "type": "object"
                },
                "properties": {},
                "type": "object"
              }
            },
            "required": [],
            "type": "object"
          },
          "concorde-project-proposal": {
            "additionalProperties": false,
            "properties": {
              "action": {
                "enum": [
                  "initialize"
                ]
              },
              "base_digest": {
                "anyOf": [
                  {
                    "minLength": 1,
                    "pattern": "^sha256:[0-9a-f]{64}$",
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ]
              },
              "files": {
                "items": {
                  "additionalProperties": false,
                  "properties": {
                    "before_digest": {
                      "anyOf": [
                        {
                          "minLength": 1,
                          "pattern": "^sha256:[0-9a-f]{64}$",
                          "type": "string"
                        },
                        {
                          "type": "null"
                        }
                      ]
                    },
                    "content": {
                      "type": "string"
                    },
                    "path": {
                      "minLength": 1,
                      "type": "string"
                    }
                  },
                  "required": [
                    "path",
                    "before_digest",
                    "content"
                  ],
                  "type": "object"
                },
                "type": "array"
              }
            },
            "required": [
              "action",
              "base_digest",
              "files"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-init-request"
          },
          "schema_version": {
            "const": 2,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-init-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 2
    },
    {
      "description": "Inspect, report, reopen or assess branch-local Issues; return needed repairs to the caller or verify current work without automatic delivery.",
      "guidance": "# concorde-issues\n\nInvoke this operation to manage or solve explicitly selected Issues. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nChoose action list, show, report, reopen or solve. Show, reopen and solve require one issue_id;\nexpected_revision optionally rejects a changed selection. Report requires target_id and a classified\nreport; an append also names its issue_id and expected_revision inside the report. Reopen requires\na note. Only solve starts the bounded decision and verification lifecycle; other actions are\ncurrent-worktree bookkeeping. An Issue is not an implementation task, and reporting it neither\nstops a running agent nor approves a repair.\n\nSolve returns needed implementation or Spec repair to the calling agent with the selected target,\nintended behavior and rationale. It does not author Specs, change implementation or start planning\nor child development. The caller performs authorized Spec, paired metadata and registry edits or\nselects retained Operations explicitly, then requests fresh verification with current inputs.\nA return-to-caller result preserves the open Issue and is not completed repair or readiness.\nSolve can run Issue-specific read-only verification, resolve, identify a duplicate or reject a\nmistaken report from evidence without mandatory human approval. Unresolved product/design choices\nare returned as needs-decision. Respect the host's bounded iteration limit and distinct execution\nfailures. Do not retry by widening permissions.\n\nFrom the primary worktree the host copies the selected Issue's exact bytes, including an uncommitted\nreport, into the candidate worktree it creates, without copying unrelated edits, and solves there;\nthis session receives the candidate's result and continues the change with its change_id.\nA successful solve ends at ready with the disposition included in verification. It does not deliver,\nmerge primary or claim another branch is fixed. Closed Issues remain recorded. Legacy Reflections\nare archived history, never automatically converted or used as current approval.\n",
      "name": "concorde-issues",
      "request_schema": {
        "$defs": {
          "concorde-issues-request": {
            "additionalProperties": false,
            "properties": {
              "action": {
                "enum": [
                  "list",
                  "show",
                  "report",
                  "solve",
                  "reopen"
                ]
              },
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "expected_revision": {
                "minLength": 1,
                "pattern": "^sha256:[0-9a-f]{64}$",
                "type": "string"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "issue_id": {
                "minLength": 1,
                "pattern": "I-[0-9a-f]{32}",
                "type": "string"
              },
              "note": {
                "minLength": 1,
                "type": "string"
              },
              "report": {
                "additionalProperties": false,
                "properties": {
                  "basis": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "description": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "evidence": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "description": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "path": {
                          "minLength": 1,
                          "type": "string"
                        }
                      },
                      "required": [
                        "path",
                        "description"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  },
                  "expected_revision": {
                    "minLength": 1,
                    "pattern": "^sha256:[0-9a-f]{64}$",
                    "type": "string"
                  },
                  "impact": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "issue_id": {
                    "minLength": 1,
                    "pattern": "I-[0-9a-f]{32}",
                    "type": "string"
                  },
                  "owner_target_id": {
                    "anyOf": [
                      {
                        "minLength": 1,
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ]
                  },
                  "report_key": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "subtype": {
                    "anyOf": [
                      {
                        "enum": [
                          "implementation-spec-mismatch",
                          "spec-conflict",
                          "missing-contract"
                        ]
                      },
                      {
                        "type": "null"
                      }
                    ]
                  },
                  "title": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "type": {
                    "enum": [
                      "bug",
                      "gap",
                      "limitation"
                    ]
                  }
                },
                "required": [
                  "report_key",
                  "type",
                  "subtype",
                  "title",
                  "description",
                  "impact",
                  "basis",
                  "owner_target_id",
                  "evidence"
                ],
                "type": "object"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "action"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-issues-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-issues-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 1
    },
    {
      "description": "Operation: plan work for the explicitly selected Module.",
      "guidance": "# concorde-plan\n\nInvoke this operation to plan work for the explicitly selected Module. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\n\nAssesses the complete Spec before accepting a nonempty revision-bound plan. Does not read implementation contents. Missing contracts return to the calling agent for direct Spec and paired metadata edits.\n\nThe calling agent chooses whether and when to invoke other Operations. Report invalid or stale\ninputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews\nthe grant without launching a worker. Execution retains bounded context and authority.\n",
      "name": "concorde-plan",
      "request_schema": {
        "$defs": {
          "concorde-plan-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-plan-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-plan-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 1
    },
    {
      "description": "Operation: independently review a Module's complete Spec, including terminology semantic consistency, and return scoped read-only findings.",
      "guidance": "# concorde-spec-review\n\nInvoke this operation to review the selected Spec, including terminology semantic consistency. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nThe request requires target_id and task. The calling agent selects the Module explicitly;\noptional focus_id must name its scenario. Constraints and a current-worktree change_id may be\nsupplied. There is no implicit routing or review_mode selector. The host deterministically checks\nthe target and freezes its complete context before starting a fresh read-only reviewer.\n\nReview runs in the current worktree without creating a development change or requiring a preexisting\nIssue. It reads the complete selected Module contract, including owned and directly referenced\nreading and metadata, but no implementation. It checks every imported terminology restatement in\nthat admitted collection against its direct canonical definition for semantic consistency; wording\nneed not match. Report coverage and unresolved comparisons rather than assuming consistency.\nReviewers have no write, network or credential grants. The host persists review reports separately\nfrom reviewer authority.\n\nA managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.\nDo not claim this compares against another branch or a merge base. Report the returned review\ncoverage, Issue judgments and limitations, preserving incomplete or failed outcomes. Findings do\nnot authorize repairs. describe-policy previews grants without launching agents or persisting\nreview results. A separate review intent cannot replace another task's required lifecycle review.\n",
      "name": "concorde-spec-review",
      "request_schema": {
        "$defs": {
          "concorde-spec-review-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-spec-review-request"
          },
          "schema_version": {
            "const": 2,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-spec-review-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 2
    },
    {
      "description": "Operation: derive implementation acceptance tasks from the current accepted plan.",
      "guidance": "# concorde-tasks\n\nInvoke this operation to derive implementation acceptance tasks from the current accepted plan. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\n\nRequires the managed change and current accepted plan for the same intent. Returns new incomplete tasks, preserving prior task identities in history. Optional repair_task_scope binds the exact incomplete task-list digest; optional repair_review names a current blocking code-review ArtifactRef for this same intent. Neither field bypasses currentness or review gates.\n\nThe calling agent chooses whether and when to invoke other Operations. Report invalid or stale\ninputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews\nthe grant without launching a worker. Execution retains bounded context and authority.\n",
      "name": "concorde-tasks",
      "request_schema": {
        "$defs": {
          "concorde-tasks-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "repair_review": {
                "additionalProperties": false,
                "properties": {
                  "digest": {
                    "minLength": 1,
                    "pattern": "^sha256:[0-9a-f]{64}$",
                    "type": "string"
                  },
                  "id": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "path": {
                    "minLength": 1,
                    "type": "string"
                  }
                },
                "required": [
                  "id",
                  "path",
                  "digest"
                ],
                "type": "object"
              },
              "repair_task_scope": {
                "additionalProperties": false,
                "properties": {
                  "tasks_digest": {
                    "minLength": 1,
                    "pattern": "^sha256:[0-9a-f]{64}$",
                    "type": "string"
                  }
                },
                "required": [
                  "tasks_digest"
                ],
                "type": "object"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-tasks-request"
          },
          "schema_version": {
            "const": 2,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-tasks-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 2
    },
    {
      "description": "Operation: run deterministic Spec and configured code checks and record readiness for the current candidate.",
      "guidance": "# concorde-validate\n\nInvoke this operation to validate. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\nThis is a deterministic lifecycle operation: it runs no agent cognition and selects no context.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nUse the supplied target identity; if it is ambiguous, ask the user to identify it instead of\nsearching other Specs.\nThe user-facing session coordinates needs and may delegate a complete task to one fresh task\nchild, or handle a simple consumer-project task directly. Task children never delegate tasks or\nmove worktrees. They may run several public Operations on the same change through delivery;\nbounded Operation workers still obey the actual harness's depth and permission limits.\n\nA mutating Operation requested from a consumer primary normally runs in a host-created candidate;\nan Operation already in an assigned candidate reuses it. The requesting session stays where it\nstarted and receives path, branch and stable change_id. Uncommitted primary edits are not copied.\nDurable status and runs belong only to the primary coordinator, not duplicate candidate archives.\nTask-authorized `.concorde` edits in the owned workspace are not forbidden by directory name;\npreserve task scope, truthful evidence and concurrency safety, and obey actual worker grants.\n\nFor Concorde source maintenance, the main creates a candidate and a fresh Skill-free maintenance\nchild with inherited/discovered catalogs disabled. After the writer checks, commits and stops,\na separate fresh sibling test child receives only exact candidate-built Skills and runtime\nprovenance. Neither forks old Skill bodies or delegates tasks. The tester never rewrites governing\nSkills; failures return to maintenance and then a new tester. Maintenance may finish through\nordinary Git with explicit merge authorization, without Concorde delivery. Skill metadata alone\nis not evidence of loading or execution. Never fall back to global or primary Skills.\n\nReport Spec gaps or blocked execution as returned. Non-implementation workers never receive\nimplementation code or raw test logs.\n\nValidation checks document-unit identity and ownership, the paired reading/metadata sources,\nPurpose/Usage/Design/Relationships reading structure, requirement and scenario syntax, local readable\nmeaning references, unique stable IDs and canonical identity links. Registry files equal the exact\nunion of entity metadata entries; file/directory kinds, pending markers, implementation exclusions,\nprovider sets and complementary interface bindings remain checked. A scoped Relationships diagram\nuses declared local entities and labeled edges, without needing to reproduce the whole inventory.\nMetadata-only edits affect complete-context identity and evidence just as reading edits do.\n\nTests declare verified scenario IDs in their own source. Unknown IDs and unreadable tests are errors;\nuncovered scenarios and tests outside their scenario owner's listing are warnings. Missing unmarked\nimplementation entries are errors; stale pending markers and unlisted files are warnings. Warnings\ndo not by themselves fail validation. No structural result proves reading completeness, semantic\ncompleteness or implementation conformance.\n",
      "name": "concorde-validate",
      "request_schema": {
        "$defs": {
          "concorde-validate-request": {
            "additionalProperties": false,
            "properties": {
              "change_id": {
                "minLength": 1,
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "focus_id": {
                "minLength": 1,
                "type": "string"
              },
              "run_checks": {
                "type": "boolean"
              },
              "target_id": {
                "minLength": 1,
                "type": "string"
              },
              "task": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-validate-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-validate-request"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "type": "object"
      },
      "request_version": 1
    }
  ],
  "schema_version": 1
};

export default concordeSession(
	fileURLToPath(new URL("../../../", import.meta.url)),
	CATALOG,
);
