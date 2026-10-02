# Kernel contracts

The canonical formats of the [Kernel](module.md): the
[workspace binding](../glossary.json#concept.workspace-binding), the
[delivery commit](../glossary.json#concept.delivery-commit), and the
[typed values](../glossary.json#concept.typed-value) and
[file transactions](../glossary.json#concept.file-transaction) parts exchange and write.
[Trace nodes](../glossary.json#concept.trace-node), locks and error links are its child [Tracing](tracing/contracts.md)'s.

## Workspace binding

```concorde-contract
{
  "id": "contract.kernel.workspace-binding",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "workspace",
      "root",
      "branch",
      "base_commit",
      "goal",
      "modules",
      "traces",
      "concorde"
    ],
    "properties": {
      "schema_version": {
        "const": 2
      },
      "workspace": {
        "type": "string",
        "pattern": "^[a-z0-9][a-z0-9-]{0,47}$"
      },
      "root": {
        "type": "string",
        "minLength": 1
      },
      "branch": {
        "type": "string",
        "minLength": 1
      },
      "base_commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "goal": {
        "type": "string",
        "minLength": 1
      },
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "string",
          "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
        }
      },
      "traces": {
        "type": "string",
        "minLength": 1
      },
      "concorde": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "semantics": "The workspace binding .concorde/workspace.json at the root of a workspace. workspace names it, as runs, locks, workflow nodes and delivery commits name it. root is the absolute real path of the worktree the file lies in; a binding whose root is another worktree is refused. branch is the branch the workspace works on, which task-validation and delivery require the worktree's head to be on; base_commit is the commit its changes are measured from; goal is the text workers are briefed with and a delivery commit carries; modules are the Modules a run works on when it names none. traces is the absolute workspace folder in which the parts that work in the workspace keep its trace nodes: its runs under runs/ and its workflow under workflow/; whoever prepares the workspace chooses it, and it must exist. concorde is the absolute .concorde directory whose locks/ holds the workspace's locks and the run locks of its runs. Whoever prepares the workspace writes the file; the parts that work in it only read it. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 2,
    "workspace": "retry",
    "root": "/home/dev/shop/.claude/worktrees/retry",
    "branch": "concorde/retry",
    "base_commit": "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
    "goal": "Limit HTTP retries to three attempts.",
    "modules": [
      "module.http"
    ],
    "traces": "/home/dev/shop/.concorde/tasks/retry/workspace",
    "concorde": "/home/dev/shop/.concorde"
  }
}
```

A binding that breaks this contract is refused by every part that reads it, never read in part. A
binding whose `root` is not the real path of the worktree it lies in is refused too, since a copied
binding would bind the wrong workspace. Git ignores the file. The [Modules](../glossary.json#concept.module) it names are Module
identities as text: a part that knows the project's Specs checks them against the registry, and a
part that does not treats them as labels.

## Delivery commit

```text
concorde: deliver <workspace>

<goal of the workspace>
```

A commit is a **delivery commit** of a workspace when it lies on the first-parent history of the
workspace's branch since the binding's base commit and its subject is exactly
`concorde: deliver <workspace>`, with the workspace's name. Its body is the workspace's goal. The
delivery commits are the only record of a delivery: anyone who needs to know whether and how often a
workspace was delivered reads them from the branch this way, and no part keeps a list of its own.

A delivery commit **verifies** when it has exactly one parent. A head that carries the subject but
has another number of parents, such as a merge commit, is no delivery: every part that reads
delivery commits refuses to treat it as one and names the mismatch.

Only a delivering command makes a delivery commit, and each states what it checks first: Method's
`delivery` validates the whole workspace ([Delivery](../method/delivery/contracts.md#delivery-commit)),
and Coordination's `task deliver`, which exists only where the method part is not installed, runs
the checks it is given ([Tasks](../coordination/tasks/module.md)). Each makes the commit with the
repository's configured author identity, runs the repository's commit hooks normally, and puts in it
every uncommitted change of the workspace that Git does not ignore; when everything was committed
before, it changes nothing and is still made, as the mark of the delivery. A workspace may be
delivered several times, each delivery a new commit on top, never amended.

## Typed values

A **typed value** is a closed JSON object `{"type_id": ..., "schema_version": ..., "data": ...}`.
`type_id` is a nonblank name such as `concorde-run-result`, `schema_version` a positive integer, and
`data` the value's content, checked against the schema the type's owner registered for that version.

- **Registration.** The part that owns a type registers its schema when its code is loaded.
  Registering an identity already registered with the same version and an equal schema changes
  nothing; another version or schema for the same identity is refused as `duplicate_type`, and the
  existing registration stays in force. The kernel registers no type of any part and imports no
  part, so whoever checks a value must have loaded the code of the value's owner.
- **Embedding.** A registered schema may embed another owner's type by name, resolved when a value
  is checked, so one part's record may hold another part's value without importing it; a reference
  to a type still unregistered at check time fails with `unknown_type`.
- **Checking.** A value of another version fails with `unsupported_version`, an unregistered type
  with `unknown_type`, a value of the wrong type where one is expected with `incompatible_handoff`,
  and any other mismatch with `invalid_field`, naming the JSON pointer of the offending field. A
  checked value is returned as a copy, never shared with its caller.
- **Schemas.** A registered schema uses the offline JSON Schema subset that every
  `concorde-contract` fence uses: no keyword that loads another document or a remote resource, no
  keyword the checker does not evaluate, and closed objects spelled with
  `additionalProperties: false`, so that no registered type promises more than its values are
  checked for.
- **Paths and artifacts.** A path inside a value is a canonical project-relative POSIX path: no
  leading `/`, no backslash, colon or control character, no empty, `.` or `..` component. An
  artifact is `{id, path, digest}`, its digest `sha256:` and 64 lowercase hexadecimal digits of the
  file's bytes, and a value whose artifact's bytes changed is refused as `stale_reference`.

The Spec tooling keeps its own copy of this format in its own code, so that the spec part installs
alone ([Spec core](../spec-tooling/spec/contracts.md#typed-values)); the two agree on the format,
not on code.

## File transactions

A **file transaction** writes a set of whole files, each bound to the digest of the bytes it
replaces (or to the file's absence), completely or not at all:

- it is refused before any write when a change is malformed, names a path twice or outside the
  paths the caller allows, or when a file's current bytes do not match the digest it replaces
  (`stale_proposal`), checked once before any write and again just before each write;
- each file is written to a temporary file in its own directory, flushed and renamed into place;
- after the last write the caller's optional final check runs; when it or any write fails, every
  written file is restored to its original bytes, or removed when it did not exist, and the failure
  reaches the caller unchanged, with every file that could not be restored named and said to hold
  its new content.

These guarantees hold for failures the process observes. A killed process restores nothing: each
file already renamed into place keeps its new content, every other file its original bytes, and
temporary files may remain beside them. The Spec tooling keeps its own copy of this mechanism, with
its own error types ([Spec core](../spec-tooling/spec/contracts.md#file-transactions)).
