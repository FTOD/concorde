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

A binding that breaks this contract is refused by every part that reads it, never read in part, and
by the library before it writes one. A binding whose `root` is not the real path of the worktree it
lies in is refused too, since a copied binding would bind the wrong workspace: a `root` that is not
an absolute real path, such as a symbolic link to the worktree or a path ending in `/.`, breaks the
contract, and the real path of another worktree is a misplaced binding. Git ignores the file. The [Modules](../glossary.json#concept.module) it names are Module
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

A delivery commit **verifies** when it has exactly one parent. A delivery commit with another number
of parents, such as a merge commit given the subject, does not verify: every part that reads
delivery commits refuses to take the workspace as delivered by it and names the mismatch. A delivery
commit is made with the repository's configured author identity and its commit hooks, and is never
amended: a workspace delivered again gets a new delivery commit on top, so the first-parent history
keeps every delivery.

This convention says what a delivery commit is, not who makes one. Which command may make it, what
it checks before, and which of the workspace's changes it holds, such as every change Git does not
ignore less the untracked paths its own validation leaves out, are the delivering command's own
rules, stated in its [Spec](../glossary.json#concept.spec): in Concorde, Method's
[`delivery`](../method/delivery/contracts.md#delivery-commit) and, where the method part is not
installed, Coordination's [`task deliver`](../coordination/tasks/module.md). Nothing here relies on
either.

## Typed values

A **typed value** is a closed JSON object `{"type_id": ..., "schema_version": ..., "data": ...}`.
`type_id` is a nonblank name such as `concorde-run-trace`, `schema_version` a positive integer, and
`data` the value's content, checked against the schema the type's owner registered for that version.
Only a value its owner's contract designates as typed carries the envelope, such as a trace node's
`content`; a record whose contract defines its own representation, such as the
workspace binding above, a [run result](../glossary.json#concept.run-result) or a grant, is checked against that contract's schema as it
is.

- **Registration.** The part that owns a type registers one schema for it when its code is loaded,
  under the type's identity and one version. Registering an identity already registered with the
  same version and an equal schema changes nothing; another version or schema for the same identity
  is refused as `duplicate_type`, and the existing registration stays in force. The Kernel registers
  no type of any part and imports no part, so whoever checks a value must have loaded the code of the
  value's owner.
- **Embedding.** A registered schema embeds a whole typed value of another owner's type with the
  reference `{"$ref": "<type_id>"}`, a bare type identity rather than a JSON pointer, which stands
  alone: a schema holding such a `$ref` has no other keyword. The reference
  is resolved when a value is checked, against the registration in force then, and matches the whole
  envelope: `type_id` equal to that identity, `schema_version` equal to its registered version, and
  `data` against its registered schema. So one part's record holds another part's value without
  importing it, and a reference to a type still unregistered at check time fails with
  `unknown_type`. For example, a type `example-batch` whose schema is
  `{"type": "object", "additionalProperties": false, "required": ["runs"], "properties": {"runs":
  {"type": "array", "items": {"$ref": "concorde-run-trace"}}}}` checks each element of `runs` as a
  whole `concorde-run-trace` value, and fails with `unknown_type` at `/data/runs/0` while that type
  is not registered.
- **Checking.** A value of another version fails with `unsupported_version`, an unregistered type
  with `unknown_type`, a value of the wrong type where one is expected with `incompatible_handoff`,
  and any other mismatch with `invalid_field`, naming the JSON pointer of the offending field. A
  checked value is returned as a copy, never shared with its caller.
- **Paths and artifacts.** A field whose registered schema gives it `"format": "project-path"` is a
  canonical project-relative POSIX path: nonempty, no leading `/`, no backslash, colon or control
  character, no empty, `.` or `..` component. An **artifact** is an object with exactly the keys
  `id`, `path` and `digest`: its `path` a project path relative to a root, its digest `sha256:` and
  64 lowercase hexadecimal digits of the file's bytes. Checking a typed value never reads a file:
  artifacts are made and verified by operations of their own over a root the caller chooses, since
  only the caller knows in which worktree its record lives. Making one digests a file that must
  exist below the root, and verifying a value walks it whole, treats every object with exactly
  those three keys as an artifact and refuses as `stale_reference` one whose file is missing or
  whose bytes changed ([Library](#library)). An array whose `items` schema is the library's
  artifact schema, which requires those three keys and admits no other, lists each artifact once:
  two of its artifacts with the same `id` or the same `path` are refused with `invalid_field`.
  The file an artifact or a [file transaction](#file-transactions) names is reached below its root
  only through real directories: a path any of whose components is a symbolic link is refused,
  naming the path and the link, with `invalid_field` for an artifact and as a malformed list
  (`invalid_proposal`) of a file transaction.
  Every other path is what its owner's schema says, an absolute location included: a task trace's
  worktree or the evidence a run result keeps are never rewritten.

### Registered schemas

A registered schema is written in the following dialect of JSON Schema, which needs no network and
loads no document. A schema is an object or a boolean. Its keywords are `title`, `description`,
`examples`, `default`, `type` with one type name, `properties`, `required`, `additionalProperties`
(a boolean or a schema), `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`,
`maxLength`, `pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`, `format` with the one
format `project-path`, and `$ref` with a bare type identity as above. Any other keyword, a list of
types, a `$ref` of another form, an invalid bound or nesting deeper than 100 levels is refused when
the schema is registered (`invalid_input`), so that no registered type promises more than its values
are checked for. Two schemas are equal, for a repeated registration, when they are equal as JSON
values, as below.

A value is checked as JSON Schema checks it, for these keywords: an object admits keys its
`properties` do not name unless its `additionalProperties` is `false`, and checks them against
`additionalProperties` when that is a schema, so a closed object spells
`additionalProperties: false`; `number` admits integers and finite non-integral numbers and
`integer` only integers, neither a boolean, and `minimum` and `maximum` bound both; `pattern`
matches anywhere in the string unless it is anchored; `const`, `enum` and `uniqueItems` compare
values as JSON values: numbers by value, so `1` equals `1.0`, a boolean only with a boolean, so
`true` is not `1`, and arrays and objects item by item and field by field under the same rule; each
keyword applies to the kind of value it constrains, whether the schema names a `type` or not; and a
string whose schema sets `minLength` must not consist of whitespace only, though `minLength` `0`
still admits the empty string. A number is finite: a JSON text holding a number too large for a
finite floating-point value is no JSON value (`invalid_json`), while an integer of any size is
checked by its value. Checking a value descends at most 100 levels: each field of an object, item of an
array, `anyOf` alternative tried, `$ref` followed and `data` of an embedded typed value counts one
level, and a value whose checking would go deeper is refused with `invalid_field` at the field
reached.

### Contract schemas

A record whose own contract defines its representation, such as a workspace binding, a
[run result](../glossary.json#concept.run-result) or an error link, carries no envelope: the part
that owns it checks it against a **contract schema**, the schema its contract gives, as code. A
contract schema is written in the registered dialect with one addition: an object `$defs` of named
schemas at its top, referred to anywhere in it as `{"$ref": "#/$defs/<name>"}`, so that a recursive
record such as an error link with its causes can be described; a `$defs` anywhere else is refused,
naming its JSON pointer. A local reference must name an entry of `$defs`; a bare type identity
embeds a typed value as above. A contract schema is checked against
the dialect when it is first used (`invalid_input`) and a record that breaks it is refused with
`invalid_field`, naming the JSON pointer of the offending field. It is never registered.

The `concorde-contract` fences of the Specs use a wider dialect of their own, with `oneOf` and
`allOf` besides, which belongs to the Spec tooling that checks the fences; neither a registered nor
a contract schema of the Kernel uses those. The Spec tooling keeps its own copy of this registered
dialect and of the typed value format in its own code, so that the spec part installs alone
([Spec core](../spec-tooling/spec/contracts.md#typed-values)); the two agree on this text, not on
code.

## File transactions

A **file transaction** writes a set of whole files below a root its caller names, each bound to the
bytes it replaces. It takes a nonempty list of changes, each

```json
{"path": "<project-relative path below the root>", "before_digest": "sha256:<64 hex digits> or null", "content": "<the file's new text>"}
```

where `path` follows the `project-path` rule above and names a file once in the list, `content` is
the whole new file as text written in UTF-8, and `before_digest` is the digest of the file's current
bytes, `sha256:` and 64 lowercase hexadecimal digits, or `null` when the file must not exist; a
`before_digest` of any other form makes the list malformed. The caller also names the paths it
allows and, optionally, a final check to run after the writes.

1. A malformed list (`invalid_proposal`), a path outside the allowed ones (`permission_denied`) or a
   file whose current bytes, or existence, do not match its `before_digest` (`stale_proposal`)
   refuses the transaction before any write; the match is checked again just before each write.
2. Each file is written to a temporary file named `.concorde-write-` and a random suffix in its own
   directory, flushed and renamed into place.
3. After the last write the final check runs. On success the transaction returns the written paths
   in order.
4. When a write or the final check fails, every file written so far is restored to its original
   bytes, or removed when it did not exist, through the same temporary file and rename.

What the caller then receives:

- when every restoration succeeded, the failure of the final check exactly as the check raised it;
  a refusal of step 1 or a `stale_proposal` of a later write as such; and an operating-system error
  of a write as `system_error`, naming the file and saying that every file written so far was
  restored, with the operating system's error as its cause;
- when the operating system refuses a restoration, the other restorations are still attempted and
  the transaction fails with `system_error`, naming every file not restored and saying each still
  holds its new content, with the first failure as its first cause and one cause per refused
  restoration. The caller must not treat that outcome as restored: it recovers the named files by
  its own records' rule, as it does after a killed process.

These guarantees hold for failures the process observes, an interruption it receives, such as
`KeyboardInterrupt` or `SystemExit`, included: the interruption is raised again unchanged once every
file is restored. A killed process restores nothing: each
file already renamed into place keeps its new content, every other file its original bytes, and
`.concorde-write-` temporary files may remain beside them, which a writer's recovery may remove.

**Concurrency.** The digest checks catch a change that happened before the transaction, not one made
during it: a writer that changes a target file between a check and its rename, or before a
restoration, is overwritten. A transaction therefore assumes that its caller excludes every other
writer of its target files for the whole transaction, by holding the lock its records require, such
as the [merge lock](../glossary.json#concept.merge-lock) every [Issue](../glossary.json#concept.issue) write holds; the Kernel takes no
lock for it.

The Spec tooling keeps its own copy of this mechanism, with its own error types
([Spec core](../spec-tooling/spec/contracts.md#file-transactions)).

## Library

The Kernel's library gives every part the same operations on these contracts. Each refuses with a
Kernel error carrying a stable `code`, the JSON pointer of the offending value or the path of the
offending file, empty when the refusal concerns the whole input, and a message; it never
writes an error link itself, since the level that called it decides why it cannot handle the
refusal and builds its own link in the
[error contract](tracing/contracts.md#contract.tracing.error), keeping the code and message as its
detail. An operation that reads or writes a file, or takes a lock, and that the operating system
refuses fails with `system_error`, naming the path and with the operating system's error as its
cause, unless the table gives that failure a code of its own; a caller's own exception raised while
it holds a lock passes unchanged. Tracing's operations on trace nodes and locks are its child's
([Tracing contracts](tracing/contracts.md)).

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

A run of Execution, for example, reads the binding of the worktree it starts in: a binding copied
from another workspace is refused with `binding_misplaced`, and the runner records the run as
refused with its own link, of level `operation` or `command`, whose code and detail name that
refusal and the file.
