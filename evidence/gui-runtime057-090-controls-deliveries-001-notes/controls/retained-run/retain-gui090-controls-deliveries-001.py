"""DRAFT ONLY: retain fixed GUI090 journals003–006 and their owned proof bytes.

Reuse030 retain,042 dual-path own_final, the ordinary9e802 seal mechanics and
strategy.native7_packets as a stored-record census. Never run Native, production
readers or GUI. Positive exports are read only from preserved preopen snapshots;
the editor-modified live trees remain stale. Later jobs are outside this packet.
"""
from pathlib import Path
import ast,datetime,hashlib,json,os,stat,sys,time
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runs/runtime-directory-057/runtime';BASE=RUNTIME/'.runs/gui-session090'
sys.path.insert(0,str(RUNTIME));sys.path.insert(1,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,handoff as h,strategy,local_settings as local,config as c
from scripts import report_current_comparison as timing
HEAD='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
MANIFEST='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
RETENTION=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
FINAL=ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
TEMPLATE=ROOT/'.runs/curate-gui-runtime057-090-ordinary-001.py'
PINS={RETENTION:'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',
 FINAL:'340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',
 TEMPLATE:'9e802a7eef9124042b06e921fbbadb56d06a5ca501b21d778defc48109b3acbb',
 Path(timing.__file__):'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e',
 RUNTIME/'autorouter/strategy.py':'35724350fbeae58cea4c2326397b63cd010f2f52c33f5e70e79b3cff033651d7',
 RUNTIME/'runtime-distribution.json':MANIFEST,
 BASE/'prepared-state.json':'dbc6ee9297c396aeedb5ee38a2a7ecafd9330b3d90dd68f94926cdd672804ed3',
 BASE/'protocol-required-001.json':'8592d9c2447ff167dcece866796a2c1a81b355fa88b42fae15f61254cdefe37e',
 ROOT/'.runs/gui090-observations-003.json':'57783176c4ad6bfbdab9fe91d9cbb460d1a522b31fe89851e786dd0f06073843',
 ROOT/'.runs/gui090-observations-004.json':'ba16334d1fd555e962c469d1918293ff76df4dcf427211453bffec502580a2ab',
 ROOT/'.runs/gui090-observations-005.json':'ee02a06fefb2e7e927029ed60bd1d155e19ed7a3b09b1bccbb906d7768148462',
 ROOT/'.runs/gui090-observations-006.json':'98512d695a441cd3df17a36b8755f61584255dabe295b00ec4ab0939401a77aa',
 ROOT/'evidence/gui-runtime057-090-ordinary-001.json':'6f55082fbc346a36a72a44bdc32e125c1b2707ea087cdde28120c7a56bc0cccf',
 ROOT/'evidence/runtime057-native-milestone-001.json':'37620250ac71559915a80873be8d9cfc36c4d65853fd337fa5537e0eac904eb9'}
COUNTS=('opens','blocking','warnings','exclusions')

def load_functions(path,names):
 nodes=[n for n in ast.parse(io.read_bytes(path,4*1024**2)).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::unchanged-shared','exec'),globals())

def main():
 global notes,refs,files,material,total
 start=time.monotonic();cpu0=time.process_time();stem='gui-runtime057-090-controls-deliveries-001'
 notes=ROOT/'evidence'/(stem+'-notes');target=ROOT/'evidence'/(stem+'.json')
 assert not os.path.lexists(notes) and not os.path.lexists(target),'Fresh packet; retain any partial failure'
 assert c.ROOT==RUNTIME and c.NATIVE_VERSION=='10.0.7' and Path(strategy.__file__).resolve()==RUNTIME/'autorouter/strategy.py'
 pins=dict(PINS);roots={};owners={};queue={};destinations={};costs={};command_rows=[];omitted=[]
 def bind(path,expected=None):
  path=h.real_path(path);raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest()
  if expected is not None:assert digest==expected,str(path)
  if path in pins:assert pins[path]==digest,str(path)
  else:pins[path]=digest
  return raw
 for path,pin in tuple(pins.items()):bind(path,pin)
 load_functions(RETENTION,('retain',));load_functions(FINAL,('read','own_final'))
 def pinned_read(path,expected=None):return json.loads(bind(path,expected))
 def watch(folder,expected=None):
  folder=h.real_path(folder);inventory=io.inventory(folder,max_bytes=64*1024**2)
  if expected is not None:assert inventory==expected,str(folder)
  if folder in roots:assert roots[folder]==inventory
  else:
   roots[folder]=inventory;owner={};h.capture_destination(owner,folder);owners[folder]=owner
  return inventory
 def add(path,name):
  path=h.real_path(path);name=Path(name)
  assert path.is_file() and ROOT in path.parents and not name.is_absolute() and not ({'..','.runs'}&set(name.parts))
  if path in queue:return
  assert name not in destinations,('Destination collision',name)
  queue[path]=name;destinations[name]=path
 def metadata(folder,name):
  folder=Path(folder);inventory=watch(folder)
  for relative in inventory:
   path=folder/relative;parts=Path(relative).parts
   if (len(parts)==1 and path.suffix in ('.json','.log','.net')) or (len(parts)==2 and parts[0].endswith('-input') and path.suffix=='.kicad_prl'):
    add(path,Path(name)/relative)
 def commands(work,expected,allow_cancel=False):
  paths=sorted(work.glob('*.command.process.json'));names={path.name.split('.command.')[0] for path in paths}
  normalized={'inspect-export' if name.startswith('inspect-export-') else name for name in names}
  assert normalized==set(expected) and len(paths)==len(expected),(work,names)
  rows=[]
  for path in paths:
   process=pinned_read(path,roots[work][path.name]);log=path.with_name(path.name.replace('.process.json','.log'));bind(log,roots[work][log.name])
   assert process['argv'][:4]==[str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter'] and process['log_truncated'] is False
   assert log.stat().st_size==process['log_bytes']
   cancelled=allow_cancel and path.name=='route.command.process.json'
   assert process['cancel_requested'] is cancelled and process['exit_code']==(2 if cancelled else 0)
   row=dict(command=path.name,receipt_sha256=pins[path],log_sha256=pins[log],sample=process)
   command_rows.append((path,log,row));rows.append(row)
   add(path,Path('commands')/work.name/path.name);add(log,Path('commands')/work.name/log.name)
  return rows
 def final_bridge(data,folder,actual,hashes,source,protected_count,guide):
  proof=own_final(data,folder,actual,hashes,actual/'candidate'/source.name)
  audit=pinned_read(folder/'final-netclass-audit.json');mapping=folder/'final-netclasses.json'
  assert audit['candidate_sha256']==data['candidate_sha256'] and audit['project_sha256']==hashes[source.with_suffix('.kicad_pro').name]
  assert audit['native']['passed'] is True and audit['route_dimensions']['passed'] is True and audit['route_dimensions']['checked']['protected']==protected_count
  assert audit['native_map_file_sha256']==p.sha(mapping)
  assert all(audit['default_targets'][key]==guide[key] for key in ('raw_nm','original_floors_nm','derived_nm'))
  binding=pinned_read(folder/'final-drc-binding.json');process=pinned_read(folder/'final-drc-process.json')
  prl=source.with_suffix('.kicad_prl').name;event=process['local_settings_protection']
  assert process['local_settings_policy']=='job-owned-prl-immutable-v1'
  assert event==dict(policy='mac-owned-prl-immutable-v1',present=True,path=str(actual/'final-drc-input'/prl),sha256=hashes[prl],flags_before=0,flags_during=stat.UF_IMMUTABLE,flags_restored=True,bytes_unchanged=True)
  assert binding['before'][prl]==hashes[prl] and local.check_current_metadata(folder/'final-drc-input'/prl)
  return dict(own_final=proof,Default_audit_sha256=pins[folder/'final-netclass-audit.json'],PRL_binding_sha256=pins[folder/'final-drc-binding.json'],PRL_process_sha256=pins[folder/'final-drc-process.json'])
 journals=[pinned_read(ROOT/'.runs'/('gui090-observations-%03d.json'%n)) for n in (3,4,5,6)]
 j3,j4,j5,j6=journals
 for journal in journals:
  assert journal['runtime']=='057' and journal['session']=='090' and journal['source_head']==HEAD and journal['manifest_sha256']==MANIFEST
  assert journal['actual_GUI'] is True and journal['project_complete'] is False and journal['human_review'] is False
 assert j4['previous']['sha256']==PINS[ROOT/'.runs/gui090-observations-003.json'] and j5['previous']['sha256']==PINS[ROOT/'.runs/gui090-observations-004.json'] and j6['previous']['sha256']==PINS[ROOT/'.runs/gui090-observations-005.json']
 for key in ('actual_idle_GUI_closed_normally','actual_idle_manager_quit_normally','owned_processes_absent_at_current_snapshot','prepared_role_sources_unchanged'):assert j6[key] is True,key
 prepared=pinned_read(BASE/'prepared-state.json');tools=prepared['tools'];assert p.tool_manifest()==tools
 assert prepared['source_head']==HEAD and prepared['runtime_manifest_sha256']==MANIFEST
 dependencies=[];refs={};files=[];material=[];total=0
 for path in (ROOT/'evidence/gui-runtime057-090-ordinary-001.json',ROOT/'evidence/runtime057-native-milestone-001.json'):
  data=pinned_read(path);index=ROOT/data['files_index']['path'];contents=pinned_read(index,data['files_index']['sha256'])
  for row in contents['files']:refs.setdefault(row['sha256'],row['path'])
  for row in contents['material']:refs.setdefault(row['sha256'],row['retained'])
  dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=pins[path],files_index=data['files_index'],scope='Same-byte deduplication/owned rights and stated prior scope only; no transferred GUI qualification.'))
 deliveries=[]
 for label,journal_row,control_name in (('via-high',j3['via_high'],'preopen-via-high-001'),('Improve',j4['improve'],'preopen-improve-001')):
  work=h.real_path(journal_row['workspace']);assert work.parent==BASE/'jobs';watch(work)
  control=BASE/control_name;pre=pinned_read(control/'preopen.json',journal_row['preopen_sha256']);post=pinned_read(control/'postopen-001.json',journal_row['postopen_sha256']);before=control/'export'
  before_hashes=watch(before,pre['snapshot_hashes']);assert len(before_hashes)==(90 if label=='via-high' else 98)
  for key in ('rendered_Edge_F_B_before_after_images','actual_ack_accept_recorded','fresh_export_and_check_completed','actual_checked_export_manager_and_PCB_open','PCB_closed_without_save','export_manager_closed_using_FileCloseProject','post_editor_validity_not_renewed'):assert journal_row[key] is True,key
  assert journal_row['observed_unrouted']==0 and pre['runtime']=='057' and pre['session']=='090' and pre['workspace']==str(work)
  assert pre['source_head']==HEAD and pre['runtime_manifest_sha256']==MANIFEST and pre['actual_GUI_opening'] is False and pre['source_unchanged'] is True
  bind(ROOT/'.runs/gui090-preopen-001.py',pre['controller_sha256'])
  assert pre['route']['current'] is True and pre['export']['current'] is True and pre['export']['fresh_native_run_performed_by_check'] is False
  assert post['preopen_sha256']==journal_row['preopen_sha256'] and post['snapshot_unchanged'] is True and post['source_unchanged'] is True
  for key in ('actual_GUI','actual_export_manager_and_PCB_opened','actual_PCB_closed_without_save','actual_manager_FileCloseProject','PCB_bytes_unchanged','positive_proof_not_renewed'):assert post[key] is True,key
  live=watch(work/'export',post['current_export_inventory']);changes=[dict(path=n,before=before_hashes.get(n),after=live.get(n)) for n in sorted(set(before_hashes)|set(live)) if before_hashes.get(n)!=live.get(n)]
  assert changes==post['changes'] and sorted(Path(row['path']).suffix for row in changes)==['.kicad_prl','.kicad_pro','.zip']
  route=pinned_read(work/'route/result.json',journal_row['route_sha256']);exported=pinned_read(before/'export.json',journal_row['export_sha256'])
  source=h.real_path(route['source']);hashes=route['source_hashes'];role=prepared['roles'][journal_row['role']]
  assert source==Path(role['source']) and hashes==role['source_hashes']==pre['source_hashes'] and pre['source']==str(source)
  watch(source.parent,hashes);watch(Path(role['original_source']).parent,hashes)
  settings=pinned_read(work/'settings.json',pre['settings_sha256']);assert settings==journal_row['settings']==role['settings']
  assert route['accepted'] is True and route['invariants_unchanged'] is True and exported['export_accepted'] is True and exported['applied'] is False
  assert route['budget_seconds']==route['cpu_budget_seconds']==exported['budget_seconds']==exported['cpu_budget_seconds']==90
  assert exported['inputs']['source']==str(source) and exported['inputs']['receipt']==str(work/'route/result.json') and exported['inputs']['receipt_sha256']==journal_row['route_sha256']
  assert exported['original_geometry_and_routing_unchanged'] is True and route['candidate_sha256']==exported['candidate_sha256']==journal_row['candidate_sha256']
  original=p.sx.read(source);protected=p.protected_for_record(route,original);assert len(protected)==journal_row['protected']
  if label=='via-high':
   assert settings['scoring_preference']=='via_high' and route['scoring_variant']=='via_high' and route['routing_preferences']['effective']==settings
   packets=[(work/'route',route)];guide_path=work/'route/default-targets.json';assert p.sha(guide_path)==route['default_target_transport']['sha256']
  else:
   assert settings['scoring_preference'] is None and route['pruning_preferences']['effective']==settings and journal_row['six_warnings_and_two_ignored_visible'] is True
   packets=strategy.native7_packets(work/'route',route);assert len(packets)==3 and len(route['trials'])==journal_row['trials']==1
   basis=route['native7_default_target_basis'];guide_path=work/'route'/basis['file'];assert p.sha(guide_path)==basis['sha256']
   assert p.sha(work/'route/incumbent/result.json')==basis['receipt_sha256']
   context=pinned_read(work/'route'/route['native7_improve_parent']['file'])['context']
   incumbent=packets[1][1];marker=incumbent['native_improve_child'];context_path=packets[1][0]/marker['file']
   assert p.sha(context_path)==marker['sha256'] and pinned_read(context_path)==context
   assert route['incumbent']['receipt']==str(packets[1][0]/'result.json') and route['incumbent']['accepted'] is incumbent['accepted'] is True
  guide=pinned_read(guide_path);proofs={};facts=[]
  for actual,data in [*packets,(work/'export/validation',exported)]:
   folder=before/'validation' if actual==work/'export/validation' else actual;watch(folder)
   trial=actual.parent==work/'route/trials'
   if not trial:assert data['source_hashes']==hashes and data['tools']==tools and data['schematic_parity']=='checked by final native DRC'
   else:assert data['id']==actual.name and data['accepted'] is True
   assert [data['native'][key] for key in COUNTS]==journal_row['native'] and len(data['native']['ignored_checks'])==2
   candidate=folder/'candidate'/source.name;tree=p.sx.read(candidate)
   assert p.sha(candidate)==data['candidate_sha256'] and p.immutable(tree)==p.immutable(original) and all(item in p.routes(tree) for item in protected)
   name='export' if actual==work/'export/validation' else 'parent' if actual==work/'route' else actual.name
   proofs[name]=final_bridge(data,folder,actual,hashes,source,len(protected),guide)
   if label=='Improve':
    # Shared field reporter binds literal worker cwd. Read those exact retained
    # metadata locations, then require every selected auxiliary byte to equal
    # the pristine pre-editor snapshot. The live export remains stale.
    auxiliary=timing.improve_auxiliary(actual,data,dict(source=str(source),source_hashes=hashes))
    assert all(p.sha(folder/relative)==pin for relative,pin in auxiliary['files_sha256'].items())
    proofs[name]['Default_field_PRL_auxiliary']=auxiliary
   metadata(folder,Path('deliveries')/label/name)
   facts.append(dict(packet=name,status=data.get('status'),accepted=data.get('accepted',data.get('export_accepted')),candidate_sha256=data['candidate_sha256'],Native_counts=[data['native'][key] for key in COUNTS],metrics=data['metrics']))
  assert p.sha(Path(exported['candidate']))==journal_row['candidate_sha256'] # Byte preservation only; live export remains stale.
  review=pinned_read(work/'review/review.json');choice=pinned_read(work/'choice/choice.json')
  assert review['receipt_sha256']==choice['receipt_sha256']==journal_row['route_sha256'] and choice['review_sha256']==pins[work/'review/review.json']
  assert choice['choice_recorded'] is True and choice['choice']=='accept' and choice['applied'] is False and choice['human_pcb_approval_observed'] is False
  metadata(work/'review',Path('deliveries')/label/'review');metadata(work/'review/plot-work',Path('deliveries')/label/'review-plot');metadata(work/'choice',Path('deliveries')/label/'choice')
  samples=commands(work,('preview','route','review','choice','export','verify_export','inspect-export'))
  deliveries.append(dict(role=journal_row['role'],workspace=str(work),source=str(source),source_hashes=hashes,settings=settings,candidate_sha256=journal_row['candidate_sha256'],Native_counts=journal_row['native'],protected_count=len(protected),preopen_sha256=journal_row['preopen_sha256'],postopen_sha256=journal_row['postopen_sha256'],snapshot_files=len(before_hashes),after_editor_changes=changes,live_export_stale=True,own_finals=proofs,packet_facts=facts,commands=samples,actual_GUI_observations=journal_row))
 cancel=j3['cancellation'];cw=h.real_path(cancel['workspace']);watch(cw)
 parent=pinned_read(cw/'route/result.json',cancel['parent_receipt_sha256']);engine=pinned_read(cw/'route/incumbent/engine-process.json',cancel['engine_receipt_sha256']);cli=pinned_read(cw/'route.command.process.json',cancel['CLI_receipt_sha256'])
 assert cancel['actual_GUI_Cancel_clicked'] is True and cancel['remaining_owned_group']==[] and cancel['no_review_choice_export'] is True and cancel['original_sources_unchanged'] is True
 assert engine==cancel['engine'] and engine['pid']==cancel['observed']['engine']['pid'] and engine['cancel_signal']=='SIGINT' and engine['status']=='cancelled' and engine['cleanup_complete'] is True and engine['exit_code']==0
 assert parent==cancel['parent'] and parent['status']=='cancelled' and parent['accepted'] is False and cli==cancel['CLI_process'] and cli['exit_code']==2 and cli['cancel_requested'] is True
 assert cancel['central_reader_refusal']=='Rejected: receipt is not an accepted routing result'
 assert not any(os.path.lexists(cw/name) for name in ('review','choice','export'))
 for key in ('failed_observer001','observer002'):
  row=cancel[key];observation=pinned_read(ROOT/row['path'],row['sha256'])
  bind(ROOT/'scripts/native_cancellation.py',observation['helper_sha256'])
  assert observation['actual_GUI_cancel'] is False # Observer sampled; the later button action is in journal003.
  if key=='failed_observer001':assert observation['observed'] is None
  else:assert observation['workspace']==str(cw) and observation['observed']==cancel['observed']
 metadata(cw/'route','cancellation/parent');metadata(cw/'route/incumbent','cancellation/incumbent');commands(cw,('preview','route'),allow_cancel=True)
 freshness=[];fc=BASE/'freshness-controls-001';fc_pre=pinned_read(fc/'preparation.json')
 assert fc_pre['prepared_state_sha256']==PINS[BASE/'prepared-state.json'] and fc_pre['original_hashes']==prepared['roles']['ordinary-alias2Cu']['source_hashes']
 watch(Path(fc_pre['source_original']),fc_pre['original_hashes'])
 for row in j4['freshness_controls']:
  kind=row['kind'];work=h.real_path(row['workspace']);watch(work);mutation=pinned_read(fc/(kind+'-mutation-001.json'),row['mutation_receipt_sha256'])
  assert row['actual_GUI_Route_refused'] is True and row['route_not_spawned'] is True and mutation['workspace']==str(work)
  assert not any(os.path.lexists(work/name) for name in ('route','route.command.log','route.command.process.json','review','choice','export'))
  bind(Path(mutation['path']),mutation['after_sha256'])
  assert mutation['before_sha256']!=mutation['after_sha256'] and mutation['GUI_Route_clicked_yet'] is False
  copy_hashes=watch(fc/(kind+'-copy'));commands(work,('preview',))
  if kind=='source':
   assert Path(mutation['path'])==fc/'source-copy'/Path(mutation['path']).name and mutation['before_sha256']==fc_pre['original_hashes'][Path(mutation['path']).name]
   expected=dict(fc_pre['control_copy_before']['source-copy']);expected[Path(mutation['path']).name]=mutation['after_sha256'];assert copy_hashes==expected
  else:
   assert Path(mutation['path'])==work/'settings.json' and copy_hashes==fc_pre['control_copy_before']['settings-copy']
   before=pinned_read(fc/'settings-captured-before.json',mutation['before_sha256']);assert pinned_read(work/'settings.json',mutation['after_sha256'])==before
  freshness.append(dict(observation=row,mutation=mutation,route_not_spawned=True,exact_queued_timing=False))
 rejection=j5['rejection'];rw=h.real_path(rejection['workspace']);watch(rw)
 rejected=pinned_read(rw/'route/result.json',rejection['route_sha256']);choice=pinned_read(rw/'choice/choice.json',rejection['choice_sha256'])
 for key in ('actual_Create_review','actual_Reject_clicked','choice_recorded','actual_GUI_Fresh_export_disabled','actual_GUI_Open_checked_export_disabled','export_absent','source_unchanged'):assert rejection[key] is True,key
 assert rejection['choice']=='reject' and rejection['applied'] is False and not os.path.lexists(rw/'export')
 assert rejected['accepted'] is True and rejected['candidate_sha256']==rejection['candidate_sha256'] and [rejected['native'][key] for key in COUNTS]==[0,0,0,0]
 assert choice['choice_recorded'] is True and choice['choice']=='reject' and choice['applied'] is False and choice['human_pcb_approval_observed'] is False and choice['receipt_sha256']==rejection['route_sha256']
 source=Path(rejection['source']);hashes=rejected['source_hashes'];watch(source.parent,hashes);original=p.sx.read(source);protected=p.protected_for_record(rejected,original);assert len(protected)==4
 assert rejected['source']==str(source) and rejected['tools']==tools and rejected['schematic_parity']=='checked by final native DRC' and rejected['invariants_unchanged'] is True
 candidate=Path(rejected['candidate']);tree=p.sx.read(candidate);assert p.sha(candidate)==rejection['candidate_sha256'] and p.immutable(tree)==p.immutable(original) and all(item in p.routes(tree) for item in protected)
 review=pinned_read(rw/'review/review.json');assert review['receipt_sha256']==rejection['route_sha256'] and choice['review_sha256']==pins[rw/'review/review.json'] and choice['validated_candidate_sha256']==rejection['candidate_sha256']
 guide=pinned_read(rw/'route/default-targets.json');assert pins[rw/'route/default-targets.json']==rejected['default_target_transport']['sha256']
 reject_proof=final_bridge(rejected,rw/'route',rw/'route',hashes,source,4,guide)
 for name in ('route','review','review/plot-work','choice'):metadata(rw/name,Path('rejection')/name)
 commands(rw,('preview','route','review','choice'))
 for name in ('gui090-preopen-via-high-001','gui090-preopen-improve-001','observe-gui090-cancel-001','observe-gui090-cancel-002'):
  path=ROOT/'.runs'/(name+'-time.log');value=timing.complete_cost(path);bind(path,value['time_log_sha256']);costs[name]=value
  bind(ROOT/'.runs'/(name+'.log'))
 launcher_cost=timing.complete_cost(Path(j6['launch_interval']['source']));assert launcher_cost==j6['launch_interval']
 bind(Path(launcher_cost['source']),launcher_cost['time_log_sha256'])
 costs['GUI090_launcher_interval']=dict(launcher_cost,scope=j6['accounting'])
 for path in (ROOT/'.runs/gui090-preopen-001.py',ROOT/'.runs/observe-gui090-cancel-001.py',ROOT/'.runs/observe-gui090-cancel-002.py',Path(__file__),ROOT/'LICENSE'):bind(path)
 # Select captured owned text only; source/candidate CAD, plots and ZIP never enter the queue.
 dependency_paths={ROOT/'evidence/gui-runtime057-090-ordinary-001.json',ROOT/'evidence/runtime057-native-milestone-001.json'}
 dependency_indexes={ROOT/row['files_index']['path'] for row in dependencies}
 for path in pins:
  if path in dependency_paths or path in dependency_indexes:continue
  if path.suffix in ('.json','.log','.py') or path.name=='LICENSE':add(path,Path('controls')/str(path.relative_to(ROOT)).replace('.runs/','retained-run/'))
 for folder,inventory in roots.items():
  for relative,pin in inventory.items():
   path=folder/relative
   if path not in queue:omitted.append(dict(original=str(path.relative_to(ROOT)),sha256=pin,reason='Unselected CAD/transport/plots/ZIP/cache or duplicate root witness remains local.'))
 omitted=list({row['original']:row for row in omitted}.values())
 def controls_fresh():
  for path,pin in pins.items():assert p.sha(path)==pin,str(path)
  for value in costs.values():assert p.sha(Path(value['source']))==value['time_log_sha256']
  for path,log,row in command_rows:assert p.sha(path)==row['receipt_sha256'] and p.sha(log)==row['log_sha256']
  for folder,inventory in roots.items():
   assert h.owned_destination(owners[folder])==folder and io.inventory(folder,max_bytes=64*1024**2)==inventory
   for relative in inventory:
    if Path(relative).suffix=='.kicad_prl':assert local.check_current_metadata(folder/relative)
  assert p.tool_manifest()==tools
  assert not any(os.path.lexists(Path(row['observation']['workspace'])/'route') for row in freshness)
  assert not os.path.lexists(rw/'export')
 known=set(refs);planned=count=0;sealed={}
 for path in queue:
  raw=io.read_bytes(path,4*1024**2);assert b'\0' not in raw;raw.decode('utf8');digest=hashlib.sha256(raw).hexdigest()
  expected=pins.get(path)
  if expected is None:
   found={inventory[str(path.relative_to(folder))] for folder,inventory in roots.items() if folder in path.parents and str(path.relative_to(folder)) in inventory};assert found=={digest}
  else:assert digest==expected
  sealed[path]=(len(raw),digest)
  if digest not in known:known.add(digest);planned+=len(raw);count+=1
 assert count<1998 and planned+sum(512+3*len(str(path))+3*len(str(name)) for path,name in queue.items())+len(json.dumps(omitted).encode())+512*1024<16*1024**2,'Split meaningfully before writing; never raise caps'
 controls_fresh();notes.mkdir()
 for path,name in queue.items():retain(path,name)
 controls_fresh()
 for path,(size,digest) in sealed.items():assert path.stat().st_size==size and p.sha(path)==digest
 index=notes/'files.json';index_data=dict(schema=1,files=files,material=material,omitted_local_hash_only=omitted)
 summary=dict(schema=1,kind='runtime057-GUI090-fixed-controls-deliveries-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=HEAD,runtime_manifest_sha256=MANIFEST,
  journals=[dict(path=str((ROOT/'.runs'/('gui090-observations-%03d.json'%n)).relative_to(ROOT)),sha256=PINS[ROOT/'.runs'/('gui090-observations-%03d.json'%n)]) for n in (3,4,5,6)],
  accepted=False,actual_GUI_observed=True,actual_GUI_qualified=False,full_GUI_claim=False,project_complete=False,human_review=False,physical_electrical_validation=False,
  deliveries=deliveries,cancellation=dict(workspace=str(cw),observed=cancel['observed'],actual_GUI_Cancel_clicked=True,engine_status=engine['status'],engine_exit_code=engine['exit_code'],cancel_signal=engine['cancel_signal'],cleanup_complete=True,CLI_exit_code=cli['exit_code'],parent_status=parent['status'],parent_accepted=False,sampled_remaining_owned_group=cancel['remaining_owned_group'],reader_refusal=cancel['central_reader_refusal'],failed_observer001=cancel['failed_observer001'],observer002=cancel['observer002'],scope=cancel['scope']),
  recovery=dict(actual_fresh_preview=j3['recovery']['actual_fresh_preview'],delivered_workspace=j4['improve']['workspace'],scope='Fresh preview after the cancelled job, then the separately bound Improve delivery; cancelled job was not reused or accepted.'),
  freshness_controls=freshness,preset_mismatch_refusal=j4['preset_mismatch_refusal'],rejection=dict(observation=rejection,own_final=reject_proof,export_absent=True),
  normal_close=dict(actual_idle_GUI_closed_normally=True,actual_idle_manager_quit_normally=True,original_sources_unchanged=True,process_absence_scope='Owned processes absent at the recorded snapshot only; no permanent absence claim.'),
  accounting=dict(command_samples=[row for _,_,row in command_rows],command_wall_sum_seconds=sum(row['sample']['wall_seconds'] for _,_,row in command_rows),command_CPU_seconds=None,complete_external_records=costs,whole_interactive_wall_seconds=None,whole_interactive_CPU_seconds=None,scope='Per-command, Native, parent/incumbent/trial/export samples overlap; do not add them. GUI090 launcher interval2222.97wall/186.91CPU includes interactive pauses and some descendant samples; it is not full GUI/subprocess/authoring/AI CPU or a fair benchmark, and must not be added to overlapping CLI costs. Other complete helper exits remain separately addressable. Interactive/orchestration/authoring/AI/curation overhead is additional and partly unmetered, unknown not zero.'),
  dependencies=dependencies,pending=dict(exact_forced_queued_callback_timing=True,fresh_root_GUI=True,full_GUI_qualification=True),
  scope='Only fixed current057 GUI090 journals003–006: explicit high-via partial90 delivery, one narrow Improve90 delivery with incumbent/one actual trial/parent/export own Native proof, observed incumbent-engine Cancel and fresh recovery, two pre-route freshness/no-spawn refusals, a fresh Native-valid Reject/export-disabled control and normal closing. Preserved snapshots provide pre-editor proof; live post-editor exports remain stale. No current Native/production reader rerun or all-phase/permanent absence, natural-expiry/all-failure, broader customization/family/quality/electrical/human/Windows/standalone/release/restoration claim. GUI091 is outside this packet.',
  publication=dict(new_files=len(files),new_bytes=total,material_rows=len(material),file_cap=4*1024**2,packet_cap=16*1024**2,file_count_cap=2000,scope='Small project-owned metadata/log/PRL/net/controller/journal/time text only. No CAD, SVG/HTML/pixels/plots/ZIP, engines/apps, private or foreign payload. New raw/preopen exports remain Mac-only/outside010; public facts are not a full raw backup.'),
  curation=dict(sampled_wall_seconds=time.monotonic()-start,sampled_parent_CPU_seconds=time.process_time()-cpu0,complete_external_exit_not_included=True,Native_executed=False,production_readers_rerun=False))
 assert len(json.dumps(index_data,indent=2).encode())<4*1024**2 and len(json.dumps(summary,indent=2).encode())+1024<4*1024**2
 assert total+len(json.dumps(index_data,indent=2).encode())+len(json.dumps(summary,indent=2).encode())+1024<16*1024**2
 controls_fresh();p.save_json(index,index_data)
 summary['files_index']=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))
 controls_fresh();p.save_json(target,summary);controls_fresh()
 print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,material=len(material),actual_GUI_qualified=False,Native_executed=False)))
if __name__=='__main__':main()
