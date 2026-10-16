"""Pure regression controls for demonstrated prototype defects; not Windows proof."""
import ast
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]/'scripts/windows_native_slice'

class WindowsProbeControls(unittest.TestCase):
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
