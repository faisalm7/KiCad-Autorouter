"""Edge-stage downgrade controls; native correctness needs the separate controls."""
from pathlib import Path
import copy,json,tempfile,unittest
from unittest.mock import patch
from autorouter import pipeline as p,native_edge as e,adapter as a,sexpr as sx


class EdgeRecord(unittest.TestCase):
    def setUp(self):
        # Reuse the transform test's original input contract; no board is routed.
        from tests.test_native_edge import BOARD,PROJECT,DSN
        cache=Path(__file__).resolve().parents[1]/'.cache/edge-record-tests';cache.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=cache);self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name);source=self.folder/'snapshot';source.mkdir()
        self.board=source/'board.kicad_pcb';self.board.write_bytes(BOARD)
        self.board.with_suffix('.kicad_pro').write_bytes(json.dumps(PROJECT).encode())
        self.raw=DSN.encode()
        adapted,self.adapter=a.adapt_bytes(self.raw,'both',[])
        corrected,record=e.correct(adapted,p.native_edge_context(self.board))
        (self.folder/'native.dsn').write_bytes(self.raw)
        (self.folder/'edge-adapter-input.dsn').write_bytes(adapted)
        (self.folder/'task.dsn').write_bytes(corrected)
        p.save_json(self.folder/'obstacles.json',[])
        p.save_json(self.folder/'native-edge-correction.json',record)
        self.data=dict(source=str(self.board),adapter='both',source_hashes=p.tree_hash(source),
            native_edge_correction=record,adapter_transformations=self.adapter,
            engine_budget={},tools={'implementation_sha256':{'autorouter/native_edge.py':'control'}})

    def test_exact_record_and_legacy_absence(self):
        self.assertTrue(p.check_native_edge_transport(self.folder,self.data)['applied'])
        self.assertIsNone(p.check_native_edge_transport(self.folder/'missing',{'adapter':'both','engine_budget':{},'tools':{'implementation_sha256':{}}}))

    def test_missing_or_lowered_marker_input_and_source_reject(self):
        for name in ('metadata','marker','prior','engine','project','adapter'):
            with self.subTest(name=name):
                data=copy.deepcopy(self.data);saved={x:x.read_bytes() for x in self.folder.rglob('*') if x.is_file()}
                if name=='metadata':del data['native_edge_correction']
                elif name=='marker':(self.folder/'native-edge-correction.json').unlink()
                elif name=='prior':(self.folder/'edge-adapter-input.dsn').write_bytes(b'changed')
                elif name=='engine':(self.folder/'task.dsn').write_bytes(self.raw)
                elif name=='project':self.board.with_suffix('.kicad_pro').write_bytes(b'{}')
                else:data['adapter_transformations']['output_sha256']='other'
                with self.assertRaises((p.Rejected,ValueError,FileNotFoundError)):p.check_native_edge_transport(self.folder,data)
                for path,raw in saved.items():path.write_bytes(raw)

    def test_complete_downgrade_and_stock_relabel_reject(self):
        self.data.pop('native_edge_correction')
        (self.folder/'native-edge-correction.json').unlink();(self.folder/'edge-adapter-input.dsn').unlink()
        with self.assertRaisesRegex(p.Rejected,'lost its edge'):p.check_native_edge_transport(self.folder,self.data)
        # Reproduced review defect: removing the budget field must not hide
        # the retained native export/direct engine lineage.
        self.data.pop('engine_budget')
        with self.assertRaisesRegex(p.Rejected,'lost its edge'):p.check_native_edge_transport(self.folder,self.data)
        (self.folder/'native.dsn').unlink()
        self.data['steps']=[{'name':'engine','cwd':str(self.folder)}]
        with self.assertRaisesRegex(p.Rejected,'lost its edge'):p.check_native_edge_transport(self.folder,self.data)
        self.data['native_edge_correction']={};self.data['adapter']='none'
        with self.assertRaisesRegex(p.Rejected,'lineage'):p.check_native_edge_transport(self.folder,self.data)

    def test_fractional_proof_cannot_relabel_the_actual_export_host(self):
        from tests.test_native_edge import NativeEdgeTests
        board,dsn,context=NativeEdgeTests().fractional()
        self.board.write_bytes(board)
        self.raw=dsn.replace('"10.0.0"','"10.0.7"').encode()
        adapted,adapter=a.adapt_bytes(self.raw,'both',[])
        corrected,record=e.correct(adapted,context)
        (self.folder/'native.dsn').write_bytes(self.raw)
        (self.folder/'edge-adapter-input.dsn').write_bytes(adapted)
        (self.folder/'task.dsn').write_bytes(corrected)
        self.data.update(source_hashes=p.tree_hash(self.board.parent),
            native_edge_correction=record,adapter_transformations=adapter)
        p.save_json(self.folder/'native-edge-correction.json',record)
        self.assertEqual(p.check_native_edge_transport(self.folder,self.data)['inward_boundary']['native_host_version'],'10.0.7')
        # Rehashing/coherently changing both metadata copies cannot alter the
        # host witnessed by the retained actual input bytes.
        record['inward_boundary']['native_host_version']='10.0.0'
        p.save_json(self.folder/'native-edge-correction.json',record)
        with self.assertRaises(p.Rejected):p.check_native_edge_transport(self.folder,self.data)


if __name__=='__main__':unittest.main()
