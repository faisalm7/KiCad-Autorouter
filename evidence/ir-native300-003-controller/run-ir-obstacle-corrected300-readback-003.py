"""One-shot whole60s pure reader enclosure; preserves the inner receipts."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,copy,shutil
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter.runner import run
from scripts import experiment_quality as q,experiment_paired as paired
CAP=60.;STARTUP=1.;PUB=2.;ARMS=['B0','B1','B2_portfolio','C_feedback']
def require(value,reason):
 if not value:raise p.Rejected(reason)
def number(value):
 require(q.finite_nonnegative(value),'invalid finite cost');return value
def inventory(path,limit=256*1024**2):return pc.inventory(path,max_bytes=limit,max_files=16000,max_entries=32000,with_directories=True)
def same(a,b):return f.canonical(a)==f.canonical(b)

def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--prospective',type=Path,required=True);args=a.parse_args();protocol=args.prospective.resolve(strict=True);spec=f.read_json(protocol)
 reader=Path(spec['reader_source']);dest=Path(spec['reader_output']);base=Path(spec['output']);out=ROOT/'.runs/ir-obstacle-corrected300-readback-execution-003'
 require(spec['status']=='frozen' and spec['reader_cap_seconds']==CAP and spec['delivered_cap_seconds']==300,'freeze exact60/300 protocol')
 require(reader==ROOT/'.runs/read-ir-obstacle-corrected300-003.py' and spec['reader_controller_source']==str(Path(__file__).resolve()) and p.sha(Path(__file__))==spec['reader_controller_sha256'],'reader/controller identity differs')
 require(out==Path(spec['reader_enclosing_output']) and ROOT/'.runs' in dest.parents and not dest.exists() and not dest.is_symlink(),'fresh owned output required')
 pins={str(protocol):p.sha(protocol),str(reader):spec['reader_sha256'],str(Path(__file__).resolve()):spec['reader_controller_sha256'],spec['wrapper_source']:spec['wrapper_sha256']}
 require(all(p.sha(Path(n))==v for n,v in pins.items()),'initial source pin differs')
 old=f.read_json(ROOT/spec['prior_reader_execution']);prior=old['final_charged_results'];require(old['passed'] is True and same(prior,spec['prior_rows']) and [x['id'] for x in prior]==ARMS and all(x['accepted'] is False for x in prior),'exact old001 rows differ')
 control=f.read_json(ROOT/spec['control_execution']);review=f.read_json(ROOT/spec['control_reader_execution'])
 for r in (control,review):require(r['passed'] is True and r['source_current'] is True and r['publication_allowance_seconds']==PUB,'control qualification incomplete')
 controls=(number(control['wall_seconds'])+PUB+number(review['wall_seconds'])+PUB,number(control['full_cpu_seconds'])+PUB+number(review['full_cpu_seconds'])+PUB)
 require(same(list(controls),spec['control_charge']),'newcontrol cost differs')
 material=inventory(base);oldbase=ROOT/spec['prior_matrix'];oldmaterial=inventory(oldbase/'run');reader_material=None
 out.mkdir();shutil.copyfile(__file__,out/'controller.py');shutil.copyfile(protocol,out/'prospective.json')
 record=dict(schema=1,passed=False,accepted=False,source_current=False,process=None,reader_sha256=spec['reader_sha256'],controller_sha256=spec['reader_controller_sha256'],protocol_sha256=pins[str(protocol)],startup_allowance_seconds=STARTUP,publication_allowance_seconds=PUB,reader_cost_replaces_inner=True,prior_rows=prior,control_charge=list(controls),failed_continuation_common_charge=spec['failed_continuation_common_charge'],final_charged_results=[],comparisons=[])
 def stable():
  # No tool/runtime callback follows these last complete byte witnesses.
  require(p.tool_manifest()==spec['tools'],'current tool/runtime/checkpoint differs')
  q.verify_freeze(spec['freeze'],Path(spec['source']))
  for n,v in {**spec['pins'],**spec['field_helpers_sha256'],**spec['source_files_sha256'],**spec['dependencies_sha256']}.items():require(p.sha(ROOT/n)==v,'source/helper/proof pin changed: '+n)
  for n,v in pins.items():require(p.sha(Path(n))==v,'controller/reader/protocol changed')
  require(p.sha(out/'controller.py')==spec['reader_controller_sha256'] and p.sha(out/'prospective.json')==pins[str(protocol)],'retained controller/protocol changed')
  require(same(inventory(base),material) and same(inventory(oldbase/'run'),oldmaterial),'new/old matrix changed')
  require(same(inventory((ROOT/spec['control_result']).parent),spec['control_material']),'control material changed')
  if reader_material is not None:require(same(inventory(dest,32*1024**2),reader_material),'child result/execution changed after readback')
 try:
  stable()
  # Frozen reader owns its exact read-only Git subprocess guard.
  argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(reader),'--prospective',str(protocol),'--output',str(dest)]
  record['process']=run(argv,cwd=out,log=out/'command.log',timeout=max(.001,CAP-PUB-(time.monotonic()-START)),max_workdir_bytes=1024**2,max_log_bytes=128*1024,max_group_rss_bytes=2*1024**3)
  # Capture BEFORE final tool callbacks; callbacks cannot silently change proof.
  reader_material=inventory(dest,32*1024**2) if dest.is_dir() else None
  pins[str(out/'command.log')]=p.sha(out/'command.log')
  child=record['process'];require(child['argv']==argv and child['cwd']==str(out) and child['log']==str(out/'command.log'),'child identity differs')
  require(child['status']=='success' and type(child.get('exit_code')) is int and child['exit_code']==0 and child['cleanup_complete'] is True and child['log_truncated'] is False,'child failed/cleanup/log incomplete')
  require((out/'command.log').stat().st_size==child['log_bytes'],'child log changed')
  result=f.read_json(dest/'result.json');inner=f.read_json(dest/'execution.json')
  require(inner['result_sha256']==p.sha(dest/'result.json') and result['status']=='completed' and result['comparison_eligible'] is True,'inner shared checks did not qualify')
  require([x['id'] for x in inner['final_charged_results']]==ARMS and all(type(x.get('accepted')) is bool for x in inner['final_charged_results']),'inner four-arm population/eligibility differs')
  outer=f.read_json(base/'execution.json');worker=f.read_json(base/'worker-result.json');pair=f.read_json(base/'feedback/paired-summary.json');new=[worker['B1'],*pair['results']]
  require([x['id'] for x in new]==ARMS[1:] and all(type(x.get('accepted')) is bool for x in new) and outer['source_current'] is True and outer['whole_delivery_within_budget'] is True,'new outer/population differs')
  overhead=(number(outer['wall_seconds'])-sum(number(x['invocation_wall_seconds']) for x in new),number(outer['full_cpu_seconds'])-sum(number(x['invocation_cpu_seconds']) for x in new));require(min(overhead)>=0,'nested arm sums exceed outer')
  overhead=tuple(overhead[i]+number(spec['failed_continuation_common_charge'][i]) for i in range(2))
  stable()  # Last callbacks, then full source/material/child-result continuity.
  wall=time.monotonic()-START;full=cpu()-CPU0;within_reader=max(wall,full)+PUB<=CAP;rows=[]
  for oldrow,innerrow in zip(prior,inner['final_charged_results']):
   raw=next((x for x in new if x['id']==oldrow['id']),None);row=copy.deepcopy(innerrow)
   # Recompute from ingredients, replacing inner reader cost rather than adding it.
   row['charged_wall_seconds']=number(oldrow['charged_wall_seconds'])+controls[0]+(number(raw['invocation_wall_seconds']) if raw else 0)+overhead[0]+PUB+wall+STARTUP+PUB
   row['charged_cpu_seconds']=number(oldrow['charged_cpu_seconds'])+controls[1]+(number(raw['invocation_cpu_seconds']) if raw else 0)+overhead[1]+PUB+full+STARTUP+PUB
   row['within_equal300_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=300
   row['accepted']=bool(within_reader and raw and raw['accepted'] and innerrow['accepted'] and row['within_equal300_wall_full_cpu_caps']);rows.append(row)
  record.update(passed=within_reader,source_current=True,wall_seconds=wall,full_cpu_seconds=full,final_charged_results=rows,comparisons=paired.comparisons(rows) if within_reader else [],whole_delivery_within_budget=within_reader,replacement_shared_cost=list(overhead),result_sha256=p.sha(dest/'result.json'),inner_execution_sha256=p.sha(dest/'execution.json'),child_material_sha256=__import__('hashlib').sha256(f.canonical(reader_material).encode()).hexdigest(),child_receipts_unchanged=True)
 except BaseException as exc:record.update(reason=type(exc).__name__+': '+str(exc),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
 p.save_json(out/'execution.json',record)
 print(f.canonical({k:record.get(k) for k in ('passed','source_current','wall_seconds','full_cpu_seconds','reason')}));return 0 if record['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
