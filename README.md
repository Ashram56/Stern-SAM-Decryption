# Stern SAM Decryption: from a SAM pinball ROM to an MPF game

Game-agnostic agents, knowledge base and tools for taking a **Stern SAM** pinball ROM apart and rebuilding the
game in the [Mission Pinball Framework](https://missionpinball.org) (MPF) with Godot (GMC). Every file here was
learned on a real game; **Tron Legacy LE 1.74** is the worked example throughout.

**Start with the [master plan](agents/README.md).** It says what the owner provides (the ROM, optionally a
Visual Pinball X table), which agents run in which order, and how to start them from one message in a Claude
project.

| Folder | What it holds |
|---|---|
| [`agents/`](agents/README.md) | One Markdown file per agent: A [ROM extraction](agents/rom_extraction.md), B [VPX extraction](agents/vpx_extraction.md), C [strict recreation](agents/recreation.md), D [VPX bridge](agents/vpx_bridge.md), E [improvements](agents/improvement.md), F [packaging](agents/packaging.md) |
| [`knowledge/`](knowledge/README.md) | The reference docs the agents share: the SAM to MPF playbook, the HD DMD method, what a recreation needs from a ROM extraction |
| [`tools/vpx/`](tools/vpx) | `vpx_extract.py` and `vpx_map.py`: a `.vpx` table to an MPF Monitor layout (`pip install olefile pillow`) |
| `tests/` | `python -m pytest -q tests` |

**What is not here**: no ROM, nothing extracted from a ROM, and nothing about one game only. Each game keeps
its own repositories (an asset/spec repo from agent A, a game repo from agents C to F) with a game page that
links them to these agents. Tron: [Tron-Legacy-LE-ROM-Decryption](https://github.com/Ashram56/Tron-Legacy-LE-ROM-Decryption)
and [Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF) (game page:
[`docs/agents/README.md`](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md)).

**Keep it current.** Any thread that learns something a later game would need (a method, a fact about SAM,
MPF or Godot, a mistake and its fix) folds it into the agent file or knowledge doc that owns it, with a PR here.
