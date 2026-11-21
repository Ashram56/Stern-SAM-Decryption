# Stern ROM sets that are not SAM (first look: Lord of the Rings, 2003)

The agents in this repository assume a **SAM** board (ARM7 / AT91, one large encrypted image). Not every Stern
ROM set is one. A set of eight small files means a pre-SAM board, and the SAM method (agents/rom_extraction.md
sections 2 to 8) does not apply as it stands. First look at Lord of the Rings (set files `lotr*`), observed
2026-11-20 from the files alone, no emulator run. Labels: **code** = read from the bytes, **inferred** = guess.

| File | Size | What it is |
|---|---|---|
| `lotrcpua.a00` | 128 KB | Game CPU program. Starts with `BANK 56COPYRIGHT (C) 2001-2003, STERN PINBALL`; a second bank header `BANK 61BUILD 1252` sits at 0x14000. Code at 0x18000 disassembles as sane **6809** (Capstone `CS_ARCH_M680X`, `CS_MODE_M680X_6809`: `lda #1; sta $02a2; jsr $54f6 ...`). **code** |
| `lotrdspa.a00` | 512 KB | Display (DMD) program and data. Header at 0x78002 `LORD OF THE RINGS DISPLAY ... (C) 2003`; `DISP VER: A10.00` at 0x15761; service-menu and diagnostic texts, credits, fonts. Its ROM-test table names the other files (0x7869: `MUSIC ROM (U7)`, `VOICE ROM 1 (U17)`, `2 (U21)`, `3 (U36)`, `4 (U37)`). **code** |
| `lotr-u7.101` | 64 KB | Music ROM (U7), per the display ROM's own table. **code** |
| `lotr-u17/u21/u36/u37.100` | 1 MB each | Voice ROMs 1 to 4, high entropy (7.0 to 7.7 bits/byte): compressed or encoded audio, format not yet identified. **inferred** |
| `bios.u8` | 2 MB | 98 % `0xFF`; only about 43 KB of code, starting with ARM instructions (`ldr pc,[pc,#..]` vectors). Role not identified (sound or display coprocessor boot code?). **inferred** |

Not encrypted at first sight (strings, tables and valid 6809 code are readable straight from the files), unlike
SAM images. The 6809 program is banked (16 KB windows, bank numbers in the headers); the memory map and vectors
are not yet recovered.

Consequence for the method: the SAM-specific tools (`tools/rom/ghidra`, the ARM hook patches, `deff_sym.py`,
the OS API in `knowledge/sam_os_api.json`) do not carry over. What does: the ground rules of rom_extraction.md
section 0 (label facts, check against sizes stored in the ROM, never trust names from another game), the
deliverable list (section 14) and the packaging side. A new decompile pipeline for 6809 is needed (Ghidra has a
6809 language; PinMAME can run Stern's pre-SAM boards as a reference emulator).

## Reference traces on a pre-SAM board without a table (learned on LOTR, 2026-11-21)

Method that works on the Whitestar 6809 board, from libpinmame alone (no VPX): a small C++ driver linked to
libpinmame plus a patched PinMAME core (RAM-write, solenoid-write and DMD-packet hooks). Generic points:

- **Keep a ball in play with a ball simulation in the driver**, reacting to the solenoid callback: load the trough
  switches after boot, move a ball to the shooter lane when the trough kicker fires, plunge after the auto-launch coil
  (or after 2 s), open a VUK / saucer / lock switch when its coil fires, and add a `drain` command that puts the ball
  back in the trough. **Ignore coils during the power-up coil test** (every coil fires once at boot; reacting empties the
  trough and the game starts a ball search). With it each mode can be driven and traced like on SAM.
- **libpinmame `PinmameSetSwitch` numbering** on this board is `(column-1)*8 + row - 1` (the 0-based index of the
  switch name list in the display ROM), not the keyboard matrix number; check it with coils that answer a switch
  (pop bumpers, slingshots, VUKs). Start and coin switches belong to PinMAME's keyboard handler and must be pressed as keys.
- **Ball search spoils long waits**: with no playfield switch for about 8 s the game runs a ball search (every coil in
  turn, a countdown screen) that holds mode timers. Wait with a harmless switch every few seconds instead.
- **Award displays delay the score**: the score RAM changes when the award screen ends (about 5 s after the hit), so
  attribute score changes per scenario step, not per instant.
- **Name every display object from renders**: inject one display packet per object id with fixed test parameters,
  capture the frames and read the text and picture of each; the resulting `id -> content` column turns the traces
  (which give only ids and parameter bytes) into readable mode specs, and lists every feature of the game up front.
- **Settings and audits**: the 6809 game ROM holds descriptor tables (adjustments: 5-byte entries format, NVRAM
  address, min, max in BCD; audits: 3-byte entries format, address) in the same order as the name lists of the
  display ROM; a fresh-NVRAM boot gives the factory defaults, and the country presets are install records
  (descriptor pointer + data, 0xFF terminated).
