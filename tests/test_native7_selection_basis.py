"""Owned Context/freshness regressions for repeated trial admission.

Static/Native/tool seams are explicit in the shared fixture. These controls
exercise real inventories, original owners, basis seals and operation lifetime;
they establish no Native, routing-quality, timing or GUI qualification.
"""
import copy
from contextlib import ExitStack
import unittest
from unittest.mock import patch
from autorouter import _improve_context as child, floor_route as f, handoff as h
from autorouter import pipeline as p, strategy as s
from tests import test_native7_guard_reconstruction as faults
from tests import test_native7_improve_parent as default_fixture
from tests import test_native7_improve_parent_classes as class_fixture


class DefaultBasisOperation(unittest.TestCase):
    setUp=default_fixture.Native7ParentControls.setUp
    make=default_fixture.Native7ParentControls.make
    record=default_fixture.Native7ParentControls.record
    parent_data=default_fixture.Native7ParentControls.parent_data
    incumbent_with_basis=default_fixture.Native7ParentControls.incumbent_with_basis
    mutation=faults.Native7GuardReconstruction.mutation

    def prepare(self):
        data=self.parent_data();self.incumbent_with_basis(data);return data

    def test_original_basis_and_no_callback_lifetime_after_exit(self):
        data=self.prepare()
        with p.validation_readback_session():
            with s._single_selection_basis(self.parent,data) as basis:
                self.assertEqual(basis(),s._native7_default_basis_material(self.parent)[0])
            with self.assertRaisesRegex(p.Rejected,'operation ended'):basis()
        with p.validation_readback_session(),self.assertRaisesRegex(p.Rejected,'operation ended'):basis()

    def test_every_live_material_fault_refuses_without_rebasing(self):
        data=self.prepare()
        for kind in ('source','preferences','code','sidecar','rebound_sidecar','tools',
                     'owner','parent_replaced','source_hardlink','parent_shape'):
            with self.subTest(kind=kind),self.mutation(kind,data) as mutate:
                with self.assertRaises((p.Rejected,OSError)),p.validation_readback_session():
                    with s._single_selection_basis(self.parent,data) as basis:
                        basis();mutate()
        self.assertIsNone(p._readback_session.get())

    def test_returned_mutable_default_basis_cannot_change_the_seal(self):
        data=self.prepare()
        with self.assertRaises(p.Rejected),p.validation_readback_session():
            with s._single_selection_basis(self.parent,data) as basis:
                basis()['schema']=999

    def test_trial_evidence_and_extra_empty_directory_changes_refuse(self):
        data=self.prepare()
        for name in ('incumbent/default-targets.json','unexpected-empty'):
            path=self.parent/name;raw=path.read_bytes() if path.exists() else None
            try:
                with self.subTest(name=name),self.assertRaises(p.Rejected),p.validation_readback_session():
                    with s._single_selection_basis(self.parent,data):
                        if raw is None:path.mkdir()
                        else:path.write_bytes(raw+b'\n')
            finally:
                if raw is None:path.rmdir()
                else:path.write_bytes(raw)

    def test_policy_replacement_after_last_material_callback_refuses(self):
        data=self.prepare();original=h.evidence_witness
        with p.validation_readback_session():
            with ExitStack() as cleanup:
                calls=[]
                def witness(path):
                    value=original(path);calls.append(path)
                    if len(calls)==2:cleanup.enter_context(patch.object(s,'NATIVE7_PARENT_POLICY','changed'))
                    return value
                with patch.object(h,'evidence_witness',side_effect=witness),self.assertRaises(p.Rejected):
                    with s._single_selection_basis(self.parent,data) as basis:basis()
                self.assertEqual(len(calls),2)

    def test_source_mutation_after_last_owned_material_callback_refuses(self):
        data=self.prepare();original=h.evidence_witness
        path=self.source.with_suffix('.kicad_pro');raw=path.read_bytes();calls=[]
        def witness(folder):
            value=original(folder);calls.append(folder)
            if len(calls)==2:path.write_bytes(raw+b'\n')
            return value
        try:
            with p.validation_readback_session(),patch.object(h,'evidence_witness',side_effect=witness):
                with self.assertRaisesRegex(p.Rejected,'source changed after final callbacks'):
                    with s._single_selection_basis(self.parent,data) as basis:basis()
                self.assertEqual(len(calls),2)
        finally:path.write_bytes(raw)

    def test_error_or_cancel_expires_callback_and_clears_shared_state(self):
        data=self.prepare()
        for error in (ValueError('trial failure'),KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__),self.assertRaises(type(error)):
                with p.validation_readback_session():
                    state=p._readback_session.get()
                    with s._single_selection_basis(self.parent,data) as basis:
                        state['entries']['constructed']=object();raise error
            self.assertFalse(state['entries']);self.assertFalse(state['native7_contexts'])
            with self.assertRaises(p.Rejected):basis()


class ParentClassBasisOperation(unittest.TestCase):
    setUp=class_fixture.ParentClassImproveControls.setUp
    make=class_fixture.ParentClassImproveControls.make
    record=class_fixture.ParentClassImproveControls.record
    parent_data=class_fixture.ParentClassImproveControls.parent_data
    incumbent=class_fixture.ParentClassImproveControls.incumbent
    mutation=faults.Native7GuardReconstruction.mutation

    def prepare(self):
        data=self.parent_data();self.incumbent(data);return data

    def test_thirty_trial_consumers_keep_two_full_basis_boundaries(self):
        data=self.prepare();original=s._checked_native7_parent_class_basis
        with p.validation_readback_session(),patch.object(s,'_checked_native7_parent_class_basis',wraps=original) as check:
            with s._single_selection_basis(self.parent,data) as basis:
                self.assertEqual(check.call_count,1)
                for _ in range(30):self.assertIsNone(basis())
                self.assertEqual(check.call_count,1)
            self.assertEqual(check.call_count,2)
            self.assertIs(check.call_args.args[2],check.call_args_list[0].args[2])

    def test_original_class_policy_and_each_dsn_basis_file_stay_bound(self):
        data=self.prepare()
        for name in ('result.json','native.dsn','task.dsn','export-netclasses.json'):
            path=self.context.output/name;raw=path.read_bytes();binding=copy.deepcopy(data['netclass_parent_dsn_basis'])
            try:
                with self.subTest(name=name),self.assertRaises(p.Rejected),p.validation_readback_session():
                    with s._single_selection_basis(self.parent,data):
                        path.write_bytes(raw+b'\n')
                        data['netclass_parent_dsn_basis']=p.parent_dsn_basis(self.parent)
            finally:path.write_bytes(raw);data['netclass_parent_dsn_basis']=binding
        with self.assertRaises(p.Rejected),p.validation_readback_session():
            with s._single_selection_basis(self.parent,data):
                data['netclass_policy']['mode']='forged'

    def test_class_source_owner_code_and_sidecar_faults_refuse(self):
        data=self.prepare()
        for kind in ('source','code','sidecar','rebound_sidecar','tools','parent_replaced','source_hardlink'):
            with self.subTest(kind=kind),self.mutation(kind,data) as mutate:
                with self.assertRaises((p.Rejected,OSError)),p.validation_readback_session():
                    with s._single_selection_basis(self.parent,data):mutate()

    def test_public_selection_cannot_skip_its_fresh_outer_basis(self):
        data=self.prepare()
        def mutate(*args,**kwargs):
            self.source.with_suffix('.kicad_pro').write_bytes(self.source.with_suffix('.kicad_pro').read_bytes()+b'\n')
            return 'constructed selection, not acceptance'
        with patch.object(s,'_check_single_selection',side_effect=mutate),self.assertRaises(p.Rejected):
            s.check_single_selection(self.parent,data)


if __name__=='__main__':unittest.main()
