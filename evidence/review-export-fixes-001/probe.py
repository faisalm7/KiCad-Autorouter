"""Narrow exporter fixes controls, using existing explicit pure process seams."""
from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('owned_current_export_tests',ROOT/'tests/test_review_export.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=HERE;e=m.e;p=m.p
def forbidden(*a,**kw):raise AssertionError('No subprocess/native/JVM/Git/network')
def case():
    value=m.ExportControls(methodName='test_actual_shared_validate_refill_and_readback_run_into_separate_copy');value.setUp();value.tmp._finalizer.detach();return value
def preserved(value):return value.inputs=={str(x):e.witness(x) for x in (value.source,value.run,value.root/'review',value.choice.parent)}
def main():
    bindings={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('autorouter/review_export.py','autorouter/pipeline.py','autorouter/handoff.py','tests/test_review_export.py')};rows=[]
    with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
        value=case()
        try:
            original=value.export();path=value.output/'export.json';raw=path.read_bytes();record=json.loads(raw);assert e.check_export(path)['current']
            rows.append({'case':'positive_control','current':True,'warning_count':record['native']['warnings'],'whole_project_drc_clean':record['whole_project_drc_clean'],'source_and_review_unchanged':preserved(value)})
            mutations={'negative_parent_cpu':{'parent_cpu_seconds':-1.,'control_child_cpu_seconds':1.,'total_cpu_seconds':0.},
                       'false_clean_with_warning':{'whole_project_drc_clean':True},'project_file_points_original':{'project_file':str(value.source/'board.kicad_pro')}}
            for name,changes in mutations.items():
                path.write_text(json.dumps({**record,**changes}));rejected=None
                try:e.check_export(path)
                except p.Rejected as exc:rejected=str(exc)
                assert rejected is not None;path.write_bytes(raw);assert e.check_export(path)['current']
                rows.append({'case':name,'rejected':rejected,'restored_positive_current':True,'source_and_review_unchanged':preserved(value)})
            # Additional cost metadata remains material: its values are the
            # claimed original workflow cost, separate from this new export.
            changed={**record,'original_routing_receipt_compute':{'budget_seconds':120.,'cpu_budget_seconds':120.,'wall_seconds':0.,'total_cpu_seconds':0.}}
            path.write_text(json.dumps(changed));caught=None;checked=None
            try:checked=e.check_export(path)
            except p.Rejected as exc:caught=str(exc)
            rows.append({'case':'original_routing_compute_metadata_changed','rejected':caught,'counterexample_current':checked.get('current') if checked else False,
                         'actual_recorded_original_compute':record['original_routing_receipt_compute'],'changed_original_compute':changed['original_routing_receipt_compute'],'source_and_review_unchanged':preserved(value)})
            path.write_bytes(raw)
        finally:value.stack.close()
        value=case()
        try:
            seam=value.native_run
            def impossible(*args,**kwargs):
                result=seam(*args,**kwargs);result['wall_seconds']=1.;return result
            e.run.side_effect=impossible;rejected=None
            try:value.export()
            except p.Rejected as exc:rejected=str(exc)
            assert rejected is not None
            raw=p.sha(value.output/'export.json');record=e.f.read_json(value.output/'export.json');assert record['export_accepted'] is False
            rows.append({'case':'sequential_wall_history','rejected':rejected,'corrective_export_accepted':False,'corrective_record_sha256':raw,'source_and_review_unchanged':preserved(value)})
        finally:value.stack.close()
        for method in ('test_gui_rules_before_choice_are_never_export_authority','test_protected_original_copper_and_empty_original_directories_survive_export'):
            value=case()
            try:getattr(value,method)();rows.append({'case':method,'assertions_passed':True,'explicit_native_process_seams':True})
            finally:value.stack.close()
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in bindings.items())
    result={'schema':1,'source_stable_before_after':True,'sources':bindings,'controls':rows,'native_subprocess_JVM_Git_network_executed':False,
            'scope':'Existing mocked native/checker/tool seams with real shared validation, capture, stage/readback/publication paths. No native qualification, real performance or actual PCB approval claim.'}
    (HERE/'probe.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
