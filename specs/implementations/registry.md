```concorde-document
{
  "id": "document.specs.implementations.registry",
  "targets": [
    "implementation.registry"
  ],
  "main_visible": false
}
```

# Registry implementation

`implementation.registry` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.registry`.

## Responsibility

Realize explicit Module/Implementation/document indexes and deterministic forward/reverse selection over safe project paths.

## Bound files

- `src/concorde/specification/repository.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/specification/repository.py` | Separately indexes Module and Implementation descriptors, explicit documents, unique file owners and reverse users. Module selection never follows an implementation reference to read its body. |

## Implementation interfaces, dependencies and constraints

SpecRepository holds separate descriptors and a document cache, with optional in-memory registry/document overlays. It depends on canonical JSON/path admission and offline schema validation. Index creation rejects unresolved or duplicate identities, invalid composition and nonunique file owners. Module selection resolves a local focus without shrinking documents; implementation file enumeration is explicit and may distinguish declared pending files from existing regular files. Inline Mermaid is carried as document bytes with diagrams=[]; cached repository instances are reconstructed after source changes. The specified spec_files/spec_pair additions resolve explicit identity indexes to complete ordered file sets without reading bound source or widening ordinary select(). These additions require implementation before full query-support claims.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Repository and Module-model cases must cover shared document membership, focus ownership, one local module.md independent of order, acyclic parentage, dependency-versus-composition meaning and duplicate file owners. Check in-memory overlays produce no writes and reverse users include every Module sharing an implementation.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
