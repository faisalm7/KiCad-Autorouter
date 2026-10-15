"""Lead-only whole45s pure reader enclosure; no Native/JVM/engine work."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,local_settings as ls,config as c
from autorouter.runner import run
from scripts import experiment_quality as q
CAP=45.;OUT=ROOT/'.runs/universal-shift-interface-native-paired300-readback-execution-001';OUT.mkdir()
PROTOCOL=ROOT/'.runs/universal-shift-interface-native-paired300-002-protocol.json';spec=f.read_json(PROTOCOL)
READER=Path(spec['reader_source']);READEROUT=Path(spec['reader_output']);BASE=Path(spec['output']).parent
pins={str(PROTOCOL):p.sha(PROTOCOL),str(READER):p.sha(READER),str(Path(__file__)):p.sha(Path(__file__))}
require=lambda value:None if value else (_ for _ in ()).throw(p.Rejected('reader enclosure witness/cost differs'))
require(spec['status']=='frozen' and spec['reader_wall_full_cpu_cap_seconds']==45 and spec['delivered_wall_full_cpu_budget_per_arm_seconds']==300)
require(spec['reader_controller_source']==str(Path(__file__)) and spec['reader_controller_sha256']==pins[str(Path(__file__))])
material=pc.inventory(BASE,max_bytes=512*1024**2,max_files=10000,max_entries=20000,with_directories=True)
board=Path(spec['source']);readback_witness=None;prl_workers=[];execution_pin=None
def stable():
 require(p.tool_manifest()==spec['tools'])
 q.verify_freeze(spec['freeze'],board)
 for name,pin in {**spec['complete_source_files_sha256'],**spec['common_prerequisites']['pins']}.items():require(p.sha(ROOT/name)==pin)
 for item in spec['common_prerequisites']['stages']:require(p.sha(ROOT/item['path'])==item['sha256'])
 require(p.sha(ROOT/spec['qualified_source_gate']['path'])==spec['qualified_source_gate']['sha256'])
 for name,pin in {**spec['prior_matrix']['pins'],**spec['netclass_delta']['control']['pins']}.items():require(p.sha(ROOT/name)==pin)
 gate=spec['netclass_delta']['control']
 required={gate['result']:gate['result_sha256'],gate['execution']:gate['execution_sha256'],gate['readback_execution']:gate['readback_execution_sha256']}
 for path,pin in required.items():require(gate['pins'].get(path)==pin and p.sha(ROOT/path)==pin)
 require(f.canonical(pc.inventory((ROOT/gate['result']).parent,max_bytes=64*1024**2,max_files=3000,max_entries=6000,with_directories=True))==f.canonical(gate['material']))

 for key in ('old','new'):require(p.sha(ROOT/spec['netclass_delta']['captured_source'][key])==spec['netclass_delta']['implementation_sha256'][key])
 for name,pin in pins.items():require(p.sha(Path(name))==pin)
 for worker in prl_workers:
  cwd=Path(worker['cwd']);name=worker['name'];process=f.read_json(cwd/(name+'-process.json'));argv=process['argv']
  command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
  if command[:3]==[str(c.CLI),'pcb','drc']:
   binding=f.read_json(cwd/(name+'-binding.json'));failed=process['status']!='success' and not (process['status']=='nonzero_exit' and process.get('exit_code')==5)
   ls.check_event(cwd,binding,process,allow_worker_failure=failed)
 require(pc.inventory(BASE,max_bytes=512*1024**2,max_files=10000,max_entries=20000,with_directories=True)==material)
 if readback_witness is not None:require(pc.inventory(READEROUT,max_bytes=32*1024**2,max_files=1000,max_entries=2000,with_directories=True)==readback_witness)
 if execution_pin is not None:require(p.sha(OUT/'execution.json')==execution_pin)
stable()
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(READER),'--prospective',str(PROTOCOL),'--output',str(READEROUT)],cwd=OUT,log=OUT/'command.log',timeout=max(.001,CAP-2-(time.monotonic()-START)),max_workdir_bytes=1024**2,max_log_bytes=128*1024,max_group_rss_bytes=2*1024**3)
readback_witness=pc.inventory(READEROUT,max_bytes=32*1024**2,max_files=1000,max_entries=2000,with_directories=True) if READEROUT.is_dir() else None
record=dict(schema=1,passed=False,process=process,reader_sha256=pins[str(READER)],source_current=False,publication_allowance_seconds=2)
try:
 stable();record['source_current']=True
 result=f.read_json(READEROUT/'result.json');inner=f.read_json(READEROUT/'execution.json');paired=f.read_json(BASE/'run/paired-summary.json');outer=f.read_json(BASE/'execution.json')
 result_pin=p.sha(READEROUT/'result.json');inner_pin=p.sha(READEROUT/'execution.json');prl_workers=result['workers']
 require(inner['result_sha256']==result_pin)
 require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
 require(result['status']=='completed' and result['comparison_eligible'] is True)
 stable()
 wall=time.monotonic()-START;full=cpu()-CPU0;rows=[]
 sw=outer['wall_seconds']-sum(x['invocation_wall_seconds'] for x in paired['results']);sc=outer['full_cpu_seconds']-sum(x['invocation_cpu_seconds'] for x in paired['results']);require(sw>=0 and sc>=0)
 for raw in inner['final_charged_results']:
  row=dict(raw);row['charged_wall_seconds']=raw['prior_row']['charged_wall_seconds']+spec['new_prerequisites_charge'][0]+raw['invocation_wall_seconds']+sw+2+wall+1+2
  row['charged_cpu_seconds']=raw['prior_row']['charged_cpu_seconds']+spec['new_prerequisites_charge'][1]+raw['invocation_cpu_seconds']+sc+2+full+1+2
  row['within_equal300_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=300
  row['accepted']=raw['accepted'] and row['within_equal300_wall_full_cpu_caps'];rows.append(row)
 delivered=max(wall,full)+2<=CAP
 if not delivered:
  for row in rows:row['accepted']=False
 record.update(passed=delivered,wall_seconds=wall,full_cpu_seconds=full,final_charged_results=rows,result_sha256=result_pin,reader_execution_sha256=inner_pin)
except BaseException as exc:
 record.update(source_current=False,reason=type(exc).__name__+': '+str(exc),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
p.save_json(OUT/'execution.json',record)
execution_pin=p.sha(OUT/'execution.json')
try:
 stable()
 require(p.sha(OUT/'execution.json')==execution_pin)
 require(time.monotonic()-START<=record['wall_seconds']+2 and cpu()-CPU0<=record['full_cpu_seconds']+2)
 require(max(time.monotonic()-START,cpu()-CPU0)<=CAP)
except BaseException as exc:
 for row in record.get('final_charged_results',[]):row['accepted']=False
 record.update(passed=False,source_current=False,reason=type(exc).__name__+': '+str(exc),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
 p.save_json(OUT/'execution.json',record)
print(json.dumps({k:record.get(k) for k in ('passed','source_current','wall_seconds','full_cpu_seconds','reason')}));raise SystemExit(0 if record['passed'] else 2)
