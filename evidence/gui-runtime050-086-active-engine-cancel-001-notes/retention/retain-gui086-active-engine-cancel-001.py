"""Hash-only foreign-source GUI cancellation retention; no worker/readers run."""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as io
notes=ROOT/'evidence/gui-runtime050-086-active-engine-cancel-001-notes'
target=ROOT/'evidence/gui-runtime050-086-active-engine-cancel-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
def read(path):return json.loads(io.read_bytes(path,4*1024**2))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
assert len(nodes)==2;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
dependency=ROOT/'evidence/gui-runtime050-086-controls-delta-001.json'
assert p.sha(dependency)=='80940009bf2cfaea006358b4525bcc31d14b431d1b37588a531cec53c1f109ca'
index=read(dependency)['files_index'];assert p.sha(ROOT/index['path'])==index['sha256']
for row in read(ROOT/index['path'])['files']:refs.setdefault(row['sha256'],row['path'])
runtime=ROOT/'.runs/runtime-directory-050/runtime';base=runtime/'.runs/gui-session086/cancel-engine-controls-001'
protocol=read(base/'protocol.json');prepared=read(base/'prepared-state.json');observed=read(base/'observed-active-001.json');result=read(base/'result.json')
assert p.sha(base/'result.json')=='261ea0dc3cc7f23dbf40bb6318a668052ff146adc2be78f56a3f484a22a02e09'
assert p.sha(base/'protocol.json')==prepared['protocol_sha256']==result['protocol_sha256']=='3a3b619aacc68900b8dd1d3395c10ec09649509d8050a2dd3d42ec7403bebaf0'
assert p.sha(base/'prepared-state.json')==result['prepared_sha256']=='57d00bf30d557e07325c5dec0e7e85b89b4c63dfc79d72e35aa16ac775b142e5'
assert p.sha(base/'observed-active-001.json')==result['active_before_Cancel_sha256']=='b65705ddc98ccb821ad935f0037238d741b84fc0beeaec8f759289c144555116'
assert protocol['source_head']=='aa0072c6b3d8090de2603e5ecb42a95968fb873b'
assert p.sha(runtime/'runtime-distribution.json')==protocol['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
w=runtime/'.runs/gui-session086/jobs/autorouter-gui-8b87139985c146729fcd08f43f745655'
assert result['workspace']==prepared['workspace']==str(w) and observed['workspace']==w.name
assert protocol['attempts']==1 and prepared['actual_GUI_preview'] is True
assert observed['actual_before_GUI_Cancel'] is True and observed['signals_sent_by_observer'] is False
assert result['GUI_Cancel_observed'] is True and result['GUI_positive_actions_disabled'] is True
assert result['accepted'] is False and result['full_GUI_qualified'] is False and result['project_complete'] is False
assert result['Native_final_counts'] is None and result['no_choice_review_export'] is True and result['owned_survivors']==[]
assert result['originals_unchanged'] is True and result['settings_unchanged'] is True
hashes=protocol['source_hashes'];source=Path(protocol['source']);original=Path(protocol['original_source'])
assert io.inventory(source.parent)==io.inventory(original.parent)==io.inventory(base/'pristine')==hashes==prepared['source_hashes']==result['source_hashes']
assert p.sha(w/'settings.json')==prepared['settings_sha256'] and read(w/'settings.json')==protocol['settings']
assert protocol['settings']==dict(schema=1,scope='whole_board_unlocked_routing',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
assert p.sha(w/'preview.command.process.json')==prepared['preview_process_sha256']
route_path=w/'route/result.json';route=read(route_path);CLI=read(w/'route.command.process.json');engine=read(w/'route/engine-process.json')
assert p.sha(route_path)==result['route']['sha256']=='7c6bb90128209487c1222b9d15acc535165f06068cdf654126cf4451a8afd079'
assert p.sha(w/'route.command.process.json')==result['CLI']['sha256'] and p.sha(w/'route/engine-process.json')==result['engine']['sha256']
assert route['status']==result['route']['status']=='cancelled' and route['accepted'] is False
assert route['source']==str(source) and route['source_hashes']==hashes and route['schematic_parity']=='not checked'
assert 'native' not in route and 'candidate' not in route and route['whole_project_drc_clean'] is False
assert CLI['cancel_requested'] is True and CLI['exit_code']==2 and CLI['log_truncated'] is False
assert CLI['wall_seconds']==result['CLI']['wall_seconds']
assert CLI['argv']==[str(runtime/'.venv/bin/python'),'-B','-m','autorouter','route',str(source),'--settings',str(w/'settings.json'),'--output',str(w/'route')]
assert engine['pid']==result['engine']['pid']==18135 and engine['status']=='cancelled' and engine['exit_code']==-9
assert engine['cleanup_complete'] is True and engine['log_truncated'] is False and Path(engine['cwd'])==w/'route'
assert all(engine[key]==result['engine'][key] for key in ('status','exit_code','cleanup_complete','wall_seconds','cpu_seconds'))
assert engine['argv'][-4:]==['-de',str(w/'route/task.dsn'),'-do',str(w/'route/routes.ses')]
assert len(observed['observed_process_rows'])==2 and observed['observed_process_rows'][1].split()[:2]==['18135','18131']
assert all(str(w) in row for row in observed['observed_process_rows'])
assert observed['observed_process_rows'][0].split()[:2]==['18131','8056']
assert [step['name'] for step in route['steps']]==['source-drc','export','obstacles','engine']
assert next(step for step in route['steps'] if step['name']=='engine')==engine
for name in ('choice','review','export'):assert not (w/name).exists()
assert not (w/'route/final-drc.json').exists() and not (w/'route/import-process.json').exists()
source_process=read(w/'route/source-drc-process.json');binding=read(w/'route/source-drc-binding.json')
assert source_process['exit_code']==5 and source_process['cleanup_complete'] is True and source_process['log_truncated'] is False
assert binding['before']==hashes and binding['saved'] is False
assert io.inventory(w/'route/source-drc-input')==binding['after']
for name,pin in route['tools']['implementation_sha256'].items():assert p.sha(runtime/name)==pin
source_counts={key:route['source_drc'][key] for key in ('opens','blocking','warnings','exclusions')}
queue={}
def add(path,name):queue.setdefault(Path(path),Path(name))
for path in (Path(__file__),helper):add(path,Path('retention')/path.name)
for name in ('protocol.json','prepared-state.json','observed-active-001.json','result.json'):add(base/name,Path('observations')/name)
for name in ('settings.json','preview.command.process.json','route.command.process.json','route/engine-process.json','route/source-drc-process.json','route/source-drc-binding.json'):
 add(w/name,Path('job')/name)
# The raw Route receipt includes foreign-source findings; retain its SHA only.
assert all(path!=route_path and path.suffix not in ('.kicad_pcb','.dsn','.ses','.svg','.zip','.net') for path in queue)
assert len(queue)<2000 and sum(path.stat().st_size for path in queue)<16*1024**2
sealed={path:p.sha(path) for path in queue}
for path,name in queue.items():retain(path,name)
assert all(p.sha(path)==pin for path,pin in sealed.items()) and p.sha(route_path)==result['route']['sha256']
assert io.inventory(source.parent)==io.inventory(original.parent)==hashes and p.sha(w/'settings.json')==prepared['settings_sha256']
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime050-GUI086-observed-active-Java-cancellation-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_GUI=True,accepted=False,production_admitted=False,workflow_delivered=False,project_complete=False,full_GUI_qualified=False,human_review=False,Native_final_counts=None,source_head=protocol['source_head'],runtime_manifest_sha256=protocol['runtime_manifest_sha256'],dependency=dict(path=str(dependency.relative_to(ROOT)),sha256=p.sha(dependency)),observation=result,raw_route_receipt=dict(sha256=p.sha(route_path),bytes=route_path.stat().st_size,retained=False,reason='Contains foreign-source raw findings; local hash-only evidence'),original_source_Native_counts=source_counts,source_findings_scope='Original source warnings/conflicts are not waived; source DRC precedes engine and is not a final candidate validation. Raw source findings/geometry and engine log are not copied.',accounting=dict(CLI_wall_seconds=CLI['wall_seconds'],engine_wall_seconds=engine['wall_seconds'],engine_CPU_seconds=engine['cpu_seconds'],route_nested_sample=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),limits='CLI/Route/engine samples overlap and are not added. Whole interactive wall/CPU, preparation/authoring/AI review unknown additional, notzero. Curator complete exit measured separately.'),review=dict(kind='AI static metadata/hash readback, not human PCB or independent generator-source review',new_workers_or_acceptance_readers=False,current_source_and_copy_and_pristine_unchanged=True,positive_UI_not_adopted=True,owned_survivors='Lead observed none in the frozen result; no new process inventory by curator'),limits='One actual Cancel after exact owned Java observed active. No Native final counts, delivery, natural expiry, all-phase cancellation, Improve, queued-CallAfter, allGUI, routing-quality, electrical or physical claim. Current050 runtime is unchanged by later root-only experimental writer fixes.',backup='Foreign source/CAD/DSN/SES/plots/Native source raw findings/engine log remain local outside010. Metadata and hashes are not full raw backup or restored evidence.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,material=len(material),Native_final_counts=None,active_Java_Cancel_observed=True)))
