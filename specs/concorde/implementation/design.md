# Implementation design notes

These notes extend the [Implementation entry](module.md) with an example of component work and the
reasons behind the design. They define nothing; every term is defined in the entry, and the exact
checks are in [programmer admission and completion](programmer.md).

## Component work, step by step

A billing Module raises the version of its payment contract, which a checkout Module requires. The
accepted task list has a local task for billing and one for checkout. Calling `concorde-implement`
for billing first returns:

```json
{"outcome": "unsupported",
 "components": [{"target_id": "module.checkout",
                 "task": "Accept payment contract version 3\nAcceptance: checkout requires version 3"}]}
```

The user session then calls `concorde-plan`, `concorde-tasks` and `concorde-implement` for
`module.checkout` with exactly that task and billing's constraints, in billing's candidate. When it
calls `concorde-implement` for billing again, the Host finds checkout's recorded work complete and
current for checkout's Spec and code, runs the programmer for billing's own task and records the
revisions of checkout it relied on. If checkout's Spec or code changes before billing's next run,
checkout is returned again. Validating billing afterwards covers every Module the candidate edited,
and delivering the candidate lands them together.

## Why one programmer per Module's tasks

A task list may reach into components, but a programmer that worked on them would silently take
over another Module's change and break promises it was never asked to keep. Returning component
work keeps each Module's tasks inside the change of the Module that owns them, even when one change
must edit several Modules to stay valid. The field is typed rather than a sentence in the answer, so
the user session acts on it without parsing prose.

## Why a shared file binds every binder

A file bound by several Modules carries the promises of all of them. A programmer bound to only one
could break a promise it cannot see, so its call is bound to every binder and reads their Spec
contexts. No extra read is granted for sharing beyond what binding to those Modules gives; the other
binders' own tasks remain component work.

## Why completion is narrow and edits are real

Marking tasks complete says only that the programmer's acceptance conditions are met in the
candidate. Independent review, validation and delivery each need their own current evidence, so a
quick completion is never mistaken for a ready change. The programmer edits the real candidate files
because copies would have to be merged back and could drift. The price is that a failed run can
leave partial edits, so the Host records nothing until an answer is accepted and a retry starts from
the candidate as it is. While the programmer works its own edits must not make its inputs look
stale, so the recheck allows the implementation files to change while the Spec, registry,
configuration, plan, tasks and review feedback must stay as prepared.
