from pathlib import Path
import json,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
out=ROOT/'.runs/rule-area-cli-controls-001';out.mkdir(exist_ok=False)
source_root=ROOT/'.runs/placement-area-native-001/fixtures';before=p.tree_hash(source_root);tools=p.tool_manifest();rows=[];started=time.monotonic()
cases=[('native-route','track_prohibited','route',[]),('floor-route','via_prohibited','route',['--guidance','board-floors-v1','--adapter','both']),('recovery','mixed','recover',[]),('pruning','track_prohibited','improve',[])]
for name,case,command,flags in cases:
 args=[sys.executable,'-B','-m','autorouter',command,str(source_root/case/'fixture.kicad_pcb'),'--output',str(out/name),'--seconds','120',*flags]
 result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=15);(out/(name+'.stdout')).write_bytes(result.stdout);(out/(name+'.stderr')).write_bytes(result.stderr)
 receipt=json.loads((out/name/'result.json').read_text())
 assert result.returncode==2 and receipt['accepted'] is False and 'rule-area restrictions' in receipt['reason'] and receipt.get('steps',[])==[]
 assert p.tree_hash(source_root)==before and p.tool_manifest()==tools
 rows.append({'case':name,'argv':args,'exit_code':result.returncode,'receipt_sha256':p.sha(out/name/'result.json'),'status':receipt['status'],'reason':receipt['reason'],'native_or_engine_steps':0,'source_unchanged':True})
p.save_json(out/'summary.json',{'schema':1,'passed':True,'checks':rows,'source_before':before,'source_after':p.tree_hash(source_root),'tools':tools,'wall_seconds':time.monotonic()-started,'native_executed':False,'scope':'Real CLI rejection before native/engine; original native omitted violations retained separately.'})
print(json.dumps({'passed':True,'cli_cases':len(rows),'native_jobs':0,'out':str(out)}))
