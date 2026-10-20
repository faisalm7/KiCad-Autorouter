"""Retain new GUI086 observations with existing bounded retention/own-final helpers.

Metadata only. Earlier deliveries remain in the immutable progress packet;
no Native solve, production acceptance reader, CAD copy or GUI action runs here.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/gui-runtime050-086-controls-delta-001-notes';target=ROOT/'evidence/gui-runtime050-086-controls-delta-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
for name,pin,names in (
 ('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',('retain',)),
 ('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',('read','own_final'))):
 helper=ROOT/'.runs'/name;assert p.sha(helper)==pin
 nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
dependency=ROOT/'evidence/gui-runtime050-086-progress-001.json';assert p.sha(dependency)=='410d4cda4ce143da61296650df73c20637db7acef4a7ef4f9bea20cf2e57f127'
index=read(dependency)['files_index'];assert p.sha(ROOT/index['path'])==index['sha256']
for row in read(ROOT/index['path'])['files']:refs.setdefault(row['sha256'],row['path'])
runtime=ROOT/'.runs/runtime-directory-050/runtime';base=runtime/'.runs/gui-session086';jobs=base/'jobs'
prepared=read(base/'prepared-state.json');assert p.sha(base/'prepared-state.json')=='59243bac41824b5efa2a336a53d3ff59bd6d725bf61a9686d3315575fe74a7ae'
assert p.sha(runtime/'runtime-distribution.json')==prepared['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
for name,pin in prepared['tools']['implementation_sha256'].items():assert p.sha(runtime/name)==pin
for role in prepared['roles'].values():assert io.inventory(Path(role['source']).parent)==io.inventory(Path(role['original_source']).parent)==role['source_hashes']
j4=ROOT/'.runs/gui086-observations-004.json';j5=ROOT/'.runs/gui086-observations-005.json'
assert p.sha(j4)=='10d7f7db401f9247d47d00bf30e985bbd5ac3c92fcfdbf5b13266c05977ff126' and p.sha(j5)=='f681f4b391957f28918ab78feb1dbf56062d70dac6f334a073a54c29bbd5892d'
four=read(j4);five=read(j5);assert five['previous']['sha256']==p.sha(j4)
post=base/'preopen-improve-001/postopen-001.json';assert p.sha(post)==four['improve']['postopen_sha256']=='3053260db57144dbc9186d46f9ec8ca6fd500bfe257c9a076611338720299d06'
after=read(post);assert after['actual_GUI_opened'] and after['actual_PCB_inspected'] and after['candidate_PCB_unchanged']
assert io.inventory(Path(after['workspace'])/'export',max_bytes=64*1024**2)==after['current_export_inventory']
reject=Path(five['rejection']['workspace']);route=read(reject/'route/result.json');choice=read(reject/'choice/choice.json')
assert choice['choice']=='reject' and choice['choice_recorded'] and choice['applied'] is False and not (reject/'export').exists()
assert choice['receipt_sha256']==p.sha(reject/'route/result.json')==five['rejection']['route_sha256']
assert route['accepted'] and route['invariants_unchanged'] and [route['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
assert read(reject/'route/final-netclass-audit.json')['route_dimensions']['checked']['protected']==4
own=own_final(route,reject/'route',reject/'route',prepared['roles']['ordinary-alias2Cu']['source_hashes'],Path(route['candidate']))
cancel=Path(four['cancel']['workspace']);cp=read(cancel/'route.command.process.json');cr=read(cancel/'route/result.json')
assert cp['cancel_requested'] and cp['exit_code']==2 and cr['status']=='cancelled' and cr['accepted'] is False
for name,item in five['freshness'].items():
 w=Path(item['workspace']);assert not (w/'route').exists() and not (w/'route.command.process.json').exists()
 assert p.sha(base/'freshness-controls-001'/(name+'-mutation.json'))==item['mutation_sha256']
queue={}
def add(path,name):queue.setdefault(Path(path),Path(name))
for path in (j4,j5,post,ROOT/'.runs/gui086-journal005-first-failure-001.json',ROOT/'.runs/retain-gui086-controls-delta-001.py',ROOT/'.runs/retain-gui086-controls-delta-001.log',ROOT/'.runs/retain-gui086-controls-delta-001-time.log',Path(__file__)):
 add(path,Path('controls')/path.name)
controls=base/'freshness-controls-001'
for name in ('protocol.json','settings-before.json','settings-mutation.json','source-mutation.json'):add(controls/name,Path('controls/freshness')/name)
work_names=('autorouter-gui-d6bd0fb8267e4db0b7098f95ad054342','autorouter-gui-6a4c70156917463bbc708ff708b8fbdd','autorouter-gui-925f3839fe194c999f92d3b139e300fe','autorouter-gui-03e2dbcc539346f5bc5df4e181231fd3','autorouter-gui-9c2eb3ccd71349dabc22b6af62214684','autorouter-gui-672dd31235a4463b90f75ce4a9baf26d')
samples=[];sealed={}
for name in work_names:
 w=jobs/name;inventory=io.inventory(w,max_bytes=64*1024**2,max_files=8000,max_entries=16000);sealed[w]=inventory
 for rel in inventory:
  path=w/rel;parts=Path(rel).parts
  if len(parts)==1 and path.suffix in ('.json','.log') or len(parts)==2 and parts[0] in ('route','choice','review') and path.suffix in ('.json','.log','.net') or len(parts)==3 and parts[0]=='route' and parts[1] in ('final-drc-input','refill-drc-input','source-drc-input') and path.suffix=='.kicad_prl':add(path,Path('jobs')/name/rel)
 for path in sorted(w.glob('*.command.process.json')):
  proc=read(path);assert proc['log_truncated'] is False
  samples.append(dict(workspace=name,command=path.name,exit_code=proc['exit_code'],cancel_requested=proc['cancel_requested'],wall_seconds=proc['wall_seconds'],sha256=p.sha(path)))
improve=Path(after['workspace'])
for name in after['checked_open_processes']:
 path=improve/name;add(path,Path('improve-checked-open')/name);add(path.with_name(name.replace('.process.json','.log')),Path('improve-checked-open')/name.replace('.process.json','.log'))
assert sum(path.stat().st_size for path in queue)<12*1024**2 and len(queue)<2000
for path,name in queue.items():retain(path,name)
assert all(io.inventory(path,max_bytes=64*1024**2,max_files=8000,max_entries=16000)==inv for path,inv in sealed.items())
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime050-GUI086-checked-opening-and-controls-delta-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=prepared['source_head'],runtime_manifest_sha256=prepared['runtime_manifest_sha256'],actual_GUI=True,full_GUI_qualified=False,project_complete=False,human_review=False,dependency=dict(path=str(dependency.relative_to(ROOT)),sha256=p.sha(dependency)),observations=[four,five],rejected_candidate_own_final=own,CLI_process_wall_samples=samples,observed='Previously completed Improve export opened in actual KiCad:6pads/0vias/2segments/3nets/0unrouted; all6warnings restored. Current actual cancellation, fresh successful recovery route, explicit rejection/export disabled, displayed-settings invalidation and captured-settings/source-copy stale-byte refusals observed. Original sources unchanged. Editor changes confined to exportPRO/PRL/newbackupZIP; pre-editor proof preserved.',limits='Exact queuedCallAfter interval unproved by these before-action changes. Engine exited0 before Cancel landed; no current Java-interruption claim. Additional Native stages/Improve cancellation/naturalexpiry/otherplatforms/breadth/human/electrical not inferred. Individual CLI wall samples overlap method samples; whole interactive CPU/wall and authoring/AI review unknown additional, notzero. No new Native/readers by curator.',backup='Owned metadata only. CAD/plots/ZIP and newer unique raw remain Mac-only outside010; no new restoration claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total)))
