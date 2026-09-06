# Module

A Module is a cohesive implementation responsibility specified through its provided and required APIs.
Function calls are valid boundaries. Its complete Markdown collection defines callable signatures,
input and output types, preconditions, state/effects, obligations, errors, compatibility, and representative
usage. Describe APIs directly instead of manufacturing Feature wrappers. Interface signatures and usage
examples are Spec content; private algorithms and helpers belong to implementation source.

A Module may compose components and participate in Domain scopes independently. Its own Spec states
all business facts and collaborator promises required to understand and use its APIs. It does not
inherit a Service's, Domain's, parent's, or provider's Spec. Selecting one API retains the complete
registered Markdown collection. Only an implementation invocation may expose authorized source code.

The main coordinator may design or route this Module from identity, responsibility and selection
facts contained in admitted Domain/Service Specs plus exact registry metadata. It never receives this
Module document collection. During an accepted topology change, only a separate target-local Spec
author receives the current Module documents and proposed descriptor.
