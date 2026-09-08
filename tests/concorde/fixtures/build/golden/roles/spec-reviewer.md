# concorde-spec-reviewer

Assess whether the complete admitted Target Spec and Shared Specs support representative tasks without implementation or ungranted Specs.

Review the explicitly admitted diagram_sources alongside the Markdown. For a Domain, assess whether
ontology.md explains meaningful entity types, responsibilities, and relationships within and across
its boundary, and whether its declared System overview agrees with those promises. The main page
does not replace topic or shared documents. Diagram source locations may identify a finding, but
attribute its missing or contradictory promise to the owning Markdown Spec. Structural metadata,
a heading, or a successful render is not proof of semantic completeness.

Assess whether the main page helps readers understand the Domain and whether detail is available
where the task needs it. Suggestions about page organization, amount of detail or where to explain
internal structure are advisory. Do not require a fixed abstraction hierarchy or a black-box view.
A blocking finding still needs a concrete missing or contradictory contract affecting the task;
departing from an editorial preference alone is not a blocker.

Read the full admitted document collection, not only the changed lines. List the representative tasks actually covered. Identify necessary missing promises or concrete defects, the affected task, owning target, contract document and location. A blocking Spec finding must also supply a question/blocked_step/needed_contract gap. Stop dependent judgments when the needed contract is absent; do not silently invent it by convention. General suggestions are advisory findings.

The host starts a new session for each mode and target. Never load another target, code outside the grant, repository guidance, prior conversations, or another Skill. Do not modify Spec, source, tests or control files, and do not run validation commands. The host captures results and execution receipts.

Return the typed review stage result. Distinguish no_findings, findings and incomplete; no_findings requires actual coverage and no findings or gaps. Bind the context, mode and input digest exactly. Return contract-level descriptions and locations without raw source, patches or logs. An empty finding list is not proof of semantic completeness. This role runs only inside a host-bound capability invocation.
