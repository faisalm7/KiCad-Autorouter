"""Prepare-only consolidated ordinary GUI081 controls; no Native/readers/GUI/tests.

One final caller-frozen journal003, four unique completed role rows. Required
labels: alias_positive_delivery, reject, ordinary_engine_cancel,
hierarchy_high_budget; plus alias_pre_routing_diagnostic_contamination_refusal.
All four roles must be complete before the one prospective curation invocation.
"""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
SOURCE_HEAD='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
MANIFEST_SHA='1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
PREPARED_SHA='7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checkpoint-head',required=True)
parser.add_argument('--journal-sha256',required=True)
parser.add_argument('--roles',nargs='+',required=True,choices=('alias_positive','reject','cancel','hierarchy'))
args=parser.parse_args()
assert re.fullmatch('[0-9a-f]{40}',args.checkpoint_head) and re.fullmatch('[0-9a-f]{64}',args.journal_sha256)
assert len(args.roles)==4 and set(args.roles)=={'alias_positive','reject','cancel','hierarchy'}
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
base=ROOT/'.runs/runtime-directory-042/runtime/.runs/gui-session081';runtime=base.parents[1]
notes=ROOT/'evidence/gui-runtime042-081-ordinary-controls-001-notes'
output=ROOT/'evidence/gui-runtime042-081-ordinary-controls-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
observations=ROOT/'.runs/gui081-observations-003.json'
assert p.sha(observations)==args.journal_sha256
observed=json.loads(observations.read_bytes())
assert observed['runtime']=='042' and observed['session']=='081'
assert observed['source_head']==SOURCE_HEAD and observed['runtime_manifest_sha256']==MANIFEST_SHA
assert observed['prepared_state_sha256']==PREPARED_SHA
assert p.sha(base/'prepared-state.json')==PREPARED_SHA
prepared=json.loads((base/'prepared-state.json').read_bytes())
assert prepared['source_head']==SOURCE_HEAD and prepared['runtime_manifest_sha256']==MANIFEST_SHA
assert p.sha(runtime/'runtime-distribution.json')==MANIFEST_SHA
manifest=json.loads((runtime/'runtime-distribution.json').read_bytes())
assert len(manifest['immutable_files_sha256'])==53
assert all(p.sha(runtime/name)==pin for name,pin in manifest['immutable_files_sha256'].items())
protocol_path=Path(prepared['recovery_protocol'])
assert protocol_path==base/'recovery-controls-001/protocol-required-001.json'
assert p.sha(protocol_path)==prepared['recovery_protocol_sha256']
protocol=json.loads(protocol_path.read_bytes())
refs={};files=[];material=[];total=0;dependencies=[];queue=[]
for name,pin in [('runtime042-native-milestone-001','7faf3fa21c08073ede6bbb1825b15633c25997a7440b6da37dc2e0edac140d4b'),
                 ('gui-runtime042-081-progress-001','20f3b09c68c861e20dafc9917652ea78df4e9db03e451179277ccf351e65af7c'),
                 ('gui-runtime042-081-postincumbent-cancel-001','a3061f78481d696c77d4d9fd071dd4a3a4f625af5c1b6d5fc7f24138b6d717a7')]:
    path=ROOT/'evidence'/(name+'.json');assert p.sha(path)==pin
    record=json.loads(path.read_bytes());index=record['files_index']
    assert record['source_head']==SOURCE_HEAD and record['runtime_manifest_sha256']==MANIFEST_SHA
    assert p.sha(ROOT/index['path'])==index['sha256']
    data=json.loads((ROOT/index['path']).read_bytes())
    for row in data.get('files',[]):refs.setdefault(row['sha256'],row['path'])
    for row in data.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
    dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=pin,files_index=index))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[node for node in ast.parse(helper.read_bytes()).body if isinstance(node,ast.FunctionDef) and node.name in ('retain','tree','cost')]
assert [node.name for node in functions]==['retain','tree','cost']
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'),globals())

def add(path,destination):
    path=Path(path);assert path.is_file() and ROOT in path.parents
    queue.append((path,Path(destination)))

def add_tree(path,destination,*,full=False):
    for relative in io.inventory(path,max_bytes=64*1024**2):
        if not full and set(Path(relative).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/relative,Path(destination)/relative)

def native_packet(packet,directory,protected):
    assert packet['schematic_parity']=='checked by final native DRC'
    assert packet['tools']['source_provenance']['git_head']==SOURCE_HEAD
    assert packet['tools']['source_provenance']['manifest_sha256']==MANIFEST_SHA
    assert packet['tools']['implementation_sha256']==prepared['tools']['implementation_sha256']
    assert all(packet['native'][key]==0 for key in ('opens','blocking','warnings','exclusions'))
    assert len(packet['native']['ignored_checks'])==2
    raw=json.loads((directory/'final-drc.json').read_bytes())
    assert raw['kicad_version']=='10.0.7' and all(raw[key]==[] for key in ('violations','unconnected_items','schematic_parity'))
    assert p.sha(directory/'final-drc.json')==packet['native_report_sha256']
    final=next(step for step in packet['steps'] if step['name']=='final-drc')
    assert '--schematic-parity' in final['argv'] and final['exit_code']==0
    assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in packet['steps'])
    if protected is not None:assert len(packet['protected_route_import']['matches'])==protected

def cli_samples(workspace,*,cancelled=False,deliberate_export_refusal=False):
    samples=[]
    for path in sorted(workspace.glob('*.command.process.json')):
        log=path.with_name(path.name.replace('.process.json','.log'));data=json.loads(path.read_bytes())
        assert log.stat().st_size==data['log_bytes'] and data['log_truncated'] is False
        is_cancel=cancelled and path.name=='route.command.process.json'
        refused=deliberate_export_refusal and path.name.startswith('inspect-export-') and data['exit_code']==2
        assert data['exit_code']==(2 if is_cancel or refused else 0) and data['cancel_requested'] is is_cancel
        samples.append(dict(stage=path.name.removesuffix('.command.process.json'),deliberate_export_refusal_sample=refused,receipt_sha256=p.sha(path),
            log_sha256=p.sha(log),wall_seconds=data['wall_seconds'],full_CPU_seconds=data.get('cpu_seconds'),process=data))
    return samples

add(observations,'cutoff/observations-003.json')
add(base/'prepared-state.json','preparation/prepared-state.json')
add(protocol_path,'preparation/protocol-required-001.json')
add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
saved_rows=[row for row in observed['observations'] if row.get('role')=='persistent_settings_save_load']
assert len(saved_rows)==1 and saved_rows[0]['actual_gui'] is True
saved_ui=saved_rows[0];saved_path=base/'gui-saved-settings-001.json'
assert saved_ui['actual_Save_settings_as'] is True and saved_ui['actual_Load_settings'] is True
assert saved_ui['file_created_without_overwrite'] is True and saved_ui['new_file']==str(saved_path)
assert saved_ui['visible_budget_changed_to']==91 and saved_ui['visible_budget_restored_to']==90
assert saved_ui['settings']==prepared['settings'] and saved_ui['prior_positive_open_controls_remained_disabled'] is True
assert saved_path.is_file() and not saved_path.is_symlink() and saved_path.resolve()==saved_path
assert saved_path.stat().st_nlink==1 and saved_path.stat().st_size==194
saved_raw=io.read_bytes(saved_path,194)
assert hashlib.sha256(saved_raw).hexdigest()==saved_ui['settings_sha256']=='a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65'
assert json.loads(saved_raw)==prepared['settings']
add(saved_path,'static-customization/gui-saved-settings-001.json')
assert io.inventory(base/'project')==prepared['source_hashes']
assert io.inventory(Path(prepared['alias_required']['source']).parent)==prepared['alias_required']['source_hashes']
labels={'alias_positive':'alias_positive_delivery','reject':'reject','cancel':'ordinary_engine_cancel','hierarchy':'hierarchy_high_budget'}
selected={};workspaces=[]
for role in args.roles:
    rows=[row for row in observed['observations'] if row.get('role')==labels[role]]
    assert len(rows)==1 and rows[0]['actual_gui'] is True
    row=rows[0];w=Path(row['workspace'])
    assert w.parent==base/'jobs' and w.resolve()==w and re.fullmatch('autorouter-gui-[0-9a-f]{32}',w.name)
    selected[role]=row;workspaces.append(w)
assert len(set(workspaces))==4
# The failed first alias invocation and quarantine metadata are mandatory.
failed=base/'jobs/autorouter-gui-e3d0d6da80ad477b8cc2f5daacb67f97'
failrows=[row for row in observed['observations'] if row.get('role')=='alias_pre_routing_diagnostic_contamination_refusal']
assert len(failrows)==1 and failrows[0]['actual_gui'] is True and failrows[0]['workspace']==str(failed)
failed_process=json.loads((failed/'route.command.process.json').read_bytes())
failed_log=json.loads((failed/'route.command.log').read_bytes())
assert failed_process['exit_code']==2 and failed_process['cancel_requested'] is False and failed_process['log_truncated'] is False
assert (failed/'route.command.log').stat().st_size==failed_process['log_bytes']
assert failed_log['accepted'] is False and 'runtime directory file population differs' in failed_log['error']
assert io.inventory(failed/'route')=={} and not any((failed/name).exists() for name in ('review','choice','export'))
quarantine=ROOT/'.runs/runtime042-root-readback-contamination-001'
qpath=quarantine/'receipt.json';qpostpath=quarantine/'post-quarantine-observation-001.json'
assert p.sha(qpath)=='dcfca7db23ae82711314d401024627215b43a4056ea1ef81d300732d46b53b58'
assert p.sha(qpostpath)=='ec518ccbbbdd2dfa03256682f5cab2ca5e2b0002097647ecf1f3c5ea12201acf'
q=json.loads(qpath.read_bytes());qpost=json.loads(qpostpath.read_bytes())
assert q['failed_GUI_workspace']==str(failed) and q['Native_started_by_failed_attempt'] is False
assert q['immutable_pinned_files_unchanged'] is True and q['all_files_preserved'] is True and q['no_rebuild'] is True
assert len(q['files'])==11 and all(item['path'].endswith('.pyc') and item['bytes']>0 for item in q['files'])
assert qpost['all_pinned_files_unchanged'] is True and qpost['runtime_cache_absent'] is True
assert not (runtime/'autorouter/__pycache__').exists()
assert failrows[0]['preserved_cache_receipt_sha256']==p.sha(qpath)
add_tree(failed,'failed-first-alias-job')
add(qpath,'diagnostic-contamination/receipt.json');add(qpostpath,'diagnostic-contamination/post-quarantine-observation-001.json')
# Never inventory/read/copy preserved-pycache: public evidence is hashes/sizes only.
roles=[]
for role in args.roles:
    row=selected[role];workspace=Path(row['workspace']);route=json.loads((workspace/'route/result.json').read_bytes())
    assert route['tools']==prepared['tools']
    add_tree(workspace,Path('jobs')/role)
    result=dict(role=labels[role],workspace=str(workspace),lead_observation=row,
        route_receipt_sha256=p.sha(workspace/'route/result.json'),interactive_full_wall_seconds=None,
        interactive_full_CPU_seconds=None,actual_UI_authority='Lead CUA journal; no human PCB review or persistent pixels.')
    if role=='cancel':
        source=Path(protocol['ordinary_cancel']['source']);hashes=protocol['recovery']['repair']['source_hashes']
        assert route['source']==str(source) and route['source_hashes']==hashes==io.inventory(source.parent)
        assert route['status']=='cancelled' and route['accepted'] is False and route['schematic_parity']=='not checked'
        assert not any((workspace/name).exists() for name in ('review','choice','export'))
        engine=next(step for step in route['steps'] if step['name']=='engine')
        assert engine['status']=='cancelled' and engine['exit_code']<0 and engine['cleanup_complete'] is True
        assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in route['steps'])
        live_path=base/'ordinary-cancel-engine-observed-001.json';live=json.loads(live_path.read_bytes())
        assert live['observed'] is True and live['workspace']==str(workspace) and live['owned_engine']['pid']==engine['pid']
        assert live['source_hashes']==hashes and live['source_head']==SOURCE_HEAD and live['runtime_manifest_sha256']==MANIFEST_SHA
        assert live['signals_sent'] is False and live['routing_started_by_observer'] is False and row['actual_Cancel'] is True
        samples=cli_samples(workspace,cancelled=True)
        add(live_path,'cancellation/ordinary-cancel-engine-observed-001.json');add_tree(source.parent,'sources/ordinary-cancel')
        result.update(accepted=False,actual_Java_engine_cancel=True,Native_interruption_proved=False,
            engine=engine,CLI_samples=samples,export_directory_exists=False,source_unchanged_now=True,
            route_nested_cost=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']))
        roles.append(result);continue
    assert route['accepted'] is True and route['status']=='routing_accepted' and route['invariants_unchanged'] is True
    choice=json.loads((workspace/'choice/choice.json').read_bytes())
    assert choice['choice']==('reject' if role=='reject' else 'accept')
    assert choice['applied'] is False and choice['human_pcb_approval_observed'] is False
    assert choice['receipt_sha256']==p.sha(workspace/'route/result.json')
    source=Path(prepared['alias_required']['source'] if role=='alias_positive' else prepared['hierarchy_source'] if role=='hierarchy' else prepared['source'])
    hashes=prepared['alias_required']['source_hashes'] if role=='alias_positive' else prepared['hierarchy_source_hashes'] if role=='hierarchy' else prepared['source_hashes']
    if role=='reject':
        allowed_sources={prepared['source']:prepared['source_hashes'],prepared['alias_required']['source']:prepared['alias_required']['source_hashes']}
        assert route['source'] in allowed_sources
        source=Path(route['source']);hashes=allowed_sources[route['source']]
        assert row['actual_Reject'] is True
    protected=0 if role=='hierarchy' else 4
    assert route['source']==str(source) and route['source_hashes']==hashes==io.inventory(source.parent)
    assert p.sha(Path(route['candidate']))==route['candidate_sha256']
    assert route['budget_seconds']==route['cpu_budget_seconds']==(420 if role=='hierarchy' else 90)
    native_packet(route,workspace/'route',protected)
    assert all(p.sha(workspace/'route/code'/Path(name).name)==pin for name,pin in route['tools']['implementation_sha256'].items())
    add_tree(source.parent,Path('sources')/role)
    result.update(candidate_sha256=route['candidate_sha256'],Native_route=route['native'],protected_count=protected,
        no_positive_protection_claim=protected==0,choice=choice['choice'],applied=False,source_unchanged_now=True)
    if role=='reject':
        assert not (workspace/'export').exists()
        result.update(export_directory_exists=False,FreshExport_and_CheckedOpen_disabled_per_lead=True)
    else:
        if role=='alias_positive':
            assert workspace.name=='autorouter-gui-4c6796dff66f46e4b4e3c0a363d1dcb1'
            pre_path=base/'preopen-alias-001.json';post_path=base/'postopen-alias-001.json'
            proof=json.loads((workspace/'route/task.alias-export.json').read_bytes())
            mapping=json.loads((workspace/'route/export-netclasses.json').read_bytes())
            assert proof['native_classmap']==mapping and len(proof['binding']['aliases'])==2
            layers=mapping['source_all_copper_layers']['layers']
            assert [(item['id'],item['canonical'],item['display_name'],item['index'],item['type']) for item in layers]==[(0,'F.Cu','upper_trace',0,'signal'),(2,'B.Cu','lower_trace',1,'signal')]
            assert [item['phase'] for item in proof['observation']['events']]==['before_alias','during_alias','after_export','restored']
            pre_count,post_count=89,90
            assert row['explicit_clean_retry_after_diagnostic_contamination'] is True and row['unattended_first_attempt_success'] is False
            assert row['preceding_failed_workspace']==str(failed)
            result.update(physical_display_identity=mapping['source_all_copper_layers'],explicit_retry_after_diagnostic_refusal=True)
        else:
            control=base/'ordinary-controls-002';pre_path=control/'preopen-001.json';post_path=control/'postopen-001.json'
            pre_count,post_count=103,104
        pre=json.loads(pre_path.read_bytes());post=json.loads(post_path.read_bytes())
        expected_role='alias_positive' if role=='alias_positive' else 'hierarchy_high_budget'
        assert pre['role']==post['role']==expected_role and pre['workspace']==post['workspace']==str(workspace)
        assert p.sha(pre_path)==row['preopen_receipt_sha256'] and p.sha(post_path)==row['postopen_receipt_sha256']
        assert row['checked_export_opened'] is True and row['source_unchanged'] is True and row['candidate_PCB_unchanged'] is True
        assert len(pre['snapshot_hashes'])==pre_count and len(post['snapshot_hashes'])==post_count
        assert pre['route']['current'] is True and pre['export']['current'] is True and pre['source_unchanged'] is True
        assert pre['source_hashes']==hashes and p.sha(workspace/'settings.json')==pre['settings_sha256']
        before=Path(pre['snapshot']);after=Path(post['snapshot'])
        assert io.inventory(before)==pre['snapshot_hashes'] and io.inventory(after)==post['snapshot_hashes']==io.inventory(workspace/'export')
        assert post['candidate_PCB_unchanged'] is True and post['source_unchanged'] is True
        changed=set(post['changed']);stem=source.stem
        assert changed==set(row['postopen_changes'])
        assert len(changed)==3 and sum(name.endswith('.zip') for name in changed)==1
        assert {'validation/candidate/'+stem+'.kicad_pro','validation/candidate/'+stem+'.kicad_prl'}<=changed
        exported=json.loads((before/'export.json').read_bytes())
        assert p.sha(before/'export.json')==pre['export_receipt_sha256']==p.sha(workspace/'export/export.json')
        assert exported['export_accepted'] is True and exported['applied'] is False and exported['original_geometry_and_routing_unchanged'] is True
        assert exported['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json') and exported['source_hashes']==hashes
        assert exported['tools']==prepared['tools'] and exported['candidate_sha256']==route['candidate_sha256']==p.sha(Path(exported['candidate']))
        assert exported['budget_seconds']==exported['cpu_budget_seconds']==(120 if role=='hierarchy' else 90)
        native_packet(exported,before/'validation',None)
        if role=='hierarchy':
            assert pre['protected_count']==0 and pre['no_positive_protection_claim'] is True
            assert post['production_readers_executed'] is False and post['current_posteditor_validity']=='not_assessed'
        add(pre_path,Path('opening')/role/'preopen-001.json');add(post_path,Path('opening')/role/'postopen-001.json')
        add_tree(before,Path('opening')/role/'preopen-export',full=True);add_tree(after,Path('opening')/role/'postopen-export',full=True)
        result.update(Native_fresh_export=exported['native'],export_receipt_sha256=pre['export_receipt_sha256'],
            preopen_receipt_sha256=p.sha(pre_path),postopen_receipt_sha256=p.sha(post_path),preopen_files=pre_count,postopen_files=post_count,
            postopen_changes=post['changed'],current_at_preopen_only=True,current_posteditor_export_freshness_claimed=False,
            export_nested_cost=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']))
    samples=cli_samples(workspace)
    result.update(CLI_samples=samples,command_stage_wall_sum_seconds=sum(item['wall_seconds'] for item in samples),
        route_nested_cost=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']))
    roles.append(result)
helper_names=['gui081-preopen-001.py','gui081-postopen-001.py','gui081-observe-ordinary-cancel-001.py',
    'gui081-hierarchy-preopen-001.py','gui081-hierarchy-postopen-001.py']
allowed=re.compile(r'gui081-(?:alias|reject|ordinary-cancel|hierarchy)-(?:[a-z-]+-)?[0-9]{3}(?:-time)?\.log')
logs=[path for path in (ROOT/'.runs').iterdir() if path.is_file() and allowed.fullmatch(path.name)]
assert len(logs)<=100
extra_costs=[]
for path in logs:
    helper_names.append(path.name)
    if path.name.endswith('-time.log'):extra_costs.append(dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),cost=cost(path)))
for name in sorted(set(helper_names)):add(ROOT/'.runs'/name,Path('helpers')/name)
add(helper,'curation/shared-retention-helper030.py')
add(ROOT/'.runs/curate-gui-runtime041-080-progress-001.py','curation/progress-template041.py')
add(ROOT/'.runs/curate-gui-runtime041-080-safety-001.py','curation/safety-template041.py')
add(Path(__file__),'curation/curate-gui-runtime042-081-ordinary-controls-001.py');add(ROOT/'LICENSE','rights/LICENSE')
scope="""Consolidated runtime042 GUI081 ordinary controls only: caller-frozen journal003 and four explicit unique completed alias-positive/Reject/ordinary-Java-Cancel/hierarchy-high-budget rows. Each positive retains its own Native10.0.7/fullSCH/original-rule/source/constraint/final-candidate proof; alias and canonical Reject protect4originalitems, hierarchy protects0(no positive protection claim). Alias retry preserves physical/canonical/display identity and padless alias export observations. Reject must have actual saved reject intent and no export. Cancel must have observed owned liveJava ancestry, actual GUI Cancel, negative engine exit/cleanup, CLI2 and rejected cancelled parent; it does not establish Native interruption or SIGINT-only/allphase/permanent-absence safety.

Actual Save settings as a fresh JSON, visible budget change91, and Load saved settings restoring90/default selections are retained as same-process static customization. This is not restart, relocation, cleanOS or new routing qualification.

The first alias attempt failed before Native due to lead diagnostic imports without bytecode suppression adding11pyc to strict immutable runtime. All53pinned files stayed unchanged. Cache was moved/preserved locally, not deleted; only its recorded hashes/sizes and exact quarantine receipt are public. The failed CLI0.73009wall/exit2 is retained separately, not erased or treated as routing/Native failure or unattended first-pass product success. Unmetered diagnostic cost is unknown, notzero; actual quarantine/tool-observation costs are retained separately. Successful alias is explicitly the fresh retry.

Alias pre89/post90 and hierarchy pre103/post104 retain exact preopen proof plus post-editor metadata scope. Opening changed exportPRO/PRL and addedZIP while source/PCB stayed unchanged. Saved preopen validity never becomes renewed posteditor Native validity. ZIP/pixels/binary assets remain Mac-only with exact digest/mapping; no screenshots or unrelated browser contents are published. Native SVG/HTML and original warnings/two ignored checks remain visible. No fullGUI/project/release, broader routing gain, independent family, speed/electrical/human/physical/Windows/cleanOS/standalone/restoration claim.

Owned fixtures/core GPL; cancellation uses exact exposed Interf CC-BY-SA/Tux source with notices, binary bitmap hash-only. No NUS/private CAD/tools/apps/venvs. Full interactive wall/CPU and unmetered research/authoring/review remain unknown, notzero. CLI costs contain nested Route/Native/export costs; helper/failed-attempt/quarantine costs separate, no double addition. Curation only checks stored bytes/schema, no Native/GUI/readers/tests/Git. Recovery/current functional roles remain separate dependencies; no unselected role is qualified by this packet.
"""
known=set(refs);planned_bytes=len(scope.encode());planned_files=1;filtered=[];omissions=[];expected={}
for path,destination in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    if path.suffix.lower() in {'.zip','.png','.jpg','.jpeg','.gif','.webp','.bmp','.pyc'}:
        omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha,
            reason='Binary/ZIP/pixels local only; digest covers omitted snapshot/source member.'));continue
    if sha not in known:
        try:assert b'\0' not in raw;raw.decode('utf8')
        except (AssertionError,UnicodeDecodeError):
            omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha,
                reason='No new binary payload; raw retained locally.'));continue
        planned_bytes+=len(raw);planned_files+=1;known.add(sha)
    filtered.append((path,destination));expected[str(path)]=(len(raw),sha)
assert planned_bytes<16*1024**2 and planned_files<2000,(planned_bytes,planned_files)
assert p.sha(observations)==args.journal_sha256 and p.sha(base/'prepared-state.json')==PREPARED_SHA
for path,destination in filtered:
    assert (path.stat().st_size,p.sha(path))==expected[str(path)]
    retain(path,destination)
notes.mkdir(parents=True,exist_ok=True)
with (notes/'SCOPE.md').open('x') as stream:stream.write(scope)
raw=(notes/'SCOPE.md').read_bytes();sha=hashlib.sha256(raw).hexdigest()
files.append(dict(path=str((notes/'SCOPE.md').relative_to(ROOT)),bytes=len(raw),sha256=sha))
material.append(dict(original='authored:SCOPE.md',retained=str((notes/'SCOPE.md').relative_to(ROOT)),bytes=len(raw),sha256=sha));total+=len(raw)
assert total<16*1024**2 and len(files)<2000
index_path=notes/'files.json'
p.save_json(index_path,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions))
u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='runtime042-GUI081-consolidated-ordinary-controls-bounded-cutoff',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,
    actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    Native_rerun_by_curation=False,production_readers_rerun_by_curation=False,
    source_head=SOURCE_HEAD,runtime_manifest_sha256=MANIFEST_SHA,immutable_runtime_files=53,publication_checkpoint_head=args.checkpoint_head,
    cutoff=dict(original=str(observations.relative_to(ROOT)),retained=refs[args.journal_sha256],sha256=args.journal_sha256,
        scope='Only explicit completed ordinary role rows; later journal mutation refuses.'),
    prepared_state_sha256=PREPARED_SHA,selected_roles=args.roles,roles=roles,
    static_settings_customization=dict(observation=saved_ui,saved_file_sha256=saved_ui['settings_sha256'],
        scope='Actual Save/Load in same GUI process; no restart/relocation/cleanOS or new routing qualification.'),
    failed_first_alias=dict(lead_observation=failrows[0],GUI_CLI_process=failed_process,CLI_output=failed_log,
        Native_started=False,product_first_attempt_success=False,cache_files_metadata=q['files'],raw_cache_copied_publicly=False,
        quarantine_receipt_sha256=p.sha(qpath),post_quarantine_observation_sha256=p.sha(qpostpath),
        all_pinned_files_unchanged=True,retry_explicit=True,unmetered_diagnostic_CPU_seconds=None),
    accounting=dict(extra_helper_costs=extra_costs,quarantine=qpost['quarantine_external_cost'],
        post_quarantine_tool_observation=qpost['tool_manifest_external_cost'],interactive_whole_wall_seconds=None,interactive_whole_CPU_seconds=None,
        scope='CLI/Route/export/Native costs nest; helper/quarantine observations additional. Unknown is not zero; no invented aggregate.'),
    forced_CallAfter_already_queued_proved=False,ordinary_cancel_Native_interruption_claimed=False,
    pending_in_this_packet=['Other GUI roles and release/breadth/external gates remain separate; no whole-product qualification.'],
    rights='Owned fixtures/core GPL; exact Interf CC-BY-SA/Tux notices, bitmap digest-only; no private/NUS/tool binary payload.',
    dependencies=dependencies,retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),
        functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,
        new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),omitted_binary_payloads=len(omissions),counts_exclude_index_summary=True),
    curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),
    files_index=dict(path=str(index_path.relative_to(ROOT)),sha256=p.sha(index_path)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
assert p.sha(observations)==args.journal_sha256 and p.sha(base/'prepared-state.json')==PREPARED_SHA
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),files_index_sha256=p.sha(index_path),
    new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binaries=len(omissions),actual_GUI_fully_qualified=False)))
