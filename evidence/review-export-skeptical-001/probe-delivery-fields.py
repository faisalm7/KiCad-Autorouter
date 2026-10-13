"""Stored export delivery claims must agree with their validated material."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent;DRAFT=ROOT/'.runs/review-export-draft-001'
spec=importlib.util.spec_from_file_location('export_owned_delivery_controls',DRAFT/'test_review_export.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from autorouter import review_export as actual
module.HERE=HERE;module.e=actual
def forbidden(*a,**kw):raise AssertionError('no subprocess/native/Git/network')
def main():
    source_hash=hashlib.sha256((ROOT/'autorouter/review_export.py').read_bytes()).hexdigest();rows=[]
    with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
        for field in ('whole_project_drc_clean','project_file'):
            case=module.ExportControls(methodName='test_actual_shared_validate_refill_and_readback_run_into_separate_copy');case.setUp();case.tmp._finalizer.detach()
            try:
                original=case.export();path=case.output/'export.json';raw=json.loads(path.read_text());before=actual.check_export(path)
                raw[field]=True if field=='whole_project_drc_clean' else str(case.source/'board.kicad_pro')
                path.write_text(json.dumps(raw));after=actual.check_export(path)
                rows.append({'field':field,'control_current':before['current'],'counterexample_current':after['current'],'export_accepted':after['export_accepted'],
                             'actual_native_warning_count':raw['native']['warnings'],'claimed_whole_project_drc_clean':raw['whole_project_drc_clean'],
                             'stored_project_file_belongs_to_export_candidate':Path(raw['project_file'])==Path(raw['candidate']).with_suffix('.kicad_pro'),
                             'owned_output':str(case.output.relative_to(HERE)),'fresh_native_processes_mocked':True,'source_and_review_unchanged':case.inputs=={str(p):actual.witness(p) for p in (case.source,case.run,case.root/'review',case.choice.parent)}})
            finally:case.stack.close()
    assert source_hash==hashlib.sha256((ROOT/'autorouter/review_export.py').read_bytes()).hexdigest()
    result={'schema':1,'actual_exporter_sha256':source_hash,'source_stable_before_after':True,'controls':rows,'native_subprocess_Git_network_executed':False,
            'scope':'Shared exporter/readback with explicit existing native/checker/tool seams. No actual native proof or application. Stored proof currently accepts delivery metadata inconsistent with its checked candidate/warnings.'}
    (HERE/'probe-delivery-fields.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
