"""Prepare-only final GUI081 role consolidation; no Native/readers/tests/GUI.

Run only after journal004 is frozen and the current recovery-deliveries packet
exists. External hashes are mandatory; missing/incomplete roles refuse.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
HEAD='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
MANIFEST='1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
PREPARED='7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3'
PROTOCOL='f4119835b72ef3b74b7cffcca50f0854ec499a95698d55e26be5bfeb67012851'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--journal004-sha256',required=True)
parser.add_argument('--recovery-packet-sha256',required=True)
parser.add_argument('--checkpoint-head',required=True)
args=parser.parse_args()
assert re.fullmatch('[0-9a-f]{64}',args.journal004_sha256)
assert re.fullmatch('[0-9a-f]{64}',args.recovery_packet_sha256)
assert re.fullmatch('[0-9a-f]{40}',args.checkpoint_head)
started=time.monotonic();cpu0=resource.getrusage(resource.RUSAGE_SELF)
base=ROOT/'.runs/runtime-directory-042/runtime/.runs/gui-session081';runtime=base.parents[1]
final_path=ROOT/'.runs/gui081-observations-final-001.json'
summary_path=ROOT/'.runs/gui-runtime042-081-functional-summary-001.json'
assert not os.path.lexists(final_path) and not os.path.lexists(summary_path)
inputs=[]
def bound(path,pin):
    path=Path(path)
    assert ROOT in path.parents and path.resolve()==path and not path.is_symlink()
    raw=io.read_bytes(path,4*1024**2)
    assert hashlib.sha256(raw).hexdigest()==pin
    inputs.append(dict(path=str(path),sha256=pin,bytes=len(raw)))
    return json.loads(raw)

prepared=bound(base/'prepared-state.json',PREPARED)
manifest=bound(runtime/'runtime-distribution.json',MANIFEST)
assert manifest['build_source']['git_head']==HEAD
assert prepared['source_head']==HEAD and prepared['runtime_manifest_sha256']==MANIFEST
protocol_path=Path(prepared['recovery_protocol'])
assert protocol_path==base/'recovery-controls-001/protocol-required-001.json'
assert prepared['recovery_protocol_sha256']==PROTOCOL
protocol=bound(protocol_path,PROTOCOL)
assert protocol['source_head']==HEAD and protocol['runtime_manifest_sha256']==MANIFEST
journal_pins=['cbdb6d3140250b23cd9ef072b26aa9c79010acb452f89ca78db9790353ce57a5',
    '0de7f543a7d63b499ec9fad82b6b2c2ca9271d8998073bb018d9c97ded7149fc',
    'bfeade4396a71deb9f3fab2526d08e538876938a22a2ed278ef583a2ad0890df',args.journal004_sha256]
journals=[];journal_records=[];rows={};row_origins={}
for number,pin in enumerate(journal_pins,1):
    path=ROOT/'.runs'/f'gui081-observations-{number:03d}.json'
    data=bound(path,pin)
    assert data['runtime']=='042' and data['session']=='081'
    assert data['source_head']==HEAD and data['runtime_manifest_sha256']==MANIFEST
    assert data['prepared_state_sha256']==PREPARED and data['active_workspace'] is None
    assert type(data['frozen_utc']) is str and data['frozen_utc']
    if number>1:
        prior=data['prior_frozen_journal']
        assert Path(prior['path'])==ROOT/'.runs'/f'gui081-observations-{number-1:03d}.json'
        assert prior['sha256']==journal_pins[number-2]
    for index,row in enumerate(data['observations']):
        label=row['role'];assert label not in rows and row['actual_gui'] is True
        rows[label]=row;row_origins[label]=dict(journal=str(path),journal_sha256=pin,row_index=index)
    journals.append(dict(path=str(path),sha256=pin,frozen_utc=data['frozen_utc']))
    journal_records.append(data)
packet_specs={
    'progress':('gui-runtime042-081-progress-001','20f3b09c68c861e20dafc9917652ea78df4e9db03e451179277ccf351e65af7c',journal_pins[0]),
    'cancel':('gui-runtime042-081-postincumbent-cancel-001','a3061f78481d696c77d4d9fd071dd4a3a4f625af5c1b6d5fc7f24138b6d717a7',journal_pins[1]),
    'ordinary':('gui-runtime042-081-ordinary-controls-001','a3ace1802935f18211229a6d55775262eeab1cd80b6c28c9d24f4702574fd936',journal_pins[2]),
    'recovery':('gui-runtime042-081-recovery-deliveries-001',args.recovery_packet_sha256,journal_pins[3])}
packets={};packet_refs={}
for key,(name,pin,jpin) in packet_specs.items():
    path=ROOT/'evidence'/(name+'.json');data=bound(path,pin)
    assert data['source_head']==HEAD and data['runtime_manifest_sha256']==MANIFEST
    assert data['actual_GUI'] is True and data['actual_GUI_fully_qualified'] is False
    assert data['accepted'] is False and data['project_complete'] is False and data['human_PCB_review'] is False
    assert data['cutoff']['sha256']==jpin
    index=data['files_index'];bound(ROOT/index['path'],index['sha256'])
    packets[key]=data;packet_refs[key]=dict(path=str(path),sha256=pin,files_index=index)

corrections=journal_records[1]['accounting_corrections']
additive=packets['progress']['accounting']['additive_corrections']
assert type(corrections) is list and len(corrections)==1 and corrections==additive
correction=corrections[0]
assert correction['original_summary_sha256']=='968873ec10544c2c7a6610d915cee78849c7b4923c37fb762c8dcbd82f5ac80b'
assert correction['frozen_journal_sha256']==journal_pins[0]
assert correction['field']=='export_freshness_after_reader.boundary_external_cost.nested_reader_included'
assert correction['original_value'] is True and rows['export_freshness_after_reader']['boundary_external_cost']['nested_reader_included'] is True
assert correction['controller_wall_seconds']==6.61 and correction['controller_CPU_seconds']==1.66
assert correction['controller_CPU_includes_reader'] is False and correction['reader_CPU_seconds'] is None
assert correction['interactive_whole_CPU_seconds'] is None and correction['original_frozen_journal_unchanged'] is True
assert correction['routing_or_Native_rerun'] is False
assert correction['correct_scope']=='Controller wall6.61seconds overlaps the GUI-owned reader interval. Controller CPU1.66seconds excludes that independently launched GUI child; reader and whole interactive CPU are unknown, not zero.'
correction_provenance=dict(journal=dict(**journals[1],JSON_pointer='/accounting_corrections'),
    packet=dict(**packet_refs['progress'],JSON_pointer='/accounting/additive_corrections'),
    original_observation=dict(**row_origins['export_freshness_after_reader'],field=correction['field']),
    precedence='Exact additive correction supersedes the original nested_reader_included=true accounting flag; frozen originals remain unchanged.')
covered={}
def record(label,packet_key,proof):
    row=rows[label]
    assert proof==row
    covered[label]=dict(**row_origins[label],packet=packet_refs[packet_key],workspace=row.get('workspace'))
for key,field in [('progress','lead_observation'),('ordinary','lead_observation'),('recovery','actual_UI')]:
    data=packets[key];seen=set()
    for item in data['roles']:
        label=item['role'];assert label not in seen;seen.add(label)
        record(label,key,item[field])
        assert item['workspace']==rows[label]['workspace']
    expected=({'positive_delivery','source_freshness','settings_freshness','export_freshness_after_reader'} if key=='progress'
        else {'alias_positive_delivery','reject','ordinary_engine_cancel','hierarchy_high_budget'} if key=='ordinary'
        else {'recovery_repair_delivery','recovery_no_repair_delivery'})
    assert seen==expected
for label,proof in packets['cancel']['actual_UI'].items():record(label,'cancel',proof)
record('unsupported4Cu_refusal','recovery',packets['recovery']['unsupported4Cu_actual_refusal'])
record('launch_settings_invalid_budget','progress',packets['progress']['launch_static_budget'])
record('persistent_settings_save_load','ordinary',packets['ordinary']['static_settings_customization']['observation'])
record('alias_pre_routing_diagnostic_contamination_refusal','ordinary',packets['ordinary']['failed_first_alias']['lead_observation'])
failure=packets['ordinary']['failed_first_alias']
assert failure['product_first_attempt_success'] is False and failure['Native_started'] is False
assert failure['GUI_CLI_process']['exit_code']==2 and failure['retry_explicit'] is True
assert packets['cancel']['parent']['accepted'] is False and packets['cancel']['parent']['schematic_parity']=='not checked'
assert packets['cancel']['incumbent']['accepted'] is True
assert packets['cancel']['incumbent']['schematic_parity']=='checked by final native DRC'
refusal=rows['unsupported4Cu_refusal']
assert refusal['new_workspace_created'] is False and refusal['job_count_before']==refusal['job_count_after']
assert refusal['dedicated_two_layer_guard_isolated'] is False
for item in packets['recovery']['roles']:
    assert all(item[name][key]==0 for name in ('parent_Native','export_Native') for key in ('opens','blocking','exclusions'))
    assert item['before_open']['production_readers_current_then'] is True
    assert item['after_open']['source_unchanged'] is True and item['after_open']['candidate_PCB_unchanged'] is True
    assert item['after_open']['new_Native_validity_inferred'] is False

ordinary={'positive':'positive_delivery','high_budget':'hierarchy_high_budget','source_control':'source_freshness',
    'settings_control':'settings_freshness','export_control':'export_freshness_after_reader','cancel':'ordinary_engine_cancel',
    'reject':'reject','alias_positive':'alias_positive_delivery'}
recovery={'repair':'recovery_repair_delivery','no-repair':'recovery_no_repair_delivery',
    'incompatible_settings_refusal':'incompatible_recovery_settings_refusal',
    'unsupported4Cu_refusal_before_workspace':'unsupported4Cu_refusal','cancel_with_incumbent_retained':'postincumbent_forced_cancel'}
assert set(protocol['ordinary_required_roles'])==set(ordinary) and set(protocol['recovery_required_roles'])==set(recovery)
coverage={kind:{role:dict(observed_role=label,**covered[label]) for role,label in mapping.items()}
    for kind,mapping in [('ordinary',ordinary),('recovery',recovery)]}
assert all(label in covered for label in rows)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
limits='Assigned functional roles only; no fullGUI/product/release, general superiority, human/electrical/physical, Windows, restoration, cleanOS or relocation claim. Forced Native Cancel is one held interval, not natural/SIGINT-only/allphase/permanent absence. After-reader refusal also delayed adoption; CallAfter already queued is unproved. Preopen proof does not renew validity after editor metadata changes.'
final=dict(schema=1,runtime='042',session='081',source_head=HEAD,runtime_manifest_sha256=MANIFEST,
    prepared_state_sha256=PREPARED,recovery_protocol_sha256=PROTOCOL,frozen_utc=now,active_workspace=None,
    observations=[row for data in [bound(ROOT/'.runs'/f'gui081-observations-{n:03d}.json',pin) for n,pin in enumerate(journal_pins,1)] for row in data['observations']],
    source_journals=journals,role_coverage=coverage,protocol_functional_roles_recorded=True,
    accounting_corrections=corrections,accounting_correction_provenance=correction_provenance,
    actual_GUI_qualified=False,actual_GUI_fully_qualified=False,project_complete=False,human_review=False,
    first_failed_alias_retained=True,forced_CallAfter_already_queued_proved=False,scope=limits)
final_raw=(json.dumps(final,indent=2,sort_keys=True)+'\n').encode();assert len(final_raw)<=1024**2
final_sha=hashlib.sha256(final_raw).hexdigest()
usage=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='runtime042-GUI081-protocol-functional-role-summary',recorded_utc=now,
    runtime='042',session='081',source_head=HEAD,runtime_manifest_sha256=MANIFEST,prepared_state_sha256=PREPARED,
    protocol=str(protocol_path),protocol_sha256=PROTOCOL,journal=str(final_path),journal_sha256=final_sha,
    source_journals=journals,packets=packet_refs,protocol_functional_roles_recorded=True,role_coverage=coverage,
    accounting_corrections=corrections,accounting_correction_provenance=correction_provenance,
    static_customization=covered['persistent_settings_save_load'],failed_alias=covered['alias_pre_routing_diagnostic_contamination_refusal'],
    unsupported4Cu_actual_gate='Earlier schematic-class preflight; dedicated two-layer guard not isolated. Ordinary Route retains separate class authority.',
    accepted=False,actual_GUI=True,actual_GUI_fully_qualified=False,project_complete=False,human_PCB_review=False,
    physical_electrical_validation=False,Windows_qualified=False,restoration_qualified=False,general_superiority_claim=False,
    first_attempt_product_success=False,forced_CallAfter_already_queued_proved=False,
    publication_checkpoint_head=args.checkpoint_head,helper_sha256=p.sha(Path(__file__)),
    accounting=dict(additive_corrections=additive,interactive_whole_wall_seconds=None,interactive_whole_CPU_seconds=None,
        export_boundary_scope=correction['correct_scope'],
        scope='Exact additive corrections supersede original inclusion flags. Controller6.61wall overlaps independent reader;1.66CPU excludes it. Packet costs retain all attempts/helpers/curation and nested samples. No synthetic aggregate; reader/interactiveCPU unknown, notzero. This consolidation does no routing/readers/Native.'),
    limits=limits,consolidation_sample=dict(wall_seconds=time.monotonic()-started,
        CPU_seconds=usage.ru_utime+usage.ru_stime-cpu0.ru_utime-cpu0.ru_stime,complete_external_unknown=True),
    checks_scope='Exact journal/packet/index hashes and mapped stored-role bindings only; no rescan/revalidation of packet material or production acceptance-reader call.')
summary_raw=(json.dumps(summary,indent=2,sort_keys=True)+'\n').encode();assert len(summary_raw)<=1024**2
for item in inputs:assert p.sha(Path(item['path']))==item['sha256']
for path,raw in ((final_path,final_raw),(summary_path,summary_raw)):
    with path.open('xb') as stream:stream.write(raw)
assert p.sha(final_path)==final_sha
for item in inputs:assert p.sha(Path(item['path']))==item['sha256']
print(json.dumps(dict(journal=str(final_path),journal_sha256=final_sha,summary=str(summary_path),
    summary_sha256=p.sha(summary_path),protocol_functional_roles_recorded=True,actual_GUI_fully_qualified=False)))
