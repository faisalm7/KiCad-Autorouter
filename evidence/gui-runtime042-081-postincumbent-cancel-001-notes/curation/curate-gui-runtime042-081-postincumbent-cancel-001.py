"""Retain one frozen actual GUI081 forced Cancel; never rerun Native/readers.

Prepare only. The lead supplies the exact frozen journal002 hash and audited
administration HEAD. Other GUI roles and full product qualification are excluded.
"""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io

SOURCE_HEAD='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
MANIFEST='1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
PREPARED='7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3'
JOURNAL='0de7f543a7d63b499ec9fad82b6b2c2ca9271d8998073bb018d9c97ded7149fc'
CONTROLLER='03602f133698d53840757111f331c40465c6d1223af3601e4bacc2c1c4a1b64e'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--journal-sha256',required=True)
parser.add_argument('--checkpoint-head',required=True)
args=parser.parse_args()
assert args.journal_sha256==JOURNAL and re.fullmatch('[0-9a-f]{40}',args.checkpoint_head)
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
base=ROOT/'.runs/runtime-directory-042/runtime/.runs/gui-session081';runtime=base.parents[1]
workspace=base/'jobs/autorouter-gui-69b2f307ec564d258aef2cfdb0312ba7'
control=base/'recovery-controls-001/no-repair'
notes=ROOT/'evidence/gui-runtime042-081-postincumbent-cancel-001-notes'
output=ROOT/'evidence/gui-runtime042-081-postincumbent-cancel-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
cutoff=ROOT/'.runs/gui081-observations-002.json'
assert p.sha(cutoff)==JOURNAL
journal=json.loads(cutoff.read_bytes())
assert journal['runtime']=='042' and journal['session']=='081'
assert journal['source_head']==SOURCE_HEAD and journal['runtime_manifest_sha256']==MANIFEST
assert journal['prepared_state_sha256']==PREPARED
selected={}
for role in ('postincumbent_forced_cancel','incompatible_recovery_settings_refusal'):
    rows=[row for row in journal['observations'] if row.get('role')==role]
    assert len(rows)==1 and rows[0]['actual_gui'] is True
    selected[role]=rows[0]
ui=selected['postincumbent_forced_cancel'];refusal=selected['incompatible_recovery_settings_refusal']
assert ui['workspace']==str(workspace) and ui['actual_Preview'] and ui['actual_Recover'] and ui['actual_Cancel']
assert 'No positive state adopted' in ui['observed_findings']
assert refusal['new_workspace_created'] is False and refusal['settings_not_silently_changed'] is True
assert refusal['job_count_before']==refusal['job_count_after']
assert 'Settings were not changed' in refusal['observed_findings']
assert p.sha(base/'prepared-state.json')==PREPARED and p.sha(runtime/'runtime-distribution.json')==MANIFEST
prepared=json.loads((base/'prepared-state.json').read_bytes())
manifest=json.loads((runtime/'runtime-distribution.json').read_bytes())
assert prepared['source_head']==SOURCE_HEAD and prepared['runtime_manifest_sha256']==MANIFEST
assert len(manifest['immutable_files_sha256'])==53
assert all(p.sha(runtime/name)==pin for name,pin in manifest['immutable_files_sha256'].items())
protocol_path=Path(prepared['recovery_protocol'])
assert protocol_path==control.parent/'protocol-required-001.json'
assert p.sha(protocol_path)==prepared['recovery_protocol_sha256']
declared=json.loads(protocol_path.read_bytes())['recovery']['no-repair']
assert declared['method']=='recover' and declared['whole_method_seconds']==90

refs={};files=[];material=[];total=0;dependencies=[];queue=[]
for name,pin in [('runtime042-native-milestone-001','7faf3fa21c08073ede6bbb1825b15633c25997a7440b6da37dc2e0edac140d4b'),
                 ('gui-runtime042-081-progress-001','20f3b09c68c861e20dafc9917652ea78df4e9db03e451179277ccf351e65af7c')]:
    path=ROOT/'evidence'/(name+'.json');assert p.sha(path)==pin
    record=json.loads(path.read_bytes());index=record['files_index']
    assert record['source_head']==SOURCE_HEAD and record['runtime_manifest_sha256']==MANIFEST
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

def add_tree(path,destination):
    for relative in io.inventory(path,max_bytes=64*1024**2):
        if set(Path(relative).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        add(path/relative,Path(destination)/relative)

parent_path=workspace/'route/result.json';inc_path=workspace/'route/incumbent/result.json'
parent=json.loads(parent_path.read_bytes());inc=json.loads(inc_path.read_bytes())
ready_path=control/'postincumbent-pause-ready-001.json';observed_path=control/'postincumbent-pause-result-001.json'
ready=json.loads(ready_path.read_bytes());observed=json.loads(observed_path.read_bytes())
cli=json.loads((workspace/'route.command.process.json').read_bytes())
assert p.sha(parent_path)==ui['parent_receipt_sha256'] and p.sha(inc_path)==ui['incumbent_receipt_sha256']
assert p.sha(ready_path)==ui['ready_receipt_sha256']==observed['ready_sha256']
assert p.sha(observed_path)==ui['control_receipt_sha256']
assert parent['status']=='cancelled' and parent['accepted'] is False and parent['schematic_parity']=='not checked'
assert parent['repair'] is None and parent['recovery_needed'] is False
assert parent['budget_seconds']==parent['cpu_budget_seconds']==90
assert parent['tools']==inc['tools']==prepared['tools']
assert parent['source']==inc['source']==declared['source'] and refusal['source']==declared['source']
assert parent['source_hashes']==inc['source_hashes']==declared['source_hashes']
source=Path(parent['source']);assert io.inventory(source.parent)==io.inventory(Path(declared['original_source']).parent)==parent['source_hashes']
assert len(parent['source_hashes'])==4 and json.loads((workspace/'settings.json').read_bytes())==declared['settings']
assert not any((workspace/name).exists() for name in ('review','choice','export'))
assert not (workspace/'route/final-drc.json').exists()
assert not any(step['name']=='final-drc' and step['cwd']==str(workspace/'route') for step in parent['steps'])
assert inc['status']=='routing_accepted' and inc['accepted'] is True and inc['invariants_unchanged'] is True
assert inc['schematic_parity']=='checked by final native DRC'
assert p.sha(inc_path)==parent['incumbent']['receipt_sha256']==observed['incumbent_sha256']==ready['incumbent_sha256']
candidate=Path(inc['candidate']);assert candidate==workspace/'route/incumbent/candidate'/source.name
assert p.sha(candidate)==inc['candidate_sha256']==observed['incumbent_candidate_sha256']
assert len(inc['protected_route_import']['matches'])==1
assert all(inc['native'][key]==0 for key in ('opens','blocking','warnings','exclusions'))
assert len(inc['native']['ignored_checks'])==2
assert p.sha(workspace/'route/incumbent/final-drc.json')==inc['native_report_sha256']
raw_drc=json.loads((workspace/'route/incumbent/final-drc.json').read_bytes())
assert raw_drc['kicad_version']=='10.0.7' and all(raw_drc[key]==[] for key in ('violations','unconnected_items','schematic_parity'))
final=next(step for step in inc['steps'] if step['name']=='final-drc')
assert '--schematic-parity' in final['argv'] and final['exit_code']==0
assert all(p.sha(workspace/'route/incumbent/code'/Path(name).name)==pin for name,pin in inc['tools']['implementation_sha256'].items())
worker=observed['worker'];assert worker==ready['worker'] and worker['pid']==40643 and worker['ppid']==40585
assert observed['ancestor_chain']==ready['ancestor_chain']
assert [row['pid'] for row in observed['ancestor_chain']]==[40643,40585,36895]
assert observed['helper_sha256']==ready['helper_sha256']==CONTROLLER
assert observed['workspace']==ready['workspace']==str(workspace)
assert observed['source_head']==SOURCE_HEAD and observed['runtime_manifest_sha256']==MANIFEST and observed['prepared_state_sha256']==PREPARED
assert observed['control_observation_complete'] is True and observed['paused'] is True
assert observed['known_worker_exit_during_hold'] is True and observed['worker_gone_at_cleanup'] is True
assert observed['hold_seconds']==15 and observed['natural_timing_claim'] is False
assert observed['GUI_signalled'] is False and observed['CLI_signalled'] is False
assert observed['parent_schematic_parity']=='not checked' and observed['incumbent_schematic_parity']=='checked by final native DRC'
refill=next(step for step in parent['steps'] if step['pid']==worker['pid'])
raw_process=json.loads((workspace/'route/refill-drc-process.json').read_bytes())
for key in ('pid','argv','cwd','status','exit_code','cleanup_complete','log_truncated','log_bytes'):
    assert refill[key]==raw_process[key]
assert refill['name']=='refill-drc' and refill['cwd']==str(workspace/'route')
assert refill['status']=='cancelled' and refill['exit_code']==-15 and refill['cleanup_complete'] is True
assert refill['local_settings_policy']=='job-owned-prl-immutable-v1'
assert refill['local_settings_protection']['flags_restored'] is True and refill['local_settings_protection']['bytes_unchanged'] is True
assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in parent['steps'])
assert cli['exit_code']==2 and cli['cancel_requested'] is True and cli['log_truncated'] is False
assert (workspace/'route.command.log').stat().st_size==cli['log_bytes']
parent_reader_path=ROOT/'.runs/gui081-postincumbent-parent-reader-001.log'
inc_reader_path=ROOT/'.runs/gui081-postincumbent-incumbent-reader-001.log'
parent_reader=json.loads(parent_reader_path.read_bytes());inc_reader=json.loads(inc_reader_path.read_bytes())
assert parent_reader['current'] is False and inc_reader['current'] is True
assert inc_reader['candidate']==str(candidate) and inc_reader['candidate_sha256']==inc['candidate_sha256']
assert ui['parent_current_reader'] is False and ui['incumbent_current_reader'] is True
assert sorted(row['pid'] for row in ui['known_PID_absence_after'])==[40585,40643]
assert all(row['returncode']==1 and row['output']=='' for row in ui['known_PID_absence_after'])
add_tree(workspace,'cancelled-job');add_tree(source.parent,'source')
for path,dest in [(cutoff,'cutoff/observations-002.json'),(base/'prepared-state.json','preparation/prepared-state.json'),
                  (protocol_path,'preparation/recovery-protocol-required-001.json'),(runtime/'runtime-distribution.json','runtime/runtime-distribution.json'),
                  (ready_path,'control/postincumbent-pause-ready-001.json'),(observed_path,'control/postincumbent-pause-result-001.json')]:add(path,dest)
for name in ('gui081-postincumbent-pause-control-001.py','gui081-postincumbent-pause-control-001.log','gui081-postincumbent-pause-control-001-time.log',
             'gui081-postincumbent-parent-reader-001.log','gui081-postincumbent-parent-reader-001-time.log',
             'gui081-postincumbent-incumbent-reader-001.log','gui081-postincumbent-incumbent-reader-001-time.log'):
    add(ROOT/'.runs'/name,Path('control-and-readers')/name)
assert p.sha(ROOT/'.runs/gui081-postincumbent-pause-control-001.py')==CONTROLLER
add(helper,'curation/retention-helper030.py')
add(ROOT/'.runs/curate-gui-runtime039-079-postincumbent-cancel-001.py','curation/template039.py')
add(Path(__file__),'curation/curate-gui-runtime042-081-postincumbent-cancel-001.py');add(ROOT/'LICENSE','rights/LICENSE')

scope='''One actual runtime042 GUI081 forced post-incumbent cancellation and one incompatible recovery-settings refusal only. The lead actually previewed/recovered, then clicked Cancel after the exact owned parent Native refill worker was deliberately held. That worker returned cancelled/-15/cleanup_complete, GUI CLI exited2/cancel_requested and the durable parent is cancelled/acceptedfalse with schematic parity not checked; no own final parity DRC/review/choice/export exists. Accepted incumbent is separately retained with its own actual Native10.0.7/fullSCH/original rules/unchanged source/protected-one proof and candidate. Parent false and incumbent true production-reader logs are retained, not rerun. No fallback/adoption/delivery is authorized by the saved incumbent.

The pause helper observed an earlier cancelled parent publication hash different from the final receipt. It stored that hash and schema observations only, not earlier raw parent bytes. The immutable042 recovery source publishes around stable/accounting again, so accounting finalization is a plausible inference, not a proved exact-byte explanation. Both hashes are retained honestly; final journal, completed CLI and actual readers bind qualification to final parent. No missing earlier bytes are invented.

This is one forced15second opportunity, not natural timing, SIGINT-only, all-phase, CallAfter already queued, permanent absence, hostile-writer/power-loss or whole-GUI/product qualification. Known PID absence is one lead-retained sample. Source is the unchanged owned four-file fixture, original protected item count1; no new family/algorithm/routing-quality/speed/electrical/human/physical/Windows/release claim. Other journal roles remain outside this packet.

Controller27.14wall/1.09CPU excludes the independent GUI child and overlaps GUI CLI23.1383wall, whose parent22.9198wall/8.68543CPU includes incumbent/Native steps. Reader costs are separate. Full interactive wall/CPU and unmetered authoring/research/review are unknown, notzero; nested costs must not be added twice. This curator checks stored bytes/schema only. No Native/readers/GUI/tests/Git rerun, downloaded tools/apps/venvs, private boards, browser content or pixels. Raw remains Mac-only outside older backups.
'''
known=set(refs);planned_bytes=len(scope.encode());planned_files=1;expected={}
for path,dest in queue:
    raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
    assert b'\0' not in raw;raw.decode('utf8')
    expected[str(path)]=(len(raw),sha)
    if sha not in known:known.add(sha);planned_bytes+=len(raw);planned_files+=1
assert planned_bytes<16*1024**2-8192 and planned_files<1999,(planned_bytes,planned_files)
assert p.sha(cutoff)==JOURNAL and p.sha(base/'prepared-state.json')==PREPARED
for path,dest in queue:
    assert (path.stat().st_size,p.sha(path))==expected[str(path)]
    retain(path,dest)
notes.mkdir(parents=True,exist_ok=True)
scope_path=notes/'SCOPE.md'
with scope_path.open('x') as stream:stream.write(scope)
raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index_path=notes/'files.json';p.save_json(index_path,dict(schema=1,files=files,material=material))
u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='actual-runtime042-GUI081-forced-postincumbent-cancel-bounded-cutoff',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,
    actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    Native_rerun_by_curation=False,production_readers_rerun_by_curation=False,
    source_head=SOURCE_HEAD,runtime_manifest_sha256=MANIFEST,native_version='10.0.7',publication_checkpoint_head=args.checkpoint_head,
    workspace=str(workspace),cutoff=dict(path=str(cutoff.relative_to(ROOT)),sha256=JOURNAL),actual_UI=selected,
    parent=dict(status='cancelled',accepted=False,schematic_parity='not checked',receipt_sha256=p.sha(parent_path),own_final_validation=False),
    incumbent=dict(status=inc['status'],accepted=True,schematic_parity=inc['schematic_parity'],receipt_sha256=p.sha(inc_path),
        candidate_sha256=inc['candidate_sha256'],protected_count=1,Native=inc['native'],fallback_delivery=False),
    source=str(source),source_hashes=parent['source_hashes'],source_unchanged_now=True,
    role=dict(forced_window=True,natural_timing_claim=False,actual_worker_interruption_in_this_forced_interval=True,
        worker_pid=40643,worker_parent_pid=40585,worker_status=refill['status'],worker_exit_code=-15,
        worker_cleanup_complete=True,controller_observation=observed,known_PID_absence_sample=ui['known_PID_absence_after']),
    parent_publication=dict(controller_observed_sha256=observed.get('parent_receipt_sha256'),final_sha256=p.sha(parent_path),
        earlier_raw_bytes_retained=False,exact_difference_unproved=True,possible_accounting_finalization_inference=True),
    production_reader_outputs=dict(parent=parent_reader,incumbent=inc_reader),
    accounting=dict(controller_complete_external=cost(ROOT/'.runs/gui081-postincumbent-pause-control-001-time.log'),
        parent_reader_complete_external=cost(ROOT/'.runs/gui081-postincumbent-parent-reader-001-time.log'),
        incumbent_reader_complete_external=cost(ROOT/'.runs/gui081-postincumbent-incumbent-reader-001-time.log'),
        GUI_CLI_process=cli,parent_nested=dict(wall_seconds=parent['wall_seconds'],CPU_seconds=parent['total_cpu_seconds']),
        incumbent_nested=dict(wall_seconds=inc['wall_seconds'],CPU_seconds=inc['total_cpu_seconds']),
        interactive_whole_wall_seconds=None,interactive_whole_CPU_seconds=None,
        scope='Controller excludes independent GUI job and wall overlaps it; CLI/parent/incumbent/Native costs nest. Readers additional; unknown not zero.'),
    rights='Owned generated fixture/core GPL; no private CAD, new binary/tool/app/venv or browser/pixel payload.',
    limitations='Forced exact phase only; no natural/SIGINT-only/allphase/permanentabsence/CallAfterqueued/fullGUI/comparative/human/physical claim.',
    dependencies=dependencies,curator_template=dict(path='.runs/curate-gui-runtime039-079-postincumbent-cancel-001.py',
        sha256=p.sha(ROOT/'.runs/curate-gui-runtime039-079-postincumbent-cancel-001.py')),
    retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),functions=['retain','tree','cost'],
        max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),
        new_payload_bytes=total,material_rows=len(material),counts_exclude_index_summary=True),
    curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),
    files_index=dict(path=str(index_path.relative_to(ROOT)),sha256=p.sha(index_path)))
p.save_json(output,summary)
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
assert p.sha(cutoff)==JOURNAL and p.sha(base/'prepared-state.json')==PREPARED
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index_path),
    new_files=len(files),new_bytes=total,material_rows=len(material),actual_GUI_fully_qualified=False)))
