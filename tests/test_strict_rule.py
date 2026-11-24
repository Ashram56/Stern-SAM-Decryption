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
        f = {"CLAUDE.md": c.MARKER, "docs/boards_inventory.md": INV % ("complet", "complet")}
        f.update(extra)
        return f

    def test_clean(self):
        self.assertEqual(self.run_(self.good()), [])

    def test_partial_board_fails(self):
        f = self.good(**{"docs/boards_inventory.md": INV % ("complet", "partiel")})
        self.assertTrue(any("Sound" in m for m in self.run_(f)))

    def test_missing_inventory_and_rule(self):
        self.assertEqual(len(self.run_({"x.txt": "1"})), 2)

    def test_pinmame_source_fails_and_waiver_passes(self):
        f = self.good(**{"game/d.csv": "id,source\n1,pinmame render\n", "game/a.py": "x", "docs/functional_diagram.md": "0x8000"})
        self.assertTrue(any("d.csv" in m for m in self.run_(f)))
        f["docs/pinmame_waivers.md"] = "- `game/d.csv` approved by Vincent 2026-11-25\n"
        self.assertEqual(self.run_(f), [])

    def test_diagram_gate(self):
        self.assertTrue(any("diagram" in m for m in self.run_(self.good(**{"game/a.py": "x"}))))


if __name__ == "__main__":
    unittest.main()
