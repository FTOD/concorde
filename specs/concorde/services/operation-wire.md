```concorde-document
{
  "id": "document.operation.wire",
  "targets": [
    "service.workflow-host"
  ],
  "main_visible": true
}
```

# Complete local Operation data contracts

The following schemas define data inside TypedValue {type_id,schema_version:1,data}. A named $ref refers to a data definition in this same collection. All objects reject additionalProperties unless explicitly stated; optional properties are those absent from required. No task arguments are inferred from filenames.


## concorde-agent-stage-context

```json
{
  "type": "object",
  "properties": {
    "snapshot": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-context-snapshot"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-context-snapshot"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
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
    "expected_artifacts": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "format": "project-path"
      }
    }
  },
  "required": [
    "snapshot",
    "change_id",
    "expected_artifacts"
  ],
  "additionalProperties": false
}
```


## concorde-agent-stage-result

```json
{
  "type": "object",
  "properties": {
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "outcome": {
      "enum": [
        "completed",
        "sufficient",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed"
      ]
    },
    "answer": {
      "type": "string"
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
    "documents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "plan": {
      "type": "string"
    },
    "tasks": {
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
          "description": {
            "type": "string",
            "minLength": 1
          },
          "acceptance": {
            "type": "string",
            "minLength": 1
          },
          "complete": {
            "type": "boolean"
          }
        },
        "required": [
          "id",
          "target_id",
          "description",
          "acceptance",
          "complete"
        ],
        "additionalProperties": false
      }
    },
    "reflection_findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "reflection_id": {
            "type": "string",
            "minLength": 1
          },
          "verified_commit": {
            "type": "string",
            "minLength": 1
          },
          "observed_state": {
            "enum": [
              "reproduced",
              "not-reproduced"
            ]
          },
          "verification": {
            "type": "string",
            "minLength": 1
          },
          "analysis": {
            "type": "string",
            "minLength": 1
          },
          "resolution": {
            "type": "string",
            "minLength": 1
          },
          "intervention_rationale": {
            "type": "string",
            "minLength": 1
          },
          "human_intervention": {
            "enum": [
              "required",
              "not-required"
            ]
          },
          "route": {
            "enum": [
              "fast-loop",
              "plan",
              "dismiss",
              "blocked"
            ]
          },
          "effort": {
            "enum": [
              "small",
              "medium",
              "large"
            ]
          },
          "files": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1,
              "format": "project-path"
            },
            "uniqueItems": true
          },
          "steps": {
            "type": "string",
            "minLength": 1
          },
          "validation": {
            "type": "string",
            "minLength": 1
          },
          "risks": {
            "type": "string",
            "minLength": 1
          },
          "protocol_change": {
            "type": "boolean"
          }
        },
        "required": [
          "reflection_id",
          "verified_commit",
          "observed_state",
          "verification",
          "analysis",
          "resolution",
          "intervention_rationale",
          "human_intervention",
          "route",
          "effort",
          "files",
          "steps",
          "validation",
          "risks",
          "protocol_change"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "context_id",
    "outcome",
    "answer",
    "gaps",
    "documents",
    "plan",
    "tasks"
  ],
  "additionalProperties": false
}
```


## concorde-analyze-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-analyze-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-checklist-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-checklist-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-clarify-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-clarify-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-configure-request

```json
{
  "type": "object",
  "properties": {
    "configuration": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-operation-configuration"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-operation-configuration"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "configuration"
  ],
  "additionalProperties": false
}
```


## concorde-configure-response

```json
{
  "type": "object",
  "properties": {
    "configuration": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-operation-configuration"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-operation-configuration"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    },
    "status": {
      "const": "applied"
    }
  },
  "required": [
    "configuration",
    "status"
  ],
  "additionalProperties": false
}
```


## concorde-constitution-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-constitution-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-context-manifest

```json
{
  "type": "object",
  "properties": {
    "schema_version": {
      "const": 1
    },
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "target_id": {
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
    "focus_id": {
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
      "type": "string",
      "minLength": 1
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
    "protocol": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "path",
          "digest"
        ],
        "additionalProperties": false
      }
    },
    "document_order": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "format": "project-path"
      },
      "uniqueItems": true
    },
    "target_spec": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true,
            "minItems": 1
          },
          "main_visible": {
            "type": "boolean"
          }
        },
        "required": [
          "document_id",
          "path",
          "digest",
          "targets",
          "main_visible"
        ],
        "additionalProperties": false
      }
    },
    "shared_specs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true,
            "minItems": 1
          },
          "main_visible": {
            "type": "boolean"
          }
        },
        "required": [
          "document_id",
          "path",
          "digest",
          "targets",
          "main_visible"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "schema_version",
    "context_id",
    "target_id",
    "kind",
    "focus_id",
    "phase",
    "protocol_binding",
    "protocol",
    "document_order",
    "target_spec",
    "shared_specs"
  ],
  "additionalProperties": false
}
```


## concorde-context-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    },
    "phase": {
      "enum": [
        "ask",
        "specify",
        "plan",
        "tasks",
        "implementation",
        "validate",
        "deliver",
        "context-solve"
      ]
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-context-response

```json
{
  "type": "object",
  "properties": {
    "manifest": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-context-manifest"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-context-manifest"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "manifest"
  ],
  "additionalProperties": false
}
```


## concorde-context-snapshot

```json
{
  "type": "object",
  "properties": {
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "schema_version": {
      "const": 1
    },
    "target_id": {
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
    "focus_id": {
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
      "type": "string",
      "minLength": 1
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
    "protocol": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "digest",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "document_order": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "format": "project-path"
      },
      "uniqueItems": true
    },
    "target_spec": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true,
            "minItems": 1
          },
          "main_visible": {
            "type": "boolean"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "document_id",
          "path",
          "digest",
          "targets",
          "main_visible",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "shared_specs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true,
            "minItems": 1
          },
          "main_visible": {
            "type": "boolean"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "document_id",
          "path",
          "digest",
          "targets",
          "main_visible",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "instructions": {
      "type": "string"
    },
    "stage_inputs": {
      "type": "array",
      "items": {
        "anyOf": [
          {
            "type": "object",
            "properties": {
              "type_id": {
                "const": "concorde-plan-artifact"
              },
              "schema_version": {
                "type": "integer",
                "const": 1
              },
              "data": {
                "$ref": "concorde-plan-artifact"
              }
            },
            "required": [
              "type_id",
              "schema_version",
              "data"
            ],
            "additionalProperties": false
          },
          {
            "type": "object",
            "properties": {
              "type_id": {
                "const": "concorde-implementation-task"
              },
              "schema_version": {
                "type": "integer",
                "const": 1
              },
              "data": {
                "$ref": "concorde-implementation-task"
              }
            },
            "required": [
              "type_id",
              "schema_version",
              "data"
            ],
            "additionalProperties": false
          },
          {
            "type": "object",
            "properties": {
              "type_id": {
                "const": "concorde-reflection-selection"
              },
              "schema_version": {
                "type": "integer",
                "const": 1
              },
              "data": {
                "$ref": "concorde-reflection-selection"
              }
            },
            "required": [
              "type_id",
              "schema_version",
              "data"
            ],
            "additionalProperties": false
          }
        ]
      }
    },
    "implementation_artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    }
  },
  "required": [
    "context_id",
    "schema_version",
    "target_id",
    "kind",
    "focus_id",
    "phase",
    "task",
    "constraints",
    "protocol_binding",
    "protocol",
    "document_order",
    "target_spec",
    "shared_specs",
    "instructions",
    "stage_inputs",
    "implementation_artifacts"
  ],
  "additionalProperties": false
}
```


## concorde-context-solve-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-context-solve-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-converge-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-converge-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-deliver-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-deliver-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-discovery-context

```json
{
  "type": "object",
  "properties": {
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "schema_version": {
      "const": 1
    },
    "operation": {
      "enum": [
        "concorde-analyze",
        "concorde-checklist",
        "concorde-clarify",
        "concorde-constitution",
        "concorde-context-solve",
        "concorde-fast-loop",
        "concorde-main",
        "concorde-plan",
        "concorde-specify",
        "concorde-standard-dev-loop"
      ]
    },
    "phase": {
      "enum": [
        "route",
        "synthesize"
      ]
    },
    "action": {
      "enum": [
        "route",
        "ask",
        "design-topology"
      ]
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
    "protocol": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "digest",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "topology": {
      "anyOf": [
        {
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
                      "minLength": 1,
                      "format": "project-path"
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
                      "minLength": 1,
                      "format": "project-path"
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
                          "minLength": 1,
                          "format": "project-path"
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
                          "minLength": 1,
                          "format": "project-path"
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
                          "minLength": 1,
                          "format": "project-path"
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
                      "minLength": 1,
                      "format": "project-path"
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
        {
          "type": "null"
        }
      ]
    },
    "targets": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "kind": {
            "enum": [
              "domain",
              "service"
            ]
          },
          "document_order": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1,
              "format": "project-path"
            },
            "uniqueItems": true
          },
          "target_spec": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "document_id": {
                  "type": "string",
                  "minLength": 1
                },
                "path": {
                  "type": "string",
                  "minLength": 1,
                  "format": "project-path"
                },
                "digest": {
                  "type": "string",
                  "minLength": 1,
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                "targets": {
                  "type": "array",
                  "items": {
                    "type": "string",
                    "minLength": 1
                  },
                  "uniqueItems": true,
                  "minItems": 1
                },
                "main_visible": {
                  "type": "boolean"
                },
                "content": {
                  "type": "string"
                }
              },
              "required": [
                "document_id",
                "path",
                "digest",
                "targets",
                "main_visible",
                "content"
              ],
              "additionalProperties": false
            }
          },
          "shared_specs": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "document_id": {
                  "type": "string",
                  "minLength": 1
                },
                "path": {
                  "type": "string",
                  "minLength": 1,
                  "format": "project-path"
                },
                "digest": {
                  "type": "string",
                  "minLength": 1,
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                "targets": {
                  "type": "array",
                  "items": {
                    "type": "string",
                    "minLength": 1
                  },
                  "uniqueItems": true,
                  "minItems": 1
                },
                "main_visible": {
                  "type": "boolean"
                },
                "content": {
                  "type": "string"
                }
              },
              "required": [
                "document_id",
                "path",
                "digest",
                "targets",
                "main_visible",
                "content"
              ],
              "additionalProperties": false
            }
          }
        },
        "required": [
          "target_id",
          "kind",
          "document_order",
          "target_spec",
          "shared_specs"
        ],
        "additionalProperties": false
      }
    },
    "instructions": {
      "type": "string"
    },
    "worker_results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type_id": {
            "const": "concorde-main-worker-result"
          },
          "schema_version": {
            "type": "integer",
            "const": 1
          },
          "data": {
            "$ref": "concorde-main-worker-result"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "context_id",
    "schema_version",
    "operation",
    "phase",
    "action",
    "task",
    "constraints",
    "target_hint",
    "focus_hint",
    "protocol_binding",
    "protocol",
    "topology",
    "targets",
    "instructions",
    "worker_results"
  ],
  "additionalProperties": false
}
```


## concorde-fast-loop-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-fast-loop-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-implement-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-implement-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-implementation-task

```json
{
  "type": "object",
  "properties": {
    "plan": {
      "type": "string",
      "minLength": 1
    },
    "tasks": {
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
          "description": {
            "type": "string",
            "minLength": 1
          },
          "acceptance": {
            "type": "string",
            "minLength": 1
          },
          "complete": {
            "type": "boolean"
          }
        },
        "required": [
          "id",
          "target_id",
          "description",
          "acceptance",
          "complete"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "plan",
    "tasks"
  ],
  "additionalProperties": false
}
```


## concorde-init-request

```json
{
  "type": "object",
  "properties": {
    "action": {
      "enum": [
        "propose",
        "apply"
      ]
    },
    "name": {
      "type": "string",
      "minLength": 1
    },
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "configuration": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-operation-configuration"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-operation-configuration"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    },
    "proposal": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-project-proposal"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-project-proposal"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "action"
  ],
  "additionalProperties": false
}
```


## concorde-init-response

```json
{
  "type": "object",
  "properties": {
    "status": {
      "enum": [
        "proposed",
        "applied"
      ]
    },
    "proposal": {
      "anyOf": [
        {
          "type": "object",
          "properties": {
            "type_id": {
              "const": "concorde-project-proposal"
            },
            "schema_version": {
              "type": "integer",
              "const": 1
            },
            "data": {
              "$ref": "concorde-project-proposal"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        },
        {
          "type": "null"
        }
      ]
    },
    "files": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "format": "project-path"
      }
    }
  },
  "required": [
    "status",
    "proposal",
    "files"
  ],
  "additionalProperties": false
}
```


## concorde-main-request

```json
{
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
          "$ref": "concorde-topology-proposal"
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
          "minLength": 1,
          "format": "project-path"
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
}
```


## concorde-main-response

```json
{
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
    "entry_target": {
      "type": "string",
      "minLength": 1
    },
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "expand",
        "routed",
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "topology_proposed",
        "topology_prepared",
        "topology_applied"
      ]
    },
    "answer": {
      "type": "string"
    },
    "discovered_targets": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "uniqueItems": true
    },
    "routes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "focus_id": {
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
            "type": "string",
            "minLength": 1
          },
          "constraints": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          }
        },
        "required": [
          "target_id",
          "focus_id",
          "task",
          "constraints"
        ],
        "additionalProperties": false
      }
    },
    "worker_results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type_id": {
            "const": "concorde-main-worker-result"
          },
          "schema_version": {
            "type": "integer",
            "const": 1
          },
          "data": {
            "$ref": "concorde-main-worker-result"
          }
        },
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "additionalProperties": false
      }
    },
    "topology_proposal": {
      "anyOf": [
        {
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
              "$ref": "concorde-topology-proposal"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        },
        {
          "type": "null"
        }
      ]
    },
    "application": {
      "anyOf": [
        {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "minLength": 1
            },
            "path": {
              "type": "string",
              "minLength": 1,
              "format": "project-path"
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
        },
        {
          "type": "null"
        }
      ]
    },
    "files": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "format": "project-path"
      },
      "uniqueItems": true
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
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "action",
    "entry_target",
    "context_id",
    "outcome",
    "answer",
    "discovered_targets",
    "routes",
    "worker_results",
    "topology_proposal",
    "application",
    "files",
    "gaps",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-main-stage-context

```json
{
  "type": "object",
  "properties": {
    "snapshot": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-discovery-context"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-discovery-context"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "snapshot"
  ],
  "additionalProperties": false
}
```


## concorde-main-stage-result

```json
{
  "type": "object",
  "properties": {
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "outcome": {
      "enum": [
        "expand",
        "routed",
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "topology_proposed",
        "topology_prepared",
        "topology_applied"
      ]
    },
    "answer": {
      "type": "string"
    },
    "expand_targets": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "uniqueItems": true
    },
    "routes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "focus_id": {
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
            "type": "string",
            "minLength": 1
          },
          "constraints": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          }
        },
        "required": [
          "target_id",
          "focus_id",
          "task",
          "constraints"
        ],
        "additionalProperties": false
      }
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
    "topology_design": {
      "anyOf": [
        {
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
              "$ref": "concorde-topology-design"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "context_id",
    "outcome",
    "answer",
    "expand_targets",
    "routes",
    "gaps",
    "topology_design"
  ],
  "additionalProperties": false
}
```


## concorde-main-worker-result

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed"
      ]
    },
    "answer": {
      "type": "string"
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
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "context_id",
    "outcome",
    "answer",
    "gaps"
  ],
  "additionalProperties": false
}
```


## concorde-migrate-request

```json
{
  "type": "object",
  "properties": {
    "action": {
      "enum": [
        "propose",
        "apply"
      ]
    },
    "registry_json": {
      "type": "string",
      "minLength": 1
    },
    "documents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "configuration": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-operation-configuration"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-operation-configuration"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    },
    "proposal": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-project-proposal"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-project-proposal"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "action"
  ],
  "additionalProperties": false
}
```


## concorde-migrate-response

```json
{
  "type": "object",
  "properties": {
    "status": {
      "enum": [
        "proposed",
        "applied"
      ]
    },
    "proposal": {
      "anyOf": [
        {
          "type": "object",
          "properties": {
            "type_id": {
              "const": "concorde-project-proposal"
            },
            "schema_version": {
              "type": "integer",
              "const": 1
            },
            "data": {
              "$ref": "concorde-project-proposal"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        },
        {
          "type": "null"
        }
      ]
    },
    "files": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "format": "project-path"
      }
    }
  },
  "required": [
    "status",
    "proposal",
    "files"
  ],
  "additionalProperties": false
}
```


## concorde-operation-configuration

```json
{
  "type": "object",
  "properties": {
    "integration": {
      "enum": [
        "codex",
        "claude"
      ]
    },
    "enforcement": {
      "enum": [
        "native",
        "outer"
      ]
    }
  },
  "required": [
    "integration",
    "enforcement"
  ],
  "additionalProperties": false
}
```


## concorde-plan-artifact

```json
{
  "type": "object",
  "properties": {
    "plan": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "plan"
  ],
  "additionalProperties": false
}
```


## concorde-plan-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-plan-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-project-proposal

```json
{
  "type": "object",
  "properties": {
    "action": {
      "enum": [
        "initialize",
        "migrate"
      ]
    },
    "base_digest": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "before_digest": {
            "anyOf": [
              {
                "type": "string",
                "minLength": 1,
                "pattern": "^sha256:[0-9a-f]{64}$"
              },
              {
                "type": "null"
              }
            ]
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "before_digest",
          "content"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "action",
    "base_digest",
    "files"
  ],
  "additionalProperties": false
}
```


## concorde-reflection-selection

```json
{
  "type": "object",
  "properties": {
    "head": {
      "type": "string",
      "minLength": 1
    },
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "content": {
            "type": "string",
            "minLength": 1
          }
        },
        "required": [
          "id",
          "path",
          "digest",
          "content"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "head",
    "records"
  ],
  "additionalProperties": false
}
```


## concorde-reflections-triage-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    },
    "action": {
      "enum": [
        "status",
        "investigate",
        "implement",
        "merge",
        "close"
      ]
    },
    "reflection_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "uniqueItems": true
    }
  },
  "required": [
    "target_id",
    "action",
    "reflection_ids"
  ],
  "additionalProperties": false
}
```


## concorde-reflections-triage-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "reflections": {
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
          "status": {
            "type": "string",
            "minLength": 1
          },
          "triage": {
            "type": "string",
            "minLength": 1
          },
          "bucket": {
            "type": "string",
            "minLength": 1
          },
          "plan_status": {
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
          "verification": {
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
          "id",
          "target_id",
          "status",
          "triage",
          "bucket",
          "plan_status",
          "verification"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-resolve-context-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    },
    "phase": {
      "enum": [
        "ask",
        "specify",
        "plan",
        "tasks",
        "implementation",
        "validate",
        "deliver",
        "context-solve"
      ]
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-resolve-context-response

```json
{
  "type": "object",
  "properties": {
    "manifest": {
      "type": "object",
      "properties": {
        "type_id": {
          "const": "concorde-context-manifest"
        },
        "schema_version": {
          "type": "integer",
          "const": 1
        },
        "data": {
          "$ref": "concorde-context-manifest"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "manifest"
  ],
  "additionalProperties": false
}
```


## concorde-specify-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-specify-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-standard-dev-loop-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-standard-dev-loop-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-tasks-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-tasks-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-taskstoissues-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-taskstoissues-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```


## concorde-topology-application

```json
{
  "type": "object",
  "properties": {
    "application_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
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
          "$ref": "concorde-topology-proposal"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
      ],
      "additionalProperties": false
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
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "before_digest": {
            "anyOf": [
              {
                "type": "string",
                "minLength": 1,
                "pattern": "^sha256:[0-9a-f]{64}$"
              },
              {
                "type": "null"
              }
            ]
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "before_digest",
          "content"
        ],
        "additionalProperties": false
      },
      "minItems": 1
    }
  },
  "required": [
    "application_id",
    "topology_proposal",
    "base_registry_digest",
    "protocol_binding",
    "files"
  ],
  "additionalProperties": false
}
```


## concorde-topology-author-context

```json
{
  "type": "object",
  "properties": {
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "base_registry_digest": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "target": {
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
            "minLength": 1,
            "format": "project-path"
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
            "minLength": 1,
            "format": "project-path"
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
                "minLength": 1,
                "format": "project-path"
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
                "minLength": 1,
                "format": "project-path"
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
                "minLength": 1,
                "format": "project-path"
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
    "task": {
      "type": "string",
      "minLength": 1
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
    "protocol": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "digest",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "candidate_document_references": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true,
            "minItems": 1
          }
        },
        "required": [
          "path",
          "targets"
        ],
        "additionalProperties": false
      }
    },
    "current_document_order": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "format": "project-path"
      },
      "uniqueItems": true
    },
    "target_spec": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true,
            "minItems": 1
          },
          "main_visible": {
            "type": "boolean"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "document_id",
          "path",
          "digest",
          "targets",
          "main_visible",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "shared_specs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true,
            "minItems": 1
          },
          "main_visible": {
            "type": "boolean"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "document_id",
          "path",
          "digest",
          "targets",
          "main_visible",
          "content"
        ],
        "additionalProperties": false
      }
    },
    "instructions": {
      "type": "string"
    }
  },
  "required": [
    "context_id",
    "base_registry_digest",
    "target",
    "task",
    "protocol_binding",
    "protocol",
    "candidate_document_references",
    "current_document_order",
    "target_spec",
    "shared_specs",
    "instructions"
  ],
  "additionalProperties": false
}
```


## concorde-topology-author-result

```json
{
  "type": "object",
  "properties": {
    "context_id": {
      "type": "string",
      "minLength": 1,
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed"
      ]
    },
    "answer": {
      "type": "string"
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
    "documents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "content": {
            "type": "string"
          }
        },
        "required": [
          "path",
          "content"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "context_id",
    "target_id",
    "outcome",
    "answer",
    "gaps",
    "documents"
  ],
  "additionalProperties": false
}
```


## concorde-topology-design

```json
{
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
                  "minLength": 1,
                  "format": "project-path"
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
                  "minLength": 1,
                  "format": "project-path"
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
                      "minLength": 1,
                      "format": "project-path"
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
                      "minLength": 1,
                      "format": "project-path"
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
                      "minLength": 1,
                      "format": "project-path"
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
                  "minLength": 1,
                  "format": "project-path"
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
```


## concorde-topology-proposal

```json
{
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
          "$ref": "concorde-topology-design"
        }
      },
      "required": [
        "type_id",
        "schema_version",
        "data"
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
    "design"
  ],
  "additionalProperties": false
}
```


## concorde-validate-request

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "task": {
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
    "change_id": {
      "type": "string",
      "minLength": 1
    },
    "run_checks": {
      "type": "boolean"
    }
  },
  "required": [
    "target_id",
    "task"
  ],
  "additionalProperties": false
}
```


## concorde-validate-response

```json
{
  "type": "object",
  "properties": {
    "target_id": {
      "type": "string",
      "minLength": 1
    },
    "focus_id": {
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
    "context_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "enum": [
        "completed",
        "spec_incomplete",
        "unsupported",
        "conflicting",
        "failed",
        "described",
        "delivered"
      ]
    },
    "answer": {
      "type": "string"
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
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
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "target_id": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "passed",
              "failed",
              "timeout"
            ]
          },
          "exit_code": {
            "type": "integer"
          },
          "source_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "log_digest": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        },
        "required": [
          "check_id",
          "target_id",
          "status",
          "exit_code",
          "source_digest",
          "log_digest"
        ],
        "additionalProperties": false
      }
    },
    "completed_operations": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "required": [
    "target_id",
    "focus_id",
    "change_id",
    "context_id",
    "outcome",
    "answer",
    "artifacts",
    "gaps",
    "checks",
    "completed_operations"
  ],
  "additionalProperties": false
}
```
