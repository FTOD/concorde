# Issue interface

The canonical contracts, provenance, record file, store operations, reporting service and store
check of [Issues](module.md). All shapes are closed: unknown fields are refused. Every shape below
is registered as a typed value with version 1 under the name given with it.

## Report

A report is what a reporter submits: through the `report_issue` tool of an Agent call, through the
Host's own reporting, or through the developer's `report` action. It is at most 64 KiB as canonical
JSON; large logs are referenced by path, not copied.

```concorde-contract
{
  "id": "contract.issues.report",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["report_key", "type", "subtype", "title", "description", "impact", "basis",
                 "owner_target_id", "evidence"],
    "properties": {
      "report_key": {"type": "string", "minLength": 1},
      "type": {"enum": ["bug", "gap", "limitation"]},
      "subtype": {
        "anyOf": [
          {"enum": ["implementation-spec-mismatch", "spec-conflict", "missing-contract"]},
          {"type": "null"}
        ]
      },
      "title": {"type": "string", "minLength": 1},
      "description": {"type": "string", "minLength": 1},
      "impact": {"type": "string", "minLength": 1},
      "basis": {"type": "string", "minLength": 1},
      "owner_target_id": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
      "evidence": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["path", "description"],
          "properties": {
            "path": {"type": "string", "minLength": 1},
            "description": {"type": "string", "minLength": 1}
          }
        }
      },
      "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
      "expected_revision": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    }
  },
  "semantics": "One observation of a concrete problem, registered as typed value concorde-issue-report. report_key is chosen by the reporter and stays the same across retries of the same observation. type bug is a defect or failure, gap an implementation/Spec mismatch, a conflict between Specs or a missing necessary promise, limitation behaviour that is consistent but insufficient; subtype is required for gap and null otherwise. owner_target_id names the Module that owns the broken promise, or null when unknown. evidence paths are canonical project-relative POSIX paths within the reporter's admitted evidence paths. issue_id and expected_revision are both absent to create an Issue and both present to append to that Issue at exactly that revision. Provenance is never part of a report. The report is at most 64 KiB as canonical JSON.",
  "example": {
    "report_key": "retry-count-unspecified",
    "type": "gap",
    "subtype": "missing-contract",
    "title": "Retry limit is not specified",
    "description": "No Spec of module.payments states how often a failed payment is retried.",
    "impact": "Planning cannot choose a retry limit without inventing a promise.",
    "basis": "The Module entry and its requirements describe retries but give no limit.",
    "owner_target_id": "module.payments",
    "evidence": [
      {"path": "specs/payments/module.md", "description": "Retry section without a limit"}
    ]
  }
}
```

## Receipt

```concorde-contract
{
  "id": "contract.issues.receipt",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["issue_id", "report_id", "path"],
    "properties": {
      "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
      "report_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
      "path": {"type": "string", "pattern": "^\\.concorde/issues/I-[0-9a-f]{32}\\.md$"}
    }
  },
  "semantics": "The durable name of one accepted report, registered as typed value concorde-issue-receipt. report_id is the digest of the report together with its Host-supplied provenance, so the receipt always names that one immutable report, even after later reports or dispositions of the same Issue. path is the record file of issue_id. A receipt is returned only after the record is on disk. The report_issue tool answers {receipt, revision}, where revision is the digest of the record file after the write and is usable as a later expected_revision.",
  "example": {
    "issue_id": "I-0123456789abcdef0123456789abcdef",
    "report_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "path": ".concorde/issues/I-0123456789abcdef0123456789abcdef.md"
  }
}
```

## Blocker

```concorde-contract
{
  "id": "contract.issues.blocker",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["issue_id", "report_id", "path", "blocked_step"],
    "properties": {
      "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
      "report_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
      "path": {"type": "string", "pattern": "^\\.concorde/issues/I-[0-9a-f]{32}\\.md$"},
      "blocked_step": {"type": "string", "minLength": 1}
    }
  },
  "semantics": "A stage result's statement that the report named by the receipt fields stops one step of its task; blocked_step names that step. A Blocker is a judgment of the result that lists it, not a second problem record: it carries no problem text. A review finding's reference with severity blocking becomes the Blocker whose blocked_step is the finding's affected_task. Disposing the Issue does not release a Blocker, and releasing a Blocker does not dispose the Issue.",
  "example": {
    "issue_id": "I-0123456789abcdef0123456789abcdef",
    "report_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "path": ".concorde/issues/I-0123456789abcdef0123456789abcdef.md",
    "blocked_step": "Choose the retry limit for failed payments"
  }
}
```

## Issue selection

```concorde-contract
{
  "id": "contract.issues.selection",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["type_id", "schema_version", "data"],
    "properties": {
      "type_id": {"const": "concorde-issue-selection"},
      "schema_version": {"type": "integer", "const": 1},
      "data": {
        "type": "object",
        "additionalProperties": false,
        "required": ["issue_id", "revision", "problem", "type", "feedback", "verification",
                     "duplicates"],
        "properties": {
          "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
          "revision": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
          "problem": {"type": "string", "minLength": 1},
          "type": {"enum": ["bug", "gap", "limitation"]},
          "feedback": {"type": "string"},
          "verification": {"type": "string"},
          "duplicates": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["issue_id", "revision", "problem"],
              "properties": {
                "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
                "revision": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                "problem": {"type": "string", "minLength": 1}
              }
            }
          }
        }
      }
    }
  },
  "semantics": "One selected Issue given to a model call as task material. revision is the record digest the selection was made at. problem is the latest report's description and impact, type its classification. feedback carries the developer's clarification and the previous step's feedback, possibly empty; verification summarizes a completed verification, possibly empty. duplicates lists other open Issues offered as possible duplicates, each at the revision it was offered. A reporter whose call received a selection may append reports to the selected Issue. The selection adds no source to the call's context.",
  "example": {
    "type_id": "concorde-issue-selection",
    "schema_version": 1,
    "data": {
      "issue_id": "I-0123456789abcdef0123456789abcdef",
      "revision": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "problem": "A transfer leaves the balance unchanged.\nImpact: Customers see stale balances.",
      "type": "bug",
      "feedback": "",
      "verification": "",
      "duplicates": []
    }
  }
}
```

## Issue context

```concorde-contract
{
  "id": "contract.issues.context",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["type_id", "schema_version", "data"],
    "properties": {
      "type_id": {"const": "concorde-issue-context"},
      "schema_version": {"type": "integer", "const": 1},
      "data": {
        "type": "object",
        "additionalProperties": false,
        "required": ["observations"],
        "properties": {
          "observations": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["receipt", "description", "impact", "basis"],
              "properties": {
                "receipt": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["issue_id", "report_id", "path"],
                  "properties": {
                    "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
                    "report_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                    "path": {"type": "string", "minLength": 1}
                  }
                },
                "description": {"type": "string", "minLength": 1},
                "impact": {"type": "string", "minLength": 1},
                "basis": {"type": "string", "minLength": 1}
              }
            }
          }
        }
      }
    }
  },
  "semantics": "The problem text of referenced reports given to a later model call. Each observation holds one receipt, at most once, with that exact report's description, impact and basis, never the whole record, its provenance or later reports. A reporter whose call received an Issue context may cite those receipts in its result and may append to their Issues. The context adds no source to the call's context.",
  "example": {
    "type_id": "concorde-issue-context",
    "schema_version": 1,
    "data": {
      "observations": [
        {
          "receipt": {
            "issue_id": "I-0123456789abcdef0123456789abcdef",
            "report_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "path": ".concorde/issues/I-0123456789abcdef0123456789abcdef.md"
          },
          "description": "No Spec of module.payments states how often a failed payment is retried.",
          "impact": "Planning cannot choose a retry limit without inventing a promise.",
          "basis": "The Module entry and its requirements describe retries but give no limit."
        }
      ]
    }
  }
}
```

## Provenance

The caller of the reporting service supplies the provenance of every report, never the reporter:

| Field | Meaning |
| --- | --- |
| `invocation_id` | the invocation the reporter belongs to |
| `agent` | the reporting Agent, `host` or `developer` |
| `operation` | the capability the invocation runs |
| `phase` | the stage, or `report` for the developer's action |
| `target_id` | the reporting Module |
| `context_id` | digest of the reporter's context |
| `change_id`, `head` | the change and Git `HEAD`, each nullable |

## Record file

A record lives at `.concorde/issues/<issue_id>.md` and is exactly: the line `# <issue_id>`, a blank
line, a `json` fence holding the record serialized with two-space indentation, and the closing
fence. Nothing else may appear in the file. A record is at most 16 MiB.

The record has `schema_version: 2`, `id`, `status` (`open` or `closed`), `reports` (at least one)
and `dispositions`. Each entry of `reports` is `{id, created_at, report, source}`, with `source`
the provenance and `id` the digest of `{report, source}`. Each disposition is
`{reason, note, evidence, duplicate_of, actor, created_at}`, where `reason` is `resolved`,
`duplicate`, `not-actionable` or `reopened`, `evidence` is a nonempty list of unique strings and
`duplicate_of` is another Issue identity for `duplicate` and `null` otherwise.

A record is valid only when:

- its `id` is `I-` plus the hex form of the UUIDv5 (URL namespace) of the canonical JSON
  `[invocation_id, report_key]` of its first report, and it matches the file name;
- every report's `id` matches its content, and no two reports share an `id` or an
  `(invocation_id, report_key)` pair;
- every report is itself a valid report of this Issue;
- dispositions alternate from open: a closing reason only while open, `reopened` only while
  closed, and `status` equals the state after the last disposition.

An Issue's owner is the latest report's `owner_target_id`, or that report's reporting Module when
the owner is `null`. Its revision is the SHA-256 digest of the file's bytes.

## Store operations

These are Host library operations. None launches a model or runs Git.

| Operation | Behaviour |
| --- | --- |
| `report_issue(root, report, source)` | Validates, then under the lock: returns the existing receipt when the same `(invocation_id, report_key)` already holds identical content; fails with `issue_key_conflict` for different content; otherwise creates the record or, for an append, checks `expected_revision` (`stale_issue`) and open status (`closed_issue`) and appends. |
| `read_issue(root, id)` | Returns the record and its revision; `unknown_issue` when absent, `invalid_issue` when malformed or oversized. |
| `list_issues(root, target_id, status)` | Returns summary rows filtered by reporting Module or latest owner and by status, whether or not the owner is a registered Module. An absent directory yields an empty list and is not created. |
| `resolve_report(root, receipt)` | Returns the exact report the receipt names, never the latest one; `stale_issue` when it is absent. |
| `disposition_record(record, ...)` | Prepares and validates a disposed record without writing. |
| `dispose_issue(root, id, expected_revision, ...)` | Under the lock, checks the revision (`stale_issue`), and for `duplicate` that the other Issue exists, is open and, when given, still has `duplicate_revision`; appends the disposition and returns the new revision. |
| `restore_issue(root, id, original, expected_revision)` | Under the lock, writes the open `original` bytes only over exactly `expected_revision`; does nothing when `original` is already on disk; otherwise `stale_issue`. |

Every write runs under the exclusive lock `.concorde/runs/issues.lock` of the primary worktree,
which serializes the writes of all worktrees of the repository. It checks the file's previous
digest, publishes a staged file through a file transaction, and syncs the directory before
returning. A failed write is never reported as success. No operation deletes a record file.

## Reporting service

A caller binds one reporting service for one reporter before the reporter starts, with:

- **provenance**, as above; its `target_id` must be among the admitted owners;
- **admitted owners**: the Modules the reporter may name as `owner_target_id`;
- **evidence paths**: the files the reporter may cite;
- **selected Issues**: the Issues the reporter may append to, besides those it created itself in
  this call;
- **admitted receipts**: the receipts the reporter was given, which its result may reference.

For an Agent call, Agent execution derives these from the call's frozen context: the bound Module,
the Modules it uses and the owner of every selected Spec document as owners; every selected Spec
document path, every implementation file in the snapshot and every path of a review patch as
evidence paths; the Issues of an Issue selection and of an Issue context as selected Issues. For
the developer's `report` action the agent is `developer` and the phase `report`.

A report naming an owner outside the admitted owners, evidence outside the evidence paths, or an
append to an Issue neither selected nor created earlier by the same service fails with
`permission_denied`. The service answers `{receipt, revision}`.

## References

| Operation | Behaviour |
| --- | --- |
| `validate_references(root, references, admitted)` | Every reference must name a receipt the reporter created or was admitted (`permission_denied`), at most once (`invalid_completion`), and must resolve to its report (`stale_issue`). |
| `review_blockers(references)` | Turns each finding reference of severity `blocking` into the Blocker with `blocked_step` equal to its `affected_task`. |
| `observation_context(root, references)` | Builds the Issue context of the referenced reports. |
| `requires_contract_repair(root, references)` | True when a referenced report is a `gap` of subtype `missing-contract` or `spec-conflict`. |

## Store check

`python3 scripts/issues.py check [--root <path>]` reads every record under `.concorde/issues/` and
the project registry, prints one JSON finding per problem and exits nonzero when any record is
invalid or any open Issue's owner is not a registered Module. A closed Issue with an unknown owner
is printed as a finding and does not change the exit status. An absent directory passes. Concorde's
configuration registers it as:

```json
{"id": "check.issues.store", "module": "module.issues",
 "argv": ["{python}", "scripts/issues.py", "check"],
 "timeout_seconds": 60,
 "inputs": [".concorde/issues", ".concorde/specs.json"]}
```

`list` and `show <id>` print the summary rows or one record with its revision. The script refuses a
directory that is not an initialized Concorde project.

## Errors

| Code | Meaning |
| --- | --- |
| `unknown_issue` | the named Issue does not exist |
| `invalid_issue` | a malformed, oversized or inconsistent report or record |
| `issue_key_conflict` | a report key reused for different content |
| `stale_issue` | the record changed since the caller's revision, or a receipt names no report |
| `closed_issue` | an append to a closed Issue |
| `permission_denied` | an owner, evidence path, append or reference outside the reporter's limits |
| `invalid_completion` | a result references the same report twice |
