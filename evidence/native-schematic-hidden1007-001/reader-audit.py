"""Retained original-rule/fullSCH field readback through shared helpers only."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
real_popen=subprocess.Popen
def readonly_popen(argv,*a,**kw):
    if argv!=['git','rev-parse','HEAD']:raise AssertionError('pure reader forbids Native/JVM/network/tests/Git mutation')
    return real_popen(argv,*a,**kw)
subprocess.Popen=readonly_popen
from autorouter import pipeline as p,floor_route as f,handoff as h,schematic_field_evidence as fields
from experiments.native_schematic_toolchain_v1 import continuation as model
OUT=Path(__file__).resolve().parent;BASE=ROOT/'.runs/native-schematic-hidden-execution-001';read=f.read_json
outer=read(BASE/'result.json');result=read(BASE/'native/result.json');frozen,prior,previous=model.reference_records()
nt=p.ExperimentalNativeToolchain.from_record(result['experimental_native_toolchain']);tools=p.tool_manifest()
material=p.tree_hash(BASE);pins={str(x):p.sha(x) for x in (Path(__file__),OUT/'run.py',model.PREPARATION,model.FAILED_FIRST)}
checks=[];failures=[];owner={};h.capture_destination(owner,OUT)
rows=[(model.REFERENCE/'native'/(r['version']+'-'+r['case']),r) for r in prior['cases']]+[(BASE/'native'/(r['version']+'-'+r['case']),r) for r in result['cases']]
def remaining():return max(0,min(58-(time.monotonic()-START),58-(cpu()-CPU0)))
def stable():
    h.owned_destination(owner);nt.check()
    if p.tool_manifest()!=tools or tools!=outer['tools'] or tools!=result['tools']:raise p.Rejected('current committed source/tool context differs')
    if p.tree_hash(BASE)!=material:raise p.Rejected('new actual Native evidence changed')
    model.reference_records()
    if any(p.sha(Path(n))!=pin for n,pin in pins.items()):raise p.Rejected('reader input/controller changed')
    if any(p.sha(Path(n))!=pin for n,pin in result['code_sha256'].items()):raise p.Rejected('actual experiment source changed')
    for folder,row in rows:
        for stage in ('refill-drc','final-drc'):fields.check_local_settings(folder/'native',stage,read(folder/'native'/(stage+'-binding.json')))
    if remaining()<=0:raise p.Rejected('bounded retained reader exhausted')
try:
    stable()
    assert outer['status']=='completed' and outer['passed'] and outer['source_current']
    proc=outer['process'];assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] and not proc['log_truncated']
    assert p.sha(BASE/'command.log')==outer['log_sha256'] and p.sha(ROOT/'experiments/native_schematic_toolchain_v1/enclosure.py')==outer['controller_sha256']
    assert p.tree_hash(BASE/'native')==outer['child_material_sha256'] and p.sha(BASE/'native/result.json')==outer['child_receipt_sha256']
    assert result['status']=='completed' and result['controls_passed'] and all(result[k] is False for k in ('accepted','production_admitted','routing_scope_accepted'))
    assert len(result['cases'])==2 and len(prior['cases'])==4 and prior['status']=='failed' and prior['controls_passed'] is False
    assert result['prior_charged_enclosure_costs']==outer['prior_charged_enclosure_costs']==previous
    assert outer['whole_wall_full_cpu_cap_seconds']==190 and result['budget_seconds']==result['cpu_budget_seconds']==120
    assert max(outer['wall_seconds']+previous['wall_seconds'],outer['full_cpu_seconds']+previous['full_cpu_seconds'])+2+62<=190
    assert {str(folder) for folder,row in rows[-2:]}==set(result['completed_evidence'])
    for folder,row in rows:
        current=nt if row['version']=='10.0.7' else None
        checked=model.common.retained_case(folder,row,current);assert checked==row['checks']
        expected=['refill-drc','refill-drc-fields-netlist','refill-drc-fields-audit','final-drc','final-drc-fields-netlist','final-drc-fields-audit']
        assert [s['name'] for s in row['steps']]==expected
        for step in row['steps']:
            process=f.process_check(folder/'native',row,step['name'],step['argv'],allowed=(0,5))
            assert process['cleanup_complete'] and not process['log_truncated'] and Path(process['log']).stat().st_size==process['log_bytes']
        if row['case']==model.fixture.MASKED_CASE:
            positive=next(x for x in prior['cases'] if x['version']==row['version'] and x['case']=='positive')
            assert all(model.same_findings(positive[stage],row[stage]) for stage in ('saved_refill','final_native'))
            assert row['same_actual_findings_as_prior_positive'] is True
            assert p.tree_hash(folder)==result['completed_evidence'][str(folder)]
        checks.append(dict(version=row['version'],case=row['case'],candidate_sha256=row['candidate_sha256'],reports={stage:p.sha(folder/'native'/(stage+'.json')) for stage in ('refill-drc','final-drc')},checks=checked,workers=len(row['steps'])))
    assert len(checks)==6 and sum(r['workers'] for r in checks)==36
    assert tools['implementation_sha256']==prior['tools']['implementation_sha256'] and tools['files']==prior['tools']['files']
    stable()
except (Exception,KeyboardInterrupt) as exc:failures.append(dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()))
report=dict(schema=1,kind='shared-retained-fullsch-prl-hidden-field-control-readback',status='completed' if not failures else 'failed',accepted=False,passed=not failures,controls_qualified=not failures,production1007_admitted=False,normal1007_routing_admitted=False,new_native_execution=False,new_jvm_execution=False,new_test_execution=False,new_network_requests=0,checks=checks,failures=failures,input_sha256=pins,native_material_inventory_sha256=material,source_head=tools['git_head'],prior_charged_enclosure_costs=previous,current_enclosure_reported_cost={k:outer[k] for k in ('wall_seconds','full_cpu_seconds','publication_allowance_seconds','cost_scope')},reader_reserved_whole_wall_full_cpu_seconds=62,cumulative_upper_wall_seconds=previous['wall_seconds']+outer['wall_seconds']+2+62,cumulative_upper_full_cpu_seconds=previous['full_cpu_seconds']+outer['full_cpu_seconds']+2+62,scope='Six owned exposed cases/12realDRCreports/36completedworkers plus3failedfirstworkers retained. Positive2 accept fullfields; visiblecustom2 and genuinelymaskedDescription2 reject. FirstNative001 and aggregate002 stayfailed. Original source/rules/zone/lockedtrace/PRL/refill/finalhash/actualtools/argv rechecked; no productionrouting/customDRUadmission/engine/GUI/gain/newfamily/physical/human/release claim.')
def account():
    report.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
    if report['status']!='completed' or remaining()<=0:report.update(passed=False,controls_qualified=False)
f.publish(OUT,report,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
print(json.dumps({k:report[k] for k in ('status','passed','controls_qualified','failures','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if report['passed'] else 2)
