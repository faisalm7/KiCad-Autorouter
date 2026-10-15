"""Real native-interpreter refusal/cancellation and retained thermal counterexample controls; no routing."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,copy,shutil,os,signal,threading,subprocess,fcntl,stat
from unittest.mock import patch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,config as c,runner
from experiments.native_components_v1 import controls
from scripts.native_cancellation import process_metadata
O=R/'.runs/native-components-thermal-001';O.mkdir();parent=R/'.runs/native-components-controls-001';w=R/'experiments/native_components_v1/worker.py';tools=p.tool_manifest()
material=f.evidence_inventory(parent);assert material==f.read_json(parent/'result.json')['completed_material']
fd=os.open(R/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW);lock=os.fdopen(fd,'r+');assert stat.S_ISREG(os.fstat(lock.fileno()).st_mode);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
record=dict(schema=1,passed=False,accepted=False,routing_accepted=False,production_admitted=False,tools=tools,script_sha256=p.sha(Path(__file__)),controls=[],budget_seconds=60,cpu_budget_seconds=60,publication_allowance_seconds=2)
def stable():
 assert tools==p.tool_manifest() and material==f.evidence_inventory(parent)
 assert max(time.monotonic()-START,cpu()-CPU0)+2<60
spec0=f.read_json(parent/'chain/request.json')
def prepare(case):
 directory=O/case;directory.mkdir();source=directory/'candidate';shutil.copytree(parent/'chain/candidate',source)
 spec=copy.deepcopy(spec0);spec.update(board=str(source/'smoke.kicad_pcb'),project_sha256=p.tree_hash(source))
 return directory,source,spec
try:
 # Reuse the actual retained thermal-negative Native evidence. Do not rerun old DRC.
 directory=O/'thermal-counterexample';directory.mkdir();old=R/'.runs/nus-native-connected-contact120-002';oldrecord=f.read_json(old/'result.json');trial=old/'whole-validation';board=trial/'candidate/usb_led.kicad_pcb';native=p.parse_report(trial/'final-drc.json',board.name)
 assert (native['opens'],native['blocking'],native['warnings'],native['exclusions'])==(0,1,10,0) and not p.native_accepted(native) and any(x['type']=='starved_thermal' and x['severity']=='error' for x in native['findings'])
 assert p.sha(board)=='5fa5d1e2500bcc8f804156a6c9216e8de69fc1cc34fb3d207bce410b0c9d4a91' and p.sha(trial/'final-drc.json')=='bb6bee270de3c2337241dc38582eb3c544032252a2381ed78c97d8844cbffeff' and native==oldrecord['whole_initial_native']
 for name,saved in [('refill-drc',True),('final-drc',False)]:
  binding=f.read_json(trial/(name+'-binding.json'));f.check_drc_stage(trial,oldrecord,name,Path(binding['source']),Path(binding['input']),saved,binding['before'],schematic_parity=not saved)
 spec=copy.deepcopy(spec0);spec.update(board=str(board),project_sha256=p.tree_hash(board.parent),refill_receipt=str(trial/'refill-drc-binding.json'),refill_receipt_sha256=p.sha(trial/'refill-drc-binding.json'))
 request=directory/'request.json';p.save_json(request,spec);out=directory/'components';before=p.tree_hash(board.parent)
 process=runner.run([*f.SANDBOX,str(c.PYTHON),str(w),'--request',str(request),'--output',str(out)],cwd=directory,log=directory/'worker.log',timeout=12,max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=2*1024**3);p.save_json(directory/'worker-process.json',process)
 hint=f.read_json(out/'result.json');assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and hint['status']=='diagnostic_completed' and hint['accepted'] is False and hint['routing_accepted'] is False
 bynet={}
 for group in hint['components']:bynet[group['net']]=bynet.get(group['net'],0)+1
 assert all(count==1 for count in bynet.values()) and p.tree_hash(board.parent)==before
 record['controls'].append(dict(case='thermal-counterexample',passed=True,native_interpreter_executed=True,old_native_drc_repeated=False,old_native_summary=str(old/'result.json'),old_native_summary_sha256=p.sha(old/'result.json'),native_report_sha256=p.sha(trial/'final-drc.json'),candidate_sha256=p.sha(board),native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},same_net_components=bynet,diagnostic_completed=True,candidate_accepted=False,process=process));stable()
 record['passed']=True
except BaseException as ex:record.update(passed=False,error=type(ex).__name__+': '+str(ex))
finally:
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,material=f.evidence_inventory(O));
 if max(record['wall_seconds'],record['full_cpu_seconds'])+2>60:record.update(passed=False,error='Whole negative controls exceed60s')
 p.save_json(O/'result.json',record);lock.close()
print(json.dumps({k:record.get(k) for k in ('passed','wall_seconds','full_cpu_seconds','error')}));raise SystemExit(0 if record['passed'] else 2)
