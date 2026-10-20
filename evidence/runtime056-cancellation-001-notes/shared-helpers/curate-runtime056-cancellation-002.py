"""Retain one current cancellation control using the established text helpers."""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
from scripts import report_current_comparison as shared
notes=ROOT/'evidence/runtime056-cancellation-001-notes';target=ROOT/'evidence/runtime056-cancellation-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
prior=f.read_json(ROOT/'evidence/runtime056-native-milestone-001.json');index=ROOT/prior['files_index']['path']
assert p.sha(index)==prior['files_index']['sha256']
for row in f.read_json(index)['files']:refs.setdefault(row['sha256'],row['path'])
for row in f.read_json(index)['material']:refs.setdefault(row['sha256'],row['retained'])
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
definitions=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree')]
assert len(definitions)==2
exec(compile(ast.Module(body=definitions,type_ignores=[]),str(helper)+'::retain','exec'),globals())
base=ROOT/'.runs/runtime056-cancellation-002';plan=f.read_json(base/'protocol.json');execution=f.read_json(base/'execution.json')
assert execution['control_passed'] is True and execution['stable'] is True and execution['protocol_sha256']==p.sha(base/'protocol.json')
child=Path(execution['child']);assert p.sha(child)==execution['child_sha256']
data=f.read_json(child);assert data['control_passed'] is True and data['status']=='completed' and data['actual_GUI'] is False
assert data['parent_status']=='cancelled' and data['parent_accepted'] is False and data['remaining_owned_group']==[]
assert data['observed_owned_engine']['pid']==data['engine_process']['pid'] and data['engine_process']['cleanup_complete'] is True
assert data['engine_process']['cancel_signal']=='SIGINT' and data['engine_process']['exit_code']==-9
assert io.inventory(Path(plan['source']).parent)==plan['source_hashes']==data['source_hashes']
runtime=Path(plan['runtime']);assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']==prior['runtime_manifest_sha256']
for name in ('review','choice','export'):assert not (Path(data['workspace'])/name).exists()
tree(base,Path('enclosure'));tree(child.parent,Path('control'));tree(Path(plan['source']).parent,Path('source'))
for name in ('run-runtime056-cancel-001.py','runtime056-cancellation-001.log','runtime056-cancellation-001-time.log','run-runtime056-cancel-002.py','runtime056-cancellation-002.log','runtime056-cancellation-002-time.log','qualify-runtime049-cancel-002.py','curate-runtime056-cancellation-001.py','curate-runtime056-cancellation-001.log','curate-runtime056-cancellation-001-time.log'):
    retain(ROOT/'.runs'/name,Path('controllers-and-exits')/name)
for path in (ROOT/'scripts/native_cancellation.py',ROOT/'autorouter/runner.py',Path(__file__)):
    retain(path,Path('shared-helpers')/path.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime056-installed-production-controller-active-engine-cancellation-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,human_review=False,actual_GUI=False,control_passed=True,source_head=prior['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],protocol_sha256=p.sha(base/'protocol.json'),child_receipt_sha256=p.sha(child),observed_owned_engine=data['observed_owned_engine'],engine_log_bytes_at_signal=data['engine_log_bytes_at_signal'],requested_signal='SIGINT',recorded_engine_exit_code=-9,engine_cleanup_complete=True,remaining_owned_group_at_observation=[],parent_status='cancelled',parent_accepted=False,adoption_refusal=data['adoption_refusal'],central_reader_refusal=data['central_reader_refusal'],source_and_tools_unchanged=True,complete_cost=shared.complete_cost(ROOT/'.runs/runtime056-cancellation-002-time.log'),failed_preflight_001_cost=shared.complete_cost(ROOT/'.runs/runtime056-cancellation-001-time.log'),failed_curation_001_cost=shared.complete_cost(ROOT/'.runs/curate-runtime056-cancellation-001-time.log'),failed_curation_001='Missing hashlib import in metadata binder; failed before any payload write.002 adds the import and reuses completed execution; no Native repeated.',independent_AI_raw_review=dict(reviewer='/root/context_reuse_skeptic',no_concrete_discrepancy_found=True,scope='Stored protocol/execution/process and child hash/controller binding only. Requested SIGINT, eventual-9 and startup-only observation explicit; no execution or human approval.'),failed_preflight_001='Wrapper used no-argument18GiB historical archive audit and stopped before any Native/controller work. Retained unchanged.002 uses the existing same18GiB per-job guard plus4GiB free prerequisite; no cap raise, evidence deletion or runtime change.',scope='One actual current056 Improve incumbent-engine SIGINT through Request/Workflow/CliJob. A75-byte engine startup log and live owned PID/group were observed, not routing-algorithm entry; parent exited2, unaccepted/cancelled, adoption and central reader refused, no review/choice/export. Engine exit-9 remains explicit: no graceful-exit claim. Immediate empty group snapshot is not permanent descendant absence or GUI/all-phase/late-natural-expiry qualification.',accounting='External complete exits count once, nested controller/CLI/engine values overlap. Preparation, curation, authoring, AI review and GUI access costs additional; unmetered is unknown, notzero.',rights='Owned fixture/code/text receipts only. No downloaded engine/tool/venv binaries or private/foreign boards. Later raw remains Mac-only/outside010; not full restoration or release qualification.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,control_passed=True,actual_GUI=False)))
