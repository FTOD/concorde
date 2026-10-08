# I-c34c317a7caa5cfbba1a863f3f60a7ab

```json
{
  "schema_version": 4,
  "id": "I-c34c317a7caa5cfbba1a863f3f60a7ab",
  "status": "open",
  "reports": [
    {
      "id": "sha256:8fd1118b1cc4d059356119b941165d0215af5f496747df3f4f7c67bd64548fc0",
      "created_at": "2026-10-08T07:08:30.124113+00:00",
      "report": {
        "report_key": "architecture/project/1",
        "tier": "obvious-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "The root excludes General work from permitted Spec-writing flows",
        "description": "The root excludes General work's workers from its exhaustive account of who may change Specs. General work explicitly permits those writes when its chosen task type grants them.\n\nSuggested repair: Explain permitted worker Spec writes by task-type grants and include General work's supported flow. Link to its canonical requirements, while retaining the separate restriction that deriving promises from code requires code-to-spec.\n\nOther Modules concerned: module.general-work, module.method, module.specification, module.adoption",
        "impact": "A reader following the root would reject or reroute General work's supported Spec-rewrite flow, despite its canonical scenario permitting it.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/module.md at Spec first, line 547 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: specs/concorde/module.md:547–552 says: \"Outside a `specify` run and the [Adoption](method/adoption/module.md) route, only these actors change Specs:\" followed by the developer, main agent and task session. In specs/concorde/method/general-work/scenarios.md, scenario.general-work.rewrite permits `general --type specify` and states \"THEN the worker may change the Module's Spec documents and nothing else\". req.general-work.grant-by-type assigns the grant of the named task type.\n\nThe panel's chair merged a2.3 and verified: Verified the root's exhaustive statement against General work's scenario and grant requirement. High severity because it contradicts a supported working flow, with the child Spec providing the way out. The obvious repair is to align the root with the existing task-type grant policy. This is distinct from the earlier Issue about Execution's unbound admission allowlist.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/module.md",
            "description": "Spec first, cited by the consistency finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "project",
        "context_id": "sha256:d60a2243d2ea4900cc78529447d25f87327f36be2dbd0e528e665dfff1bcbf94",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "architecture"
      }
    }
  ],
  "dispositions": []
}
```
