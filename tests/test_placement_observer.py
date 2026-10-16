"""Mock native API semantics and static parity only, no native execution."""
import ast,copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from autorouter import floor_context as observer,floor_route as f,placement_clearance as pc
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'MASTER_PROMPT.md').is_file())
d=SimpleNamespace(observer=observer,f=f)
class ObserverExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.root=Path(self.tmp.name);self.input=self.root/'input';self.input.mkdir()
        self.board=self.input/'fixture.kicad_pcb';self.board.write_text('owned mock native source');self.board.with_suffix('.kicad_pro').write_text('{}')
        self.dsn=self.root/'native.dsn';self.output=self.root/'floor.json';self.areas=self.root/'areas.json'
        settings=SimpleNamespace(**{value:300000 for value in d.observer.FLOORS.values()})
        self.native=SimpleNamespace(GetCopperLayerCount=lambda:2,SynchronizeNetsAndNetClasses=lambda _:None,Zones=lambda:[],GetFootprints=lambda:[],GetPads=lambda:[],GetNetsByName=lambda:{},GetTracks=lambda:[],GetDrawings=lambda:[],GetDesignSettings=lambda:settings)
    def tearDown(self):self.tmp.cleanup()
    def test_empty_areas_do_not_request_unused_layer_constants(self):
        pcb=SimpleNamespace(PLACEMENT_SOURCE_T_SHEETNAME=0,PLACEMENT_SOURCE_T_COMPONENT_CLASS=1,PLACEMENT_SOURCE_T_GROUP_PLACEMENT=2,PLACEMENT_SOURCE_T_DESIGN_BLOCK=3)
        for layers in (None,('F.Cu','In1.Cu','In2.Cu','B.Cu')):
            with self.subTest(layers=layers):
                self.assertEqual(observer.observe_areas(self.native,pcb,copper_layers=layers),{'zones':[],'footprint_zone_count':0,'footprint_rulearea_count':0})
        with self.assertRaisesRegex(ValueError,'explicit canonical four-copper'):
            observer.observe_areas(self.native,pcb,copper_layers=('F.Cu','In2.Cu','In1.Cu','B.Cu'))
    def collect(self,export):
        pcb=SimpleNamespace(PLACEMENT_SOURCE_T_SHEETNAME=0,PLACEMENT_SOURCE_T_COMPONENT_CLASS=1,PLACEMENT_SOURCE_T_GROUP_PLACEMENT=2,PLACEMENT_SOURCE_T_DESIGN_BLOCK=3,GetBuildVersion=lambda:'10.0.0',LoadBoard=lambda _:self.native,ExportSpecctraDSN=export)
        with patch.dict(sys.modules,{'pcbnew':pcb}):d.observer.collect('export',str(self.board),str(self.output),str(self.dsn),str(self.areas))
    def test_actual_empty_export_refused_before_context_publication(self):
        def export(*_):self.dsn.write_bytes(b'');return True
        with self.assertRaisesRegex(ValueError,'bounded native DSN'):self.collect(export)
        self.assertFalse(self.output.exists());self.assertFalse(self.areas.exists())
    def test_actual_symlink_export_refused_before_context_publication(self):
        def export(*_):self.dsn.symlink_to(self.board);return True
        with self.assertRaisesRegex(ValueError,'bounded native DSN'):self.collect(export)
        self.assertFalse(self.output.exists());self.assertFalse(self.areas.exists())
    def test_oversize_export_stat_refused_without_large_allocation(self):
        import os
        original=Path.stat
        def stat(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if path==self.dsn:
                fields=list(value);fields[6]=20*1024*1024+1;return os.stat_result(fields)
            return value
        def export(*_):self.dsn.write_bytes(b'x');return True
        with patch.object(Path,'stat',stat),self.assertRaisesRegex(ValueError,'bounded native DSN'):self.collect(export)
        self.assertFalse(self.output.exists());self.assertEqual(self.dsn.read_bytes(),b'x')
    def test_one_loaded_board_and_export_feed_both_bound_contexts(self):
        calls=[]
        def export(native,*_):calls.append(native);self.dsn.write_bytes(b'owned mock DSN');return True
        self.collect(export);self.assertEqual(calls,[self.native])
        floor=d.f.read_json(self.output);areas=d.f.read_json(self.areas)
        for key in ('source','board_sha256','project_sha256','input_hashes_before','input_hashes_after','dsn_sha256'):
            self.assertEqual(floor[key],areas[key])


    def test_optional_absent_keeps_original_floor_collector_output(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('original_floor_context',ROOT/'evidence/board-floor-production-native-001/code/floor_context.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        pcb=SimpleNamespace(GetBuildVersion=lambda:'10.0.0',LoadBoard=lambda _:self.native,ExportSpecctraDSN=lambda native,path:(Path(path).write_bytes(b'owned mock DSN') or True))
        with patch.dict(sys.modules,{'pcbnew':pcb}),patch.object(observer,'observe_areas',side_effect=AssertionError('unexpected opt-in collection')):
            observer.collect('export',str(self.board),str(self.output),str(self.dsn))
            second=self.root/'old.json';old.collect('export',str(self.board),str(second),str(self.root/'old.dsn'))
        self.assertEqual(json.loads(self.output.read_text()),json.loads(second.read_text()))
    def test_opt_in_outputs_must_be_distinct(self):
        with self.assertRaisesRegex(ValueError,'distinct'):
            observer.collect('export',str(self.board),str(self.output),str(self.dsn),str(self.output))

class ParityAndBounds(unittest.TestCase):
 def test_getter_collector_exact_reviewed_ast(self):
  current=ast.parse(Path(observer.__file__).read_text());prior=ast.parse((ROOT/'experiments/placement_diagnostic_v2/native_combined.py').read_text())
  for name in ('observe_areas','native_bool'):
   first=next(x for x in current.body if isinstance(x,ast.FunctionDef) and x.name==name)
   second=next(x for x in prior.body if isinstance(x,ast.FunctionDef) and x.name==name)
   if name=='observe_areas':
    # Permit only the reviewed explicit four-layer extension. After removing
    # those exact additions, the complete old two-layer collector must match.
    self.assertEqual([x.arg for x in first.args.kwonlyargs],['copper_layers'])
    self.assertEqual(ast.dump(first.args.kw_defaults[0]),ast.dump(ast.Constant(value=None)))
    guard=ast.parse("if copper_layers is not None and copper_layers != ('F.Cu','In1.Cu','In2.Cu','B.Cu'):\n raise ValueError('explicit canonical four-copper observation context required')").body[0]
    self.assertEqual(ast.dump(first.body[0]),ast.dump(guard));first.body.pop(0)
    first.args.kwonlyargs=[];first.args.kw_defaults=[]
    def layers(function):
     return next(value for node in ast.walk(function) if isinstance(node,ast.Dict)
                 for key,value in zip(node.keys,node.values) if isinstance(key,ast.Constant) and key.value=='layers')
    actual=layers(first).generators[0];old=layers(second).generators[0]
    expected=ast.parse("((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')) if copper_layers is None else ((pcbnew.F_Cu,'F.Cu'),(pcbnew.In1_Cu,'In1.Cu'),(pcbnew.In2_Cu,'In2.Cu'),(pcbnew.B_Cu,'B.Cu'))",mode='eval').body
    self.assertEqual(ast.dump(actual.iter),ast.dump(expected))
    self.assertEqual(ast.dump(actual.iter.body),ast.dump(old.iter));actual.iter=copy.deepcopy(old.iter)
   self.assertEqual(ast.dump(first),ast.dump(second))
 def test_entry_and_file_limit_fail_before_unbounded_population(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as name:
   root=Path(name)
   for i in range(5):(root/str(i)).mkdir()
   with self.assertRaisesRegex(Exception,'entry ceiling'):pc.inventory(root,max_entries=3)
   for i in range(4):(root/str(i)/'x').write_bytes(b'a')
   with self.assertRaisesRegex(Exception,'file ceiling'):pc.inventory(root,max_files=2)
 def test_actual_file_size_symlink_and_growth_limit(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as name:
   root=Path(name);path=root/'x';path.write_bytes(b'12345')
   with self.assertRaisesRegex(Exception,'bounded'):pc.read_bytes(path,4)
   with self.assertRaisesRegex(Exception,'bounded'):pc.inventory(root,max_bytes=4)
   (root/'link').symlink_to(path)
   with self.assertRaisesRegex(Exception,'symlink'):pc.inventory(root)
 def test_descriptor_limits_read_and_rejects_size_race(self):
  import os
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as name:
   path=Path(name)/'x';path.write_bytes(b'12345');real=observer.os.fstat if hasattr(observer,'os') else os.fstat
   class RacingFile:
    def __init__(self,handle):self.handle=handle
    def __enter__(self):return self
    def __exit__(self,*args):self.handle.close()
    def fileno(self):return self.handle.fileno()
    def read(self,size):
     self.request=size
     with path.open('ab') as writer:writer.write(b'12345')
     return self.handle.read(size)
   realopen=os.fdopen;handles=[]
   def fdopen(fd,mode):
    handle=RacingFile(realopen(fd,mode));handles.append(handle);return handle
   with patch.object(pc.os,'fdopen',fdopen),self.assertRaisesRegex(Exception,'changed or exceeded'):pc.read_bytes(path,6)
   self.assertEqual(handles[0].request,6)
