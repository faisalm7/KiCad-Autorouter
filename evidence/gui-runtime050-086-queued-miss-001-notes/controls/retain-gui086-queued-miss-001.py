"""Retain the one missed menu interval and its completed own Native proofs.

Static receipt/hash readback only: no acceptance reader, Native worker or GUI.
CAD, plot and ZIP bytes stay local; this is not a queued-freshness pass.
"""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as io
notes=ROOT/'evidence/gui-runtime050-086-queued-miss-001-notes'
target=ROOT/'evidence/gui-runtime050-086-queued-miss-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helpers=[]
for name,pin,names in (
 ('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',('retain','cost')),
 ('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',('read','own_final'))):
 helper=ROOT/'.runs'/name;assert p.sha(helper)==pin;helpers.append(helper)
 nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
dependencies=[]
for name,pin in (
 ('gui-runtime050-086-progress-001.json','410d4cda4ce143da61296650df73c20637db7acef4a7ef4f9bea20cf2e57f127'),
 ('gui-runtime050-086-controls-delta-001.json','80940009bf2cfaea006358b4525bcc31d14b431d1b37588a531cec53c1f109ca')):
 dependency=ROOT/'evidence'/name;assert p.sha(dependency)==pin
 index=read(dependency)['files_index'];assert p.sha(ROOT/index['path'])==index['sha256']
 for row in read(ROOT/index['path'])['files']:refs.setdefault(row['sha256'],row['path'])
 dependencies.append(dict(path=str(dependency.relative_to(ROOT)),sha256=pin,files_index=index))
runtime=ROOT/'.runs/runtime-directory-050/runtime';base=runtime/'.runs/gui-session086'
w=base/'jobs/autorouter-gui-672dd31235a4463b90f75ce4a9baf26d'
prepared_path=base/'prepared-state.json';prepared=read(prepared_path)
assert p.sha(prepared_path)=='59243bac41824b5efa2a336a53d3ff59bd6d725bf61a9686d3315575fe74a7ae'
assert prepared['source_head']=='aa0072c6b3d8090de2603e5ecb42a95968fb873b'
assert p.sha(runtime/'runtime-distribution.json')==prepared['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
for name,pin in prepared['tools']['implementation_sha256'].items():assert p.sha(runtime/name)==pin
for role in prepared['roles'].values():
 assert io.inventory(Path(role['source']).parent)==io.inventory(Path(role['original_source']).parent)==role['source_hashes']
control=base/'queued-open-controls-001';protocol=read(control/'protocol.json');observed=read(control/'result.json')
assert p.sha(control/'result.json')=='d68a4646617d94e783c9d1d6f54482829093e026c2c5a39658105b7771071448'
assert p.sha(control/'protocol.json')==observed['protocol_sha256']=='c5822457ad8283df3466467d1095b772e537f4e7e38f6a08d1ef9dd7e1c27901'
assert observed['workspace']==protocol['existing_fresh_preview']==str(w)
assert observed['outcome']=='MISSED_INTERVAL_NOT_A_FRESHNESS_PASS' and observed['mutation_performed'] is False
assert observed['actual_ordinary_Route_review_explicit_accept_export'] is True
assert observed['actual_Open_checked_export_and_native_context_menu'] is True
assert observed['source_settings_and_candidate_PCB_unchanged'] is True
assert all(value is True for value in observed['originals_unchanged'].values())
assert observed['post_open_export_changes']=={}
role=prepared['roles']['ordinary-alias2Cu'];hashes=role['source_hashes']
assert protocol['source']==role['source'] and protocol['source_hashes']==hashes
assert protocol['source_head']==prepared['source_head'] and protocol['runtime_manifest_sha256']==prepared['runtime_manifest_sha256']
assert p.sha(w/'settings.json')==protocol['settings_sha256']
assert p.sha(w/'preview.command.process.json')==protocol['preview_process_sha256']
pre_path=base/'preopen-boundary-settings-001/preopen.json';pre=read(pre_path);snapshot=pre_path.parent/'export'
assert p.sha(pre_path)==observed['preopen_sha256']=='742139261026219fff609ecc3779f85bfd065a625d82494606734c96d2f3abd0'
assert pre['workspace']==str(w) and pre['source_hashes']==hashes and pre['source_unchanged'] is True
assert pre['settings_sha256']==protocol['settings_sha256'] and pre['export']['current'] is True
assert pre['route']['current'] is True and pre['export']['export_accepted'] is True
assert pre['actual_GUI_opening'] is False and str(snapshot)==pre['snapshot']
export_inventory=io.inventory(snapshot,max_bytes=64*1024**2)
assert len(export_inventory)==observed['preopen_files']==90
assert export_inventory==pre['snapshot_hashes']==observed['current_export_inventory']==io.inventory(w/'export',max_bytes=64*1024**2)
route=read(w/'route/result.json');exported=read(snapshot/'export.json');choice=read(w/'choice/choice.json')
assert route['source']==role['source'] and route['source_hashes']==exported['source_hashes']==hashes
assert route['tools']==exported['tools']==prepared['tools']
assert route['accepted'] is True and route['invariants_unchanged'] is True and exported['export_accepted'] is True
assert exported['original_geometry_and_routing_unchanged'] is True and exported['native_validation_performed'] is True
assert exported['inputs']['source']==role['source'] and exported['inputs']['receipt']==str(w/'route/result.json')
assert exported['inputs']['receipt_sha256']==p.sha(w/'route/result.json')
assert route['candidate_sha256']==exported['candidate_sha256']
assert choice['choice']=='accept' and choice['choice_recorded'] is True and choice['applied'] is False
own={}
for label,record,folder,actual in (
 ('route',route,w/'route',w/'route'),
 ('export',exported,snapshot/'validation',w/'export/validation')):
 assert [record['native'][key] for key in ('opens','blocking','warnings','exclusions')]==observed['native']==[0,0,0,0]
 assert record['schematic_parity']=='checked by final native DRC'
 audit=read(folder/'final-netclass-audit.json')
 assert audit['candidate_sha256']==record['candidate_sha256'] and audit['project_sha256']==hashes[Path(role['source']).with_suffix('.kicad_pro').name]
 assert audit['route_dimensions']['passed'] is True and audit['route_dimensions']['checked']['protected']==observed['protected']==4
 own[label]=own_final(record,folder,actual,hashes,Path(record['candidate']))
guide=route['default_target_transport'];assert p.sha(w/'route'/guide['file'])==guide['sha256']
reader=observed['reader_process'];reader_path=Path(reader['path'])
assert reader_path.parent==w and p.sha(reader_path)==reader['sha256']
reader_process=read(reader_path);reader_log=reader_path.with_name(reader_path.name.replace('.process.json','.log'))
assert reader_process['exit_code']==0 and reader_process['cancel_requested'] is False and reader_process['log_truncated'] is False
assert read(reader_log)['current'] is True and reader['current'] is True
assert reader_process['wall_seconds']==reader['recorded_wall_seconds']
queue={}
def add(path,name):queue.setdefault(Path(path),Path(name))
for path in [Path(__file__),*helpers,ROOT/'.runs/retain-gui086-controls-delta-002.py',ROOT/'.runs/gui086-preopen-001.py',ROOT/'.runs/gui086-boundary-preopen-001.log',ROOT/'.runs/gui086-boundary-preopen-001-time.log',prepared_path,base/'protocol-required-001.json',control/'protocol.json',control/'result.json',pre_path]:
 add(path,Path('controls')/path.name)
sealed={};omitted=[];samples=[]
for folder,label in ((w,'job'),(snapshot,'preopen-export')):
 inventory=io.inventory(folder,max_bytes=64*1024**2,max_files=8000,max_entries=16000);sealed[folder]=inventory
 for name,pin in inventory.items():
  path=folder/name;parts=Path(name).parts
  if path.suffix in ('.json','.log','.kicad_prl') and not any(part in ('code','kicad-config','kicad-cache','kicad-documents','tmp') for part in parts):
   add(path,Path(label)/name)
  else:omitted.append(dict(original=str(path.relative_to(ROOT)),sha256=pin,reason='CAD/plot/code/config/cache or other payload not copied; raw remains local'))
for path in sorted(w.glob('*.command.process.json')):
 proc=read(path);assert proc['log_truncated'] is False
 samples.append(dict(command=path.name,sha256=p.sha(path),wall_seconds=proc['wall_seconds'],exit_code=proc['exit_code'],cancel_requested=proc['cancel_requested']))
assert len(queue)<2000 and sum(path.stat().st_size for path in queue)<16*1024**2
for path,name in queue.items():retain(path,name)
assert all(io.inventory(path,max_bytes=64*1024**2,max_files=8000,max_entries=16000)==inventory for path,inventory in sealed.items())
assert io.inventory(Path(role['source']).parent)==hashes and p.sha(w/'settings.json')==protocol['settings_sha256']
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted=omitted))
p.save_json(target,dict(schema=1,kind='runtime050-GUI086-single-menu-queued-miss-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=prepared['source_head'],runtime_manifest_sha256=prepared['runtime_manifest_sha256'],actual_GUI=True,full_GUI_qualified=False,project_complete=False,human_review=False,dependencies=dependencies,observation=observed,outcome=observed['outcome'],mutation_performed=False,queued_freshness_pass=False,literal_CallAfter_already_queued_proven=False,PCB_editor_opened=False,own_final=own,preopen_snapshot=dict(receipt_sha256=p.sha(pre_path),files=90,live_export_still_exact=True,CAD_bytes_published=False),CLI_process_wall_samples=samples,accounting=dict(preopen_additional=cost(ROOT/'.runs/gui086-boundary-preopen-001-time.log'),nested_route=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),nested_export=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']),limits='CLI wall samples overlap nested Native/method samples and preopen readback; do not add overlapping samples. Whole interactive CPU/wall, menu duration and authoring/review remain unknown additional, notzero. Curation complete-exit cost is in the separately measured helper log, not a routing cost.'),scope='One actual Open checked export/native-menu attempt missed the hold interval. Manager opened; no PCB editor or mutation. Existing successful own Route/export Native0all/fullSCH/original/Default/protected4 proofs are preserved; no validation was rerun by this curator.',backup='Owned metadata/log/PRL only; CAD/plots/ZIP/code/cache payloads remain Mac-only outside010. No restoration, human, electrical, routing-gain, allGUI or exact queued-callback qualification claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,material=len(material),outcome=observed['outcome'])))
