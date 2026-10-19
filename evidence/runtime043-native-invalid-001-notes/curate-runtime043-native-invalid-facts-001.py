"""Small additive record of existing invalid controls; no Native or admission replay."""
from pathlib import Path
from collections import Counter
import ast,json,sys,datetime,re,math
R=Path(__file__).resolve().parents[1];ROOT=R;sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
for filename,pin,names in [('.runs/curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',['cost']),('.runs/curate-runtime042-current-comparison-001.py','d6d99941d9afe8d6a81e862d406d66b72f39fdf1c5241dc6cb7403154a61d974',['complete_cost'])]:
 path=R/filename;assert p.sha(path)==pin;defs=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names];exec(compile(ast.Module(body=defs,type_ignores=[]),str(path),'exec'),globals())
base=R/'.runs/runtime043-ordinary-native-invalid-001';outer=f.read_json(base/'enclosure/result.json');plan=f.read_json(base/'protocol.json');childpath=Path(outer['child_receipt']);child=f.read_json(childpath)
assert p.sha(base/'protocol.json')==outer['protocol_sha256']==child['protocol_sha256']=='9865a023bda86d47b1aa8becae7bbd0b9965cef52c242210e62817bea8c20d5d'
assert p.sha(childpath)==outer['child_sha256'] and outer['passed'] and child['control_passed'] and child['status']=='completed'
assert child['source_head']=='6ec7ad2344ed060d5e0971965ef05bd9de68925d' and child['runtime_manifest_sha256']=='6fdfe60bcbe6aecc2c950a6917b22d8e591f5ae3078eca5a52ae051a1aac5aa3'
assert child['accepted'] is False and child['production_admitted'] is False and io.inventory(Path(child['source']).parent)==child['source_hashes']
assert outer['process']['cleanup_complete'] and not outer['process']['log_truncated'] and outer['process']['exit_code']==0
rows=[]
for c in child['cases']:
 assert c['control_observed'] and c['accepted'] is False and c['routing_accepted'] is False
 assert p.sha(Path(c['candidate']))==c['candidate_sha256']
 reports=[Path(step['argv'][step['argv'].index('--output')+1]) for step in c['steps'] if '--output' in step['argv']]
 matching=[q for q in reports if p.sha(q)==c['native_report_sha256']];assert len(matching)==1
 raw=f.read_json(matching[0]);assert raw['kicad_version']=='10.0.7'
 assert all(s['cleanup_complete'] and not s['log_truncated'] for s in c['steps'])
 rows.append({k:c.get(k) for k in ['label','control_observed','accepted','routing_accepted','protected_routes','before_candidate_sha256','candidate_sha256','native_report_sha256','rejection','Native_diagnostic_routing_accepted','no_additional_native_after_invariant_refusal']})
 rows[-1].update(Native_counts=[c['native'][k] for k in ['opens','blocking','warnings','exclusions']],ignored_checks=c['native']['ignored_checks'],finding_types=dict(Counter(v['type'] for v in c['native']['findings'])),actual_report=str(matching[0]))
assert [x['Native_counts'] for x in rows]==[[0,4,0,0],[0,0,0,0]] and rows[1]['no_additional_native_after_invariant_refusal']
notes=R/'evidence/runtime043-native-invalid-001-notes';output=R/'evidence/runtime043-native-invalid-001.json';assert not notes.exists() and not output.exists();notes.mkdir();files=[]
paths=[Path(__file__),*[base/n for n in ['protocol.json','outer.log','outer-time.log','enclosure/result.json','enclosure/process.json','enclosure/command.log','tools-defaults.json','tools-defaults-process.json']],R/'.runs/qualify-runtime043-ordinary-native-invalid-001.py',R/'.runs/freeze-runtime043-ordinary-native-invalid-001.py',R/'.runs/freeze-runtime043-ordinary-native-invalid-001.log',R/'.runs/freeze-runtime043-ordinary-native-invalid-001-time.log']
for path in paths:
 raw=io.read_bytes(path,4*1024**2);raw.decode();assert b'\0' not in raw;target=notes/Path(*path.relative_to(R).parts[1:]);target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as stream:stream.write(raw)
 files.append({'source':str(path.relative_to(R)),'path':str(target.relative_to(R)),'sha256':p.sha(path),'bytes':len(raw)})
p.save_json(output,{'schema':1,'kind':'runtime043-actual-short-and-protected-width-invalid-facts-v1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'accepted':False,'project_complete':False,'actual_GUI':False,'human_review':False,'control_passed':True,'source_head':child['source_head'],'runtime_manifest_sha256':child['runtime_manifest_sha256'],'source_hashes':child['source_hashes'],'source_unchanged':True,'child_sha256':p.sha(childpath),'cases':rows,'complete_cost':complete_cost(base/'outer-time.log'),'files':files,'scope':'Two actual pinned7invalidcontrols using unchanged shared validator: addedshort has4blocking; protectedwidth+1nm is Nativeclean but original/protected guard refuses. No populationfalseacceptance/electrical claim. Current GUI pending. RawretainedMac-only/outside010; metadata is not fullrawbackup.'})
print(json.dumps({'control_passed':True,'cases':[x['Native_counts'] for x in rows],'files':len(files)}))
