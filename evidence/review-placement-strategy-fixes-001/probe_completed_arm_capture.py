"""Actual paired wrapper, synthetic owned arm receipts and stubbed tool/source/native checks.
The stub candidate checker compares retained bytes to the originally recorded hash.
A mutation at invocation publication isolates whether completed-arm capture guards
that acceptance interval. No real board, routing result or native evidence is claimed.
"""
from pathlib import Path
import json,sys,tempfile,hashlib
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from scripts import experiment_paired as paired
results=[]
for variant in ('unchanged','mutated_after_check'):
 with tempfile.TemporaryDirectory(dir=HERE) as tmp:
  base=Path(tmp);source=base/'source/fixture.kicad_pcb';source.parent.mkdir();source.write_text('owned synthetic input\n');out=base/'paired'
  frozen={'tools':{'git_head':'owned-synthetic'},'source_hashes':{},'files_sha256':{}}
  checks=[];mutations=[]
  def fake_route(board,directory,assigned,*args,**kwargs):
   directory=Path(directory);directory.mkdir();candidate=directory/'candidate/fixture.kicad_pcb';candidate.parent.mkdir();candidate.write_text('owned synthetic candidate\n')
   result={'status':'routing_accepted','accepted':True,'source':str(board),'tools':frozen['tools'],'source_hashes':{},'candidate':str(candidate),'candidate_sha256':p.sha(candidate),'metrics':{'track_length_mm':100.,'vias':0},'guidance_policy':'placement-search-v1','wall_budget_seconds':assigned,'budget_seconds':assigned,'cpu_budget_seconds':assigned,'trials':[]}
   p.save_json(directory/'result.json',result);return result
  def fake_portfolio(directory,*args,**kwargs):
   result=fake_route(source,directory,kwargs['budget']);p.save_json(Path(directory)/'portfolio-summary.json',result);return result
  def checker(path):
   data=json.loads(Path(path).read_text());okay=p.sha(Path(data['candidate']))==data['candidate_sha256'];checks.append({'receipt':str(path),'matches':okay})
   if not okay:raise p.Rejected('owned candidate hash mismatch')
   return True
  def summarize(arm,directory,result,*args):
   checker(Path(directory)/'result.json')
   return {**arm,'accepted':True,'status':'routing_accepted','length_mm':100.,'vias':0,'candidate_sha256':result['candidate_sha256'],'result':str(Path(directory)/'result.json'),'result_sha256':p.sha(Path(directory)/'result.json')}
  def publish(path,data):
   p.save_json(path,data)
   if variant=='mutated_after_check' and path.name=='B1-invocation.json' and not mutations:
    target=out/'B1/candidate/fixture.kicad_pcb';before=p.sha(target);target.write_text('owned deliberately mutated candidate\n');mutations.append({'target':str(target),'before':before,'after':p.sha(target)})
  portfolio_record={'id':'B2_portfolio','accepted':True,'status':'completed','trials':[],'pareto_frontier':[],'selected':{}}
  with patch.object(paired.q,'selected_source',return_value=(source,{'owned':True})),patch.object(paired.portfolio,'freeze',return_value=frozen),patch.object(paired.q,'verify_freeze'),patch.object(paired.subprocess,'run',return_value=SimpleNamespace(stdout=paired.SCRIPT.read_bytes())),patch.object(paired.p,'route',side_effect=fake_route),patch.object(paired.f,'route',side_effect=fake_route),patch.object(paired.ps,'prune',side_effect=fake_route),patch.object(paired.portfolio,'experiment',side_effect=fake_portfolio),patch.object(paired,'verify_portfolio',return_value=portfolio_record),patch.object(paired.q,'summarize',side_effect=summarize),patch.object(paired.q,'observations',return_value=[]),patch.object(paired,'publish',side_effect=publish):
   summary=paired.experiment(out,'multichannel','placement')
  try:checker(out/'B1/result.json')
  except p.Rejected as exc:post_consistent=False;post_error=str(exc)
  else:post_consistent=True;post_error=None
  row=next(x for x in summary['results'] if x['id']=='B1')
  results.append({'variant':variant,'paired_status':summary['status'],'B1_accepted_in_final_summary':row['accepted'],'postrun_candidate_consistent':post_consistent,'postrun_error':post_error,'mutations':mutations,'shared_wall_seconds':summary.get('shared_overhead_wall_seconds'),'shared_cpu_seconds':summary.get('shared_overhead_cpu_seconds'),'inner_allowance_seconds':json.loads((out/'protocol.json').read_text())['inner_allowance_seconds'],'checks':checks})
(HERE/'completed-arm-capture-001.json').write_text(json.dumps({'scope':__doc__,'current_source_sha256':p.sha(ROOT/'scripts/experiment_paired.py'),'results':results},indent=2)+'\n');print(json.dumps(results))
