# Stern SAM Decryption: from a pinball ROM and a VPX table to the decoded game

Game-agnostic agents, knowledge base and tools for **taking a Stern SAM pinball ROM apart** (and, by adaptation, a 6809
Williams WPC or Stern Whitestar one) and a Visual Pinball X table with it: the Ghidra decompile, the reference traces, the
functional diagram taken from the code, the IO and rules tables, the media, the table's MPF Monitor layout. Every file here
was learned on a real game; **Tron Legacy LE 1.74** is the worked example throughout.

**Since 2026-11-23 the master plan has two halves, one repository each.** This repository is the **decryption** half
(agents A and B). The **MPF implementation** half (agents C to G: strict recreation, VPX bridge, improvements, packaging,
PuP Pack, with the playbook and the MPF, Godot and GMC knowledge) is in
[MPF-Godot-Packaging](https://github.com/Ashram56/MPF-Godot-Packaging) ([its plan](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/agents/README.md)).

**Start with the [master plan](agents/README.md).** It says what the owner provides (the ROM, optionally a
Visual Pinball X table), which agents run in which order across both repositories, and how to start them from one message in a Claude
project.

| Folder | What it holds |
|---|---|
| [`agents/`](agents/README.md) | The master plan, and the agents of this half: A [ROM extraction](agents/rom_extraction.md), B [VPX extraction](agents/vpx_extraction.md). C to G live in MPF-Godot-Packaging: [strict recreation](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/agents/recreation.md), [VPX bridge](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/agents/vpx_bridge.md), [improvements](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/agents/improvement.md), [packaging](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/agents/packaging.md), [PuP Pack](https://github.com/Ashram56/MPF-Godot-Packaging/blob/main/agents/pup_pack.md) |
| [`knowledge/`](knowledge/README.md) | The reference docs of the decryption: the SAM boards' bus and interfaces, the SAM OS API, 6809 / WPC notes, the DMD display-effect engine rules, rules spec templates, what a recreation needs from a ROM extraction. The MPF-side docs (playbook, HD DMD, PuP Pack format, MPF quirks) are in MPF-Godot-Packaging `knowledge/` |
| [`tools/rom/`](tools/rom/README.md) | The ROM extraction toolkit from Tron: PinMAME hooks and trace recorder, Ghidra pipeline, table and media extractors, bus tracer |
| [`tools/vpx/`](tools/vpx) | `vpx_extract.py` and `vpx_map.py`: a `.vpx` table to an MPF Monitor layout (`pip install olefile pillow`) |
| `tests/` | `python -m pytest -q tests` |

**What is not here**: no ROM, nothing extracted from a ROM, and nothing about one game only. Each game keeps
its own repositories (an asset/spec repo from agent A, a game repo from agents C to G) with a game page that
links them to these agents. Tron: [Tron-Legacy-LE-ROM-Decryption](https://github.com/Ashram56/Tron-Legacy-LE-ROM-Decryption)
and [Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF) (game page:
[`docs/agents/README.md`](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md)).

**Feed it back.** Every agent that uses this repository, on any game, reports what it learns that a later game
would need (a method, a fact about SAM or about taking a ROM or a table apart, a mistake and its fix; MPF, Godot and GMC findings go to MPF-Godot-Packaging) in the same session, without being
asked: a pull request if it has write access here, otherwise a GitHub issue opened directly. See
[CONTRIBUTING.md](CONTRIBUTING.md).
