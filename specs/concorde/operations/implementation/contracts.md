# Implementation contracts

The exact shapes of what [Implementation](module.md) returns. Each is the `output` of the
Operation result. Fields computed by the host are facts it observed; fields the worker supplies as
the Operation-specific part of its answer are its claims and are passed on unchanged.

## Code change

```concorde-contract
{
  "id": "contract.implementation.code-change",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["goal", "summary", "changed_files", "created_files", "deleted_files",
                 "refused_deletions", "pending_cleared", "rounds", "checks", "addresses"],
    "properties": {
      "goal": {"type": "string", "minLength": 1},
      "summary": {"type": "string", "minLength": 1},
      "changed_files": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "created_files": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "deleted_files": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "refused_deletions": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "pending_cleared": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "rounds": {"type": "integer", "minimum": 1},
      "checks": {"type": "array", "items": {"$ref": "#/$defs/check"}},
      "addresses": {"type": "array", "items": {"type": "string", "minLength": 1}}
    },
    "$defs": {
      "check": {
        "type": "object",
        "additionalProperties": false,
        "required": ["check", "module", "outcome", "exit_code", "log"],
        "properties": {
          "check": {"type": "string", "minLength": 1},
          "module": {"type": "string", "pattern": "^module\\."},
          "outcome": {"enum": ["passed", "failed", "timed_out", "not_started"]},
          "exit_code": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
          "log": {"type": "string", "minLength": 1}
        }
      }
    }
  },
  "semantics": "The outcome of one implement run. goal repeats the --goal argument. summary and addresses are the worker's claims: its account of the change and the requirement or scenario identities it believes the change addresses. Everything else is computed by the host: changed_files, created_files and deleted_files from the task worktree after the last audit, relative to the state before the run; refused_deletions lists deletions the worker proposed outside its writable paths; pending_cleared lists the realization entries whose pending marker the host removed; rounds counts worker rounds including the first; checks holds the configured check results of the last round that ran checks, each with the check identity, the Module it belongs to, its outcome, its exit code (null when it did not exit) and the path of its log. An empty checks list means the bound Modules have no configured check. The run's status is ok only when every listed check passed.",
  "example": {
    "goal": "accept and store the report severity",
    "summary": "Added the severity field to report parsing and storage.",
    "changed_files": ["src/concorde/issues/shapes.py", "src/concorde/issues/store.py"],
    "created_files": ["src/concorde/issues/severity.py"],
    "deleted_files": [],
    "refused_deletions": [],
    "pending_cleared": ["src/concorde/issues/severity.py"],
    "rounds": 2,
    "checks": [
      {"check": "check.issues.store", "module": "module.issues", "outcome": "passed", "exit_code": 0, "log": ".concorde/runs/r-0001/checks/check.issues.store.log"}
    ],
    "addresses": ["scenario.issues.report-severity"]
  }
}
```

## Test report

```concorde-contract
{
  "id": "contract.implementation.test-report",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["focus", "passed", "checks", "summary", "failures", "notes"],
    "properties": {
      "focus": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
      "passed": {"type": "boolean"},
      "checks": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["check", "module", "outcome", "exit_code", "log"],
          "properties": {
            "check": {"type": "string", "minLength": 1},
            "module": {"type": "string", "pattern": "^module\\."},
            "outcome": {"enum": ["passed", "failed", "timed_out", "not_started"]},
            "exit_code": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "log": {"type": "string", "minLength": 1}
          }
        }
      },
      "summary": {"type": "string", "minLength": 1},
      "failures": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["check", "concerns", "cause", "fault", "locations"],
          "properties": {
            "check": {"type": "string", "minLength": 1},
            "concerns": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "cause": {"type": "string", "minLength": 1},
            "fault": {"enum": ["code", "test", "spec", "environment", "unknown"]},
            "locations": {"type": "array", "items": {"type": "string", "minLength": 1}}
          }
        }
      },
      "notes": {"type": "array", "items": {"type": "string", "minLength": 1}}
    }
  },
  "semantics": "The outcome of one test run. focus repeats the --focus argument or is null. passed and checks are computed by the host: checks holds every configured check of the bound Modules with its identity, Module, outcome, exit code (null when it did not exit) and log path, and passed is true exactly when every check passed. summary, failures and notes are the worker's interpretation: one failures entry per check that did not pass, naming the requirement or scenario identities it concerns, the likely cause, whether the fault lies in the code, a test, the Spec, the environment or is unknown, and the files and lines that show it; notes hold other observations, such as a scenario of a bound Module that no check seems to exercise. A failures entry never changes a check's outcome.",
  "example": {
    "focus": null,
    "passed": false,
    "checks": [
      {"check": "check.issues.store", "module": "module.issues", "outcome": "failed", "exit_code": 1, "log": ".concorde/runs/r-0002/checks/check.issues.store.log"}
    ],
    "summary": "One Issues check fails because a stored report drops its severity.",
    "failures": [
      {
        "check": "check.issues.store",
        "concerns": ["scenario.issues.report-severity"],
        "cause": "the store writes reports without the new severity field",
        "fault": "code",
        "locations": ["src/concorde/issues/store.py:212"]
      }
    ],
    "notes": []
  }
}
```
