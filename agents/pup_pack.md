# Agent G: PuP Pack (videos and music from a PinUP Player pack)

> **Feed back what you learn.** Whatever game you run this agent on, report every game-agnostic learning to
> Ashram56/Stern-SAM-Decryption in the same session, without being asked: a pull request if you have write
> access, otherwise a GitHub issue opened directly. How and what: [CONTRIBUTING.md](../CONTRIBUTING.md).

Game agnostic. Play a PuP Pack (the videos, pictures and music a PinUP Player setup shows around a Visual
Pinball table) with the MPF game, at the same moments PinUP Player would, without Visual Pinball or PinMAME:
decode the pack, map its triggers to the game's events, play it on the game's extra screens, and install it
from the pack author's own download. Optional, like the [improvements](improvement.md): it runs after the
[strict recreation](recreation.md) works and never changes the game itself; with the pack off the game is the
strict game. Part of the [master plan](README.md). The format and the matching method are in
[knowledge/pup_pack_format.md](../knowledge/pup_pack_format.md); the tool is
[tools/pup/pup_decode.py](../tools/pup/pup_decode.py). Tron is the worked example: its game with the pack is
[Tron-Legacy-MPF-PuP](https://github.com/Ashram56/Tron-Legacy-MPF-PuP) (a fork of the game repo), its decoded
pack [Tron-LE-PuP-Pack `docs/decoding/`](https://github.com/Ashram56/Tron-LE-PuP-Pack/blob/main/docs/decoding/README.md).
Paths in `code` are Tron-Legacy-MPF-PuP's unless said otherwise.

## 1. Inputs and outputs

| In | Out |
|---|---|
| The pack: **the zip its author publishes** (or a private copy, section 2) and its author's name and download page | A game repo (or fork) that plays the pack on its own windows, with the game unchanged when the pack is off |
| C's game repo: its display effect events, switch names, sound tracks | The pack decoded: `pup_decode.py decode` JSON, and a human page (Tron: Tron-LE-PuP-Pack `docs/decoding/`) |
| The owner's screens: backglass, a large DMD/LCD, a topper, which are optional | The trigger map (`game/<game>_pup/trigger_map.yaml`) and its match report (`docs/pup_captures.md`) |
| | Install and setup taking the pack from its zip, crediting its author; per-cabinet screen settings |

## 2. Where the pack comes from: its author's zip (credit the author)

A PuP Pack is someone else's work. **The install must be able to take the pack straight from the zip its author
publishes**, so players download it from the author's page (where the author is credited, and sees the
interest), and the game's repositories never redistribute it.

1. **Ship the zip option, always**, in setup and in every installer, even when the project keeps its own copy.
   Tron (verified 2026-10-10 with a zip of the real pack): `TRON_PUP_ZIP=<zip file or https URL>` for
   `setup.py` and the one-line installers, or `--pup-zip FILE` (macOS / Linux installers, `scripts/pup_setup.py`),
   `-PupZip FILE` (Windows installer). `pup_setup.py` finds the folder holding `triggers.pup` at any depth in
   the zip (`PUPVideos/<romset>/`), extracts it into the pack folder, and stamps it with the zip's SHA-256 so the
   same zip is not extracted twice; with a zip the installers don't ask for access to the pack's repository.
2. **Name the author and link the download page** in the README's install section, next to the zip option, and
   in the README's first lines (Tron's README credits the pack's author by name).
3. **The default source is the owner's call.** A private copy (a private repository as a git submodule) is fine
   for the owner's own cabinets (Tron's default: the `pup_pack` submodule from the private
   `Ashram56/Tron-LE-PuP-Pack`; the installers ask for a GitHub token for it). The zip option stays next to it.
4. **Never commit the pack's media to a public repository**, and nothing derived from it beyond what the
   decoding needs (thumbnails and capture pictures stay with the pack's private copy). This repository only
   holds the method.
5. A pack already checked out (the submodule) is left alone when a zip is given; deleting the folder switches.

## 3. Decode the pack

```
pip install pillow
python tools/pup/pup_decode.py decode PACK.zip pack.json        # or the pack folder
```

Read `summary` first: rows, active rows, captures, trigger codes used, captures no row uses, media counts. Then
the screens (which window shows each), the playlists, and every row whose terms are not a single `D<n>` or
`W<n>` (they become overrides). Write the human page for the owner when the pack is big (Tron's
`tools/gen_decoding_doc.py` in Tron-LE-PuP-Pack: one row per capture with its picture and what it fires; it
lives with the pack's private copy because it shows the pack's pictures).

### Checking a run (Tron values)

On the Tron pack (`trn_174h`, the author's v1.0 pack):
`{"triggers": 183, "active": 183, "captures": 98, "codes": {"D": 85, "W": 10, "L": 1}, "unused_captures": [6, 15, 24, 25, 34, 47, 48, 49, 59, 61, 63, 89, 93, 97], "media": {"video": 128, "audio": 26, "picture": 108}}`.
Screens 2 and 12 (backglass underlay and top layer), 13 and 14 (topper, `off` in the shipped option), 15 (OST).

## 4. Map the triggers to the game's events

1. **The game says what it shows.** C's display layer posts one event when a display effect takes the DMD
   (Tron: `tron_deff_<id>`, the ROM's deff number, from `game/tron/display.py`). Without such an event, add it
   in C's game first (a one-line hook): a PuP match is only as good as this signal.
2. **Match every capture** against every frame the game can show:
   ```
   python tools/pup/pup_decode.py match PACK OUT.md --frames '<asset repo>/mpf_package/media/dmd/deff_*/*.gif' \
       --frames '<...>/deff_*/variants/**/*.gif' --frames '<...>/dmd_library/anim_*/animation_128x32.gif' \
       --owners owners.csv --event '<game>_deff_{id}' --map trigger_map.yaml
   ```
   `owners.csv` (`pattern,id`) credits shared library animations to the effects that play them (Tron: built
   from the asset package's `event_map.csv`, column `library_animations`). Tron: 14,691 frames, 22 s; 83 of 98
   captures at 100 %, 88 at 90 % or more; the written map agrees with Tron's hand-checked map on 87 of its 99
   lines.
   The package layout differs per game: Transformers' frames are one level deeper
   (`rom/mpf_package/media/dmd/deffs/deff_NNN/frames/*.png`, `.../deff_NNN/reference_capture.gif`); the runtime's
   `scripts/pup_captures.py` takes the globs, `event_map.csv` and the event name from `game/pup.cfg [captures]`
   and checks the trigger map against the match after every sync.
3. **Check every line by hand** (knowledge doc section 6): shared frames, partial frames (score lines: map to
   `player_added{num==n}`), frames the game never records (boot screen, attract logo: the game's PuP side posts
   its own events), unused captures, conditions on event arguments.
4. **Switches by name** (`switches: {n: s_name}`); **lamp terms and multi-term rows as overrides** (`override:
   {row ID: [events]}`): PinMAME's lamp numbers are not the SAM lamp matrix's (Tron `L35`).
5. Keep the game's own matcher in the game repo (Tron: `scripts/pup_captures.py` writes `docs/pup_captures.md`
   and marks **check** where the mapped effect no longer draws the capture) and run it after every sync with
   the upstream game.

## 5. Play it: the runtime ([tools/pup/runtime/](../tools/pup/runtime/README.md))

The runtime is game agnostic and lives in this repository: `python tools/pup/runtime/install.py <game repo>`
copies it into the game, which configures it in `game/pup.cfg` and never edits the copies (change them here,
install again). Its README lists the files, the one-line hooks and every setting. Built on Tron
(Tron-Legacy-MPF-PuP) and made generic on Transformers (Transformers-MPF, branch `claude/pup-pack`).

| Piece | In the game | What it does |
|---|---|---|
| Pack reader | `game/pup_runtime/pupfiles.py` | reads the three `.pup` files as PinUP Player does; the pack is never edited |
| Engine | `game/pup_runtime/engine.py` | event (with conditions on its arguments, list items, the player's state, counts since a reset) or switch -> rows; `RestSeconds`; two captures of one effect send a row once; no MPF import, so unit tests drive it |
| MPF side | `game/pup_runtime/mode.py`, a mode that is never started | hooks the machine at init (the rules stay untouched); ignores events until Godot's player is ready (so no row starts resting unseen); sends each row as a BCP `pup_play`; posts `pup_boot`, `pup_power_up`, `pup_attract_cycle`; gives each event the player's rule state (`[pup] state`) |
| Godot player | `game/pup/pup_player.gd`, `pup_screen.gd` (autoload `Pup`) | the windows from `[pup] windows` (layers of PuP screens, `CustomPos` boxes, `PuPOverlays` pictures, the DMD window), and per screen the PinUP Player rules: priority, `Loop`, `SetBG`, `StopFile`, `StopPlayer`, `SkipSamePrty`, playlists in order or random, pop-up top layers, background back after a video |
| Settings | `game/pup.cfg` + untracked `game/pup.local.cfg`, read by both sides | on/off (`<env>_PUP=0`), windows and their screens, music screen, third screen, window layout (`stack` on a desktop, `manual` per screen for a cabinet), video fit |
| Video add-ons | `pup_addons/` (copied to `game/addons/` by setup) | native_video (Windows, macOS; the heap-fixed build) and GDE GoZen (Linux): the pack's mp4s play as they are, hardware decoded |

- **Music hand-over**: Godot answers MPF's `pup_hello` with `pup_ready` once its windows and media are there;
  only then MPF drops the ROM's music calls (the sound pools on the music track) and stops the running ROM
  music. No ready player (no media, PuP off, tests): the ROM music plays.
- **The DMD window**: the game's 128x32 DMD stays the source (render checks, P-ROC output unchanged); the PuP DMD
  window draws it larger in the pack's DMD frame art or a generated background.
- **Say why the PuP is off**: `run.py` prints one line (`PuP on: ...` or what is missing). Without it, a missing
  conversion looks like a broken install (it did on Tron's first launch).

## 6. Video playback per platform

**Play the pack's mp4s as they are, with a native hardware-decoding add-on; do not convert them** (the owner's
rule, 2026-10-10: converting a 1 GB pack to Theora took most of an hour on the first Transformers setup for
nothing). The game needs Godot 4.6+ for native_video (Transformers moved from 4.5.2 to 4.6.3 for it). Godot's own
player only does Theora, so conversion is the fallback for a machine with no add-on. Details in
Tron-Legacy-MPF-PuP `docs/pup.md` and `docs/jetson.md`:

| Platform | Player | Note |
|---|---|---|
| Windows, macOS | a native video GDExtension (Media Foundation, AVFoundation), the pack's mp4s as they are | Godot 4.6+; Tron carries a fixed build (a heap overrun upstream): never replace a patched add-on with the upstream zip |
| Linux x86_64 / arm64 | GDE GoZen (FFmpeg) | on a Jetson, NVIDIA's hardware decoder through libnvmpi (packaging agent, section 5a) |
| Anywhere, fallback only | mp4 -> Theora conversion at setup (ffmpeg with libtheora, or imageio-ffmpeg in the venv) | slow on the first setup; later runs redo only changed files |

## 7. Packaging and keeping up with the game

- **Keep the PuP in its own files** and touch the game's files with one-line hooks only (Tron: the config
  include, the Godot autoload, `.gitmodules`, `.gitignore`, one `pup_setup` call each in `setup.py` and
  `run.py`), so the upstream game merges in cleanly (`scripts/sync_upstream.py`, then the capture re-check).
- `setup.py` runs the PuP step after the game's media: fetch or extract the pack (section 2), install the video
  add-on for the platform, list the videos (convert them only where no add-on runs), print the status line.
- Every installer gets the zip option and passes it on; the [packaging agent](packaging.md) owns the installers.

## 8. Learned so far

- A capture of a score line fires on any frame that shows that text: map it to the game event it means.
- PinMAME lamp numbers differ from the SAM lamp matrix; prefer a game event over a lamp term.
- Topper screens are often `off` in the shipped option set; turn them on in the game's settings, not in the pack.
- Linux needs X11 (not Wayland) for one window per monitor; a cabinet needs screen blanking off and autologin.
- Several screens switching videos at once, and video work on Godot's main thread, froze ARM boards: decode
  off the main thread at the size the window shows (Tron-Legacy-MPF-PuP `docs/jetson.md`).
- A capture without a purple rectangle compares the whole frame; the decoder skipped them before (Transformers
  1, 8, 9).
- Most of a pack's captures can be the variants of one effect (Transformers: every battle shot, side, lock and
  wizard shot): map them with conditions on the event's arguments and the player's state (section 4,
  knowledge doc section 6), adding the argument to the game's call when it is missing.
- Screen numbers and roles are the author's: Transformers puts the music on 4 and the topper on 0 (both `off` in
  the shipped option), and five overlay boxes on the backglass with `CustomPos`. Read `screens.pup`; configure
  the windows' `layers` from it.
- `D0` without `=1` is the start-up trigger too (Transformers row 246, the backglass overlay).
- Events that reach the PuP side before Godot's player is ready must not fire rows: their `RestSeconds` would
  start counting for nothing (seen on Transformers: Ball Saved silenced for 10 s after Godot came up).

## 9. Status per game

| Game | Pack | Game with the pack | State |
|---|---|---|---|
| Tron Legacy LE 1.74 | `trn_174h`, by its author (credited in the fork's README), private copy `Ashram56/Tron-LE-PuP-Pack` | [Tron-Legacy-MPF-PuP](https://github.com/Ashram56/Tron-Legacy-MPF-PuP) | Built: three screens, OST, Windows / macOS / Linux / Jetson; zip option in setup and installers; not yet on `tools/pup/runtime/` |
| Transformers Pro 1.80 | `tf_180` v1.0 by TerryRed, private copy `Ashram56/Transformers-PuP` | [Transformers-MPF](https://github.com/Ashram56/Transformers-MPF) `claude/pup-pack` (in the game repo, not a fork) | Built on `tools/pup/runtime/`: backglass with its five overlay boxes, DMD in the pack's art, topper, the pack's music; 210 of 213 captures in use mapped; native mp4 on Godot 4.6.3; seen running a Blackout battle on Windows |

Keep this file current. Last updated 2026-10-10 (new: the runtime in `tools/pup/runtime/`, conditions on
arguments and the player's state, whole-frame captures, native mp4 only; from the Transformers pack).
