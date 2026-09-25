# Spec tooling errors

Spec tooling reports every error with its own type, independent of the rest of Concorde: the
Framework's error chain is built on top of Spec tooling, never inside it. This document defines
that type exactly, as the [Spec core](module.md) implements it in `concorde.spec.errors` and as
every command of Spec tooling and the [Spec MCP server](../spec-mcp/module.md) return it.

## The error record

Every failure raises a `SpecError` or one of its subclasses (`TypedDataError`, `ContractError`,
`FrontMatterError`, `DeclarationError`, `DiagramError`, `DocsiteTemplateError` and the Spec MCP
server's `ToolError`). Besides a stable code and a concrete message, each carries where the error
is, why it is an error, how to fix it and what caused it, so that its caller can reason about it
without reading Spec tooling's code. Its `record()` is the data form below.

```concorde-contract
{
  "id": "contract.spec.error",
  "version": 1,
  "schema": {
    "$ref": "#/$defs/error",
    "$defs": {
      "error": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "code",
          "message",
          "reason",
          "location",
          "remediation",
          "causes"
        ],
        "properties": {
          "code": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$"
          },
          "message": {
            "type": "string",
            "minLength": 1
          },
          "reason": {
            "type": "string",
            "minLength": 1
          },
          "location": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "path",
              "line",
              "field",
              "subject"
            ],
            "properties": {
              "path": {
                "anyOf": [
                  {
                    "type": "null"
                  },
                  {
                    "type": "string"
                  }
                ]
              },
              "line": {
                "anyOf": [
                  {
                    "type": "null"
                  },
                  {
                    "type": "integer"
                  }
                ]
              },
              "field": {
                "anyOf": [
                  {
                    "type": "null"
                  },
                  {
                    "type": "string"
                  }
                ]
              },
              "subject": {
                "anyOf": [
                  {
                    "type": "null"
                  },
                  {
                    "type": "string"
                  }
                ]
              }
            }
          },
          "remediation": {
            "type": "string",
            "minLength": 1
          },
          "causes": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/error"
            }
          }
        }
      }
    }
  },
  "semantics": "One error of Spec tooling and, through causes, the errors behind it. code is a stable code from the table below or from the table of the subclass that raised it. message says concretely what failed, naming the values, paths and identities concerned. reason says why this is an error: the rule, requirement or Protocol check it breaks; for a failed Protocol check it quotes the check's statement. location names where: path is a project-relative path (or, for a defect, the source file of Spec tooling), line a 1-based line, field a JSON pointer, argument or configuration field, subject a node or Module identity; each is null when it does not apply. remediation says how to fix it. causes are the errors that caused this one, such as every fatal problem behind a refused load or the operating system's error behind an unreadable file; a cause is never dropped. A behaviour or field change increments the version.",
  "example": {
    "code": "missing_source",
    "message": "the metadata of module.payments's entry cannot be read: the required file specs/payments/module.md.json is missing in /home/dev/shop",
    "reason": "a file the Specs or the configuration require does not exist or cannot be read",
    "location": {
      "path": "specs/payments/module.md.json",
      "line": null,
      "field": null,
      "subject": "module.payments"
    },
    "remediation": "create the file, restore it, or remove the reference to it",
    "causes": [
      {
        "code": "missing_source",
        "message": "the required file specs/payments/module.md.json is missing in /home/dev/shop",
        "reason": "a file the Specs or the configuration require does not exist or cannot be read",
        "location": {
          "path": "specs/payments/module.md.json",
          "line": null,
          "field": null,
          "subject": null
        },
        "remediation": "create the file, restore it, or remove the reference to it",
        "causes": []
      }
    ]
  }
}
```

Where the record appears:

| Where | What it holds |
| --- | --- |
| `error` of a command's envelope (`validate`, `grant`, `registry`, `docsite`, `init`, `build`, `protocol-manifest`) | the command's own failure; `null` when the command did its work, whatever its findings |
| `{"error": …}` of a Spec MCP tool result with `isError` true | the tool's failure |
| `result.load_error` of `validate` | why the configuration, registry or Protocol binding could not be loaded; the `CONCORDE-SOURCE-008` finding repeats its message, reason and remediation |
| the exception a caller of the Python interface catches | the same fields as attributes, `record()` and `describe()`, a one-paragraph rendering |

A failure the Spec tooling does not anticipate still becomes a record, with the code
`unexpected_error`, the exception's type and message, and the source location where it was raised.
An operating-system error becomes a `system_error` cause with the path concerned.

Findings are not errors. A finding is a diagnostic of the Specs that `validate` reports while it
succeeds in diagnosing; an error is a call or command that could not do its work. A refused load
turns the fatal findings into causes, each with its check's statement as its reason.

## Codes

A subclass that belongs to another Module registers its own codes the same way; for example Check
execution's `CheckError` and the Issue store's `IssueError`. The reason and remediation below are
the defaults; a call site gives more specific ones when it knows more.

| Code | Reason | Remediation |
| --- | --- | --- |
| `invalid_spec` | the Spec sources break a rule of the Spec Protocol or of the project configuration | correct the named file or field so that it follows the Protocol, then validate again |
| `invalid_owner` | every Spec document is owned by exactly one Module (CHK.owns.unique) | list the document in the owns of one Module only |
| `unsafe_path` | Spec tooling reads only canonical project-relative paths of regular files, never through a symbolic link or outside the project | use a canonical project-relative path to a regular file and remove the symbolic link |
| `missing_source` | a file the Specs or the configuration require does not exist or cannot be read | create the file, restore it, or remove the reference to it |
| `unsupported_profile` | this Spec tooling reads only the project profile and registry schema of Protocol 13 (schema_version 3) | migrate the configuration and registry to the current profile explicitly |
| `protocol_mismatch` | the project's Protocol binding must name exactly the Protocol copy installed under .concorde/protocol/, and that copy must be unchanged | reinstall Concorde, or accept the installed Protocol by updating the binding |
| `not_installed` | initialization needs the Protocol copy that only the installer places | run the Concorde installer in this project first |
| `already_initialized` | initialization creates the first Spec only; it never overwrites a configured project | change an initialized project's Specs through ordinary work instead |
| `invalid_input` | the arguments of the call do not have the required form | correct the named argument and call again |
| `invalid_task_type` | a grant exists only for the seven task types the Protocol defines | use understand, specify, implement, test, review-spec, review-code or code-to-spec |
| `unknown_module` | a grant, boundary or query names only Modules the registry registers | name registered Modules, or register the Module first |
| `unknown_target` | the named Module or node is not declared in the loaded Specs | name a declared Module or node; `concorde validate` lists what exists |
| `invalid_target` | the identity does not name a document, scenario or context of the requested kind | name an identity of the requested kind |
| `invalid_focus` | a scenario focus must belong to the Module it narrows | focus on a scenario of the selected Module |
| `shared_file` | a task may write a file only when every Module that binds it is bound by the task, so no other Module's promise changes behind its back | bind every Module that binds the shared file, or leave the file unchanged |
| `invalid_context` | a context holds each registered document member once, with its owner's role and provenance | recompute the context from the current Specs instead of editing it |
| `stale_context` | a context is valid only for the exact Spec sources it was computed from | compute the context again from the current Specs |
| `invalid_proposal` | a proposal is applied only in exactly the shape and content it was proposed with | propose again and apply the new proposal unchanged |
| `stale_proposal` | a proposal is applied only to the bytes it was computed from | propose again from the current files |
| `permission_denied` | the change or read lies outside the paths its caller authorized | restrict the change to the authorized paths, or ask for the wider boundary |
| `contract_violation` | the value does not satisfy the published schema it is checked against | correct the value at the named field so that it satisfies the schema |
| `duplicate_type` | a typed value's identity is registered once, with one version and one schema | register the type once, or choose a new type identity |
| `unknown_type` | a typed value names only a registered type | register the type, or use a registered type identity |
| `invalid_json` | Spec tooling accepts strict JSON: no duplicate fields and no NaN or Infinity | write strict JSON |
| `invalid_field` | the typed value does not satisfy its registered schema | correct the value at the named field |
| `incompatible_handoff` | a typed value is accepted only as the type its receiver expects | pass a value of the expected type |
| `unsupported_version` | a typed value must have its type's registered schema version | convert the value to the registered version |
| `stale_reference` | an artifact reference is valid only while the referenced bytes are unchanged | recompute the reference from the current file |
| `invalid_front_matter` | front matter is the restricted YAML subset the Protocol defines | rewrite the front matter in the supported subset |
| `invalid_declaration` | a verification declaration names scenario identities as string literals in a parseable test | fix the declaration or the test source |
| `invalid_diagram` | a checked D2 diagram uses only the semantic subset the Views chapter defines: shapes, nesting and '->' edges, with no styling or layout | remove the styling or layout statement, or mark the block `d2 illustrative` |
| `invalid_docsite_template` | the docsite scaffold is copied only from the package's complete, safe template | reinstall or rebuild the Concorde package |
| `no_root` | the Spec MCP server answers only for one project root | set CLAUDE_PROJECT_DIR or offer exactly one file:// root |
| `outside_root` | the Spec MCP server answers only about paths inside its root | pass a path inside the server's root |
| `system_error` | the operating system or the Python runtime refused an operation Spec tooling needed | fix the file, permission or environment named in the message |
| `unexpected_error` | an exception Spec tooling does not anticipate ended the command; it is a defect | report the error with its location and message |

## Requirements

### req.spec.error-detail — Every error explains itself

Every error Spec tooling raises SHALL carry a registered code, a concrete message naming the values concerned, its location when one applies, the reason it is an error and a remediation.

### req.spec.error-causes — No cause is dropped

An error that results from other errors, such as a refused load with several fatal problems or an unreadable file, SHALL carry each of them as a cause.

### req.spec.error-independent — Spec tooling has its own error type

Spec tooling SHALL NOT depend on any other Module of Concorde to report its errors.

Other Modules translate Spec tooling's record into their own error types; the Operations turn it into a link of the Framework's error chain.

## Scenarios

### scenario.spec.error-registered — Every code has a reason and a remedy

- GIVEN the sources of Spec core, the Spec MCP server and Views
- WHEN every literal error code they raise is collected
- THEN each code is registered with a nonblank reason and remediation

### scenario.spec.error-independent — Spec tooling imports no Framework error type

- GIVEN the sources of Spec core, the Spec MCP server and Views
- WHEN their imports are read
- THEN none imports the Framework's error chain, the Harness, the Operations or Tasks

### scenario.spec.error-contract — The record is the contract

- GIVEN the error record schema and the code table of `concorde.spec.errors`
- WHEN they are compared with this document
- THEN the schema equals the contract's schema and the code table equals the table above

### scenario.spec.error-every-cause — A refused load names every fatal problem

- GIVEN a registry whose two Modules name entries that do not exist
- WHEN a repository is opened
- THEN the error says how many fatal problems there are and carries each as a cause
- AND each cause names its path and quotes the statement of the Protocol check it fails
