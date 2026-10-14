"""Narrow stored ArcDice low/high readback; uses shared validators only."""
import time
START=time.monotonic()
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import copy,hashlib,json,math,subprocess,traceback
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,config as c
from scripts import experiment_portfolio as m,experiment_paired as paired
D=Path(__file__).resolve().parent
OLD=ROOT/'.runs/arcdice-native-paired-complete-sch-003'
PREFIX=ROOT/'.runs/arcdice-b2-continuation-001'
HIGH=ROOT/'.runs/arcdice-b2-high-only-001'
Q1=ROOT/'.runs/arcdice-additive-comparison-001'
Q2=ROOT/'.runs/arcdice-additive-comparison-002'
SPEC=ROOT/'.runs/arcdice-b2-high-only-001-protocol.json'
def no_process(*a,**k):raise AssertionError('no subprocess/native/Git in readback')
def witness(root):return pc.inventory(root,max_bytes=96*1024**2,max_files=6000,max_entries=12000,with_directories=True)
def hashed(value):return hashlib.sha256(f.canonical(value).encode()).hexdigest()
def close(a,b):assert math.isclose(a,b,abs_tol=1e-8,rel_tol=0),(a,b)
def warn(native):return hashed([x for x in native['findings'] if x['severity']=='warning'])
def counts(native):return {k:native[k]for k in ('opens','blocking','warnings','exclusions')}
def native_argv(action,board,out,*extra):return [str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),action,str(board),str(out),*[str(x)for x in extra]]
def run():
    roots=(OLD,PREFIX,HIGH,Q1,Q2);inputs={str(x.relative_to(ROOT)):witness(x)for x in roots}
    spec=f.read_json(SPEC);before_spec=p.sha(SPEC);prefix=f.read_json(PREFIX/'portfolio/portfolio-summary.json');protocol=f.read_json(PREFIX/'portfolio/protocol.json');outer=f.read_json(PREFIX/'execution.json');high_outer=f.read_json(HIGH/'execution.json');qualified=f.read_json(Q2/'result.json');prior=f.read_json(ROOT/'.runs/arcdice-native-paired-complete-sch-003-qualification/result.json')
    source=Path(spec['source']);original=p.preflight(source);hashes=spec['freeze']['source_hashes'];protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    assert not protected and p.tree_hash(source.parent)==hashes
    original_record=f.read_json(ROOT/'.runs/arcdice-original-native-001/result.json');original_native=original_record['parity_native'];assert counts(original_native)=={'opens':0,'blocking':0,'warnings':26,'exclusions':0}
    assert p.tree_hash(ROOT/'.runs/arcdice-original-native-001/original')==original_record['original_hashes']
    core={n:p.sha(ROOT/n)for n in spec['freeze']['tools']['implementation_sha256']};assert core==spec['freeze']['tools']['implementation_sha256']
    for path,digest in spec['artifacts'].items():assert p.sha(Path(path))==digest
    m.verify_resume_basis(protocol['resume']);m.compatible_resume_freeze(protocol['freeze'],spec['freeze'])
    assert [x['id']for x in prefix['trials']]==['via_default','via_low'] and prefix['stop_reason']=='insufficient remaining budget for another attempt and reserves'
    assert outer['combined_active_wall_seconds']==outer['prior_entire_invocation']['wall_seconds']+outer['whole_new_wall_seconds']
    assert outer['combined_full_cpu_seconds']==outer['prior_entire_invocation']['full_cpu_seconds']+outer['whole_new_full_cpu_seconds']
    assert high_outer['protocol_sha256']==before_spec and high_outer['within_full120_caps'] is True
    for record in (outer,high_outer):assert record['process']['status']=='success'and record['process']['exit_code']==0 and record['process']['cleanup_complete'] is True and not record['process']['log_truncated']
    assert high_outer['whole_new_wall_seconds']<=spec['inherited_remaining_wall_seconds']
    for key in ('wall_seconds','full_cpu_seconds'):assert high_outer['already_committed_charge'][key]==spec['already_committed_charge'][key]
    high=f.read_json(HIGH/'trial/result.json');metric=high['metrics'];row=dict(index=2,id='via_high',assigned_seconds=spec['assigned_inner_seconds'],guidance_policy=None,result=str(HIGH/'trial/result.json'),result_sha256=p.sha(HIGH/'trial/result.json'),candidate=high['candidate'],candidate_sha256=high['candidate_sha256'],native_report_sha256=high['native_report_sha256'],vias=metric['vias'],length_mm=metric['track_length_mm'],eligible=True)
    m.verify_row(prefix['trials'][0],source,m.trial_freeze(protocol,prefix['trials'][0]));m.verify_row(row,source,spec['freeze'])
    assert high['accepted']is True and high['scoring_variant']=='via_high'
    task=copy.deepcopy(original);task[:]=[n for n in task if not isinstance(n,list)or not n or n[0]not in p.ROUTES or p.locked(n)]
    for z in sx.children(task,'zone'):z[:]=[n for n in z if not isinstance(n,list)or not n or n[0]not in p.DERIVED_ZONE]
    task_hash=hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest();finals=[]
    for kind,folder,accepted in [('via_low',PREFIX/'portfolio/02-via_low',False),('via_high',HIGH/'trial',True)]:
        data=f.read_json(folder/'result.json');candidate=folder/'candidate'/source.name;assert data['task_sha256']==task_hash and data['source_hashes']==hashes
        p.check_resource_accounting(data);p.verify_candidate_files(candidate,hashes,data['candidate_sha256']);assert p.immutable(sx.read(candidate))==p.immutable(original)
        source_native=f.check_drc_stage(folder,data,'source-drc',folder/'snapshot'/source.name,folder/'source-drc-input'/source.name,False,hashes,sandboxed=False);assert source_native==data['source_drc']
        for name,action,out,extra in [('export','export',folder/'task.dsn',(folder/'export-netclasses.json',)),('obstacles','obstacles',folder/'obstacles.json',()),('import','import',folder/'imported.kicad_pcb',(folder/'routes.ses',)),('metrics','metrics',folder/'metrics.json',()),('final-netclasses','netclasses',folder/'final-netclasses.json',())]:f.process_check(folder,data,name,native_argv(action,candidate,out,*extra))
        f.process_check(folder,data,'engine',p.engine_argv(folder,data['engine_budget']['argv']))
        before=p.transplant_routes(task,sx.read(folder/'imported.kicad_pcb'),protected=protected,policy='exact_non_uuid_lock_position_v2');expected=dict(hashes);expected[source.name]=hashlib.sha256((sx.dump(before)+'\n').encode()).hexdigest()
        refill=folder/'refill'/source.name;f.check_drc_stage(folder,data,'refill-drc',refill,refill,True,expected,sandboxed=False)
        assert (sx.dump(p.transplant_fill(before,sx.read(refill)))+'\n').encode()==candidate.read_bytes()
        expected=dict(hashes);expected[source.name]=data['candidate_sha256'];native=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/source.name,False,expected,schematic_parity=True,sandboxed=False)
        assert native==data['native']and p.sha(folder/'final-drc.json')==data['native_report_sha256']and warn(native)==warn(original_native)
        assert p.native_accepted(native)is accepted
        audit=p.audit_candidate_netclasses(candidate,protected,f.read_json(folder/'final-netclasses.json'))
        assert f.read_json(folder/'metrics.json')==data['metrics'];p.check_protected_import(folder,data,original,candidate,protected);p.check_pour_evidence(folder,data,original,candidate,correction=True)
        finals.append(dict(id=kind,receipt_sha256=p.sha(folder/'result.json'),candidate_sha256=data['candidate_sha256'],report_sha256=data['native_report_sha256'],native=counts(native),metrics=data['metrics'],warning_full_signature_sha256=warn(native),original_rules_and_immutable_exact=True,import_saved_refill_exact=True,complete_parity_bound=True,class_dimensions=audit['route_dimensions'],all9_processes_bound=True))
    assert qualified['status']=='completed'and qualified['accepted']is False and qualified['comparison_eligible']is True
    for old,new in zip(prior['results'],qualified['results']):
        assert old['id']==new['id']
        for key,cost in [('charged_wall_seconds','whole_new_wall_seconds'),('charged_full_cpu_seconds','whole_new_full_cpu_seconds')]:
            expected=old[key]+15
            if old['id']=='B2_portfolio':expected+=outer[cost]+2+high_outer[cost]
            close(new[key],expected)
        assert new['within_equal120_wall_full_cpu_caps']is(max(new['charged_wall_seconds'],new['charged_full_cpu_seconds'])<=120)
    assert qualified['strong_B2_selected']=='via_high'and qualified['actual_tuned_variants']==list(m.VARIANTS)
    assert qualified['comparisons']==paired.comparisons(qualified['results'])
    assert all(x.get('C_dominates_with_1e_6mm_tolerance',x.get('pareto_improvement'))for x in qualified['comparisons'])
    close(qualified['C_gain_vs_B2_mm'],metric['track_length_mm']-qualified['C_length_mm'])
    B2=next(x for x in qualified['results']if x['id']=='B2_portfolio');assert B2['selected']['candidate_sha256']==high['candidate_sha256']and B2['selected']['native_report_sha256']==high['native_report_sha256']
    failed=f.read_json(Q1/'result.json');assert failed['comparison_eligible']is False and failed['status']=='invalidated'and "'accepted'"in failed['reason']
    successful_exec=f.read_json(Q2/'execution.json');assert successful_exec['result_sha256']==p.sha(Q2/'result.json')
    failed_exec=f.read_json(Q1/'execution.json')
    assert {str(x.relative_to(ROOT)):witness(x)for x in roots}==inputs and p.sha(SPEC)==before_spec and p.tree_hash(source.parent)==hashes
    assert {n:p.sha(ROOT/n)for n in core}==core
    return dict(status='passed',new_native_execution=False,no_subprocesses=True,source_five_file_packet_exact=True,source_hardware_sha256=hashes,core_sha256=core,source_full_warning_signature_sha256=warn(original_native),finals=finals,old_default_receipt_sha256=prefix['trials'][0]['result_sha256'],actual_profiles=['via_default','via_low','via_high'],rejected_low_charged=True,no_completed_native_repeated=True,high_nominal_inner_seconds=spec['assigned_inner_seconds'],high_hard_wall_seconds=spec['inherited_remaining_wall_seconds'],high_measured_whole_wall_seconds=high_outer['whole_new_wall_seconds'],high_measured_whole_full_cpu_seconds=high_outer['whole_new_full_cpu_seconds'],results=[{k:x[k]for k in ('id','accepted','charged_wall_seconds','charged_full_cpu_seconds')}for x in qualified['results']],gain_mm=qualified['C_gain_vs_B2_mm'],strong_B2_selected='via_high',actual_qualified_receipt_sha256=p.sha(Q2/'result.json'),actual_qualification_helper_sha256=qualified['controller_sha256'],current_helper_sha256=p.sha(ROOT/'experiments/native_paired_v1/readback.py'),publication_fix_not_native_change=True,failed_publication=failed_exec,successful_publication=successful_exec,input_inventory_sha256=hashed(inputs),all_inputs_unchanged=True,metadata_correction=qualified['metadata_correction'],research_preparation_scope='Unsampled read-only source preparation/inline metadata syntax failure outside routing/audit execution; not claimed algorithm runtime.',physical_electrical_human_battery_validation=False)
if __name__=='__main__':
    try:
        with patch.object(subprocess,'run',no_process),patch.object(subprocess,'Popen',no_process):record=run()
    except BaseException as exc:record=dict(status='failed',error=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),new_native_execution=False)
    record.update(review_wall_seconds=time.monotonic()-START,review_lifetime_self_cpu_seconds=time.process_time(),review_children=0)
    filename='actual-readback.json'if record['status']=='passed'else'audit-failure-001.json'
    (D/filename).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:record.get(k)for k in ('status','error','message','review_wall_seconds','review_lifetime_self_cpu_seconds')}))
    raise SystemExit(0 if record['status']=='passed'else1)
