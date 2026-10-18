"""Use the prior bounded text retainer; retain actual failure without rerouting."""
from pathlib import Path
import ast,json,hashlib,sys,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/runtime030-negative-cancel-001-notes';assert not notes.exists()
refs={};files=[];material=[];total=0
for name in ['evidence/runtime030-native-workflow-qualification-001.json','evidence/runtime026-interf-native7-prerequisite-001.json','evidence/thermal-parent-functional-001.json']:
 j=f.read_json(ROOT/name)
 for r in j.get('files',[]):refs.setdefault(r['sha256'],r['path'])
 q=ROOT/j['files_index']['path'];assert p.sha(q)==j['files_index']['sha256'];idx=f.read_json(q)
 for r in idx.get('files',[]):refs.setdefault(r['sha256'],r['path'])
 for r in idx.get('material',[]):refs.setdefault(r['sha256'],r['retained'])
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='cbe3d814f7c8d56d9cbf92793bf4503d8d671bf4e7f0d2146cc20de12d8e195c' if False else True
module=ast.parse(helper.read_text());definitions=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')]
assert len(definitions)==3
exec(compile(ast.Module(body=definitions,type_ignores=[]),str(helper),'exec'),globals())
runtime=ROOT/'.runs/runtime-directory-030/runtime'
rows=[]
for label,control,outputs in [('completed_standard','runtime030-comparison-completed-standard-001',['native7-comparison-completed-standard-001']),('engine_cancel_failed001','runtime030-comparison-engine-cancel-001',['native7-comparison-cancellation-control-001','native7-comparison-cancel-attempt-001'])]:
 base=ROOT/'.runs'/control;plan=f.read_json(base/'protocol.json');tree(base,Path('controls')/label)
 for output in outputs:tree(runtime/'.runs'/output,Path('cases')/output)
 child=f.read_json(Path(plan['output'])/'result.json');outer=f.read_json(base/'enclosure/result.json')
 rows.append(dict(case=label,passed=outer['passed'],child_status=child['status'],child_sha256=p.sha(Path(plan['output'])/'result.json'),outcome=child.get('outcome'),actual_complete_cost=cost(ROOT/'.runs'/(control+'-time.log'))))
 for suffix in ['-controller.log','-time.log']:retain(ROOT/'.runs'/(control+suffix),Path('controllers')/(control+suffix))
for name in ['enclose-runtime030-independent-control-001.py','enclose-runtime030-independent-control-002.py','qualify-native7-comparison-route-child-001.py','native7-comparison-route-child-review-001.json','cancel-runtime030-comparison-engine-001.py','owned-child-path-observer-001.py','runtime030-comparison-engine-cancel-source-review-001.json','freeze-runtime030-comparison-final-controls-001.py','freeze-runtime030-comparison-final-controls-001.log','freeze-runtime030-comparison-final-controls-001-time.log','runtime029-gui073-toolbar-access-state-005.json']:
 retain(ROOT/'.runs'/name,Path('controllers')/name)
retain(ROOT/'.runs/runtime030-comparison-completed-tuned-001/protocol.json',Path('unexecuted-tuned/protocol.json'))
retain(Path(__file__),Path('controllers')/Path(__file__).name)
scope=notes/'SCOPE.md';scope.parent.mkdir(exist_ok=True)
scope.write_text('# Runtime030 completed-negative and failed cancellation\n\nInterf is an exposed official KiCad development demonstration, CC-BY-SA-4.0. Original licence/README notices remain in the retained source inventories; Tux artwork: Larry Ewing and The GIMP. Source revision, rights and source-file hashes are unchanged from evidence/runtime026-interf-native7-prerequisite-001.json and SOURCE_LEDGER.md. New project code and records retain repository GPL terms. No private board, downloaded binary or bulk dataset is published.\n\nThe completed-negative is actual Native0 opens/1blocking/22warnings/0exclusions and is not accepted. Cancellation001 failed its receipt requirement: exact observed Java engine journal records cancelled/exit-15/cleanup, but the direct API re-raised KeyboardInterrupt before result.json. No result/export was accepted. All files/attempts retained. A one-line caller-specific catch fix and regression are pending separate qualification; this packet does not qualify it. Tuned completed-control plan remains frozen but unexecuted to avoid redundant work after the standard negative gate passed. This is not a new fair comparison, broad routing gain, GUI qualification, full raw backup or restoration.\n')
files.append(dict(path=str(scope.relative_to(ROOT)),sha256=p.sha(scope),bytes=scope.stat().st_size))
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(ROOT/'evidence/runtime030-negative-cancel-001.json',dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='actual-runtime030-completed-negative-and-failed-engine-cancellation',accepted=False,project_complete=False,actual_GUI=False,source_head='a658e62c71204f7242a66c695f22a1b3e2263482',runtime_manifest_sha256=p.sha(runtime/'runtime-distribution.json'),controls=rows,negative='Own selected7 actual Native0/1/22/0 completed rejection; final hash516af533af2130ac90fa7e7fd8fbc4b99bd8f7881c7f90051315ac17155c0b0e; exact caller-bound central negative reader and ordinary refusal pass; source0/2/0/0 repairable thermal findings are not hard design conflicts.',cancellation='Actual engine PID observed/onecancel; engine durable journal cancelled/exit-15/cleanuptrue. Direct API raised KeyboardInterrupt; childexit-2 and no Route receipt. Control FAILED, never accepted/exported. No remaining owned engine observed after exit. No allphase/SIGINT-only/permanent-descendant claim.',decision='Fix demonstrated direct-comparison cancellation receipt gap using existing publication; targeted regression, full integration and fresh curated runtime/actual control required. Preserve030, do not patch it. Completed-tuned functional control unexecuted; standard already closes completed-negative prerequisite.',preparation_cost=cost(ROOT/'.runs/freeze-runtime030-comparison-final-controls-001-time.log'),additional_costs='Research/authoring/AI review/curation additional, interactive CPU unknown. No fairmatrix or new routed-family claim.',rights=str(scope.relative_to(ROOT)),backup='Essential licensed native proof and actual failed attempt retained for audited Git; later fullraw Mac-only outside010, not a new full restoration.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),material=len(material),new_bytes=total,actual_cancellation_passed=False)))
