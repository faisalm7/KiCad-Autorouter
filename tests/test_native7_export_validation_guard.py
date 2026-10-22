"""Owned Context and byte-custody controls; never Native export qualification.

Reuse the existing private-parent fixture's explicit tool/preflight stubs.
Context reconstruction, owners, policy identity and export byte witnesses are
real. The constructed review/choice records do not assert central acceptance.
"""
import copy
from contextlib import ExitStack
import shutil
import unittest
from unittest.mock import patch

from autorouter import _improve_context as child, handoff as h, pipeline as p
from autorouter import review_export as e, strategy as s
from tests import test_native7_improve_parent as fixture
from tests import test_review_export as export_fixture


class Native7ExportValidationGuardControls(unittest.TestCase):
    make = fixture.Native7ParentControls.make
    record = fixture.Native7ParentControls.record
    parent_data = fixture.Native7ParentControls.parent_data

    def setUp(self):
        fixture.Native7ParentControls.setUp(self)
        self.report = self.parent_data()
        incumbent = self.record()
        p.save_json(self.context.output / 'result.json', incumbent)
        self.trial = self.parent / 'trials/trial-0000'
        self.trial.mkdir(parents=True)
        p.save_json(self.trial / 'result.json',
                    dict(status='quality_rejected', accepted=False, steps=[]))
        self.report['trials'] = [dict(id=self.trial.name,
            receipt=str(self.trial / 'result.json'),
            status='quality_rejected', accepted=False)]
        self.candidate = self.parent / 'candidate' / self.source.name
        shutil.copytree(self.source.parent, self.candidate.parent)
        self.report.update(candidate=str(self.candidate),
            candidate_sha256=p.sha(self.candidate), accepted=True,
            status='routing_accepted', native=dict(opens=0, blocking=0,
                warnings=1, exclusions=0, ignored_checks=[], findings=[]),
            metrics=dict(track_length_mm=1., vias=0))
        self.receipt = self.parent / 'result.json'
        p.save_json(self.receipt, self.report)
        self.review = self.workspace / 'review'
        self.choice = self.workspace / 'choice/choice.json'
        shutil.copytree(self.candidate.parent, self.review / 'project')
        p.save_json(self.review / 'review.json',
                    dict(receipt=str(self.receipt), project=str(self.review / 'project')))
        self.choice.parent.mkdir()
        p.save_json(self.choice, dict(choice='accept', receipt=str(self.receipt),
                    review=str(self.review / 'review.json')))
        inputs = {str(path): e.witness(path, project=small) for path, small in (
            (self.source.parent, True), (self.candidate.parent, True),
            (self.parent, False), (self.review, False), (self.choice.parent, False))}
        self.binding = dict(choice=str(self.choice), choice_sha256=p.sha(self.choice),
            review=str(self.review / 'review.json'),
            review_sha256=p.sha(self.review / 'review.json'),
            receipt=str(self.receipt), receipt_sha256=p.sha(self.receipt),
            source=str(self.source), validated_candidate=str(self.candidate),
            validated_candidate_sha256=p.sha(self.candidate), input_policy='native',
            source_receipt_schema=1, source_hashes=copy.deepcopy(self.hashes),
            candidate_hashes=copy.deepcopy(inputs[str(self.candidate.parent)]['files']),
            input_witnesses=inputs)

    def guarded(self):
        context = s.native7_incumbent_context(self.parent, self.report)
        identity = h._review_validation_identity()
        return context, e._export_validation_guard(self.binding, self.report, identity)

    def test_operation_lifetime_and_unchanged_material_return_no_acceptance(self):
        before = copy.deepcopy((self.binding, self.report))
        with self.assertRaises(p.Rejected):
            e._export_validation_guard(self.binding, self.report, object())
        with p.validation_readback_session():
            context, guard = self.guarded()
            self.assertIs(type(context), child._Context)
            self.assertFalse(hasattr(context, 'parent_job'))
            self.assertIsNone(guard())
            self.assertEqual((self.binding, self.report), before)
        with self.assertRaises(p.Rejected):
            guard()

    def test_source_candidate_incumbent_trial_choice_and_review_bytes_refuse(self):
        paths = (self.source.with_suffix('.kicad_pro'),
            self.candidate.with_suffix('.kicad_sch'),
            self.context.output / 'result.json', self.trial / 'result.json',
            self.receipt, self.choice, self.review / 'review.json',
            self.review / 'project' / self.source.with_suffix('.kicad_pro').name)
        with p.validation_readback_session():
            _, guard = self.guarded()
            for path in paths:
                raw = path.read_bytes()
                try:
                    path.write_bytes(raw + b'\n')
                    with self.subTest(path=path), self.assertRaises(p.Rejected):
                        guard()
                finally:
                    path.write_bytes(raw)
                self.assertIsNone(guard())

    def test_empty_directory_or_unrecorded_file_cannot_escape_witness(self):
        with p.validation_readback_session():
            _, guard = self.guarded()
            for root in (self.review, self.choice.parent, self.trial):
                extra = root / 'unrecorded-empty-directory'
                try:
                    extra.mkdir()
                    with self.subTest(root=root), self.assertRaises(p.Rejected):
                        guard()
                finally:
                    extra.rmdir()
            extra = self.trial / 'unrecorded.json'
            try:
                extra.write_text('{}')
                with self.assertRaises(p.Rejected):
                    guard()
            finally:
                extra.unlink()
            self.assertIsNone(guard())

    def test_parsed_binding_and_report_cannot_be_rebound_without_byte_change(self):
        changes = ((self.binding, 'validated_candidate_sha256', '0' * 64),
            (self.binding, 'source_receipt_schema', 1.),
            (self.binding['source_hashes'], self.source.name, '0' * 64),
            (self.report, 'accepted', False),
            (self.report['metrics'], 'track_length_mm', 2.))
        with p.validation_readback_session():
            _, guard = self.guarded()
            for target, key, value in changes:
                before = copy.deepcopy(target[key])
                try:
                    target[key] = value
                    with self.subTest(key=key), self.assertRaises(p.Rejected):
                        guard()
                finally:
                    target[key] = before
                self.assertIsNone(guard())

    def test_same_byte_parent_replacement_keeps_original_inode_authority(self):
        retained = self.workspace / 'retained-export-parent'
        with p.validation_readback_session():
            _, guard = self.guarded()
            self.parent.rename(retained)
            try:
                shutil.copytree(retained, self.parent)
                with self.assertRaises(p.Rejected):
                    guard()
            finally:
                shutil.rmtree(self.parent)
                retained.rename(self.parent)
            self.assertIsNone(guard())

    def test_equal_valued_owner_types_and_context_seal_remain_bound(self):
        with p.validation_readback_session():
            context, guard = self.guarded()
            for mapping in ('parent_owner', '_owner'):
                for key, value in (('created', 1), ('directory_identity',
                        tuple(float(x) for x in self.owner['directory_identity']))):
                    target = getattr(context, mapping)
                    before = copy.deepcopy(target)
                    try:
                        target[key] = value
                        with self.subTest(mapping=mapping, key=key), self.assertRaises(p.Rejected):
                            guard()
                    finally:
                        target.clear()
                        target.update(before)
            seal = context._seal
            try:
                object.__setattr__(context, '_seal', 'changed')
                with self.assertRaises(p.Rejected):
                    guard()
            finally:
                object.__setattr__(context, '_seal', seal)
            self.assertIsNone(guard())

    def test_export_callbacks_constants_and_context_methods_are_live_policy(self):
        original_check = child._Context.check
        def checked(context):
            return original_check(context)
        changes = ((e, 'bind', lambda *a, **kw: None),
            (e, '_export_validation_guard', lambda *a, **kw: None),
            (e, 'bound_material', lambda *a, **kw: None),
            (e, 'KIND', 'changed-export-policy'),
            (e, 'OUTPUT_BYTES', e.OUTPUT_BYTES + 1),
            (child._Context, 'check', checked))
        for target, name, value in changes:
            with self.subTest(name=name), p.validation_readback_session():
                _, guard = self.guarded()
                with patch.object(target, name, value), self.assertRaises(p.Rejected):
                    guard()

    def test_policy_replaced_during_material_is_checked_after_callback(self):
        material = e.bound_material
        changes = (('bind', lambda *a, **kw: None),
            ('_export_validation_guard', lambda *a, **kw: None),
            ('KIND', 'changed-during-material'))
        for name, value in changes:
            armed = [False]
            with self.subTest(name=name), ExitStack() as stack:
                def callback(binding):
                    material(binding)
                    if armed[0]:
                        armed[0] = False
                        stack.enter_context(patch.object(e, name, value))
                with patch.object(e, 'bound_material', callback), p.validation_readback_session():
                    _, guard = self.guarded()
                    armed[0] = True
                    with self.assertRaises(p.Rejected):
                        guard()

    def test_parsed_binding_or_report_changed_during_material_refuses(self):
        material = e.bound_material
        for target, key, value in ((self.binding, 'validated_candidate_sha256', '0' * 64),
                (self.report['metrics'], 'track_length_mm', 2.)):
            armed = [False]
            before = copy.deepcopy(target[key])
            def callback(binding):
                material(binding)
                if armed[0]:
                    armed[0] = False
                    target[key] = value
            try:
                # Install the same callback before identity capture; this tests
                # parsed custody rather than a replaced function's identity.
                with self.subTest(key=key), patch.object(e, 'bound_material', callback), p.validation_readback_session():
                    _, guard = self.guarded()
                    armed[0] = True
                    with self.assertRaises(p.Rejected):
                        guard()
            finally:
                target[key] = before

    def test_export_entry_identity_is_captured_before_initial_bind(self):
        output = self.workspace / 'entry-export'
        for name, value in (('bind', lambda *a, **kw: None),
                ('_export_validation_guard', lambda *a, **kw: None),
                ('KIND', 'changed-during-entry')):
            with self.subTest(name=name), ExitStack() as stack:
                def entry(*args, **kwargs):
                    stack.enter_context(patch.object(e, name, value))
                    return self.binding, self.report
                # Stop at the entry fence. No mocked Native outcome is used.
                with patch.object(e, 'bind', entry), patch.object(e, 'run') as worker:
                    with self.assertRaisesRegex(p.Rejected, 'policy changed during initial check'):
                        e.export(self.choice, output)
                    worker.assert_not_called()
                self.assertFalse(output.exists())

    def test_final_pure_fence_checks_seals_without_source_or_tool_reads(self):
        material, witness, tools = e.bound_material, e.witness, p.tool_manifest
        armed = [False]
        def material_read(*args, **kwargs):
            self.assertFalse(armed[0], 'pure fence reread material')
            return material(*args, **kwargs)
        def witness_read(*args, **kwargs):
            self.assertFalse(armed[0], 'pure fence reread source/evidence')
            return witness(*args, **kwargs)
        def tool_read(*args, **kwargs):
            self.assertFalse(armed[0], 'pure fence rediscovered tools')
            return tools(*args, **kwargs)
        with patch.object(e, 'bound_material', material_read), \
                patch.object(e, 'witness', witness_read), \
                patch.object(p, 'tool_manifest', tool_read), p.validation_readback_session():
            _, guard = self.guarded()
            armed[0] = True
            self.assertIsNone(guard(material=False))
            self.binding['validated_candidate_sha256'] = '0' * 64
            with self.assertRaisesRegex(p.Rejected, 'binding or routing record changed'):
                guard(material=False)


class Native7ExportFinalBoundaryControls(unittest.TestCase):
    """Actual export transaction with existing synthetic Native worker seams.

    Native7 recognition/final semantic checks and Context are explicit stubs.
    The complete export, full bind calls, final policy fingerprint, witnesses,
    publication and invalidation execute. These controls cannot qualify Native7.
    """
    setUp = export_fixture.ExportControls.setUp
    native_run = export_fixture.ExportControls.native_run
    export = export_fixture.ExportControls.export
    preserved = export_fixture.ExportControls.preserved
    no_positive = export_fixture.ExportControls.no_positive

    def native7_controls(self, stack, final=None):
        def context_guard(directory, report, identity):
            def check():
                if h._review_validation_identity() != identity:
                    raise p.Rejected('constructed Context live policy changed')
            check()
            return check
        def final_guard(*args, material=None, **kwargs):
            if material is not None:
                material()
        stack.enter_context(patch.object(s, 'native7_parent', lambda *a, **kw: {}))
        stack.enter_context(patch.object(s, 'native7_marked', lambda *a, **kw: True))
        stack.enter_context(patch.object(s, 'native7_default_target_basis', lambda *a, **kw: None))
        stack.enter_context(patch.object(s, 'check_native7_final', final or final_guard))
        stack.enter_context(patch.object(h, '_review_validation_guard', context_guard))

    def test_constructed_native7_export_keeps_entry_and_two_final_full_binds(self):
        original = e.bind
        calls = []
        def bound(*args, **kwargs):
            calls.append(args[0])
            return original(*args, **kwargs)
        with ExitStack() as stack:
            self.native7_controls(stack)
            stack.enter_context(patch.object(e, 'bind', bound))
            result = self.export()
        self.assertTrue(result['export_accepted'])
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(self.calls), 3)
        self.preserved()

    def test_final_tool_callback_cannot_replace_delivery_dispatcher(self):
        for target, name in ((h, 'delivery_guards'), (s, 'check_native7_final')):
            self.output = self.root / ('late-tools-' + name)
            armed, changed, replacement_called = [False], [False], [False]
            original_tools, original_check, original_bind = p.tool_manifest, e._check_export, e.bind
            calls = []
            with self.subTest(name=name), ExitStack() as stack:
                def replacement(*args, **kwargs):
                    replacement_called[0] = True
                def checked(*args, **kwargs):
                    result = original_check(*args, **kwargs)
                    armed[0] = True
                    return result
                def bound(*args, **kwargs):
                    calls.append(args[0])
                    return original_bind(*args, **kwargs)
                def tools(*args, **kwargs):
                    result = original_tools(*args, **kwargs)
                    if armed[0]:
                        armed[0] = False
                        changed[0] = True
                        stack.enter_context(patch.object(target, name, replacement))
                    return result
                self.native7_controls(stack)
                stack.enter_context(patch.object(e, 'bind', bound))
                stack.enter_context(patch.object(e, '_check_export', checked))
                stack.enter_context(patch.object(p, 'tool_manifest', tools))
                with self.assertRaisesRegex(p.Rejected, 'live policy changed'):
                    self.export()
                self.assertTrue(changed[0])
                self.assertFalse(replacement_called[0])
                self.assertEqual(len(calls), 3)
                self.no_positive()
                self.assertTrue(list(self.output.glob('invalidated-export-*')))
                self.preserved()

    def test_final_dispatcher_skipping_material_still_hits_pure_fence(self):
        armed, skipped = [False], [False]
        original_check, original_bind = e._check_export, e.bind
        calls = []
        with ExitStack() as stack:
            def final(*args, material=None, **kwargs):
                if armed[0]:
                    armed[0] = False
                    skipped[0] = True
                    stack.enter_context(patch.object(e, 'KIND', 'changed-by-final-dispatcher'))
                    return  # Deliberately omit the caller's material callback.
                if material is not None:
                    material()
            def checked(*args, **kwargs):
                result = original_check(*args, **kwargs)
                armed[0] = True
                return result
            def bound(*args, **kwargs):
                calls.append(args[0])
                return original_bind(*args, **kwargs)
            self.native7_controls(stack, final=final)
            stack.enter_context(patch.object(e, 'bind', bound))
            stack.enter_context(patch.object(e, '_check_export', checked))
            with self.assertRaisesRegex(p.Rejected, 'live policy changed'):
                self.export()
            self.assertTrue(skipped[0])
            self.assertEqual(len(calls), 3)
            self.no_positive()
            self.assertTrue(list(self.output.glob('invalidated-export-*')))
            self.preserved()


if __name__ == '__main__':
    unittest.main()
