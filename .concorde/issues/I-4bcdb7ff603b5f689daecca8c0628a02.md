# I-4bcdb7ff603b5f689daecca8c0628a02

```json
{
  "schema_version": 4,
  "id": "I-4bcdb7ff603b5f689daecca8c0628a02",
  "status": "open",
  "reports": [
    {
      "id": "sha256:7c8984aef013b87900b2f5aff1f14d1ca53be3bc8840fa326792d96773e5d800",
      "created_at": "2026-10-08T08:29:04.110543+00:00",
      "report": {
        "report_key": "spec-panel/module.method/8",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Distinguish configuration refusals from recorded worker runs",
        "description": "The recording explanation does not explicitly distinguish a host refusal of a worker-run request from a configuration-reader refusal before that request. The surrounding sequence includes both kinds of refusal.\n\nSuggested repair: State locally that configuration-reader refusals yield the Operation's component error and no worker record. Preserve the record guarantee for worker runs actually requested from the host.\n\nOther Modules concerned: module.workers",
        "impact": "A reader troubleshooting a configuration refusal can look for a worker record that does not exist, although the provider document explains the distinction.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/method/workers.md at Standard worker sequence, line 185 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: workers.md says, “Workers writes the run record for every worker run it was asked to start, including one refused before launch.” Its step 3 includes configuration and model refusals. Workers' launch.md, under “Refusals before a run,” states that configuration-reader refusals occur before any worker run exists and create no run directory, progress file or run record.\n\nThe panel's chair merged r3.3 and verified: Verified the wording, surrounding sequence, and provider's explicit distinction between configuration-reader refusals and host run requests. Retained this as low-severity advice: “was asked to start” limits the guarantee, so the promise need not change, but the local explanation could make that limit clearer.",
        "owner_target_id": "module.method",
        "evidence": [
          {
            "path": "specs/concorde/method/workers.md",
            "description": "Standard worker sequence, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.method",
        "context_id": "sha256:d54d768ad7d3c5e67afd9b0e84e27e9dfacdaab25ce1f46fbcbf1d1678f815fb",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
