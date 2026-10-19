"""Retain one completed cancellation schedule without replaying Native/readers."""
from pathlib import Path
import ast,datetime,hashlib,json,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
notes=ROOT/'evidence/gui-runtime039-079-postincumbent-cancel-001-notes'
output=ROOT/'evidence/gui-runtime039-079-postincumbent-cancel-001.json'
assert notes.is_dir() and not output.exists()
base=ROOT/'.runs/runtime-directory-039/runtime/.runs/gui-session079';runtime=base.parents[1]
workspace=base/'jobs/autorouter-gui-c3d011286e45412d96ebe208506582a0'
control=base/'recovery-controls-001/no-repair';cutoff=notes/'cutoff/observations-001.json'
assert p.sha(cutoff)=='cdfc9b92a3f6addd06c7bb17b6ac274415e6ba5c3d57c729d99194358c7a00b4'
journal=json.loads(cutoff.read_bytes());ui=journal['postincumbent_cancel']
assert ui['workspace']==str(workspace) and ui['actual_UI_Cancel'] is True
assert ui['parent_accepted'] is False and ui['choice_or_export'] is False
assert journal['source_head']=='57542e996f2b6e7704acd408ac99f6c72e70adc5'
assert p.sha(runtime/'runtime-distribution.json')==journal['runtime_manifest_sha256']=='ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'

refs={};files=[];material=[];total=0;dependencies=[]
for name in ['gui-runtime039-079-recovery-repair-001','gui-runtime039-079-ordinary-controls-001',
    'gui-runtime039-079-positive-reject-001','runtime039-native-floor-schema-milestone-001']:
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
material.append(dict(original=str((base/'observations-001.json').relative_to(ROOT)),retained=str(cutoff.relative_to(ROOT)),bytes=len(raw),sha256=csha,
    scope='Frozen journal including actual postincumbent_cancel root key; later positive job excluded.'))
refs[csha]=str(cutoff.relative_to(ROOT))
queue=[]
def add(path,name):
    path=Path(path);assert path.is_file() and ROOT in path.parents
    queue.append((path,Path(name)))
def add_tree(path,name):
    for rel in io.inventory(path,max_bytes=64*1024**2):
        if set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/rel,Path(name)/rel)

plan_path=control/'postincumbent-cancel-plan-001.json';obs_path=control/'postincumbent-cancel-observed-001.json';verified_path=control/'postincumbent-cancel-verified-001.json'
plan=json.loads(plan_path.read_bytes());observed=json.loads(obs_path.read_bytes());verified=json.loads(verified_path.read_bytes())
parent=json.loads((workspace/'route/result.json').read_bytes());incumbent=json.loads((workspace/'route/incumbent/result.json').read_bytes())
cli=json.loads((workspace/'route.command.process.json').read_bytes());prepared=json.loads((base/'prepared-state.json').read_bytes())
protocol_path=Path(prepared['recovery_protocol']);protocol=json.loads(protocol_path.read_bytes());declared=protocol['recovery']['no-repair']
assert p.sha(protocol_path)==prepared['recovery_protocol_sha256']==verified['frozen_protocol_sha256']
assert verified['all_expected_records_valid'] is True and all(verified['checks'].values())
assert verified['plan_sha256']==p.sha(plan_path) and verified['observer_sha256']==p.sha(obs_path)
assert verified['parent_receipt_sha256']==p.sha(workspace/'route/result.json')
assert parent['status']=='cancelled' and parent['accepted'] is False
assert parent['repair'] is None and parent['recovery_needed'] is False
assert cli['exit_code']==2 and cli['cancel_requested'] is True and cli['log_truncated'] is False
assert not (workspace/'export').exists() and not (workspace/'choice').exists() and not (workspace/'review').exists()
assert parent['source']==incumbent['source']==declared['source']
assert parent['source_hashes']==incumbent['source_hashes']==declared['source_hashes']
assert all(p.sha(Path(parent['source']).parent/name)==sha for name,sha in parent['source_hashes'].items())
assert incumbent['accepted'] is True and incumbent['status']=='routing_accepted' and incumbent['invariants_unchanged'] is True
assert all(incumbent['native'][k]==0 for k in ['opens','blocking','warnings','exclusions'])
assert incumbent['schematic_parity']=='checked by final native DRC'
assert p.sha(workspace/'route/incumbent/result.json')==parent['incumbent']['receipt_sha256']==observed['incumbent_sha256']
candidate_sha=observed['incumbent_candidate_sha256']
assert p.sha(Path(incumbent['candidate']))==incumbent['candidate_sha256']==p.sha(Path(parent['candidate']))==parent['candidate_sha256']==candidate_sha
assert p.sha(workspace/'route/incumbent/final-drc.json')==incumbent['native_report_sha256']
assert observed['observed'] is True and observed['signals_sent'] is False and observed['Native_executed_by_observer'] is False
observed_step=next(s for s in parent['steps'] if str(s['pid'])==observed['live_final_workers'][0][0])
assert observed_step['name']=='refill-drc' and observed_step['cwd']==str(workspace/'route')
assert observed_step['status']=='success' and observed_step['exit_code']==0
assert all(s['cleanup_complete'] is True and s['log_truncated'] is False for s in parent['steps'])
assert verified['current_owned_worker_snapshot']['owned_matches']==[]
add_tree(workspace,Path('job-cancelled'))
for path in [plan_path,obs_path,verified_path]:add(path,Path('observations')/path.name)
add(base/'prepared-state.json','preparation/prepared-state.json');add(protocol_path,'preparation/recovery-protocol-required-001.json')
add(runtime/'runtime-distribution.json','runtime/runtime-distribution.json')
for name in ['gui079-observe-postincumbent-cancel-001.py','gui079-postincumbent-cancel-observer-001.log','gui079-postincumbent-cancel-observer-001-time.log']:
    add(ROOT/'.runs'/name,Path('observer')/name)
assert p.sha(Path(plan['helper']))==plan['helper_sha256']
add(helper,'curation/retention-helper030.py');add(Path(__file__),'curation/curate-gui-runtime039-079-postincumbent-cancel-001.py')

known=set(refs);planned_bytes=total;planned_files=len(files)
for path,dest in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    if sha not in known:
        assert b'\0' not in raw;raw.decode('utf-8');known.add(sha);planned_bytes+=len(raw);planned_files+=1
assert planned_bytes<16*1024**2-8192 and planned_files<1999,(planned_bytes,planned_files)
for path,dest in queue:retain(path,dest)

scope='''This packet records one actual runtime039 GUI079 recovery Cancel after a saved accepted invariant-preserved Native-clean incumbent. The finite observer captured the exact owned parent refill Native worker and GUI/CLI ancestry; the lead used actual GUI Cancel. The GUI reported no positive state adopted; CLI exited2 with cancel_requested true, and the durable parent is cancelled/acceptedfalse. No review, accept-choice or export was created. The saved incumbent receipt/candidate and immutable original source remain byte-exact.

Timing is deliberately narrow: the observed refill worker completed normally (exit0), as did subsequent parent final Native DRC and metrics workers. This is not proof that the button interrupted the observed Native worker or of the exact button-click phase. It proves post-incumbent cancellation prevented positive parent adoption in this schedule. The stored final candidate/Native fields are not a cancelled-result acceptance or fallback. The valid saved incumbent remains inspectable retained evidence only.

Own incumbent, parent, actual Native/full-schematic/original/protected/process/rule/PRL artifacts and every completed worker are retained or exactly referenced. The verifier checked stored bindings and one bounded filtered process snapshot (no exact-job workers at that instant), without a Native/test/production-reader rerun or signals. The observer similarly sent no signals or Native commands. There is no all-phase, SIGINT-only, Improve, permanent descendant absence, physical/electrical or human review claim.

The source is the unchanged project-owned generated two-copper fixture under repository LICENSE, with frozen whole recovery-method90 settings and default corrected transport. The journal includes actual cancellation at its root key; earlier observation entries remain historical at the frozen cutoff. The later positive no-repair job is NOT inspected or retained. Other GUI roles/full qualification and external release gates remain pending. No new algorithm, routing-quality/comparison/speed/platform/release-completion claim is made.

Observer6.73wall/.74CPU is additional observation cost. GUI CLI13.296321wall contains parent13.133539wall/9.963494CPU, including incumbent7.473238wall/5.013481CPU and parent final checks; these nested values must not be added twice. Whole interactive GUI, unmetered authoring/review and complete verifier CPU are unknown, not zero. All raw artifacts remain on this Mac outside older raw backups. No downloaded tools, private boards, screenshots or unrelated browser content are published.
'''
scope_path=notes/'SCOPE.md';scope_path.open('x').write(scope);raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha));material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='actual-runtime039-GUI079-post-incumbent-cancellation-partial-cutoff',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,
    actual_GUI=True,actual_GUI_fully_qualified=False,Native_rerun_by_curation=False,human_PCB_review=False,
    source_head=journal['source_head'],runtime_manifest_sha256=journal['runtime_manifest_sha256'],native_version='10.0.7',workspace=str(workspace),
    cutoff=dict(path=str(cutoff.relative_to(ROOT)),sha256=csha,scope='Includes actual postincumbent_cancel root key. Active positive no-repair job excluded.'),
    actual_UI_Cancel=True,actual_UI_outcome=ui['UI_outcome'],whole_recovery_method_seconds=90,
    result=dict(status=parent['status'],accepted=False,repair=None,recovery_needed=False,review_choice_export_created=False,
        parent_receipt_sha256=p.sha(workspace/'route/result.json'),candidate_sha256=parent['candidate_sha256'],
        stored_parent_Native_counts={key:parent['native'][key] for key in ['opens','blocking','warnings','exclusions']},
        candidate_fields_do_not_authorize_cancelled_result=True),
    saved_incumbent=dict(accepted=True,invariants_unchanged=True,Native_counts={key:incumbent['native'][key] for key in ['opens','blocking','warnings','exclusions']},
        full_schematic_parity=incumbent['schematic_parity'],receipt_sha256=p.sha(workspace/'route/incumbent/result.json'),candidate_sha256=candidate_sha,
        receipt_and_candidate_unchanged_since_observer=True,protected_original_items=len(incumbent['protected_route_import']['matches']),cancelled_result_fallback=False),
    original_source=parent['source'],source_hashes=parent['source_hashes'],source_unchanged_now=True,
    timing=dict(observer_live_parent_refill_recorded=True,observed_worker_pid=observed_step['pid'],observed_worker_eventual_status='success',observed_worker_eventual_exit_code=0,
        subsequent_parent_final_workers_completed_normally=True,actual_Native_worker_interruption_proven=False,exact_button_click_phase_proven=False,
        meaning='Actual post-incumbent cancellation/no positive adoption. Native interruption not established.'),
    current_worker_absence=verified['current_owned_worker_snapshot'],verification_receipt_sha256=p.sha(verified_path),all_expected_stored_records_valid=True,
    accounting=dict(observer_complete_external=cost(ROOT/'.runs/gui079-postincumbent-cancel-observer-001-time.log'),CLI_process=cli,
        parent_nested=dict(wall_seconds=parent['wall_seconds'],CPU_seconds=parent['total_cpu_seconds']),
        incumbent_nested=dict(wall_seconds=incumbent['wall_seconds'],CPU_seconds=incumbent['total_cpu_seconds']),
        scope='CLI/parent/incumbent/Native costs nest; do not add twice. Whole interactive GUI, complete verifier CPU and unmetered authoring/review unknown, not zero.'),
    remaining='Positive no-repair, hierarchy/high ordinary/current clean-environment and final GUI roles remain separate; breadth/Windows/restoration/human/physical/publication gates unchanged.',
    rights='Project-owned generated fixture/code; exact original repository GPL license and fixture provenance through retained prior packet references. No private CAD/new binary/browser/screenshots.',
    limits='One actual post-incumbent GUI cancellation schedule, no Native interruption/all-phase/SIGINT-only/Improve/permanent-descendant or full-GUI/project-completion claim.',
    dependencies=dependencies,retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,
        new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),counts_exclude_index_summary=True),
    curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),new_files=len(files),new_bytes=total,material_rows=len(material),actual_GUI_fully_qualified=False)))
