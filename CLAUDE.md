# Stern SAM decryption: instructions for Claude

> **STRICT RULE: DECOMPILE EVERYTHING (owner, 2026-11-24), and working rules 6-7 (owner, 2026-11-24). Binding on every agent, every game.**
> 1. Agent A decompiles **all**: the main ROM **and the firmware of every independent board** (any board with its own CPU, MCU, ROM or firmware: DMD, sound, others).
> 2. **Step zero, before anything else**: `docs/boards_inventory.md` lists every such board (board, CPU, ROM, decompile state `complet` / `partiel` / `absent`). A board that is not `complet` blocks the rules that depend on it.
> 3. The decompiled code is the source of every rule, value and behaviour, with the **ROM address cited**. It must cover scores, displays, inserts, coils and sounds. Every datum sent that is not understood is traced in the code (destination, function).
> 4. **Never code from an emulator capture** (PinMAME frames, renders, traces), images and DMD renders included. Last resort only, after a dead end, and **ask Vincent first**; record it in `docs/pinmame_waivers.md`.
> 5. Agent C codes nothing until A has delivered the **visual diagram taken from the code, one ROM address per node** (`docs/functional_diagram.md` or `docs/flow/`).
> 6. **Never end a turn by announcing "I continue" or "next step".** A finished turn stops the work. Chain on while doable work remains; stop only when everything is done, or on a blocker, which you name (what, and what you need).
> 7. **Post a factual progress report at least every 15 minutes** (done, running, blocked). The coordinator checks every active session every 15 minutes; a session that shows no progress is chased.
> 8. Enforced by `python tools/check_strict_rule.py .` (canonical copy: `tools/strict_rule/` in Stern-SAM-Decryption). Run it before every push; it must pass.

This repository holds the game-agnostic agents and knowledge base for taking a Stern SAM (also WPC / Whitestar) ROM and its
Visual Pinball X table apart: agent A (ROM extraction, Ghidra decompile, traces, functional diagram) and agent B (VPX extraction).
Start from the master plan below: it says which agent file covers the task at hand. Read only that agent file and the knowledge
docs it names; update it in the same session when you learn something it should say.
The MPF implementation (agents C to G: strict recreation, VPX bridge, improvements, packaging, PuP Pack; Godot / GoZen / GMC / MPF /
platform and board findings) belongs in Ashram56/MPF-Godot-Packaging, not here (CONTRIBUTING.md). Game facts belong in that game's
repositories, not here. Every game-agnostic learning comes back here in the same session, without asking the user: a PR with write
access, otherwise a GitHub issue (CONTRIBUTING.md).

**Layout of a decoding repository:** [knowledge/repo_layout.md](knowledge/repo_layout.md) (standard tree, where each agent writes; checked by `check_strict_rule.py`, `--layout-strict` on a new game repository).

@agents/README.md
