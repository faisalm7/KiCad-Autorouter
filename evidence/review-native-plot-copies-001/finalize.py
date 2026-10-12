"""Compact source/failure bindings; read-only original artifacts, no native."""
from pathlib import Path
import sys,json,hashlib,difflib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import placement_clearance as pc
HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def record(path):return {'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2)+'\n')
actual=ROOT/'.runs/review-render-fixture-002';receipt=ROOT/'.runs/default-tuning-native-001/result.json';input_record=json.loads(receipt.read_text());source=Path(input_record['source']).parent
before={'actual':pc.inventory(actual),'source':pc.inventory(source)}
review=json.loads((actual/'review.json').read_text());process=json.loads((actual/'plot-work/before-F.Cu-process.json').read_text())
copy=pc.inventory(actual/'before');original=before['source']
difference={'added':sorted(set(copy)-set(original)),'removed':sorted(set(original)-set(copy)),'changed':[name for name in original if name in copy and original[name]!=copy[name]]}
assert difference=={'added':['fixture.kicad_prl'],'removed':[],'changed':[]}
assert review['status']=='rejected' and review['error']=='Rejected: copied original changed while preparing review preview'
assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
assert before=={'actual':pc.inventory(actual),'source':pc.inventory(source)}
save('actual-failure-binding.json',{'schema':1,'native_rerun':False,'receipt':record(receipt),'source':str(source),'review':record(actual/'review.json'),'process':record(actual/'plot-work/before-F.Cu-process.json'),'prior_process_status':process['status'],'prior_process_exit':process['exit_code'],'prior_process_wall_seconds':process['wall_seconds'],'prior_process_cpu_seconds':process['cpu_seconds'],'error':review['error'],'copy_vs_original':difference,'actual_added_prl':record(actual/'before/fixture.kicad_prl'),'actual_and_source_unchanged_during_read':True,'actual_inventory_digest':hashlib.sha256(json.dumps(before['actual'],sort_keys=True).encode()).hexdigest(),'source_inventory_digest':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),'files_in_actual':len(before['actual']),'files_in_source':len(original),'scope':'Historical rejected preview; successful plot is not a ready preview or DRC. No rerun.'})
source_paths=['autorouter/review_view.py','autorouter/handoff.py','tests/test_review_view.py']
save('final-source-bindings.json',{'schema':1,'source':[record(ROOT/name) for name in source_paths],'baseline':record(ROOT/'.runs/review-native-plot-copies-baseline-c3fa13f.py'),'original_probe_source_sha256':json.loads((HERE/'probe-before-001/results.json').read_text())['review_view_sha256'],'provenance_correction':'Preserved baseline-bindings.json key initial_reviewed_source and initial-diff.patch actually capture intermediate ae930075 source after ROOT began the membership fix; they are not the earlier e8c2b223 source exercised by probe-before-001. The before-probe result binds that exact earlier hash; no exact earlier snapshot is claimed. Final source is bound here.'})
baseline=(ROOT/'.runs/review-native-plot-copies-baseline-c3fa13f.py').read_text().splitlines(True);current=(ROOT/'autorouter/review_view.py').read_text().splitlines(True)
(HERE/'final-renderer-diff.patch').write_text(''.join(difflib.unified_diff(baseline,current,fromfile='ROOT-supplied-c3fa13f/review_view.py',tofile='reviewed/review_view.py')))
print(json.dumps({'actual_difference':difference,'source_pins':{name:sha(ROOT/name) for name in source_paths}},indent=2))
