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

## Display objects and lamps for the recreation agent (learned on LOTR, 2026-11-23)
- **Display objects with their real parameters.** A capture of every object with default parameters is not enough:
  the game agent redraws "ARAGORN 200,000" for every member and "INSERT COINS" whatever the credits. Before handing
  over, render by DMD injection (a PinMAME hook that replaces the game's DMD writes by packets from a file):
  one render per value of each discrete parameter (member, mode, rank, message), two renders per object that differ
  only by a BCD value (1,234,567 / 9,876,543) to locate the number, renders where every parameter byte is a distinct
  BCD pair for objects whose value is elsewhere, and the credit screens after the credit packets (0, 1/2, 1, 2, 9
  credits, free play). Deliver 1x frames with their durations and a CSV per case. LOTR tool:
  `tools/dmd_param_renders.py` in the game's extraction repo.
- **Lamps are two layers on Whitestar.** Layer 1 is the game state (on, flash, off bit arrays, saved per player with
  the flags); layer 2 belongs to lamp effects (a table of lamp list + code task per effect id, start/stop by id,
  priority by id), which own their lamps while they run. Decode layer 1 from the redraw routines that a "refresh the
  playfield" routine calls one after the other (find it by the run of calls into the lamp bank), and list each
  effect's lamps and starters; record attract and one game with lamp events (as a mask per change) so the game can
  replay the shows whose internal timing is not decoded. Hand this over with the rules: the game agent otherwise
  lights only the mode inserts.
- **Record lamps per full matrix scan, not per sample.** Whitestar games drive the rows of a lamp column in turns, so
  one sample of the matrix (or libpinmame's changed-lamp polling) shows about half of the lamps that are on (LOTR:
  alternating 0x5 / 0xA nibbles) and a replay flickers at random. Hook the lamp driver writes in PinMAME's `se.c`
  (row and strobe handlers), OR the rows per column over 2 scans (a scan is about 10 ms; the strobe returning to
  column 0 marks it) and write one full state per change. LOTR's recorder: `LOTR_LAMPSCAN` in its
  `tools/pinmame/lotr_trace.patch` (private repo).
- **Know what each input port bit is before reading a wait as "the display finished".** On Whitestar the game CPU's
  0x3700 is a 74HC245 of mixed lines (PinMAME `se.c` `dmdstatus_r`, the board wiring, not a capture): bit 7 the DMD
  board's busy, bits 3-6 the four DMD status bits (what the DMD ROM writes to its own 0x4000), bit 1 the **sound
  board's** SST0, bit 0 the sound busy. A game loop that waits for bit 1 to change (LOTR's bonus screens, 61:727D,
  2 + up to 64 ticks) is waiting for the sound board, not the display: its exact length needs the sound board's ROM;
  rebuild the bound from the code and say the early exit is open.
- **An effect's table object can be overwritten by its script.** The effect start writes the table's object to the
  packet buffer (LOTR 0x05D8) and the script may write another one before the first send: list what the script sends,
  not the table's object (LOTR effect 0x0F: table 0xE2, sent 9B E3 / 9B E5).
- **Timers of entry screens may not count in task ticks.** LOTR's initials entry counts 0x0266 units of 10.25 ms
  (the IRQ's own counter), not the 16.4 ms task tick: read the counter the loop decrements before converting.
- **Audits are inline calls.** `jsr 0x9EF6; fdb counter` (+1, 4 BCD bytes, saturating) on Whitestar LOTR: scan the
  ROM for the call bytes to list every counter and its site (168 on LOTR), and decode the percentage routine
  (57:5F92 / 6127) when a rule reads a percentage (match, mystery extra ball / special weights).
- **Run the display board's own ROM for the display; a port is only as fast as its timing model.** The Whitestar /
  Data East 128x32 DMD board (MAME `src/mame/pinball/decodmd2.cpp`, hardware, not a capture): 6809E at 8 MHz / 4 =
  2 MHz; FIRQ periodic at **80 Hz** (HOLD_LINE: keep it pending until the CPU takes it); reading the latch 0x3003 clears
  the IRQ and BUSY; 0x3002 bits 0-4 the 16 KB ROM bank at 0x4000-0x7FFF; 0x8000-0xFFFF the ROM's last 32 KB; writes
  to 0x4000-0x7FFF the status port. The two planes are 0x200 apart and the **first plane is the high bit** of the
  2-bit intensity (linear: MAME `crtc_update_row`). The board is render-bound: on LOTR a full-screen render takes about
  51,000 cycles (2 FIRQ ticks), so its display loop runs once per 3 ticks and a 9-tick script sleep shows as 12 ticks
  (150 ms). A Python port that runs a pass per tick (and LOTR's port assumed 125 Hz) shows the same images twice as
  fast. The boot sums the whole ROM first (about 700 ticks). A pure-Python 6809 core (`pip install MC6809`) runs the
  board at about 2x real time: LOTR's `game/lotr/dmd/cpu_board.py` (private repo) feeds it the game CPU's packets
  (length byte, then the bytes, one packet at a time once `$36` is clear) and sends the page on show to the display.
  **MC6809 0.9.0 has a SEX bug**: a negative B leaves A unchanged (D = 0x??E8, not 0xFFE8); override `instruction_SEX`
  with `@opcode(0x1D)` in a CPU subclass. On LOTR it put every text with a negative dx 256 dots to the right. Check a
  core against a port object by object (frame sets) before trusting either, and run the whole board in a live game:
  the game side must send what the main ROM sends (LOTR: 0x9C every 100 ticks from the main play background effect
  0x1B, 61:702C), or the real board keeps its last object on screen where a lenient port does not.
