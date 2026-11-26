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
| `end_addr` | where the effect ends or returns (finite), cited |
| `loop_addr` | back-edge target (loop) or the address that holds the last frame (held) |
| `decider_addr` | RAM or code address that decides a state-dependent duration |
| `method` | `exec_hooked` (D), `static_path` (A) or `both` (D checked against A) |
| `states_tested`, `state_stable` | number of states run; `yes` / `no` |
| `wait_sites` | space-separated `addr:ticks` list of the waits summed (proof of the number) |

Rules: every row cites addresses; `class=finite` needs `ticks`, `ms`, `end_addr`; `loop`/`held` need `loop_addr`; `state_dependent` needs
`min_ticks`, `max_ticks`, `decider_addr`; `empty` has `ticks=0`. A `capture`, `pinmame` or `render` value in `method` is a failure.
No duration without `wait_sites`, except `empty`. The human view of a row is the effect's page in `docs/boards/dmd/`, which links the row.

## 4. Check

`tools/check_strict_rule.py` validates `rom_data/dmd_durations.csv` when it exists (columns, class rules, `ms = ticks * tick_ms` within
0.5 ms, addresses cited, no capture method); a game that has a DMD effect table (`rom_data/dmd_*effects*.csv`, `dmd_deff*.csv`,
`dmd_animations.csv`) but no durations file gets a WARN `dmd:`, and `--layout-strict` makes it a failure.

Last updated 2026-11-26.
