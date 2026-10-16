"""Owned project/static controls only; no native profile enforcement claim."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from autorouter import netclass as n, pipeline as p

ROOT = next(path for path in Path(__file__).resolve().parents if (path/'autorouter/runner.py').is_file())
FIXTURE = ROOT/'tests/fixtures/board-floor/fixture.kicad_pcb'


def project():
    return json.loads(FIXTURE.with_suffix('.kicad_pro').read_text())


class TuningIntentGuard(unittest.TestCase):
    def test_absent_and_empty_profiles_preserve_input(self):
        for definitions in (None, {}, {'meta': {'version': 0}, 'tuning_profiles_impedance_geometric': []}):
            value = project()
            value['net_settings']['classes'][0].pop('tuning_profile', None)
            if definitions is not None:
                value['tuning_profiles'] = definitions
            for explicit_empty in (False, True):
                if explicit_empty:
                    value['net_settings']['classes'][0]['tuning_profile'] = ''
                before = copy.deepcopy(value)
                self.assertIsNone(n.reject_tuning_intent(value))
                self.assertEqual(value, before)

    def test_default_and_unused_named_profile_both_rejected(self):
        for name in ('Default', 'UnusedSupply'):
            value = project()
            if name == 'Default':
                cls = value['net_settings']['classes'][0]
            else:
                cls = copy.deepcopy(value['net_settings']['classes'][0]); cls['name'] = name
                value['net_settings']['classes'].append(cls)
            cls['tuning_profile'] = 'OwnedMissingProfile'
            before = copy.deepcopy(value)
            with self.assertRaisesRegex(ValueError, 'Netclass tuning profiles not qualified'):
                n.reject_tuning_intent(value)
            self.assertEqual(value, before)

    def test_unassigned_nonempty_definitions_are_rejected(self):
        for rows in ([{'profile_name': 'OwnedUnusedProfile'}], [{}]):
            value = project()
            value['tuning_profiles'] = {'meta': {'version': 0}, 'tuning_profiles_impedance_geometric': rows}
            with self.assertRaisesRegex(ValueError, 'Tuning profile definitions not qualified'):
                n.reject_tuning_intent(value)

    def test_recognized_field_malformed_values_are_not_absence(self):
        for raw in (None, False, 0, [], {}):
            value = project(); value['net_settings']['classes'][0]['tuning_profile'] = raw
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'Malformed netclass tuning profile'):
                n.reject_tuning_intent(value)
        for raw in (None, [], {'meta': {'version': True}}, {'future_profiles': []},
                    {'tuning_profiles_impedance_geometric': False}):
            value = project(); value['tuning_profiles'] = raw
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                n.reject_tuning_intent(value)

    def test_ordinary_meander_preferences_are_not_profile_assignments(self):
        value = project()
        value['board']['design_settings']['tuning_pattern_settings'] = {
            'single_track_defaults': {'corner_radius_percentage': 80, 'spacing': 0.6}}
        before = copy.deepcopy(value)
        self.assertIsNone(n.reject_tuning_intent(value))
        self.assertEqual(value, before)

    def test_native_mapping_entry_still_rejects_tuning_intent(self):
        value = project(); value['net_settings']['classes'][0]['tuning_profile'] = 'OwnedMissingProfile'
        with self.assertRaisesRegex(ValueError, 'Netclass tuning profiles not qualified'):
            n.qualify_project(value)
        value = project(); value['tuning_profiles'] = {'tuning_profiles_impedance_geometric': [{'profile_name': 'Owned'}]}
        with self.assertRaisesRegex(ValueError, 'Tuning profile definitions not qualified'):
            n.qualify_project(value)


class DefaultPreflightGuard(unittest.TestCase):
    def check_project(self, value, expected_error=None):
        with tempfile.TemporaryDirectory() as tmp:
            board = Path(tmp).resolve()/FIXTURE.name
            board.write_bytes(FIXTURE.read_bytes())
            pro = board.with_suffix('.kicad_pro'); pro.write_text(json.dumps(value))
            before = (board.read_bytes(), pro.read_bytes())
            if expected_error:
                with self.assertRaisesRegex(p.Rejected, expected_error):
                    p.preflight(board)
            else:
                self.assertEqual(p.preflight(board)[0], 'kicad_pcb')
            self.assertEqual((board.read_bytes(), pro.read_bytes()), before)

    def test_real_preflight_rejects_default_before_early_return(self):
        value = project(); value['net_settings']['classes'][0]['tuning_profile'] = 'OwnedMissingProfile'
        self.check_project(value, 'Netclass tuning profiles not qualified')
        value = project(); value['tuning_profiles'] = {'tuning_profiles_impedance_geometric': [{'profile_name': 'Owned'}]}
        self.check_project(value, 'Tuning profile definitions not qualified')

    def test_real_preflight_preserves_inactive_settings_and_meander_preferences(self):
        value = project(); self.check_project(value)
        value['net_settings']['classes'][0]['tuning_profile'] = ''
        value['tuning_profiles'] = {'meta': {'version': 0}, 'tuning_profiles_impedance_geometric': []}
        value['board']['design_settings']['tuning_pattern_settings'] = {'single_track_defaults': {'spacing': 0.6}}
        self.check_project(value)


if __name__ == '__main__':
    unittest.main()
