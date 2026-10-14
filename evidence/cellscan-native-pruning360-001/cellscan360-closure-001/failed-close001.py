"""Final comparison from completed shared proofs; no processes or native repeat."""
import time
START=time.monotonic();CPU0=time.process_time()
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import floor_route as f,pipeline as p
out=Path(__file__).parent;paths=f.read_json(out/'inputs.json');proof={m:f.read_json(ROOT/n) for m,n in paths.items()}
costs={'B0':proof['B0']['audit_cost'],'B1':proof['B1']['audit_cost'],'B2':f.read_json(ROOT/'.runs/cellscan-b2-balanced-edge-budget360-001-readback-002/printed-final-cost.json'),'C':f.read_json(ROOT/'.runs/cellscan-c-default-pruning-edge-budget360-001-readback-001/printed-final-cost.json')}
rows=[];pins={str(ROOT/n):p.sha(ROOT/n) for n in paths.values()}
method_dirs={'B0':('cellscan-b0-stock-budget360-001','trial'),'B1':('cellscan-b1-edge-budget360-001','trial'),'B2':('cellscan-b2-balanced-edge-budget360-001','portfolio/01-via_default'),'C':('cellscan-c-default-pruning-edge-budget360-001','trial')}
for method,(dirname,inner) in method_dirs.items():
    base=ROOT/'.runs'/dirname;receipt=base/inner/'result.json';d=f.read_json(receipt);e=f.read_json(base/'execution.json');check=proof[method]
    assert check['status'] in ('completed','readback_closed') and check['passed']
    candidate=Path(d['candidate']);assert p.sha(candidate)==d['candidate_sha256'] and p.sha(receipt.parent/'final-drc.json')==d['native_report_sha256']
    if method in ('B2','C'):
        assert check['method_qualified'] and costs[method]['charged_wall_seconds']+.75<=15 and costs[method]['charged_full_cpu_seconds']+.75<=15
    elif method=='B0':assert not d['accepted'] and not check['method_qualified']
    else:assert check['accepted'] and check['all209_original_warning_signatures_exact']
    assert e['within_cumulative360_caps'] and max(e['combined_charged_wall_seconds'],e['combined_charged_full_cpu_seconds'])<=360
    pins[str(receipt)]=p.sha(receipt);pins[str(base/'execution.json')]=p.sha(base/'execution.json')
    rows.append(dict(method=method,accepted=d['accepted'],status=d['status'],metrics=d['metrics'],native_counts={k:d['native'][k] for k in ('opens','blocking','warnings','exclusions')},candidate_sha256=d['candidate_sha256'],native_report_sha256=d['native_report_sha256'],charged_wall_seconds=e['combined_charged_wall_seconds'],charged_full_cpu_seconds=e['combined_charged_full_cpu_seconds']))
b1,b2,c=rows[1:];assert b1['metrics']['vias']==b2['metrics']['vias']==c['metrics']['vias']==111
assert abs(b1['metrics']['track_length_mm']-b2['metrics']['track_length_mm'])<1e-8
assert proof['B2']['all_three_final_native_proofs'] and proof['B2']['all_variants_attempted']
assert all(x['all209_original_warning_signatures_exact'] for x in proof['C']['observations'])
assert proof['C']['improvements']==12 and len(proof['C']['trials'])==13
result=dict(schema=1,status='comparison_closed',accepted=False,comparison_eligible=True,runtime_head='965796670d2835e185938d52ef694333e5752356',methods=rows,inputs_sha256=pins,
    C_length_reduction_from_B1_B2_mm=b2['metrics']['track_length_mm']-c['metrics']['track_length_mm'],C_via_change=0,
    B2_rejected_profiles=['via_low','via_high'],C_rejected_trials=['trial-0000'],
    audit_closure_charge_seconds_each_method=.75,
    claims_limit='One exposed larger development circuit. All failed120/240 and current attempts charged under cumulative360wall/fullCPU. Correction granted equally toB1/B2/C. No speedup,120rescue,independentpedigree,broadcompletion,untouched,human,electrical/physical,GUI or formalrelease claim.')
wall=time.monotonic()-START;cpu=time.process_time()-CPU0;assert max(wall,cpu)+.25<=.75
result['closure_cost']=dict(active_wall_seconds=wall,active_full_cpu_seconds=cpu,bootstrap_emission_allowance_seconds=.25,charged_seconds_each_method=.75)
p.save_json(out/'result.json',result);print(json.dumps(dict(status=result['status'],comparison_eligible=True,reduction_mm=result['C_length_reduction_from_B1_B2_mm'],wall_seconds=wall,cpu_seconds=cpu)))
