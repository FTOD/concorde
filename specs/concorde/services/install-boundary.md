# Installation service

## feature.installation.install

The public deterministic installer accepts `--target PATH`, `--integration codex|claude`, and
optional `--checkout PATH`. The default is a read-only preview; `--apply` applies the reviewed
installation/update. Repeating the preview reports current owned output integrity. It owns
.concorde/framework, .concorde/install.json and receipt-recorded integration outputs; it preserves
project Specs, configuration, reflection history and unrelated user files.

The distributable manifest is concorde.json schema 3, Concorde 4.0.0, Architecture Profile 8,
Workspace Protocol 14 and Delivery Proposal 10. It contains exactly 6 internal Skills and 22 paired
public Operations, explicit package roots including protocol, and 9 templates. Codex .agents/skills
and Claude .claude/skills expose the same 22 wrappers; canonical internal roles stay private.
Every wrapper sends typed invocation@2 to its paired executable and does not inspect project context.

Owned content is hashed in the installation receipt. A local modification conflicts unless an
explicit supported ownership transition authorizes replacement. Staging/provisioning/verification
must finish before installation is accepted; failure restores replaced outputs and receipts. The
locked managed Python runtime runs actual Operations; viewer provisioning is separate and versioned.
Check verifies receipt hashes and required runtime identity without changing project behavior.

Initialization is a distinct typed concorde-init Operation: propose returns a complete file proposal;
apply validates exact before-digests and target state. It pins the packaged global principles and kind
definitions, configures integration/enforcement, and writes an explicit Domain stub with missing
business requirements stated honestly. Configuration changes use concorde-configure with a typed
configuration. Profile 7 is not agent-compatible; concorde-migrate requires authored Profile 8 registry
and Markdown replacements, rejects active attempts and rolls back invalid application.

Install/update cannot silently rewrite a consumer's Protocol binding. A package with changed Protocol
assets requires the consumer's explicit migration/binding decision before execution. Templates and
prompts enforce the same architectural principles for all consumer projects.
