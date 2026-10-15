from pathlib import Path
import sys,time,json,resource,cProfile,pstats,io,importlib.util
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
source=ROOT/'.runs/adaptive-native-controller-002.py';s=importlib.util.spec_from_file_location('pure_controller_profile',source);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=ROOT/'.runs/adaptive-incumbent-readback-profile-001';out.mkdir();rows=[]
with m.pure_reader_guard(audit=True):
 for name in ('arcdice-adaptive-001-native/C_adaptive/incumbent','arcdice-chain-native300-002/run/C_feedback/incumbent'):
  path=ROOT/'.runs'/name/'result.json';pin=p.sha(path);profile=cProfile.Profile();start=time.monotonic();cpu=time.process_time();profile.enable();result=p.check_result(path);profile.disable()
  row=dict(path=str(path),receipt_sha256=pin,current=result['current'],profiled_wall_seconds=time.monotonic()-start,profiled_parent_cpu_seconds=time.process_time()-cpu);assert p.sha(path)==pin
  stream=io.StringIO();pstats.Stats(profile,stream=stream).sort_stats('cumulative').print_stats(35);(out/(str(len(rows))+'.txt')).write_text(stream.getvalue());row['profile_summary_sha256']=p.sha(out/(str(len(rows))+'.txt'));rows.append(row)
(out/'result.json').write_text(json.dumps(dict(schema=1,passed=True,scope='Pure retained full-check diagnostic under profiler; instrumentation overhead included. No Native/engine/new route, no failure omitted. Development cost separate from frozen completed routing comparisons.',rows=rows),indent=2)+'\n');print(json.dumps(rows))
