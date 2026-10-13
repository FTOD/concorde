# How code_to_spec links tests

Part of the [Spec](../../glossary.json#concept.spec) of [Adoption](module.md). It gives the exact
edits the code_to_spec host makes to existing test files in step 10 of the [Code to spec
Operation](module.md#realization.adoption.code-to-spec). It also gives every case in which the host
makes none. [req.adoption.tests-linked-by-host](requirements.md#req.adoption.tests-linked-by-host),
[req.adoption.test-edits-limited](requirements.md#req.adoption.test-edits-limited) and
[req.adoption.unlinked-reported](requirements.md#req.adoption.unlinked-reported) state the
obligations.

## The edits

A scenario the worker took from existing tests names them in its promise's `tests`, as `path::name`
or `path::Class::name`. The host adds a `verifies` decorator above each named test that exists in a
[Module](../../glossary.json#concept.module)'s implementation file. Once per file, it adds a
two-line no-op definition of `verifies` after the file's docstring and imports. This keeps the
project's tests free of any import of Concorde. They run the same in the project's own environment.
The coverage check sees which test verifies which scenario.

The host finds a test where the coverage check finds it:

- In the module body.
- In a class body.
- Under a control-flow statement such as a top-level `if` or `try`.

It never finds a test inside a function. When a name is defined more than once in those places, the
host reports it, since it cannot tell which definition is the test. The host adds nothing else. It
adds nothing twice. A test that already declares the scenario is linked as it is, but only once its
name is found exactly once. It leaves every byte already in the file as it was, including its line
endings and blank lines. What it inserts takes the file's own line ending and indentation. The blank
lines it adds around the helper only make up the two that set it apart.

When the decorated file would not parse or cannot be written, the host leaves the file untouched. It
replaces a file only through a new file beside it, so that a failed write leaves the original whole.
It reports the links of such a file. It links the next file all the same.

When a file already binds `verifies` at module level, the host keeps that binding. This applies to
bindings by any of these forms:

- A statement.
- An `except` clause.
- An assignment expression.
- A match pattern.

When that existing binding stands at the file's top level before the test and is one of these, the
host adds only decorators:

- Its own no-op helper, however formatted.
- An import of Concorde's decorator from `concorde.spec.verification`.

[req.adoption.tests-linked-by-host](requirements.md#req.adoption.tests-linked-by-host) gives the
precise exceptions. When the existing binding is neither, or follows the test, or stands only in a
branch, the host leaves the file untouched. It reports each of the file's links in `unlinked_tests`.
A decorator would call the project's own `verifies`, whatever it does, or find no `verifies` at all
when the module is imported. A `del verifies` at module level counts as such a binding, since a
decorator after it would find no `verifies`. So does a `global verifies` anywhere in the file, since
the function declaring it may rebind the module's name.

A decorator of a method is evaluated in its class body, where a binding of `verifies` in that body
comes before the module's. So when the body of the class that defines a test binds `verifies`, the
host leaves that test without a decorator and reports its link with the class and the binding's
line. It links the file's other tests all the same. Only Python tests are linked.