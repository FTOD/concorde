# I-8f9eb3e6cdfd5456bfab5b13b97440da

```json
{
  "schema_version": 4,
  "id": "I-8f9eb3e6cdfd5456bfab5b13b97440da",
  "status": "open",
  "reports": [
    {
      "id": "sha256:c6f1283d9a0f1e6675fa666f4b0ab0835f02d3f00276d2f6d84b228fa7795a87",
      "created_at": "2026-10-03T05:42:50.606269+00:00",
      "report": {
        "report_key": "module.dogfooding/4",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Develop guidance omits execution-command runs",
        "description": "The develop guidance omits execution commands from both its explicit run-observation rule and the list of running work to check before updating. The Module expressly includes execution commands, which are distinct from Operations.\n\nSuggested repair: Add execution-command runs to the shared observation fragment and the pre-update guidance, and update the guidance assertions to retain that distinction.",
        "impact": "The instructions omit standalone deterministic runs such as task-validation and delivery from the explicit observation and pre-update checks, leaving those runs outside the stated monitoring procedure.",
        "basis": "code_review run r-20261003T053126-code_review-bd94cc7c (module review) judged prompts/dogfooding/common/observe-runs.md:5-6, prompts/dogfooding/skill.md:149-154, tests/concorde/dogfooding/test_dogfooding.py:259-279 against specs/concorde/dogfooding/module.md#what-the-projects-main-agent-does and reported a violation: The Spec requires observation of 'every run of an Operation or execution command'. The shared rule says only 'Observe every Operation, workflow and worker run closely'. The update guidance likewise says 'while no Operation, workflow or task session is running' and describes refusal only while 'an Operation run is still running'.",
        "owner_target_id": "module.dogfooding",
        "evidence": [
          {
            "path": "prompts/dogfooding/common/observe-runs.md",
            "description": "lines 5-6, shown by the violation finding"
          },
          {
            "path": "prompts/dogfooding/skill.md",
            "description": "lines 149-154, shown by the violation finding"
          },
          {
            "path": "tests/concorde/dogfooding/test_dogfooding.py",
            "description": "lines 259-279, shown by the violation finding"
          },
          {
            "path": "specs/concorde/dogfooding/module.md",
            "description": "defines specs/concorde/dogfooding/module.md#what-the-projects-main-agent-does, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T053126-code_review-bd94cc7c",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.dogfooding",
        "context_id": "sha256:9230d00ae980f3ee793903cac51170f04f38967a32aa3d85efe273d558793650",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": []
}
```
