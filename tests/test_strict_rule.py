import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "strict_rule"))
import check_strict_rule as c

INV = "| Board | CPU | ROM | Decompile state |\n|---|---|---|---|\n| Main | 6809 | a.rom | %s |\n| Sound | ARM | s.rom | %s |\n"


def mk(root, files):
    for rel, txt in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(txt)


class T(unittest.TestCase):
    def run_(self, files):
        with tempfile.TemporaryDirectory() as d:
            mk(d, files)
            return c.run(d)[0]

    def good(self, **extra):
        f = {"CLAUDE.md": " ".join(c.MARKERS), "docs/boards_inventory.md": INV % ("complet", "complet")}
        f.update(extra)
        return f

    def test_clean(self):
        self.assertEqual(self.run_(self.good()), [])

    def test_partial_board_fails(self):
        f = self.good(**{"docs/boards_inventory.md": INV % ("complet", "partiel")})
        self.assertTrue(any("Sound" in m for m in self.run_(f)))

    def test_missing_inventory_and_rule(self):
        self.assertEqual(len(self.run_({"x.txt": "1"})), 4)

    def test_pinmame_source_fails_and_waiver_passes(self):
        f = self.good(**{"game/d.csv": "id,source\n1,pinmame render\n", "game/a.py": "x", "docs/functional_diagram.md": "0x8000"})
        self.assertTrue(any("d.csv" in m for m in self.run_(f)))
        f["docs/pinmame_waivers.md"] = "- `game/d.csv` approved by Vincent 2026-11-25\n"
        self.assertEqual(self.run_(f), [])

    def test_second_table_without_state_column(self):
        # a note table after the inventory (boards with no firmware) is not read as inventory rows
        inv = INV % ("complet", "complet") + "\n| Board | Why no firmware |\n|---|---|\n| IO driver | latches |\n"
        self.assertEqual(self.run_(self.good(**{"docs/boards_inventory.md": inv})), [])

    def test_short_row_is_a_failure_not_a_crash(self):
        inv = "| Board | CPU | ROM | Decompile state |\n|---|---|---|---|\n| Main | ARM |\n"
        self.assertTrue(any("Main" in m for m in self.run_(self.good(**{"docs/boards_inventory.md": inv}))))

    def test_undeclared_captures_are_found(self):
        f = self.good(**{"game/a.py": "x", "docs/functional_diagram.md": "0x8000",
                         "pkg/coils.csv": "coil,mpf_source\n1,observed in play\n",
                         "pkg/shows/leff_1.yaml": "#show_version=6\n# lamp effect 1, captured in the emulator (lfx.cpp)\n- duration: 80ms\n",
                         "pkg/deff_1/timing.json": '{"deff": 1, "capture": "fg2"}'})
        out = " ".join(self.run_(f))
        for name in ("coils.csv", "leff_1.yaml", "timing.json"):
            self.assertIn(name, out)

    def test_diagram_gate(self):
        self.assertTrue(any("diagram" in m for m in self.run_(self.good(**{"game/a.py": "x"}))))


    def test_rom_file_fails_and_exception_passes(self):
        f = self.good(**{"rom/game.a00": "x"})
        self.assertTrue(any("game.a00" in m for m in self.run_(f)))
        f["docs/rom_exceptions.md"] = "- `rom/game.a00` approved by Vincent 2026-11-26\n"
        self.assertEqual(self.run_(f), [])

    def test_layout_warns_then_strict_fails(self):
        with tempfile.TemporaryDirectory() as d:
            mk(d, self.good(**{"mpf/x.yaml": "a: 1"}))
            fails, warns = c.run(d)
            self.assertEqual(fails, [])
            self.assertTrue(any("mpf/" in w and "game/" in w for w in warns))
            fails, _ = c.run(d, layout_strict=True)
            self.assertTrue(any(m.startswith("layout:") for m in fails))

    def test_dmd_tick_external_warns(self):
        with tempfile.TemporaryDirectory() as d:
            mk(d, self.good(**{"rom_data/dmd_tick.csv": "game,board,base_hz_source,tick_ms\ng,main,external (PinMAME),16.4\n"}))
            self.assertTrue(any("external" in w for w in c.run(d)[1]))
            mk(d, {"rom_data/dmd_tick.csv": "game,board,base_hz_source,tick_ms\ng,main,code,16.0\n"})
            self.assertFalse(any("external" in w for w in c.run(d)[1]))

    def test_dmd_unmeasured(self):
        H = "game,animation_id,class,ticks,ms,end_addr,loop_addr,min_ticks,max_ticks,decider_addr,method,wait_sites,notes\n"
        with tempfile.TemporaryDirectory() as d:
            mk(d, self.good(**{"rom_data/dmd_durations.csv": H + "g,01,unmeasured,,,,,,,,exec_hooked,,refused everywhere\n"}))
            fails, warns = c.run(d)
            self.assertEqual(fails, [])
            self.assertTrue(any("unmeasured" in w for w in warns))

    def test_dmd_durations(self):
        H = "game,animation_id,class,ticks,ms,end_addr,loop_addr,min_ticks,max_ticks,decider_addr,method,wait_sites\n"
        tick = "game,tick_ms\ng,16.4\n"
        ok = H + "g,01,finite,10,164,33:7448,,10,10,,exec_hooked,33:7430:10\n" + "g,02,empty,0,0,,,,,,,\n"
        self.assertEqual(self.run_(self.good(**{"rom_data/dmd_durations.csv": ok, "rom_data/dmd_tick.csv": tick})), [])
        bad = H + "g,01,finite,10,200,33:7448,,10,10,,pinmame,33:7430:10\ng,02,loop,5,82,,,,,,exec_hooked,\n"
        f = self.run_(self.good(**{"rom_data/dmd_durations.csv": bad, "rom_data/dmd_tick.csv": tick}))
        self.assertTrue(any("tick_ms" in m for m in f) and any("capture" in m for m in f) and any("loop_addr" in m for m in f))
        with tempfile.TemporaryDirectory() as d:
            mk(d, self.good(**{"rom_data/dmd_deffs.csv": "id\n1\n"}))
            self.assertTrue(any(m.startswith("dmd:") for m in c.run(d)[1]))


if __name__ == "__main__":
    unittest.main()
