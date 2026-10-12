"""Run the exact production stable closure with real files and fake metadata/checker."""
import ast,copy,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref,floor_route as f
HERE=Path(__file__).resolve().parent;OUT=HERE/sys.argv[1];OUT.mkdir(exist_ok=False)
raw=(ROOT/'autorouter/floor_route.py').read_bytes();tree=ast.parse(raw)
route=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_route')
node=next(n for n in route.body if isinstance(n,ast.FunctionDef) and n.name=='stable')
module=ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]))
rows=[]
for name,mutate in [('unchanged',False),('late_metadata_preset',True)]:
    work=OUT/name;work.mkdir();source=work/'source';source.mkdir();(source/'board.txt').write_text('immutable')
    out=work/'run';out.mkdir();(out/'snapshot').mkdir();(out/'snapshot/board.txt').write_text('immutable')
    preset=work/'preset.json';preset.write_text(json.dumps(dict(pref.DEFAULTS)))
    captured=pref.load(preset);request={'captured':captured,'snapshot':pref.snapshot(captured),'effective':pref.resolve(captured)}
    report={'accepted':True,'status':'routing_accepted','tools':{'fake':'metadata'}};p.capture_preferences(report,out,request)
    completed=f.evidence_inventory(out);calls=[]
    namespace=dict(f.__dict__);namespace.update(output=out,source=source/'board.txt',preferences=request,frozen=True,new_policy=False,hashes=p.tree_hash(source),report=report,completed=completed)
    exec(compile(module,'<exact-current-floor-stable>','exec'),namespace)
    def metadata():
        calls.append(len(calls)+1)
        if mutate and len(calls)==3:preset.write_text(json.dumps(dict(pref.DEFAULTS,seconds=60)))
        return {'fake':'metadata'}
    with patch.object(p,'tool_manifest',metadata),patch.object(p,'check_result',return_value={'current':True}):
        result=f.publish(out,report,namespace['stable'],lambda:None,lambda:120)
    canonical=json.loads((out/'result.json').read_text()) if (out/'result.json').is_file() else None
    row={'case':name,'metadata_calls':len(calls),'preset_changed':preset.read_bytes()!=captured.raw,'returned_accepted':result['accepted'],'canonical_accepted':canonical['accepted'] if canonical else None,'status':result['status']};rows.append(row)
(OUT/'results.json').write_text(json.dumps({'scope':'Exact stable closure + actual floor.publish; native/checker/metadata mocked; no native inference','source_sha256':hashlib.sha256(raw).hexdigest(),'cases':rows},indent=2)+'\n');print(json.dumps(rows,indent=2))
