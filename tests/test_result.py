"""Filesystem receipt-freshness controls; no native tools or routing are run.

The synthetic receipt tests consistency checks only. It is deliberately not
presented as evidence that the placeholder board has passed actual native DRC.
"""

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from autorouter import pipeline as p, sexpr as sx


ROOT = Path(__file__).resolve().parents[1]


class ResultFreshnessTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".cache" / "result-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source_dir = self.root / "source"
        self.source_dir.mkdir()
        self.source = self.source_dir / "test.kicad_pcb"
        self.source.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) (footprint "fixture" (at 10 10)) (segment (start 1 1) (end 2 1) (width 0.2) (layer "F.Cu") (net "GND") (locked yes)) (segment (start 2 1) (end 3 1) (width 0.2) (layer "F.Cu") (net "GND")))\n')
        self.source.with_suffix(".kicad_pro").write_text("{}\n")
        self.run = self.root / "run"
        self.run.mkdir()
        shutil.copytree(self.source_dir, self.run / "snapshot")
        shutil.copytree(self.source_dir, self.run / "candidate")
        self.candidate = self.run / "candidate" / self.source.name
        shutil.copytree(self.candidate.parent, self.run / "final-drc-input")
        self.native = self.run / "final-drc.json"
        self.native_shape = {
            "$schema": "https://schemas.kicad.org/drc.v1.json",
            "kicad_version": "10.0.0",
            "source": self.source.name,
            "coordinate_units": "mm",
            "date": "2026-10-09T19:00:00",
            "included_severities": ["error", "warning", "exclusion"],
            "ignored_checks": [],
            "violations": [],
            "unconnected_items": [],
            "schematic_parity": [],
        }
        self.native.write_text(json.dumps(self.native_shape))
        self.binding = {"source": str(self.candidate), "input": str(self.run / "final-drc-input" / self.source.name),
                        "saved": False, "before": p.tree_hash(self.candidate.parent), "after": p.tree_hash(self.candidate.parent)}
        (self.run / "final-drc-binding.json").write_text(json.dumps(self.binding))
        process = {"name": "final-drc", "status": "success", "exit_code": 0, "cleanup_complete": True,
                   "wall_seconds": 1, "cpu_seconds": 1, "monitor_cpu_seconds": 0.1, "cwd": str(self.run),
                   "argv": [str(p.c.CLI), "pcb", "drc", "--format", "json", "--severity-all", "--all-track-errors", "--refill-zones", "--exit-code-violations", "--output", str(self.native), self.binding["input"]]}
        (self.run / "final-drc-process.json").write_text(json.dumps(process))
        step = dict(process, validated_input_sha256=p.sha(self.candidate), emitted_candidate=str(self.candidate))
        metrics = {"version": "10.0.0", "track_length_mm": 2.0, "vias": 0}
        (self.run / "metrics.json").write_text(json.dumps(metrics))
        code = self.run / "code"
        code.mkdir()
        implementation = {}
        for source_code in (ROOT / "autorouter").glob("*.py"):
            shutil.copy2(source_code, code / source_code.name)
            implementation["autorouter/" + source_code.name] = p.sha(source_code)
        pins = json.loads((ROOT / "toolchain.lock.json").read_text())["tools"]
        self.receipt = self.run / "result.json"
        self.data = {
            "schema": 1,
            "accepted": True,
            "status": "routing_accepted",
            "source": str(self.source),
            "source_hashes": p.tree_hash(self.source_dir),
            "candidate": str(self.candidate),
            "candidate_sha256": p.sha(self.candidate),
            "native_report_sha256": p.sha(self.native),
            "native": p.parse_report(self.native, self.source.name),
            "scope": "whole_board_unlocked_routing",
            "invariants_unchanged": True,
            "whole_project_drc_clean": True,
            "metrics": metrics,
            "steps": [step],
            "wall_seconds": 2,
            "budget_seconds": 120,
            "cpu_budget_seconds": 120,
            "parent_cpu_seconds": 0.2,
            "child_cpu_seconds": 1,
            "monitor_cpu_seconds": 0.1,
            "total_cpu_seconds": 1.3,
            "tools": {"kicad": "10.0.0", "implementation_sha256": implementation,
                      "files": {str(p.c.resolve_tool_path(pin["path"])): pin["sha256"] for pin in pins.values()}},
        }
        self.save_receipt()

    def save_receipt(self):
        self.receipt.write_text(json.dumps(self.data))

    def test_matching_files_remain_current_without_applying_anything(self):
        before = p.tree_hash(self.root)
        result = p.check_result(self.receipt)
        self.assertIs(result["current"], True)
        self.assertIs(result["applied"], False)
        self.assertEqual(p.tree_hash(self.root), before)

    def test_retained_raw_and_adapted_exports_reject_missing_or_changed_bytes(self):
        for name, field in [("native.dsn", "native_dsn_sha256"), ("task.dsn", "task_dsn_sha256")]:
            (self.run / name).write_text("raw export\n" if name == "native.dsn" else "adapted export\n")
            self.data[field] = p.sha(self.run / name)
        self.save_receipt()
        self.assertTrue(p.check_result(self.receipt)["current"])
        for name in ("native.dsn", "task.dsn"):
            with self.subTest(name=name):
                file = self.run / name
                raw = file.read_bytes()
                file.write_bytes(raw + b"changed\n")
                with self.assertRaisesRegex(p.Rejected, "routing export changed"):
                    p.check_result(self.receipt)
                file.unlink()
                with self.assertRaisesRegex(p.Rejected, "routing export changed"):
                    p.check_result(self.receipt)
                file.write_bytes(raw)
        del self.data["task_dsn_sha256"]
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "routing export changed"):
            p.check_result(self.receipt)

    def test_control_process_cpu_is_charged_and_validated(self):
        self.data["control_child_cpu_seconds"] = 0.25
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "inconsistent CPU"):
            p.check_result(self.receipt)
        self.data["total_cpu_seconds"] += 0.25
        self.save_receipt()
        self.assertTrue(p.check_result(self.receipt)["current"])
        for value in (-1, True, float("nan")):
            self.data["control_child_cpu_seconds"] = value
            self.save_receipt()
            with self.assertRaisesRegex(p.Rejected, "invalid resource"):
                p.check_result(self.receipt)

    def test_edited_source_board_is_stale(self):
        self.source.write_text("edited board\n")
        with self.assertRaisesRegex(p.Rejected, "stale source"):
            p.check_result(self.receipt)

    def test_edited_source_rules_are_stale(self):
        self.source.with_suffix(".kicad_pro").write_text('{"changed":"rules"}\n')
        with self.assertRaisesRegex(p.Rejected, "stale source"):
            p.check_result(self.receipt)

    def test_new_source_rule_file_is_stale(self):
        self.source.with_suffix(".kicad_dru").write_text("(version 1)\n")
        with self.assertRaisesRegex(p.Rejected, "stale source"):
            p.check_result(self.receipt)

    def test_candidate_board_changed_after_validation_is_rejected(self):
        self.candidate.write_text("edited candidate\n")
        with self.assertRaisesRegex(p.Rejected, "project/rules/file set changed"):
            p.check_result(self.receipt)

    def test_candidate_rule_changes_and_additions_are_rejected(self):
        self.candidate.with_suffix(".kicad_pro").write_text('{"changed":"rules"}\n')
        with self.assertRaises(p.Rejected):
            p.check_result(self.receipt)
        self.candidate.with_suffix(".kicad_pro").write_bytes(self.source.with_suffix(".kicad_pro").read_bytes())
        self.candidate.with_suffix(".kicad_dru").write_text("(version 1)\n")
        with self.assertRaises(p.Rejected):
            p.check_result(self.receipt)

    def test_changed_or_missing_native_report_is_rejected(self):
        self.native.write_text(self.native.read_text() + "\n")
        with self.assertRaisesRegex(p.Rejected, "native report changed"):
            p.check_result(self.receipt)
        self.native.unlink()
        with self.assertRaises(FileNotFoundError):
            p.check_result(self.receipt)

    def test_hashed_malformed_report_is_still_rejected(self):
        malformed = copy.deepcopy(self.native_shape)
        del malformed["unconnected_items"]
        self.native.write_text(json.dumps(malformed))
        self.data["native_report_sha256"] = p.sha(self.native)
        self.save_receipt()
        with self.assertRaises(p.Rejected):
            p.check_result(self.receipt)

    def test_hashed_report_with_blocking_finding_is_still_rejected(self):
        reported = copy.deepcopy(self.native_shape)
        reported["violations"] = [{"severity": "error", "type": "clearance", "items": []}]
        self.native.write_text(json.dumps(reported))
        self.data["native_report_sha256"] = p.sha(self.native)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "native findings reject"):
            p.check_result(self.receipt)

    def test_failed_receipt_does_not_become_accepted_when_files_match(self):
        self.data["accepted"] = False
        self.data["status"] = "drc_rejected"
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "not an accepted routing result"):
            p.check_result(self.receipt)

    def test_candidate_path_outside_run_is_rejected(self):
        outside = self.root / "outside"
        shutil.copytree(self.candidate.parent, outside)
        self.data["candidate"] = str(outside / self.candidate.name)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "does not belong"):
            p.check_result(self.receipt)

    def test_candidate_directory_symlink_cannot_escape_run(self):
        outside = self.root / "outside"
        self.candidate.parent.rename(outside)
        self.candidate.parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(p.Rejected):
            p.check_result(self.receipt)

    def test_rehashed_geometry_mutation_cannot_reuse_clean_native_report(self):
        tree = sx.read(self.candidate)
        sx.one(sx.children(tree, "footprint")[0], "at")[1] = "20"
        sx.write(self.candidate, tree)
        self.data["candidate_sha256"] = p.sha(self.candidate)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "immutable geometry"):
            p.check_result(self.receipt)

    def test_rehashed_route_mutation_cannot_reuse_old_input_binding(self):
        tree = sx.read(self.candidate)
        tree.remove(p.routes(tree)[-1])
        sx.write(self.candidate, tree)
        self.data["candidate_sha256"] = p.sha(self.candidate)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "input binding"):
            p.check_result(self.receipt)

    def test_locked_route_and_partial_completion_copper_are_protected(self):
        tree = sx.read(self.candidate)
        tree.remove(p.routes(tree)[0])
        sx.write(self.candidate, tree)
        self.data["candidate_sha256"] = p.sha(self.candidate)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "protected route"):
            p.check_result(self.receipt)
        tree = sx.read(self.source)
        tree.remove(p.routes(tree)[-1])
        sx.write(self.candidate, tree)
        self.data.update(candidate_sha256=p.sha(self.candidate), scope="partial_completion")
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "protected route"):
            p.check_result(self.receipt)

    def test_snapshot_tampering_is_detected(self):
        (self.run / "snapshot" / self.source.name).write_text("different snapshot")
        with self.assertRaisesRegex(p.Rejected, "snapshot changed"):
            p.check_result(self.receipt)

    def test_retained_native_input_tampering_is_detected(self):
        (self.run / "final-drc-input" / self.source.name).write_text("different native input")
        with self.assertRaisesRegex(p.Rejected, "native input changed"):
            p.check_result(self.receipt)

    def test_missing_or_wrong_binding_is_rejected(self):
        self.binding["before"][self.source.name] = "0" * 64
        (self.run / "final-drc-binding.json").write_text(json.dumps(self.binding))
        with self.assertRaisesRegex(p.Rejected, "input binding"):
            p.check_result(self.receipt)
        (self.run / "final-drc-binding.json").unlink()
        with self.assertRaises(FileNotFoundError):
            p.check_result(self.receipt)

    def test_native_summary_and_metrics_are_not_trusted(self):
        self.data["native"]["warnings"] = 50
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "native summary"):
            p.check_result(self.receipt)
        self.data["native"] = p.parse_report(self.native, self.source.name)
        self.data["metrics"]["track_length_mm"] = 0
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "metrics differ"):
            p.check_result(self.receipt)

    def test_process_command_and_result_cross_check(self):
        process_path = self.run / "final-drc-process.json"
        process = json.loads(process_path.read_text())
        process["argv"].remove("--refill-zones")
        process_path.write_text(json.dumps(process))
        with self.assertRaisesRegex(p.Rejected, "process provenance"):
            p.check_result(self.receipt)

    def test_finalization_step_selection_handles_nested_final_drc_names(self):
        nested = copy.deepcopy(self.data["steps"][0])
        nested.update(cwd=str(self.run / "incumbent"), phase="incumbent")
        self.data["steps"].insert(0, nested)
        self.data.update(wall_seconds=3, child_cpu_seconds=2, monitor_cpu_seconds=0.2, total_cpu_seconds=2.4)
        self.save_receipt()
        self.assertTrue(p.check_result(self.receipt)["current"])
        self.data["steps"][-1]["validated_input_sha256"] = "1" * 64
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "final native step"):
            p.check_result(self.receipt)

    def test_over_budget_cpu_inconsistency_and_cancellation_reject(self):
        self.data["wall_seconds"] = 121
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "wall budget"):
            p.check_result(self.receipt)
        self.data.update(wall_seconds=2, total_cpu_seconds=0)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "CPU accounting"):
            p.check_result(self.receipt)
        self.data["total_cpu_seconds"] = 1.3
        cancelled = dict(self.data["steps"][0], name="cancelled-trial", status="cancelled")
        self.data["steps"].append(cancelled)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "cancelled"):
            p.check_result(self.receipt)

    def test_missing_nonfinite_and_exceeded_cpu_ceiling_reject(self):
        for value in (None, 0, float("nan"), float("inf"), 4):
            self.data["cpu_budget_seconds"] = value
            self.save_receipt()
            with self.assertRaises(p.Rejected):
                p.check_result(self.receipt)
        self.data["cpu_budget_seconds"] = 5
        self.data.update(parent_cpu_seconds=5, total_cpu_seconds=6.1)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "CPU budget"):
            p.check_result(self.receipt)

    def test_saved_code_or_tool_provenance_must_match(self):
        (self.run / "code" / "native.py").write_text("changed implementation")
        with self.assertRaisesRegex(p.Rejected, "implementation differs"):
            p.check_result(self.receipt)
        shutil.copy2(ROOT / "autorouter/native.py", self.run / "code/native.py")
        self.data["tools"]["files"][str(p.c.CLI)] = "2" * 64
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected, "tool pins"):
            p.check_result(self.receipt)


class RelocatableToolPinTests(unittest.TestCase):
    """Real-file pin resolution controls, not native binary execution tests."""

    def test_relocated_manifest_verifies_project_local_engine_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / 'relocated-checkout'
            (root / '.tools').mkdir(parents=True)
            (root / 'autorouter').mkdir()
            (root / 'autorouter/config.py').write_text('# fixture implementation\n')
            names = {'CLI': 'kicad_cli', 'PYTHON': 'kicad_python', 'JAVA': 'java', 'PCBNEW': 'pcbnew', 'JAR': 'freerouting'}
            overrides, pins = {'ROOT': root}, {}
            for attribute, name in names.items():
                file = root / ('.tools/freerouting-2.5.0.jar' if attribute == 'JAR' else name)
                file.write_bytes(('non-executable pin fixture: ' + name).encode())
                overrides[attribute] = file
                pins[name] = {'path': str(file.relative_to(root)) if attribute == 'JAR' else str(file), 'sha256': p.sha(file)}
            (root / 'toolchain.lock.json').write_text(json.dumps({'tools': pins}))
            # Only Git metadata is stubbed; path resolution and all file digests
            # use actual files in a new checkout-shaped directory.
            with patch.multiple(p.c, **overrides), patch.object(p.subprocess, 'run', return_value=SimpleNamespace(stdout='a' * 40 + '\n')):
                result = p.tool_manifest()
                self.assertEqual(result['files'][str(overrides['JAR'])], pins['freerouting']['sha256'])
                self.assertEqual(p.c.resolve_tool_path(pins['freerouting']['path']), p.c.JAR)
                overrides['JAR'].write_bytes(b'tampered engine')
                with self.assertRaisesRegex(p.Rejected, 'pinned tool changed'):
                    p.tool_manifest()

    def test_relative_pin_rejects_escape_aliases_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / '.tools').mkdir()
            (root / 'outside').mkdir()
            (root / '.tools/link').symlink_to(root / 'outside', target_is_directory=True)
            with patch.object(p.c, 'ROOT', root):
                for value in ('../outside.jar', './.tools/a.jar', '.tools/../a.jar', '.tools//a.jar', '.tools/link/a.jar', '.'):
                    with self.subTest(value=value), self.assertRaises(ValueError):
                        p.c.resolve_tool_path(value)
                self.assertEqual(p.c.resolve_tool_path(str(p.c.CLI)), p.c.CLI)


if __name__ == "__main__":
    unittest.main()
