# SWE-bench cases contracts

This document defines the interface of `grade` in [SWE-bench cases](module.md):

- The case it reads with `--instance`.
- The verdict it prints.
- The errors it fails with.

[Grading a case](module.md#grading-a-case) explains how grading reaches its verdict.

## The case

A case is one row of SWE-bench's dataset, saved as a JSON object. Grading reads the fields below
and ignores every other field of the row. `FAIL_TO_PASS` and `PASS_TO_PASS` are each a JSON list of
pytest node identities or a string holding one, as the dataset stores them. A missing
`PASS_TO_PASS` is an empty list.

```concorde-contract
{
  "id": "contract.swe-bench-cases.case",
  "version": 1,
  "semantics": "One SWE-bench instance, a row of its dataset saved as a JSON object, given to grade with --instance. instance_id names the case. base_commit is the commit the case's repository starts from and the one every file the test patch touches is reset to. test_patch is the case's own test change, applied in the grading worktree only. FAIL_TO_PASS lists the pytest node identities that must pass once the issue is resolved; PASS_TO_PASS those that must keep passing. Each list is a JSON list or a string holding one; a missing PASS_TO_PASS is empty. Other fields of the row are ignored.",
  "schema": {
    "type": "object",
    "required": [
      "base_commit",
      "test_patch",
      "FAIL_TO_PASS"
    ],
    "properties": {
      "instance_id": {
        "type": "string"
      },
      "base_commit": {
        "type": "string",
        "minLength": 1
      },
      "test_patch": {
        "type": "string",
        "minLength": 1
      },
      "FAIL_TO_PASS": {
        "type": [
          "array",
          "string"
        ],
        "items": {
          "type": "string"
        }
      },
      "PASS_TO_PASS": {
        "type": [
          "array",
          "string"
        ],
        "items": {
          "type": "string"
        }
      }
    }
  },
  "example": {
    "instance_id": "toy__calc-1",
    "base_commit": "5d41402abc4b2a76b9719d911017c592ae1b3c1f",
    "test_patch": "diff --git a/test_calc.py b/test_calc.py\nnew file mode 100644\n--- /dev/null\n+++ b/test_calc.py\n@@ -0,0 +1,2 @@\n+def test_add():\n+    assert 1 + 1 == 2\n",
    "FAIL_TO_PASS": "[\"test_calc.py::test_add\"]",
    "PASS_TO_PASS": []
  }
}
```

A case whose `base_commit` or `test_patch` is empty, or whose `FAIL_TO_PASS` lists no test, is
refused with `invalid_case`.

## The verdict

`grade` prints one JSON object, the verdict:

- `instance` is the case's `instance_id`.
- `ref` is the graded Git ref.
- `resolved` is true when every FAIL_TO_PASS and every PASS_TO_PASS test passed.
- `fail_to_pass` and `pass_to_pass` each count their list's tests. `passed` is the number that
  passed by their list's rule, `total` the number listed. `not_passed` maps each listed test that did
  not pass to its status.
- `command` is the pytest command line, as a list of arguments.
- `exit_code` is pytest's exit code. It is kept for the reader. The verdict never depends on it.
- `log` is the file that keeps pytest's whole output, or null when the caller named none.

A status is one of SWE-bench's pytest statuses, or `not run` for a listed identity pytest never
reported.

```concorde-contract
{
  "id": "contract.swe-bench-cases.verdict",
  "version": 1,
  "semantics": "What grade prints when grading ends with a verdict. instance and ref name the case and the graded ref. fail_to_pass and pass_to_pass count their list: passed is the number that passed by the list's rule (PASSED or XFAIL for FAIL_TO_PASS; PASSED, XFAIL or SKIPPED for PASS_TO_PASS), total the number listed, and not_passed maps each other listed test to its status. resolved is true exactly when both lists passed whole. command is the pytest command line, exit_code pytest's exit code, which the verdict never depends on, and log the file that keeps pytest's whole output, or null.",
  "schema": {
    "type": "object",
    "required": [
      "instance",
      "ref",
      "resolved",
      "fail_to_pass",
      "pass_to_pass",
      "command",
      "exit_code",
      "log"
    ],
    "additionalProperties": false,
    "properties": {
      "instance": {
        "type": [
          "string",
          "null"
        ]
      },
      "ref": {
        "type": "string"
      },
      "resolved": {
        "type": "boolean"
      },
      "fail_to_pass": {
        "$ref": "#/$defs/count"
      },
      "pass_to_pass": {
        "$ref": "#/$defs/count"
      },
      "command": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "exit_code": {
        "type": "integer"
      },
      "log": {
        "type": [
          "string",
          "null"
        ]
      }
    },
    "$defs": {
      "count": {
        "type": "object",
        "required": [
          "passed",
          "total",
          "not_passed"
        ],
        "additionalProperties": false,
        "properties": {
          "passed": {
            "type": "integer",
            "minimum": 0
          },
          "total": {
            "type": "integer",
            "minimum": 0
          },
          "not_passed": {
            "type": "object",
            "additionalProperties": {
              "enum": [
                "PASSED",
                "FAILED",
                "ERROR",
                "SKIPPED",
                "XFAIL",
                "XPASS",
                "not run"
              ]
            }
          }
        }
      }
    }
  },
  "example": {
    "instance": "toy__calc-1",
    "ref": "main",
    "resolved": false,
    "fail_to_pass": {
      "passed": 0,
      "total": 1,
      "not_passed": {
        "test_calc.py::test_add": "FAILED"
      }
    },
    "pass_to_pass": {
      "passed": 1,
      "total": 1,
      "not_passed": {}
    },
    "command": [
      "/venv/bin/python",
      "-m",
      "pytest",
      "-rA",
      "--color=no",
      "-p",
      "no:cacheprovider",
      "-p",
      "concorde_grade_report",
      "test_calc.py"
    ],
    "exit_code": 1,
    "log": null
  }
}
```

For example, a case whose fix is still missing:

```json
{
  "instance": "psf__requests-3362",
  "ref": "main",
  "resolved": false,
  "fail_to_pass": {"passed": 0, "total": 1, "not_passed": {"tests/test_requests.py::test_x": "FAILED"}},
  "pass_to_pass": {"passed": 2, "total": 2, "not_passed": {}},
  "command": ["/venv/bin/python", "-m", "pytest", "-rA", "--color=no", "-p", "no:cacheprovider",
              "-p", "concorde_grade_report", "tests/test_requests.py"],
  "exit_code": 1,
  "log": "/tmp/concorde-e2e/test-psf__requests-3362/.concorde/runs/e2e/grade-psf__requests-3362.log"
}
```

## The errors

Instead of a verdict, `grade` prints End-to-end testing's `{"error": …}`
([The commands](../module.md#the-commands)) with one of these codes:

- `invalid_case` for a case without FAIL_TO_PASS tests, a test patch or a base commit.
- `command_failed` when the grading worktree cannot be made or the test patch does not apply. It
  names the command and carries its exit status and the end of its output.
- `grade_timeout` when the test run exceeds 30 minutes. It names the case, the ref, the limit and the
  command. It carries the end of the output under `stdout` and `stderr`, and the kept whole output
  under `log` when the caller names its place.
- `cleanup_failed` when the grading worktree, its registration or its scratch directory is left
  after grading. It names the worktree and lists under `left` what is left, each with Git's
  account. When grading had failed before, it names that error in its detail and under `cause`.
