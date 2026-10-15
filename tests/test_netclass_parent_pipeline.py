"""Guarded production policy controls; these do not establish native routing."""
import copy,json,tempfile,unittest
from unittest import mock
from pathlib import Path
from autorouter import pipeline as p,sexpr as sx,netclass as n
from experiments.netclass_parent_transport_v1 import fixture

class ParentPipelineControls(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
  files,self.recipe=fixture.prepare()
  for name,raw in files.items():
   path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  self.board=self.root/'fixture.kicad_pcb';self.project=json.loads(self.board.with_suffix('.kicad_pro').read_text())
 def mapping(self):
  rows=[]
  for code,(cls,name,*_) in enumerate(fixture.PAIRS,1):
   source=next(x for x in self.project['net_settings']['classes'] if x['name']==cls)
   values={key:round(source[json_key]*1000000) for key,json_key,_ in n._DIMENSIONS}
   rows.append({'name':name,'netcode':code,'class':cls if cls=='Default' else cls+',Default','copper_pad_count':2,**values,
    'parameter_parents':{key:{'name':cls,'priority':source['priority'],'value_nm':values[key],'specified':True} for key,_,_ in n._DIMENSIONS}})
  return {'schema':1,'native_version':'10.0.0','units':'integer nanometres','source':str(self.board),'board_sha256':p.sha(self.board),
   'project_sha256':p.sha(self.board.with_suffix('.kicad_pro')),'board_saved':False,'nets':sorted(rows,key=lambda x:x['name'])}
 def test_preflight_admits_closed_three_class_source_without_rewriting_it(self):
  before=p.tree_hash(self.root);p.preflight(self.board)
  self.assertEqual(p.netclass_policy(self.board)['mode'],n.PARENT_POLICY);self.assertEqual(p.tree_hash(self.root),before)
 def test_candidate_audit_requires_source_parent_observation_and_exact_dimensions(self):
  self.assertTrue(p.audit_candidate_netclasses(self.board,[],self.mapping())['native']['passed'])
  altered=self.mapping();altered['nets'][1]['parameter_parents']['width_nm']['name']='Default'
  with self.assertRaisesRegex(ValueError,'dimension parent'):p.audit_candidate_netclasses(self.board,[],altered)
  tree=sx.read(self.board);tree.append(['segment',['start','10','10'],['end','15','10'],['width','0.4'],['layer','"F.Cu"'],['net','"/PWR_PAIR"'],['uuid','"00000000-0000-0000-0000-000000000001"']]);sx.write(self.board,tree)
  with self.assertRaisesRegex(p.Rejected,'native netclass target'):p.audit_candidate_netclasses(self.board,[],self.mapping())
 def test_unknown_names_and_noncanonical_four_layer_classes_remain_blocked(self):
  self.project['net_settings']['classes'][1]['name']='POWER,Default';self.board.with_suffix('.kicad_pro').write_text(json.dumps(self.project))
  with self.assertRaisesRegex(p.Rejected,'class names'):p.preflight(self.board)
  files,_=fixture.prepare();self.board.with_suffix('.kicad_pro').write_bytes(files['fixture.kicad_pro']);tree=sx.read(self.board);sx.one(tree,'layers').append(['4','"In1.Cu"','signal']);sx.one(tree,'layers').append(['6','"In2.Cu"','signal']);sx.write(self.board,tree)
  with self.assertRaisesRegex(p.Rejected,'unqualified four-copper layer declaration'):p.preflight(self.board)
 def test_parent_strategy_label_cannot_drop_dsn_basis_or_incumbent_costs(self):
  base=self.root/'incumbent';base.mkdir();step={'name':'engine','argv':['owned-engine'],'cpu_seconds':1,'wall_seconds':1}
  incumbent={'baseline':'B2_tuned','engine_profile':'tuned','netclass_policy':{'mode':n.PARENT_POLICY},'source':str(self.board),
   'source_hashes':{'source':'bound'},'task_sha256':'bound-task','scope':'whole_board_unlocked_routing','steps':[step]}
  for name in ('native.dsn','task.dsn','export-netclasses.json'):(base/name).write_text('owned synthetic metadata')
  (base/'result.json').write_text(json.dumps(incumbent))
  data={**incumbent,'baseline':'C-prototype','strategy':'native_validated_zone_net_pruning','incumbent':{'receipt':str(base/'result.json')},'steps':[{**step,'phase':'incumbent'}]}
  with self.assertRaisesRegex(p.Rejected,'incumbent basis'):p.check_parent_dsn_basis(self.root,data)
  data['netclass_parent_dsn_basis']=p.parent_dsn_basis(self.root)
  with mock.patch.object(p,'check_result',return_value={'current':True}) as checker:
   p.check_parent_dsn_basis(self.root,data);checker.assert_called_once_with(base/'result.json')
   altered=copy.deepcopy(data);altered['steps'][0]['cpu_seconds']=0
   with self.assertRaisesRegex(p.Rejected,'process/cost lineage'):p.check_parent_dsn_basis(self.root,altered)
   (base/'task.dsn').write_text('changed synthetic metadata')
   with self.assertRaisesRegex(p.Rejected,'incumbent basis'):p.check_parent_dsn_basis(self.root,data)
if __name__=='__main__':unittest.main()
