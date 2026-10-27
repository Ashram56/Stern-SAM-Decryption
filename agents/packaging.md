# Agent F: packaging (install and run on every platform)

> **Feed back what you learn.** Whatever game you run this agent on, report every game-agnostic learning to
> Ashram56/Stern-SAM-Decryption in the same session, without being asked: a pull request if you have write
> access, otherwise a GitHub issue opened directly. How and what: [CONTRIBUTING.md](../CONTRIBUTING.md).

Make the game installable and runnable by the owner on every platform the master plan targets, with **one
line to install** and **one command to run** per platform: Windows, macOS, Linux, plus the options for each
hardware target (virtual + MPF Monitor, the real machine on a P-ROC, Visual Pinball X). Part of the
[master plan](README.md). Tron Legacy MPF ([Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF)) is the worked example: copy its
scripts, rename, and keep them in step. File paths in `code` are the Tron game repo's ([Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF)) unless said otherwise.

"Packaging" here is the game's **install and run kit**. It is not the ROM extraction's MPF asset package
(`mpf_package/`, agent A's `AGENTS.md` section 10) and not the game itself (agent C).

> **The game-agnostic kit:** [Ashram56/MPF-Godot-Packaging](https://github.com/Ashram56/MPF-Godot-Packaging) installs
> MPF, MPF Monitor, Godot and the patched GMC with one line per OS (Jetson included), documents every fix to MPF,
> GMC, Godot and the video add-ons one file each with an upstream issue draft (`fixes/`), and every platform finding
> (`platforms/`). Take new pins, patches and installer lessons from there and add new ones there; a game's kit
> (below) keeps only what is the game's own. A game can point its launcher at that toolchain (`GODOT`, the venv) or
> copy the patched GMC with `python -m mpf_godot addons GAME` (2026-10-12).

## 1. What this agent owns

Every file below is this agent's, in the game repo. Other agents may add a feature flag to `setup.py` or
`run.py` for their own work (C: `--hw proc`, `--machine le`; D: `--hw vpx`, `--vpx`; E: `--dmd ...`); this agent
then carries it into every installer, the one-line commands, Docker, CI and the docs, on every platform.

| File (Tron) | What it does |
|---|---|
| `scripts/toolchain.py` | the pinned versions (Python, MPF, Godot, GMC, MPF Monitor, extra packages per option) and every per-OS path; standard library only |
| `scripts/setup.py` | the workspace on any OS: assets submodule, `.venv/`, Godot for the host, GMC (patched), MPF Monitor and its missing `.ui` files, generated config and media, Godot import. Idempotent; `--dry-run`, `--os/--arch` plan for another host; `--no-monitor`, `--vpx`, `--skip-godot`, `--skip-media`, `--upgrade` |
| `scripts/run.py` | starts Godot (GMC, BCP 5050) first, then MPF, optionally MPF Monitor; one option per hardware target (`--hw virtual/proc/vpx`, `--machine`, `--monitor`); stale media regenerated on launch; Xvfb on Linux without a display |
| `scripts/install/install_prereqs_windows.ps1` | Windows 10/11, PowerShell 5.1 or 7: Git, Python 3.11 (winget or the official installers), long paths, the clone, `setup.py`; `-Proc` (VC++ runtime, FTDI check). Transformers adds `-Vpx` / `-Table` (section 4) |
| `scripts/install/install_prereqs_macos.sh` | macOS 12+, Intel or Apple silicon: Homebrew or python.org 3.11, Git, `setup.py`; `--proc` |
| `scripts/install/install_prereqs_linux.sh` | apt, dnf, pacman; x86_64 or arm64; Python 3.11 from the distribution, deadsnakes or uv; Qt and Xvfb libraries; `--proc` builds the driver and installs the udev rule |
| `scripts/install/build_pinproc.sh`, `99-pinproc.rules` | libpinproc and pypinproc from pinned commits (Linux, macOS) |
| `scripts/setup.bat`, `setup.ps1`, `setup_workspace.sh` | thin wrappers that find Python and run `setup.py` |
| `docker/` | Linux alternative: one image, compose services (setup, godot, mpf, monitor), overlays for GPU, audio, P-ROC; `docker/tron.sh` |
| `.github/workflows/test.yml` | CI on Windows, macOS and Linux: `setup.py`, `pytest`, render check on Linux; pushes to `main` only |
| `tests/test_install.py`, `tests/test_toolchain.py` | installers in `--dry-run`, standalone clone, private-repo token flow, Docker plans, toolchain paths, `run.py` arguments |
| Docs: the whole README (section 3, item 7), `docs/requirements.md`, `docs/development.md` "Getting started", `docker/README.md`, the set-up parts of `docs/vpx.md` and `docs/hardware.md` (P-ROC driver) | what the owner reads to install and start the game |

## 2. Inputs

- The game repo from agent C, once its toolchain step boots MPF + GMC (playbook section 4, step 1).
- The asset repo's location and visibility (submodule at `assets/`, or a folder in the game repo: Transformers
  keeps the ROM extraction in `rom/`, so it has no second repository to check).
- The owner's hardware line from the kickoff message (desktop, VPX, P-ROC, ...): which options to build.
- D's bridge (`vpx_bridge.py --register`, `vpx_table.py`) and E's display options, as they land.

## 3. Definition of done

1. **One line to install, per platform**, given in the README, that works on a computer with nothing
   installed. It installs what is missing (Git, Python 3.11, system libraries), clones the repo (or pulls an
   existing clone), runs `setup.py`, and ends by printing the run command. Tron:

   ```powershell
   powershell -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/install/install_prereqs_windows.ps1) -join [char]10))"
   ```
   ```sh
   bash <(curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/install/install_prereqs_macos.sh)   # or ..._linux.sh
   ```

   Options go at the end of the Windows line: `... -join [char]10)) -Vpx -Table '<table.vpx>'"`. **Never
   `irm <URL> | iex`**: on the Transformers owner's Windows PowerShell it ran the script line by line and stopped
   on line 1 ("the terminator #> is missing from the multiline comment"; reproduced in pwsh with
   `Get-Content <script> | iex`, observed 2026-10-10). The `-join [char]10` makes one script whether `irm` returns
   a string or lines; dry-run the README's exact line with pwsh before publishing it.
2. **One command to run**, per platform and target, from the install folder:
   `.venv\Scripts\python scripts\run.py [--monitor | --hw proc | --hw vpx]` (Windows), `.venv/bin/python
   scripts/run.py ...` (macOS, Linux). The installer prints it at the end, with the options it was given.
3. **Every option on every installer** the platform can support: dry run (plan only, changes nothing), no
   questions, no MPF Monitor, P-ROC, VPX (Windows only: VPX runs only there), prerequisites only, and
   pass-through arguments to `setup.py`. The same names everywhere (`--dry-run` / `-DryRun`, and so on).
4. **Safe to re-run**: every step is skipped when in place; a second run updates the clone and redoes only
   what changed. A clone whose branch was deleted on GitHub (a merged PR) moves to the default branch.
   Before the pull, fetch and clear the files the update adds that already sit untracked in the clone, or
   `git pull` aborts ("untracked working tree files would be overwritten"): Godot writes a `.uid` next to each
   script and shader it opens, so a player's PC often has one before the commit that tracks it. Remove Godot's
   `.uid`/`.import` files and identical copies, move anything else to `<file>.local`, never delete a user's
   file. Commit every `.uid` with its script; ignore `.import`. Observed on Tron, 2026-10-10:
   `game/tools/bake_fonts.gd.uid` stopped the Windows update (Tron-Legacy-MPF PR #43 has the bash and
   PowerShell functions).
5. **Settings by environment**, one prefix per game (Tron `TRON_`, Transformers `TF_`): `<P>_DIR` (install
   folder), `<P>_BRANCH`, `<P>_REPO`, `<P>_ASSETS_REPO` when there is a second repository, `<P>_GITHUB_TOKEN`.
6. **Tests**: every installer runs in its dry-run mode in `tests/test_install.py` (Linux families, macOS plan,
   standalone clone, branch gone, token flow); `pytest -q tests` green before pushing.
7. **A full README** at the game repo's root, the player's front page, owned by this agent (Tron's
   [README.md](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/README.md) is the model; Transformers-MPF's
   follows it). In this order: what the game is (game, model, ROM version, MPF / GMC / Godot versions, the
   platforms) and a pointer to the master plan; **Install** (the one line per platform, Windows with VPX when
   D's bridge exists; folder, branch, token and pack-zip settings; the options; clone-first fallback);
   **Play** (the run command per platform and target, free play, the key table from `gmc.cfg`); **Settings**
   (every `run.py` option and environment override); optional parts (PuP Pack with its author named, VPX);
   the status table; **Update**; **Tests**; **More** (links to every doc in `docs/`, the asset package);
   **Credits** (the manufacturer, pack and table authors, MPF, Godot). Plus `docs/requirements.md` per OS. A
   game's README that is only a status page is not done: on Transformers it had no macOS / Linux line and no
   Play or Settings section until the owner asked (2026-10-10).
8. **Docs** say the one line, the run command, the options and the requirements, in the owner's words, and are
   updated in the same change as any installer or `run.py` option.

## 4. Porting the kit to a new game

On Transformers the kit was not ported with the game: its VPX bridge thread had to port the Windows installer
by hand to give the owner a one-line VPX set-up (Transformers-MPF commit 85e87a3). Port it all at once, as
soon as the game repo exists:

1. Copy `scripts/toolchain.py`, `setup.py`, `run.py`, `fsutil.py`, `gmc_patch.py`, `scripts/install/`, the
   wrappers, `docker/`, the CI workflow and `tests/test_install.py` / `test_toolchain.py`.
2. Rename, in one block at the top of each installer: the environment prefix, repository URL, default
   branch, install folder name (`~/Tron-Legacy-MPF`), the assets repository (or drop that check when there
   is none), the banner text, the short-path hint (`C:\tron`), the Docker image and service names, the COM
   ProgID (`TronMPF.Controller`).
3. **Default branch**: a repository without `main` yet (Transformers, during the build) needs the working
   branch as the default and in the raw URL of the one line; switch both to `main` once it exists (Transformers:
   2026-10-10, together with `docs/vpx.md`'s line). Also set `main` as the GitHub default branch (Settings >
   General): only the owner can, and until then `raw.githubusercontent.com/<repo>/HEAD/...` and the repo page
   show the old branch.
4. **VPX set-up on Windows** (Transformers, worth porting back to Tron): `-Vpx` runs `setup.py --vpx` (olefile,
   pywin32), registers the COM server elevated (`Start-Process ... -Verb RunAs -Wait`, then check the exit
   code; the rest of the script stays unelevated), and with `-Table <path>` writes the table's `.vbs` with
   `vpx_table.py` (the `.vpx` itself is never changed). The final notes add the `run.py --hw vpx` line.
   `-Table` is a string parameter next to the `ValueFromRemainingArguments` pass-through, so the script needs
   `[CmdletBinding(PositionalBinding = $false)]`: without it, in the one line's `& ([scriptblock]::Create(...))`
   form, a bare extra argument binds to `-Table` (verified with pwsh 7.4 on Linux; a `-File` run did not show it).
   Dry-run the published one line with pwsh on Linux (the linux-x64 tarball runs from the scratchpad).
5. Run every installer with its dry-run option and the tests; on Windows, ask the owner to run the one line
   (`-DryRun` first) and report the output.

## 5. Learned so far

- **Private repositories**: test read access anonymously first (`git -c credential.helper= ls-remote`), then
  ask for a fine-grained GitHub token (Contents: read-only) and pass it to git for this run only (`url.insteadOf`
  in the environment, inherited by `setup.py`), and hand it to the credential helper for later pulls. Never
  open Git Credential Manager's window. A private repository answers 404 to `curl`/`irm` without a token, so
  the one line cannot fetch itself: document clone-then-run for that case.
- **Testing the token step on macOS CI**: run it with `GIT_CONFIG_NOSYSTEM=1` as well as a temporary HOME.
  Homebrew git's system config sets `credential.helper=osxkeychain`, which hangs in `git credential approve` when
  HOME has no keychain, so the test times out on `macos-latest` only (observed, Transformers `tests/test_install.py`
  `test_github_auth`, red on every main push from 2026-10-10 until the fix, 2026-10-22).
- **A private pack repository next to a public game**: when the only private repository is an optional one
  (Transformers: the PuP Pack's submodule, the owner's copy), the token step must not stop the install. With no
  token, `--yes`, an empty answer or a token that cannot read it, say the game installs without that part and
  go on; skip the check entirely when the pack comes from its zip (`<P>_PUP_ZIP`) or is off (`<P>_PUP=0`).
  `setup.py` must already treat a failed submodule fetch as "without the PuP", not an error. Test each case in
  `test_install.py` (Transformers-MPF's `test_github_auth`).
- **Run this agent, not only its file**: on Transformers the packaging thread wrote this file but the kit was
  never ported (only the Windows installer existed, from the VPX bridge thread) until the owner asked for the
  README. The coordinator starts F on the game as soon as C boots, per the master plan's section 3.
- **Windows PowerShell 5.1** turns a native command's stderr into a terminating error under
  `$ErrorActionPreference = 'Stop'`: run git quietly and test `$LASTEXITCODE` only.
- **Never the bare `python` on Windows**: on a fresh install it is the Microsoft Store stub. Use the `py`
  launcher, then the default install folders.
- **Long paths**: turn on `LongPathsEnabled` (needs administrator once), or keep the clone in a short folder.
- **OneDrive**: deletes and renames fail transiently; every build-time file operation goes through
  `scripts/fsutil.py`, and the default install folder is outside OneDrive.
- **Pins and launch order**: every pin carries its reason in `toolchain.py` (the playbook's toolchain table
  lists them: `ruamel.yaml.clib`, MPF Monitor's missing `.ui` files, Godot from GitHub releases); probing
  GMC's port and the start order are in the playbook's section 6 (MPF, GMC). Re-read both before changing
  `setup.py` or `run.py`.
- **macOS and Linux one lines** use `bash <(curl ...)`, not `curl | bash`, so the script keeps the terminal as
  stdin for its questions and takes options after the line (inferred from the scripts' prompts).
- **Third-party packs install from their author's zip**: a game that plays a PuP Pack takes it from the zip the
  author publishes, as an option of setup and of every installer (Tron: `TRON_PUP_ZIP`, `--pup-zip`, `-PupZip`;
  the [PuP Pack agent](pup_pack.md), section 2), and the README names the author next to it. With a zip the
  installers skip the pack repository's token check; without one, see "A private pack repository next to a public
  game" above (Tron: the pack's repository joins the check only with a token given or credentials that read it). Windows installer parameters need
  `[CmdletBinding(PositionalBinding = $false)]` once a string parameter is added, or a stray setup argument binds to
  it. (verified 2026-10-10 with pwsh 7.4 on Linux)
- **CI runs only on pushes to `main`**: test the installers locally in dry-run mode; on Windows only the
  owner can run them for real.
- **Pasting a token on Windows**: in the PowerShell / cmd console, paste with a right-click; Ctrl+V did nothing at
  the installer's token prompt (observed, Tron owner test on Windows). Say so next to the prompt in the README.
- **Release tags from a cloud session**: the session's git proxy refuses tag pushes (403), so the owner creates
  the tag on GitHub or from a clone (observed, Tron-Legacy-MPF-PuP `jetson-agx-orin-l4t-r36.4.3`). Name the tag and
  the commit in the report.

## 5a. Jetson (Xavier NX, AGX Orin): an ARM cabinet with the PuP Pack

The Jetson kit lives in the game repository with the PuP Pack (Tron: [Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF),
merged in from the fork Tron-Legacy-MPF-PuP on 2026-10-10), because it exists for the pack's videos: its `docs/jetson/xavier_nx.md` has every finding and figure,
`docs/jetson/README.md` the video decoding fixes, `docs/performance.md` the measurements. What an installer or launcher
for a Jetson must do (Tron tested on a Xavier NX Developer Kit, L4T R35.6.4 / JetPack 5.1.4, Ubuntu 20.04, and an
AGX Orin, L4T R36.4.3 / JetPack 6.2):

- **Install order:** the Linux one line (arm64; Ubuntu 20.04 ships Python 3.8, so Python 3.11 comes from uv), then
  `scripts/install/install_jetson_hwdec.sh` (libnvmpi from jetson-ffmpeg with `scripts/gozen/nvmpi_flush.patch`,
  NVIDIA packages pinned to the board's own L4T release: the r36.4 apt repo also offers 36.4.7; config files kept
  instead of a dpkg prompt; GNOME idle blanking off), then `scripts/install/jetson_selftest.sh --stock`, which must
  pass every check. JetPack 5 keeps NVIDIA's libraries in `/usr/lib/aarch64-linux-gnu/tegra/`, JetPack 6 in
  `.../nvidia/`.
- **Hardware video decoding** is a GDExtension (GDE GoZen) with FFmpeg and the nvmpi decoders linked in, cross-built
  in Docker (`scripts/build_gozen.sh arm64`) from a clean work folder; the `.so` is committed with its sha256 in the
  commit message and needs glibc 2.29 at most. No decoder device in `/dev` means software decoding, never a crash.
- **The same add-on on Windows** (`scripts/build_gozen.sh windows`, a MinGW-w64 cross build in Docker): one
  static DLL with FFmpeg's Direct3D 11 Video / DXVA2 decoding, nothing else to install, so `setup.py` only copies
  it (with the native video add-on beside it as the fallback). Details: the PuP Pack agent, section 6.
- **Session:** X11 (Godot places one window per monitor only there), autologin, no screen blanking (`run.py` runs
  `xset s off -dpms`). openbox without a display manager works.
- **Sound:** the Xavier NX devkit's ALSA default is an I2S card with nothing on it; the hwdec install writes a
  `~/.asoundrc` to HDMI through dmix when there is no PulseAudio or PipeWire.
- **Power mode:** `sudo nvpmodel -m 5` (10 W desktop, 4 cores at 1.91 GHz) or 8 (20 W). Per-core speed matters more
  than cores; the 2- and 4-core 10 W modes are not playable. `jetson_clocks` gains nothing. Mode 5 is the only mode
  with the top CPU clock: the 15 W and 20 W 6-core modes run at 1.42 GHz, so a higher mode does not cure hitches on
  Godot's main thread (slide creation); fix those in software (improvement agent, section 2a). Tron's full game,
  2026-10-12: mode 5 56.9 FPS, 70 frames over 100 ms, 8.8 W; mode 8 56.9 FPS, 87 over 100 ms, 8.7 W (observed).
- **Screens in standby between runs:** `run.py` turns DPMS off for play, so the backlights stay on after it exits;
  put them to sleep with `xset +dpms; xset dpms force off`. On the Xavier NX (NVIDIA X driver, no desktop
  environment) a sleeping monitor loses its output's mode, and `xset dpms force on` does not bring it back: redo the
  session's `xrandr --auto` layout before the next run, or Godot sees one screen, stacks every window on it and
  runs at 39 FPS instead of 58 (observed, Tron, 2026-10-12: a lost one-hour soak).
- **Submodules on a board reused across sessions:** a session may have pointed a submodule at a local checkout
  (`git -C assets remote -v` shows a path); syncing then fails with `transport 'file' not allowed`. Fetch from the
  GitHub URL directly (`git -C assets fetch <url> main`, then check out `FETCH_HEAD`) instead of rewriting the
  remote, and copy a private submodule's content (a PuP Pack) from the old checkout when the board has no
  credentials for it (observed, Tron on the Xavier NX, 2026-10-12).
- **Screens:** the devkit's DisplayPort has no DP++ mode, so a passive DP to HDMI adapter never works (an active
  one does); the USB-C port has no video. A panel's EDID refresh rate cannot be overridden (`CustomEDID` is
  ignored). Cabinet placement goes in the untracked `game/pup.local.cfg`, never in the tracked defaults.
- **Setup steps that matter on ARM:** `setup.py` bakes the clean HD fonts' signed distance fields
  (`game/tools/bake_fonts.gd`, about 2 minutes on a Xavier NX; without it the first text froze the game 20 s and
  more) and `gen_media.py` imports the HD effect frames VRAM-compressed. Both rerun when their inputs change.
- **Run options**: `run.py --no-render-thread` / `TRON_RENDER_THREAD=0` (Godot's separate render thread is on by
  default on Godot 4.6.3, where it won with three videos; on Godot 4.5.2 with the DMD alone it lost, so retest it at
  every Godot upgrade), `TRON_PIN=0` (core pinning, Linux with 4+ cores), `TRON_PERF_DIR` (the performance probe; use
  `scripts/perf/run.sh`). Each new run option reaches `docker/entrypoint.py` and `docker/tron.env.example` too.
- **On the board by Remote Control:** the cabinet has no GitHub credentials, so the session there hands its changes
  back as `git format-patch` files in the project's shared files, and a cloud thread applies, checks and pushes
  them (observed, Tron on the AGX Orin).
- **Testing without the board:** an arm64 Ubuntu 20.04 root under qemu, posing as a Xavier NX with NVIDIA's r35.4
  apt packages, runs the whole Linux install and builds libnvmpi. When Docker Hub rate-limits, build the base
  image with `debootstrap focal` and `docker import`. Godot renders headless in the cloud with lavapipe
  (`VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json`, `--rendering-method mobile`, under `xvfb-run`). Tests
  that import MPF run on the board.

## 5d. Raspberry Pi 4 (and the next SoCs): what to check before promising a frame rate

Tron tested on a Pi 4B, Debian 13 (trixie), Raspberry Pi kernel 6.18, Mesa 25.0.7 (Mesa 26.2.2 from the Pi repository
gave the same times), Godot 4.6.3 on the Compatibility (OpenGL ES) renderer, GoZen for the PuP Pack's videos, a 1080p
backglass full screen, the classic 128x32 DMD in its own window (2026-10-24; findings also in issue #44). The Tron
numbers are in the game repository (`docs/pup/README.md`, "Raspberry Pi 4"); this is the method and what applies to
any SAM game or any new board (a Pi 5, an Orange Pi, another Jetson). All observed on the machine unless said.

**A. Check these first, in this order, before profiling the game**

1. **Which renderer and which thread mode really run.** The Pi 4 needs `--rendering-driver opengl3` (Vulkan is not a freeze but 1 fps:
   V3DV uploads each copied video plane with a render pass that allocates and zeroes a fresh tile-state buffer, about
   2 s a frame with 1080p planes; stack `texture_2d_update` > `vkCmdCopyBufferToImage` > `copy_buffer_to_image_shader`
   > `v3dv_job_allocate_tile_state`. A bare Godot 1080p scene does 74.8 fps in Vulkan against 39 in OpenGL, so only
   video uploads are the problem. The separate render thread under Vulkan crashed after 5 s: a game script touched
   the scene tree from that thread. V3DV exposes `VK_EXT_external_memory_dma_buf`, but a zero-copy import needs a
   GDExtension doing the import and a TFU copy to a tiled image: not built). Tron's `run.py` added `--render-thread safe` whenever `opengl3` was asked (a workaround for
   the captures under Xvfb), so the Pi ran with the separate render thread off while `project.godot` said on and
   Jetson docs said "on by default". Ask the engine (`RenderingServer.is_on_render_thread()`), never the setting
   (a command-line `--render-thread` overrides `project.godot`'s `thread_model`). It cannot be turned on there: Godot 4.6.3
   with `--render-thread separate` and opengl3 crashes at start ("Error initializing GLAD", SIGSEGV; the GL ES context
   is not created on the render thread), so the main thread stays the limit. The same applies to a launcher's
   window mode: test fullscreen against windowed.
2. **Fullscreen or not.** A windowed Godot on X is copied by X every frame (a Pi 4: +7 ms TFU and +10 ms render at
   1080p; an empty scene 45 fps windowed, 60 fps with `--fullscreen`, which page flips).
3. **The cost of a full-window layer, with the default 2D shader.** Measure an empty scene, then a `ColorRect`,
   then N layers. On the Pi 4 (V3D, 8 QPU at 500 MHz, about 16 G instructions a second) Godot's default canvas
   shader is 118 instructions a pixel, so about 136 Mpixel/s: 10-14 ms for one 1080p layer, +10 ms for each more.
   `render_mode unshaded` and a branch-free YUV shader (32 instructions) cut that 4 times. Blending is free
   (opaque and transparent `ColorRect` cost the same); textures and bandwidth were not the limit. Use
   `V3D_DEBUG=shaderdb` (instructions, threads, spills) and `/sys/devices/platform/v3dbus/fec00000.v3d/gpu_stats`.
   A full-window `ColorRect` for a black background costs 3 to 6 fps: use `RenderingServer.set_default_clear_color`.
4. **Videos: layers hidden under an opaque video should neither be drawn nor decoded** (a silent one pauses until
   uncovered). The Pi 4's hardware decoder slows the GPU by 15 to 30 %, software decoding in parallel does not.
5. **A heavy background in a SubViewport** (Tron's DMD light cycles: 3D with glow, about 13 passes a frame) cost
   27 ms a frame on the Pi 4 and half of the frame rate; turning it off (or the classic 128x32 DMD) is the largest
   single gain. Count the render passes a frame before blaming the video.
6. **GPU frequency was not the limit once the shaders were light**: an overclock to 600 MHz (no extra voltage)
   gave nothing, because the main thread became the limit. Overclocking is the last step, and needs the owner.

**B. The V4L2 stateful decoder (`bcm2835-codec`, `/dev/video10`, FFmpeg `h264_v4l2m2m`)**

- `avcodec_flush_buffers()` leaves it answering EOF to every later request (a looping video stops): restart in
  place (`VIDIOC_STREAMOFF`/`STREAMON` on both queues, as the stateful decoder interface defines a seek) or recreate
  the decoder. `pkt_timebase` and `time_base` must be set. Capture buffers are YU12 or NV12, 1920x1088 for 1080p.
- The capture buffers are **uncached** mappings: reading a 1080p frame costs 10-15 ms (1.3 ms from normal memory),
  and NEON does not help (25 %). So copying frames to Godot's textures is the bottleneck, not decoding.
- **Zero-copy** (validated: 54 fps and 1.1 ms CPU a frame in a C prototype; Godot's CPU 160 % -> 93 %, video lag
  4.4 s -> 0.9 s in the game): `VIDIOC_EXPBUF` (dmabuf per capture buffer, once) -> `EGL_EXT_image_dma_buf_import`
  per plane (R8 for Y, U and V with their offsets and pitches; GR88 for NV12's UV) -> `glEGLImageTargetTexture2DOES`
  -> `RenderingServer.texture_create_from_native_handle` -> the existing YUV shader. FFmpeg 7.1 has no drm_prime
  output for `v4l2m2m`: find the buffer from `frame->buf[0]` (opaque is FFmpeg's internal `V4L2Buffer`), so FFmpeg's
  source tree must stay configured next to GoZen. The GL calls must run on the render thread. Keep the software
  fallback, hold decoded frames until a few frames after they were shown, and skip late frames instead of slipping
  the clock.
- **Mesa v3d cannot sample a linear dmabuf texture**: it copies the plane to a tiled shadow on the TFU at every
  draw (`V3D_DEBUG=perf`: "Updating WxH@0 shadow for linear texture", `v3d_update_shadow_texture`): about 1.6 ms a
  1080p plane, 12 ms a frame for two 1080p videos. Converting once per decoded frame does not help while the game
  shows fewer frames than the video has. Re-encoding the videos to 720p cuts it 4 to 6 times but the owner may
  refuse to touch the pack; `Window.content_scale_size` (a lower render size, videos untouched) is the other lever
  (1280x720: +38 % fps).
- Pi sound and screens, found on the way: the 3.5 mm jack card is missing on trixie (`snd_bcm2835.enable_headphones=0`
  in the DTB bootargs: append `snd_bcm2835.enable_headphones=1` to `cmdline.txt`); a screen that sends no EDID and is
  forced with `video=HDMI-A-n:1920x1080@60D` gets no HDMI audio (vc4 treats it as DVI): give it an EDID with a CEA
  block (audio, LPCM, HDMI VSDB) through `drm.edid_firmware=HDMI-A-n:edid/<file>.bin`; without PipeWire ALSA
  `default` is card 0 (often an HDMI port with nothing), Godot then uses its Dummy driver: write `/etc/asound.conf`
  (`plug` to `hw:Headphones`; dmix on the jack stalls); X can keep an unplugged HDMI output as the primary at 0,0
  (turn it off in `~/.xinitrc` with `xrandr`).
- **Remote Control on the board:** a `claude remote-control` session started by a service from the home directory
  asks for folder trust at every start: start it from a dedicated folder (`~/claude-rc`) and answer once. Builds do
  not belong on the board (FFmpeg and godot-cpp took about 45 minutes with the game stopped): cross-build in
  Docker or on a build machine and hand the library over through a throwaway git branch the board clones.

**Open:** `tools/pup/runtime/` (the runtime other games copy) does not have these changes yet: the fast YUV shader,
covered layers neither drawn nor decoded, no full-window `ColorRect`, `render_size`, and the zero-copy patch of GoZen
(Tron: `scripts/gozen/gozen_zerocopy.patch`, `pup_addons/gde_gozen/video_playback.gd`, `game/pup/`).

**C. Measuring (any new board)**: compare at the same frame rate and report the video lag (median and the 95th
percentile) and the frames over 50 ms, not CPU percent alone (a lower CPU at a lower frame rate proves nothing);
three runs per variant, because random video picks move the frame rate by 15 %; stop the game and any build while
measuring; the GPU's queue time (`gpu_stats`), ALSA underruns and `vcgencmd get_throttled` go in every row.

## 6. Status and open work per game

On each game's page (Tron: [Tron-Legacy-MPF `docs/agents/README.md`](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md), "F, packaging").

Keep this file current with every installer change and owner test. Last updated 2026-10-24 (Raspberry Pi 4: section 5d, the checks before promising a frame rate, the V4L2 decoder and zero-copy, Mesa v3d, sound and screens; before 2026-10-22: macOS CI: no system git config in the token test; the game-agnostic kit in MPF-Godot-Packaging; Xavier NX power modes and hitches, submodules on a reused board; before 2026-10-10: untracked Godot .uid files before the update's pull; PuP fork merged into Tron's game repo; the full README in the definition of done; optional private pack repository; main as default branch; GoZen on Windows; token paste on Windows, tags from cloud sessions, patches from the board; Jetson doc paths;
before: moved to Stern-SAM-Decryption; Tron status to the Tron game page; PuP Pack zip option).
