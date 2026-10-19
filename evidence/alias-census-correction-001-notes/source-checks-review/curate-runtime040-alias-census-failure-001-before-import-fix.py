"""Retain actual040 failed Native qualification; never rerun or relabel it."""
from pathlib import Path
import ast,datetime,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/runtime040-alias-census-failure-001-notes';output=ROOT/'evidence/runtime040-alias-census-failure-001.json';assert not notes.exists() and not output.exists()
refs={};files=[];material=[];total=0;dependencies=[]
for name in ('runtime039-native-floor-schema-milestone-001','source-all-layer-identity-correction-001'):
 q=ROOT/'evidence'/(name+'.json');d=json.loads(q.read_bytes());index=d['files_index'];assert p.sha(ROOT/index['path'])==index['sha256'];idx=json.loads((ROOT/index['path']).read_bytes())
 for row in idx['files']+idx.get('material',[]):refs.setdefault(row['sha256'],row.get('retained',row.get('path')))
 dependencies.append(dict(path=str(q.relative_to(ROOT)),sha256=p.sha(q),files_index=index))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')];exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'),globals())
runtime=ROOT/'.runs/runtime-directory-040/runtime';base=ROOT/'.runs/runtime040-ordinary-alias2Cu-003';plan=json.loads((base/'protocol.json').read_bytes());out=Path(plan['output']);workflow=json.loads((out/'result.json').read_bytes());work=Path(workflow['workspace']);route=json.loads((work/'route/result.json').read_bytes())
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']=='079bd29a8b00fcb53aa1b4a663630e7f06906e329cd8485ae11e27f35d91d7b9'
assert plan['source_head']=='e5593ae129e88c719c9066d0464edb6aba0df487'
assert workflow['workflow_delivered'] is False and route['accepted'] is False and route['status']=='invalidated'
assert route['reason']=='Rejected: Native alias source copper layers differ'
assert [route['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
assert [v['name'] for v in route['steps']]==['source-drc','export','obstacles','engine','import','refill-drc','final-netclasses','final-drc','metrics']
assert all(s['status']=='success' and s['exit_code']==0 and s['cleanup_complete'] is True and not s['log_truncated'] for s in route['steps'][1:])
assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']==workflow['source_hashes']==route['source_hashes']
assert not any((work/name).exists() for name in ('review','choice','export'))
for case in ('full-integration-185','install-distribution-native-013'):
 d=json.loads((ROOT/'.runs'/case/'execution.json').read_bytes());assert d['passed'] is True;tree(ROOT/'.runs'/case,Path(case))
 for suffix in ('-time.log','-controller.log'):retain(ROOT/'.runs'/(case+suffix),Path('controllers')/(case+suffix))
retain(runtime/'runtime-distribution.json',Path('runtime/runtime-distribution.json'));retain(runtime.parent/'result.json',Path('installation/result.json'))
install=json.loads((runtime.parent/'result.json').read_bytes())
for row in install['commands']:retain(Path(row['log']),Path('installation/logs')/Path(row['log']).name)
tree(runtime/'.runs/install-native-smoke',Path('installation/native-smoke'));tree(runtime.parent/'source-fixture',Path('installation/source-fixture'))
for case in ('runtime040-ordinary-alias2Cu-001','runtime040-ordinary-alias2Cu-002','runtime040-ordinary-alias2Cu-003'):
 tree(ROOT/'.runs'/case,Path('attempts')/case)
 for suffix in ('-time.log','-controller.log'):retain(ROOT/'.runs'/(case+suffix),Path('controllers')/(case+suffix))
tree(out,Path('actual-alias-failure'));tree(Path(plan['source']).parent,Path('unchanged-owned-source'))
for case in ('hierarchy-whole2Cu','whole4Cu','partial2Cu','floor-2Cu','floor-4Cu'):
 tree(ROOT/'.runs'/('runtime040-ordinary-'+case+'-001'),Path('frozen-NOTRUN')/case)
for name in ('run-full-integration-185.py','full-suite-local-root-019.py','run-install-distribution-native-013.py','freeze-install013-001.py','freeze-runtime040-workflow-plans-001.py','freeze-runtime040-workflow-plans-001.log','runtime040-alias-invocation-failures-001.json','native7-source-all-alias-correction-plan-amendment-002.json'):
 retain(ROOT/'.runs'/name,Path('controllers')/name)
retain(ROOT/'.runs/native7-source-all-alias-controls-001/fixture-preparation.json',Path('controls/fixture-preparation.json'));retain(Path(__file__),Path('curation')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='runtime040-alias-census-failed-integration-milestone',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,actual_GUI=False,human_review=False,source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],full185=dict(passed=True,tests=2311,skips=1,cost=cost(ROOT/'.runs/full-integration-185-time.log')),install013=dict(passed=True,cost=cost(ROOT/'.runs/install-distribution-native-013-time.log')),actual_alias003=dict(passed=False,accepted=False,route_status=route['status'],reason=route['reason'],Native_counts=[0,0,0,0],candidate_sha256=route['candidate_sha256'],final_Native_performed=True,route_receipt_sha256=p.sha(work/'route/result.json'),workflow_sha256=p.sha(out/'result.json'),cost=cost(ROOT/'.runs/runtime040-ordinary-alias2Cu-003-time.log')),pre_Native_failures=[dict(attempt='001',cost=cost(ROOT/'.runs/runtime040-ordinary-alias2Cu-001-time.log'),reason='Relative settings path after child cwd change; empty output created before refusal.'),dict(attempt='002',cost=cost(ROOT/'.runs/runtime040-ordinary-alias2Cu-002-time.log'),reason='Preparation assertion incorrectly required absent rather than empty001 output. Then missing protocol refusal before child.')],unexecuted='Five frozen040 canonical/floor/hierarchy protocols, actual invalid040, Sonde040 and GUI040 NOTRUN after real alias failure. No NUS rerun.',scope='Actual new source-all getters/DSN/engine/import/refill/final fullSCH Native0all performed, but final padless-reference observation census invalidates. NO accepted Route/review/choice/export. Frozen original aliases/both sides/protected via and all source hashes unchanged; this failed control is not a routing gain or retroactive pass.',decision='One bounded general source/display census correction authorized by recorded amendment002; keep all original/protected/same-load/restoration/hash checks and NUS/type/mask/class refusals. Changed candidate requires its own fresh native qualification.',accounting='Complete external samples retained once; internal steps nested, not additional. Preparation/research/authoring/AI review/curation additional or unknown, never zero.',rights='Owned functional fixture/runtime/source/test logs under project GPL with inherited demo-settings provenance retained by exact prior039 reference; no private/NUS payload or downloaded engines/apps/venvs published.',dependencies=dependencies,files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(output,record);print(json.dumps(dict(files=len(files),bytes=total,material=len(material),packet_sha256=p.sha(output))))
