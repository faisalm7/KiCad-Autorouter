"""Pure regression controls for demonstrated prototype defects; not Windows proof."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]/'scripts/windows_native_slice'

class WindowsProbeControls(unittest.TestCase):
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
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
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
