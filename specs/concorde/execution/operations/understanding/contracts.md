# Understanding contracts

The exact shape of what [Understanding](module.md) returns: the assessment of `understand` and the
plan review report of `plan_review`, each the `output` of its
[run result](../../../glossary.json#concept.run-result). The understand worker proposes the
assessment as the Operation-specific part of its answer, and the
[Operation](../../../glossary.json#concept.operation)'s steps pass it on once their checks have
passed, with `goal` set to the run's own `--goal` argument.

## Assessment

```concorde-contract
{
  "id": "contract.understanding.assessment",
  "version": 4,
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
            "required": ["summary", "modules", "new_files", "steps", "decisions"],
            "properties": {
              "summary": {"type": "string", "minLength": 1},
              "modules": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "pattern": "^module\\."}
              },
              "new_files": {
                "type": "array",
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["module", "path", "reason"],
                  "properties": {
                    "module": {"type": "string", "pattern": "^module\\."},
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
                  "required": ["run", "modules", "purpose"],
                  "properties": {
                    "run": {
                      "enum": [
                        "understand",
                        "specify",
                        "implement",
                        "test",
                        "spec_review",
                        "code_review",
                        "task-validation",
                        "delivery"
                      ]
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
  "semantics": "One assessment of the bound Modules' Specs for the stated goal, as proposed by the understand worker. goal is the --goal argument, set by the Operation's steps. modules has one entry per bound Module summarizing what it promises that matters for the goal, taken only from its Spec context. sufficient is true when the Specs state every promise the goal relies on: for a goal that asks what the Modules promise, every promise the answer needs; for a goal that changes them, every existing promise the change relies on, and where each new promise the change adds belongs, so that the change can be planned. A new promise the change adds is never a gap: it becomes a specify step of the plan. gaps lists each Spec gap, a promise the goal relies on that the Specs do not state, including where a new promise belongs when no bound Module's Spec says so: the Module and the project-relative document where the promise belongs, what is missing, why the goal needs it and a suggested repair; gaps is empty exactly when sufficient is true. plan is null unless --plan was given and sufficient is true. A plan names the Modules to change, in new_files the project-relative files the change needs that do not exist yet, each with the Module that will bind it, for the task level to create and bind before the run that fills them, the ordered runs to start next, each with its Modules and purpose, and the decisions left to the task level. A step's run names an Operation (understand, specify, implement, test, spec_review or code_review) or one of the execution commands task-validation and delivery that end a task's work. Every Module identity must exist in the Specs of the worktree the run works on, and gaps, sufficient, plan and the --plan argument must agree as stated above, with exactly one modules entry per bound Module and none for a Module that is not bound; the Operation's steps check both. Everything else is the worker's claim and is never restated by the Operation as fact.",
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
      "new_files": [],
      "steps": [
        {"run": "specify", "modules": ["module.issues"], "purpose": "add severity to the report contract and a scenario for it"},
        {"run": "implement", "modules": ["module.issues"], "purpose": "accept and store the severity"},
        {"run": "test", "modules": ["module.issues"], "purpose": "run and interpret the Issues checks"},
        {"run": "code_review", "modules": ["module.issues"], "purpose": "judge the change against the updated Spec"},
        {"run": "task-validation", "modules": ["module.issues"], "purpose": "decide whether the workspace is ready to deliver"},
        {"run": "delivery", "modules": ["module.issues"], "purpose": "validate the whole workspace again and commit the change"}
      ],
      "decisions": ["whether severity is required for new reports or optional"]
    }
  }
}
```

## Plan review report

The `output` of a `plan_review` run. The reviewer supplies `responses` and `findings` as the
Operation-specific part of its answer and `summary` as the summary of its
[worker result](../../../glossary.json#concept.worker-result); the Operation
adds the plan it read, the iteration, the previous run and the answers, and derives the verdict.

```concorde-contract
{
  "id": "contract.understanding.plan-review",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["plan", "iteration", "previous", "answers", "summary", "responses", "findings",
                 "verdict"],
    "properties": {
      "plan": {
        "type": "object",
        "additionalProperties": false,
        "required": ["file", "copy", "digest"],
        "properties": {
          "file": {"type": "string", "minLength": 1},
          "copy": {"type": "string", "minLength": 1},
          "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
        }
      },
      "iteration": {"type": "integer", "minimum": 1},
      "previous": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
      "answers": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["finding", "answer", "text"],
          "properties": {
            "finding": {"type": "string", "pattern": "^F[0-9]+$"},
            "answer": {"enum": ["accepted", "rejected"]},
            "text": {"type": "string", "minLength": 1}
          }
        }
      },
      "summary": {"type": "string", "minLength": 1},
      "responses": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["finding", "outcome", "comment"],
          "properties": {
            "finding": {"type": "string", "pattern": "^F[0-9]+$"},
            "outcome": {"enum": ["settled", "maintained"]},
            "comment": {"type": "string", "minLength": 1}
          }
        }
      },
      "findings": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["id", "severity", "kind", "module", "basis", "locations", "description",
                       "suggestion", "previous"],
          "properties": {
            "id": {"type": "string", "pattern": "^F[0-9]+$"},
            "severity": {"enum": ["blocking", "advisory"]},
            "kind": {"enum": ["goal", "violation", "spec-gap", "code", "scope", "sequence"]},
            "module": {"anyOf": [{"type": "string", "pattern": "^module\\."}, {"type": "null"}]},
            "basis": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
            "locations": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "description": {"type": "string", "minLength": 1},
            "suggestion": {"type": "string", "minLength": 1},
            "previous": {"anyOf": [{"type": "string", "pattern": "^F[0-9]+$"}, {"type": "null"}]}
          }
        }
      },
      "verdict": {"enum": ["accepted", "changes_required"]}
    }
  },
  "semantics": "One review of a plan the caller wrote, against the workspace's goal, the bound Modules' Specs and the project's code. plan names the file as --plan gave it, resolved against the worktree the run works on, the absolute path of the exact copy the Operation kept as plan.md in the run's trace node, and the sha256 digest of the bytes reviewed. previous is the run identity of the admitted plan_review input, the previous iteration, or null when none was admitted; iteration is 1 without a previous iteration and the previous iteration's plus one otherwise. answers lists the caller's --accept and --reject arguments in the order given, each naming a finding of the previous iteration, accepted with how the revised plan settles it or rejected with why; it is empty without a previous iteration and otherwise answers every finding of it exactly once. plan, iteration, previous and answers are set by the Operation. summary, responses and findings are the reviewer's claims. responses has exactly one entry per finding of the previous iteration and none otherwise, saying whether the revision or the answer's reason settled it or the reviewer maintains it, with a comment. findings lists every problem the reviewer establishes in this iteration: a run-local id, a severity (blocking when following the plan unchanged would miss the goal or break a promise), a kind (goal: the plan misses the goal or part of it; violation: a planned step would break a stated promise; spec-gap: the plan relies on a promise the Specs do not state or adds one without a step that states it; code: the plan misjudges the existing code; scope: the plan changes something outside the bound Modules or the goal; sequence: steps missing, in an order that cannot work, or a new file not created before the worker that fills it), the bound Module it concerns or null when it concerns the plan as a whole, its basis (a stable identity or a document path with an optional anchor from the bound Modules' Spec context, required for a violation and otherwise possibly null), the locations in the plan, Specs or code that show it, what is wrong, a suggested direction, and in previous the id of the maintained finding of the previous iteration it restates, or null for a new finding. Every maintained response is restated by exactly one finding and every restating finding continues a maintained response. The Operation checks that every basis resolves, that every violation has one, that module names a bound Module when it is not null and that responses and restated findings match the previous iteration as stated; it sets verdict to changes_required exactly when a finding is blocking, accepted otherwise. An accepted verdict is evidence about this plan and these inputs only.",
  "example": {
    "plan": {
      "file": "/home/dev/shop/.claude/worktrees/severity/plan.md",
      "copy": "/home/dev/shop/.concorde/tasks/severity/workspace/runs/r-0005/plan.md",
      "digest": "sha256:4f2a0c55a3e1b7f2d9c0e8a6b5d4c3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6"
    },
    "iteration": 2,
    "previous": "r-0004",
    "answers": [
      {"finding": "F1", "answer": "accepted", "text": "Step 2 now adds the severity to the report contract before implement."},
      {"finding": "F2", "answer": "rejected", "text": "The main agent decided severity stays optional; req.issues.retention is unchanged."}
    ],
    "summary": "The revised plan states the contract change first; one step still rewrites stored reports.",
    "responses": [
      {"finding": "F1", "outcome": "settled", "comment": "The specify step now comes first."},
      {"finding": "F2", "outcome": "maintained", "comment": "Optional is fine, but step 4 still rewrites earlier reports."}
    ],
    "findings": [
      {
        "id": "F1",
        "severity": "blocking",
        "kind": "violation",
        "module": "module.issues",
        "basis": "req.issues.retention",
        "locations": ["plan.md: step 4", "src/concorde/issues/store.py:240"],
        "description": "Step 4 migrates stored reports to add a severity, rewriting reports the Spec says are never rewritten.",
        "suggestion": "Read a missing severity as absent instead of migrating stored reports.",
        "previous": "F2"
      }
    ],
    "verdict": "changes_required"
  }
}
```
