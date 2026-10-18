"""Explicit tool/version binding controls only; never native qualification."""
import ast,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from autorouter import pipeline as p,config as c,floor_route as f

class NativeToolchainControls(unittest.TestCase):
    def setUp(self):
        scratch=c.ROOT/'.cache';scratch.mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.paths={}
        for name in ('cli','python','pcbnew'):
            path=self.root/name;path.write_bytes(('authored '+name+'; never executed').encode());self.paths[name]=path
        self.args={**self.paths,'expected_version':'10.0.7',
                   **{name+'_sha256':hashlib.sha256(path.read_bytes()).hexdigest() for name,path in self.paths.items()}}
        self.toolchain=p.ExperimentalNativeToolchain(**self.args)
    def report(self,version):
        path=self.root/'drc.json'
        path.write_text(json.dumps({'$schema':'https://schemas.kicad.org/drc.v1.json','source':'fixture.kicad_pcb',
            'kicad_version':version,'included_severities':['error','warning','exclusion'],'ignored_checks':[],
            'violations':[],'unconnected_items':[],'schematic_parity':[]}));return path
    def test_default_report_remains_exact1000(self):
        self.assertEqual(p.parse_report(self.report('10.0.0'),'fixture.kicad_pcb')['opens'],0)
        with self.assertRaises(p.Rejected):p.parse_report(self.report('10.0.7'),'fixture.kicad_pcb')
    def test_explicit1007_report_keeps_real_version_and_rejects_wrong_version(self):
        path=self.report('10.0.7');before=path.read_bytes()
        self.assertEqual(p.parse_report(path,'fixture.kicad_pcb',native_toolchain=self.toolchain)['blocking'],0)
        self.assertEqual(path.read_bytes(),before)
        with self.assertRaises(p.Rejected):p.parse_report(self.report('10.0.0'),'fixture.kicad_pcb',native_toolchain=self.toolchain)
        with self.assertRaises(p.Rejected):p.parse_report(self.report('10.0.7'),'fixture.kicad_pcb',native_toolchain={'expected_version':'10.0.7'})
    def test_changed_tool_symlink_and_unknown_version_reject(self):
        with self.assertRaises(p.Rejected):p.ExperimentalNativeToolchain(**{**self.args,'expected_version':'10.0.8'})
        self.paths['cli'].write_bytes(b'changed')
        with self.assertRaisesRegex(p.Rejected,'tool changed'):p.parse_report(self.report('10.0.7'),'fixture.kicad_pcb',native_toolchain=self.toolchain)
        self.paths['cli'].unlink();self.paths['cli'].symlink_to(self.paths['python'])
        with self.assertRaises(p.Rejected):p.ExperimentalNativeToolchain(**self.args)
    def test_default_and_explicit_job_argv_do_not_mutate_config(self):
        original=(c.CLI,c.PYTHON,c.PCBNEW)
        default=p.Job(self.root/'default',30)
        explicit=p.Job(self.root/'explicit',30,native_toolchain=self.toolchain)
        for job,python,prefix in ((default,c.PYTHON,False),(explicit,self.paths['python'],True)):
            with patch.object(job,'step',return_value={}) as worker:
                job.native('roundtrip','roundtrip',self.root/'source',self.root/'candidate')
            argv=worker.call_args.args[1];self.assertEqual(argv[0],python)
            self.assertEqual('--experimental-native' in argv,prefix)
            if prefix:self.assertEqual(json.loads(argv[3]),self.toolchain.record())
        self.assertEqual((c.CLI,c.PYTHON,c.PCBNEW),original)
        self.assertEqual(explicit.native_cli,self.paths['cli']);self.assertEqual(default.native_cli,c.CLI)
    def test_step_tool_drift_rejects_after_actual_journal_before_approval(self):
        job=p.Job(self.root/'drift',30,native_toolchain=self.toolchain)
        def controlled(*args,**kwargs):
            self.paths['cli'].write_bytes(b'changed during owned synthetic process')
            return {'status':'success','exit_code':0}
        with patch.object(p,'run',side_effect=controlled),self.assertRaisesRegex(p.Rejected,'tool changed'):
            job.step('controlled',[str(self.paths['cli'])])
        self.assertTrue((job.out/'controlled-process.json').exists())
    def test_record_tamper_unknown_context_and_experimental_parity_refuse(self):
        record=self.toolchain.record();record['tools']['cli']['sha256']='0'*64
        with self.assertRaises(p.Rejected):p.ExperimentalNativeToolchain.from_record(record)
        output=self.root/'uncreated'
        with self.assertRaises(p.Rejected):p.Job(output,30,native_toolchain={})
        self.assertFalse(output.exists())
        job=f.FloorJob(self.root/'floor',30,lambda:30,native_toolchain=self.toolchain)
        with self.assertRaisesRegex(p.Rejected,'parity'):
            job.drc('blocked',self.root/'absent.kicad_pcb',schematic_parity=True)
        self.assertFalse((job.out/'blocked-input').exists())

    def worker(self, *, selected='10.0.0', actual='10.0.0', wrong=None, experimental=False, fixed=False):
        """Execute the real entry guard with fake modules, stopping at board load."""
        tree=ast.parse((c.ROOT/'autorouter/native.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        argv=['native.py','roundtrip','source','output']
        if experimental:argv=['native.py','--experimental-native',json.dumps(self.toolchain.record()),'export','source','output']
        if fixed:argv.append('--task-copper-fixed')
        paths=dict(self.paths)
        if wrong is not None:paths[wrong]=self.root/'different'
        api=SimpleNamespace(GetBuildVersion=lambda:actual,
            LoadBoard=lambda source:(_ for _ in ()).throw(RuntimeError('synthetic board-load boundary')))
        fake_sys=SimpleNamespace(argv=argv,executable=str(paths['python']))
        scope=dict(sys=fake_sys,Path=Path,json=json,pcbnew=api,c=c,
                   TASK_COPPER_FIXED_POLICY='native-task-copper-fixed-v1')
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'owned-native-entry','exec'),scope)
        with patch.object(c,'NATIVE_VERSION',selected),patch.object(c,'PYTHON',self.paths['python']),patch.object(c,'PCBNEW',self.paths['pcbnew']),patch.dict(sys.modules,{'_pcbnew':SimpleNamespace(__file__=str(paths['pcbnew']))}):
            scope['main']()

    def test_normal_worker_binds_selected_version_and_both_loaded_paths(self):
        for selected in ('10.0.0','10.0.7'):
            with self.subTest(selected=selected),self.assertRaisesRegex(RuntimeError,'synthetic board-load boundary'):
                self.worker(selected=selected,actual=selected)
            for mismatch in ('version','python','pcbnew'):
                with self.subTest(selected=selected,mismatch=mismatch),self.assertRaisesRegex(RuntimeError,'production native worker'):
                    self.worker(selected=selected,actual='unknown' if mismatch=='version' else selected,
                                wrong=None if mismatch=='version' else mismatch)

    def test_experimental_task_copper_flag_still_refuses_when_default_is1007(self):
        with self.assertRaisesRegex(RuntimeError,'unqualified Native task copper flag'):
            self.worker(selected='10.0.7',actual='10.0.7',experimental=True,fixed=True)

if __name__=='__main__':unittest.main()
