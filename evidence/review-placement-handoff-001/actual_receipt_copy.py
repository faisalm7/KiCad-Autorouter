"""Exercise draft only against actual saved schema3 evidence, without native or GUI."""
from pathlib import Path
import importlib.util,json,sys,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as pc
module=HERE/'snapshot-002/handoff.py';spec=importlib.util.spec_from_file_location('autorouter.actual_handoff_review',module);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
receipt=ROOT/'.runs/placement-production-native-001/result.json';raw=json.loads(receipt.read_text());source=Path(raw['source']);candidate=Path(raw['candidate'])
before=pc.evidence_inventory(receipt.parent);source_before=pc.inventory(source.parent);candidate_before=pc.inventory(candidate.parent);receipt_sha=p.sha(receipt)
output=HERE/'actual-schema3-copy-001';started=time.monotonic();record=h.review_copy(receipt,output);elapsed=time.monotonic()-started
canonical=json.loads((output/'review.json').read_text());assert canonical==record and record['status']=='ready_for_manual_review'
assert record['native_validation_performed'] is False and record['input_policy']=='placement-clearance-v1' and record['source_receipt_schema']==3
assert pc.inventory(output/'project')==candidate_before==record['initial_project_hashes']
assert p.sha(output/'project'/candidate.name)==p.sha(candidate)==record['candidate_sha256']==record['verified_candidate_sha256']==raw['candidate_sha256']
assert pc.evidence_inventory(receipt.parent)==before and pc.inventory(source.parent)==source_before and p.sha(receipt)==receipt_sha
result={'schema':1,'passed':True,'module_sha256':p.sha(module),'actual_original_receipt':str(receipt),'receipt_sha256':receipt_sha,'candidate_sha256':raw['candidate_sha256'],'copy_project_files':len(candidate_before),'all_project_bytes_match':True,'original_source_and_run_unchanged':True,'canonical_matches_return':True,'wall_seconds_independent_outer':elapsed,'recorded_wall_seconds':record['wall_seconds'],'recorded_total_cpu_seconds':record['total_cpu_seconds'],'recorded_totals_scope':record['accounting_point'],'native_jobs':0,'engine_jobs':0,'gui_actions':0,'status_scope':'Actual saved-evidence disposable copy using ignored draft; not production CLI or actual GUI qualification.'}
(HERE/'actual-schema3-copy-001-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
