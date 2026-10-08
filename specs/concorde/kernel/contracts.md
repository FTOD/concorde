# Kernel contracts

The [Kernel](module.md) defines the canonical formats that parts exchange and write:

- The [workspace binding](../glossary.json#concept.workspace-binding).
- The [delivery commit](../glossary.json#concept.delivery-commit).
- The [unfinished-merge marker](../glossary.json#concept.unfinished-merge-marker).
- The [typed values](../glossary.json#concept.typed-value).
- The [file transactions](../glossary.json#concept.file-transaction).

Its child [Tracing](tracing/contracts.md) owns these formats:

- [Trace nodes](../glossary.json#concept.trace-node).
- Locks.
- Error links.

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

When a binding breaks this contract, every part that reads it refuses it.
No part reads such a binding in part. Before writing a binding that breaks this contract, the
library refuses it. When a binding's `root` is not the real path of the worktree it lies in,
the binding is refused too. The reason is that a copied binding would bind the wrong workspace.
When a `root` is not an absolute real path, it breaks the contract.
Examples are a symbolic link to the worktree or a path ending in `/.`.
The real path of another worktree is a misplaced binding. Git ignores the file.
The [Modules](../glossary.json#concept.module) it names are Module identities as text.
When a part knows the project's Specs, it checks those identities against the registry.
When a part does not know the project's Specs, it treats those identities as labels.

## Delivery commit

```text
concorde: deliver <workspace>

<goal of the workspace>
```

When both conditions hold, a commit is a **delivery commit** of a workspace:

- It lies on the first-parent history of the workspace's branch since the binding's base commit.
- Its subject is exactly `concorde: deliver <workspace>`, with the workspace's name.

Its body is the workspace's goal. The delivery commits are the only record of a delivery.
To know whether and how often a workspace was delivered, anyone reads its delivery commits from
the branch this way. No part keeps a list of its own.

When a delivery commit has exactly one parent, it **verifies**.
When a delivery commit has another number of parents, it does not verify.
A merge commit given the subject is an example.
For such a delivery commit, every part that reads delivery commits refuses to take the workspace
as delivered by that commit. Every such part names the mismatch.
A delivery commit is made with the repository's configured author identity.
A delivery commit is made with the repository's commit hooks.
A delivery commit is never amended.
When a workspace is delivered again, it gets a new delivery commit on top.
Thus, the first-parent history keeps every delivery.

This convention says what a delivery commit is, not who makes one.
The delivering command's own rules state these matters in its [Spec](../glossary.json#concept.spec):

- Which command may make the delivery commit.
- What the command checks before making the delivery commit.
- Which of the workspace's changes the delivery commit holds.

An example of the last matter is every change Git does not ignore less the untracked paths the
command's own validation leaves out. In Concorde, Method's
[`delivery`](../method/delivery/contracts.md#delivery-commit) states these rules.
Where the method part is not installed, Coordination's
[`task deliver`](../coordination/tasks/module.md) states these rules. Nothing here relies on either.

## Unfinished-merge marker

```concorde-contract
{
  "id": "contract.kernel.unfinished-merge",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "part",
      "by",
      "pid",
      "since",
      "branch",
      "before",
      "merging",
      "after",
      "finish"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "part": {
        "type": "string",
        "pattern": "^[a-z][a-z0-9_-]*$"
      },
      "by": {
        "type": "string",
        "minLength": 1
      },
      "pid": {
        "type": "integer",
        "minimum": 1
      },
      "since": {
        "type": "string",
        "minLength": 1
      },
      "branch": {
        "type": "string",
        "minLength": 1
      },
      "before": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "merging": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "after": {
        "anyOf": [
          {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          {
            "type": "null"
          }
        ]
      },
      "finish": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "string",
          "minLength": 1
        }
      }
    }
  },
  "semantics": "The unfinished-merge marker .concorde/unfinished-merge.json of the primary worktree, which Git ignores. part names the part that wrote it, the only one that replaces or removes it. by names the command that merges, pid its process and since when it began. branch is the primary branch the merge changes, before its commit before the merge, merging the commit merged in and after the merge commit once it exists, else null. finish lists the commands that finish an unfinished merge, each of which decides it and removes the marker. The writer holds the merge lock while it writes, replaces or removes the marker; it writes the marker before it changes the primary branch or records the merge anywhere, and removes it only after the merge is decided and its own records say so. Every other part that commits on the primary branch reads the marker while it holds the merge lock and refuses, committing nothing, while the marker is present or cannot be read. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "part": "coordination",
    "by": "`concorde task merge` of task severity",
    "pid": 41822,
    "since": "2026-10-08T09:14:03+00:00",
    "branch": "main",
    "before": "3d15110b5361942cb600c30b7baaae2cf3dd5c9f",
    "merging": "8c2e0a51f4b7d9e3a6c1b0f2e4d6a8c0b2e4f6a8",
    "after": null,
    "finish": [
      "concorde task merge severity --resume",
      "concorde task merge severity --abort"
    ]
  }
}
```

The marker lies at `.concorde/unfinished-merge.json` of the primary worktree, beside `locks/` but
not inside it. The Kernel's registration names it among the paths Git ignores. Thus, the marker
never makes the primary worktree dirty. The marker is written in one rename. A reader therefore
finds either no marker, the whole earlier marker or the whole new one.

The writer keeps this order while it holds the merge lock:

1. It writes the marker.
2. It records the merge in its own records and changes the primary branch.
3. It writes the marker again whenever a field changes, such as `after` once the merge commit
   exists.
4. Once the merge is decided, kept or undone, it records that in its own records.
5. It removes the marker.

A crash after step 1 and before step 5 leaves the marker. A marker whose writer's own records say
that no merge is unfinished is one a crash left at step 1 or step 5. Only its writer can tell, so
only the writer removes it. A writer that cannot write the marker at step 1 changes nothing.
A writer that cannot replace or remove it leaves the earlier marker, which still refuses every
commit. The writer removes it once it can.

A reader holds the merge lock. A marker present then belongs to a writer that ended, or to one that
handed the lock on after it removed the marker. The reader refuses its commit with its own error
link. The link carries the marker's account: who was merging what into which branch, where the
primary worktree's head is now and the commands that finish the merge. A marker that cannot be read
or breaks its contract refuses the commit too. Its refusal names the file.

## Typed values

A **typed value** is a closed JSON object `{"type_id": ..., "schema_version": ..., "data": ...}`.
Its fields have these meanings:

- `type_id` is a nonblank name such as `concorde-run-trace`.
- `schema_version` is a positive integer.
- `data` is the value's content.

The content is checked against the schema the type's owner registered for that version.
Only when its owner's contract designates a value as typed does the value carry the envelope.
A trace node's `content` is an example.
When a record's contract defines its own representation, the record is checked against that
contract's schema as it is. Examples are:

- The workspace binding above.
- A [run result](../glossary.json#concept.run-result).
- A grant.

- **Registration.** When its code is loaded, the part that owns a type registers one schema under
  the type's identity and one version.
  Registering an identity already registered with the same version and an equal schema changes
  nothing. For the same identity, another version or schema is refused as `duplicate_type`.
  In that case, the existing registration stays in force.
  The Kernel registers no type of any part. The Kernel imports no part.
  Thus, whoever checks a value must have loaded the code of the value's owner.
- **Embedding.** A registered schema embeds a whole typed value of another owner's type with the
  reference `{"$ref": "<type_id>"}`. This reference is a bare type identity rather than a JSON
  pointer. The reference stands alone.
  A schema holding such a `$ref` has no other keyword.
  When a value is checked, the reference is resolved against the registration in force then.
  The reference matches the whole envelope:

  - `type_id` equals that identity.
  - `schema_version` equals its registered version.
  - `data` matches its registered schema.

  So one part's record holds another part's value without importing it.
  When a type is still unregistered at check time, a reference to that type fails with
  `unknown_type`. For example, a type `example-batch` has this schema:
  `{"type": "object", "additionalProperties": false, "required": ["runs"], "properties": {"runs":
  {"type": "array", "items": {"$ref": "concorde-run-trace"}}}}`.
  The type checks each element of `runs` as a whole `concorde-run-trace` value.
  While the referenced type is not registered, the check fails with `unknown_type` at `/data/runs/0`.
- **Checking.** Checking fails as follows, naming the JSON pointer of the offending field:

  - A value of another version fails with `unsupported_version`.
  - An unregistered type fails with `unknown_type`.
  - Where one type is expected, a value of the wrong type fails with `incompatible_handoff`.
  - Any other mismatch fails with `invalid_field`.

  A checked value is returned as a copy. The checked value is never shared with its caller.
- **Paths and artifacts.** When a field's registered schema gives it `"format": "project-path"`,
  the field is a canonical project-relative POSIX path. Such a path has these properties:

  - It is nonempty.
  - It has no leading `/`.
  - It has no backslash.
  - It has no colon.
  - It has no control character.
  - It has no empty component.
  - It has no `.` component.
  - It has no `..` component.

  An **artifact** is an object with exactly these keys:

  - `id`.
  - `path`.
  - `digest`.

  Its `path` is a project path relative to a root.
  Its digest is `sha256:` and 64 lowercase hexadecimal digits of the file's bytes.
  Checking a typed value never reads a file.
  Artifacts are made and verified by operations of their own over a root the caller chooses.
  The reason is that only the caller knows in which worktree its record lives.
  Making an artifact digests a file that must exist below the root.
  Verifying a value walks the whole value.
  Verification treats every object with exactly those three keys as an artifact.
  When an artifact's file is missing or its bytes changed, verification refuses the artifact as
  `stale_reference` ([Library](#library)).
  When an array's `items` schema is the library's artifact schema, the array lists each artifact
  once. That schema requires those three keys. That schema admits no other key.
  In such an array, two artifacts with the same `id` or the same `path` are refused with
  `invalid_field`.
  Below its root, the file an artifact or a [file transaction](#file-transactions) names is reached
  only through real directories.
  When any path component is a symbolic link, the path is refused.
  That refusal names the path and the link.
  For an artifact, that refusal uses `invalid_field`.
  For a file transaction, that refusal treats the list as malformed (`invalid_proposal`).
  Every other path is what its owner's schema says, an absolute location included.
  A task trace's worktree or the evidence a run result keeps are never rewritten.

### Registered schemas

A registered schema is written in the following dialect of JSON Schema. The dialect needs no
network. It loads no document. A schema is an object or a boolean. Its keywords are:

- `title`
- `description`
- `examples`
- `default`
- `type` with one type name
- `properties`
- `required`
- `additionalProperties` (a boolean or a schema)
- `items`
- `minItems`
- `maxItems`
- `uniqueItems`
- `minLength`
- `maxLength`
- `pattern`
- `minimum`
- `maximum`
- `enum`
- `const`
- `anyOf`
- `format` with the one format `project-path`
- `$ref` with a bare type identity as above

When the schema is registered, the Kernel refuses any of the following with `invalid_input`:

- Any other keyword.
- A list of types.
- A `$ref` of another form.
- An invalid bound.
- Nesting deeper than 100 levels.

Thus, no registered type promises more than its values are checked for. For a repeated registration,
two schemas are equal when they are equal as JSON values, as below.

For these keywords, a value is checked as JSON Schema checks it. Unless its
`additionalProperties` is `false`, an object admits keys its `properties` do not name. When
`additionalProperties` is a schema, the object checks those keys against that schema. Thus, a
closed object spells `additionalProperties: false`. `number` admits integers and finite
non-integral numbers. `integer` admits only integers. Neither admits a boolean. `minimum` and
`maximum` bound both. Unless it is anchored, `pattern` matches anywhere in the string. The
following keywords compare values as JSON values:

- `const`
- `enum`
- `uniqueItems`

The comparison follows these rules:

- Numbers compare by value. Thus, `1` equals `1.0`.
- A boolean compares only with a boolean. Thus, `true` is not `1`.
- Arrays and objects compare item by item and field by field under the same rule.

Whether the schema names a `type` or not, each keyword applies to the kind of value it constrains.
When a string's schema sets `minLength`, the string must not consist of whitespace only.
However, `minLength` `0` still admits the empty string. A number is finite. When a JSON text holds
a number too large for a finite floating-point value, the JSON text is no JSON value (`invalid_json`). An
integer of any size is checked by its value. Checking a value descends at most 100 levels. Each of
the following counts one level:

- Each field of an object.
- Each item of an array.
- Each `anyOf` alternative tried.
- Each `$ref` followed.
- Each `data` of an embedded typed value.

When checking a value would go deeper, the Kernel refuses the value with `invalid_field` at the
field reached.

### Contract schemas

A record whose own contract defines its representation carries no envelope. Such records include:

- A workspace binding.
- A [run result](../glossary.json#concept.run-result).
- An error link.

The part that owns the record checks it against a **contract schema** as code. A contract schema
is the schema the record's contract gives. A contract schema is written in the registered dialect
with one addition. At its top, it admits an object `$defs` of named schemas. Anywhere in the
contract schema, `{"$ref": "#/$defs/<name>"}` refers to these named schemas. This permits the
description of a recursive record such as an error link with its causes. When a `$defs` occurs
anywhere else, the Kernel refuses it, naming its JSON pointer. A local reference must name an
entry of `$defs`. A bare type identity embeds a typed value as above. When a contract schema is
first used, the Kernel checks it against the dialect (`invalid_input`). When a record breaks the
contract schema, the Kernel refuses it with `invalid_field`, naming the JSON pointer of the
offending field. The contract schema is never registered.

The `concorde-contract` fences of the Specs use a wider dialect of their own, with `oneOf` and
`allOf` besides. This wider dialect belongs to the Spec tooling that checks the fences. Neither
a registered nor a contract schema of the Kernel uses those keywords. The Spec tooling keeps its
own copy of this registered dialect and of the typed value format in its own code. Thus, the spec
part installs alone ([Spec core](../spec-tooling/spec/contracts.md#typed-values)). The two agree
on this text, not on code.

## File transactions

A **file transaction** writes a set of whole files below a root its caller names. Each file is
bound to the bytes it replaces. It takes a nonempty list of changes, each with this form:

```json
{"path": "<project-relative path below the root>", "before_digest": "sha256:<64 hex digits> or null", "content": "<the file's new text>"}
```

The fields follow these rules:

- `path` follows the `project-path` rule above. It names a file once in the list.
- `content` is the whole new file as text written in UTF-8.
- `before_digest` is the digest of the file's current bytes: `sha256:` and 64 lowercase hexadecimal
  digits. When the file must not exist, `before_digest` is `null`.

When a `before_digest` has any other form, the list is malformed. The caller also names the paths
it allows. Optionally, the caller names a final check to run after the writes.

1. Before any write, the transaction refuses any of the following:
   - A malformed list (`invalid_proposal`).
   - A path outside the allowed ones (`permission_denied`).
   - A file whose current bytes, or existence, do not match its `before_digest` (`stale_proposal`).

   Just before each write, the transaction checks the match again.
2. The transaction writes each file to a temporary file in its own directory. The temporary file's
   name is `.concorde-write-` and a random suffix. The transaction flushes the temporary file.
   It then renames the temporary file into place.
3. After the last write, the final check runs. On success, the transaction returns the written paths
   in order.
4. When a write or the final check fails, the transaction restores every file written so far
   through the same temporary file and rename. When a file originally exists, the transaction
   restores its original bytes. When a file originally does not exist, the transaction removes it.

What the caller then receives:

- When every restoration succeeds, the caller receives the applicable failure:
  - The failure of the final check exactly as the check raises it.
  - A refusal of step 1 or a `stale_proposal` of a later write as such.
  - An operating-system error of a write as `system_error`.

  For that `system_error`, the transaction names the file. It says that every file written so far
  is restored. It gives the operating system's error as its cause.
- When the operating system refuses a restoration, the transaction still attempts the other
  restorations. In that case, the transaction fails with `system_error`. The error names every
  file not restored. It says each such file still holds its new content. It has the first failure
  as its first cause. It has one cause per refused restoration. The caller must not treat that
  outcome as restored. The caller recovers the named files by its own records' rule, as it does after a
  killed process.

These guarantees hold for failures the process observes. They include an interruption the process
receives, such as `KeyboardInterrupt` or `SystemExit`. Once every file is restored, the process
raises the interruption again unchanged. A killed process restores nothing. After a killed
process, the files have these states:

- Each file already renamed into place keeps its new content.
- Every other file keeps its original bytes.
- `.concorde-write-` temporary files may remain beside them.

A writer's recovery may remove those temporary files.

**Concurrency.** The digest checks catch a change that happened before the transaction. They do not
catch a change made during it. When a writer changes a target file between a check and its rename,
or before a restoration, the transaction overwrites that change. A transaction therefore assumes
that its caller excludes every other writer of its target files for the whole transaction. The
caller does so by holding the lock its records require. One such lock is the
[merge lock](../glossary.json#concept.merge-lock) every [Issue](../glossary.json#concept.issue)
write holds. The Kernel takes no lock for the transaction.

The Spec tooling keeps its own copy of this mechanism, with its own error types
([Spec core](../spec-tooling/spec/contracts.md#file-transactions)).

## Library

The Kernel's library gives every part the same operations on these contracts. Each operation refuses
with a Kernel error carrying these fields:

- A stable `code`.
- The JSON pointer of the offending value or the path of the offending file.
- A message.

When the refusal concerns the whole input, the JSON pointer or path is empty. An operation never
writes an error link itself. The reason is that the level that called the operation has these responsibilities:

- It decides why it cannot handle the refusal.
- It builds its own link in the [error contract](tracing/contracts.md#contract.tracing.error).

The link keeps the code and message
as its detail. Unless the table gives the failure its own code, an operating-system refusal fails
with `system_error` for any of these operations:

- Reading a file.
- Writing a file.
- Taking a lock.

For such a `system_error`, the operation names the path. The error carries the operating system's
error as its cause. When a caller raises its own exception while it holds a lock, that exception
passes unchanged. Tracing's operations on trace nodes and locks belong to the Kernel's child
Tracing ([Tracing contracts](tracing/contracts.md)).

| Operation | Takes | Returns | Refuses with |
| --- | --- | --- | --- |
| Find the worktree | a directory | the real root of the Git worktree it lies in | `not_a_worktree` |
| Read a binding | a worktree | its workspace binding, or none when the worktree has no binding file | `binding_unreadable` (the file cannot be read or is no JSON), `binding_invalid` (it breaks the contract, names a `root` that is not an absolute real path, a relative folder or a workspace folder that does not exist), `binding_misplaced` (its `root` is another worktree) |
| Write a binding | a worktree and a binding | the file's path, having checked the binding as reading it does and replaced any binding there in one rename | `binding_invalid` (reading it would refuse it, its `root` naming another worktree included), `system_error` |
| Register a type | an identity, a version and a schema | nothing | `duplicate_type`, `invalid_input` |
| Make or check a typed value | a type identity and data, or a value and the type expected | a checked copy | `unknown_type`, `unsupported_version`, `incompatible_handoff`, `invalid_field` |
| Make an artifact | a root, an identity and a path below the root | `{id, path, digest}` of the file | `stale_reference` (the file does not exist), `invalid_field` (a path that is not canonical or passes through a symbolic link), `system_error` |
| Verify artifacts | a root and a value | nothing | `stale_reference` (an artifact's file is missing or its bytes changed), `invalid_field` (an artifact's fields break the artifact format or its path passes through a symbolic link) |
| Check a record | a value and its contract schema | nothing | `invalid_input` (the schema), `invalid_field` (the value), and the codes of an embedded typed value |
| Apply a file transaction | a root, the changes, the allowed paths and an optional final check | the written paths | the outcomes of [File transactions](#file-transactions) |
| Make a delivery message | a workspace's name and its goal | the message of a [delivery commit](#delivery-commit): the subject `concorde: deliver <workspace>`, a blank line and the goal without its surrounding whitespace, ending in one newline | nothing |
| List deliveries | a worktree, its branch, its base commit and the workspace's name | the delivery commits on the first-parent history since the base, oldest first, each with how it fails to verify, nothing when it verifies | `git_failed`, naming the Git command and its output |
| Take the [workspace lock](../glossary.json#concept.workspace-lock) | the `.concorde` a binding names, the workspace, the holder, how long to wait and whether to take a lock file its holder removed meanwhile | holds it until released | `workspace_busy` naming the holder, `workspace_retired` (its holder removed the file while the taker waited, as a close does), `system_error` |
| Take the merge lock | the primary worktree's `.concorde`, the holder, the task when there is one and how long to wait, 300 seconds by default | holds it until released | `merge_busy` naming the holder, `system_error` |
| Read a lock's holder | the workspace lock or the merge lock | its holder line, or none when nobody holds it | nothing |
| Read the [unfinished-merge marker](#unfinished-merge-marker) | the primary worktree's `.concorde` | the marker, or none when there is none | `marker_unreadable` (the file cannot be read or is no JSON), `marker_invalid` (it breaks its contract) |
| Write the unfinished-merge marker | the primary worktree's `.concorde` and a marker | the file's path, having checked the marker and replaced any marker there in one rename | `marker_invalid`, `system_error` |
| Remove the unfinished-merge marker | the primary worktree's `.concorde` | whether there was a marker | `system_error` |
| Describe an unfinished merge | the primary worktree's `.concorde` and its marker | the account a reader's refusal carries: the command, its process and start, the commit merged into which branch at which commit, where the primary worktree's head is now and the commands that finish the merge | nothing |

A run of Execution, for example, reads the binding of the worktree it starts in. When the binding
is copied from another workspace, the binding is refused with `binding_misplaced`. In that case,
the runner records the run as refused with its own link. The link has level `operation` or
`command`. The link's code and detail name that refusal and the file.
