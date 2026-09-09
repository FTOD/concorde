```concorde-document
{
  "id": "document.specs.modules.concorde.publication.architecture",
  "targets": [
    "module.publication"
  ],
  "main_visible": true
}
```

# Architecture

concorde docsite proposes and applies site scaffolding. The site reads registry schema 2 and builds pages, navigation and relationship views from registered sources. Module composition, dependencies and implementation reuse are distinct edges. Each Module opens its module.md. Implementation pages expose their file bindings and using Modules. Only a complete current candidate is promoted.

## Internal domain

A scaffold proposal establishes a site. The content pipeline resolves registered Module and Implementation documents into pages, routes, sidebars and relationship edges. Diagrams are rendered only from declared sources. Candidate manifests bind generated views to source bytes before promotion. The Python scaffolder and TypeScript publishing pipeline are separate reusable implementations of this one Module.

## Relied-upon Module promises

Each declaration below is local contract content. It grants no access to the provider's remaining Spec or implementation.

```concorde-dependencies
[
  {
    "target_id": "module.file-transactions",
    "responsibility": "Apply exact multi-file changes with before-digest checks and rollback.",
    "selection_condition": "Select when the task concerns file transactions.",
    "relied_upon_promises": [
      "file_change captures a current before-digest. apply_files accepts exact allowed paths, stages changes, rechecks originals and invokes verification. A stale, invalid or failed application restores prior bytes and removes newly created files. Proposed content cannot expand the allowed set."
    ]
  }
]
```
