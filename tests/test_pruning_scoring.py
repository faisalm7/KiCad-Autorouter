"""Scoring-contract falsifiers only; actual native routing is separate evidence."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import strategy as s,pipeline as p


class PruningScoring(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.path=self.root/'incumbent/result.json';self.path.parent.mkdir()
  self.inc={'scoring_variant':'via_high','engine_profile':'tuned','adapter':'both','scope':'whole_board_unlocked_routing',
    'source':'owned-source','source_hashes':{'board':'exact'},'tools':{'frozen':'exact'}}
  self.inc['engine_budget']=p.engine_profile_settings('tuned',90.,scoring_variant='via_high')
  self.inc.update(budget_seconds=120.,cpu_budget_seconds=120.)
  self.inc['engine_budget'].update(outer_task_wall_budget_seconds=120.,outer_task_cpu_budget_seconds=120.)
  self.inc['steps']=[{'name':'engine','cpu_seconds':1,'argv':p.engine_argv(self.path.parent,self.inc['engine_budget']['argv']),'cwd':str(self.path.parent),
    'status':'success','exit_code':0,'cleanup_complete':True}]
  p.save_json(self.path.parent/'engine-process.json',self.inc['steps'][0])
  p.save_json(self.path,self.inc)
  self.parent={key:copy.deepcopy(self.inc[key]) for key in ('source','source_hashes','tools')}
  self.parent.update(incumbent_scoring_variant='via_high',incumbent_receipt_sha256=p.sha(self.path),steps=[dict(self.inc['steps'][0],phase='incumbent')])
  self.parent['strategy']='native_validated_zone_net_pruning'
  self.marker=self.root/'pruning-scoring.json'
  p.save_json(self.marker,{'schema':1,'strategy':self.parent['strategy'],'incumbent_scoring_variant':'via_high'})
  self.parent['incumbent_scoring_contract']={'file':self.marker.name,'sha256':p.sha(self.marker)}
 def test_explicit_preset_requires_actual_incumbent_validation(self):
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result') as check:
   s.check_incumbent_scoring(self.root,self.parent);check.assert_called_once_with(self.path)
 def test_marker_downgrade_wrong_preset_or_receipt_and_worker_change_reject(self):
  for mutation in ('missing-preset','wrong-preset','missing-pin','wrong-pin','worker'):
   data=copy.deepcopy(self.parent)
   if mutation=='missing-preset':del data['incumbent_scoring_variant']
   elif mutation=='wrong-preset':data['incumbent_scoring_variant']='via_low'
   elif mutation=='missing-pin':del data['incumbent_receipt_sha256']
   elif mutation=='wrong-pin':data['incumbent_receipt_sha256']='wrong'
   else:data['steps'][0]['cpu_seconds']=.5
   with self.subTest(mutation=mutation),self.assertRaises(p.Rejected):s.check_incumbent_scoring(self.root,data)
 def test_different_source_profile_scope_or_tools_are_not_free_incumbents(self):
  for key,value in [('source','other'),('source_hashes',{}),('tools',{}),('scope','partial_completion'),('engine_profile','standard')]:
   inc=copy.deepcopy(self.inc);inc[key]=value;p.save_json(self.path,inc);data=copy.deepcopy(self.parent);data['incumbent_receipt_sha256']=p.sha(self.path)
   with self.subTest(key=key),self.assertRaises(p.Rejected):s.check_incumbent_scoring(self.root,data)
 def test_legacy_default_is_preserved_but_unknown_preset_never_creates_output(self):
  self.inc['scoring_variant']=None
  self.inc['engine_budget']=p.engine_profile_settings('tuned',90.)
  self.inc['engine_budget'].update(outer_task_wall_budget_seconds=120.,outer_task_cpu_budget_seconds=120.)
  self.inc['steps'][0]['argv']=p.engine_argv(self.path.parent,self.inc['engine_budget']['argv'])
  p.save_json(self.path.parent/'engine-process.json',self.inc['steps'][0]);p.save_json(self.path,self.inc);data=copy.deepcopy(self.parent)
  data['steps']=[dict(self.inc['steps'][0],phase='incumbent')]
  del data['incumbent_scoring_variant'];del data['incumbent_receipt_sha256']
  del data['incumbent_scoring_contract'];self.marker.unlink()
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result') as check:s.check_incumbent_scoring(self.root,data);check.assert_called_once_with(self.path)
  for preset in ('invented',True,[]):
   out=self.root/'no-output'
   with self.subTest(preset=preset),self.assertRaises(p.Rejected):s.prune(self.root/'absent-source',out,incumbent_scoring=preset)
   self.assertFalse(out.exists())
 def test_relabelled_high_incumbent_cannot_be_downgraded_to_legacy_default(self):
  self.inc['scoring_variant']=None;p.save_json(self.path,self.inc);data=copy.deepcopy(self.parent)
  del data['incumbent_scoring_variant'];del data['incumbent_receipt_sha256'];del data['incumbent_scoring_contract'];self.marker.unlink()
  with patch.object(p,'check_minimum_width_record',return_value=None),self.assertRaisesRegex(p.Rejected,'execution journal'):
   s.check_incumbent_scoring(self.root,data)
 def test_coherently_edited_full_command_and_cwd_cannot_escape_router_flags(self):
  for change in ('output','jar','sandbox','cwd'):
   inc=copy.deepcopy(self.inc);worker=inc['steps'][0]
   if change=='cwd':worker['cwd']=str(self.root/'other')
   elif change=='output':worker['argv'][-1]=str(self.root/'other.ses')
   elif change=='jar':worker['argv'][worker['argv'].index('-jar')+1]='other.jar'
   else:worker['argv'][0]='other-supervisor'
   p.save_json(self.path,inc);p.save_json(self.path.parent/'engine-process.json',worker)
   data=copy.deepcopy(self.parent);data['incumbent_receipt_sha256']=p.sha(self.path);data['steps']=[dict(worker,phase='incumbent')]
   with self.subTest(change=change),patch.object(p,'check_minimum_width_record',return_value=None),self.assertRaisesRegex(p.Rejected,'execution journal'):
    s.check_incumbent_scoring(self.root,data)
 def test_symlink_contract_rejects_before_any_marker_digest(self):
  target=self.root/'owned-target';target.write_text('{}');self.marker.unlink();self.marker.symlink_to(target)
  with (patch.object(p,'sha',side_effect=AssertionError('digest must not follow marker symlink')),
        self.assertRaises(p.Rejected)):
   s.check_incumbent_scoring(self.root,self.parent)
