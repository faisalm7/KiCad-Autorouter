"""Pure retained PRL-event controls; fake metadata is not Native/OS proof."""
import ast
from collections import UserDict
from contextlib import contextmanager
import copy
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, floor_route as f, local_settings as ls
from tests import test_core_local_settings as core
from tests import test_normal_local_settings_policy as normal


class PreservedFieldEventControls(unittest.TestCase):
    def setUp(self):
        # Reuse the existing owned temporary project without its Mac-only tests.
        core.CoreLocalSettingsControls.setUp(self)
        self.flag=getattr(stat,'UF_IMMUTABLE',2)
        self.event={'policy':ls.POLICY,'present':True,'path':str(self.prl),
                    'sha256':self.original[self.prl.name],'flags_before':0,
                    'flags_during':self.flag,'flags_restored':True,'bytes_unchanged':True}

    @contextmanager
    def metadata(self,flags=0):
        """Expose controlled flags portably; no OS flags or workers are changed."""
        real_stat=Path.stat
        def observed(path,*args,**kwargs):
            info=real_stat(path,*args,**kwargs)
            if self.root in path.parents and path.suffix=='.kicad_prl':
                values={name:getattr(info,name) for name in dir(info) if name.startswith('st_')}
                values['st_flags']=flags
                return SimpleNamespace(**values)
            return info
        with patch.object(Path,'stat',observed),patch.object(ls.stat,'UF_IMMUTABLE',getattr(self,'flag',2),create=True):
            yield

    def test_current_preserved_file_has_exact_event_without_mutating_inputs(self):
        before,event=copy.deepcopy(self.original),copy.deepcopy(self.event)
        with self.metadata():
            ls.check_preserved(self.prl,before,event)
            ls.check_preserved(str(self.prl),before,event)
        self.assertEqual(before,self.original);self.assertEqual(event,self.event)

    def test_absent_original_and_created_prl_keep_existing_absence_contract(self):
        before={name:pin for name,pin in self.original.items() if name!=self.prl.name}
        absent={'policy':ls.POLICY,'present':False}
        self.prl.unlink()
        with self.metadata():ls.check_preserved(self.prl,before,absent)
        # Existing DRC semantics allow KiCad to create its PRL when none existed.
        self.prl.write_bytes(b'owned newly created local state')
        with self.metadata():ls.check_preserved(self.prl,before,absent)
        with self.metadata(flags=self.flag),self.assertRaises(p.Rejected):ls.check_preserved(self.prl,before,absent)

    def test_missing_preexisting_file_changed_bytes_and_retained_flags_reject(self):
        raw=self.prl.read_bytes()
        self.prl.unlink()
        with self.metadata(),self.assertRaises(p.Rejected):ls.check_preserved(self.prl,self.original,self.event)
        self.prl.write_bytes(raw+b' ')
        with self.metadata(),self.assertRaises(p.Rejected):ls.check_preserved(self.prl,self.original,self.event)
        self.prl.write_bytes(raw)
        with self.metadata(flags=self.flag),self.assertRaises(p.Rejected):ls.check_preserved(self.prl,self.original,self.event)

    def test_nonregular_and_hardlinked_current_files_reject(self):
        raw=self.prl.read_bytes();self.prl.unlink();self.prl.mkdir()
        with self.metadata(),self.assertRaises(p.Rejected):ls.check_preserved(self.prl,self.original,self.event)
        self.prl.rmdir();self.prl.write_bytes(raw)
        alias=self.root/'hardlink.kicad_prl';os.link(self.prl,alias)
        with self.metadata(),self.assertRaises(p.Rejected):ls.check_preserved(self.prl,self.original,self.event)

    def test_event_policy_keys_values_and_exact_types_cannot_be_weakened(self):
        class TextAlias(str):pass
        variants=[None,[],UserDict(self.event),{**self.event,'extra':True},
                  {key:value for key,value in self.event.items() if key!='sha256'}]
        for key,value in [('policy','other'),('present',False),('present',1),
                          ('path',str(self.root/'other.kicad_prl')),('path',self.prl),
                          ('sha256','0'*64),('sha256',TextAlias(self.event['sha256'])),
                          ('flags_before',False),('flags_during',True),
                          ('flags_restored',1),('flags_restored',False),
                          ('bytes_unchanged',1),('bytes_unchanged',False)]:
            variants.append({**self.event,key:value})
        with self.metadata():
            for event in variants:
                with self.subTest(event=event),self.assertRaises(p.Rejected):ls.check_preserved(self.prl,self.original,event)
            with self.assertRaises(p.Rejected):ls.check_preserved(self.prl,[],self.event)

    def test_noncanonical_wrong_suffix_and_alias_paths_reject(self):
        link=self.root/'alias.kicad_prl';link.symlink_to(self.prl)
        for path in (Path(self.prl.name),self.root/'source'/'..'/'source'/self.prl.name,link,self.source/'board.txt'):
            with self.subTest(path=path),self.metadata(),self.assertRaises(p.Rejected):ls.check_preserved(path,self.original,self.event)


class CapturedFieldPolicyControls(unittest.TestCase):
    setUp=normal.NormalPolicyReceiptControls.setUp
    save_receipt=normal.NormalPolicyReceiptControls.save_receipt
    _put_prl_in_fixture=normal.NormalPolicyReceiptControls._put_prl_in_fixture
    _failed_stage=normal.NormalPolicyReceiptControls._failed_stage
    metadata=PreservedFieldEventControls.metadata
    FIELD_POLICY='job-owned-field-prl-immutable-v1'

    def capture_policy(self,declared):
        path=self.run/'code/pipeline.py';raw=path.read_text();lines=raw.splitlines(keepends=True)
        # Modify only the authored source fixture; never production or a real run.
        nodes=[]
        for node in ast.parse(raw).body:
            targets=node.targets if isinstance(node,ast.Assign) else [node.target] if isinstance(node,ast.AnnAssign) else []
            if any(isinstance(target,ast.Name) and target.id=='FIELD_LOCAL_SETTINGS_POLICY' for target in targets):nodes.append(node)
        for node in reversed(nodes):del lines[node.lineno-1:node.end_lineno]
        raw=''.join(lines)
        if declared:raw+='\nFIELD_LOCAL_SETTINGS_POLICY='+repr(self.FIELD_POLICY)+'\n'
        path.write_text(raw);self.data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(path)

    def final_stage(self,parity,marker):
        path=self.run/'final-drc-process.json';process=f.read_json(path)
        process['argv']=[arg for arg in process['argv'] if arg!='--schematic-parity']
        if parity:process['argv'].insert(-1,'--schematic-parity')
        p.save_json(path,process)
        step=next(row for row in self.data['steps'] if row.get('name')=='final-drc' and row.get('cwd')==str(self.run));step.update(copy.deepcopy(process))
        path=self.run/'final-drc-binding.json';binding=f.read_json(path)
        binding.pop('field_local_settings_policy',None)
        if marker is not None:binding['field_local_settings_policy']=marker
        p.save_json(path,binding)

    def test_new_captured_parity_producer_requires_exact_field_policy_marker(self):
        self._put_prl_in_fixture();self.capture_policy(True)
        with self.metadata():
            for marker in (None,'other',True):
                self.final_stage(True,marker)
                with self.subTest(marker=marker),self.assertRaisesRegex(p.Rejected,'field local-settings policy'):ls.check_normal_policy(self.run,self.data)
            self.final_stage(True,self.FIELD_POLICY);ls.check_normal_policy(self.run,self.data)

    def test_legacy_source_and_nonparity_stage_preserve_prior_policy_behavior(self):
        self._put_prl_in_fixture()
        with self.metadata():
            self.capture_policy(False);self.final_stage(True,None);ls.check_normal_policy(self.run,self.data)
            self.capture_policy(True);self.final_stage(False,None);ls.check_normal_policy(self.run,self.data)

    def test_failed_drc_annotations_are_stripped_only_after_full_failure_replay(self):
        with self.metadata():
            directory,binding,process,_=self._failed_stage()
            with patch.object(ls,'check_preserved',wraps=ls.check_preserved) as check:
                ls.check_event(directory,binding,process,allow_worker_failure=True)
            checked=check.call_args.args
            self.assertEqual(checked[0],Path(binding['input']).with_suffix('.kicad_prl'))
            self.assertEqual(checked[1],binding['before']);self.assertNotIn('native_error',checked[2]);self.assertNotIn('guard_error',checked[2])
            self.assertIn('native_error',process['local_settings_protection'])
            with self.assertRaises(p.Rejected):ls.check_event(directory,binding,process)
            with self.assertRaises(p.Rejected):ls.check_preserved(checked[0],checked[1],process['local_settings_protection'])


if __name__=='__main__':unittest.main()
