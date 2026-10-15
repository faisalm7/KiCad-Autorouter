"""Generic finite pure-reader enclosure; shared validators only, no Native/JVM/engine work."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,copy,argparse,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,local_settings as ls,config as c
from autorouter.runner import run
from experiments.native_paired_v1.observations import require,inventory,number
from scripts import experiment_quality as q
parser=argparse.ArgumentParser(description=__doc__)
for name in ('prospective','output','enclosure'):parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args();PROTOCOL=args.prospective.resolve(strict=True);spec=f.read_json(PROTOCOL);BASE=Path(spec['output']);OUT=args.enclosure.absolute();READEROUT=args.output.absolute();OUT.mkdir();CAP=90
READER=Path(spec['reader_source']);pin=p.sha(PROTOCOL);own=p.sha(Path(__file__));material=inventory(BASE);workers=[];result_pin=execution_pin=None
require(p.sha(READER)==spec['reader_sha256'],'frozen reader differs')
def stable():
 require(p.tool_manifest()==spec['tools'],'current tools differ');q.verify_freeze(spec['freeze'],Path(spec['source']))
 require(p.sha(PROTOCOL)==pin and p.sha(Path(__file__))==own and p.sha(READER)==spec['reader_sha256'],'reader/protocol/controller changed')
 for name,digest in spec['pins'].items():require(p.sha(R/name)==digest,'pinned source/original proof changed')
 require(hashlib.sha256(f.canonical(inventory(Path(spec['source_gate']['receipt']).parent)).encode()).hexdigest()==spec['source_gate']['inventory_sha256'],'original source qualification material changed')
 for worker in workers:
  cwd=Path(worker['cwd']);name=worker['name'];proc=f.read_json(cwd/(name+'-process.json'));argv=proc['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
  if command[:3]==[str(c.CLI),'pcb','drc']:
   binding=f.read_json(cwd/(name+'-binding.json'));failed=proc['status']!='success' and not (proc['status']=='nonzero_exit' and proc.get('exit_code')==5);ls.check_event(cwd,binding,proc,allow_worker_failure=failed)
 require(inventory(BASE)==material,'matrix material changed')
 if result_pin:require(p.sha(READEROUT/'result.json')==result_pin,'reader result changed')
 if execution_pin:require(p.sha(READEROUT/'execution.json')==execution_pin,'inner execution changed')
stable();p.save_json(OUT/'prospective-enclosure.json',dict(schema=1,controller_sha256=own,protocol_sha256=pin,reader_sha256=spec['reader_sha256'],wall_full_cpu_cap_seconds=CAP,publication_allowance_seconds=2,startup_allowance_seconds=1))
record=dict(schema=1,passed=False,new_native_execution=False,new_engine_execution=False,controller_sha256=own,protocol_sha256=pin,publication_allowance_seconds=2)
try:
 process=run([*f.SANDBOX,str(R/'.venv/bin/python'),'-B',str(READER),'--prospective',str(PROTOCOL),'--output',str(READEROUT)],cwd=OUT,log=OUT/'command.log',timeout=max(.001,CAP-2-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3);record['process']=process
 require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False,'reader process failed')
 result=f.read_json(READEROUT/'result.json');inner=f.read_json(READEROUT/'execution.json');workers=result['workers'];result_pin=p.sha(READEROUT/'result.json');execution_pin=p.sha(READEROUT/'execution.json')
 require(result['status']=='completed' and result['comparison_eligible'] is True and inner['result_sha256']==result_pin,'reader did not qualify matrix')
 stable();outer=f.read_json(BASE/'execution.json');summary=f.read_json(BASE/'run/paired-summary.json');rows=[];wall=time.monotonic()-START;full=cpu()-CPU0
 sw=number(outer['wall_seconds'])-sum(number(x['invocation_wall_seconds']) for x in summary['results']);sc=number(outer['full_cpu_seconds'])-sum(number(x['invocation_cpu_seconds']) for x in summary['results']);require(min(sw,sc)>=0,'enclosing costs omit invocations')
 common=spec['shared_original_qualification_cost'];prep=spec['source_preparation_cost']
 for raw in inner['final_charged_results']:
  row=copy.deepcopy(raw);row.update(charged_wall_seconds=row['invocation_wall_seconds']+sw+2+wall+1+2+common['wall_seconds']+prep['wall_seconds'],charged_cpu_seconds=row['invocation_cpu_seconds']+sc+2+full+1+2+common['full_cpu_seconds']+prep['full_cpu_seconds'])
  row['within_equal300_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=300;row['accepted']=raw['accepted'] and row['within_equal300_wall_full_cpu_caps']
  for observation in row.get('observations',[]):observation['final_delivery_accepted']=row['accepted']
  rows.append(row)
 require(max(wall,full)+2<=CAP,'reader enclosure exceeds90 wall/fullCPU')
 record.update(passed=True,source_current=True,wall_seconds=wall,full_cpu_seconds=full,final_charged_results=rows,result_sha256=result_pin,reader_execution_sha256=execution_pin,workers=len(workers),final_candidates=len(result['final_candidates']))
except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,reason=type(exc).__name__+': '+str(exc),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
p.save_json(OUT/'execution.json',record)
try:
 stable();require(max(time.monotonic()-START,cpu()-CPU0)<=CAP,'final reader enclosure cap exceeded');require(time.monotonic()-START<=record['wall_seconds']+2 and cpu()-CPU0<=record['full_cpu_seconds']+2,'final callbacks exceed publication reserve')
except (Exception,KeyboardInterrupt) as exc:
 for row in record.get('final_charged_results',[]):row['accepted']=False
 record.update(passed=False,reason=type(exc).__name__+': '+str(exc),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0);p.save_json(OUT/'execution.json',record)
print(json.dumps({k:record.get(k) for k in ('passed','reason','workers','final_candidates','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
