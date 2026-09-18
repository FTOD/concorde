// Rendered by `python3 scripts/concorde.py build` from skills/, prompts/ and the
// operation contracts; do not edit. The Concorde session extension itself lives at
// pi/extensions/concorde-session.ts; this shim binds it to this project.
import { fileURLToPath } from "node:url";
import { concordeSession } from "../../pi/extensions/concorde-session.ts";
import type { SessionCatalog } from "../../pi/extensions/concorde-session.ts";

const CATALOG: SessionCatalog = {
  "explicit_request_only": true,
  "interpreters": [
    ".venv/bin/python",
    ".venv/Scripts/python.exe"
  ],
  "launcher": "scripts/run-operation.py",
  "operations": [
    {
      "description": "Operation: apply the Pi worker model selection (model, thinking level, timeout and per-worker overrides); with accept_protocol, rebind the project to the installed Protocol copy.",
      "guidance": "# concorde-configure\n\nInvoke this operation to configure. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\nThis is a deterministic lifecycle operation: it runs no agent cognition and selects no context.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nUse the supplied target identity; if it is ambiguous, ask the user to identify it instead of\nsearching other Specs.\nA mutating request from the primary worktree runs in a candidate worktree the host creates from\nthe committed base; this session stays where it is and receives that candidate's result, whose\nworkspace names the candidate's path, branch and change_id. Continue the same change from here\nwith that change_id. Uncommitted primary edits are not carried into the candidate. Report Spec gaps\nor blocked execution as returned; do not work around the boundary. Non-implementation agents never\nreceive implementation code or raw test logs.\n",
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
      "description": "Operation: stage a verified change, remove its worktree, and explicitly merge from the primary session.",
      "guidance": "# concorde-deliver\n\nInvoke delivery from an agent whose initial working directory is either the selected source\nworktree or the primary Git worktree. A third-worktree or nested invocation cannot deliver this\nchange. Keep the session and its loaded Skills bound to their original participant.\n\nconfiguration (null to load initialized host settings, or a matching concorde-operation-configuration@1),\nand input (concorde-deliver-request@1). Supply the selected change_id from the primary worktree's\n`.concorde/worktrees.json` inventory or its saved delivery receipt. Optional target/task metadata\ncannot replace change ownership. No domain flags or positional arguments are accepted.\n\nDefault delivery verifies the candidate and its integration with the current primary commit,\nconfirms every entity entry marked `pending`, an exact file or a directory prefix, that now exists on\ndisk and clears its marker as part of the delivered commit (an entry still missing stays pending and\nis reported), creates\n`concorde/delivered/<change_id>` without checking it out, and removes the source worktree\nand its local state. Each change has an independent delivery branch. The primary worktree's\nchecked-out branch, index and project files are unchanged. `keep_worktree:true` explicitly retains\nthe source; ownership of the requesting session does not retain it automatically. After removal,\nend the source session without further project work. Further work requires a fresh P10 session.\nManaged AGENTS.md/CLAUDE.md blocks and local control state never enter the delivered tree.\n\nOnly when the user explicitly requests the final primary-branch merge, invoke a separate request\nwith `merge_primary:true` and the delivered change_id from the primary worktree's owning session.\nA generic delivery request does not authorize this flag. At most one agent may own writes in the\nprimary worktree; other agents work in their own linked worktrees. The host holds the shared\nrepository lock for delivery state changes and the entire primary merge, rechecks the current\nintegration and rejects conflicts or failed checks before changing the primary branch. Preserve\nlocal edits; a dirty primary blocks final merging but does not block default branch delivery.\nDo not start another primary writer or perform manual Git delivery around the host.\n\nReceipts retain delivery and primary merge evidence separately, including which files were\nconfirmed and which remain pending. Retry failed cleanup without\nanother branch merge. Retry an already completed primary merge without merging twice. After source\nremoval, retry from the primary session using the receipt's change_id. Conflicts or failed checks\npreserve the candidate or delivered branch for repair in a new change worktree. Report the returned\nbranch, outcome, cleanup status and whether final primary merging remains pending faithfully.\n",
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
      "description": "Development loop: route one change, call specify-loop, then plan, task, implement, validate and review code to a ready candidate; specify=false skips authoring and run_reviews=false records explicit review skips.",
      "guidance": "# concorde-dev-loop\n\nInvoke this operation to run the development loop. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nNew task requests require task and may supply target_id/focus_id (a scenario ID) as routing hints;\nmain discovery selects the owning target before the bounded loop starts. Existing changes retain\ntheir bound target.\nOptional `specify` (default true) and `run_reviews` (default true) flags select the loop shape.\n`specify:false` skips Spec authoring for this pass, exactly like the former fast loop.\n`run_reviews:false` records an explicit skip for each review mode instead of running it. A review\nrequirement already recorded for this change cannot be disabled by a later `run_reviews:false`;\nevery skip and every required review remains visible in the change record.\n\nTo repair an existing incomplete task list that incorrectly requires later Host validation,\nreview or commit before implementation can finish, pass `repair_task_scope:{tasks_digest:...}`.\nThe digest is `sha256:` plus SHA-256 of the UTF-8 canonical JSON task list (sorted keys, compact\nseparators, ASCII escaping as in Python `json.dumps`). The Host binds that exact list, supplies only semantic phase\nfeedback and the admitted plan/tasks to a fresh task author, preserves history and then runs\nimplementation, validation and required reviews normally. It preserves software acceptance and\ndoes not edit the plan, complete tasks, grant permissions or skip checks. Replaying a consumed\ndigest resumes the replacement list; stale digests and unresolved gaps are rejected.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nMain may explicitly admit complete Module Specs for routing, but cannot read implementation files.\nIt returns one typed route for this operation; the host then starts a different target worker.\nA mutating request from the primary worktree runs in a candidate worktree the host creates from\nthe committed base; this session stays where it is and receives that candidate's result, whose\nworkspace names the candidate's path, branch and change_id. Continue the same change from here\nwith that change_id. Uncommitted primary edits are not carried into the candidate. Report Spec gaps\nor blocked execution as returned; do not work around the boundary. Non-implementation agents never\nreceive implementation code or raw test logs.\n\nThis loop ends at a verified `ready` candidate in the current change worktree. It never\ninvokes deliver. Partial progress and gaps remain in `.concorde/worktree.json` and resume under\nthe same worktree change. Delivery is a separate request from an agent whose initial working directory is either the\nsource change worktree or the destination primary worktree; report the participating paths and\nchange_id when the candidate is ready. Delivery creates an independent branch and removes the\ncandidate worktree by default. Only an explicit user request permits a separate final merge by\nthe primary worktree's sole writing agent; other agents must use linked worktrees.\n\nThe loop calls `concorde-specify-loop` for Spec authoring and review before planning. When enabled,\nit requires independent Spec review after authoring and before planning, then\nread-only code review after implementation/checks and before ready. A skipped review is recorded\nexplicitly rather than run. A review already required for this change cannot be disabled by a\nlater request. Required review failure, incomplete coverage and blocking findings stop advancement;\nadvisory findings remain in the review artifacts. Each mode and target uses a separate fresh\nsession. Changed inputs invalidate older conclusions. Necessary contract gaps persist in the existing\nchange state; repair the Spec and resume with a fresh context. No-finding review is not proof of\nsemantic completeness.\n",
      "name": "concorde-dev-loop",
      "request_schema": {
        "$defs": {
          "concorde-dev-loop-request": {
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
              "run_reviews": {
                "type": "boolean"
              },
              "specify": {
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
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-dev-loop-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-dev-loop-request"
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
      "guidance": "# concorde-init\n\nInvoke this operation to init. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\nThis is a deterministic lifecycle operation: it runs no agent cognition and selects no context.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nUse the supplied target identity; if it is ambiguous, ask the user to identify it instead of\nsearching other Specs.\nA mutating request from the primary worktree runs in a candidate worktree the host creates from\nthe committed base; this session stays where it is and receives that candidate's result, whose\nworkspace names the candidate's path, branch and change_id. Continue the same change from here\nwith that change_id. Uncommitted primary edits are not carried into the candidate. Report Spec gaps\nor blocked execution as returned; do not work around the boundary. Non-implementation agents never\nreceive implementation code or raw test logs.\n",
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
      "description": "Inspect, report, reopen or solve branch-local Issues; solving stops at a verified candidate without automatic delivery.",
      "guidance": "# concorde-issues\n\nInvoke this operation to manage or solve explicitly selected Issues. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nChoose action list, show, report, reopen or solve. Show, reopen and solve require one issue_id;\nexpected_revision optionally rejects a changed selection. Report requires target_id and a classified\nreport; an append also names its issue_id and expected_revision inside the report. Reopen requires\na note. Only solve starts development; other actions are current-worktree bookkeeping. An Issue is\nnot an implementation task, and reporting it neither stops a running agent nor approves a repair.\n\nSolve may use ordinary development, a fresh Spec repair, or Issue-specific read-only verification.\nIt can resolve, identify a duplicate or reject a mistaken report from evidence without mandatory\nhuman approval. Unresolved product/design choices are returned as needs-decision. Respect the host's\nbounded iteration limit and distinct execution failures. Do not retry by widening permissions.\n\nFrom the primary worktree the host copies the selected Issue's exact bytes, including an uncommitted\nreport, into the candidate worktree it creates, without copying unrelated edits, and solves there;\nthis session receives the candidate's result and continues the change with its change_id.\nA successful solve ends at ready with the disposition included in verification. It does not deliver,\nmerge primary or claim another branch is fixed. Closed Issues remain recorded. Legacy Reflections\nare archived history, never automatically converted or used as current approval.\n",
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
      "description": "Operation: answer questions, route work, and design or apply system topology from complete Module Specs.",
      "guidance": "# concorde-main\n\nThis is Concorde's public main entry. It replaces the former ask operation. Its internal discovery workers (answerer, router and\ntopology designer) start from the project's entry Module and may expand only registered Module\ncomplete document units and their explicit one-level references. Inclusion never expands a\nprovider's own references or transfers ownership. It understands the Module contract and never reads implementation files.\n\nAction `ask` (the default when action is omitted) answers directly from complete Spec contexts\nresolved by Python and granted to the answerer as read-only files beside an index. Each source\nis granted once, with explicit per-Module membership; additional contexts are loaded only on\nexplicit selection.\nAction `design-topology` returns a digest-bound architecture\nproposal without changing files. Action `accept-topology` explicitly accepts that design, launches\nprivate target-local Spec authors and stores the resulting exact application as a host artifact;\nonly its path and digest return to ambient cognition. After the developer reviews that artifact,\naction `apply-topology` accepts it and atomically applies or rolls back the registry/document set.\n\nAsk and design-topology requests require task and accept optional target_id/focus_id (a candidate\nscenario ID) routing hints and constraints. Accept-topology requires the exact topology_proposal returned by design. Apply-\ntopology requires only the exact application ArtifactRef returned by accept.\nThe hint never grants Spec access to a discovery worker. The development loop\n(`concorde-dev-loop`) accepts the same task, with optional target_id, focus_id, constraints, and\nchange_id, and uses main's discovery to select one mutation target; its internal\nstages are bound to one target by the loop and are never invoked directly.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nDiscovery expands complete Module collections only as needed and records the exact\ndocument-unit membership, source roles, owners and byte digests in every discovery identity.\nThe answerer can reason across all admitted complete contexts and answer without a reader or\nintermediate summaries. A mutation route selects a Module from admitted responsibilities; the fresh worker receives only its own\ncomplete Module context, including both reading and metadata members. A publisher's presentation\ndoes not trim that context or admit implementation files.\nTopology design receives exact registry metadata and explicitly admits affected Module contracts. Target authors' complete output\nis never returned through this operation; it stays in the ignored host application artifact. Report\nSpec gaps or blocked execution as returned and do not work around the boundary. Non-implementation\nagents never receive implementation code or raw test logs.\n\nA topology proposal that adds, removes or changes a component's `uses` relationship must\nalso task every retained affected Module to reconcile its dependency metadata and local readable collaboration agreement.\nThe Module task carries the exact ID, local responsibility, selection condition and relied-upon\npromises. Candidate overlay validation rejects a registry edge without that self-contained Module\nrouting view.\n\nA topology proposal that adds, removes or moves an entry in a Module's implementation `files` list\nlikewise tasks that Module -- and every other Module whose entries already bind the same file -- to\nreconcile its entity declarations, since the registry `files` must equal the sorted union of a\nModule's entity entries, entry for entry. An entry is an exact file or a directory prefix ending in\n`/` that binds every regular file below it; a directory prefix suits a directory one Module alone\nowns, a file bound by several Modules stays an exact entry in each of them, and a listed directory\nmust not contain a registered Spec document.\n\nEvery document unit has one stable ID and one owner, with reading Markdown and paired metadata.\nModule registration alone declares context references. A shared definition is authored once by its\nsole owner; consumers receive it read-only and contribute separate compatibility evidence, never\nduplicate replacement bytes. Topology authors return both source members of every candidate-owned\nunit in registration order. Reference and ownership changes reconcile all affected contexts.\n\nEvery main invocation receives host-supplied workspace metadata. In the primary worktree it lists\nall live linked worktrees and their basic change status, so ongoing work is visible without loading\nother worktrees' Spec or implementation bodies. In a secondary worktree it identifies the current\ncandidate, its phase/status, and the primary worktree. The primary inventory is\n`.concorde/worktrees.json`; secondary lifecycle state is `.concorde/worktree.json`.\nA worktree is a mutable candidate until its exact version is verified and delivered. Do not treat\npartial drafts as the accepted primary revision. Read-only awareness does not authorize cross-worktree\nreads or a continuation of the same agent session in another checkout.\n\n`concorde-deliver` may be requested from either the selected source or destination worktree.\nReport the selected change_id and both participants; a third worktree cannot deliver that change.\nDefault delivery creates `concorde/delivered/<change_id>` and removes the source worktree unless\nkeep_worktree:true is explicitly requested. End the source session after removal. The primary\nbranch stays unchanged until the user explicitly requests a separate merge_primary:true delivery\nfrom the primary worktree's sole writing agent. All other agents develop in linked worktrees;\nthe host serializes shared lifecycle writes and final primary merges with the repository lock.\n",
      "name": "concorde-main",
      "request_schema": {
        "$defs": {
          "concorde-main-request": {
            "additionalProperties": false,
            "properties": {
              "action": {
                "enum": [
                  "ask",
                  "design-topology",
                  "accept-topology",
                  "apply-topology"
                ]
              },
              "application": {
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
              },
              "topology_proposal": {
                "additionalProperties": false,
                "properties": {
                  "data": {
                    "$ref": "#/$defs/concorde-topology-proposal"
                  },
                  "schema_version": {
                    "const": 1,
                    "type": "integer"
                  },
                  "type_id": {
                    "const": "concorde-topology-proposal"
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
            "required": [],
            "type": "object"
          },
          "concorde-topology-design": {
            "additionalProperties": false,
            "properties": {
              "acceptance": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "minItems": 1,
                "type": "array"
              },
              "migration_constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "registry": {
                "additionalProperties": false,
                "properties": {
                  "checks": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "argv": {
                          "items": {
                            "minLength": 1,
                            "type": "string"
                          },
                          "minItems": 1,
                          "type": "array"
                        },
                        "id": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "inputs": {
                          "items": {
                            "minLength": 1,
                            "type": "string"
                          },
                          "type": "array",
                          "uniqueItems": true
                        },
                        "target_id": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "timeout_seconds": {
                          "maximum": 3600,
                          "minimum": 1,
                          "type": "integer"
                        }
                      },
                      "required": [
                        "id",
                        "target_id",
                        "argv",
                        "timeout_seconds"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  },
                  "entry_target": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "project_id": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "schema_version": {
                    "const": 5
                  },
                  "targets": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "checks": {
                          "items": {
                            "minLength": 1,
                            "type": "string"
                          },
                          "type": "array",
                          "uniqueItems": true
                        },
                        "documents": {
                          "items": {
                            "minLength": 1,
                            "type": "string"
                          },
                          "minItems": 1,
                          "type": "array",
                          "uniqueItems": true
                        },
                        "files": {
                          "items": {
                            "minLength": 1,
                            "pattern": "^[^/](?:[^/]*/)*[^/]*$",
                            "type": "string"
                          },
                          "type": "array",
                          "uniqueItems": true
                        },
                        "id": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "kind": {
                          "const": "module"
                        },
                        "parent": {
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
                        "references": {
                          "items": {
                            "anyOf": [
                              {
                                "additionalProperties": false,
                                "properties": {
                                  "id": {
                                    "minLength": 1,
                                    "type": "string"
                                  },
                                  "kind": {
                                    "enum": [
                                      "module",
                                      "document"
                                    ]
                                  }
                                },
                                "required": [
                                  "kind",
                                  "id"
                                ],
                                "type": "object"
                              },
                              {
                                "additionalProperties": false,
                                "properties": {
                                  "kind": {
                                    "const": "external"
                                  },
                                  "path": {
                                    "minLength": 1,
                                    "pattern": "^[^/](?:[^/]*/)*[^/]*$",
                                    "type": "string"
                                  }
                                },
                                "required": [
                                  "kind",
                                  "path"
                                ],
                                "type": "object"
                              }
                            ]
                          },
                          "type": "array",
                          "uniqueItems": true
                        },
                        "title": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "uses": {
                          "items": {
                            "minLength": 1,
                            "type": "string"
                          },
                          "type": "array",
                          "uniqueItems": true
                        }
                      },
                      "required": [
                        "id",
                        "kind",
                        "title",
                        "documents",
                        "references",
                        "parent",
                        "uses",
                        "files",
                        "checks"
                      ],
                      "type": "object"
                    },
                    "minItems": 1,
                    "type": "array"
                  }
                },
                "required": [
                  "schema_version",
                  "project_id",
                  "entry_target",
                  "targets",
                  "checks"
                ],
                "type": "object"
              },
              "spec_tasks": {
                "items": {
                  "additionalProperties": false,
                  "properties": {
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
                },
                "minItems": 1,
                "type": "array"
              },
              "summary": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "summary",
              "registry",
              "spec_tasks",
              "migration_constraints",
              "acceptance"
            ],
            "type": "object"
          },
          "concorde-topology-proposal": {
            "additionalProperties": false,
            "properties": {
              "base_registry_digest": {
                "minLength": 1,
                "pattern": "^sha256:[0-9a-f]{64}$",
                "type": "string"
              },
              "constraints": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": "array"
              },
              "context_id": {
                "minLength": 1,
                "pattern": "^sha256:[0-9a-f]{64}$",
                "type": "string"
              },
              "design": {
                "additionalProperties": false,
                "properties": {
                  "data": {
                    "$ref": "#/$defs/concorde-topology-design"
                  },
                  "schema_version": {
                    "const": 1,
                    "type": "integer"
                  },
                  "type_id": {
                    "const": "concorde-topology-design"
                  }
                },
                "required": [
                  "type_id",
                  "schema_version",
                  "data"
                ],
                "type": "object"
              },
              "discovered_targets": {
                "items": {
                  "minLength": 1,
                  "type": "string"
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": true
              },
              "focus_hint": {
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
              "proposal_id": {
                "minLength": 1,
                "pattern": "^sha256:[0-9a-f]{64}$",
                "type": "string"
              },
              "protocol_binding": {
                "additionalProperties": false,
                "properties": {
                  "digest": {
                    "minLength": 1,
                    "pattern": "^sha256:[0-9a-f]{64}$",
                    "type": "string"
                  },
                  "version": {
                    "minLength": 1,
                    "type": "string"
                  }
                },
                "required": [
                  "version",
                  "digest"
                ],
                "type": "object"
              },
              "target_hint": {
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
              "task": {
                "minLength": 1,
                "type": "string"
              },
              "workspace": {
                "additionalProperties": false,
                "properties": {
                  "active_worktrees": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "branch": {
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
                        "change_id": {
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
                        "head": {
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
                        "locked": {
                          "type": "boolean"
                        },
                        "managed": {
                          "type": "boolean"
                        },
                        "outcome": {
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
                        "path": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "phase": {
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
                        "status": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "target_id": {
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
                        "task": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "path",
                        "branch",
                        "head",
                        "managed",
                        "locked",
                        "change_id",
                        "target_id",
                        "task",
                        "phase",
                        "status",
                        "outcome"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  },
                  "blockers": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "blocked_step": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "issue_id": {
                          "minLength": 1,
                          "pattern": "I-[0-9a-f]{32}",
                          "type": "string"
                        },
                        "path": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "report_id": {
                          "minLength": 1,
                          "pattern": "^sha256:[0-9a-f]{64}$",
                          "type": "string"
                        }
                      },
                      "required": [
                        "issue_id",
                        "report_id",
                        "path",
                        "blocked_step"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  },
                  "change_id": {
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
                  "components": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "implementation_status": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "outcome": {
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
                        "spec_status": {
                          "minLength": 1,
                          "type": "string"
                        },
                        "target_id": {
                          "minLength": 1,
                          "type": "string"
                        }
                      },
                      "required": [
                        "target_id",
                        "spec_status",
                        "implementation_status",
                        "outcome"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  },
                  "current_branch": {
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
                  "current_worktree": {
                    "minLength": 1,
                    "type": "string"
                  },
                  "kind": {
                    "enum": [
                      "primary",
                      "change",
                      "unversioned"
                    ]
                  },
                  "outcome": {
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
                  "phase": {
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
                  "primary_branch": {
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
                  "primary_worktree": {
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
                  "status": {
                    "anyOf": [
                      {
                        "minLength": 1,
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ]
                  }
                },
                "required": [
                  "kind",
                  "current_worktree",
                  "current_branch",
                  "primary_worktree",
                  "primary_branch",
                  "change_id",
                  "phase",
                  "status",
                  "outcome",
                  "blockers",
                  "components",
                  "active_worktrees"
                ],
                "type": "object"
              }
            },
            "required": [
              "proposal_id",
              "base_registry_digest",
              "protocol_binding",
              "context_id",
              "discovered_targets",
              "task",
              "constraints",
              "target_hint",
              "focus_hint",
              "design",
              "workspace"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-main-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-main-request"
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
      "description": "Operation: route a standalone Spec review, code review or source diagnosis to its owning Module and return scoped, read-only findings.",
      "guidance": "# concorde-review\n\nInvoke this operation to review the selected Spec or implementation. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nThe request requires task and review_mode (spec or code). Use code for code review or source\ndiagnosis, and spec for contract review. A new task may supply target_id and focus_id (a scenario\nID) as routing hints, plus constraints. The router selects the owning Module. When resuming\na bound review with change_id, supply its target_id and current-worktree change_id.\nNo positional task arguments or domain flags are accepted.\n\nMain may explicitly admit complete Module Specs for routing, but cannot read implementation files.\nIt returns one typed route for this operation; the host then starts a fresh read-only reviewer.\n\nReview runs in the current worktree without creating a development change or requiring a\npreexisting Issue. Spec review reads the complete selected Module contract; code review also reads only\nits admitted implementation files and scoped changes. Reviewers have no write, network or\ncredential grants. The host persists review reports separately from reviewer authority.\n\nA managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.\nDo not claim this compares against another branch or a merge base. Report the returned review\ncoverage, Issue judgments and limitations, preserving incomplete or failed outcomes. Findings do\nnot authorize repairs. describe-policy previews grants without launching agents or persisting\nreview results. A separate review intent cannot replace another task's required lifecycle review.\n",
      "name": "concorde-review",
      "request_schema": {
        "$defs": {
          "concorde-review-request": {
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
              "review_mode": {
                "enum": [
                  "spec",
                  "code"
                ]
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
              "task",
              "review_mode"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-review-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-review-request"
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
      "description": "Spec loop: route one change, author or revise its Spec, then independently review it; stop before planning and implementation.",
      "guidance": "# concorde-specify-loop\n\nInvoke this operation to run the Spec loop. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\n\nNew task requests require task and may supply target_id/focus_id (a scenario ID) as routing hints;\nmain discovery selects the owning target before the bounded loop starts. Existing changes retain\ntheir bound target.\nOptional `specify` (default true) and `run_reviews` (default true) select authoring and Spec review.\n`specify:false` reviews the existing Spec without authoring. `run_reviews:false` records an explicit\nSpec review skip unless that review was already required for this change. A later request cannot\ncancel a recorded requirement. This loop does not require or skip code review.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nMain may explicitly admit complete Module Specs for routing, but cannot read implementation files.\nIt returns one typed route for this operation; the host then starts a different target worker.\nA mutating request from the primary worktree runs in a candidate worktree the host creates from\nthe committed base; this session stays where it is and receives that candidate's result, whose\nworkspace names the candidate's path, branch and change_id. Continue the same change from here\nwith that change_id. Uncommitted primary edits are not carried into the candidate. Report Spec gaps\nor blocked execution as returned; do not work around the boundary. Non-implementation agents never\nreceive implementation code or raw test logs.\n\nThis loop authors or revises the selected Module's owned Spec documents, then independently reviews\nthe complete contract and every affected consumer in separate fresh contexts. It returns `completed`\nwith artifact references after the selected Spec stages succeed. Explicit review skips remain\nvisible; completion never claims semantic completeness or implementation readiness.\n\nBlocking findings, incomplete coverage and necessary contract gaps stop advancement. Preserve the\ncandidate, repair the missing contract and resume with fresh context. Accepted authoring and current\nreview evidence are retained for the same task. This loop does not plan, author implementation tasks,\nwrite code, run code checks, mark ready or deliver. To continue implementation, invoke\n`concorde-dev-loop` in the same change with the same task and constraints; it composes this loop and\nthen proceeds through planning, tasks, implementation, checks and code review.\n",
      "name": "concorde-specify-loop",
      "request_schema": {
        "$defs": {
          "concorde-specify-loop-request": {
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
              "run_reviews": {
                "type": "boolean"
              },
              "specify": {
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
              "task"
            ],
            "type": "object"
          }
        },
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": false,
        "properties": {
          "data": {
            "$ref": "#/$defs/concorde-specify-loop-request"
          },
          "schema_version": {
            "const": 1,
            "type": "integer"
          },
          "type_id": {
            "const": "concorde-specify-loop-request"
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
      "description": "Operation: run deterministic Spec and configured code checks and record readiness for the current candidate.",
      "guidance": "# concorde-validate\n\nInvoke this operation to validate. The host owns context\nresolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed\ninput; do not perform it directly in this ambient conversation or inspect additional project files.\nThis is a deterministic lifecycle operation: it runs no agent cognition and selects no context.\n\nTask requests select target_id and task, with optional focus_id (a scenario ID), constraints, and\nchange_id.\nInitialization uses its typed propose/apply request; use the published request schema.\nNo domain flags or positional task arguments are accepted. Configuration is never a context grant.\n\nUse the supplied target identity; if it is ambiguous, ask the user to identify it instead of\nsearching other Specs.\nA mutating request from the primary worktree runs in a candidate worktree the host creates from\nthe committed base; this session stays where it is and receives that candidate's result, whose\nworkspace names the candidate's path, branch and change_id. Continue the same change from here\nwith that change_id. Uncommitted primary edits are not carried into the candidate. Report Spec gaps\nor blocked execution as returned; do not work around the boundary. Non-implementation agents never\nreceive implementation code or raw test logs.\n\nValidation checks document-unit identity and ownership, the paired reading/metadata sources,\nPurpose/Usage/Design/Relationships reading structure, requirement and scenario syntax, local readable\nmeaning references, unique stable IDs and canonical identity links. Registry files equal the exact\nunion of entity metadata entries; file/directory kinds, pending markers, implementation exclusions,\nprovider sets and complementary interface bindings remain checked. A scoped Relationships diagram\nuses declared local entities and labeled edges, without needing to reproduce the whole inventory.\nMetadata-only edits affect complete-context identity and evidence just as reading edits do.\n\nTests declare verified scenario IDs in their own source. Unknown IDs and unreadable tests are errors;\nuncovered scenarios and tests outside their scenario owner's listing are warnings. Missing unmarked\nimplementation entries are errors; stale pending markers and unlisted files are warnings. Warnings\ndo not by themselves fail validation. No structural result proves reading completeness, semantic\ncompleteness or implementation conformance.\n",
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
	fileURLToPath(new URL("../../", import.meta.url)),
	CATALOG,
);
