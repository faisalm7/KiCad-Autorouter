"""Acceptance-boundary controls; native KiCad controls are a separate suite.

These tests reject tampering before native execution. They do not substitute a
mocked native success or claim that any synthetic tree is a routable board.
"""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from autorouter import pipeline as p
from autorouter import sexpr as sx


ROOT = Path(__file__).resolve().parents[1]
BOARD = '''(kicad_pcb
  (version 20260206)
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
  (net 1 "signal")
  (footprint "test" (at 10 10) (layer "F.Cu")
    (pad "1" thru_hole circle (at 0 0) (size 2 2) (drill 1)
      (layers "*.Cu" "*.Mask") (net 1 "signal")))
  (gr_rect (start 0 0) (end 20 20) (layer "Edge.Cuts")
    (stroke (width 0.05) (type default)))
  (zone (net 1) (net_name "signal") (layer "F.Cu") (uuid "zone-id")
    (connect_pads (clearance 0.3))
    (polygon (pts (xy 1 1) (xy 19 1) (xy 19 19) (xy 1 19))))
  (future_constraint (value "preserve unknown constraints"))
  (segment (start 10 10) (end 12 10) (width 0.3) (layer "F.Cu")
    (net 1) (locked yes) (uuid "protected-id")))'''


class NativeMustNotRun:
    def __init__(self, output):
        self.out = output

    def drc(self, *_args, **_kwargs):
        raise AssertionError("tampering was not rejected before native execution")


class ValidationBoundaryTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".cache" / "validation-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.project = self.work / "candidate"
        self.project.mkdir()
        self.board = self.project / "test.kicad_pcb"
        self.original = sx.parse(BOARD)
        sx.write(self.board, self.original)
        self.rules = self.board.with_suffix(".kicad_pro")
        self.rules.write_text('{"board":{"design_settings":{}}}\n')
        self.hashes = p.tree_hash(self.project)
        self.protected = copy.deepcopy(p.routes(self.original))

    def assert_pre_native_rejection(self, modified, reason):
        sx.write(self.board, modified)
        with self.assertRaisesRegex(p.Rejected, reason):
            p.validate_candidate(NativeMustNotRun(self.work), self.original, self.board, self.hashes, self.protected)

    def test_pad_geometry_and_terminal_net_cannot_change(self):
        for field, value in (("size", "0.2"), ("net", "2")):
            with self.subTest(field=field):
                modified = copy.deepcopy(self.original)
                pad = sx.one(sx.one(modified, "footprint"), "pad")
                sx.one(pad, field)[1] = value
                self.assert_pre_native_rejection(modified, "immutable geometry changed")

    def test_outline_zone_and_unknown_constraint_cannot_change(self):
        for kind in ("gr_rect", "zone", "future_constraint"):
            with self.subTest(kind=kind):
                modified = copy.deepcopy(self.original)
                modified.remove(sx.one(modified, kind))
                self.assert_pre_native_rejection(modified, "immutable geometry changed")

    def test_footprint_position_cannot_change(self):
        modified = copy.deepcopy(self.original)
        sx.one(sx.one(modified, "footprint"), "at")[1] = "11"
        self.assert_pre_native_rejection(modified, "immutable geometry changed")

    def test_protected_track_cannot_be_removed_or_reassigned(self):
        for change in ("remove", "wrong_net"):
            with self.subTest(change=change):
                modified = copy.deepcopy(self.original)
                track = sx.one(modified, "segment")
                if change == "remove":
                    modified.remove(track)
                else:
                    sx.one(track, "net")[1] = "2"
                self.assert_pre_native_rejection(modified, "protected route changed")

    def test_new_rule_file_is_detected(self):
        self.board.with_suffix(".kicad_dru").write_text('(version 1)\n(rule "relax" (constraint clearance (min 0)))\n')
        with self.assertRaisesRegex(p.Rejected, "project/rules/file set changed"):
            p.verify_candidate_files(self.board, self.hashes)

    def test_changed_and_missing_project_rules_are_detected(self):
        self.rules.write_text('{"board":{"design_settings":{"rule_severities":{"clearance":"ignore"}}}}\n')
        with self.assertRaises(p.Rejected):
            p.verify_candidate_files(self.board, self.hashes)
        self.rules.unlink()
        with self.assertRaises(p.Rejected):
            p.verify_candidate_files(self.board, self.hashes)

    def test_candidate_cannot_change_after_hash_binding(self):
        expected = p.sha(self.board)
        self.board.write_text(self.board.read_text() + "\n")
        with self.assertRaises(p.Rejected):
            p.verify_candidate_files(self.board, self.hashes, expected)

    def test_project_symlink_is_rejected(self):
        target = self.work / "external-rules"
        target.write_text("not project data")
        (self.project / "link.kicad_dru").symlink_to(target)
        with self.assertRaisesRegex(p.Rejected, "symlink in project"):
            p.tree_hash(self.project)

    def test_existing_output_cannot_replace_prior_evidence(self):
        result = self.work / "result.json"
        result.write_text("prior evidence")
        with self.assertRaises(FileExistsError):
            p.Job(self.work, 10)
        self.assertEqual(result.read_text(), "prior evidence")


class NativeReportParserTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".cache" / "validation-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.report = Path(self.temp.name) / "report.json"
        self.valid_shape = {
            "$schema": "https://schemas.kicad.org/drc.v1.json",
            "kicad_version": "10.0.0",
            "source": "test.kicad_pcb",
            "coordinate_units": "mm",
            "date": "2026-10-09T19:00:00",
            "included_severities": ["error", "warning", "exclusion"],
            "ignored_checks": [],
            "violations": [],
            "unconnected_items": [],
            "schematic_parity": [],
        }

    def parse(self, data):
        self.report.write_text(json.dumps(data))
        return p.parse_report(self.report, "test.kicad_pcb")

    def test_missing_or_corrupt_report_is_not_a_pass(self):
        with self.assertRaises(FileNotFoundError):
            p.parse_report(self.report, "test.kicad_pcb")
        self.report.write_text("{")
        with self.assertRaises(json.JSONDecodeError):
            p.parse_report(self.report, "test.kicad_pcb")
        for missing in ("violations", "unconnected_items", "schematic_parity", "ignored_checks", "included_severities"):
            with self.subTest(missing=missing):
                data = copy.deepcopy(self.valid_shape)
                del data[missing]
                with self.assertRaises(p.Rejected):
                    self.parse(data)

    def test_report_cannot_name_another_board_or_tool_version(self):
        for key, value in (("source", "other.kicad_pcb"), ("kicad_version", "9.0.2"), ("$schema", "unknown")):
            with self.subTest(key=key):
                data = copy.deepcopy(self.valid_shape)
                data[key] = value
                with self.assertRaises(p.Rejected):
                    self.parse(data)

    def test_malformed_ignored_check_is_rejected(self):
        for entry in ({"description": "key missing"}, {"key": None}, {"key": 1}, "clearance"):
            with self.subTest(entry=entry):
                data = copy.deepcopy(self.valid_shape)
                data["ignored_checks"] = [entry]
                with self.assertRaises(p.Rejected):
                    self.parse(data)

    def test_unknown_or_core_disabled_check_is_rejected(self):
        for key in ("future_unqualified_constraint", "clearance", "unconnected_items", "hole_clearance"):
            with self.subTest(key=key):
                data = copy.deepcopy(self.valid_shape)
                data["ignored_checks"] = [{"key": key, "description": key}]
                with self.assertRaises(p.Rejected):
                    self.parse(data)

    def test_omitted_severities_and_malformed_findings_are_rejected(self):
        data = copy.deepcopy(self.valid_shape)
        data["included_severities"] = ["error"]
        with self.assertRaises(p.Rejected):
            self.parse(data)
        data = copy.deepcopy(self.valid_shape)
        data["violations"] = [{"severity": "warning", "type": "clearance", "items": None}]
        with self.assertRaises(p.Rejected):
            self.parse(data)


class SExpressionPreservationTests(unittest.TestCase):
    def test_unknown_fields_and_quoted_content_survive_roundtrip(self):
        text = r'''(kicad_pcb (unknown (s "café; () \"quoted\" \\path") (n -1.2e-3)))'''
        tree = sx.parse(text)
        self.assertEqual(sx.parse(sx.dump(tree)), tree)

    def test_truncated_multiple_root_and_deep_inputs_are_rejected(self):
        for text in ("(a", ")", "(a)(b)", '(a "x)', "outside", "(" * 140 + "x" + ")" * 140):
            with self.subTest(text=text[:30]):
                with self.assertRaises(ValueError):
                    sx.parse(text)


if __name__ == "__main__":
    unittest.main()
