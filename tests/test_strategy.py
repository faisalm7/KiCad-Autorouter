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
        # The pure selection fixture above deliberately contains a restricted
        # area. Actual routing now rejects that unsupported native constraint;
        # budget/control-flow tests need an explicitly unrestricted area.
        control_board = BOARD.replace('(keepout (tracks not_allowed))',
            '(keepout (tracks allowed) (vias allowed) (pads allowed) '
            '(copperpour allowed) (footprints allowed))')
        self.source.write_text(control_board)
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
        self.trial_storage_advance = 0
        self.trial_copy_advance = 0
        self.process_cpu = 0
        self.trial_storage_cpu_advance = 0
        self.trial_copy_cpu_advance = 0
        self.feedback_scenario = False
        self.tamper_feedback_report = False
        self.tamper_feedback_base = False
        self.adaptive_probe_event = None
        self.publication_tools = {}

    def exercise(self, proposal_policy="single"):
        owner = self
        real_job = p.Job
        real_save = p.save_json
        real_copytree = shutil.copytree

        def storage(**kwargs):
            if (owner.output / "incumbent/result.json").exists():
                owner.clock += owner.trial_storage_advance
                owner.process_cpu += owner.trial_storage_cpu_advance

        def copytree(source, destination, *args, **kwargs):
            value = real_copytree(source, destination, *args, **kwargs)
            if Path(destination).parent.name.startswith("trial-"):
                owner.clock += owner.trial_copy_advance
                owner.process_cpu += owner.trial_copy_cpu_advance
            return value

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
                if owner.tamper_feedback_report and self.out.name == "trial-0001":
                    (self.out / "final-drc.json").write_text("altered after native validation")
                if owner.tamper_feedback_base and self.out.name == "trial-0001":
                    best = owner.output / "incumbent" / "candidate" / owner.source.name
                    best.write_text(best.read_text() + "\n")
                self.steps.append({"name": name, "status": "success", "cpu_seconds": 0.25, "monitor_cpu_seconds": 0.01, "max_rss_bytes": 123})

        def baseline(source, output, seconds, keep_existing, adapter, engine_profile):
            owner.budgets.append(seconds)
            owner.assertFalse(keep_existing)
            owner.assertEqual(adapter, "both")
            owner.assertEqual(engine_profile, "tuned")
            output.mkdir()
            shutil.copytree(source.parent, output / "candidate")
            candidate = output / "candidate" / source.name
            tree = candidate_tree(sx.read(source))
            if owner.feedback_scenario:
                tree.append(track("tool-bridge", 1, 1))
            sx.write(candidate, tree)
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
            if proposal_policy == "adaptive":
                (job.out / "pre-refill.kicad_pcb").write_bytes(candidate.read_bytes())
                event = owner.adaptive_probe_event if job.out.name == "trial-0001" else None
                if event in {"exception", "timeout", "crash", "cancel"}:
                    if event != "exception":
                        job.steps.append({"name":"authored_probe_failure", "status":{"timeout":"timeout","crash":"signal","cancel":"cancelled"}[event], "cpu_seconds":0})
                    raise p.Rejected("authored incomplete probe: " + event)
            raw = native_report(candidate.name, opens=0 if eligible else 1)
            if owner.feedback_scenario:
                names = {sx.unquote(sx.one(route, "uuid")[1]) for route in eligible}
                raw = native_report(candidate.name, opens=0 if "tool-bridge" in names else 1)
                if "tool-long" not in names and "tool-short" in names:
                    raw["violations"] = [{"type": "track_dangling", "severity": "warning",
                                           "items": [{"uuid": "tool-short"}]}]
            if proposal_policy == "adaptive" and job.out.name == "trial-0001" and owner.adaptive_probe_event == "drc":
                raw = native_report(candidate.name, opens=1)
            report_path.write_text(json.dumps(raw))
            job.steps.append({"name": "full_validation_substitute", "status": "success", "cpu_seconds": owner.validation_cpu, "monitor_cpu_seconds": 0.1, "max_rss_bytes": 234})
            return p.sha(candidate), p.parse_report(report_path, candidate.name)

        def geometry(job, best):
            # Synthetic control-flow geometry only; actual Native has separate controls.
            context = {'pads': [], 'input_hashes_before': p.tree_hash(best.parent)}
            p.save_json(job.out / 'floor-final-context.json', context)
            job.steps.append({'name': 'geometry_substitute', 'status': 'success', 'cpu_seconds': 0.1, 'monitor_cpu_seconds': 0, 'max_rss_bytes': 123})
            return context, p.sha(job.out / 'floor-final-context.json')

        with patch.object(s, '_adaptive_trial_native', side_effect=owner.authored_adaptive_native), patch.object(s, '_chain_context', side_effect=geometry), patch.object(s.time, "monotonic", lambda: owner.clock), patch.object(s.time, "process_time", lambda: owner.process_cpu), patch.object(p, "Job", ControlledJob), patch.object(p, "route", baseline), patch.object(p, "validate_candidate", validate), patch.object(p, "tool_manifest", lambda: {"implementation_sha256": owner.publication_tools}), patch.object(p, "check_storage", storage), patch.object(shutil, "copytree", copytree), patch.object(p, "save_json", save), patch.object(p, "check_result", return_value={"current": True}):
            return s.prune(self.source, self.output, 120, proposal_policy=proposal_policy)

    def test_trial_storage_cost_is_rechecked_before_creating_job(self):
        self.baseline_advance = 85
        self.trial_storage_advance = 7
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["trials"], [])

    def test_preparation_exhaustion_retains_trial_without_native_attempt(self):
        self.baseline_advance = 70
        self.trial_copy_advance = 7
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(len(result["trials"]), 1)
        trial = json.loads(Path(result["trials"][0]["receipt"]).read_text())
        self.assertFalse(trial["accepted"])
        self.assertEqual(trial["steps"], [])
        self.assertIn("insufficient trial budget after preparation", trial["reason"])
        self.assertFalse(list(Path(result["trials"][0]["receipt"]).parent.glob("*-binding.json")))

    def test_trial_storage_cpu_is_rechecked_with_wall_time_remaining(self):
        self.baseline_child_cpu = 85.0
        self.trial_storage_cpu_advance = 7
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["trials"], [])
        self.assertLess(result["wall_seconds"], 30)

    def test_preparation_cpu_exhaustion_refuses_native_with_wall_time_remaining(self):
        self.baseline_child_cpu = 70.0
        self.trial_copy_cpu_advance = 7
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(len(result["trials"]), 1)
        trial = json.loads(Path(result["trials"][0]["receipt"]).read_text())
        self.assertEqual(trial["steps"], [])
        self.assertIn("insufficient trial budget after preparation", trial["reason"])
        self.assertLess(result["wall_seconds"], 30)

    def test_preparation_also_respects_local_trial_deadline(self):
        self.trial_copy_advance = s.MAX_TRIAL_SECONDS + 1
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(len(result["trials"]), 1)
        trial = json.loads(Path(result["trials"][0]["receipt"]).read_text())
        self.assertEqual(trial["steps"], [])
        self.assertIn("insufficient trial budget after preparation", trial["reason"])

    def test_native_final_reserve_stops_late_trial_before_publication(self):
        # Larger native validation needs time after a nearly exhausted incumbent.
        # This is scheduling only; real Native/publication is a separate regression.
        self.baseline_child_cpu = 100.0
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["trials"], [])
        self.assertEqual(result["improvements"], 0)

    def test_all_attempts_accounted_and_failed_trials_retained(self):
        result = self.exercise()
        self.assertTrue(result["accepted"], result)
        self.assertLessEqual(self.budgets[0], 120 - s.NATIVE_FINAL_RESERVE_SECONDS)
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


    def test_feedback_compound_move_retains_every_failure_and_full_check(self):
        self.feedback_scenario = True
        result = self.exercise("feedback")
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["proposal_policy"], "feedback")
        self.assertEqual(result["metrics"]["track_length_mm"], 6)
        self.assertEqual([t["status"] for t in result["trials"]],
                         ["drc_rejected", "quality_rejected", "improvement_validated", "drc_rejected"])
        receipts = [json.loads(Path(t["receipt"]).read_text()) for t in result["trials"]]
        self.assertEqual(receipts[2]["proposal"]["kind"], "native_warning_cleanup")
        self.assertEqual(receipts[2]["proposal"]["parent_trial"], receipts[1]["id"])
        self.assertEqual(receipts[2]["proposal"]["added_route_uuids"], ["tool-short"])
        self.assertEqual(len(receipts[2]["proposal"]["route_ids"]), 2)
        self.assertEqual(len([st for st in result["steps"] if st.get("name") == "full_validation_substitute"]), 5)
        self.assertAlmostEqual(result["child_cpu_seconds"], sum(st["cpu_seconds"] for st in result["steps"]))
        self.assertAlmostEqual(result["total_cpu_seconds"], result["child_cpu_seconds"] + result["monitor_cpu_seconds"] + result["parent_cpu_seconds"])

    def test_single_policy_does_not_consume_warning_feedback(self):
        self.feedback_scenario = True
        result = self.exercise("single")
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["metrics"]["track_length_mm"], 14)
        self.assertEqual(list(self.output.glob("trials/*/feedback-decision.json")), [])

    def test_feedback_uses_same_total_trial_cap(self):
        self.feedback_scenario = True
        with patch.object(s, "MAX_TRIALS", 2):
            result = self.exercise("feedback")
        self.assertTrue(result["accepted"], result)
        self.assertEqual(len(result["trials"]), 2)
        self.assertEqual(result["improvements"], 0)
        self.assertEqual(len([st for st in result["steps"] if st.get("name") == "full_validation_substitute"]), 3)

    def test_feedback_cpu_cost_can_reject_total_even_after_valid_improvement(self):
        self.feedback_scenario = True
        self.validation_cpu = 31
        result = self.exercise("feedback")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "cpu_limit")
        self.assertGreater(result["total_cpu_seconds"], result["cpu_budget_seconds"])
        self.assertEqual(result["child_cpu_seconds"], sum(st["cpu_seconds"] for st in result["steps"]))

    def test_feedback_rejects_changed_incumbent_before_compound_move(self):
        self.feedback_scenario = True
        self.tamper_feedback_base = True
        result = self.exercise("feedback")
        self.assertFalse(result["accepted"])
        self.assertEqual(len(result["trials"]), 2)

    def test_feedback_rejects_changed_raw_native_report(self):
        self.feedback_scenario = True
        self.tamper_feedback_report = True
        result = self.exercise("feedback")
        self.assertFalse(result["accepted"])
        self.assertIn("native report changed", result["reason"])
        self.assertEqual(len(result["trials"]), 2)

    def test_invalid_policy_never_creates_job(self):
        with patch.object(p, "route", side_effect=AssertionError("must not run")):
            with self.assertRaises(p.Rejected):
                s.prune(self.source, self.output, 120, proposal_policy="invented")
        self.assertFalse(self.output.exists())

    def test_chain_proposal_reuses_full_validation_and_cannot_accept_an_open(self):
        self.source.write_text(self.source.read_text().replace('(net 1 "ordinary_signal")', '(net 0 "") (net 1 "ordinary_signal")'))
        real = candidate_tree
        def separated(original):
            candidate = real(original)
            # Keep the unrelated synthetic route away from the tested joint.
            for route in p.routes(candidate):
                if sx.one(route, "net")[1] == "2":
                    for name in ("start", "end"):
                        point = sx.one(route, name)
                        point[2] = str(float(point[2]) + 10)
            return candidate
        with patch(__name__ + ".candidate_tree", side_effect=separated):
            result = self.exercise("chains")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["proposal_policy"], "chains")
        self.assertEqual(len(result["chain_proposal_batches"]), 1)
        trial = json.loads(Path(result["trials"][1]["receipt"]).read_text())
        self.assertEqual(trial["proposal"]["kind"], "endpoint_chain")
        self.assertEqual(trial["status"], "drc_rejected")
        self.assertFalse(trial["accepted"])
        self.assertEqual(trial["native"]["opens"], 1)
        self.assertEqual(trial["steps"][0]["name"], "full_validation_substitute")

    def test_chain_batch_cannot_bind_a_changed_incumbent(self):
        from autorouter import chain_proposals as cp
        build = cp.build
        def changed(*args, **kwargs):
            batch = build(*args, **kwargs)
            best = self.output / "incumbent/candidate" / self.source.name
            best.write_bytes(best.read_bytes() + b"\n")
            return batch
        with patch.object(cp, "build", side_effect=changed):
            result = self.exercise("chains")
        self.assertFalse(result["accepted"])
        self.assertIn("incumbent changed during chain proposal", result["reason"])

    def test_changed_chain_context_after_batch_cannot_publish(self):
        from autorouter import chain_proposals as cp
        build = cp.build
        def changed(*args, **kwargs):
            batch = build(*args, **kwargs)
            path = self.output / 'chain-context/floor-final-context.json'
            path.write_bytes(path.read_bytes() + b'\n')
            return batch
        with patch.object(cp, 'build', side_effect=changed):
            result = self.exercise('chains')
        self.assertFalse(result['accepted'])
        self.assertIn('chain context', result['reason'])


    def authored_adaptive_native(self, directory, data, record):
        # Explicit process-proof substitute for control-flow cases only. Real
        # refill/final/metrics/process proofs require separate Native controls.
        if record.get('status') not in {'improvement_validated','drc_rejected','quality_rejected'} or 'reason' in record:
            return False
        guard=record.get('adaptive_trial_guard',{})
        if (record['finished_elapsed_seconds']>guard['wall_deadline_elapsed_seconds']
                or record['finished_observed_cpu_seconds']>guard['work_cpu_limit_seconds']): return False
        folder=Path(directory)/'trials'/record['id']
        self.assertEqual(p.sha(folder/'final-drc.json'),record['native_report_sha256'])
        self.assertEqual(p.parse_report(folder/'final-drc.json',Path(data['source']).name),record['native'])
        return True

    def adaptive_decision(self, result):
        from autorouter import floor_route as f
        with patch.object(s,'_adaptive_trial_native',side_effect=self.authored_adaptive_native):
            checked=s.check_adaptive_policy(self.output,result)
        self.assertEqual(checked,f.read_json(self.output/'adaptive-branch.json'))
        return checked

    def adaptive_chain_failure(self, *, extra_group_terminal=False):
        self.adaptive_probe_event='drc'
        self.source.write_text(self.source.read_text().replace('(net 1 "ordinary_signal")','(net 0 "") (net 1 "ordinary_signal")'))
        real=candidate_tree
        def separated(original):
            candidate=real(original)
            for route in p.routes(candidate):
                if sx.one(route,'net')[1]=='2':
                    for name in ('start','end'):
                        point=sx.one(route,name);point[2]=str(float(point[2])+10)
            if extra_group_terminal:
                # Keep the endpoint group distinct from the already attempted
                # whole-net deletion, which the adaptive deduplicator skips.
                candidate.append(sx.parse('(segment (start 32 22) (end 33 22) (net 1) (width 0.3) (layer "F.Cu") (uuid "separate-singleton"))'))
            return candidate
        with patch(__name__+'.candidate_tree',side_effect=separated):
            return self.exercise('adaptive')

    def test_adaptive_successful_first_single_skips_chains_and_keeps_final_checks(self):
        result=self.exercise('adaptive');decision=self.adaptive_decision(result)
        self.assertTrue(result['accepted'],result)
        self.assertEqual((decision['outcome'],decision['continuation']),('improved','feedback_singles'))
        self.assertEqual(decision['probe_trials'],['trial-0001'])
        self.assertNotIn('chain_pad_context',result)
        self.assertEqual(result['chain_context_skipped'],'adaptive improved')
        self.assertEqual(result['finalization_reserve_seconds'],40.)
        self.assertEqual(result['metrics']['track_length_mm'],8.)

    def test_adaptive_branch_rebinds_after_last_inventory_callback(self):
        result=self.exercise('adaptive');branch=self.adaptive_decision(result)
        path=self.output/'adaptive-branch.json';last=self.output/list(branch['material'])[-1]
        inventory=s._chain_context_inventory;triggered=[]
        def late(folder):
            value=inventory(folder)
            if Path(folder)==last and not triggered:
                triggered.append(True);path.write_bytes(path.read_bytes()+b' ')
            return value
        with patch.object(s,'_chain_context_inventory',side_effect=late),self.assertRaisesRegex(p.Rejected,'adaptive branch'):
            s._adaptive_branch_fresh(self.output,result)
        self.assertTrue(triggered)

    def test_adaptive_final_source_or_code_callback_invalidates_publication(self):
        from autorouter import floor_route as f
        publish=f.publish;tree_hash=p.tree_hash;sha=p.sha
        for callback in ('source','code'):
            with self.subTest(callback=callback):
                self.output=self.root/('late-'+callback);self.clock=1000.;self.process_cpu=0
                code=ROOT/'autorouter/strategy.py'
                self.publication_tools={'autorouter/strategy.py':sha(code)}
                calls=[];triggered=[]
                def mutate():
                    if len(calls)==3 and not triggered:
                        triggered.append(True);path=self.output/'adaptive-branch.json'
                        path.write_bytes(path.read_bytes()+b' ')
                def late_tree(folder):
                    value=tree_hash(folder)
                    if callback=='source' and Path(folder)==self.source.parent:mutate()
                    return value
                def late_sha(path):
                    value=sha(path)
                    if callback=='code' and Path(path)==code:mutate()
                    return value
                def guarded(output,report,stable,*args,**kwargs):
                    def observed():
                        calls.append(True);stable()
                    return publish(output,report,observed,*args,**kwargs)
                with patch.object(f,'publish',side_effect=guarded),patch.object(p,'tree_hash',side_effect=late_tree),patch.object(p,'sha',side_effect=late_sha):
                    result=self.exercise('adaptive')
                self.assertTrue(triggered)
                self.assertFalse(result['accepted'])
                self.assertFalse(json.loads((self.output/'result.json').read_text())['accepted'])
                self.assertEqual(result['status'],'invalidated')

    def test_adaptive_stop_decision_rejects_an_appended_trial(self):
        self.adaptive_probe_event='exception'
        result=self.exercise('adaptive');branch=self.adaptive_decision(result)
        self.assertEqual(branch['continuation'],'stop')
        trial_id='trial-%04d'%len(result['trials'])
        folder=self.output/'trials'/trial_id;folder.mkdir()
        record=json.loads(Path(result['trials'][-1]['receipt']).read_text())
        record['id']=trial_id;record['proposal']['route_ids']=['unseen-suffix-route']
        p.save_json(folder/'result.json',record)
        result['trials'].append(dict(id=trial_id,receipt=str(folder/'result.json'),status=record['status'],accepted=False))
        with patch.object(s,'_adaptive_trial_native',side_effect=self.authored_adaptive_native),self.assertRaisesRegex(p.Rejected,'stop.*trial'):
            s.check_adaptive_policy(self.output,result)

    def test_adaptive_duplicate_chain_does_not_skip_later_distinct_group(self):
        from autorouter import chain_proposals as cp
        build=cp.build;duplicates=[];novel=[]
        def with_duplicate(tree,*args,**kwargs):
            batch=build(tree,*args,**kwargs)
            self.assertTrue(batch['proposals'])
            group=copy.deepcopy(batch['proposals'][0]);novel.extend(group['route_ids'])
            duplicate=copy.deepcopy(group)
            first=json.loads((self.output/'trials/trial-0000/result.json').read_text())
            duplicate['route_ids']=first['proposal']['route_ids'];duplicates.extend(duplicate['route_ids'])
            batch['proposals']=[duplicate,group]
            return batch
        with patch.object(cp,'build',side_effect=with_duplicate):
            result=self.adaptive_chain_failure(extra_group_terminal=True)
        self.adaptive_decision(result)
        trials=[json.loads(Path(row['receipt']).read_text()) for row in result['trials']]
        chains=[row for row in trials if row['proposal']['kind']=='endpoint_chain']
        self.assertEqual(len(chains),1)
        self.assertEqual(chains[0]['proposal']['route_ids'],novel)
        keys=[s._adaptive_key(row['base_candidate_sha256'],row['proposal']) for row in trials]
        self.assertEqual(len(keys),len(set(keys)))
        self.assertNotEqual(set(duplicates),set(novel))
        self.assertGreater(chains[0]['finished_elapsed_seconds'],chains[0]['started_elapsed_seconds'])

    def test_adaptive_initial_quality_rejection_with_feedback_success_skips_chains(self):
        self.feedback_scenario=True
        result=self.exercise('adaptive');decision=self.adaptive_decision(result)
        self.assertTrue(result['accepted'],result)
        self.assertEqual(decision['probe_trials'],['trial-0001','trial-0002'])
        self.assertEqual(decision['outcome'],'improved')
        self.assertNotIn('chain_pad_context',result)
        trials=[json.loads(Path(row['receipt']).read_text()) for row in result['trials']]
        self.assertEqual(trials[1]['status'],'quality_rejected')
        self.assertEqual(trials[2]['status'],'improvement_validated')
        self.assertEqual(trials[2]['proposal']['parent_trial'],trials[1]['id'])

    def test_adaptive_completed_native_probe_failure_chooses_bound_chain_batch(self):
        result=self.adaptive_chain_failure(extra_group_terminal=True);decision=self.adaptive_decision(result)
        self.assertTrue(result['accepted'],result)
        self.assertEqual((decision['outcome'],decision['continuation']),('completed_rejection','chains_then_singles'))
        self.assertIn('chain_pad_context',result)
        self.assertEqual(result['chain_proposal_batches'][0]['base_candidate_sha256'],decision['after_sha256'])
        trials=[json.loads(Path(row['receipt']).read_text()) for row in result['trials']]
        self.assertEqual(trials[1]['status'],'drc_rejected')
        self.assertTrue(any(row['proposal']['kind']=='endpoint_chain' for row in trials[2:]))

    def test_adaptive_incomplete_probe_never_becomes_a_chain_rejection(self):
        for event in ('exception','timeout','crash','cancel'):
            with self.subTest(event=event):
                self.output=self.root/('run-'+event);self.clock=1000.;self.process_cpu=0
                self.adaptive_probe_event=event
                result=self.exercise('adaptive')
                self.assertNotIn('chain_pad_context',result)
                if event=='cancel':
                    self.assertEqual(result['status'],'cancelled');self.assertFalse(result['accepted'])
                else:
                    decision=self.adaptive_decision(result)
                    self.assertEqual((decision['outcome'],decision['continuation']),('incomplete','stop'))
                    self.assertEqual(len(result['trials']),2)

    def test_adaptive_no_probe_budget_is_explicit_and_does_not_request_context(self):
        self.baseline_advance=85;self.trial_storage_advance=7
        result=self.exercise('adaptive');decision=self.adaptive_decision(result)
        self.assertTrue(result['accepted'],result)
        self.assertEqual(decision['outcome'],'no_probe');self.assertEqual(decision['probe_trials'],[])
        self.assertIn(decision['reason'],{'insufficient_work_budget','preparation_exhausted'})
        self.assertNotIn('chain_pad_context',result)

    def test_adaptive_duplicate_key_is_same_base_sorted_ids_and_changed_base_may_retry(self):
        self.assertEqual(s._adaptive_key('a'*64,{'route_ids':['two','one']}),s._adaptive_key('a'*64,{'route_ids':['one','two']}))
        self.assertNotEqual(s._adaptive_key('a'*64,{'route_ids':['one']}),s._adaptive_key('b'*64,{'route_ids':['one']}))
        result=self.adaptive_chain_failure();self.adaptive_decision(result)
        trials=[json.loads(Path(row['receipt']).read_text()) for row in result['trials']]
        keys=[s._adaptive_key(row['base_candidate_sha256'],row['proposal']) for row in trials]
        self.assertEqual(len(keys),len(set(keys)))
        first=trials[1]['proposal']['route_ids']
        retried=[row for row in trials if row['proposal']['route_ids']==first]
        self.assertGreaterEqual(len(retried),2)
        self.assertGreaterEqual(len({row['base_candidate_sha256'] for row in retried}),2)

    def test_adaptive_proposals_preserve_source_protected_and_non_zone_routes(self):
        original=self.source.read_bytes();result=self.exercise('adaptive')
        self.assertEqual(self.source.read_bytes(),original)
        protected=[row for row in p.routes(sx.read(self.source)) if p.locked(row)]
        final=p.routes(sx.read(result['candidate']))
        self.assertTrue(all(row in final for row in protected))
        wanted=s.route_id(candidate_tree(sx.read(self.source))[-1])
        self.assertIn(wanted,{s.route_id(row) for row in final})

    def test_adaptive_bound_branch_cannot_claim_rejection_after_successful_probe(self):
        result=self.exercise('adaptive');self.adaptive_decision(result)
        path=self.output/'adaptive-branch.json';branch=json.loads(path.read_text())
        branch.update(outcome='completed_rejection',continuation='chains_then_singles',reason='completed_native_sequence_rejected',chain_remaining_seconds=30.)
        p.save_json(path,branch);result['adaptive_branch']['sha256']=p.sha(path)
        with patch.object(s,'_adaptive_trial_native',side_effect=self.authored_adaptive_native),self.assertRaisesRegex(p.Rejected,'adaptive branch (classification|reason)'):
            s.check_adaptive_policy(self.output,result)

    def test_adaptive_changed_probe_report_or_prefix_inventory_rejects(self):
        result=self.exercise('adaptive');self.adaptive_decision(result)
        (self.output/'trials/trial-0001/final-drc.json').write_text('tampered Native report')
        with self.assertRaisesRegex(p.Rejected,'prefix evidence changed'):
            s.check_adaptive_policy(self.output,result)

    def test_adaptive_selected_chain_cannot_omit_its_context_binding(self):
        result=self.adaptive_chain_failure();self.adaptive_decision(result)
        del result['chain_pad_context']
        with patch.object(s,'_adaptive_trial_native',side_effect=self.authored_adaptive_native),self.assertRaisesRegex(p.Rejected,'chain context binding missing'):
            s.check_chain_context(self.output,result)

    def test_adaptive_policy_cannot_lose_branch_marker_or_downgrade_to_feedback(self):
        result=self.exercise('adaptive');self.adaptive_decision(result)
        del result['adaptive_branch']
        with self.assertRaisesRegex(p.Rejected,'adaptive branch binding'):
            s.check_adaptive_policy(self.output,result)
        result['proposal_policy']='feedback'
        with self.assertRaisesRegex(p.Rejected,'another proposal policy'):
            s.check_adaptive_policy(self.output,result)

    def test_adaptive_over_deadline_native_label_is_not_a_completed_probe(self):
        record=dict(status='drc_rejected',accepted=False,steps=[],
            adaptive_trial_guard={'wall_deadline_elapsed_seconds':12.,'work_cpu_limit_seconds':80.},
            finished_elapsed_seconds=13.,finished_observed_cpu_seconds=1.)
        self.assertFalse(s._adaptive_trial_native(self.output,{'budget_seconds':120.,'cpu_budget_seconds':120.},record))


class AdaptiveNativeJournalControls(unittest.TestCase):
    """Worker/checker interoperability with actual command builder; no Native run."""
    def setUp(self):
        from autorouter import floor_route as f
        self.f = f
        scratch = ROOT / '.cache' / 'adaptive-journal-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.folder = self.root / 'trials/trial-0000'
        self.job = p.Job(self.folder, 120, protect_local_settings=True)
        self.candidate = self.folder / 'candidate/test.kicad_pcb'
        self.candidate.parent.mkdir()
        tree = sx.parse('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (31 "B.Cu" signal)))')
        sx.write(self.candidate, tree)
        self.candidate.with_suffix('.kicad_pro').write_text('{}\n')
        shutil.copyfile(self.candidate, self.folder / 'pre-refill.kicad_pcb')
        shutil.copytree(self.candidate.parent, self.folder / 'refill')
        self.measure = {'track_length_mm': 10., 'vias': 0, 'version': '10.0.0'}
        report = self.folder / 'final-drc.json'
        report.write_text(json.dumps(native_report(self.candidate.name)))
        self.native = p.parse_report(report, self.candidate.name)

        def retained_step(name, argv):
            # Exercise the existing Job.native argv builder, retaining its real
            # expected journal form. The process itself is explicitly substituted.
            worker = dict(name=name, argv=[str(x) for x in argv], cwd=str(self.folder),
                          status='success', exit_code=0, cleanup_complete=True)
            p.save_json(self.folder / (name + '-process.json'), worker)
            self.job.steps.append(worker)
            p.save_json(self.folder / 'metrics.json', self.measure)
            return worker
        with patch.object(self.job, 'step', side_effect=retained_step):
            self.job.native('metrics', 'metrics', self.candidate, self.folder / 'metrics.json')
        self.data = dict(source=str(self.root / 'source/test.kicad_pcb'),
                         source_hashes=p.tree_hash(self.candidate.parent),
                         budget_seconds=120., cpu_budget_seconds=120.)
        self.record = dict(id='trial-0000', status='improvement_validated', accepted=True,
                           adaptive_trial_guard=dict(wall_deadline_elapsed_seconds=80., work_cpu_limit_seconds=80.),
                           finished_elapsed_seconds=1., finished_observed_cpu_seconds=1.,
                           candidate_sha256=p.sha(self.candidate), native_report_sha256=p.sha(report),
                           native=self.native, metrics=self.measure, steps=self.job.steps)

    def stage(self, *args, **kwargs):
        self.assertIs(kwargs.get('sandboxed'), False)
        return self.native

    def test_standard_native_worker_journal_and_drc_contract_match_checker(self):
        with patch.object(self.f, 'check_drc_stage', side_effect=self.stage) as drc:
            self.assertTrue(s._adaptive_trial_native(self.root, self.data, self.record))
        self.assertEqual(drc.call_count, 2)

    def test_sandbox_prefix_cannot_be_added_to_a_standard_native_metrics_journal(self):
        changed = copy.deepcopy(self.record)
        changed['steps'][0]['argv'] = [*self.f.SANDBOX, *changed['steps'][0]['argv']]
        p.save_json(self.folder / 'metrics-process.json', changed['steps'][0])
        with patch.object(self.f, 'check_drc_stage', side_effect=self.stage), self.assertRaisesRegex(p.Rejected, 'provenance'):
            s._adaptive_trial_native(self.root, self.data, changed)


class FeedbackSelectionTests(unittest.TestCase):
    def setUp(self):
        original = sx.parse(BOARD)
        self.tree = candidate_tree(original)
        self.protected = [route for route in p.routes(original) if p.locked(route)]
        self.nets = s.zone_net_ids(original)
        self.root_proposal = s.proposals(self.tree, self.nets, self.protected, False)[0]
        self.failed = s.delete_routes(self.tree, self.root_proposal["route_ids"], self.nets, self.protected)
        self.baseline = {"opens": 0, "blocking": 0, "warnings": 0, "exclusions": 0, "ignored_checks": [], "findings": []}
        self.native = dict(self.baseline, findings=[self.warning("tool-short")])

    @staticmethod
    def warning(identifier, kind="track_dangling"):
        return {"severity": "warning", "type": kind, "items": [{"uuid": identifier}]}

    def decide(self):
        return s.feedback_proposal(self.failed, self.root_proposal, self.native, self.baseline,
                                   self.nets, self.protected)

    def test_warning_uses_exact_remaining_owned_uuid_and_cumulative_ids(self):
        decision = self.decide()
        self.assertTrue(decision["proposed"], decision)
        proposal = decision["proposal"]
        self.assertEqual(proposal["feedback_depth"], 1)
        self.assertEqual(proposal["feedback_added_routes"], 1)
        self.assertEqual(proposal["added_route_uuids"], ["tool-short"])
        result = s.delete_routes(self.tree, proposal["route_ids"], self.nets, self.protected)
        self.assertIn(self.protected[0], p.routes(result))
        self.assertIn(p.routes(self.tree)[-1], p.routes(result))

    def test_all_native_failure_categories_block_feedback(self):
        for key in ("opens", "blocking", "exclusions"):
            with self.subTest(key=key):
                self.native[key] = 1
                self.assertFalse(self.decide()["proposed"])
                self.native[key] = 0

    def test_other_new_warning_never_permits_cleanup(self):
        self.native["findings"].append(self.warning("tool-short", "clearance"))
        self.assertFalse(self.decide()["proposed"])

    def test_existing_warning_is_allowed_but_never_drives_deletion(self):
        old = self.warning("footprint", "lib_footprint_mismatch")
        self.baseline["findings"] = [old]
        self.native["findings"].append(copy.deepcopy(old))
        self.assertTrue(self.decide()["proposed"])
        self.baseline["findings"] = copy.deepcopy(self.native["findings"])
        self.assertFalse(self.decide()["proposed"])

    def test_protected_other_net_missing_and_nonroute_refs_refused(self):
        for identifier in ("protected", "unrelated-ground-name", "absent", "plane-zone", "tool-long"):
            with self.subTest(identifier=identifier):
                self.native["findings"] = [self.warning(identifier)]
                self.assertFalse(self.decide()["proposed"])

    def test_duplicate_uuid_routes_or_nonroute_objects_are_ambiguous(self):
        for node in (track("tool-short", 1, 1), sx.parse('(zone (net 1) (uuid "tool-short"))')):
            with self.subTest(kind=node[0]):
                self.failed.append(node)
                self.assertFalse(self.decide()["proposed"])
                self.failed.pop()

    def test_malformed_or_repeated_finding_items_refused(self):
        for items in ([], [{}], [{"uuid": ""}], [{"uuid": "tool-short"}, {"uuid": "tool-short"}], ["tool-short"]):
            with self.subTest(items=items):
                self.native["findings"][0]["items"] = items
                self.assertFalse(self.decide()["proposed"])

    def test_depth_and_added_route_caps_refuse_more_work(self):
        self.root_proposal["feedback_depth"] = s.MAX_FEEDBACK_DEPTH
        self.assertFalse(self.decide()["proposed"])
        self.root_proposal["feedback_depth"] = 0
        self.root_proposal["feedback_added_routes"] = s.MAX_FEEDBACK_ADDED_ROUTES
        self.assertFalse(self.decide()["proposed"])

    def test_stale_candidate_with_preceding_route_still_present_refused(self):
        self.failed = copy.deepcopy(self.tree)
        self.assertFalse(self.decide()["proposed"])


if __name__ == "__main__":
    unittest.main()
