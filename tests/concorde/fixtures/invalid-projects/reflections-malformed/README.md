# reflections-malformed

Overlay `.concorde/reflections/` onto a copy of `valid-project`. Validation must report
all four reflection rule categories and leave every file byte-identical:

| Entry | Breach | Rule |
|---|---|---|
| R-001 | empty `Observed` | `CONCORDE-REFLECT-001` |
| R-002 metadata | duplicate R-001 identifier | `CONCORDE-REFLECT-002` |
| R-001 | `kind: bug` | `CONCORDE-REFLECT-003` |
| R-001 | missing concerns path | `CONCORDE-REFLECT-004` |
