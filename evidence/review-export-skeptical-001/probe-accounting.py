"""Export accounting consistency controls using retained pure process seams."""
from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent;DRAFT=ROOT/'.runs/review-export-draft-001'
spec=importlib.util.spec_from_file_location('export_owned_controls',DRAFT/'test_review_export.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from autorouter import review_export as actual
module.HERE=HERE;module.e=actual
def forbidden(*a,**kw):raise AssertionError('No subprocess/native/Git/network execution allowed')
def run_case(kind):
    case=module.ExportControls(methodName='test_actual_shared_validate_refill_and_readback_run_into_separate_copy');case.setUp();case.tmp._finalizer.detach()
    try:
        if kind=='wall-history':
            seam=case.native_run
            def timed(*args,**kwargs):
                result=seam(*args,**kwargs);result['wall_seconds']=1.;return result
            actual.run.side_effect=timed
        record=case.export();path=case.output/'export.json';raw=json.loads(path.read_text())
        control=actual.check_export(path)
        original=copy.deepcopy(raw)
        if kind=='negative-parent-cpu':
            raw.update(parent_cpu_seconds=-1.,control_child_cpu_seconds=1.,child_step_cpu_seconds=0.,monitor_cpu_seconds=0.,total_cpu_seconds=0.,within_budget=True)
            path.write_text(json.dumps(raw));checked=actual.check_export(path)
        else:checked=control
        return {'case':kind,'owned_output':str(case.output.relative_to(HERE)),'fresh_native_processes_are_mocked':True,'real_native_execution':False,
                'control_returned_current':control['current'],'counterexample_returned_current':checked['current'],'counterexample_export_accepted':checked['export_accepted'],
                'declared_parent_cpu_seconds':raw['parent_cpu_seconds'],'declared_total_cpu_seconds':raw['total_cpu_seconds'],'declared_wall_seconds':raw['wall_seconds'],
                'sum_retained_sequential_native_wall_seconds':sum(x['wall_seconds'] for x in raw['steps']),
                'sum_retained_native_cpu_seconds':sum(x['cpu_seconds'] for x in raw['steps']),
                'candidate_sha256':raw['candidate_sha256'],'original_source_and_review_unchanged':case.inputs=={str(p):actual.witness(p) for p in (case.source,case.run,case.root/'review',case.choice.parent)}}
    finally:case.stack.close()
def main():
    before=hashlib.sha256((ROOT/'autorouter/review_export.py').read_bytes()).hexdigest();rows=[]
    with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
        for kind in ('negative-parent-cpu','wall-history'):rows.append(run_case(kind))
    after=hashlib.sha256((ROOT/'autorouter/review_export.py').read_bytes()).hexdigest();assert before==after
    result={'schema':1,'actual_exporter_sha256':before,'draft_exporter_sha256':hashlib.sha256((DRAFT/'review_export.py').read_bytes()).hexdigest(),
            'source_stable_before_after':True,'controls':rows,'native_subprocess_Git_network_executed':False,
            'scope':'Real shared exporter/finalizer/readback filesystem and process-binding paths with explicit mocked native/checker/tool seams. No native validation or actual CPU/wall performance claim; malformed metadata acceptance is the finding.'}
    (HERE/'probe-accounting.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
