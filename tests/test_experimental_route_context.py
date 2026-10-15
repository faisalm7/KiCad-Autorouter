"""Portable explicit-context/downgrade controls, never Native routing proof."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,config as c

class ExperimentalRouteContext(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();args={'expected_version':'10.0.7'}
        for name in ('cli','python','pcbnew'):
            file=self.root/name;file.write_text('authored never-executed '+name)
            args[name]=file;args[name+'_sha256']=p.sha(file)
        self.nt=p.ExperimentalNativeToolchain(**args)
        self.row={'schema':1,'scope':'whole_board_unlocked_routing','adapter':'none','baseline':'B0',
                  'engine_profile':'standard','scoring_variant':None,'source':'/owned/board.kicad_pcb',
                  'source_hashes':{'board.kicad_sch':'bound'},'schematic_parity':'checked by final native DRC',
                  **p.experimental_route_record(self.nt,True)}
    def test_explicit_contract_requires_caller_and_exact_markers(self):
        p.check_experimental_route(self.row,self.nt,True)
        for name in p.experimental_route_record(self.nt,True):
            row=copy.deepcopy(self.row);row.pop(name)
            with self.subTest(name=name),self.assertRaises(p.Rejected):p.check_experimental_route(row,self.nt,True)
        row=copy.deepcopy(self.row);row['production_admitted']=0
        with self.assertRaises(p.Rejected):p.check_experimental_route(row,self.nt,True)
    def test_nested_context_bool_cannot_equal_integer_schema(self):
        row=copy.deepcopy(self.row);row['experimental_native_toolchain']['schema']=True
        with self.assertRaises(p.Rejected):p.check_experimental_route(row,self.nt,True)
        row=copy.deepcopy(self.row);row['schema']=True
        with self.assertRaises(p.Rejected):p.check_experimental_route(row,self.nt,True)
    def test_default_refuses_each_marker_including_false_or_empty(self):
        for name,value in p.experimental_route_record(self.nt,True).items():
            with self.subTest(name=name),self.assertRaises(p.Rejected):p.check_experimental_route({name:value})
        with self.assertRaises(p.Rejected):p.check_experimental_route({'tools':{'experimental_native_toolchain':{}}})
        p.check_experimental_route({'tools':{'kicad':'10.0.0'}})
    def test_unsupported_modes_and_schematic_optout_refuse(self):
        for name,value in [('adapter','both'),('engine_profile','tuned'),('scope','selected_nets'),
                           ('strategy','arbitrary'),('input_policy','board-floors-v1'),('baseline','B1'),
                           ('schema',3),('scoring_variant','via_low'),('routing_preferences',{}),
                           ('source_hashes',{}),('schematic_parity','not checked')]:
            row=copy.deepcopy(self.row);row[name]=value
            with self.subTest(name=name),self.assertRaises(p.Rejected):p.check_experimental_route(row,self.nt,True)
    def test_optin_is_typed_and_tools_stay_pinned(self):
        for nt,enabled in [(self.nt,False),(None,True),(self.nt,1),({},True)]:
            with self.subTest(nt=type(nt),enabled=enabled),self.assertRaises(p.Rejected):p.experimental_route_record(nt,enabled)
        self.nt.cli.write_bytes(b'drift')
        with self.assertRaises(p.Rejected):p.native_prefix(self.nt)
    def test_exact_worker_prefix_default_and_explicit(self):
        self.assertEqual(p.native_prefix(),[str(c.PYTHON),str(c.ROOT/'autorouter/native.py')])
        self.assertEqual(p.native_prefix(self.nt),[str(self.nt.python),str(c.ROOT/'autorouter/native.py'),
                        '--experimental-native',json.dumps(self.nt.record(),sort_keys=True)])
    def test_unsupported_requests_refuse_before_output_or_dispatch(self):
        for kw in ({'adapter':'both'},{'keep_existing':True},{'guidance_policy':'board-floors-v1'},
                   {'engine_profile':'tuned'},{'settings_path':self.root/'missing.json'},
                   {'preference_overrides':{}},{'scoring_variant':'via_high'}):
            out=self.root/'uncreated'
            with self.subTest(kw=kw),patch.object(p,'check_storage',side_effect=AssertionError('late dispatch')),self.assertRaisesRegex(p.Rejected,'unsupported'):
                p.route(self.root/'missing.kicad_pcb',out,native_toolchain=self.nt,experimental_schematic_parity=True,**kw)
            self.assertFalse(out.exists())
    def test_explicit_reader_bypasses_production_cache(self):
        with p.validation_readback_session(),patch.object(p,'_check_result_uncached',return_value={'controlled':True}) as reader:
            self.assertEqual(p.check_result('unused',native_toolchain=self.nt,experimental_schematic_parity=True),{'controlled':True})
        reader.assert_called_once_with('unused',native_toolchain=self.nt,experimental_schematic_parity=True)
    def test_shared_publisher_uses_explicit_reader_and_preserves_default(self):
        for explicit in (False,True):
            out=self.root/str(explicit);out.mkdir();row={'accepted':True,'status':'routing_accepted'}
            checker=unittest.mock.Mock()
            with patch.object(p,'check_result') as default:
                f.publish(out,row,lambda:None,lambda:None,lambda:30,result_checker=checker if explicit else None)
            (checker if explicit else default).assert_called_once_with(out/'result.json')
            (default if explicit else checker).assert_not_called()
            self.assertTrue(row['accepted'])
    def test_manifest_uses_explicit_native_and_original_engine_pins(self):
        source=self.root/'manifest';source.mkdir();(source/'autorouter').mkdir();(source/'autorouter/a.py').write_text('# authored')
        java=source/'java';jar=source/'engine.jar';java.write_text('authored Java');jar.write_text('authored JAR')
        pins={name:{'path':str(file),'sha256':p.sha(file)} for name,file in [('java',java),('freerouting',jar)]}
        pins['kicad_cli']={'path':str(source/'absent-old-cli'),'sha256':'0'*64}
        (source/'toolchain.lock.json').write_text(json.dumps({'tools':pins}))
        with patch.multiple(c,ROOT=source,JAVA=java,JAR=jar),patch.object(p.subprocess,'run',return_value=SimpleNamespace(stdout='a'*40)):
            actual=p.tool_manifest(native_toolchain=self.nt)
            self.assertEqual(actual['kicad'],'10.0.7');self.assertEqual(actual['experimental_native_toolchain'],self.nt.record())
            self.assertEqual(set(actual['files']),{str(x) for x in (java,jar,self.nt.cli,self.nt.python,self.nt.pcbnew)})
            java.write_text('changed')
            with self.assertRaises(p.Rejected):p.tool_manifest(native_toolchain=self.nt)

if __name__=='__main__':unittest.main()
