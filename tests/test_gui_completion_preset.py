"""Preset intent and stale-control regressions; no actual GUI qualification."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from autorouter import gui, preferences as pref


class CompletionPresetTests(unittest.TestCase):
    def test_changes_search_only_for_both_routing_scopes(self):
        for scope in ('whole_board_unlocked_routing', 'partial_completion'):
            original = pref.validate(dict(pref.DEFAULTS, scope=scope, seconds=91,
                                          scoring_preference='via_high'))
            before = copy.deepcopy(original)
            actual = gui.completion_search_preset(original)
            self.assertEqual(actual, dict(before, profile='tuned', scoring_preference='via_low'))
            self.assertEqual(original, before)

    def test_incompatible_problem_is_refused_without_rewriting_settings(self):
        for changes in (dict(layers=['F.Cu'], profile='completion-only'), dict(adapter='none'),
                        dict(scope='selected_nets', profile='completion-only', nets=['one'])):
            original = pref.validate(dict(pref.DEFAULTS, **changes)); before = copy.deepcopy(original)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                gui.completion_search_preset(original)
            self.assertEqual(original, before)

    def test_saved_configuration_retains_preset_and_budget(self):
        import json
        import tempfile
        requested = gui.completion_search_preset(dict(pref.DEFAULTS, seconds=123))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'completion.json'
            path.write_text(json.dumps(requested))
            self.assertEqual(pref.resolve(pref.load(path)), requested)
        self.assertEqual(requested['seconds'], 123)

    def callback(self, name='completion_preset'):
        tree = ast.parse(Path(gui.__file__).read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        window = next(n for n in main.body if isinstance(n, ast.ClassDef) and n.name == 'Window')
        method = next(n for n in window.body if isinstance(n, ast.FunctionDef) and n.name == name)
        namespace = dict(__name__='autorouter.gui', __package__='autorouter',
                         method_for_index=gui.method_for_index,
                         _check_source_guard=gui._check_source_guard,
                         completion_search_preset=gui.completion_search_preset)
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(gui.__file__), 'exec'), namespace)
        return namespace[name]

    def fake(self, method=0):
        state = SimpleNamespace(busy=False, chooser=None, input_generation=7, flow=object(),
                                messages=[], refreshes=0, inspected_value=True)
        state.method = SimpleNamespace(GetSelection=lambda: method)
        state.board = SimpleNamespace(GetValue=lambda: '/owned/board.kicad_pcb')
        state.values = dict(profile=[('Standard','standard'),('More search','tuned')],
                            scoring_preference=[('Default',None),('Low','via_low')])
        state.selected = {}; state.choices = {
            name: SimpleNamespace(SetSelection=lambda i, name=name: state.selected.__setitem__(name,i))
            for name in state.values}
        state.config = lambda: dict(pref.DEFAULTS, scope='partial_completion', seconds=93)
        state.inspected = SimpleNamespace(SetValue=lambda v: setattr(state,'inspected_value',v))
        state.status = SimpleNamespace(SetLabel=state.messages.append)
        state.log = SimpleNamespace(SetValue=state.messages.append)
        state.method_note = SimpleNamespace(SetLabel=state.messages.append, Wrap=lambda _: None,
                                            GetParent=lambda: SimpleNamespace(Layout=lambda: None))
        state.refresh = lambda: setattr(state,'refreshes',state.refreshes+1)
        state.refused = state.messages.append
        return state

    def test_explicit_preset_revokes_old_accept_export_controls(self):
        state = self.fake(); self.callback()(state, None)
        self.assertIsNone(state.flow)
        self.assertFalse(state.inspected_value)
        self.assertEqual(state.input_generation, 8)
        self.assertEqual(state.selected, dict(profile=1, scoring_preference=1))
        self.assertEqual(state.config()['seconds'], 93)
        self.assertEqual(state.refreshes, 1)
        self.assertTrue(any('Earlier findings are no longer current' in item for item in state.messages))

    def test_preset_revokes_hidden_old_proposal(self):
        state=self.fake(); state.pending_proposal=object()
        self.callback()(state,None)
        self.assertIsNone(state.pending_proposal)

    def test_method_change_revokes_hidden_old_proposal(self):
        state=self.fake(); state.pending_proposal=object()
        self.callback('method_changed')(state,SimpleNamespace(Skip=lambda: None))
        self.assertIsNone(state.pending_proposal)

    def test_old_proposal_generation_cannot_override_new_settings(self):
        state=self.fake(); state.pending_proposal=({}, {}, state.input_generation-1)
        self.callback('apply_proposal')(state,None)
        self.assertIn('Settings or method changed',state.messages[-1])
        self.assertFalse(state.selected)

    def test_improve_is_not_silently_changed_to_routing(self):
        state = self.fake(method=1); old_flow=state.flow
        self.callback()(state, None)
        self.assertIs(state.flow, old_flow)
        self.assertFalse(state.selected)
        self.assertEqual(state.input_generation, 7)
        self.assertIn('Select Route first', state.messages[-1])


if __name__ == '__main__':
    unittest.main()
