#!/usr/bin/env python3
"""Layer B of the SAM OS signatures: masked ARM byte patterns, stored as hashes (no ROM bytes in the database).

ARM code is position dependent in two places: B/BL offsets and pc-relative `ldr rX,[pc,#imm]` literal loads.
Both are masked before hashing, so the same OS routine hashes the same in two ROMs whatever its address.
The first 16, 32 and 64 bytes of a function (as far as the function is long) are hashed with BLAKE2b.

  build  --game NAME=EXPORT.c:ROM.bin [--names names.tsv] --out sam_os_bytesigs.json   (EXPORT.c gives names, addresses, ends)
  apply  --db sam_os_bytesigs.json --rom NEW.bin --out-names names.tsv [--os-end 0x40000]

Needs the ROM of every game in the database (they are never committed): the database is rebuilt locally from the
exports + ROMs, and committed as hashes only. Same masks as the Pro port (tools/rom/ghidra/pro/fmatch.py).
"""
import sys, os, json, struct, hashlib, argparse, collections, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from samsig import load, is_named, OS_END

WINDOWS = (16, 32, 64)


def mask(b):
    """Zero the position dependent parts of ARM words: B/BL offset (24 bits) and ldr pc-relative immediate (12 bits)."""
    out = bytearray(b)
    for i in range(0, len(b) - 3, 4):
        w = struct.unpack_from('<I', b, i)[0]
        if ((w >> 25) & 7) == 5:                 # B / BL (any condition)
            out[i:i + 3] = b'\0\0\0'
        elif (w & 0x0F7F0000) == 0x051F0000:     # ldr rX,[pc,#+-imm12]
            out[i] = 0
            out[i + 1] &= 0xF0
    return bytes(out)


def hwin(m, off, n):
    return hashlib.blake2b(m[off:off + n], digest_size=8).hexdigest()


def sigs_at(m, off, length):
    return {str(n): hwin(m, off, n) for n in WINDOWS if n <= length and off + n <= len(m)}


def build(specs, names_tsv=None, os_end=OS_END):
    per = collections.defaultdict(dict)
    for s in specs:
        g, rest = s.split('=', 1)
        exp, rom = rest.split(':', 1)
        fs = load(exp)
        data = open(rom, 'rb').read()
        m = mask(data[:os_end + 0x100])
        addrs = sorted(a for a in fs if a < os_end)
        if names_tsv:
            for l in open(names_tsv):
                x = l.rstrip('\n').split('\t')
                if len(x) > 1 and int(x[0], 16) in fs:
                    fs[int(x[0], 16)] = (x[1].strip(), fs[int(x[0], 16)][1])
        for i, a in enumerate(addrs):
            n = fs[a][0]
            if not is_named(n):
                continue
            ln = (addrs[i + 1] if i + 1 < len(addrs) else os_end) - a
            sg = sigs_at(m, a, ln)
            if sg:
                per[n][g] = dict(addr=a, length=ln, h=sg)
    return dict(version=1, windows=WINDOWS, os_end=os_end, functions=[dict(name=n, games=v) for n, v in sorted(per.items())])


def apply(db, rom, os_end=None):
    os_end = os_end or db['os_end']
    m = mask(rom[:os_end + 0x100])
    index = {w: collections.defaultdict(set) for w in map(str, WINDOWS)}
    for f in db['functions']:
        for g, v in f['games'].items():
            for w, h in v['h'].items():
                index[w][h].add(f['name'])
    res = {}
    for off in range(0, os_end, 4):
        for w in sorted(index, key=int, reverse=True):          # longest window first
            c = index[w].get(hwin(m, off, int(w)))
            if c and len(c) == 1:
                res[off] = (next(iter(c)), w)
                break
    byname = collections.defaultdict(list)
    for a, (n, w) in res.items():
        byname[n].append(a)
    return {a: v for a, v in res.items() if len(byname[v[0]]) == 1}      # a name found twice is ambiguous


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='cmd', required=True)
    b = sp.add_parser('build'); b.add_argument('--game', action='append', required=True); b.add_argument('--names'); b.add_argument('--out', required=True)
    a_ = sp.add_parser('apply'); a_.add_argument('--db', required=True); a_.add_argument('--rom', required=True); a_.add_argument('--out-names', required=True); a_.add_argument('--os-end', type=lambda x: int(x, 0))
    a = p.parse_args()
    if a.cmd == 'build':
        db = build(a.game, a.names)
        json.dump(db, open(a.out, 'w'), separators=(',', ':'))
        print('functions', len(db['functions']))
    else:
        r = apply(json.load(open(a.db)), open(a.rom, 'rb').read(), a.os_end)
        with open(a.out_names, 'w') as f:
            for off in sorted(r):
                f.write('%08x\t%s\n' % (off, r[off][0]))
        print('matched', len(r))
