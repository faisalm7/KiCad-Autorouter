"""Real controller/API budget controls; no wx, Native or routing qualification."""
import json
import unittest
from unittest.mock import patch

from autorouter import gui, preferences as pref, pipeline as p, review_export as export_api
from tests import test_gui as gt


class GuiExportBudgetTests(unittest.TestCase):
    setUp = gt.GuiWorkflowTests.setUp
    request = gt.GuiWorkflowTests.request
    flow = gt.GuiWorkflowTests.flow

    def test_captured_routing_and_export_command_keep_separate_allocations(self):
        for route_seconds, export_seconds in ((5, 30), (29, 30), (30, 30), (90, 90),
                                               (120, 120), (121, 120), (420, 120), (900, 120)):
            with self.subTest(route_seconds=route_seconds):
                self.settings = dict(pref.DEFAULTS, seconds=route_seconds)
                flow = self.flow()
                settings_path = flow.workspace / 'settings.json'
                captured_bytes = settings_path.read_bytes()
                self.assertEqual(json.loads(captured_bytes), self.settings)
                self.assertEqual(flow.settings_bytes, captured_bytes)
                flow.ready.add('preview')
                route = flow.command('route')
                self.assertEqual(route[4], 'route')
                self.assertEqual(route[route.index('--settings') + 1], str(settings_path))
                self.assertEqual(flow.timeout('route'), route_seconds + 45)
                # Readiness and choice are synthetic; no accepted routing/review is claimed.
                flow.ready.update(('route', 'review', 'choice')); flow.choice = 'accept'
                export = flow.command('export')
                self.assertEqual(export[4:6], ['review-export',
                    str(flow.workspace / 'choice/choice.json')])
                allocation = export[export.index('--seconds') + 1]
                self.assertEqual(allocation, str(export_seconds))
                self.assertEqual(export_api.validate_seconds(float(allocation)), export_seconds)
                self.assertEqual(gui.export_validation_seconds(route_seconds), export_seconds)
                self.assertEqual(flow.timeout('export'), export_seconds + 45)
                self.assertEqual(settings_path.read_bytes(), captured_bytes)
                self.assertEqual(json.loads(flow.settings_bytes)['seconds'], route_seconds)
                flow.fresh()
        for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
            self.assertEqual(self.board.with_suffix(suffix).read_bytes(), b'owned synthetic source\n')

    def test_preview_findings_disclose_additional_export_budget_without_changing_route_budget(self):
        for route_seconds, export_seconds in ((5, 30), (29, 30), (30, 30), (90, 90),
                                               (120, 120), (121, 120), (420, 120), (900, 120)):
            with self.subTest(route_seconds=route_seconds):
                settings = dict(pref.DEFAULTS, seconds=route_seconds)
                text = gui.human_summary('preview', dict(status='preview', effective_preferences=settings))
                self.assertIn('routing budget ' + str(route_seconds) + ' s', text)
                self.assertIn('Additional Native export-validation budget: ' + str(export_seconds)
                              + ' s after acceptance, separate from routing', text)
                self.assertIn('the routing budget is unchanged', text)
                self.assertEqual(settings['seconds'], route_seconds)

    def test_invalid_routing_budget_is_refused_before_creating_workspace(self):
        for value in (None, True, False, '90', float('nan'), float('inf'), -1, 4.9, 900.1, [], {}):
            with self.subTest(value=value):
                self.settings = dict(pref.DEFAULTS, seconds=value)
                with self.assertRaises(pref.PreferenceError): self.flow()
                with self.assertRaises(pref.PreferenceError): gui.export_validation_seconds(value)
                self.assertEqual(list(self.output.iterdir()), [])

    def test_explicit_export_api_keeps_its_original_strict_bounds(self):
        for value in (None, True, False, '90', float('nan'), float('inf'), -1, 5, 29, 120.1, 121, 420, 900, [], {}):
            with self.subTest(value=value), patch.object(export_api, 'bind') as bind:
                with self.assertRaises(p.Rejected): export_api.validate_seconds(value)
                with self.assertRaises(p.Rejected):
                    export_api.export(self.root / 'missing-choice.json', self.root / 'never-created', value)
                bind.assert_not_called()
                self.assertFalse((self.root / 'never-created').exists())
        for value in (30, 30.5, 90, 120):
            with self.subTest(value=value): self.assertEqual(export_api.validate_seconds(value), value)


if __name__ == '__main__':
    unittest.main()
