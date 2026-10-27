# Agent C: strict recreation of the ROM's game in MPF

> **Feed back what you learn.** Whatever game you run this agent on, report every game-agnostic learning to
> Ashram56/Stern-SAM-Decryption in the same session, without being asked: a pull request if you have write
> access, otherwise a GitHub issue opened directly. How and what: [CONTRIBUTING.md](../CONTRIBUTING.md).
> **Route it:** ROM extraction and re-coding learnings stay here; anything about Godot, GDE GoZen, GMC, MPF, a
> platform or a board (decoders, kernel, sound, screens, frame rates, installers' toolchain) goes to
> [Ashram56/MPF-Godot-Packaging](https://github.com/Ashram56/MPF-Godot-Packaging) instead (its CONTRIBUTING.md), with at most a pointer here.

Rebuild a Stern SAM game in MPF + Godot (GMC) **exactly as the ROM plays it**: rules, scoring, display,
sound, lamps, service menu and every operator setting. Nothing here improves on the original; that is the
optional [improvement agent](improvement.md). Part of the [master plan](README.md). Tron Legacy LE 1.74 is
the worked example. File paths in `code` are the Tron game repo's ([Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF)) unless said otherwise.

## 1. Scope

**In** (all as the ROM does it, from the asset repo's specs, `rom_data/` and traces):

| Area | Includes |
|---|---|
| Rules | every reachable mode, multiball, hurry-up, wizard mode, combo, skill shot, extra ball, ball save, bonus, match, tilt and slam tilt, ball search, playfield validation, multi-player |
| OS semantics | ROM tasks as tick timers, switch hooks in the ROM's order, deff priorities and the show queue, deff/lamp rules, audits, `score_add` gating |
| Display | one slide per display effect with the ROM's frames and timing, the ROM's fonts and text layout with live values, the score display and status panel, attract pages, **classic 128x32 output byte-exact** |
| Sound | one pool per ROM sound call, channel stops, music replacement |
| Lights | lamp states, lamp-matrix effects (captured and code-drawn), flashers, GI, game-specific outputs (Tron: RGB ramp tubes), shaker |
| Service | **service menu reached as on the machine** (coin door buttons BACK, MINUS, PLUS, SELECT), every adjustment with the ROM's labels, defaults and ranges, audits with their formulas, credits and pricing tables, high scores, coin door open / interlock behaviour, tests the menu offers |
| Hardware overlays | virtual (desktop + MPF Monitor), the real machine (Tron: P-ROC on the SAM boards), every model of the game (Tron: Pro default, LE), the ROM's coil drive times |

**Out**: anything that changes what the player sees or hears compared with the ROM (HD display, other fonts,
colour, glow, new modes, rule changes) belongs to the [improvement agent](improvement.md). The VPX bridge is
the [VPX bridge agent](vpx_bridge.md); the MPF Monitor layout comes from the [VPX extraction agent](vpx_extraction.md);
installing and starting the game on each platform (`setup.py`, `run.py`, the installers, Docker, CI) is the
[packaging agent](packaging.md). C adds a `run.py` or `setup.py` option for its own features (a hardware
overlay, a model) and tells the packaging agent, which carries it to every installer.

## 2. Read, in this order

1. [sam_to_mpf_playbook.md](../knowledge/sam_to_mpf_playbook.md): architecture, build order, verification
   loop and every gotcha so far. It is this agent's main manual; this page adds scope and what changed since.
2. The asset repo's `AGENTS.md` section 14 (what it delivers) and `rom_data/README.md` (where each fact is;
   `rom_data/` wins over older files).
3. The game repo's `docs/rom_differences.md` (Tron: [rom_differences.md](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/rom_differences.md)) before changing any rule: what is meant to differ, and ROM
   behaviour that looks like a bug but is the original.
4. The [knowledge base README](../knowledge/README.md)'s token rules: grep specs, read module docstrings, `git log --no-merges` for the why.

## 3. Definition of done

- `tests/test_traces.py` (scenario → event kinds that match the reference trace) only ever gains kinds; a
  feature is accepted when its scenario's trace matches (`scripts/trace_check.py <scenario>`).
- `pytest -q tests` green; `scripts/render_check.py` (no blank DMD); `scripts/render_diff.py` for display work
  (text pixel-exact against the reference captures); classic frames unchanged (pixel-hash tests).
- Unit tests for paths no reference scenario reaches; RNG seeded in tests only.
- No unreachable ROM code built (the asset repo lists dead code).
- Where MPF cannot do what the ROM does, the smallest departure that keeps the player's experience, logged in
  `rom_differences.md` with the ROM's behaviour and its address, and said to the owner.

## 4. Learned since the playbook (2026-10-04 to 2026-10-08)

- **Coin door open** (deff 4, priority 247, never ends by itself): "50V / 20V DISABLED" covers the display
  while the door is open, dims after 30 s; BACK takes it away (sound 0x009) instead of a service credit; the
  interlock cuts every coil but the optional coil 24. Model the power handler, not a timer
  (`os_layer._power_off_warning`, `tests/test_coin_door.py`). [SAM]
- **Service menu during a game**: the ROM suspends the game task (`task_suspend(0, 0x800)`) and resumes it on
  exit. MPF's timers cannot be suspended, so the game asks "END GAME?" and a second SELECT ends it into the
  menu (logged as a departure). [MPF]
  Every effect that hangs off the normal game over (music, PuP/OST, lamps, audits, high scores) is skipped on
  that route: for each game end that is not the ROM's own (service menu, slam, reset), list those effects and
  redo them explicitly. Tron: the PuP OST of the cancelled game kept looping into attract, which sounded
  quieter; `tron_service_entered` now stops it (observed, 2026-10-27; the Godot side is
  MPF-Godot-Packaging `fixes/godot/audio-only-screen-keeps-playing.md`). [MPF]
- **Pro and LE**: one config in one model's ROM numbers, the other model as an overlay; rules look devices up
  by name (`tron/hw_numbers.py`). Pro decompile: outputs the Pro lacks are reused as flashers (Tron Pro ramp
  flashers 19/25, lower flashers 22/23 fired with them). docs/hardware.md "Pro or LE". [SAM]
- **Asset sync**: a scheduled job opens "Sync assets to <sha>" PRs; run setup, the render check and the tests
  on it, then the owner merges. [Tron]
- **OneDrive**: deletes and renames fail transiently; every build-time file operation (generators included)
  goes through `scripts/fsutil.py`. Installer lessons (private repositories, PowerShell 5.1) are in
  [packaging.md](packaging.md).
- **CI runs only on pushes to `main`**: test locally before pushing a branch, don't wait on CI there.
- **Answers that matched the ROM** (check before "fixing"): Disc Multiball "JACKPOT" screen on every blue
  shot; Sea of Simulation stages played by their shots pay the shot value, not the stage million. Both are
  in `rom_differences.md`; future owner reports may be the same kind.

## 5. Starting a second game (from Transformers Pro 1.80)

What the second game showed (Transformers-MPF, ROM tf_180, 2026-10-04 to 2026-10-10); read before porting a third.
Each line has the Transformers value as the example.

**Setting up**

- **Start from the previous game's OS, not from scratch.** Compare the new ROM's OS tables with the old one's
  first (A's `rom_map.json` table registry): on tf_180, deffs 1-39, leffs 1-19, sound calls 0x001-0x019,
  adjustments 1-64 and the audit counter ids have Tron's numbers, priorities and flags. Copy `game/tron` as
  `game/<tag>` with a rename (`tron` -> tag, `TronOS`, event prefix, env vars), keep the OS modules, and isolate
  every game value (start/shoot-again lamps, music and speech calls, game-over leff) in one `GAME` dict set to
  `None` until A's specs say otherwise. The machine boots and plays a full game on virtual hardware in a few
  hours that way; the boot test is the first test to write. [code]
- **One repository** works: A in `rom/`, B in `game/monitor/` + `docs/vpx/`, C everywhere else. Merge A's and
  B's branches into C's (the first merge needs `--allow-unrelated-histories`); re-merge as they push.
- **Read what A has not packaged yet from the ROM yourself**, as interim files under `game/config/interim/`
  with a generator that needs the ROM path (adjustments, audits, deff and leff tables, the font table), and let
  the build prefer A's files when they land. It keeps C unblocked without guessing.
- **Dedicated switches** come numbered 129-160 in A's package (128 + n): `gen_config.py` turns them into "D<n>".
- **Fonts are ROM data**: the font table gives every glyph's image and x/y offsets, so `gen_fonts.py` builds
  BMFonts straight from `fonts.json` (Tron had to rebuild offsets from captures).
- **A's per-deff `timing.json` carries every text draw** (`pages[].texts`: string, font, x, y, flags, return
  address) and image draw. Layouts come from there, not from guesses; the status panel is found by its draw
  call's return address (`216cc` on tf_180). A page whose texts are all panel calls is not a value page.
- **Music loops**: A exports intro + looped body as one WAV with `loop_start_at`; write a RIFF `smpl` loop into
  the copied WAV and Godot's importer loops only the body.
- **Godot imports CSVs as translations**: put a `.gdignore` in `game/config/` when CSVs live there.
- **Leff tables can move between A's releases** (Transformers: `rom_data/io/lamp_effects.csv`, `loops` = yes for
  until stopped, `tag` = code for leffs drawn from game state). When the traces log coil drivers raw (3-17 ms
  slices), drop Tron's 0.24 s coil hold (`COIL_OFF_DELAY`).

**Matching the traces**

- **Drive scenarios on the reference's input times** (each hit, drain and button waits until the reference
  input's time after "ready"); otherwise timing drifts up to 0.4 s across a long trace and every timed rule looks
  wrong. Replace the old game's switch numbers in the runners with the new game's ball device holes. Forced
  random picks come from watched variables, or, when none is traced, from the scores and audits they cause
  (Transformers: mode-start relight picks from the mode-start score caller and shot audits). Ignore values that
  are uninitialised RAM (0xffff before the game starts).
- **Read the gate, not its name.** A decompile name can say the opposite of the code: `any_timed_mode_running`
  [0x01006704] tests the six multiball flags; the timed modes are [0x010067bc]. Ask A for the flag list behind
  every "multiball / timed mode" condition and check it against a trace where only one of them runs.
- **Switch flags matter.** The captive ball (flags 0x1fff0000) runs its handler on both edges, 3 ticks after each.
- **A captured deff starts its own leffs and sounds.** Calling `leff_start` too doubles them in the trace; start
  the rule's leff and first sound only when the capture lacks them. Passing `sounds=` replaces the capture's
  sounds, so use it only for deffs with none. A deff with no capture length never ends and blocks every lower
  one: give each such deff a length from the traces.
- **Show tasks**: a show ends when another effect replaces its deff; queueing a show task that is already
  playing replaces it; a multiball intro waits on its own priority, not on the show below it.
- **Sound channels decide some rules.** A sound call is refused while a higher priority sample holds its channel
  (sample `mask` in samples.csv, low byte of the call's flags); a rule that retries until it plays then acts at
  once (Transformers' eject warning: 937 retries, logged). Track the playing samples to know.
- **The shaker** belongs to the deff, not the rule: run it when the deff gets the display (A's `shaker.csv`),
  never when the rule requests it; a new run never cuts a longer one short.
- **Ball search timing is a reload hunt.** Each search at the wrong time is a missing or extra reload: look 10 s
  before the ROM's search for the event that reloaded it, then grep the decompile for the reload function's
  callers (tf_180: score, playfield switches, each show task at queue, start and end, the mode totals, the deffs
  of FUN_01006350; flipper buttons pause it; a scoop eject does not reload). Once scores match, compare one
  kicker's coil on-times per trace: they show every search (Transformers: all searches matched).
- **Ball end clears the display, the ROM does not always.** A mode total on screen at the drain plays out before
  the ball-end total shows again (tf_180 deff 137); time it from its start.
- **A multiball's end waits for a lock kick in progress**: the drain check defers while a device is kicking.
- **Timers that pause**: the combo window does not count while the eject holds a ball ([0x0103a4f0(3)]).

**MPF and Python**

- **MPF ball devices**: a ball that comes back while an eject is unconfirmed is a failed eject to MPF and goes
  straight out again; keep `eject_timeouts` under the scenario's shortest return (1 s on the left eject, with the
  ROM's 2 s device task kept in the rules) and lower `exit_count_delay` / `entrance_count_delay` to let a lock
  release four balls 0.4 s apart. A ball hold must cover every ball the rules keep. Log the eject coil yourself
  if the trace check compares it (MPF's pulse is not in the trace).
- **Mechs on virtual platforms**: model them as the reference emulator does, not as the machine (the Optimus
  figure's position switches never move in the simulator, so every move runs to its 7.65 s time limit).
- Do not give a feature an attribute and a method of the same name: Python replaces the method silently and
  the hook dies with "int is not callable" deep in a scenario.

## 6. Status and open work per game

On each game's page (Tron: [Tron-Legacy-MPF `docs/agents/README.md`](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md), "C, strict recreation"; Transformers: [Transformers-MPF](https://github.com/Ashram56/Transformers-MPF) `README.md`).

Last updated 2026-10-10 (section 5: what porting Transformers Pro 1.80 showed).
