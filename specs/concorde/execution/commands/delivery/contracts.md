# Delivery contracts

The exact commit and output of the
[execution command](../../../glossary.json#concept.execution-command) `delivery` of
[Delivery](module.md).

## Delivery commit

```text
concorde: deliver <workspace>

<goal of the workspace>
```

The commit uses the repository's configured author identity and runs the repository's commit hooks
normally. Its parent is the head of the workspace's bound branch that the delivery validated, whose
commits since the base commit the readiness examined. It contains every uncommitted change of the
workspace that Git does not ignore, except the untracked paths Validation's
[input measurement](../validation/contracts.md#input-measurement) leaves out as no content of the
task, and the metadata changed by the applied confirmations; when
every step was committed before and nothing was confirmed, it changes nothing and is still made, as
the mark of the delivery.

The [delivery commits](../../../glossary.json#concept.delivery-commit) are the only record of a
delivery. A commit is a delivery commit of a workspace when it lies on the first-parent history of
the branch since the base commit and its subject is exactly `concorde: deliver <workspace>`.
Delivery reads its earlier deliveries this way, and so may anyone who needs to know whether and how
often a workspace was delivered.

A delivery commit **verifies** when it has exactly one parent, as every commit Delivery creates has.
Delivery reports a delivery commit it finds at the branch head only when it verifies. A delivery
commit Delivery creates verifies further when its only parent is the head it validated and its tree
is the tree `git write-tree` recorded from the index after staging, so that no commit hook changed
what was committed.

## Output

```concorde-contract
{
  "id": "contract.delivery.output",
  "version": 4,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "commit",
      "branch",
      "sequence",
      "confirmed",
      "recovered"
    ],
    "properties": {
      "commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "branch": {
        "type": "string",
        "minLength": 1
      },
      "sequence": {
        "type": "integer",
        "minimum": 1
      },
      "confirmed": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "recovered": {
        "type": "boolean"
      }
    }
  },
  "semantics": "The output of a delivery run whose status is ok. commit is the delivery commit, now the head of branch, the workspace's bound branch; sequence is its number among the workspace's delivery commits on the branch, counting from 1; confirmed lists the realization entries whose pending markers the delivery cleared. recovered is true when the run found that the branch head already is a delivery commit of the workspace that verifies, as the delivery commit section defines, and nothing waits to be delivered, such as after a delivery whose run ended after its commit, and reports that commit instead of committing; confirmed is then empty. A head that is a delivery commit but does not verify ends the run failed with commit_unverified. A run whose status is not ok has no output. A behaviour or field change increments the version.",
  "example": {
    "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
    "branch": "concorde/severity",
    "sequence": 1,
    "confirmed": [
      "src/concorde/issues/severity.py"
    ],
    "recovered": false
  }
}
```
