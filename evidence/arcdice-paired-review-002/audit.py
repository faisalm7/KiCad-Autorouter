"""Read only completed ArcDice evidence; no native execution or Git.
Uses existing central/native/process/resource/replay helpers. Geometry stays local.
"""
import time
START=time.monotonic()
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import copy, hashlib, json, math, subprocess, time, traceback
from unittest.mock import patch
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc, sexpr as sx, strategy as s, config as c
from scripts import experiment_paired as paired
OUT=Path(__file__).resolve().parent
B=ROOT/'.runs/arcdice-native-paired-complete-sch-003'
Q=ROOT/'.runs/arcdice-native-paired-complete-sch-003-qualification'
O=ROOT/'.runs/arcdice-original-native-001'
R=ROOT/'.runs/arcdice-original-native-002-readback/result.json'
SPEC=ROOT/'.runs/arcdice-native-paired-complete-sch-003-protocol.json'
CPU=0.0  # Lifetime self CPU includes bootstrap/imports; no child processes.
def dump(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def witness(path,cap=96*1024**2):return pc.inventory(path,max_bytes=cap,max_files=6000,max_entries=12000,with_directories=True)
def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def no_process(*a,**k):raise AssertionError('review must not launch a subprocess')
def close(a,b):assert math.isclose(a,b,abs_tol=1e-8,rel_tol=0),(a,b)
def warn_hash(native):return sha_bytes(f.canonical([x for x in native['findings'] if x['severity']=='warning']).encode())
def counts(native):return {k:native[k] for k in ('opens','blocking','warnings','exclusions')}
def argv_native(action,board,output,*extras):return [str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),action,str(board),str(output),*[str(x) for x in extras]]

def run():
    inputs={str(x.relative_to(ROOT)):witness(x) for x in (B,Q,O)}
    digests={str(x.relative_to(ROOT)):p.sha(x) for x in (R,SPEC)}
    spec=f.read_json(SPEC); protocol=f.read_json(B/'run/protocol.json'); summary=f.read_json(B/'run/paired-summary.json'); outer=f.read_json(B/'execution.json'); qualified=f.read_json(Q/'result.json')
    tools=protocol['freeze']['tools']; source=Path(protocol['source']); source_hashes=protocol['freeze']['source_hashes']; original=p.preflight(source); protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    assert not protected and len(p.routes(original))==67
    assert p.tree_hash(O/'original')=={k:v['sha256'] for k,v in spec['source_five_files'].items()}
    assert p.tree_hash(source.parent)==source_hashes
    assert spec['tools']==tools and spec['git_head']==tools['git_head']==outer['git_head']
    assert outer['prospective_protocol_sha256']==p.sha(SPEC) and outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete'] is True
    assert p.sha(ROOT/'experiments/native_paired_v1/readback.py')==qualified['controller_sha256']
    assert p.sha(B/'run/paired-summary.json')==qualified['paired_summary_sha256'] and p.sha(B/'execution.json')==qualified['outer_execution_sha256']
    assert f.read_json(Q/'execution.json')['result_sha256']==p.sha(Q/'result.json')
    current_code={name:p.sha(ROOT/name) for name in tools['implementation_sha256']}
    assert current_code==tools['implementation_sha256']
    for path,digest in tools['files'].items():assert p.sha(Path(path))==digest
    source_data=f.read_json(O/'result.json'); source_readback=f.read_json(R)
    assert p.sha(O/'result.json')==spec['source_original_native_receipt_sha256']==qualified['original_receipt_sha256']
    assert p.sha(R)==spec['source_original_native_readback_sha256']==qualified['original_readback_sha256']
    assert source_data['original_hashes']==p.tree_hash(O/'original') and source_readback['controls_passed'] is True and source_readback['source_exact'] is True
    original_native=source_data['parity_native']; assert original_native==source_readback['native']; assert counts(original_native)==spec['original_expected_native']
    original_candidate=Path(source_data['final_candidate'])
    assert p.immutable(sx.read(original_candidate))==p.immutable(original) and p.routes(sx.read(original_candidate))==p.routes(original)
    before=dict(source_hashes);before[source.name]=p.sha(original_candidate)
    assert f.check_drc_stage(O/'job',source_data,'original-final',original_candidate,O/'job/original-final-input'/source.name,False,before,schematic_parity=True,sandboxed=True)==original_native
    assert p.sha(O/'job/original-final.json')==source_data['final_native_report_sha256']
    warning_digest=warn_hash(original_native)
    assert len([x for x in original_native['findings'] if x['severity']=='warning'])==26
    task=copy.deepcopy(original)
    task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in p.ROUTES or p.locked(n)]
    for z in sx.children(task,'zone'):z[:]=[n for n in z if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
    task_hash=sha_bytes((sx.dump(task)+'\n').encode())
    assert not p.routes(task)
    out=[];central=[];native_stages=1;process_stages=0
    def candidate(folder,data,before_refill,expected_accepted,kind):
        nonlocal native_stages,process_stages
        candidate=folder/'candidate'/source.name
        if 'candidate' in data:assert data['candidate']==str(candidate)
        p.verify_candidate_files(candidate,source_hashes,data['candidate_sha256'])
        tree=sx.read(candidate); assert p.immutable(tree)==p.immutable(original)
        expected=dict(source_hashes);expected[source.name]=sha_bytes((sx.dump(before_refill)+'\n').encode())
        refill=folder/'refill'/source.name
        refill_native=f.check_drc_stage(folder,data,'refill-drc',refill,refill,True,expected,sandboxed=False)
        rebuilt=p.transplant_fill(before_refill,sx.read(refill)); assert (sx.dump(rebuilt)+'\n').encode()==candidate.read_bytes()
        before=dict(source_hashes);before[source.name]=data['candidate_sha256']
        native=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/source.name,False,before,schematic_parity=True,sandboxed=False)
        assert native==data['native'] and p.sha(folder/'final-drc.json')==data['native_report_sha256']
        assert warn_hash(native)==warning_digest
        assert p.native_accepted(native) is expected_accepted
        classes=f.read_json(folder/'final-netclasses.json'); audit=p.audit_candidate_netclasses(candidate,protected,classes)
        f.process_check(folder,data,'final-netclasses',argv_native('netclasses',candidate,folder/'final-netclasses.json'))
        if 'metrics' in data:
            assert f.read_json(folder/'metrics.json')==data['metrics']
            f.process_check(folder,data,'metrics',argv_native('metrics',candidate,folder/'metrics.json'));process_stages+=1
        native_stages+=2;process_stages+=3
        result={'id':kind,'receipt_sha256':p.sha(folder/'result.json'),'candidate_sha256':p.sha(candidate),'native_report_sha256':p.sha(folder/'final-drc.json'),'native':counts(native),'rejection_types':sorted(set(x['type'] for x in native['findings'] if x['severity']!='warning')),'full_warning_signature_sha256':warn_hash(native),'original_design_exact':True,'saved_refill_reconstruction_exact':True,'complete_schematic_parity_bound':True,'native_class_map_sha256':p.sha(folder/'final-netclasses.json'),'native_class_dimensions':audit['route_dimensions'],'native_accepted':expected_accepted,'metrics':data.get('metrics')}
        out.append(result);return candidate,result
    direct=[('B0',B/'run/B0',False),('B1',B/'run/B1',True),('B2/via_default',B/'run/B2_portfolio/01-via_default',True),('C/own_incumbent',B/'run/C_feedback/incumbent',True)]
    for kind,folder,accepted in direct:
        data=f.read_json(folder/'result.json');assert data['tools']==tools and data['source_hashes']==source_hashes and data['task_sha256']==task_hash
        assert data['scope']=='whole_board_unlocked_routing' and data['schematic_parity']!='not checked'
        if accepted:p.check_result(folder/'result.json');central.append(kind)
        p.check_resource_accounting(data)
        source_native=f.check_drc_stage(folder,data,'source-drc',folder/'snapshot'/source.name,folder/'source-drc-input'/source.name,False,source_hashes,sandboxed=False)
        assert source_native==data['source_drc'];native_stages+=1
        target=folder/'candidate'/source.name
        f.process_check(folder,data,'export',argv_native('export',target,folder/'task.dsn',folder/'export-netclasses.json'))
        if data['adapter']!='none':f.process_check(folder,data,'obstacles',argv_native('obstacles',target,folder/'obstacles.json'));process_stages+=1
        f.process_check(folder,data,'engine',p.engine_argv(folder,data['engine_budget']['argv']))
        f.process_check(folder,data,'import',argv_native('import',target,folder/'imported.kicad_pcb',folder/'routes.ses'));process_stages+=3
        before_refill=p.transplant_routes(task,sx.read(folder/'imported.kicad_pcb'),protected=protected,policy='exact_non_uuid_lock_position_v2')
        candidate(folder,data,before_refill,accepted,kind)
    portfolio=f.read_json(B/'run/B2_portfolio/portfolio-summary.json')
    paired.verify_portfolio(B/'run/B2_portfolio',portfolio,source,protocol['freeze'])
    assert [x['id'] for x in portfolio['trials']]==['via_default'] and portfolio['selected']['id']=='via_default'
    assert portfolio['stop_reason']=='insufficient remaining budget for another attempt and reserves'
    assert protocol['external_reserve_seconds']==40 and 60<=protocol['inner_allowance_seconds']<75
    strategy=f.read_json(B/'run/C_feedback/result.json');p.check_result(B/'run/C_feedback/result.json');central.append('C/final')
    p.check_parent_dsn_basis(B/'run/C_feedback',strategy);assert strategy['netclass_parent_dsn_basis']==p.parent_dsn_basis(B/'run/C_feedback')
    assert strategy['reference_routes_used_for_selection'] is False
    nets=s.zone_net_ids(original);assert sorted(nets)==strategy['zone_net_ids']
    best=B/'run/C_feedback/incumbent/candidate'/source.name;metrics=f.read_json(B/'run/C_feedback/incumbent/result.json')['metrics'];best_native=f.read_json(B/'run/C_feedback/incumbent/result.json')['native']
    trials=[];last_length=metrics['track_length_mm']
    assert len(strategy['trials'])==5 and strategy['improvements']==4
    # Runtime computes grouped proposals then an ordered singleton population once;
    # each accepted deletion preserves relative order of still-available members.
    initial=sx.read(best); grouped=s.proposals(initial,nets,protected,True);single=s.proposals(initial,nets,protected,False)
    expected_proposals=grouped+single
    for index,row in enumerate(strategy['trials']):
        folder=B/'run/C_feedback/trials'/row['id'];data=f.read_json(folder/'result.json')
        assert row['receipt']==str(folder/'result.json') and all(data[k]==row[k] for k in ('id','status','accepted'))
        assert data['base_candidate_sha256']==p.sha(best) and data['proposal']==expected_proposals[index]
        inherited=[x for x in strategy['steps'] if x.get('phase')==row['id']];assert inherited==data['steps']
        before_refill=s.delete_routes(sx.read(best),data['proposal']['route_ids'],nets,protected)
        passed=data['accepted'];assert passed is (index!=0)
        path,item=candidate(folder,data,before_refill,passed,'C/'+row['id'])
        trials.append({'id':row['id'],'status':row['status'],'accepted':passed,'base_candidate_sha256':data['base_candidate_sha256'],'candidate_sha256':item['candidate_sha256'],'proposal_kind':data['proposal']['kind'],'removed_route_count':len(data['proposal']['route_ids']),'native':item['native'],'length_mm':data.get('metrics',{}).get('track_length_mm'),'receipt_sha256':p.sha(folder/'result.json'),'all_steps_in_outer_cost':True})
        if passed:
            assert s._improves(data['metrics'],metrics,data['native'],best_native)
            assert data['metrics']['track_length_mm']<last_length
            best=path;metrics=data['metrics'];best_native=data['native'];last_length=metrics['track_length_mm']
    candidate(B/'run/C_feedback',strategy,sx.read(best),True,'C/final')
    assert strategy['metrics']==metrics
    final_rows=[]
    for old,new in zip(summary['results'],qualified['results']):
        assert old['id']==new['id'] and p.sha(Path(old['result']))==old['result_sha256']
        assert new['paired_charged_wall_seconds']==old['charged_wall_seconds'] and new['paired_charged_full_cpu_seconds']==old['charged_cpu_seconds']
        close(old['charged_wall_seconds'],old['invocation_wall_seconds']+summary['shared_overhead_wall_seconds'])
        close(old['charged_cpu_seconds'],old['invocation_cpu_seconds']+summary['shared_overhead_cpu_seconds'])
        addwall=max(0,outer['wall_seconds']-summary['batch_wall_seconds'])+15+1+spec['shared_original_qualification_cost']['wall_seconds']
        addcpu=max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds'])+15+1+spec['shared_original_qualification_cost']['full_cpu_seconds']
        close(new['charged_wall_seconds'],old['charged_wall_seconds']+addwall);close(new['charged_full_cpu_seconds'],old['charged_cpu_seconds']+addcpu)
        assert new['within_equal120_wall_full_cpu_caps'] is (max(new['charged_wall_seconds'],new['charged_full_cpu_seconds'])<=120)
        assert new['accepted'] is (old['accepted'] and new['within_equal120_wall_full_cpu_caps'])
        final_rows.append({k:new[k] for k in ('id','accepted','native_accepted','charged_wall_seconds','charged_full_cpu_seconds','within_equal120_wall_full_cpu_caps')})
    assert qualified['status']=='completed' and qualified['accepted'] is False and qualified['comparison_eligible'] is True
    assert qualified['comparisons']==paired.comparisons(qualified['results']) and len(qualified['comparisons'])==2
    assert all(x.get('C_dominates_with_1e_6mm_tolerance',x.get('pareto_improvement')) for x in qualified['comparisons'])
    byid={x['id']:x for x in final_rows};assert byid['B1']['accepted'] and byid['B2_portfolio']['accepted'] and not byid['B0']['accepted'] and byid['C_feedback']['accepted']
    assert byid['C_feedback']['charged_wall_seconds']<120 and byid['C_feedback']['charged_full_cpu_seconds']<120
    assert Q.joinpath('execution.json').is_file() and max(f.read_json(Q/'execution.json')[k] for k in ('wall_seconds','full_cpu_seconds'))<15
    assert {str(x.relative_to(ROOT)):witness(x) for x in (B,Q,O)}==inputs
    assert {str(x.relative_to(ROOT)):p.sha(x) for x in (R,SPEC)}==digests
    assert {name:p.sha(ROOT/name) for name in current_code}==current_code
    return dict(status='passed',review_scope='read-only consistency/replay of completed evidence; no new native qualification, no source/runtime execution',new_native_execution=False,new_solver_execution=False,source_hardware_sha256=source_hashes,source_whole_packet_exact=True,source_original_all67_routes_exact=True,source_native=counts(original_native),source_warning_full_signature_sha256=warning_digest,source_warning_types=sorted(set(x['type'] for x in original_native['findings'] if x['severity']=='warning')),source_original_diagnostic_receipt_sha256=p.sha(O/'result.json'),source_original_corrected_readback_sha256=p.sha(R),prospective_sha256=p.sha(SPEC),actual_qualification_sha256=p.sha(Q/'result.json'),tools_head=tools['git_head'],core_sha256=current_code,all_inputs_unchanged=True,input_inventory_sha256=sha_bytes(f.canonical(inputs).encode()),central_accepted_receipts=central,native_stages_checked=native_stages,other_process_journals_checked=process_stages,finals=out,trials=trials,own_incumbent_basis=strategy['netclass_parent_dsn_basis'],reference_route_selection=False,results=final_rows,comparison_eligible=True,comparisons=qualified['comparisons'],raw_valid_shortening_mm_vs_B1=636.9890979739067-metrics['track_length_mm'],raw_valid_shortening_mm_vs_B2_default=636.9890979739067-metrics['track_length_mm'],strong_three_variant_B2_superiority=False,unattempted_B2_variants=['via_low','via_high'],B2_stop_reason=portfolio['stop_reason'],external_reserve_seconds=40,stock_scope=qualified['stock_scope'],measured_outer_wall_seconds=outer['wall_seconds'],measured_outer_full_cpu_seconds=outer['full_cpu_seconds'],readback_allowance_charged_each_arm=15,original_qualification_charged_each_arm=spec['shared_original_qualification_cost'],startup_allowance_charged_each_arm=1,physical_electrical_or_battery_validation=False,limits=spec['limits'])

if __name__=='__main__':
    try:
        with patch.object(subprocess,'run',no_process),patch.object(subprocess,'Popen',no_process):result=run()
    except BaseException as exc:
        result={'status':'failed','exception':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'new_native_execution':False}
    result.update(review_wall_seconds=time.monotonic()-START,review_process_cpu_seconds=time.process_time()-CPU)
    path=OUT/(('actual-readback.json') if result['status']=='passed' else 'audit-failure-001.json')
    dump(path,result);print(json.dumps({k:result.get(k) for k in ('status','exception','message','review_wall_seconds','review_process_cpu_seconds')}))
    raise SystemExit(0 if result['status']=='passed' else 1)
