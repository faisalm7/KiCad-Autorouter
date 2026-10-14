"""One readback of retained native failure using the existing shared validators."""
import time, resource
START=time.monotonic(); usage=resource.getrusage(resource.RUSAGE_SELF); CPU0=usage.ru_utime+usage.ru_stime
from pathlib import Path
import hashlib, json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def forbidden(*args,**kwargs):raise AssertionError('readback must not execute Native/JVM/Git/network')
subprocess.run=forbidden;subprocess.Popen=forbidden
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc, handoff as h
from experiments.native_paired_v1.readback import final_candidate_readback

OUT=Path(__file__).resolve().parent;BASE=ROOT/'.runs/cellscan-b1-budget240-001'
PROSPECTIVE=ROOT/'.runs/cellscan-b1-budget240-001-protocol.json'
OLD=ROOT/'.runs/cellscan-native-paired-complete-sch-001'
PRIOR_QUAL=ROOT/'.runs/cellscan-native-paired-complete-sch-001-qualification-001'
PROBE=ROOT/'.runs/cellscan-readback-schema-review-001/result.json'
OWNER={};h.capture_destination(OWNER,OUT)
read=f.read_json;spec=read(PROSPECTIVE);outer=read(BASE/'execution.json');trial=read(BASE/'trial/result.json')
old_spec=read(ROOT/'.runs/cellscan-native-paired-complete-sch-001-protocol.json')
old_outer=read(OLD/'execution.json');old_summary=read(OLD/'run/paired-summary.json')
qualification=read(PRIOR_QUAL/'result.json');qual_execution=read(PRIOR_QUAL/'execution.json');probe=read(PROBE)
original_receipt=ROOT/'.runs/cellscan-original-native-001/result.json';original=read(original_receipt)
board=Path(spec['source']);inputs={**spec['artifacts'],str(PROSPECTIVE):p.sha(PROSPECTIVE),
    str(BASE/'execution.json'):p.sha(BASE/'execution.json'),str(PRIOR_QUAL/'result.json'):p.sha(PRIOR_QUAL/'result.json'),
    str(PRIOR_QUAL/'execution.json'):p.sha(PRIOR_QUAL/'execution.json'),str(PROBE):p.sha(PROBE),
    str(Path(__file__).resolve()):p.sha(Path(__file__))}
roots=(BASE,OLD,PRIOR_QUAL)
witnesses={str(root):pc.inventory(root,max_bytes=96*1024**2,max_files=6000,max_entries=12000,with_directories=True)for root in roots}
qual_wall=qual_execution['wall_seconds']+1;qual_cpu=qual_execution['full_cpu_seconds']+1
probe_wall=probe['pure_schema_probe']['wall_seconds']+2;probe_cpu=probe['pure_schema_probe']['full_cpu_seconds']+2
def measured():
    usage=resource.getrusage(resource.RUSAGE_SELF)
    return time.monotonic()-START,usage.ru_utime+usage.ru_stime-CPU0
def remaining():
    wall,cpu=measured()
    return min(15-qual_wall-probe_wall-wall-2,15-qual_cpu-probe_cpu-cpu-2)
report=dict(schema=1,kind='CellScan longer-budget B1 shared native failure readback',status='incomplete',
    accepted=False,passed=False,comparison_eligible=False,new_native_execution=False,new_engine_execution=False,
    physical_electrical_validation=False,prospective_protocol_sha256=p.sha(PROSPECTIVE),
    controller_sha256=p.sha(Path(__file__)),shared_reader_sha256=p.sha(ROOT/'experiments/native_paired_v1/readback.py'),
    inputs_sha256=inputs,claims_limit=spec['claims_limit'])
def stable():
    h.owned_destination(OWNER)
    for path,digest in inputs.items():
        if p.sha(Path(path))!=digest:raise p.Rejected('retained input pin changed')
    for root in roots:
        if pc.inventory(root,max_bytes=96*1024**2,max_files=6000,max_entries=12000,with_directories=True)!=witnesses[str(root)]:
            raise p.Rejected('retained completed evidence changed')
    if p.tree_hash(board.parent)!=spec['freeze']['source_hashes']:raise p.Rejected('source changed')
    for path,digest in {**spec['freeze']['files_sha256'],**spec['freeze']['tools']['files']}.items():
        target=Path(path) if Path(path).is_absolute() else ROOT/path
        if p.sha(target)!=digest:raise p.Rejected('frozen source or tool bytes changed')
    if report['passed'] and remaining()<=0:raise p.Rejected('cumulative original15 audit exceeded')
def account():
    wall,cpu=measured();report['audit_cost']=dict(active_wall_seconds=wall,active_full_cpu_seconds=cpu,
        bootstrap_allowance_seconds=1,emission_allowance_seconds=1,
        charged_wall_seconds=wall+2,charged_full_cpu_seconds=cpu+2,
        prior_qualification_final_wall_seconds=qual_execution['wall_seconds'],
        prior_qualification_final_full_cpu_seconds=qual_execution['full_cpu_seconds'],
        prior_qualification_conservative_emission_allowance_seconds=1,
        prior_schema_probe_charged_wall_seconds=probe_wall,prior_schema_probe_charged_full_cpu_seconds=probe_cpu,
        cumulative_original15_wall_seconds=qual_wall+probe_wall+wall+2,
        cumulative_original15_full_cpu_seconds=qual_cpu+probe_cpu+cpu+2,
        within_original15_caps=remaining()>0,
        scope='No new audit charge added to route cost: all measured readbacks plus conservative bootstrap/emission allowances close inside the original charged15. Prior qualification startup is already separately charged by its original row.')
    if remaining()<=0:report.update(status='audit_budget_exceeded',passed=False,accepted=False)
try:
    stable()
    assert qualification['status']=='completed' and qualification['comparison_eligible'] is False
    assert qual_execution['result_sha256']==p.sha(PRIOR_QUAL/'result.json')
    assert qualification['prospective_protocol_sha256']==p.sha(ROOT/'.runs/cellscan-native-paired-complete-sch-001-protocol.json')
    assert qualification['controller_sha256']==report['shared_reader_sha256']
    prior=next(row for row in qualification['results']if row['id']=='B1')
    raw=next(row for row in old_summary['results']if row['id']=='B1')
    assert prior['accepted'] is False and prior['status']=='drc_rejected'
    assert prior['result_sha256']==p.sha(OLD/'run/B1/result.json')
    assert old_outer['prospective_protocol_sha256']==qualification['prospective_protocol_sha256']
    expected_old=dict(wall_seconds=raw['charged_wall_seconds']+max(0,old_outer['wall_seconds']-old_summary['batch_wall_seconds'])+15+1+25,
        full_cpu_seconds=raw['charged_cpu_seconds']+max(0,old_outer['full_cpu_seconds']-old_summary['batch_cpu_seconds'])+15+1+25)
    assert prior['charged_wall_seconds']==expected_old['wall_seconds'] and prior['charged_full_cpu_seconds']==expected_old['full_cpu_seconds']
    assert old_spec['shared_original_qualification_cost']['wall_seconds']==old_spec['shared_original_qualification_cost']['full_cpu_seconds']==spec['source_charge_seconds']==25
    assert old_spec['final_readback_allowance_wall_full_cpu_seconds']==spec['cumulative_audit_charge_seconds']==15
    assert spec['new_bootstrap_charge_seconds']==1 and spec['prior_budget_seconds']==120 and spec['outer_wall_full_cpu_cap_seconds']==240
    committed={key:value+1 for key,value in expected_old.items()}
    assert spec['already_committed_charge']==outer['already_committed_charge']==committed
    assert spec['remaining_wall_seconds']==240-committed['wall_seconds'] and spec['remaining_full_cpu_seconds']==240-committed['full_cpu_seconds']
    assert spec['assigned_inner_seconds']==min(spec['remaining_wall_seconds'],spec['remaining_full_cpu_seconds'])-2
    assert outer['protocol_sha256']==p.sha(PROSPECTIVE) and outer['wrapper_sha256']==p.sha(ROOT/'.runs/run-cellscan-b1-budget240-001.py')
    process=outer['process'];assert process['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/run-cellscan-b1-budget240-001.py'),'--inner']
    assert process['cwd']==str(BASE) and process['status']=='nonzero_exit' and process['exit_code']==2 and process['cleanup_complete'] is True
    assert Path(process['log'])==BASE/'command.log' and Path(process['log']).stat().st_size==process['log_bytes'] and process['log_truncated'] is False
    assert trial['source']==str(board) and trial['source_hashes']==spec['freeze']['source_hashes'] and trial['tools']==spec['freeze']['tools']
    assert trial['adapter']==spec['adapter']=='both' and trial['engine_profile']==spec['engine_profile']=='standard'
    assert trial['budget_seconds']==trial['cpu_budget_seconds']==spec['assigned_inner_seconds']
    assert trial['status']=='drc_rejected' and trial['accepted'] is False
    p.check_engine_profile_record(trial,BASE/'trial')
    with p.validation_readback_session():
        final=final_candidate_readback(BASE/'trial',trial,board,p.preflight(board),spec['freeze']['source_hashes'])
    warnings=lambda native:f.canonical([finding for finding in native['findings']if finding['severity']=='warning'])
    unchanged=warnings(trial['native'])==warnings(original['parity_native']);assert unchanged
    errors=[finding for finding in trial['native']['findings']if finding['severity']=='error']
    assert final['native_counts']==dict(opens=0,blocking=1,warnings=209,exclusions=0)
    assert len(errors)==1 and errors[0]['type']=='copper_edge_clearance'
    assert '0.3000 mm; actual 0.2827 mm' in errors[0]['description']
    assert trial['wall_seconds']<=outer['whole_new_wall_seconds'] and trial['total_cpu_seconds']<=outer['whole_new_full_cpu_seconds']
    combined=dict(wall_seconds=committed['wall_seconds']+outer['whole_new_wall_seconds'],
        full_cpu_seconds=committed['full_cpu_seconds']+outer['whole_new_full_cpu_seconds'])
    assert combined['wall_seconds']==outer['combined_charged_wall_seconds'] and combined['full_cpu_seconds']==outer['combined_charged_full_cpu_seconds']
    assert max(combined.values())<=240 and outer['within_cumulative240_caps'] is True
    report.update(status='readback_closed_native_failure',passed=True,final_candidate=final,
        unchanged_all209_original_warning_signatures=unchanged,error_findings=errors,
        process_log_sha256=p.sha(BASE/'command.log'),process_status='nonzero_exit',process_exit_code=2,cleanup_complete=True,
        prior120_failed_charge=expected_old,new_bootstrap_charge_seconds=1,new_outer_wall_seconds=outer['whole_new_wall_seconds'],
        new_outer_full_cpu_seconds=outer['whole_new_full_cpu_seconds'],combined_charged_wall_full_cpu_seconds=combined,
        within_cumulative240_caps=True,original120_result_unchanged=True,
        wrapper_expectation='Inner correctly emits2 for rejected candidate; outer success-status conjunction returns2 despite allowing exit2. Controller/protocol remain exact; completed Native failure is not process success or routing acceptance.',
        longer_budget_finding='Longer unchanged standard search closes the sole signal open and removes12 generated via_dangling warnings, but adds one native copper-edge violation. Candidate remains rejected.',
        skipped_comparators='Matching240 B2 Low/High/C not executed by this probe; no comparative superiority claim.')
except BaseException as exc:
    report.update(status='readback_failed',passed=False,reason=type(exc).__name__+': '+str(exc))
f.publish(OUT,report,stable,account,remaining,owned=lambda:h.owned_destination(OWNER))
stable();account()
saved=read(OUT/'result.json')
assert saved['status']==report['status'] and saved['accepted'] is False
print(json.dumps({key:report.get(key)for key in ('status','passed','accepted','comparison_eligible','audit_cost','combined_charged_wall_full_cpu_seconds')}))
raise SystemExit(0 if report['passed'] else 2)
