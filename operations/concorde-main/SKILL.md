---
name: concorde-main
description: "Global entry: answer questions, route work, and design or apply system topology from main-visible Domain and Service Specs."
exposure: public
operation: operation.py
capabilities: ["concorde-coordinator", "concorde-reader", "concorde-spec-author"]
---

# concorde-main

This is Concorde's public main entry. It replaces the former ask Operation. The internal coordinator
starts from the project's entry Domain or Service and may expand only registered Domain and Service
main-visible Target Spec and Shared Specs. Shared membership never expands another entity's remaining
documents. It understands every global kind definition but cannot directly expand a Module target or read
implementation code.

Action `ask` (the default when action is omitted) routes one or more fresh target readers and then
synthesizes only their typed results. Action `design-topology` returns a digest-bound architecture
proposal without changing files. Action `accept-topology` explicitly accepts that design, launches
private target-local Spec authors and stores the resulting exact application as a host artifact;
only its path and digest return to ambient cognition. After the maintainer reviews that artifact,
action `apply-topology` accepts it and atomically applies or rolls back the registry/document set.

Send one concorde-operation-invocation@2 JSON object on stdin to `{OPERATION}`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-main", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-main-request@1).
Ask and design-topology requests require task and accept optional target_id/focus_id routing hints
and constraints. Accept-topology requires the exact topology_proposal returned by design. Apply-
topology requires only the exact application ArtifactRef returned by accept.
The hint never grants Spec access to the coordinator. The global development loops
(`concorde-standard-dev-loop`, `concorde-fast-loop`) accept the same task, with optional target_id,
focus_id, constraints, and change_id, and route through main exactly like this Operation's own ask
action; their internal stages are bound to one target by the loop and are never invoked directly.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

The coordinator expands main-visible Domain/Service documents only as needed and records the exact
Target Spec/Shared Specs membership and digests in every discovery identity. A Module may be selected
from visible responsibilities, but its remaining Spec is visible only to the fresh target reader.
Topology design receives exact registry metadata but does not expand Module targets. Target authors' complete output
is never returned through this Operation; it stays in the ignored host application artifact. Report
Spec gaps or blocked execution as returned and do not work around the boundary. Non-implementation
agents never receive implementation code or raw test logs.

A topology proposal that adds, removes or changes a component's `participates_in` relationship must
also task every retained affected Domain to reconcile its local `concorde-participants` declaration.
The Domain task carries the exact ID, kind, local responsibility, selection condition and relied-upon
promises. Candidate overlay validation rejects a registry edge without that self-contained Domain
routing view.

Every physical Spec document declares stable ID, exact target references and main visibility.
Changing document references tasks every retained current/candidate target. Shared truth has no
unique owner: ordinary single-target authoring cannot change it, and topology preparation accepts a
replacement only when every candidate referencing target author returns identical exact bytes.


Every main invocation receives host-supplied workspace metadata. In the primary worktree it lists
all live linked worktrees and their basic change status, so ongoing work is visible without loading
other worktrees' Spec or implementation bodies. In a secondary worktree it identifies the current
candidate, its phase/status, and the primary worktree. The primary inventory is
`.concorde/worktrees.json`; secondary lifecycle state is `.concorde/worktree.json`.
A worktree is a mutable candidate until its exact version is verified and delivered. Do not treat
partial drafts as the accepted primary revision. Read-only awareness does not authorize cross-worktree
reads or a continuation of the same agent session in another checkout.

`concorde-deliver` may be requested from either the selected source or destination worktree.
Report the selected change_id and both participants; a third worktree cannot deliver that change.
The source is retained when it owns the active session or keep_worktree:true is requested.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-main-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-main-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-main-request": {
      "type": "object",
      "properties": {
        "action": {
          "enum": [
            "ask",
            "design-topology",
            "accept-topology",
            "apply-topology"
          ]
        },
        "task": {
          "type": "string",
          "minLength": 1
        },
        "target_id": {
          "type": "string",
          "minLength": 1
        },
        "focus_id": {
          "type": "string",
          "minLength": 1
        },
        "constraints": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "topology_proposal": {
          "type": "object",
          "properties": {
            "type_id": {
              "const": "concorde-topology-proposal"
            },
            "schema_version": {
              "type": "integer",
              "const": 1
            },
            "data": {
              "$ref": "#/$defs/concorde-topology-proposal"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        },
        "application": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "minLength": 1
            },
            "path": {
              "type": "string",
              "minLength": 1
            },
            "digest": {
              "type": "string",
              "minLength": 1,
              "pattern": "^sha256:[0-9a-f]{64}$"
            }
          },
          "required": [
            "id",
            "path",
            "digest"
          ],
          "additionalProperties": false
        }
      },
      "required": [],
      "additionalProperties": false
    },
    "concorde-topology-proposal": {
      "type": "object",
      "properties": {
        "proposal_id": {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        "base_registry_digest": {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        "protocol_binding": {
          "type": "object",
          "properties": {
            "version": {
              "type": "string",
              "minLength": 1
            },
            "digest": {
              "type": "string",
              "minLength": 1,
              "pattern": "^sha256:[0-9a-f]{64}$"
            }
          },
          "required": [
            "version",
            "digest"
          ],
          "additionalProperties": false
        },
        "context_id": {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        "discovered_targets": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          },
          "uniqueItems": true,
          "minItems": 1
        },
        "task": {
          "type": "string",
          "minLength": 1
        },
        "constraints": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "target_hint": {
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
        "focus_hint": {
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
        "design": {
          "type": "object",
          "properties": {
            "type_id": {
              "const": "concorde-topology-design"
            },
            "schema_version": {
              "type": "integer",
              "const": 1
            },
            "data": {
              "$ref": "#/$defs/concorde-topology-design"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        },
        "workspace": {
          "type": "object",
          "properties": {
            "kind": {
              "enum": [
                "primary",
                "change",
                "unversioned"
              ]
            },
            "current_worktree": {
              "type": "string",
              "minLength": 1
            },
            "current_branch": {
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
            "primary_worktree": {
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
            "primary_branch": {
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
            "change_id": {
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
            "phase": {
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
            "status": {
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
            "outcome": {
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
            "gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "question": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_step": {
                    "type": "string",
                    "minLength": 1
                  },
                  "needed_contract": {
                    "type": "string",
                    "minLength": 1
                  },
                  "target_id": {
                    "type": "string",
                    "minLength": 1
                  },
                  "context_id": {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^sha256:[0-9a-f]{64}$"
                  }
                },
                "required": [
                  "question",
                  "blocked_step",
                  "needed_contract"
                ],
                "additionalProperties": false
              }
            },
            "components": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "target_id": {
                    "type": "string",
                    "minLength": 1
                  },
                  "spec_status": {
                    "type": "string",
                    "minLength": 1
                  },
                  "implementation_status": {
                    "type": "string",
                    "minLength": 1
                  },
                  "outcome": {
                    "anyOf": [
                      {
                        "type": "string",
                        "minLength": 1
                      },
                      {
                        "type": "null"
                      }
                    ]
                  }
                },
                "required": [
                  "target_id",
                  "spec_status",
                  "implementation_status",
                  "outcome"
                ],
                "additionalProperties": false
              }
            },
            "active_worktrees": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "minLength": 1
                  },
                  "branch": {
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
                  "head": {
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
                  "managed": {
                    "type": "boolean"
                  },
                  "locked": {
                    "type": "boolean"
                  },
                  "change_id": {
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
                  "target_id": {
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
                  "task": {
                    "type": "string"
                  },
                  "phase": {
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
                  "status": {
                    "type": "string",
                    "minLength": 1
                  },
                  "outcome": {
                    "anyOf": [
                      {
                        "type": "string",
                        "minLength": 1
                      },
                      {
                        "type": "null"
                      }
                    ]
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
                "additionalProperties": false
              }
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
            "gaps",
            "components",
            "active_worktrees"
          ],
          "additionalProperties": false
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
      "additionalProperties": false
    },
    "concorde-topology-design": {
      "type": "object",
      "properties": {
        "summary": {
          "type": "string",
          "minLength": 1
        },
        "registry": {
          "type": "object",
          "properties": {
            "schema_version": {
              "const": 1
            },
            "project_id": {
              "type": "string",
              "minLength": 1
            },
            "entry_target": {
              "type": "string",
              "minLength": 1
            },
            "targets": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "id": {
                    "type": "string",
                    "minLength": 1
                  },
                  "kind": {
                    "enum": [
                      "domain",
                      "service",
                      "module"
                    ]
                  },
                  "title": {
                    "type": "string",
                    "minLength": 1
                  },
                  "documents": {
                    "type": "array",
                    "items": {
                      "type": "string",
                      "minLength": 1
                    },
                    "uniqueItems": true,
                    "minItems": 1
                  },
                  "scope_parent": {
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
                  "component_parent": {
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
                  "participates_in": {
                    "type": "array",
                    "items": {
                      "type": "string",
                      "minLength": 1
                    },
                    "uniqueItems": true
                  },
                  "implementation": {
                    "type": "array",
                    "items": {
                      "type": "string",
                      "minLength": 1
                    },
                    "uniqueItems": true
                  },
                  "features": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "id": {
                          "type": "string",
                          "minLength": 1
                        },
                        "title": {
                          "type": "string",
                          "minLength": 1
                        },
                        "document": {
                          "type": "string",
                          "minLength": 1
                        }
                      },
                      "required": [
                        "id",
                        "title",
                        "document"
                      ],
                      "additionalProperties": false
                    }
                  },
                  "apis": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "id": {
                          "type": "string",
                          "minLength": 1
                        },
                        "title": {
                          "type": "string",
                          "minLength": 1
                        },
                        "document": {
                          "type": "string",
                          "minLength": 1
                        }
                      },
                      "required": [
                        "id",
                        "title",
                        "document"
                      ],
                      "additionalProperties": false
                    }
                  },
                  "checks": {
                    "type": "array",
                    "items": {
                      "type": "string",
                      "minLength": 1
                    },
                    "uniqueItems": true
                  },
                  "diagrams": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "source": {
                          "type": "string",
                          "minLength": 1
                        },
                        "kind": {
                          "type": "string",
                          "minLength": 1
                        },
                        "title": {
                          "type": "string",
                          "minLength": 1
                        }
                      },
                      "required": [
                        "source",
                        "kind",
                        "title"
                      ],
                      "additionalProperties": false
                    }
                  }
                },
                "required": [
                  "id",
                  "kind",
                  "title",
                  "documents",
                  "scope_parent",
                  "component_parent",
                  "participates_in",
                  "implementation",
                  "features",
                  "apis",
                  "checks",
                  "diagrams"
                ],
                "additionalProperties": false
              },
              "minItems": 1
            },
            "checks": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "id": {
                    "type": "string",
                    "minLength": 1
                  },
                  "target_id": {
                    "type": "string",
                    "minLength": 1
                  },
                  "argv": {
                    "type": "array",
                    "items": {
                      "type": "string",
                      "minLength": 1
                    },
                    "minItems": 1
                  },
                  "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3600
                  },
                  "inputs": {
                    "type": "array",
                    "items": {
                      "type": "string",
                      "minLength": 1
                    },
                    "uniqueItems": true
                  }
                },
                "required": [
                  "id",
                  "target_id",
                  "argv",
                  "timeout_seconds"
                ],
                "additionalProperties": false
              }
            }
          },
          "required": [
            "schema_version",
            "project_id",
            "entry_target",
            "targets",
            "checks"
          ],
          "additionalProperties": false
        },
        "spec_tasks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "target_id": {
                "type": "string",
                "minLength": 1
              },
              "task": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "target_id",
              "task"
            ],
            "additionalProperties": false
          },
          "minItems": 1
        },
        "migration_constraints": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "acceptance": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          },
          "minItems": 1
        }
      },
      "required": [
        "summary",
        "registry",
        "spec_tasks",
        "migration_constraints",
        "acceptance"
      ],
      "additionalProperties": false
    }
  }
}
```
