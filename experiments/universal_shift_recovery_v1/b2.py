"""Only the two previously unattempted B2 settings; all Native runs sequential."""
from pathlib import Path
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
import sys,json
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,local_settings as ls,config as c,handoff as h
from experiments.native_paired_v1 import observations as obs
PROTOCOL=ROOT/'.runs/universal-B2-missing450-001-protocol.json';CAP=220.
def need(v,reason):
 if not v:raise p.Rejected(reason)
def inputs(spec):
 need(spec['status']=='frozen' and spec['kind']=='universal-missing-B2-two-settings-v1','unfrozen B2 protocol')
 for name,pin in spec['pins'].items():need(p.sha(ROOT/name)==pin,'frozen source/evidence changed: '+name)
 source=Path(spec['source']);need(p.tree_hash(source.parent)==spec['source_hashes'],'original source changed')
 previous=f.read_json(ROOT/spec['prior_execution']);need(previous['passed'] is True and previous['source_current'] is True and previous['final_charged_results']==spec['prior_rows'],'actual C-probe prefix differs')
 baseline=f.read_json(ROOT/spec['original_receipt'])['parity_native'];need(p.native_accepted(baseline) and baseline['warnings']==81 and len(baseline['ignored_checks'])==5,'original baseline differs')
 need(spec['variants']==['via_low','via_high'] and spec['assigned_seconds']==90,'exact unattempted settings required')
 return source,p.preflight(source),baseline

def observe(folder,data,source,original,hashes,baseline):
 need(data['source']==str(source) and data['source_hashes']==hashes,'trial source identity differs')
 need(data['scope']=='whole_board_unlocked_routing' and data['adapter']=='both' and data['engine_profile']=='tuned' and data['budget_seconds']==data['cpu_budget_seconds']==90 and data.get('input_policy') is None,'trial configuration differs')
 workers=obs.workers(folder,data,source,hashes,original);entry=None
 engines=[step for step in data['steps'] if step.get('name')=='engine']
 engine_verified=len(engines)==1 and engines[0].get('status')=='success' and engines[0].get('exit_code')==0
 if engine_verified:p.check_engine_profile_record(data,folder)
 if (folder/'final-drc.json').is_file() and data.get('candidate_sha256'):
  entry=obs.candidate(folder,data,source,original,hashes,baseline,resource_error=obs.resource_failure(folder,data))
  need(entry['metrics'] is not None and engine_verified,'final candidate lacks actual metrics or verified engine settings')
 valid=bool(entry and entry['full_shared_candidate_readback'] and entry['unchanged_original_warning_signatures'] and data['accepted'] is True and p.native_accepted(data['native']))
 if data['accepted'] is True:p.check_result(folder/'result.json')
 return dict(workers=workers,final_candidate=entry,engine_profile_verified=engine_verified,candidate_valid=valid,status=data['status'],scoring_variant=data['scoring_variant'],accepted=data['accepted'])

def metadata(data):
 for row in data['trials']:
  trial=f.read_json(ROOT/row['result'])
  for step in trial['steps']:
   argv=step['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
   if command[:3]==[str(c.CLI),'pcb','drc']:
    folder=Path(step['cwd']);name=step['name'];process=f.read_json(folder/(name+'-process.json'));failed=process['status']!='success' and not (process['status']=='nonzero_exit' and process.get('exit_code')==5)
    ls.check_event(folder,f.read_json(folder/(name+'-binding.json')),process,allow_worker_failure=failed)

def check(out,data,spec):
 source,original,baseline=inputs(spec);entries=[]
 need(len(data['trials'])==2 and [r['id'] for r in data['trials']]==spec['variants'],'missing or duplicated B2 attempts')
 for row in data['trials']:
  folder=out/row['id'];receipt=folder/'result.json';trial=f.read_json(receipt)
  need(str(receipt.relative_to(ROOT))==row['result'] and p.sha(receipt)==row['result_sha256'],'trial receipt changed')
  need(trial['tools']==data['tools']==spec['tools'] and trial['scoring_variant']==row['id'],'trial code/settings changed')
  entry=observe(folder,trial,source,original,spec['source_hashes'],baseline);need(entry==row['observation'],'actual B2 observation differs');entries.append(entry)
 valid=any(row['candidate_valid'] for row in entries) and max(data['wall_seconds'],data['full_cpu_seconds'])+2<=CAP
 need(data['candidate_valid'] is valid and data['accepted'] is False and data['production_admitted'] is False and entries==data['final_observation'],'diagnostic qualification differs')
 return dict(passed=True,candidate_valid=valid,final_observation=entries,original_design_checks=all(r['final_candidate'] is not None for r in entries),complete_schematic_checks=all(r['final_candidate'] is not None for r in entries))

def run(out):
 spec=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL);out=Path(out).absolute()
 need(out==ROOT/'.runs/universal-B2-missing450-001/work' and str(out)==spec['output'] and out.resolve()==out and not any(x.is_symlink() for x in (out,*out.parents)) and not out.exists(),'new exact canonical output required')
 out.mkdir();owner={};h.capture_destination(owner,out);tools=p.tool_manifest();need(tools==spec['tools'],'committed tools differ')
 result=dict(schema=1,kind=spec['kind'],status='failed',accepted=False,production_admitted=False,candidate_valid=False,method_qualified=False,tools=tools,protocol_sha256=pin,trials=[],final_observation=[])
 def elapsed():return time.monotonic()-START,cpu()-CPU0
 def remaining():return CAP-max(elapsed())
 material=None
 def stable():
  need(p.tool_manifest()==tools and p.sha(PROTOCOL)==pin,'tool/protocol changed');inputs(spec);h.owned_destination(owner)
  if material is not None:
   metadata(result);need(f.evidence_inventory(out)==material,'completed B2 material changed')
  need(remaining()>0,'B2 actor220-second wall/fullCPU cap exceeded')
 def account():
  wall,full=elapsed();result.update(wall_seconds=wall,full_cpu_seconds=full)
  if max(wall,full)+2>CAP:result.update(candidate_valid=False,method_qualified=False)
 try:
  source,original,baseline=inputs(spec);stable();need(remaining()>=190,'insufficient time for two standalone90s settings plus readback')
  for variant in spec['variants']:
   stable();folder=out/variant
   trial=p.route(source,folder,90,False,'both','tuned',scoring_variant=variant)
   row=dict(id=variant,result=str((folder/'result.json').relative_to(ROOT)),result_sha256=p.sha(folder/'result.json'));result['trials'].append(row)
   row['observation']=observe(folder,trial,source,original,spec['source_hashes'],baseline)
  result.update(status='completed',final_observation=[r['observation'] for r in result['trials']],candidate_valid=any(r['observation']['candidate_valid'] for r in result['trials']),method_qualified=True)
  account();result['shared_checks']=check(out,result,spec)
 except BaseException as exc:result.update(status='failed',candidate_valid=False,method_qualified=False,reason=type(exc).__name__+': '+str(exc))
 account();material=f.evidence_inventory(out);result['completed_material']=material
 f.publish(out,result,stable,account,remaining,owned=lambda:h.owned_destination(owner))
 receipt=out/'result.json';need(f.canonical(f.read_json(receipt))==f.canonical(result),'published B2 receipt differs');rpin=p.sha(receipt);stable();need(p.sha(receipt)==rpin,'published B2 receipt changed')
 print(json.dumps({k:result.get(k) for k in ('status','candidate_valid','method_qualified','reason','wall_seconds','full_cpu_seconds')}));return result
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args();r=run(a.output);raise SystemExit(0 if r['status']=='completed' else 2)
