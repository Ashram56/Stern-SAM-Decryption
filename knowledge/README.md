# Knowledge base: taking a Stern SAM game apart

The master plan is [../agents/README.md](../agents/README.md): what the owner provides, and the agents with their instructions. This
repository is the **decryption** half (ROM extraction, VPX extraction); the MPF implementation half, with its own knowledge
([the SAM to MPF playbook](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/knowledge/sam_to_mpf_playbook.md), [MPF's own quirks](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/knowledge/mpf.md), the
[HD DMD method](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/knowledge/dmd_hd_upscaling.md), [DMD conformance](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/knowledge/dmd_conformance.md), the
[PuP Pack format](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/knowledge/pup_pack_format.md)), is in [MPF-Godot-Packaging](https://github.com/Ashram56/MPF-Godot-Packaging).
The files below are the reference docs agents A and B read. Each is short, dense and self-contained: read only
the one your task needs. The biggest body of SAM knowledge, how to take a ROM apart, is the ROM extraction
agent itself: [../agents/rom_extraction.md](../agents/rom_extraction.md).

| File | Read it when | Size |
|---|---|---|
| [sam_hardware/](sam_hardware/README.md) | You need the SAM CPU to IO board bus, its timing, the lamp matrix, or any interface the CPU board drives (DMD, sound, switches, timers): same boards on every SAM game, measured with the Tron ROM. CSVs beside it. | ~15 min |
| [sam_os_api.json](sam_os_api.json) | You name OS functions in a new ROM's decompile: 160 SAM OS functions with signatures, meaning and evidence (Tron LE 1.74 addresses; find each again with the ROM extraction agent's section 5.1). | grep it |
| [dmd_deff_engine_rules.md](dmd_deff_engine_rules.md) | You read the SAM display-effect engine from the ROM (what is the engine, what is the game) instead of fitting it to captures. | ~4 min |
| [wpc_6809.md](wpc_6809.md) | You apply the method to a 6809 game (Williams WPC; Whitestar similar): memory map, far calls and inline-argument wrappers, the OS registry, emulator gotchas, effect and sound injection. Measured on Terminator 2 L-8. | ~5 min |
| [repo_layout.md](repo_layout.md) | You start or tidy a decoding repository: the standard tree (docs, ghidra, listings, rom_data, traces, dmd, sounds, vpx, tools, game), where each agent writes, the gaps of the existing repositories, and the layout check. | ~5 min |
| [dmd_animation_durations.md](dmd_animation_durations.md) | You state how long each DMD animation lasts: the one method (hooked run of the effect's own code, cross-checked by a static tick sum), the tick, the `rom_data/dmd_durations.csv` format and its check. | ~4 min |
| [templates/](templates) | You write rules specs: one-file-per-feature template and the brief given to the Tron rules workers. | ~3 min |
| [../tools/rom/](../tools/rom/README.md) | You extract a ROM: the Tron toolkit (emulator trace, Ghidra pipeline, table extractors, media exporters, bus tracer) and how to retarget it. | ~3 min |
| [rom_decomp_feedback.md](rom_decomp_feedback.md) | You are the ROM extraction agent, or brief one. Dated record of what the Tron MPF build had to recover or guess, and the package defects it found. The instructions (what worked, what to deliver) are the ROM extraction agent's section 14. | ~4 min |

New learnings come back here as [CONTRIBUTING.md](../CONTRIBUTING.md) says (a PR with write access, otherwise an
issue). What stays in each game's repositories, not here: the game's own facts (addresses, status, open work, owner
decisions, departures from the ROM, player docs). For Tron: the
[Tron game page](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md), which also lists
where the Tron instance lives.

[stern_pre_sam_rom_sets.md](stern_pre_sam_rom_sets.md): what a non-SAM Stern set (Lord of the Rings, 6809 + ARM
bios, 8 files) looks like and why the SAM tools do not apply as is.

## Token rules for an agent taking over a game

1. Read this README, then one doc above. Do not read the whole game repo: every doc names the exact file to open.
2. Grep the specs, never read them whole. Spec files are long; the rules you need are a section.
3. Trust the code's module docstrings: each `game/<game>/*.py` and `scripts/*.py` opens with what it models
   and which ROM addresses it follows. `sed -n '1,/^"""$/p' FILE` reads only that.
4. Commit messages carry the "why" of each fix: `git log --no-merges --format='%h %s%n%b'` (about 33 KB
   for the whole Tron build) is cheaper than rediscovering a bug.
5. Run the checks instead of reasoning about them: `pytest -q tests` and `scripts/trace_check.py <scenario>`
   answer "does it match the ROM" faster than reading the trace.

Last updated 2026-11-23 (MPF-side docs moved to MPF-Godot-Packaging; earlier 2026-11-21: WPC / 6809 page added; earlier: moved here from Tron-Legacy-MPF `docs/handover/`, PuP Pack format).
