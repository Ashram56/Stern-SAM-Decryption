# SAM OS signatures: naming the OS of a new ROM from the games already named

*Résumé (FR).* L'OS d'un jeu SAM (tâches, texte, bitmaps, audits, réglages, sons, bobines, mémoire...) est le même code d'un jeu à l'autre, mais à d'autres adresses. `sam_os_api.json` ne donne que des adresses Tron. Cette base retrouve les noms dans une nouvelle ROM sans adresse : par la structure du décompilé (couche A) et par des motifs d'octets masqués (couche B). Aucun octet de ROM ni texte décompilé n'est dans le dépôt : seulement des hashes. Les noms viennent du code (règle stricte) ; une correspondance est une proposition à relire, pas une preuve.

**Files.** `knowledge/sam_os_signatures.json` (layer A), `knowledge/sam_os_bytesigs.json` (layer B), tools in [`tools/rom/sam_os_sigs/`](../tools/rom/sam_os_sigs/) (`samsig.py`, `sam_os_sigs.py`, `bytesig.py`, `merge_seeds.py`), tests `tests/test_sam_os_sigs.py`. Names and signatures come from [`sam_os_api.json`](sam_os_api.json) and from the named exports of Tron LE 1.74, Tron Pro 1.74 and Transformers Pro 1.80 (sources in the `sources` field of the JSON).

## Use on a new SAM ROM (agent A, section 5.1 of the agent file)

1. Decompile the new ROM once with the usual seeds (no names), giving `export.c` (`// ==== <addr> <name>` headers).
2. `python3 tools/rom/sam_os_sigs/sam_os_sigs.py apply --db knowledge/sam_os_signatures.json --bytes-db knowledge/sam_os_bytesigs.json --rom NEW.bin --os-end 0x<OS end> --export export.c --out-names names.tsv --out-sigs sigs.tsv --report report.md` (leave out `--bytes-db/--rom` to use layer A alone).
3. Read `report.md` (address, name, how, score, status). Check the `weak` and `callee` rows and every name that has a `single` status in the database against the new decompile, then keep them. Where the new ROM's own evidence disagrees, the code wins (see the example below).
4. `python3 tools/rom/sam_os_sigs/merge_seeds.py seeds.tsv names.tsv seeds_named.tsv` and re-run the Ghidra setup (`STSetup.java` / `TronSetup.java` read `addr<TAB>name` seeds and `sigs.tsv`); the decompile now carries the OS names.
5. Name what remains by hand, then **add the new game to the database** (below) so the next ROM matches better.

## How it matches

**Layer A, structure** (needs only the Ghidra C). Per function: the body is reduced to a token stream with identifiers, variable names, types and large (address-like) numbers erased, small constants and control flow kept. Stored: SHA-1 of the stream (exact), a 64-value MinHash of its 4-token shingles (fuzzy), the small constants and the ordered callee names. Tiers: `exact` (hash identical and one name), `fuzzy` (mean best Jaccard over the games ≥ 0.75, second best 0.10 behind), `weak` (≥ 0.50, 0.25 ahead, ≥ 80 tokens), `callee` (an already matched function calls the same position in the reference: ordered call lists must have equal length, the target must not have been named otherwise). Functions under 8 tokens are never signed.

**Layer B, bytes** (needs the ROM). First 16, 32 and 64 bytes of each function, ARM words with B/BL offsets and `ldr rX,[pc,#imm]` immediates masked (same masks as `tools/rom/ghidra/pro/fmatch.py`), hashed with BLAKE2b-64. Longest window first; a hash shared by two names is ignored. Tests prove the relocation property on synthetic ARM; the database is hashes only.

**Combined.** `apply` runs both; when they name the same address differently the address is dropped (printed as `DISAGREE`); when they agree the row says `bytes+<tier>`.

**Status in the database.** `validated`: the name's body is the same function in at least two games (identical stream or all pairwise Jaccard ≥ 0.60); `single`: one game only; `partial` / `conflict`: the games' bodies differ (the name is used for related functions: `dmd_clear_work0/1`, `dmd_fill_work0`, `text_draw_str_page`); never trusted blindly. Per-game handler names (`sw16_start_button`, `leff_013`, `snd_play_009`, `task_2b`...) are not signed: they are the game, not the OS.

## Measured (2026-11-27)

Database: 206 OS names (`validated` 165, `single` 32, `partial` 5, `conflict` 4) from 3 exports, 1813 / 1525 / 1345 OS-region functions.

| Test | Result |
|---|---|
| Leave one game out, layer A (names compared with the held-out game's own names) | Transformers Pro 1.80 (db = Tron LE + Pro): 75 of 99 named OS functions found with the same name, 2 named differently (`bitmap_blit` and `bitmap_blit_masked` swapped: both are 100-line blitters with the same shape), 59 more names proposed. Tron LE (db = Pro + Transformers): 150 of 195, 1 different (`task_timer_start`/`task_timer_restart`). Tron Pro: 149 of 179, 0 different. Tron LE and Pro are the same code, so they flatter each other; Transformers is the honest number. |
| By tier, over the three held-out games (right / wrong) | `exact` 279 / 1, `fuzzy` 44 / 0, `weak` 2 / 0, `callee` 49 / 2 |
| Star Trek LE 1.61 (`st_161h`, the game's decompile and ROM), layers A + B | 157 OS names proposed (layer B alone, built from Tron LE only: 109; 79 of them also found by layer A, **0 disagreements**). Of the 16 names in the Star Trek `docs/os_names.md` (set by hand from its code): 11 proposed identically (`adj_get`, `checksum8`, `error_log`, `msg_get`, `task_create`, `task_sleep`, `text_draw_msg`, `text_draw_str`, `snd_play`, `snd_resolve_call`, `memset8` as `memset`), 1 synonym (`player_current` / `current_player`), **1 different** (`deff_start`, below), 3 not found (`audit_get`, `coil_record`, `coil_system_init`). |
| Layer B on the Tron LE ROM itself | 123 of 169 signed functions found again (the others share a 16-byte window with another name and are dropped on purpose). |

**The difference, as the example of "the code wins".** The hand-set `deff_start` of Star Trek (0xa750) is `leff_start` for the database in all three games (Jaccard 0.88 to 0.92, 699 vs 702 tokens), and the function that looks like `deff_start_core` is 0x22084. A hand name is a hypothesis too: the match asks for a re-read of the code at 0xa750 (lamp effects table, lamp groups, task id), not for an automatic rename.

Not measured yet: layer B across two ROMs of different games for both directions (only the Tron LE ROM was available when this was built: Tron Pro and Transformers ROMs add their hashes with the `bytesig.py build` command below, which also gives the byte-level Transformers leave-one-out).

## Adding a game to the database (agent A, end of section 5.1)

```
python3 tools/rom/sam_os_sigs/sam_os_sigs.py build --game NAME=export.c[:names.tsv] --game ... --api knowledge/sam_os_api.json \
        --source "NAME=repo@commit (ROM set and version)" --out knowledge/sam_os_signatures.json
python3 tools/rom/sam_os_sigs/bytesig.py build --game NAME=export.c:NEW.bin --game ... --out knowledge/sam_os_bytesigs.json
python3 tools/rom/sam_os_sigs/sam_os_sigs.py eval --game NAME=export.c ...      # leave-one-out numbers for the doc
```

Rules: list **every** game each time (the command rebuilds from scratch); only give a game's export once its OS names were read from the code (fact tag `code`); never name a function from a match alone; do not commit a ROM, an export or a decompile (the JSON holds hashes, names, signatures and Jaccard sketches only).

## Limits

- The OS end is 0x40000 in the SAM ROMs seen (OS copied to SRAM), `--os-end` for a ROM that ends earlier (Star Trek 0x339e8). Games' own code (0x01000000 and up) is not signed.
- A new ROM version with a rewritten routine has a different stream: it falls to `fuzzy` / `weak` or is missed. Misses are expected for the audit and coil functions of Star Trek.
- Layer B is ARM-mode only; Thumb code would need its own masks. The SAM OS has none so far.
- Fact tag of every proposed name: **inferred** (structural identity with a function named from code in another game) until read in the new decompile.

Last updated 2026-11-27 (created; Tron LE / Tron Pro / Transformers, measured on Star Trek LE 1.61).
