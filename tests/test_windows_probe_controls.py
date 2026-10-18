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
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_setup_argv')
        import os,re,sys
        scope=dict(Path=Path,os=os,re=re,sys=sys,__file__=str(ROOT/'windows_process.py'),
                   digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(),
                   safe=lambda path,root:path)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(ROOT/'windows_process.py'),'exec'),scope)
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
                  *['/LIBPATH:'+str(p) for p in libraries],'kernel32.lib','advapi32.lib','ws2_32.lib']
            with patch.dict(os.environ,{'ProgramFiles':str(program),'ProgramFiles(x86)':str(program86)}):
                self.assertEqual(gate(argv,setup)[2]['kind'],'fixed-owned-C-canary-build')
                for index,value in ((8,'/DPROBE_ROLE=3'),(13,str(root/'other.c')),(14,'/Fo'+str(root/'escape.obj')),
                                    (15,'/Fe'+str(root/'escape.exe')),(17,'@response.rsp')):
                    altered=argv.copy();altered[index]=value
                    with self.subTest(index=index),self.assertRaises(ValueError):gate(altered,setup)
                with self.assertRaises(ValueError):gate(argv+['/extra'],setup)
                (setup/'probe-parent.exe').touch()
                with self.assertRaisesRegex(ValueError,'fresh owned compiler outputs'):gate(argv,setup)

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
            scope=dict(ACCOUNT=lambda:account,K=SimpleNamespace(QueryInformationJobObject=lambda *args:True),C=SimpleNamespace(byref=lambda x:x,sizeof=lambda x:0),job=1,yes=lambda value:self.assertTrue(value),time=SimpleNamespace(monotonic=lambda:elapsed),started=0,seconds=30,cancel_after=None,reason=None,log=log,cwd=cwd,root=cwd,safe=lambda path,root:path)
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
