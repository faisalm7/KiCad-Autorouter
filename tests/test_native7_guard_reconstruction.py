"""Constructed final-guard controls, never Native or parent acceptance proof.

The existing owned fixture supplies real Context, source/code inventories,
preferences and seals. Only final Native-map replay and worker/PRL primitives
are stubbed so callbacks can fault those live bindings at precise boundaries.
"""
import copy
from contextlib import contextmanager, ExitStack
import os
import shutil
import unittest
from unittest.mock import patch

from autorouter import _improve_context as child, floor_route as f
from autorouter import local_settings as local, pipeline as p, strategy as s
from tests import test_native7_improve_parent as fixture


class Native7GuardReconstruction(unittest.TestCase):
    setUp = fixture.Native7ParentControls.setUp
    make = fixture.Native7ParentControls.make
    record = fixture.Native7ParentControls.record
    parent_data = fixture.Native7ParentControls.parent_data
    incumbent_with_basis = fixture.Native7ParentControls.incumbent_with_basis

    def prepared(self):
        data = self.parent_data()
        self.incumbent_with_basis(data)
        folder = self.parent / 'trials' / 'trial-0000'
        folder.mkdir(parents=True)
        trial = dict(id=folder.name, status='quality_rejected', accepted=False, steps=[])
        p.save_json(folder / 'result.json', trial)
        data['trials'] = [dict(id=folder.name, receipt=str(folder / 'result.json'),
                               status=trial['status'], accepted=False)]
        return data

    @contextmanager
    def mutation(self, kind, data):
        """Fault only after initial reconstruction; always restore owned data."""
        paths = {
            'source': self.source.with_suffix('.kicad_pro'),
            'preferences': self.parent / 'pruning-preferences.json',
            'code': self.parent / 'code' / 'strategy.py',
            'sidecar': self.parent / s.NATIVE7_PARENT_FILE,
            'rebound_sidecar': self.parent / s.NATIVE7_PARENT_FILE,
        }
        target = paths.get(kind)
        raw = target.read_bytes() if target is not None else None
        marker = copy.deepcopy(data['native7_improve_parent'])
        tools = copy.deepcopy(self.tools)
        proposal_policy = data['proposal_policy']
        retained = self.workspace / 'retained-original-parent'
        link = self.base / 'retained-source-hardlink.kicad_pro'
        replaced = False
        with ExitStack() as stack:
            def mutate():
                nonlocal replaced
                if kind == 'rebound_sidecar':
                    contract = f.read_json(target)
                    contract['context']['assigned_seconds'] = 64
                    p.save_json(target, contract)
                    data['native7_improve_parent']['sha256'] = p.sha(target)
                elif target is not None:
                    target.write_bytes(raw + b'\n')
                elif kind == 'tools':
                    self.tools['files']['not-executed'] = '3' * 64
                elif kind == 'owner':
                    stack.enter_context(patch.object(child.os, 'getuid', return_value=os.getuid() + 1))
                elif kind == 'parent_replaced':
                    self.parent.rename(retained)
                    replaced = True
                    shutil.copytree(retained, self.parent)
                elif kind == 'source_hardlink':
                    os.link(self.source.with_suffix('.kicad_pro'), link)
                elif kind == 'parent_shape':
                    data['proposal_policy'] = 'feedback'
                else:
                    raise AssertionError('unknown constructed fault')
            try:
                yield mutate
            finally:
                if replaced:
                    shutil.rmtree(self.parent)
                    retained.rename(self.parent)
                if link.exists():
                    link.unlink()
                if target is not None:
                    target.write_bytes(raw)
                data['native7_improve_parent'] = marker
                data['proposal_policy'] = proposal_policy
                self.tools.clear()
                self.tools.update(tools)

    def assert_late_faults(self, phase):
        data = self.prepared()
        for kind in ('source', 'preferences', 'code', 'sidecar', 'rebound_sidecar',
                     'tools', 'owner', 'parent_replaced', 'source_hardlink', 'parent_shape'):
            fired = []
            with self.subTest(phase=phase, kind=kind), self.mutation(kind, data) as mutate:
                def final_class(*args, **kwargs):
                    if phase == 'final_class':
                        fired.append(kind)
                        mutate()
                def lineage(folder, *args):
                    if phase == 'lineage' and folder == self.context.output:
                        fired.append(kind)
                        mutate()
                with patch.object(p, 'check_final_netclass_evidence', side_effect=final_class), \
                        patch.object(p, 'check_experimental_local_settings', side_effect=lineage), \
                        patch.object(local, 'check_final_events') as metadata:
                    with self.assertRaises(p.Rejected):
                        # No caller material callback may be needed for these
                        # source/tool/owner/definition bindings to remain live.
                        s.check_native7_final(self.parent, data)
                    self.assertEqual(fired, [kind])
                    metadata.assert_not_called()

    def test_late_final_class_faults_refuse_without_material_callback(self):
        self.assert_late_faults('final_class')

    def test_late_incumbent_lineage_faults_refuse_without_material_callback(self):
        self.assert_late_faults('lineage')

    def test_checked_reconstruction_keeps_all_roots_and_last_metadata(self):
        data = self.prepared()
        extra = (self.workspace / 'export-validation', {'steps': []})
        pairs = [('owned plot root', 'owned binding', 'owned process')]
        events = []
        def lineage(folder, *args):
            self.assertNotEqual(folder, self.parent / 'trials' / 'trial-0000')
            events.append(('lineage', folder))
        def material():
            events.append(('material', None))
        def metadata(packets, cli, *, pairs):
            events.append(('metadata', None))
            self.assertEqual([folder for folder, _ in packets],
                             [self.parent, self.context.output,
                              self.parent / 'trials' / 'trial-0000', extra[0]])
            self.assertIs(packets[2][1]['accepted'], False)
            self.assertEqual(pairs, [('owned plot root', 'owned binding', 'owned process')])
        with patch.object(s, 'native7_parent', wraps=s.native7_parent) as admission, \
                patch.object(p, 'check_final_netclass_evidence') as audit, \
                patch.object(p, 'check_experimental_local_settings', side_effect=lineage), \
                patch.object(local, 'check_final_events', side_effect=metadata):
            self.assertTrue(s.check_native7_final(self.parent, data, additional=(extra,),
                                                pairs=pairs, material=material))
            admission.assert_called_once()
        self.assertTrue(audit.call_args.kwargs['default_target_policy'])
        self.assertEqual(audit.call_args.kwargs['default_target_basis']['policy'],
                         data['native7_default_target_basis']['policy'])
        self.assertEqual(events, [('lineage', self.parent), ('lineage', self.context.output),
                                  ('lineage', extra[0]), ('material', None), ('metadata', None)])

    def test_both_incumbent_and_parent_default_guide_bindings_are_required(self):
        data = self.prepared()
        receipt = self.context.output / 'result.json'
        original = receipt.read_bytes()
        binding = copy.deepcopy(data['native7_default_target_basis'])
        for kind in ('parent_to_guide', 'incumbent_to_guide'):
            with self.subTest(kind=kind):
                if kind == 'parent_to_guide':
                    data['native7_default_target_basis']['sha256'] = '0' * 64
                else:
                    incumbent = f.read_json(receipt)
                    incumbent['default_target_transport']['sha256'] = '0' * 64
                    p.save_json(receipt, incumbent)
                    # Keep the outer receipt hash coherent: the inner guide
                    # binding itself must still be rejected independently.
                    data['native7_default_target_basis']['receipt_sha256'] = p.sha(receipt)
                try:
                    with patch.object(p, 'check_final_netclass_evidence') as audit, \
                            patch.object(p, 'check_experimental_local_settings'), \
                            patch.object(local, 'check_final_events') as metadata:
                        with self.assertRaises(p.Rejected):
                            s.check_native7_final(self.parent, data)
                        audit.assert_not_called()
                        metadata.assert_not_called()
                finally:
                    receipt.write_bytes(original)
                    data['native7_default_target_basis'] = copy.deepcopy(binding)

    def test_trial_census_and_summary_cannot_be_omitted_or_extended(self):
        data = self.prepared()
        rows = copy.deepcopy(data['trials'])
        extra = self.parent / 'trials' / 'trial-0001'
        for kind in ('extra_folder', 'omitted_row', 'foreign_receipt', 'wrong_status', 'too_many_rows'):
            with self.subTest(kind=kind):
                if kind == 'extra_folder':
                    extra.mkdir()
                elif kind == 'omitted_row':
                    data['trials'] = []
                elif kind == 'foreign_receipt':
                    data['trials'][0]['receipt'] = str(self.workspace / 'foreign' / 'result.json')
                elif kind == 'wrong_status':
                    data['trials'][0]['status'] = 'improvement_validated'
                else:
                    data['trials'] = rows * (s.MAX_TRIALS + 1)
                try:
                    with patch.object(p, 'check_final_netclass_evidence'), \
                            patch.object(p, 'check_experimental_local_settings'), \
                            patch.object(local, 'check_final_events') as metadata:
                        with self.assertRaises(p.Rejected):
                            s.check_native7_final(self.parent, data)
                        metadata.assert_not_called()
                finally:
                    if extra.exists():
                        extra.rmdir()
                    data['trials'] = copy.deepcopy(rows)

    def test_public_collectors_still_require_parent_admission(self):
        data = self.prepared()
        for helper in (s.native7_packets, s.native7_default_target_basis):
            for field, value in (('proposal_policy', 'feedback'), ('single_selection_policy', 'other')):
                wrong = copy.deepcopy(data)
                wrong[field] = value
                with self.subTest(helper=helper.__name__, field=field), self.assertRaises(p.Rejected):
                    helper(self.parent, wrong)


if __name__ == '__main__':
    unittest.main()
