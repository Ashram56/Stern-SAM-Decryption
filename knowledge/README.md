# Knowledge base: rebuilding a Stern SAM game in MPF

The master plan is [../agents/README.md](../agents/README.md): what the owner provides, and the agents (ROM
extraction, VPX extraction, strict recreation, VPX bridge, improvements, packaging) with their instructions.
The files below are the reference docs those agents read. Each is short, dense and self-contained: read only
the one your task needs. The biggest body of SAM knowledge, how to take a ROM apart, is the ROM extraction
agent itself: [../agents/rom_extraction.md](../agents/rom_extraction.md).

| File | Read it when | Size |
|---|---|---|
| [sam_to_mpf_playbook.md](sam_to_mpf_playbook.md) | You build or maintain an MPF recreation of **any** Stern SAM game from ROM-derived specs. Architecture, build order, verification loop and every gotcha that cost real time. Game agnostic; Tron is only the worked example. | ~15 min |
| [dmd_hd_upscaling.md](dmd_hd_upscaling.md) | You work on the optional HD display (128x32 DMD drawn at any window size). Separate from the rules work on purpose. | ~5 min |
| [rom_decomp_feedback.md](rom_decomp_feedback.md) | You are the ROM extraction agent, or brief one. What the Tron MPF build consumed, what was missing or wrong, and what to deliver for the next game (now folded into the ROM extraction agent's section 14). | ~8 min |

What stays in each game's repositories, not here: the game's own facts (addresses, status, open work, owner
decisions, departures from the ROM, player docs). For Tron: the
[Tron game page](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md), which also lists
where the Tron instance lives.

## Token rules for an agent taking over a game

1. Read this README, then one doc above. Do not read the whole game repo: every doc names the exact file to open.
2. Grep the specs, never read them whole. Spec files are long; the rules you need are a section.
3. Trust the code's module docstrings: each `game/<game>/*.py` and `scripts/*.py` opens with what it models
   and which ROM addresses it follows. `sed -n '1,/^"""$/p' FILE` reads only that.
4. Commit messages carry the "why" of each fix: `git log --no-merges --format='%h %s%n%b'` (about 33 KB
   for the whole Tron build) is cheaper than rediscovering a bug.
5. Run the checks instead of reasoning about them: `pytest -q tests` and `scripts/trace_check.py <scenario>`
   answer "does it match the ROM" faster than reading the trace.

Last updated 2026-10-10 (moved here from Tron-Legacy-MPF `docs/handover/`).
