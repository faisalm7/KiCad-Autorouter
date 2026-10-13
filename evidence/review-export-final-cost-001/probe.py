"""Only the final original-workflow cost counterexample and restored positive."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('owned_export_cost_controls',ROOT/'tests/test_review_export.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=HERE;e=m.e;p=m.p
def forbidden(*a,**kw):raise AssertionError('No subprocess/native/JVM/Git/network')
def main():
    bindings={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('autorouter/review_export.py','autorouter/pipeline.py','tests/test_review_export.py')}
    with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
        case=m.ExportControls(methodName='test_actual_shared_validate_refill_and_readback_run_into_separate_copy');case.setUp();case.tmp._finalizer.detach()
        try:
            control=case.export();path=case.output/'export.json';raw=path.read_bytes();assert e.check_export(path)['current']
            data=json.loads(raw);data['original_routing_receipt_compute']={'budget_seconds':120.,'cpu_budget_seconds':120.,'wall_seconds':0.,'total_cpu_seconds':0.};path.write_text(json.dumps(data));rejection=None
            try:e.check_export(path)
            except p.Rejected as exc:rejection=str(exc)
            assert rejection is not None;path.write_bytes(raw);restored=e.check_export(path);assert restored['current']
            assert case.inputs=={str(x):e.witness(x) for x in (case.source,case.run,case.root/'review',case.choice.parent)}
            result={'schema':1,'status':'final_compute_gap_resolved','sources':bindings,'source_stable_before_after':True,'positive_control_current':True,'tampered_original_cost_rejected':rejection,'restored_positive_current':True,
                    'source_and_review_unchanged':True,'owned_output':str(case.output.relative_to(HERE)),'native_subprocess_JVM_Git_network_executed':False,
                    'scope':'Existing explicit mocked native/checker/tool seams; real shared capture/validation/readback. No actual native, PCB qualification, measured native runtime or benchmark cost claim.'}
        finally:case.stack.close()
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in bindings.items())
    (HERE/'probe.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
