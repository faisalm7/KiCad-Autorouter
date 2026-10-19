"""Retain completed hierarchy/high-budget GUI role; no Native or reader replay."""
from pathlib import Path
import ast,datetime,hashlib,json,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
notes=ROOT/'evidence/gui-runtime039-079-hierarchy-high-budget-001-notes';output=ROOT/'evidence/gui-runtime039-079-hierarchy-high-budget-001.json'
assert notes.is_dir() and not output.exists()
base=ROOT/'.runs/runtime-directory-039/runtime/.runs/gui-session079';runtime=base.parents[1]
workspace=base/'jobs/autorouter-gui-da1eb0d8bad74424a8c713db2a828b1b';control=base/'ordinary-controls-002';cutoff=notes/'cutoff/observations-001.json'
assert p.sha(cutoff)=='af12e6c8510e4407f56fe999799e498db405aa5dd819f9c142733f3c038d55d8'
journal=json.loads(cutoff.read_bytes());ui=journal['ordinary_hierarchy_high_budget']
assert ui['workspace']==str(workspace) and ui['method']=='route' and ui['route_accepted'] is True and ui['export_accepted'] is True
assert journal['source_head']=='57542e996f2b6e7704acd408ac99f6c72e70adc5'
assert p.sha(runtime/'runtime-distribution.json')==journal['runtime_manifest_sha256']=='ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'
refs={};files=[];material=[];total=0;dependencies=[]
for name in ['gui-runtime039-079-recovery-no-repair-001','gui-runtime039-079-recovery-repair-001','gui-runtime039-079-postincumbent-cancel-001',
    'gui-runtime039-079-ordinary-controls-001','gui-runtime039-079-positive-reject-001','runtime039-native-floor-schema-milestone-001']:
    path=ROOT/'evidence'/(name+'.json');record=json.loads(path.read_bytes());index=record['files_index']
    assert p.sha(ROOT/index['path'])==index['sha256'];data=json.loads((ROOT/index['path']).read_bytes())
    for row in data.get('files',[]):refs.setdefault(row['sha256'],row['path'])
    for row in data.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
    dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),files_index=index))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')]
assert [n.name for n in functions]==['retain','tree','cost']
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'),globals())
raw=cutoff.read_bytes();csha=hashlib.sha256(raw).hexdigest();total=len(raw)
files.append(dict(path=str(cutoff.relative_to(ROOT)),bytes=len(raw),sha256=csha));refs[csha]=str(cutoff.relative_to(ROOT))
material.append(dict(original=str((base/'observations-001.json').relative_to(ROOT)),retained=str(cutoff.relative_to(ROOT)),bytes=len(raw),sha256=csha,scope='Frozen completed ordinary_hierarchy_high_budget root key; later events excluded.'))
queue=[]
def add(path,name):
    path=Path(path);assert path.is_file() and ROOT in path.parents;queue.append((path,Path(name)))
def add_tree(path,name,*,full=False):
    for rel in io.inventory(path,max_bytes=64*1024**2):
        if not full and set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/rel,Path(name)/rel)

protocol_path=control/'protocol-frozen-001.json';binding_path=control/'workspace-binding-001.json'
assert p.sha(protocol_path)=='266a0586b7d2a93a33119e7bbf45b7d564cc8c692199126bfc7f8abdf3add56e'
protocol=json.loads(protocol_path.read_bytes());binding=json.loads(binding_path.read_bytes())
assert binding['protocol_sha256']==p.sha(protocol_path) and binding['workspace']==str(workspace)
assert binding['method']=='route' and binding['actual_preview_completed'] is True
assert binding['pre_workspace_refusal_observed']['actual'] is True and binding['pre_workspace_refusal_observed']['job_count_before_after']==9
route=json.loads((workspace/'route/result.json').read_bytes());review=json.loads((workspace/'review/review.json').read_bytes());choice=json.loads((workspace/'choice/choice.json').read_bytes())
pre=json.loads((control/'preopen-001.json').read_bytes());post=json.loads((control/'postopen-001.json').read_bytes())
before=control/'preopen-export-001';after=control/'postopen-export-001';export=json.loads((before/'export.json').read_bytes())
settings=json.loads((workspace/'settings.json').read_bytes())
assert settings==protocol['settings'] and settings['seconds']==route['budget_seconds']==route['cpu_budget_seconds']==420
assert p.sha(workspace/'settings.json')==pre['settings_sha256']
assert route['source']==export['inputs']['source']==protocol['source']==pre['source']==post['source']
assert route['source_hashes']==export['source_hashes']==protocol['source_hashes']==pre['source_hashes']==post['source_hashes']
assert all(p.sha(Path(route['source']).parent/name)==sha for name,sha in route['source_hashes'].items())
assert route['accepted'] is True and route['invariants_unchanged'] is True and route['status']=='routing_accepted'
assert route['scope']=='whole_board_unlocked_routing' and route['engine_profile']=='standard' and route['adapter']=='both' and route['scoring_variant'] is None
assert len(route['protected_route_import']['matches'])==pre['protected_count']==ui['protected_count']==0
assert export['export_accepted'] is True and export['applied'] is False and export['original_geometry_and_routing_unchanged'] is True
assert export['budget_seconds']==export['cpu_budget_seconds']==120
assert export['inputs']['receipt_sha256']==pre['route_receipt_sha256']==p.sha(workspace/'route/result.json')
assert pre['export_receipt_sha256']==p.sha(before/'export.json')
assert choice['choice']=='accept' and choice['applied'] is False and review['status']=='ready_for_manual_review'
candidate_sha=route['candidate_sha256'];assert p.sha(Path(route['candidate']))==export['candidate_sha256']==pre['candidate_sha256']==candidate_sha
for record in [route,export]:
    assert all(record['native'][k]==0 for k in ['opens','blocking','warnings','exclusions'])
    assert record['schematic_parity']=='checked by final native DRC'
    assert all(s['cleanup_complete'] is True and s['log_truncated'] is False for s in record['steps'])
    assert '--schematic-parity' in [s for s in record['steps'] if s['name']=='final-drc'][-1]['argv']
assert p.sha(workspace/'route/final-drc.json')==route['native_report_sha256']
assert p.sha(before/'validation/final-drc.json')==export['native_report_sha256']
assert pre['route']['current'] is True and pre['export']['current'] is True and pre['production_readers_executed'] is True
assert pre['Native_executed'] is False and pre['source_unchanged'] is True
assert pre['protocol_sha256']==post['protocol_sha256']==p.sha(protocol_path)
assert len(pre['snapshot_hashes'])==103 and len(post['snapshot_hashes'])==104
assert all(p.sha(before/name)==sha for name,sha in pre['snapshot_hashes'].items())
assert all(p.sha(after/name)==sha for name,sha in post['snapshot_hashes'].items())
assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
assert post['production_readers_executed'] is False and post['Native_executed'] is False and post['current_posteditor_validity']=='not_assessed'
hierarchy=[]
for stage,rootdir,name in [('task',workspace/'route','task-classes-proof.json'),('final',workspace/'route','final-classes-proof.json'),('export',before/'validation','final-classes-proof.json')]:
    proof=json.loads((rootdir/name).read_bytes());qualification=proof['qualification']
    assert proof['context']=='native-route-hierarchy-default-v2' and qualification['class_parity_qualified'] is True
    assert [qualification[k] for k in ['components','terminals','nets','instances']]==[5,11,5,3] and len(qualification['unconnected_pads'])==4
    assert qualification['accepted'] is False and qualification['routing_accepted'] is False and qualification['production_qualified'] is False
    if stage in ('task','final'):assert p.sha(rootdir/name)==route['schematic_class_'+stage]['sha256']
    hierarchy.append(dict(stage=stage,proof_sha256=p.sha(rootdir/name),policy=qualification['policy'],components=5,terminals=11,nets=5,instances=3,unconnected_pads=4,class_parity_qualified=True,standalone_routing_acceptance=False))

add_tree(workspace,Path('job-hierarchy-high'));add_tree(before,Path('before-open/export'),full=True);add_tree(after,Path('after-open/export'),full=True)
for name in ['protocol-frozen-001.json','workspace-binding-001.json','preopen-001.json','postopen-001.json','route-settings420.json']:add(control/name,Path('control')/name)
add(base/'prepared-state.json','preparation/prepared-state.json');add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
for name in ['gui079-hierarchy-high-prepost-001.py','gui079-hierarchy-high-prepost-preparation-001.json','gui079-hierarchy-high-preopen-001.log','gui079-hierarchy-high-preopen-001-time.log','gui079-hierarchy-high-postopen-001.log','gui079-hierarchy-high-postopen-001-time.log']:
    add(ROOT/'.runs'/name,Path('helpers-logs')/name)
assert p.sha(ROOT/'.runs/gui079-hierarchy-high-prepost-001.py')=='1d819bf3802c86abe166d5d5a57f5c060088e1a8b09f4aa888c9bb7d478e4ae2'
add(helper,'curation/retention-helper030.py');add(Path(__file__),'curation/curate-gui-runtime039-079-hierarchy-high-budget-001.py')
known=set(refs);planned_bytes=total;planned_files=len(files);filtered=[];omissions=[]
for path,dest in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    if sha not in known:
        try:assert b'\0' not in raw;raw.decode('utf-8')
        except (AssertionError,UnicodeDecodeError):
            omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha,reason='New binary backupZIP stays Mac-only; digest only. No screenshot/tool payload.'));continue
        planned_bytes+=len(raw);planned_files+=1;known.add(sha)
    filtered.append((path,dest))
assert planned_bytes<16*1024**2-8192 and planned_files<1999,(planned_bytes,planned_files)
for path,dest in filtered:retain(path,dest)
samples=[]
for process_path in sorted(workspace.glob('*.command.process.json')):
    log=process_path.with_name(process_path.name.replace('.process.json','.log'));process=json.loads(process_path.read_bytes())
    assert process['exit_code']==0 and process['cancel_requested'] is False and process['log_truncated'] is False and log.stat().st_size==process['log_bytes']
    samples.append(dict(stage=process_path.name.removesuffix('.command.process.json'),receipt_sha256=p.sha(process_path),log_sha256=p.sha(log),sample=process))
scope='''This packet retains one prospectively assigned combined hierarchy/high ordinary-budget runtime039 GUI079 role: normal corrected-standard Route420 and separate Native export120. The original required-role protocol stays unchanged; ordinary-controls-002 supplement and exact workspace binding supply the combined mapping before routing. An earlier batched Cocoa method-popup/Preview action still used the previous thermal guard and refused before any new workspace (job count stayed9). A separate normal Preview then passed. This was a truthful pre-work refusal, not a Native routing failure or constraint change.

Actual Route/fresh export each performed own Native/refill/full-schematic/original-design checks at0opens/0blocking/0warnings/0exclusions, plus stored task/final/export hierarchy class proofs. The controlled owned source binds5components/11connectedterminals/5nets/3instances/4unconnected pads; class-only proofs do not independently grant routing acceptance. Protected source copper count was0: no positive protection claim is made. All original source/rules/severities/exclusions, Native reports/process journals/candidate hashes and hierarchy/instance/unit/terminal evidence are retained or exact-content referenced.

The lead observed exact local Native F.Cu/B.Cu before/after images in Microsoft Edge, zero findings/two original ignored checks, acknowledgement and explicit Accept intent, fresh export120 and checked KiCad opening. PCB Editor displayed15pads/0vias/13segments/5nets/0unrouted. It was closed without requested edits or save, then File Close Project left no loaded project. CUA screenshot observations remain transcript-only; no local screenshot/unrelated browser pixels or AX are copied. This is not human PCB/electrical review or a new development/evaluation family gain.

The shared helper1d819bf3 preserved103complete preopen files and recorded current Route/export consistency before actual opening; it ran no Native commands. Postopen104files show changed PRO/PRL plus a new backupZIP, while source and candidatePCB remain byte-exact. The postopen helper records bytes only, performed no production-reader retry and leaves current post-editor validity unassessed. ZIP payload stays Mac-only with digest/size. Before-open Native evidence is preserved separately; no renewed validity is inferred after metadata changes.

No Native/engine/test/production reader was rerun by curation. Code and generated hierarchy fixture are project-owned under repository LICENSE through retained provenance. No private inputs, downloaded tools/apps/venvs/new binary payloads or unrelated browser content are published. Other raw evidence remains on this Mac outside older raw backups. The separate clean-environment qualification underway is not inspected or claimed here.

Route/review/export/GUI CLI costs are nested, not additive whole-job totals. Preopen2.56wall/2.43CPU and postopen.53/.20 are additional recorded reader/snapshot costs. Whole interactive GUI wall/CPU and unmetered authoring/review costs are unknown, not zero. This packet completes its assigned functional role, not by itself full candidate/cleanOS/relocation/standalone/Windows/restoration/human/physical/industry quality or formal-release qualification. No fair comparative superiority, general routing gain or speed/electrical claim is made.
'''
scope_path=notes/'SCOPE.md';scope_path.open('x').write(scope);raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha));material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions));u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='actual-runtime039-GUI079-hierarchy-and-ordinary-high-budget-role',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    source_head=journal['source_head'],runtime_manifest_sha256=journal['runtime_manifest_sha256'],native_version='10.0.7',workspace=str(workspace),cutoff=dict(path=str(cutoff.relative_to(ROOT)),sha256=csha,scope='Completed ordinary_hierarchy_high_budget root key; later clean-environment work excluded.'),
    prospective_protocol_sha256=p.sha(protocol_path),workspace_binding_sha256=p.sha(binding_path),pre_workspace_refusal=binding['pre_workspace_refusal_observed'],method='route',settings=settings,route_seconds=420,separate_export_seconds=120,
    original_source=route['source'],source_hashes=route['source_hashes'],source_unchanged_now=True,route_receipt_sha256=p.sha(workspace/'route/result.json'),candidate_sha256=candidate_sha,Native_counts={key:route['native'][key] for key in ['opens','blocking','warnings','exclusions']},ignored_checks=route['native']['ignored_checks'],full_schematic_parity=route['schematic_parity'],original_invariants_recorded=True,hierarchy_proofs=hierarchy,protected_original_items=0,positive_protection_claim=False,
    before_open=dict(current_route_and_export_recorded=True,snapshot_files=103,snapshot_bytes=sum((before/name).stat().st_size for name in pre['snapshot_hashes']),preopen_receipt_sha256=p.sha(control/'preopen-001.json'),export_receipt_sha256=p.sha(before/'export.json'),Native_counts={key:export['native'][key] for key in ['opens','blocking','warnings','exclusions']},original_geometry_and_routing_unchanged=True,all_snapshot_files_retained_or_exact_referenced=True),
    actual_UI=ui,after_open=dict(snapshot_files=104,snapshot_bytes=sum((after/name).stat().st_size for name in post['snapshot_hashes']),source_unchanged=True,candidate_PCB_unchanged=True,changed=post['changed'],production_readers_executed=False,Native_executed=False,current_posteditor_validity='not_assessed',backupZIP_payload='Mac-only; digest/size retained.'),
    accounting=dict(CLI_samples=samples,route_nested=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),review_nested=dict(wall_seconds=review['wall_seconds'],CPU_seconds=review['total_cpu_seconds']),export_nested=dict(wall_seconds=export['wall_seconds'],CPU_seconds=export['total_cpu_seconds']),preopen_verification_additional=cost(ROOT/'.runs/gui079-hierarchy-high-preopen-001-time.log'),postopen_snapshot_additional=cost(ROOT/'.runs/gui079-hierarchy-high-postopen-001-time.log'),prospective_protocol_preparation=protocol['preparation_cost'],scope='Nested runtime costs not additive. Whole interactive GUI and unmetered authoring/review wall/CPU unknown, not zero.'),
    pending='Separate current clean-environment evidence/integrated final GUI review and original breadth/Windows/restoration/human/physical/formal-publication gates remain.',rights='Project-owned generated hierarchy fixture/code; repository LICENSE and exact provenance through prior packets. No private CAD/new binary/browser/screenshot payload.',limits='One owned functional hierarchy/high-budget control, not a new family or general/comparative routing-quality/speed/human/electrical/full-product/release claim.',dependencies=dependencies,
    retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),omitted_binary_rows=len(omissions),counts_exclude_index_summary=True),curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binary_rows=len(omissions),actual_GUI_fully_qualified=False)))
