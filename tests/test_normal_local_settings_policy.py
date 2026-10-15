"""Authored receipt/AST controls only; no Native tools or routing proof.

These reuse the filesystem fixture, never reinterpret synthetic process data as
an executed Native check. Existing actual evidence and code declarations stay.
"""
import copy
import json
from pathlib import Path
import shutil
import stat
import unittest
from autorouter import pipeline as p, floor_route as f, local_settings as ls
from tests import test_result as fixture
from tests.normal_prl_fixture import mark_authored_receipt


class PolicyDeclarationControls(unittest.TestCase):
    def test_exact_literal_and_annotated_declaration(self):
        for declaration in (f"NORMAL_DRC_LOCAL_SETTINGS_POLICY={ls.JOB_POLICY!r}\n",
                            f"NORMAL_DRC_LOCAL_SETTINGS_POLICY: str={ls.JOB_POLICY!r}\n"):
            with self.subTest(declaration=declaration):
                self.assertEqual(ls.policy_declaration(declaration.encode()), ls.JOB_POLICY)

    def test_nested_duplicate_dynamic_and_assignment_expressions_refuse(self):
        assignment=f"NORMAL_DRC_LOCAL_SETTINGS_POLICY={ls.JOB_POLICY!r}\n"
        cases=('def nested():\n    '+assignment, 'if True:\n    '+assignment,
               assignment+assignment, 'NORMAL_DRC_LOCAL_SETTINGS_POLICY=choose()\n',
               "NORMAL_DRC_LOCAL_SETTINGS_POLICY += ''\n",
               assignment+"NORMAL_DRC_LOCAL_SETTINGS_POLICY += ''\n",
               f"(NORMAL_DRC_LOCAL_SETTINGS_POLICY := {ls.JOB_POLICY!r})\n",
               f"other = NORMAL_DRC_LOCAL_SETTINGS_POLICY = {ls.JOB_POLICY!r}\n",
               "NORMAL_DRC_LOCAL_SETTINGS_POLICY='unsupported'\n")
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(p.Rejected):
                ls.policy_declaration(raw.encode())

    def test_real_frozen_pre_policy_source_remains_legacy_data(self):
        # Project-owned historical source, no imported/changed captured code.
        old=fixture.ROOT/'evidence/default-tuning-native-001/code/pipeline.py'
        self.assertIsNone(ls.policy_declaration(old.read_bytes()))

    def test_bounded_malformed_and_nonbytes_source_refuses(self):
        for raw in (None, 'text', b'x'*(1024**2+1), b'def broken(:\n'):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(p.Rejected):
                ls.policy_declaration(raw)


class NormalPolicyReceiptControls(unittest.TestCase):
    # Reuse only fixture setup/save methods, not its inherited test population.
    setUp=fixture.ResultFreshnessTests.setUp
    save_receipt=fixture.ResultFreshnessTests.save_receipt

    def _stage(self, *, append=True):
        folder=self.run/'trials/authored-nested';folder.mkdir(parents=True)
        for name in ('candidate','final-drc-input'):
            shutil.copytree(self.run/name, folder/name)
        shutil.copy2(self.native, folder/self.native.name)
        def rebase(value):
            if isinstance(value,str):return value.replace(str(self.run),str(folder))
            if isinstance(value,list):return [rebase(x) for x in value]
            if isinstance(value,dict):return {k:rebase(v) for k,v in value.items()}
            return value
        binding=rebase(f.read_json(self.run/'final-drc-binding.json'))
        process=rebase(f.read_json(self.run/'final-drc-process.json'))
        step=rebase(copy.deepcopy(self.data['steps'][0]));step['phase']='authored-test-trial'
        p.save_json(folder/'final-drc-binding.json',binding)
        p.save_json(folder/'final-drc-process.json',process)
        if append:self.data['steps'].append(step)
        return folder,binding,process,step

    def _put_prl_in_fixture(self):
        raw=b'{"authored":"unchanged source PRL"}\n'
        for directory in (self.source_dir,self.run/'snapshot',self.candidate.parent,self.run/'final-drc-input',self.run/'refill'):
            (directory/self.source.with_suffix('.kicad_prl').name).write_bytes(raw)
        self.data['source_hashes']=p.tree_hash(self.source_dir)
        binding=f.read_json(self.run/'final-drc-binding.json')
        binding['before']=p.tree_hash(self.candidate.parent);binding['after']=p.tree_hash(self.run/'final-drc-input')
        p.save_json(self.run/'final-drc-binding.json',binding)
        binding=f.read_json(self.run/'refill-drc-binding.json')
        binding['before']=p.tree_hash(self.candidate.parent);binding['after']=p.tree_hash(self.run/'refill')
        p.save_json(self.run/'refill-drc-binding.json',binding)
        mark_authored_receipt(self.run,self.data,test_root=self.root)

    def _failed_stage(self):
        self._put_prl_in_fixture()
        folder=self.run/'trials/authored-timeout';folder.mkdir(parents=True)
        board=folder/'refill'/self.source.name;shutil.copytree(self.candidate.parent,board.parent)
        before=p.tree_hash(board.parent);name='refill-drc';message='refill-drc: timeout exit=-15';error='Rejected: '+message
        binding={'source':str(board),'input':str(board),'before':before,'after':dict(before),'saved':True,'local_settings_policy':ls.JOB_POLICY}
        event={'policy':ls.POLICY,'present':True,'path':str(board.with_suffix('.kicad_prl')),
               'sha256':before[board.with_suffix('.kicad_prl').name],'flags_before':0,
               'flags_during':stat.UF_IMMUTABLE,'flags_restored':True,'bytes_unchanged':True,
               'native_error':error,'guard_error':error}
        log=folder/(name+'.log');log.write_text('Authored timeout metadata only; Native never ran.\n')
        process={'name':name,'cwd':str(folder),'argv':[str(p.c.CLI),'pcb','drc','--format','json',
                 '--severity-all','--all-track-errors','--refill-zones','--exit-code-violations',
                 '--output',str(folder/(name+'.json')),'--save-board',str(board)],
                 'status':'timeout','exit_code':-15,'cleanup_complete':True,'log':str(log),
                 'log_bytes':log.stat().st_size,'log_truncated':False,'wall_seconds':1,
                 'cpu_seconds':1,'monitor_cpu_seconds':0,'local_settings_policy':ls.JOB_POLICY,
                 'local_settings_protection':event}
        p.save_json(folder/(name+'-binding.json'),binding);p.save_json(folder/(name+'-process.json'),process)
        artifacts={name+'.json':None,name+'.log':{'sha256':p.sha(log),'bytes':log.stat().st_size},
                   name+'-process.json':{'sha256':p.sha(folder/(name+'-process.json')),'bytes':(folder/(name+'-process.json')).stat().st_size}}
        failure={'schema':1,'passed':False,'phase':'native','error':{'type':'Rejected','message':message},
                 'binding':copy.deepcopy(binding),'validation_copy_before':dict(before),'artifacts':artifacts,'capture_errors':[]}
        failure_path=folder/(name+'-failure.json');p.save_json(failure_path,failure)
        self.data['steps'].append(dict(process,phase='authored-failed-trial'))
        return folder,binding,process,failure_path

    def test_current_source_and_tools_policy_must_agree(self):
        original=copy.deepcopy(self.data['tools'])
        for value in (None,'other',True):
            with self.subTest(value=value):
                self.data['tools']['normal_drc_local_settings_policy']=value
                with self.assertRaises(p.Rejected):ls.check_normal_policy(self.run,self.data)
                self.data['tools']=copy.deepcopy(original)
        self.data['tools']['implementation_sha256']['autorouter/pipeline.py']='0'*64
        with self.assertRaisesRegex(p.Rejected,'source pin'):ls.check_normal_policy(self.run,self.data)

    def test_source_without_declaration_cannot_keep_new_tools_policy(self):
        old=fixture.ROOT/'evidence/default-tuning-native-001/code/pipeline.py'
        shutil.copy2(old,self.run/'code/pipeline.py')
        self.data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(old)
        with self.assertRaisesRegex(p.Rejected,'declaration missing|alias export producer and tool policies differ'):ls.check_normal_policy(self.run,self.data)

    def test_all_optional_policy_and_helper_evidence_deletion_still_rejects(self):
        self.data['tools'].pop('normal_drc_local_settings_policy')
        self.data['tools']['implementation_sha256'].pop('autorouter/local_settings.py')
        (self.run/'code/local_settings.py').unlink()
        for filename in ('final-drc-binding.json','final-drc-process.json'):
            row=f.read_json(self.run/filename)
            for key in ('local_settings_policy','local_settings_protection'):row.pop(key,None)
            p.save_json(self.run/filename,row)
        for step in self.data['steps']:
            for key in ('local_settings_policy','local_settings_protection'):step.pop(key,None)
        self.save_receipt()
        with self.assertRaisesRegex(p.Rejected,'normal DRC'):p.check_result(self.receipt)

    def test_nested_worker_needs_its_own_markers(self):
        folder,_,_,step=self._stage();ls.check_normal_policy(self.run,self.data)
        for filename in ('final-drc-binding.json','final-drc-process.json'):
            row=f.read_json(folder/filename)
            for key in ('local_settings_policy','local_settings_protection'):row.pop(key,None)
            p.save_json(folder/filename,row)
        for key in ('local_settings_policy','local_settings_protection'):step.pop(key,None)
        with self.assertRaisesRegex(p.Rejected,'policy or lineage'):ls.check_normal_policy(self.run,self.data)

    def test_omitted_retained_worker_or_binding_only_cannot_escape_census(self):
        folder,_,_,_=self._stage(append=False)
        for retained in ('both','binding_only'):
            with self.subTest(retained=retained):
                if retained=='binding_only':(folder/'final-drc-process.json').unlink()
                with self.assertRaisesRegex(p.Rejected,'population'):ls.check_normal_policy(self.run,self.data)

    def test_duplicate_declared_worker_is_not_an_extra_measured_attempt(self):
        self.data['steps'].append(copy.deepcopy(self.data['steps'][0]))
        with self.assertRaisesRegex(p.Rejected,'duplicate'):ls.check_normal_policy(self.run,self.data)

    def test_complete_safely_failed_journal_retains_policy_consistency_only(self):
        folder,binding,process,_=self._failed_stage()
        ls.check_event(folder,binding,process,allow_worker_failure=True)
        ls.check_normal_policy(self.run,self.data)
        with self.assertRaises(p.Rejected):ls.check_event(folder,binding,process)

    def test_failed_journal_does_not_waive_errors_cleanup_or_input_witness(self):
        folder,binding,process,path=self._failed_stage();journal=f.read_json(path)
        cases=('guard_error','one_error','success','cleanup','before','after','artifact_pin','artifact_size','capture_error','saved_nonsaving_argv')
        for fault in cases:
            with self.subTest(fault=fault):
                worker=copy.deepcopy(process);changed=copy.deepcopy(journal);bound=copy.deepcopy(binding)
                if fault=='guard_error':worker['local_settings_protection']['guard_error']='different preservation failure'
                elif fault=='one_error':worker['local_settings_protection'].pop('native_error')
                elif fault=='success':worker.update(status='success',exit_code=0)
                elif fault=='cleanup':worker['cleanup_complete']=False
                elif fault=='before':changed['validation_copy_before']={}
                elif fault=='after':bound['after']={};changed['binding']=copy.deepcopy(bound)
                elif fault=='artifact_pin':changed['artifacts']['refill-drc.log']['sha256']='0'*64
                elif fault=='artifact_size':changed['artifacts']['refill-drc.log']['bytes']+=1
                elif fault=='capture_error':changed['capture_errors']=['missing artifact capture']
                else:
                    worker['argv'].remove('--save-board')
                    process_path=folder/'refill-drc-process.json';p.save_json(process_path,worker)
                    changed['artifacts'][process_path.name]={'sha256':p.sha(process_path),'bytes':process_path.stat().st_size}
                p.save_json(path,changed)
                with self.assertRaises(p.Rejected):ls.check_event(folder,bound,worker,allow_worker_failure=True)
        p.save_json(folder/'refill-drc-process.json',process)
        p.save_json(path,journal)

    def test_impossible_worker_status_exit_pairs_are_not_safe_failures(self):
        path=self.run/'final-drc-process.json';original=f.read_json(path)
        for status,code in (('success',-15),('success',5),('success',True),('nonzero_exit',0)):
            with self.subTest(status=status,code=code):
                process=copy.deepcopy(original);process.update(status=status,exit_code=code)
                p.save_json(path,process);self.data['steps'][0].update(status=status,exit_code=code)
                with self.assertRaises(p.Rejected):ls.check_normal_policy(self.run,self.data)
        p.save_json(path,original)
