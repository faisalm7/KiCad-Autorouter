"""Real owned-Context boundary guards; no Native/GUI/acceptance qualification.

The guard retains original owner/seal/live policy only. Complete byte custody
and the late fresh Context/Native/PRL guards remain its callers' obligations.
"""
import copy
import os
import shutil
import unittest
from unittest.mock import patch

from autorouter import _improve_context as child, handoff as h, pipeline as p
from autorouter import provenance as pv, review_view as view, strategy as s
from tests import test_native7_improve_parent as fixture


class Native7ReviewValidationGuardControls(unittest.TestCase):
    setUp = fixture.Native7ParentControls.setUp
    make = fixture.Native7ParentControls.make
    record = fixture.Native7ParentControls.record
    parent_data = fixture.Native7ParentControls.parent_data

    def guarded(self,data):
        context=s.native7_incumbent_context(self.parent,data)
        identity=h._review_validation_identity()
        return context,h._review_validation_guard(self.parent,data,identity)

    def test_captured_guard_requires_operation_and_returns_no_acceptance(self):
        data=self.parent_data()
        with self.assertRaises(p.Rejected):h._review_validation_identity()
        with p.validation_readback_session():
            context,guard=self.guarded(data)
            self.assertIs(type(context),child._Context)
            self.assertIsNone(guard())
            self.assertFalse(hasattr(context,'parent_job'))
        with self.assertRaises(p.Rejected):guard()

    def test_same_byte_parent_replacement_cannot_renew_saved_owner(self):
        data=self.parent_data();retained=self.workspace/'retained-review-parent'
        with p.validation_readback_session():
            _,guard=self.guarded(data)
            self.parent.rename(retained)
            try:
                shutil.copytree(retained,self.parent)
                with self.assertRaises(p.Rejected):guard()
            finally:
                shutil.rmtree(self.parent)
                retained.rename(self.parent)

    def test_entry_owner_is_not_recaptured_by_context_or_uid_changes(self):
        data=self.parent_data();entry,check=h._routing_entry_owner(self.parent)
        with p.validation_readback_session():
            identity=h._review_validation_identity()
            self.assertIsNone(h._review_validation_guard(self.parent,data,identity,entry_owner=entry)())
            wrong=copy.deepcopy(entry);wrong['directory_identity']=(entry['directory_identity'][0],entry['directory_identity'][1]+1)
            with self.assertRaises(p.Rejected):h._review_validation_guard(self.parent,data,identity,entry_owner=wrong)
        with patch.object(h.os,'getuid',return_value=os.getuid()+1),self.assertRaises(p.Rejected):check()

    def test_equal_valued_owner_type_mutations_are_not_invisible(self):
        data=self.parent_data()
        for mapping in ('parent_owner','_owner'):
            for field,value in (('created',1),
                    ('directory_identity',tuple(float(x) for x in self.owner['directory_identity']))):
                with self.subTest(mapping=mapping,field=field),p.validation_readback_session():
                    context,guard=self.guarded(data)
                    owner=getattr(context,mapping);before=copy.deepcopy(owner)
                    try:
                        owner[field]=value
                        with self.assertRaises(p.Rejected):guard()
                    finally:
                        owner.clear();owner.update(before)

    def test_context_record_or_captured_seal_change_refuses(self):
        data=self.parent_data()
        with p.validation_readback_session():
            context,guard=self.guarded(data)
            before=copy.deepcopy(context.allocation)
            try:
                context.allocation['elapsed_cpu_seconds']=3
                with self.assertRaises(p.Rejected):guard()
            finally:
                context.allocation.clear();context.allocation.update(before)
            seal=context._seal
            try:
                object.__setattr__(context,'_seal','changed')
                with self.assertRaises(p.Rejected):guard()
            finally:object.__setattr__(context,'_seal',seal)

    def test_class_provenance_and_review_function_replacements_are_bound(self):
        data=self.parent_data()
        original_check=child._Context.check
        def checked(context):return original_check(context)
        for target,name,value in ((child._Context,'check',checked),
                (child,'POLICY','changed-private-policy'),
                (pv,'_runtime_identity',lambda *a,**kw:None),
                (view,'render',lambda *a,**kw:None)):
            with self.subTest(name=name),p.validation_readback_session():
                _,guard=self.guarded(data)
                with patch.object(target,name,value),self.assertRaises(p.Rejected):guard()

    def test_guard_alone_does_not_replace_source_bytes_or_fresh_context(self):
        data=self.parent_data();path=self.source.with_suffix('.kicad_pro');raw=path.read_bytes()
        with p.validation_readback_session():
            context,guard=self.guarded(data)
            try:
                path.write_bytes(raw+b'\n')
                # This boundary-only function deliberately does not reread
                # source bytes; callers must retain their complete witnesses.
                self.assertIsNone(guard())
                with self.assertRaises(p.Rejected):child.require(context)
            finally:path.write_bytes(raw)


if __name__=='__main__':unittest.main()
