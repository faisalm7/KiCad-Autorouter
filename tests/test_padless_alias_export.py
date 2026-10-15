"""Fake Native export census controls; no actual Native or routing proof."""
import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from autorouter import padless_alias as a,pipeline as p,sexpr as sx
from tests.normal_prl_fixture import authored_zero_alias_dsn

ROOT=Path(__file__).resolve().parents[1]
UID='cc7020da-7305-4b42-b9ac-f444c9dd74c6'


class ExportCensus(unittest.TestCase):
    def setUp(self):
        (ROOT/'.cache').mkdir(exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.cache')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()

    def fixture(self,name='one'):
        root=self.root/name;root.mkdir();inputs=root/'input';inputs.mkdir();out=root/'job';out.mkdir()
        source=inputs/'owned.kicad_pcb'
        source.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (49 "F.Fab" user)) '
            '(footprint "Authored" (uuid "'+UID+'") (property "Reference" "J1" (layer "F.Fab")) '
            '(pad "1" smd rect (layers "F.Cu"))))\n')
        source.with_suffix('.kicad_pro').write_text('{}\n');raw=source.read_bytes();output=out/'task.dsn'
        class Footprint:
            def __init__(self,uid,ref):
                self.uid=uid;self.ref=ref;self.m_Uuid=SimpleNamespace(AsString=lambda:self.uid)
            def GetReference(self):return self.ref
        fp=Footprint(UID,'J1');pads=[SimpleNamespace(GetParentFootprint=lambda:fp)];fps=[fp]
        board=SimpleNamespace(GetFootprints=lambda:fps,GetPads=lambda:pads)
        before=(a.sha(raw),p.sha(source.with_suffix('.kicad_pro')))
        return source,raw,output,fp,pads,fps,board,before,Footprint

    def test_zero_alias_export_binds_actual_native_census_without_source_writes(self):
        source,raw,output,fp,pads,fps,board,before,_=self.fixture();calls=[];input_hashes=p.tree_hash(source.parent)
        dsn=authored_zero_alias_dsn(sx.parse(raw.decode()),output)
        def export(value,path):
            self.assertIs(value,board);self.assertEqual(path,str(output));calls.append(path);Path(path).write_bytes(dsn);return True
        record=a.export_board(board,source,output,SimpleNamespace(ExportSpecctraDSN=export,GetBuildVersion=lambda:'10.0.0'),mapping=None,before=before)
        self.assertEqual(calls,[str(output)]);self.assertTrue(record['zero_alias']);self.assertIsNone(record['observation'])
        self.assertEqual(record['native_footprints'],a.plan(raw)['footprints']);self.assertFalse(record['board_saved'])
        self.assertEqual(p.tree_hash(source.parent),input_hashes);self.assertEqual(output.read_bytes(),dsn)
        paths=a.artifact_paths(output);self.assertEqual(paths['source_copy'].read_bytes(),raw)
        self.assertEqual(json.loads(paths['proof'].read_text()),record)
        self.assertFalse(paths['before'].exists());self.assertFalse(paths['after'].exists())

    def test_wrong_native_uuid_reference_padcount_or_parent_refuses_before_export(self):
        for mode in ('uuid','reference','padcount','dangling_parent','duplicate_uuid'):
            with self.subTest(mode=mode):
                source,raw,output,fp,pads,fps,board,before,Footprint=self.fixture(mode);calls=[]
                if mode=='uuid':fp.uid='0a6145dd-055c-47c7-8f9f-ef09f732aa37'
                elif mode=='reference':fp.ref='J2'
                elif mode=='padcount':pads.clear()
                elif mode=='dangling_parent':
                    foreign=Footprint('0a6145dd-055c-47c7-8f9f-ef09f732aa37','J2')
                    pads.append(SimpleNamespace(GetParentFootprint=lambda:foreign))
                else:fps.append(Footprint(UID,'J1'))
                api=SimpleNamespace(ExportSpecctraDSN=lambda *args:calls.append(args),GetBuildVersion=lambda:'10.0.0')
                with self.assertRaisesRegex(ValueError,'census|bound pad parents'):a.export_board(board,source,output,api,mapping=None,before=before)
                self.assertEqual(calls,[]);self.assertFalse(output.exists());self.assertFalse(a.artifact_paths(output)['proof'].exists())
                self.assertEqual(source.read_bytes(),raw)

    def test_ordinary_exporter_census_mutation_cannot_emit_final_proof(self):
        source,raw,output,fp,pads,fps,board,before,_=self.fixture();dsn=authored_zero_alias_dsn(sx.parse(raw.decode()),output)
        def export(value,path):Path(path).write_bytes(dsn);fp.ref='CHANGED';return True
        with self.assertRaisesRegex(ValueError,'export changed Native footprint census'):
            a.export_board(board,source,output,SimpleNamespace(ExportSpecctraDSN=export,GetBuildVersion=lambda:'10.0.0'),mapping=None,before=before)
        self.assertTrue(output.is_file());self.assertFalse(a.artifact_paths(output)['proof'].exists());self.assertEqual(source.read_bytes(),raw)

    def test_reader_native_census_field_cannot_be_omitted_or_relabelled(self):
        # Reuse setup only, without inheriting/rerunning the policy test class.
        from tests import test_padless_alias_policy as fixtures
        case=fixtures.ExportPolicy(methodName='runTest');case.setUp();self.addCleanup(case.doCleanups)
        self.assertEqual(case.check()[0]['alias_count'],0);proof=case.paths['proof'].read_bytes()
        for mode in ('missing','empty','uuid','reference','padcount','boolean_padcount'):
            with self.subTest(mode=mode):
                record=json.loads(proof)
                if mode=='missing':del record['native_footprints']
                elif mode=='empty':record['native_footprints']=[]
                elif mode=='uuid':record['native_footprints'][0]['uuid']='0a6145dd-055c-47c7-8f9f-ef09f732aa37'
                elif mode=='reference':record['native_footprints'][0]['reference']='CHANGED'
                elif mode=='padcount':record['native_footprints'][0]['pad_count']+=1
                else:record['native_footprints'][0]['pad_count']=True
                try:
                    p.save_json(case.paths['proof'],record)
                    with self.assertRaises(p.Rejected):case.check()
                finally:case.paths['proof'].write_bytes(proof)


if __name__=='__main__':unittest.main()
