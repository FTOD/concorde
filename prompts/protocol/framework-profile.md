---
audience: shared
---

## Concorde Framework execution profile

This profile applies the independent Spec Protocol to Concorde's runtime. Framework configuration
uses `profile_version: 10` for the four-part Module model and registry schema 3 for its JSON
storage. `.concorde/config.json` declares `profile_version`, `registry`, `protocol` and
`capability_configuration`. Its `protocol` binding identifies the accepted version and exact
manifest digest. These configuration and storage versions are Framework compatibility identifiers,
not additional versions of the specification language. Older configurations require explicit
migration; the runtime must not infer their meaning from paths or names.

### P5. One complete Module context per bounded task

A bounded invocation selects one Module and freezes four kinds of context. Its **Spec context**
is that Module's complete registered document collection; scenario focus does not trim it. Its
**implementation context** is the Protocol-defined set of files bound by the Module's entities.
Every phase may see those file names, because the entity declarations are part of the Spec
context; only code-writing and code-review phases receive file contents, in their declared
subsets. Its **capability context** is the set of admitted Capability and Tool contracts the
invocation may use. Its **task context** is the task, constraints, admitted stage artifacts and
lifecycle metadata. A kind may be empty for a phase, but the frozen closure is never empty.
Planner and task-author inputs contain no file contents. A global coordinator may reason across
explicitly selected complete Module Spec contexts for questions, routing and topology design. The
host deterministically resolves their registered documents, injects each source body once, and
preserves per-Module membership and source digests. Questions are answered directly from these
original sources; additional Module contexts require explicit selection. For mutations, each
selected worker is a fresh invocation with only its own complete Module context. Routing metadata
is an explicit input, not permission to inspect implementation. Coordinator discovery never loads
implementation files.

Spec authors, assessors, planners and task authors use only the selected Module's complete
project-Spec collection. They MUST NOT read source code to supply missing Module meaning. Only
the code-writing phase receives the complete implementation context; code review receives its
separately declared read-only subset. Agent instructions, the Protocol rule bundle and Skills are
not context: instructions belong to the Agent definition, and a Skill is the installed projection
of a global or lifecycle capability for the developer's own agent runtime.

Context identities cover document membership and bytes, Protocol and instructions, declared stage
artifacts and lifecycle identity. Code-phase context identities additionally cover the listed
files and their current digests. A changed input requires a new snapshot. Implementation-only
changes do not add implementation knowledge to a planner.

### P6. Gaps and review are tied to the affected contract

Missing required behavior is a Module Spec gap. Name the missing promise, blocked step, Module and
snapshot; continue only independent work. Implementation source cannot resolve that gap implicitly.
A failed execution, an explicit prohibition and a missing runtime value with defined failure
behavior are distinct from an unspecified contract.

Spec review uses Module Specs. Code review uses the same Module contracts and authorized code in a
fresh read-only invocation. A review records its exact inputs, coverage, findings and completion.
Changed relevant inputs invalidate it. Skipped, failed, incomplete and successful reviews remain
distinct. A change to a file listed by several Modules requires checks for all listing Modules,
with separate Module contexts and explicit per-consumer evidence. No passing structural check
proves semantic completeness.

### P7. Execution authority is explicit

The host binds each normal Framework invocation to declared context and file permissions. Only
code-writing invocations receive file contents with write authority, and only for the files the
selected Module lists; they never change Spec documents, entity declarations or the registry.
Code review and deterministic checks have separately declared read authority. The registry's
reverse index never grants a writer another Module's Spec or unrelated code. Unsupported
enforcement fails closed. An outer developer-authorized maintenance session may read and modify
the project directly; its explicit authorization does not silently widen normal worker
permissions or become a project business contract.

Every Framework capability's control flow is a LangGraph graph. Its nodes are deterministic
capabilities, which make no model call, or Agents, which do; a leaf node may be either. The same
graphs are the inspectable Studio surface, and no capability runs control flow outside them.

Agent instructions, Skills, schemas and rule assets are deterministic projections of authored
sources. Generated output is not edited as source. Builds distribute the Module kind definition
and the accepted Protocol binding. Configuration, installation and publication must agree on that
binding. Runtime Agent responsibility files are authored implementation assets, not another
category of project Spec.

### P8. Structure and file listings change together

Topology changes reconcile Module parentage, uses, document memberships and file listings as one
consistent proposal. A candidate registry states each Module's `files`; the private author of
that Module writes entity declarations whose file union equals it, marking files that do not yet
exist as pending. The reverse index identifies every listing Module before a shared file changes.
A new or changed Module's author sees only that Module's contract collection; code-writing work
receives the listed files. Other Module contracts are reviewed separately. An atomic application
checks source versions and preserves prior bytes if applying the proposed structure fails. Human
acceptance is explicit where the selected workflow requires it; direct maintenance follows the
developer's explicit task authorization.

### P9. Candidate and delivery evidence belong to a worktree

One candidate worktree holds one change, including its component progress, gaps and implementation
impact evidence. Partial work is inspectable and resumable, not represented as completed delivery.
Validation and review evidence bind to actual candidate inputs. Changes to a file listed by
several Modules invalidate evidence for every listing Module even if only one Module initiated the
change. Delivery preserves unrelated local changes, checks the actual integration and records
incomplete cleanup separately from a completed merge. After the candidate is verified, delivery
confirms pending files: every declared pending file that now exists has its marker removed by a
deterministic host edit included in the delivered commit, and the receipt names the confirmed
files; a pending file that still does not exist stays pending and is reported. No component
independently delivers its enclosing change.

### P10. Explicit session handoffs

When the selected workflow requires a new outer session, start it in the intended worktree with
fresh context and that worktree's instructions. Changing cwd does not erase prior cognitive inputs.
Supply a self-contained prompt in the developer's language with the absolute directory, branch,
task, authorizations, completed and remaining work, artifacts, checks and next steps. Start the
session automatically when isolation can be established; otherwise provide a complete copyable
prompt. A direct maintenance task explicitly authorized by the developer does not require a
workflow handoff solely because it updates the Framework's own instructions.

### Framework authoring and publication conventions

Every Concorde Module's `module.md` carries the four mandatory parts in order: Purpose, Scenarios,
Entities and Architecture. Its Architecture section holds an inline Mermaid flowchart with English
`accTitle` and `accDescr` lines whose nodes are exactly the declared entity titles and whose edge
labels are the relationship verbs. Show real responsibilities and connections; do not invent
nodes to satisfy a diagram shape. Files that realize an entity are listed on that entity; a
program shared by several Modules is listed by each of them under its own entity. Publication
renders each fence inside its own Markdown page; rendered views and navigation are derived and
create no additional membership. These conventions implement the Protocol's architecture
requirements for this project; they are not requirements on every Protocol implementation.
