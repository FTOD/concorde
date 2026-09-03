# reflections-malformed

Overlay `.concorde/reflections/` onto a copy of `valid-project`. Validation must report
all five reflection rule categories and leave every file byte-identical:

| Entry | Breach | Rule |
|---|---|---|
| pending/R-001 | empty `Observed` | `CONCORDE-REFLECT-001` |
| pending/R-002 metadata | duplicate R-001 identifier | `CONCORDE-REFLECT-002` |
| pending/R-001 | `kind: bug` | `CONCORDE-REFLECT-003` |
| pending/R-001 | missing concerns path | `CONCORDE-REFLECT-004` |
| planned/R-003 | `triage: pending` filed under `planned/` | `CONCORDE-REFLECT-005` |
