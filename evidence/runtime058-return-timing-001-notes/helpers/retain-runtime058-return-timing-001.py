"""DRAFT: retain owned return-check timing metadata, without rerunning readers.

The failed cProfile attempt has unknown full worker CPU. The subsequent direct
worker timing pair is one diagnostic, not Native acceptance or a benchmark.
"""
from pathlib import Path
import ast, datetime, hashlib, json, math, os, re, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,provenance as pv
self_path=Path(__file__);self_pin=p.sha(self_path)
notes=ROOT/'evidence/runtime058-return-timing-001-notes'
target=ROOT/'evidence/runtime058-return-timing-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target)
refs={};files=[];material=[];total=0;pins={self_path:self_pin}
def bind(path,expected=None):
    path=Path(path);raw=io.read_bytes(path,4*1024**2);pin=hashlib.sha256(raw).hexdigest()
    if expected is not None:assert pin==expected,str(path)
    if path in pins:assert pins[path]==pin,str(path)
    else:pins[path]=pin
    return raw
read=lambda path:json.loads(bind(path))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
nodes=[n for n in ast.parse(bind(helper,'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1')).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
timing=ROOT/'scripts/report_current_comparison.py'
nodes=[n for n in ast.parse(bind(timing,'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e')).body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','complete_cost')]
assert len(nodes)==3
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(timing)+'::cost','exec'),globals())
def cost(path):
    bind(path);value=complete_cost(path)
    assert Path(value['source'])==path and value['time_log_sha256']==pins[path]
    bind(path,value['time_log_sha256']);return value
PINS={
    'runtime058-return-profile-draft-001.py':'19008b159e07e70930f41737643e788b340b2671ae86317f6726eeb292d75eda',
    'runtime058-return-profile-protocol-draft-001.json':'b5688b1ecb9c90f2d8d61c3a25b79577b927d8cc31404fa4a45a74e091583119',
    'runtime058-return-profile-001/execution.json':'01ef79960577ae30cf4700aef5b27c9243b19565a0868cd88641a9c5bea37a8d',
    'runtime058-return-profile-001/cold/process.json':'7ce8a8920a47e30f3baa137091382ab4b50c9b99027b35a737d8085d0104d5bc',
    'runtime058-return-profile-001/cold/complete-command-and-time.log':'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'runtime058-return-profile-001.log':'35f8bcec4118428eba669555f43f4d95a7b833334c9e2acdc322671d1b2ce180',
    'runtime058-return-profile-001-time.log':'5b6f537c830f817d760f4a7df9baee241506675ae7f49ad9b07be7490d5ad674',
    'runtime058-return-timing-draft-002.py':'eace924d19f0f2cb0ca7591d3dc2498e87d7f644ea38f2fa0c0b9fb57ee3ec9b',
    'runtime058-return-timing-protocol-draft-002.json':'be5ed59f9efed660f5b1bbc44f0d69ec5cfaca25f3b5de99dd0055e367cf94f2',
    'runtime058-return-timing-002/execution.json':'3bf155c4885d739ee5b4a7c9637d1f953b09b6d0f7ce2e8e960af91178ecc6fa',
    'runtime058-return-timing-002/cold/process.json':'d35980f2c5ab81aebc0cbc7e7770f22830b6ed1d41768ed448bfe893227d53a9',
    'runtime058-return-timing-002/cold/command.log':'42d333818f87a22824f9148ac3205f43b8789aba1d0f4c0106501d31fa0f1367',
    'runtime058-return-timing-002/cold/result.json':'7e1e65937ec420904a236ed9415bc2e34138463aa8cba0fd25e74f015b65ed05',
    'runtime058-return-timing-002/session/process.json':'b21a337aca58389f8ca4a6af55def35bb03c26903067ad3c608c5a112114b117',
    'runtime058-return-timing-002/session/command.log':'9725964ae79f515205579a0b3b3b451729b0f9a7828622f42e80d8c3b0be578e',
    'runtime058-return-timing-002/session/result.json':'60eb0c1fbcfd75ca9b49da9113c8f0720951e4a317dcbbe2ed09e09d7b8e4859',
    'runtime058-return-timing-002.log':'b3367d79c607731b3e0f0e19ed9645dbea25ec8af2daddbe886bb2731cbd75f9',
    'runtime058-return-timing-002-time.log':'768e0980c9b287b825ec12440a73c88ef178b8772f0e9d6998154edcce66b7eb',
}
queue={ROOT/'.runs'/name:Path('owned')/name for name in PINS}
for path in queue:bind(path,PINS[str(path.relative_to(ROOT/'.runs'))])
queue[helper]=Path('helpers')/helper.name;queue[timing]=Path('helpers')/timing.name
queue[self_path]=Path('helpers')/self_path.name
old=ROOT/'.runs/runtime058-return-profile-001';new=ROOT/'.runs/runtime058-return-timing-002'
old_plan=read(ROOT/'.runs/runtime058-return-profile-protocol-draft-001.json')
plan=read(ROOT/'.runs/runtime058-return-timing-protocol-draft-002.json')
for item,controller in ((old_plan,'runtime058-return-profile-draft-001.py'),(plan,'runtime058-return-timing-draft-002.py')):
    assert item['controller_sha256']==PINS[controller]
    assert item['source_head']=='8f5e96b88dd22cd25919bb71ce47711612994efa'
    assert item['runtime']==str(ROOT/'.runs/runtime-directory-058/runtime')
    assert item['runtime_manifest_sha256']=='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
    assert item['packet_file_count']==813 and item['packet_bytes']==26229091
    assert len(item['PRL_metadata'])==32 and item['variants']==['cold','session']
assert plan['source_hashes']==old_plan['source_hashes'] and plan['packet_files_sha256']==old_plan['packet_files_sha256']
previous=read(old/'execution.json');completed=read(new/'execution.json')
for data,protocol,controller in ((previous,'runtime058-return-profile-protocol-draft-001.json','runtime058-return-profile-draft-001.py'),(completed,'runtime058-return-timing-protocol-draft-002.json','runtime058-return-timing-draft-002.py')):
    assert all(data[key] is False for key in ('accepted','Native','routing','project_complete'))
    assert data['protocol_sha256']==PINS[protocol] and data['controller_sha256']==PINS[controller]
assert len(previous['rows'])==1 and previous['rows'][0]['variant']=='cold'
assert previous['rows'][0]['profile_completed'] is False and previous['rows'][0]['result_sha256'] is None
missing=[old/'cold/result.json',old/'cold/profile.pstats',old/'session']
assert all(not os.path.lexists(path) for path in missing)
sandbox=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)']
def process_bound(folder,variant,controller,protocol,wrapped,okay):
    data=read(folder/'process.json');log=folder/('complete-command-and-time.log' if wrapped else 'command.log')
    argv=(['/usr/bin/time','-lp'] if wrapped else [])+sandbox+[str(ROOT/'.runs/runtime-directory-058/runtime/.venv/bin/python'),'-B',str(ROOT/'.runs'/controller),'--protocol',str(ROOT/'.runs'/protocol),'--protocol-sha256',PINS[protocol],'--execute','--worker',variant]
    assert data['argv']==argv and data['cwd']==str(folder) and data['log']==str(log)
    assert data['cleanup_complete'] is True and data['log_truncated'] is False
    assert type(data['exit_code']) is int and data['exit_code']==(0 if okay else -15)
    assert data['status']==('success' if okay else 'timeout') and data['log_bytes']==len(bind(log))
    return data
failed=process_bound(old/'cold','cold','runtime058-return-profile-draft-001.py','runtime058-return-profile-protocol-draft-001.json',True,False)
assert previous['rows'][0]['process_sha256']==pins[old/'cold/process.json']
assert previous['rows'][0]['complete_log_sha256']==pins[old/'cold/complete-command-and-time.log']
assert read(ROOT/'.runs/runtime058-return-profile-001.log')==dict(completed_variants=1,all_profiled=False,accepted=False,Native=False,routing=False)
assert read(ROOT/'.runs/runtime058-return-timing-002.log')==dict(completed_variants=2,all_timed=True,accepted=False,Native=False,routing=False)
assert [row['variant'] for row in completed['rows']]==['cold','session']
variants=[]
for row in completed['rows']:
    variant=row['variant'];folder=new/variant
    proc=process_bound(folder,variant,'runtime058-return-timing-draft-002.py','runtime058-return-timing-protocol-draft-002.json',False,True)
    record=read(folder/'result.json')
    assert row['timing_completed'] is True and record['status']=='completed' and record['inputs_unchanged'] is True
    assert row['process_sha256']==pins[folder/'process.json'] and row['command_log_sha256']==pins[folder/'command.log'] and row['result_sha256']==pins[folder/'result.json']
    assert record['controller_sha256']==plan['controller_sha256'] and record['protocol_sha256']==completed['protocol_sha256']
    assert all(record[key] is False for key in ('accepted','Native','routing','applied','project_complete'))
    assert record['variant']==variant and record['omissions']==plan['omissions']
    assert [stage['name'] for stage in record['stages']]==['stable_before_account','stable_after_omitted_write','one_full_stored_reader','stable_after_reader']
    variants.append(dict(variant=variant,process_wall_seconds=proc['wall_seconds'],waited_worker_CPU_seconds=proc['cpu_seconds'],stages=record['stages'],sequence_wall_seconds=record['sequence_wall_seconds'],sequence_full_CPU_seconds=record['sequence_full_CPU_seconds'],simulated_post_account_wall_seconds=record['simulated_post_account_wall_seconds'],simulated_post_account_full_CPU_seconds=record['simulated_post_account_full_CPU_seconds'],inputs_unchanged=True,result_sha256=row['result_sha256'],cleanup_complete=True))
failed_time=cost(ROOT/'.runs/runtime058-return-profile-001-time.log')
complete_time=cost(ROOT/'.runs/runtime058-return-timing-002-time.log')
assert failed_time['wall_seconds']==91.24 and failed_time['CPU_seconds']==1.21
assert complete_time['wall_seconds']==70.68 and complete_time['CPU_seconds']==70.25
planned_refs={};planned_files=[];planned_material=[];planned_bytes=0
for path,name in queue.items():
    raw=bind(path);pin=pins[path];destination=planned_refs.get(pin)
    if destination is None:
        assert b'\0' not in raw;raw.decode('utf8');destination=str((notes/name).relative_to(ROOT))
        planned_refs[pin]=destination;planned_bytes+=len(raw)
        planned_files.append(dict(path=destination,bytes=len(raw),sha256=pin))
    planned_material.append(dict(original=str(path.relative_to(ROOT)),retained=destination,bytes=len(raw),sha256=pin))
index=notes/'files.json';index_data=dict(schema=1,files=planned_files,material=planned_material)
index_raw=(json.dumps(index_data,indent=2)+'\n').encode();index_pin=hashlib.sha256(index_raw).hexdigest()
summary=dict(schema=1,kind='runtime058-stored-return-check-timing-with-failed-profiler-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],runtime=plan['runtime'],accepted=False,production_admitted=False,Native=False,routing=False,applied=False,actual_GUI=False,human_review=False,project_complete=False,
    prior_attempt=dict(status='timeout',cold_completed=False,session_started=False,result_written=False,pstats_written=False,cleanup_complete=True,complete_external_wall_seconds=failed_time['wall_seconds'],complete_full_CPU_seconds=None,reported_outer_CPU_seconds=failed_time['CPU_seconds'],reported_direct_time_wrapper_CPU_seconds=failed['cpu_seconds'],time_log_sha256=failed_time['time_log_sha256'],accounting='The killed /usr/bin/time wrapper did not wait/reap its worker into rusage. Both CPU samples are incomplete; unknown additional full worker CPU is not zero. No timing result or pstats was produced.'),
    completed_pair=dict(order=['cold','session'],complete_external_cost=complete_time,variants=variants),
    input_fences_recorded=dict(packet_files=plan['packet_file_count'],packet_bytes=plan['packet_bytes'],PRL_metadata_entries=len(plan['PRL_metadata']),source_hashes=plan['source_hashes'],scope='Successful002 recorded before/after material, original runtime/tools, owner and PRL checks. The001 timeout supplies no completed postcheck. This curator does not rerun source readers, Native or acceptance.'),
    sequence=plan['sequence'],omissions=plan['omissions'],resource_limits=plan['resource_limits'],
    interpretation='One fixed cold-then-session pair: cold means no operation session, not cold OS caches. Session combines existing S-expression memo and Context reconstruction reuse; contributions and generic speedups cannot be inferred. All repeated semantic/source/tool/PRL checks were retained. The Native7 parent/privatechild path does not cache accepted semantic results. Even the session sequence exceeds the historical25s reserve; this is diagnostic evidence for a separately qualified return repair, not proof that a future90s operation fits.',
    archive_scope='The known-vulnerable immutable058 reader consumed an archived provisional positive solely as a stored cost seam. Its canonical result remained timeout/unaccepted. This packet grants neither canonical freshness nor handoff/candidate acceptance and does not promote the archive.',
    accounting='The002 external70.68wall/70.25CPU includes both workers, setup and cleanup; do not add nested stage/sequence/worker samples. The00191.24wall is an additional failed attempt with full CPU unknown. Authoring, AI source review and future curation cost are additional/unknown, not zero. No routing, Native, review, choice, export, candidate copy, account(), canonical publication or final live deadline acceptance was measured.',
    retention='Only owned controllers/protocols, process/results metadata and bounded text logs, plus the pinned shared retention/cost source functions. No foreign CAD/DSN/SES, plots, full Native findings, tools, binaries or pstats. This small metadata packet is not a backup of the813 source/evidence files, full raw restoration or release/electrical/human qualification. The separate source recommendation is not merged here.',
    files_index=dict(path=str(index.relative_to(ROOT)),sha256=index_pin))
summary_raw=(json.dumps(summary,indent=2)+'\n').encode();summary_pin=hashlib.sha256(summary_raw).hexdigest()
assert len(planned_files)+2<2000 and max(len(index_raw),len(summary_raw))<=4*1024**2
assert planned_bytes+len(index_raw)+len(summary_raw)<16*1024**2,'Refuse before writing; do not raise caps'
def fresh():
    for path,pin in pins.items():assert hashlib.sha256(io.read_bytes(path,4*1024**2)).hexdigest()==pin,str(path)
    assert all(not os.path.lexists(path) for path in missing)
fresh()
for path,name in queue.items():retain(path,name)
assert files==planned_files and material==planned_material and total==planned_bytes
for row in files:pins[ROOT/row['path']]=row['sha256']
fresh();p.save_json(index,index_data);bind(index,index_pin);fresh()
fresh();p.save_json(target,summary);bind(target,summary_pin);fresh()
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),summary_sha256=summary_pin,accepted=False,Native=False)))
