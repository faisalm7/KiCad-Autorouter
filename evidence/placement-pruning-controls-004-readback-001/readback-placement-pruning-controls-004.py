"""Inspect completed native evidence; never mutate or repeat its execution."""
from pathlib import Path
import json,sys,time
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,placement_strategy as ps,sexpr as sx
from experiments.placement_pruning_controls_v1 import driver as control
out=root/'.runs/placement-pruning-controls-004-readback-001';out.mkdir();run=root/'.runs/placement-pruning-controls-004/run'
start=time.monotonic();cpu=time.process_time()+f.child_cpu();before=pc.inventory(run,max_bytes=64*1024**2,max_files=4000,max_entries=8000)
record=f.read_json(run/'result.json');assert record['status']=='failed' and record['controls_passed'] is False
observations=[];checked=[]
for arm in record['arms']:
    receipt=Path(arm['receipt']);checked.append(p.check_result(receipt));assert p.sha(receipt)==arm['result_sha256']
for row in record['cases']:
    case=row['case'];basis=root/'.runs/placement-pruning-controls-002/run/tuned' if case=='redundant' else run/'necessary_tuned'
    receipt=f.read_json(basis/'result.json');source=Path(receipt['source']);original=p.preflight(source);hashes=pc.inventory(source.parent)
    parent_recipe,expected=control.bridge_parent(sx.read(Path(receipt['candidate'])),ps.s.zone_net_ids(original));assert expected==row['parent_recipe']
    parent,pnative,pmetrics=ps.check_candidate_stage(Path(row['parent']['candidate']).parent.parent,row['parent'],original,hashes,basis,parent_recipe)
    removed=ps.deletion(parent,row['proposal'],ps.s.zone_net_ids(original))
    candidate,native,metrics=ps.check_candidate_stage(Path(row['deletion']['candidate']).parent.parent,row['deletion'],original,hashes,basis,removed)
    passed,targets=control.control_observation(case,pnative,native,pmetrics,metrics);assert passed
    assert p.native_accepted(pnative) and ps.warnings(pnative)<=ps.warnings(receipt['native'])
    observations.append({'case':case,'passed_current_predicate':passed,'original_controller_passed':row['passed'],'parent_native':pnative,'native':native,'targeted_findings':targets,'parent_metrics':pmetrics,'metrics':metrics,'candidate_sha256':p.sha(candidate)})
assert pc.inventory(run,max_bytes=64*1024**2,max_files=4000,max_entries=8000)==before
result={'schema':1,'status':'readback_passed','native_reexecuted':False,'original_controller_status':'failed','original_controller_unchanged':True,
    'original_error':record['error'],'explanation':'Actual negative has expected unexcluded zone/J6 error. Native v1 omits the optional excluded=false field; original harness incorrectly required it. Corrected default-false predicate qualifies stored observation without rewriting old result.',
    'original_run_inventory':before,'checked_arm_receipts':checked,'observations':observations,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,
    'readback_script_sha256':p.sha(Path(__file__)),'predicate_source_sha256':p.sha(root/'experiments/placement_pruning_controls_v1/driver.py'),
    'scope':'Engineered native search/C/positive/necessary-deletion controls only; no independent-family or routing-quality claim.'}
p.save_json(out/'result.json',result);print(json.dumps({k:result[k] for k in ('status','native_reexecuted','original_controller_status','wall_seconds','full_cpu_seconds')}))
