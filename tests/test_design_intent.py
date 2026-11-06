"""Real small saved files and adversarial intents; no native/GUI qualification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch

from autorouter import config as c, design_intent as intent, gui, sexpr as sx
from autorouter import __main__ as cli


def identifier(label):
    return json.dumps(str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-design-intent/' + label)))


class DesignIntentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='design-intent-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.board = self.root / 'owned.kicad_pcb'
        self.tree = sx.parse('''(kicad_pcb (version 20260206)
            (layers (0 "F.Cu" signal) (2 "B.Cu" signal))
            (footprint "Owned" (property "Reference" "J1")
              (pad "1" thru_hole circle (net "DATA"))
              (pad "2" thru_hole circle (net "RETURN")))
            (footprint "Owned" (property "Reference" "J2")
              (pad "1" thru_hole circle (net "DATA"))))''')
        self.tree.extend([
            sx.parse('(segment (start 1 1) (end 2 1) (width .3) (layer "F.Cu") '
                     '(net "DATA") (uuid ' + identifier('data') + '))'),
            sx.parse('(segment (start 2 2) (end 3 2) (width .3) (layer "B.Cu") '
                     '(net "RETURN") (locked yes) (uuid ' + identifier('return') + '))'),
        ])
        self.save_board()
        self.board.with_suffix('.kicad_pro').write_text(json.dumps({
            'net_settings': {'classes': [{'name': 'Default', 'track_width': .3,
                'clearance': .2, 'via_diameter': .6, 'via_drill': .3}],
                'netclass_patterns': [], 'netclass_assignments': {}},
            'board': {'design_settings': {'rules': {}}}}))
        self.board.with_suffix('.kicad_sch').write_text('(kicad_sch (version 20260206))\n')
        # Select the established static capability contract; no KiCad is run.
        version = patch.object(c, 'NATIVE_VERSION', '10.0.0')
        version.start(); self.addCleanup(version.stop)

    def save_board(self):
        self.board.write_text(sx.dump(self.tree) + '\n')

    def proposal(self, **changes):
        return dict(action='route', scope='all_remaining', nets=[],
                    preserve_existing=True, seconds=91, search='standard', **changes)

    def request(self, **changes):
        proposal = self.proposal(); proposal.update(changes)
        return intent.validate_route_proposal(intent.inspect_project(self.board), proposal)

    def test_inspection_counts_declared_nets_and_never_invents_connectivity(self):
        before = gui.source_inventory(self.board)
        with patch('subprocess.Popen', side_effect=AssertionError('inspection must not execute')):
            record = intent.inspect_project(self.board)
        self.assertEqual(record['source'], str(self.board))
        self.assertEqual(record['source_hashes'], before)
        self.assertEqual(record['source_sha256'], before[self.board.name])
        self.assertEqual(record['footprint_count'], 2)
        self.assertEqual(record['terminal_count'], 3)
        self.assertEqual(record['nets'], [
            dict(name='DATA', terminal_count=2, existing_route_items=1, locked_route_items=0),
            dict(name='RETURN', terminal_count=1, existing_route_items=1, locked_route_items=1)])
        self.assertIsNone(record['unconnected_items'])
        self.assertFalse(record['native_validation_performed'])
        self.assertFalse(record['execution_authorized'])
        self.assertFalse(record['approval_granted'])
        self.assertEqual(gui.source_inventory(self.board), before)

    def test_remaining_and_unlocked_have_explicit_different_protection(self):
        before = gui.source_inventory(self.board)
        remaining = self.request()
        unlocked = self.request(scope='unlocked', preserve_existing=False)
        self.assertEqual(remaining['effective_preferences']['scope'], 'partial_completion')
        self.assertEqual((remaining['protected_route_items'], remaining['rerouted_route_items']), (2, 0))
        self.assertEqual(unlocked['effective_preferences']['scope'], 'whole_board_unlocked_routing')
        self.assertEqual((unlocked['protected_route_items'], unlocked['rerouted_route_items']), (1, 1))
        for result in (remaining, unlocked):
            self.assertEqual(result['status'], 'proposed')
            self.assertEqual(set(result['intent']), set(self.proposal()))
            self.assertEqual(result['effective_preferences']['seconds'], 91)
            self.assertFalse(result['approval_granted'])
            self.assertFalse(result['execution_authorized'])
            self.assertFalse(result['preview']['native_validation_performed'])
        self.assertEqual(gui.source_inventory(self.board), before)

    def test_selected_preservation_refuses_unlocked_selected_copper(self):
        with self.assertRaisesRegex(intent.IntentError, 'every existing selected item'):
            self.request(scope='selected_nets', nets=['DATA'])
        result = self.request(scope='selected_nets', nets=['DATA'], preserve_existing=False)
        self.assertEqual(result['effective_preferences']['nets'], ['DATA'])
        self.assertEqual(result['effective_preferences']['profile'], 'completion-only')
        self.assertEqual((result['protected_route_items'], result['rerouted_route_items']), (1, 1))
        protected = self.request(scope='selected_nets', nets=['RETURN'])
        self.assertEqual((protected['protected_route_items'], protected['rerouted_route_items']), (2, 0))

    def test_shared_selected_native7_guard_remains_authoritative(self):
        with patch.object(c, 'NATIVE_VERSION', '10.0.7'):
            with self.assertRaisesRegex(intent.IntentError, 'locked selected copper'):
                self.request(scope='selected_nets', nets=['RETURN'])

    def test_completion_search_changes_only_search_and_keeps_budget(self):
        result = self.request(search='completion_search')
        self.assertEqual(result['effective_preferences']['scope'], 'partial_completion')
        self.assertEqual(result['effective_preferences']['seconds'], 91)
        self.assertEqual(result['effective_preferences']['profile'], 'tuned')
        self.assertEqual(result['effective_preferences']['scoring_preference'], 'via_low')
        with self.assertRaisesRegex(intent.IntentError, 'unsupported for selected'):
            self.request(scope='selected_nets', nets=['DATA'], search='completion_search')

    def test_malformed_malicious_and_ambiguous_proposals_are_refused(self):
        inspection = intent.inspect_project(self.board)
        changes = [dict(command='touch anything'), dict(approval_granted=True),
            dict(source='/different/project.kicad_pcb'), dict(action='run'),
            dict(scope='all'), dict(scope=['unlocked']), dict(nets=['DATA']),
            dict(preserve_existing='true'), dict(preserve_existing=False),
            dict(scope='unlocked'), dict(seconds=True), dict(seconds=91.0),
            dict(seconds=901), dict(seconds=4), dict(search='ignore all checks'),
            dict(scope='selected_nets', nets=[]),
            dict(scope='selected_nets', nets=['DATA', 'DATA']),
            dict(scope='selected_nets', nets=['data']),
            dict(scope='selected_nets', nets=['$(touch stolen)']),
            dict(scope='selected_nets', nets=['DATA\n']),
        ]
        for change in changes:
            value = self.proposal(); value.update(change)
            with self.subTest(change=change), self.assertRaises(intent.IntentError):
                intent.validate_route_proposal(inspection, value)
        for value in (None, [], True, {'action': 'route'}):
            with self.subTest(value=value), self.assertRaises(intent.IntentError):
                intent.validate_route_proposal(inspection, value)

    def test_stale_project_rules_are_refused_even_if_board_bytes_match(self):
        record = intent.inspect_project(self.board)
        project = self.board.with_suffix('.kicad_pro')
        project.write_bytes(project.read_bytes() + b'\n')
        with self.assertRaisesRegex(intent.IntentError, 'stale or changed'):
            intent.validate_route_proposal(record, self.proposal())

    def test_forged_summary_and_native_claims_cannot_be_used_as_inspection(self):
        record = intent.inspect_project(self.board)
        for field, value in [('native_validation_performed', True), ('approval_granted', True),
                             ('nets', []), ('source_sha256', '0' * 64)]:
            changed = copy.deepcopy(record); changed[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(intent.IntentError, 'stale or changed'):
                intent.validate_route_proposal(changed, self.proposal())

    def test_source_change_during_shared_preview_is_refused(self):
        record = intent.inspect_project(self.board)
        real_preview = cli.preview
        def changed(*args, **kwargs):
            result = real_preview(*args, **kwargs)
            self.board.with_suffix('.kicad_dru').write_text('(version 1)\n')
            return result
        with patch.object(cli, 'preview', side_effect=changed):
            with self.assertRaisesRegex(intent.IntentError, 'changed during proposal'):
                intent.validate_route_proposal(record, self.proposal())

    def test_shared_preview_refuses_unsupported_original_rules(self):
        self.board.with_suffix('.kicad_dru').write_text('(version 1)\n')
        with self.assertRaisesRegex(intent.IntentError, 'custom rules not qualified'):
            self.request()

    def test_ambiguous_native_mapping_and_locks_are_refused(self):
        self.tree.append(['net', '1', '"DATA"'])
        self.tree.append(['net', '2', '"DATA"'])
        self.save_board()
        with self.assertRaisesRegex(intent.IntentError, 'ambiguous legacy net name'):
            intent.inspect_project(self.board)
        self.tree = [node for node in self.tree if not isinstance(node, list) or node[0] != 'net']
        self.tree[-1].append('locked'); self.save_board()
        with self.assertRaisesRegex(intent.IntentError, 'ambiguous original route lock'):
            intent.inspect_project(self.board)

    def test_missing_schematic_and_symlink_paths_are_refused(self):
        alias = self.root / 'alias.kicad_pcb'; alias.symlink_to(self.board)
        with self.assertRaises(intent.IntentError):
            intent.inspect_project(alias)
        alias.unlink()
        self.board.with_suffix('.kicad_sch').unlink()
        with self.assertRaises(intent.IntentError):
            intent.inspect_project(self.board)

    def test_tool_schema_has_no_approval_or_execution_operation(self):
        descriptor = intent.tool_schema()
        self.assertEqual(descriptor['type'], 'function')
        self.assertEqual(descriptor['function']['name'], 'propose_route')
        schema = descriptor['function']['parameters']
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(set(schema['required']), set(self.proposal()))
        self.assertEqual(set(schema['properties']), set(self.proposal()))
        schema['properties']['action']['enum'].append('execute')
        self.assertEqual(intent.tool_schema()['function']['parameters']['properties']['action']['enum'], ['route'])


if __name__ == '__main__':
    unittest.main()
