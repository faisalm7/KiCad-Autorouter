"""Unfrozen IR continuation; --worker is owned one-shot subprocess, never B0."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,shutil,fcntl,subprocess
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter.runner import run
from scripts import experiment_quality as q,experiment_portfolio as portfolio,experiment_paired as paired
ARMS=['B0','B1','B2_portfolio','C_feedback'];CAP=420.
def require(value,reason):
 if not value:raise p.Rejected(reason)
def num(value):
 require(q.finite_nonnegative(value),'invalid finite cost');return value
def inv(path):return pc.inventory(path,max_bytes=256*1024**2,max_files=16000,max_entries=32000,with_directories=True)
def pinned(spec):
 for name,pin in spec['pins'].items():require(p.sha(ROOT/name)==pin,'frozen receipt/source changed: '+name)
 for name,pin in spec['field_helpers_sha256'].items():require(p.sha(ROOT/name)==pin,'qualified field helper changed')
 for name,pin in spec['source_files_sha256'].items():require(p.sha(ROOT/name)==pin,'IR original input changed')
def contract(spec):
 require(spec['status']=='frozen' and spec['delivered_cap_seconds']==300 and spec['inner_cap_seconds']==120 and spec['reader_cap_seconds']==60,'freeze exact300/120/60 protocol')
 pinned(spec);old=f.read_json(ROOT/spec['prior_reader_execution']);require(old['passed'] is True and old['source_current'] is True,'old independent readback incomplete')
 rows=old['final_charged_results'];require([x['id'] for x in rows]==ARMS and all(x['accepted'] is False for x in rows) and rows==spec['prior_rows'],'old four failed outcomes/costs differ')
 require(all(max(num(x['charged_wall_seconds']),num(x['charged_cpu_seconds']))<=240 for x in rows),'old240 costs invalid')
 control=f.read_json(ROOT/spec['control_execution']);require(control['passed'] is True and control['source_current'] is True and control['publication_allowance_seconds']==2,'fresh fractional controls not qualified')
 require({k:v for k,v in control['tools'].items() if k!='git_head'}=={k:v for k,v in spec['tools'].items() if k!='git_head'} and control['actor_result_sha256']==p.sha(ROOT/spec['control_result']),'control producer/result differs')
 require(f.canonical(inv((ROOT/spec['control_result']).parent))==f.canonical(spec['control_material']),'qualified control material changed')
 result=f.read_json(ROOT/spec['control_result']);require(result['all_passed'] is True and result['accepted'] is False,'diagnostic control outcomes differ')
 review=f.read_json(ROOT/spec['control_reader_execution']);require(review['passed'] is True and review['source_current'] is True and review['publication_allowance_seconds']==2,'control independent readback not qualified')
 controlcost=(num(control['wall_seconds'])+2+num(review['wall_seconds'])+2,num(control['full_cpu_seconds'])+2+num(review['full_cpu_seconds'])+2)
 require(list(controlcost)==spec['control_charge'],'control actual+pub cost differs')
 gate=f.read_json(ROOT/spec['field_gate']);require(gate['passed'] is True and gate['source_current'] is True and gate['original_unchanged'] is True,'original field gate not qualified')
 require(gate['source_hashes']==spec['gate_source_hashes'] and gate['native_report_sha256']==spec['raw_baseline_sha256'],'field gate source/raw report differs')
 # Gate's old overall tools/HEAD are intentionally not equated to new edge code.
 require(all(gate['tools']['implementation_sha256'][name]==pin for name,pin in spec['field_helpers_sha256'].items()),'field gate helper lineage differs')
 require(max(max(x['charged_wall_seconds'],x['charged_cpu_seconds']) for x in rows)+max(controlcost)+120+60+13<=300,'prospective300 reserve insufficient')
 return rows,controlcost

def stable(spec):
 require(p.tool_manifest()==spec['tools'],'current tools/checkpoint differ')
 q.verify_freeze(spec['freeze'],Path(spec['source']))
 pinned(spec)
 require(p.sha(Path(spec['wrapper_source']))==spec['wrapper_sha256'] and p.sha(Path(spec['reader_source']))==spec['reader_sha256'],'controller/reader changed')
 for name,pin in spec['dependencies_sha256'].items():require(p.sha(ROOT/name)==pin,'shared reader dependency changed')
 require(p.tree_hash(Path(spec['source']).parent)==spec['source_hashes'],'source subtree changed')
def child(spec,out):
 record=dict(schema=1,status='incomplete',accepted=False,B1=None,feedback=None)
 try:
  stable(spec);contract(spec)
  lock=ROOT/'.runs/quality-experiment.lock';require(not lock.is_symlink(),'experiment lock alias')
  with lock.open('a') as held:
   fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
   before=time.monotonic();beforecpu=cpu()
   try:
    stable(spec);r=p.route(Path(spec['source']),out/'B1',120,False,'both','standard')
    row=q.summarize(dict(id='B1',adapter='both',engine_profile='standard',operation='route'),out/'B1',r,time.monotonic()-before,cpu()-beforecpu)
    stable(spec);record['B1']=row
   except Exception as exc:record['B1']=dict(id='B1',accepted=False,status='invocation_error',reason=type(exc).__name__+': '+str(exc))
   finally:
    record['B1'].update(invocation_wall_seconds=time.monotonic()-before,invocation_cpu_seconds=cpu()-beforecpu)
    row=record['B1'];row['within_equal_budgets']=all(q.finite_nonnegative(x) and x<=120 for x in (row.get('wall_seconds'),row.get('total_cpu_seconds'),row['invocation_wall_seconds'],row['invocation_cpu_seconds']));row['accepted']=row['accepted'] and row['within_equal_budgets']
    p.save_json(out/'B1-invocation.json',record['B1']);p.save_json(out/'worker-result.json',record)
   stable(spec)
   pair=paired.experiment(out/'feedback','ir-obstacle',system='feedback')
   record['feedback']=dict(status=pair['status'],summary_sha256=p.sha(out/'feedback/paired-summary.json'))
   stable(spec);record['status']='completed'
 except BaseException as exc:record.update(status='failed',reason=type(exc).__name__+': '+str(exc))
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
 p.save_json(out/'worker-result.json',record)
 return record

def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--prospective',type=Path,required=True);a.add_argument('--worker',action='store_true');args=a.parse_args();spec=f.read_json(args.prospective)
 out=Path(spec['output']);require(out==ROOT/'.runs/ir-obstacle-corrected-cumulative300-002','fixed fresh output required')
 if args.worker:return 0 if child(spec,out)['status']=='completed' else 2
 contract(spec);stable(spec)
 require(subprocess.run(['git','status','--porcelain','--untracked-files=normal'],cwd=ROOT,capture_output=True,check=True,timeout=10).stdout==b'','clean committed checkpoint required')
 oldbase=ROOT/spec['prior_matrix'];oldouter=f.read_json(oldbase/'execution.json');oldmaterial=inv(oldbase/'run')
 require(oldmaterial[0]==oldouter['paired_material'],'old matrix bytes differ; no old semantic replay')
 out.mkdir();shutil.copyfile(args.prospective,out/'prospective.json');shutil.copyfile(__file__,out/'wrapper.py');shutil.copyfile(spec['reader_source'],out/'reader.py')
 raw=Path(spec['raw_baseline']);shutil.copyfile(raw,out/'original-baseline.json');require(p.sha(raw)==p.sha(out/'original-baseline.json')==spec['raw_baseline_sha256'],'raw baseline copy differs')
 for name,pin in spec['dependencies_sha256'].items():
  target=out/'reader-dependencies'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target);require(p.sha(target)==pin,'dependency copy differs')
 record=dict(schema=1,status='incomplete',accepted=False,qualified=False,process=None,source_current=False,prospective_sha256=p.sha(args.prospective),wrapper_sha256=p.sha(Path(__file__)),reader_sha256=spec['reader_sha256'],prior_rows=spec['prior_rows'],control_charge=spec['control_charge'])
 try:
  record['process']=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),'--prospective',str(args.prospective),'--worker'],cwd=out,log=out/'command.log',timeout=max(.001,CAP-2-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=2*1024**3)
  stable(spec);contract(spec);require(inv(oldbase/'run')==oldmaterial,'retained old material changed')
  require(p.sha(args.prospective)==record['prospective_sha256'] and p.sha(Path(__file__))==record['wrapper_sha256'],'prospective/wrapper changed')
  record['source_current']=True;worker=f.read_json(out/'worker-result.json');record['status']=worker['status']
 except BaseException as exc:record.update(status='failed',reason=type(exc).__name__+': '+str(exc))
 record.update(material=inv(out),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
 record['whole_delivery_within_budget']=max(record['wall_seconds'],record['full_cpu_seconds'])+2<=CAP
 p.save_json(out/'execution.json',record);print(f.canonical({k:record[k] for k in ('status','source_current','wall_seconds','full_cpu_seconds')}))
 return 0 if record['status']=='completed' and record['source_current'] and record['process']['status']=='success' and record['process']['cleanup_complete'] is True and record['whole_delivery_within_budget'] else 2
if __name__=='__main__':raise SystemExit(main())
