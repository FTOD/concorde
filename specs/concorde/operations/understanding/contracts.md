# Understanding contracts

The exact shape of what [Understanding](module.md) returns. The assessment is the `output` of the
Operation result. The worker proposes it as the Operation-specific part of its answer, and the host
passes it on once its checks have passed, with `goal` set to its own `--goal` argument.

## Assessment

```concorde-contract
{
  "id": "contract.understanding.assessment",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["goal", "modules", "sufficient", "gaps", "plan"],
    "properties": {
      "goal": {"type": "string", "minLength": 1},
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["module", "promises"],
          "properties": {
            "module": {"type": "string", "pattern": "^module\\."},
            "promises": {"type": "string", "minLength": 1}
          }
        }
      },
      "sufficient": {"type": "boolean"},
      "gaps": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["module", "document", "missing", "needed_for", "suggestion"],
          "properties": {
            "module": {"type": "string", "pattern": "^module\\."},
            "document": {"type": "string", "minLength": 1},
            "missing": {"type": "string", "minLength": 1},
            "needed_for": {"type": "string", "minLength": 1},
            "suggestion": {"type": "string", "minLength": 1}
          }
        }
      },
      "plan": {
        "anyOf": [
          {"type": "null"},
          {
            "type": "object",
            "additionalProperties": false,
            "required": ["summary", "modules", "pending", "steps", "decisions"],
            "properties": {
              "summary": {"type": "string", "minLength": 1},
              "modules": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "pattern": "^module\\."}
              },
              "pending": {
                "type": "array",
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["module", "realization", "path", "reason"],
                  "properties": {
                    "module": {"type": "string", "pattern": "^module\\."},
                    "realization": {"type": "string", "pattern": "^realization\\."},
                    "path": {"type": "string", "minLength": 1},
                    "reason": {"type": "string", "minLength": 1}
                  }
                }
              },
              "steps": {
                "type": "array",
                "minItems": 1,
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["operation", "modules", "purpose"],
                  "properties": {
                    "operation": {
                      "enum": ["understand", "specify", "implement", "test", "spec_review",
                               "code_review", "validate", "delivery"]
                    },
                    "modules": {
                      "type": "array",
                      "items": {"type": "string", "pattern": "^module\\."}
                    },
                    "purpose": {"type": "string", "minLength": 1}
                  }
                }
              },
              "decisions": {"type": "array", "items": {"type": "string", "minLength": 1}}
            }
          }
        ]
      }
    }
  },
  "semantics": "One assessment of the bound Modules' Specs for the stated goal, as proposed by the understand worker. goal is the --goal argument, set by the host. modules has one entry per bound Module summarizing what it promises that matters for the goal, taken only from its Spec context. sufficient is true when the Specs state every promise the goal needs. gaps lists each Spec gap: the Module and the project-relative document where the promise belongs, what is missing, why the goal needs it and a suggested repair; gaps is empty exactly when sufficient is true. plan is null unless --plan was given and sufficient is true. A plan names the Modules to change, the files to declare as pending entries of a named realization of a named Module, the ordered Operations to run next with their Modules and purpose, and the decisions left to the main agent. Every Module identity must exist in the task worktree's Specs, and gaps, sufficient, plan and the --plan argument must agree as stated above, with one modules entry per bound Module; the host checks both. Everything else is the worker's claim and is never restated by the host as fact.",
  "example": {
    "goal": "let Issue reports carry a severity",
    "modules": [
      {
        "module": "module.issues",
        "promises": "Issues keeps branch-local Issue records whose reports have a type, a title, a description, an impact and evidence; reports are never rewritten."
      }
    ],
    "sufficient": true,
    "gaps": [],
    "plan": {
      "summary": "Add an optional severity to the report contract, then implement and test it in the store.",
      "modules": ["module.issues"],
      "pending": [],
      "steps": [
        {"operation": "specify", "modules": ["module.issues"], "purpose": "add severity to the report contract and a scenario for it"},
        {"operation": "implement", "modules": ["module.issues"], "purpose": "accept and store the severity"},
        {"operation": "test", "modules": ["module.issues"], "purpose": "run and interpret the Issues checks"},
        {"operation": "code_review", "modules": ["module.issues"], "purpose": "judge the change against the updated Spec"}
      ],
      "decisions": ["whether severity is required for new reports or optional"]
    }
  }
}
```
