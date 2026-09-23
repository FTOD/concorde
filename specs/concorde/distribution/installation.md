# Installing and updating Concorde

This topic explains how the installer puts Concorde into a consumer project, how updates avoid
overwriting the developer's work, how the Host makes each worktree runnable, and how the managed
runtime is created and checked. The installer supplies tools; it creates no Spec, registry or
configuration of the project. `concorde-init` of Spec tooling does that afterwards. Exact file
names, record fields and exit codes are in [Distribution interfaces](interfaces.md#installer).

## Terminology

| Term | Definition |
| --- | --- |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Host](../vocabulary.md#concept.concorde.host) | |
| [Candidate](../harness/worktrees/module.md#concept.worktrees.candidate) | |

The installation terms themselves, such as installation receipt, Protocol copy, managed runtime and
local installation, are defined in the [Distribution entry](module.md#terminology).

## What an installation contains

| Location in the consumer project | Content | Owned by the receipt |
| --- | --- | --- |
| `.concorde/framework/` | The package roots, the docsite template, the command-line and launcher scripts, `concorde.json`, `LICENSE`, `README.md`, and the installed-layout build outputs with their build manifest | yes, file by file |
| `.pi/extensions/concorde-session.ts` | The session entry with the installed capability catalog | yes |
| `.pi/extensions/concorde-observe.ts`, `.pi/agents/tester.md` | The passive observer entry and the tester definition | yes |
| `.concorde/protocol/` | The Protocol copy: the Protocol manifest and the rendered Protocol assets it lists | yes |
| `AGENTS.md` | One marked block telling readers to follow `.concorde/protocol/principles.md` | the block only |
| `.concorde/issues/.gitignore` | A default the project starts from | no; written only when absent |
| `.concorde/.venv` | The managed runtime | yes, as one runtime record |
| `.concorde/install.json` | The installation receipt | it is the receipt |

Files that Pi session classifies as source-only never ship, nor do `node_modules` below `pi/` and
Python caches. A package containing a symbolic link is refused.

## Previewing and applying

The installer first loads the package: it checks `concorde.json`, renders the installed layout,
checks the runtime lock and, for a source checkout, runs the package check. It then plans one action
per path:

| Action | Meaning |
| --- | --- |
| `create` | The path is absent and will be written |
| `unchanged` | The path already holds the wanted bytes and the receipt owns them |
| `adopt` | The path already holds the wanted bytes but was not recorded; applying records it |
| `update` | The path holds exactly the bytes the receipt recorded and will be replaced |
| `remove` | An owned file the new package no longer ships, unchanged since it was written |
| `drop-missing` | An owned file that is already gone; its record is dropped |
| `preserve` | A project default or preserved project file that stays as it is |
| `conflict` | Anything else: a changed owned file, an unowned file in the way, a symbolic link, or an unsafe path |

The managed runtime appears as one more action: `create`, `unchanged`, `rebuild` or `conflict`.
Without `--apply` the installer prints the plan and exits; a preview writes nothing and gives the
same plan when repeated.

With `--apply` and no conflict, the installer takes the target's installation lock and applies the
plan in this order:

1. It rechecks that every root file is byte for byte what the preview saw, then recomputes the whole
   plan and refuses if anything differs. A plan is only ever applied to the state it was made from.
2. It writes each file through a temporary file and a rename, marking installed scripts executable
   and keeping the mode of files it updates.
3. It provisions the managed runtime.
4. It recomputes the package identity and refuses if the package changed meanwhile.
5. It writes the new receipt the same way as the files.

If any step fails, it removes the files it created, restores the bytes and modes of the files it
replaced or removed, restores or deletes the receipt, removes a runtime it created in this apply and
removes the directories it created. The one exception is a runtime rebuild; see
[the managed runtime](#the-managed-runtime).

## The root guidance block

`AGENTS.md` is the developer's file, so the installer owns only one marked block inside it, which
tells readers to follow the Protocol principles in the Protocol copy. A new block goes before the
existing text so that it is not hidden inside the developer's Markdown; an existing owned block keeps
its position. The receipt records only the digest of the block. Duplicated, misordered or unrecorded
markers, an edited block, a symbolic link or a directory in place of the file are conflicts. If the
installer created `AGENTS.md` only to hold its block, the receipt says so, and removing the block
later also removes the then empty file; a file the developer created stays even when it becomes
empty.

## Updating

Running the installer from a newer package produces a plan against the current receipt. Owned files
that changed in the package are updated, files the package no longer ships are removed, and every
file the developer modified is a conflict that blocks the apply. Nothing is merged. A receipt of any
schema other than the current one is refused.

`--remove-protocol-guidance` removes only the owned root blocks and records the removal in the
receipt; the Framework and the runtime stay. Running it again changes nothing.

## Preserving an inherited project

A worktree created from a branch that already contains Concorde files, for example a committed
`AGENTS.md` block and a committed Protocol copy, has no receipt of its own: receipts and the runtime
are usually not committed. `--preserve-project` installs the Framework and runtime there without
taking ownership of those inherited files:

- An existing `AGENTS.md` stays byte for byte, and an absent `AGENTS.md` receives a new owned block.
- An existing Protocol copy must be complete, with every asset matching its manifest, and is kept as
  it is, even if it belongs to another version; it is never completed with files of the new package.
- An absent Protocol copy is seeded only when the project is uninitialized or its configuration
  already binds exactly the package's Protocol manifest.
- Files a local receipt already owns keep their ownership and must still match it.

Preservation and `--remove-protocol-guidance` cannot be combined. Keeping a different Protocol copy
does not make the project runnable: capabilities stay refused until the binding and the copy agree.

## The Protocol copy and its acceptance

The installer always writes the package's Protocol copy (outside preservation) but never touches the
project's Protocol binding. Admission refuses to run capabilities while the binding does not match
the copy. The developer reviews the Protocol change, migrates the project's Specs if needed, and
then accepts it through `concorde-configure`, which Request admission provides. This separates
receiving new software from agreeing to a new specification language.

## Local installations in worktrees

Each worktree that runs Concorde needs its own complete installation, because its Framework, runtime
and receipt are ignored by Git and never shared. The local installation service gives the Host three
operations:

- **Admit a package.** The Host names the exact package that admitted the request. Its identity is
  the version plus a digest over every file the installer would write and a digest of the installed
  build manifest, so a source checkout and an installed copy with the same bytes have the same
  identity.
- **Verify.** Read every owned file and compare it with the receipt and a fresh render, check that
  the receipt names the admitted package, and check the runtime: its owner marker, the installed Pi
  dependencies, that LangGraph is imported from inside the runtime and not through a global site
  directory, and every capability's runtime check. Verification writes nothing.
- **Ensure.** Verify, and only when the caller passes an explicit bootstrap grant, install a current
  plan with preservation and verify again. The package is re-admitted after the lock is taken, so a
  package that changed while waiting is refused.

Every applying installer, whether started from the command line or by the service, holds an
exclusive lock on the target; a second one fails at once instead of waiting, and a system without
file locking cannot apply at all. The lock excludes other installers, not editors or running
capabilities, so the caller keeps the worktree quiet while installing and verifying.

A failed verification returns no installation, and no path falls back to the provider's files, the
primary worktree's runtime or a global package. The service creates no worktree, starts no
capability, grants nothing and records no candidate status. It refuses to install into a Concorde
source checkout.

Installed Concorde can also bootstrap another ordinary Git worktree with its own deployed installer:

```sh
python3 /path/to/project/.concorde/framework/scripts/install-concorde.py \
  --target /path/to/new-worktree --preserve-project --preview
```

## The managed runtime

**Plan.** Planning compares the runtime directory with the package without changing anything. The
action is `create` when the directory does not exist; `unchanged` when Concorde owns it and its
owner marker, lock digests, Pi dependencies and capability list match the package and the
interpreter reports the pinned LangGraph version from inside the runtime; `rebuild` when Concorde
owns it but anything differs; and `conflict` when the path is a symbolic link, not a directory, or
not owned by Concorde. Planning may run local, offline health probes.

**Provision.** For `create` and `rebuild`, the provisioner creates a virtual environment with the
installer's interpreter, installs the locked Python dependencies and installs the locked Pi
dependencies into the runtime. For every action it then runs each public capability's runtime check
with the runtime's own interpreter, requires each check to report the runtime as its environment and
the pinned LangGraph version, verifies the installed Pi dependencies, and only then writes the owner
marker. A `create` whose directory appeared after planning is refused rather than adopted. `npm` must
be available on the host.

**Failure.** On any failure during `create`, the provisioner deletes the directory it was building,
and no marker claims a verified runtime. A `rebuild` deletes the previous environment before
creating the new one, so on failure the project has **no** managed runtime: the provisioner removes
what it was building, the installation's rollback of files and receipt does not restore the old
environment, and later verification fails until an installation succeeds. This is the one part of an
installation that a failure does not return to its previous state.

**Verify.** Local verification repeats the plan, which must be `unchanged`, compares the marker and
the receipt's runtime record with what it observes, runs the isolation and capability checks, and
writes nothing.
