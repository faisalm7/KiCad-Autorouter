"""Curate one frozen GUI080 progress cutoff; no Native/readers/tests/GUI/Git."""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io

SOURCE_HEAD='f7524d7bbfb4824640c8ca51dc978769b2fab98b'
MANIFEST_SHA='3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
PREPARED_SHA='a0ee6588cdaf5594c1baaf4564a79b86ff9117484f642eadfe4cc253ca6cd3ff'
OBSERVATIONS_SHA='3c630b85595aa8b17fa0983d6127a9e268f26ca4a3432a7d1b3f49caf84bae72'
REVIEW_SHA='8ec23d792b632a39f5dbd74bc0b4d8b9b0dae65a71bde4cc2ad2eba61bbbfb1e'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checkpoint-head',required=True)
args=parser.parse_args();assert re.fullmatch(r'[0-9a-f]{40}',args.checkpoint_head)
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
base=ROOT/'.runs/runtime-directory-041/runtime/.runs/gui-session080';runtime=base.parents[1]
notes=ROOT/'evidence/gui-runtime041-080-progress-001-notes'
output=ROOT/'evidence/gui-runtime041-080-progress-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
observations=ROOT/'.runs/gui080-observations-001.json'
assert p.sha(observations)==OBSERVATIONS_SHA
observed=json.loads(observations.read_bytes())
assert observed['runtime']=='041' and observed['session']=='080' and observed['actual_GUI_qualified'] is False
assert observed['prepared_state_sha256']==PREPARED_SHA
assert p.sha(base/'prepared-state.json')==PREPARED_SHA
prepared=json.loads((base/'prepared-state.json').read_bytes())
assert prepared['source_head']==SOURCE_HEAD and prepared['runtime_manifest_sha256']==MANIFEST_SHA
assert p.sha(runtime/'runtime-distribution.json')==MANIFEST_SHA
manifest=json.loads((runtime/'runtime-distribution.json').read_bytes())
assert len(manifest['immutable_files_sha256'])==53
assert all(p.sha(runtime/name)==pin for name,pin in manifest['immutable_files_sha256'].items())
assert p.sha(ROOT/'.runs/gui080-two-positive-static-review-001.json')==REVIEW_SHA

refs={};files=[];material=[];total=0;dependencies=[];queue=[]
dependency=ROOT/'evidence/runtime041-native-milestone-001.json'
assert p.sha(dependency)=='6b490ab1b16b6bbb81c0e4c3a3584d0d96b7d21a116a9cd69e2463d47642da34'
record=json.loads(dependency.read_bytes());assert record['source_head']==SOURCE_HEAD and record['runtime_manifest_sha256']==MANIFEST_SHA
dependency_sha=p.sha(dependency);index=record['files_index'];ipath=ROOT/index['path']
assert p.sha(ipath)==index['sha256']
data=json.loads(ipath.read_bytes())
for row in data.get('files',[]):refs.setdefault(row['sha256'],row['path'])
for row in data.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
dependencies.append(dict(path=str(dependency.relative_to(ROOT)),sha256=dependency_sha,files_index=index))
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

add(observations,'cutoff/observations-001.json')
add(ROOT/'.runs/gui080-two-positive-static-review-001.json','review/two-positive-static-review-001.json')
for name in ('prepared-state.json','route-settings.json','alias-route-settings.json','prepare-launcher-process.json','prepare-launcher.log'):
    add(base/name,Path('preparation')/name)
for name in ('runtime-distribution.json','RUNTIME_README.txt'):
    add(runtime/name,Path('runtime')/name)
for relative in ('freshness-controls-001/protocol-frozen-001.json','ordinary-controls-002/protocol-frozen-001.json','ordinary-controls-002/route-settings420.json','recovery-controls-001/protocol-required-001.json'):
    add(base/relative,Path('preparation/prospective-controls')/relative)
for name,pin in prepared['prerequisites_sha256'].items():
    assert p.sha(Path(name))==pin
    add(Path(name),Path('preparation/prerequisite-receipts')/Path(name).relative_to(ROOT))
assert io.inventory(base/'project')==prepared['source_hashes']
assert io.inventory(base/'alias-project')==prepared['alias_required']['source_hashes']
add_tree(base/'project',Path('sources/ordinary'));add_tree(base/'alias-project',Path('sources/alias'))

roles=[]
cases=[('positive','9b3dc21ee49445b0999398777b178728','preopen-001.json','postopen-001.json'),
       ('alias_positive','35958ffc9a6f48df86ae149c892031b2','preopen-alias-001.json','postopen-alias-001.json'),
       ('reject','6f9288d0252646e59e3e6da75f3f6739',None,None)]
for role,identity,pre_name,post_name in cases:
    workspace=base/'jobs'/('autorouter-gui-'+identity)
    route=json.loads((workspace/'route/result.json').read_bytes())
    choice=json.loads((workspace/'choice/choice.json').read_bytes())
    source_hashes=prepared['alias_required']['source_hashes'] if role=='alias_positive' else prepared['source_hashes']
    source=Path(prepared['alias_required']['source']) if role=='alias_positive' else Path(prepared['source'])
    assert io.inventory(source.parent)==source_hashes==route['source_hashes']
    assert route['source']==str(source) and route['accepted'] is True and route['status']=='routing_accepted'
    assert route['invariants_unchanged'] is True and route['schematic_parity']=='checked by final native DRC'
    assert route['tools']['source_provenance']['git_head']==SOURCE_HEAD
    assert route['tools']['source_provenance']['manifest_sha256']==MANIFEST_SHA
    assert all(p.sha(workspace/'route/code'/Path(name).name)==pin and p.sha(runtime/name)==pin for name,pin in route['tools']['implementation_sha256'].items())
    assert len(route['protected_route_import']['matches'])==4 and len(route['native']['ignored_checks'])==2
    assert all(route['native'][key]==0 for key in ('opens','blocking','warnings','exclusions'))
    assert p.sha(Path(route['candidate']))==route['candidate_sha256']
    assert choice['choice']==('reject' if role=='reject' else 'accept') and choice['applied'] is False and choice['human_pcb_approval_observed'] is False
    assert choice['receipt_sha256']==p.sha(workspace/'route/result.json')
    add_tree(workspace,Path('jobs')/role)
    packets=[(route,workspace/'route')]
    result=dict(role=role,workspace=str(workspace),route_receipt_sha256=p.sha(workspace/'route/result.json'),candidate_sha256=route['candidate_sha256'],Native_route=route['native'],protected_count=4,original_source_unchanged_now=True,original_invariants_recorded=True,full_schematic_parity='Actual own final Native argv/report retained',choice=choice['choice'],applied=False,actual_UI_observation_authority='Lead CUA transcript journal, not human PCB approval',route_nested_cost=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']))
    if role=='reject':
        assert not (workspace/'export').exists()
        result.update(export_directory_exists=False,FreshExport_and_CheckedOpen_disabled_per_lead=True)
    else:
        pre_path=base/pre_name;post_path=base/post_name
        pre=json.loads(pre_path.read_bytes());post=json.loads(post_path.read_bytes())
        assert pre['role']==post['role']==role and pre['workspace']==post['workspace']==str(workspace)
        before=Path(pre['snapshot']);after=Path(post['snapshot'])
        assert len(pre['snapshot_hashes'])==89 and len(post['snapshot_hashes'])==90
        assert io.inventory(before)==pre['snapshot_hashes'] and io.inventory(after)==post['snapshot_hashes']
        assert io.inventory(workspace/'export')==post['snapshot_hashes']
        assert pre['route']['current'] is True and pre['export']['current'] is True and pre['source_unchanged'] is True
        assert p.sha(workspace/'settings.json')==pre['settings_sha256']
        exported=json.loads((before/'export.json').read_bytes())
        assert p.sha(before/'export.json')==pre['export_receipt_sha256']==p.sha(workspace/'export/export.json')
        assert exported['export_accepted'] is True and exported['applied'] is False and exported['original_geometry_and_routing_unchanged'] is True
        assert exported['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json')
        assert exported['source_hashes']==source_hashes and exported['schematic_parity']=='checked by final native DRC'
        assert all(exported['native'][key]==0 for key in ('opens','blocking','warnings','exclusions'))
        assert exported['candidate_sha256']==route['candidate_sha256']==p.sha(Path(exported['candidate']))
        assert post['candidate_PCB_unchanged'] is True and post['source_unchanged'] is True
        changed=set(post['changed']);stem=source.stem
        assert len(changed)==3 and 'validation/candidate/'+stem+'.kicad_pro' in changed and 'validation/candidate/'+stem+'.kicad_prl' in changed
        assert sum(name.endswith('.zip') for name in changed)==1
        assert exported['tools']['implementation_sha256']==route['tools']['implementation_sha256']
        packets.append((exported,before/'validation'))
        add(pre_path,Path('opening')/role/pre_name);add(post_path,Path('opening')/role/post_name)
        add_tree(before,Path('opening')/role/'preopen-export',full=True)
        add_tree(after,Path('opening')/role/'postopen-export',full=True)
        result.update(Native_fresh_export=exported['native'],export_receipt_sha256=pre['export_receipt_sha256'],preopen_receipt_sha256=p.sha(pre_path),postopen_receipt_sha256=p.sha(post_path),preopen_files=89,postopen_files=90,current_at_preopen_only=True,current_posteditor_export_freshness_claimed=False,postopen_changes=post['changed'],candidate_PCB_unchanged_after_open=True,export_nested_cost=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']),preopen_helper_internal_wall_seconds=pre['wall_seconds'],preopen_helper_full_CPU_seconds=None)
    for packet,directory in packets:
        raw=json.loads((directory/'final-drc.json').read_bytes())
        assert raw['kicad_version']=='10.0.7' and all(raw[key]==[] for key in ('violations','unconnected_items','schematic_parity'))
        assert p.sha(directory/'final-drc.json')==packet['native_report_sha256']
        final=next(step for step in packet['steps'] if step['name']=='final-drc')
        assert '--schematic-parity' in final['argv'] and final['exit_code']==0
        assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in packet['steps'])
    proof=json.loads((workspace/'route/task.alias-export.json').read_bytes())
    mapping=json.loads((workspace/'route/export-netclasses.json').read_bytes())
    assert proof['native_classmap']==mapping and len(proof['binding']['aliases'])==2
    if role=='alias_positive':
        layers=mapping['source_all_copper_layers']['layers']
        assert [(row['id'],row['canonical'],row['display_name'],row['index'],row['type']) for row in layers]==[(0,'F.Cu','upper_trace',0,'signal'),(2,'B.Cu','lower_trace',1,'signal')]
        assert [event['phase'] for event in proof['observation']['events']]==['before_alias','during_alias','after_export','restored']
        result['physical_display_identity']=mapping['source_all_copper_layers']
    samples=[]
    for process_path in sorted(workspace.glob('*.command.process.json')):
        log=process_path.with_name(process_path.name.replace('.process.json','.log'))
        process=json.loads(process_path.read_bytes())
        assert log.stat().st_size==process['log_bytes'] and process['exit_code']==0 and process['cancel_requested'] is False and process['log_truncated'] is False
        samples.append(dict(stage=process_path.name.removesuffix('.command.process.json'),receipt_sha256=p.sha(process_path),log_sha256=p.sha(log),wall_seconds=process['wall_seconds'],full_CPU_seconds=process.get('cpu_seconds'),sample=process))
    result.update(CLI_samples=samples,command_stage_wall_sum_seconds=sum(row['wall_seconds'] for row in samples),interactive_full_wall_seconds=None,interactive_full_CPU_seconds=None,accounting_limit='Command-stage durations exclude interactive time; missingCPU is unknown, not zero. Nested Route/export costs are already included in their CLI commands, not additive.')
    roles.append(result)

preview=base/'jobs/autorouter-gui-7f5ad176c1e84c28a384ec2554be20ae'
assert set(path.name for path in preview.iterdir())=={'settings.json','preview.command.log','preview.command.process.json'}
static=json.loads((preview/'preview.command.log').read_bytes());process=json.loads((preview/'preview.command.process.json').read_bytes())
assert static['status']=='preview' and static['static_preflight_passed'] is True and static['native_validation_performed'] is False
assert process['exit_code']==0 and process['cancel_requested'] is False and process['log_truncated'] is False
assert static['source']==prepared['alias_required']['source'] and static['effective_preferences']==prepared['settings']
add_tree(preview,Path('jobs/extra-static-preview'))
for name in ('gui080-preopen-001.py','gui080-mutate-control-001.py','gui080-postopen-001.py','gui080-recovery-preopen-001.py','gui080-recovery-postopen-001.py','gui080-hierarchy-high-prepost-001.py','gui080-observe-postincumbent-cancel-001.py','gui080-prepare-controls-001.py','gui080-helper-preparation-001.json','prepare-runtime041-gui080.py','runtime041-gui080-preparation-001.log','runtime041-gui080-preparation-001-time.log','runtime041-gui080-launch-001.log'):
    add(ROOT/'.runs'/name,Path('helpers-preparation')/name)
add(Path(prepared['launcher']),'preparation/Launch Autorouter.command')
add(helper,'curation/shared-retention-helper030.py')
add(ROOT/'.runs/curate-gui-runtime039-079-ordinary-controls-001.py','curation/template079-ordinary-controls.py')
add(Path(__file__),'curation/curate-gui-runtime041-080-progress-001.py')
add(ROOT/'LICENSE','rights/LICENSE')

scope="""Current runtime041/GUI080 partial progress only: ordinary9b3dc and source-all copper-display alias35958 completed fresh graphical Route/review/accept intent/export/current preopen/checked KiCad opening; reject6f928 completed fresh Route/review/Reject with no export. Extra7f5 was a static ordinary-method preview while method selection was interleaved; no Route or Native worker existed for it. Refusals were separately observed only after settings settled. The prepared original4Cu recovery fixture hit the schematic-class guard first, so this does not prove the later two-copper guard ran. Original039/079 evidence and failed040 work remain unchanged.

Each candidate retains its own final Native10.0.7/full-schematic/original-rule/source/protected-four proof, raw reports/process journals, source/candidate/design bytes, same-load class/layer map, protected-via/import/adapter/default-floor proof, rendered Native SVG/HTML and original two ignored checks. Both positives have byte-exact89-file preopen exports and90-file postopen snapshots. Actual opening later changed only exportPRO/PRL and added a ZIP while source and PCB stayed unchanged. ZIP bytes are omitted publicly but exact size/hash/mapping are retained; raw material remains local. Saved preopen validity is not renewed validity of posteditor material.

Actual toolbar, Edge F/B rendering, review acknowledgement/open-project refusal, explicit accept/reject, checked KiCad opening/zero-unrouted and close observations come from the lead CUA journal. Screenshots are transcript-only: no persistent pixels, unrelated browser AX, Chrome content or human PCB review are claimed/published. Owned GPL fixtures/core/license and prior immutable041 metadata are retained; no NUS/private board, downloaded engine/app/tool/venv, .local-reference or historical population is copied.

Full GUI qualification remains false. High-budget/hierarchy, independent source/settings/typed-export freshness, ordinary engine cancellation, recovery repair, recovery no-repair and recovery cancellation are pending. Forced queued-open timing remains unproved, and no Native interruption is claimed. Earlier evidence cannot substitute for remaining actual041 roles. No general routing/quality/speed/independent-family/electrical/physical/Windows/standalone/cleanOS/restoration/release claim is made.

Command processes record wall durations only. Full interactive time/CPU and authoring/research/AI-review costs are unknown, not zero. Nested Route/export samples are included within CLI commands, not additional. Preopen reader/snapshot cost has internal wall only here. GUI preparation is one already reported event, not an additional repeated cost. This curator does text/hash retention only, never Native, GUI, tests, Git or production acceptance-reader execution. Newer raw remains on this Mac outside older backups.
"""
known=set(refs);planned_bytes=len(scope.encode());planned_files=1;filtered=[];omissions=[];expected={}
for path,destination in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    if path.suffix.lower() in {'.zip','.png','.jpg','.jpeg','.gif','.webp','.pyc'}:
        omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha,reason='ZIP/binary/pixels local only; digest covers omitted snapshot member.'));continue
    if sha not in known:
        try:assert b'\0' not in raw;raw.decode('utf8')
        except (AssertionError,UnicodeDecodeError):
            omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha,reason='No new binary payload; raw retained locally.'));continue
        planned_bytes+=len(raw);planned_files+=1;known.add(sha)
    filtered.append((path,destination));expected[str(path)]=(len(raw),sha)
assert planned_bytes<16*1024**2 and planned_files<2000,(planned_bytes,planned_files)
assert p.sha(observations)==OBSERVATIONS_SHA and p.sha(base/'prepared-state.json')==PREPARED_SHA
for path,destination in filtered:
    assert (path.stat().st_size,p.sha(path))==expected[str(path)]
    retain(path,destination)
notes.mkdir(parents=True,exist_ok=True)
with (notes/'SCOPE.md').open('x') as stream:stream.write(scope)
raw=(notes/'SCOPE.md').read_bytes();sha=hashlib.sha256(raw).hexdigest()
files.append(dict(path=str((notes/'SCOPE.md').relative_to(ROOT)),bytes=len(raw),sha256=sha))
material.append(dict(original='authored:SCOPE.md',retained=str((notes/'SCOPE.md').relative_to(ROOT)),bytes=len(raw),sha256=sha));total+=len(raw)
assert total<16*1024**2 and len(files)<2000
index_path=notes/'files.json';p.save_json(index_path,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions))
u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='runtime041-GUI080-three-completed-jobs-partial-progress',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,source_head=SOURCE_HEAD,runtime_manifest_sha256=MANIFEST_SHA,immutable_runtime_files=53,publication_checkpoint_head=args.checkpoint_head,publication_checkpoint_authority='Caller-supplied source/evidence checkpoint; immutable product source remains f752.',cutoff=dict(original=str(observations.relative_to(ROOT)),retained=refs[OBSERVATIONS_SHA],sha256=OBSERVATIONS_SHA,scope='Frozen current001 only; continuation002 and later observations excluded.'),prepared_state_sha256=PREPARED_SHA,roles=roles,extra_static_preview=dict(workspace=str(preview),Native_executed=False,Route_executed=False,preview=static,CLI=process,scope='Interleaved static ordinary-method preview counted; settled recovery refusals were separate.'),static_refusals=dict(incompatible_recovery_partial90=True,recovery_whole89=True,original4Cu_before_workspace='Schematic-class guard first, not two-copper-guard proof.'),pending=['High-budget/hierarchy combined fresh normal job','Source freshness actual GUI job','Settings freshness actual GUI job','Typed-export freshness actual GUI job','Ordinary engine cancellation','Recovery repair GUI job','Recovery no-repair GUI job','Recovery cancellation with saved incumbent'],forced_queued_open_interval_observed=False,Native_interruption_claimed=False,rights='Owned GPL fixtures/core/LICENSE; no NUS/private CAD or binary tools/engines/apps/venvs.',accounting=dict(GUI_preparation=cost(ROOT/'.runs/runtime041-gui080-preparation-001-time.log'),GUI_preparation_also_reported_in_native041_dependency=True,interactive_whole_wall_seconds=None,interactive_whole_CPU_seconds=None,authoring_research_review_CPU_seconds=None,scope='Unknown is not zero. CLI wall and nested samples retained without double-counting. Curation complete external timing is separate.'),dependencies=dependencies,retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),omitted_binary_payloads=len(omissions),counts_exclude_index_summary=True),curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),files_index=dict(path=str(index_path.relative_to(ROOT)),sha256=p.sha(index_path)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
assert p.sha(observations)==OBSERVATIONS_SHA and p.sha(base/'prepared-state.json')==PREPARED_SHA
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),files_index_sha256=p.sha(index_path),new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binaries=len(omissions),actual_GUI_fully_qualified=False)))

