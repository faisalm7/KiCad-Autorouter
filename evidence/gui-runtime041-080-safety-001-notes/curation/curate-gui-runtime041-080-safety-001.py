"""Retain five completed GUI080 safety roles; no readers/Native/tests/GUI/Git.

Prepare only until the lead freezes journal002 and supplies its exact SHA.
Recovery delivery/cancellation and full GUI qualification are outside this packet.
"""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io

SOURCE_HEAD='f7524d7bbfb4824640c8ca51dc978769b2fab98b'
MANIFEST_SHA='3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
PREPARED_SHA='a0ee6588cdaf5594c1baaf4564a79b86ff9117484f642eadfe4cc253ca6cd3ff'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checkpoint-head',required=True)
parser.add_argument('--journal-sha256',required=True)
args=parser.parse_args()
assert re.fullmatch('[0-9a-f]{40}',args.checkpoint_head)
assert re.fullmatch('[0-9a-f]{64}',args.journal_sha256)
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
base=ROOT/'.runs/runtime-directory-041/runtime/.runs/gui-session080';runtime=base.parents[1]
notes=ROOT/'evidence/gui-runtime041-080-safety-001-notes'
output=ROOT/'evidence/gui-runtime041-080-safety-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
observations=ROOT/'.runs/gui080-observations-002.json'
assert p.sha(observations)==args.journal_sha256
observed=json.loads(observations.read_bytes())
assert observed['runtime']=='041' and observed['session']=='080'
assert p.sha(base/'prepared-state.json')==PREPARED_SHA
prepared=json.loads((base/'prepared-state.json').read_bytes())
assert prepared['source_head']==SOURCE_HEAD and prepared['runtime_manifest_sha256']==MANIFEST_SHA
assert p.sha(runtime/'runtime-distribution.json')==MANIFEST_SHA
manifest=json.loads((runtime/'runtime-distribution.json').read_bytes())
assert len(manifest['immutable_files_sha256'])==53
assert all(p.sha(runtime/name)==pin for name,pin in manifest['immutable_files_sha256'].items())

refs={};files=[];material=[];total=0;dependencies=[];queue=[]
for name,pin in [('runtime041-native-milestone-001','6b490ab1b16b6bbb81c0e4c3a3584d0d96b7d21a116a9cd69e2463d47642da34'),
                 ('gui-runtime041-080-progress-001','4bb6f6b09c3364a803ab79e2f6ef9212ef955dd626ffccbd9f909d27a22651e3')]:
    path=ROOT/'evidence'/(name+'.json');assert p.sha(path)==pin
    record=json.loads(path.read_bytes())
    assert record['source_head']==SOURCE_HEAD and record['runtime_manifest_sha256']==MANIFEST_SHA
    index=record['files_index'];ipath=ROOT/index['path'];assert p.sha(ipath)==index['sha256']
    data=json.loads(ipath.read_bytes())
    for row in data.get('files',[]):refs.setdefault(row['sha256'],row['path'])
    for row in data.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
    dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=pin,files_index=index))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
parsed=ast.parse(helper.read_bytes())
functions=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name in ('retain','tree','cost')]
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

def cli_samples(workspace,*,cancelled=False):
    samples=[]
    for path in sorted(workspace.glob('*.command.process.json')):
        log=path.with_name(path.name.replace('.process.json','.log'));data=json.loads(path.read_bytes())
        assert log.stat().st_size==data['log_bytes'] and data['log_truncated'] is False
        is_cancel=cancelled and path.name=='route.command.process.json'
        assert data['exit_code']==(2 if is_cancel else 0) and data['cancel_requested'] is is_cancel
        samples.append(dict(stage=path.name.removesuffix('.command.process.json'),receipt_sha256=p.sha(path),
            log_sha256=p.sha(log),wall_seconds=data['wall_seconds'],full_CPU_seconds=data.get('cpu_seconds'),process=data))
    return samples

add(observations,'cutoff/observations-002.json')
add(base/'prepared-state.json','preparation/prepared-state.json')
add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
for relative in ['freshness-controls-001/protocol-frozen-001.json','ordinary-controls-002/protocol-frozen-001.json',
                 'ordinary-controls-002/route-settings420.json','recovery-controls-001/protocol-required-001.json']:
    add(base/relative,Path('preparation')/relative)
assert io.inventory(base/'project')==prepared['source_hashes']
role_table=[('source','source_freshness','6ac0dd2ce78a4a3e87719ac83d52f4b7'),
            ('settings','settings_freshness','1f22307c452649bc92143a6e6ff22663'),
            ('export','export_freshness_after_reader','b1ac68eceb0e41cebae84faeba4a6c09'),
            ('cancel','ordinary_engine_cancel','ba2cad19f6064deba72cce5aad669d55'),
            ('hierarchy','hierarchy_high_budget','40edf5387f094d7c99d0c58118f4e3e4')]
rows={}
for role,label,identity in role_table:
    selected=[row for row in observed['observations'] if row.get('role')==label]
    assert len(selected)==1 and selected[0]['actual_gui'] is True
    assert selected[0]['workspace']==str(base/'jobs'/('autorouter-gui-'+identity))
    rows[role]=selected[0]

roles=[]
for role,label,identity in role_table:
    workspace=base/'jobs'/('autorouter-gui-'+identity)
    route=json.loads((workspace/'route/result.json').read_bytes())
    assert route['tools']['source_provenance']['git_head']==SOURCE_HEAD
    assert route['tools']['source_provenance']['manifest_sha256']==MANIFEST_SHA
    add_tree(workspace,Path('jobs')/role)
    result=dict(role=label,workspace=str(workspace),route_receipt_sha256=p.sha(workspace/'route/result.json'),
        lead_observation=rows[role],interactive_full_wall_seconds=None,interactive_full_CPU_seconds=None,
        actual_UI_authority='Lead CUA transcript journal; no human PCB review or persistent screenshot claim.')
    if role=='cancel':
        assert route['accepted'] is False and route['status']=='cancelled'
        assert not (workspace/'export').exists() and 'candidate_sha256' not in route
        engine=next(step for step in route['steps'] if step['name']=='engine')
        assert engine['status']=='cancelled' and engine['exit_code']==-9 and engine['cleanup_complete'] is True
        assert engine['log_truncated'] is False and engine['pid']==rows[role]['observed_java_pid']
        assert engine==rows[role]['engine_process']
        live_path=base/'ordinary-cancel-engine-observed-001.json'
        live=json.loads(live_path.read_bytes())
        assert live['observed'] is True and live['owned_engine']['pid']==engine['pid']
        assert live['workspace']==str(workspace) and live['source_hashes']==route['source_hashes']
        assert live['signals_sent'] is False and live['routing_started_by_observer'] is False
        assert live['source_head']==SOURCE_HEAD and live['runtime_manifest_sha256']==MANIFEST_SHA
        assert io.inventory(Path(route['source']).parent)==route['source_hashes']
        assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in route['steps'])
        add(live_path,'cancellation/ordinary-cancel-engine-observed-001.json')
        result.update(actual_Java_engine_cancel=True,Native_interruption_proved=False,export_exists=False,
            accepted=False,engine=engine,CLI_samples=cli_samples(workspace,cancelled=True),
            route_nested_cost=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),
            original_source_unchanged=True,no_SIGINT_only_or_all_phase_claim=True)
        roles.append(result);continue
    assert route['accepted'] is True and route['status']=='routing_accepted' and route['invariants_unchanged'] is True
    choice=json.loads((workspace/'choice/choice.json').read_bytes())
    assert choice['choice']=='accept' and choice['applied'] is False and choice['human_pcb_approval_observed'] is False
    assert choice['receipt_sha256']==p.sha(workspace/'route/result.json')
    if role=='hierarchy':
        control=base/'ordinary-controls-002';pre_path=control/'preopen-001.json';post_path=control/'postopen-001.json'
        pre=json.loads(pre_path.read_bytes());post=json.loads(post_path.read_bytes())
        assert pre['role']==post['role']=='hierarchy_high_budget'
        assert pre['protected_count']==0 and pre['no_positive_protection_claim'] is True
        assert len(pre['snapshot_hashes'])==103 and len(post['snapshot_hashes'])==104
        assert post['candidate_PCB_unchanged'] is True and post['source_unchanged'] is True
        assert post['production_readers_executed'] is False and post['current_posteditor_validity']=='not_assessed'
        assert io.inventory(Path(post['snapshot']))==post['snapshot_hashes']==io.inventory(workspace/'export')
        assert route['budget_seconds']==route['cpu_budget_seconds']==420
        assert io.inventory(Path(route['source']).parent)==route['source_hashes']==prepared['hierarchy_source_hashes']
        assert set(post['changed'])==set(rows[role]['postopen_changed'])
        assert len(post['changed'])==3 and sum(name.endswith('.zip') for name in post['changed'])==1
        add(post_path,'opening/hierarchy/postopen-001.json')
        add_tree(Path(post['snapshot']),'opening/hierarchy/postopen-export',full=True)
        result.update(protected_count=0,no_positive_protection_claim=True,routing_seconds=420,additional_export_seconds=120,
            postopen_files=104,postopen_changes=post['changed'],current_posteditor_validity_claimed=False)
    else:
        control=base/'freshness-controls-001'/role;pre_path=control/'preopen-001.json'
        pre=json.loads(pre_path.read_bytes());mutation=json.loads((control/'mutation-001.json').read_bytes())
        assert pre['role']==role and len(pre['snapshot_hashes'])==89
        assert p.sha(pre_path)==rows[role]['preopen_sha256'] and pre['source_hashes']==prepared['source_hashes']
        assert mutation['kind']==role and mutation['workspace']==str(workspace) and mutation['preopen_sha256']==p.sha(pre_path)
        changed_path=Path(mutation['path']);assert p.sha(changed_path)==mutation['after_sha256']
        expected=(pre['source_hashes'][changed_path.name] if role=='source' else
                  pre['settings_sha256'] if role=='settings' else pre['export_receipt_sha256'])
        assert mutation['before_sha256']==expected and mutation['before_sha256']!=mutation['after_sha256']
        current_source=io.inventory(Path(route['source']).parent)
        allowed=dict(pre['source_hashes'])
        if role=='source':allowed[changed_path.name]=mutation['after_sha256']
        assert current_source==allowed and route['source_hashes']==pre['source_hashes']
        if role=='settings':assert p.sha(workspace/'settings.json')==mutation['after_sha256']
        else:assert p.sha(workspace/'settings.json')==pre['settings_sha256']
        add_tree(control/'project',Path('sources')/role)
        add(control/'mutation-001.json',Path('faults')/role/'mutation-001.json')
        assert 'No positive state adopted' in rows[role]['observed_findings']
        expected_refusal={'source':'Saved source project changed.','settings':'Captured settings changed.',
            'export':'Checked export changed while opening.'}[role]
        assert expected_refusal in rows[role]['observed_findings']
        if role=='export':
            boundary_path=control/'open-boundary-001.json';boundary=json.loads(boundary_path.read_bytes())
            assert boundary==rows[role]['bounded_injection'] and boundary['workspace']==str(workspace)
            assert boundary['paused'] is True and boundary['resumed'] is True and boundary['mutated'] is True
            assert boundary['child_completion_state']=='Z' and boundary['child_completion_birth']==boundary['child_birth']
            assert boundary['CallAfter_already_queued_proved'] is False and boundary['signals_target_GUI_only'] is True
            assert boundary['mutation_receipt_sha256']==p.sha(control/'mutation-001.json')
            altered=json.loads((workspace/'export/export.json').read_bytes())
            assert type(altered['export_accepted']) is int and altered['export_accepted']==1
            logs=list(workspace.glob('inspect-export-*.command.log'));assert len(logs)==1
            checked=json.loads(logs[0].read_bytes())
            assert checked['current'] is True and checked['export_accepted'] is True
            assert checked['candidate_sha256']==route['candidate_sha256']
            result.update(actual_after_reader_material_refusal=True,CallAfter_already_queued_proved=False,boundary=boundary)
            add(boundary_path,'faults/export/open-boundary-001.json')
        result.update(protected_count=4,mutation=mutation,actual_GUI_refusal_observed=True,
            original_pristine_source_unchanged=True,declared_fault_copy_changed_only=True)
    assert pre['workspace']==str(workspace) and pre['source_unchanged'] is True
    assert pre['route']['current'] is True and pre['export']['current'] is True
    before=Path(pre['snapshot']);assert io.inventory(before)==pre['snapshot_hashes']
    assert p.sha(before/'export.json')==pre['export_receipt_sha256']
    exported=json.loads((before/'export.json').read_bytes())
    assert exported['export_accepted'] is True and exported['applied'] is False
    assert exported['original_geometry_and_routing_unchanged'] is True
    assert exported['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json')
    assert exported['source_hashes']==route['source_hashes']
    assert exported['candidate_sha256']==route['candidate_sha256']==p.sha(Path(exported['candidate']))
    assert exported['budget_seconds']==exported['cpu_budget_seconds']==(120 if role=='hierarchy' else 90)
    native_packet(route,workspace/'route',0 if role=='hierarchy' else 4)
    native_packet(exported,before/'validation',None)
    assert all(p.sha(workspace/'route/code'/Path(name).name)==pin
        for name,pin in route['tools']['implementation_sha256'].items())
    add(pre_path,Path('opening')/role/'preopen-001.json')
    add_tree(before,Path('opening')/role/'preopen-export',full=True)
    samples=cli_samples(workspace)
    result.update(Native_route=route['native'],Native_fresh_export=exported['native'],
        candidate_sha256=route['candidate_sha256'],export_receipt_before_mutation_sha256=pre['export_receipt_sha256'],
        preopen_receipt_sha256=p.sha(pre_path),preopen_files=len(pre['snapshot_hashes']),current_at_preopen_only=True,
        CLI_samples=samples,command_stage_wall_sum_seconds=sum(row['wall_seconds'] for row in samples),
        route_nested_cost=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),
        export_nested_cost=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']),
        preopen_helper_internal_wall_seconds=pre['wall_seconds'])
    roles.append(result)

# Preserve this unsuccessful timing opportunity/cost, without qualifying recovery
# or copying its subsequently reused delivery job or other active recovery files.
miss=[row for row in observed['observations'] if row.get('role')=='natural_postincumbent_cancel_interval_missed']
assert len(miss)==1 and miss[0]['cancellation_pass'] is False
assert miss[0]['Native_interruption_proved'] is False
miss_workspace=base/'jobs/autorouter-gui-3772928c5eb14119afa94c9c14446414'
assert miss[0]['workspace']==str(miss_workspace)
assert miss[0]['gui_cli_process']==json.loads((miss_workspace/'route.command.process.json').read_bytes())
assert miss[0]['gui_cli_process']['exit_code']==0 and miss[0]['gui_cli_process']['cancel_requested'] is False
add(Path(miss[0]['observer']),'other-costs/postincumbent-cancel-observed-001.json')
add(miss_workspace/'route.command.process.json','other-costs/missed-route.command.process.json')
add(miss_workspace/'route.command.log','other-costs/missed-route.command.log')
helper_names=['gui080-preopen-001.py','gui080-mutate-control-001.py','gui080-hierarchy-high-prepost-001.py',
    'gui080-export-open-boundary-001.py','gui080-export-open-boundary-plan-001.json',
    'gui080-export-open-boundary-001.log','gui080-export-open-boundary-001-time.log',
    'gui080-observe-ordinary-cancel-authored-v1-001.py','gui080-observe-ordinary-cancel-first-execute-001.py',
    'gui080-observe-ordinary-cancel-001.py','gui080-ordinary-cancel-observer-001.log',
    'gui080-ordinary-cancel-observer-001-time.log','gui080-ordinary-cancel-observer-002.log',
    'gui080-ordinary-cancel-observer-002-time.log','gui080-observe-postincumbent-cancel-001.py',
    'gui080-postincumbent-cancel-observer-001.log','gui080-postincumbent-cancel-observer-001-time.log',
    'gui080-prepare-controls-001.py','gui080-helper-preparation-001.json']
for name in helper_names:add(ROOT/'.runs'/name,Path('helpers')/name)
add(helper,'curation/shared-retention-helper030.py')
add(ROOT/'.runs/curate-gui-runtime041-080-progress-001.py','curation/progress-template041.py')
add(ROOT/'.runs/curate-gui-runtime039-079-ordinary-controls-001.py','curation/ordinary-template079.py')
add(Path(__file__),'curation/curate-gui-runtime041-080-safety-001.py')
add(ROOT/'LICENSE','rights/LICENSE')

scope="""Runtime041 GUI080 safety progress: five completed roles only. Three independent protected-four canonical partial90 jobs each completed Route, rendered review, acknowledged accept intent, fresh export and current89-file preopen proof before a declared source/settings/typed-export change. Actual Open refused changed source and captured settings. The typed-export control observed the exact direct CLI reader live, paused only the owned GUI, observed that same child as zombie, changed export_accepted true to integer1, resumed the GUI, and observed the final 'Checked export changed while opening' refusal. The reader's successful JSON/process is retained. This also delayed worker adoption; it does not establish that CallAfter was already queued, an atomic boundary, all-phase safety or hostile-writer isolation.

Actual Cancel on the owned live Java engine produced CLI exit2/cancel_requested, durable route cancelled and engine exit-9/cleanup_complete, no accepted candidate/export. This is not SIGINT-only, Native interruption, all-phase or permanent-descendant-absence proof. The first observer failed on nonrecursive directory hashing; its original code/log/cost remains, the shared-inventory correction reused the same routing job.

The separate normal hierarchy420/export120 job completed actual Edge F/B review, acknowledgement/Accept, fresh export and checked KiCad opening. It retains own full-schematic/hierarchy/original-rule Native0all/two ignored checks and protected0 (no protection-positive claim),103-file preopen and104-file postopen snapshots. Opening changed PRO/PRL and added a ZIP while source/PCB stayed unchanged. No new Native or renewed posteditor validity is inferred. ZIP/pixels/binary payloads are omitted with exact mappings/hashes; Native SVG/HTML is retained. Screenshots remain CUA-transcript-only; no unrelated browser content or human PCB review is published.

Natural post-incumbent cancellation job377 missed the interval: Cancel was disabled after success. Its stable CLI/observer/cost records are retained only as an unsuccessful timing opportunity, not recovery/cancellation/no-fallback qualification. No other recovery job tree is copied. The initial three completed jobs remain in the dependency progress packet. A full frozen journal may mention other roles; only the five explicit bound roles here are qualified by this packet.

Full GUI qualification remains false here. Recovery repair/no-repair delivery and post-incumbent cancellation require their separate current proofs. No general routing/completion/quality/speed/independent-family/electrical/physical/Windows/cleanOS/standalone/restoration/release claim. Actual Native/final-candidate/source/protected evidence is retained; this curator only checks stored bytes/schema and never reruns readers, Native, GUI, tests, Git or routing.

Command wall durations and nested Route/export/engine samples are retained, not double-added. Whole interactive wall/CPU and authoring/research/AI-review costs remain unknown, notzero. Observer failure/success, injection and missed-opportunity costs are explicit. New raw remains on this Mac outside older backups. Owned GPL fixtures/core and Interf CC-BY-SA/Tux notices remain bound; no NUS/private source, downloaded engines/apps/venvs or new binary payloads.
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
summary=dict(schema=1,kind='runtime041-GUI080-five-completed-safety-roles-partial-progress',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,
    actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    source_head=SOURCE_HEAD,runtime_manifest_sha256=MANIFEST_SHA,immutable_runtime_files=53,
    publication_checkpoint_head=args.checkpoint_head,
    cutoff=dict(original=str(observations.relative_to(ROOT)),retained=refs[args.journal_sha256],sha256=args.journal_sha256,
        scope='Caller-frozen journal002; only five explicit safety roles qualified here; later journal appends refuse.'),
    prepared_state_sha256=PREPARED_SHA,roles=roles,forced_CallAfter_already_queued_proved=False,
    actual_after_reader_export_material_refusal_observed=True,Native_interruption_claimed=False,
    other_timing_opportunity_not_qualification=miss[0],
    pending_in_this_packet=['Recovery repair delivery','Recovery no-repair delivery','Post-incumbent cancellation'],
    rights='Owned GPL fixtures/core; Interf exact CC-BY-SA/source/Tux notices bound; binary image remains local digest-only. No private/NUS payload.',
    accounting=dict(export_boundary=cost(ROOT/'.runs/gui080-export-open-boundary-001-time.log'),
        ordinary_observer_failed001=cost(ROOT/'.runs/gui080-ordinary-cancel-observer-001-time.log'),
        ordinary_observer_success002=cost(ROOT/'.runs/gui080-ordinary-cancel-observer-002-time.log'),
        missed_postincumbent_observer=cost(ROOT/'.runs/gui080-postincumbent-cancel-observer-001-time.log'),
        missed_postincumbent_CLI_wall_seconds=miss[0]['gui_cli_process']['wall_seconds'],
        interactive_whole_wall_seconds=None,interactive_whole_CPU_seconds=None,
        scope='Observers/injection are additional; nested Route/export/engine samples already included in CLI commands. Whole interactive CPU unknown, notzero. Preparation reported in existing041 dependencies, not repeated.'),
    dependencies=dependencies,
    retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],
        max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,
        new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),
        omitted_binary_payloads=len(omissions),counts_exclude_index_summary=True),
    curation_sample=dict(wall_seconds=time.monotonic()-START,
        CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),
    files_index=dict(path=str(index_path.relative_to(ROOT)),sha256=p.sha(index_path)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
assert p.sha(observations)==args.journal_sha256 and p.sha(base/'prepared-state.json')==PREPARED_SHA
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),files_index_sha256=p.sha(index_path),
    new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binaries=len(omissions),actual_GUI_fully_qualified=False)))
