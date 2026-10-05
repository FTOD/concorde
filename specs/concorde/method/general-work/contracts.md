# General work contracts

The output contract of [General work](module.md)'s [Operation](../../glossary.json#concept.operation) `general`. The
[requirements](requirements.md) state the obligations. The [scenarios](scenarios.md) show them at
work.

## The general work result

The `output` of an `ok` `general` run. The Operation sets these fields:

- `type` and `read_only`.
- `instruction`.
- `change`.
- The review's `verdict`.

The worker's `answer` and the review's `summary` and `findings` are the workers' claims.

```concorde-contract
{
  "id": "contract.general-work.result",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["type", "read_only", "instruction", "answer", "change", "review"],
    "properties": {
      "type": {"enum": ["understand", "specify", "implement", "test", "review-spec", "review-code",
                        "code-to-spec", "review-architecture"]},
      "read_only": {"type": "boolean"},
      "instruction": {
        "type": "object",
        "additionalProperties": false,
        "required": ["file", "copy", "digest"],
        "properties": {
          "file": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
          "copy": {"type": "string", "minLength": 1},
          "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
        }
      },
      "answer": {"type": "string", "minLength": 1},
      "change": {
        "type": "object",
        "additionalProperties": false,
        "required": ["files", "diff", "before"],
        "properties": {
          "files": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["path", "change"],
              "properties": {
                "path": {"type": "string", "minLength": 1},
                "change": {"enum": ["added", "modified", "deleted"]}
              }
            }
          },
          "diff": {"type": "string", "minLength": 1},
          "before": {"type": "string", "minLength": 1}
        }
      },
      "review": {
        "type": "object",
        "additionalProperties": false,
        "required": ["summary", "findings", "verdict"],
        "properties": {
          "summary": {"type": "string", "minLength": 1},
          "findings": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["id", "severity", "kind", "locations", "description", "suggestion"],
              "properties": {
                "id": {"type": "string", "pattern": "^F[0-9]+$"},
                "severity": {"enum": ["blocking", "advisory"]},
                "kind": {"enum": ["instruction", "meaning", "scope", "error", "claim"]},
                "locations": {"type": "array", "items": {"type": "string", "minLength": 1}},
                "description": {"type": "string", "minLength": 1},
                "suggestion": {"type": "string", "minLength": 1}
              }
            }
          },
          "verdict": {"enum": ["accepted", "changes_required"]}
        }
      }
    }
  },
  "semantics": "One piece of free-form work and its independent review. type is the task type --type named, whose grant bounded both workers; read_only is true when --read-only lowered every writable level of the worker's grant to read. instruction names the file --instruction-file gave, resolved against the worktree the run works on, or null when --instruction gave the text; copy is the absolute path of the exact copy the Operation kept as instruction.md in the run's trace node, and digest the sha256 digest of its bytes. answer is the worker's own account of what it did or found, a claim. change is what the Operation observed between the Git trees of the worktree it recorded before the worker launched and after it ended, files Git ignores excluded: files lists every added, modified or deleted path relative to the worktree, sorted by path; diff is the absolute path of change.diff in the run's trace node, the unified diff between the two trees, empty when nothing changed; before is the absolute path of the before/ folder in that node, which holds the earlier content of every modified or deleted file at its worktree-relative path. review holds the reviewer's summary and findings, its claims, and the verdict the Operation derived. Each finding has a run-local id distinct among them, a severity (blocking when the caller cannot take the result as it is, advisory otherwise), a kind (instruction: the result does not do, or does only part of, what the instruction asks; meaning: the change alters or loses meaning the instruction asked to keep; scope: the change goes beyond what the instruction asks; error: the change introduces a mistake such as a broken link, a wrong statement or an invalid format; claim: the worker's answer misstates what it did), the locations in the changed files or the answer that show it, what is wrong and a suggested repair. The Operation checks that the finding ids are distinct and sets verdict to changes_required exactly when a finding is blocking, accepted otherwise. The reviewer changes nothing; acting on a finding is the caller's decision.",
  "example": {
    "type": "specify",
    "read_only": false,
    "instruction": {
      "file": "/home/dev/shop/.claude/worktrees/restyle-issues/restyle.md",
      "copy": "/home/dev/shop/.concorde/tasks/restyle-issues/workspace/runs/r-0003/instruction.md",
      "digest": "sha256:9b1c0d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c"
    },
    "answer": "Rewrote specs/issues/module.md in short sentences, one fact each; kept every requirement keyword and link.",
    "change": {
      "files": [{"path": "specs/issues/module.md", "change": "modified"}],
      "diff": "/home/dev/shop/.concorde/tasks/restyle-issues/workspace/runs/r-0003/change.diff",
      "before": "/home/dev/shop/.concorde/tasks/restyle-issues/workspace/runs/r-0003/before"
    },
    "review": {
      "summary": "The rewrite keeps the meaning except for one dropped condition.",
      "findings": [
        {
          "id": "F1",
          "severity": "blocking",
          "kind": "meaning",
          "locations": ["specs/issues/module.md: Retention"],
          "description": "The old text kept closed Issues for 30 days only after a merge; the new text drops the merge condition.",
          "suggestion": "Restore the condition: closed Issues are kept for 30 days after the merge that closed them."
        }
      ],
      "verdict": "changes_required"
    }
  }
}
```
