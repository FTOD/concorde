# Validation contracts

The [execution command](../../glossary.json#concept.execution-command) `task-validation` of
[Validation](module.md) returns readiness as its output. This contract also describes the exact
input measurement the readiness is bound to.

## Input measurement

- The **changed paths** are the union of these paths:
  - The paths Git reports as different between the base commit and the working tree, staged or not.
  - The untracked paths Git does not ignore.

  Each is a project-relative POSIX path, sorted by byte order. Two kinds of untracked path are
  left out, since they are no content of the task. One is a path that is neither a regular file,
  a symbolic link nor a directory. Git cannot version it. This is how Claude Code's Bash sandbox hides a path such as `.bashrc`
  behind a `/dev/null` mount. The other is a **sandbox placeholder**: an empty regular file with
  no write bit and a single link. Where an absent path is to be hidden, that sandbox creates the
  file on the host before it mounts `/dev/null` over it. It removes the file only when no sandbox
  of its Claude Code process is alive. Meanwhile, another command sees it as a regular file.
  This is the signature by which the sandbox runtime itself recognises such a file. A file a task
  creates has a write bit, content or another link. Such a file is measured. Neither kind is an
  uncommitted change for Delivery either, which tests for one with this measurement's rules.
  When its checked-out commit differs, a submodule is a changed path. Since the workspace commits
  only the submodule's commit, changes inside the submodule's own worktree are not measured.
  Those changes are no uncommitted change for Delivery.
- A changed path is **recorded** as text. When its bytes are valid UTF-8 and it does not begin
  with `"`, it is recorded as it is. Otherwise, it is recorded in double quotes, as Git quotes a
  path. Each `"` and `\` is preceded by `\`. Every byte that is no part of a valid UTF-8 sequence
  is written as `\` followed by its three octal digits. Thus, `"caf\351.txt"` records the file
  named `caf`, the byte `0xE9` and `.txt`.

  The record names exactly one path, whatever bytes Git reports for it. The changed paths stay
  sorted by the byte order of the paths themselves. Every finding names a changed path as it is
  recorded. Validation compares the path itself with the entries of the
  [Specs](../../glossary.json#concept.spec).
- A changed path's **digest** is `sha256:` followed by the hexadecimal SHA-256 of its content in
  the worktree. The content depends on the kind of path:
  - For a regular file, the content is its bytes.
  - For a symbolic link, the content is `symlink:` followed by its link text.
  - For a directory, which is a submodule or another repository, the content starts with
    `gitlink:`.

  For a directory, what follows depends on these cases:
  - When it is the top level of a repository whose head names a commit, the hexadecimal name of
    its checked-out commit follows.
  - Otherwise, such as for a submodule that is not initialized, when the worktree's index records
    a commit for the path, that commit follows. This is what Delivery would commit.
  - When the index records none in that latter case, nothing follows.

  When the path no longer exists, its digest is `null`. A changed path that exists but cannot be
  read, or whose Git file mode cannot be determined, fails the measurement (`path_unreadable`).
- A changed path's **mode** is its Git file mode in the worktree, as six octal digits:
  - `100755` for a regular file whose owner may execute it.
  - `100644` for any other regular file.
  - `120000` for a symbolic link.
  - `160000` for a directory, which is a submodule.

  When the path no longer exists, its mode is `null`. Setting or clearing a file's execute bit
  therefore changes the input digest even when its bytes stay the same.
- The **configuration digest** is the digest of a canonical JSON object. The object maps
  `.concorde/config.json` and every entry of `.concorde/checks/` in the workspace to the digest of
  its bytes. Each is named as a changed path is recorded. For a symbolic link, the object uses
  the digest of its link text. For any other entry of the checks directory that is not a file,
  the object uses `null`. Thus, a changed check command changes the configuration digest as a
  changed configuration does. The measurement fails (`config_unreadable`) in any of these cases:
  - A configuration is missing.
  - A configuration cannot be read.
  - A checks directory entry cannot be read.
- The **input digest** is the digest of the canonical JSON of the object
  `{"head", "base", "changed", "config_digest"}`. Its values are those recorded in `inputs`, with
  each changed path as it is recorded. The canonical JSON has sorted keys, no insignificant
  whitespace and UTF-8.

Delivery uses the same measurement through Validation, so both compute the same input digest for
the same workspace.

## Readiness

Beside the readiness's fields, the `output` of `task-validation` also carries the `workflow`
object of the [step output convention](../../workflows/contracts.md#contract.workflows.step-output).
This follows [req.validation.step-output](requirements.md#req.validation.step-output).
The object's `data` holds `ready`, the readiness's own value. When the workspace is ready,
`blocking` is `null`. Otherwise, it is
`{"code": "not_ready", "detail": "<each blocking finding's kind and subject>"}`. In that case, the run
declares to a workflow that its procedure stops here. The workflow reads nothing else of the
run's output. The readiness saved as `readiness.json` does not carry the object. The object
declares no [decision point](../../glossary.json#concept.decision-point), decision or note. The convention,
not this contract, defines the object.

```concorde-contract
{
  "id": "contract.validation.readiness",
  "version": 8,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workspace",
      "ready",
      "inputs",
      "modules",
      "blocking",
      "warnings",
      "checks",
      "workflow"
    ],
    "properties": {
      "workspace": {
        "type": "string",
        "minLength": 1
      },
      "ready": {
        "type": "boolean"
      },
      "inputs": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "head",
          "base",
          "changed",
          "config_digest",
          "digest"
        ],
        "properties": {
          "head": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          "base": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          "changed": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "path",
                "mode",
                "digest"
              ],
              "properties": {
                "path": {
                  "type": "string",
                  "minLength": 1
                },
                "mode": {
                  "anyOf": [
                    {
                      "type": "null"
                    },
                    {
                      "enum": [
                        "100644",
                        "100755",
                        "120000",
                        "160000"
                      ]
                    }
                  ]
                },
                "digest": {
                  "anyOf": [
                    {
                      "type": "null"
                    },
                    {
                      "type": "string",
                      "pattern": "^sha256:[0-9a-f]{64}$"
                    }
                  ]
                }
              }
            }
          },
          "config_digest": {
            "type": "string",
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "digest": {
            "type": "string",
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        }
      },
      "modules": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "blocking": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/finding"
        }
      },
      "workflow": {
        "type": "object"
      },
      "warnings": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/finding"
        }
      },
      "checks": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "check",
            "module",
            "status",
            "exit_code",
            "measured_digest",
            "log"
          ],
          "properties": {
            "check": {
              "type": "string",
              "minLength": 1
            },
            "module": {
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
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "measured_digest": {
              "type": "string",
              "pattern": "^sha256:[0-9a-f]{64}$"
            },
            "log": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    },
    "$defs": {
      "finding": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "kind",
          "ref",
          "detail"
        ],
        "properties": {
          "kind": {
            "enum": [
              "load",
              "structural",
              "unbound",
              "check"
            ]
          },
          "ref": {
            "type": "string",
            "minLength": 1
          },
          "detail": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "The output of one task-validation run of the bound workspace named by workspace, and the readiness a delivery run decides with the same steps and saves in its trace node. inputs is the input measurement taken at the start of the run and confirmed unchanged at its end: every changed path, as the input measurement records it, with its mode and digest; digest is the input digest. modules lists, sorted, the changed Modules (binding a changed path or owning a changed Spec document) together with the run's Modules. blocking lists every blocking finding: load when the Specs could not be loaded, structural for a structural-check error (ref is the rule identity and path) or one of the run's Modules that the workspace's registry does not register (ref is the Module identity), unbound for an existing changed path that is no document member, not the project glossary, no control record under .concorde/, no generated or build output, no external material and bound by no Module (ref is the path as recorded), check for a configured check that failed or timed out (ref is the check identity), for a checks file or declared input of the project that is invalid (ref is configured checks) or for Modules whose checks could not be run (ref is the Module identity, or the comma-separated identities of the whole selection when its selective checks could not run). warnings lists structural-check warnings in the same shape and never affects ready. checks lists one result per configured check run, in run order, including the checks a call of Check execution finished before it failed, with measured_digest the measured digest Check execution took before the check ran, exit_code null on timeout and log the path of its saved log relative to the run's trace node, checks/<check>/output.log. ready is true exactly when blocking is empty; every check then has status passed. The run's status is ok when ready is true and blocked otherwise, and a blocked run still carries this readiness as its output. A readiness is valid only while a fresh input measurement of the same workspace yields the same digest. workflow is the object of Workflows' step output convention, which defines its fields: its data holds ready, and blocking is null when the workspace is ready and otherwise names the blocking findings (req.validation.step-output); the readiness saved as readiness.json does not carry it. A behaviour or field change increments the version.",
  "example": {
    "workspace": "severity",
    "ready": true,
    "inputs": {
      "head": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
      "base": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
      "changed": [
        {
          "path": "specs/concorde/issues/interface.md",
          "mode": "100644",
          "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
        },
        {
          "path": "src/concorde/issues/severity.py",
          "mode": "100644",
          "digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222"
        }
      ],
      "config_digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
      "digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444"
    },
    "modules": [
      "module.issues"
    ],
    "blocking": [],
    "warnings": [
      {
        "kind": "structural",
        "ref": "CONCORDE-COVERAGE-001 specs/concorde/issues/scenarios.md",
        "detail": "no test declares that it verifies scenario.issues.severity"
      }
    ],
    "checks": [
      {
        "check": "check.issues.tests",
        "module": "module.issues",
        "status": "passed",
        "exit_code": 0,
        "measured_digest": "sha256:6666666666666666666666666666666666666666666666666666666666666666",
        "log": "checks/check.issues.tests/output.log"
      }
    ],
    "workflow": {
      "decision_points": [],
      "decisions": [],
      "deviations": [],
      "notes": [],
      "blocking": null,
      "data": {
        "ready": true
      }
    }
  }
}
```
