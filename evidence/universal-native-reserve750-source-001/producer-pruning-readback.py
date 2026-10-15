"""Shared actual worker/final observers for one native product improve run."""
from pathlib import Path
from autorouter import pipeline as p,floor_route as f,local_settings as ls,config as c,sexpr as sx
from experiments.native_paired_v1 import observations as obs
ROOT=c.ROOT

def inputs(spec):
 obs.require(spec['status']=='frozen' and spec['kind']=='universal-own-low-pruning450-v1','unfrozen own-C pruning protocol')
 for name,pin in spec['pins'].items():obs.require(p.sha(ROOT/name)==pin,'frozen material changed: '+name)
 source=Path(spec['source']);obs.require(p.tree_hash(source.parent)==spec['source_hashes'],'original source changed')
 old=f.read_json(ROOT/spec['prior_execution']);obs.require(old['passed'] is True and old['source_current'] is True and old['final_charged_results']==spec['prior_rows'],'completed B2 prefix changed')
 baseline=f.read_json(ROOT/spec['original_receipt'])['parity_native'];obs.require(p.native_accepted(baseline) and baseline['warnings']==81 and len(baseline['ignored_checks'])==5,'original Native changed')
 return source,p.preflight(source),baseline

def check(folder,data,spec):
 source,original,baseline=inputs(spec);hashes=spec['source_hashes']
 obs.require(data['source']==str(source) and data['source_hashes']==hashes and data['tools']==spec['tools'],'C source/code changed')
 obs.require(data['budget_seconds']==data['cpu_budget_seconds']==200 and data['scope']=='whole_board_unlocked_routing' and data['strategy']=='native_validated_zone_net_pruning' and data['proposal_policy']=='feedback' and data['incumbent_scoring_variant']=='via_low','C product settings changed')
 workers=obs.workers(folder,data,source,hashes,original);finals=[]
 paths=[('incumbent',folder/'incumbent/result.json',None)]+[(r['id'],Path(r['receipt']),data) for r in data['trials']]+[('final',folder/'result.json',None)]
 for name,path,parent in paths:
  if not path.is_file():continue
  trial=f.read_json(path);base=path.parent
  if not (base/'final-drc.json').is_file() or not trial.get('candidate_sha256'):continue
  if name=='incumbent':p.check_engine_profile_record(trial,base)
  error=obs.resource_failure(base,trial,parent)
  proof=obs.candidate(base,trial,source,original,hashes,baseline,parent=parent,resource_error=error)
  finals.append(dict(id=name,status=trial['status'],accepted=trial['accepted'],**proof))
 valid=data['accepted'] is True
 if valid:
  obs.require(p.check_result(folder/'result.json')['current'] is True,'accepted product result stale')
  final=next(r for r in finals if r['id']=='final')
  obs.require(final['full_shared_candidate_readback'] and final['unchanged_original_warning_signatures'],'final unqualified or warning signatures differ')
 return dict(passed=True,candidate_valid=valid,workers=workers,final_observations=finals,all_actual_finals_checked=True,original_design_checks=bool(finals),complete_schematic_checks=bool(finals))

def metadata(data):
 for step in data['steps']:
  argv=step['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
  if command[:3]==[str(c.CLI),'pcb','drc']:
   folder=Path(step['cwd']);name=step['name'];process=f.read_json(folder/(name+'-process.json'));failed=process['status']!='success' and not (process['status']=='nonzero_exit' and process.get('exit_code')==5)
   ls.check_event(folder,f.read_json(folder/(name+'-binding.json')),process,allow_worker_failure=failed)
