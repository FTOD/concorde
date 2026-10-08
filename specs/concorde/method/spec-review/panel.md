# Spec panel Operation

The `spec_panel` [Operation](../../glossary.json#concept.operation) of [Spec review](module.md) has
these details:

- The arguments.
- The exact step sequence.
- The earlier Issues and the Issue reports.
- The panel graph and its accounting rule.
- The workers' results.
- The run's result and payload.

## Invocation

```text
concorde run spec_panel [--modules <id>[,<id>...]] [--reviewers <2-5>] [--architects <0-2>]
```

The panel works on the worktree it starts in. With a
[workspace binding](../../glossary.json#concept.workspace-binding) there, it works on the bound
[workspace](../../glossary.json#concept.workspace). `--modules` defaults to that workspace's
Modules. Without a binding, it runs as an [unbound run](../../glossary.json#concept.unbound-run),
for instance on the primary worktree. Such a run judges the [Specs](../../glossary.json#concept.spec)
as merged there. `--modules` names one or more registered Modules of that worktree. `--reviewers`
is the number of reviewers on each [Module](../../glossary.json#concept.module)'s panel. Its
default is 3. `--architects` is the number of architects. Its default is 2. The workers have these
names:

- Each reviewer is the worker `reviewer<seat>`, `reviewer1` to `reviewer5`.
- Each architect is the worker `architect<seat>`, `architect1` or `architect2`.
- The chair is the worker `chair`.

By these [worker ids](../../glossary.json#concept.worker-id), the
[worker configuration](../../glossary.json#concept.worker-configuration) gives each worker its own
backend, model and thinking level. Workers on different models make their reviews more independent
still. The Operation takes no other argument. It needs no user consent.

The panel runs as a LangGraph graph, one of Concorde's Python dependencies. When an Execution
runner's interpreter cannot import LangGraph, such as an install made with
`--without-dependencies`, the runner fails the run with `langgraph_unavailable`. It fails before
the Operation launches any worker.

## Host sequence

| # | Step | Actor | On failure |
| --- | --- | --- | --- |
| 1 | Load the workspace's Specs and validate every named Module | Operation (Spec core) | a loading error fails the run; a structural error in the Module's own documents or about the Module or a node it defines makes the Module `incomplete`, with the findings as host evidence; an unknown Module is `incomplete` |
| 2 | For each Module that passed, read its [earlier Issues](#earlier-issues) from the project's Issues | Operation (Issues) | Issues that cannot be read: the Module is `incomplete` (`issues_unreadable`) |
| 3 | For each Module whose earlier Issues were read, run the [panel graph](#the-panel-graph). Every reviewer runs under the Module's `review-spec` grant, every architect under its `review-architecture` grant, and the chair under the `review-architecture` grant when the panel has an architect and the `review-spec` grant otherwise. Each grant is frozen with its [context identity](../../glossary.json#concept.context-identity). Each worker receives the Panel brief and the earlier Issues. It is resumed once only when a finding's path is not one of the workspace, with those paths to correct. An audit that nothing changed follows it | Operation (Workers) | a grant that cannot be computed, a worker that ends `blocked` or `failed`, times out, returns an invalid result or changes a file stops that Module's panel, and so does a chair report still unaccounted after its last attempt: the Module is `incomplete` |
| 4 | For each Module whose panel completed, [settle](#earlier-issues) the earlier Issues the chair's findings name and resolve, and [report](#reporting-findings) every finding of the chair's report as an [Issue](../../glossary.json#concept.issue), in the order of the report | Operation (Issues) | a refusal of the Issue store: the Module is `incomplete` (`issues_unreported`) and its later findings are not reported |
| 5 | Derive every Module's outcome and the verdict from the Issues that stand | Operation | none |
| 6 | Write a [run record](../../glossary.json#concept.run-record) per worker | Operation (Workers) | the Operation fails |

The Operation panels Modules one after another. The reviewers and architects of one Module run at
the same time. A panel changes no file of the workspace. Its only writes are its
[Issue reports](../../glossary.json#concept.issue-report), which the primary worktree keeps.
Because no worker changes a file, no step runs
[configured checks](../../glossary.json#concept.configured-check). The only
[resume round](../../glossary.json#concept.resume-round) is the one that asks a worker to correct
the paths of its findings. When a Module's panel stops, the Module reports no Issue. It keeps the
reviews it had. It also keeps its **stop**: the status, summary and error link that stopped it.

### Normalizing a finding

The Operation normalizes every worker finding and every finding of the chair's report by these
rules:

- An absolute path inside the workspace becomes relative to it.
- When the path is a registered document or its metadata file, `module` becomes the Module that
  owns the cited document.
- When both conditions hold, the finding becomes a `suggestion`:
  - The finding has a blocking tier.
  - Its path is outside the reviewed Module's own documents and their metadata files.

  The `finding-scope` host evidence names the finding.
- When the path is still not one of the workspace after the worker's one resume round, the
  Operation rejects that finding alone. It reports the finding nowhere. It lists the finding with
  the reason and as `invalid-output` evidence. The worker's other findings go on.

### Earlier Issues

A Module's **earlier Issues** are the open [Issues](../../glossary.json#concept.issue) of the
project that meet both conditions:

- Their owner is the Module.
- One of their reports was made by a `spec_panel` run, or by a `project_review` run with the
  provenance phase `spec-panel` or `architecture`.

The Operation reads them from the primary worktree of the worktree the run started in. It reads
them in the order of their identities. A worker receives each as its latest report states it, with
these fields:

- Its identity.
- Its severity.
- Its tier.
- Its title.
- Its description.
- Its evidence.

Settling them follows the chair's claims under these rules. A finding whose `earlier` names an
earlier Issue is that Issue's new report. In either of these cases, a finding keeps no `earlier`
and becomes a new Issue:

- Its `earlier` names any other Issue.
- It names an Issue another finding of the report already named.

In those cases, the name is listed under `ignored`. When a resolution names an earlier Issue that
no finding names, it lists the Issue as `resolved` with its reason. When a resolution names any of
these, it is listed under `ignored`:

- Any other Issue.
- An Issue a finding names.
- An Issue already resolved.

Every earlier Issue that is neither named nor resolved is `carried`.

### Reporting findings

In bound and unbound runs alike, the Operation reports each finding through the Issue store as one
[Issue report](../../glossary.json#concept.issue-report). It never reports through a worker. When a
finding names an earlier Issue, the Operation appends it to that Issue. It uses the
[revision](../../glossary.json#concept.issue-revision) it reads just before the append. Any other
finding creates a new Issue. The report is:

| Field | Value |
| --- | --- |
| `report_key` | `<module>/<n>`: the reviewed Module and the finding's position in the chair's report, prefixed with `architecture/` for an architects' finding |
| `tier` | the finding's tier |
| `severity` | the finding's severity |
| `type`, `subtype` | `gap` and `missing-contract` for the dimension `context`, `gap` and `spec-conflict` for `consistency`, `bug` and `null` for every other dimension |
| `title` | the finding's title |
| `description` | the finding's problem, then its suggested repair, then the other Modules it names in `related` |
| `impact` | the finding's impact |
| `basis` | the Operation and run, the document, anchor and line judged, the dimension and the quoted evidence, the chair's note and the labels merged |
| `owner_target_id` | the finding's `module` |
| `evidence` | the cited document, described by its anchor or line |
| `issue_id`, `expected_revision` | for an append only: the earlier Issue and its revision |

The Operation supplies the report's provenance:

- `invocation_id` is the run identity.
- `agent` is `operation`.
- `operation` is `spec_panel`.
- `phase` is `architecture` for an **architects' finding**, a finding every label of whose `sources`
  is an architect's. It is `report` for every other finding, which merges at least one reviewer's
  label. Thus [Project review](../project-review/module.md)'s architecture review can offer an
  architects' finding as an earlier Issue, and its Module panels the others.
- `target_id` is the reviewed Module.
- `context_id` is the context identity of the chair's grant.
- For an unbound run, `change_id` is `null`. Otherwise, it is the workspace.
- When Git cannot tell, `head` is `null`. Otherwise, it is the commit the reviewed worktree's `HEAD`
  names.

The store commits each report on the primary branch before it answers. A refusal stops the
Module's reporting. Examples include:

- A busy [merge lock](../../glossary.json#concept.merge-lock) after the store's wait.
- An unfinished merge.
- A stale revision.
- A closed earlier Issue.

In that case, the Module is `incomplete` with `issues_unreported`. The cause of that error is the
store's error. The Operation reports no further finding of that Module. It never records the refusal
as an Issue. It goes on with the next Module. A finding left unreported keeps no `earlier`, since
nothing was appended to the earlier Issue it named. That Issue is `carried`. The Operation never
closes or reopens an Issue.

### Without the issues part

Where the issues part is not installed, steps 2 and 4 read and report no Issues:

- No earlier Issues are read or offered. Thus, every Module's `earlier_issues` is null.
- Every merged finding stays in the result with `issue` null.
- The result's summary says that the findings were not recorded as Issues.

Step 5 then derives each Module's outcome from the blocking findings of the chair's report, exactly
as from the Issues they would become. When one of a blocking tier stands, the outcome is
`changes_required`.

### Step output

Whether or not Issues are installed, the run's output also carries one `notes` item of kind
`review`. It follows the [step output convention](../../workflows/contracts.md#contract.workflows.step-output).
The item holds the verdict and each Module's outcome with its count of blocking findings. This
lets a workflow report the review without knowing this payload.

## The panel graph

```d2 illustrative
direction: right
review: "review\n(reviewer 1 … N and architect 1 … M,\nin parallel)"
gather: "gather\n(Operation)"
chair: "chair\n(chair worker, then the Operation's accounting)"
review -> gather
gather -> chair: every worker finished
chair -> chair: "a label unaccounted\nand an attempt remains"
```

- **review** runs once per seat. All seats run at the same time. Reviewer `n` reviews the Module on
  its own, by the Module quality criteria. Architect `n` judges it on its own, by the architecture
  quality criteria. Each sees no other review. The Operation [normalizes](#normalizing-a-finding)
  their findings. It labels a reviewer's findings `r<n>.1`, `r<n>.2` and so on. It labels an
  architect's findings `a<n>.1`, `a<n>.2` and so on. It keeps a rejected finding unlabelled, with
  the reason, among that worker's `rejected`. It keeps each worker's resolutions as its claims.
- **gather** waits for every seat. When any worker did not finish, it stops the Module with
  `panel_short`. Its causes are every such worker's error link. In that case, the chair does not
  run because a report must never silently lack a review.
- **chair** receives these items:
  - Every labelled finding, grouped by worker.
  - Every claimed resolution, grouped by worker.
  - The earlier Issues.

  It returns the report with these items:
  - Merged findings, each with these items:
    - The labels it merges as `sources`.
    - A `note`.
    - The severity and tier the chair gives it.
  - Rejections, each with a label and a reason.
  - Earlier Issues it finds resolved, each with a reason.

  The Operation normalizes the merged findings as well. When a merged finding's path is not one
  of the workspace, the Operation reports it nowhere. In that case, each of its labels becomes a
  rejection with the Operation's reason.
- **accounting**, part of the chair node, is the Operation's check of the report's labels. It
  checks that every label appears exactly once, in one finding's `sources` or as one rejection.
  It checks that the report names no other label. The result is host evidence of kind
  `panel-accounting`.

Control moves by these rules:

1. The reviewers and architects start together. Once all of them end, `gather` runs.
2. When every worker finished, the chair runs after `gather`. Otherwise the graph ends.
3. When the chair's turn stopped or its report is complete, the graph ends after the chair. When a
   label meets any of these conditions, the chair runs once more:
   - It is unaccounted for.
   - It is named twice.
   - It is unknown.

   On that second attempt, the chair receives its previous report and every accounting problem.
   When a report is still incomplete after that second attempt, it stops the Module with
   `report_unaccounted`. Its detail names every problem.

A Module's panel therefore takes these runs:

- `--reviewers` reviewer runs.
- `--architects` architect runs.
- When every reviewer and architect finished, one or two chair runs.

The graph's state holds these plain JSON values:

- The reviews.
- The host evidence.
- The Module's [context identities](../../glossary.json#concept.context-identity) for the two
  [task types](../../glossary.json#concept.task-type).
- The chair's latest report.
- Its accounting problems.
- The chair attempts.
- The Module's stop.

The parallel workers append to the reviews and the evidence in whatever order they end. The
Operation sorts the reviews by role and seat.

## Panel result

Every worker ends with the ordinary [worker result](../../glossary.json#concept.worker-result).
Its `output` depends on its role:

| Role | `output` |
| --- | --- |
| `reviewer` | `{"findings": [...], "resolved": [...]}` |
| `architect` | `{"findings": [...], "resolved": [...]}` |
| `chair` | `{"findings": [...], "rejected": [...], "resolved": [...]}` |

A reviewer finding is `{module, path, anchor, line, dimension, severity, tier, title, problem,
impact, evidence, suggestion}`. When it is an earlier Issue's problem, it also has `earlier`,
naming that Issue. The fields have these meanings:

- `module` is the reviewed Module, or the provider whose selected document the finding concerns.
- `path` is a document member in the grant.
- `anchor` and `line` are optional.
- `dimension` is one of the Module quality dimensions `readability`, `obligations`, `design`,
  `views`, `terminology` and `context`.
- `severity` is one of `critical`, `high`, `medium` and `low`.
- `tier` is one of `suggestion`, `obvious-fix`, `preferred-fix` and `decision-needed`.

Whatever its severity, a finding about another Module's document is always a `suggestion`.

Except for its dimension and the other registered Modules it may name, an architect finding has
that same shape. Its `dimension` is one of these architecture quality dimensions, or `context`:

- `responsibilities`.
- `ownership`.
- `interfaces`.
- `dependencies`.
- `failure-containment`.
- `consistency`.

It may add `related`, the other registered Modules the problem concerns. A chair finding has either
shape. It adds `sources`, a non-empty list of labels. It also adds `note`, which says what the chair
verified. The note also says why it chose the severity and tier. A rejection is `{source, reason}`.
A resolution is `{issue, reason}`. Both are optional lists, unlike `findings`. When a result does
not match its role's shape, it is an **invalid result**. An invalid result stops the Module. When a
report matches but accounts badly, it goes back to the chair as rule 3 says. When a worker is
`blocked` or `failed`, it still returns the empty lists its role asks for.

The chair may change these parts of a merged finding:

- Its wording.
- Its evidence.
- Its suggestion.
- Its severity.
- Its tier.

When any of that finding's sources named an earlier Issue, the chair names the earlier Issue it is.
It may not add a problem that no reviewer or architect reported. Every report finding has sources.
Each worker's findings stay in the payload as the Operation normalized them, so that the chair's
changes can be compared with them.

## Result status

| Verdict | Status | Error |
| --- | --- | --- |
| `accepted` or `changes_required` | `ok` | none |
| `incomplete`, and some incomplete Module failed: a worker that failed, a launch error, a timeout, an invalid result, an audit violation, an unaccounted report, Issues that could not be read or written, an unknown Module or a grant that could not be computed | `failed` | `panel_incomplete`, one cause per incomplete Module |
| `incomplete` otherwise: a structural error or a `blocked` reviewer, architect or chair | `blocked` | `panel_incomplete`, one cause per incomplete Module |

A loading error in step 1 and `langgraph_unavailable` are `failed` with no output. The same applies
to any other failure the step table calls a failure of the Operation. The Execution runner turns it
into a `failed` result with `host-error` evidence. In every other case, the result's `output` is the
panel payload, including for `blocked` and `failed`. It includes the reviews of a Module whose
panel stopped. Thus, the findings of the Modules that were paneled are never lost. The result's
error is the Operation's `panel_incomplete` link with the reason `decision`. Its causes are the
error of every incomplete Module, in the order of the Modules, never only the first.

The error of an incomplete Module is the Operation's link for it. Its actor names the Module. It
has one of these forms:

- `structural_errors`, with one cause per failing rule, file and message.
- `unknown_module`.
- `panel_short` over the links of the workers that did not finish, each naming its worker id.
  Below a worker's link are Workers' link and the worker's own.
- The link of a chair turn that stopped, with Workers' link and the chair's own below it.
- `report_unaccounted`.
- `issues_unreadable` or `issues_unreported` over the Issue store's error.

The summary names every incomplete Module with its own summary. It counts these items:

- The report's findings of a blocking tier and suggestions.
- The worker findings they were merged from.
- The rejections.
- The blocking Issues that stand.

The `worker` field holds the last worker result. The Operation adds the
[run result](../../glossary.json#concept.run-result)'s own evidence.
Each item names the Module and worker it concerns. The evidence includes:

- The grant and context identity of every worker.
- The `worker-model` item naming each worker's worker id, backend, model and level
  ([worker settings](../workers.md#worker-backend-and-model)).
- The audits.
- The transcript paths.
- The structural findings of step 1 (kind `structural`).
- The scope corrections (kind `finding-scope`).
- Every rejected finding (kind `invalid-output`).
- The accounting of every chair attempt (kind `panel-accounting`).
- Every Issue it reported to (kind `issue`).
- The panel graph as Mermaid text (kind `graph`).

For an Issue, the evidence item gives:

- The Issue.
- Whether the report created or appended to it.
- Its receipt's report identity.

The Operation writes the panel graph once per run in the
[run directory](../../glossary.json#concept.run-directory). The worker run identities are in the
result's `worker_runs`, in Module order.

## Panel payload

```concorde-contract
{
  "id": "contract.spec-review.panel-payload",
  "version": 6,
  "schema": {
    "type": "object",
    "required": [
      "verdict",
      "modules",
      "workflow"
    ],
    "additionalProperties": false,
    "properties": {
      "verdict": {
        "enum": [
          "accepted",
          "changes_required",
          "incomplete"
        ]
      },
      "workflow": {
        "type": "object"
      },
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "required": [
            "module",
            "outcome",
            "context_identity",
            "architecture_identity",
            "reviews",
            "findings",
            "rejected",
            "earlier_issues"
          ],
          "additionalProperties": false,
          "properties": {
            "module": {
              "type": "string",
              "minLength": 1
            },
            "outcome": {
              "enum": [
                "accepted",
                "changes_required",
                "incomplete"
              ]
            },
            "context_identity": {
              "anyOf": [
                {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                {
                  "type": "null"
                }
              ]
            },
            "architecture_identity": {
              "anyOf": [
                {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                {
                  "type": "null"
                }
              ]
            },
            "reviews": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "worker",
                  "role",
                  "seat",
                  "status",
                  "findings",
                  "rejected",
                  "resolved"
                ],
                "properties": {
                  "worker": {
                    "enum": [
                      "reviewer1",
                      "reviewer2",
                      "reviewer3",
                      "reviewer4",
                      "reviewer5",
                      "architect1",
                      "architect2"
                    ]
                  },
                  "role": {
                    "enum": [
                      "reviewer",
                      "architect"
                    ]
                  },
                  "seat": {
                    "type": "integer",
                    "minimum": 1
                  },
                  "status": {
                    "enum": [
                      "ok",
                      "blocked",
                      "failed"
                    ]
                  },
                  "findings": {
                    "type": "array",
                    "items": {
                      "$ref": "#/$defs/labelled"
                    }
                  },
                  "rejected": {
                    "type": "array",
                    "items": {
                      "$ref": "#/$defs/unusable"
                    }
                  },
                  "resolved": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "issue",
                        "reason"
                      ],
                      "properties": {
                        "issue": {
                          "type": "string",
                          "minLength": 1
                        },
                        "reason": {
                          "type": "string",
                          "minLength": 1
                        }
                      }
                    }
                  }
                }
              }
            },
            "findings": {
              "type": "array",
              "items": {
                "$ref": "#/$defs/reported"
              }
            },
            "rejected": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "source",
                  "reason"
                ],
                "properties": {
                  "source": {
                    "type": "string",
                    "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
                  },
                  "reason": {
                    "type": "string",
                    "minLength": 1
                  }
                }
              }
            },
            "earlier_issues": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "carried",
                    "resolved",
                    "ignored"
                  ],
                  "properties": {
                    "carried": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "issue",
                          "severity",
                          "tier",
                          "title"
                        ],
                        "properties": {
                          "issue": {
                            "type": "string",
                            "pattern": "^I-[0-9a-f]{32}$"
                          },
                          "severity": {
                            "anyOf": [
                              {
                                "enum": [
                                  "critical",
                                  "high",
                                  "medium",
                                  "low"
                                ]
                              },
                              {
                                "type": "null"
                              }
                            ]
                          },
                          "tier": {
                            "anyOf": [
                              {
                                "enum": [
                                  "suggestion",
                                  "obvious-fix",
                                  "preferred-fix",
                                  "decision-needed"
                                ]
                              },
                              {
                                "type": "null"
                              }
                            ]
                          },
                          "title": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    },
                    "resolved": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "issue",
                          "reason"
                        ],
                        "properties": {
                          "issue": {
                            "type": "string",
                            "pattern": "^I-[0-9a-f]{32}$"
                          },
                          "reason": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    },
                    "ignored": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "issue",
                          "reason"
                        ],
                        "properties": {
                          "issue": {
                            "type": "string",
                            "minLength": 1
                          },
                          "reason": {
                            "type": "string",
                            "minLength": 1
                          }
                        }
                      }
                    }
                  }
                }
              ]
            }
          }
        }
      }
    },
    "$defs": {
      "labelled": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "module",
          "path",
          "dimension",
          "severity",
          "tier",
          "title",
          "problem",
          "impact",
          "evidence",
          "suggestion",
          "label"
        ],
        "properties": {
          "module": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "format": "project-path"
          },
          "anchor": {
            "type": "string",
            "minLength": 1
          },
          "line": {
            "type": "integer",
            "minimum": 1
          },
          "dimension": {
            "enum": [
              "readability",
              "obligations",
              "design",
              "views",
              "terminology",
              "context",
              "responsibilities",
              "ownership",
              "interfaces",
              "dependencies",
              "failure-containment",
              "consistency"
            ]
          },
          "severity": {
            "enum": [
              "critical",
              "high",
              "medium",
              "low"
            ]
          },
          "tier": {
            "enum": [
              "suggestion",
              "obvious-fix",
              "preferred-fix",
              "decision-needed"
            ]
          },
          "title": {
            "type": "string",
            "minLength": 1
          },
          "problem": {
            "type": "string",
            "minLength": 1
          },
          "impact": {
            "type": "string",
            "minLength": 1
          },
          "evidence": {
            "type": "string",
            "minLength": 1
          },
          "suggestion": {
            "type": "string",
            "minLength": 1
          },
          "earlier": {
            "type": "string",
            "minLength": 1
          },
          "related": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "label": {
            "type": "string",
            "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
          }
        }
      },
      "reported": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "module",
          "path",
          "dimension",
          "severity",
          "tier",
          "title",
          "problem",
          "impact",
          "evidence",
          "suggestion",
          "sources",
          "note",
          "workers",
          "issue"
        ],
        "properties": {
          "module": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "format": "project-path"
          },
          "anchor": {
            "type": "string",
            "minLength": 1
          },
          "line": {
            "type": "integer",
            "minimum": 1
          },
          "dimension": {
            "enum": [
              "readability",
              "obligations",
              "design",
              "views",
              "terminology",
              "context",
              "responsibilities",
              "ownership",
              "interfaces",
              "dependencies",
              "failure-containment",
              "consistency"
            ]
          },
          "severity": {
            "enum": [
              "critical",
              "high",
              "medium",
              "low"
            ]
          },
          "tier": {
            "enum": [
              "suggestion",
              "obvious-fix",
              "preferred-fix",
              "decision-needed"
            ]
          },
          "title": {
            "type": "string",
            "minLength": 1
          },
          "problem": {
            "type": "string",
            "minLength": 1
          },
          "impact": {
            "type": "string",
            "minLength": 1
          },
          "evidence": {
            "type": "string",
            "minLength": 1
          },
          "suggestion": {
            "type": "string",
            "minLength": 1
          },
          "earlier": {
            "type": "string",
            "pattern": "^I-[0-9a-f]{32}$"
          },
          "related": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "sources": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
            }
          },
          "note": {
            "type": "string",
            "minLength": 1
          },
          "workers": {
            "type": "integer",
            "minimum": 1
          },
          "issue": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "string",
                "pattern": "^I-[0-9a-f]{32}$"
              }
            ]
          }
        }
      },
      "unusable": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "finding",
          "reason"
        ],
        "properties": {
          "finding": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "module",
              "path",
              "dimension",
              "severity",
              "tier",
              "title",
              "problem",
              "impact",
              "evidence",
              "suggestion"
            ],
            "properties": {
              "module": {
                "type": "string",
                "minLength": 1
              },
              "path": {
                "type": "string",
                "minLength": 1
              },
              "anchor": {
                "type": "string",
                "minLength": 1
              },
              "line": {
                "type": "integer",
                "minimum": 1
              },
              "dimension": {
                "enum": [
                  "readability",
                  "obligations",
                  "design",
                  "views",
                  "terminology",
                  "context",
                  "responsibilities",
                  "ownership",
                  "interfaces",
                  "dependencies",
                  "failure-containment",
                  "consistency"
                ]
              },
              "severity": {
                "enum": [
                  "critical",
                  "high",
                  "medium",
                  "low"
                ]
              },
              "tier": {
                "enum": [
                  "suggestion",
                  "obvious-fix",
                  "preferred-fix",
                  "decision-needed"
                ]
              },
              "title": {
                "type": "string",
                "minLength": 1
              },
              "problem": {
                "type": "string",
                "minLength": 1
              },
              "impact": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "string",
                "minLength": 1
              },
              "suggestion": {
                "type": "string",
                "minLength": 1
              },
              "related": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              }
            }
          },
          "reason": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "The outcome of one Spec panel. For each Module, reviews holds every worker's own findings and claimed resolutions, reviewers then architects, each in seat order, with its worker id, role and seat, each finding labelled r<seat>.<n> for a reviewer and a<seat>.<n> for an architect by the Operation; a worker that did not finish has its status and whatever it returned before stopping, usually nothing; rejected holds a worker's findings whose path is not one of the workspace, unlabelled, each as returned but for the earlier Issue it named, with the Operation's reason. findings is the chair's report: each merged finding lists in sources the labels it merges, with the chair's note, severity and tier, workers counts the distinct workers among those labels, issue is the Issue the Operation reported it to, null when the Issue store refused an earlier report, and earlier, present only when it was appended to an earlier Issue the Operation offered, names that Issue. rejected holds the labels the chair judged not to hold, each with its reason, and the labels of a merged finding whose path is not one of the workspace, with the Operation's reason, all reported nowhere. In a complete report every label appears exactly once, in one finding's sources or as one rejection. earlier_issues is null when the Module's earlier Issues were never read; otherwise carried lists the earlier Issues no finding named and no resolution resolved, which still stand, with their severity, tier and title; resolved lists the earlier Issues the chair found the Specs no longer have, with its reason, for the task to close, since the Operation closes none; ignored lists the names of Issues a finding or resolution gave that were not offered or already settled, with why. context_identity is the Module's review-spec grant identity and architecture_identity its review-architecture grant identity, null when no architect ran or no grant could be computed. A Module's outcome is incomplete when its panel stopped or its Issues could not be read or all written, changes_required when an Issue of a blocking tier stands for it, reported now or carried, and accepted otherwise; the verdict is the highest outcome in the order accepted, changes_required, incomplete. Findings, severities, tiers, merges, notes, rejections and resolutions are worker claims; the Operation labels, normalizes, counts, checks the accounting and reports the Issues. workflow is the object of Workflows' step output convention, which defines its fields: one review note whose data holds the verdict and each Module's outcome with its count of blocking findings that stand. A behaviour or field change increments the version.",
  "example": {
    "verdict": "changes_required",
    "modules": [
      {
        "module": "module.checkout",
        "outcome": "changes_required",
        "context_identity": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "architecture_identity": "sha256:1f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "reviews": [
          {
            "worker": "reviewer1",
            "role": "reviewer",
            "seat": 1,
            "status": "ok",
            "findings": [
              {
                "module": "module.checkout",
                "path": "specs/checkout/requirements.md",
                "anchor": "req.checkout.single-order",
                "dimension": "obligations",
                "severity": "medium",
                "tier": "obvious-fix",
                "title": "A requirement joins two obligations",
                "problem": "The requirement states two obligations.",
                "impact": "A test cannot tell which obligation a failure breaks.",
                "evidence": "Checkout SHALL create one order and SHALL notify the customer.",
                "suggestion": "Split the notification into its own requirement.",
                "label": "r1.1"
              }
            ],
            "rejected": [],
            "resolved": []
          },
          {
            "worker": "architect1",
            "role": "architect",
            "seat": 1,
            "status": "ok",
            "findings": [
              {
                "module": "module.checkout",
                "path": "specs/checkout/module.md",
                "anchor": "uses-inventory",
                "dimension": "interfaces",
                "severity": "high",
                "tier": "decision-needed",
                "title": "Checkout relies on Inventory's internal reservation table",
                "problem": "Checkout reads Inventory's reservation rows instead of a promise of Inventory.",
                "impact": "A change of Inventory's storage silently breaks Checkout.",
                "evidence": "Checkout reads the reservations table to confirm stock.",
                "suggestion": "Rely on an Inventory promise to confirm a reservation.",
                "related": [
                  "module.inventory"
                ],
                "label": "a1.1"
              }
            ],
            "rejected": [],
            "resolved": []
          }
        ],
        "findings": [
          {
            "module": "module.checkout",
            "path": "specs/checkout/module.md",
            "anchor": "uses-inventory",
            "dimension": "interfaces",
            "severity": "high",
            "tier": "decision-needed",
            "title": "Checkout relies on Inventory's internal reservation table",
            "problem": "Checkout reads Inventory's reservation rows instead of a promise of Inventory.",
            "impact": "A change of Inventory's storage silently breaks Checkout.",
            "evidence": "Checkout reads the reservations table to confirm stock.",
            "suggestion": "Rely on an Inventory promise to confirm a reservation.",
            "related": [
              "module.inventory"
            ],
            "sources": [
              "a1.1"
            ],
            "note": "Inventory's Spec promises no reservation query; which promise to add is a design choice.",
            "workers": 1,
            "issue": "I-0123456789abcdef0123456789abcdef"
          }
        ],
        "rejected": [
          {
            "source": "r1.1",
            "reason": "The requirement was split in the current Specs; the quoted sentence is not there."
          }
        ],
        "earlier_issues": {
          "carried": [],
          "resolved": [],
          "ignored": []
        }
      }
    ],
    "workflow": {
      "decision_points": [],
      "decisions": [],
      "deviations": [],
      "notes": [
        {
          "kind": "review",
          "text": "spec_panel verdict changes_required: module.checkout changes_required",
          "data": {
            "verdict": "changes_required",
            "modules": [
              {
                "module": "module.checkout",
                "outcome": "changes_required",
                "blocking": 1
              }
            ]
          }
        }
      ],
      "blocking": null,
      "data": {}
    }
  }
}
```
