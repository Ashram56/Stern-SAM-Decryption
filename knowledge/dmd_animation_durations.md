# DMD animation durations: how to measure and present them

Owner decision (Vincent, 2026-11-26): the duration of **every** display animation is an explicit, normalised datum, chosen by **precision**,
derived from the code only (STRICT RULE: no duration read from a PinMAME run or a video).

## 1. Why games used different techniques, and which one is kept

Terminator 2 (WPC) renders each effect by running the ROM on a full machine core over a time window and reads the duration from the
last frame change. Medieval Madness replays effects with a small 6809 interpreter and lists images, texts and waits in ticks. LOTR runs
the DMD board ROM on a 6809 core. There was no design reason: three threads, three starting points (T2 needed rendered frames; MM had no
display yet; LOTR's board has its own firmware). Compared on precision:

| Method | Exact to the tick? | Branches | Depends on game state | Weak point |
|---|---|---|---|---|
| A. Sum of `task_sleep` ticks along one path (static) | Yes on that path | Only the path chosen by hand | Not seen | Wrong when waits are computed, looped or conditional |
| B. Window run on a full core, last frame change | No: window-limited, cut by loops, includes the game's own screen activity (T2 pitfall: frame counts change with run order) | Real ones | Yes, silently | Measures the screen, not the effect |
| C. Interpreter replay with stubbed OS | Tick-exact only if wait arguments are right | Real ones, stub state | Hidden in the stubs | Timing not measured, only summed |
| **D. Kept: run the effect's own code on the core, hooked at the OS wait call** | **Yes: every `task_sleep` call logged with its argument, tick = cited IRQ divider** | **Real ones, followed and logged** | **Explicit: run under several states, compare** | needs a faithful core |

**Standard method (D, with A as the cross-check).** Start the effect from its entry address on the real core, intercept the wait routine
(address cited) and log `(pc, ticks)` until the effect returns, loops, or a held state is reached; the duration is the sum of logged waits,
not the time of the last pixel. Re-run under at least 3 different states (other effect running, other RAM flags: the `states_tested`
column); if the sums agree the animation is `state_stable=yes`; if not, report `min`/`max` and name the RAM variable that decides
(address). A static path sum (A) must equal a logged run on the same path; a difference is a defect of one of the two, not a rounding.
Frame times of rendered GIFs follow from the same ticks, never the reverse.

## 2. The tick

One row per game (`rom_data/dmd_tick.csv`: game, tick_source, irq_hz, irq_per_tick, tick_ms, address of the divider, address of the wait routine).
Convert `ms = ticks * tick_ms`; keep `tick_ms` to 3 decimals. Example (T2, WPC): 16 IRQ per tick, tick = 16.4 ms (cite the divider and
the wait routine). A board with its own firmware (LOTR DMD) cites the timer setup of that firmware, not the main CPU's.

## 3. The file: `rom_data/dmd_durations.csv` (one row per animation, every animation of the game)

| Column | Meaning |
|---|---|
| `game`, `animation_id`, `kind` | `deff` / `object` / `sequence` / `screen` |
| `entry_addr` | ROM address (`bank:addr`) where the animation starts |
| `class` | `finite` / `loop` (repeats until stopped) / `held` (last frame held until replaced) / `state_dependent` / `empty` (no animation) |
| `ticks`, `ms` | finite: total; `ms = ticks * tick_ms`. loop: duration of **one cycle**. held: ticks before the held frame. state_dependent: leave empty and fill `min_ticks`, `max_ticks` |
| `min_ticks`, `max_ticks` | range when `class=state_dependent`, else equal to `ticks` |
| `end_addr` | finite: the call site of the last wait (the code after it returns without waiting), cited |
| `loop_addr` | back-edge target (loop) or the address that holds the last frame (held) |
| `decider_addr` | RAM or code address that decides a state-dependent duration |
| `method` | `exec_hooked` (D), `static_path` (A) or `both` (D checked against A) |
| `elapsed_ticks` (optional) | elapsed time measured on a core with a real interrupt model; must equal `ticks` within the code time between waits (empty on a stubbed scheduler) |
| `notes` (optional) | child tasks, forced random values, loop arguments |
| `states_tested`, `state_stable` | number of states run; `yes` / `no` |
| `wait_sites` | space-separated `addr:ticks` list of the waits summed (proof of the number) |

Rules: every row cites addresses; `class=finite` needs `ticks`, `ms`, `end_addr`; `loop`/`held` need `loop_addr`; `state_dependent` needs
`min_ticks`, `max_ticks`, `decider_addr`; `empty` has `ticks=0`. A `capture`, `pinmame` or `render` value in `method` is a failure.
No duration without `wait_sites`, except `empty`. The human view of a row is the effect's page in `docs/boards/dmd/`, which links the row.

## 5. Per platform: what to hook, where the tick comes from

The method (D) is the same everywhere; only the wait routine and the tick source change. `wait_sites` always cite the call site.

| | WPC / Whitestar 6809 (T2, MM) | Stern SAM (ARM7, DMD driven by the main CPU) |
|---|---|---|
| Wait routine to intercept | `task_sleep`, inline 1-byte argument (T2 `fix:8346`; hook its `jmp task_save_and_switch` at `fix:835b`: B = ticks; call site = word at the stack top - 4) | `task_sleep(ticks)` (r0 = ticks; Tron `0xb91c`, call site = LR - 4). Also `deff_frame_sleep(ticks)` = `dmd_flip` + `task_sleep` (Tron `0x2791c`), and the library loops that sleep inside: `anim_play` / `anim_play_pal` (Tron `0x1023edc`, `ticks_per_frame x frames x loops`): the sleeps are logged where they happen, inside the library, with the library call site as `wait_sites` and the loop arguments in `notes`. Addresses differ per game and OS build: find them again through `sam_os_api.json` and rom_extraction.md section 5.1. |
| Current task | RAM `$53` (T2), hook reads it to tell the effect's task from the game's | the OS current-task global (rom_extraction.md section 3.3: tasks are answered in Python by the stub scheduler) |
| Tick source | IRQ vector (T2 `fix:d9c0`): `incb / andb #15` = 16 IRQ per tick, `inc $50` at `fix:d9ce`; IRQ 976 Hz from the 2 MHz ASIC timer; tick = 16.384 ms | 64 IO ticks of 250 us (TC0 RC=5000 at MCK/2, set at Tron `0x13484`), counter advanced every 64 (Tron `0x37364`), consumed by the main loop (Tron `0x3405c`): **tick = 16.000 ms in the code**. |
| How the core runs | full machine core (T2 `wpcemu`): real IRQ, so `elapsed_ticks` can cross-check the sum | whole ROM in Unicorn with the scheduler stubbed (Transformers `deff_lift.py`, rom_extraction.md section 3.3): no interrupt model, so the duration is the **sum of logged waits only**; `elapsed_ticks` stays empty. |
| Random branches | rare | `random_below`, `random_percent`, `bag_weighted_pick` are OS calls: force every value in turn and report the `min_ticks` / `max_ticks` range (the forced variable is the `decider_addr`) |
| Caller state | RAM flags | task arguments stored by the caller after `deff_start` (task + 0x30...), game RAM read by the effect: run with several argument sets; unresolved ones are `state_dependent` |

**SAM-specific rules.**
1. `tick_ms = 16.000` from the code. Never write the 16.15-16.26 ms a PinMAME trace shows (a pass can overrun; Transformers measured 16.15, Tron 16.26): that is an emulator capture, forbidden as a source. A trace is only ever compared to it, in ticks.
2. A picture is shown for its `task_sleep` ticks **plus** the rest of the main-loop pass that flips it: the flip happens once per pass, so the effective on-screen time of a frame is quantised to whole ticks. The CSV holds the code's ticks; the playback layer (agent C) applies the quantisation.
3. Effects that write the DMD page directly, take pointer arguments (high-score entry) or depend on task arguments set by the caller are `state_dependent` until the caller's arguments are enumerated from the callers' call sites (static scan of `deff_start` callers); say so in `notes`, never guess a value.
4. DMD driven by the main CPU (SAM, MM): the effect's task is the main CPU's task; there is no firmware tick to find. A game whose display board has its own firmware (LOTR Whitestar) cites that firmware's timer setup (section 2) and hooks the board's wait routine.

**Blocker to report.** The SAM instance needs the game's ROM and a Unicorn lift (Transformers has one; Tron's deffs are not lifted yet), so applying the standard to a SAM game costs one lift run per game; nothing in the standard itself blocks it.

## 6. Check

`tools/check_strict_rule.py` validates `rom_data/dmd_durations.csv` when it exists (columns, class rules, `ms = ticks * tick_ms` within
0.5 ms, addresses cited, no capture method); a game that has a DMD effect table (`rom_data/dmd_*effects*.csv`, `dmd_deff*.csv`,
`dmd_animations.csv`) but no durations file gets a WARN `dmd:`, and `--layout-strict` makes it a failure.

Last updated 2026-11-26.
