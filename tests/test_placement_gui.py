"""Pure placement UI lifecycle/dispatch controls; not actual wx/Native qualification."""
import copy
from decimal import localcontext
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui, placement_gui as pg


def window_method(name, **overrides):
    """Return an actual complete Window method; no extracted source execution."""
    wx = overrides.pop('wx', SimpleNamespace(Frame=object, NOT_FOUND=-1))
    wx.Frame = object
    wx.EXPAND = 0
    on_closed = overrides.pop('on_closed', None)
    if overrides:
        raise AssertionError('Use explicit controlled dependencies, not fragment globals: ' + str(sorted(overrides)))
    return getattr(pg.window_type(wx, on_closed=on_closed), name)


def review():
    return SimpleNamespace(revision=1, pose={'x': 3}, settings={'selected': ['one', 'two']},
                           inspection={'source': '/owned/source.kicad_pcb'}, intent=None,
                           copper_plan=None, observation={})


def canvas(on_error, on_ready=None):
    """Actual Canvas methods with a minimal passive wx surface; no real GUI."""
    class Panel:
        def __init__(self, *args, **kwargs):
            self.SetMinSize=Mock();self.SetBackgroundStyle=Mock();self.SetToolTip=Mock();self.Bind=Mock()
            self.HasCapture=Mock(return_value=False);self.ReleaseMouse=Mock();self.Refresh=Mock()
            self.GetClientSize=Mock(return_value=(800,500));self.GetContentScaleFactor=Mock(return_value=1)
        def FromDIP(self,value):return value
    dc=Mock()
    wx=SimpleNamespace(Panel=Panel,BORDER_SIMPLE=1,WANTS_CHARS=2,BG_STYLE_PAINT=0,
        AutoBufferedPaintDC=Mock(return_value=dc),Brush=lambda x:x,Colour=lambda x:x,
        CallAfter=Mock(side_effect=lambda callback: callback()))
    for name in ('EVT_PAINT','EVT_SIZE','EVT_LEFT_DOWN','EVT_MOTION','EVT_LEFT_UP',
                 'EVT_MOUSE_CAPTURE_LOST','EVT_CHAR_HOOK'):
        setattr(wx,name,name)
    picture=pg.board_canvas(wx,object(),Mock(),Mock(),on_error,on_ready)
    picture.SetScene=Mock(wraps=picture.SetScene)
    picture.test_dc=dc
    picture.test_call_after=wx.CallAfter
    return picture


class PlacementGuiTests(unittest.TestCase):
    def test_open_example_uses_the_shared_intake_only_in_an_empty_workspace(self):
        window = SimpleNamespace(board=Mock(), example_project=Path('/owned/example.kicad_pro'),
                                 open_saved_source=Mock())
        window.board.GetValue.return_value = ''
        window_method('open_example')(window, None)
        window.open_saved_source.assert_called_once_with(window.example_project)
        window.board.GetValue.return_value = '/owned/current.kicad_pcb'
        window_method('open_example')(window, None)
        window.open_saved_source.assert_called_once_with(window.example_project)

    def gate(self):
        gate = pg.ReviewGate(); gate.attach(review()); gate.acknowledged = True
        return gate

    def window(self):
        gate = self.gate()
        window = SimpleNamespace(gate=gate, job=gui.CliJob(), busy=False, routing=None, finalized=False,
            qualified=None, validation_revoked=False, pending_coordinates={}, editing_component=None,
            alternative_labels=[], alternative_targets=[],
            copilot_generation=0, pending_copilot=None, approved_copilot=None,
            conversation=pg.conversation.Conversation(),
            cancel_event=threading.Event(), inspection=gate.review.inspection,
            picture=Mock(), pages=Mock(), alternative=Mock(), part=Mock(), parts=Mock(),
            x=Mock(), y=Mock(), status=Mock(), timer=Mock(), findings=Mock(),
            assistant_ack=Mock(), assistant_result=Mock(),
            constraint_offer=None, constraint_key=Mock(), update_schematic_view=Mock(),
            copper_policy=Mock(), rigid_group=Mock(), target_region=Mock(), original_group=Mock(), protected_names=Mock(), protected_route_ids=Mock(),
            current_review_settings=Mock(), overview=Mock(), region_summary=Mock(),
            refresh=Mock(), message=Mock(), present=Mock(), layout_panel=Mock(), Destroy=Mock(), Hide=Mock(),
            panel=Mock(), GetSizer=Mock(), Layout=Mock())
        window.open_saved_source = MethodType(window_method('open_saved_source'), window)
        window.picture.Ready.return_value = True
        window.copper_policy.GetSelection.return_value = 0
        window.rigid_group.GetValue.return_value = False
        window.target_region.GetValue.return_value = False
        window.rebuild_copper = MethodType(window_method('rebuild_copper'), window)
        window.revoke = MethodType(window_method('revoke'), window)
        window.edit_component = MethodType(window_method('edit_component'), window)
        window.finish_close = MethodType(window_method('finish_close'), window)
        window.invalidate_copilot = MethodType(window_method('invalidate_copilot'), window)
        window.set_board_scene = MethodType(window_method('set_board_scene'), window)
        return window

    def test_target_region_is_explicit_and_has_the_same_settings_and_revocation_path(self):
        from autorouter import placement_intent as intent
        from experiments.placement_native_proposal_v1 import ordinary_fixture
        window = self.window()
        selected = ordinary_fixture.selected()
        window.inspection = dict(observation=dict(scope=intent.contract.THT_BASELINE_SCOPE),
            components=[dict(uuid=identity) for identity in selected])
        window.parts.IsChecked.return_value = True
        window.region = [Mock() for _ in range(4)]
        for field, value in zip(window.region, ['14', '8', '22', '13']): field.GetValue.return_value = value
        plain = window_method('options')(window, validate_geometry=False)
        self.assertNotIn('region_initialization', plain)
        window.target_region.GetValue.return_value = True
        target = window_method('options')(window, validate_geometry=False)
        self.assertEqual(target['schema'], 5)
        self.assertEqual(target['region_initialization'], intent.prototype.EXACT_TRACK_REGION_POLICY)
        window.target_start_policy = intent.prototype.REGION_INITIALIZATION_POLICY
        self.assertEqual(window_method('options')(window, validate_geometry=False)['region_initialization'],
                         intent.prototype.REGION_INITIALIZATION_POLICY)
        self.assertEqual(target['region_nm'], plain['region_nm'])
        self.assertEqual(target['selected'], plain['selected'])
        # Settings changes use the existing revoke/discard path; never a special
        # source/constraint-bypassing GUI action.
        window.updating = False; window.inspection = None
        window.revoke = Mock()
        window_method('settings_changed')(window, Mock())
        window.revoke.assert_called_once_with(discard=True)

    def test_target_region_resets_on_source_change(self):
        window = self.window(); window.updating = False
        window.revoke = Mock()
        window_method('source_changed')(window, Mock())
        window.target_region.SetValue.assert_called_once_with(False)
        self.assertIsNone(window.inspection)
        window.revoke.assert_called_once_with(discard=True)

    def test_project_caption_uses_the_captured_board_and_clears_on_source_change(self):
        window = self.window()
        window.updating = False
        window.inspection = None
        window.project_title = Mock()
        window.overview = MethodType(window_method('overview'), window)
        saved = '/owned/a long parent folder/Relay & light.kicad_pcb'
        window.saved_route_context = dict(static={'source': saved}, scene=None, open_in_kicad=True)

        window.overview()
        window.project_title.SetLabelText.assert_called_once_with('Relay & light')
        window.project_title.SetToolTip.assert_called_once_with(saved)
        window.project_title.Show.assert_called_once_with(True)

        window_method('source_changed')(window, Mock())
        window.project_title.SetLabelText.assert_called_with('')
        window.project_title.SetToolTip.assert_called_with('')
        window.project_title.Show.assert_called_with(False)

    def test_start_new_design_launches_the_prepared_native_manager(self):
        from scripts import install_gui

        window = self.window()
        window.board = Mock()
        window.board.GetValue.return_value = ''
        window.start = Mock()
        manifest = '/owned/launcher/install.json'
        app = pg.window_type(SimpleNamespace(Frame=object), launcher_manifest=manifest)
        app.start_new_design(window, None)
        _, prepare, open_manager = window.start.call_args.args
        material = (['/owned/kicad', '--new'], {'KICAD_CONFIG_HOME': '/owned/config'})
        with patch.object(install_gui, 'prepare_new_project_manager', return_value=material) as read, \
                patch.object(install_gui, 'require_closed_kicad') as closed, patch('subprocess.Popen') as launch:
            approved = prepare(Mock(), threading.Event())
            read.assert_called_once_with(manifest)
            open_manager(approved)
            closed.assert_called_once_with()
            launch.assert_called_once()
            self.assertEqual(launch.call_args.args, (material[0],))
            self.assertEqual(launch.call_args.kwargs['env'], material[1])
        self.assertIn('File > New Project > Default', window.message.call_args.args[0])

    def test_closed_source_preflight_retains_locks_and_requires_fresh_inspection_after_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); board = root / 'owned.kicad_pcb'
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_prl'):
                board.with_suffix(suffix).write_bytes(b'owned synthetic source')
            captured = dict(source=str(board), source_hashes=gui.source_inventory(board))
            self.assertEqual(pg.require_closed_source(board, inspection=captured), board)
            self.assertEqual(pg.require_closed_source(board.with_suffix('.kicad_pro'), inspection=captured), board)
            lock = root / '~owned.kicad_pro.lck'; lock.write_bytes(b'owned synthetic KiCad lock')
            with self.assertRaisesRegex(ValueError, 'File > Close Project'):
                pg.require_closed_source(board.with_suffix('.kicad_pro'), inspection=captured)
            self.assertEqual(lock.read_bytes(), b'owned synthetic KiCad lock')
            lock.unlink()  # Only this test-created lock, owned by this process.
            board.with_suffix('.kicad_prl').write_bytes(b'ordinary editor-sidecar update')
            with self.assertRaisesRegex(ValueError, 'Refresh inspection'):
                pg.require_closed_source(board, inspection=captured)
            fresh = dict(source=str(board), source_hashes=gui.source_inventory(board))
            self.assertEqual(pg.require_closed_source(board, inspection=fresh), board)

    def test_real_inspection_method_refuses_open_project_before_geometry_or_native_work(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); board = root / 'owned.kicad_pcb'
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
                board.with_suffix(suffix).write_bytes(b'owned source')
            lock = root / '~owned.kicad_pro.lck'; lock.write_bytes(b'owned test lock')
            window = self.window(); window.board = Mock(); window.board.GetValue.return_value = str(board)
            window.start = Mock()
            window_method('inspect_project')(window, None)
            inspect = window.start.call_args.args[1]; job = Mock()
            with patch.object(pg.intent, 'inspect_saved') as geometry:
                with self.assertRaisesRegex(ValueError, 'File > Close Project'):
                    inspect(job, threading.Event())
                geometry.assert_not_called(); job.run.assert_not_called()
            self.assertTrue(lock.exists())
            self.assertIsNone(window.inspection)

    def test_placement_scope_refusal_preserves_passive_board_without_dispatch(self):
        from experiments.placement_native_proposal_v1 import ordinary_fixture

        with tempfile.TemporaryDirectory() as temp:
            board = ordinary_fixture.write_project(Path(temp).resolve() / 'source')
            window = self.window()
            window.board = Mock()
            window.board.GetValue.return_value = str(board)
            window.start = Mock()
            window_method('inspect_project')(window, None)
            inspect, adopt = window.start.call_args.args[1:]
            job = Mock()
            reason = 'J1 has 9 pads. This placement profile supports up to eight per component.'
            with patch.object(pg.intent, 'inspect_saved', side_effect=pg.intent.contract.UnsupportedPlacement(reason)):
                captured = inspect(job, threading.Event())
            inspected, _, _, _, native, read_only = captured
            self.assertIsNone(inspected)
            self.assertIsNone(native)
            self.assertEqual(read_only['reason'], reason)
            self.assertIn('>J1</text>', read_only['scene']['svg'])
            self.assertEqual(read_only['static']['source_hashes'], gui.source_inventory(board))
            adopt(captured)
            self.assertIs(window.saved_route_context, read_only)
            self.assertIsNone(window.inspection)
            window.pages.SetSelection.assert_called_with(1)
            self.assertIn('Read-only saved board', window.message.call_args.args[0])
            self.assertIn(reason, window.findings.SetValue.call_args.args[0])
            job.run.assert_not_called()
            with patch.object(pg.intent, 'inspect_saved', side_effect=ValueError('Saved project changed.')):
                with self.assertRaisesRegex(ValueError, 'Saved project changed'):
                    inspect(job, threading.Event())
            job.run.assert_not_called()

    def test_locked_project_shows_only_a_saved_snapshot_until_closed_and_refreshed(self):
        from experiments.placement_native_proposal_v1 import ordinary_fixture

        with tempfile.TemporaryDirectory() as temp:
            board = ordinary_fixture.write_project(Path(temp).resolve() / 'source')
            lock = board.with_name('~' + board.with_suffix('.kicad_pro').name + '.lck')
            lock.write_bytes(b'owned test lock')
            original = gui.source_inventory(board)
            window = self.window(); window.board = Mock(); window.start = Mock()
            window.board.GetValue.return_value = str(board)
            window_method('inspect_project')(window, None)
            inspect, adopt = window.start.call_args.args[1:]
            job = Mock()
            with patch.object(pg.intent, 'inspect_saved') as placement, \
                    patch.object(pg.schematic_context, 'observe') as schematic:
                captured = inspect(job, threading.Event())
                placement.assert_not_called(); schematic.assert_not_called(); job.run.assert_not_called()
            adopt(captured)
            self.assertIsNone(window.inspection)
            self.assertTrue(window.saved_route_context['open_in_kicad'])
            self.assertIn('>J1</text>', window.saved_route_context['scene']['svg'])
            self.assertIn('Unsaved changes', window.findings.SetValue.call_args.args[0])
            self.assertEqual(gui.source_inventory(board), original)
            lock.unlink()  # This fixture created the lock deliberately.
            with self.assertRaisesRegex(ValueError, 'refresh inspection before routing'):
                window_method('open_saved_routing')(window, None)
            window_method('ask_conversation')(window, None)
            self.assertIn('refresh inspection before making a proposal', window.message.call_args.args[0])
            with self.assertRaisesRegex(ValueError, 'changed before display'):
                adopt(captured)

    def test_native_project_stub_and_missing_outline_use_setup_guidance_without_native_worker(self):
        from autorouter import sexpr
        from experiments.placement_native_proposal_v1 import ordinary_fixture

        with tempfile.TemporaryDirectory() as temp:
            for missing in ('footprints', 'outline'):
                with self.subTest(missing=missing):
                    board = ordinary_fixture.write_project(Path(temp).resolve() / missing)
                    tree = sexpr.parse(board.read_text())
                    if missing == 'footprints':
                        tree = tree[:4]  # Native 10.x Manager's board header-only stub.
                    else:
                        tree = [row for row in tree if not isinstance(row, list) or row[0] != 'gr_rect']
                    board.write_text(sexpr.dump(tree) + '\n')
                    initial = gui.source_inventory(board)
                    window = self.window(); window.board = Mock(); window.start = Mock()
                    window.board.GetValue.return_value = str(board)
                    window_method('inspect_project')(window, None)
                    inspect, adopt = window.start.call_args.args[1:]
                    job = Mock()
                    captured = inspect(job, threading.Event())
                    adopt(captured)
                    self.assertIsNone(window.inspection)
                    self.assertEqual(window.saved_route_context['pcb_setup'], missing + '_needed')
                    self.assertIn('F8' if missing == 'footprints' else 'Edge.Cuts', window.findings.SetValue.call_args.args[0])
                    if missing == 'footprints':
                        self.assertIn('saved schematic assigns footprints to 6 components',
                                      window.findings.SetValue.call_args.args[0])
                        with patch.object(pg.schematic_context, 'assigned_footprint_count',
                                          side_effect=ValueError('Missing footprint assignment')):
                            adopt(inspect(job, threading.Event()))
                        self.assertIn('Add and connect symbols', window.findings.SetValue.call_args.args[0])
                        self.assertIn('See Findings for the PCB setup steps', window.schematic_refusal)
                        self.assertIsNone(window.saved_route_context['assigned_footprints'])
                    with self.assertRaisesRegex(ValueError, 'Finish PCB setup in KiCad'):
                        window_method('open_saved_routing')(window, None)
                    window.saved_route_context = None  # The same project was typed without Return.
                    with self.assertRaisesRegex(ValueError, 'Finish PCB setup in KiCad'):
                        window_method('open_saved_routing')(window, None)
                    window.constraint_binding = Mock(return_value=dict(source=str(board), request='Finish gaps', revision=1))
                    window.conversation_kind = Mock(GetSelection=Mock(return_value=1))
                    window.conversation_routing_preferences = Mock(return_value={})
                    window_method('ask_conversation')(window, None)
                    from autorouter import hosted_intent
                    with patch.object(hosted_intent, 'prepare_conversation') as ask:
                        with self.assertRaisesRegex(ValueError, 'Finish PCB setup in KiCad'):
                            window.start.call_args.args[1](job, threading.Event())
                        ask.assert_not_called()
                    job.run.assert_not_called()
                    self.assertEqual(gui.source_inventory(board), initial)

    def test_lock_that_appears_during_geometry_capture_stops_native_dispatch(self):
        from experiments.placement_native_proposal_v1 import multipad_fixture
        with tempfile.TemporaryDirectory() as temp:
            board = multipad_fixture.write_project(Path(temp).resolve() / 'source')
            lock = board.parent / '~owned.kicad_pro.lck'
            window = self.window(); window.board = Mock(); window.board.GetValue.return_value = str(board)
            window.start = Mock(); window.owned_workspace = Mock()
            window_method('inspect_project')(window, None)
            inspect = window.start.call_args.args[1]; job = Mock()

            def capture(source):
                lock.write_bytes(b'KiCad opened during inspection')
                return dict(source=source, source_hashes=gui.source_inventory(board),
                    observation=dict(scope=pg.intent.contract.ORDINARY_SCOPE))

            with patch.object(pg.c, 'NATIVE_VERSION', '10.0.7'), patch.object(pg.intent, 'inspect_saved', side_effect=capture):
                with self.assertRaisesRegex(ValueError, 'project lock is still present'):
                    inspect(job, threading.Event())
            window.owned_workspace.assert_not_called(); job.run.assert_not_called()

    def test_affected_routing_notice_reuses_actual_saved_netclass_gate(self):
        from autorouter import pipeline
        with tempfile.TemporaryDirectory() as temp, patch.object(pg.c, 'NATIVE_VERSION', '10.0.7'):
            board = Path(temp).resolve() / 'owned.kicad_pcb'
            pro = board.with_suffix('.kicad_pro')
            settings = {'classes': [{'name': 'Default'}]}
            pro.write_text(json.dumps({'net_settings': settings}))
            self.assertEqual(pg.affected_routing_notice(board), '')
            for changed in (dict(settings, classes=[*settings['classes'], {'name': 'Power'}]),
                            dict(settings, netclass_patterns=[{'netclass': 'Default', 'pattern': 'GND'}])):
                pro.write_text(json.dumps({'net_settings': changed}))
                with self.assertRaisesRegex(ValueError, 'sole Default'):
                    pipeline.check_native7_selected_netclasses(board)
                self.assertIn('block routing after copper rebuild', pg.affected_routing_notice(board))

    def test_typed_project_rebinds_the_exact_pcb_after_fresh_inspection(self):
        from experiments.placement_native_proposal_v1 import multipad_fixture
        with tempfile.TemporaryDirectory() as temp:
            board = multipad_fixture.write_project(Path(temp).resolve() / 'source')
            project = board.with_suffix('.kicad_pro')
            window = self.window()
            window.board = Mock()
            window.board.GetValue.return_value = str(project)
            window.start = Mock()
            window.region = [Mock() for _ in range(4)]
            window_method('inspect_project')(window, None)
            inspect, adopt = window.start.call_args.args[1:]
            job = Mock()
            captured = inspect(job, threading.Event())
            with project.open('ab') as stream:
                stream.write(b'\n')
            with self.assertRaisesRegex(ValueError, 'Refresh inspection'):
                adopt(captured)
            window.board.ChangeValue.assert_not_called()
            adopt(inspect(job, threading.Event()))
            window.board.ChangeValue.assert_called_once_with(str(board))
            self.assertEqual(window.inspection['source'], str(board))
            job.run.assert_not_called()

    def test_choose_project_resolves_the_exact_coboard_and_retains_previous_on_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            board = root / 'complete.kicad_pcb'
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
                board.with_suffix(suffix).write_bytes(b'owned fixture')
            incomplete = root / 'incomplete.kicad_pro'
            incomplete.write_bytes(b'owned fixture')
            selected = Mock()
            selected.__enter__ = Mock(return_value=selected)
            selected.__exit__ = Mock(return_value=False)
            selected.ShowModal.return_value = 1
            wx = SimpleNamespace(FileDialog=Mock(return_value=selected),
                                 ID_OK=1, FD_OPEN=2, FD_FILE_MUST_EXIST=4)
            choose = window_method('choose_board', wx=wx)
            window = self.window()
            window.board = Mock(); window.source_changed = Mock()
            window.inspect_project = Mock(side_effect=lambda _: selected.__exit__.assert_called_once())
            selected.GetPath.return_value = str(board.with_suffix('.kicad_pro'))
            choose(window, None)
            window.board.ChangeValue.assert_called_once_with(str(board))
            window.source_changed.assert_called_once_with(None)
            window.inspect_project.assert_called_once_with(None)
            selected.GetPath.return_value = str(incomplete)
            choose(window, None)
            window.board.ChangeValue.assert_called_once()
            self.assertIn('Missing incomplete.kicad_pcb', window.message.call_args.args[0])
            selected.ShowModal.return_value = 0
            choose(window, None)
            window.board.ChangeValue.assert_called_once()
            window.inspect_project.assert_called_once()

    def test_prefilled_source_inspects_once_on_show_and_never_replaces_new_selection(self):
        source = '/saved/known.kicad_pro'
        wx = SimpleNamespace(Frame=object, EVT_SHOW=object())
        window_type = pg.window_type(wx, board=source)
        for current in (source, '/other/chosen.kicad_pro'):
            with self.subTest(current=current):
                window = self.window(); window.board = Mock(); window.board.GetValue.return_value = current
                window.Unbind = Mock(); window.inspect_project = Mock()
                shown = MethodType(window_type.inspect_initial_project, window)
                window.inspect_initial_project = shown
                event = Mock(); event.IsShown.return_value = False
                shown(event)
                window.Unbind.assert_not_called(); window.inspect_project.assert_not_called()
                event.IsShown.return_value = True
                shown(event)
                window.Unbind.assert_called_once_with(wx.EVT_SHOW, handler=shown)
                if current == source: window.inspect_project.assert_called_once_with(None)
                else: window.inspect_project.assert_not_called()

    def test_toolbar_selection_changes_only_current_eligible_saved_component_controls(self):
        use = window_method('use_toolbar_selection')
        for mode in ('eligible', 'stale', 'locked', 'other project', 'missing'):
            with self.subTest(mode=mode):
                window = self.window()
                window.toolbar_source = Path('/owned/test.kicad_pcb')
                window.toolbar_selection = ('j1', 'j2')
                window.constraint_offer = None
                window.board = Mock(); window.board.GetValue.return_value = str(window.toolbar_source)
                window.parts = Mock()
                window.rebuild_copper = Mock(return_value=False)
                before = window.gate.review, window.gate.generation, window.copilot_generation
                window.inspection = {'components': [
                    {'uuid': 'j1', 'reference': 'J1', 'fixed_reasons': []},
                    {'uuid': 'other' if mode == 'missing' else 'j2', 'reference': 'J2',
                     'fixed_reasons': ['Locked in KiCad'] if mode == 'locked' else []},
                    {'uuid': 'j3', 'reference': 'J3', 'fixed_reasons': []}]}
                expected = Path('/owned/other.kicad_pcb') if mode == 'other project' else window.toolbar_source
                fault = ValueError('Saved source files changed since inspection.') if mode == 'stale' else None
                with patch.object(pg, 'require_closed_source', return_value=expected, side_effect=fault) as verify, \
                        patch.object(pg, 'update_target_area'):
                    use(window, None)
                verify.assert_called_once_with(str(window.toolbar_source), inspection=window.inspection)
                if mode == 'eligible':
                    self.assertEqual([call.args for call in window.parts.Check.call_args_list],
                                     [(0, True), (1, True), (2, False)])
                    self.assertEqual(window.toolbar_selection, ())
                    self.assertIsNone(window.gate.review)
                    self.assertGreater(window.gate.generation, before[1])
                    self.assertGreater(window.copilot_generation, before[2])
                else:
                    window.parts.Check.assert_not_called()
                    self.assertEqual((window.gate.review, window.gate.generation, window.copilot_generation), before)
                    self.assertIn({'locked': 'J2 stays fixed', 'stale': 'changed since inspection',
                                   'other project': 'different project', 'missing': 'missing from the saved board'}[mode],
                                  window.message.call_args.args[0])

    def test_real_inspection_refuses_non_PCB_identity_before_inventory_geometry_or_native(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            wrong = root / 'notes.txt'; wrong.write_bytes(b'owned fixture')
            directory = root / 'folder.kicad_pcb'; directory.mkdir()
            source = root / 'source.kicad_pcb'; source.write_bytes(b'owned saved source')
            link = root / 'alias.kicad_pcb'; link.symlink_to(source)
            for invalid in ('', root, directory, wrong, link, None, True):
                window = self.window(); window.board = Mock()
                window.board.GetValue.return_value = invalid; window.start = Mock()
                window_method('inspect_project')(window, None)
                inspect = window.start.call_args.args[1]; job = Mock()
                with self.subTest(source=invalid), patch.object(pg.gui, 'source_inventory') as inventory, \
                        patch.object(pg.intent, 'inspect_saved') as geometry:
                    with self.assertRaises((ValueError, OSError, pg.h.Rejected)):
                        inspect(job, threading.Event())
                    inventory.assert_not_called(); geometry.assert_not_called()
                    job.run.assert_not_called()
                self.assertIsNone(window.inspection)
            self.assertTrue(link.is_symlink())
            self.assertEqual(source.read_bytes(), b'owned saved source')

    def test_real_qualification_work_refuses_reopened_or_changed_source_before_draft_and_native(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); board = root / 'owned.kicad_pcb'; board.write_bytes(b'owned source')
            captured = dict(source=str(board), source_hashes=gui.source_inventory(board))
            window = self.window(); window.gate.review.inspection = captured
            window.gate.review.decision = Mock(); window.start = Mock()
            window_method('qualify_draft')(window, None)
            work = window.start.call_args.args[1]; job = Mock()
            lock = root / '~owned.kicad_pro.lck'; lock.write_bytes(b'owned test lock')
            with patch.object(pg, 'write_new_json') as draft:
                with self.assertRaisesRegex(ValueError, 'File > Close Project'):
                    work(job, threading.Event())
                lock.unlink()  # This newly created test fixture only.
                board.write_bytes(b'changed while project closed')
                with self.assertRaisesRegex(ValueError, 'Refresh inspection'):
                    work(job, threading.Event())
                draft.assert_not_called(); window.gate.review.decision.assert_not_called()
                job.run.assert_not_called()

    def test_explicit_literal_ack_and_each_ticket_dependency(self):
        gate = self.gate(); ticket = gate.ticket(); self.assertIsNone(gate.check(ticket))
        for ack in (False, 1, 'yes', None):
            gate.acknowledged = ack
            with self.subTest(ack=ack), self.assertRaises(ValueError): gate.check(ticket)
        gate.acknowledged = True
        for field, mutation in (('revision', 2), ('pose', {'x': 4}), ('settings', {'selected': []}),
                                ('inspection', {'source': '/other.kicad_pcb'}),
                                ('copper_plan', {'changed': True}), ('observation', {'changed': True})):
            original = getattr(gate.review, field); setattr(gate.review, field, mutation)
            with self.subTest(field=field), self.assertRaises(ValueError): gate.check(ticket)
            setattr(gate.review, field, original)
        self.assertIsNone(gate.check(ticket))

    def test_pending_edit_cancel_reject_and_close_revoke_old_tickets(self):
        for action in ('dirty', 'invalidate', 'attach', 'close'):
            gate = self.gate(); ticket = gate.ticket(); gate.review.intent = {'choice': 'reviewed_draft'}
            with self.subTest(action=action):
                if action == 'dirty': gate.invalidate(dirty=True)
                elif action == 'invalidate': gate.invalidate()
                elif action == 'attach': gate.attach(review())
                else: gate.close()
                with self.assertRaises(ValueError): gate.check(ticket)
                self.assertIsNone(gate.review.intent)

    def test_decimal_region_refuses_nonfinite_excessive_precision_and_bounds(self):
        self.assertEqual(pg.millimetres('-12.000001'), -12000001)
        self.assertEqual(pg.mm(-12000001), '-12.000001')
        for value in ('', 'nan', 'Infinity', '1e99', '2000.000001', '0.0000001', 'x', 1, True, '0' * 33):
            with self.subTest(value=value), self.assertRaises(ValueError): pg.millimetres(value)

    def test_region_input_and_saved_coordinate_display_ignore_ambient_decimal_precision(self):
        for precision in (3, 6, 28):
            with self.subTest(precision=precision), localcontext() as context:
                context.prec = precision
                self.assertEqual(pg.millimetres('16.123456'), 16123456)
                self.assertEqual(pg.mm(16123456), '16.123456')
                self.assertEqual(pg.mm(-16123456), '-16.123456')
                with self.assertRaises(ValueError): pg.millimetres('16.1234561')
                with self.assertRaises(ValueError): pg.millimetres('2000.000001')

    def test_compact_component_labels_keep_complete_reasons_in_findings(self):
        row = dict(reference='J4', fixed_reasons=['Shares a net with existing copper'])
        self.assertEqual(pg.component_label(row), 'J4 · fixed (routed net)')
        self.assertIn('J4: Shares a net with existing copper', pg.component_findings({'components': [row]}))
        row['fixed_reasons'].append('Locked in KiCad')
        self.assertEqual(pg.component_label(row), 'J4 · fixed (routed net, locked)')
        self.assertIn('Locked in KiCad', pg.component_findings({'components': [row]}))

    def test_render_reflows_responsive_frame_after_scene_changes(self):
        window = self.window(); window.Layout = Mock(); window.panel = Mock(); window.controls = Mock()
        window.layout_panel = MethodType(window_method('layout_panel'), window)
        item = dict(uuid='one', reference='J1', fixed_reasons=[])
        window.gate.review = SimpleNamespace(inspection=dict(components=[item], observation={}, source='/owned/source'),
            settings=dict(selected=['one'], region_nm=[0, 0, 10, 10]), moves={'one': [1, 1]}, alternatives=[{}],
            copper_plan=None, observation={'footprints': [dict(item, position_nm=[0, 1])]})
        window.coordinates = Mock(); display = {'svg':'<svg/>','size':(1000,540)}
        window.alternative.GetSelection.return_value = 0
        window.present = MethodType(window_method('present'), window)
        with patch.object(pg.placement_view, 'scene', return_value=display):
            window_method('render')(window, 0)
        window.picture.SetScene.assert_called_once_with(display)
        window.Layout.assert_called_once(); window.panel.Layout.assert_called_once()
        window.controls.FitInside.assert_called_once(); window.panel.FitInside.assert_not_called()
        window.picture.SetMinSize.assert_not_called()

    def test_new_private_settings_refuse_overwrite_links_and_oversized_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); path = root / 'settings.json'
            pg.write_new_json(path, {'selected': ['owned']})
            original = path.read_bytes(); self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises((ValueError, OSError)): pg.write_new_json(path, {})
            self.assertEqual(path.read_bytes(), original)
            link = root / 'linked.json'; link.symlink_to(path)
            with self.assertRaises((ValueError, OSError, pg.h.Rejected)): pg.write_new_json(link, {})
            self.assertEqual(path.read_bytes(), original)
            huge = root / 'huge.json'
            with self.assertRaises(ValueError): pg.write_new_json(huge, {'data': 'x' * 65536})
            self.assertFalse(huge.exists())

    def test_qualification_dispatch_is_exact_bounded_argv_with_fresh_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); (root / '.runs').mkdir(); (root / '.venv/bin').mkdir(parents=True)
            python = root / '.venv/bin/python'; python.write_bytes(b'owned-not-executed'); python.chmod(0o700)
            draft = root / "review ' $(literal).json"; pg.write_new_json(draft, {'draft': 'owned'})
            output = root / '.runs/new-job'
            with patch.object(pg.c, 'ROOT', root):
                argv = pg.qualification_command(draft, output)
                self.assertEqual(argv, [str(python), '-B', '-m', 'autorouter.placement', '--draft', str(draft),
                    '--draft-sha256', hashlib.sha256(draft.read_bytes()).hexdigest(), '--output', str(output), '--qualify'])
                self.assertFalse(output.exists()); output.mkdir()
                with self.assertRaises(ValueError): pg.qualification_command(draft, output)
                with self.assertRaises(ValueError): pg.qualification_command(draft, root / 'wrong-parent')

    def test_revoke_closes_routing_cancels_authority_and_clears_rejected_preview(self):
        window = self.window(); ticket = window.gate.ticket(); window.routing = Mock()
        window.qualified = {'old': 'candidate'}; window.revoke(discard=True)
        window.routing.Close.assert_called_once(); self.assertIsNone(window.qualified)
        self.assertIsNone(window.gate.review); window.picture.SetScene.assert_called_once_with(None)
        window.alternative.Set.assert_called_once_with([]); window.part.Set.assert_called_once_with([])
        with self.assertRaises(ValueError): window.gate.check(ticket)

    def test_queued_result_never_adopts_after_late_cancel_changed_inputs_or_close(self):
        for fault in ('cancel', 'changed', 'closed'):
            window = self.window(); generation = window.gate.generation; adopt = Mock()
            if fault == 'cancel': window.job.cancel()
            elif fault == 'changed': window.gate.invalidate()
            else: window.gate.close()
            with self.subTest(fault=fault):
                window_method('finish')(window, window.job, generation, {'success': True}, None, adopt)
                adopt.assert_not_called()
                if fault == 'closed': window.Destroy.assert_called_once()

    def test_worker_exception_keeps_receipt_and_never_adopts(self):
        window = self.window(); adopt = Mock()
        window_method('finish')(window, window.job, window.gate.generation, None, 'Native output failed', adopt)
        adopt.assert_not_called(); self.assertIsNone(window.qualified)
        self.assertIn('Native output failed', window.message.call_args.args[0])

    def test_search_timeout_cancel_or_no_change_never_adopts_a_draft(self):
        window = self.window(); window.options = Mock(return_value={'search': {'seconds': 2}})
        window.start = Mock(); window.render = Mock()
        window_method('find_alternatives')(window, None)
        adopt = window.start.call_args.args[2]
        for status, message in (('budget_exhausted', 'time limit'),
                                ('no_changed_alternative', 'current constraints'),
                                ('cancelled', 'cancelled'), ('untrusted', 'unsupported result')):
            with self.subTest(status=status), patch.object(pg.intent, 'Review') as review:
                with self.assertRaisesRegex(ValueError, message):
                    adopt({'search': {'status': status, 'alternatives': [{'untrusted': 'draft'}]}})
                review.assert_not_called()
                window.render.assert_not_called()

    def test_region_refusal_opens_findings_without_adopting_a_draft(self):
        window = self.window(); window.options = Mock(return_value={'search': {'seconds': 2}})
        window.start = Mock(); window.render = Mock()
        window.inspection.update(native_source_baseline={'native': {
            'opens': 0, 'blocking': 0, 'warnings': 1, 'exclusions': 0,
            'findings': [{'type': 'text_height', 'severity': 'warning', 'description': 'Original text warning'}],
        }}, native_context={'receipt': '/owned/inspection.json'})
        window_method('find_alternatives')(window, None)
        result = {'search': {'status': 'no_feasible_region_seed', 'alternatives': [],
            'region_initialization': {'candidates_checked': 9,
                                      'rejected_by_constraint': {'protected_tracks': 8, 'component_spacing': 1}}}}
        with patch.object(pg.intent, 'Review') as review:
            window.start.call_args.args[2](result)
        review.assert_not_called(); window.render.assert_not_called()
        window.pages.SetSelection.assert_called_once_with(1)
        self.assertIsNone(window.gate.review); self.assertFalse(window.gate.acknowledged)
        self.assertIsNone(window.qualified)
        findings = window.findings.SetValue.call_args.args[0]
        for line in ('Checked 9 starting arrangements', '8 · Clearance from protected tracks',
                     '1 · Spacing between component courtyards', 'Original text warning'):
            self.assertIn(line, findings)

    def test_close_requests_existing_worker_and_child_cleanup_before_destroy(self):
        window = self.window(); window.busy = True; window.routing = Mock(); event = Mock()
        window_method('close')(window, event)
        self.assertTrue(window.gate.closed); self.assertTrue(window.cancel_event.is_set())
        self.assertTrue(window.job.cancel_requested); window.routing.Close.assert_called_once()
        window.Hide.assert_called_once(); window.Destroy.assert_not_called(); event.Veto.assert_called_once()

    def test_parent_close_waits_for_both_worker_and_owned_routing_frame(self):
        window = self.window(); window.busy = True; window.routing = Mock(); window.gate.close()
        window.finish_close(); window.Destroy.assert_not_called()
        # Own worker finishes first: the existing child still controls cleanup.
        window_method('finish')(window, window.job, window.gate.generation, None, None, Mock())
        window.Destroy.assert_not_called()
        window.routing = None; window.finish_close(); window.Destroy.assert_called_once()
        window.finish_close(); window.Destroy.assert_called_once()

    def test_parent_notification_is_queued_once_only_after_both_cleanup_scopes(self):
        window = self.window(); window.busy = True; window.routing = Mock(); window.gate.close()
        callback = Mock(); wx = Mock(); calls = Mock()
        calls.attach_mock(window.Destroy, 'destroy'); calls.attach_mock(wx.CallAfter, 'call_after')
        window.finish_close = MethodType(window_method('finish_close', on_closed=callback, wx=wx), window)
        window.finish_close(); wx.CallAfter.assert_not_called()
        window.busy = False; window.finish_close(); wx.CallAfter.assert_not_called()
        window.routing = None; window.finish_close(); window.finish_close()
        self.assertEqual([row[0] for row in calls.mock_calls], ['destroy', 'call_after'])
        wx.CallAfter.assert_called_once_with(callback); callback.assert_not_called()
        wx.CallAfter.call_args.args[0]()
        callback.assert_called_once_with()

    def test_rendered_edit_is_never_mislabeled_as_first_alternative(self):
        window, _ = self.presentation_window(); window.coordinates = Mock()
        window.alternative.SetSelection.side_effect = lambda index: setattr(window.alternative.GetSelection, 'return_value', index)
        before = copy.deepcopy((window.gate.review.pose, window.gate.review.moves,
                                window.gate.review.revision, window.gate.acknowledged, window.gate.generation))
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>'):
            window_method('render')(window)
        window.alternative.Set.assert_called_once_with(['Alternative 1', 'Alternative 2', 'Edited draft'])
        window.alternative.SetSelection.assert_called_once_with(2)
        self.assertEqual(window.alternative_targets, [0, 1, None])
        self.assertIn('Edited draft.', window.findings.SetValue.call_args.args[0])
        self.assertNotIn('Alternative 3.', window.findings.SetValue.call_args.args[0])
        self.assertEqual((window.gate.review.pose, window.gate.review.moves,
                          window.gate.review.revision, window.gate.acknowledged, window.gate.generation), before)

    def test_current_edited_choice_is_noop_for_pose_pending_ack_and_native_ticket(self):
        for dirty in (False, True):
            window, result = self.presentation_window(); window.qualified = result
            window.alternative_targets = [0, 1, None]; window.alternative.GetSelection.return_value = 2
            window.gate.dirty = dirty; window.gate.acknowledged = not dirty
            window.pending_coordinates = {'two': ['20.', '10.4']} if dirty else {}
            window.gate.review.choose = Mock(); window.revoke = Mock(); window.render = Mock()
            before = copy.deepcopy((window.gate.review.pose, window.gate.review.moves,
                window.gate.review.revision, window.pending_coordinates, window.gate.acknowledged,
                window.gate.dirty, window.gate.generation))
            window_method('choose_alternative')(window, None)
            self.assertEqual((window.gate.review.pose, window.gate.review.moves,
                window.gate.review.revision, window.pending_coordinates, window.gate.acknowledged,
                window.gate.dirty, window.gate.generation), before)
            self.assertIs(window.qualified, result)
            window.gate.review.choose.assert_not_called(); window.revoke.assert_not_called(); window.render.assert_not_called()
            if not dirty: self.assertIsNone(window.gate.check(result['ticket']))

    def test_real_choice_removes_current_edited_item_and_revokes_previous_validation(self):
        window, result = self.presentation_window(); window.qualified = result
        window.alternative_targets = [0, 1, None]
        window.alternative_labels = ['Alternative 1', 'Alternative 2', 'Edited draft']
        window.alternative.GetSelection.return_value = 1
        window.pending_coordinates = {'two': ['20.', '10.4']}; window.gate.dirty = True
        window.gate.review.choose = Mock(); window.present = Mock(); window.coordinates = Mock()
        window.render = MethodType(window_method('render'), window)
        window_method('choose_alternative')(window, None)
        window.gate.review.choose.assert_called_once_with(1)
        self.assertEqual(window.alternative_targets, [0, 1])
        window.alternative.Set.assert_called_once_with(['Alternative 1', 'Alternative 2'])
        self.assertEqual(window.pending_coordinates, {}); self.assertFalse(window.gate.acknowledged)
        self.assertIsNone(window.qualified)
        with self.assertRaises(ValueError): window.gate.check(result['ticket'])

    def test_invalid_display_choice_still_revokes_without_discarding_pending_edits(self):
        for selection, targets in ((-1, [0, 1, None]), (3, [0, 1, None]),
                                   (True, [0, 1, None]), (0, [False])):
            window, result = self.presentation_window(); window.qualified = result
            window.alternative_targets = targets; window.alternative.GetSelection.return_value = selection
            window.pending_coordinates = {'two': ['20.', '10.4']}
            window.gate.review.choose = Mock(); window.present = Mock(); window.render = Mock()
            window_method('choose_alternative')(window, None)
            self.assertEqual(window.pending_coordinates, {'two': ['20.', '10.4']})
            self.assertTrue(window.gate.dirty); self.assertFalse(window.gate.acknowledged)
            self.assertIsNone(window.qualified); window.gate.review.choose.assert_not_called()
            window.render.assert_not_called(); self.assertIn('Alternative refused', window.message.call_args.args[0])
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])

    def test_late_cancel_during_guard_prevents_even_routing_frame_construction(self):
        window = self.window(); guard = Mock(); guard.check.side_effect = lambda _: window.job.cancel()
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window') as factory:
            window_method('open_routing')(window, None)
        factory.assert_not_called(); self.assertIsNone(window.routing)

    def test_review_pause_does_not_reexpire_an_already_adopted_placement(self):
        window = self.window(); guard = Mock(); frame = Mock(source_guard=guard)
        window.job.process = Mock()
        window.job._action_process = window.job.process
        window.job._action_started = 1
        window.job._action_deadline = 2
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard,
                                witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'elapsed_time', return_value=3), \
                patch.object(gui, 'create_window', return_value=frame) as factory:
            window_method('open_routing')(window, None)
        factory.assert_called_once()
        frame.Show.assert_called_once()
        self.assertEqual(guard.check.call_count, 2)
        self.assertFalse(window.job.cancel_requested)
        window.gate.check(window.qualified['ticket'])

    def test_late_stale_guard_destroys_unshown_frame_without_routing(self):
        window = self.window(); guard = Mock(); guard.check.side_effect = [None, ValueError('source changed')]
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'})
        frame = Mock()
        with patch.object(gui, 'create_window', return_value=frame) as factory:
            window_method('open_routing')(window, None)
        factory.assert_called_once()
        self.assertEqual(factory.call_args.args, ('/owned/candidate.kicad_pcb',))
        self.assertIs(factory.call_args.kwargs['source_guard'], guard)
        self.assertTrue(callable(factory.call_args.kwargs['on_closed']))
        frame.Destroy.assert_called_once(); frame.Show.assert_not_called(); self.assertIsNone(window.routing)

    def test_explicit_routing_close_callback_releases_child_and_finishes_parent_close(self):
        window = self.window(); guard = Mock(); frame = Mock(source_guard=guard)
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard,
                                witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window', return_value=frame) as factory:
            window_method('open_routing')(window, None)
        closed = factory.call_args.kwargs['on_closed']
        frame.Show.assert_called_once(); frame.Bind.assert_not_called()
        self.assertIs(window.routing, frame)
        window_method('close')(window, Mock())
        frame.Close.assert_called_once(); window.Destroy.assert_not_called()
        closed(); closed()
        self.assertIsNone(window.routing); window.Destroy.assert_called_once()

    def test_routing_handoff_keeps_chosen_output_and_mandatory_guard(self):
        window = self.window(); guard = Mock(); frame = Mock(source_guard=guard)
        window.routing_output_hint = '/chosen/candidate jobs'
        window.inspection = {'source': '/owned/source.kicad_pcb', 'source_hashes': {'board': 'exact'}}
        origin = window.conversation.check_source(window.inspection, False)
        question = pg.conversation.design.validate_design_clarification(
            dict(reason='ambiguous_request', questions=['Which parts should move?']))
        window.conversation.remember('Move the connectors.', clarification=question, source=origin)
        window.conversation.remember_placement_adoption('Last adopted placement settings',
                                                        inspection=window.inspection, local_request='Select J1')
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard,
                                witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window', return_value=frame) as factory:
            window_method('open_routing')(window, None)
        frame.output.SetValue.assert_called_once_with('/chosen/candidate jobs')
        self.assertIs(factory.call_args.kwargs['source_guard'], guard)
        self.assertIn('Which parts should move?', factory.call_args.kwargs['conversation_history'])
        self.assertIn('Select J1', factory.call_args.kwargs['conversation_history'])
        frame.prefill_placement_completion.assert_called_once_with(dict(gui.pref.DEFAULTS, scope='partial_completion', seconds=90))
        frame.Show.assert_called_once(); frame.Destroy.assert_not_called()

    def test_existing_routing_frame_is_not_duplicated_or_rebound(self):
        window = self.window(); guard = Mock(); frame = Mock(source_guard=guard); window.routing = frame
        window.qualified = dict(ticket=window.gate.ticket(), guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'})
        with patch.object(gui, 'create_window') as factory:
            window_method('open_routing')(window, None)
            frame.Raise.assert_called_once(); factory.assert_not_called()
            frame.source_guard = Mock(); frame.Raise.reset_mock()
            window_method('open_routing')(window, None)
            frame.Raise.assert_not_called(); factory.assert_not_called()

    def test_qualification_cannot_overlap_closing_routing_frame(self):
        window = self.window(); window.routing = Mock(); window.start = Mock()
        window_method('qualify_draft')(window, None)
        window.start.assert_not_called(); self.assertIn('previous routing window', window.message.call_args.args[0])

    def test_qualification_adoption_rechecks_cancel_after_origin_guard(self):
        window = self.window(); window.start = Mock()
        window_method('qualify_draft')(window, None)
        adopt = window.start.call_args.args[2]
        guard = Mock(); guard.check.side_effect = lambda _: window.job.cancel()
        with self.assertRaises(ValueError):
            adopt(dict(guard=guard, witness={'candidate': '/owned/candidate.kicad_pcb'}))
        self.assertIsNone(window.qualified); window.findings.SetValue.assert_not_called()

    def presentation_window(self):
        """Small presentation model; no claim of actual Native qualification."""
        window = self.window()
        item = dict(uuid='one', reference='J1', fixed_reasons=[])
        second = dict(uuid='two', reference='J2', fixed_reasons=[])
        draft = SimpleNamespace(revision=1, pose={'one': [1000000, 2000000], 'two': [3000000, 4000000]},
            moves={'one': [1000000, 2000000], 'two': [3000000, 4000000]}, alternatives=[{}, {}],
            inspection=dict(components=[item, second], observation={'scope': pg.intent.contract.ORDINARY_SCOPE},
                            source='/owned/source.kicad_pcb'),
            settings=dict(selected=['one', 'two'], region_nm=[0, 0, 10000000, 10000000]), intent=None,
            copper_plan=None, observation={'footprints': [dict(item, position_nm=[2000000, 2000000]),
                                                        dict(second, position_nm=[3000000, 4000000])]})
        window.gate.attach(draft); window.gate.acknowledged = True; window.inspection = draft.inspection
        window.alternative_labels = ['Alternative 1', 'Alternative 2']; window.alternative_targets = [0, 1]
        window.alternative.GetSelection.return_value = 1; window.part.GetSelection.return_value = 1
        window.editing_component = 'two'
        window.x.GetValue.return_value = '3'; window.y.GetValue.return_value = '4'
        window.updating = False
        bitmap = Mock(); bitmap.GetSize.return_value = (850, 486)
        window.present = MethodType(window_method('present', wx=SimpleNamespace(NOT_FOUND=-1)), window)
        witness = dict(candidate='/owned/separate/candidate.kicad_pcb', findings=dict(opens=2,
            blocking=0, warnings=1, exclusions=0, ignored_checks=[dict(key='retained_check', description='Retained ignored check')],
            findings=[dict(severity='warning', type='library_mismatch', description='Retained source warning')]))
        result = dict(ticket=window.gate.ticket(), witness=witness, guard=Mock())
        return window, result

    def test_native_adoption_presents_actual_findings_and_pending_routing_without_resetting_controls(self):
        window, result = self.presentation_window(); window.start = Mock()
        original = copy.deepcopy(window.gate.review.moves)
        window_method('qualify_draft')(window, None); adopt = window.start.call_args.args[2]
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>') as render:
            adopt(result)
        self.assertIs(window.qualified, result)
        self.assertEqual(render.call_args.kwargs['state'], 'Placement validated — routing pending')
        self.assertEqual(render.call_args.kwargs['title'], 'Placement review')
        text = window.findings.SetValue.call_args.args[0]
        self.assertIn('Status: placement validated; routing pending', text)
        self.assertNotIn('not reported', text)
        self.assertIn('2 opens; 0 blocking; 1 warnings; 0 exclusions', text)
        self.assertIn('Retained source warning', text); self.assertIn('Retained ignored check', text)
        self.assertIn('No electrical or manufacturing approval', text)
        self.assertEqual(window.gate.review.moves, original)
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
        window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

    def test_draft_and_edited_labels_use_current_selection_without_changing_it(self):
        window, _ = self.presentation_window()
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>') as render:
            window.present()
            self.assertEqual(render.call_args.kwargs['state'], 'Geometry draft — Native validation required')
            self.assertIn('Alternative 2.', window.findings.SetValue.call_args.args[0])
            window.alternative.GetSelection.return_value = -1; window.present()
        self.assertIn('Edited draft.', window.findings.SetValue.call_args.args[0])
        self.assertNotIn('Alternative 1.', window.findings.SetValue.call_args.args[0])
        self.assertIn('Displayed placement · 1 move · 1 stays in place', window.findings.SetValue.call_args.args[0])
        self.assertIn('J1 · (2, 2) → (1, 2) mm', window.findings.SetValue.call_args.args[0])
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()

    def test_options_preserve_explicit_inspected_scope(self):
        window, _ = self.presentation_window()
        window.inspection['observation']['scope'] = 'explicit-observed-scope'
        window.parts.IsChecked.side_effect = [True, True]
        window.region = [Mock() for _ in range(4)]
        for field, value in zip(window.region, ('0', '0', '10', '10')):
            field.GetValue.return_value = value
        expected = {'guarded': 'settings'}
        with patch.object(pg.intent, 'settings', return_value=expected) as settings, patch.object(pg.intent, 'facts') as facts:
            self.assertIs(window_method('options')(window), expected)
        settings.assert_called_once_with(['one', 'two'], [0, 0, 10000000, 10000000], scope='explicit-observed-scope')
        facts.assert_called_once_with(window.inspection, expected)

    def test_findings_use_inspected_scope_limits_without_inheriting_old_pth_claim(self):
        window, result = self.presentation_window()
        window.gate.review.inspection['limitations'] = ['Explicit scope: fixed-angle SMD translation only.']
        # Changing the inspected limitations also changes the bound ticket.
        result['ticket'] = window.gate.ticket(); window.qualified = result
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>'):
            window.present()
        text = window.findings.SetValue.call_args.args[0]
        self.assertIn('fixed-angle SMD translation only', text)
        self.assertNotIn('circular through-hole pads', text)
        self.assertIn('Placement validated', text)

    def test_pending_coordinate_text_replaces_success_without_altering_text_pose_or_selection(self):
        window, result = self.presentation_window(); window.qualified = result
        original = copy.deepcopy(window.gate.review.moves)
        window.x.GetValue.return_value = '26.'
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>') as render:
            window_method('pending_edit')(window, Mock())
        self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
        with self.assertRaises(ValueError): window.gate.check(result['ticket'])
        self.assertEqual(render.call_args.kwargs['state'], 'Pending edits — displayed pose has not been updated')
        text = window.findings.SetValue.call_args.args[0]
        self.assertNotIn('Placement validated', text); self.assertNotIn('Native findings:', text)
        self.assertIn('No current Native placement validation', text)
        self.assertIn('J1 · (2, 2) → (1, 2) mm', text)
        self.assertNotIn('26.', text)
        self.assertEqual(window.gate.review.moves, original)
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
        window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

    def test_cancel_removes_success_and_revokes_routing(self):
        window, result = self.presentation_window(); window.qualified = result
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>') as render:
            window_method('cancel_work')(window, None)
        self.assertIsNone(window.qualified)
        with self.assertRaises(ValueError): window.gate.check(result['ticket'])
        self.assertEqual(render.call_args.kwargs['state'], 'Validation revoked — review and validate again')
        self.assertNotIn('Placement validated', window.findings.SetValue.call_args.args[0])

    def test_approval_keeps_findings_visible_and_needs_current_board_bitmap(self):
        window, previous = self.presentation_window(); window.start = Mock()
        before = copy.deepcopy((window.gate.review.pose, window.gate.review.moves))
        window.picture = canvas(MethodType(window_method('preview_failed'), window),
            MethodType(window_method('preview_ready'), window))
        window.picture.GetClientSize.return_value = (0, 0)
        display = {'svg': '<svg/>', 'size': (1000, 540)}
        with patch.object(pg.placement_view, 'scene', return_value=display), \
                patch.object(pg, 'bitmap_with_labels', return_value=Mock()) as raster:
            window_method('qualify_draft')(window, None)
            window.pages.SetSelection.assert_not_called()
            window.start.assert_not_called()
            self.assertFalse(window.gate.acknowledged)
            self.assertFalse(window.picture.Ready()); raster.assert_not_called()
            self.assertIsNone(window.qualified)
            with self.assertRaises(ValueError): window.gate.check(previous['ticket'])
            window.picture.GetClientSize.return_value = (800, 500)
            window.picture.paint(None)
        self.assertTrue(window.picture.Ready()); raster.assert_called_once()
        self.assertFalse(window.gate.acknowledged)
        window_method('qualify_draft')(window, None)
        window.start.assert_called_once()
        self.assertTrue(window.gate.acknowledged); self.assertIsNone(window.qualified)
        self.assertEqual((window.gate.review.pose, window.gate.review.moves), before)
        window.picture.test_dc.DrawBitmap.assert_called_once()

    def test_same_size_events_keep_current_bitmap_but_actual_resize_requires_render(self):
        picture = canvas(Mock(), Mock())
        with patch.object(pg, 'bitmap_with_labels', return_value=Mock()) as raster:
            picture.SetScene({'svg': '<svg/>', 'size': (800, 500)})
            for _ in range(2): picture.resized(Mock())
            self.assertTrue(picture.Ready())
            raster.assert_called_once()
            picture.GetClientSize.return_value = (640, 480)
            picture.resized(Mock())
            self.assertFalse(picture.Ready())
            picture.paint(None)
            self.assertTrue(picture.Ready())
            self.assertEqual(raster.call_count, 2)

    def test_placement_approval_does_not_survive_late_render_failure(self):
        window, previous = self.presentation_window(); window.start = Mock()
        window.picture = canvas(MethodType(window_method('preview_failed'), window))
        with patch.object(pg, 'bitmap_with_labels', return_value=Mock()):
            window.picture.SetScene({'svg': '<svg/>', 'size': (1000, 540)})
        window_method('qualify_draft')(window, None)
        window.start.assert_called_once()
        self.assertTrue(window.gate.acknowledged)
        window.picture.GetClientSize.return_value = (900, 515)
        with patch.object(pg, 'bitmap_with_labels', side_effect=RuntimeError('deliberate late raster failure')):
            window.picture.paint(None)
        self.assertFalse(window.gate.acknowledged); self.assertFalse(window.picture.Ready())
        self.assertIsNone(window.qualified)
        with self.assertRaises(ValueError): window.gate.check(previous['ticket'])
        self.assertIn('No current placement validation', window.findings.SetValue.call_args.args[0])

    def test_dirty_unready_or_missing_draft_does_not_navigate_or_validate(self):
        for dirty, unready, missing in [(True, False, False), (False, True, False), (False, False, True)]:
            with self.subTest(dirty=dirty, unready=unready, missing=missing):
                window = self.window(); window.gate.dirty = dirty; window.start = Mock()
                window.picture.Ready.return_value = not unready
                if missing: window.gate.review = None
                window_method('qualify_draft')(window, None)
                window.pages.SetSelection.assert_not_called()
                window.start.assert_not_called()
                self.assertIsNone(window.qualified)
                with self.assertRaises(ValueError): window.gate.ticket()

    def test_late_preview_ready_after_source_change_reject_or_cancel_cannot_restore_approval(self):
        for action in ('source_changed', 'reject_draft', 'cancel_work'):
            with self.subTest(action=action):
                window, previous = self.presentation_window(); window.qualified = previous
                window.owned_workspace = Mock(side_effect=ValueError('receipt unavailable in control'))
                window.picture = canvas(MethodType(window_method('preview_failed'), window),
                    MethodType(window_method('preview_ready'), window))
                queued = []; window.picture.test_call_after.side_effect = queued.append
                with patch.object(pg.placement_view, 'scene', return_value={'svg': '<svg/>', 'size': (1000, 540)}), \
                        patch.object(pg, 'bitmap_with_labels', return_value=Mock()):
                    window.present()
                    self.assertTrue(queued)
                    window_method(action)(window, Mock())
                    for callback in queued: callback()
                self.assertFalse(window.gate.acknowledged); self.assertIsNone(window.qualified)
                with self.assertRaises(ValueError): window.gate.check(previous['ticket'])

    def test_source_settings_and_rejection_clear_success_findings_and_diagram(self):
        for action in ('source_changed', 'settings_changed', 'reject_draft'):
            window, result = self.presentation_window(); window.qualified = result
            window.owned_workspace = Mock(side_effect=ValueError('receipt write deliberately unavailable'))
            with self.subTest(action=action): window_method(action)(window, Mock())
            self.assertIsNone(window.qualified); self.assertIsNone(window.gate.review)
            window.picture.SetScene.assert_called_once_with(None)
            text = window.findings.SetValue.call_args.args[0]
            self.assertIn('No current placement draft or validation', text)
            self.assertNotIn('Placement validated', text)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])

    def test_failed_edit_retains_pose_and_pending_text_but_not_qualification(self):
        window, result = self.presentation_window(); window.qualified = result
        original = copy.deepcopy(window.gate.review.moves)
        window.gate.review.edit_many = Mock(side_effect=ValueError('outside allowed rectangle'))
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>') as render:
            window_method('edit')(window, None)
        self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
        self.assertIn('Pending edits', render.call_args.kwargs['state'])
        self.assertEqual(window.gate.review.moves, original)
        window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()
        window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
        self.assertIn('previous pose retained', window.message.call_args.args[0])

    def test_component_switch_preserves_pending_text_and_loads_committed_selection(self):
        window, result = self.presentation_window(); window.present = Mock()
        window.coordinates = MethodType(window_method('coordinates'), window)
        window.x.GetValue.return_value = '20.'; window.y.GetValue.return_value = '10.4'
        window_method('pending_edit')(window, Mock())
        self.assertEqual(window.pending_coordinates, {'two': ['20.', '10.4']})
        queued = []; wx = SimpleNamespace(CallAfter=lambda action: queued.append(action))
        # Popup still reports the previous part during its event; commits later.
        window_method('select_part', wx=wx)(window, None)
        window.part.GetSelection.return_value = 0
        queued.pop()()
        self.assertEqual(window.editing_component, 'one')
        window.x.ChangeValue.assert_called_with('1'); window.y.ChangeValue.assert_called_with('2')
        self.assertTrue(window.gate.dirty)
        with self.assertRaises(ValueError): window.gate.check(result['ticket'])
        window.part.GetSelection.return_value = 1
        window_method('select_part', wx=wx)(window, None); queued.pop()()
        window.x.ChangeValue.assert_called_with('20.'); window.y.ChangeValue.assert_called_with('10.4')
        self.assertEqual(window.pending_coordinates, {'two': ['20.', '10.4']})

    def test_queued_component_load_cannot_overwrite_a_newer_edit_or_review(self):
        for action in ('edit', 'discard', 'close'):
            window, _ = self.presentation_window(); window.present = Mock(); window.coordinates = Mock()
            queued = []; wx = SimpleNamespace(CallAfter=lambda function: queued.append(function))
            window_method('select_part', wx=wx)(window, None)
            if action == 'close': window.gate.close()
            elif action == 'discard': window.revoke(discard=True)
            else: window_method('pending_edit')(window, Mock())
            queued.pop()()
            window.coordinates.assert_not_called()

    def test_unloaded_component_text_cannot_be_assigned_to_another_part(self):
        for action in ('pending_edit', 'edit'):
            window, result = self.presentation_window(); window.present = Mock()
            window.gate.review.edit_many = Mock(); window.part.GetSelection.return_value = 0
            # Coordinates still belong to part two while popup now displays one.
            window.pending_coordinates = {'two': ['20', '10.4']}
            window_method(action)(window, Mock())
            self.assertEqual(window.pending_coordinates, {'two': ['20', '10.4']})
            window.gate.review.edit_many.assert_not_called(); self.assertTrue(window.gate.dirty)
            self.assertIsNone(window.qualified)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])
            self.assertIn('Choose the component again', window.message.call_args.args[0])

    def test_update_submits_all_pending_components_once_and_keeps_refusal_atomic(self):
        for rejected in (False, True):
            window, _ = self.presentation_window(); window.present = Mock(); window.render = Mock()
            window.pending_coordinates = {'one': ['16.2', '10.4']}
            window.x.GetValue.return_value = '20.8'; window.y.GetValue.return_value = '10.4'
            window.gate.review.edit_many = Mock(side_effect=ValueError('overlap') if rejected else None)
            original = copy.deepcopy(window.gate.review.moves)
            window_method('edit')(window, None)
            window.gate.review.edit_many.assert_called_once_with({'one': ['16.2', '10.4'], 'two': ['20.8', '10.4']})
            self.assertFalse(window.gate.acknowledged)
            if rejected:
                window.render.assert_not_called(); self.assertTrue(window.gate.dirty)
                self.assertEqual(window.gate.review.moves, original)
                self.assertEqual(len(window.pending_coordinates), 2)
            else:
                window.render.assert_called_once_with(); self.assertFalse(window.gate.dirty)

    def test_explicit_render_or_discard_clears_pending_coordinates(self):
        window, _ = self.presentation_window(); window.present = Mock(); window.coordinates = Mock()
        window.pending_coordinates = {'two': ['20.', '10.4']}
        window_method('render', wx=SimpleNamespace(NOT_FOUND=-1))(window)
        self.assertEqual(window.pending_coordinates, {})
        window.pending_coordinates = {'two': ['20.', '10.4']}
        window.revoke(discard=True)
        self.assertEqual(window.pending_coordinates, {}); self.assertIsNone(window.editing_component)

    def test_invalid_alternative_cannot_clear_dirty_batch_or_reenable_approval(self):
        window, _ = self.presentation_window(); window.present = Mock(); window.render = Mock()
        window.pending_coordinates = {'two': ['20.', '10.4']}
        window.gate.review.choose = Mock(side_effect=ValueError('Unavailable alternative'))
        window_method('choose_alternative')(window, None)
        self.assertTrue(window.gate.dirty); self.assertFalse(window.gate.acknowledged)
        self.assertEqual(window.pending_coordinates, {'two': ['20.', '10.4']})
        window.render.assert_not_called()

    def test_invalid_alternative_cannot_approve_unbound_typed_coordinates(self):
        window, _ = self.presentation_window(); window.present = Mock(); window.render = Mock()
        window.part.GetSelection.return_value = 0  # Text still belongs to part two.
        window_method('pending_edit')(window, Mock())
        self.assertTrue(window.gate.dirty); self.assertEqual(window.pending_coordinates, {})
        window.gate.review.choose = Mock(side_effect=ValueError('Unavailable alternative'))
        window_method('choose_alternative')(window, None)
        self.assertTrue(window.gate.dirty)
        window.start = Mock()
        window_method('qualify_draft')(window, None)
        window.start.assert_not_called()
        with self.assertRaises(ValueError): window.gate.ticket()
        self.assertFalse(window.gate.acknowledged); window.render.assert_not_called()

    def test_redraw_failure_rolls_back_real_atomic_edit_and_preserves_typed_batch(self):
        from autorouter import placement_intent as intent
        from experiments.placement_native_proposal_v1 import contract, multipad_fixture as fixture
        with tempfile.TemporaryDirectory(prefix='placement-redraw-') as temporary:
            board = fixture.write_project(Path(temporary).resolve() / 'source')
            inspected = intent.inspect_saved(board)
            selected = [fixture.uid(ref + '-footprint') for ref in ('J1', 'J2')]
            settings = intent.settings(selected, [7000000, 7000000, 31000000, 13000000])
            moves = dict(zip(selected, [[14000000, 10000000], [20000000, 10000000]]))
            pose = contract.validate_moves(inspected['observation'], moves,
                scope=contract.MULTIPAD_SCOPE, selected=selected, region_nm=settings['region_nm'])
            review = intent.Review(dict(kind='autorouter.placement-proposals.v1', inspection=inspected,
                settings=settings, search=dict(status='proposals_ready', alternatives=[dict(candidate=pose)])))
            window, _ = self.presentation_window(); window.gate.attach(review)
            window.alternative_labels = ['Alternative 1']; window.alternative_targets = [0]
            window.alternative.GetSelection.return_value = 0
            window.editing_component = selected[1]; window.part.GetSelection.return_value = 1
            window.pending_coordinates = {selected[0]: ['20', '10']}
            window.x.GetValue.return_value = '14'; window.y.GetValue.return_value = '10'
            window.coordinates = MethodType(window_method('coordinates'), window)
            window.render = MethodType(window_method('render', wx=SimpleNamespace(NOT_FOUND=-1)), window)
            window.present = Mock(side_effect=RuntimeError('deliberate bitmap failure'))
            previous = copy.deepcopy((review.pose, review.moves, review.revision))
            window_method('edit')(window, None)
            self.assertEqual((review.pose, review.moves, review.revision), previous)
            self.assertEqual(window.pending_coordinates, {selected[0]: ['20', '10'], selected[1]: ['14', '10']})
            window.x.ChangeValue.assert_called_with('14'); window.y.ChangeValue.assert_called_with('10')
            window.part.SetSelection.assert_called_with(1)
            self.assertEqual(window.alternative_labels, ['Alternative 1'])
            self.assertEqual(window.alternative_targets, [0])
            window.alternative.Set.assert_called_with(['Alternative 1'])
            window.alternative.SetSelection.assert_called_with(0)
            self.assertIsNone(review.intent); self.assertTrue(window.gate.dirty)
            self.assertFalse(window.gate.acknowledged); self.assertIsNone(window.qualified)
            self.assertIn('previous pose retained', window.message.call_args.args[0])

    def test_stale_origin_at_routing_open_removes_success_and_handoff_authority(self):
        window, result = self.presentation_window(); window.qualified = result
        result['guard'].check.side_effect = ValueError('source changed on disk')
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>') as render, patch.object(gui, 'create_window') as factory:
            window_method('open_routing')(window, None)
        factory.assert_not_called(); self.assertIsNone(window.qualified)
        self.assertIn('Validation revoked', render.call_args.kwargs['state'])
        self.assertNotIn('Placement validated', window.findings.SetValue.call_args.args[0])
        self.assertIn('source changed on disk', window.message.call_args.args[0])

    def test_presentation_cannot_keep_success_after_review_ticket_changes(self):
        window, result = self.presentation_window(); window.qualified = result
        window.gate.review.revision += 1
        with patch.object(pg.placement_view, 'scene', return_value='<svg/>') as render:
            window.present()
        self.assertIsNone(window.qualified)
        self.assertIn('Validation revoked', render.call_args.kwargs['state'])
        self.assertNotIn('Placement validated', window.findings.SetValue.call_args.args[0])

    def test_refusal_or_cancellation_keeps_unapplied_coordinate_text_dirty(self):
        for action in ('present', 'cancel_work', 'open_routing', 'finish'):
            window, result = self.presentation_window(); window.qualified = result
            window.gate.invalidate(dirty=True); window.x.GetValue.return_value = '26.'
            with self.subTest(action=action), patch.object(pg.placement_view, 'scene', return_value='<svg/>'):
                if action == 'present': window.present()
                elif action == 'finish':
                    window_method('finish')(window, window.job, window.gate.generation,
                                            None, 'validation refused', Mock())
                else: window_method(action)(window, None)
            self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
            window.gate.acknowledged = True
            with self.assertRaises(ValueError): window.gate.ticket()
            window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()
            self.assertIn('Pending edits', window.findings.SetValue.call_args.args[0])

    def test_render_and_bitmap_failure_cannot_prevent_cancel_or_leave_success(self):
        for failure in ('render', 'bitmap'):
            window, result = self.presentation_window(); window.qualified = result
            window.busy = True
            original = copy.deepcopy(window.gate.review.moves)
            def fail(*args, **kwargs):
                self.assertTrue(window.cancel_event.is_set())
                self.assertTrue(window.job.cancel_requested)
                raise RuntimeError('deliberate ' + failure + ' failure')
            if failure == 'bitmap':
                window.picture=canvas(Mock(side_effect=AssertionError('initial raster failure is synchronous')))
            with self.subTest(failure=failure), patch.object(pg.placement_view, 'scene',
                    side_effect=fail if failure == 'render' else None, return_value={'svg':'<svg/>','size':(1000,540)}), \
                    patch.object(pg,'bitmap_with_labels',side_effect=fail if failure=='bitmap'else None):
                window_method('cancel_work')(window, None)
            self.assertIsNone(window.qualified)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])
            self.assertEqual(window.picture.SetScene.call_args_list[0].args,(None,))
            if failure=='bitmap':
                self.assertFalse(window.picture.Ready());self.assertIsNone(window.picture.display)
                self.assertEqual(window.picture.SetScene.call_count,2)
            else:window.picture.SetScene.assert_called_once_with(None)
            text = window.findings.SetValue.call_args.args[0]
            self.assertIn('Placement preview refused: deliberate ' + failure + ' failure', text)
            self.assertIn('No current placement validation', text)
            self.assertNotIn('Placement validated', text)
            self.assertEqual(window.gate.review.moves, original)
            window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
            window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

    def test_stale_presentation_failure_keeps_revocation_and_pending_edits_visible(self):
        for failure in ('render', 'bitmap'):
            window, result = self.presentation_window(); window.qualified = result
            window.gate.invalidate(dirty=True); window.x.GetValue.return_value = '26.'
            original = copy.deepcopy(window.gate.review.moves)
            window.present = MethodType(window_method('present', wx=SimpleNamespace(NOT_FOUND=-1)), window)
            if failure=='bitmap':window.picture=canvas(Mock(side_effect=AssertionError('no asynchronous callback')))
            with self.subTest(failure=failure), patch.object(pg.placement_view, 'scene',
                    side_effect=RuntimeError('deliberate render failure') if failure == 'render' else None,
                    return_value={'svg':'<svg/>','size':(1000,540)}) as render, \
                    patch.object(pg,'bitmap_with_labels',side_effect=RuntimeError('deliberate bitmap failure')):
                window.present()
            self.assertEqual(render.call_count, 1)  # Stale-ticket re-entry is bounded.
            self.assertIsNone(window.qualified); self.assertTrue(window.gate.dirty)
            with self.assertRaises(ValueError): window.gate.check(result['ticket'])
            self.assertEqual(window.picture.SetScene.call_args_list[0].args,(None,))
            if failure=='bitmap':
                self.assertFalse(window.picture.Ready());self.assertIsNone(window.picture.display)
                self.assertEqual(window.picture.SetScene.call_count,2)
            else:window.picture.SetScene.assert_called_once_with(None)
            text = window.findings.SetValue.call_args.args[0]
            self.assertIn('Placement preview refused: deliberate ' + failure + ' failure', text)
            self.assertIn('pending coordinate text are retained', text)
            self.assertNotIn('Placement validated', text)
            self.assertEqual(window.gate.review.moves, original)
            window.part.SetSelection.assert_not_called(); window.alternative.SetSelection.assert_not_called()
            window.x.ChangeValue.assert_not_called(); window.y.ChangeValue.assert_not_called()

    def test_actual_late_paint_callback_revokes_validation_without_render_retry(self):
        window,result=self.presentation_window();window.qualified=result;window.routing=Mock()
        self.assertIsNone(window.gate.check(result['ticket']))
        previous=copy.deepcopy((window.gate.review.pose,window.gate.review.moves,window.pending_coordinates))
        window.present=Mock(side_effect=AssertionError('paint failure must not retry presentation'))
        window.picture=canvas(MethodType(window_method('preview_failed'),window))
        display={'svg':'<svg/>','size':(1000,540)}
        with patch.object(pg,'bitmap_with_labels',return_value=Mock()):window.picture.SetScene(display)
        self.assertTrue(window.picture.Ready());window.picture.bitmap=None
        with patch.object(pg,'bitmap_with_labels',side_effect=RuntimeError('late paint failure'))as raster:
            window.picture.paint(None)
        raster.assert_called_once();window.present.assert_not_called()
        self.assertFalse(window.picture.Ready());self.assertIsNone(window.picture.display)
        self.assertIsNone(window.qualified);self.assertFalse(window.gate.acknowledged)
        self.assertIsNone(window.gate.review.intent);self.assertFalse(window.gate.dirty)
        self.assertEqual((window.gate.review.pose,window.gate.review.moves,window.pending_coordinates),previous)
        window.routing.Close.assert_called_once()
        with self.assertRaises(ValueError):window.gate.check(result['ticket'])
        self.assertIn('No current placement validation',window.findings.SetValue.call_args.args[0])
        with patch.object(gui,'create_window')as factory:window_method('open_routing')(window,None)
        factory.assert_not_called()

    def test_unready_canvas_cannot_qualify_or_open_routing(self):
        for name in ('qualify_draft','open_routing'):
            window,result=self.presentation_window();window.qualified=result;window.start=Mock()
            window.picture.Ready.return_value=False
            with self.subTest(action=name),patch.object(gui,'create_window')as factory:
                window_method(name)(window,None)
            window.start.assert_not_called();factory.assert_not_called();self.assertIsNone(window.qualified)
            with self.assertRaises(ValueError):window.gate.check(result['ticket'])

    def test_actual_drawbitmap_failure_revokes_validation_and_blocks_handoff(self):
        window,result=self.presentation_window();window.qualified=result
        self.assertIsNone(window.gate.check(result['ticket']))
        window.present=Mock()
        window.picture=canvas(MethodType(window_method('preview_failed'),window))
        with patch.object(pg,'bitmap_with_labels',return_value=Mock()):
            window.picture.SetScene({'svg':'<svg/>','size':(1000,540)})
        window.picture.test_dc.DrawBitmap.side_effect=RuntimeError('deliberate DrawBitmap failure')
        escaped=None
        try:window.picture.paint(None)
        except Exception as exc:escaped=str(exc)
        with patch.object(gui,'create_window',return_value=Mock(source_guard=result['guard']))as factory:
            window_method('open_routing')(window,None)
        self.assertFalse(factory.called,'DrawBitmap error escaped='+str(escaped)+'; failed paint must revoke before constructing a routing frame')
        self.assertIsNone(escaped);self.assertIsNone(window.qualified);self.assertFalse(window.picture.Ready())
        with self.assertRaises(ValueError):window.gate.check(result['ticket'])

    def test_actual_callback_rejects_and_records_without_inventing_acknowledgement(self):
        window = self.window(); window.gate.acknowledged = False
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp).resolve(); window.owned_workspace = lambda: folder
            window_method('reject_draft')(window, None)
            paths = list(folder.iterdir()); self.assertEqual(len(paths), 1)
            record = json.loads(paths[0].read_bytes())
            self.assertEqual(record['choice'], 'reject'); self.assertFalse(record['approval_granted'])
            self.assertFalse(record['execution_authorized']); self.assertFalse(record['human_PCB_approval'])
            self.assertIsNone(window.gate.review); self.assertFalse(window.gate.acknowledged)

    def test_factory_refuses_missing_app_worker_thread_and_nested_main(self):
        wx = Mock(); svg = Mock(); wx.GetApp.return_value = None
        with patch.dict(sys.modules, {'wx': wx, 'wx.svg': svg}):
            for callback in (False, True, 'approve', {}, 1):
                with self.subTest(callback=callback), self.assertRaises(ValueError):
                    pg.create_window('', on_closed=callback)
            with self.assertRaises(ValueError): pg.create_window('')
            wx.GetApp.return_value = object()
            with patch.object(threading, 'current_thread', return_value=object()):
                with self.assertRaises(ValueError): pg.create_window('')
            with self.assertRaises(ValueError): pg.main([])
        wx.App.assert_not_called()


if __name__ == '__main__':
    unittest.main()
