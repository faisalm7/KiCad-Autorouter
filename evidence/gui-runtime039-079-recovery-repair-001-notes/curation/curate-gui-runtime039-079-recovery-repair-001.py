"""Bounded retention of one completed GUI recovery delivery, with no validation rerun."""
from pathlib import Path
import ast, datetime, hashlib, json, resource, sys, time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
notes=ROOT/'evidence/gui-runtime039-079-recovery-repair-001-notes'
output=ROOT/'evidence/gui-runtime039-079-recovery-repair-001.json'
assert notes.is_dir() and not output.exists()
base=ROOT/'.runs/runtime-directory-039/runtime/.runs/gui-session079';runtime=base.parents[1]
workspace=base/'jobs/autorouter-gui-8258a46a7da54e2aa3fdff49ac24f183'
control=base/'recovery-controls-001/repair'
cutoff=notes/'cutoff/observations-001.json'
assert p.sha(cutoff)=='31d90cad3d807759e685b3808e4333b76303b8d59da62fc57b6e2b7ab66f68a0'
observed=json.loads(cutoff.read_bytes())
assert observed['source_head']=='57542e996f2b6e7704acd408ac99f6c72e70adc5'
assert observed['runtime_manifest_sha256']=='ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'
assert p.sha(runtime/'runtime-distribution.json')==observed['runtime_manifest_sha256']
assert any(row.get('stage')=='recovery_repair_delivery' and row.get('workspace')==workspace.name for row in observed['observations'])

refs={};files=[];material=[];total=0;dependencies=[]
for name in ['gui-runtime039-079-ordinary-controls-001','gui-runtime039-079-positive-reject-001',
    'runtime039-native-floor-schema-milestone-001','runtime039-mixer-default-failure-001',
    'runtime033-current-interf-Cthermal-001']:
    path=ROOT/'evidence'/(name+'.json');record=json.loads(path.read_bytes());index=record['files_index']
    assert p.sha(ROOT/index['path'])==index['sha256']
    data=json.loads((ROOT/index['path']).read_bytes())
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
material.append(dict(original=str((base/'observations-001.json').relative_to(ROOT)),retained=str(cutoff.relative_to(ROOT)),
    bytes=len(raw),sha256=csha,scope='Frozen current observations; later entries excluded.'))
refs[csha]=str(cutoff.relative_to(ROOT))
queue=[]
def add(path,name):
    path=Path(path);assert path.is_file() and ROOT in path.parents
    queue.append((path,Path(name)))
def add_tree(path,name,*,full=False):
    for rel in io.inventory(path,max_bytes=64*1024**2):
        if not full and set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/rel,Path(name)/rel)

prepared=json.loads((base/'prepared-state.json').read_bytes())
protocol_path=Path(prepared['recovery_protocol'])
assert p.sha(protocol_path)==prepared['recovery_protocol_sha256']
protocol=json.loads(protocol_path.read_bytes());declared=protocol['recovery']['repair']
parent=json.loads((workspace/'route/result.json').read_bytes())
incumbent=json.loads((workspace/'route/incumbent/result.json').read_bytes())
pre=json.loads((control/'preopen-001.json').read_bytes())
post=json.loads((control/'postopen-001.json').read_bytes())
postproof=json.loads((control/'postopen-current-proof-001.json').read_bytes())
before=control/'preopen-export';after=control/'postopen-snapshot-001'
export=json.loads((before/'export.json').read_bytes())
review=json.loads((workspace/'review/review.json').read_bytes());choice=json.loads((workspace/'choice/choice.json').read_bytes())
settings=json.loads((workspace/'settings.json').read_bytes())
assert settings==pre['settings']==declared['settings']
assert settings['seconds']==parent['budget_seconds']==parent['cpu_budget_seconds']==420
assert p.sha(workspace/'settings.json')==pre['settings_sha256']
assert parent['strategy']=='native_validated_thermal_bridge' and parent['recovery_needed'] is True
assert parent['source']==pre['source']==declared['source']
assert parent['source_hashes']==pre['source_hashes']==declared['source_hashes']
assert parent['tools']==prepared['tools'] and parent['accepted'] is True and parent['invariants_unchanged'] is True
assert parent['incumbent']['receipt']==str(workspace/'route/incumbent/result.json')
assert parent['incumbent']['receipt_sha256']==pre['incumbent_receipt_sha256']==p.sha(workspace/'route/incumbent/result.json')
assert incumbent['accepted'] is False and incumbent['status']=='drc_rejected'
assert len(incumbent['protected_route_import']['matches'])==pre['protected_original_locked_items']==0
assert incumbent['native']['opens']==0 and incumbent['native']['blocking']==1 and incumbent['native']['warnings']==22
assert parent['repair']['status']=='validated_trial_candidate' and len(parent['repair']['trials'])==1
trial=parent['repair']['trials'][0]
assert trial['validation_passed'] is True and trial['id']=='trial-01'
assert parent['repair']['routing_accepted'] is False and parent['repair']['comparison_eligible'] is False
assert parent['candidate_sha256']==trial['candidate_sha256']==export['candidate_sha256']
candidate_sha=parent['candidate_sha256']
assert p.sha(Path(parent['candidate']))==p.sha(Path(trial['candidate']))==candidate_sha
assert parent['metrics']['version']=='10.0.7'
assert parent['schematic_parity']==export['schematic_parity']=='checked by final native DRC'
assert export['budget_seconds']==export['cpu_budget_seconds']==declared['additional_export_seconds']==120
assert export['export_accepted'] is True and export['applied'] is False
assert export['original_geometry_and_routing_unchanged'] is True
assert export['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json')
assert export['source_hashes']==parent['source_hashes']
assert choice['choice']=='accept' and choice['applied'] is False
assert review['status']=='ready_for_manual_review' and review['candidate_sha256']==candidate_sha
for record in (parent,export):
    assert [record['native'][k] for k in ['opens','blocking','warnings','exclusions']]==[0,0,22,0]
    assert len(record['native']['ignored_checks'])==7
    assert all(s['cleanup_complete'] is True and s['log_truncated'] is False for s in record['steps'])
    final=[s for s in record['steps'] if s['name']=='final-drc'][-1]
    assert '--schematic-parity' in final['argv']
assert p.sha(workspace/'route/final-drc.json')==parent['native_report_sha256']
assert p.sha(before/'validation/final-drc.json')==export['native_report_sha256']
assert pre['route']['current'] is True and pre['export']['current'] is True and pre['source_unchanged'] is True
assert len(pre['snapshot_hashes'])==175
assert sum((before/name).stat().st_size for name in pre['snapshot_hashes'])==8078484
assert all(p.sha(before/name)==sha for name,sha in pre['snapshot_hashes'].items())
assert len(post['snapshot_hashes'])==177
assert all(p.sha(after/name)==sha for name,sha in post['snapshot_hashes'].items())
assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
pcb='validation/candidate/interf_u.kicad_pcb'
assert pre['snapshot_hashes'][pcb]==post['snapshot_hashes'][pcb]==candidate_sha
assert all(p.sha(Path(parent['source']).parent/name)==sha for name,sha in parent['source_hashes'].items())
assert postproof['Native_executed'] is False and postproof['postopen_current_proof']['refused'] is True
assert postproof['postopen_current_proof']['error']=='export inputs/runtime/evidence changed'
assert len(post['changed'])==3 and any(name.endswith('.zip') for name in post['changed'])

add_tree(workspace,Path('job-repair'))
add_tree(before,Path('before-open/export'),full=True)
add_tree(after,Path('after-open/export'),full=True)
for name in ['preopen-001.json','postopen-001.json','postopen-current-proof-001.json','route-settings.json']:
    add(control/name,Path('control')/name)
add(protocol_path,'preparation/recovery-protocol-required-001.json')
add(base/'prepared-state.json','preparation/prepared-state.json')
add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
for name in ['gui079-recovery-preopen-001.py','gui079-recovery-postopen-001.py',
    'gui079-repair-preopen-001.log','gui079-repair-preopen-001-time.log',
    'gui079-repair-postopen-001.log','gui079-repair-postopen-001-time.log']:
    add(ROOT/'.runs'/name,Path('helpers-logs')/name)
add(helper,'curation/retention-helper030.py');add(Path(__file__),'curation/curate-gui-runtime039-079-recovery-repair-001.py')

# Bound all new unique content before writing any payload beyond the frozen cutoff.
known=set(refs);planned_bytes=total;planned_files=len(files);filtered=[];omissions=[]
for path,dest in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    if sha not in known:
        try:assert b'\0' not in raw;raw.decode('utf-8')
        except (AssertionError,UnicodeDecodeError):
            omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha,
                reason='New binary remains on Mac; digest only. No screenshots/tool binaries published.'))
            continue
        planned_bytes+=len(raw);planned_files+=1;known.add(sha)
    filtered.append((path,dest))
print(json.dumps(dict(prospective_new_files=planned_files,prospective_new_bytes=planned_bytes,
    queue_rows=len(filtered),binary_omission_rows=len(omissions))),flush=True)
assert planned_bytes<16*1024**2-8192 and planned_files<1999,(planned_bytes,planned_files)
for path,dest in filtered:retain(path,dest)

samples=[]
for process_path in sorted(workspace.glob('*.command.process.json')):
    log=process_path.with_name(process_path.name.replace('.process.json','.log'))
    process=json.loads(process_path.read_bytes())
    assert process['exit_code']==0 and process['cancel_requested'] is False and process['log_truncated'] is False
    assert log.stat().st_size==process['log_bytes']
    samples.append(dict(stage=process_path.name.removesuffix('.command.process.json'),receipt_sha256=p.sha(process_path),
        log_sha256=p.sha(log),sample=process))
scope='''This packet records ONE actual graphical runtime039/GUI079 opt-in thermal recovery repair delivery on the already exposed licensed Interf source. The captured 420-second budget is the whole recovery method, with a separate fresh Native export allocation of120seconds. Corrected-standard Route remains the default. This is not a fair new B0/B1/B2/C comparison, another unrelated family, speed/general quality/electrical claim or complete GUI qualification.

The incumbent completed but was Native DRC rejected (0opens/1blocking/22warnings); it was NOT a valid fallback. Recovery was needed and one bounded trial was validated. The parent then performed own final Native/refill/full-schematic/original-design checks and accepted0opens/0blocking/22warnings/0exclusions. The fresh export repeated own final checks at those same counts. All22warnings,7original ignored checks, original rules/severities/exclusions, source files and actual candidate/report/process bindings remain in retained bytes. Protected original copper count was0: this is not a positive thermal-protection control.

The lead observed the actual graphical whole-method420/export120 display, Native F.Cu/B.Cu rendered review in Microsoft Edge,22warnings/7ignored checks, review acknowledgement, explicit Accept intent, fresh export and checked KiCad opening. The editor displayed379pads/35vias/1038segments/173nets/0unrouted. KiCad asked to save load-converted generated data; no editing was performed and conversion saving was declined, then File Close Project left no project. These are actual CUA transcript observations, not human PCB/electrical approval. No screenshot pixels or unrelated browser content are copied; Native SVG/HTML is retained.

The before-open proof is the complete175file/8,078,484B export snapshot and current production-reader receipt, taken at8.41wall/7.91CPU without new Native execution by that helper. After opening, candidatePCB and original25file source were unchanged, but exportPRO changed and newPRL plus a backupZIP appeared. The actual postopen manifest is177files, not the earlier verbal176; every text file is retained or exactly referenced, while the newZIP stays Mac-only with hash/size. The later production current-proof check correctly refused changed export material. That refusal does not invalidate the preserved before-open proof and is not a fresh Native approval of edited metadata.

All Route parent/incumbent/trial/final and export Native/report/original/source/proposal/geometry/process/PRL artifacts are retained or exact-content referenced using the existing bounded retention helpers. The preopen reader is the previously executed shared current reader, not a new curation acceptance check. All final recorded candidates and the rejected incumbent keep their actual validation. No Native/engine/test/production-reader command was rerun by curation. No later no-repair/cancellation/hierarchy/high-budget/clean-environment results are included.

Source is the same25file official KiCad Interf family, CC-BY-SA-4.0, with original notices and Larry Ewing/The GIMP Tux attribution through exact existing public references. Project code is covered by repository LICENSE. No private boards, downloaded engines/apps/venvs, new binaries or unrelated browser data are published. Raw snapshots and the binary backupZIP remain on this Mac outside older raw backups.

Parent72.911731wall/92.459484CPU includes incumbent, repair and parent Native checks. RouteCLI78.175600wall also includes CLI startup/final readback. ExportCLI15.222460wall contains its own12.038565wall/11.312662CPU Native export sample. These nested numbers must not be added twice. All GUI CLI logs/process samples and separate preopen/postopen costs are retained; whole interactive wall/CPU and unmetered research/authoring/review costs are unknown, not zero. There is no physical, broad performance, Windows, cleanOS/relocation, formal release or project-completion claim.
'''
scope_path=notes/'SCOPE.md';scope_path.open('x').write(scope)
raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index=notes/'files.json'
p.save_json(index,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions))
u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='actual-runtime039-GUI079-recovery-repair-delivery-partial-cutoff',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,
    actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    source_head=observed['source_head'],runtime_manifest_sha256=observed['runtime_manifest_sha256'],native_version='10.0.7',
    workspace=str(workspace),cutoff=dict(path=str(cutoff.relative_to(ROOT)),sha256=csha,recorded_utc=observed['recorded_utc']),
    original_source=str(parent['source']),source_hashes=parent['source_hashes'],source_unchanged_now=True,
    settings=settings,method='Opt-in experimental thermal recovery',whole_method_seconds=420,separate_export_seconds=120,
    route_receipt_sha256=p.sha(workspace/'route/result.json'),candidate_sha256=candidate_sha,
    Native_counts={key:parent['native'][key] for key in ['opens','blocking','warnings','exclusions']},
    ignored_checks=parent['native']['ignored_checks'],all22warnings_retained=True,full_schematic_parity=parent['schematic_parity'],
    protected_original_items=0,thermal_protection_positive_control=False,original_invariants_recorded=True,
    incumbent=dict(accepted=False,status=incumbent['status'],native_counts={key:incumbent['native'][key] for key in ['opens','blocking','warnings','exclusions']},
        candidate_sha256=incumbent['candidate_sha256'],receipt_sha256=p.sha(workspace/'route/incumbent/result.json'),
        valid_fallback=False,native_rejection_reasons=incumbent['native_rejection_reasons']),
    recovery_needed=True,repair=dict(validated_trials=1,id='trial-01',candidate_sha256=trial['candidate_sha256'],
        direct_component_routing_accepted=parent['repair']['routing_accepted'],comparison_eligible=False,
        parent_final_accepted=True,geometry_receipt=parent['repair']['geometry_receipt'],proposal_receipt=parent['repair']['proposal_receipt']),
    before_open=dict(current_route_and_export_recorded=True,snapshot_files=175,snapshot_bytes=8078484,
        preopen_receipt_sha256=p.sha(control/'preopen-001.json'),export_receipt_sha256=p.sha(before/'export.json'),
        fresh_export_Native_counts={key:export['native'][key] for key in ['opens','blocking','warnings','exclusions']},
        original_geometry_and_routing_unchanged=True,all_snapshot_files_retained_or_exact_referenced=True),
    actual_UI_scope=dict(browser='Microsoft Edge at owner request',rendered_F_and_B_copper_observed=True,
        warnings22_and_ignored7_visible=True,review_acknowledged=True,explicit_accept_intent=True,
        checked_KiCad_opening=dict(pads=379,vias=35,segments=1038,nets=173,unrouted=0),
        generated_load_conversion_save_declined=True,project_closed=True,screenshots='CUA transcript only; no local pixels retained.'),
    after_open=dict(snapshot_files=177,snapshot_bytes=sum((after/name).stat().st_size for name in post['snapshot_hashes']),
        count_correction='177 actual manifest files; earlier verbal176 omitted the second new file.',
        source_unchanged=True,candidate_PCB_unchanged=True,changed=post['changed'],current_export_fresh=False,
        current_proof_refusal=postproof['postopen_current_proof'],Native_executed_by_postcheck=False,
        postcheck_sample_wall_seconds=postproof['wall_seconds'],new_backup_ZIP_payload='Mac only; digest/size retained.'),
    accounting=dict(CLI_samples=samples,parent_nested=dict(wall_seconds=parent['wall_seconds'],CPU_seconds=parent['total_cpu_seconds']),
        review_nested=dict(wall_seconds=review['wall_seconds'],CPU_seconds=review['total_cpu_seconds']),
        export_nested=dict(wall_seconds=export['wall_seconds'],CPU_seconds=export['total_cpu_seconds']),
        preopen_verification_additional=cost(ROOT/'.runs/gui079-repair-preopen-001-time.log'),
        postopen_snapshot_additional=cost(ROOT/'.runs/gui079-repair-postopen-001-time.log'),
        scope='Nested parent/incumbent/repair/Native and export costs are included by enclosing CLI samples, not additive totals. Whole interactive wall/CPU and unmetered authoring/review are unknown, not zero.'),
    pending=['Post-incumbent recovery cancellation','Recovery no-repair role','Hierarchy actual GUI role','High ordinary budget and current clean environment if required by final protocol','Broader coverage, Windows, restoration capacity, human/physical and separate formal publication gates'],
    rights='Existing exposed Interf CC-BY-SA-4.0 source and original Tux attribution through exact prior references; project-owned GPL code. No private CAD or new binary/browser payload.',
    limits='One exposed-family GUI repair delivery only. B1 remains default; no fair-comparison, new-family, broad-quality/speed, human/electrical, full-GUI/platform or release-completion claim.',
    dependencies=dependencies,retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],
        max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),new_payload_bytes=total,
        material_rows=len(material),omitted_binary_rows=len(omissions),counts_exclude_index_summary=True),
    curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),
    files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),
    new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binary_rows=len(omissions),actual_GUI_fully_qualified=False)))
