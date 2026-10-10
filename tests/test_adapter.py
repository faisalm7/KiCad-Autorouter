"""B1 DSN semantic controls; native/engine validation remains a separate gate."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from autorouter import adapter as a
from autorouter import sexpr as sx


ROOT = Path(__file__).resolve().parents[1]
DSN = '''(pcb "native development task"
  (parser (string_quote ") (host_cad "KiCad's Pcbnew"))
  (resolution um 10) (unit um)
  (structure
    (layer top_copper (type signal) (property (index 0)))
    (layer bottom_copper (type signal) (property (index 1)))
    (boundary (rect pcb 0 -20000 20000 0))
    (plane GND (polygon bottom_copper 0 0 0 20000 0 20000 -20000 0 -20000))
    (keepout original (rect bottom_copper 100 -200 200 -100))
    (rule (width 250) (clearance 200))
    (unknown (value "preserve; parentheses () and unicode café")))
  (placement (component component1 (place U1 1000 -1000 front 90)))
  (library (image component1 (pin pad1 1 0 0))
    (padstack pad1 (shape (circle signal 1000))))
  (network (net GND (pins U1-1 J1-2 J2-1)) (net signal (pins U1-2 J1-1)))
  (wiring (wire (path top_copper 250 1000 -1000 2000 -1000) (net signal))))
'''


class AdapterTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".cache" / "adapter-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "task.dsn"
        self.path.write_text(DSN)
        self.obstacles = [{"layer": "B.Cu", "bbox_mm": [1.25, 2.5, 4.75, 6.125]}]

    def assert_failure_preserves_source(self, text, mode="both", obstacles=None):
        self.path.write_text(text)
        original = self.path.read_bytes()
        with self.assertRaises(ValueError):
            a.adapt_dsn(self.path, mode, self.obstacles if obstacles is None else obstacles)
        self.assertEqual(self.path.read_bytes(), original)

    def test_graphics_converts_mm_flips_y_and_preserves_every_other_node(self):
        before = a._parse_dsn(DSN)
        result = a.adapt_dsn(self.path, "graphics", self.obstacles)
        after = a._parse_dsn(self.path.read_text())
        structure = sx.one(after, "structure")
        keepout = sx.children(structure, "keepout")[-1]
        self.assertEqual(keepout[2], ["rect", "bottom_copper", "1250", "-6125", "4750", "-2500"])
        structure.remove(keepout)
        self.assertEqual(after, before)
        self.assertEqual(result["planes_removed"], 0)
        self.assertEqual(result["graphics_keepouts_added"], 1)
        self.assertEqual(result["input_sha256"], hashlib.sha256(DSN.encode()).hexdigest())
        self.assertEqual(result["output_sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_planes_only_removes_direct_structure_declarations(self):
        text = DSN.replace('(unknown (value', '(unknown (plane hidden (shape unchanged)) (value')
        self.path.write_text(text)
        expected = a._parse_dsn(text)
        expected_structure = sx.one(expected, "structure")
        expected_structure.remove(sx.one(expected_structure, "plane"))
        report = a.adapt_dsn(self.path, "planes", self.obstacles)
        self.assertEqual(a._parse_dsn(self.path.read_text()), expected)
        self.assertEqual(report["planes_removed"], 1)
        self.assertEqual(report["graphics_keepouts_added"], 0)
        self.assertIn("over-routing", report["limitations"][1])

    def test_both_preserves_net_pin_mapping(self):
        original = a._parse_dsn(DSN)
        report = a.adapt_dsn(self.path, "both", self.obstacles)
        after = a._parse_dsn(self.path.read_text())
        for section in ("network", "placement", "library", "wiring"):
            self.assertEqual(sx.one(after, section), sx.one(original, section))
        self.assertEqual(report["net_pin_mapping"]["nets"], 2)
        self.assertEqual(report["net_pin_mapping"]["pins"], 5)
        self.assertTrue(report["net_pin_mapping_unchanged"])
        self.assertEqual(report["classification"], "B1_adapter_only")
        self.assertEqual((report["planes_removed"], report["graphics_keepouts_added"]), (1, 1))

    def test_layer_mapping_accepts_exact_and_explicit_and_rejects_unknown(self):
        for obstacle in ({"layer": "bottom_copper", "bbox_mm": [1, 2, 3, 4]},
                         {"layer": "native-custom-name", "dsn_layer": "top_copper", "bbox_mm": [1, 2, 3, 4]}):
            self.path.write_text(DSN)
            a.adapt_dsn(self.path, "graphics", [obstacle])
        for obstacle in ({"layer": "In2.Cu", "bbox_mm": [1, 2, 3, 4]},
                         {"layer": "B.Cu", "dsn_layer": "not-present", "bbox_mm": [1, 2, 3, 4]}):
            self.assert_failure_preserves_source(DSN, obstacles=[obstacle])

    def test_bad_bounds_modes_units_and_malformed_input_fail_before_write(self):
        for bbox in ([1, 2, 1, 3], [2, 2, 1, 3], [0, 0, float("nan"), 3],
                     [0, 0, float("inf"), 3], [True, 0, 2, 3], ["1", 2, 3, 4], [1, 2, 3]):
            self.assert_failure_preserves_source(DSN, obstacles=[{"layer": "B.Cu", "bbox_mm": bbox}])
        self.assert_failure_preserves_source(DSN, mode="strategy-c")
        for text in (DSN.replace("(unit um)", "(unit mm)"),
                     DSN.replace("(resolution um 10)", "(resolution mil 10)"),
                     DSN.replace("(resolution um 10)", "(resolution um NaN)"),
                     DSN.replace("(rule (width", "(unit mm) (rule (width"),
                     DSN + "(second_root)", DSN[:-3],
                     DSN.replace('(plane GND (polygon', '(plane GND malformed (polygon'),
                     DSN.replace('(pcb "native development task"', '(pcb'),
                     DSN.replace('(string_quote ")', '(string_quote x)')):
            self.assert_failure_preserves_source(text)

    def test_quote_normalization_ignores_comments_and_escaped_quoted_content(self):
        text = '; fake (string_quote ") declaration\n' + DSN.replace(
            '"native development task"', r'"literal (string_quote \") and \\ backslash"')
        tree = a._parse_dsn(text)
        self.assertEqual(a._parse_dsn(a._dump_dsn(tree)), tree)
        self.assertIn('(string_quote ")', a._dump_dsn(tree))
        self.assertNotIn(a._QUOTE_SENTINEL, a._dump_dsn(tree))
        self.assert_failure_preserves_source(DSN.replace("native development task", a._QUOTE_SENTINEL))

    def test_symlink_non_dsn_and_double_graphics_application_rejected(self):
        link = self.path.parent / "link.dsn"
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            a.adapt_dsn(link, "both", self.obstacles)
        other = self.path.parent / "board.kicad_pcb"
        other.write_text(DSN)
        with self.assertRaises(ValueError):
            a.adapt_dsn(other, "both", self.obstacles)
        a.adapt_dsn(self.path, "graphics", self.obstacles)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "already contains"):
            a.adapt_dsn(self.path, "graphics", self.obstacles)
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
