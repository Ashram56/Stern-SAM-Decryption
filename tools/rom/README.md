# ROM extraction tools (the Tron toolkit)

The scripts and emulator hooks that took the Tron Legacy LE 1.74 ROM apart, copied here (2026-10-10) from
[Tron-Legacy-LE-ROM-Decryption](https://github.com/Ashram56/Tron-Legacy-LE-ROM-Decryption) so the next SAM game
starts from them. The [ROM extraction agent](../../agents/rom_extraction.md) explains each method; this page
says where its tool is. Improve the tools here; the Tron repo keeps the versions that produced its data (and
the Tron game repo reads `rules/tools/trace/` there as a submodule).

**Retargeting.** Most tools were written for one ROM: they hardcode Tron addresses (tables, OS functions, RAM),
the ROM file name (`trn_174h.bin`) and Tron-session paths (`/mnt/project-files/tron/...`, `/home/claude/work`).
The agent file's sections 5 to 8 say how to find each address again on another ROM. Generic as they stand: the
PinMAME patches, `trace_compare.py`, `la_capture_decode.py`, and the scenario language.

| Here | Tron path | What | Agent section |
|---|---|---|---|
| [`emulator_trace/`](emulator_trace) | `rules/tools/trace/` | `pinmame_arm_hook.patch` (per-instruction ARM hook in libpinmame), `tron_ref.cpp` (run the ROM from a scenario script, log score/deff/sound/leff/audit events as JSONL, deterministic), `trace_compare.py` (first difference between two traces), README with the scenario language and trace format | 3.2, 4, 9 |
| [`ghidra/`](ghidra) | `rules/tools/ghidra/` | headless Ghidra decompile: `TronSetup.java` (memory map, seeds, names, signatures), `TronExport.java`, `run_ghidra.sh`, seed/name/signature tables (`sigs.tsv`, `seeds_*.tsv`, `ram_symbols.tsv`), `annotate.py` (comments for sounds, messages, adjustments); `pro/` ports the names to a second model by function matching (`fmatch.py`) | 3.1, 15 |
| [`rom_data/`](rom_data) | `rom_data/tools/` | the machine-readable tables: `rom.py` (ROM reader), display effects (`deff_static.py`, `deff_sym.py` symbolic ARM interpreter, `deff_trace.cpp`, `deff_build.py`), `fonts.py`, IO and coil drive (`hw_*.py`, `hw_trace.cpp`, scenarios), settings/audits/pricing (`settings_extract.py`, `settings_emu.cpp`), game states (`states_*.py`, `states_ref.cpp`), Pro port (`pro_hw*.py`) | 5, 7, 8, 14 |
| [`media/`](media) | `mpf_package/tools/` | first-generation exporters: images (`imgdec.py`), ADPCM sounds (`adpcm.py`), animations and DMD captures (`tracer.cpp`, `export_*.py`, `build_dmd.py`), lamp effects (`lfx.cpp`, `build_lampfx.py`), service menu (`build_service.py`, `fmt.cpp`), call graph (`cg.py`); several are one-off scratch scripts with Tron paths | 6, 7, 8, 10 |
| [`bus/`](bus) | `io/bus/tools/` | `pinmame_bus_hook.patch` and `bus_trace.cpp` (every IO, DMD, sound and AT91 peripheral access with cycle stamps), scenario scripts, `la_capture_decode.py` (logic analyzer CSVs), summaries | 8.2; [sam_hardware](../../knowledge/sam_hardware/README.md) |

The Tron data these tools produced (traces, tables, decompiles) stays in the Tron repo; never copy ROM-derived
media here.
