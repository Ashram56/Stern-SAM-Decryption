#!/usr/bin/env python3
"""Turn a Ghidra export that carries a disassembly fallback after each
`decompile failed` line (tools/MMExport.java of the 6809 games) into bench
batch files: one `F <addr> <name>` header then `<addr>\\t<mnemonic>` per
instruction. Functions are split into batches whose address ranges do not
overlap (banked games reuse 0x4000-0x7fff), because the bench loads one flat
64 KB space. usage: extract_failed.py export.c OUT_PREFIX  -> OUT_PREFIX0.txt ..."""
import re, sys
src = open(sys.argv[1], errors="replace").read().split("\n")
funcs = []; cur = None; fail = False
for l in src:
    m = re.match(r"// ==== (\S+) (\S+)", l)
    if m: cur = [m.group(1).split("::")[-1], m.group(2), []]; funcs.append(cur); fail = False; continue
    if cur is None: continue
    if "decompile failed" in l: fail = True
    elif fail:
        m = re.match(r"// (?:[A-Za-z0-9]+::)?([0-9a-f]+)  (.*)", l)
        if m: cur[2].append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(2)).strip()))
bad = [f for f in funcs if f[2]]
batches = []
for f in bad:
    s, e = min(a for a, _ in f[2]), max(a for a, _ in f[2]) + 4
    for b in batches:
        if all(e <= bs or s >= be for bs, be in b[1]): b[0].append(f); b[1].append((s, e)); break
    else: batches.append(([f], [(s, e)]))
for i, (fs, _) in enumerate(batches):
    with open(f"{sys.argv[2]}{i}.txt", "w") as o:
        for a, n, ins in fs:
            o.write(f"F {ins[0][0]:x} {n}\n")
            for ad, t in ins: o.write(f"{ad:x}\t{t}\n")
print(len(bad), "failed functions in", len(batches), "batches")
