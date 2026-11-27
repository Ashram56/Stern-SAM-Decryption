import os, sys, struct, tempfile, unittest, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "rom", "sam_os_sigs"))
import samsig, sam_os_sigs as S, bytesig

BODY = """
void %(n)s(int a,int b)

{
  int iVar1;
  uint uVar2;

  iVar1 = FUN_%(f1)s(a,0x40);
  uVar2 = DAT_%(d)s + b * 0x1000;
  while (iVar1 < 0x100) {
    if (uVar2 != 0) { iVar1 = iVar1 + FUN_%(f2)s(uVar2,0x20); }
    else { %(c)s(iVar1,7); }
    iVar1 = iVar1 + 1;
  }
  switch (a) { case 1: uVar2 = uVar2 + 0x30; break; case 2: uVar2 = uVar2 - 0x31; break; }
  return;
}
"""


def export(path, funcs):
    with open(path, "w") as f:
        for addr, name, kw in funcs:
            f.write("// ==== %08x %s\n%s\n" % (addr, name, BODY % dict(kw, n=name)))


class Layer(unittest.TestCase):
    def test_structural_match_across_addresses(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c = (os.path.join(d, x) for x in ("a.c", "b.c", "c.c"))
            export(a, [(0x1000, "draw_thing", dict(f1="00002000", f2="00002100", d="00300010", c="FUN_00002200"))])
            export(b, [(0x1400, "draw_thing", dict(f1="00002400", f2="00002500", d="00300ff0", c="FUN_00002600"))])
            export(c, [(0x5000, "FUN_00005000", dict(f1="00006000", f2="00006100", d="00301000", c="FUN_00006200"))])
            db = S.build(["g1=" + a, "g2=" + b])
            self.assertEqual(db["functions"][0]["status"], "validated")
            res, _ = S.match(db, samsig.load(c))
            self.assertEqual(res[0x5000][0], "draw_thing")
            self.assertEqual(res[0x5000][1], "exact")

    def test_generic_names_are_not_signed(self):
        self.assertFalse(samsig.is_named("FUN_00001234"))
        self.assertFalse(samsig.is_named("thunk_FUN_00001234"))
        self.assertTrue(samsig.is_named("task_sleep"))

    def test_changed_function_is_not_matched(self):
        with tempfile.TemporaryDirectory() as d:
            a, c = os.path.join(d, "a.c"), os.path.join(d, "c.c")
            export(a, [(0x1000, "draw_thing", dict(f1="00002000", f2="00002100", d="00300010", c="FUN_00002200"))])
            with open(c, "w") as f:
                f.write("// ==== 00005000 FUN_00005000\nvoid FUN_00005000(void)\n{\n  do { x = x + 1; } while (x < 9);\n  return;\n}\n")
            res, _ = S.match(S.build(["g1=" + a]), samsig.load(c))
            self.assertEqual(res, {})


def arm(*words):
    return b"".join(struct.pack("<I", w) for w in words)


def bl(src, dst):
    return 0xEB000000 | (((dst - src - 8) >> 2) & 0xFFFFFF)


def ldr_pc(rd, imm):
    return 0xE59F0000 | (rd << 12) | imm


class Bytes(unittest.TestCase):
    def test_mask_ignores_bl_and_literal_offsets(self):
        f1 = arm(0xE92D4010, bl(0x100, 0x2000), ldr_pc(1, 0x30), 0xE1A00001, 0xE8BD8010) + bytes(64)
        f2 = arm(0xE92D4010, bl(0x9000, 0x4400), ldr_pc(1, 0x7C), 0xE1A00001, 0xE8BD8010) + bytes(64)
        self.assertNotEqual(f1, f2)
        self.assertEqual(bytesig.mask(f1), bytesig.mask(f2))

    def test_register_and_opcode_changes_are_kept(self):
        f1 = arm(0xE92D4010, ldr_pc(1, 0x30))
        f2 = arm(0xE92D4010, ldr_pc(2, 0x30))
        self.assertNotEqual(bytesig.mask(f1), bytesig.mask(f2))

    def test_apply_finds_function_at_new_address(self):
        fn = lambda base, tgt, lit: arm(0xE92D4010, bl(base + 4, tgt), ldr_pc(1, lit), 0xE1A00001, 0xE8BD8010, 0xE1A00000, 0xE1A00000, 0xE1A00000, 0xE3A00001, 0xE3A01002, 0xE1A02003, 0xE1A04004, 0xE1A05005, 0xE1A06006, 0xE1A07007, 0xE12FFF1E)
        with tempfile.TemporaryDirectory() as d:
            rom1 = bytes(0x100) + fn(0x100, 0x400, 0x20) + bytes(0x200)
            exp = os.path.join(d, "e.c"); open(exp, "w").write("// ==== 00000100 my_func\nvoid my_func(void)\n{\n}\n// ==== 00000200 FUN_00000200\nvoid FUN_00000200(void)\n{\n}\n")
            rp = os.path.join(d, "r1.bin"); open(rp, "wb").write(rom1)
            db = bytesig.build(["g1=%s:%s" % (exp, rp)], os_end=0x400)
            rom2 = bytes(0x240) + fn(0x240, 0x380, 0x5C) + bytes(0x100)
            res = bytesig.apply(db, rom2, 0x400)
            self.assertEqual(res[0x240][0], "my_func")


if __name__ == "__main__":
    unittest.main()
