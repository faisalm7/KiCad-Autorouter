"""Retain completed normal workflows; execute only the missing cancellation control."""
from pathlib import Path
import sys,time,signal,json
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as e,handoff as h
from scripts import native_cancellation as cancellation

PROTOCOL=Path(__file__).with_name('cancellation-input-pins.json')

def prior_charge():
    """Derive the conservative charge from pinned actual receipts, never a hint."""
    root='.runs/'
    sources=[('normal-selected-workflow-native-execution-001/execution.json','total_cpu_seconds'),
        ('owned-process-metadata-targeted-preserved-001/output/execution.json','full_cpu_seconds'),
        ('cancellation-observer-targeted-001/execution.json','total_cpu_seconds'),
        ('cancellation-observer-targeted-002/output/execution.json','full_cpu_seconds'),
        ('full-integration-073/execution.json','full_cpu_seconds'),
        ('full-integration-074/execution.json','full_cpu_seconds'),
        ('normal-selected001-readback-review-001/initial-refusal-execution.json','full_cpu_seconds'),
        ('normal-selected001-readback-review-001/execution.json','full_cpu_seconds')]
    rows=[]
    for name,cpu_key in sources:
        path=ROOT/(root+name);data=f.read_json(path);wall=data['wall_seconds'];full=data[cpu_key]
        if not e.finite(wall) or not e.finite(full):raise p.Rejected('invalid actual prior resource receipt')
        rows.append(dict(path=root+name,sha256=p.sha(path),wall_seconds=wall,total_cpu_seconds=full,publication_and_startup_allowance_seconds=2))
    actor=f.read_json(ROOT/'.runs/normal-selected-workflow-native-001/result.json')
    if not e.finite(actor['wall_seconds']) or not e.finite(actor['total_cpu_seconds']):raise p.Rejected('invalid actual001 actor costs')
    rows[0]['wall_seconds']=max(rows[0]['wall_seconds'],actor['wall_seconds'])
    rows[0]['total_cpu_seconds']=max(rows[0]['total_cpu_seconds'],actor['total_cpu_seconds'])
    return dict(components=rows,wall_seconds=sum(x['wall_seconds']+2 for x in rows),total_cpu_seconds=sum(x['total_cpu_seconds']+2 for x in rows))

def retained(spec):
    """Recheck actual saved evidence through the existing production readers."""
    prior=f.read_json(ROOT/'.runs/normal-selected-workflow-native-001/result.json')
    outer=f.read_json(ROOT/'.runs/normal-selected-workflow-native-execution-001/execution.json')
    exports=f.read_json(ROOT/'.runs/review-export-native-selected-promotion-001/result.json')
    if (prior['controls_passed'] is not False or prior['engine_cancellation_passed'] is not False
            or prior['workflow_controls_passed'] is not True or outer['outer_qualified'] is not False
            or outer['process']['cleanup_complete'] is not True or outer['source_current'] is not True
            or exports['controls_passed'] is not True):
        raise p.Rejected('retained failed aggregate or passed workflow identity changed')
    names=['nus_protected','zero_protected','locked_selected','legacy_whole']
    if [r['name'] for r in prior['cases']]!=names or [r['name'] for r in exports['cases']]!=names:
        raise p.Rejected('all four retained workflow cases are required')
    rows=[]
    for route,export in zip(prior['cases'],exports['cases']):
        receipt=Path(route['receipt']);export_path=ROOT/'.runs/review-export-native-selected-promotion-001'/route['name']/'export/export.json'
        if (route['passed'] is not True or export['passed'] is not True
                or not p.check_result(receipt)['current'] or not e.check_export(export_path)['current']):
            raise p.Rejected('retained actual route or export is no longer current')
        rows.append(dict(name=route['name'],route_receipt_sha256=p.sha(receipt),export_receipt_sha256=p.sha(export_path),native=route['native']))
    return rows

def qualify(out):
    out=Path(out);out.mkdir();owner={};h.capture_destination(owner,out)
    start=time.monotonic();cpu=time.process_time()+f.child_cpu()
    spec=f.read_json(PROTOCOL);protocol_pin=p.sha(PROTOCOL);tools=p.tool_manifest();controller=p.sha(Path(__file__))
    if spec['status']!='prospectively_frozen' or spec['driver_sha256']!=controller:
        raise p.Rejected('missing-only continuation protocol is not frozen')
    prior=prior_charge()
    if spec['prior_charge']!=prior:raise p.Rejected('frozen charge does not match actual cumulative costs')
    completed={}
    record=dict(schema=1,kind='normal-selected-missing-cancellation-v1',status='failed',accepted=False,
        controls_passed=False,human_pcb_approval_observed=False,protocol_sha256=protocol_pin,
        controller_sha256=controller,tools=tools,budget_seconds=600,cpu_budget_seconds=600,
        prior_charge=prior,new_routing_cases_executed=False,new_export_cases_executed=False,
        scope='Four retained actual normal routes and preview/test-intent/fresh Native exports, plus ONLY new engine-stage SIGINT observer qualification under unchanged network denial. Authored controls are not independent boards. Prior failed aggregate remains false. No GUI, live apply, human/physical approval or comparative claim.')
    def remaining():
        return min(600-prior['wall_seconds']-(time.monotonic()-start),600-prior['total_cpu_seconds']-(time.process_time()+f.child_cpu()-cpu))
    def stable():
        h.owned_destination(owner)
        if p.sha(PROTOCOL)!=protocol_pin or p.sha(Path(__file__))!=controller or p.tool_manifest()!=tools:
            raise p.Rejected('continuation source/tools changed')
        for name,pin in spec['code_sha256'].items():
            if p.sha(ROOT/name)!=pin:raise p.Rejected('continuation pinned source changed: '+name)
        for name,pins in spec['source_projects'].items():
            if p.tree_hash(ROOT/name)!=pins:raise p.Rejected('continuation immutable input changed: '+name)
        for name,pins in {**spec['retained_prefixes'],**completed}.items():
            if e.witness(ROOT/name)!=pins:raise p.Rejected('retained evidence changed: '+name)
        # Runtime must remain identical to the four completed cases. The fix is
        # confined to the qualification script, never a compatibility exception.
        old=f.read_json(ROOT/'.runs/normal-selected-workflow-native-001/result.json')['tools']
        if {k:v for k,v in old.items() if k!='git_head'}!={k:v for k,v in tools.items() if k!='git_head'}:
            raise p.Rejected('completed workflow runtime changed')
        if remaining()<=0:raise p.Rejected('cumulative qualification budget exhausted')
    def replay():
        stable();rows=retained(spec)
        if rows!=record.get('retained_cases'):raise p.Rejected('retained workflow readback changed')
        if record.get('engine_cancellation_passed'):
            control=f.read_json(out/'cancellation/control.json');engine=control['engine_receipt']['data']
            if (control.get('passed') is not True or control['status']!='passed'
                    or not all(control['checks'].values()) or control['remaining_owned_engine_group']!=[]
                    or engine['pid']!=control['observed_owned_engine']['pid']
                    or control['signals'][0]['signal']!='SIGINT'
                    or p.sha(Path(control['route_receipt']['path']))!=control['route_receipt']['sha256']
                    or p.sha(Path(control['engine_receipt']['path']))!=control['engine_receipt']['sha256']):
                raise p.Rejected('actual owned cancellation evidence changed')
        stable()
    try:
        stable();record['retained_cases']=retained(spec);stable()
        if remaining()<135:raise p.Rejected('insufficient cumulative cancellation reserve')
        record['engine_cancellation_passed']=cancellation.control(out/'cancellation',signal.SIGINT)==0
        completed[str((out/'cancellation').relative_to(ROOT))]=e.witness(out/'cancellation')
        stable();record.update(status='completed')
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='failed',error=type(exc).__name__+': '+str(exc))
    def account():
        wall=time.monotonic()-start;full=time.process_time()+f.child_cpu()-cpu
        record.update(wall_seconds=wall,total_cpu_seconds=full,
            cumulative_wall_seconds=prior['wall_seconds']+wall,cumulative_total_cpu_seconds=prior['total_cpu_seconds']+full,
            within_budget=remaining()>0,completed_evidence=completed)
        record['controls_passed']=(record['status']=='completed' and record.get('engine_cancellation_passed') is True and remaining()>0)
    return f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
    if not a.run_native:ap.error('explicit Native opt-in required')
    if a.output.parent!=ROOT/'.runs' or a.output.exists():ap.error('fresh direct local output required')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    result=qualify(a.output);print(json.dumps({k:result.get(k) for k in ('status','controls_passed','error','cumulative_wall_seconds','cumulative_total_cpu_seconds')}));raise SystemExit(0 if result['controls_passed'] else 2)
