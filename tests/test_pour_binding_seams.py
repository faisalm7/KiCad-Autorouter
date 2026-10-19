"""Pure adversarial binding regressions; no native/engine proof."""
from pathlib import Path
import copy,hashlib,sys,types,unittest
from unittest import mock
from autorouter import pipeline as p,pour_rule_area as policy,pour_rule_area_native as native,floor_context as context,floor_route as f,placement_clearance as pc,sexpr as sx
def digest(raw):return hashlib.sha256(raw).hexdigest()
aid='00000000-0000-0000-0000-000000000001'
zid='00000000-0000-0000-0000-000000000002'
area=['zone',['net','0'],['net_name','""'],['uuid','"'+aid+'"'],['layer','"F.Cu"'],
    ['keepout',*[[flag,'not_allowed' if flag=='copperpour' else 'allowed'] for flag in policy.FLAGS]],
    ['polygon',['pts',['xy','10','10'],['xy','15','10'],['xy','15','15'],['xy','10','15']]]]
zone=['zone',['net','1'],['uuid','"'+zid+'"'],['layer','"F.Cu"'],
    ['filled_polygon',['layer','"F.Cu"'],['pts',['xy','20','20'],['xy','21','20'],['xy','21','21'],['xy','20','21']]]]
tree=['kicad_pcb',['net','0','""'],['net','1','"GND"'],['layers',['0','"F.Cu"','signal'],['31','"B.Cu"','signal']],area,zone]
good=(sx.dump(tree)+'\n').encode();changed=copy.deepcopy(tree)
sx.one(sx.one(sx.children(changed,'zone')[1],'filled_polygon'),'pts')[1:]=[
    ['xy','11','11'],['xy','12','11'],['xy','12','12'],['xy','11','12']]
bad=(sx.dump(changed)+'\n').encode();project_bytes=b'{}'
source=Path('/__owned_pure_binding_control__/owned.kicad_pcb')
project=source.with_suffix('.kicad_pro')
areas=policy.qualify(tree)

class UID:
    def __init__(self,value):self.value=value
    def AsString(self):return self.value
class Poly:
    def __init__(self,other=None):self.count=1
    def OutlineCount(self):return self.count
    def BooleanIntersection(self,outline):self.count=0
class Zone:
    def __init__(self,value):self.m_Uuid=UID(value)
    def IsOnLayer(self,layer):return layer==0
    def GetFilledPolysList(self,layer):return Poly()
    def Outline(self):return Poly()
class Board:
    def Zones(self):return [Zone(aid),Zone(zid)]

shim=types.SimpleNamespace(SHAPE_POLY_SET=Poly,F_Cu=0,B_Cu=31,GetBuildVersion=lambda:'10.0.0')
observed=[{key:value for key,value in row.items() if key!='source_zone_ast_sha256'} for row in areas]
before=(digest(good),digest(project_bytes))

class PourBindingSeams(unittest.TestCase):
 def test_optimizer_incumbent_uses_contextual_reader_without_uncontextualized_retry(self):
  # Native pour audit/refill are seams here; the production dispatch is real.
  from autorouter import strategy
  directory=Path('/__owned_pure_parent_lineage_control__');candidate=directory/'candidate'/'owned.kicad_pcb'
  data={'baseline':'C-prototype','steps':[],'source_hashes':{'owned.kicad_pcb':digest(good)}}
  for contextual in (True,False):
   with self.subTest(contextual=contextual),mock.patch.object(pc,'read_bytes',return_value=good),mock.patch.object(p,'sha',return_value=digest(good)),mock.patch.object(f,'read_json',return_value={}),mock.patch.object(policy,'verify_native_record'),mock.patch.object(f,'process_check'),mock.patch.object(f,'check_drc_stage'),mock.patch.object(sx,'read',return_value=copy.deepcopy(tree)),mock.patch.object(strategy,'check_native7_incumbent',return_value=contextual) as reader,mock.patch.object(p,'check_result') as legacy:
    p.check_pour_evidence(directory,data,tree,candidate)
    reader.assert_called_once_with(directory,data)
    if contextual:legacy.assert_not_called()
    else:legacy.assert_called_once_with(directory/'incumbent/result.json')
  with mock.patch.object(pc,'read_bytes',return_value=good),mock.patch.object(p,'sha',return_value=digest(good)),mock.patch.object(f,'read_json',return_value={}),mock.patch.object(policy,'verify_native_record'),mock.patch.object(f,'process_check'),mock.patch.object(f,'check_drc_stage'),mock.patch.object(sx,'read',return_value=copy.deepcopy(tree)),mock.patch.object(strategy,'check_native7_incumbent',side_effect=p.Rejected('context changed')),mock.patch.object(p,'check_result') as legacy:
   with self.assertRaisesRegex(p.Rejected,'context changed'):p.check_pour_evidence(directory,data,tree,candidate)
   legacy.assert_not_called()
 def test_native_input_capture_precedes_loaded_board(self):
  for raw,expected in ((good,True),(bad,False)):
   with self.subTest(matched=expected),mock.patch.dict(sys.modules,{'pcbnew':shim}),mock.patch.object(Path,'read_bytes',lambda self:raw if self==source else project_bytes),mock.patch.object(context,'observe_areas',lambda *args:{'footprint_zone_count':0,'zones':copy.deepcopy(observed)}):
    if expected:self.assertTrue(native.audit(Board(),source,before)['passed'])
    else:
     with self.assertRaisesRegex(ValueError,'across native board load'):native.audit(Board(),source,before)
 def test_native_both_layer_observation_order_is_normalized_without_source_edit(self):
  both=copy.deepcopy(tree);area_copy=sx.children(both,'zone')[0];area_copy[area_copy.index(sx.one(area_copy,'layer'))]=['layers','"F.Cu"','"B.Cu"']
  raw=(sx.dump(both)+'\n').encode();capture=(digest(raw),digest(project_bytes));aa=policy.qualify(both)
  obs=[{k:v for k,v in a.items() if k!='source_zone_ast_sha256'} for a in aa];obs[0]['layers']=['F.Cu','B.Cu']
  class BothZone(Zone):
   def IsOnLayer(self,layer):return layer in (0,31) if self.m_Uuid.AsString()==aid else layer==0
  class BothBoard(Board):
   def Zones(self):return [BothZone(aid),BothZone(zid)]
  with mock.patch.dict(sys.modules,{'pcbnew':shim}),mock.patch.object(Path,'read_bytes',lambda self:raw if self==source else project_bytes),mock.patch.object(context,'observe_areas',lambda *args:{'footprint_zone_count':0,'zones':obs}):
   result=native.audit(BothBoard(),source,capture);self.assertTrue(result['passed']);self.assertEqual(result['native_areas'][0]['layers'],['B.Cu','F.Cu']);self.assertEqual(result['board_sha256'],digest(raw))
 def test_stock_input_and_selected_prepartition_input_must_be_actual_raw_export(self):
  directory=Path('/__owned_pure_stock_lineage_control__');candidate=directory/'candidate'/'owned.kicad_pcb'
  raw_dsn=b'(owned raw DSN)';corrected_dsn=b'(owned corrected DSN)'
  for scope in ('whole_board_unlocked_routing','selected_nets'):
   for engine_input,extra,expected in ((raw_dsn,{},True),(corrected_dsn,{},False),(raw_dsn,{'adapter_transformations':{}},False)):
    data={'adapter':'none','baseline':'B0_stock','scope':scope,'steps':[{'name':'engine','cwd':str(directory)}],'source_hashes':{'owned.kicad_pcb':digest(good)},**extra}
    def read(path,*args,**kwargs):
     path=Path(path)
     if path==directory/'native.dsn':return raw_dsn
     if path in (directory/'task.dsn',directory/'routing-scope-input.dsn'):return engine_input
     if path in (directory/'pour-before-refill.kicad_pcb',candidate):return good
     raise AssertionError(str(path))
    with self.subTest(scope=scope,expected=expected,markers=bool(extra)),mock.patch.object(pc,'read_bytes',read),mock.patch.object(p,'sha',lambda path:digest(good)),mock.patch.object(f,'read_json',lambda path:{}),mock.patch.object(policy,'verify_native_record',lambda *args:True),mock.patch.object(f,'process_check',lambda *args,**kwargs:None),mock.patch.object(f,'check_drc_stage',lambda *args,**kwargs:None),mock.patch.object(sx,'read',lambda path:copy.deepcopy(tree)):
     if expected:p.check_pour_evidence(directory,data,tree,candidate)
     else:
      with self.assertRaises(p.Rejected):p.check_pour_evidence(directory,data,tree,candidate)
if __name__=='__main__':unittest.main()
