"""Stock final native/original checks with existing shared readers, no new native."""
import time,resource
START=time.monotonic();u=resource.getrusage(resource.RUSAGE_SELF);CPU0=u.ru_utime+u.ru_stime
from pathlib import Path
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def forbidden(*a,**kw):raise AssertionError('readback forbids processes')
subprocess.run=forbidden;subprocess.Popen=forbidden
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from experiments.native_paired_v1.readback import final_candidate_readback
base=ROOT/'.runs/cellscan-b0-stock-budget360-001';out=ROOT/'.runs/cellscan-b0-stock-budget360-readback-001';out.mkdir()
specpath=base.with_name(base.name+'-protocol.json');s=f.read_json(specpath);e=f.read_json(base/'execution.json');d=f.read_json(base/'trial/result.json');board=Path(s['source'])
r=dict(schema=1,status='incomplete',passed=False,accepted=False,comparison_eligible=False,new_native_execution=False,controller_sha256=p.sha(Path(__file__)))
try:
    before=pc.inventory(base,max_bytes=64*1024**2,max_files=6000,max_entries=12000,with_directories=True)
    for name,pin in s['artifacts'].items():assert p.sha(Path(name))==pin
    for name,pin in {**s['freeze']['files_sha256'],**s['freeze']['tools']['files']}.items():assert p.sha(Path(name) if Path(name).is_absolute() else ROOT/name)==pin
    assert e['protocol_sha256']==p.sha(specpath) and e['wrapper_sha256']==p.sha(ROOT/'.runs/run-cellscan-b0-stock-budget360-001.py')
    prior=next(x for x in f.read_json(ROOT/'.runs/cellscan-native-paired-complete-sch-001-qualification-001/result.json')['results']if x['id']=='B0')
    committed=dict(wall_seconds=prior['charged_wall_seconds']+16,full_cpu_seconds=prior['charged_full_cpu_seconds']+16)
    assert committed==s['already_committed_charge']==e['already_committed_charge']
    assert s['new_final_readback_charge_seconds']==15 and s['new_bootstrap_charge_seconds']==1
    combined=dict(wall_seconds=committed['wall_seconds']+e['whole_new_wall_seconds'],full_cpu_seconds=committed['full_cpu_seconds']+e['whole_new_full_cpu_seconds'])
    assert combined['wall_seconds']==e['combined_charged_wall_seconds'] and combined['full_cpu_seconds']==e['combined_charged_full_cpu_seconds'] and max(combined.values())<=360
    process=e['process'];assert (process['status'],process['exit_code']) in (('success',0),('nonzero_exit',2)) and process['cleanup_complete'] and not process['log_truncated']
    assert process['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/run-cellscan-b0-stock-budget360-001.py'),'--inner'] and process['cwd']==str(base)
    assert d['adapter']=='none' and d['engine_profile']=='standard' and d['tools']==s['freeze']['tools'] and d['source_hashes']==s['freeze']['source_hashes']
    assert d['budget_seconds']==d['cpu_budget_seconds']==s['assigned_inner_seconds']
    assert d['wall_seconds']<=e['whole_new_wall_seconds'] and d['total_cpu_seconds']<=e['whole_new_full_cpu_seconds']
    p.check_engine_profile_record(d,base/'trial')
    with p.validation_readback_session():
        checked=final_candidate_readback(base/'trial',d,board,p.preflight(board),s['freeze']['source_hashes'])
        if d['accepted']:p.check_result(base/'trial/result.json')
    original=f.read_json(ROOT/'.runs/cellscan-original-native-001/result.json')['parity_native']
    warnings=lambda x:f.canonical([v for v in x['findings'] if v['severity']=='warning'])
    same=warnings(original)==warnings(d['native'])
    assert p.tree_hash(board.parent)==s['freeze']['source_hashes'] and pc.inventory(base,max_bytes=64*1024**2,max_files=6000,max_entries=12000,with_directories=True)==before
    r.update(status='readback_closed',passed=True,method_qualified=d['accepted'] is True and same,final_candidate=checked,metrics=d.get('metrics'),all209_original_warning_signatures_exact=same,
        combined_charged_wall_full_cpu_seconds=combined,inputs_sha256={str(specpath):p.sha(specpath),str(base/'execution.json'):p.sha(base/'execution.json'),str(base/'trial/result.json'):p.sha(base/'trial/result.json')})
except BaseException as exc:r.update(status='readback_failed',reason=type(exc).__name__+': '+str(exc))
u=resource.getrusage(resource.RUSAGE_SELF);wall=time.monotonic()-START;cpu=u.ru_utime+u.ru_stime-CPU0
r['audit_cost']=dict(active_wall_seconds=wall,active_full_cpu_seconds=cpu,bootstrap_emission_allowance_seconds=2,separate_skeptical_review_allowance_seconds=3,charged_wall_seconds=wall+5,charged_full_cpu_seconds=cpu+5,cap_seconds=15,within_caps=max(wall,cpu)+5<=15)
if not r['audit_cost']['within_caps']:r.update(status='audit_budget_exceeded',passed=False,method_qualified=False)
p.save_json(out/'result.json',r);print(json.dumps(r));raise SystemExit(0 if r['passed'] else 2)
