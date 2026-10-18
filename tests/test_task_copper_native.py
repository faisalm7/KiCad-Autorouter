"""Synthetic Native API guard controls only; no pcbnew or routing qualification."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import uuid

from autorouter import sexpr as sx, task_copper as tc
from tests.test_floor_via_observation import Via as LayerWidthVia

IDS = [str(uuid.UUID(int=value)) for value in range(1, 10)]


class Track:
    native_kind = 'PCB_TRACK'

    def __init__(self, identity=IDS[0], locked=False):
        self.identity = identity
        self.m_Uuid = SimpleNamespace(AsString=lambda: self.identity)
        self.locked = locked
        self.lock_calls = []
        self.lock_faults = {}
        self.net = 'A'
        self.width = 300000
        self.start, self.end, self.mid = (0, 0), (5000000, 0), (2500000, 1000000)
        self.layer = 0

    def GetClass(self): return self.native_kind
    def IsLocked(self): return self.locked
    def GetNetname(self): return self.net
    def GetWidth(self): return self.width
    def GetStart(self): return SimpleNamespace(x=self.start[0], y=self.start[1])
    def GetEnd(self): return SimpleNamespace(x=self.end[0], y=self.end[1])
    def GetLayer(self): return self.layer

    def SetLocked(self, value):
        self.lock_calls.append(value)
        fault = self.lock_faults.get(value)
        if fault == 'raise': raise RuntimeError('synthetic SetLocked failure')
        if fault != 'ignore': self.locked = value
        if fault == 'mutate_then_raise': raise RuntimeError('synthetic SetLocked failure after mutation')


class Arc(Track):
    native_kind = 'PCB_ARC'

    def GetMid(self): return SimpleNamespace(x=self.mid[0], y=self.mid[1])


class Via(Track, LayerWidthVia):
    native_kind = 'PCB_VIA'

    def __init__(self, identity=IDS[1], locked=True):
        Track.__init__(self, identity, locked)
        LayerWidthVia.__init__(self, widths=(800000, 800000))
        self.at, self.drill, self.top, self.bottom = (1000000, 1000000), 400000, 0, 2

    GetWidth = LayerWidthVia.GetWidth
    GetViaType = LayerWidthVia.GetViaType
    IsOnLayer = LayerWidthVia.IsOnLayer
    def GetPosition(self): return SimpleNamespace(x=self.at[0], y=self.at[1])
    def GetDrillValue(self): return self.drill
    def TopLayer(self): return self.top
    def BottomLayer(self): return self.bottom


class Board:
    def __init__(self, items): self.items = items
    def GetTracks(self): return list(self.items)


class TaskCopperNativeGuards(unittest.TestCase):
    def make(self, items=None, version='10.0.0'):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        source = Path(directory.name).resolve() / 'owned.kicad_pcb'
        source.with_suffix('.kicad_pro').write_bytes(b'{"owned_guard_fixture":true}\n')
        board = Board([Track(), Via(), Arc(IDS[2])] if items is None else items)
        tree = ['kicad_pcb', ['version', '20241229'], ['net', '1', '"A"']]
        for item in board.items:
            if isinstance(item, Via):
                node = sx.parse('(via (at 1 1) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1))')
            elif isinstance(item, Arc):
                node = sx.parse('(arc (start 0 0) (mid 2.5 1) (end 5 0) (width 0.3) (layer "F.Cu") (net 1))')
            else:
                node = sx.parse('(segment (start 0 0) (end 5 0) (width 0.3) (layer "F.Cu") (net 1))')
            if item.locked: node.append(['locked', 'yes'])
            node.append(['uuid', '"' + item.identity + '"'])
            tree.append(node)
        sx.write(source, tree)
        api = SimpleNamespace(PCB_VIA=Via, PCB_ARC=Arc, F_Cu=0, B_Cu=2,
                              GetBuildVersion=lambda: version)
        return board, source, api

    def test_success_fixes_all_task_kinds_then_restores_only_original_false(self):
        board, source, api = self.make()
        original = tc.native_census(board, api)
        original_bytes = (source.read_bytes(), source.with_suffix('.kicad_pro').read_bytes())
        result = object()

        def operation():
            self.assertTrue(all(item.locked is True for item in board.items))
            return result

        self.assertIs(tc.invoke(board, source, api, operation), result)
        self.assertEqual(tc.native_census(board, api), original)
        self.assertEqual([item.lock_calls for item in board.items], [[True, False], [True], [True, False]])
        self.assertEqual((source.read_bytes(), source.with_suffix('.kicad_pro').read_bytes()), original_bytes)

    def test_operation_exceptions_restore_locks_and_preserve_original_exception(self):
        for failure in (RuntimeError('synthetic operation'), KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(exception=type(failure).__name__):
                board, source, api = self.make()
                before = tc.native_census(board, api)

                def operation(): raise failure

                with self.assertRaises(type(failure)) as caught:
                    tc.invoke(board, source, api, operation)
                self.assertIs(caught.exception, failure)
                self.assertEqual(tc.native_census(board, api), before)

    def test_source_lock_decoder_matches_shared_scope_for_bare_locked(self):
        # Software decoding control only. This does not qualify another Native
        # source spelling or override strict import's serialization requirements.
        board,source,api=self.make()
        tree=sx.read(source)
        via=sx.children(tree,'via')[0]
        via.remove(sx.one(via,'locked'));via.append('locked');sx.write(source,tree)
        self.assertTrue(board.items[1].locked)
        self.assertIs(tc.invoke(board,source,api,lambda:True),True)
        self.assertTrue(board.items[1].locked)

    def test_original_true_lock_loss_refuses_without_repairing_it(self):
        board, source, api = self.make()
        locked_original = board.items[1]

        def operation(): locked_original.locked = False

        with self.assertRaisesRegex(ValueError, 'restoration failed'):
            tc.invoke(board, source, api, operation, importing=True)
        self.assertFalse(locked_original.locked)
        self.assertEqual(locked_original.lock_calls, [True])

    def test_operation_missing_duplicate_or_replaced_uuid_refuses(self):
        for change in ('missing', 'duplicate', 'replaced', 'zero', 'malformed'):
            with self.subTest(change=change):
                board, source, api = self.make()
                called = []

                def operation():
                    called.append(True)
                    self.assertTrue(all(item.locked is True for item in board.items))
                    if change == 'missing': board.items.pop(0)
                    elif change == 'duplicate': board.items.append(copy.deepcopy(board.items[0]))
                    elif change == 'replaced': board.items[0].identity = IDS[5]
                    elif change == 'zero': board.items[0].identity = str(uuid.UUID(int=0))
                    else: board.items[0].identity = 'not-a-uuid'

                with self.assertRaises(ValueError):
                    tc.invoke(board, source, api, operation, importing=True)
                self.assertEqual(called, [True])

    def test_operation_geometry_net_width_drill_and_layer_changes_refuse(self):
        mutations = {
            'segment-start': lambda rows: setattr(rows[0], 'start', (1, 0)),
            'segment-end': lambda rows: setattr(rows[0], 'end', (5000001, 0)),
            'segment-width': lambda rows: setattr(rows[0], 'width', 300001),
            'segment-layer': lambda rows: setattr(rows[0], 'layer', 2),
            'net': lambda rows: setattr(rows[0], 'net', 'B'),
            'arc-mid': lambda rows: setattr(rows[2], 'mid', (2500001, 1000000)),
            'via-position': lambda rows: setattr(rows[1], 'at', (1000001, 1000000)),
            'via-drill': lambda rows: setattr(rows[1], 'drill', 400001),
            'via-top': lambda rows: setattr(rows[1], 'top', 1),
            'via-bottom': lambda rows: setattr(rows[1], 'bottom', 1),
            'via-diameter': lambda rows: rows[1].widths.update({0: 800001, 2: 800001}),
            'via-type': lambda rows: setattr(rows[1], 'kind', 3),
        }
        for label, mutation in mutations.items():
            with self.subTest(change=label):
                board, source, api = self.make()
                called = []

                def operation():
                    called.append(True)
                    self.assertTrue(all(item.locked is True for item in board.items))
                    mutation(board.items)

                with self.assertRaises(ValueError):
                    tc.invoke(board, source, api, operation, importing=True)
                self.assertEqual(called, [True])

    def test_import_never_unlocks_generated_records(self):
        for generated_locked in (False, True):
            with self.subTest(generated_locked=generated_locked):
                board, source, api = self.make()
                generated = Track(IDS[3], locked=generated_locked)
                tc.invoke(board, source, api, lambda: board.items.append(generated), importing=True)
                self.assertIs(board.items[-1], generated)
                self.assertEqual(len(board.items), 4)
                self.assertIs(generated.locked, generated_locked)
                self.assertEqual(generated.lock_calls, [])
                self.assertEqual([item.locked for item in board.items[:3]], [False, True, False])

    def test_export_refuses_generated_records_without_unlocking_them(self):
        board, source, api = self.make()
        generated = Track(IDS[3], locked=True)
        with self.assertRaisesRegex(ValueError, 'changed or missed fixed task copper'):
            tc.invoke(board, source, api, lambda: board.items.append(generated))
        self.assertTrue(generated.locked)
        self.assertEqual(generated.lock_calls, [])
        self.assertEqual([item.locked for item in board.items[:3]], [False, True, False])

    def test_exception_does_not_unlock_generated_records(self):
        board, source, api = self.make()
        generated = Track(IDS[3], locked=True)

        def operation():
            board.items.append(generated)
            raise RuntimeError('synthetic import interruption')

        with self.assertRaisesRegex(RuntimeError, 'synthetic import interruption'):
            tc.invoke(board, source, api, operation, importing=True)
        self.assertTrue(generated.locked)
        self.assertEqual(generated.lock_calls, [])

    def test_zero_task_routes_are_valid_for_export_and_import(self):
        for importing in (False, True):
            with self.subTest(importing=importing):
                board, source, api = self.make([])
                called = []
                self.assertEqual(tc.invoke(board, source, api, lambda: called.append(True) or 'result',
                                           importing=importing), 'result')
                self.assertEqual(called, [True])
                self.assertEqual(board.items, [])

    def test_empty_import_leaves_generated_lock_as_returned_by_operation(self):
        board, source, api = self.make([])
        generated = Track(IDS[3], locked=True)
        tc.invoke(board, source, api, lambda: board.items.append(generated), importing=True)
        self.assertEqual(board.items, [generated])
        self.assertTrue(generated.locked)
        self.assertEqual(generated.lock_calls, [])

    def test_source_or_project_change_refuses_after_restoring_task_locks(self):
        for suffix in ('.kicad_pcb', '.kicad_pro'):
            with self.subTest(changed=suffix):
                board, source, api = self.make()
                path = source.with_suffix(suffix)
                before = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'source or project changed'):
                    tc.invoke(board, source, api, lambda: path.write_bytes(before + b'\n'))
                self.assertEqual([item.locked for item in board.items], [False, True, False])
                self.assertEqual(path.read_bytes(), before + b'\n')

    def test_source_native_uuid_population_mismatch_never_starts_operation(self):
        for change in ('missing', 'extra', 'duplicate', 'replaced'):
            with self.subTest(change=change):
                board, source, api = self.make()
                if change == 'missing': board.items.pop()
                elif change == 'extra': board.items.append(Track(IDS[4]))
                elif change == 'duplicate': board.items.append(copy.deepcopy(board.items[0]))
                else: board.items[0].identity = IDS[4]
                called = []
                with self.assertRaises(ValueError):
                    tc.invoke(board, source, api, lambda: called.append(True))
                self.assertEqual(called, [])
                self.assertTrue(all(not item.lock_calls for item in board.items))

    def test_source_native_lock_mismatch_or_untyped_lock_never_starts_operation(self):
        for index, changed in ((0, True), (1, False), (0, 1)):
            with self.subTest(index=index, native_lock=changed):
                board, source, api = self.make()
                board.items[index].locked = changed
                called = []
                with self.assertRaises(ValueError):
                    tc.invoke(board, source, api, lambda: called.append(True))
                self.assertEqual(called, [])
                self.assertTrue(all(not item.lock_calls for item in board.items))

    def test_fix_api_failure_or_ignored_lock_refuses_before_operation(self):
        for fault in ('raise', 'ignore', 'mutate_then_raise'):
            with self.subTest(fault=fault):
                board, source, api = self.make()
                board.items[0].lock_faults[True] = fault
                called = []
                with self.assertRaises(ValueError):
                    tc.invoke(board, source, api, lambda: called.append(True))
                self.assertEqual(called, [])

    def test_restore_api_failure_or_ignored_unlock_refuses(self):
        for fault in ('raise', 'ignore', 'mutate_then_raise'):
            with self.subTest(fault=fault):
                board, source, api = self.make()
                generated = Track(IDS[3], locked=True)
                board.items[0].lock_faults[False] = fault
                called = []

                def operation():
                    called.append(True)
                    board.items.append(generated)

                with self.assertRaisesRegex(ValueError, 'restoration failed'):
                    tc.invoke(board, source, api, operation, importing=True)
                self.assertEqual(called, [True])
                self.assertEqual(board.items[1].lock_calls, [True])
                self.assertEqual(generated.lock_calls, [])
                self.assertTrue(generated.locked)

    def test_unknown_native_version_and_untyped_importing_refuse_before_locking(self):
        for version, importing in (('10.0.7', False), ('9.0.2', False), ('unknown', False),
                                   ('10.0.0', 1), ('10.0.0', None)):
            with self.subTest(version=version, importing=importing):
                board, source, api = self.make(version=version)
                called = []
                with self.assertRaisesRegex(ValueError, 'qualified Native10.0.0'):
                    tc.invoke(board, source, api, lambda: called.append(True), importing=importing)
                self.assertEqual(called, [])
                self.assertTrue(all(not item.lock_calls for item in board.items))


if __name__ == '__main__':
    unittest.main()
