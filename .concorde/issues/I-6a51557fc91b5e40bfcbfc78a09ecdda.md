# I-6a51557fc91b5e40bfcbfc78a09ecdda

```json
{
  "schema_version": 3,
  "id": "I-6a51557fc91b5e40bfcbfc78a09ecdda",
  "status": "open",
  "reports": [
    {
      "id": "sha256:5775d7799558dc02a30857a9fe8e000017a88d2d388694a497f8545341cc73bb",
      "created_at": "2026-10-01T06:13:09.803108+00:00",
      "report": {
        "report_key": "module.workers/15",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "The canonical audit evidence record lacks a defined structure",
        "description": "The canonical round contract does not define audit fields or nonempty violation item shapes, including the required glossary-owner evidence.\n\nSuggested repair: Define changed-path and violation fields and their item types, covering ordinary paths, deletions, Git-state changes and glossary entries with before/after owners. Include a nonempty example and preserve the existing null-before-audit meaning.\n\nOther Modules concerned: module.operations",
        "impact": "Independent producers and consumers can disagree about nonempty violations and ownership evidence while satisfying the published contract.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/execution/workers/contracts.md at contract.workers.worker-round-trace, line 680 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The audit schema accepts any object; its semantics specify only \"the verdict of the host's audit after the round (changed paths and violations)\". The example is `{\"changed\": [\"src/http/retry.py\"], \"violations\": []}`. The entry requires glossary violations named `<glossary>#<concept>` \"with both owners\".\n\nThe panel's chair merged r2.3 and verified: Checked the entire round contract and audit explanations. Null already means the audit did not run; the unresolved part is the canonical completed-audit structure and violation representations, which require a contract decision.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/contracts.md",
            "description": "contract.workers.worker-round-trace, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:d9d26b9c3b118a1ec71a8cb21310fcb039173ad3cfece95db1c14e2faee0ef23",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    },
    {
      "id": "sha256:e41da97b312b8072a98223033adc62723403e82c0ef4aa36eab59a627381dff4",
      "created_at": "2026-10-01T14:47:38.757058+00:00",
      "report": {
        "report_key": "module.workers/15--severity",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "The canonical audit evidence record lacks a defined structure",
        "description": "The canonical round contract does not define audit fields or nonempty violation item shapes, including the required glossary-owner evidence.\n\nSuggested repair: Define changed-path and violation fields and their item types, covering ordinary paths, deletions, Git-state changes and glossary entries with before/after owners. Include a nonempty example and preserve the existing null-before-audit meaning.\n\nOther Modules concerned: module.operations",
        "impact": "Independent producers and consumers can disagree about nonempty violations and ownership evidence while satisfying the published contract.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/execution/workers/contracts.md at contract.workers.worker-round-trace, line 680 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The audit schema accepts any object; its semantics specify only \"the verdict of the host's audit after the round (changed paths and violations)\". The example is `{\"changed\": [\"src/http/retry.py\"], \"violations\": []}`. The entry requires glossary violations named `<glossary>#<concept>` \"with both owners\".\n\nThe panel's chair merged r2.3 and verified: Checked the entire round contract and audit explanations. Null already means the audit did not run; the unresolved part is the canonical completed-audit structure and violation representations, which require a contract decision. Severity medium assessed by the main agent on 2026-10-01: Audit violation records have no defined structure, so producers and consumers can disagree on nonempty violations while both conforming.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/contracts.md",
            "description": "contract.workers.worker-round-trace, cited by the obligations finding"
          }
        ],
        "severity": "medium",
        "issue_id": "I-6a51557fc91b5e40bfcbfc78a09ecdda",
        "expected_revision": "sha256:3947d839b5e91bf5a9fb718f915ed03239ccfa451739a10eea54ea86e82cbe07"
      },
      "source": {
        "invocation_id": "cli-458ec656-74bb-4935-a90f-49f78e59672d",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:faf611ab5bdd47f3ab93968932072ec605e527fb468e96a4f6c20a419e8f0f8c",
        "change_id": null,
        "head": "b12075aa582fd715d80249501fcfafa95a48ebfd"
      }
    }
  ],
  "dispositions": []
}
```
