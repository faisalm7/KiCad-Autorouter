"""Single fresh whole-zone deletion from this method's own rejected C candidate.
Diagnostic only. Existing source/class/Native/PRL/protection helpers determine validity.
"""
from pathlib import Path
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
import sys,json,shutil
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,local_settings as ls,config as c,handoff as h
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.universal_shift_recovery_v1 import proposal as helper
PROTOCOL=Path(__file__).with_name('input-pins.json');CAP=45.
def need(v,reason):
 if not v:raise p.Rejected(reason)
def inputs(spec):
 need(spec['status']=='frozen' and spec['kind']=='universal-own-C-whole-zone-deletion-v1','unfrozen single deletion protocol')
 for name,pin in spec['pins'].items():need(p.sha(ROOT/name)==pin,'frozen source/evidence changed: '+name)
 source=Path(spec['source']);need(p.tree_hash(source.parent)==spec['source_hashes'],'original seven-file source changed')
 previous=f.read_json(ROOT/spec['prior_reader_execution']);need(previous['passed'] is True and previous['source_current'] is True and previous['final_charged_results']==spec['prior_rows'],'previous actual whole readback differs')
 warm=f.read_json(ROOT/spec['warm_receipt']);candidate=Path(warm['candidate'])
 need({k:v for k,v in warm['tools'].items() if k!='git_head'}=={k:v for k,v in spec['tools'].items() if k!='git_head'},'retained core/native tools changed beyond historical HEAD')
 need(warm['accepted'] is False and warm['status']=='drc_rejected' and warm['candidate_sha256']==spec['warm_sha256']==p.sha(candidate),'own failed C candidate differs')
 need(warm['source']==str(source) and warm['source_hashes']==spec['source_hashes'] and warm['native']['opens']==1 and warm['native']['blocking']==1 and warm['native']['warnings']==81 and warm['native']['exclusions']==0,'frozen failed Native disposition differs')
 baseline=f.read_json(ROOT/spec['original_receipt'])['parity_native'];need(p.native_accepted(baseline) and baseline['warnings']==81 and len(baseline['ignored_checks'])==5,'original baseline Native differs')
 return source,p.preflight(source),candidate,baseline

def check(out,data,spec):
 """Pure existing-helper replay. No Native/engine execution."""
 source,original,warm,baseline=inputs(spec);folder=out/'validation'
 tree,proposal,protected,names,protection=helper.deletion(original,sx.read(warm))
 need(data['proposal']==proposal and data['protected_before']==protection and data['zone_names']==names,'deletion/protected proposal differs')
 need(pc.read_bytes(folder/'pre-refill.kicad_pcb')==(sx.dump(tree)+'\n').encode(),'single deletion preimage differs')
 phase=helper.phase(folder,data['steps'],source,spec['source_hashes'],data['tools'],protected,sx.read(warm),names,baseline)
 entry={k:v for k,v in phase['entry'].items() if k!='job'}
 need(entry==data['final_observation'] and phase['metrics']==data['metrics'] and phase['protected_signal_audit']==data['protected_after'],'actual final Native/metrics/protection differs')
 valid=phase['candidate_valid'] and max(data['wall_seconds'],data['full_cpu_seconds'])+2<=CAP
 need(data['candidate_valid'] is valid and data['accepted'] is False and data['production_admitted'] is False,'diagnostic qualification differs')
 return dict(passed=True,candidate_valid=valid,candidate_sha256=entry['candidate_sha256'],original_design_checks=True,complete_schematic_checks=True,protected_signals_exact=True,original_warning_signatures_unchanged=helper.warnings(entry['native'])==helper.warnings(baseline))

def run(out):
 spec=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL);out=Path(out).absolute();need(str(out)==spec['output'] and not out.exists(),'new exact owned output required')
 expected=ROOT/'.runs/universal-own-C-ground-delete450-001/work'
 need(out==expected and out.resolve()==out and not any(x.is_symlink() for x in (out,*out.parents)),'canonical project output required')
 out.mkdir();owner={};h.capture_destination(owner,out);tools=p.tool_manifest();need(tools==spec['tools'],'current committed tools differ')
 result=dict(schema=1,kind='universal-own-C-whole-zone-deletion-v1',status='failed',accepted=False,production_admitted=False,candidate_valid=False,method_qualified=False,tools=tools,protocol_sha256=pin,steps=[])
 def elapsed():return time.monotonic()-START,cpu()-CPU0
 def remaining():return CAP-max(elapsed())
 material=None
 def stable():
  need(p.tool_manifest()==tools and p.sha(PROTOCOL)==pin,'tool/protocol changed')
  inputs(spec);h.owned_destination(owner)
  if material is not None:
   # Native metadata after callbacks; final bytes after metadata.
   folder=out/'validation'
   for step in result['steps']:
    argv=step['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
    if command[:3]==[str(c.CLI),'pcb','drc']:
     name=step['name'];process=f.read_json(folder/(name+'-process.json'));failed=process['status']!='success' and not (process['status']=='nonzero_exit' and process.get('exit_code')==5)
     ls.check_event(folder,f.read_json(folder/(name+'-binding.json')),process,allow_worker_failure=failed)
   need(f.evidence_inventory(out)==material,'completed candidate/Native material changed')
  need(remaining()>0,'single deletion45-second wall/fullCPU cap exceeded')
 def account():
  wall,full=elapsed();result.update(wall_seconds=wall,full_cpu_seconds=full)
  if max(wall,full)+2>CAP:result.update(candidate_valid=False,method_qualified=False)
 try:
  source,original,warm,baseline=inputs(spec);stable()
  tree,proposal,protected,names,protection=helper.deletion(original,sx.read(warm))
  folder=out/'validation';job=f.FloorJob(folder,45,remaining,protect_local_settings=True)
  copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},folder/'code')
  copy_bytes(pc.inventory(source.parent,contents=True),folder/'snapshot');copy_bytes(pc.inventory(source.parent,contents=True),folder/'candidate')
  candidate=folder/'candidate'/source.name;sx.write(candidate,tree)
  digest,native=p.validate_candidate(job,original,candidate,spec['source_hashes'],protected,schematic_parity=True)
  job.native('metrics','metrics',candidate,folder/'metrics.json')
  phase=helper.phase(folder,job.steps,source,spec['source_hashes'],tools,protected,sx.read(warm),names,baseline)
  result.update(status='completed',steps=job.steps,proposal=proposal,zone_names=names,protected_before=protection,protected_after=phase['protected_signal_audit'],final_observation={k:v for k,v in phase['entry'].items() if k!='job'},metrics=phase['metrics'],candidate_valid=phase['candidate_valid'],method_qualified=True)
  account();result['shared_checks']=check(out,result,spec)
 except BaseException as exc:
  result.update(status='failed',candidate_valid=False,method_qualified=False,reason=type(exc).__name__+': '+str(exc))
  if 'job' in locals():result['steps']=job.steps
 account();material=f.evidence_inventory(out);result['completed_material']=material
 f.publish(out,result,stable,account,remaining,owned=lambda:h.owned_destination(owner))
 receipt=out/'result.json';need(f.canonical(f.read_json(receipt))==f.canonical(result),'published C receipt differs');rpin=p.sha(receipt);stable();need(p.sha(receipt)==rpin,'published C receipt changed')
 print(json.dumps({k:result.get(k) for k in ('status','candidate_valid','method_qualified','reason','wall_seconds','full_cpu_seconds')}));return result
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();r=run(args.output);raise SystemExit(0 if r['status']=='completed' else 2)
