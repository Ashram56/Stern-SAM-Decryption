#!/usr/bin/env python3
"""Build, apply and evaluate the address-independent SAM OS signature database (layer A, from Ghidra C).

  build  --game NAME=EXPORT.c[:names.tsv] ... --api sam_os_api.json --out sam_os_signatures.json
  apply  --db sam_os_signatures.json --export NEW.c --out-names names.tsv [--out-sigs sigs.tsv] [--report r.md]
  eval   --game NAME=EXPORT.c[:names.tsv] ...      (leave-one-out: each game is matched with a DB built from the others)

Exports use the '// ==== <addr> <name>' headers of TronExport.java / STExport.java. names.tsv: 'addr<TAB>name'.
Only OS functions (address < 0x40000) are signed. Layer B (byte patterns) is in bytesig.py.
"""
import sys, os, json, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from samsig import *

VALID_J = 0.60     # two games' bodies are "the same function" above this MinHash Jaccard
FUZZY_J = 0.75     # apply: minimum Jaccard for a fuzzy match
WEAK_J = 0.50      # apply: 'weak' tier, large functions only
WEAK_GAP = 0.25
MARGIN = 0.10      # apply: best must beat the second best (other name) by this much


def read_names(p):
    d = {}
    for l in open(p):
        x = l.rstrip('\n').split('\t')
        if len(x) > 1 and x[1].strip():
            d[int(x[0], 16)] = x[1].strip()
    return d


def load_game(spec):
    name, rest = spec.split('=', 1)
    path, _, names = rest.partition(':')
    fs = load(path)
    if names:
        for a, n in read_names(names).items():
            if a in fs and not is_named(fs[a][0]):
                fs[a] = (n, fs[a][1])
    return name, fs


def game_entries(fs):
    """named OS functions of one export, with features; callee names resolved."""
    feat = features(fs)
    named = {a: f['name'] for a, f in feat.items() if is_named(f['name'])}
    out = {}
    for a, f in feat.items():
        if a < OS_END and is_named(f['name']) and f['ntok'] >= 8:
            out[f['name']] = dict(addr=a, ntok=f['ntok'], hash=f['hash'], sketch=f['sketch'], consts=f['consts'],
                                  calls=[named.get(c, '') for c in f['calls']])
    return out


def build(specs, api=None, sources=()):
    games = {}
    per = collections.defaultdict(dict)
    for s in specs:
        g, fs = load_game(s)
        e = game_entries(fs)
        games[g] = len([1 for a, (n, b) in fs.items() if a < OS_END])
        for n, v in e.items():
            per[n][g] = v
    sigs = {}
    if api:
        for e in json.load(open(api)):
            sigs[e['name']] = (e.get('signature', ''), e.get('meaning', ''))
    funcs = []
    for n in sorted(per):
        gs = per[n]
        sk = [(g, v['sketch']) for g, v in gs.items() if v['sketch']]
        js = [jaccard(a[1], b[1]) for i, a in enumerate(sk) for b in sk[i + 1:]]
        hs = {v['hash'] for v in gs.values()}
        if len(gs) == 1:
            st = 'single'
        elif len(hs) == 1 or (js and min(js) >= VALID_J):
            st = 'validated'
        elif js and max(js) >= VALID_J:
            st = 'partial'
        elif not js:
            st = 'validated' if len(hs) == 1 else 'single'
        else:
            st = 'conflict'
        funcs.append(dict(name=n, status=st, signature=sigs.get(n, ('', ''))[0], meaning=sigs.get(n, ('', ''))[1],
                          min_jaccard=round(min(js), 2) if js else None, games=gs))
    return dict(version=1, os_end=OS_END, games=games, sources=dict(x.split('=', 1) for x in sources), functions=funcs)


def ref_index(db, only=None):
    """hash -> {names}, and list of (name, game, entry) with sketches."""
    byhash = collections.defaultdict(set)
    sk = []
    for f in db['functions']:
        if f['status'] == 'conflict':
            continue
        for g, v in f['games'].items():
            if only and g not in only:
                continue
            byhash[v['hash']].add(f['name'])
            if v['sketch']:
                sk.append((f['name'], g, v))
    return byhash, sk


def match(db, fs, exclude_games=()):
    """-> {addr: (name, how, score)} for the OS functions of export `fs`."""
    only = {g for g in db['games'] if g not in exclude_games}
    byhash, sk = ref_index(db, only)
    refcalls = {}
    for f in db['functions']:
        for g, v in f['games'].items():
            if g in only:
                refcalls.setdefault(f['name'], []).append(v['calls'])
    feat = features(fs)
    named_t = {a: f['name'] for a, f in feat.items() if is_named(f['name'])}
    res = {}
    # 1. exact normalised hash (unique name)
    for a, f in feat.items():
        if a >= OS_END or f['ntok'] < 8:
            continue
        c = byhash.get(f['hash'])
        if c and len(c) == 1 and (f['ntok'] >= MIN_TOKENS or True):
            res[a] = (next(iter(c)), 'exact', 1.0)
    # 2. fuzzy: score of a name = mean over the games that know it of the best Jaccard in that game
    bygame = collections.defaultdict(lambda: collections.defaultdict(list))
    for n, g, v in sk:
        bygame[n][g].append(v)
    for a, f in feat.items():
        if a in res or a >= OS_END or not f['sketch']:
            continue
        best = {}
        for n, gs in bygame.items():
            js = []
            for g, vs in gs.items():
                j = max((jaccard(f['sketch'], v['sketch']) for v in vs if abs(v['ntok'] - f['ntok']) <= 0.5 * f['ntok']), default=0)
                js.append(j)
            best[n] = sum(js) / len(js)
        rk = sorted(best.items(), key=lambda x: -x[1])
        if not rk:
            continue
        top = rk[0][1]
        gap = top - (rk[1][1] if len(rk) > 1 else 0)
        if top >= FUZZY_J and gap >= MARGIN:
            res[a] = (rk[0][0], 'fuzzy', round(top, 2))
        elif top >= WEAK_J and gap >= WEAK_GAP and f['ntok'] >= 80:
            res[a] = (rk[0][0], 'weak', round(top, 2))
    # 3. propagate through ordered callees
    changed = True
    while changed:
        changed = False
        taken = collections.Counter(n for n, _, _ in res.values())
        for a, (n, how, sc) in list(res.items()):
            tc = feat[a]['calls']
            for rc in refcalls.get(n, []):
                if len(rc) != len(tc) or not rc:
                    continue
                for tcall, rname in zip(tc, rc):
                    if rname and tcall < OS_END and tcall in feat and tcall not in res and feat[tcall]['ntok'] >= 8 \
                            and taken[rname] == 0 and byhash.get(feat[tcall]['hash'], {rname}) >= {rname}:
                        res[tcall] = (rname, 'callee', 0.0)
                        taken[rname] += 1
                        changed = True
                break
    # a name claimed twice by exact/fuzzy is ambiguous: keep the best score only
    byname = collections.defaultdict(list)
    for a, v in res.items():
        byname[v[0]].append(a)
    for n, al in byname.items():
        if len(al) > 1:
            al.sort(key=lambda a: -res[a][2])
            for a in al[1:]:
                del res[a]
    return res, feat


def cmd_apply(a):
    db = json.load(open(a.db))
    fs = load(a.export)
    res, feat = match(db, fs)
    if a.bytes_db:
        import bytesig
        bd = json.load(open(a.bytes_db))
        rom = open(a.rom, 'rb').read()
        for ad, (n, w) in bytesig.apply(bd, rom, a.os_end).items():
            if ad in res and res[ad][0] != n:
                print('DISAGREE 0x%x: structure %s, bytes %s: dropped' % (ad, res[ad][0], n))
                del res[ad]
            elif ad in res:
                res[ad] = (n, 'bytes+' + res[ad][1], 1.0)
            else:
                res[ad] = (n, 'bytes', 1.0)
    with open(a.out_names, 'w') as f:
        for ad in sorted(res):
            f.write('%08x\t%s\n' % (ad, res[ad][0]))
    if a.out_sigs:
        sg = {x['name']: x['signature'] for x in db['functions'] if x['signature']}
        with open(a.out_sigs, 'w') as f:
            for ad in sorted(res):
                if res[ad][0] in sg:
                    f.write('%08x\t%s\n' % (ad, sg[res[ad][0]]))
    if a.report:
        with open(a.report, 'w') as f:
            f.write('# SAM OS names applied to %s\n\n| Address | Name | How | Score | Status in DB |\n|---|---|---|---|---|\n' % os.path.basename(a.export))
            st = {x['name']: x['status'] for x in db['functions']}
            for ad in sorted(res):
                n, how, sc = res[ad]
                f.write('| 0x%x | %s | %s | %s | %s |\n' % (ad, n, how, sc, st.get(n, '')))
    c = collections.Counter(v[1] for v in res.values())
    print('matched %d OS functions: %s' % (len(res), dict(c)))


def cmd_build(a):
    db = build(a.game, a.api, a.source)
    json.dump(db, open(a.out, 'w'), separators=(',', ':'))
    c = collections.Counter(f['status'] for f in db['functions'])
    print('functions %d, games %s, status %s, bytes %d' % (len(db['functions']), db['games'], dict(c), os.path.getsize(a.out)))


def cmd_eval(a):
    specs = {}
    for s in a.game:
        g, fs = load_game(s)
        specs[g] = (s, fs)
    rows = []
    for g, (s, fs) in specs.items():
        db = build([x[0] for k, x in specs.items() if k != g])
        res, feat = match(db, fs)
        truth = {ad: n for ad, (n, b) in fs.items() if ad < OS_END and is_named(n)}
        ok = sum(1 for ad, v in res.items() if truth.get(ad) == v[0])
        bad = [(ad, v[0], truth[ad]) for ad, v in res.items() if ad in truth and truth[ad] != v[0]]
        new = sum(1 for ad in res if ad not in truth)
        byhow = collections.Counter((v[1], truth.get(ad) == v[0]) for ad, v in res.items() if ad in truth)
        rows.append((g, len(truth), ok, len(bad), new, byhow, bad))
        print('%-9s named OS %3d | matched same name %3d | named differently %3d | new names %3d' % (g, len(truth), ok, len(bad), new))
        print('     by tier (right/wrong): ' + ', '.join('%s %d/%d' % (h, byhow[(h, True)], byhow[(h, False)]) for h in ('exact', 'fuzzy', 'weak', 'callee')))
        for ad, mine, theirs in bad[:40]:
            print('     0x%x  db=%s  own=%s' % (ad, mine, theirs))
    return rows


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='cmd', required=True)
    b = sp.add_parser('build'); b.add_argument('--game', action='append', required=True); b.add_argument('--api'); b.add_argument('--source', action='append', default=[]); b.add_argument('--out', required=True)
    ap = sp.add_parser('apply'); ap.add_argument('--db', required=True); ap.add_argument('--export', required=True)
    ap.add_argument('--out-names', required=True); ap.add_argument('--out-sigs'); ap.add_argument('--report'); ap.add_argument('--bytes-db'); ap.add_argument('--rom'); ap.add_argument('--os-end', type=lambda x: int(x, 0))
    e = sp.add_parser('eval'); e.add_argument('--game', action='append', required=True)
    a = p.parse_args()
    {'build': cmd_build, 'apply': cmd_apply, 'eval': cmd_eval}[a.cmd](a)
