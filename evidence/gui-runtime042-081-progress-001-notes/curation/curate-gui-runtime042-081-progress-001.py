"""Prepare-only GUI042/081 progress retention; no Native/readers/tests/GUI/Git.

Invoke only after the lead freezes the selected completed journal rows. Examples:
  --checkpoint-head HEAD --journal-sha256 SHA --roles positive source settings export
The role names are closed; unselected/newer roles never become packet claims.
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
parser.add_argument('--journal',type=Path,default=ROOT/'.runs/gui081-observations-001.json')
parser.add_argument('--roles',nargs='+',required=True,choices=('positive','source','settings','export'))
args=parser.parse_args()
assert re.fullmatch('[0-9a-f]{40}',args.checkpoint_head) and re.fullmatch('[0-9a-f]{64}',args.journal_sha256)
assert len(args.roles)==len(set(args.roles)) and 'positive' in args.roles
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
base=ROOT/'.runs/runtime-directory-042/runtime/.runs/gui-session081';runtime=base.parents[1]
notes=ROOT/'evidence/gui-runtime042-081-progress-001-notes'
output=ROOT/'evidence/gui-runtime042-081-progress-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
observations=args.journal.absolute()
assert observations.parent==ROOT/'.runs' and re.fullmatch('gui081-observations-[0-9]{3}\.json',observations.name)
assert not observations.is_symlink() and p.sha(observations)==args.journal_sha256
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
refs={};files=[];material=[];total=0;dependencies=[];queue=[]
dependency=ROOT/'evidence/runtime042-native-milestone-001.json'
assert p.sha(dependency)=='7faf3fa21c08073ede6bbb1825b15633c25997a7440b6da37dc2e0edac140d4b'
record=json.loads(dependency.read_bytes())
assert record['source_head']==SOURCE_HEAD and record['runtime_manifest_sha256']==MANIFEST_SHA
index=record['files_index'];ipath=ROOT/index['path'];assert p.sha(ipath)==index['sha256']
data=json.loads(ipath.read_bytes())
for row in data.get('files',[]):refs.setdefault(row['sha256'],row['path'])
for row in data.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
dependencies.append(dict(path=str(dependency.relative_to(ROOT)),sha256=p.sha(dependency),files_index=index))
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

add(observations,'cutoff/observations.json')
for name in ('prepared-state.json','route-settings.json','prepare-launcher-process.json','prepare-launcher.log'):
    add(base/name,Path('preparation')/name)
for name in ('runtime-distribution.json','RUNTIME_README.txt'):
    add(runtime/name,Path('runtime')/name)
add(Path(prepared['launcher']),'preparation/Launch Autorouter.command')
add(Path(prepared['recovery_protocol']),'preparation/protocol-required-001.json')
for name,pin in prepared['prerequisites_sha256'].items():
    path=Path(name);assert p.sha(path)==pin
    add(path,Path('preparation/prerequisites')/path.relative_to(ROOT))
assert io.inventory(base/'project')==prepared['source_hashes']
add_tree(base/'project','sources/pristine')
launch=[row for row in observed['observations'] if row.get('role')=='launch_settings_invalid_budget']
assert len(launch)==1 and launch[0]['actual_gui'] is True
assert launch[0]['actual_Finder_launch'] is True and launch[0]['toolbar_green_bent_trace_actual_click'] is True
assert launch[0]['invalid_budget_display']=='0' and launch[0]['jobs_created']==0
assert 'No positive state adopted' in launch[0]['actual_Preview_refusal']
labels={'positive':'positive_delivery','source':'source_freshness','settings':'settings_freshness','export':'export_freshness_after_reader'}
roles=[]
for role in args.roles:
    found=[row for row in observed['observations'] if row.get('role')==labels[role]]
    assert len(found)==1 and found[0]['actual_gui'] is True
    row=found[0];workspace=Path(row['workspace'])
    assert workspace.parent==base/'jobs' and workspace.resolve()==workspace
    assert re.fullmatch('autorouter-gui-[0-9a-f]{32}',workspace.name)
    if role=='positive':assert workspace.name=='autorouter-gui-5a509a66b30a47e4b0c024c35a6f08e4'
    route=json.loads((workspace/'route/result.json').read_bytes())
    assert route['accepted'] is True and route['status']=='routing_accepted' and route['invariants_unchanged'] is True
    assert route['source_hashes']==prepared['source_hashes']
    assert route['tools']==prepared['tools']
    assert route['budget_seconds']==route['cpu_budget_seconds']==90
    assert p.sha(Path(route['candidate']))==route['candidate_sha256']
    choice=json.loads((workspace/'choice/choice.json').read_bytes())
    assert choice['choice']=='accept' and choice['applied'] is False and choice['human_pcb_approval_observed'] is False
    assert choice['receipt_sha256']==p.sha(workspace/'route/result.json')
    add_tree(workspace,Path('jobs')/role)
    result=dict(role=labels[role],workspace=str(workspace),route_receipt_sha256=p.sha(workspace/'route/result.json'),
        lead_observation=row,interactive_full_wall_seconds=None,interactive_full_CPU_seconds=None,
        actual_UI_authority='Lead CUA journal; no human PCB review or screenshot/pixel claim.')
    if role=='positive':
        pre_path=base/'preopen-001.json';post_path=base/'postopen-001.json'
        pre=json.loads(pre_path.read_bytes());post=json.loads(post_path.read_bytes())
        assert pre['role']==post['role']=='positive' and post['workspace']==str(workspace)
        assert row['checked_export_opened'] is True and row['candidate_PCB_unchanged'] is True and row['source_unchanged'] is True
        assert row['accept_without_ack_refused'] is True and row['accept_with_open_review_project_refused'] is True
        assert row['accept_after_review_project_closed'] is True
        assert p.sha(pre_path)==row['preopen_receipt_sha256'] and p.sha(post_path)==row['postopen_receipt_sha256']
        assert len(pre['snapshot_hashes'])==89 and len(post['snapshot_hashes'])==90
        assert io.inventory(Path(post['snapshot']))==post['snapshot_hashes']==io.inventory(workspace/'export')
        assert post['candidate_PCB_unchanged'] is True and post['source_unchanged'] is True
        assert set(post['changed'])==set(row['postopen_changes'])
        stem=Path(route['source']).stem;changed=set(post['changed'])
        assert len(changed)==3 and sum(name.endswith('.zip') for name in changed)==1
        assert {'validation/candidate/'+stem+'.kicad_pro','validation/candidate/'+stem+'.kicad_prl'}<=changed
        assert Path(route['source']).parent==base/'project'
        add(post_path,'opening/positive/postopen-001.json')
        add_tree(Path(post['snapshot']),'opening/positive/postopen-export',full=True)
        result.update(postopen_changes=post['changed'],postopen_files=90,candidate_PCB_unchanged_after_open=True,
            current_posteditor_export_freshness_claimed=False)
    else:
        control=base/'freshness-controls-001'/role;pre_path=control/'preopen-001.json'
        protocol=base/'freshness-controls-001/protocol-frozen-001.json'
        frozen=json.loads(protocol.read_bytes());assert frozen['prepared_state_sha256']==PREPARED_SHA
        assert frozen['source_hashes']==prepared['source_hashes']
        add(protocol,'preparation/freshness-protocol-frozen-001.json')
        pre=json.loads(pre_path.read_bytes());mutation_path=control/'mutation-001.json'
        mutation=json.loads(mutation_path.read_bytes())
        assert pre['role']==role and len(pre['snapshot_hashes'])==89
        assert mutation['kind']==role and mutation['workspace']==str(workspace) and mutation['preopen_sha256']==p.sha(pre_path)
        changed_path=Path(mutation['path'])
        expected_path=(control/'project/owned1007-transport.kicad_pro' if role=='source' else workspace/'settings.json' if role=='settings' else workspace/'export/export.json')
        assert changed_path==expected_path and p.sha(changed_path)==mutation['after_sha256']
        expected=(pre['source_hashes'][changed_path.name] if role=='source' else pre['settings_sha256'] if role=='settings' else pre['export_receipt_sha256'])
        assert mutation['before_sha256']==expected and expected!=mutation['after_sha256']
        assert Path(route['source']).parent==control/'project'
        allowed=dict(pre['source_hashes'])
        if role=='source':allowed[changed_path.name]=mutation['after_sha256']
        assert io.inventory(control/'project')==allowed
        assert p.sha(workspace/'settings.json')==(mutation['after_sha256'] if role=='settings' else pre['settings_sha256'])
        assert 'No positive state adopted' in row['observed_findings']
        if role=='export':
            assert any(text in row['observed_findings'] for text in ('Checked export changed while opening.','current bounded fresh export proof required'))
            altered=json.loads((workspace/'export/export.json').read_bytes())
            assert type(altered['export_accepted']) is int and altered['export_accepted']==1
            boundary_path=control/'open-boundary-001.json'
            if boundary_path.exists():
                boundary=json.loads(boundary_path.read_bytes());assert boundary['workspace']==str(workspace)
                assert boundary['CallAfter_already_queued_proved'] is False
                if boundary.get('mutated') is True:
                    assert boundary['paused'] is True and boundary['resumed'] is True
                    assert 'Z' in boundary['child_completion_state'] and boundary['child_completion_birth']==boundary['child_birth']
                    assert boundary['signals_target_GUI_only'] is True
                    assert boundary['mutation_receipt_sha256']==p.sha(mutation_path)
                    logs=list(workspace.glob('inspect-export-*.command.log'));assert len(logs)==1
                    checked=json.loads(logs[0].read_bytes())
                    assert checked['current'] is True and checked['export_accepted'] is True
                    assert checked['candidate_sha256']==route['candidate_sha256']
                    assert 'Checked export changed while opening.' in row['observed_findings']
                    result['actual_after_reader_material_refusal']=True
                else:
                    assert boundary['mutation_attempted'] is False
                    result['actual_after_reader_material_refusal']=False
                result['boundary']=boundary;add(boundary_path,'faults/export/open-boundary-001.json')
            else:result['actual_after_reader_material_refusal']=False
        else:assert ('Saved source project changed.' if role=='source' else 'Captured settings changed.') in row['observed_findings']
        add_tree(control/'project',Path('sources')/role)
        add(mutation_path,Path('faults')/role/'mutation-001.json')
        result.update(mutation=mutation,actual_GUI_refusal_observed=True,declared_fault_copy_changed_only=True)
    assert pre['workspace']==str(workspace) and pre['source_unchanged'] is True
    assert pre['route']['current'] is True and pre['export']['current'] is True
    assert pre['source_hashes']==route['source_hashes']
    before=Path(pre['snapshot']);assert io.inventory(before)==pre['snapshot_hashes']
    assert p.sha(before/'export.json')==pre['export_receipt_sha256']
    exported=json.loads((before/'export.json').read_bytes())
    assert exported['export_accepted'] is True and exported['applied'] is False and exported['original_geometry_and_routing_unchanged'] is True
    assert exported['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json')
    assert exported['source_hashes']==route['source_hashes'] and exported['tools']==prepared['tools']
    assert exported['candidate_sha256']==route['candidate_sha256']==p.sha(Path(exported['candidate']))
    assert exported['budget_seconds']==exported['cpu_budget_seconds']==90
    native_packet(route,workspace/'route',4);native_packet(exported,before/'validation',None)
    assert all(p.sha(workspace/'route/code'/Path(name).name)==pin for name,pin in route['tools']['implementation_sha256'].items())
    add(pre_path,Path('opening')/role/'preopen-001.json');add_tree(before,Path('opening')/role/'preopen-export',full=True)
    samples=cli_samples(workspace,deliberate_export_refusal=role=='export')
    result.update(Native_route=route['native'],Native_fresh_export=exported['native'],protected_count=4,
        candidate_sha256=route['candidate_sha256'],export_receipt_before_mutation_sha256=pre['export_receipt_sha256'],
        preopen_receipt_sha256=p.sha(pre_path),preopen_files=89,current_at_preopen_only=True,
        CLI_samples=samples,command_stage_wall_sum_seconds=sum(item['wall_seconds'] for item in samples),
        route_nested_cost=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),
        export_nested_cost=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']),
        preopen_helper_internal_wall_seconds=pre['wall_seconds'])
    roles.append(result)
# Top-level finite helper attempts only, including unsuccessful timing/cost logs.
helper_names=['gui081-preopen-001.py','gui081-postopen-001.py','gui081-mutate-control-001.py',
    'gui081-prepare-controls-001.py','prepare-runtime042-gui081.py',
    'gui081-control-source-reviews-001.json',
    'runtime042-gui081-preparation-001.log','runtime042-gui081-preparation-001-time.log']
if 'export' in args.roles:helper_names.append('gui081-export-open-boundary-001.py')
extra_costs=[]
allowed=re.compile(r'gui081-(?:positive|source|settings|export|prepare-controls)-(?:[a-z-]+-)?[0-9]{3}(?:-time)?\.log')
selected_helpers=[path for path in (ROOT/'.runs').iterdir() if path.is_file() and allowed.fullmatch(path.name)]
assert len(selected_helpers)<=100
for path in selected_helpers:
    prefix=path.name.split('-')[1]
    if prefix in args.roles or prefix in ('positive','prepare'):
        helper_names.append(path.name)
        if path.name.endswith('-time.log'):extra_costs.append(dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),cost=cost(path)))
for name in sorted(set(helper_names)):add(ROOT/'.runs'/name,Path('helpers-preparation')/name)
add(helper,'curation/shared-retention-helper030.py')
add(ROOT/'.runs/curate-gui-runtime041-080-progress-001.py','curation/progress-template041.py')
add(ROOT/'.runs/curate-gui-runtime041-080-safety-001.py','curation/safety-template041.py')
add(Path(__file__),'curation/curate-gui-runtime042-081-progress-001.py');add(ROOT/'LICENSE','rights/LICENSE')
scope="""Runtime042 GUI081 partial progress only. The caller supplies one frozen journal hash and explicitly selects completed canonical positive/source/settings/typed-export roles. Unique actual-GUI journal rows, current042 source/manifest/prepared state, each own Native/full-schematic/original/protected-four Route and fresh export proof are required; missing/incomplete rows refuse before retention. This packet never substitutes041 evidence for042 or qualifies unselected jobs.

The positive keeps byte-exact89-file preopen and90-file postopen export snapshots. Opening changed exportPRO/PRL and added a backup ZIP while source/PCB stayed unchanged; preopen proof does not renew Native validity after opening. Fault jobs keep their own89-file fresh preopen and only the declared owned source/settings/export mutation. A successful GUI-pause/reader-zombie boundary, if actually observed, is stated separately; a missed boundary remains a failure/cost, and ordinary preopen refusal does not imply after-reader refusal. CallAfter already queued is not proved because worker adoption is delayed too.

Native SVG/HTML and actual stored reports/processes are retained. ZIP/pixels/binaries remain local with digest/mapping only; no screenshots, unrelated browser content, human/physical PCB review or Native interruption is claimed. Owned GPL source/core only; no private/NUS input, engines/apps/venvs or historical archive copied. Two ignored checks and all findings remain visible. No fullGUI/product/release, general routing gain, family-independent, speed/electrical/Windows/cleanOS/standalone/restoration claim.

CLI wall and nested samples are retained without double addition. Full interactive wall/CPU, unmetered authoring/research/review are unknown, notzero. Helper failures/timing logs and external costs are additional; GUI preparation is the same event already reported in the Native042 dependency, not repeated. This curator performs only bounded stored-byte/schema retention; no Native, routing, GUI, tests, Git or production acceptance readers. Other current GUI roles remain outside this packet, even if a later frozen journal mentions them.
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
summary=dict(schema=1,kind='runtime042-GUI081-selected-completed-roles-partial-progress',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,
    actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    source_head=SOURCE_HEAD,runtime_manifest_sha256=MANIFEST_SHA,immutable_runtime_files=53,
    publication_checkpoint_head=args.checkpoint_head,publication_checkpoint_authority='Caller supplied audited administration HEAD; immutable product source remains82aaa.',
    cutoff=dict(original=str(observations.relative_to(ROOT)),retained=refs[args.journal_sha256],sha256=args.journal_sha256,
        scope='Caller-frozen journal; only explicit selected completed roles claimed. Any later append refuses.'),
    prepared_state_sha256=PREPARED_SHA,launch_static_budget=launch[0],selected_roles=args.roles,roles=roles,
    forced_CallAfter_already_queued_proved=False,Native_interruption_claimed=False,
    pending_in_this_packet=['All GUI roles not explicitly selected; no alias/reject/ordinary engine Cancel/hierarchy/recovery qualification here.'],
    rights='Owned GPL fixtures/core/LICENSE; no NUS/private CAD or tool/engine/app/venv payload.',
    accounting=dict(extra_helper_costs=extra_costs,
        GUI_preparation=cost(ROOT/'.runs/runtime042-gui081-preparation-001-time.log'),GUI_preparation_also_in_Native042_dependency=True,
        interactive_whole_wall_seconds=None,interactive_whole_CPU_seconds=None,authoring_research_review_CPU_seconds=None,
        scope='Unknown is not zero; nested samples included in CLI, not additive. Helper/curation costs separate.'),
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
