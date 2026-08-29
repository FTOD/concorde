# reflections-malformed

Overlay `specs/example/reflections.md` onto a copy of `valid-project`. Validation must report exactly
one finding per rule and leave every file byte-identical:

| Entry | Breach | Rule |
|---|---|---|
| R-001 | missing `Effect` | `CONCORDE-REFLECT-001` |
| R-001 (second) | duplicate identifier | `CONCORDE-REFLECT-002` |
| R-002 | `Kind: bug` | `CONCORDE-REFLECT-003` |
| R-003 | `Feature: feature.example.missing` | `CONCORDE-REFLECT-004` |
