"""Real tiny filesystem closure controls; no Native or placement authority."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from autorouter import placement

REFUSALS = (ValueError, OSError, placement.p.Rejected)


class PlacementReadbackWitness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='placement-readback-',dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.runtime = self.root/'runtime'
        self.output = self.runtime/'.runs/qualification'
        self.task = self.root/'task'
        self.source = self.task/'original/source.kicad_pcb'
        self.route = self.task/'workflow/route'; self.route.mkdir(parents=True)
        self.draft = self.task/'reviewed-draft.json'
        self.context = self.task/'native-inspection'; self.context.mkdir()
        self.wrapper = self.root/'tools/pcbnew.py'; self.wrapper.parent.mkdir()
        self.wrapper.write_text('synthetic Native wrapper')
        self.native = self.wrapper.with_name('_pcbnew.so'); self.native.write_text('synthetic tool')
        for parent in (self.source.parent,self.output/'work/candidate',self.output/'work/snapshot',
                       self.context/'snapshot',self.context/'source-drc-input'):
            parent.mkdir(parents=True)
            for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_prl'):
                (parent/('source'+suffix)).write_text('synthetic '+suffix)
        for name in ('placement-context.json','source-drc.json','source-drc-process.json','helper.py'):
            (self.context/name).write_text('synthetic '+name)
        hashes = placement.pc.inventory(self.source.parent)
        tools = {'files':{str(self.native):self.sha(self.native)}}
        fields = 'schema policy source source_hashes static tools accepted status native_validation_performed budget_seconds cpu_budget_seconds native steps wall_seconds parent_cpu_seconds child_cpu_seconds control_child_cpu_seconds monitor_cpu_seconds total_cpu_seconds native_report_sha256 note placement_context'.split()
        self.native_record = dict.fromkeys(fields)
        self.native_record.update(source=str(self.source),source_hashes=hashes,tools=tools,
            static={'source':str(self.source)},steps=[{'argv':[str(self.native),str(self.context/'source-drc.json')]}])
        self.write(self.context/'inspection.json',self.native_record)
        reference = dict(receipt=str(self.context/'inspection.json'),
            receipt_sha256=self.sha(self.context/'inspection.json'),context_sha256=self.sha(self.context/'placement-context.json'))
        self.inspection = dict(schema=1,kind='autorouter.saved-placement-inspection.v1',
            source=str(self.source),source_hashes=hashes,observation={},components=[],
            native_validation_performed=False,execution_authorized=False,approval_granted=False,
            limitations=[],native_context=reference,annotation_context={})
        self.intent = dict(source=str(self.source),source_hashes=hashes,native_context=reference,
            settings={'schema':5,'region_initialization':'selected-target-region-initialization-v1'})
        self.write(self.draft,self.intent)
        self.binding = dict(schema=1,kind=placement.KIND,draft=str(self.draft),draft_sha256=self.sha(self.draft),
            intent=self.intent,inspection=self.inspection,runtime=str(self.runtime),
            runtime_manifest_sha256='0'*64,wrapper_sha256=self.sha(self.wrapper),code_sha256={},tools=tools)
        self.write(self.output/'binding.json',self.binding)
        self.write(self.output/'result.json',dict(schema=1,kind=placement.KIND,status='pending_candidate',
            placement_qualified=True,**{key:False for key in placement.AUTHORITY}))
        self.write(self.output/'work/result.json',{'synthetic_only':True})
        self.descriptor = placement._origin(self.output,dict(evidence_hashes=placement.h.evidence_witness(self.output)))
        self.write(self.route/placement.ORIGIN_FILE,self.descriptor)
        self.report = dict(schema=1,source=str(self.output/'work/candidate/source.kicad_pcb'),placement_origin=self.descriptor)

    def sha(self,path):return hashlib.sha256(path.read_bytes()).hexdigest()
    def write(self,path,value):path.write_text(json.dumps(value,sort_keys=True))

    def witness(self):
        with patch.object(placement.c,'ROOT',self.runtime),patch.object(placement.c,'PCBNEW',self.native):
            return placement.readback_origin_witness(self.route,self.report)

    def assert_changed_or_refused(self,before):
        try:after=self.witness()
        except REFUSALS:return
        self.assertNotEqual(before,after)

    def test_fresh_immutable_detached_material_witness_grants_no_authority(self):
        with patch.object(placement,'check',side_effect=AssertionError('full proof called')), \
                patch.object(placement,'proof',side_effect=AssertionError('proof called')), \
                patch.object(placement,'material',side_effect=AssertionError('material called')), \
                patch.object(placement.intent,'current',side_effect=AssertionError('source proof called')):
            first=self.witness();second=self.witness()
        self.assertEqual(first,second)
        def immutable(value):
            self.assertIn(type(value),(tuple,str,int))
            if type(value)is tuple:
                for child in value:immutable(child)
        immutable(first);hash(first)
        self.binding['intent']['settings']['region_initialization']='changed in caller memory'
        self.assertEqual(first,self.witness())

    def test_no_origin_is_none_but_partial_marker_or_descriptor_refuses(self):
        marker=self.route/placement.ORIGIN_FILE;marker.unlink()
        with patch.object(placement.c,'ROOT',self.runtime):
            self.assertIsNone(placement.readback_origin_witness(self.route,{}))
        with self.assertRaises(REFUSALS):self.witness()
        self.write(marker,self.descriptor)
        with patch.object(placement.c,'ROOT',self.runtime),self.assertRaises(ValueError):
            placement.readback_origin_witness(self.route,{'schema':1})
        self.write(marker,dict(self.descriptor,kind='different-origin'))
        with self.assertRaises(ValueError):self.witness()

    def test_every_external_role_and_qualification_dependency_is_fresh(self):
        paths=[self.source,self.source.with_suffix('.kicad_pro'),self.source.with_suffix('.kicad_sch'),
            self.source.with_suffix('.kicad_prl'),self.draft,self.wrapper,
            self.output/'result.json',self.output/'binding.json',self.output/'work/result.json',
            self.output/'work/candidate/source.kicad_pcb',self.context/'inspection.json',
            self.context/'placement-context.json',self.context/'source-drc.json',
            self.context/'source-drc-process.json',self.context/'helper.py',
            self.context/'snapshot/source.kicad_pcb',self.context/'source-drc-input/source.kicad_prl']
        for path in paths:
            before=self.witness()
            raw=path.read_bytes()
            with self.subTest(path=path.relative_to(self.root)):
                path.write_bytes(raw+b'\n');self.assert_changed_or_refused(before)
            path.write_bytes(raw)

    def test_extra_files_and_empty_directories_in_each_tree_change_witness(self):
        for root in (self.source.parent,self.output,self.context):
            before=self.witness();extra=root/'extra-proof';extra.write_text('extra')
            with self.subTest(root=root.name,kind='file'):self.assert_changed_or_refused(before)
            extra.unlink();extra.mkdir()
            with self.subTest(root=root.name,kind='empty directory'):self.assert_changed_or_refused(before)
            extra.rmdir()

    def test_draft_parent_is_not_scanned_as_a_circular_workflow_tree(self):
        before=self.witness()
        (self.task/'unrelated-live-log').write_text('not a draft dependency')
        (self.route/'new-current-result.json').write_text('current routing activity')
        self.assertEqual(before,self.witness())

    def test_byte_identical_directory_replacement_including_work_changes_identity(self):
        for index,path in enumerate((self.output,self.output/'work',self.source.parent,self.context)):
            before=self.witness();saved=self.root/('kept-original-'+str(index))
            path.rename(saved);shutil.copytree(saved,path)
            with self.subTest(path=path):self.assert_changed_or_refused(before)

    def test_byte_identical_draft_file_or_parent_replacement_changes_identity(self):
        before=self.witness();saved=self.root/'old-draft';self.draft.rename(saved)
        shutil.copy2(saved,self.draft);self.assert_changed_or_refused(before)
        before=self.witness();saved_parent=self.root/'kept-task';self.task.rename(saved_parent)
        shutil.copytree(saved_parent,self.task);self.assert_changed_or_refused(before)

    def test_prl_link_count_flags_and_file_type_are_witnessed_or_refused(self):
        for root in (self.source.parent,self.output/'work/snapshot',self.context/'snapshot'):
            prl=root/'source.kicad_prl';before=self.witness();link=self.root/'extra-prl-link'
            os.link(prl,link)
            with self.subTest(root=root,kind='hardlink'):self.assert_changed_or_refused(before)
            link.unlink()
            original=Path.lstat
            def flags(path,*args,**kwargs):
                info=original(path,*args,**kwargs)
                if path==prl:
                    values={key:getattr(info,key)for key in dir(info)if key.startswith('st_')}
                    values['st_flags']=getattr(info,'st_flags',0)^1
                    return SimpleNamespace(**values)
                return info
            with self.subTest(root=root,kind='flags'),patch.object(Path,'lstat',flags):
                self.assert_changed_or_refused(before)
            raw=prl.read_bytes();prl.unlink();prl.mkdir()
            with self.subTest(root=root,kind='directory'):self.assert_changed_or_refused(before)
            prl.rmdir();prl.write_bytes(raw)

    def test_symlinks_in_source_draft_context_marker_and_Q_refuse(self):
        paths=[self.source,self.draft,self.context/'source-drc.json',self.route/placement.ORIGIN_FILE,
               self.output/'work/result.json']
        for index,path in enumerate(paths):
            raw=path.read_bytes();saved=self.root/('symlink-target-'+str(index));saved.write_bytes(raw)
            path.unlink();path.symlink_to(saved)
            with self.subTest(path=path),self.assertRaises(REFUSALS):self.witness()
            path.unlink();path.write_bytes(raw)

    def test_missing_roles_and_oversized_exact_draft_refuse(self):
        for path in (self.draft,self.wrapper,self.context/'inspection.json',self.output/'result.json'):
            raw=path.read_bytes();path.unlink()
            with self.subTest(path=path),self.assertRaises(REFUSALS):self.witness()
            path.write_bytes(raw)
        self.draft.write_bytes(b'x'*(64*1024+1))
        with self.assertRaises(REFUSALS):self.witness()

    def test_foreign_qualification_wrong_runtime_and_unfamiliar_inspection_refuse(self):
        mutations=[lambda b:b.update(runtime=str(self.root)),lambda b:b.update(kind='other-binding'),
            lambda b:b['intent'].update(settings=[]),
            lambda b:b['inspection'].update(extra_native_evidence=str(self.root)),
            lambda b:b['inspection']['native_context'].update(extra='unfamiliar')]
        for mutation in mutations:
            changed=copy.deepcopy(self.binding);mutation(changed);self.write(self.output/'binding.json',changed)
            with self.subTest(binding=changed),self.assertRaises(REFUSALS):self.witness()
        self.write(self.output/'binding.json',self.binding)
        old=self.report['placement_origin'];foreign=dict(old,qualification=str(self.context))
        self.report['placement_origin']=foreign;self.write(self.route/placement.ORIGIN_FILE,foreign)
        with self.assertRaises(ValueError):self.witness()

    def test_native_proof_reference_cannot_escape_captured_inspection_or_source_trees(self):
        outside=self.root/'uncaptured-proof.json';outside.write_text('external proof')
        record=copy.deepcopy(self.native_record);record['steps'].append({'proof':str(outside)})
        self.write(self.context/'inspection.json',record)
        with self.assertRaisesRegex(ValueError,'external Native proof'):self.witness()
        record=copy.deepcopy(self.native_record);record['new_dependency']=str(outside)
        self.write(self.context/'inspection.json',record)
        with self.assertRaisesRegex(ValueError,'dependency graph'):self.witness()

    def test_semantic_slash_names_never_become_filesystem_dependencies(self):
        record=copy.deepcopy(self.native_record)
        record['static']['nets']=[{'name':'/GND','terminal_count':2}]
        record['native']={'findings':[{'description':'/semantic-note'}]}
        self.write(self.context/'inspection.json',record)
        semantic={'/GND','/semantic-note'};resolved=[];opened=[]
        original_path=placement.h.real_path;original_read=placement.pc.read_bytes
        def resolve(value,*args,**kwargs):
            self.assertNotIn(str(value),semantic);resolved.append(str(value))
            return original_path(value,*args,**kwargs)
        def read(value,*args,**kwargs):
            self.assertNotIn(str(value),semantic);opened.append(str(value))
            return original_read(value,*args,**kwargs)
        with patch.object(placement.h,'real_path',side_effect=resolve), \
                patch.object(placement.pc,'read_bytes',side_effect=read):
            self.assertIsNotNone(self.witness())
            outside=self.root/'uncaptured-process-proof.json';outside.write_text('external proof')
            record['steps'].append({'argv':[str(outside)]})
            self.write(self.context/'inspection.json',record)
            with self.assertRaisesRegex(ValueError,'external Native proof'):self.witness()
        self.assertFalse(semantic.intersection(resolved+opened))

    def test_noncanonical_source_reference_and_ancestor_tree_overlap_refuse(self):
        changed=copy.deepcopy(self.binding);changed['inspection']['source']=str(self.source.parent/'..'/'original'/self.source.name)
        self.write(self.output/'binding.json',changed)
        with self.assertRaises(REFUSALS):self.witness()
        changed=copy.deepcopy(self.binding);changed['inspection']['source']=str(self.task/'source.kicad_pcb')
        (self.task/'source.kicad_pcb').write_text('broad source')
        changed['intent']['source']=changed['inspection']['source']
        changed['inspection'].pop('native_context');changed['inspection'].pop('annotation_context')
        changed['intent'].pop('native_context');self.write(self.output/'binding.json',changed)
        with self.assertRaisesRegex(ValueError,'overlapping'):self.witness()

    def test_marker_or_binding_mutation_during_inventory_refuses(self):
        original=placement.h.evidence_witness
        for target in (self.route/placement.ORIGIN_FILE,self.output/'binding.json'):
            raw=target.read_bytes()
            def mutate(root):
                value=original(root);target.write_bytes(raw+b'\n');return value
            with self.subTest(target=target),patch.object(placement.h,'evidence_witness',side_effect=mutate), \
                    self.assertRaisesRegex(ValueError,'binding/marker changed'):
                self.witness()
            target.write_bytes(raw)

    def test_after_only_wrapper_callback_precedes_every_closure_sample(self):
        original=placement.pc.read_bytes
        for target in (self.source,self.output/'work/result.json',
                       self.context/'source-drc.json',self.draft):
            raw=target.read_bytes();reads=[0]
            def late(path,*args,**kwargs):
                value=original(path,*args,**kwargs)
                if Path(path)==self.wrapper:
                    reads[0]+=1
                    if reads[0]==2:target.write_bytes(raw+b'\n')
                return value
            with self.subTest(target=target),patch.object(placement.pc,'read_bytes',side_effect=late):
                before=self.witness()
                try:after=self.witness()
                except REFUSALS:pass
                else:self.assertNotEqual(before,after,'second witness reused bytes sampled before wrapper callback')
            self.assertEqual(reads[0],2)
            self.assertNotEqual(target.read_bytes(),raw)
            target.write_bytes(raw)

    def test_legacy_inspection_without_native_context_has_no_extra_closure(self):
        changed=copy.deepcopy(self.binding)
        changed['inspection'].pop('native_context');changed['inspection'].pop('annotation_context')
        changed['intent'].pop('native_context');self.write(self.draft,changed['intent'])
        changed['draft_sha256']=self.sha(self.draft);self.write(self.output/'binding.json',changed)
        witness=self.witness()
        self.assertEqual([role[0]for role in witness[3]],['qualification','source'])


if __name__=='__main__':unittest.main()
