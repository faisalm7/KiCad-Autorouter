"""Unexecuted cumulative120 fallback: own retained signals + one selected-GND engine."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import argparse,hashlib,json,math,signal,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h,sexpr as sx,board_floor as g,native_connected as nc,preferences as pref,routing_scope as rs,thermal,thermal_geometry as geom,local_settings
from experiments.native_connected_pair_v1 import driver as pair
from experiments.native_contact_continuation_v1.actor import inventory,need
from experiments.placement_handoff_native_v1.driver import copy_bytes
OLD=ROOT/'.runs/nus-native-connected-contact120-001';PROBE=ROOT/'.runs/nus-native-connected-contact120-001-classifier'
TWO=ROOT/'.runs/nus-native-connected-contact120-002';TWO_OUTER=ROOT/'.runs/nus-native-connected-contact120-002-execution';TWO_LEAD=ROOT/'.runs/nus-native-connected-contact120-002-lead-execution'
POLICY='native-feedback-engine-fallback-v1';BOOT=1;FINAL=12;MIN_CHILD=50;LIMIT=64*1024**2

def check_outer_witness(out,data,spec,protocol_sha):
    identity={'schema':1,'kind':POLICY,'method':'selected-GND-completion-only','status':'completed','method_qualified':True,'accepted':False,'production_admitted':False,'budget_seconds':120,'cpu_budget_seconds':120,'bootstrap_allowance_seconds':1,'protocol_sha256':protocol_sha}
    need(all(type(data.get(k)) is type(v) and data[k]==v for k,v in identity.items()),'fallback identity differs')
    need(f.canonical(data['prior_costs'])==f.canonical(spec['prior_costs']),'prior charges differ')
    for label,charged,prior in [('new_wall_seconds','charged_wall_seconds','wall_seconds'),('new_full_cpu_seconds','charged_full_cpu_seconds','full_cpu_seconds')]:
        a=data[label];need(type(a) in (int,float) and math.isfinite(a) and a>=0 and data[charged]==spec['prior_costs'][prior]+BOOT+a,'fallback cumulative algebra differs')
    need(data['within_budget'] is True and max(data['charged_wall_seconds'],data['charged_full_cpu_seconds'])<120,'fallback cumulative cap differs')
    need(f.evidence_inventory(out)==data['completed_material'],'completed fallback changed')
    need(p.tool_manifest()==data['tools'] and p.tree_hash(Path(spec['source']).parent)==spec['source_hashes'],'source/current runtime changed')
    for key in ('code_sha256','retained_files'):
        for name,pin in spec[key].items():need(p.sha(ROOT/name)==pin,'frozen file changed: '+name)
    for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'retained evidence changed: '+name)

def _ground_readback(directory,data,source,hashes,preset,material):
    """Freeze any failed child; replay a complete DRC rejection without admission."""
    need(inventory(directory)==material,'new GND evidence changed')
    need(data['source']==str(source) and data.get('source_hashes')==hashes
        and p.tree_hash(directory/'snapshot')==hashes
        and pref.readback(pc.read_bytes(directory/'routing-preferences.json'))==pref.validate(preset),'ground source/preferences/snapshot differ')
    if data['accepted'] is not True and data['status']!='drc_rejected':
        need(inventory(directory)==material,'new GND incomplete evidence changed during input readback');return  # No stage claims.
    original=sx.read(source);candidate=directory/'candidate'/source.name
    need(data['candidate']==str(candidate),'ground candidate escaped owned output')
    p.verify_candidate_files(candidate,hashes,data['candidate_sha256'])
    need(rs.audit(original,sx.read(candidate),['GND'])==data['selected_net_audit'],'ground protected signals/scope differ')
    if data['accepted'] is True:need(p.check_result(directory/'result.json')['current'] is True,'new GND result stale')
    else:
        task=rs.task(original,['GND']);protected=rs.protected_routes(original,['GND'])
        p.check_preferences_record(directory,data);p.check_engine_profile_record(data,directory);p.check_resource_accounting(data)
        p.check_protected_import(directory,data,original,candidate,protected)
        p.check_native_edge_transport(directory,data);p.check_pour_evidence(directory,data,original,candidate)
        p.check_legacy_zone_evidence(directory,original,candidate,implementation=data['tools']['implementation_sha256'])
        prefill=p.transplant_routes(task,sx.read(directory/'imported.kicad_pcb'),protected=protected,policy='exact_non_uuid_lock_position_v2')
        before={**hashes,source.name:hashlib.sha256((sx.dump(prefill)+'\n').encode()).hexdigest()}
        source_native=f.check_drc_stage(directory,data,'source-drc',directory/'snapshot'/source.name,directory/'source-drc-input'/source.name,False,hashes,sandboxed=False)
        f.check_drc_stage(directory,data,'refill-drc',directory/'refill'/source.name,directory/'refill'/source.name,True,before,sandboxed=False)
        native=f.check_drc_stage(directory,data,'final-drc',candidate,directory/'final-drc-input'/source.name,False,{**hashes,source.name:data['candidate_sha256']},schematic_parity=True,sandboxed=False)
        expected=p.transplant_fill(prefill,sx.read(directory/'refill'/source.name))
        need(pc.read_bytes(candidate)==(sx.dump(expected)+'\n').encode() and native==data['native'] and source_native==data['source_drc']
            and p.sha(directory/'final-drc.json')==data['native_report_sha256'] and not p.native_accepted(native)
            and data['native_rejection_reasons']==p.native_rejection_reasons(native),'ground failed Native/import/refill/report differs')
        pair.check_source_warning_lineage(source_native,native)
        f.process_check(directory,data,'metrics',[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(directory/'metrics.json')])
        need(f.read_json(directory/'metrics.json')==data['metrics'] and all(p.sha(directory/name)==data[field] for name,field in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]),'ground failed metrics/export differs')
        local_settings.check_normal_policy(directory,data)
    need(inventory(directory)==material,'new GND evidence changed during readback')

def experiment(out,protocol,protocol_sha):
    need(Path(__file__).parent==ROOT/'experiments/native_feedback_engine_continuation_v1','promote/review/checkpoint before Native')
    need(out.parent==ROOT/'.runs' and not out.exists() and not out.is_symlink(),'fresh direct output required')
    need(p.sha(protocol)==protocol_sha,'prospective protocol differs');spec=f.read_json(protocol)
    need(spec['status']=='prospectively_frozen' and spec['policy']==POLICY and spec['actor_sha256']==p.sha(__file__) and spec['bootstrap_allowance_seconds']==BOOT and spec['cumulative_wall_full_cpu_seconds']==120 and spec['final_reserve_seconds']==FINAL and spec['minimum_assigned_child_seconds']==MIN_CHILD,'unfrozen fallback policy')
    need(all(not Path(n).is_absolute() and '..' not in Path(n).parts for group in ('code_sha256','prefixes','retained_files') for n in spec[group]),'project-relative fixed pins required')
    old=f.read_json(OLD/'result.json');child=OLD/'selected-route';first=f.read_json(child/'result.json');probe=f.read_json(PROBE/'result.json');two=f.read_json(TWO/'result.json');outer=f.read_json(TWO_OUTER/'result.json');lead=f.read_json(TWO_LEAD/'execution.json');previous=f.read_json(TWO/'prospective-pins.json')
    audit_path=ROOT/spec['prior_audit_receipt'];audit=f.read_json(audit_path);audit_execution=ROOT/spec['prior_audit_execution'];audit_outer=f.read_json(audit_execution);audit_cost=audit_outer['whole_reader_execution_cost'];prior=spec['prior_costs'];charged=[prior['wall_seconds'],prior['full_cpu_seconds']]
    need(p.sha(audit_path)==spec['prior_audit_sha256'] and p.sha(audit_execution)==spec['prior_audit_execution_sha256'] and audit['passed'] is True and audit_outer['result_sha256']==p.sha(audit_path) and audit['source_result_sha256']==p.sha(TWO/'result.json'),'actual002 independent readback/result/execution required')
    need(all(type(audit_cost[k]) in (int,float) and math.isfinite(audit_cost[k]) and audit_cost[k]>=0 for k in ('wall_seconds','full_cpu_seconds')) and audit_outer['startup_allowance_seconds']==2,'actual whole reader costs missing')
    minimum=[max(two['charged_wall_seconds'],outer['charged_wall_seconds'],lead['charged_wall_seconds'])+audit_cost['wall_seconds']+2,max(two['charged_full_cpu_seconds'],outer['charged_full_cpu_seconds'],lead['charged_full_cpu_seconds'])+audit_cost['full_cpu_seconds']+2]
    need(all(type(v) in (int,float) and math.isfinite(v) and bound<=v<119 for v,bound in zip(charged,minimum)),'prior omits actual001+002/reader/allowance')
    left=lambda:min(120-charged[0]-BOOT-(time.monotonic()-START),120-charged[1]-BOOT-(cpu()-CPU0))
    source=Path(spec['source']);hashes=spec['source_hashes'];tools=p.tool_manifest();old_tools=old['tools'];original=p.preflight(source)
    need(old_tools['git_head']=='7aeaac72f3f79e70cb0226275daadb326419ebdb' and all({k:v for k,v in row.items() if k!='git_head'}=={k:v for k,v in tools.items() if k!='git_head'} for row in (old_tools,two['tools'])),'only historical HEAD may differ; core/tool bytes must match')
    need(two['source']==str(source)==old['source'] and two['source_hashes']==hashes==old['source_hashes'] and len(hashes)==8,'exact original lineage differs')
    required=set(previous['prefixes'])|{str(x.relative_to(ROOT)) for x in (TWO,TWO_OUTER,TWO_LEAD,audit_path.parent)}
    need(required<=set(spec['prefixes']) and {str(audit_path.relative_to(ROOT)),str(audit_execution.relative_to(ROOT))}<=set(spec['retained_files']),'all prior whole prefixes/audit must be frozen')
    need(set(previous['code_sha256'])|set(tools['implementation_sha256'])|{'experiments/native_feedback_engine_continuation_v1/actor.py','experiments/native_feedback_engine_continuation_v1/run.py'}<=set(spec['code_sha256']),'complete current source/helper closure required')
    need(two['accepted'] is False and two['method_qualified'] is False and two['initial_failure']=='Rejected: no actual Native-validated contact repair','actual002 failure differs')
    for row in (outer,lead):need(row['process']['status']=='nonzero_exit' and row['process']['exit_code']==2 and row['process']['cleanup_complete'] is True,'prior outer did not cleanly reject')
    need(lead['source_current'] is True,'actual002 source not current')
    repair=f.read_json(TWO/'whole-validation/contact-repair/repair.json');geometry=f.read_json(TWO/'whole-validation/contact-repair/geometry.json')
    need(repair==two['contact_repair'] and repair['status']=='unsupported' and repair['validation_passed'] is False and not repair['trials'] and repair['proposal_receipt'] is None and not (TWO/'whole-final').exists() and not (TWO/'whole-validation/contact-repair/proposals.json').exists(),'contact stays unsupported; no old proposals/trials/final')
    out.mkdir();owner={};h.capture_destination(owner,out);copy_bytes(pc.inventory(source.parent,contents=True),out/'original',expected_parent_owner=owner)
    copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},out/'code',expected_parent_owner=owner)
    copy_bytes({n:pc.read_bytes(ROOT/n) for n in spec['code_sha256'] if n not in tools['implementation_sha256']},out/'helper-code',expected_parent_owner=owner)
    p.save_json(out/'prospective-pins.json',spec);job=None;entry=None;second=None;settings=None;settings_pin=None;warm_hashes=None;completed=None;ground_inventory=None
    warm=TWO/'whole-validation/candidate'/source.name
    record=dict(schema=1,kind=POLICY,method='selected-GND-completion-only',status='incomplete',accepted=False,production_admitted=False,method_qualified=False,budget_seconds=120,cpu_budget_seconds=120,bootstrap_allowance_seconds=BOOT,final_reserve_seconds=FINAL,protocol_sha256=protocol_sha,prior_costs=prior,source=str(source),source_hashes=hashes,tools=tools,steps=[],retained_stage_tools=old_tools,original_native=two['original_native'],original_native_report_sha256=two['original_native_report_sha256'],original_native_reused_from=str(TWO/'whole-validation/pristine-original.json'),prior_audit_receipt=str(audit_path),prior_audit_sha256=spec['prior_audit_sha256'],prior_minimum_wall_seconds=minimum[0],prior_minimum_full_cpu_seconds=minimum[1],scope='Own failed001+002 feedback fallback, not fresh independent B2; one selected-GND engine plus whole-original validation; contact remains unsupported; all prior actual work charged.')
    def stable():
        h.owned_destination(owner);need(left()>0,'cumulative120 exhausted')
        need(p.sha(protocol)==protocol_sha and p.tool_manifest()==tools and p.tree_hash(source.parent)==hashes and p.tree_hash(out/'original')==hashes,'source/protocol/runtime changed')
        need(p.tree_hash(out/'code')=={Path(n).name:pin for n,pin in tools['implementation_sha256'].items()},'captured core changed')
        need(p.tree_hash(out/'helper-code')=={n:pin for n,pin in spec['code_sha256'].items() if n not in tools['implementation_sha256']},'captured helpers changed')
        for key in ('code_sha256','retained_files'):
            for name,pin in spec[key].items():need(p.sha(ROOT/name)==pin,'frozen file changed: '+name)
        for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'old evidence changed: '+name)
        pc.inventory(out,max_bytes=LIMIT,max_files=6000,max_entries=12000)
        if settings is not None:need(p.sha(settings)==settings_pin,'owned GND preset changed')
        if warm_hashes is not None:need(p.tree_hash(out/'warm-source')==warm_hashes,'owned warm source changed')
        if completed is not None:need(f.evidence_inventory(out)==completed,'completed fallback changed')
    def retained():
        task=PROBE/'task'/source.name
        need(probe['tools']==old_tools and probe['eligibility_qualified'] is True and probe['status']=='completed' and p.sha(PROBE/'result.json')==old['classifier_sha256'] and f.evidence_inventory(PROBE)==probe['completed_evidence'],'retained own classifier differs')
        classification=nc.readback(PROBE,probe,source,task,PROBE/'refill'/source.name,PROBE/'candidate'/source.name,PROBE/'native.dsn')
        need(classification==old['classification'] and classification['inactive_names']==['GND'] and classification['active_names']==old['selected_names'] and len(classification['active_names'])==5,'exact fresh-original classification differs')
        need(pc.read_bytes(task)==(sx.dump(g.task_from_source(original))+'\n').encode() and p.tree_hash(task.parent)==old['task_hashes'],'retained classifier stripped task differs')
        pair._contact_child(child,first,task,old['task_hashes'],pref.validate(f.read_json(OLD/'route-preferences.json')),old['selected_names'])
        directory=TWO/'whole-validation';data={'steps':two['steps']}
        baseline=f.check_drc_stage(directory,data,'pristine-original',directory/'snapshot'/source.name,directory/'pristine-original-input'/source.name,False,hashes,schematic_parity=True)
        before={**hashes,source.name:p.sha(directory/'pre-refill.kicad_pcb')}
        saved=f.check_drc_stage(directory,data,'refill-drc',directory/'refill'/source.name,directory/'refill'/source.name,True,before)
        native=f.check_drc_stage(directory,data,'final-drc',warm,directory/'final-drc-input'/source.name,False,{**hashes,source.name:p.sha(warm)},schematic_parity=True)
        expected=p.transplant_fill(sx.read(directory/'pre-refill.kicad_pcb'),sx.read(directory/'refill'/source.name))
        need(pc.read_bytes(warm)==(sx.dump(expected)+'\n').encode() and p.immutable(expected)==p.immutable(original) and p.routes(expected)==p.routes(sx.read(Path(first['candidate']))),'owned warm source/original/fresh signal records differ')
        need(baseline==two['original_native'] and p.native_accepted(baseline) and baseline['warnings']==10 and native==two['whole_initial_native'] and thermal.sole_thermal(native) is not None and pair.warnings(native)==pair.warnings(baseline),'retained pristine/whole Native differs')
        need(p.sha(directory/'pristine-original.json')==two['original_native_report_sha256'] and p.sha(directory/'final-drc.json')==two['whole_initial_report_sha256'],'retained report pins differ')
        p.verify_candidate_files(warm,hashes,p.sha(warm));local_settings.check_normal_policy(directory,{'tools':two['tools'],'source_hashes':hashes,'steps':two['steps']})
        request=f.read_json(directory/'contact-repair/request.json');need(geometry['board_sha256']==p.sha(warm) and geometry['source_unchanged'] is True and geometry['finding']==thermal.sole_thermal(native) and request['candidate_files']==p.tree_hash(warm.parent),'retained failed contact context differs')
        f.process_check(directory/'contact-repair',data,'thermal-geometry',[*f.SANDBOX,str(p.c.PYTHON),'-B',str(directory/'contact-repair/worker.py'),str(directory/'contact-repair/input'/source.name),str(directory/'contact-repair/request.json'),str(directory/'contact-repair/geometry.json')])
        return baseline,native
    def final_readback():
        stable();baseline,_=retained()
        if second is not None:
            need(p.sha(out/'ground-route/result.json')==record['ground_receipt_sha256'] and f.read_json(out/'ground-route/result.json')==second,'new selected-GND receipt changed')
            _ground_readback(out/'ground-route',second,out/'warm-source'/source.name,warm_hashes,preset,ground_inventory)
        if entry is not None:
            native=pair._contact_phase_readback(entry,original,hashes);scope=rs.audit(sx.read(warm),sx.read(Path(entry['candidate'])),['GND'])
            need(scope==record['protected_signal_audit_final'],'final protected signal audit changed')
            local_settings.check_normal_policy(job.out,{'tools':tools,'source_hashes':hashes,'steps':job.steps})
            if record['method_qualified']:
                need(native==record['native'] and p.native_accepted(native) and pair.warnings(native)==pair.warnings(baseline),'whole original acceptance/warnings changed')
                f.process_check(job.out,{'steps':job.steps},'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',entry['candidate'],str(job.out/'metrics.json')])
                need(record['candidate_sha256']==p.sha(Path(entry['candidate'])) and record['native_report_sha256']==p.sha(job.out/'final-drc.json') and record['metrics']==f.read_json(job.out/'metrics.json') and record['metrics_sha256']==p.sha(job.out/'metrics.json'),'final hashes/metrics changed')
    def account():
        wall,full=time.monotonic()-START,cpu()-CPU0
        record.update(new_wall_seconds=wall,new_full_cpu_seconds=full,charged_wall_seconds=charged[0]+BOOT+wall,charged_full_cpu_seconds=charged[1]+BOOT+full,within_budget=left()>0,steps=[] if job is None else job.steps)
        record.update(cumulative_active002_reader_and_fallback_wall_seconds=27.294584+record['charged_wall_seconds'],cumulative_active002_reader_and_fallback_full_cpu_seconds=22.430367+record['charged_full_cpu_seconds'])
        if record['status']!='completed' or not record['within_budget']:record['method_qualified']=False
    try:
        stable();baseline,native=retained()
        finding=thermal.sole_thermal(native);owners=geom.uuid_index(sx.read(warm),sx);objects=[owners.get(i['uuid'],[]) for i in finding['items']]
        need(all(len(v)==1 for v in objects) and sorted(v[0][0] for v in objects)==['pad','zone'],'sole report targets not unique pad/zone')
        _,resolve=g.source_net_identity(sx.read(warm));need(all(resolve(sx.one(v[0],'net'))=='GND' for v in objects),'feedback target not exact skipped GND')
        warm_hashes=p.tree_hash(warm.parent);copy_bytes(pc.inventory(warm.parent,contents=True),out/'warm-source',expected_parent_owner=owner);warm_input=out/'warm-source'/source.name
        seconds=math.floor(left()-FINAL);record.update(assigned_child_seconds=seconds,engine_prework_allowance_seconds=10,existing_engine_native_reserve_seconds=10,existing_engine_grace_seconds=30,warm_source=str(warm_input),warm_source_hashes=warm_hashes,protected_signal_audit=rs.audit(sx.read(warm),sx.read(warm_input),['GND']))
        need(seconds>=MIN_CHILD,'insufficient existing40s engine reserve/prework plus12s final reserve')
        settings=out/'ground-preferences.json';preset={**pref.DEFAULTS,'scope':'selected_nets','nets':['GND'],'seconds':seconds,'profile':'completion-only','adapter':'both','guidance':'native','layers':'source_all'};pref.validate(preset)
        with settings.open('x') as stream:json.dump(preset,stream,sort_keys=True,allow_nan=False);stream.write('\n')
        settings_pin=p.sha(settings);second=p.route(warm_input,out/'ground-route',settings_path=settings);ground_inventory=inventory(out/'ground-route')
        record.update(ground_receipt_sha256=p.sha(out/'ground-route/result.json'),ground_status=second['status'],ground_accepted=second['accepted'],ground_inventory=ground_inventory)
        _ground_readback(out/'ground-route',second,warm_input,warm_hashes,preset,ground_inventory)
        need(second['accepted'] is True and p.native_accepted(second['native']) and p.check_result(out/'ground-route/result.json')['current'] is True,'selected-GND fallback rejected')
        need(second['source']==str(warm_input) and second['source_hashes']==warm_hashes and pref.readback(pc.read_bytes(out/'ground-route/routing-preferences.json'))==pref.validate(preset),'ground source/preferences differ')
        rs.audit(sx.read(warm),sx.read(Path(second['candidate'])),['GND']);stable()
        job=f.FloorJob(out/'whole-final',left(),left,protect_local_settings=True);copy_bytes(pc.inventory(source.parent,contents=True),job.out/'snapshot');copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},job.out/'code')
        tree=p.transplant_routes(g.task_from_source(original),sx.read(Path(second['candidate'])),protected=[],policy='exact_non_uuid_lock_position_v2');files=pc.inventory(source.parent,contents=True);files[source.name]=(sx.dump(tree)+'\n').encode();copy_bytes(files,job.out/'candidate');candidate=job.out/'candidate'/source.name;(job.out/'pre-refill.kicad_pcb').write_bytes(files[source.name])
        digest,final=p.validate_candidate(job,original,candidate,hashes,rs.protected_routes(sx.read(warm),['GND']),schematic_parity=True)
        saved=f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',job.out/'refill'/source.name,job.out/'refill'/source.name,True,{**hashes,source.name:p.sha(job.out/'pre-refill.kicad_pcb')})
        entry={'job':job,'candidate':str(candidate),'candidate_sha256':digest,'native':final,'saved_native':saved,'report_sha256':p.sha(job.out/'final-drc.json')};record.update(candidate=str(candidate),candidate_sha256=digest,native=final,native_report_sha256=entry['report_sha256'],protected_signal_audit_final=rs.audit(sx.read(warm),sx.read(candidate),['GND']))
        need(p.native_accepted(final) and pair.warnings(final)==pair.warnings(baseline),'fresh whole-original GND fallback failed')
        job.native('metrics','metrics',candidate,job.out/'metrics.json');metrics=f.read_json(job.out/'metrics.json');need(metrics['version']=='10.0.0' and type(metrics['vias']) is int and metrics['vias']>=0 and type(metrics['track_length_mm']) in (int,float) and math.isfinite(metrics['track_length_mm']) and metrics['track_length_mm']>=0,'actual final metrics invalid')
        record.update(metrics=metrics,metrics_sha256=p.sha(job.out/'metrics.json'),status='completed',method_qualified=True)
        final_readback();completed=f.evidence_inventory(out);record['completed_material']=completed
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',method_qualified=False,reason=type(exc).__name__+': '+str(exc),initial_failure=type(exc).__name__+': '+str(exc))
    return f.publish(out,record,stable,account,left,owned=lambda:h.owned_destination(owner),final_check=final_readback)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
    if not a.run_native:ap.error('explicit Native opt-in required')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    d=experiment(a.output,a.protocol,a.protocol_sha256);print(json.dumps({k:d[k] for k in ('status','method_qualified','charged_wall_seconds','charged_full_cpu_seconds')}));raise SystemExit(0 if d['method_qualified'] else 2)
