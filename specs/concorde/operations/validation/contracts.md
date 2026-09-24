# Validation contracts

The readiness that the `validate` Operation of [Validation](module.md) returns as its output, and
the exact input measurement it is bound to.

## Input measurement

- The **changed paths** are the union of the paths Git reports as different between the base
  commit and the working tree, staged or not, and the untracked paths Git does not ignore, each as
  a project-relative POSIX path, sorted by byte order.
- A changed path's **digest** is `sha256:` followed by the hexadecimal SHA-256 of the file's bytes
  in the worktree, or `null` when the path no longer exists.
- The **configuration digest** is the digest of `.concorde/config.json` in the task worktree.
- The **input digest** is the digest of the canonical JSON (sorted keys, no insignificant
  whitespace, UTF-8) of the object `{"head", "base", "changed", "config_digest"}` with the values
  recorded in `inputs`.

Delivery uses the same measurement through Validation, so both compute the same input digest for
the same worktree.

## Readiness

```concorde-contract
{
  "id": "contract.validation.readiness",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["task", "ready", "inputs", "modules", "blocking", "warnings", "confirmations",
                 "checks"],
    "properties": {
      "task": {"type": "string", "minLength": 1},
      "ready": {"type": "boolean"},
      "inputs": {
        "type": "object",
        "additionalProperties": false,
        "required": ["head", "base", "changed", "config_digest", "digest"],
        "properties": {
          "head": {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
          "base": {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
          "changed": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["path", "digest"],
              "properties": {
                "path": {"type": "string", "minLength": 1},
                "digest": {"anyOf": [{"type": "null"},
                                     {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}]}
              }
            }
          },
          "config_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
          "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
        }
      },
      "modules": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "blocking": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
      "warnings": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
      "confirmations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["module", "realization", "entry", "metadata", "metadata_digest"],
          "properties": {
            "module": {"type": "string", "minLength": 1},
            "realization": {"type": "string", "minLength": 1},
            "entry": {"type": "string", "minLength": 1},
            "metadata": {"type": "string", "minLength": 1},
            "metadata_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
          }
        }
      },
      "checks": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["check", "module", "status", "exit_code", "measured_digest", "log"],
          "properties": {
            "check": {"type": "string", "minLength": 1},
            "module": {"type": "string", "minLength": 1},
            "status": {"enum": ["passed", "failed", "timeout"]},
            "exit_code": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
            "measured_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "log": {"type": "string", "minLength": 1}
          }
        }
      }
    },
    "$defs": {
      "finding": {
        "type": "object",
        "additionalProperties": false,
        "required": ["kind", "ref", "detail"],
        "properties": {
          "kind": {"enum": ["load", "structural", "unbound", "check"]},
          "ref": {"type": "string", "minLength": 1},
          "detail": {"type": "string", "minLength": 1}
        }
      }
    }
  },
  "semantics": "The output of one validate run for task. inputs is the input measurement taken at the start of the run and confirmed unchanged at its end; digest is the input digest. modules lists, sorted, the changed Modules (binding a changed path or owning a changed Spec document) together with the run's bound Modules. blocking lists every blocking finding: load when the Specs could not be loaded, structural for a structural-check error (ref is the rule identity and path), unbound for an existing changed path that is no document member, no control record under .concorde/, no generated or build output, no external material and bound by no Module (ref is the path), check for a configured check that failed or timed out (ref is the check identity) or for a Module whose checks could not be run (ref is the Module identity). warnings lists structural-check warnings in the same shape and never affects ready. confirmations lists every pending realization entry whose file exists, with the metadata document declaring it and that document's digest, for Delivery to clear; blocking and warnings are those of the Specs as they read with these markers cleared. checks lists one result per configured check run, in run order, with exit_code null on timeout and log the path of its saved log under the run directory in the primary worktree. ready is true exactly when blocking is empty; every check then has status passed. The run's status is ok when ready is true and blocked otherwise, and a blocked run still carries this readiness as its output. A readiness is valid only while a fresh input measurement of the same worktree yields the same digest.",
  "example": {
    "task": "severity",
    "ready": true,
    "inputs": {
      "head": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
      "base": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
      "changed": [
        {"path": "specs/concorde/issues/interface.md", "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111"},
        {"path": "src/concorde/issues/severity.py", "digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222"}
      ],
      "config_digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
      "digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444"
    },
    "modules": ["module.issues"],
    "blocking": [],
    "warnings": [
      {"kind": "structural", "ref": "CONCORDE-COVERAGE-001 specs/concorde/issues/scenarios.md",
       "detail": "no test declares that it verifies scenario.issues.severity"}
    ],
    "confirmations": [
      {"module": "module.issues", "realization": "realization.issues.store",
       "entry": "src/concorde/issues/severity.py",
       "metadata": "specs/concorde/issues/module.md.json",
       "metadata_digest": "sha256:5555555555555555555555555555555555555555555555555555555555555555"}
    ],
    "checks": [
      {"check": "check.issues.tests", "module": "module.issues", "status": "passed",
       "exit_code": 0,
       "measured_digest": "sha256:6666666666666666666666666666666666666666666666666666666666666666",
       "log": ".concorde/runs/r-20260924T103000-validate-9b1c0d2e/checks/check.issues.tests.log"}
    ]
  }
}
```
