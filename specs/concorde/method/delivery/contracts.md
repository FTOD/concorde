# Delivery contracts

The exact commit and output of the
[execution command](../../glossary.json#concept.execution-command) `delivery` of
[Delivery](module.md).

## Delivery commit

```text
concorde: deliver <workspace>

<goal of the workspace>
```

The commit uses the repository's configured author identity. It runs the repository's commit hooks
normally. Its parent is the head of the workspace's bound branch that the delivery validated. The
readiness examined that branch's commits since the base commit.

The commit contains every uncommitted change of the workspace that Git does not ignore, with one
exception. It excludes the untracked paths Validation's
[input measurement](../validation/contracts.md#input-measurement) leaves out as no content of the
task. Delivery commits only when a checkout of the staged index gives back what the readiness
examined. When every step was committed before, the commit changes nothing. In that case, it is
still made as the mark of the delivery.

The [delivery commits](../../glossary.json#concept.delivery-commit) are the only record of a
delivery. The Kernel's convention defines which commit is a delivery commit of a workspace
([Kernel contracts](../../kernel/contracts.md#delivery-commit)). It also defines when one verifies.
Delivery reads its earlier deliveries by that rule. Every commit it creates has exactly one
parent.

Delivery reports a delivery commit it finds at the branch head only when both conditions hold:

- The delivery commit verifies.
- The workspace it holds is ready again, as a readiness the same run decided shows.

A delivery commit Delivery creates verifies further when all of these conditions hold:

- Its only parent is the head it validated.
- Its subject is exactly the subject above.
- Its tree is the tree `git write-tree` recorded from the index after staging.

These conditions ensure that no commit hook changed what was committed or its mark. When such a
commit does not verify, Delivery takes it off the branch again in the same run. Since only the
subject marks a delivery, a commit message hook may add to the body, such as a trailer.

## Output

```concorde-contract
{
  "id": "contract.delivery.output",
  "version": 6,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "commit",
      "branch",
      "sequence",
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
      "recovered": {
        "type": "boolean"
      }
    }
  },
  "semantics": "The output of a delivery run whose status is ok. commit is the delivery commit, now the head of branch, the workspace's bound branch; sequence is its number among the workspace's delivery commits on the branch, counting from 1. recovered is true when the run found that the branch head already is a delivery commit of the workspace that verifies, as the delivery commit section defines, and nothing waits to be delivered, such as after a delivery whose run ended after its commit, validated the workspace again and found it ready, and reports that commit instead of committing. A head that is a delivery commit but does not verify ends the run failed with commit_unverified; one whose workspace is not ready ends it blocked, as a new delivery would. A run whose status is not ok has no output. A behaviour or field change increments the version.",
  "example": {
    "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
    "branch": "concorde/severity",
    "sequence": 1,
    "recovered": false
  }
}
```
