# Decoding a SAM ROM with less capable agents: the tricks, one method each, the global method, escalation

Written from the Tron DMD-from-code work (2026-11). Game-agnostic: addresses below are SAM OS conventions seen on one game, to be re-found
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

## 2. Global method (decode, then code in MPF, then improve)

1. **Inventory first** (`boards_inventory.md`): every board with its own CPU/ROM, decompile state. A board that is not complete blocks the rules that depend on it.
2. **Tables from the image**: OS routine names, effect table, coil/lamp/switch descriptors, page tables: read the ROM bytes, never a screenshot.
3. **Functional diagram from the code**, one ROM address per node, before any MPF code (agent C waits for it).
4. **Per mode, decode the whole block** (start, values, end, effects, sounds, lamps) with addresses; open points need a code-based reason or are sent back to work.
5. **Display from code** with the recipes of section 1; the capture is only the control column of the conformance table.
6. **MPF rules per node**, tests citing the address; run the bench; log every departure in `rom_differences.md`.
7. **Improvements** (HD, colour, new modes, service menus) are switchable and listed apart; the base game with them off must equal the ROM's. After any improvement, rerun the conformance table with the improvements off.
8. **Guard rails**: `check_strict_rule.py` before every push; progress report every 15 minutes; never end a turn announcing a next step while doable work remains.

## 3. Escalation rule

An agent that cannot finish a task (a recipe stuck below 100 % with no code-based reason, a routine it cannot read, a rule it cannot place in the diagram, two failed attempts at the same step) **stops and defers the task to a more capable agent** instead of guessing, approximating from a capture, or marking it done. The hand-over note holds: the effect or rule, the ROM addresses read, what was tried (arguments, state, draws), the measured result, and the exact question. The more capable agent either finishes it or writes the code-based reason; the original agent continues with the rest meanwhile. A capture is never the way out: only the owner can grant a waiver, recorded in `docs/pinmame_waivers.md`.
