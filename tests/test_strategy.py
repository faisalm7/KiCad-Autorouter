"""C-prototype selection/budget controls; native routing must be tested separately.

Control-flow cases substitute the native stages explicitly. Their synthetic
receipts test budgeting and evidence retention, never routing correctness.
"""

import copy
import json
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, sexpr as sx, strategy as s


ROOT = Path(__file__).resolve().parents[1]
BOARD = '''(kicad_pcb (version 20260206)
 (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
 (net 1 "ordinary_signal") (net 2 "GND") (net 3 "keepout_net")
 (zone (net 1) (layer "F.Cu") (uuid "plane-zone"))
 (zone (net 3) (layer "F.Cu") (uuid "keepout") (keepout (tracks not_allowed)))
 (zone (net 0) (layer "F.Cu") (uuid "no-net"))
 (segment (start 0 0) (end 1 0) (net 1) (width 0.3) (layer "F.Cu") (locked yes) (uuid "protected"))
 (segment (start 90 90) (end 200 200) (net 1) (width 0.3) (layer "F.Cu") (uuid "hidden-reference")))'''


def track(identifier, net, length):
    return sx.parse(f'(segment (start 2 2) (end {2 + length} 2) (net {net}) (width 0.3) (layer "F.Cu") (uuid "{identifier}"))')


def candidate_tree(original):
    tree = copy.deepcopy(original)
    tree[:] = [node for node in tree if not isinstance(node, list) or not node or node[0] not in p.ROUTES or p.locked(node)]
    tree.extend((track("tool-long", 1, 8), track("tool-short", 1, 3), track("unrelated-ground-name", 2, 4)))
    return tree


def metrics(tree):
    return {"track_length_mm": sum(s._length(route) for route in p.routes(tree)),
            "vias": sum(route[0] == "via" for route in p.routes(tree)), "version": "10.0.0"}


def native_report(board_name, opens=0):
    return {"$schema": "https://schemas.kicad.org/drc.v1.json", "kicad_version": "10.0.0",
            "source": board_name, "included_severities": ["error", "warning", "exclusion"],
            "ignored_checks": [], "violations": [], "schematic_parity": [],
            "unconnected_items": [{"type": "unconnected_items", "severity": "error", "items": []}] * opens}


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.original = sx.parse(BOARD)
        self.tree = candidate_tree(self.original)
        self.protected = [route for route in p.routes(self.original) if p.locked(route)]
        self.nets = s.zone_net_ids(self.original)

    def test_zone_net_ids_ignore_names_keepouts_and_no_net_zones(self):
        self.assertEqual(self.nets, {"1"})
        eligible = s.eligible_routes(self.tree, self.nets, self.protected)
        self.assertEqual({sx.one(route, "uuid")[1] for route in eligible}, {'"tool-long"', '"tool-short"'})
        self.assertNotIn('"hidden-reference"', sx.dump(s.proposals(self.tree, self.nets, self.protected, True)))

    def test_protected_and_non_zone_routes_cannot_be_deleted(self):
        for route in (self.protected[0], p.routes(self.tree)[-1]):
            with self.subTest(route=route):
                with self.assertRaises(p.Rejected):
                    s.delete_routes(self.tree, [s.route_id(route)], self.nets, self.protected)

    def test_whole_net_deletion_preserves_locked_and_other_net_copper(self):
        proposal = s.proposals(self.tree, self.nets, self.protected, True)[0]
        changed = s.delete_routes(self.tree, proposal["route_ids"], self.nets, self.protected)
        self.assertIn(self.protected[0], p.routes(changed))
        self.assertIn(p.routes(self.tree)[-1], p.routes(changed))
        self.assertEqual(len(p.routes(changed)), 2)
        self.assertEqual(p.immutable(changed), p.immutable(self.original))

    def test_individual_proposals_rank_actual_candidate_lengths(self):
        proposals = s.proposals(self.tree, self.nets, self.protected, False)
        self.assertEqual([proposal["ranking_length_mm"] for proposal in proposals], [8, 3])

    def test_quality_cannot_trade_new_warnings_or_vias_for_length(self):
        clean = {"findings": []}
        warning = {"findings": [{"type": "track_dangling", "severity": "warning", "items": [{"uuid": "new-warning"}]}]}
        self.assertFalse(s._improves({"track_length_mm": 1, "vias": 2}, {"track_length_mm": 2, "vias": 1}, clean, clean))
        self.assertFalse(s._improves({"track_length_mm": 1, "vias": 1}, {"track_length_mm": 2, "vias": 1}, warning, clean))


class StrategyControlFlowTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".cache" / "strategy-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source_dir = self.root / "source"
        self.source_dir.mkdir()
        self.source = self.source_dir / "test.kicad_pcb"
        self.source.write_text(BOARD)
        self.source.with_suffix(".kicad_pro").write_text("{}\n")
        self.output = self.root / "run"
        self.clock = 1000.0
        self.budgets = []
        self.baseline_advance = 10
        self.reject_incumbent = False
        self.modify_source = False
        self.slow_final_emission = False
        self.baseline_child_cpu = 3.0
        self.validation_cpu = 2.0

    def exercise(self):
        owner = self
        real_job = p.Job
        real_save = p.save_json

        def save(path, value):
            real_save(path, value)
            if owner.slow_final_emission and Path(path) == owner.output / "result.json":
                owner.clock += 120
                owner.slow_final_emission = False

        class ControlledJob(real_job):
            def native(self, name, action, board, output, *args):
                owner.assertEqual(action, "metrics")
                owner.clock += 0.2
                Path(output).write_text(json.dumps(metrics(sx.read(board))))
                self.steps.append({"name": name, "status": "success", "cpu_seconds": 0.25, "monitor_cpu_seconds": 0.01, "max_rss_bytes": 123})

        def baseline(source, output, seconds, keep_existing, adapter, engine_profile):
            owner.budgets.append(seconds)
            owner.assertFalse(keep_existing)
            owner.assertEqual(adapter, "both")
            owner.assertEqual(engine_profile, "tuned")
            output.mkdir()
            shutil.copytree(source.parent, output / "candidate")
            candidate = output / "candidate" / source.name
            sx.write(candidate, candidate_tree(sx.read(source)))
            native_path = output / "final-drc.json"
            native_path.write_text(json.dumps(native_report(source.name)))
            receipt = {"schema": 1, "status": "drc_rejected" if owner.reject_incumbent else "routing_accepted",
                       "accepted": not owner.reject_incumbent, "source": str(source), "source_hashes": p.tree_hash(source.parent),
                       "candidate": str(candidate), "candidate_sha256": p.sha(candidate),
                       "native_report_sha256": p.sha(native_path), "native": p.parse_report(native_path, source.name),
                       "metrics": metrics(sx.read(candidate)), "wall_seconds": owner.baseline_advance,
                       "parent_cpu_seconds": 99, "steps": [{"status": "success", "cpu_seconds": owner.baseline_child_cpu, "monitor_cpu_seconds": 0.5, "max_rss_bytes": 456}]}
            p.save_json(output / "result.json", receipt)
            owner.clock += owner.baseline_advance
            if owner.modify_source:
                source.write_text(BOARD + "\n")
            return receipt

        def validate(job, original, candidate, hashes, protected):
            owner.assertEqual(len(protected), 1)
            owner.assertIn(protected[0], p.routes(sx.read(candidate)))
            owner.assertEqual(p.immutable(sx.read(candidate)), p.immutable(original))
            p.verify_candidate_files(candidate, hashes)
            owner.clock += 1
            eligible = s.eligible_routes(sx.read(candidate), {"1"}, protected)
            report_path = job.out / "final-drc.json"
            report_path.write_text(json.dumps(native_report(candidate.name, opens=0 if eligible else 1)))
            job.steps.append({"name": "full_validation_substitute", "status": "success", "cpu_seconds": owner.validation_cpu, "monitor_cpu_seconds": 0.1, "max_rss_bytes": 234})
            return p.sha(candidate), p.parse_report(report_path, candidate.name)

        with patch.object(s.time, "monotonic", lambda: owner.clock), patch.object(p, "Job", ControlledJob), patch.object(p, "route", baseline), patch.object(p, "validate_candidate", validate), patch.object(p, "tool_manifest", lambda: {"implementation_sha256": {}}), patch.object(p, "check_storage", lambda: 0), patch.object(p, "save_json", save), patch.object(p, "check_result", return_value={"current": True}):
            return s.prune(self.source, self.output, 120)

    def test_all_attempts_accounted_and_failed_trials_retained(self):
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertLessEqual(self.budgets[0], 120 - s.FINAL_RESERVE_SECONDS)
        self.assertEqual(result["improvements"], 1)
        self.assertEqual([trial["accepted"] for trial in result["trials"]], [False, True, False])
        for trial in result["trials"]:
            self.assertTrue(Path(trial["receipt"]).is_file())
        expected_child = sum(step["cpu_seconds"] for step in result["steps"])
        expected_monitor = sum(step["monitor_cpu_seconds"] for step in result["steps"])
        self.assertAlmostEqual(result["child_cpu_seconds"], expected_child)
        self.assertAlmostEqual(result["monitor_cpu_seconds"], expected_monitor)
        self.assertAlmostEqual(result["total_cpu_seconds"], expected_child + expected_monitor + result["parent_cpu_seconds"])
        self.assertLess(result["parent_cpu_seconds"], 99)  # Nested parent's fake receipt is not double-counted.
        self.assertEqual(result["cpu_budget_seconds"], 120)
        self.assertEqual(result["incumbent_baseline"], "B2_tuned")
        self.assertEqual(result["engine_profile"], "tuned")
        self.assertLessEqual(result["total_cpu_seconds"], 120)

    def test_rejected_incumbent_never_becomes_accepted(self):
        self.reject_incumbent = True
        result = self.exercise()
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "incumbent_rejected")
        self.assertFalse((self.output / "candidate").exists())
        self.assertEqual(result["child_cpu_seconds"], 3)

    def test_global_deadline_overrides_any_incumbent_success(self):
        self.baseline_advance = 121
        result = self.exercise()
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["trials"], [])

    def test_insufficient_finalization_reserve_rejects(self):
        self.baseline_advance = 110
        result = self.exercise()
        self.assertFalse(result["accepted"])
        self.assertIn("insufficient reserved time", result["reason"])
        self.assertEqual(result["trials"], [])

    def test_stale_source_after_incumbent_rejects(self):
        self.modify_source = True
        result = self.exercise()
        self.assertFalse(result["accepted"])
        self.assertIn("source", result["reason"])

    def test_cpu_exhaustion_blocks_trials_and_final_acceptance(self):
        self.baseline_child_cpu = 121
        result = self.exercise()
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "cpu_limit")
        self.assertEqual(result["trials"], [])

    def test_cpu_reserve_stops_proposals_before_finalization(self):
        self.baseline_child_cpu = 104.0
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["trials"], [])
        self.assertEqual(result["improvements"], 0)

    def test_trial_cpu_overshoot_never_becomes_root_acceptance(self):
        self.validation_cpu = 121
        result = self.exercise()
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "cpu_limit")
        self.assertEqual(len(result["trials"]), 1)

    def test_final_evidence_emission_is_charged_to_global_budget(self):
        self.slow_final_emission = True
        result = self.exercise()
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "timeout")
        saved = json.loads((self.output / "result.json").read_text())
        self.assertFalse(saved["accepted"])
        self.assertEqual(saved["status"], "timeout")

    def test_invalid_budget_or_existing_output_never_starts_incumbent(self):
        with patch.object(p, "route", side_effect=AssertionError("must not run")):
            for budget in (29, 901, float("nan"), True):
                with self.subTest(budget=budget), self.assertRaises(p.Rejected):
                    s.prune(self.source, self.output, budget)
            self.output.mkdir()
            marker = self.output / "original"
            marker.write_text("preserve")
            with self.assertRaises(FileExistsError):
                s.prune(self.source, self.output, 120)
            self.assertEqual(marker.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
