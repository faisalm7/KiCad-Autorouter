from pathlib import Path
import sys,time,json,importlib.util
START=time.monotonic();CPU0=time.process_time();R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx
s=importlib.util.spec_from_file_location('owned_proposal',Path(__file__).with_name('proposal.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
original=R/'.data/universal-shift-interface-demo-001/native-project/KiCad/Interface Board/USR_LED_Board.kicad_pcb';warm=R/'.runs/universal-shift-interface-native-paired300-002/run/C_feedback/incumbent/candidate/USR_LED_Board.kicad_pcb'
before={str(x):p.sha(x) for x in (original,warm)}
tree,proposal,protected,names,audit=m.deletion(sx.read(original),sx.read(warm))
result=dict(schema=1,kind='first-pure-own-C-whole-zone-proposal',new_native_execution=False,new_engine_execution=False,source_sha256=before,zone_names=names,deleted_route_count=len(proposal['route_ids']),protected_count=len(protected),remaining_route_count=len(p.routes(tree)),scope_audit=audit,original_geometry_exact=p.immutable(tree)==p.immutable(sx.read(original)),wall_seconds=time.monotonic()-START,full_cpu_seconds=time.process_time()-CPU0)
assert before=={str(x):p.sha(x) for x in (original,warm)}
out=Path(__file__).with_name('dry-proposal-result-001.json');assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('scope_audit','source_sha256')}))
