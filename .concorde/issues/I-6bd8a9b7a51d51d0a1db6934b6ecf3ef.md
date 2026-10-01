# I-6bd8a9b7a51d51d0a1db6934b6ecf3ef

```json
{
  "schema_version": 3,
  "id": "I-6bd8a9b7a51d51d0a1db6934b6ecf3ef",
  "status": "open",
  "reports": [
    {
      "id": "sha256:ba668bcce5af1d970bc4080e2aca415add0532c4e0cfb3bdedac7615991eae2f",
      "created_at": "2026-10-01T05:39:37.002938+00:00",
      "report": {
        "report_key": "module.e2e/16",
        "tier": "suggestion",
        "type": "bug",
        "subtype": null,
        "title": "Link session statuses and prompt parts to their explanations",
        "description": "The uses of child-specific statuses and prompt parts lack nearby links to their explanations.\n\nSuggested repair: Link exited and no_session to the child's overview, and link the scenario's headless note and test procedure to the child's prompt explanation.\n\nOther Modules concerned: module.headless-sessions",
        "impact": "Readers arriving at these passages must search the child document to understand the session outcomes and prompt components.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/e2e/module.md at running-a-workflow, line 261 by the terminology criterion of the Protocol's Evaluating a Spec; the Specs read: The entry uses \"`run_failed` when the headless session ends `exited` or `no_session`\". scenario.e2e.headless uses \"the headless note alone, without the test procedure of a headless main session\". Headless sessions explains those statuses in its overview and the prompt parts under What the session is told.\n\nThe panel's chair merged r1.11 and verified: Verified the definitions exist in the selected child and that the parent already links the child generally. Retained as a local navigation improvement, not missing context or a blocking undefined concept.",
        "owner_target_id": "module.e2e",
        "evidence": [
          {
            "path": "specs/concorde/e2e/module.md",
            "description": "running-a-workflow, cited by the terminology finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.e2e",
        "context_id": "sha256:6d1ed9a2394f063345e81a92404e19816da64eedbb1c079e0a2bac0dfb3233b5",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    },
    {
      "id": "sha256:5c6ab33762f9f78c1c9cb12848d9f96bdc382bb95870f21f91769ade2025fc7b",
      "created_at": "2026-10-01T14:47:27.540286+00:00",
      "report": {
        "report_key": "module.e2e/16--severity",
        "tier": "suggestion",
        "type": "bug",
        "subtype": null,
        "title": "Link session statuses and prompt parts to their explanations",
        "description": "The uses of child-specific statuses and prompt parts lack nearby links to their explanations.\n\nSuggested repair: Link exited and no_session to the child's overview, and link the scenario's headless note and test procedure to the child's prompt explanation.\n\nOther Modules concerned: module.headless-sessions",
        "impact": "Readers arriving at these passages must search the child document to understand the session outcomes and prompt components.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/e2e/module.md at running-a-workflow, line 261 by the terminology criterion of the Protocol's Evaluating a Spec; the Specs read: The entry uses \"`run_failed` when the headless session ends `exited` or `no_session`\". scenario.e2e.headless uses \"the headless note alone, without the test procedure of a headless main session\". Headless sessions explains those statuses in its overview and the prompt parts under What the session is told.\n\nThe panel's chair merged r1.11 and verified: Verified the definitions exist in the selected child and that the parent already links the child generally. Retained as a local navigation improvement, not missing context or a blocking undefined concept. Severity low assessed by the main agent on 2026-10-01: Missing links only make readers search the child document for status and prompt explanations.",
        "owner_target_id": "module.e2e",
        "evidence": [
          {
            "path": "specs/concorde/e2e/module.md",
            "description": "running-a-workflow, cited by the terminology finding"
          }
        ],
        "severity": "low",
        "issue_id": "I-6bd8a9b7a51d51d0a1db6934b6ecf3ef",
        "expected_revision": "sha256:87abecad07012fe07c857ecb2efeaa1d09f370c31aba799303fa0d0e6ab7aed5"
      },
      "source": {
        "invocation_id": "cli-4c8113c3-7b96-40e1-9740-c772776c72fc",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.e2e",
        "context_id": "sha256:faf611ab5bdd47f3ab93968932072ec605e527fb468e96a4f6c20a419e8f0f8c",
        "change_id": null,
        "head": "60c07fda95bec78c88896741815d68320fdde369"
      }
    }
  ],
  "dispositions": []
}
```
