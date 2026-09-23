# Worker result contract

The exact answer every worker ends with. The [entry](module.md#concept.workers.worker-result)
explains its role; [the run mechanics](launch.md#rounds) say how the host reacts to it.

```concorde-contract
{
  "id": "contract.workers.worker-result",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["status", "summary", "problem", "attempts", "evidence", "options",
                 "recommendation", "blocking", "impact", "proposed_deletions", "output"],
    "properties": {
      "status": {"enum": ["ok", "blocked", "failed"]},
      "summary": {"type": "string", "minLength": 1},
      "problem": {"type": "string"},
      "attempts": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "evidence": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["kind", "ref", "detail"],
          "properties": {
            "kind": {"enum": ["file", "command", "output", "spec"]},
            "ref": {"type": "string", "minLength": 1},
            "detail": {"type": "string"}
          }
        }
      },
      "options": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "recommendation": {"type": "string"},
      "blocking": {"type": "boolean"},
      "impact": {"type": "string"},
      "proposed_deletions": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "output": {"type": "object"}
    }
  },
  "semantics": "The structured result a worker returns through --json-schema at the end of every round. status ok means the worker finished its task; blocked means it cannot continue without a decision above it, such as a Spec gap or a missing grant, and failed means it tried and could not finish. summary says what was done. For blocked and failed, problem says what could not be done and why, attempts what was tried, options the possible ways forward, recommendation the worker's preferred option, blocking whether the task cannot proceed without a decision, and impact what else is affected; for ok they may be empty. evidence items point at a file, command, output or Spec (kind) by a path or identity (ref) with a short explanation (detail); they are the worker's claims, never host evidence. proposed_deletions lists absolute paths in the task worktree the worker wants deleted; the host deletes only those in the grant's rw list after a clean audit. output is the Operation-specific part of the answer, such as an assessment, a code change summary or review findings; the Operation supplies its schema, which the host embeds at this key in the schema it passes to --json-schema, and it is an empty object for Operations without one. The host keeps the result verbatim in the run record.",
  "example": {
    "status": "blocked",
    "summary": "Added discount rules to the cart; the rounding rule is not specified.",
    "problem": "The Spec does not say whether discounts are rounded per line or per order.",
    "attempts": ["Searched the Module's requirements and scenarios for rounding"],
    "evidence": [
      {"kind": "spec", "ref": "req.shop.discount-total", "detail": "states the total but not the rounding"}
    ],
    "options": ["Round per line", "Round per order"],
    "recommendation": "Round per order, as the invoice scenario implies.",
    "blocking": true,
    "impact": "Invoices and refunds use the same total.",
    "proposed_deletions": [],
    "output": {}
  }
}
```
