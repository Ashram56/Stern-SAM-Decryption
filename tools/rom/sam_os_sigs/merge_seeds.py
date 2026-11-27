#!/usr/bin/env python3
"""Merge a names.tsv (addr<TAB>name, from sam_os_sigs.py or bytesig.py apply) into a Ghidra seeds file (addr<TAB>name).
usage: merge_seeds.py SEEDS.tsv NAMES.tsv OUT.tsv [--force]
Existing names are kept unless --force. Addresses of NAMES that are not in SEEDS are added (seeds are function starts)."""
import sys


def read(p):
    d = {}
    for l in open(p):
        x = l.rstrip('\n').split('\t')
        if x and x[0]:
            d[int(x[0], 16)] = x[1].strip() if len(x) > 1 else ''
    return d


seeds, names = read(sys.argv[1]), read(sys.argv[3 - 1])
force = '--force' in sys.argv
n = 0
for a, nm in names.items():
    if force or not seeds.get(a):
        n += seeds.get(a) != nm
        seeds[a] = nm
with open(sys.argv[3], 'w') as f:
    for a in sorted(seeds):
        f.write('%08x\t%s\n' % (a, seeds[a]))
print('seeds %d, names set %d' % (len(seeds), n))
