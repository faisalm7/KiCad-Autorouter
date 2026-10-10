"""Independent source/mode controls. No native, engine, Git or network process."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,signal,sys,tempfile,unittest
from unittest import mock
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE/'snapshot'));sys.path.insert(1,str(ROOT));sys.dont_write_bytecode=True
import driver as d
import test_driver as fixture

class Independent(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='mode-',dir=HERE);self.out=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_security_functions_exact_ast_parity(self):
        def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        base=functions(ROOT/'experiments/lipo_native_diagnostic_v1/driver.py');now=functions(HERE/'snapshot/driver.py')
        for name in ('owned','inventory','source_binding','source_notes','snapshot','reserve_copy','drc_argv','drc_binding','publish','cpu'):
            with self.subTest(name=name):self.assertEqual(now[name],base[name])
        self.assertEqual((d.SECONDS,d.LIMIT,d.RESERVE),(30,20*1024*1024,1024*1024))
    def test_final_context_missing_dsn_is_intentional(self):
        row=fixture.flow_case(self.out,'unchanged','context-only')
        self.assertTrue(row['observations_complete']);self.assertEqual(len(row['steps']),2)
        args=row['steps'][0]['argv'];self.assertEqual(args[5],'final');self.assertEqual(len(args),8)
        self.assertEqual(args[:3],d.f.SANDBOX);self.assertFalse(row['dsn_export_requested']);self.assertFalse(row['dsn_export_succeeded']);self.assertIsNone(row['native_dsn_sha256'])
        summary=d.read(self.out/'unchanged/.runs/out/summary.json')
        for key in ('routing_accepted','format_support_qualified','dependency_complete','semantic_migration_performed','board_saved','new_engine_execution'):self.assertIs(summary[key],False)
    def test_whole_flow_export_default_still_requests_dsn(self):
        row=fixture.flow_case(self.out,'unchanged')
        self.assertTrue(row['observations_complete']);self.assertTrue(row['dsn_export_requested']);self.assertTrue(row['dsn_export_succeeded']);self.assertIsInstance(row['native_dsn_sha256'],str)
        self.assertEqual(row['steps'][0]['argv'][5],'export');self.assertEqual(len(row['steps'][0]['argv']),9)
    def test_json_mode_counterfactuals(self):
        hashes,total=d.source_binding();notes=d.source_notes(d.sx.read(d.SOURCE),d.read(d.SOURCE.with_suffix('.kicad_pro')))
        raw={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':'final','source':str(self.out/'observe-input'/d.SOURCE.name),'board_sha256':d.BOARD_SHA,'project_sha256':d.PROJECT_SHA,'dsn_sha256':None,'input_hashes_before':hashes,'input_hashes_after':hashes,'limits':d.f.LIMITS,'board_saved':False,'routing_accepted':False,'pads':notes['source_pads_identity'],'routes':[{'uuid':x} for x in notes['source_route_ids']],'nets':[{'name':x} for x in notes['source_nonempty_nets']]}
        for field,value in [('mode','export'),('dsn_sha256','0'*64),('board_saved',1),('routing_accepted',0),('project_sha256','0'*64)]:
            with self.subTest(field=field):
                altered=copy.deepcopy(raw);altered[field]=value;d.p.save_json(self.out/'observation.json',altered)
                with self.assertRaises(d.p.Rejected):d.observe_binding(self.out,hashes,notes,'context-only')
    def test_after_publication_mode_tamper_invalidated(self):
        record={'status':'observations_complete','observations_complete':True,'observation':'context-only','native_observation_mode':'final','routing_accepted':False,'dsn_export_requested':False,'dsn_export_succeeded':False,'native_dsn_sha256':None}
        def stable():
            path=self.out/'summary.json'
            if path.exists():
                raw=d.read(path);raw.update(observation='export',dsn_export_requested=True,dsn_export_succeeded=True);d.p.save_json(path,raw)
        result=d.publish(self.out,record,stable,lambda:None,lambda:1)
        self.assertFalse(result['observations_complete']);self.assertFalse(d.read(self.out/'summary.json')['dsn_export_succeeded'])
    def test_actual_self_signals_context_cli(self):
        for sig in (signal.SIGINT,signal.SIGTERM):
            with self.subTest(signal=sig):
                root=self.out/str(sig);(root/'.runs').mkdir(parents=True);out=root/'.runs/control';out.mkdir()
                before={x:signal.getsignal(x) for x in (signal.SIGINT,signal.SIGTERM)}
                def experiment(path,*,run_native,observation):
                    self.assertEqual(observation,'context-only')
                    record={'status':'observations_complete','observations_complete':True,'routing_accepted':False,'observation':observation}
                    def stable():
                        if (path/'summary.json').exists():os.kill(os.getpid(),sig)
                    return d.publish(path,record,stable,lambda:None,lambda:1)
                with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'experiment',side_effect=experiment),mock.patch('builtins.print'):
                    self.assertEqual(d.main(['--output',str(out),'--run-native','--observation','context-only']),2)
                self.assertEqual(d.read(out/'summary.json')['status'],'cancelled');self.assertFalse(d.read(out/'summary.json')['observations_complete'])
                self.assertEqual({x:signal.getsignal(x) for x in before},before)

if __name__=='__main__':unittest.main()
