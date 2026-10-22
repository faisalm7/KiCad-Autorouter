"""Pure regression controls for demonstrated prototype defects; not Windows proof."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]/'scripts/windows_native_slice'

class WindowsProbeControls(unittest.TestCase):
    def test_persistent_cleanup_never_uses_counter_or_saved_receipt_as_authority(self):
        """Fault injection at the Python boundary; not real WFP qualification."""
        tree=ast.parse((ROOT/'appcontainer_launch.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AppContainerLaunch')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__exit__')
        def yes(value):
            if not value:raise OSError('injected Win32 failure')
        scope=dict(Path=Path,C=SimpleNamespace(c_void_p=lambda:SimpleNamespace(value=0)),_yes=yes)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'persistent-cleanup-boundary','exec'),scope)
        leave=scope['__exit__']
        for fault in ('caller_exception','counter','unsealed','contract','remove','no_live_authority','restore','verify','close','none'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                calls=[]
                class Guard:
                    cleanup_authorized=False
                    def poison(self,reason):calls.append('poison')
                    def seal_and_remove(self):
                        calls.append('remove')
                        if fault=='remove':raise OSError('ambiguous removal')
                        self.cleanup_authorized=fault!='no_live_authority'
                    def abandon(self):calls.append('abandon')
                    def receipt(self):return dict(cleanup_authorized=True,saved_job_count=0)
                def contract():
                    calls.append('contract')
                    if fault=='contract':raise OSError('changed sealed input')
                def delete(name):calls.append('delete_profile');return 0
                def set_acl(*args):
                    if fault=='restore':raise OSError('original ACL restoration failed')
                owner=SimpleNamespace(_persistent=Guard(),_outstanding=int(fault=='counter'),
                    _sealed=fault!='unsealed',_original_acls={str(Path(tmp)/'owned'):(b'ACL',True)},
                    _handles=[42] if fault=='close' else [],_created=True,
                    _profile_folder=Path(tmp)/'absent-owned-profile',profile_name='owned-profile',
                    _sid=SimpleNamespace(value=0),_entered=True,scope=Path(tmp),scratch=Path(tmp),
                    _tree=lambda path:[],check_contract=contract,u=SimpleNamespace(DeleteAppContainerProfile=delete),
                    cleanup_receipt={},evidence={},_set_acl=set_acl,
                    _acl=lambda path:(b'changed',True) if fault=='verify' else (b'ACL',True),
                    k=SimpleNamespace(CloseHandle=lambda handle:False))
                error=RuntimeError('caller failed') if fault=='caller_exception' else None
                if fault=='none':
                    self.assertFalse(leave(owner,None,None,None))
                    self.assertTrue(owner.cleanup_receipt['cleanup_complete'])
                    self.assertLess(calls.index('remove'),calls.index('delete_profile'))
                    self.assertLess(calls.index('delete_profile'),calls.index('abandon'))
                else:
                    with self.assertRaisesRegex(RuntimeError,'cleanup incomplete'):leave(owner,type(error) if error else None,error,None)
                    self.assertNotIn('delete_profile',calls)
                    self.assertFalse(owner.cleanup_receipt['cleanup_complete'])
                    self.assertEqual(owner.cleanup_receipt['persistent_removal_verified'],fault in ('restore','verify','close'))
                    self.assertIn('poison',calls)
                self.assertIn('abandon',calls)
                # This deliberately lying JSON is retained for diagnosis but
                # cannot turn failed live custody/removal into cleanup success.
                self.assertTrue(owner.evidence['persistent_guard']['cleanup_authorized'])

    def test_new_process_is_retained_before_a_failing_source_witness(self):
        calls=[]
        def require(ok,message):
            if not ok:raise RuntimeError(message)
        def fresh():calls.append('source_witness');raise RuntimeError('source changed')
        def register(*args):calls.append('capture_actual_process');return 0
        owner=SimpleNamespace(_thread_check=lambda:calls.append('thread'),_bad=False,_abandoned=False,
            _owner=SimpleNamespace(value=1),_lib=SimpleNamespace(PG_RegisterProcess=register),
            _info=lambda:calls.append('info') or dict(poisoned=0),_sid=None,_keys=None,_fresh=fresh,
            _remember_failure=lambda *args:calls.append('first_failure'),
            poison=lambda error:calls.append('poison'))
        invoke=self.process_function('_invoke',source='persistent_guard_state.py',_require=require)
        with self.assertRaisesRegex(RuntimeError,'source changed'):
            invoke(owner,'PG_RegisterProcess',0,object(),object(),created_registration=True)
        self.assertEqual(calls,['thread','capture_actual_process','info','source_witness','first_failure','poison'])
        calls.clear()
        with self.assertRaisesRegex(RuntimeError,'source changed'):
            invoke(owner,'PG_RegisterProcess',0,object(),object())
        self.assertEqual(calls,['source_witness','first_failure','poison'])

    def test_all_sixteen_decimal_tombstone_slots_are_valid_and_exhaustion_is_visible(self):
        import os,re
        def require(ok,message):
            if not ok:raise RuntimeError(message)
        census=self.process_function('_census',source='persistent_guard_state.py',os=os,re=re,Path=Path,_require=require)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            owner=SimpleNamespace(_root=root,MAX_ENTRIES=145,MAX_STATE_BYTES=2*1024**2,
                                  _wp=SimpleNamespace(safe=lambda path,base:path))
            for index in range(16):(root/('slot-%02d'%index)).write_bytes(b'reserved')
            census(owner)
            (root/'slot-16').write_bytes(b'unsupported')
            with self.assertRaisesRegex(RuntimeError,'known host reservation'):census(owner)

    def test_state_projection_preserves_partial_actual_bytes_without_reading_other_owners(self):
        import base64
        def require(ok,message):
            if not ok:raise RuntimeError(message)
        snapshot=self.process_function('material_snapshot',source='persistent_guard_state.py',
            base64=base64,hashlib=hashlib,_require=require)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);name='name-owned.jsonl';(root/name).write_bytes(b'complete\n')
            foreign=root/'name-other-owner.jsonl';foreign.write_bytes(b'never read')
            owner=SimpleNamespace(_thread_check=lambda:None,_root=root,_owned_names={name},
                _files={name:{'raw':b'complete\n'}},_wp=SimpleNamespace(safe=lambda path,base:path))
            complete=snapshot(owner);self.assertTrue(complete['complete'])
            self.assertEqual([row['name'] for row in complete['files']],[name])
            (root/name).write_bytes(b'complete\npartial')
            partial=snapshot(owner);self.assertFalse(partial['complete'])
            self.assertEqual(base64.b64decode(partial['files'][0]['base64']),b'complete\npartial')
            self.assertFalse(partial['files'][0]['matches_last_complete_write'])
            self.assertEqual(foreign.read_bytes(),b'never read')

    def process_function(self,name,source='windows_process.py',**scope):
        tree=ast.parse((ROOT/source).read_text())
        fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(ROOT/source),'exec'),scope)
        return scope[name]

    def test_setup_main_poll_uses_retained_handle_and_never_waits(self):
        calls=[];handle=object();process=SimpleNamespace(hProcess=handle,dwProcessId=51)
        code=lambda:SimpleNamespace(value=0)
        def wait(h,millis):
            self.assertIs(h,handle);self.assertEqual(millis,0);calls.append('wait');return 258
        def exit_code(*args):calls.append('exit');return True
        kernel=SimpleNamespace(WaitForSingleObject=wait,GetExitCodeProcess=exit_code)
        poll=self.process_function('_poll_setup_main',K=kernel,W=SimpleNamespace(DWORD=code),C=SimpleNamespace(byref=lambda x:x,get_last_error=lambda:6))
        self.assertEqual(poll(process),dict(pid=51,state='running',exit_code=None,wait_result=258))
        self.assertEqual(calls,['wait'])
        kernel.WaitForSingleObject=lambda h,millis:0
        observed=poll(process)
        self.assertEqual((observed['state'],observed['exit_code']),('exited',0))
        # A signaled process may legitimately have exited with STILL_ACTIVE's number.
        kernel.GetExitCodeProcess=lambda h,out:setattr(out,'value',259) or True
        self.assertEqual(poll(process)['exit_code'],259)

    def test_setup_main_poll_failure_is_explicit_unknown(self):
        process=SimpleNamespace(hProcess=object(),dwProcessId=51)
        kernel=SimpleNamespace(WaitForSingleObject=lambda *args:0xffffffff,GetExitCodeProcess=lambda *args:False)
        poll=self.process_function('_poll_setup_main',K=kernel,W=SimpleNamespace(DWORD=lambda:SimpleNamespace(value=0)),C=SimpleNamespace(byref=lambda x:x,get_last_error=lambda:6))
        observed=poll(process)
        self.assertEqual((observed['state'],observed['exit_code']),('unknown',None))
        self.assertEqual(observed['error'],dict(api='WaitForSingleObject',winerror=6))
        kernel.WaitForSingleObject=lambda *args:0
        self.assertEqual(poll(process)['error'],dict(api='GetExitCodeProcess',winerror=6))
        kernel.WaitForSingleObject=lambda *args:(_ for _ in ()).throw(OSError('mock API failure'))
        self.assertEqual(poll(process)['state'],'unknown')

    def setup_job_snapshot(self,*,query_ok=True,assigned=2,listed=2,pids=(51,52)):
        job=object();calls=[]
        def query(h,kind,out,size,unused):
            self.assertIs(h,job);self.assertEqual(kind,3);calls.append('owned-job-only')
            out.NumberOfAssignedProcesses=assigned;out.NumberOfProcessIdsInList=listed
            out.ProcessIdList=list(pids)+[0]*32
            return query_ok
        observe=self.process_function('_observe_setup_job',K=SimpleNamespace(QueryInformationJobObject=query),
                                      JOBPIDS=lambda:SimpleNamespace(),C=SimpleNamespace(byref=lambda x:x,sizeof=lambda x:0,get_last_error=lambda:234))
        result=observe(job,SimpleNamespace(ActiveProcesses=2,TotalProcesses=3),29.99,'before_termination',dict(state='exited',exit_code=0,pid=51))
        self.assertEqual(calls,['owned-job-only'])
        return result

    def test_setup_snapshot_only_lists_owned_job_pids_and_disclaims_identity(self):
        result=self.setup_job_snapshot()
        self.assertEqual(result['status'],'observed')
        self.assertEqual(result['members']['pids'],[51,52])
        self.assertIs(result['members']['image_identity_observed'],False)
        self.assertIs(result['snapshots_atomic'],False)
        self.assertEqual((result['accounting_active_processes'],result['accounting_total_processes']),(2,3))

    def test_setup_snapshot_failures_truncation_and_bad_pids_remain_unknown(self):
        for options in (dict(query_ok=False),dict(assigned=33),dict(listed=33),dict(assigned=3,listed=2),dict(assigned=1,listed=2),dict(pids=(51,51)),dict(pids=(51,0))):
            with self.subTest(options=options):
                result=self.setup_job_snapshot(**options)
                self.assertEqual(result['status'],'unknown')
                self.assertEqual(result['members']['pids'],[])

    def iterate_setup_job(self,*,main_state='exited',exit_code=0,snapshot_status='observed',elapsed=(1,31),owned_setup=True,active_sequence=None,main_states=None,compiler_role=None,cancel_after=None,cpu=0,log_bytes=0,scratch_bytes=0,terminate_ok=True):
        """Real polling block only; mocked API observations are not Windows proof."""
        tree=ast.parse((ROOT/'windows_process.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_run_job')
        loop=next(n for n in ast.walk(fn) if isinstance(n,ast.While));events=[];clock=iter(elapsed)
        active_values=iter(active_sequence) if active_sequence is not None else None
        main_values=iter(main_states) if main_states is not None else None
        account=SimpleNamespace(ActiveProcesses=2,TotalProcesses=3,TotalUserTime=int(cpu*10_000_000),TotalKernelTime=0)
        def query(*args):
            if active_values is not None:account.ActiveProcesses=next(active_values)
            return True
        def terminate(*args):events.append('terminate');account.ActiveProcesses=0;return terminate_ok
        def observe(job,sample,when,trigger,main):
            events.append(('snapshot',trigger,sample.ActiveProcesses,main['state'],main['exit_code']))
            return dict(status=snapshot_status,main=main,trigger=trigger,elapsed_seconds=when,members={'status':snapshot_status,'pids':[52]})
        def poll(process):
            events.append('main_poll')
            state,code=next(main_values) if main_values is not None else (main_state,exit_code)
            return dict(state=state,exit_code=code)
        with tempfile.TemporaryDirectory() as tmp:
            cwd=Path(tmp);log=cwd/'job.log'
            with log.open('wb') as stream:stream.truncate(log_bytes)
            with (cwd/'output').open('wb') as stream:stream.truncate(scratch_bytes)
            scope=dict(ACCOUNT=lambda:account,K=SimpleNamespace(QueryInformationJobObject=query,TerminateJobObject=terminate),
                       C=SimpleNamespace(byref=lambda x:x,sizeof=lambda x:0),job=1,process=object(),
                       yes=lambda value:self.assertTrue(value),time=SimpleNamespace(monotonic=lambda:next(clock,31),sleep=lambda value:None),
                       started=0,seconds=30,cancel_after=cancel_after,reason=None,log=log,cwd=cwd,root=cwd,safe=lambda path,root:path,
                       owned_setup=owned_setup,setup_termination_observed=False,setup_observations=[],last_main_state=None,setup_main_polls=0,
                       _poll_setup_main=poll,_observe_setup_job=observe,compiler_role=compiler_role,compiler_finalization=None)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),str(ROOT/'windows_process.py'),'exec'),scope)
            return scope,events

    def test_setup_main_zero_does_not_finish_or_drain_job_before_original_timeout(self):
        scope,events=self.iterate_setup_job()
        self.assertEqual(scope['reason'],'budget_exceeded')
        self.assertEqual(scope['setup_main_polls'],2)
        self.assertEqual(events[-2:],[('snapshot','before_termination',2,'exited',0),'terminate'])
        self.assertEqual(len(scope['setup_observations']),2)
        self.assertIs(scope['setup_observations'][-1]['before_termination'],True)

    def test_setup_main_nonzero_does_not_bypass_original_job_timeout(self):
        scope,events=self.iterate_setup_job(exit_code=2)
        self.assertEqual(scope['reason'],'budget_exceeded')
        self.assertEqual(events[-2:],[('snapshot','before_termination',2,'exited',2),'terminate'])

    def test_setup_unknown_main_or_query_never_passes(self):
        for options in (dict(main_state='unknown',exit_code=None),dict(snapshot_status='unknown')):
            with self.subTest(options=options):
                scope,events=self.iterate_setup_job(elapsed=(1,1),**options)
                self.assertEqual(scope['reason'],'process_diagnostic_unknown')
                self.assertEqual(events[-1],'terminate')
                self.assertIs(scope['setup_observations'][0]['before_termination'],True)

    def test_setup_diagnostics_preserve_prior_budget_failure_and_do_not_touch_ordinary_jobs(self):
        scope,events=self.iterate_setup_job(main_state='unknown',exit_code=None,elapsed=(31,31))
        self.assertEqual(scope['reason'],'budget_exceeded')
        scope,events=self.iterate_setup_job(owned_setup=False)
        self.assertEqual(scope['reason'],'budget_exceeded')
        self.assertEqual(events,['terminate'])
        self.assertEqual(scope['setup_observations'],[])

    def test_setup_natural_exit_records_bounded_transitions_without_termination(self):
        scope,events=self.iterate_setup_job(elapsed=(1,2,3),active_sequence=(2,1,0),
                                            main_states=(('running',None),('exited',0),('exited',0)))
        self.assertIsNone(scope['reason'])
        self.assertEqual([x['trigger'] for x in scope['setup_observations']],['initial','main_state_changed','job_inactive'])
        self.assertEqual(scope['setup_main_polls'],3)
        self.assertNotIn('terminate',events)
        self.assertTrue(all(not x['before_termination'] for x in scope['setup_observations']))

    def test_compiler_finalization_requires_exact_authoring_kind_and_integer_role(self):
        tree=ast.parse((ROOT/'windows_process.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_run_job')
        guard=next(n for n in fn.body if isinstance(n,ast.If) and isinstance(n.test,ast.Compare)
                   and isinstance(n.test.left,ast.Name) and n.test.left.id=='setup_authoring')
        code=compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),'compiler-contract','exec')
        for contract,expected in ((None,None),({'kind':'fixed-owned-DNS-helper'},None),
                                  ({'kind':'fixed-owned-C-guard-DLL-build'},'persistent-sid-guard'),
                                  ({'kind':'fixed-owned-C-canary-build','role':1},1),({'kind':'fixed-owned-C-canary-build','role':2},2)):
            scope=dict(setup_authoring=contract,owned_setup=True,appcontainer=None,compiler_role=None)
            exec(code,scope);self.assertEqual(scope['compiler_role'],expected)
        for contract in ({'kind':'other','role':1},{'kind':'fixed-owned-C-canary-build','role':True},
                         {'kind':'fixed-owned-C-canary-build','role':3},{'kind':'fixed-owned-C-canary-build'},True):
            with self.subTest(contract=contract),self.assertRaises(ValueError):
                exec(code,dict(setup_authoring=contract,owned_setup=True,appcontainer=None,compiler_role=None))
        with self.assertRaises(ValueError):
            exec(code,dict(setup_authoring={'kind':'fixed-owned-C-guard-DLL-build','role':1},owned_setup=True,appcontainer=None,compiler_role=None))
        with self.assertRaises(ValueError):
            exec(code,dict(setup_authoring={'kind':'fixed-owned-C-canary-build','role':1},owned_setup=False,appcontainer=None,compiler_role=None))
        with self.assertRaises(ValueError):
            exec(code,dict(setup_authoring={'kind':'fixed-owned-C-canary-build','role':1},owned_setup=True,appcontainer=object(),compiler_role=None))

    def test_compiler_main_zero_reaps_only_owned_job_and_records_non_natural_completion(self):
        scope,events=self.iterate_setup_job(compiler_role=1,elapsed=(6.265,6.266,6.267,6.3))
        self.assertIsNone(scope['reason'])
        self.assertEqual(events,['main_poll',('snapshot','initial',2,'exited',0),'terminate'])
        proof=scope['compiler_finalization']
        self.assertEqual(proof['kind'],'exact-owned-C-build-main-zero-then-job-reap-v1')
        self.assertTrue(proof['termination_requested']);self.assertTrue(proof['terminate_job_succeeded'])
        self.assertFalse(proof['remaining_members_natural_completion_claimed'])
        self.assertFalse(proof['zero_active_processes_verified'])  # Set only by the original post-loop verification.
        self.assertEqual(proof['member_snapshot']['pids'],[52])
        self.assertEqual(scope['setup_observations'][-1]['termination_reason'],'compiler_main_zero_owned_cleanup')

    def test_compiler_nonzero_unknown_and_failures_never_enable_finalization(self):
        cases=(dict(exit_code=2),dict(main_state='running',exit_code=None),dict(main_state='unknown',exit_code=None),
               dict(snapshot_status='unknown'),dict(elapsed=(31,31)),dict(cpu=31),dict(log_bytes=256*1024+1),
               dict(scratch_bytes=128*1024**2+1),dict(cancel_after=.5))
        for options in cases:
            with self.subTest(options=options):
                scope,events=self.iterate_setup_job(compiler_role=1,**options)
                self.assertIsNone(scope['compiler_finalization'])
                self.assertIsNotNone(scope['reason'])

    def test_compiler_concurrent_deadline_or_cancel_prevents_finalization(self):
        for options in (dict(elapsed=(29.9,30,30,30)),dict(elapsed=(1,1.5,2.1,2.1),cancel_after=2)):
            with self.subTest(options=options):
                scope,events=self.iterate_setup_job(compiler_role=2,**options)
                self.assertIsNone(scope['compiler_finalization'])
                self.assertIsNotNone(scope['reason'])
                self.assertEqual(events[-1],'terminate')
        with self.assertRaises(AssertionError):
            self.iterate_setup_job(compiler_role=1,elapsed=(1,1,1,1),terminate_ok=False)

    def compiled_output_reader(self):
        from contextlib import contextmanager
        @contextmanager
        def preserved(path,root):
            yield dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),file_id=[1,2,3])
        read=self.process_function('_read_compiler_pe_output',safe=lambda path,root:path,preserved=preserved)
        return self.process_function('_compiled_role_output',_read_compiler_pe_output=read)

    def test_guard_dll_output_cannot_be_an_executable_or_wrong_architecture(self):
        read=self.compiled_output_reader().__globals__['_read_compiler_pe_output']
        guard=self.process_function('_compiled_guard_output',_read_compiler_pe_output=read)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'persistent-sid-guard.dll';raw=self.minimal_pe()
            path.write_bytes(raw)
            with self.assertRaises(ValueError):guard(root)
            raw[86:88]=(0x2002).to_bytes(2,'little');path.write_bytes(raw)
            self.assertEqual(guard(root)['role'],'persistent-sid-guard')
            self.assertIn('DLL;',guard(root)['format'])
            raw[68:70]=b'\x4c\x01';path.write_bytes(raw)
            with self.assertRaises(ValueError):guard(root)

    def minimal_pe(self):
        raw=bytearray(256);raw[:2]=b'MZ';raw[60:64]=(64).to_bytes(4,'little')
        raw[64:70]=b'PE\0\0\x64\x86';raw[84:86]=(112).to_bytes(2,'little')
        raw[86:88]=(2).to_bytes(2,'little');raw[88:90]=b'\x0b\x02'
        return raw

    def test_compiler_role_output_requires_bounded_amd64_executable_header(self):
        read=self.compiled_output_reader()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'probe-parent.exe';raw=self.minimal_pe();path.write_bytes(raw)
            proof=read(root,1)
            self.assertEqual(proof['path'],str(path));self.assertEqual(proof['sha256'],hashlib.sha256(raw).hexdigest())
            self.assertTrue(proof['validated']);self.assertTrue(proof['validation_after_job_reaped'])
            for offset,value in ((0,b'XX'),(64,b'XX'),(68,b'\x4c\x01'),(84,b'\0\0'),(86,b'\x02\x20'),(88,b'\x0b\x01')):
                altered=raw.copy();altered[offset:offset+len(value)]=value;path.write_bytes(altered)
                with self.subTest(offset=offset),self.assertRaises(ValueError):read(root,1)
            path.write_bytes(raw[:80])
            with self.assertRaises(ValueError):read(root,1)
            with path.open('wb') as stream:stream.truncate(4*1024**2+1)
            with self.assertRaises(ValueError):read(root,1)
            with self.assertRaises(FileNotFoundError):read(root,2)
            with self.assertRaises(ValueError):read(root,True)

    def test_owned_setup_forwards_only_allowlisted_authoring_and_reads_output_after_reaping(self):
        from contextlib import contextmanager,ExitStack
        @contextmanager
        def owned_scope(root):yield root,{'owned':True}
        @contextmanager
        def preserved(path,parent):yield {'sha256':'pin'}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);exe=root/'compiler.exe';source=root/'probe.c';events=[]
            contract={'kind':'fixed-owned-C-canary-build','role':1}
            result=dict(status='success',cleanup_complete=True,_suspended_token=None)
            def run(argv,**kwargs):
                self.assertIs(kwargs['setup_authoring'],contract);events.append('job-returned-after-finally');return result.copy()
            def output(owned,role):
                self.assertEqual(events,['job-returned-after-finally']);events.append('read-output');return {'validated':True}
            scope=dict(Path=Path,math=__import__('math'),time=SimpleNamespace(monotonic=lambda:1),ExitStack=ExitStack,
                       _owned_setup_root=owned_scope,safe=lambda path,owned:path,_setup_argv=lambda argv,owned:(exe,[source],contract),
                       digest=lambda path:'pin',preserved=preserved,_run_job=run,_compiled_role_output=output)
            setup=self.process_function('run_owned_setup',**scope)
            returned=setup(['compiler.exe'],cwd=root,log=root/'compile.log',root=root)
            self.assertEqual(events,['job-returned-after-finally','read-output'])
            self.assertTrue(returned['compiler_output']['validated']);self.assertFalse(returned['Native_admitted'])
            for status,cleanup in (('budget_exceeded',True),('nonzero_exit',True),('process_diagnostic_unknown',True),('success',False)):
                events.clear();result.update(status=status,cleanup_complete=cleanup)
                returned=setup(['compiler.exe'],cwd=root,log=root/'compile.log',root=root)
                self.assertEqual(events,['job-returned-after-finally']);self.assertNotEqual(returned['status'],'success')
            events.clear();result.update(status='success',cleanup_complete=True)
            def invalid(*args):raise ValueError('invalid PE')
            setup.__globals__['_compiled_role_output']=invalid
            returned=setup(['compiler.exe'],cwd=root,log=root/'compile.log',root=root)
            self.assertEqual(returned['status'],'compiler_output_invalid');self.assertFalse(returned['compiler_output']['validated'])
            contract.clear();contract.update(kind='fixed-owned-DNS-helper');events.clear()
            returned=setup(['dns.exe'],cwd=root,log=root/'DNS.log',root=root)
            self.assertEqual(events,['job-returned-after-finally']);self.assertEqual(returned['status'],'success')

    def test_original_finally_cleanup_failure_overrides_pending_success(self):
        """Execute the retained cleanup block, including failure after zero active."""
        import copy
        tree=ast.parse((ROOT/'windows_process.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_run_job')
        cleanup=next(n for n in fn.body if isinstance(n,ast.Try)).finalbody
        wrapper=ast.parse('def exercise():\n try:\n  return "success"\n finally:\n  pass\n').body[0]
        wrapper.body[0].finalbody=copy.deepcopy(cleanup)
        def yes(value):
            if not value:raise OSError('mock handle cleanup failure')
        kernel=SimpleNamespace(TerminateJobObject=lambda *args:True,WaitForSingleObject=lambda *args:0,
                               QueryInformationJobObject=lambda *args:True,CloseHandle=lambda *args:True)
        scope=dict(K=kernel,yes=yes,created=True,assigned=True,job=object(),appcontainer=None,
                   process=SimpleNamespace(hProcess=object(),hThread=object()),ACCOUNT=lambda:SimpleNamespace(ActiveProcesses=0),
                   C=SimpleNamespace(byref=lambda x:x,sizeof=lambda x:0),time=SimpleNamespace(monotonic=lambda:1))
        exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),'retained-finally','exec'),scope)
        self.assertEqual(scope['exercise'](),'success')
        kernel.CloseHandle=lambda *args:False
        with self.assertRaisesRegex(RuntimeError,'Windows process cleanup incomplete'):scope['exercise']()

    def canary_function(self,name,**scope):
        tree=ast.parse((ROOT/'appcontainer_canary.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        scope.update(Path=Path,json=json)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(ROOT/'appcontainer_canary.py'),'exec'),scope)
        return scope[name]

    def test_setup_cleanup_exception_preserves_bounded_diagnostics_without_receipt(self):
        from contextlib import redirect_stdout
        import io
        def failed(*args,**kwargs):raise RuntimeError('owned cleanup unproved')
        execute=self.canary_function('execute',run_owned_setup=failed)
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'compile.log';log.write_bytes(b'x'*(256*1024+1));output=io.StringIO()
            with redirect_stdout(output),self.assertRaisesRegex(RuntimeError,'owned cleanup unproved'):
                execute(['owned.exe'],cwd=Path(tmp),log=log)
            receipt=json.loads(output.getvalue())
            self.assertIsNone(receipt['process'])
            self.assertIs(receipt['process_receipt_available'],False)
            self.assertIs(receipt['log_truncated'],True)
            self.assertEqual(receipt['log_utf8'],'x'*(256*1024))
            self.assertFalse(Path(str(log)+'.process.json').exists())

    def test_canary_unknown_network_error_cannot_be_denial(self):
        import copy
        check=self.canary_function('check_tokens');sid='S-1-15-2-owned-control'
        rows=[dict(kind='self_token',role=role,pid=role,is_appcontainer=1,capabilities=0,sid=sid) for role in (1,2)]
        rows.append(dict(kind='suspended_child_token',role=1,pid=2,is_appcontainer=1,capabilities=0,sid=sid))
        rows.extend(dict(kind='tcp',role=role,endpoint=endpoint,connected=False,wsa_error=10013,explicit_access_denied=True)
                    for role in (1,2) for endpoint in ('owned_loopback','public_ipv4'))
        rows.append(dict(kind='child_resumed',pid=2))
        check(rows,sid,cancelled=True)
        for key,value in (('connected',True),('wsa_error',10060),('explicit_access_denied',False)):
            altered=copy.deepcopy(rows);altered[3][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):check(altered,sid,cancelled=True)
        altered=copy.deepcopy(rows);altered[2]['sid']='wrong'
        with self.assertRaises(RuntimeError):check(altered,sid)
        with self.assertRaises(RuntimeError):check(rows[:-1],sid,cancelled=True)

    def setup_argv(self):
        """Exercise the real authoring allowlist without importing Windows APIs."""
        tree=ast.parse((ROOT/'windows_process.py').read_text())
        functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_setup_argv','_guard_setup_argv')]
        import os,re,sys
        scope=dict(Path=Path,os=os,re=re,sys=sys,__file__=str(ROOT/'windows_process.py'),
                   digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(),
                   safe=lambda path,root:path)
        exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(ROOT/'windows_process.py'),'exec'),scope)
        return scope['_setup_argv']

    def test_setup_dns_allows_only_fixed_isolated_helper(self):
        import sys
        gate=self.setup_argv()
        exe=str(Path(sys.executable).resolve());helper=str((ROOT/'appcontainer_dns.py').resolve())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertEqual(gate([exe,'-I','-B',helper],root)[2]['kind'],'fixed-owned-DNS-helper')
            for argv in ([exe,'-c','print(1)'],[exe,'-B',helper],
                         [exe,'-I','-B',helper,'extra'],[exe,'-I','-B',str(root/'other.py')]):
                with self.subTest(argv=argv),self.assertRaises(ValueError):gate(argv,root)

    def test_setup_compiler_refuses_arbitrary_source_flags_and_output(self):
        import os
        from unittest.mock import patch
        gate=self.setup_argv()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();program=root/'ProgramFiles';program86=root/'ProgramFilesX86';setup=root/'setup';setup.mkdir()
            vc=program/'Microsoft Visual Studio/2022/Enterprise/VC/Tools/MSVC/14.44.0'
            exe=vc/'bin/Hostx64/x64/cl.exe';exe.parent.mkdir(parents=True);exe.write_bytes(b'owned test path only')
            kit=program86/'Windows Kits/10';sdk=kit/'Include/10.0.26100.0'
            includes=[vc/'include',sdk/'ucrt',sdk/'shared',sdk/'um']
            libraries=[vc/'lib/x64',kit/'Lib'/sdk.name/'ucrt/x64',kit/'Lib'/sdk.name/'um/x64']
            for path in [*includes,*libraries]:path.mkdir(parents=True)
            argv=[str(exe),'/nologo','/W4','/WX','/O1','/MT','/DUNICODE','/D_UNICODE','/DPROBE_ROLE=1',
                  *['/I'+str(p) for p in includes],str((ROOT/'appcontainer_probe.c').resolve()),
                  '/Fo'+str(setup/'role1.obj'),'/Fe'+str(setup/'probe-parent.exe'),'/link','/INCREMENTAL:NO',
                  *['/LIBPATH:'+str(p) for p in libraries],'kernel32.lib','advapi32.lib','ws2_32.lib','fwpuclnt.lib','ole32.lib']
            with patch.dict(os.environ,{'ProgramFiles':str(program),'ProgramFiles(x86)':str(program86)}):
                self.assertEqual(gate(argv,setup)[2]['kind'],'fixed-owned-C-canary-build')
                for index,value in ((8,'/DPROBE_ROLE=3'),(13,str(root/'other.c')),(14,'/Fo'+str(root/'escape.obj')),
                                    (15,'/Fe'+str(root/'escape.exe')),(17,'@response.rsp'),
                                    (24,'other.lib'),(25,'@linker.rsp')):
                    altered=argv.copy();altered[index]=value
                    with self.subTest(index=index),self.assertRaises(ValueError):gate(altered,setup)
                with self.assertRaises(ValueError):gate(argv+['/extra'],setup)
                (setup/'probe-parent.exe').touch()
                with self.assertRaisesRegex(ValueError,'fresh owned compiler outputs'):gate(argv,setup)

    def test_guard_setup_allows_one_fixed_source_and_cannot_widen_the_compiler(self):
        import os
        from unittest.mock import patch
        gate=self.setup_argv()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();program=root/'ProgramFiles';program86=root/'ProgramFilesX86';setup=root/'setup';setup.mkdir()
            vc=program/'Microsoft Visual Studio/2022/Enterprise/VC/Tools/MSVC/14.44.0'
            exe=vc/'bin/Hostx64/x64/cl.exe';exe.parent.mkdir(parents=True);exe.write_bytes(b'owned test path only')
            kit=program86/'Windows Kits/10';sdk=kit/'Include/10.0.26100.0'
            includes=[vc/'include',sdk/'ucrt',sdk/'shared',sdk/'um']
            libraries=[vc/'lib/x64',kit/'Lib'/sdk.name/'ucrt/x64',kit/'Lib'/sdk.name/'um/x64']
            for path in [*includes,*libraries]:path.mkdir(parents=True)
            argv=[str(exe),'/nologo','/W4','/WX','/O1','/MT','/LD','/DUNICODE','/D_UNICODE',
                  *['/I'+str(p) for p in includes],str((ROOT/'persistent_sid_guard.c').resolve()),
                  '/Fo'+str(setup/'persistent-sid-guard.obj'),'/Fe'+str(setup/'persistent-sid-guard.dll'),'/link','/INCREMENTAL:NO',
                  '/IMPLIB:'+str(setup/'persistent-sid-guard.lib'),'/PDB:'+str(setup/'persistent-sid-guard.pdb'),
                  *['/LIBPATH:'+str(p) for p in libraries],'kernel32.lib','advapi32.lib','fwpuclnt.lib','ole32.lib']
            with patch.dict(os.environ,{'ProgramFiles':str(program),'ProgramFiles(x86)':str(program86)}):
                self.assertEqual(gate(argv,setup)[2]['kind'],'fixed-owned-C-guard-DLL-build')
                for index,value in ((6,'/LDd'),(13,str(ROOT/'appcontainer_probe.c')),(14,'/Fo'+str(root/'escape.obj')),
                                    (15,'/Fe'+str(root/'escape.dll')),(18,'/IMPLIB:'+str(root/'escape.lib')),
                                    (19,'@response.rsp'),(26,'ws2_32.lib')):
                    changed=argv.copy();changed[index]=value
                    with self.subTest(index=index),self.assertRaises(ValueError):gate(changed,setup)
                with self.assertRaises(ValueError):gate(argv+['/extra'],setup)
                (setup/'persistent-sid-guard.exp').touch()
                with self.assertRaisesRegex(ValueError,'fresh owned guard compiler outputs'):gate(argv,setup)

    def firewall_gate(self, output, result):
        tree=ast.parse((ROOT/'slice.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='firewall')
        refusal={}
        scope=dict(digest=lambda path:'pin',manifest=output/'manifest.json',manifest_pin='pin',
                   subprocess=SimpleNamespace(run=lambda *args,**kwargs:result),
                   powershell='pwsh.exe',gate=ROOT/'firewall_gate.ps1',OUT=output,
                   gate_failure=refusal,json=json)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(ROOT/'slice.py'),'exec'),scope)
        return scope['firewall'],refusal

    def test_refused_firewall_retains_complete_diagnostic_beyond_error_summary(self):
        raw=b'PowerShell preamble '*30+b'{"EnforcementStatus":"unknown"}\n'
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)
            gate,refusal=self.firewall_gate(output,SimpleNamespace(returncode=1,stdout=b'',stderr=raw))
            with self.assertRaisesRegex(RuntimeError,'retained firewall-refusal logs'):
                gate('owned-tool.exe','sha')
            self.assertEqual((output/'firewall-refusal.stderr.log').read_bytes(),raw)
            self.assertFalse(refusal['logs_truncated'])
            self.assertEqual(refusal['stderr_bytes'],len(raw))

    def test_oversize_firewall_diagnostic_refuses_and_marks_bounded_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)
            gate,refusal=self.firewall_gate(output,SimpleNamespace(returncode=0,stdout=b'{}',stderr=b'x'*16385))
            with self.assertRaises(RuntimeError):gate('owned-tool.exe','sha')
            self.assertTrue(refusal['logs_truncated'])
            self.assertEqual((output/'firewall-refusal.stderr.log').stat().st_size,16384)

    def test_successful_firewall_preserves_response_without_refusal_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)
            gate,refusal=self.firewall_gate(output,SimpleNamespace(returncode=0,stdout=b'{"verified": true}',stderr=b''))
            self.assertEqual(gate('owned-tool.exe','sha'),{'verified':True})
            self.assertEqual(refusal,{})
            self.assertEqual(list(output.iterdir()),[])

    def iterate_finished_job(self, *, log_bytes=0, scratch_bytes=0, elapsed=1, cpu=0, entries=0):
        """Execute the real polling block with an already-reaped job and real files."""
        tree=ast.parse((ROOT/'windows_process.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_run_job')
        loop=next(n for n in ast.walk(fn) if isinstance(n,ast.While))
        account=SimpleNamespace(ActiveProcesses=0,TotalUserTime=int(cpu*10_000_000),TotalKernelTime=0)
        with tempfile.TemporaryDirectory() as tmp:
            cwd=Path(tmp);log=cwd/'job.log'
            with log.open('wb') as stream:stream.truncate(log_bytes)
            with (cwd/'output').open('wb') as stream:stream.truncate(scratch_bytes)
            for index in range(entries):(cwd/str(index)).touch()
            scope=dict(ACCOUNT=lambda:account,K=SimpleNamespace(QueryInformationJobObject=lambda *args:True),C=SimpleNamespace(byref=lambda x:x,sizeof=lambda x:0),job=1,yes=lambda value:self.assertTrue(value),time=SimpleNamespace(monotonic=lambda:elapsed),started=0,seconds=30,cancel_after=None,reason=None,log=log,cwd=cwd,root=cwd,safe=lambda path,root:path,owned_setup=False,compiler_role=None)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),str(ROOT/'windows_process.py'),'exec'),scope)
            return scope['reason']

    def test_fast_exited_oversize_log_refuses(self):
        self.assertEqual(self.iterate_finished_job(log_bytes=256*1024+1),'log_limit')

    def test_fast_exited_oversize_output_refuses(self):
        self.assertEqual(self.iterate_finished_job(scratch_bytes=128*1024**2+1),'scratch_limit')

    def test_fast_exited_entry_flood_refuses(self):
        with self.assertRaisesRegex(RuntimeError,'scratch entry bound'):
            self.iterate_finished_job(entries=4001)

    def test_fast_exited_wall_and_cpu_budget_refuse(self):
        self.assertEqual(self.iterate_finished_job(elapsed=31),'budget_exceeded')
        self.assertEqual(self.iterate_finished_job(cpu=31),'budget_exceeded')

    def test_in_bound_finished_job_is_not_cancelled_after_exit(self):
        self.assertIsNone(self.iterate_finished_job())

    def test_cancelled_controller_is_terminal_exit130(self):
        tree=ast.parse((ROOT/'slice.py').read_text())
        handler=next(n for n in tree.body if isinstance(n,ast.Try)).handlers[0]
        result={'native_transport_observed':True}
        exec(compile(ast.fix_missing_locations(ast.Module(body=handler.body,type_ignores=[])),'slice-exception','exec'),{'result':result,'exc':KeyboardInterrupt()})
        self.assertIs(result['native_transport_observed'],False)
        self.assertIs(result['cancelled'],True)
        result['wall_seconds_before_publication']=1
        final=tree.body[-1]
        self.assertIsInstance(final,ast.Raise)
        code=compile(ast.Expression(body=final.exc.args[0]),'slice-exit','eval')
        self.assertEqual(eval(code,{'result':result}),130)

if __name__=='__main__':unittest.main()
