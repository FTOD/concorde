# Validation contracts

The readiness that the [execution command](../../../glossary.json#concept.execution-command)
`task-validation` of [Validation](module.md) returns as its output, and the exact input measurement
it is bound to.

## Input measurement

- The **changed paths** are the union of the paths Git reports as different between the base
  commit and the working tree, staged or not, and the untracked paths Git does not ignore, each as
  a project-relative POSIX path, sorted by byte order. An untracked path that is neither a regular
  file, a symbolic link nor a directory is left out: Git cannot version it, and it is how Claude
  Code's Bash sandbox hides a path such as `.bashrc` behind a `/dev/null` mount. Such a path is no
  uncommitted change for Delivery either, which tests for one with this measurement's rules. A
  submodule is a changed path when its checked-out commit differs; changes inside the submodule's
  own worktree are not measured and are no uncommitted change for Delivery, since the workspace
  commits only the submodule's commit.
- A changed path's **digest** is `sha256:` followed by the hexadecimal SHA-256 of its content in
  the worktree: a regular file's bytes; for a symbolic link, `symlink:` followed by its link text;
  for a directory, which is a submodule or another repository, `gitlink:` followed by the
  hexadecimal name of the commit it has checked out. It is `null` when the path no longer exists.
- A changed path's **mode** is its Git file mode in the worktree, as six octal digits: `100755`
  for a regular file whose owner may execute it, `100644` for any other regular file, `120000` for
  a symbolic link and `160000` for a directory, which is a submodule; it is `null` when the path no
  longer exists. Setting or clearing a file's execute bit therefore changes the input digest even
  when its bytes stay the same.
- The **configuration digest** is the digest of the canonical JSON object that maps
  `.concorde/config.json` and every entry of `.concorde/checks/` in the workspace to the digest of
  its bytes (a symbolic link's by its link text, any other entry that is not a file as `null`), so
  a changed check command changes it as a changed configuration does.
- The **input digest** is the digest of the canonical JSON (sorted keys, no insignificant
  whitespace, UTF-8) of the object `{"head", "base", "changed", "config_digest"}` with the values
  recorded in `inputs`.

Delivery uses the same measurement through Validation, so both compute the same input digest for
the same workspace.

## Readiness

```concorde-contract
{
  "id": "contract.validation.readiness",
  "version": 5,
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
      "confirmations",
      "checks"
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
      "warnings": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/finding"
        }
      },
      "confirmations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "module",
            "realization",
            "entry",
            "metadata",
            "metadata_digest"
          ],
          "properties": {
            "module": {
              "type": "string",
              "minLength": 1
            },
            "realization": {
              "type": "string",
              "minLength": 1
            },
            "entry": {
              "type": "string",
              "minLength": 1
            },
            "metadata": {
              "type": "string",
              "minLength": 1
            },
            "metadata_digest": {
              "type": "string",
              "pattern": "^sha256:[0-9a-f]{64}$"
            }
          }
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
  "semantics": "The output of one task-validation run of the bound workspace named by workspace, and the readiness a delivery run decides with the same steps and saves in its trace node. inputs is the input measurement taken at the start of the run and confirmed unchanged at its end: every changed path with its mode and digest; digest is the input digest. modules lists, sorted, the changed Modules (binding a changed path or owning a changed Spec document) together with the run's Modules. blocking lists every blocking finding: load when the Specs could not be loaded, structural for a structural-check error (ref is the rule identity and path) or one of the run's Modules that the workspace's registry does not register (ref is the Module identity), unbound for an existing changed path that is no document member, not the project glossary, no control record under .concorde/, no generated or build output, no external material and bound by no Module (ref is the path), check for a configured check that failed or timed out (ref is the check identity) or for Modules whose checks could not be run (ref is the Module identity, or the comma-separated identities of the whole selection when its selective checks could not run). warnings lists structural-check warnings in the same shape and never affects ready. confirmations lists every pending realization entry whose file exists, with the metadata document declaring it and that document's digest, for Delivery to clear; blocking and warnings are those of the Specs as they read with these markers cleared. checks lists one result per configured check run, in run order, with measured_digest the measured digest Check execution took before the check ran, exit_code null on timeout and log the path of its saved log relative to the run's trace node, checks/<check>/output.log. ready is true exactly when blocking is empty; every check then has status passed. The run's status is ok when ready is true and blocked otherwise, and a blocked run still carries this readiness as its output. A readiness is valid only while a fresh input measurement of the same workspace yields the same digest. A behaviour or field change increments the version.",
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
    "confirmations": [
      {
        "module": "module.issues",
        "realization": "realization.issues.store",
        "entry": "src/concorde/issues/severity.py",
        "metadata": "specs/concorde/issues/module.md.json",
        "metadata_digest": "sha256:5555555555555555555555555555555555555555555555555555555555555555"
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
    ]
  }
}
```
