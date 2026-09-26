# Framework contracts

The one contract every Module of the [Concorde Framework](module.md) shares: the shape of an
[error chain](vocabulary.md#concept.concorde.error-chain). The rules it serves are the
[result and error requirements](requirements.md#results-and-errors).

## Error link

An error chain is a tree of links read from the top. The top link is written by the actor that
reports to the reader, such as the Operation in an Operation result or the main agent in an
escalation; each link's `causes` are the errors of its children that it could not handle. The
order of reading is therefore the order of responsibility: the reader first learns what the level
directly below it could not do and why, then what that level received, down to where the error
started.

```concorde-contract
{
  "id": "contract.concorde.error",
  "version": 3,
  "schema": {
    "$ref": "#/$defs/error",
    "$defs": {
      "error": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "level",
          "actor",
          "code",
          "detail",
          "evidence",
          "attempts",
          "unhandled",
          "options",
          "recommendation",
          "causes"
        ],
        "properties": {
          "level": {
            "enum": [
              "main-agent",
              "task-session",
              "workflow",
              "operation",
              "harness",
              "worker",
              "check",
              "component"
            ]
          },
          "actor": {
            "type": "string",
            "minLength": 1
          },
          "code": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$"
          },
          "detail": {
            "type": "string",
            "minLength": 1
          },
          "evidence": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/evidence"
            }
          },
          "attempts": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "unhandled": {
            "$ref": "#/$defs/unhandled"
          },
          "options": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "recommendation": {
            "type": "string"
          },
          "causes": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/error"
            }
          }
        }
      },
      "evidence": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "kind",
          "ref",
          "detail"
        ],
        "properties": {
          "kind": {
            "type": "string",
            "minLength": 1
          },
          "ref": {
            "type": "string"
          },
          "detail": {
            "type": "string"
          }
        }
      },
      "unhandled": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "reason",
          "explanation"
        ],
        "properties": {
          "reason": {
            "enum": [
              "permission",
              "decision",
              "scope",
              "capability",
              "exhausted",
              "environment",
              "input"
            ]
          },
          "explanation": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "One error link and, through causes, the chain below it. level names the kind of actor that wrote the link: main-agent, task-session (a session working inside one task worktree for the main agent), workflow (a workflow run in one task, reporting the Operations it ran), operation (an Operation host and its provider steps), harness (Workers running one worker; the level keeps the name it had before the Harness became a Module of its own), worker (the worker's own report, a claim), check (one configured check) or component (a deterministic component the host called, such as Git, Tasks, Spec core or the Claude Code process). actor identifies it exactly, with the run, task, check or command concerned. code is a stable snake_case name chosen by the actor. detail describes the error completely: what failed, where, and the exact message or output; it is never only the code. evidence names the paths, commands and outputs that show it, each with a kind, a reference and a detail. attempts lists what the actor tried, in order. unhandled states why the actor could not handle the error itself; its reason is one of the reasons in the table below and explanation names the specifics. options and recommendation are what the actor offers its parent. causes are the errors the actor received from its children and could not handle, each exactly as its child wrote it; independent errors are siblings, and a link without causes is where an error started. A parent never edits or drops a cause. A behaviour or field change increments the version.",
  "example": {
    "level": "operation",
    "actor": "Operation implement r-20260924T093000-implement-5c1e0a77 (task severity)",
    "code": "checks_failed",
    "detail": "the implement worker run w-20260924T093001-implement-0f3b2a91 ended failed: checks_failed: 1 configured check(s) still fail after 4 round(s) (3 resume round(s) allowed): check.issues.tests",
    "evidence": [],
    "attempts": [],
    "unhandled": {
      "reason": "decision",
      "explanation": "the Operation used every resume round it is configured with; whether to narrow the goal, change the Spec or allow more rounds is the main agent's decision"
    },
    "options": [
      "run the Operation again with a narrower goal or more --rounds",
      "run understand to check whether the Spec supports the change"
    ],
    "recommendation": "run the Operation again with a narrower goal or more --rounds",
    "causes": [
      {
        "level": "harness",
        "actor": "Workers run w-20260924T093001-implement-0f3b2a91 (implement worker)",
        "code": "checks_failed",
        "detail": "1 configured check(s) still fail after 4 round(s) (3 resume round(s) allowed): check.issues.tests",
        "evidence": [
          {
            "kind": "run-record",
            "ref": ".concorde/runs/w-20260924T093001-implement-0f3b2a91/record.json",
            "detail": ""
          }
        ],
        "attempts": [
          "round 1: the worker ended ok; failing: check.issues.tests (failed, exit 1)",
          "round 4: the worker ended ok; failing: check.issues.tests (failed, exit 1)"
        ],
        "unhandled": {
          "reason": "exhausted",
          "explanation": "Workers resumes the worker at most 3 time(s) with the failures and does not extend that"
        },
        "options": [],
        "recommendation": "",
        "causes": [
          {
            "level": "check",
            "actor": "check.issues.tests",
            "code": "check_failed",
            "detail": "the configured check check.issues.tests of module.issues failed with exit code 1; its log ends with: FAILED tests/concorde/issues/test_store.py::test_severity_round_trip - KeyError: 'severity'",
            "evidence": [
              {
                "kind": "log",
                "ref": ".concorde/runs/w-20260924T093001-implement-0f3b2a91/checks/4/check.issues.tests.log",
                "detail": ""
              }
            ],
            "attempts": [],
            "unhandled": {
              "reason": "capability",
              "explanation": "a configured check only measures the code it runs against"
            },
            "options": [],
            "recommendation": "",
            "causes": []
          }
        ]
      }
    ]
  }
}
```

## Where links appear

| Where | The top link is written by |
| --- | --- |
| `error` of a workflow result | the workflow (`workflow`) |
| `error` of an Operation result | the Operation (`operation`) |
| `error` of a worker run record | Workers (`harness`) |
| `error` of a worker result | the worker, without `level`, `actor` and `causes`, which the harness adds |
| `{"error": …}` printed by a refused `concorde task` or `concorde issues` command | the refusing component (`component`) |
| an escalation recorded with `concorde task escalate` | the main agent (`main-agent`) |

Spec tooling is the exception: it depends on no other Module and reports with its
[own error record](spec-tooling/spec/errors.md). A Module that receives a Spec tooling error and
cannot handle it translates it into a `component` link and keeps its causes as nested links.

## Reasons

| Reason | The actor cannot handle the error because |
| --- | --- |
| `permission` | the fix needs a read, write or tool it is not granted |
| `decision` | the fix needs a decision reserved to a higher level |
| `scope` | the fix lies outside its task or bound Modules |
| `capability` | it has no means to repair this kind of error |
| `exhausted` | it used up its allowed rounds, turns, time or budget |
| `environment` | the environment failed and it cannot change it |
| `input` | the input it received is invalid and only its sender can correct it |
