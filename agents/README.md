# Master plan: from a Stern SAM ROM to an MPF game

**Read this first.** It says what you (the owner) provide, which agents turn it into a playable MPF game, in
what order, and where each agent's instructions live. It is game agnostic: Tron Legacy LE 1.74 is the worked
example throughout, and every agent file names the Tron result to copy from.

**Where things live.** This repository, [Stern-SAM-Decryption](https://github.com/Ashram56/Stern-SAM-Decryption),
holds what every game shares: the agents (`agents/`), the knowledge base they read (`knowledge/`) and the
game-agnostic tools (`tools/`). Each game's repositories keep only that game's facts: its result, its status
and open work, its owner decisions, and one **game page** that links them to these agents (Tron:
[Tron-Legacy-MPF `docs/agents/README.md`](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md)). Links to Tron files
below point into the Tron repositories; they are the worked example, not part of the method.

> **Have a Visual Pinball X table of the game? Run the [VPX extraction agent](vpx_extraction.md) early.**
> From the `.vpx` alone it gives MPF Monitor a real playfield picture with every switch, lamp and flasher
> placed on it (`monitor.yaml`), plus the table script the VPX bridge needs. Two commands, a few seconds:
> `python tools/vpx/vpx_extract.py TABLE.vpx OUT` then `python tools/vpx/vpx_map.py OUT --names <MPF config files>`
> (tools in this repository).
> Without it, MPF Monitor only has a labelled grid. On Tron it placed 44 switches, 64 lamps and 8 flashers.

## 0. Getting started (once)

The agents are Markdown files in public repositories: there is nothing to install or copy. Claude reads them
when a repository is attached or when you point it at them.

1. **GitHub.** For a new game, create two empty repositories of your own, one for the extraction and one for
   the game, plus a private one if third-party media will be involved. The agents' instructions and the
   knowledge base stay in this repository and are read from here. For Tron the repositories exist:
   [Tron-Legacy-LE-ROM-Decryption](https://github.com/Ashram56/Tron-Legacy-LE-ROM-Decryption) (ROM extraction)
   and [Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF) (game).
2. **Connect Claude to GitHub** at [claude.ai/connect-github](https://claude.ai/connect-github) and install the
   Claude GitHub App on your repositories when asked.
3. **Create a Claude project** (claude.ai, Projects) and add your repositories to it in the project settings,
   plus `Ashram56/Stern-SAM-Decryption` (this one), so every thread can read the agents and update them.
4. **Point the project at this plan.** Paste into the project's instructions, as is (it is the same for every
   game; nothing about your game goes here):
   > Before any work, read agents/README.md in Ashram56/Stern-SAM-Decryption (the master plan). The
   > coordinator runs the plan: it takes the game details and input files from the owner's kickoff message,
   > starts one thread per agent in the order of section 3, briefs each with its agent file and the inputs it
   > needs, starts the next agent when the previous one has delivered what it needs, and brings back to the
   > project chat only what needs the owner. Every thread follows its agent file and updates it whenever it
   > learns something the file should say: method in Stern-SAM-Decryption, game facts in the game's repos.
5. **Start the plan with one message in the project chat**, with your inputs (section 1) attached as files:
   > Run the master plan.
   > Game: `<game, model, version>`. ROM: `<set name(s)>`. VPX table: `<table name, author, version>`.
   > Extraction repo: `<owner/repo>`. Game repo: `<owner/repo>`. Private repo: `<owner/repo, if any>`.
   > Hardware: `<desktop, VPX, P-ROC, ...>`.

   Attach the ROM zip(s) and the `.vpx` to that message. A file too big to attach (a `.vpx` can be
   150-300 MB) goes in the project's files or as a download link instead; say which in the message. The
   project's coordinator (the Claude that answers in the project chat) then starts each agent's thread
   itself, in order, and you only answer the questions it or the threads bring you. You never brief an
   agent yourself.

Working in Claude Code on your own computer instead: clone this repository next to the game's repositories and
run `claude` in one of them. This repository's `CLAUDE.md` loads this plan; a game repository's `CLAUDE.md`
loads its game page, which sends Claude here for the agent (Tron: `../Stern-SAM-Decryption` if cloned beside it,
else read from GitHub). The same holds in a cloud session that has the repositories attached.

## 1. What you provide

| Input | Needed for | Required? | How to hand it over |
|---|---|---|---|
| **The game ROM**, one per model (Pro, Premium, LE): the PinMAME set zip, e.g. `trn_174h.zip` (LE 1.74), `trn_17402.zip` (Pro 1.74) | Everything: rules, sounds, DMD, lamp shows, settings, coil timing | **Yes** | Attach it to the kickoff message (section 0, step 5), or give a download link. It is copyrighted: it is never committed to any repository. Say which version and model it is if you know. |
| **The VPX table** (`.vpx`) of the same game | MPF Monitor layout and playfield picture; playing the game in VPX with MPF instead of PinMAME | Recommended | Attach it to the kickoff message; tables are 150-300 MB, so if it is too big, put it in the project's files (Tron: `Tron Legacy (Stern 2011) VPW Mod v1.1.vpx`), give a download link, or let an agent work on your PC through Remote Control. Say which table it is (author, version) and which model it simulates. |
| Your target hardware | Which overlays to build, and which installers and run options F ships: desktop only, VPX, a P-ROC on the original boards, other | Yes (one line) | In the kickoff message. Tron: P-ROC on the SAM boards, Pro by default, LE selectable; VPX on Windows. |
| GitHub repositories | Where the agents write | Yes | Named in the kickoff message. One for the ROM extraction (asset/spec repo), one for the game. Private work (third-party colourisation) goes in a separate private repo. Connect GitHub to Claude once. |
| A Windows PC with VPX | Testing the VPX bridge and the Windows installer (VPX runs only on Windows) | For the bridge | Run the checks the bridge and packaging agents list, or allow Remote Control on a folder. |
| Optional: operator manual, switch/lamp matrix | Cross-checking IO numbers | No | Attach the PDF to the kickoff message or a later one. |
| Optional: schematics, logic analyzer captures | Hardware work (P-ROC, replacement boards) | No | Attach them; say which ROM the machine ran when captured. |
| Optional: third-party media (videos, colourisation files) | Improvements only | No | Private repo only; never named or described in the public game repo. |
| Your decisions | Model, defaults, look and feel | As they come up | Agents pick sensible defaults, say which, and ask only for what they cannot decide. |

## 2. The agents

| # | Agent | Instructions | Input | Output |
|---|---|---|---|---|
| A | **ROM extraction** | [rom_extraction.md](rom_extraction.md) | ROM image(s) | The asset/spec repo: rules specs, reference traces, decompile, MPF package (config, sounds, DMD frames, shows), `rom_data/` tables |
| B | **VPX extraction** (MPF Monitor) | [vpx_extraction.md](vpx_extraction.md) | `.vpx` table (+ A's MPF config for names) | `playfield.png`, `monitor.yaml`, switch/lamp/flasher CSVs with numbers and positions, `script.vbs`, overlay to check by eye |
| C | **Strict recreation** | [recreation.md](recreation.md) | A's repo (as a submodule), B's layout | The game repo: the ROM's game exactly (rules, display, sound, lamps, service menu, settings, audits, credits, hardware overlays), checked against A's traces |
| D | **VPX bridge** (work in progress) | [vpx_bridge.md](vpx_bridge.md) | C's game, B's table script | VPX plays the ball, MPF replaces PinMAME and the ROM |
| E | **Improvements** (optional) | [improvement.md](improvement.md) | C's game | Switchable departures: HD DMD, clean fonts, colour, new modes; the ROM's behaviour stays one option away |
| F | **Packaging** | [packaging.md](packaging.md) | C's game repo, the owner's hardware line, D's and E's options | One line to install and one command to run on Windows, macOS and Linux (installers, `setup.py`, `run.py`, toolchain pins, Docker, CI), with every hardware option (MPF Monitor, P-ROC, VPX) |

The knowledge base the agents share (not agents themselves), in [`knowledge/`](../knowledge/README.md):
[sam_to_mpf_playbook.md](../knowledge/sam_to_mpf_playbook.md) (how C builds),
[dmd_hd_upscaling.md](../knowledge/dmd_hd_upscaling.md) (how E's HD display works),
[rom_decomp_feedback.md](../knowledge/rom_decomp_feedback.md) (what C needed from A). Per game, in the game
repo: `docs/rom_differences.md` (every departure from the ROM; Tron: [rom_differences.md](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/rom_differences.md))
and the players' set-up pages (Tron: [vpx.md](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/vpx.md)).

## 3. Order

```
ROM ──► A ROM extraction ──► C strict recreation ──► E improvements (optional)
                                   ▲        │  │
.vpx ─► B VPX extraction ──────────┘        │  └──► D VPX bridge ◄── B's table script
                                            └─────► F packaging ◄── D's and E's options
```

1. **A and B in parallel.** They need nothing from each other; B only borrows A's MPF config for device names
   (without it B writes placeholder names that carry the numbers, which C renames).
2. **C** starts when A has delivered the IO tables, sounds and DMD frames; rules features follow A's specs
   and traces mode by mode. C feeds missing-data requests back to A (Tron: [rom_decomp_feedback.md](../knowledge/rom_decomp_feedback.md)).
3. **F** as soon as C's repo boots MPF + GMC (C's toolchain step): it ports the whole install and run kit at
   once, so the owner can install and test from the first playable build. F runs again whenever C, D or E add
   an option (P-ROC, VPX set-up, display modes), so each one reaches every installer and platform.
4. **D** once C boots a game on virtual hardware. **E** any time after C's display works, always switchable.
5. Every new ROM version or model: A again (A's section 15 ports a second model), then C's asset sync.

## 4. Starting the agents

In a Claude project the coordinator starts them (section 0, step 5): one thread per agent, A and B in
parallel, then C, then F, D and E. To run only one agent, ask the coordinator for it by name ("run the VPX
extraction agent on the new table"). Outside a project (a single Claude Code session), start the agent
yourself with its line:

Each line means the file in `agents/` of Ashram56/Stern-SAM-Decryption.

| Agent | Message |
|---|---|
| A | "Act as the ROM extraction agent (agents/rom_extraction.md in Ashram56/Stern-SAM-Decryption) on the attached ROM `<set name>`; write into `<asset repo>`." |
| B | "Act as the VPX extraction agent (agents/vpx_extraction.md) on `<table.vpx>`; names from `<asset repo>`'s MPF config; deliver into `<game repo>`." |
| C | "Act as the strict recreation agent (agents/recreation.md) for `<game>` in `<game repo>` from `<asset repo>`." |
| D | "Act as the VPX bridge agent (agents/vpx_bridge.md) for `<game repo>`; the table is `<table.vpx>`." |
| E | "Act as the improvement agent (agents/improvement.md) for `<game repo>`: `<what to improve>`." |
| F | "Act as the packaging agent (agents/packaging.md) for `<game repo>`: one-line install and run on `<platforms>`, with `<options: MPF Monitor, P-ROC, VPX>`." |

## 5. Rules every agent follows

- **Keep these docs current.** When a thread learns something that changes how a later agent would work (a
  method, a fact, a mistake and its fix, an owner decision), fold it in, in the same session, with a PR here:
  ROM methods in rom_extraction.md, build facts in the playbook or recreation.md, install and run facts in
  packaging.md, VPX facts in vpx_extraction.md or vpx_bridge.md, look-and-feel methods in improvement.md.
  Facts true of one game only (its status, open work, owner decisions, addresses, run values) go in that
  game's repositories, on its game page; a generic lesson learned on one game goes here, with that game's value
  as the example. Update the "Last updated" line.
- **Where a file goes**: this repository is public and game agnostic; never put a ROM, ROM-derived media, or
  anything private here.
- **Strict first, improvements second.** C reproduces the ROM; anything that differs is E's, is switchable,
  and gets a row in the game repo's `docs/rom_differences.md`.
- **Label facts**: observed (emulator or machine), code (decompile/table, with the ROM address), inferred.
- **Machine-readable first**: tables (CSV/JSON) that code reads, prose second.
- **Never commit the ROM**, and never name or describe third-party colourisation or media work in a public
  repo beyond a pointer to the private repo.
- **Test locally before pushing.** CI on the game repo runs only on pushes to `main`; don't wait on it for a
  branch. Run `pytest -q tests` (and the trace and render checks for rules or display work).
- **Owner preferences (Ashram56's games, Tron first):** go ahead without asking for approval; pick a default, say which, and list what
  needs the owner's judgement as a short numbered list. Small update zips of changed files only, never a full
  rebuild (A). Answer in the owner's language (Vincent sometimes writes in French).

## 6. Games using this plan

| Game | Asset repo (A) | Game repo (C, D, E, F) | Game page |
|---|---|---|---|
| Tron Legacy LE 1.74 / Pro 1.74 (worked example) | [Tron-Legacy-LE-ROM-Decryption](https://github.com/Ashram56/Tron-Legacy-LE-ROM-Decryption) | [Tron-Legacy-MPF](https://github.com/Ashram56/Tron-Legacy-MPF) | [docs/agents/README.md](https://github.com/Ashram56/Tron-Legacy-MPF/blob/main/docs/agents/README.md) |

Add a row when a new game starts. Last updated 2026-10-10 (moved here from Tron-Legacy-MPF with the knowledge
base and the ROM extraction agent).
