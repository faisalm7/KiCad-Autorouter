"""Whole pure readback of fresh literal composite positive/Native negative."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,local_settings as ls,config as c
from experiments.literal_composite_controls_v1 import run as controls
OUT=ROOT/'.runs/literal-composite-native-controls-readback-001';OUT.mkdir();BASE=ROOT/'.runs/literal-composite-native-controls-001';EXE=ROOT/'.runs/literal-composite-native-controls-execution-001/execution.json'
tools=p.tool_manifest();material=pc.inventory(BASE,max_bytes=64*1024**2,max_files=3000,max_entries=6000,with_directories=True);epin=p.sha(EXE);pin=p.sha(ROOT/'experiments/literal_composite_controls_v1/run.py');result=dict(schema=1,passed=False,source_current=False,publication_allowance_seconds=2,new_native_execution=False,tools=tools)
try:
 data=f.read_json(BASE/'result.json');outer=f.read_json(EXE)
 assert outer['passed'] is True and outer['source_current'] is True and outer['actor_result_sha256']==p.sha(BASE/'result.json') and outer['tools']==tools
 result['checks']=controls.check(BASE,data)
 assert p.tool_manifest()==tools and p.sha(ROOT/'experiments/literal_composite_controls_v1/run.py')==pin and p.sha(EXE)==epin
 # Metadata replay follows final tool callbacks, preceding all byte witnesses.
 positive=f.read_json(BASE/'positive/result.json')
 for step in positive['steps']:
  argv=step['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
  if command[:3]==[str(c.CLI),'pcb','drc']:
   folder=Path(step['cwd']);name=step['name'];ls.check_event(folder,f.read_json(folder/(name+'-binding.json')),f.read_json(folder/(name+'-process.json')))
 folder=BASE/'negative';ls.check_event(folder,f.read_json(folder/'refill-drc-binding.json'),f.read_json(folder/'refill-drc-process.json'))
 assert pc.inventory(BASE,max_bytes=64*1024**2,max_files=3000,max_entries=6000,with_directories=True)==material
 result.update(passed=True,source_current=True,actor_result_sha256=p.sha(BASE/'result.json'),actor_execution_sha256=epin,actor_sha256=pin)
except BaseException as exc:result.update(reason=type(exc).__name__+': '+str(exc))
result.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,reader_sha256=p.sha(Path(__file__)))
result['passed']=result['passed'] and max(result['wall_seconds'],result['full_cpu_seconds'])+2<=30
p.save_json(OUT/'execution.json',result);print(json.dumps({k:result.get(k) for k in ('passed','source_current','wall_seconds','full_cpu_seconds','reason')}));raise SystemExit(0 if result['passed'] else 2)
