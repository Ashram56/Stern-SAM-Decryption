"""Address-independent signatures of the Stern SAM OS (ARM7), layer A: structural, from Ghidra pseudo-C.

A SAM ROM carries the same OS code (task switcher, text and bitmap draw, audits, adjustments, sound
calls, coils...) at different addresses per game and per version. This module turns a named Ghidra
export (`// ==== <addr> <name>` headers, as written by TronExport.java / STExport.java) into
signatures that do not depend on any address, and applies them to a new export.

A signature never contains ROM bytes or decompiled text: only hashes of a normalised token stream
(identifiers, addresses and variable names erased), a MinHash sketch of its 4-token shingles, the
small constants, the number of calls and the position-ordered callee ids. See knowledge/sam_os_signatures.md.
"""
import re, hashlib, json, collections, bisect

OS_END = 0x40000            # OS code lives below this address in every SAM ROM seen so far (map in rom_map.json)
NSKETCH = 64                # MinHash length
MIN_TOKENS = 30             # below this a function is too small to match on structure alone
HDR = re.compile(r'// ==== ([0-9a-f]{8}) (\S+)')
KEYW = {'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'default', 'return', 'goto', 'break', 'continue', 'sizeof'}
TYPES = {'void', 'int', 'uint', 'char', 'uchar', 'byte', 'short', 'ushort', 'long', 'ulong', 'bool', 'code', 'undefined',
         'undefined1', 'undefined2', 'undefined4', 'undefined8', 'float', 'double', 'dword', 'word', 'longlong', 'ulonglong'}
TOK = re.compile(r'0x[0-9a-fA-F]+|\d+|[A-Za-z_]\w*|<<|>>|<=|>=|==|!=|&&|\|\||->|[-+*/%&|^~!<>=?:;,.(){}\[\]]')
GENERIC_NAME = re.compile(r'^(FUN|thunk_FUN|DAT|PTR|LAB|switchD|caseD|UNK|SUB)_[0-9a-fA-F]+|^[0-9a-f]{8}$')


def load(path):
    """-> {addr: (name, body)} from a Ghidra export with '// ==== addr name' headers."""
    fs, cur, buf = {}, None, []
    with open(path, errors='replace') as fh:
        for l in fh:
            m = HDR.match(l)
            if m:
                if cur:
                    fs[cur[0]] = (cur[1], ''.join(buf))
                cur, buf = (int(m.group(1), 16), m.group(2)), []
            else:
                buf.append(l)
    if cur:
        fs[cur[0]] = (cur[1], ''.join(buf))
    return fs


GAME_SPECIFIC = re.compile(r'^(sw\d+_|leff_\d+|lamp_\d+_|snd_play_[0-9a-f]{3}$|task_[0-9a-f]{1,3}(_\d+)?$|task_2b)')


def is_named(name):
    """A real name: not a Ghidra default, not a vector, and not a per-game handler (switch / lamp effect / sound call number)."""
    return not GENERIC_NAME.match(name) and not GAME_SPECIFIC.match(name) and name not in ('Reset', 'IRQ', 'FIQ', 'UndefinedInstruction', 'SupervisorCall',
                                                         'PrefetchAbort', 'DataAbort', 'NotUsed')


def strip(body):
    body = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
    return re.sub(r'//[^\n]*', '', body)


def tokens(body):
    """Normalised token stream: names erased, large (address-like) numbers erased, calls kept as F(."""
    toks = TOK.findall(strip(body))
    # drop the signature line (up to the first '{'): argument names/types differ between annotated exports
    if '{' in toks:
        toks = toks[toks.index('{'):]
    out = []
    for i, t in enumerate(toks):
        c = t[0]
        if c.isdigit():
            v = int(t, 16 if t[:2] in ('0x', '0X') else 10)
            out.append(t.lower() if v < 0x10000 else 'A')
        elif c.isalpha() or c == '_':
            if t in KEYW:
                out.append(t)
            elif t in TYPES:
                out.append('T')
            elif i + 1 < len(toks) and toks[i + 1] == '(':
                out.append('F')
            else:
                out.append('I')
        else:
            out.append(t)
    return out


def h32(s):
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=4).digest(), 'big')


def shingles(toks, k=4):
    return {h32(' '.join(toks[i:i + k])) for i in range(max(1, len(toks) - k + 1))}


_PRIMES = [(0x9E3779B1 * (i + 1)) | 1 for i in range(NSKETCH)]


def sketch(sh):
    return [min((h * p) & 0xFFFFFFFF for h in sh) for p in _PRIMES]


def jaccard(a, b):
    return sum(x == y for x, y in zip(a, b)) / len(a)


def callees(body, names_by_addr, addr_of_name):
    """Callee addresses in order of appearance (FUN_xxxxxxxx or a known name followed by '(')."""
    out = []
    for m in re.finditer(r'\b(?:FUN_|thunk_FUN_)([0-9a-fA-F]{8})\b|\b([A-Za-z_]\w*)\s*\(', strip(body)):
        if m.group(1):
            out.append(int(m.group(1), 16))
        elif m.group(2) in addr_of_name:
            out.append(addr_of_name[m.group(2)])
    return out


def features(fs):
    """-> {addr: dict(name, ntok, hash, sketch, consts, calls)} for every function of an export."""
    addr_of_name = {n: a for a, (n, b) in fs.items() if is_named(n)}
    feat = {}
    for a, (n, b) in fs.items():
        t = tokens(b)
        feat[a] = dict(name=n, ntok=len(t), hash=hashlib.sha1(' '.join(t).encode()).hexdigest()[:16],
                       sketch=sketch(shingles(t)) if len(t) >= MIN_TOKENS else None,
                       consts=sorted({x for x in t if x.startswith('0x')})[:40],
                       calls=callees(b, None, addr_of_name))
    return feat
