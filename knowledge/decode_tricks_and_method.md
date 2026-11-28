# Decoding a SAM ROM with less capable agents: the tricks, one method each, the global method, escalation

Written from the Tron DMD-from-code work (2026-11); section 4 and the additions marked Transformers from Transformers Pro 1.80 (2026-11-26). Game-agnostic: addresses below are SAM OS conventions seen on one game, to be re-found
on another ROM (rom_extraction.md says how). Everything here serves the STRICT RULE: every value comes from the ROM code, an emulator
capture is only a control.

## 1. The tricks that needed thought, and the method for each

| # | Trick | Why it is hard | Method (do this, in order) |
|---|---|---|---|
| 1 | **Run one ROM routine in Unicorn instead of a whole emulator** | The OS (tasks, sound, coils) is not needed to draw a screen | Map the ROM image at its load addresses (file offset = VMA minus the data base for table data), stub OS calls by address with one `UC_HOOK_CODE` hook per address (a hook over the whole OS range is ~10x slower), log their registers, make `task_sleep` advance a fake tick counter and return. |
| 2 | **One frame per page flip, time from the OS tick** | The ROM never says "frame"; it flips two DMD pages | Stub the page-flip routine, snapshot both pages at each call, record the fake tick at that moment; the tick length is the IO ISR period times its interrupts per tick (read from the timer setup, not measured). Mix pages with the display rule read from the mixer code. |
| 3 | **Effect arguments** | They are words in the task block, not function arguments | Find where the effect reads the current task block (+0x30...), list every use in the decompile, give each a value from the code that reads it (menu, game state, mode id). A forced reference run with all zero arguments can read null buffers: compare, do not assume. |
| 4 | **Simulated game state** | Effects read RAM the game would have set (credits, scores, adjustments, counters) | Run the ROM's own factory-reset routine first, then set only the RAM words the effect reads; write each word and the code address that reads it in the recipe. |
| 5 | **Random draws** | `random_below(n)` makes several clips/variants | Hook the RNG entry, force the pick (an int or a function of n), sweep k in range(n) and keep every variant; the draw sites come from the table of random calls, one site per effect. |
| 6 | **Previous screen for dissolves/transitions** | A transition reads the pages shown before it | Run the real page-show routine (it keeps bookkeeping RAM the transition reads), run the previous effect to a chosen frame, copy its two pages to free pages and point the bookkeeping words at them. |
| 7 | **Flash bank / image heap** | Images live in a banked window and a heap built at boot | Emulate the bank-select write (copy the chosen 8 MB chunk into the window, set the read-back register), run the boot initialisers (image heap, factory reset) before the effect. |
| 8 | **Child tasks** | A parent spawns one task per page and only waits | Read the page table straight from the ROM image (pairs of predicate and routine, null-terminated); run each routine on its own (`fn_addr`) and snapshot at the sleep as well as at the flip when the page draws then sleeps. |
| 9 | **Instruction limits and runaway loops** | A redraw loop that never sleeps gives 10^5 frames | Cap instructions per recipe, cap kept flips per tick, merge identical neighbours; a frame count far above the effect's length is a bug in the run, not in the effect. |
| 10 | **Proving a gap comes from the capture, not the code** | An effect stays under 100 % against the capture | Write the reason with its code address: forced zero-argument record, reads emulator memory at a null buffer, gated by a mode the factory state never enters, dead code (the routine returns at its first instruction). No reason with an address = not done: tune arguments, draws, state. |
| 11 | **Speed** | Hundreds of effects x thousands of frames | Process pool with `imap_unordered` (one slow effect must not hold the others), per-effect instruction budget, write results as they arrive; regenerate only the changed effects. |
| 12 | **Size of the result** | Frame dumps reach hundreds of MB | Merge identical neighbouring frames, cap per tick, store 16-level greys; check the total before committing (the Tron set: 144 effects and all variants, 35 MB). |
| 13 | **The test bench** | A rules change can break a mode elsewhere | Run the game's player-robot bench before and after each rules change; it is the regression net the traces cannot be. |

## 2. Global method (decode; the MPF coding and improvements part is in MPF-Godot-Packaging)

1. **Inventory first** (`boards_inventory.md`): every board with its own CPU/ROM, decompile state. A board that is not complete blocks the rules that depend on it.
2. **Tables from the image**: OS routine names, effect table, coil/lamp/switch descriptors, page tables: read the ROM bytes, never a screenshot.
3. **Functional diagram from the code**, one ROM address per node, before any MPF code (agent C waits for it).
4. **Per mode, decode the whole block** (start, values, end, effects, sounds, lamps) with addresses; open points need a code-based reason or are sent back to work.
5. **Display from code** with the recipes of section 1; the capture is only the control column of the conformance table.
6. **MPF rules and improvements** are the MPF half's: `knowledge/recreation_method_for_weaker_agents.md` in Ashram56/MPF-Godot-Packaging (rules per node, bench, switchable improvements). Log every departure in `rom_differences.md`.
7. **Display conformance**: rerun it against the code frames with improvements off after any change.
8. **Guard rails**: `check_strict_rule.py` before every push; progress report every 15 minutes; never end a turn announcing a next step while doable work remains.
9. **Pilot, then scale.** A new runner or lift runs first on one item that has independent evidence (an old capture, a trace
   span the code counts in ticks); scale only when the pilot matches exactly (Transformers: deffs 53, 54 and 65 pixel for pixel,
   then 152 of 155 deffs ran to their end). Before writing the runner, list the addresses it needs and where each was found:
   `task_current`, the task list head, `task_sleep`, `task_create` / exit, the bank register, the constructor table, the
   dedicated switch table, the rule-record request flag (rom_extraction.md 3.3 has the Transformers values and the traps).
10. **Every step ends on a number** in the progress report: strict-check failures (never up; Transformers 268, 41, 2, 0), lifts that
   end / total, matches against independent evidence / total, items a parser read / expected, `FUN_` left, trace checks (never down).
   "It looks right" is not a result.
11. **Run, do not infer.** A value that goes through more than one routine (a delay through a chain of tasks, a text through a
   formatter, a priority through the display queue) is taken from a run of the code, not reasoned from the one routine you read.
   Transformers: an end-of-ball delay during a ball search, inferred from the search task alone, came 1 s early against its trace.
12. **Two agents at once** (decoder and recreation on stacked branches): the recreation side sends one batched request per need
   (ids, tables, offsets, the trace and time that show the gap, and what it does itself); each shared file has one owner, the other
   merges the owner's branch (never rebases it) before editing and keeps the owner's wording; disputes are settled by the code (see
   trick 17).

## 3. Escalation rule

An agent that cannot finish a task (a recipe stuck below 100 % with no code-based reason, a routine it cannot read, a rule it cannot place in the diagram, two failed attempts at the same step) **stops and defers the task to a more capable agent** instead of guessing, approximating from a capture, or marking it done. The hand-over note holds: the effect or rule, the ROM addresses read, what was tried (arguments, state, draws), the measured result, and the exact question. The more capable agent either finishes it or writes the code-based reason; the original agent continues with the rest meanwhile. A capture is never the way out: only the owner can grant a waiver, recorded in `docs/pinmame_waivers.md`.

Additions from Transformers (2026-11-26):
- **More triggers.** Also stop and defer when a code result and a trace disagree and you cannot explain it from the code in about
  30 minutes; when the task needs a new tool design rather than running or extending one (a new runner, scheduler, sound FIQ or bank
  model, an attribution rule); when going on would mean guessing a value, an address or a name; and when you are about to weaken a
  check, skip a test or mark something "observed" to get past it.
- **The hand-over is a file**, `docs/handoff/<date>_<topic>.md` in the game repository, with the commands run and their output, so the
  next agent starts from the evidence, not from a chat summary. Report it as a blocker in the progress report.
- **What a less capable agent can do alone:** run an existing lift on new ids, extract a table whose reader exists, rerun a recipe
  with new state or draws, fix a finding whose ROM address and expected value are given, update docs and strict-check declarations.
  **Defer by default:** writing or changing a code runner; anything in the OS scheduler, FIQ, bank switching or switch dispatcher;
  a code / trace disagreement. A choice that needs the owner (look, a departure, a waiver) goes to the owner, not to a stronger model.
- **Close the loop:** the more capable agent writes what it learned back here as a recipe, so the next less capable agent no longer
  needs to defer for that class of problem.

## 4. Tricks learned on Transformers Pro 1.80 that section 1 does not cover

Transformers (tf_180, 2026-11-24 to 11-26) decoded 153 deffs, 178 leffs, coil times, the service menu and 24 whole scenarios by running
the ROM's code. The runner itself, effects from game state, whole scenarios, the sound FIQ, flash banks, coil slots, motors, rule records,
priority drops and the service walk are in [rom_extraction.md](../agents/rom_extraction.md) section 3.3; the tricks below are not.
Game values are the worked example (addresses in tf_180's game code, which starts at 0x01000000; the OS below it).

| # | Trick | Why it is hard | Method (do this, in order) |
|---|---|---|---|
| 14 | **Attribute a caller's task writes to the right effect** | Callers store an effect's arguments into the task `deff_start` returns; when two effects start in one function and the code reuses one variable, a write is easily given to the wrong one | A write belongs to the last `deff_start` before it in the same function, and only until the next one. `task_create` clears the task block (TF: `memset` 0x68 in `task_create` 0x0000aa04), so an offset no caller writes is 0. Package a variant only if the effect's own body loads that offset. TF: the index stored at +0x38 after `deff_start(0x42)` is deff 66's; deff 65 always plays entry 0, and five false variants (and false arguments for five other deffs) went away. |
| 15 | **Table-driven animations** | The effect picks an animation function from a table by an index; one run exports one animation, and the sounds of the others look "missing" | Find each table and how its index is chosen (task argument, capped counter, random pick with a no-repeat mask, popcount; TF deff 102: 12 minus shots left, capped at 11, the last shot entry 1 via +0x3c). Run every entry as its own variant. The frame players take a sound table: record each entry at its frame, and the chain entry (TF 0x1f, `snd_play_after_if` 0x00025364: play after the running sample ends) as its own op. One row per effect: table, index source with its address, variants, length, sounds. Close it: every sound id those players use is in an op list or proven dead (rom_extraction.md ground rule 5). |
| 16 | **Values printed live** | A run bakes one value into the frames (a bonus page, a count) | Keep each formatted-print op as a slot keyed by its call site: format, font, position, and the source of each argument (RAM or task offset, cited); run once per page layout (TF deff 25: 24 runs, one per multiplier). The recreation fills the slots from its state. Baked values in packaged frames: none. |
| 17 | **An effect's length in a trace** | The trace shows the next `deff_start` long before the effect ends | Sum the code's sleeps on the path (TF deff 92: 74 frames x 3 + 40 x 3 + 1 = 343 ticks). In the trace, use the tick the DMD task's function changes, not the next `deff_start`: a background rule may request the next effect while a higher-priority one still holds the display. Convert with the trace's own tick measured on code-counted spans (rom_extraction.md section 4). |
| 18 | **Order of a rule list** | Rule records are registered at power-up; their order decides which effect wins, and nothing in the image lists it | Read the insert routine (TF 0x00017580: before the first record whose priority is not above its own; all leff rules have priority 0, so each goes to the head) and the constructor walker (TF 0x0002c0c8: last entry first). The list then runs the modules in ascending address order, last registration first within a module. Write it as a table; never invent an order key. |
| 19 | **Name every function** | Thousands of `FUN_`; a name carried from another game by address or signature is often wrong (ground rule 20) | Fixed rule order, each name with its evidence in a CSV: (1) from the tables: switch handler, task entry (`task_create` argument), event hook, effect / sound / adjustment / audit / message when it is the one clear purpose; (2) wrapper, getter, setter; (3) purpose: calls with constant arguments resolved through the ROM's tables; (4) by hand, one row each. Suffix the low address bits for uniqueness; an OS and a game function sharing low bits get separate names. TF: 2,555 named, zero `FUN_` left. |
| 20 | **Lamp effect arbitration** | Which lamp effect wins is not a priority alone | Read `leff_start`'s conflict test (TF 0x00007c10): a running leff that shares a lamp of the new one's lamp group, or a coil of its coil group, refuses it when higher (or equal without flag bit 2), else it is killed, and a killed rule leff restarts when it can. From its start a leff owns its group's lamps (cleared in the override planes). Export the lamp and coil group tables (TF 0x040d1510, 0x040cf65c) for the recreation. |
| 21 | **Sound arbitration** | "Missing" sounds in traces are refused starts | Read the call record (TF 0x14 bytes at 0x040dee08): no-repeat ring (+0x0e), priority (+0x10), take-over flag (+0x11); and each sample's stream script: byte 1 the voice mask, byte 2 the voices taken. The start routine (TF `snd_start_sample` 0x00024ae4) takes free voices first, then the longest-playing slot of lower priority; else the sample does not start. Export both as tables. |
| 22 | **What is not in the code** | Some game timings include the ball's travel or the recreation engine's device timing | Decode the code part (serve, feed and search tasks, the device table's settle times: TF 0x040d17fc, trough 31 ticks) and label the rest as physics, measured, never "decoded". Write each constant as code part + physics part. |
| 23 | **Empty actions** | A menu or rule entry whose label promises a screen | Its routine is `bx lr`: in this ROM it does nothing; the recreation does nothing too (TF DISPLAY HELP SCREEN 0x01045a74). |
| 24 | **A scenario replay in Unicorn stalls after the first ball** | The harness runs the scheduler tick only, not the 1 ms coil IRQ, so a coil pulse queued in *sync* mode (a ball-device kick: the routine that queues it then `task_sleep(1)` while the pulse-pending test says the handle is still queued or firing) never ends; the ball-serve task (a device task id 0x18+device) never exits, `no_balldev_tasks()` stays false and the end-of-ball check (trough drain check) returns at its first test, so no ball 2 | Do not guess the missing condition: hook each condition of the check one at a time (entry, return value) and list the live task ids with their entry address (task list head RAM, id at +0, next at +0x1c, entry in the word after the id); a device task that never ends points at what it waits on. Stub the pulse-pending test (Tron: FUN_000028f4 at 0x28f4, args coil, handle, 1) to answer "pending" for the pulse's duration in ticks (4 ticks covers 64 ms), then "done". Switch-model fixes (opening the kicker switch, jam switch on drain) are needed too but are not enough alone. Check the result: event 0x13 of the next ball comes about 0.5 s before its kick, as ball 1's does (Tron, 2 players: 4.098 s and 36.357 s, kicks 4.650 s and 36.878 s). Also check that the harness plays the script's `start N` as N players (coins and one START each): a harness that ignores N replays a solo game and every multi-player conclusion is wrong; read the current-player RAM byte at each ball start to prove it. Event hooks on the event-post routine miss a list the ball-start routine walks inline, so a ball can start without a visible event |
