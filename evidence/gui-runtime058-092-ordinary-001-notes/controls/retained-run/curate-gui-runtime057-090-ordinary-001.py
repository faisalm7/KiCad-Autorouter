"""DRAFT: retain the fixed057/090 ordinary GUI job; never execute readers/Native.

Narrow ordinary-only port of050 progress curation. Reuse unchanged030 retain,
042 own_final dual storage/actual-path binding, and public complete-exit parser.
The preserved preopen export supplies proof bytes. The editor-modified live
export remains stale; later jobs/session activity are outside this fixed scope.
"""
from pathlib import Path
import ast,datetime,hashlib,json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
from scripts import report_current_comparison as timing
RUNTIME=ROOT/'.runs/runtime-directory-057/runtime';BASE=RUNTIME/'.runs/gui-session090'
WORK=BASE/'jobs/autorouter-gui-196c63415c964d58997ee708d5e844bd';CONTROL=BASE/'preopen-ordinary-001'
HEAD='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
MANIFEST='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
PREPARED='dbc6ee9297c396aeedb5ee38a2a7ecafd9330b3d90dd68f94926cdd672804ed3'
ROUTE='dd40bf8b3dc676b3aab0d992148886e221d117fa6b19f666bf94795facbb8b86'
EXPORT='b282626a5755a6dd44d368ecbfa62b1cf59636aa9c90ade361a5ddad4eeaf7ed'
CANDIDATE='52b47dcb4482a4f16e8f8c1b3bfc1c6d42e257fca9d07babc96dd745e202164f'
PREOPEN='20a1443890743074403980299f5e28fb8c0b7b2a2bda5b93840a237580d55cda'
POSTOPEN='1aa9985c360f14d4c9cd2d16ae5ab4ab30d5b0207c2fe3c1dbc72d5447f834c6'
SETTINGS='a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65'
JOB_SETTINGS='2258e809e1efc6a1020ef0f55f2f63eecb5ebc126f6ae3d554658e94a5753880'
RETENTION=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
FINAL_HELPER=ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
TEMPLATE=ROOT/'.runs/curate-gui-runtime050-086-progress-001.py'
DEPENDENCY=ROOT/'evidence/runtime057-native-milestone-001.json'
PINS={RETENTION:'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',
 FINAL_HELPER:'340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',
 TEMPLATE:'43d7e1df052bdc1deed858ce72f85402cfb8b4da770c1cda06a18b309a2997d5',
 Path(timing.__file__):'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e',
 DEPENDENCY:'37620250ac71559915a80873be8d9cfc36c4d65853fd337fa5537e0eac904eb9',
 BASE/'prepared-state.json':PREPARED,
 BASE/'protocol-required-001.json':'8592d9c2447ff167dcece866796a2c1a81b355fa88b42fae15f61254cdefe37e',
 ROOT/'.runs/gui090-observations-001.json':'2dd0707db7d0fac3a9741b7972d84a39186bb9513071e5b0c7f447127f6a241d',
 ROOT/'.runs/gui090-observations-002.json':'684352159f6aaa100cef3ecbfe908eb59fc3fecd293e71524d9ae0b8feb4a691',
 CONTROL/'preopen.json':PREOPEN,CONTROL/'postopen-001.json':POSTOPEN,
 WORK/'route/result.json':ROUTE,CONTROL/'export/export.json':EXPORT,
 ROOT/'.runs/gui090-preopen-001.py':'0dbfa7831bf1745cdb42bef5c7ac41f13d2b2817f1b9f66a890ef71611c95006',
 ROOT/'.runs/prepare-runtime057-gui090.py':'3f57631308e333f6589023c36448d215a88cccda639e2513c234b3f7d9c0b708',
 ROOT/'.runs/prepare-runtime057-gui090.draft.json':'3e5b4d6ee6cd80a259aee11c5999b505d9afec28ec7560aa9f94a64b21edfe98'}
COMMANDS={'choice.command.process.json':'a9535ecde49c8e025b15d38537c147a600135e502fdf82a4c5d0637fb8599c47',
 'export.command.process.json':'d6c03a4c61b480a9ac03a70bb43172d1ea1cf0534adb2af7573c2892eaa85cc2',
 'inspect-export-2fc19e1beaaf47d0b43261cf5626abaa.command.process.json':'b500b671955a841947b4f4d93c87d3c3dc6f37efe8eca1e8e06755f2e4ea489b',
 'inspect-export-7da6296120da4558964af780caf89108.command.process.json':'d1493afe7ecd33f9dc5eebecff1964a48edf100411a94ff041aaf1d36552721f',
 'preview.command.process.json':'d8e3ccbe92c211d679f9d2e72b34c1688242c89c58f2d8c6dd493f018bbda454',
 'review.command.process.json':'9f350e974035e53f460e13046d48fde93a78b51a3b14a8a959ba46e9665a3c3f',
 'route.command.process.json':'e15747621d501f96d29e6b9e03150d8cefe409edce241db92f688d39e822ea8e',
 'verify_export.command.process.json':'42a5033e7fe6eb403b0fb200e713b9edbf70184a9ad1e83d8e8d26e8b6a98470'}
STALE='inspect-export-7da6296120da4558964af780caf89108.command.process.json'
COUNTS=('opens','blocking','warnings','exclusions')

def load_functions(path,names):
 nodes=[n for n in ast.parse(io.read_bytes(path,4*1024**2)).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::unchanged-shared','exec'),globals())

def main():
 global notes,refs,files,material,total
 start=time.monotonic();cpu0=time.process_time();stem='gui-runtime057-090-ordinary-001'
 notes=ROOT/'evidence'/(stem+'-notes');output=ROOT/'evidence'/(stem+'.json')
 assert not os.path.lexists(notes) and not os.path.lexists(output), 'Fresh packet; preserve any partial failure'
 control_pins=tuple(PINS.items());commands=tuple(COMMANDS.items())
 for path,pin in control_pins:assert p.sha(path)==pin,str(path)
 load_functions(RETENTION,('retain',));load_functions(FINAL_HELPER,('read','own_final'));cost=timing.complete_cost
 prepared=read(BASE/'prepared-state.json');protocol=read(BASE/'protocol-required-001.json')
 first=read(ROOT/'.runs/gui090-observations-001.json');second=read(ROOT/'.runs/gui090-observations-002.json')
 for j in (first,second):
  assert j['runtime']=='057' and j['session']=='090' and j['actual_GUI'] is True and j['project_complete'] is False
  assert j['source_head']==HEAD and j['manifest_sha256']==MANIFEST and j['human_review'] is False
 assert first['prepared_state_sha256']==PREPARED and first['toolbar_launch'] is True and first['workspace']==str(WORK)
 assert second['previous']['sha256']==PINS[ROOT/'.runs/gui090-observations-001.json']
 ordinary=second['ordinary'];assert ordinary['role']=='ordinary-alias2Cu' and ordinary['workspace']==str(WORK)
 for key in ('rendered_Edge_F_B_before_after_images','actual_review_project_opened','accept_without_ack_refused_route_retained',
  'accept_with_review_manager_open_refused_route_retained','review_closed_using_FileCloseProject','actual_ack_accept_recorded',
  'fresh_export_and_check_completed','actual_checked_export_manager_and_PCB_open','PCB_closed_without_save',
  'export_manager_closed_using_FileCloseProject','stale_editor_modified_export_refused','positive_controls_cleared','source_original_unchanged'):
  assert ordinary[key] is True,key
 assert ordinary['route_sha256']==ROUTE and ordinary['export_sha256']==EXPORT and ordinary['candidate_sha256']==CANDIDATE
 assert ordinary['native']==[0,0,0,0] and ordinary['protected']==4 and ordinary['observed_unrouted']==0
 assert ordinary['preopen_sha256']==PREOPEN and ordinary['postopen_sha256']==POSTOPEN
 for data in (prepared,protocol):assert data['source_head']==HEAD and data['runtime_manifest_sha256']==MANIFEST
 assert p.sha(RUNTIME/'runtime-distribution.json')==MANIFEST
 for name,pin in prepared['tools']['implementation_sha256'].items():assert p.sha(RUNTIME/name)==pin
 for name,pin in prepared['prerequisite_sha256'].items():assert p.sha(Path(name))==pin
 role=prepared['roles']['ordinary-alias2Cu'];assert role==protocol['roles']['ordinary-alias2Cu'] and role['method']=='route'
 source=Path(role['source']);hashes=role['source_hashes'];assert source==BASE/'project/owned1007-transport.kicad_pcb'
 assert io.inventory(source.parent)==io.inventory(Path(role['original_source']).parent)==hashes
 settings=dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
 assert read(WORK/'settings.json')==read(Path(role['settings_path']))==role['settings']==settings
 assert p.sha(WORK/'settings.json')==JOB_SETTINGS and p.sha(Path(role['settings_path']))==SETTINGS
 saved=BASE/'gui090-saved-settings-001.json';assert p.sha(saved)==SETTINGS and read(saved)==settings
 pre=read(CONTROL/'preopen.json');post=read(CONTROL/'postopen-001.json');before=CONTROL/'export'
 before_hashes=io.inventory(before,max_bytes=64*1024**2);assert before_hashes==pre['snapshot_hashes'] and len(before_hashes)==90
 assert pre['runtime']=='057' and pre['session']=='090' and pre['role']=='ordinary-alias2Cu'
 assert pre['snapshot']==str(before) and pre['workspace']==str(WORK) and pre['source']==str(source)
 assert pre['source_hashes']==hashes and pre['source_unchanged'] is True and pre['settings_sha256']==JOB_SETTINGS
 assert pre['source_head']==HEAD and pre['runtime_manifest_sha256']==MANIFEST
 assert pre['controller_sha256']==PINS[ROOT/'.runs/gui090-preopen-001.py'] and pre['actual_GUI_opening'] is False
 assert pre['route']['current'] is True and pre['export']['current'] is True and pre['export']['fresh_native_run_performed_by_check'] is False
 assert post['preopen_sha256']==PREOPEN and post['snapshot_unchanged'] is True and post['source_unchanged'] is True
 assert post['actual_GUI'] is True and post['actual_export_manager_and_PCB_opened'] is True and post['actual_PCB_closed_without_save'] is True
 assert post['actual_manager_FileCloseProject'] is True and post['PCB_bytes_unchanged'] is True and post['positive_proof_not_renewed'] is True
 current=io.inventory(WORK/'export',max_bytes=64*1024**2)
 changes=[dict(path=n,before=before_hashes.get(n),after=current.get(n)) for n in sorted(set(before_hashes)|set(current)) if before_hashes.get(n)!=current.get(n)]
 assert current==post['current_export_inventory'] and changes==post['changes'] and len(changes)==3
 assert sorted(Path(row['path']).suffix for row in changes)==['.kicad_prl','.kicad_pro','.zip']
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
 assert p.sha(idx)==dep['files_index']['sha256']=='1965f5fa09bcbb4ac44d7f010851e69f0e36c1c016c0a04564fed8438b9cfa09'
 for row in read(idx)['files']:refs.setdefault(row['sha256'],row['path'])
 for row in read(idx)['material']:refs.setdefault(row['sha256'],row['retained'])
 queue={};roots={};samples=[]
 def add(path,name):
  path=Path(path);name=Path(name);assert path.is_file() and not path.is_symlink() and ROOT in path.parents
  assert not name.is_absolute() and '.runs' not in name.parts and '..' not in name.parts
  queue.setdefault(path,name)
 def metadata(folder,name):
  inv=io.inventory(folder,max_bytes=64*1024**2);roots[folder]=inv
  for rel in inv:
   path=folder/rel;parts=Path(rel).parts
   if (len(parts)==1 and path.suffix in ('.json','.log','.net')) or (len(parts)==2 and parts[0] in ('final-drc-input','refill-drc-input','source-drc-input') and path.suffix=='.kicad_prl'):
    add(path,Path(name)/rel)
 for path in PINS:add(path,Path('controls')/str(path.relative_to(ROOT)).replace('.runs/','retained-run/'))
 add(RUNTIME/'runtime-distribution.json','runtime/runtime-distribution.json');add(Path(__file__),'curation/'+Path(__file__).name);add(ROOT/'LICENSE','rights/LICENSE')
 add(WORK/'settings.json','settings/job-settings.json');add(Path(role['settings_path']),'settings/route-settings.json');add(saved,'settings/gui090-saved-settings-001.json')
 add(before/'export.json','before-open/export/export.json')
 metadata(WORK/'route','job/route');metadata(before/'validation','before-open/export/validation')
 metadata(WORK/'review','job/review');metadata(WORK/'review/plot-work','job/review/plot-work');metadata(WORK/'choice','job/choice')
 for name,pin in commands:
  path=WORK/name;assert p.sha(path)==pin;proc=read(path);log=path.with_name(path.name.replace('.process.json','.log'))
  assert proc['argv'][:4]==[str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter']
  assert proc['cancel_requested'] is False and proc['log_truncated'] is False and log.stat().st_size==proc['log_bytes']
  if name==STALE:
   assert proc['exit_code']==2 and read(log)==dict(current=False,reason='export inputs/runtime/evidence changed')
   assert str(log)==ordinary['stale_log']
  else:assert proc['exit_code']==0
  samples.append(dict(command=name,receipt_sha256=pin,log_sha256=p.sha(log),sample=proc))
  add(path,Path('commands')/path.name);add(log,Path('commands')/log.name)
 for name in ('prepare-runtime057-gui090-001.log','prepare-runtime057-gui090-001-time.log','gui090-preopen-ordinary-001.log','gui090-preopen-ordinary-001-time.log'):
  add(ROOT/'.runs'/name,Path('costs')/name)
 for name in ('prepare-launcher.log','prepare-launcher-process.json'):add(BASE/name,Path('setup')/name)
 measured={name:cost(ROOT/'.runs'/name) for name in ('prepare-runtime057-gui090-001-time.log','gui090-preopen-ordinary-001-time.log')}
 def controls_fresh():
  for path,pin in control_pins:assert p.sha(path)==pin,str(path)
  for row in measured.values():assert p.sha(Path(row['source']))==row['time_log_sha256']
  for row in samples:
   path=WORK/row['command'];log=path.with_name(path.name.replace('.process.json','.log'))
   assert p.sha(path)==row['receipt_sha256'] and p.sha(log)==row['log_sha256']
 omitted=[dict(original=str((folder/rel).relative_to(ROOT)),bytes=(folder/rel).stat().st_size,sha256=pin,reason='CAD/transport/plots/HTML/SVG/config/code/cache stays local; selected metadata retained separately.') for folder,inv in roots.items() for rel,pin in inv.items() if folder/rel not in queue]
 omitted += [dict(original=str((WORK/'export'/row['path']).relative_to(ROOT)),bytes=(WORK/'export'/row['path']).stat().st_size,sha256=row['after'],reason='Editor-created backup ZIP bytes omitted; observed hash only.') for row in changes if Path(row['path']).suffix=='.zip']
 known=set(refs);planned=count=0;sealed={}
 for path in queue:
  raw=io.read_bytes(path,4*1024**2);assert b'\0' not in raw;raw.decode('utf-8');pin=hashlib.sha256(raw).hexdigest();sealed[path]=(len(raw),pin)
  if pin not in known:known.add(pin);planned+=len(raw);count+=1
 assert planned<16*1024**2 and count<2000,('Split before writing; never raise caps',planned,count)
 controls_fresh()
 notes.mkdir()
 for path,name in queue.items():retain(path,name)
 controls_fresh()
 for path,(size,pin) in sealed.items():assert path.stat().st_size==size and p.sha(path)==pin
 for folder,inv in roots.items():assert io.inventory(folder,max_bytes=64*1024**2)==inv
 assert io.inventory(source.parent)==io.inventory(Path(role['original_source']).parent)==hashes
 assert io.inventory(before,max_bytes=64*1024**2)==before_hashes and io.inventory(WORK/'export',max_bytes=64*1024**2)==current
 # No assertion over BASE/jobs or other roles: later independent jobs may exist.
 controls_fresh()
 index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted=omitted))
 summary=dict(schema=1,kind='runtime057-GUI090-assigned-ordinary-role-only-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  source_head=HEAD,runtime_manifest_sha256=MANIFEST,prepared_state_sha256=PREPARED,
  journals=[dict(path='.runs/gui090-observations-00'+str(i)+'.json',sha256=PINS[ROOT/('.runs/gui090-observations-00'+str(i)+'.json')]) for i in (1,2)],
  assigned_ordinary_role_recorded=True,actual_GUI_observed=True,actual_GUI_qualified=False,full_GUI_claim=False,Improve_qualified=False,project_complete=False,human_review=False,physical_electrical_validation=False,
  workspace=str(WORK),source=str(source),source_hashes=hashes,source_unchanged=True,settings=settings,job_settings_sha256=JOB_SETTINGS,saved_settings_sha256=SETTINGS,
  settings_serialization='Prepared/saved preset bytes and job serialization differ; decoded settings are equal.',candidate_sha256=CANDIDATE,protected_original_items=4,native=route['native'],metrics=route['metrics'],own_final_bindings=own,
  before_open=dict(snapshot=str(before),files=90,receipt_sha256=PREOPEN,current_production_readers_then=True,new_Native_run_by_curator=False,actual_to_preserved_mapping={str(WORK/'export'):str(before)}),
  after_open=dict(receipt_sha256=POSTOPEN,files=len(current),changes=changes,candidate_PCB_unchanged=True,actual_checked_opening=True,closed_without_save=True,current_export_stale_refusal_recorded=True,new_Native_validity_inferred=False,exact_CallAfter_queue_proved=False),
  actual_GUI_observations=dict(initial_setup_and_static=first['observations'],ordinary=ordinary,setup=first['setup'],automation=first['automation']),
  pending_at_cutoff=dict(via_high_GUI=True,Improve_GUI=True,explicit_Reject=True,active_Cancel=True,recovery=True,source_settings_freshness_refusals=True,forced_queued_timing=True,fresh_root_GUI=True),
  accounting=dict(CLI_command_samples=samples,CLI_command_wall_sum_seconds=sum(r['sample']['wall_seconds'] for r in samples),CLI_command_CPU_seconds=None,whole_interactive_wall_seconds=None,whole_interactive_CPU_seconds=None,
   nested_route=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),nested_export=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']),additional_measured_helpers=measured,
   raw_journal_costs=[first['costs'],second['costs']],limitation='Per-stage CLI/nested Native costs overlap and are not added. Full interactive/UI/authoring/AI CPU and wall remain additional unknown, not zero; no fair performance comparison.'),
  dependency=dict(path=str(DEPENDENCY.relative_to(ROOT)),sha256=PINS[DEPENDENCY],files_index=dep['files_index'],scope='Owned source rights and same-byte mechanics only; current cohort or prior GUI outcomes do not transfer this job proof.'),
  publication=dict(new_files=len(files),new_bytes=total,material_rows=len(material),file_cap=4*1024**2,packet_cap=16*1024**2,file_count_cap=2000,scope='Owned metadata/log/net/PRL and shared controller code only; no CAD, pixels, plots, ZIP bytes, engines/apps or caches. Raw preopen snapshot is Mac-only/outside010, not a full restore copy.'),
  limitations='One fixed ordinary partial90 default-score GUI job only. Lead observed toolbar, Edge F+B, review acknowledgement/open-project guards, Accept, fresh export and checked KiCad opening0unrouted, then editor-metadata stale refusal. No current validity inferred after editor, independent human/electrical approval, full057GUI, Improve, cancellation, exact queued timing, fresh-rootGUI, quality gain, comparison, Windows or standalone/release/restoration claim.',
  curation=dict(sampled_wall_seconds=time.monotonic()-start,sampled_parent_CPU_seconds=time.process_time()-cpu0,complete_external_exit_not_included=True,Native_executed=False,production_readers_rerun=False),
  files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
 controls_fresh()
 p.save_json(output,summary)
 controls_fresh()
 print(json.dumps(dict(output=str(output),sha256=p.sha(output),files=len(files),bytes=total,material=len(material),actual_GUI_qualified=False,Native_executed=False)))
if __name__=='__main__':main()
