"""DRAFT: retain fixed058/092 ordinary GUI observations, no reader/Native run.

Port of057 ordinary curation: unchanged030 retain and042 own_final bind preserved
preopen bytes to actual original paths. Live editor metadata remains stale.
Separate high/Improve/open-review-manager guard observations are excluded.
"""
from pathlib import Path
import ast,datetime,hashlib,json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
from scripts import report_current_comparison as timing
RUNTIME=ROOT/'.runs/runtime-directory-058/runtime';BASE=RUNTIME/'.runs/gui-session092'
WORK=BASE/'jobs/autorouter-gui-272e1539f82849a1bf4d56f229931c2f';CONTROL=BASE
BEFORE=BASE/'preopen-ordinary-export-001'
HEAD='8f5e96b88dd22cd25919bb71ce47711612994efa'
MANIFEST='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
PREPARED='276ce0ef459b0155f4a62112c4e7893d9caa742b38bd13fac527967d5219cc87'
ROUTE='6c8afab684e156b084b14f3d2af9a050db932962e54fce57c712076727ee38f1'
EXPORT='7e0190db7359c4d976dd339832d6d2a8407487e4d28a357689442390f5e614f8'
CANDIDATE='9c826f330a70e8af6f5feb91cf0e742497874bfb78eea4e6b515066dac5ced9a'
PREOPEN='b10896cd36a0f52548be24e7c3216332c99f316375a11657f194e25806cb9829'
POSTOPEN='c8122d9f75c98b75eff08d1d8844fa35bc11df330ec6dd5115f10247ef4ca830'
SETTINGS='a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65'
JOB_SETTINGS='2258e809e1efc6a1020ef0f55f2f63eecb5ebc126f6ae3d554658e94a5753880'
RETENTION=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
FINAL_HELPER=ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
TEMPLATE=ROOT/'.runs/curate-gui-runtime057-090-ordinary-001.py'
DEPENDENCY=ROOT/'evidence/runtime058-native-milestone-001.json'
PINS={
 WORK/'settings.json':JOB_SETTINGS,
 BASE/'route-settings.json':SETTINGS,
 BASE/'saved-route-settings-001.json':SETTINGS,
 ROOT/'evidence/native7-export-test-isolation-001.json':'26ded7c783214de9278ed461a6b93d0c5a057cb28e18cf3ae7fb91103a12b1f4',
 ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py':'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',
 ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py':'340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',
 ROOT/'.runs/curate-gui-runtime057-090-ordinary-001.py':'9e802a7eef9124042b06e921fbbadb56d06a5ca501b21d778defc48109b3acbb',
 ROOT/'scripts/report_current_comparison.py':'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e',
 ROOT/'evidence/runtime058-native-milestone-001.json':'1dd9972cdf5b20392cde77f42ddb177838e8a65c2b4cd22dc8409580ad42fc29',
 ROOT/'.runs/runtime-directory-058/runtime/.runs/gui-session092/prepared-state.json':'276ce0ef459b0155f4a62112c4e7893d9caa742b38bd13fac527967d5219cc87',
 ROOT/'.runs/runtime-directory-058/runtime/.runs/gui-session092/protocol-required-001.json':'231ab43d723d46f9d54e99458e439bd0eadebee1d54ad43c06ce206c61932f17',
 ROOT/'.runs/runtime-directory-058/runtime/.runs/gui-session092/observed-controls-001.json':'20cae7a0b5fa05563a4af6cc3c3b6e8968db5de7297b979fd4c44992e13ca672',
 ROOT/'.runs/runtime-directory-058/runtime/.runs/gui-session092/observed-ordinary-002.json':'c8122d9f75c98b75eff08d1d8844fa35bc11df330ec6dd5115f10247ef4ca830',
 ROOT/'.runs/runtime-directory-058/runtime/.runs/gui-session092/preopen-ordinary-001.json':'b10896cd36a0f52548be24e7c3216332c99f316375a11657f194e25806cb9829',
 ROOT/'.runs/runtime-directory-058/runtime/.runs/gui-session092/jobs/autorouter-gui-272e1539f82849a1bf4d56f229931c2f/route/result.json':'6c8afab684e156b084b14f3d2af9a050db932962e54fce57c712076727ee38f1',
 ROOT/'.runs/runtime-directory-058/runtime/.runs/gui-session092/preopen-ordinary-export-001/export.json':'7e0190db7359c4d976dd339832d6d2a8407487e4d28a357689442390f5e614f8',
 ROOT/'.runs/gui-runtime058-092-ordinary-preopen-001.py':'871b70f36fbee78d8cd9155c73e4b6e1abb5c4415c16997a1de12e3d3bd7bbfd',
 ROOT/'.runs/prepare-runtime058-gui092.py':'4a44069b4fde79fd87c7fee94a3ceefbb8be89fd45e34bf4dd002740f8af9416',
 ROOT/'.runs/prepare-runtime058-gui092.draft.json':'e3b035770ed80f7a3c37e88486308c247e4d7a1d007663950fed30efd91d7c49',
 ROOT/'.runs/prepare-runtime057-gui090.py':'3f57631308e333f6589023c36448d215a88cccda639e2513c234b3f7d9c0b708',
 ROOT/'.runs/runtime058-gui092-preparation-port-001.json':'b694c1ed2300e5ebaacb7a435d662e558efd0b75b0a288a74eaf100437148589',
 ROOT/'.runs/prepare-runtime058-gui092-001.log':'c7b9d3c452988390edd2e13b8142300c758d56f557c20f3ece7ddde370ed7468',
 ROOT/'.runs/prepare-runtime058-gui092-001-time.log':'1a12db93992e8dc43894f21daa2f802944c7a20cd1b5d949d5df1e913f12a2a2',
 ROOT/'.runs/gui-runtime058-092-ordinary-preopen-001.log':'60b6f9fdd77d991e4f16171cbadb0e60337e063236753ec454a9f3242ba31000',
 ROOT/'.runs/gui-runtime058-092-ordinary-preopen-001-time.log':'41c4fd6914bce94b7fba5da5f3328e29f733bd00d501407c71a197c0411406a5',
}
COMMANDS={'choice.command.process.json': 'eb5adb4248559092bd71ad706e90b2e05bfc694227d4603c2e20a0024e082e34', 'export.command.process.json': '6fe80ac5aca008e0ebdfdf5f2c4e83ee90e758823825440be240859142b07533', 'inspect-export-08efed2add1d420888bc65d2dc129d18.command.process.json': '79e38abb5800c9444570481a598b95857abb830425c801c12842a9e5074f6772', 'inspect-export-296c09f4bbc44722ab1856d331b53fc0.command.process.json': '9204c43d4526e24f9c569e3fabcf5a9d4cad24d71a8d0169668de4a6094b099b', 'preview.command.process.json': 'fec472edb386f6dacd697b1bfbea3da96f565072fe3106ba1e7da3e1263014d5', 'review.command.process.json': 'acf31849a2d23a8dc62ad21d6f3edcf6476cdb69eeaed90d92e56c1022b407f0', 'route.command.process.json': 'c7ce2ecd07e86a7f59f9ae0dc81caf97a61abb8452b9540538b5ef2689396a76', 'verify_export.command.process.json': '535237f78c91b699563edded03d84b71cf7cc00098f0e322bbe2f08663848c57'}
LOGS={'choice.command.log': '519621b38d228ae195db85f0adfcad0fb60b78b401831daae3e52ca43bff38b5', 'export.command.log': '4d4392bcb8e44ec879a85fa4ef8eb5e77f0751e248a5467c0cea49b9e9626be4', 'inspect-export-08efed2add1d420888bc65d2dc129d18.command.log': 'd147d9e647ae479d83edb5e8126948cbfe34b663cf46a9147b45da7dc9fcb718', 'inspect-export-296c09f4bbc44722ab1856d331b53fc0.command.log': '9d3d89639adc19889fb3902ac9249863f5192318e730b8763c7859f26b47d274', 'preview.command.log': '8c50a836875bafc844cc238ab322e8843d46e058eabc8bc287fe516c02ac00ea', 'review.command.log': '46580df02e73e6c0863f505a894d59cb94c220e4953c0edc6e93eb187788214a', 'route.command.log': '0e769511483e7997097d8884a259e109c3b02f3b06faafc34702a52924125906', 'verify_export.command.log': '9d3d89639adc19889fb3902ac9249863f5192318e730b8763c7859f26b47d274'}
STALE='inspect-export-08efed2add1d420888bc65d2dc129d18.command.process.json'
COUNTS=('opens','blocking','warnings','exclusions')

def load_functions(path,names):
 nodes=[n for n in ast.parse(io.read_bytes(path,4*1024**2)).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::unchanged-shared','exec'),globals())

def main():
 global notes,refs,files,material,total
 start=time.monotonic();cpu0=time.process_time();stem='gui-runtime058-092-ordinary-001'
 notes=ROOT/'evidence'/(stem+'-notes');output=ROOT/'evidence'/(stem+'.json')
 assert not os.path.lexists(notes) and not os.path.lexists(output), 'Fresh packet; preserve any partial failure'
 control_pins=tuple([*PINS.items(),(Path(__file__),p.sha(Path(__file__)))]);commands=tuple(COMMANDS.items())
 for path,pin in control_pins:assert p.sha(path)==pin,str(path)
 load_functions(RETENTION,('retain',));load_functions(FINAL_HELPER,('read','own_final'));cost=timing.complete_cost
 prepared=read(BASE/'prepared-state.json');protocol=read(BASE/'protocol-required-001.json')
 first=read(BASE/'observed-controls-001.json');second=read(BASE/'observed-ordinary-002.json')
 assert first['runtime_manifest_sha256']==second['runtime_manifest_sha256']==MANIFEST
 assert first['prepared_sha256']==second['prepared_sha256']==PREPARED
 assert first['actual_GUI_qualified'] is False and first['Native_job_executed'] is False
 assert first['human_review'] is False and second['human_PCB_review'] is False
 assert first['project_complete'] is False and second['project_complete'] is False
 assert second['kind']=='runtime058-actual-GUI092-ordinary-observation-journal-v1'
 assert second['previous_journal_sha256']==PINS[BASE/'observed-controls-001.json']
 assert second['workspace']==str(WORK) and second['candidate_sha256']==CANDIDATE
 assert second['preopen_proof_sha256']==PREOPEN and second['preopen_snapshot_hashes_unchanged'] is True
 assert first['source_unchanged'] is True and second['source_unchanged'] is True
 assert second['full_GUI_qualified'] is False and second['exact_queued_callback_interval_qualified'] is False
 ordinary=second['actual_GUI_observations'];assert len(ordinary)==7 and all(type(row) is str and row for row in ordinary)
 assert second['native']==read(WORK/'route/result.json')['native']
 # The high-role manager guard was not observed on this ordinary job.
 assert ordinary[1].startswith('Actual missing review acknowledgement refused Accept intent')
 assert ordinary[2].startswith('Open preview launched current preview.html in Microsoft Edge; F.Cu and B.Cu')
 assert 'Unrouted0/Pads6/Vias1/Tracks6/Nets3' in ordinary[5]
 assert ordinary[6].startswith('Closed candidate PCB without saving, then closed candidate project.')
 for data in (prepared,protocol):assert data['source_head']==HEAD and data['runtime_manifest_sha256']==MANIFEST
 assert p.sha(RUNTIME/'runtime-distribution.json')==MANIFEST
 for name,pin in prepared['tools']['implementation_sha256'].items():assert p.sha(RUNTIME/name)==pin
 for name,pin in prepared['prerequisite_sha256'].items():assert p.sha(Path(name))==pin
 role=prepared['roles']['ordinary-alias2Cu'];assert role==protocol['roles']['ordinary-alias2Cu'] and role['method']=='route'
 source=Path(role['source']);hashes=role['source_hashes'];assert source==BASE/'project/owned1007-transport.kicad_pcb'
 assert io.inventory(source.parent)==io.inventory(Path(role['original_source']).parent)==hashes
 assert first['source']==str(source) and first['source_hashes']==hashes and first['jobs_before_preview']==[]
 settings=dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
 assert read(WORK/'settings.json')==read(Path(role['settings_path']))==role['settings']==settings
 assert p.sha(WORK/'settings.json')==JOB_SETTINGS and p.sha(Path(role['settings_path']))==SETTINGS
 saved=BASE/'saved-route-settings-001.json';assert p.sha(saved)==SETTINGS and read(saved)==settings
 assert first['saved_settings_sha256']==first['prepared_settings_sha256']==SETTINGS
 pre=read(CONTROL/'preopen-ordinary-001.json');before=BEFORE
 before_hashes=io.inventory(before,max_bytes=64*1024**2);assert before_hashes==pre['snapshot_hashes'] and len(before_hashes)==90
 assert pre['kind']=='point-in-time-current-export-before-editor-open-v1' and pre['snapshot']==str(before)
 assert pre['source_unchanged'] is True and pre['human_review'] is False and pre['actual_GUI_qualified'] is False
 assert pre['route']['current'] is True and pre['export']['current'] is True and pre['export']['export_accepted'] is True
 assert pre['export']['fresh_native_run_performed_by_check'] is False and pre['export']['applied'] is False
 assert pre['route']['candidate']==str(WORK/'route/candidate'/source.name)
 assert pre['export']['candidate']==str(WORK/'export/validation/candidate'/source.name)
 assert pre['export']['original_routing_receipt']==str(WORK/'route/result.json')
 assert pre['route']['candidate_sha256']==pre['export']['candidate_sha256']==CANDIDATE
 current=dict(before_hashes);changes=[]
 for name,pair in sorted(second['post_editor_export_changes'].items()):
  assert current.get(name)==pair['before'];changes.append(dict(path=name,**pair))
  if pair['after'] is None:current.pop(name)
  else:current[name]=pair['after']
 assert len(changes)==3 and sorted(Path(row['path']).suffix for row in changes)==['.kicad_prl','.kicad_pro','.zip']
 assert io.inventory(WORK/'export',max_bytes=64*1024**2)==current
 roots={folder:io.inventory(folder,max_bytes=64*1024**2) for folder in
  (WORK/'route',before/'validation',WORK/'review',WORK/'review/plot-work',WORK/'choice')}
 route=read(WORK/'route/result.json');exported=read(before/'export.json')
 assert route['accepted'] is True and route['invariants_unchanged'] is True and route['scope']=='partial_completion'
 assert route['adapter']=='both' and route['engine_profile']=='standard' and route['scoring_variant'] is None
 assert route['routing_preferences']['effective']==settings
 assert route['budget_seconds']==route['cpu_budget_seconds']==exported['budget_seconds']==exported['cpu_budget_seconds']==90
 assert exported['export_accepted'] is True and exported['applied'] is False and exported['original_geometry_and_routing_unchanged'] is True
 assert exported['inputs']['source']==route['source']==str(source) and exported['inputs']['receipt']==str(WORK/'route/result.json')
 assert exported['inputs']['receipt_sha256']==ROUTE
 for data in (route,exported):
  assert data['source_hashes']==hashes and data['tools']==prepared['tools'] and data['schematic_parity']=='checked by final native DRC'
  assert data['candidate_sha256']==CANDIDATE and [data['native'][k] for k in COUNTS]==[0,0,0,0] and len(data['native']['ignored_checks'])==2
 own=dict(route=own_final(route,WORK/'route',WORK/'route',hashes,Path(route['candidate'])),
  export=own_final(exported,before/'validation',WORK/'export/validation',hashes,Path(exported['candidate'])))
 original=p.sx.read(source);protected=p.protected_for_record(route,original);assert len(protected)==4
 for candidate in (Path(route['candidate']),before/'validation/candidate'/source.name):
  tree=p.sx.read(candidate);assert p.immutable(tree)==p.immutable(original) and all(n in p.routes(tree) for n in protected) and p.sha(candidate)==CANDIDATE
 assert p.sha(Path(exported['candidate']))==CANDIDATE
 guide=read(WORK/'route/default-targets.json');assert p.sha(WORK/'route/default-targets.json')==route['default_target_transport']['sha256']
 for folder in (WORK/'route',before/'validation'):
  audit=read(folder/'final-netclass-audit.json')
  assert audit['candidate_sha256']==CANDIDATE and audit['project_sha256']==hashes[source.with_suffix('.kicad_pro').name]
  assert audit['native']['passed'] is True and audit['route_dimensions']['passed'] is True and audit['route_dimensions']['checked']['protected']==4
  assert audit['native_map_file_sha256']==p.sha(folder/'final-netclasses.json')
  assert all(audit['default_targets'][key]==guide[key] for key in ('raw_nm','original_floors_nm','derived_nm'))
 review=read(WORK/'review/review.json');choice=read(WORK/'choice/choice.json')
 assert review['receipt_sha256']==choice['receipt_sha256']==ROUTE and review['candidate_sha256']==choice['validated_candidate_sha256']==CANDIDATE
 assert choice['choice']=='accept' and choice['choice_recorded'] is True and choice['applied'] is False and choice['human_pcb_approval_observed'] is False
 assert choice['review_sha256']==p.sha(WORK/'review/review.json')
 refs={};files=[];material=[];total=0;dep=read(DEPENDENCY);idx=ROOT/dep['files_index']['path']
 assert p.sha(idx)==dep['files_index']['sha256']=='47676017af71df28954a8a5878e4efccd34d31da7fdaf234711c2e2ccd341e38'
 for row in read(idx)['files']:refs.setdefault(row['sha256'],row['path'])
 for row in read(idx)['material']:refs.setdefault(row['sha256'],row['retained'])
 queue={};samples=[]
 def add(path,name):
  path=Path(path);name=Path(name);assert path.is_file() and not path.is_symlink() and ROOT in path.parents
  assert not name.is_absolute() and '.runs' not in name.parts and '..' not in name.parts
  queue.setdefault(path,name)
 def metadata(folder,name):
  inv=roots[folder];assert io.inventory(folder,max_bytes=64*1024**2)==inv
  for rel in inv:
   path=folder/rel;parts=Path(rel).parts
   if (len(parts)==1 and path.suffix in ('.json','.log','.net')) or (len(parts)==2 and parts[0] in ('final-drc-input','refill-drc-input','source-drc-input') and path.suffix=='.kicad_prl'):
    add(path,Path(name)/rel)
 for path in PINS:add(path,Path('controls')/str(path.relative_to(ROOT)).replace('.runs/','retained-run/'))
 add(RUNTIME/'runtime-distribution.json','runtime/runtime-distribution.json');add(Path(__file__),'curation/'+Path(__file__).name);add(ROOT/'LICENSE','rights/LICENSE')
 add(WORK/'settings.json','settings/job-settings.json');add(Path(role['settings_path']),'settings/route-settings.json');add(saved,'settings/saved-route-settings-001.json')
 add(before/'export.json','before-open/export/export.json')
 metadata(WORK/'route','job/route');metadata(before/'validation','before-open/export/validation')
 metadata(WORK/'review','job/review');metadata(WORK/'review/plot-work','job/review/plot-work');metadata(WORK/'choice','job/choice')
 for name,pin in commands:
  path=WORK/name;assert p.sha(path)==pin;proc=read(path);log=path.with_name(path.name.replace('.process.json','.log'))
  assert proc['argv'][:4]==[str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter']
  assert proc['cancel_requested'] is False and proc['log_truncated'] is False and log.stat().st_size==proc['log_bytes']
  if name==STALE:
   assert proc['exit_code']==2 and read(log)==dict(current=False,reason='export inputs/runtime/evidence changed')
   assert second['inspect_process_pins'][name]==pin
  else:assert proc['exit_code']==0
  assert p.sha(log)==LOGS[log.name]
  samples.append(dict(command=name,receipt_sha256=pin,log_sha256=p.sha(log),sample=proc))
  add(path,Path('commands')/path.name);add(log,Path('commands')/log.name)
 for name in ('prepare-runtime058-gui092-001.log', 'prepare-runtime058-gui092-001-time.log', 'gui-runtime058-092-ordinary-preopen-001.log', 'gui-runtime058-092-ordinary-preopen-001-time.log'):
  add(ROOT/'.runs'/name,Path('costs')/name)
 for name in ('prepare-launcher.log','prepare-launcher-process.json'):add(BASE/name,Path('setup')/name)
 measured={name:cost(ROOT/'.runs'/name) for name in ('prepare-runtime058-gui092-001-time.log', 'gui-runtime058-092-ordinary-preopen-001-time.log')}
 def controls_fresh():
  for path,pin in control_pins:assert p.sha(path)==pin,str(path)
  for row in measured.values():assert p.sha(Path(row['source']))==row['time_log_sha256']
  for row in samples:
   path=WORK/row['command'];log=path.with_name(path.name.replace('.process.json','.log'))
   assert p.sha(path)==row['receipt_sha256'] and p.sha(log)==row['log_sha256']==LOGS[log.name]
  for name,pin in prepared['prerequisite_sha256'].items():assert p.sha(Path(name))==pin
  assert p.sha(RUNTIME/'runtime-distribution.json')==MANIFEST
  for name,pin in prepared['tools']['implementation_sha256'].items():assert p.sha(RUNTIME/name)==pin
  assert p.sha(idx)==dep['files_index']['sha256']
 omitted=[dict(original=str((folder/rel).relative_to(ROOT)),bytes=(folder/rel).stat().st_size,sha256=pin,reason='CAD/transport/plots/HTML/SVG/config/code/cache stays local; selected metadata retained separately.') for folder,inv in roots.items() for rel,pin in inv.items() if folder/rel not in queue]
 omitted += [dict(original=str((WORK/'export'/row['path']).relative_to(ROOT)),bytes=(WORK/'export'/row['path']).stat().st_size,sha256=row['after'],reason='Editor-created backup ZIP bytes omitted; observed hash only.') for row in changes if Path(row['path']).suffix=='.zip']
 known=set(refs);planned=count=0;sealed={}
 for path in queue:
  raw=io.read_bytes(path,4*1024**2);assert b'\0' not in raw;raw.decode('utf-8');pin=hashlib.sha256(raw).hexdigest();sealed[path]=(len(raw),pin)
  if pin not in known:known.add(pin);planned+=len(raw);count+=1
 assert planned<16*1024**2 and count<2000,('Split before writing; never raise caps',planned,count)
 def material_fresh():
  controls_fresh()
  for path,(size,pin) in sealed.items():assert path.stat().st_size==size and p.sha(path)==pin
  for folder,inv in roots.items():assert io.inventory(folder,max_bytes=64*1024**2)==inv
  assert io.inventory(source.parent)==io.inventory(Path(role['original_source']).parent)==hashes
  assert io.inventory(before,max_bytes=64*1024**2)==before_hashes and io.inventory(WORK/'export',max_bytes=64*1024**2)==current
  for row in material:assert p.sha(ROOT/row['retained'])==row['sha256']
 # Other roles/jobs may exist; this fence covers only the fixed ordinary job.
 material_fresh();notes.mkdir()
 for path,name in queue.items():retain(path,name)
 material_fresh()
 index=notes/'files.json';index_data=dict(schema=1,files=files,material=material,omitted=omitted)
 index_pin=hashlib.sha256((json.dumps(index_data,indent=2)+'\n').encode()).hexdigest()
 material_fresh();p.save_json(index,index_data);assert p.sha(index)==index_pin;material_fresh()
 summary=dict(schema=1,kind='runtime058-GUI092-assigned-ordinary-role-only-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  source_head=HEAD,runtime_manifest_sha256=MANIFEST,prepared_state_sha256=PREPARED,
  journals=[dict(path=str(path.relative_to(ROOT)),sha256=PINS[path]) for path in (BASE/'observed-controls-001.json',BASE/'observed-ordinary-002.json')],
  assigned_ordinary_role_recorded=True,actual_GUI_observed=True,actual_GUI_qualified=False,full_GUI_claim=False,Improve_qualified=False,project_complete=False,human_review=False,physical_electrical_validation=False,
  workspace=str(WORK),source=str(source),source_hashes=hashes,source_unchanged=True,settings=settings,job_settings_sha256=JOB_SETTINGS,saved_settings_sha256=SETTINGS,
  settings_serialization='Prepared/saved preset bytes and job serialization differ; decoded settings are equal.',candidate_sha256=CANDIDATE,protected_original_items=4,native=route['native'],metrics=route['metrics'],own_final_bindings=own,
  before_open=dict(snapshot=str(before),files=90,receipt_sha256=PREOPEN,current_production_readers_then=True,new_Native_run_by_curator=False,actual_to_preserved_mapping={str(WORK/'export'):str(before)}),
  after_open=dict(observation_journal_sha256=POSTOPEN,files=len(current),changes=changes,candidate_PCB_unchanged=True,actual_checked_opening=True,closed_without_save=True,current_export_stale_refusal_recorded=True,new_Native_validity_inferred=False,exact_CallAfter_queue_proved=False),
  actual_GUI_observations=dict(initial_setup_and_static=first['actual_GUI_observations'],ordinary=ordinary,ordinary_open_review_manager_guard_observed=False,missing_acknowledgement_refusal_observed=True),
  not_qualified_by_this_packet=dict(via_high_GUI=True,Improve_GUI=True,explicit_Reject=True,active_Cancel=True,recovery=True,source_settings_freshness_refusals=True,forced_queued_timing=True,fresh_root_GUI=True),
  accounting=dict(CLI_command_samples=samples,CLI_command_wall_sum_seconds=sum(r['sample']['wall_seconds'] for r in samples),CLI_command_CPU_seconds=None,whole_interactive_wall_seconds=None,whole_interactive_CPU_seconds=None,
   nested_route=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),nested_export=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']),additional_measured_helpers=measured,
   raw_journal_costs=None,historical_failed_full208=dict(path='evidence/native7-export-test-isolation-001.json',sha256=PINS[ROOT/'evidence/native7-export-test-isolation-001.json'],scope='Separate historical test-isolation failure and correction costs; no GUI cost or outcome transfer.'),prior_failure_and_curation_costs='Failed full208 costs are recorded in historical_failed_full208; Native-packet curation costs remain separate in the linked058 Native packet.',limitation='Per-stage CLI/nested Native costs overlap and are not added. Full interactive/UI/authoring/AI CPU and wall remain additional unknown, not zero; no fair performance comparison.'),
  dependency=dict(path=str(DEPENDENCY.relative_to(ROOT)),sha256=PINS[DEPENDENCY],files_index=dep['files_index'],scope='Owned source rights and same-byte mechanics only; current cohort or prior GUI outcomes do not transfer this job proof.'),
  publication=dict(new_files=len(files),new_bytes=total,material_rows=len(material),file_cap=4*1024**2,packet_cap=16*1024**2,file_count_cap=2000,scope='Owned metadata/log/net/PRL and shared controller code only; no CAD, pixels, plots, ZIP bytes, engines/apps or caches. Raw preopen snapshot is Mac-only/outside010, not a full restore copy.'),
  limitations='One fixed ordinary partial90 default-score GUI job only. Lead observed toolbar, Edge F+B, missing review acknowledgement refusal, Accept, fresh export and checked KiCad opening0unrouted, then editor-metadata stale refusal. No current validity inferred after editor, independent human/electrical approval, full058GUI, Improve, cancellation, exact queued timing, fresh-rootGUI, quality gain, comparison, Windows or standalone/release/restoration claim.',
  curation=dict(sampled_wall_seconds=time.monotonic()-start,sampled_parent_CPU_seconds=time.process_time()-cpu0,complete_external_exit_not_included=True,Native_executed=False,production_readers_rerun=False),
  files_index=dict(path=str(index.relative_to(ROOT)),sha256=index_pin))
 summary_pin=hashlib.sha256((json.dumps(summary,indent=2)+'\n').encode()).hexdigest()
 assert total+index.stat().st_size+len((json.dumps(summary,indent=2)+'\n').encode())<16*1024**2 and len(files)+2<2000
 material_fresh();assert p.sha(index)==index_pin;p.save_json(output,summary)
 assert p.sha(output)==summary_pin and p.sha(index)==index_pin;material_fresh()
 print(json.dumps(dict(output=str(output),sha256=p.sha(output),files=len(files),bytes=total,material=len(material),actual_GUI_qualified=False,Native_executed=False)))
if __name__=='__main__':main()
