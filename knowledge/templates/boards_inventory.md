# Boards inventory (step zero, STRICT RULE: DECOMPILE EVERYTHING)

One row per board with its own CPU, MCU, ROM or firmware. States: `complet` (every routine decompiled, named where used,
every datum it sends or receives traced), `partiel`, `absent`. `tools/check_strict_rule.py` fails while any row is not `complet`, except an `absent` board listed with an owner approval in `docs/board_exceptions.md` (template `board_exceptions.md`).
Column names matter (`Board` first, a column containing `Decompile`).

| Board | CPU / MCU | ROM file(s) | Decompile state | Where (decompile, notes) | Open |
|---|---|---|---|---|---|
| Main CPU | e.g. 6809 / ARM7 | | absent | | |
| DMD controller | | | absent | | |
| Sound board | | | absent | | |
| (any other: power driver, display driver, I/O expander...) | | | absent | | |
