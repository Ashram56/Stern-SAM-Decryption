# DMD display-effect rules: what is the SAM engine, what is the game, and how to get them from the ROM

Study, 2026-11-01. Source: Tron-Legacy-MPF PR #69 (16 conformance measures, 55 commits, classic DMD vs PinMAME on the real
ROM, 66.9 % -> 94.4 % of PinMAME's Serum-known frames found) and `docs/dmd_conformance.md` there. Facts below are read from
those commit messages and that document, not from re-reading the code: label **inferred** where it is a conclusion.

## 1. Why this matters

In PR #69 almost every fix was found by comparing captures, then fitted by hand (blink "48 ms on / 48 ms off fitted on the
capture", "text at 4240 ms read off the capture"). Several later turned out to be constants of the ROM (3 ticks a picture,
`FUN_01024378(3)`; blink 3-tick frames; text starts when the picked clip function returns). A rule that is in the ROM code
should be read from the ROM, once, for every SAM game, and the capture should only validate it.

## 2. Sorting the rules

### A. Generic SAM engine behaviour (same code in every Stern SAM game; static analysis of the shared engine gives it once)

| Rule seen in PR #69 | Why generic |
|---|---|
| Time is in OS ticks, not ms: clip pictures `delay(3 ticks)`, blink frames of N ticks, "lit on frames 0-1 of 4, hidden on the others" | the delay/blink API of the display library; the tick length is a OS constant |
| A deff that is "the rule's deff" is started only when it is not already running (`FUN_000198a8`): so a music change does not restart deff 19, and when deff 96 ends, deff 95 simply reappears (Zuse), while another mode restarts its background | start semantics of the deff manager (start / restart / priority / preempt); the *calls* are game code, the *semantics* are engine |
| Draw order is call order: text then `bitmap_draw_masked` = clip over the text; bitmap then text = text over the clip; "open white area transparent" = the masked draw | display library primitives (draw text, draw bitmap, masked draw); the order is read off the deff's call sequence |
| Dimming / levels: picture at level 1 under the text, palette slots (0x30, 0x40), "level 1 shown as 0" | palette and level arguments of the draw primitives |
| Event posting: score_add posts event 0x4d, ball start posts 0x13; hooks (`FUN_010238ac` last points, `FUN_01023858` ticks since last points) | OS event numbers are the shared API (`knowledge/sam_os_api.json`); who hooks them is game code |
| Score roll: starts 62 ticks after the last points, then every 62 + 4H ticks; band blanked one row per 2 ticks; status-panel score 6 + 6 steps (`FUN_01023940`, `deff_draw_status_panel`) | status panel and score display are library routines; **inferred**: shared across games of the same OS generation, to check on a second game |
| Score font by magnitude from a size table (0x40d3484 area) | the table's *position* is game data; the lookup routine is engine |
| Random primitives: `random_below`, `random_percent`, `bag_weighted_pick` | OS API; forcing them (TRON_RNG_ZERO) is generic and already done in the harness |
| Rotation of the bottom line: deff counts its own ticks from the moment it gets the display | deff lifetime = engine; the 156/312/1250 split is that deff's constants (game) |

### B. Game-specific (needs the game's ROM, no shortcut)

- Which deff does what: the 144-ish deff table, their texts and fonts, screens per argument (`rom_layout.SCREENS`).
- The tables a deff indexes: film-clip tables (0x040d2804 Disc Multiball, 0x040d3084 Light Cycle by level, 0x040d6fd4 Zuse), award reels, bonus lines.
- Rule logic that picks a clip or argument: Light Cycle `lc_clip_level` and n-th jackpot, Sea of Simulation stage-completing shot (fixed clip), Disc access counter ("3 MORE"), end-of-ball bonus screen order, combo names.
- When the rules start or stop a given deff (which mode keeps a background, e.g. Zuse deff 95/96, Sea of Simulation restart by deff 114).
- Rule tasks that change what the display shows: the Recognizer moving target (task 0x7d, 93 ticks a step, disabled-switch mask) is a pure rules gap, not display.
- The numeric constants of one effect (4240 ms, 1410 ms, 1718-tick cycle), unless derived from A + the code.

### C. Pattern generic, instance specific (the best candidates for automation)

"Pick a clip from a table, play it, take the last bitmap it returns, dim it, then loop the text": deffs 48, 49, 87-89, 97, 142, 111 all follow it. The *pattern* is generic; the table address, text and values are per game. A pattern matcher on the decompiled deff finds every instance.

## 3. Can it come from the ROM? Yes, for most of A and C

Mostly yes. Tron already extracts part of it: `rom_layout.py` parses the decompiled C two call levels deep for text draws, `timing.json` takes the time of the last sound call, `text_draws.csv` places the text. What remained hand-fitted from captures (`OVERRIDES`, `blink_frames`, `DIM_AFTER_MS`, `TEXT_UNDER_CLIP`, `CLIP_END_TEXT`, `OPEN_WHITE`, `CLIP_OVER_PANEL`) is exactly the layer a deff-level lift would produce. Limits: values that come from RAM at run time (scores, counters) and rule-side start/stop conditions are not constants.

## 4. Proposal: extract the effect model automatically

1. **Lift each deff to a small op list** (static, Ghidra decompile + `sam_os_api.json` names): `clip(table, index|fn)`, `bitmap(id, x, y, masked|plain, palette)`, `text(fmt, font, x, y, palette, args)`, `delay(ticks)`, `loop(n)`/`blink(on, off)`, `dim(level)`, `sound(id)`, `end`. One JSON per deff. Resolve the tables (clip, score-size) through data cross references.
2. **Confirm with concrete execution, not only static reading.** Run each deff function in an emulator with the OS API stubbed to record calls and ticks (hook in PinMAME, which the PR's conformance build already patches; or Unicorn). Enumerate random branches by forcing `random_*` to every value (extension of TRON_RNG_ZERO), giving every clip variant and its exact end tick, no fitting. Output the same op list with real times.
3. **Pattern recogniser for family C** to name the clip-then-text effects, so the renderer gets `text_after_clip=true`, dim level and variant end times without a per-effect override.
4. **Rule-side graph** (harder, second phase): list the call sites of the deff manager (start/restart/stop with the rule's deff flag), keep the condition code location, and let traces decide the rest. Do not try to infer rule logic statically beyond this.
5. **Validate with the PR #69 harness** (PinMAME dump vs game, per deff window). It becomes a regression test; each game's figure is "share of deffs generated with no override".
6. **Measure the generality** on the Transformers ROM (already in the family) before declaring anything generic: score roll and deff-start semantics are the first two rules to check.

Output location: the generated op lists belong in the game's asset repo (they are ROM-derived, never in this public repo); the extractor and the schema belong here (`tools/rom/`).

## 5. Open questions

- Is the tick length and status panel identical in all SAM games? Only Tron was measured.
- Pro vs LE vs Premium use different deff tables; the extractor should key on function addresses per ROM.
- Mono DMD only here; colour (Serum) is outside this method.

Where to put it: rom_extraction.md (new deliverable "deff op lists") and the recreation agent's rendering step, once step 1 exists.
