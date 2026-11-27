# SAM OS signatures (tools)

Names the OS functions of a new SAM ROM from the games already named, without addresses. Method, numbers and use: [knowledge/sam_os_signatures.md](../../../knowledge/sam_os_signatures.md).

| File | What |
|---|---|
| `samsig.py` | Reads a Ghidra export, normalises function bodies, hashes, MinHash sketches, call lists (layer A library) |
| `sam_os_sigs.py` | `build` the database, `apply` it to a new export (+ layer B with `--bytes-db --rom`), `eval` leave-one-out |
| `bytesig.py` | Layer B: masked ARM byte windows hashed; `build` needs the ROMs, `apply` needs the new ROM |
| `merge_seeds.py` | Merge the proposed `names.tsv` into a Ghidra seeds file |

Tests: `python3 -m unittest tests.test_sam_os_sigs` (synthetic data, no ROM).
