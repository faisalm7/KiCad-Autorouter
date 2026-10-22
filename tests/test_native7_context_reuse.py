"""Constructed Context reuse controls, not Native/engine/GUI qualification.

Reuse existing owned fixtures and explicit tool/static-preflight seams. Real
source/code/preferences inventories, Context seals and owner checks execute.
No parent/private-child result or live execution Budget may be reused here.
"""
import copy
from contextlib import ExitStack
import os
import shutil
import unittest
from unittest.mock import patch

from autorouter import _improve_context as child, floor_route as f, handoff as h
from autorouter import pipeline as p, strategy as s
from tests import test_native7_improve_parent as fixture
from tests import test_native7_guard_reconstruction as guard_fixture


class Native7ContextReuseControls(unittest.TestCase):
    setUp = fixture.Native7ParentControls.setUp
    make = fixture.Native7ParentControls.make
    record = fixture.Native7ParentControls.record
    parent_data = fixture.Native7ParentControls.parent_data
    mutation = guard_fixture.Native7GuardReconstruction.mutation

    def assert_empty(self, state):
        self.assertEqual(state['entries'], {})
        self.assertEqual(state['native7_contexts'], {})

    def test_construction_once_in_operation_nested_sharing_and_no_outside_reuse(self):
        data = self.parent_data()
        original_init = child._Context.__init__
        calls = []
        def counted(context, *args, **kwargs):
            calls.append(context)
            original_init(context, *args, **kwargs)
        with patch.object(child._Context, '__init__', counted):
            first = s.native7_incumbent_context(self.parent, data)
            self.assertIsNot(first, s.native7_incumbent_context(self.parent, data))
            self.assertEqual(len(calls), 2)
            with p.validation_readback_session():
                state = p._readback_session.get()
                cached = s.native7_incumbent_context(self.parent, data)
                self.assertIs(cached, s.native7_incumbent_context(self.parent, data))
                with p.validation_readback_session():
                    self.assertIs(cached, s.native7_incumbent_context(self.parent, data))
                self.assertEqual(len(calls), 3)
                self.assertEqual(len(state['native7_contexts']), 1)
            self.assert_empty(state)
            self.assertIsNone(p._readback_session.get())
            self.assertIsNot(cached, s.native7_incumbent_context(self.parent, data))
            self.assertEqual(len(calls), 4)

    def test_exact_and_canonical_constructor_request_changes_cannot_hit(self):
        data = self.parent_data()
        variants = [
            ('source', str(self.source.with_name('foreign.kicad_pcb'))),
            ('source_hashes', dict(self.hashes, **{self.source.name: '0' * 64})),
            ('tools', dict(self.tools, files={'changed': '0' * 64})),
            ('budget_seconds', 90.0), ('cpu_budget_seconds', 90.0),
            ('incumbent_assigned_seconds', 48.0),
            ('incumbent_allocation', dict(elapsed_wall_seconds=1.0, elapsed_cpu_seconds=2)),
            ('cpu_budget_seconds', True),
        ]
        for field, value in variants:
            with self.subTest(field=field, value=value), p.validation_readback_session():
                s.native7_incumbent_context(self.parent, data)
                state = p._readback_session.get()
                state['entries']['constructed-sentinel'] = None
                wrong = copy.deepcopy(data)
                wrong[field] = value
                with self.assertRaises(p.Rejected):
                    s.native7_incumbent_context(self.parent, wrong)
                self.assert_empty(state)
        with p.validation_readback_session():
            cached = s.native7_incumbent_context(self.parent, data)
            equivalent = copy.deepcopy(data)
            for field in ('tools', 'source_hashes', 'incumbent_allocation'):
                equivalent[field] = dict(reversed(list(equivalent[field].items())))
            self.assertIs(cached, s.native7_incumbent_context(self.parent, equivalent))

    def test_coherently_rebound_definition_does_not_renew_warmed_context(self):
        data = self.parent_data()
        path = self.parent / s.NATIVE7_PARENT_FILE
        raw = path.read_bytes()
        with p.validation_readback_session():
            s.native7_incumbent_context(self.parent, data)
            changed = copy.deepcopy(data)
            changed['incumbent_assigned_seconds'] = 47
            changed['incumbent_allocation']['elapsed_cpu_seconds'] = 3
            replacement = self.make(assigned_seconds=47,
                                    allocation=dict(elapsed_wall_seconds=1, elapsed_cpu_seconds=3))
            contract = f.read_json(path)
            contract['context'] = replacement.record()
            try:
                p.save_json(path, contract)
                changed['native7_improve_parent']['sha256'] = p.sha(path)
                with self.assertRaises(p.Rejected):
                    s.native7_incumbent_context(self.parent, changed)
                self.assert_empty(p._readback_session.get())
            finally:
                path.write_bytes(raw)

    def test_material_owner_sidecar_and_shape_faults_clear_all_reuse(self):
        data = self.parent_data()
        for kind in ('source', 'preferences', 'code', 'sidecar', 'rebound_sidecar',
                     'tools', 'owner', 'parent_replaced', 'source_hardlink', 'parent_shape'):
            with self.subTest(kind=kind), p.validation_readback_session(), self.mutation(kind, data) as mutate:
                s.native7_incumbent_context(self.parent, data)
                state = p._readback_session.get()
                state['entries']['constructed-sentinel'] = None
                mutate()
                with self.assertRaises(p.Rejected):
                    s.native7_incumbent_context(self.parent, data)
                self.assert_empty(state)

    def test_same_byte_code_hardlink_and_exact_owner_types_still_refuse(self):
        data = self.parent_data()
        link = self.base / 'retained-code-hardlink.py'
        for kind in ('code_link', 'owner_bool', 'owner_float'):
            with self.subTest(kind=kind), p.validation_readback_session():
                cached = s.native7_incumbent_context(self.parent, data)
                owner = copy.deepcopy(cached.parent_owner)
                try:
                    if kind == 'code_link':
                        os.link(self.parent / 'code' / 'strategy.py', link)
                    elif kind == 'owner_bool':
                        cached.parent_owner['created'] = 1
                    else:
                        cached.parent_owner['directory_identity'] = tuple(float(x) for x in owner['directory_identity'])
                    with self.assertRaises(p.Rejected):
                        s.native7_incumbent_context(self.parent, data)
                    self.assert_empty(p._readback_session.get())
                finally:
                    if link.exists():
                        link.unlink()
                    cached.parent_owner.clear()
                    cached.parent_owner.update(owner)

    def test_live_class_method_and_module_policy_changes_cannot_reuse_construction(self):
        data = self.parent_data()
        original_material = child._Context._material
        def material(context):
            return original_material(context)
        with p.validation_readback_session():
            first = s.native7_incumbent_context(self.parent, data)
            with patch.object(child._Context, '_material', material):
                second = s.native7_incumbent_context(self.parent, data)
                self.assertIsNot(first, second)
                self.assertEqual(first._seal, second._seal)
            with patch.object(child, 'RESERVE_SECONDS', 39), self.assertRaises(p.Rejected):
                s.native7_incumbent_context(self.parent, data)
            self.assert_empty(p._readback_session.get())

    def test_late_tool_callback_parent_replacement_is_not_rebased(self):
        data = self.parent_data()
        armed = [False]
        fired = []
        with self.mutation('parent_replaced', data) as mutate:
            def tools():
                if armed[0] and not fired:
                    fired.append(True)
                    mutate()
                return copy.deepcopy(self.tools)
            with patch.object(p, 'tool_manifest', tools), p.validation_readback_session():
                s.native7_incumbent_context(self.parent, data)
                armed[0] = True
                with self.assertRaises(p.Rejected):
                    s.native7_incumbent_context(self.parent, data)
                self.assertEqual(fired, [True])
                self.assert_empty(p._readback_session.get())

    def test_identity_change_during_initial_construction_never_populates(self):
        data = self.parent_data()
        original_record = child._Context.record
        fired = []
        def record(context):
            return original_record(context)
        with ExitStack() as changes:
            def tools():
                if not fired:
                    fired.append(True)
                    changes.enter_context(patch.object(child._Context, 'record', record))
                return copy.deepcopy(self.tools)
            with patch.object(p, 'tool_manifest', tools), p.validation_readback_session():
                with self.assertRaises(p.Rejected):
                    s.native7_incumbent_context(self.parent, data)
                self.assertEqual(fired, [True])
                self.assert_empty(p._readback_session.get())

    def test_bound_eight_original_contexts_and_operation_exit(self):
        data = self.parent_data()
        records = []
        for index in range(9):
            folder = self.workspace / ('owned-route-' + str(index))
            folder.mkdir()
            for name in ('code', 'snapshot'):
                shutil.copytree(self.parent / name, folder / name)
            shutil.copy2(self.parent / 'pruning-preferences.json', folder / 'pruning-preferences.json')
            owner = {}
            h.capture_destination(owner, folder)
            definition = self.make(parent=folder, parent_owner=owner)
            value = copy.deepcopy(data)
            s._bind_native7_parent(folder, value, definition)
            records.append((folder, value))
        with p.validation_readback_session():
            state = p._readback_session.get()
            contexts = []
            for folder, value in records:
                contexts.append(s.native7_incumbent_context(folder, value))
                self.assertLessEqual(len(state['native7_contexts']), 8)
            self.assertEqual(len(state['native7_contexts']), 8)
            self.assertIsNot(contexts[0], s.native7_incumbent_context(*records[0]))
            self.assertEqual(len(state['native7_contexts']), 8)
        self.assert_empty(state)

    def test_nested_handled_errors_and_cancellation_clear_both_maps(self):
        data = self.parent_data()
        with p.validation_readback_session():
            state = p._readback_session.get()
            for failure in (ValueError('constructed failure'), KeyboardInterrupt()):
                previous = s.native7_incumbent_context(self.parent, data)
                state['entries']['constructed-sentinel'] = None
                try:
                    with p.validation_readback_session():
                        raise failure
                except BaseException:
                    pass
                self.assert_empty(state)
                self.assertIsNot(previous, s.native7_incumbent_context(self.parent, data))

    def test_no_budget_or_private_child_result_reuse_and_failure_clears(self):
        data = self.parent_data()
        # Retain authored child metadata for canonical filename/existence
        # intake; no Native acceptance is supplied by this mocked reader.
        p.save_json(self.context.output / 'result.json', self.record())
        with patch.object(child, '_Budget', side_effect=AssertionError('no live Budget')) as budget, \
                patch.object(p, '_check_result_uncached', return_value={'constructed': True}) as reader, \
                p.validation_readback_session():
            context = s.native7_incumbent_context(self.parent, data)
            state = p._readback_session.get()
            self.assertFalse(hasattr(context, 'parent_job'))
            for _ in range(2):
                p.check_result(context.output / 'result.json', _improve_context=context)
            self.assertEqual(reader.call_count, 2)
            self.assertEqual(state['entries'], {})
            self.assertEqual(len(state['native7_contexts']), 1)
            budget.assert_not_called()
            state['entries']['constructed-sentinel'] = None
            reader.side_effect = p.Rejected('constructed private reader failure')
            with self.assertRaises(p.Rejected):
                p.check_result(context.output / 'result.json', _improve_context=context)
            self.assert_empty(state)

    def test_forged_marker_and_missing_constructor_intake_fail_closed(self):
        data = self.parent_data()
        for field in (None, 'source_hashes', 'cpu_budget_seconds', 'incumbent_assigned_seconds'):
            with self.subTest(missing=field), p.validation_readback_session():
                s.native7_incumbent_context(self.parent, data)
                state = p._readback_session.get()
                state['entries']['constructed-sentinel'] = None
                wrong = {'native7_improve_parent': {}} if field is None else copy.deepcopy(data)
                if field is not None:
                    del wrong[field]
                expected = p.Rejected if field is None else (p.Rejected, KeyError)
                with self.assertRaises(expected):
                    s.native7_incumbent_context(self.parent, wrong)
                self.assert_empty(state)


if __name__ == '__main__':
    unittest.main()
