"""Retain one no-repair GUI delivery; never replay Native or acceptance readers."""
from pathlib import Path
import ast,datetime,hashlib,json,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
notes=ROOT/'evidence/gui-runtime039-079-recovery-no-repair-001-notes'
output=ROOT/'evidence/gui-runtime039-079-recovery-no-repair-001.json'
assert notes.is_dir() and not output.exists()
base=ROOT/'.runs/runtime-directory-039/runtime/.runs/gui-session079';runtime=base.parents[1]
workspace=base/'jobs/autorouter-gui-66b8a788a518415599cf023c9af284eb';control=base/'recovery-controls-001/no-repair'
cutoff=notes/'cutoff/observations-001.json'
assert p.sha(cutoff)=='47749e5fbfbdddc129d6bf6b0c0dc5fafcee6b00e8857a8ee984c34e6210859b'
journal=json.loads(cutoff.read_bytes());ui=journal['recovery_no_repair_delivery']
assert ui['workspace']==str(workspace) and ui['route_accepted'] is True and ui['fresh_export_accepted'] is True
assert journal['source_head']=='57542e996f2b6e7704acd408ac99f6c72e70adc5'
assert p.sha(runtime/'runtime-distribution.json')==journal['runtime_manifest_sha256']=='ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'
refs={};files=[];material=[];total=0;dependencies=[]
for name in ['gui-runtime039-079-postincumbent-cancel-001','gui-runtime039-079-recovery-repair-001',
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
files.append(dict(path=str(cutoff.relative_to(ROOT)),bytes=len(raw),sha256=csha))
material.append(dict(original=str((base/'observations-001.json').relative_to(ROOT)),retained=str(cutoff.relative_to(ROOT)),bytes=len(raw),sha256=csha,scope='Frozen journal including completed recovery_no_repair_delivery. Active hierarchy job excluded.'))
refs[csha]=str(cutoff.relative_to(ROOT));queue=[]
def add(path,name):
    path=Path(path);assert path.is_file() and ROOT in path.parents;queue.append((path,Path(name)))
def add_tree(path,name,*,full=False):
    for rel in io.inventory(path,max_bytes=64*1024**2):
        if not full and set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/rel,Path(name)/rel)

prepared=json.loads((base/'prepared-state.json').read_bytes());protocol_path=Path(prepared['recovery_protocol'])
assert p.sha(protocol_path)==prepared['recovery_protocol_sha256']
protocol=json.loads(protocol_path.read_bytes());declared=protocol['recovery']['no-repair']
parent=json.loads((workspace/'route/result.json').read_bytes());incumbent=json.loads((workspace/'route/incumbent/result.json').read_bytes())
pre=json.loads((control/'preopen-001.json').read_bytes());post=json.loads((control/'postopen-001.json').read_bytes())
before=control/'preopen-export';after=control/'postopen-snapshot-001';export=json.loads((before/'export.json').read_bytes())
review=json.loads((workspace/'review/review.json').read_bytes());choice=json.loads((workspace/'choice/choice.json').read_bytes());settings=json.loads((workspace/'settings.json').read_bytes())
assert settings==pre['settings']==declared['settings'] and settings['seconds']==parent['budget_seconds']==parent['cpu_budget_seconds']==90
assert p.sha(workspace/'settings.json')==pre['settings_sha256']
assert parent['strategy']=='native_validated_thermal_bridge' and parent['recovery_needed'] is False and parent['repair'] is None
assert parent['accepted'] is True and parent['invariants_unchanged'] is True
assert parent['source']==incumbent['source']==pre['source']==declared['source']
assert parent['source_hashes']==incumbent['source_hashes']==pre['source_hashes']==declared['source_hashes']
assert all(p.sha(Path(parent['source']).parent/name)==sha for name,sha in parent['source_hashes'].items())
assert parent['tools']==incumbent['tools']==prepared['tools']
assert incumbent['accepted'] is True and incumbent['status']=='routing_accepted' and incumbent['invariants_unchanged'] is True
assert parent['incumbent']['receipt_sha256']==pre['incumbent_receipt_sha256']==p.sha(workspace/'route/incumbent/result.json')
assert len(incumbent['protected_route_import']['matches'])==pre['protected_original_locked_items']==ui['protected_items']==1
candidate_sha=parent['candidate_sha256']
assert p.sha(Path(parent['candidate']))==p.sha(Path(incumbent['candidate']))==incumbent['candidate_sha256']==candidate_sha
assert export['candidate_sha256']==candidate_sha and export['export_accepted'] is True and export['applied'] is False
assert export['budget_seconds']==export['cpu_budget_seconds']==90
assert export['original_geometry_and_routing_unchanged'] is True
assert export['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json')
assert choice['choice']=='accept' and choice['applied'] is False and review['status']=='ready_for_manual_review'
for record in [parent,incumbent,export]:
    assert all(record['native'][k]==0 for k in ['opens','blocking','warnings','exclusions'])
    assert record['schematic_parity']=='checked by final native DRC'
    assert all(s['cleanup_complete'] is True and s['log_truncated'] is False for s in record['steps'])
    assert '--schematic-parity' in [s for s in record['steps'] if s['name']=='final-drc'][-1]['argv']
assert p.sha(workspace/'route/final-drc.json')==parent['native_report_sha256']
assert p.sha(workspace/'route/incumbent/final-drc.json')==incumbent['native_report_sha256']
assert p.sha(before/'validation/final-drc.json')==export['native_report_sha256']
assert pre['route']['current'] is True and pre['export']['current'] is True and pre['source_unchanged'] is True
assert len(pre['snapshot_hashes'])==85 and len(post['snapshot_hashes'])==86
assert all(p.sha(before/name)==sha for name,sha in pre['snapshot_hashes'].items())
assert all(p.sha(after/name)==sha for name,sha in post['snapshot_hashes'].items())
assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
pcb='validation/candidate/owned1007-transport.kicad_pcb'
assert pre['snapshot_hashes'][pcb]==post['snapshot_hashes'][pcb]==candidate_sha
assert len(post['changed'])==3 and any(name.endswith('.zip') for name in post['changed'])
assert not (control/'postopen-current-proof-001.json').exists()
add_tree(workspace,Path('job-no-repair'));add_tree(before,Path('before-open/export'),full=True);add_tree(after,Path('after-open/export'),full=True)
for name in ['preopen-001.json','postopen-001.json','route-settings.json']:add(control/name,Path('control')/name)
add(protocol_path,'preparation/recovery-protocol-required-001.json');add(base/'prepared-state.json','preparation/prepared-state.json');add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
for name in ['gui079-recovery-preopen-001.py','gui079-recovery-postopen-001.py','gui079-no-repair-preopen-001.log','gui079-no-repair-preopen-001-time.log','gui079-no-repair-postopen-001.log','gui079-no-repair-postopen-001-time.log']:
    add(ROOT/'.runs'/name,Path('helpers-logs')/name)
add(helper,'curation/retention-helper030.py');add(Path(__file__),'curation/curate-gui-runtime039-079-recovery-no-repair-001.py')
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
scope='''This packet retains ONE completed graphical runtime039 GUI079 no-repair recovery delivery on the original owned two-copper fixture. Whole-method budget90 and separate fresh export90 were captured unchanged. The saved incumbent was accepted/Native0all; recovery_needed wasfalse and repairwasNone. The parent still completed its own final Native/full-schematic/original-design checks before acceptance, then rendered review/explicit Accept intent/fresh Native export/checked opening. This is an ordinary no-repair branch of existing opt-in recovery, not fallback from a failed/cancelled attempt or a new algorithm/family/comparative routing improvement.

The lead observed Microsoft Edge F.Cu/B.Cu before/after Native images, zero findings/two original ignored checks, acknowledgement/Accept intent, fresh export90 and exact KiCad candidate opening. PCB Editor displayed6pads/0vias/4segments/3nets/0unrouted. PCB closed without requested edits or save prompt, File Close Project left no project loaded. CUA screenshots remain transcript-only; no local screenshot/unrelated browser pixels or AX copied. Human PCB/electrical review was not performed.

The preserved before-open85file snapshot and previously executed shared current-reader receipt bind exact candidate/proof bytes, own NativeRoute/parent/export0opens/0blocking/0warnings/0exclusions, fullSCH, originalrules/severities/exclusions and1protected original item. All original/source/candidate/process/PRL/report artifacts remain retained or exact-content referenced. After opening86files were recorded: exportPRO/PRL changed and a new backupZIP appeared; PCB and immutable original source remained unchanged. ZIP is digest/size only, Mac-local. There was NO subsequent production-reader stale check on this job and no new Native validity is inferred after the metadata changes.

No Native/engine/test/production reader was rerun by curation. Source and code are project-owned under repository LICENSE, exactly referenced through earlier packets. No private boards/downloaded tools/apps/venvs/new binary payloads or unrelated browser data are published. All raw work remains on this Mac outside older raw backups. The active hierarchy job and any later observations/results are excluded.

CLI stage samples and parent/incumbent/review/export Native costs are nested, not additive whole-job totals. Separate preopen4.82wall/4.69CPU and postopen.19/.14 are additional verification/snapshot costs. Whole interactive GUI wall/CPU and unmetered research/authoring/review costs are unknown, not zero. Full GUI candidate qualification, remaining hierarchy/high-budget/clean-environment roles and broader coverage/Windows/restoration/human/physical/publication gates remain separate. No broad quality/speed/electrical/physical/platform/release-completion claim is made.
'''
scope_path=notes/'SCOPE.md';scope_path.open('x').write(scope);raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha));material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions));u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='actual-runtime039-GUI079-recovery-no-repair-delivery-partial-cutoff',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    source_head=journal['source_head'],runtime_manifest_sha256=journal['runtime_manifest_sha256'],native_version='10.0.7',workspace=str(workspace),cutoff=dict(path=str(cutoff.relative_to(ROOT)),sha256=csha,scope='Completed recovery_no_repair_delivery; active hierarchy job excluded.'),
    original_source=parent['source'],source_hashes=parent['source_hashes'],source_unchanged_now=True,settings=settings,whole_recovery_method_seconds=90,separate_export_seconds=90,
    parent=dict(accepted=True,status=parent['status'],recovery_needed=False,repair=None,candidate_sha256=candidate_sha,receipt_sha256=p.sha(workspace/'route/result.json'),Native_counts={key:parent['native'][key] for key in ['opens','blocking','warnings','exclusions']},full_schematic_parity=parent['schematic_parity'],original_invariants_recorded=True),
    incumbent=dict(accepted=True,status=incumbent['status'],receipt_sha256=p.sha(workspace/'route/incumbent/result.json'),candidate_sha256=incumbent['candidate_sha256'],protected_original_items=1,not_a_failed_or_cancelled_fallback=True),
    before_open=dict(current_route_and_export_recorded=True,snapshot_files=85,snapshot_bytes=sum((before/name).stat().st_size for name in pre['snapshot_hashes']),preopen_receipt_sha256=p.sha(control/'preopen-001.json'),export_receipt_sha256=p.sha(before/'export.json'),Native_counts={key:export['native'][key] for key in ['opens','blocking','warnings','exclusions']},original_geometry_and_routing_unchanged=True,all_snapshot_files_retained_or_exact_referenced=True),
    actual_UI=ui,after_open=dict(snapshot_files=86,snapshot_bytes=sum((after/name).stat().st_size for name in post['snapshot_hashes']),source_unchanged=True,candidate_PCB_unchanged=True,changed=post['changed'],postopen_production_reader_trial=False,new_Native_validity_inferred=False,backupZIP_payload='Mac-only; digest/size retained.'),
    accounting=dict(CLI_samples=samples,parent_nested=dict(wall_seconds=parent['wall_seconds'],CPU_seconds=parent['total_cpu_seconds']),incumbent_nested=dict(wall_seconds=incumbent['wall_seconds'],CPU_seconds=incumbent['total_cpu_seconds']),review_nested=dict(wall_seconds=review['wall_seconds'],CPU_seconds=review['total_cpu_seconds']),export_nested=dict(wall_seconds=export['wall_seconds'],CPU_seconds=export['total_cpu_seconds']),preopen_verification_additional=cost(ROOT/'.runs/gui079-no-repair-preopen-001-time.log'),postopen_snapshot_additional=cost(ROOT/'.runs/gui079-no-repair-postopen-001-time.log'),scope='Nested costs not additive; whole interactive GUI and unmetered authoring/review wall/CPU unknown, not zero.'),
    pending=['Hierarchy and any other final GUI079 roles','Current clean-environment/broader coverage/Windows/restoration capacity/human/physical and formal-publication gates'],rights='Project-owned generated fixture/code and repository LICENSE through exact prior evidence references. No private/new binary/browser payload.',limits='One no-repair graphical functional delivery, no new family/algorithm/fallback/comparative gain/human/electrical/full-GUI/release-completion claim.',dependencies=dependencies,
    retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),omitted_binary_rows=len(omissions),counts_exclude_index_summary=True),curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binary_rows=len(omissions),actual_GUI_fully_qualified=False)))
