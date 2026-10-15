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
O=R/'.runs/native-components-negative-002';O.mkdir();parent=R/'.runs/native-components-controls-001';w=R/'experiments/native_components_v1/worker.py';tools=p.tool_manifest()
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
 for case,reason in [('stale-rules','complete input project pins differ'),('stale-refill','caller refill receipt pin differs'),('wrong-wrapper','pinned native Python wrapper differs'),('wrong-worker','observer implementation differs')]:
  stable();directory,source,spec=prepare(case)
  if case=='stale-board':
   with (source/'smoke.kicad_pcb').open('a') as stream:stream.write('\n')
  elif case=='stale-rules':
   path=source/'smoke.kicad_pro';data=f.read_json(path);data.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{})['min_clearance']=0.75;p.save_json(path,data)
  elif case=='stale-refill':
   path=directory/'refill-binding.json';path.write_bytes(Path(spec['refill_receipt']).read_bytes()+b'\n');spec['refill_receipt']=str(path)
  elif case=='wrong-wrapper':spec['wrapper_sha256']='0'*64
  elif case=='wrong-worker':spec['worker_sha256']='0'*64
  request=directory/'request.json';p.save_json(request,spec);out=directory/'components';before=p.tree_hash(source)
  process=runner.run([*f.SANDBOX,str(c.PYTHON),str(w),'--request',str(request),'--output',str(out)],cwd=directory,log=directory/'worker.log',timeout=8,max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=2*1024**3)
  p.save_json(directory/'worker-process.json',process)
  assert process['status']=='nonzero_exit' and process['exit_code']==1 and process['cleanup_complete'] and reason in (directory/'worker.log').read_text() and not out.exists() and p.tree_hash(source)==before
  record['controls'].append(dict(case=case,passed=True,expected_refusal=reason,native_interpreter_executed=True,observer_output_created=False,api_execution_claim=False,process=process));stable()
 # Reuse the actual retained thermal-negative Native evidence. Do not rerun old DRC.
 directory=O/'thermal-counterexample';directory.mkdir();old=R/'.runs/thermal-production-negative-001';oldrecord=f.read_json(old/'negative-summary.json');trial=old/'trial';board=Path(oldrecord['candidate']);native=p.parse_report(trial/'final-drc.json',board.name)
 assert (native['opens'],native['blocking'],native['warnings'],native['exclusions'])==(0,1,0,0) and not p.native_accepted(native) and any(x['type']=='starved_thermal' and x['severity']=='error' for x in native['findings'])
 assert p.sha(board)==oldrecord['candidate_sha256'] and p.sha(trial/'final-drc.json')==oldrecord['native_report_sha256'] and native==oldrecord['native']
 for name,saved in [('refill-drc',True),('final-drc',False)]:
  binding=f.read_json(trial/(name+'-binding.json'));f.check_drc_stage(trial,oldrecord,name,Path(binding['source']),Path(binding['input']),saved,binding['before'])
 spec=copy.deepcopy(spec0);spec.update(board=str(board),project_sha256=p.tree_hash(board.parent),refill_receipt=str(trial/'refill-drc-binding.json'),refill_receipt_sha256=p.sha(trial/'refill-drc-binding.json'))
 request=directory/'request.json';p.save_json(request,spec);out=directory/'components';before=p.tree_hash(board.parent)
 process=runner.run([*f.SANDBOX,str(c.PYTHON),str(w),'--request',str(request),'--output',str(out)],cwd=directory,log=directory/'worker.log',timeout=12,max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=2*1024**3);p.save_json(directory/'worker-process.json',process)
 hint=f.read_json(out/'result.json');assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and hint['status']=='diagnostic_completed' and hint['accepted'] is False and hint['routing_accepted'] is False
 bynet={}
 for group in hint['components']:bynet[group['net']]=bynet.get(group['net'],0)+1
 assert all(count==1 for count in bynet.values()) and p.tree_hash(board.parent)==before
 record['controls'].append(dict(case='thermal-counterexample',passed=True,native_interpreter_executed=True,old_native_drc_repeated=False,old_native_summary=str(old/'negative-summary.json'),old_native_summary_sha256=p.sha(old/'negative-summary.json'),native_report_sha256=p.sha(trial/'final-drc.json'),candidate_sha256=p.sha(board),native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},same_net_components=bynet,diagnostic_completed=True,candidate_accepted=False,process=process));stable()
 # Signal only our unreaped actual child after output creation, which follows
 # LoadBoard and the complete native pad census. No delay hook in the worker.
 directory,source,spec=prepare('actual-sigint');request=directory/'request.json';p.save_json(request,spec);out=directory/'components';before=p.tree_hash(source)
 argv=[*f.SANDBOX,str(c.PYTHON),str(w),'--request',str(request),'--output',str(out)];real=subprocess.Popen;watch=[];sent=[];errors=[]
 def capture(*args,**kwargs):
  child=real(*args,**kwargs)
  if list(args[0])==argv:
   def signal_owned():
    try:
     until=time.monotonic()+8
     while child.poll() is None and time.monotonic()<until:
      if out.is_dir():
       lineage=process_metadata(parent_pid=os.getpid());assert any(x['pid']==child.pid and x['pgid']==child.pid for x in lineage)
       if child.poll() is None:os.kill(child.pid,signal.SIGINT);sent.append({'pid':child.pid,'signal':'SIGINT','output_created_after_native_census':True})
       return
      time.sleep(.001)
    except BaseException as ex:errors.append(type(ex).__name__+': '+str(ex))
   thread=threading.Thread(target=signal_owned);watch.append(thread);thread.start()
  return child
 with patch.object(subprocess,'Popen',side_effect=capture):
  process=runner.run(argv,cwd=directory,log=directory/'worker.log',timeout=12,max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=2*1024**3)
 for thread in watch:thread.join(10);assert not thread.is_alive()
 p.save_json(directory/'worker-process.json',process)
 result=f.read_json(out/'result.json') if (out/'result.json').exists() else None
 assert len(sent)==1 and not errors and process['status']=='nonzero_exit' and process['exit_code']!=0 and process['cleanup_complete'] and (result is None or result['status']!='diagnostic_completed') and p.tree_hash(source)==before
 record['controls'].append(dict(case='actual-sigint',passed=True,signals=sent,watch_errors=errors,canonical_positive_survived=False,observed_status=None if result is None else result['status'],process=process));stable();record['passed']=True
except BaseException as ex:record.update(passed=False,error=type(ex).__name__+': '+str(ex))
finally:
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,material=f.evidence_inventory(O));
 if max(record['wall_seconds'],record['full_cpu_seconds'])+2>60:record.update(passed=False,error='Whole negative controls exceed60s')
 p.save_json(O/'result.json',record);lock.close()
print(json.dumps({k:record.get(k) for k in ('passed','wall_seconds','full_cpu_seconds','error')}));raise SystemExit(0 if record['passed'] else 2)
