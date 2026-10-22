"""Retain EEPROM intake facts only, using030 text retention and shared costs.

Foreign CAD/README, raw Native findings and field values remain hash-only.
No acquisition, Preview, Native, acceptance reader or routing is executed here.
"""
from pathlib import Path
import ast,collections,datetime,hashlib,json,math,os,re,stat,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,provenance as pv
B=ROOT/'.runs/development-eeprom-001';DATA=ROOT/'.data/development-eeprom-001';N=B/'native-original-001'
notes=ROOT/'evidence/development-eeprom-001-notes';OUTPUT=ROOT/'evidence/development-eeprom-001.json'
assert not any(os.path.lexists(path) for path in (notes,OUTPUT))
pins={};queue={};refs={};files=[];material=[];total=0
def bind(path,expected=None):
    path=Path(path);raw=io.read_bytes(path,4*1024**2);pin=hashlib.sha256(raw).hexdigest()
    if expected is not None:assert pin==expected,str(path)
    if path in pins:assert pins[path]==pin,str(path)
    else:pins[path]=pin
    return raw
def read(path,expected=None):return json.loads(bind(path,expected),object_pairs_hook=pv._strict_object)
def add(path,name):queue.setdefault(Path(path),Path(name))
def omitted(path,reason):
    raw=bind(path);return dict(path=str(path.relative_to(ROOT)),sha256=pins[path],bytes=len(raw),reason=reason)
owners={path:(path.stat().st_dev,path.stat().st_ino,path.stat().st_uid) for path in (B,DATA,DATA/'project',B/'reference-project',N)}
SHARED=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
COST=ROOT/'scripts/report_current_comparison.py'
nodes=[n for n in ast.parse(bind(SHARED,'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1')).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
assert len(nodes)==1;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SHARED),'exec'),globals())
nodes=[n for n in ast.parse(bind(COST,'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e')).body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','complete_cost')]
assert len(nodes)==3;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(COST),'exec'),globals())
def cost(path):
    bind(path);value=complete_cost(path);assert value['time_log_sha256']==pins[path] and value['source']==str(path)
    bind(path,value['time_log_sha256']);return value
protocol_path=ROOT/'.runs/acquire-development-eeprom-001-protocol.json'
plan=read(protocol_path,'1cb01715549fb08ef88077b444191c3cb2f143c4854c4fa03ae59bfacac81a95')
lead=read(ROOT/'.runs/development-eeprom-lead-001.json','69f18043c8f3173d2659bfb49b8f6c8a72d48059db7413fc9fe186344643a1d4')
acquired=read(B/'acquisition.json','18d61396200305f9090d5ed41ed8bccfafde0d34bb3af383cac4257ad692c3ae')
inspection=read(B/'inspection.json','b3db2c3796ebb9933ce5cb67266abb30fb1c7e6cb26a3bf1f529cd46965feed4')
reference=read(B/'reference-copy.json','7d97724572753e5ab88fc42b3c73b3052b6b788e20c9aa237c10b2231e8e0c19')
preview=read(B/'installed-preview.log','dd026c02d1ad4324d2572e601467662b22a5e3ffce7808391685f48364e3c0f9')
native=read(N/'result.json','e14ee05340b79b2acf268dc3032f304da8806b6f398a3f7629f204b9ec196137')
assert plan['repository']==acquired['repository']=='WestianPKl/pcb-docs' and plan['commit']==acquired['commit']=='b89a09c2e95cc0a6954d0576389f07868b80c1ad'
assert acquired['source_exact'] is True and inspection['source_unchanged'] is True and acquired['requests_actual']==4 and acquired['received_bytes']==360526
assert acquired['protocol_sha256']==inspection['protocol_sha256']==pins[protocol_path] and inspection['acquisition_sha256']==pins[B/'acquisition.json']
assert all(row['http_status']==200 and row['status']=='response_received' and row['url']==row['final_url'] for row in acquired['requests'])
originals=[];omissions=[]
for row in plan['rows']:
    path=DATA/row['destination'];raw=bind(path,row['sha256']);info=path.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and not info.st_mode&0o222
    assert len(raw)==row['bytes'] and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha1']
    assert acquired['files'][row['destination']]==dict(bytes=len(raw),sha256=pins[path])
    originals.append(dict(source_path=row['source_path'],url=row['raw_url'],git_blob_sha1=row['git_blob_sha1'],sha256=pins[path],bytes=len(raw)))
    omissions.append(omitted(path,'Foreign native source or full publisher README; public metadata/hash only.'))
assert sum(row['bytes'] for row in originals)==360526 and len(originals)==4
assert reference['hashes']==native['source_hashes'] and native['source_unchanged'] is True
for name,pin in reference['hashes'].items():bind(B/'reference-project'/name,pin)
assert preview['status']=='preview' and preview['static_preflight_passed'] is True and preview['native_validation_performed'] is False
assert preview['source_sha256']==reference['hashes']['EEPROM_Board.kicad_pcb'] and preview['existing_route_items']==123 and preview['protected_route_items']==0
assert native['status']=='completed' and native['Native'] is True and native['accepted'] is False and native['routing_attempted'] is False
assert [native['native'][key] for key in ('opens','blocking','warnings','exclusions')]==[0,0,36,0] and native['source_native_policy'] is True and native['source_native_reasons']==[]
report=read(N/'original-drc.json','6d9f6f9cb7b3434d8115e36d47b4f669501acb3f220b554de658ffe4ae0c8bfc')
binding=read(N/'original-drc-binding.json','0241eda2fd124645edab9fcc197ec96d42579ea517c9700a0f8e16a0457fd978')
guard=read(N/'original-drc-fields-local-settings.json','eb5c6e8fa75d513f0311afe66f1ed3ec0c03bd63a8b3874b8d066e7d001f6b49')
assert report['kicad_version']=='10.0.7' and set(report['included_severities'])=={'error','warning','exclusion'}
assert report['unconnected_items']==[] and report['violations']+report['schematic_parity']==native['native']['findings']
assert all(row['severity']=='warning' for row in native['native']['findings']) and len(native['native']['findings'])==36
assert binding['source']==native['source'] and binding['before']==reference['hashes'] and binding['saved'] is False
assert all(binding['after'][name]==pin for name,pin in reference['hashes'].items())
assert guard['before']==guard['after']==binding['after'] and guard['protection']['flags_restored'] is True and guard['protection']['bytes_unchanged'] is True
field=native['native']['field_parity'];qualified=field['qualification']
assert qualified['qualified'] is True and field['native_report_sha256']==pins[N/'original-drc.json'] and field['binding_sha256']==pins[N/'original-drc-binding.json'] and field['local_settings_guard_sha256']==pins[N/'original-drc-fields-local-settings.json']
steps=[]
for name in ('original-drc','original-drc-fields-netlist','original-drc-fields-audit'):
    process_path=N/(name+'-process.json');process=read(process_path)
    assert process['cleanup_complete'] is True and process['log_truncated'] is False and process['cwd']==str(N)
    assert process['status']==('nonzero_exit' if name=='original-drc' else 'success') and type(process['exit_code']) is int and process['exit_code']==(5 if name=='original-drc' else 0)
    step=next(row for row in native['steps'] if row['name']==name)
    assert all(step[key]==process[key] for key in ('argv','status','exit_code','cwd','cleanup_complete','log_truncated'))
    if name=='original-drc':assert '--schematic-parity' in process['argv'] and '--refill-zones' in process['argv'] and str(N/'original-drc.json') in process['argv'] and process['argv'][-1]==binding['input']
    steps.append(dict(name=name,process_sha256=pins[process_path],status=process['status'],exit_code=process['exit_code'],cleanup_complete=True,log_truncated=False))
    add(process_path,Path('native-original')/process_path.name);add(Path(process['log']),Path('native-original')/Path(process['log']).name)
assert len(native['steps'])==3
costs={}
for phase,time_path in (('acquisition',ROOT/'.runs/acquire-development-eeprom-001-time.log'),('static_inspection',ROOT/'.runs/inspect-development-eeprom-001-time.log'),('installed_static_preview',B/'installed-preview-time.log'),('original_project_Native',B/'native-original-probe-001-time.log')):
    costs[phase]=cost(time_path);add(time_path,Path('costs')/time_path.name)
for phase in ('acquire','inspect'):
    process=read(B/(phase+'-process.json'));assert process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
for path in (protocol_path,ROOT/'.runs/acquire-development-eeprom-001.py',ROOT/'.runs/acquire-development-eeprom-001-reviewed-draft001.py',ROOT/'.runs/acquire-development-eeprom-001-protocol-reviewed-draft001.json',ROOT/'.runs/acquire-development-eeprom-001.log',ROOT/'.runs/inspect-development-eeprom-001.log',B/'acquisition.json',B/'acquire-process.json',B/'inspect-process.json',B/'acquire.log',B/'inspect.log',B/'installed-preview.log',B/'reference-copy.json',B/'route-settings.json',B/'native-original-probe-001.py',B/'native-original-probe-001.log',N/'original-drc-binding.json',N/'original-drc-fields-local-settings.json',Path(__file__).resolve()):add(path,Path('retained-run')/path.name)
for name in ('result.json','original-drc.json','original-drc-fields-proof.json','original-drc-fields.json','original-drc-fields.net'):
    omissions.append(omitted(N/name,'Raw original-source Native/field findings or source field/netlist values remain private; sanitized scalar summary only.'))
omissions += [omitted(B/'inspection.json','Detailed source geometry/model/requirement observations remain private.'),omitted(ROOT/'.runs/development-eeprom-lead-001.json','Prospective research lead includes source-derived strings; selected safe provenance facts only.')]
for name,pin in plan['material_sha256'].items():bind(ROOT/name,pin)
runtime=ROOT/'.runs/runtime-directory-057/runtime';bind(runtime/pv.MANIFEST,'9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e')
assert native['tools']['source_provenance']['git_head']=='ac1a48c3b25b2217e0f8252e0e6da21905f144a4' and native['tools']['source_provenance']['manifest_sha256']==pins[runtime/pv.MANIFEST]
planned=[];planned_material=[];known={};planned_bytes=0
for path,name in queue.items():
    raw=bind(path);assert b'\0' not in raw;raw.decode('utf8');pin=pins[path]
    if pin not in known:
        known[pin]=str((notes/name).relative_to(ROOT));planned.append(dict(path=known[pin],sha256=pin,bytes=len(raw)));planned_bytes+=len(raw)
    planned_material.append(dict(original=str(path.relative_to(ROOT)),retained=known[pin],bytes=len(raw),sha256=pin))
index=notes/'files.json';index_data=dict(schema=1,files=planned,material=planned_material,omitted_hash_only=omissions)
index_raw=(json.dumps(index_data,indent=2)+'\n').encode();index_pin=hashlib.sha256(index_raw).hexdigest()
summary=dict(schema=1,kind='development-eeprom-acquisition-static-preview-and-original-Native-facts-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='intake_cutoff_complete_no_routing_result',repository='https://github.com/'+plan['repository'],source_revision=plan['commit'],split='development-exposed',originals=originals,rights=dict(publisher=plan['rights']['publisher'],declared_hardware_license='CERN-OHL-P-2.0',basis='Pinned publisher README designation; no legal/title certification.',README_sha256=acquired['files']['README.md']['sha256'],license_body=plan['license_body'],asset_title_model_and_ancestry_closure=False,raw_publication_authorized=False),acquisition=dict(requests=4,all_HTTP_200=True,bytes=360526,source_files_exact_unchanged=True,redirects=False,retries=0,external_scripts_executed=False,models_or_extra_files_downloaded=False,prospective_protocol_draft_flags_preserved=True,actual_success_process_receipts_retained=True),static=dict(pcb_format=inspection['pcb_format'],schematic_format=inspection['schematic_format'],copper=['F.Cu','B.Cu'],footprints=inspection['footprints'],pads=inspection['pads'],pad_types=inspection['pad_types'],routes=inspection['route_counts'],zones=inspection['zones'],original_protected_routes=0,custom_pads=0,netclass_count=len(inspection['original_net_settings']['classes']),netclass_names=[row['name'] for row in inspection['original_net_settings']['classes']],schematic_flat=True,missing_embedded_definitions=0,external_models_declared=inspection['external_models_summary']['unique'],models_acquired=0,constraints_removed=False),installed_preview=dict(static_preflight_passed=True,Native_performed=False,settings=preview['effective_preferences'],existing_routes=123,protected_routes=0,standalone_process_receipt_present=False,scope='Stored CLI Preview output plus complete exit cost; no new Preview or candidate validation.'),original_Native=dict(executions=1,source_unchanged=True,Native_counts=[0,0,36,0],warning_type_counts=dict(collections.Counter(row['type'] for row in native['native']['findings'])),ignored_check_count=len(native['native']['ignored_checks']),ignored_check_keys=[row['key'] for row in native['native']['ignored_checks']],full_schematic_flag=True,refill_requested=True,source_native_policy=True,field_qualification=dict(qualified=True,policy=qualified['policy'],components=qualified['component_count'],compared_fields=qualified['compared_field_count']),processes=steps,raw_result_sha256=pins[N/'result.json'],raw_report_sha256=pins[N/'original-drc.json'],binding_sha256=pins[N/'original-drc-binding.json'],field_PRL_guard_sha256=pins[N/'original-drc-fields-local-settings.json'],scope='Original already-routed project on exact preserved copy only. Zero original opens is not zero rerouting demand, candidate acceptance or whole-project/electrical cleanliness;36warnings/7ignored remain.'),costs=costs,measured_listed_phase_totals=dict(wall_seconds=round(sum(v['wall_seconds'] for v in costs.values()),2),CPU_seconds=round(sum(v['CPU_seconds'] for v in costs.values()),2),scope='Only four distinct complete phase exits; nested worker/Native samples are included, not added.'),additional_costs=dict(authoring_research_review_and_prior_screen='unknown additional, not zero',reference_copy_and_metadata_preparation='unmetered additional',curation='Invoker must retain the separate complete-exit log; not included in phase totals.'),claims=dict(accepted=False,production_admitted=False,routing_outcome=False,comparison_outcome=False,eligible_routing_family_claim=False,independent_or_unrelated_ancestry_established=False,holdout=False,human_review=False,electrical_or_physical_approval=False,quality_gain=False,GUI=False),protocol_sha256=pins[protocol_path],acquisition_sha256=pins[B/'acquisition.json'],inspection_sha256=pins[B/'inspection.json'],review_scope='AI source-only readback/retention of completed facts, not human PCB review or a new validation execution. Separate lead-frozen comparison is outside this intake cutoff.',remaining=['Actual default/Improve/B0/B1/B2 routing, delivery and all final-candidate proof under a separate prospectively frozen protocol','Independent ancestry, complete per-asset/library/model title and licence-body conveyance closure','Electrical/current/timing/return-path/physical suitability and human cleanup','Broader licensed development and untouched confirmation; no family gain from this intake'],preservation='Only owned provenance/process/cost/source-controller metadata retained. Foreign CAD/README/full findings/field values/netlist remain private on this Mac/outside010; hashes are not a raw backup.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=index_pin))
summary_raw=(json.dumps(summary,indent=2)+'\n').encode();summary_pin=hashlib.sha256(summary_raw).hexdigest()
assert len(planned)+2<2000 and len(index_raw)<=4*1024**2 and len(summary_raw)<=4*1024**2 and planned_bytes+len(index_raw)+len(summary_raw)<16*1024**2
def stable():
    for path,pin in pins.items():assert hashlib.sha256(io.read_bytes(path,4*1024**2)).hexdigest()==pin,str(path)
    for path,owner in owners.items():
        info=path.lstat();assert stat.S_ISDIR(info.st_mode) and not path.is_symlink() and (info.st_dev,info.st_ino,info.st_uid)==owner and info.st_uid==os.getuid()
stable()
for path,name in queue.items():retain(path,name)
assert files==planned and material==planned_material and total==planned_bytes
for row in files:pins[ROOT/row['path']]=row['sha256']
stable();p.save_json(index,index_data);bind(index,index_pin);stable()
p.save_json(OUTPUT,summary);bind(OUTPUT,summary_pin);stable()
print(json.dumps(dict(packet=str(OUTPUT.relative_to(ROOT)),sha256=summary_pin,index_sha256=index_pin,new_files=len(files),new_bytes=total,material_rows=len(material),Native_rerun=False,routing=False)))
