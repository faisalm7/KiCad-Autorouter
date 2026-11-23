"""Controlled Responses replies and exact local review. No external inference."""
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from autorouter import conversation, design_intent as design, gui, hosted_intent as hosted
from autorouter import placement_gui, placement_intent
from experiments.placement_native_proposal_v1 import multipad_fixture
from tests.test_hosted_intent import KEY, response, tagged


class ConversationChecks(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='copperpath-conversation-', dir=Path.cwd())
        self.addCleanup(tmp.cleanup)
        self.workspace = Path(tmp.name)
        self.board = multipad_fixture.write_project(self.workspace / 'source')
        self.inspection = placement_intent.inspect_saved(self.board)
        self.controls = dict(selected=[], fixed=[], region_nm=None,
            region_limit_nm=[7_000_000, 7_000_000, 31_000_000, 13_000_000],
            route_seconds=90, policy=dict(scope=self.inspection['observation']['scope']))
        self.settings = dict(selected_refs=['J1', 'J2'],
                             region_nm=[8_000_000, 8_000_000, 30_000_000, 12_000_000],
                             route_seconds=75)

    def hosted_turn(self, name, arguments, history, text, revision, *, ledger_name):
        binding = dict(request=text, revision=revision, source=str(self.board))
        review = design.PlacementConstraintReview(self.inspection, self.controls, request=text, revision=revision)
        ledger = self.workspace / ledger_name
        prepared = hosted.prepare_conversation(review, text, history, inspection=self.inspection)
        self.assertNotIn(str(self.board).encode(), prepared['body'])
        self.assertNotIn(KEY.encode(), prepared['body'])
        consent = hosted.make_consent(prepared, ledger_path=ledger)
        consent['approved'] = True
        with patch.object(hosted, '_run_worker', return_value=(tagged(response(arguments, name=name)), {})) as transport:
            result = hosted.propose_conversation(review, self.controls, binding, history, self.inspection,
                                                  credential=KEY, consent=consent, ledger_path=ledger)
        transport.assert_called_once()
        packet = json.loads(prepared['body'])
        sent = json.loads(packet['input'][0]['content'])
        self.assertEqual(sent['conversation_history'], history)
        self.assertIs(packet['store'], False)
        return review, binding, result

    def test_editor_notes_stay_local_and_follow_the_exact_saved_design(self):
        history = conversation.Conversation()
        files = {self.board.with_suffix(ext).name: self.inspection['source_hashes'][self.board.with_suffix(ext).name]
                 for ext in conversation.DESIGN_SUFFIXES}
        context = dict(source=str(self.board), files=files, selection=[])
        history.remember_editor_notes(context, ['local editor request'])
        after_close = dict(files, **{'~test.kicad_pro.lck': 'different auxiliary file'})
        self.assertIn('local editor request', history.summary_for(self.board, after_close))
        self.assertEqual(history.summary_for(self.board, after_close, include_editor=False), '')
        self.assertEqual(history.history('Request a new placement'), [])
        self.assertEqual(history.summary_for(self.board.with_name('other.kicad_pcb'), after_close), '')
        after_close[self.board.name] = 'e' * 64
        self.assertEqual(history.summary_for(self.board, after_close), '')

    def test_clarify_answer_revise_and_adopt_with_real_reply_envelope(self):
        history = conversation.Conversation()
        before = gui.source_inventory(self.board)
        text = 'Could you move the two connectors closer together?'
        name = 'clarify_design_request'
        question = dict(reason='ambiguous_request', questions=['Which components and what area?'])
        review, binding, first = self.hosted_turn(name, question, history.history(text), text, 1,
                                                   ledger_name='clarification.json')
        self.assertIsNone(first['proposal'])
        self.assertEqual(first['clarification'], design.validate_design_clarification(question))
        history.remember(text, clarification=first['clarification'])
        self.assertIn(question['questions'][0], history.summary())
        with self.assertRaises(design.PendingContextChanged):
            review.adopt(first['clarification'], self.controls, **binding)
        text = 'J1 and J2, within the strip from 8,8 to 30,12 mm. Allow 75 seconds.'
        review, binding, followup = self.hosted_turn('propose_placement_constraints_v2', self.settings,
            history.history(text), text, 2, ledger_name='answered.json')
        offer = followup['proposal']
        self.assertEqual(offer['after'], self.settings)
        history.remember(text, proposal=offer)
        edited = review.revise(offer, dict(self.settings, route_seconds=85), self.controls, **binding)
        with self.assertRaises(design.IntentError):
            review.adopt(offer, self.controls, **binding)
        checked = review.adopt(edited, self.controls, **binding)
        self.assertEqual(checked['route_seconds'], 85)
        self.assertEqual(gui.source_inventory(self.board), before)
        self.assertNotIn('approval_granted', history.turns[-1]['visible_settings'])

    def test_routing_controls_are_inert_until_adopt_and_refuse_stale_source(self):
        static = design.inspect_project(self.board)
        base = dict(gui.pref.DEFAULTS, scope='partial_completion', seconds=90, scoring_preference='via_low')
        binding = dict(request='Finish ROUTE_A in one minute.', revision=3, source=self.board)
        review = conversation.RoutingReview(static, base, request=binding['request'], revision=3)
        offer = review.receive(conversation.ROUTING_TOOL, dict(nets=['ROUTE_A'], route_seconds=60),
                               base, **binding)
        self.assertIs(offer['approval_granted'], False)
        self.assertEqual(offer['checked']['effective_preferences']['scoring_preference'], 'via_low')
        self.assertEqual(base['scope'], 'partial_completion')
        self.board.with_suffix('.kicad_pro').write_bytes(self.board.with_suffix('.kicad_pro').read_bytes() + b'\n')
        with self.assertRaises(design.PendingContextChanged):
            review.adopt(offer, base, **binding)

    def test_placement_packet_distinguishes_retained_positions_and_lock_changes(self):
        text = ('Select J1 and J2 for placement inside the area from (8, 8) to (30, 12) mm. '
                'Keep the other components fixed and existing copper protected. '
                'Set routing time to 85 seconds. Suggest settings only.')
        review = design.PlacementConstraintReview(self.inspection, self.controls, request=text, revision=1)
        prepared = hosted.prepare_conversation(review, text, [], inspection=self.inspection)
        packet = json.loads(prepared['body'])
        self.assertIn('requests to keep, leave or hold the remaining parts in place concern their positions',
                      packet['instructions'])
        self.assertIn('change a KiCad lock or a pinned setting, use clarify_design_request with '
                      'unsupported_requirement', packet['instructions'])
        fields = packet['tools'][0]['parameters']['properties']
        self.assertEqual(set(fields), {'selected_refs', 'region_nm', 'route_seconds'})
        self.assertIn('All other components keep their current poses', fields['selected_refs']['description'])
        binding = dict(request=text, revision=1, source=self.board)
        proposal = dict(self.settings, route_seconds=85)
        with self.assertRaises(design.IntentError):
            review.receive('propose_placement_constraints_v2', dict(proposal, fixed=[]), self.controls, **binding)
        before = gui.source_inventory(self.board)
        offer = review.receive('propose_placement_constraints_v2', proposal, self.controls, **binding)
        self.assertEqual(offer['after'], proposal)
        self.assertIs(offer['approval_granted'], False)
        self.assertIs(offer['execution_authorized'], False)
        summary = placement_gui.constraint_change_text(offer)
        self.assertIn('Other parts stay in place. KiCad locks stay as saved.', summary)
        self.assertIn('Existing copper stays protected.', summary)
        self.assertEqual(gui.source_inventory(self.board), before)

    def test_routing_context_can_draw_the_exact_saved_board_without_placement(self):
        captured = design.inspect_project(self.board)
        view = placement_gui.saved_routing_scene(captured, None)
        self.assertIn('preserved-segment', view['svg'])
        self.assertNotIn('allowed-region', view['svg'])
        project = self.board.with_suffix('.kicad_pro')
        project.write_bytes(project.read_bytes() + b'\n')
        self.assertIsNone(placement_gui.saved_routing_scene(captured, None))

    def test_history_has_a_finite_size_and_cannot_retain_a_forged_clarification(self):
        history = conversation.Conversation()
        checked = design.validate_design_clarification(
            dict(reason='ambiguous_request', questions=['Which part?']))
        with self.assertRaises(design.IntentError):
            history.remember('Move it', clarification=dict(checked, approval_granted=True))
        for _ in range(conversation.MAX_TURNS):
            history.remember('Move it', clarification=checked)
        with self.assertRaisesRegex(design.IntentError, 'three replies'):
            history.history('Try again')
        with self.assertRaises(design.IntentError):
            conversation.request_text('é' * 2049)

    def test_same_path_project_change_invalidates_history_and_an_adopted_routing_handoff(self):
        inspection = design.inspect_project(self.board)
        history = conversation.Conversation()
        context = history.check_source(inspection, True)
        history.remember_placement_adoption('Last adopted placement settings\nRouting time  81 s',
                                            inspection=inspection, local_request='Local-only placement request')
        base = dict(gui.pref.DEFAULTS, scope='partial_completion')
        binding = dict(request='Finish ROUTE_A.', revision=1, source=self.board)
        review = conversation.RoutingReview(inspection, base, request=binding['request'], revision=1)
        offer = review.receive(conversation.ROUTING_TOOL, dict(nets=['ROUTE_A'], route_seconds=60),
                               base, **binding)
        history.remember(binding['request'], proposal=offer, source=context)
        summary = history.summary_for(self.board, inspection['source_hashes'])
        self.assertTrue(summary.startswith('Last adopted placement settings\nRouting time  81 s'))
        self.assertIn(binding['request'], summary)
        self.assertIn('Local-only placement request', summary)
        self.assertNotIn('Local-only placement request', repr(history.history('Finish routing.')))
        values = review.adopt(offer, base, **binding)
        guard = conversation.routing_source_guard(values)
        guard.check(self.board)
        guard.check_task(values['effective_preferences'], 'route', None)
        with self.assertRaises(design.PendingContextChanged):
            guard.check_task(dict(values['effective_preferences'], seconds=61), 'route', None)
        project = self.board.with_suffix('.kicad_pro')
        project.write_bytes(project.read_bytes() + b'\n')
        changed = design.inspect_project(self.board)
        self.assertEqual(history.summary_for(self.board, changed['source_hashes']), '')
        with self.assertRaisesRegex(ValueError, 'source project changed'):
            guard.check(self.board)
        with self.assertRaises(design.PendingContextChanged):
            history.check_source(changed, True)
