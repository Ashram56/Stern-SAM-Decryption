# Board exceptions to the strict rule (owner-approved)

Use only when a board's firmware cannot be had (no dump exists) **and** the code shows no score, display, insert, coil or sound depends on it. The owner decides; the line carries his approval. `tools/check_strict_rule.py` then accepts that board as `absent` in `docs/boards_inventory.md` (a `partiel` board is never excused).

Rule for a line: the board name in backticks (it must appear in the inventory's Board cell), then the words `approved by <owner> YYYY-MM-DD`. Give the code evidence in the Exception cell: the addresses where the board is read or written, the variables the exchange uses, and the proof (static search) that nothing else reads them.

| Board | State | Exception | Approval |
|---|---|---|---|
| `Security PIC` (example) | absent: no dump exists | **Absent, no game logic.** Status read at `0x3fc6` (bank:addr), counter in RAM `$051e` / `$0524`, read and written only by these routines: no score, display, insert, coil or sound depends on them. | approved by Vincent 2026-11-26 |
