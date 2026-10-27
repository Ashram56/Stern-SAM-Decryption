# Agent G: PuP Pack (videos and music from a PinUP Player pack)

> **Feed back what you learn.** Whatever game you run this agent on, report every game-agnostic learning to
> Ashram56/Stern-SAM-Decryption in the same session, without being asked: a pull request if you have write
> access, otherwise a GitHub issue opened directly. How and what: [CONTRIBUTING.md](../CONTRIBUTING.md).
> **Route it:** ROM extraction and re-coding learnings stay here; anything about Godot, GDE GoZen, GMC, MPF, a
> platform or a board (decoders, kernel, sound, screens, frame rates, installers' toolchain) goes to
> [Ashram56/MPF-Godot-Packaging](https://github.com/Ashram56/MPF-Godot-Packaging) instead (its CONTRIBUTING.md), with at most a pointer here.

Game agnostic. Play a PuP Pack (the videos, pictures and music a PinUP Player setup shows around a Visual
Pinball table) with the MPF game, at the same moments PinUP Player would, without Visual Pinball or PinMAME:
decode the pack, map its triggers to the game's events, play it on the game's extra screens, and install it
from the pack author's own download. Optional, like the [improvements](improvement.md): it runs after the
[strict recreation](recreation.md) works and never changes the game itself; with the pack off the game is the
strict game. Part of the [master plan](README.md). The format and the matching method are in
[knowledge/pup_pack_format.md](../knowledge/pup_pack_format.md); the tool is
[tools/pup/pup_decode.py](../tools/pup/pup_decode.py). Tron is the worked example: its game with the pack is
[Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF) (built in the fork Tron-Legacy-MPF-PuP, merged
back into the game repo on 2026-10-10), its decoded
pack [Tron-LE-PuP-Pack `docs/decoding/`](https://github.com/Ashram56/Tron-LE-PuP-Pack/blob/main/docs/decoding/README.md).
Paths in `code` are Tron-Legacy-MPF's unless said otherwise.

## 1. Inputs and outputs

| In | Out |
|---|---|
| The pack: **the zip its author publishes** (or a private copy, section 2) and its author's name and download page | The game repo playing the pack (build it there, not in a fork: section 7) on its own windows, with the game unchanged when the pack is off |
| C's game repo: its display effect events, switch names, sound tracks | The pack decoded: `pup_decode.py decode` JSON, and a human page (Tron: Tron-LE-PuP-Pack `docs/decoding/`) |
| The owner's screens: backglass, a large DMD/LCD, a topper, which are optional | The trigger map (`game/<game>_pup/trigger_map.yaml`) and its match report (`docs/pup/captures.md`) |
| | Install and setup taking the pack from its zip, crediting its author; per-cabinet screen settings |

## 2. Where the pack comes from: its author's zip (credit the author)

A PuP Pack is someone else's work. **The install must be able to take the pack straight from the zip its author
publishes**, so players download it from the author's page (where the author is credited, and sees the
interest), and the game's repositories never redistribute it.

1. **Ship the zip option, always**, in setup and in every installer, even when the project keeps its own copy.
   Tron (verified 2026-10-10 with a zip of the real pack): `TRON_PUP_ZIP=<zip file or https URL>` for
   `setup.py` and the one-line installers, or `--pup-zip FILE` (macOS / Linux installers, `scripts/pup/pup_setup.py`),
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
5. Keep the game's own matcher in the game repo (Tron: `scripts/pup/pup_captures.py` writes `docs/pup/captures.md`
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
- **Size the DMD on the glass, not in pixels**: bar panels (1280x390, 1920x480 LCDs) often have pixels that are
  not quite square. Take the monitor's picture size in mm as a setting, keep the DMD 4:1 in mm (height in pixels
  = width / 4 x pixel aspect, pixel aspect = (mm wide / px wide) / (mm tall / px tall)), and offer a real DMD's
  size (128x32 dots on 320x80 mm) as the "full size" choice. A generated background with moving parts round the
  DMD needs room, so offer both: a smaller DMD with the background's action round it, or the DMD full size over
  a still background, settable in the service menu. Tron: a 1280x390 bar of 360x109 mm (pixel aspect 1.0063)
  takes a 320x80 mm DMD at 1138x286 px; with the light cycles round it the DMD is 870x219 px (Tron-Legacy-MPF
  `docs/pup/README.md`, "DMD size").
- **Say why the PuP is off**: `run.py` prints one line (`PuP on: ...` or what is missing). Without it, a missing
  conversion looks like a broken install (it did on Tron's first launch).

## 6. Video playback per platform

**Play the pack's mp4s as they are, never convert them** (the owner's rule, 2026-10-10: converting a 1 GB pack
to Theora took most of an hour on the first Transformers setup for nothing). Godot's own player only does Theora,
so conversion is the last fallback for a machine with no add-on. The add-ons ship in `tools/pup/runtime/pup_addons/`.
Tron's choices (details in Tron-Legacy-MPF-PuP `docs/pup/README.md` and `docs/jetson/README.md`):

| Platform | Player | Note |
|---|---|---|
| Windows x86_64 | GDE GoZen (FFmpeg), the pack's mp4s as they are; the GPU decodes through FFmpeg's Direct3D 11 Video hwaccel, else DXVA2 (any GPU vendor, nothing to install), frames copied back as NV12; software when the GPU cannot | the same player and optimizations as Linux (frame queue, worker-thread opens, NV12 upload). The native video add-on stays installed as the fallback, picked by a setting (Tron: `[pup] video_player="native"` or `TRON_VIDEO_PLAYER=native`) |
| macOS | a native video GDExtension (AVFoundation), the pack's mp4s as they are | Godot 4.6+; Tron carries a fixed build (a heap overrun upstream): never replace a patched add-on with the upstream zip |
| Linux x86_64 / arm64 | GDE GoZen (FFmpeg) | on a Jetson, NVIDIA's hardware decoder through libnvmpi ([MPF-Godot-Packaging `platforms/jetson.md`](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/platforms/jetson.md)) |
| Raspberry Pi 4 (Linux arm64) | GDE GoZen with `h264_v4l2m2m` and a zero-copy patch (EGLImage of the decoder's dmabuf) | opt-in; the GPU is the limit with 1080p layers: unshaded YUV shader, layers hidden under an opaque video neither drawn nor decoded, no full-window `ColorRect`, optional lower render size (packaging agent, section 5d) |
| Anywhere, fallback only | mp4 -> Theora conversion at setup (ffmpeg with libtheora, or imageio-ffmpeg in the venv) | slow on the first setup; later runs redo only changed files |

- **How the players behave** (one player everywhere, a switch never waits for a worker, the GoZen Windows build,
  checking the decoder without the game) moved to [MPF-Godot-Packaging `platforms/video-playback.md`](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/platforms/video-playback.md)
  on 2026-10-27, with the decoder fixes in its `fixes/gde-gozen/` (decode queue fill, hardware decoding order). Add new
  player, decoder and VideoCore findings there. (Tron)


## 7. Packaging and keeping up with the game

- **Build the pack into the game repo, not a fork.** Tron's fork (Tron-Legacy-MPF-PuP) diverged by 112 commits
  in five days; every platform fix landed twice and each sync conflicted (14 files at the final merge), so the
  owner merged it back into the game repo (Tron-Legacy-MPF PR #41, 2026-10-10). Transformers built it in the game
  repo from the start. With the pack optional and in its own files, the game repo stays the strict game when
  the pack is absent. (observed)
- **An optional private pack never blocks a public install.** When the pack's default source is a private
  submodule, the installers include it in the token check only when a token was given up front or git's
  credentials can already read it; otherwise they say so in one line and install the game without the pack
  (Tron: `install_prereqs_*` `github_auth`). `setup.py`'s pack step fails soft and the game runs without it.
  The CI checkout leaves that submodule out. (code, Tron merge 2026-10-10)
- **Keep the PuP in its own files** and touch the game's files with one-line hooks only (Tron: the config
  include, the Godot autoload, `.gitmodules`, `.gitignore`, one `pup_setup` call each in `setup.py` and
  `run.py`), so a reader sees what is the pack's and a game change rarely touches it (then re-run the capture
  check).
- `setup.py` runs the PuP step after the game's media: fetch or extract the pack (section 2), install the video
  add-on for the platform, list the videos (convert them only where no add-on runs), print the status line.
- Every installer gets the zip option and passes it on; the [packaging agent](packaging.md) owns the installers.
- **The pack's own files in their own folders** (Tron: `scripts/pup/`, `docs/pup/`, `docs/jetson/`, `game/pup/`,
  `game/tron_pup/`), marked *(PuP)* in the README's folder tree. (code, Tron-Legacy-MPF-PuP PR #16)
- **Never move a folder something outside the repository links to**: filed upstream issues link to their test
  programs and patches, and the one-line installers are fetched by URL (Tron: `scripts/gozen/`,
  `scripts/install/`, `pup_addons/`, `docs/upstream_issues/` stay where they are). A pull that empties a folder
  leaves it behind: `scripts/clean_tree.py` lists and removes them, and the sync runs it. (code)
- **If a fork already exists, merge it back** rather than keep syncing: a platform fix made in a fork and again
  upstream conflicts at every sync (Tron's Xavier NX work landed in both, upstream PR #35; the next sync
  conflicted in 10 files). At the merge, where both sides changed the same setting, take the side measured with
  the toolchain the merged repo ends up on (Tron: Godot 4.6.3 from the fork, so its render thread default),
  restore the game repo's install URLs and folder names, drop the fork's sync script, and log the pack's
  departures (music, extra screens) in the game's `docs/rom_differences.md`. (observed, Tron 2026-10-10)

## 8. Learned so far

- A capture of a score line fires on any frame that shows that text: map it to the game event it means.
- PinMAME lamp numbers differ from the SAM lamp matrix; prefer a game event over a lamp term.
- Topper screens are often `off` in the shipped option set; turn them on in the game's settings, not in the pack.
- Linux needs X11 (not Wayland) for one window per monitor; a cabinet needs screen blanking off and autologin.
- Several screens switching videos at once, and video work on Godot's main thread, froze ARM boards: decode
  off the main thread at the size the window shows (Tron-Legacy-MPF-PuP `docs/jetson/README.md`).
- A capture without a purple rectangle compares the whole frame; the decoder skipped them before (Transformers
  1, 8, 9).
- Most of a pack's captures can be the variants of one effect (Transformers: every battle shot, side, lock and
  wizard shot): map them with conditions on the event's arguments and the player's state (section 4,
  knowledge doc section 6), adding the argument to the game's call when it is missing.
- **Variants come from the ROM's animation tables, never from the pack's row order** (code, Transformers 1.80).
  An effect with one capture per shot, lock or jackpot draws from a table of animation functions; read the
  index in the deff (`(**(code **)(&DAT_040cXXXX + idx*4))()`, each function `FUN_0102ff60(first_image, last,
  ...)`) and in the function that starts it (what it stores in the task's `+0x30..+0x44` fields), read the table
  from the ROM image, and match each entry's first image to the capture's best library animation
  (`dmd_library/anim_NNN_img<first image>`). On Transformers the row-order guesses were wrong for every jackpot
  and several battles: battle hits index by **shots left** (`BASE - left`, kept per player across restarts), not
  hits since the start; jackpots by the shot, a random draw or a no-repeat bag; a lock's animation by a
  per-player music call that moves on at each multiball. Post that index from the game (an event argument such
  as `left` or `anim`) and key the map on it. Captures drawn as run-time text (wizard character names) score
  under 50 % against every recorded frame yet are real ROM output: map them from the code too.
- Pack row labels can be wrong ("JP2" rows that are double-jackpot frames): trust the capture's frames.
- Screen numbers and roles are the author's: Transformers puts the music on 4 and the topper on 0 (both `off` in
  the shipped option), and five overlay boxes on the backglass with `CustomPos`. Read `screens.pup`; configure
  the windows' `layers` from it.
- `D0` without `=1` is the start-up trigger too (Transformers row 246, the backglass overlay).
- Events that reach the PuP side before Godot's player is ready must not fire rows: their `RestSeconds` would
  start counting for nothing (seen on Transformers: Ball Saved silenced for 10 s after Godot came up).

## 9. Status per game

| Game | Pack | Game with the pack | State |
|---|---|---|---|
| Tron Legacy LE 1.74 | `trn_174h`, by its author (credited in the game's README), private copy `Ashram56/Tron-LE-PuP-Pack` | [Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF) (the fork merged back 2026-10-10) | Built: three screens, OST, Windows / macOS / Linux / Jetson; zip option in setup and installers; not yet on `tools/pup/runtime/` |
| Transformers Pro 1.80 | `tf_180` v1.0 by TerryRed, private copy `Ashram56/Transformers-PuP` | [Transformers-MPF](https://github.com/Ashram56/Transformers-MPF) `claude/pup-pack` (in the game repo, not a fork) | Built on `tools/pup/runtime/`: backglass with its five overlay boxes, DMD in the pack's art, topper, the pack's music; every capture in use mapped, each variant checked against the ROM's animation tables; GoZen with d3d11va on Windows (1080p at 4.3 ms a frame, Ryzen 7 2700), Godot 4.6.3; seen running a Blackout battle on Windows |

Keep this file current. Last updated 2026-10-27 (player behaviour moved to MPF-Godot-Packaging; before 2026-10-12: music preloaded on a worker; a video switch never waits for a worker; DMD sized in mm on bar panels, full size or with the background's action; before 2026-10-10: Tron's fork merged back into the game repo: build in the game repo, optional private pack in installers; before: variants from the ROM's animation tables, not the pack's row order; before: the runtime in `tools/pup/runtime/` with GoZen on Windows,
conditions on arguments and the player's state, whole-frame captures, never convert; from the Transformers pack;
before: Windows plays the pack through GoZen with GPU decoding, fork layout and sync lessons, the PuP Pack agent,
the format page and `tools/pup/`, from the Tron work in Tron-Legacy-MPF-PuP and Tron-LE-PuP-Pack).
