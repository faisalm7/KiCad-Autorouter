"""Actual findings callback display controls; no wx or Native qualification."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from autorouter import preferences as pref
from tests.test_gui import window_method


class RecoveryBudgetDisplayTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve()
        self.settings_bytes = json.dumps(dict(pref.DEFAULTS, seconds=420)).encode()
        self.route = dict(status='routing_accepted', strategy='native_validated_thermal_bridge',
                          scope='whole_board_unlocked_routing', budget_seconds=420,
                          cpu_budget_seconds=420, engine_profile='standard', adapter='both',
                          native=dict(opens=0, blocking=0, warnings=22, exclusions=0))
        self.review = dict(status='ready_for_manual_review', budget_seconds=60, cpu_budget_seconds=60)
        self.choice = dict(choice_recorded=True, choice='accept', budget_seconds=60)
        self.export = dict(status='export_validated', export_accepted=True,
                           budget_seconds=120, cpu_budget_seconds=120)
        self.records = dict(route=self.route, review=self.review, choice=self.choice, export=self.export)
        self.receipt_bytes = {}
        for stage, record in self.records.items():
            path = self.workspace / stage / ('result.json' if stage == 'route' else stage + '.json')
            path.parent.mkdir()
            raw = (json.dumps(record, sort_keys=True) + '\n').encode()
            path.write_bytes(raw)
            self.receipt_bytes[path] = raw

    def findings(self, stage, record, *, method='recover'):
        flow = SimpleNamespace(records=self.records, settings_bytes=self.settings_bytes,
                               workspace=self.workspace, method=method)
        job = Mock()
        window = SimpleNamespace(job=job, busy=True, flow=None, log=Mock(), status=Mock(),
                                 refresh=Mock(), closing=False, refused=Mock())
        before = copy.deepcopy(self.records)
        original_record = copy.deepcopy(record)
        window_method('finished')(window, job, flow, stage, record, None)
        window.refused.assert_not_called()
        self.assertEqual(self.records, before)
        self.assertEqual(record, original_record)
        self.assertEqual(flow.settings_bytes, self.settings_bytes)
        for path, raw in self.receipt_bytes.items():
            self.assertEqual(path.read_bytes(), raw)
        return window.log.SetValue.call_args.args[0]

    def test_recovery_route_review_accept_and_export_show_captured_method_budget(self):
        # Export's callback receives the readback and then merges the stored
        # export receipt, whose120seconds differs from the420second method.
        stages = [('route', self.route), ('review', self.review), ('choice', self.choice),
                  ('export', dict(current=True, export_accepted=True))]
        for stage, record in stages:
            with self.subTest(stage=stage):
                text = self.findings(stage, record)
                self.assertRegex(text, r'(?i)whole recovery-method budget[: ]+420 s')
                self.assertIn('Additional Native export-validation budget: 120 s', text)
                self.assertNotRegex(text, r'(?i)whole recovery-method budget[: ]+(?:30|120) s')
                self.assertIn('22 warnings', text)
        self.assertEqual(self.review['budget_seconds'], 60)
        self.assertEqual(self.export['budget_seconds'], 120)

    def test_ordinary_route_display_keeps_its_existing_settings_meaning(self):
        self.route.pop('strategy')
        self.route['routing_preferences'] = dict(effective=dict(pref.DEFAULTS, seconds=420))
        text = self.findings('review', self.review, method='route')
        self.assertIn('routing budget 420 s', text)
        self.assertNotIn('whole recovery-method budget', text)
        self.assertIn('Additional Native export-validation budget: 120 s', text)


if __name__ == '__main__':
    unittest.main()
