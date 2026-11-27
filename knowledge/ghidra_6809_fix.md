# Ghidra 6809: fixing "Overlapping input varnodes"

*Résumé (FR).* Sur la ROM Medieval Madness 1.09c, Ghidra 11.2.1 ne décompilait pas 156 fonctions sur 1 390 (`Low-level Error: Overlapping input varnodes`). Cause trouvée (code, banc d'essai + vraie ROM) : dans la spécification SLEIGH du 6809, `PULS/PULU ... PC` est un `goto [t]` (saut indirect) au lieu d'un `return [t]` ; le décompilateur croit alors tous les registres vivants à la sortie, d'où le conflit entre A, B et D. Correctif : `tools/ghidra_6809/` (2 mots dans `6x09_pull.sinc`, plus un `6809.cspec` où D remplace les paramètres A et B). Résultat : 156 -> 0 échec, avertissements « jumptable » 777 -> 1.

Applies to every 6809 game (Williams WPC, Stern Whitestar; Medieval Madness, Terminator 2, Lord of the Rings): they all use `PULS ...,PC` as the return of a function that saved A and B.

## Cause (code, measured)

Ghidra's 6809 language (`Ghidra/Processors/MC6800/data/languages/`, `6x09.sinc`) declares `A` (offset 0), `B` (offset 1) and `D` (offset 0, size 2) as overlapping registers, and its `6809.cspec` passes `A` and `B` as separate 1-byte parameters. The minimal failing function (4 instructions) is

```
PSHS A        ; A saved: the input A is read
LDD  #1       ; D written (2 bytes over A:B)
PULS A,PC     ; A restored, then the return address is popped
```

`PULS`/`PULU` with the PC bit are written `goto [t]` in `6x09_pull.sinc` (lines 21 and 44, Ghidra 11.2.1): an indirect branch, so every register is live at that point and the decompiler must keep the *incoming* A, B and D as inputs at the same time, at sizes 1 and 2: it stops with `Overlapping input varnodes`. The same function ending with `PULS A` + `RTS` decompiles. Observed on the 156 failures of MM 1.09c: 150 start with `PSHS`/`PUSHU` of A and B, 141 also use D. The fix was found on the 4-line case above, not by reading all 156 endings (inferred for the rest, confirmed by the 156 -> 0 result).

Second effect of the same line: the PC pull was a jump, so callers showed `UNRECOVERED_JUMPTABLE` + "Treating indirect jump as call" (777 functions of 1,234 on MM 1.09c) and the function never "returned".

## Fix (`tools/ghidra_6809/`)

1. `spec/6x09_pull.sinc`: `goto [t]` becomes `return [t]` for `PULS` and `PULU`. Alone (`install_fix.sh GHIDRA sleigh`): 156 -> 53 failures on MM 1.09c; the remaining ones are tail calls (`JMP` into another function after D was written) with A and B declared as parameters.
2. `spec/6809.cspec`: the two 1-byte parameters `A`, `B` are replaced by one `D` parameter (minsize 1, maxsize 2). A 1-byte argument is then `A` (the high byte of D), a 2-byte one is `A:B`. With both changes (`install_fix.sh GHIDRA full`, default): **0 failures of 1,404 functions** (the 14 more come from `return` creating the functions the old jump hid), jumptable warnings 777 -> 1, "Heritage" warnings 130 -> 7.

Costs of the `full` mode: a function that takes B alone as an argument shows it as part of `param_1` (`(char)param_1` or `param_1 >> 8`); output differs from the old export on most functions (282 of 1,234 identical, 440 with the pull fix alone), so a published decompile must be regenerated, not patched. A game that wants to keep the A / B split can use `sleigh` mode and read the remaining functions from the disassembly fallback.

No SLEIGH change to the register layout was needed (the overlap itself is fine for Ghidra, as for x86 AX/AL/AH).

## Applying it

```
sh tools/ghidra_6809/install_fix.sh <ghidra dir> [full|sleigh|revert]   # copies the files, rebuilds 6809.sla with support/sleigh
```
Run it once per Ghidra install, before `run_ghidra.sh`. The files are the Ghidra 11.2.1 ones (the originals are kept beside them as `*.ghidra_11.2.1`); on another version diff first. `revert` restores the saved originals (`*.before_fix`, written on the first run).

## Bench without the ROM

`tools/ghidra_6809/bench/`: `extract_failed.py` reads an export that has the disassembly fallback after each `decompile failed` line (`tools/MMExport.java` of the 6809 games) and writes batch files; `run_bench.sh GHIDRA batch.txt` re-assembles each function at its address with Ghidra's own assembler and decompiles it, so a Ghidra spec change can be measured without the ROM (it was how the cause was found: 4-line cases in `minimal_cases.txt`). Limits: calls to other functions are only as good as the batch holds them, and inline-argument gaps are zero bytes. The final measure is always the real pipeline on the ROM.

Fact tags: cause and counts are **code** (Ghidra 11.2.1, MM 1.09c, 27/11/2026); the generalisation to LOTR and T2 is **inferred** (same SLEIGH, same `PULS ...PC` idiom) until their ROMs are run.
