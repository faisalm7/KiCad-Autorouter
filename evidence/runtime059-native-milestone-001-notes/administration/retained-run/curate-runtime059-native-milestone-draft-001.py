"""DRAFT: retain current059 Native regression metadata; never run Native/readers.

Reuse the pinned030 retention,042 own-final and public reporting functions.
The eleven GPL-owned fixtures retain bounded original proof metadata. EEPROM
retains only sanitized generated facts/hashes, never raw CAD/findings/netlists.
The actual passed invalid002 receipt/time pins remain mandatory CLI inputs.
"""
from pathlib import Path
from collections import Counter
import argparse, ast, copy, datetime, hashlib, json, math, os, re, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,sexpr as sx,provenance as pv,floor_route as f
H='50f63338a67cdbdb81e0392fff7dda5dceaf5b4d';M='3cb071002cdcba008801545bf0813e20118f142a98aa6bda84af32d0668604dc'
runtime=ROOT/'.runs/runtime-directory-059/runtime';base=ROOT/'.runs/runtime059-native-qualification-001'
notes=ROOT/'evidence/runtime059-native-milestone-001-notes';target=ROOT/'evidence/runtime059-native-milestone-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target),'Fresh namespace; preserve partial failure'
SELF=Path(__file__).resolve();pins={SELF:p.sha(SELF)};refs={};files=[];material=[];total=0;queue={};destinations={}
source_snapshots={};output_snapshots={};KEYS=('opens','blocking','warnings','exclusions');MAX_JSON=4*1024**2
def bind(path,expected=None):
    path=Path(path);raw=io.read_bytes(path,MAX_JSON);pin=hashlib.sha256(raw).hexdigest()
    if expected is not None:assert pin==expected,str(path)
    if path in pins:assert pins[path]==pin,str(path)
    else:pins[path]=pin
    return raw
def read(path):return json.loads(bind(path),object_pairs_hook=pv._strict_object)
helpers=[
    (ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',{'retain'}),
    (ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',{'own_final'}),
    (ROOT/'scripts/report_current_comparison.py','0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e',{'require','digest','complete_cost','counts','field_fact','finding_types','ignored_check_facts','native_application_policy','own_final','improve_auxiliary'}),
]
for index,(path,pin,names) in enumerate(helpers):
    nodes=[copy.deepcopy(n) for n in ast.parse(bind(path,pin)).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    if index==1:
        for node in nodes:node.name='owned_own_final'
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::shared-functions','exec'),globals())
def cost(path):
    path=Path(path);bind(path);value=complete_cost(path)
    assert value['source']==str(path) and value['time_log_sha256']==pins[path]
    bind(path,value['time_log_sha256']);return value
def add(path,name):
    path=Path(path);name=Path(name)
    assert ROOT in path.parents and path.is_file() and not path.is_symlink()
    assert not name.is_absolute() and not ({'..','.runs'}&set(name.parts))
    if path in queue:return
    assert name not in destinations,(name,path)
    bind(path);queue[path]=name;destinations[name]=path
def metadata(directory,name):
    # Existing058 selection: root text proof metadata and owned Native input PRL.
    for rel in io.inventory(directory,max_bytes=256*1024**2,max_files=8000,max_entries=16000):
        path=directory/rel;parts=Path(rel).parts
        if (len(parts)==1 and path.suffix in ('.json','.log','.net')) or (len(parts)==2 and parts[0].endswith('-input') and path.suffix=='.kicad_prl'):add(path,Path(name)/rel)
def process_ok(process):
    assert process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False
ap=argparse.ArgumentParser(description=__doc__)
for flag in ('invalid-enclosure-sha256','invalid-child-sha256','invalid-time-sha256'):ap.add_argument('--'+flag,required=True)
args=ap.parse_args();assert all(pv._DIGEST.fullmatch(value) for value in vars(args).values())
FIXED={
    runtime/'runtime-distribution.json':M,
    runtime.parent/'preparation.json':'8dcd9208f62498bac54112c4248045d4c870b4b915984febcb78b697390e9717',
    base/'frozen.json':'cdd09180e16e80752ea8bdf140ac8b83d93f21421e3f8d1f24c820738c983d90',
    base/'batch-result.json':'478ba16f51ad12576f97401679b5e1430da7ea12fb2bf3850e3c541cce24e673',
    ROOT/'.runs/full-integration-211/execution.json':'f68242e6ac7fd9fb4e9b5ad9ecbca0fb425dabf8dc7104586654d0db43358d10',
    ROOT/'.runs/full-integration-211/protocol.json':'8da48a7120ee3ff8111c0e42f020a050e34cd19b36c29b31d39159aee33e6992',
    ROOT/'.runs/full-integration-210/execution.json':'c2160fc3761b58c97f729dae79f61cd9ea537c5616c984b4a30461e63b0d57a4',
    ROOT/'.runs/full-integration-210/protocol.json':'b01a15547d06bc3618d780fd33706131167251959a1504497a6f7a70854b7a6d',
    ROOT/'.runs/runtime059-native-batch-001-time.log':'df563e6dbb5f0e6a853aa8ead2da093d26386f625e6c5fc0f19d607b30d1805e',
    ROOT/'.runs/prepare-runtime059-001.py':'9fb8db5eb2ba216ea1c7951c678ebdf1baf0a294237c9f4448215485188d45b1',
    ROOT/'.runs/prepare-runtime059-002.py':'970505598a270f65adb0274e29818e2d89549219ec8f6401dc451c802a42cee4',
    ROOT/'.runs/freeze-runtime059-native-and-return-draft-001.py':'0119d07774ed0ba4962f889fc1b00c390b6487648bb00e039165cca85bff8603',
    ROOT/'.runs/freeze-runtime059-native-and-return-draft-002.py':'a19837e19dcd69ee02a24fe2ca51f4f022ca3d2abf9ccf52d53740eef2128529',
    ROOT/'.runs/curate-runtime058-native-milestone-002.py':'024d04525c58d4c08c79e4b85f10f2d21a3a45339f4c1e9b7181ee33990f8cc9',
}
for path,pin in FIXED.items():bind(path,pin)
prepared=read(runtime.parent/'preparation.json');full=read(ROOT/'.runs/full-integration-211/execution.json');full_plan=read(ROOT/'.runs/full-integration-211/protocol.json')
assert prepared['prepared'] is True and prepared['source_head']==H and prepared['runtime']==str(runtime) and prepared['manifest_sha256']==M
assert prepared['full211_execution_sha256']==pins[ROOT/'.runs/full-integration-211/execution.json'] and prepared['controller_sha256']==pins[ROOT/'.runs/prepare-runtime059-002.py']
assert full['passed'] is True and full['sources_unchanged'] is True;process_ok(full['process'])
assert full_plan['tools']['git_head']==H
for name,pin in full_plan['tools']['implementation_sha256'].items():
    assert p.sha(runtime/name)==pin and p.sha(ROOT/name)==pin and full_plan['source_sha256'][name]==pin
    pins[runtime/name]=pin;pins[ROOT/name]=pin
bind(Path(full['process']['log']),full['log_sha256'])
failed_full=read(ROOT/'.runs/full-integration-210/execution.json');assert failed_full['passed'] is False and failed_full['process']['exit_code']!=0 and failed_full['process']['cleanup_complete'] is True
bind(Path(failed_full['process']['log']),failed_full['log_sha256'])
frozen=read(base/'frozen.json');batch=read(base/'batch-result.json')
owned_cases=['via-high-whole2Cu','via-high-partial2Cu','via-high-whole4Cu','via-high-partial4Cu','ordinary-npth2Cu','improve-pour-only','improve-fractional','improve-floor2Cu','ordinary-alias2Cu','ordinary-whole4Cu','ordinary-hierarchy2Cu']
cases=owned_cases+['improve-eeprom90-return']
assert frozen['source_head']==H and frozen['runtime_manifest_sha256']==M and frozen['runtime']==str(runtime)
assert [row['case'] for row in frozen['protocols']]==cases
assert frozen['controller_sha256']==pins[ROOT/'.runs/freeze-runtime059-native-and-return-draft-002.py']
assert frozen['return_policy']['current_return_reserve_seconds']==40 and frozen['whole_batch_seconds']==900
assert batch['passed'] is True and batch['full_CPU_complete'] is True and batch['completed_cases']==12 and batch['unstarted_cases']==0
assert batch['frozen_sha256']==pins[base/'frozen.json'] and batch['controller_sha256']==frozen['controller_sha256']
assert [row['case'] for row in batch['rows']]==cases and all(row['passed'] is True and row['status']=='passed' for row in batch['rows'])
assert max(batch['wall_seconds'],batch['full_CPU_seconds'])<=900
dependencies=[]
for name,pin in (
    ('evidence/runtime058-native-milestone-001.json','1dd9972cdf5b20392cde77f42ddb177838e8a65c2b4cd22dc8409580ad42fc29'),
    ('evidence/runtime058-ir-delivery-001.json','f2fd277f94a94e05be1748b5619490870bc2ef134bf33fb4d04eed0b19eceed8'),
    ('evidence/runtime058-eeprom-improve-regression-001.json','4d05669921fa9b186552a2d57ff3f8a50aa70dead331de3edf89ef8d8ba44176'),
    ('evidence/development-eeprom-001.json','3cdf0561e184daaac153de58a788c735332bdfd67c340f73756530b6171ca223')):
    path=ROOT/name;bind(path,pin);data=read(path)
    dependencies.append(dict(path=name,sha256=pin,files_index=data.get('files_index'),scope='Historical Native/source-intake evidence only; no current059, GUI, install or comparison authority transferred.'))
    if label_index:=data.get('files_index'):
        index=ROOT/label_index['path'];bind(index,label_index['sha256'])
        # Only owned proof dedup references are reused, never foreign source CAD.
        if name=='evidence/runtime058-native-milestone-001.json':
            for row in read(index).get('files',[]):refs.setdefault(row['sha256'],row['path'])
rows=[];eeprom=None
for entry,batch_row in zip(frozen['protocols'],batch['rows']):
    label=entry['case'];foreign=label=='improve-eeprom90-return';folder=base/label;protocol=Path(entry['protocol'])
    assert protocol==folder/'protocol.json';bind(protocol,entry['protocol_sha256']);plan=read(protocol)
    assert plan['kind']=='runtime059-six-stage-native-and-return-CLI' and plan['case']==label and plan['source_head']==H and plan['runtime_manifest_sha256']==M and plan['runtime']==str(runtime)
    output=Path(plan['output']);assert output==runtime/'.runs'/(label+'-001')
    output_snapshots[output]=io.inventory(output,max_bytes=256*1024**2,max_files=8000,max_entries=16000)
    source=Path(plan['source']);hashes=plan['source_hashes'];assert io.inventory(source.parent)==hashes;source_snapshots[source.parent]=hashes
    execution_path=folder/'execution.json';bind(execution_path,batch_row['execution_sha256']);execution=read(execution_path)
    bind(folder/'batch-process.json',batch_row['process_sha256']);bind(folder/'complete-command-and-time.log',batch_row['complete_log_sha256'])
    child_path=output/'result.json';bind(child_path,execution['child_sha256']);child=read(child_path);workspace=Path(child['workspace'])
    assert workspace.parent==output and re.fullmatch('autorouter-gui-[0-9a-f]{32}',workspace.name)
    assert execution['child_receipt']==str(child_path) and execution['protocol_sha256']==entry['protocol_sha256'] and execution['error'] is None
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True and max(execution['complete_wall_seconds'],execution['complete_full_CPU_seconds'])<=240;process_ok(execution['process'])
    assert child['status']=='completed' and child['workflow_delivered'] is True and child['accepted'] is False and child['actual_GUI'] is False
    assert child['source']==str(source) and child['source_hashes']==hashes and child['tools']==plan['tools'] and child['method']==plan['method']==entry['method']
    assert child['settings']==plan['settings']==read(folder/'settings.json');bind(folder/'settings.json',plan['settings_sha256']);assert child['settings_sha256']==plan['settings_sha256']
    assert [step['stage'] for step in child['processes']]==['preview','route','review','choice','export','verify_export']
    for step in child['processes']:
        assert step['process']['exit_code']==0 and step['process']['cancel_requested'] is False and step['process']['log_truncated'] is False
        bind(output/(step['stage']+'.log'),step['log_sha256'])
        if not foreign:add(output/(step['stage']+'.log'),Path('cases')/label/'workflow'/(step['stage']+'.log'))
    counts_value=execution['Native_counts'];assert execution['protected_count']==plan['expected_protected_count']
    if plan['expected_counts'] is None:assert plan['warning_policy']=='retain_all_native_findings' and counts_value[:2]==[0,0] and counts_value[3]==plan['expected_exclusions']
    else:assert counts_value==plan['expected_counts']
    route_path=workspace/'route/result.json';export_path=workspace/'export/export.json';route=read(route_path);exported=read(export_path)
    assert route['accepted'] is True and route['status']=='routing_accepted' and exported['export_accepted'] is True
    assert route['candidate_sha256']==exported['candidate_sha256']==child['candidate_sha256'] and route['tools']==exported['tools']==plan['tools']
    assert exported['inputs']['source']==str(source) and exported['inputs']['receipt']==str(route_path) and exported['inputs']['receipt_sha256']==pins[route_path] and exported['original_geometry_and_routing_unchanged'] is True
    assert route['budget_seconds']==route['cpu_budget_seconds']==exported['budget_seconds']==exported['cpu_budget_seconds']==plan['settings']['seconds']
    for name,pin in plan['tools']['implementation_sha256'].items():assert p.sha(runtime/name)==pin
    if entry['method']=='route':
        score='via_high' if label.startswith('via-high-') else None
        assert route['routing_preferences']['effective']==plan['settings'] and route['scoring_variant']==plan['settings']['scoring_preference']==score
        if score is not None:assert route['engine_budget']['scoring']==dict(variant='via_high',via_costs=100,plane_via_costs=10,argv=['--router.scoring.via_costs=100','--router.scoring.plane_via_costs=10'])
    else:assert route['pruning_preferences']['effective']==plan['settings'] and route['finalization_reserve_seconds']==route['finalization_cpu_reserve_seconds']==40
    original=sx.read(source);protected=p.protected_for_record(route,original);assert len(protected)==execution['protected_count']
    packets=[('parent',route,route_path.parent,route_path),('export',exported,export_path.parent/'validation',export_path)]
    if entry['method']=='improve':
        inc=route_path.parent/'incumbent/result.json';assert route['incumbent']['receipt']==str(inc)
        packets.append(('incumbent',read(inc),inc.parent,inc));assert len(route['trials'])<=32
        for i,trial in enumerate(route['trials']):
            directory=route_path.parent/'trials'/('trial-%04d'%i);path=directory/'result.json';data=read(path)
            assert trial==dict(id=directory.name,receipt=str(path),status=data['status'],accepted=data['accepted'])
            packets.append((directory.name,data,directory,path))
    proofs={}
    for part,data,directory,receipt_path in packets:
        candidate=directory/'candidate'/source.name;assert p.sha(candidate)==data['candidate_sha256']
        assert p.immutable(sx.read(candidate))==p.immutable(original) and all(item in p.routes(sx.read(candidate)) for item in protected)
        if foreign:
            trial_parent=route if part.startswith('trial-') else None
            proof=own_final(receipt_path,export=part=='export',plan=plan,allowed=[output],accepted=data['accepted'] if part!='export' else data['export_accepted'],public_sanitize=True,trial_parent=trial_parent)
            # No free-form Native policy refusal strings are published either.
            policy=proof['Native_application_policy'];policy['rejection_reasons']=field_fact(policy['rejection_reasons'],receipt_path,'Native_application_policy.rejection_reasons',True)
            proof['auxiliary']=improve_auxiliary(directory,data,plan)
        else:
            if not part.startswith('trial-'):assert data['source_hashes']==hashes and data['tools']==plan['tools'] and data['schematic_parity']=='checked by final native DRC'
            proof=owned_own_final(data,directory,directory,hashes,candidate);metadata(directory,Path('cases')/label/part)
        proofs[part]=dict(accepted=data['accepted'] if part!='export' else data['export_accepted'],candidate_sha256=data['candidate_sha256'],Native_counts=[data['native'][key] for key in KEYS],ignored_check_count=len(data['native']['ignored_checks']),own_final=proof)
    assert counts_value==proofs['parent']['Native_counts']==proofs['export']['Native_counts']
    review=read(workspace/'review/review.json');choice=read(workspace/'choice/choice.json')
    assert review['receipt_sha256']==choice['receipt_sha256']==pins[route_path] and choice['choice']=='accept' and choice['applied'] is False and choice['review_sha256']==pins[workspace/'review/review.json']
    case_cost=cost(folder/'complete-command-and-time.log')
    row=dict(case=label,method=entry['method'],protocol_sha256=entry['protocol_sha256'],execution_sha256=pins[execution_path],child_sha256=pins[child_path],route_sha256=pins[route_path],export_sha256=pins[export_path],source_hashes=hashes,source_unchanged=True,controls_passed=True,workflow_delivered=True,actual_GUI=False,Native_counts=counts_value,protected_count=len(protected),own_finals=proofs,complete_external_cost=case_cost,enclosure_sample_wall_seconds=execution['complete_wall_seconds'],enclosure_sample_full_CPU_seconds=execution['complete_full_CPU_seconds'],scoring_preference=plan['settings']['scoring_preference'],trials=len(route.get('trials',[])),improvements=route.get('improvements'))
    if foreign:
        assert route['budget_seconds']==90 and counts_value==[0,0,36,0] and len(route['trials'])==9 and route['improvements']==8 and len(protected)==0
        route_cli=next(step['process']['wall_seconds'] for step in child['processes'] if step['stage']=='route');start=route['finalization_started_elapsed_seconds']
        row.update(source_rights_scope='Exposed EEPROM source rights/title/per-asset/model closure is unqualified. Only owned generated facts/hashes are published; no source CAD/DSN/SES/raw findings/netlists/log payload is retained.',finalization_started_elapsed_seconds=start,actual_route_CLI_wall_seconds=route_cli,complete_route_return_tail_seconds=route_cli-start,return_reserve_seconds=40,literal50s_expiry_observed=False,interpretation='Finalization began before50s. Actual nine trials/eight improvements and own accepted final delivery establish this safe-best return slice and tail below40s, not literal deadline expiry, no-better/exact-incumbent return, broad robustness or comparative gain.')
        assert start<50 and 0<route_cli-start<40;eeprom=row
    else:
        for path in (protocol,folder/'settings.json',execution_path,folder/'batch-process.json',folder/'complete-command-and-time.log',folder/'enclosure/process.json',folder/'enclosure/command.log'):add(path,Path('cases')/label/'workflow'/path.relative_to(folder))
        add(child_path,Path('cases')/label/'workflow/child-result.json')
        for path in (workspace/'settings.json',workspace/'review/review.json',workspace/'choice/choice.json',export_path):add(path,Path('cases')/label/'workflow/job'/path.relative_to(workspace))
        metadata(workspace/'review/plot-work',Path('cases')/label/'workflow/review-plot-metadata')
    rows.append(row)
assert len(rows)==12 and eeprom is not None
invalid_base=ROOT/'.runs/runtime059-native-controls-001/invalid-execution002';invalid_original=ROOT/'.runs/runtime059-native-controls-001/invalid'
bind(invalid_base/'protocol.json','0c49e9052b792f0e13881ecbc7d4d2fca76da033e0fa22cee19277ea6238a7ac');plan=read(invalid_base/'protocol.json')
assert bind(invalid_original/'protocol.json')==bind(invalid_base/'protocol.json')
bind(invalid_base/'enclosure/result.json',args.invalid_enclosure_sha256);outer=read(invalid_base/'enclosure/result.json');process_ok(outer['process'])
assert outer['passed'] is True and outer['status']=='completed' and outer['process']==read(invalid_base/'enclosure/process.json')
assert outer['protocol_sha256']==pins[invalid_base/'protocol.json'] and plan['source_head']==H and plan['runtime_manifest_sha256']==M and plan['runtime']==str(runtime) and plan['expected_scoring']=='via_high'
invalid_path=Path(outer['child_receipt']);assert invalid_path==Path(plan['output'])/'result.json';bind(invalid_path,args.invalid_child_sha256);invalid=read(invalid_path)
assert outer['child_sha256']==args.invalid_child_sha256 and invalid['control_passed'] is True and invalid['status']=='completed' and invalid['accepted'] is False and invalid['production_admitted'] is False
assert invalid['source_head']==H and invalid['runtime_manifest_sha256']==M and invalid['protocol_sha256']==pins[invalid_base/'protocol.json']
assert invalid['controller_sha256']==plan['controller_sha256']==p.sha(Path(plan['controller'])) and invalid['tools']==read(base/owned_cases[0]/'protocol.json')['tools']
assert invalid['positive_sha256']==rows[0]['route_sha256'] and p.sha(Path(invalid['positive_receipt']))==rows[0]['route_sha256']
assert [row['case'] for row in invalid['cases']]==['short','protected-width','hole-clearance'] and all(row['passed'] is True for row in invalid['cases'])
source_snapshots[Path(invalid['source']).parent]=invalid['source_hashes'];assert io.inventory(Path(invalid['source']).parent)==invalid['source_hashes']
output_snapshots[invalid_path.parent]=io.inventory(invalid_path.parent,max_bytes=256*1024**2,max_files=8000,max_entries=16000)
invalid_proofs={}
for row in invalid['cases']:
    directory=invalid_path.parent/row['case'];assert all(step['cleanup_complete'] is True for step in row['steps'])
    if row['case']=='protected-width':
        assert row['rejection']=='protected route changed' and [row['diagnostic_native'][key] for key in KEYS][:2]==[0,0]
        invalid_proofs[row['case']]=dict(diagnostic_only=True,final_acceptance=False,diagnostic_report_sha256=p.sha(directory/'diagnostic-drc.json'),diagnostic_process_sha256=p.sha(directory/'diagnostic-drc-process.json'),diagnostic_binding_sha256=p.sha(directory/'diagnostic-drc-binding.json'))
    else:
        assert row['native']['blocking']>0;view=dict(row,native_report_sha256=row['report_sha256'])
        invalid_proofs[row['case']]=owned_own_final(view,directory,directory,invalid['source_hashes'],directory/'candidate'/Path(invalid['source']).name)
    metadata(directory,Path('invalid-controls')/row['case'])
failed_outer=read(invalid_original/'enclosure/result.json')
assert failed_outer['passed'] is False and failed_outer['child_sha256'] is None and failed_outer['process']['exit_code']==1 and failed_outer['process']['cleanup_complete'] is True
assert b'FileNotFoundError' in bind(invalid_original/'enclosure/command.log') and failed_outer['protocol_sha256']==pins[invalid_base/'protocol.json']
additional={}
for label,name in (('failed_full210','full-integration-210'),('full211','full-integration-211'),('preparation002','prepare-runtime059-002'),('native_freeze001','runtime059-native-freeze-001'),('failed_invalid001','runtime059-invalid-native-001'),('completed_invalid002','runtime059-invalid-native-002')):
    time_path=ROOT/'.runs'/(name+'-time.log')
    if label=='completed_invalid002':bind(time_path,args.invalid_time_sha256)
    additional[label]=cost(time_path)
    for path in (ROOT/'.runs'/(name+'.log'),time_path):add(path,Path('administration/logs')/path.name)
batch_complete=cost(ROOT/'.runs/runtime059-native-batch-001-time.log');assert batch_complete['wall_seconds']==717.86 and batch_complete['CPU_seconds']==686.13
assert additional['full211']['wall_seconds']==184.33 and additional['full211']['CPU_seconds']==177.16
assert additional['completed_invalid002']['wall_seconds']==7.58 and additional['completed_invalid002']['CPU_seconds']==5.96
complete=dict(wall_seconds=round(sum(row['complete_external_cost']['wall_seconds'] for row in rows),2),CPU_seconds=round(sum(row['complete_external_cost']['CPU_seconds'] for row in rows),2))
for path in (*FIXED,base/'doctor.json',base/'doctor-process.json',base/'tools-defaults.json',base/'tools-defaults-process.json',runtime.parent/'venv-process.json',ROOT/'.runs/runtime059-native-batch-001.log',ROOT/'.runs/runtime059-native-batch-001-time.log',ROOT/'.runs/run-full-integration-210.py',ROOT/'.runs/run-full-integration-211.py',ROOT/'.runs/full-integration-210/command.log',ROOT/'.runs/full-integration-211/command.log',ROOT/'.runs/full-suite-local-root-019.py',ROOT/'.runs/qualify-runtime059-hole-safety-001.py',Path(plan['controller']),ROOT/'.runs/freeze-runtime059-native-invalid-001.py',invalid_original/'protocol.json',invalid_original/'frozen.json',invalid_original/'enclosure/result.json',invalid_original/'enclosure/process.json',invalid_original/'enclosure/command.log',invalid_base/'protocol.json',invalid_base/'enclosure/result.json',invalid_base/'enclosure/process.json',invalid_base/'enclosure/command.log',invalid_path,ROOT/'LICENSE',SELF):
    relative=path.relative_to(ROOT);safe=Path(*('retained-run' if part=='.runs' else part for part in relative.parts));add(path,Path('administration')/safe)
for path,pin,names in helpers:add(path,Path('shared-helpers')/path.name)
# Preflight every new public byte and capture expected facts before copying.
planned_refs=dict(refs);planned_files=[];planned_material=[];planned_bytes=0
for path,name in queue.items():
    raw=bind(path);pin=pins[path];destination=planned_refs.get(pin)
    if destination is None:
        assert b'\0' not in raw;raw.decode('utf8');destination=str((notes/name).relative_to(ROOT));planned_refs[pin]=destination;planned_bytes+=len(raw)
        planned_files.append(dict(path=destination,bytes=len(raw),sha256=pin))
    elif pin in refs:bind(ROOT/destination,pin)
    planned_material.append(dict(original=str(path.relative_to(ROOT)),retained=destination,bytes=len(raw),sha256=pin))
index=notes/'files.json';index_data=dict(schema=1,files=planned_files,material=planned_material)
index_raw=(json.dumps(index_data,indent=2)+'\n').encode();index_pin=hashlib.sha256(index_raw).hexdigest()
record=dict(schema=1,kind='runtime059-twelve-completed-native-workflows-and-return-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=H,runtime_manifest_sha256=M,Native_cohort_passed=True,accepted=False,production_admitted=False,release_qualified=False,actual_GUI=False,human_review=False,project_complete=False,
    cases=rows,owned_cases=11,sanitized_exposed_EEPROM_cases=1,complete_deliveries_external_cost=complete,complete_batch_external_cost=batch_complete,additional_complete_external=additional,return_policy=frozen['return_policy'],dependencies=dependencies,
    invalid_controls=dict(passed=True,protocol_sha256=pins[invalid_base/'protocol.json'],enclosure_sha256=args.invalid_enclosure_sha256,child_sha256=args.invalid_child_sha256,own_final_proofs=invalid_proofs,cases=[dict(case=row['case'],passed=True,Native_counts=[row['native'][key] for key in KEYS] if row.get('native') else None) for row in invalid['cases']],failed001=dict(passed=False,Native_started=False,reason='Relative protocol argument failed to resolve before payload creation; original receipt/traceback retained.',receipt_sha256=pins[invalid_original/'enclosure/result.json'])),
    result='All twelve frozen current059 six-stage workflows passed under unchanged global budgets. Eleven GPL-owned ordinary/high/Improve regressions and one exposed EEPROM Improve90 retain their own final Native/source/original evidence. EEPROM nine trials/eight improvements returned a verified best through own export, with48.446s finalization and25.705s return tail below40s; this is not literal50s expiry or exact-incumbent/no-better qualification. No family breadth, completion/quality superiority, untouched evaluation or fair current059 comparison follows.',
    proof_scope='Curator checks stored original/candidate hashes, own Native output/process/fullSCH bindings and original semantic/protected invariants; it executes no Native or central readers and does not renew live acceptance authority. Default/class/field/PRL proof metadata for owned fixtures remains in selected records. EEPROM publishes only shared reporter sanitized own-final/Default/class/field/PRL facts and hashes for parent/export/incumbent/all nine attempts, including the negative first trial; raw reports/netlists/source/candidate proof stay onMac.',
    accounting='Per-case complete exits are included inside717.86wall/686.13CPU batch; never add those totals or nested Native/workflow/stage samples. Full211184.33/177.16, failed full210, preparation002, query/doctor freeze and failed/completed invalid outer exits are separately recorded additional events. Invalid001 failed before Native;002 is the sole actual three-control run. Preparation001/freezer001 source versions are preserved without inventing separate measured attempts. Source authoring/AI review, GUI/install/comparison and future curation cost remain separate or unknown, notzero.',
    remaining=dict(GUI='UNQUALIFIED_CURRENT059',fresh_install='UNQUALIFIED_CURRENT059',fair_comparison='UNQUALIFIED_CURRENT059',literal_deadline_expiry='NOT_OBSERVED',human_electrical_release='UNQUALIFIED'),
    retention='Small owned metadata/log/net/PRL text for the eleven GPL fixtures and owned administration only. No CAD/DSN/SES/plots/tools/cache/binaries are copied. In particular no EEPROM raw receipt, Native findings, netlist or private source payload is queued. This packet and old index dedup do not back up all raw059/EEPROM Native/source/proof bytes, which remain onMac/outside010; no full restoration, cleanOS/standalone/Windows or formal release claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=index_pin))
record_raw=(json.dumps(record,indent=2)+'\n').encode();record_pin=hashlib.sha256(record_raw).hexdigest()
assert len(planned_files)+2<2000 and max(len(index_raw),len(record_raw))<=4*1024**2
assert planned_bytes+len(index_raw)+len(record_raw)<16*1024**2,'Refuse before publication; never raise caps'
def fresh():
    for path,pin in pins.items():assert hashlib.sha256(io.read_bytes(path,MAX_JSON)).hexdigest()==pin,str(path)
    for path,hashes in source_snapshots.items():assert io.inventory(path)==hashes,str(path)
    for path,hashes in output_snapshots.items():assert io.inventory(path,max_bytes=256*1024**2,max_files=8000,max_entries=16000)==hashes,str(path)
fresh()
for path,name in queue.items():retain(path,name)
assert files==planned_files and material==planned_material and total==planned_bytes
for row in files:pins[ROOT/row['path']]=row['sha256']
fresh();p.save_json(index,index_data);bind(index,index_pin);fresh()
fresh();p.save_json(target,record);bind(target,record_pin);fresh()
print(json.dumps(dict(path=str(target),sha256=record_pin,files=len(files),bytes=total,material=len(material),Native_executed=False,actual_GUI=False)))
