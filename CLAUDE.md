# Stern SAM decryption: instructions for Claude

This repository holds the game-agnostic agents and knowledge base for taking a Stern SAM (also WPC / Whitestar) ROM and its
Visual Pinball X table apart: agent A (ROM extraction, Ghidra decompile, traces, functional diagram) and agent B (VPX extraction).
Start from the master plan below: it says which agent file covers the task at hand. Read only that agent file and the knowledge
docs it names; update it in the same session when you learn something it should say.
The MPF implementation (agents C to G: strict recreation, VPX bridge, improvements, packaging, PuP Pack; Godot / GoZen / GMC / MPF /
platform and board findings) belongs in Ashram56/MPF-Godot-Packaging, not here (CONTRIBUTING.md). Game facts belong in that game's
repositories, not here. Every game-agnostic learning comes back here in the same session, without asking the user: a PR with write
access, otherwise a GitHub issue (CONTRIBUTING.md).

@agents/README.md
