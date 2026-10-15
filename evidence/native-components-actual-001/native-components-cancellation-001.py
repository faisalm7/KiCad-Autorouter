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
O=R/'.runs/native-components-cancellation-001';O.mkdir();parent=R/'.runs/native-components-controls-001';w=R/'experiments/native_components_v1/worker.py';tools=p.tool_manifest()
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
