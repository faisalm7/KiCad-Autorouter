"""Sequential actual normal selected workflow qualification; never PCB approval."""
from pathlib import Path
import sys,time,json,copy,shutil,signal
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,preferences as pref,routing_scope as rs,handoff as h,review_export as e
from autorouter.__main__ import preview
from scripts import qualify_review_export as workflow,native_cancellation as cancellation

def qualify(out):
    out=Path(out);out.mkdir();start=time.monotonic();cpu=time.process_time()+f.child_cpu();tools=p.tool_manifest();controller=p.sha(Path(__file__));inputs={};completed={};files={};owner={};h.capture_destination(owner,out);record=dict(schema=1,kind='normal-selected-promotion-native-v1',status='incomplete',accepted=False,controls_passed=False,human_pcb_approval_observed=False,tools=tools,controller_sha256=controller,cases=[],budget_seconds=600,cpu_budget_seconds=600,scope='Actual normal selected import paths plus authoredlegacywhole strict-zero-proof regression (tagged currentbody, nevergenuineKiCad8export), and separate-project preview/intent/freshNativeexport/cancellation qualification. All routes/new Native measured; authored zero-protection fixture is a validator control. No comparative routing/broadcoverage/electrical claim.')
    protocol=Path(__file__).parent/'input-pins.json';spec=f.read_json(protocol);protocol_sha=p.sha(protocol)
    if spec['status']!='prospectively_frozen' or spec['driver_sha256']!=controller:
        raise p.Rejected('workflow source protocol is not frozen')
    record['protocol_sha256']=protocol_sha
    def frozen():
        if p.sha(protocol)!=protocol_sha:raise p.Rejected('workflow protocol changed')
        for name,pin in spec['code_sha256'].items():
            if p.sha(ROOT/name)!=pin:raise p.Rejected('workflow frozen source changed: '+name)
        for name,pins in spec['source_projects'].items():
            if p.tree_hash(ROOT/name)!=pins:raise p.Rejected('workflow frozen input changed: '+name)
    frozen()
    if (ROOT/'.runs/review-export-native-selected-promotion-001').exists():
        raise p.Rejected('fresh workflow export prefix required before routing')
    def remaining():return min(600-(time.monotonic()-start),600-(time.process_time()+f.child_cpu()-cpu))
    def stable():
        h.owned_destination(owner);frozen()
        if p.tool_manifest()!=tools or p.sha(Path(__file__))!=controller:raise p.Rejected('workflow source/tools changed')
        if max(time.monotonic()-start,time.process_time()+f.child_cpu()-cpu)>=600:raise p.Rejected('workflow aggregate cap exhausted')
        for path,pins in completed.items():
            if e.witness(Path(path))!=pins:raise p.Rejected('completed workflow evidence changed')
        for path,pin in files.items():
            if p.sha(Path(path))!=pin:raise p.Rejected('captured preset/preview changed')
        for path,pins in inputs.items():
            if p.tree_hash(Path(path))!=pins:raise p.Rejected('immutable workflow input changed')
    try:
        original=ROOT/'.runs/selected-net-native-input-001/positive/smoke.kicad_pcb';zero=out/'zero-source'/original.name
        shutil.copytree(original.parent,zero.parent);tree=sx.read(zero);tree[:]=[n for n in tree if n not in p.routes(tree)];sx.write(zero,tree)
        cases=[('nus_protected',ROOT/'.runs/nus-native-feedback-engine120-003/warm-source/usb_led.kicad_pcb',['GND'],22,p.SELECTED_PROPOSAL_IMPORT_POLICY,10),('zero_protected',zero,['SIGNAL_A','SIGNAL_B'],0,p.SELECTED_PROPOSAL_IMPORT_POLICY,0),('locked_selected',original,['SIGNAL_A'],3,'exact_non_uuid_lock_position_v2',0),('legacy_whole',ROOT/'.runs/legacy-normal-workflow-native-001/source/smoke.kicad_pcb',None,0,'exact_non_uuid_lock_position_v2',0)]
        settings=out/'presets';settings.mkdir()
        for name,source,names,protected,policy,warnings in cases:
            stable();inputs[str(source.parent)]=p.tree_hash(source.parent);preset=settings/(name+'.json');p.save_json(preset,{**pref.DEFAULTS,'scope':'selected_nets' if names is not None else 'whole_board_unlocked_routing','seconds':120,'adapter':'both','profile':'completion-only',**({'nets':names} if names is not None else {})})
            if remaining()<130:raise p.Rejected('insufficient aggregate routing reserve')
            files[str(preset)]=p.sha(preset)
            row=dict(name=name,source=str(source),source_hashes=inputs[str(source.parent)],passed=False,settings_sha256=p.sha(preset));record['cases'].append(row)
            try:
                view=preview(source,settings=preset);p.save_json(out/(name+'-preview.json'),view);files[str(out/(name+'-preview.json'))]=p.sha(out/(name+'-preview.json'))
                if view['protected_route_items']!=protected:raise p.Rejected('preview source protection differs')
                result=p.route(source,out/name,settings_path=preset);receipt=out/name/'result.json'
                row.update(receipt=str(receipt),receipt_sha256=p.sha(receipt),status=result['status'],native=result.get('native'),candidate_sha256=result.get('candidate_sha256'),metrics=result.get('metrics'),wall_seconds=result.get('wall_seconds'),total_cpu_seconds=result.get('total_cpu_seconds'))
                if result['accepted'] is not True:raise p.Rejected('actual normal route rejected')
                if not p.check_result(receipt)['current']:raise p.Rejected('actual normal shared readback failed')
                if result['protected_route_import']['policy']!=policy or result['native']['warnings']!=warnings or result['native']['exclusions']!=0:raise p.Rejected('normal path/policy/warnings differ')
                audit=rs.audit(sx.read(source),sx.read(Path(result['candidate'])),names) if names is not None else None
                if names is not None and audit!=result['selected_net_audit']:raise p.Rejected('normal exact source selected audit differs')
                row.update(passed=True,import_policy=policy,protected_route_count=protected,selected_net_audit=audit)
            except (Exception,KeyboardInterrupt) as exc:
                row.update(error=type(exc).__name__+': '+str(exc))
                if isinstance(exc,KeyboardInterrupt):raise
            if (out/name).exists():completed[str(out/name)]=e.witness(out/name)
            stable();p.save_json(out/'progress.json',record)
        if all(row['passed'] for row in record['cases']):
            workflow.CASES=tuple((row['name'],str(Path(row['receipt']).relative_to(ROOT)),1,row['name']!='zero_protected') for row in record['cases'])
            workflow.SECONDS=min(600,remaining()-150)
            if workflow.SECONDS<5:raise p.Rejected('insufficient aggregate export/cancellation reserve')
            exports=workflow.qualify(ROOT/'.runs/review-export-native-selected-promotion-001',run_native=True)
            completed[str(ROOT/'.runs/review-export-native-selected-promotion-001')]=e.witness(ROOT/'.runs/review-export-native-selected-promotion-001')
            record.update(workflow_controls_passed=exports['controls_passed'],workflow_result=str(ROOT/'.runs/review-export-native-selected-promotion-001/result.json'),workflow_result_sha256=p.sha(ROOT/'.runs/review-export-native-selected-promotion-001/result.json'))
        else:record.update(workflow_controls_passed=False,workflow_reason='A required routing path failed; no omission of failed cases.')
        stable()
        if remaining()<135:raise p.Rejected('insufficient aggregate cancellation reserve')
        record['engine_cancellation_passed']=cancellation.control(out/'cancellation',signal.SIGINT)==0
        record['cancellation_control_sha256']=p.sha(out/'cancellation/control.json');completed[str(out/'cancellation')]=e.witness(out/'cancellation');stable()
        record.update(status='completed',controls_passed=all(row['passed'] for row in record['cases']) and record['workflow_controls_passed'] and record['engine_cancellation_passed'])
    except (Exception,KeyboardInterrupt) as exc:record.update(status='failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    record.update(completed_evidence=completed,source_inputs=inputs,preset_and_preview_sha256=files)
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu)
        record['within_budget']=remaining()>0
        record['controls_passed']=(record['status']=='completed' and record['within_budget'] and len(record['cases'])==4
            and all(row['passed'] for row in record['cases']) and record.get('workflow_controls_passed') is True
            and record.get('engine_cancellation_passed') is True)
    def replay():
        stable()
        for row in record['cases']:
            if row['passed'] and not p.check_result(Path(row['receipt']))['current']:
                raise p.Rejected('final normal route readback failed')
        if record.get('workflow_controls_passed'):
            exports=f.read_json(ROOT/'.runs/review-export-native-selected-promotion-001/result.json')
            for row in exports['cases']:
                if not e.check_export(ROOT/'.runs/review-export-native-selected-promotion-001'/row['name']/'export/export.json')['current']:
                    raise p.Rejected('final export readback failed')
        stable()
    return f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
    if not a.run_native:ap.error('explicit Native opt-in required')
    if a.output.parent!=ROOT/'.runs' or a.output.exists():ap.error('fresh direct project-local output required')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    result=qualify(a.output);print(json.dumps({k:result.get(k) for k in ('status','controls_passed','error','wall_seconds','total_cpu_seconds')}));raise SystemExit(0 if result['controls_passed'] else 2)
