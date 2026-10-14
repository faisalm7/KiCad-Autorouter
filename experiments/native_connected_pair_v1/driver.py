"""Unexecuted two-arm NUS120 diagnostic; use run.py sequentially per arm."""
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
from autorouter import pipeline as p,floor_route as f,sexpr as sx,board_floor as g
from autorouter import handoff as h,placement_clearance as pc,preferences as pref,native_connected as nc
from experiments.native_connected_v1 import driver as classifier
from experiments.placement_handoff_native_v1.driver import copy_bytes
from scripts.experiment_quality import selected_source
SECONDS=120;BOOTSTRAP=1;FINAL_RESERVE=20
def remaining():return min(SECONDS-BOOTSTRAP-(time.monotonic()-START),SECONDS-BOOTSTRAP-(cpu()-CPU0))
def warnings(native):return sorted(f.canonical(x) for x in native['findings'] if x['severity']=='warning')

def check_source_warning_lineage(source_native,final_native):
    # source-drc has no schematic parity; the final fullSCH check can add
    # inherited schematic findings. None of the ordinary source warnings may
    # disappear. Adoption still requires exact fresh whole-original fullSCH
    # warning equality in _contact_treatment/_contact_replay.
    if not set(warnings(source_native))<=set(warnings(final_native)):
        raise p.Rejected('contact child removed an original source warning')

def _contact_child(child,data,task,task_hashes,settings,names):
    """Shared rejected-child checks; never turn its receipt into an accepted one."""
    from autorouter import local_settings,thermal
    candidate=child/'candidate'/task.name;original=sx.read(task)
    if (data['source']!=str(task) or data['source_hashes']!=task_hashes or data['scope']!='selected_nets'
            or pref.readback(pc.read_bytes(child/'routing-preferences.json'))!=pref.validate(settings)
            or p.tree_hash(child/'snapshot')!=task_hashes):raise p.Rejected('contact child task/preferences/snapshot differ')
    p.verify_candidate_files(candidate,task_hashes,data['candidate_sha256'])
    p.check_preferences_record(child,data);p.check_engine_profile_record(data,child);p.check_resource_accounting(data)
    p.check_native_edge_transport(child,data);p.check_pour_evidence(child,data,original,candidate)
    p.check_legacy_zone_evidence(child,original,candidate,implementation=data['tools']['implementation_sha256'])
    imported=sx.read(child/'imported.kicad_pcb')
    prefill=p.transplant_routes(original,imported,protected=[],policy='exact_non_uuid_lock_position_v2')
    before={**task_hashes,task.name:hashlib.sha256((sx.dump(prefill)+'\n').encode()).hexdigest()}
    source_native=f.check_drc_stage(child,data,'source-drc',child/'snapshot'/task.name,child/'source-drc-input'/task.name,False,task_hashes,sandboxed=False)
    saved=f.check_drc_stage(child,data,'refill-drc',child/'refill'/task.name,child/'refill'/task.name,True,before,sandboxed=False)
    native=f.check_drc_stage(child,data,'final-drc',candidate,child/'final-drc-input'/task.name,False,{**task_hashes,task.name:data['candidate_sha256']},schematic_parity=True,sandboxed=False)
    expected=p.transplant_fill(prefill,sx.read(child/'refill'/task.name))
    if (pc.read_bytes(candidate)!=(sx.dump(expected)+'\n').encode() or native!=data['native']
            or p.sha(child/'final-drc.json')!=data['native_report_sha256'] or source_native!=data['source_drc']):raise p.Rejected('contact child source/import/refill/report/warnings differ')
    check_source_warning_lineage(source_native,native)
    if data['accepted'] is True:
        if p.check_result(child/'result.json')['current'] is not True:raise p.Rejected('accepted contact child stale')
    elif data['status']!='drc_rejected' or thermal.sole_thermal(native) is None:
        raise p.Rejected('contact requires a complete accepted child or sole-thermal rejected child')
    if any(step['cleanup_complete'] is not True for step in data['steps']):raise p.Rejected('contact child cleanup incomplete')
    f.process_check(child,data,'metrics',[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(child/'metrics.json')])
    if f.read_json(child/'metrics.json')!=data['metrics'] or any(p.sha(child/name)!=data[field] for name,field in (('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256'))):raise p.Rejected('contact child metrics/raw/task hashes differ')
    local_settings.check_normal_policy(child,data)
    if f.canonical(f.read_json(child/'result.json'))!=f.canonical(data):raise p.Rejected('contact child receipt changed')
    return candidate


def _contact_proof(state):
    from autorouter import thermal_contact
    repair=state['repair'];directory=state['whole'].out/'contact-repair'
    if (repair.get('experimental_contact') is not True or repair.get('proposal_policy')!=thermal_contact.POLICY
            or repair.get('final_refill_validation_required') is not True or repair.get('routing_accepted') is not False
            or repair.get('whole_body_certificate_qualified') is not False or repair.get('proposal_scene_qualified') is not False
            or repair.get('geometry_receipt')!=str(directory/'geometry.json')
            or repair.get('proposal_receipt')!=str(directory/'proposals.json')):raise p.Rejected('explicit speculative contact policy/proof missing or changed')
    request=f.read_json(directory/'request.json');geometry=f.read_json(directory/'geometry.json');proposals=f.read_json(directory/'proposals.json')
    if request.get('mode')!=thermal_contact.POLICY or geometry.get('mode')!=thermal_contact.POLICY or proposals.get('policy')!=thermal_contact.POLICY:raise p.Rejected('contact request/geometry/proposal mode differs')
    base=Path(state['phases']['whole']['candidate'])
    if request['candidate_files']!=p.tree_hash(base.parent) or p.tree_hash(directory/'input')!=request['candidate_files'] or request['final_drc_sha256']!=p.sha(state['whole'].out/'final-drc.json') or geometry['board_sha256']!=p.sha(base):raise p.Rejected('contact geometry/report/owned input binding changed')
    from autorouter import thermal
    if geometry.get('finding')!=thermal.sole_thermal(state['phases']['whole']['native']) or geometry.get('project_sha256')!=p.sha(base.with_suffix('.kicad_pro')):raise p.Rejected('contact observation report/project differs')
    thermal_contact.fill_binding(state['base_tree'],geometry,sx)
    f.process_check(directory,{'steps':state['whole'].steps},'thermal-geometry',[*f.SANDBOX,str(p.c.PYTHON),'-B',str(directory/'worker.py'),str(directory/'input'/base.name),str(directory/'request.json'),str(directory/'geometry.json')])
    thermal_contact.verify_proposals(geometry,proposals,remaining_seconds=state['_remaining'])


def _contact_phase_readback(entry,original,hashes):
    job=entry['job'];candidate=Path(entry['candidate']);data={'steps':job.steps}
    prefill=sx.read(job.out/'pre-refill.kicad_pcb')
    saved=f.check_drc_stage(job.out,data,'refill-drc',job.out/'refill'/candidate.name,job.out/'refill'/candidate.name,True,{**hashes,candidate.name:p.sha(job.out/'pre-refill.kicad_pcb')})
    native=f.check_drc_stage(job.out,data,'final-drc',candidate,job.out/'final-drc-input'/candidate.name,False,{**hashes,candidate.name:entry['candidate_sha256']},schematic_parity=True)
    if (native!=entry['native'] or saved!=entry['saved_native'] or p.sha(job.out/'final-drc.json')!=entry['report_sha256']
            or pc.read_bytes(candidate)!=(sx.dump(p.transplant_fill(prefill,sx.read(job.out/'refill'/candidate.name)))+'\n').encode()
            or p.immutable(sx.read(candidate))!=p.immutable(original)):raise p.Rejected('contact whole-original phase changed')
    p.verify_candidate_files(candidate,hashes,entry['candidate_sha256'])
    return native


def _contact_treatment(state,record,out,source,original,hashes,task,child,child_record,settings_data,tools,*,remaining_seconds=None):
    from autorouter import thermal
    left=remaining if remaining_seconds is None else remaining_seconds
    if not callable(left):raise p.Rejected('contact shared remaining budget must be callable')
    state['_remaining']=left
    if state['spec'].get('experimental_contact') is not True:raise p.Rejected('contact mode not prospectively enabled')
    if child_record.get('tools')!=tools:raise p.Rejected('fresh contact child tool/code differs')
    state.update(child=child,child_record=child_record,task=task,settings=settings_data,jobs=[],phases={})
    _contact_child(child,child_record,task,record['task_hashes'],settings_data,record['selected_names'])
    def job(name):
        value=f.FloorJob(out/name,left(),left,protect_local_settings=True);state['jobs'].append(value)
        copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},value.out/'code')
        copy_bytes(pc.inventory(source.parent,contents=True),value.out/'snapshot')
        return value
    def validate(value,tree,key):
        files=pc.inventory(source.parent,contents=True);files[source.name]=(sx.dump(tree)+'\n').encode();copy_bytes(files,value.out/'candidate')
        candidate=value.out/'candidate'/source.name;(value.out/'pre-refill.kicad_pcb').write_bytes(files[source.name])
        entry={'job':value,'candidate':str(candidate)};state['phases'][key]=entry
        digest,native=p.validate_candidate(value,original,candidate,hashes,[],schematic_parity=True)
        entry.update(candidate_sha256=digest,native=native,report_sha256=p.sha(value.out/'final-drc.json'))
        entry['saved_native']=f.check_drc_stage(value.out,{'steps':value.steps},'refill-drc',value.out/'refill'/source.name,value.out/'refill'/source.name,True,{**hashes,source.name:p.sha(value.out/'pre-refill.kicad_pcb')})
        _contact_phase_readback(entry,original,hashes);return candidate,native
    whole=job('whole-validation');state['whole']=whole
    baseline=whole.drc('pristine-original',whole.out/'snapshot'/source.name,schematic_parity=True)
    record.update(original_native=baseline,original_native_report_sha256=p.sha(whole.out/'pristine-original.json'),original_warning_signatures=warnings(baseline))
    if not p.native_accepted(baseline) or baseline['warnings']!=10:raise p.Rejected('contact pristine original Native baseline failed')
    tree=p.transplant_routes(sx.read(task),sx.read(Path(child_record['candidate'])),protected=[],policy='exact_non_uuid_lock_position_v2')
    candidate,native=validate(whole,tree,'whole');state['base_tree']=sx.read(candidate)
    if warnings(native)!=warnings(baseline):raise p.Rejected('contact whole candidate inherited warnings changed')
    record.update(whole_initial_native=native,whole_initial_report_sha256=p.sha(whole.out/'final-drc.json'))
    if not p.native_accepted(native):
        if thermal.sole_thermal(native) is None:raise p.Rejected('whole-original candidate is not sole thermal')
        repair=thermal.attempt_repair(whole,original,candidate,hashes,[],native,
            report_path=whole.out/'final-drc.json',binding_path=whole.out/'final-drc-binding.json',
            remaining_seconds=lambda:max(0,left()-6),out=whole.out/'contact-repair',experimental_contact=True)
        state['repair']=repair;record['contact_repair']=repair
        if repair.get('validation_passed') is not True or repair.get('candidate') is None:raise p.Rejected('no actual Native-validated contact repair')
        _contact_proof(state)
        repaired=sx.read(Path(repair['candidate']));base_routes=p.routes(state['base_tree']);after=p.routes(repaired)
        if (p.sha(repair['candidate'])!=repair['candidate_sha256'] or p.immutable(repaired)!=p.immutable(original)
                or after[:len(base_routes)]!=base_routes or len(after)!=len(base_routes)+1 or after[-1][0]!='segment'):
            raise p.Rejected('contact repair must append exactly one segment with original fixed intent')
        state['added_track']=after[-1];state['repaired_tree']=repaired
        _,resolve=g.source_net_identity(repaired)
        if resolve(sx.one(after[-1],'net'),owner=after[-1]) not in record['classification']['inactive_names']:raise p.Rejected('contact segment not on the skipped connected net')
        tree=p.transplant_routes(sx.read(task),repaired,protected=[],policy='exact_non_uuid_lock_position_v2')
    final_job=job('whole-final');candidate,native=validate(final_job,tree,'final')
    record.update(candidate=str(candidate),candidate_sha256=p.sha(candidate),native=native,native_report_sha256=p.sha(final_job.out/'final-drc.json'))
    if not p.native_accepted(native) or warnings(native)!=warnings(baseline):raise p.Rejected('fresh emitted contact candidate failed original Native')
    final_job.native('metrics','metrics',candidate,final_job.out/'metrics.json');metrics=f.read_json(final_job.out/'metrics.json')
    if metrics.get('version')!='10.0.0' or type(metrics.get('vias')) is not int or metrics['vias']<0 or type(metrics.get('track_length_mm')) not in (int,float) or not math.isfinite(metrics['track_length_mm']) or metrics['track_length_mm']<0:raise p.Rejected('invalid actual contact final metrics')
    record.update(metrics=metrics,metrics_sha256=p.sha(final_job.out/'metrics.json'),contact_candidate_native_validated=True,contact_control_qualified='added_track' not in state)
    if 'added_track' in state:
        record['contact_control']={'status':'not_run','reason':'less than six seconds of whole120 budget remain'}
        if left()<6:raise p.Rejected('fresh contact candidate valid but removal control reserve exhausted')
        negative=job('contact-negative');bad=sx.read(candidate)
        matches=[node for node in p.routes(bad) if node==state['added_track']]
        if len(matches)!=1:raise p.Rejected('added contact segment identity ambiguous')
        bad.remove(matches[0]);_,invalid=validate(negative,bad,'negative')
        finding=thermal.sole_thermal(invalid);original_finding=thermal.sole_thermal(state['phases']['whole']['native'])
        if finding is None or finding!=original_finding or warnings(invalid)!=warnings(baseline):raise p.Rejected('contact removal did not reproduce exact sole thermal under original Native')
        record.update(contact_control_qualified=True,contact_control={'status':'native_rejected','candidate_sha256':state['phases']['negative']['candidate_sha256'],'native':invalid,'report_sha256':state['phases']['negative']['report_sha256']})
    record.update(status='completed',method_qualified=True)


def _contact_replay(state,record,original,hashes,tools):
    from autorouter import local_settings
    if 'child' not in state:return
    if p.sha(state['child']/'result.json')!=record['child_receipt_sha256']:raise p.Rejected('contact child receipt pin differs')
    _contact_child(state['child'],state['child_record'],state['task'],record['task_hashes'],state['settings'],record['selected_names'])
    for entry in state['phases'].values():
        if 'candidate_sha256' in entry:_contact_phase_readback(entry,original,hashes)
    for job in state['jobs']:
        local_settings.check_normal_policy(job.out,{'tools':tools,'source_hashes':hashes,'steps':job.steps})
        for step in job.steps:
            command=step['argv'][len(f.SANDBOX):] if step['argv'][:len(f.SANDBOX)]==f.SANDBOX else step['argv']
            if command[:3]!=[str(p.c.CLI),'pcb','drc']:continue
            cwd=Path(step['cwd']);binding=f.read_json(cwd/(step['name']+'-binding.json'))
            p.check_drc_project(hashes,binding['before'],Path(binding['input']).name,saved=True)
            f.check_drc_stage(cwd,{'steps':job.steps},step['name'],Path(binding['source']),Path(binding['input']),binding['saved'],binding['before'],schematic_parity=step['name'] in ('pristine-original','final-drc'))
    if 'whole' in state:
        whole=state['whole'];native=f.check_drc_stage(whole.out,{'steps':whole.steps},'pristine-original',whole.out/'snapshot'/Path(record['source']).name,whole.out/'pristine-original-input'/Path(record['source']).name,False,hashes,schematic_parity=True)
        if native!=record['original_native'] or p.sha(whole.out/'pristine-original.json')!=record['original_native_report_sha256']:raise p.Rejected('contact pristine baseline changed')
    if 'repair' in state:
        repair=state['repair'];directory=state['whole'].out/'contact-repair'
        if f.read_json(directory/'repair.json')!=repair:raise p.Rejected('contact repair receipt changed')
        if repair.get('validation_passed') is True:
            _contact_proof(state)
            if p.sha(repair['candidate'])!=repair['candidate_sha256']:raise p.Rejected('contact repaired candidate changed')
    if record['method_qualified']:
        final=state['phases']['final'];job=final['job'];candidate=Path(final['candidate'])
        f.process_check(job.out,{'steps':job.steps},'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(job.out/'metrics.json')])
        if (record['native']!=final['native'] or not p.native_accepted(final['native']) or warnings(final['native'])!=record['original_warning_signatures']
                or record['candidate_sha256']!=p.sha(candidate) or record['native_report_sha256']!=p.sha(job.out/'final-drc.json')
                or f.read_json(job.out/'metrics.json')!=record['metrics'] or p.sha(job.out/'metrics.json')!=record['metrics_sha256']
                or record['contact_control_qualified'] is not True):raise p.Rejected('final contact native/metrics/control proof changed')


def check_outer_witness(out,record,method,protocol_sha,spec):
    """Check byte continuity to the actor's completed native proof; no native rerun."""
    identity={'schema':1,'kind':'exposed-NUS-native-connected-selected-seam-diagnostic',
        'method':method,'status':'completed','accepted':False,'method_qualified':True,
        'production_admitted':False,'within_budget':True,'protocol_sha256':protocol_sha,
        'budget_seconds':120,'cpu_budget_seconds':120,'bootstrap_allowance_seconds':1,
        'final_reserve_seconds':20}
    for key,value in identity.items():
        if type(record.get(key)) is not type(value) or record[key]!=value:
            raise p.Rejected('outer actor identity/cap differs: '+key)
    for raw,charged in [('wall_seconds','charged_wall_seconds'),('total_cpu_seconds','charged_full_cpu_seconds')]:
        a,b=record.get(raw),record.get(charged)
        if (type(a) not in (int,float) or type(b) not in (int,float)
                or not math.isfinite(a) or not math.isfinite(b) or a<0 or b>120 or b!=a+BOOTSTRAP):
            raise p.Rejected('outer actor accounting differs: '+charged)
    probe=out.parent/(out.name+'-classifier')
    if record.get('classifier')!=str(probe) or p.sha(probe/'result.json')!=record.get('classifier_sha256'):
        raise p.Rejected('outer classifier receipt differs')
    if f.evidence_inventory(probe)!=record.get('classifier_material'):
        raise p.Rejected('outer classifier material changed')
    if f.evidence_inventory(out)!=record.get('completed_material'):
        raise p.Rejected('outer completed actor material changed')
    source=Path(spec['source'])
    if (record.get('source')!=str(source) or record.get('source_hashes')!=spec['source_hashes']
            or p.tree_hash(source.parent)!=spec['source_hashes']):
        raise p.Rejected('outer pristine source changed')
    if p.tool_manifest()!=record.get('tools'):raise p.Rejected('outer tool/code/HEAD changed')
    for name,pin in spec['code_sha256'].items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('outer frozen implementation changed: '+name)

def experiment(method,out,protocol_path,protocol_sha):
    if method not in ('all-active','native-connected','native-connected-contact') or out.parent!=ROOT/'.runs' or out.exists() or out.is_symlink():raise p.Rejected('fixed method and fresh direct .runs output required')
    if p.sha(protocol_path)!=protocol_sha:raise p.Rejected('prospective protocol pin differs')
    spec=f.read_json(protocol_path)
    if spec['parent_wall_full_cpu_seconds']!=120 or spec['final_reserve_seconds']!=20:raise p.Rejected('fixed parent budget/reserve differs')
    for name,pin in spec['code_sha256'].items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('frozen implementation differs: '+name)
    if p.sha(Path(__file__))!=spec['driver_sha256']:raise p.Rejected('frozen harness differs')
    source,family=selected_source('nus-usb-led');original=p.preflight(source);hashes=p.tree_hash(source.parent)
    if str(source)!=spec['source'] or hashes!=spec['source_hashes']:raise p.Rejected('pristine fixed source differs')
    tools=p.tool_manifest();out.mkdir();owner={};h.capture_destination(owner,out)
    probe=out.parent/(out.name+'-classifier');child=out/'selected-route';final_job=None;child_record=None;child_evidence=None;completed=None;settings=None;settings_pin=None;contact_state={'spec':spec}
    record=dict(schema=1,kind='exposed-NUS-native-connected-selected-seam-diagnostic',method=method,status='incomplete',accepted=False,method_qualified=False,production_admitted=False,
        budget_seconds=120,cpu_budget_seconds=120,bootstrap_allowance_seconds=BOOTSTRAP,final_reserve_seconds=20,protocol_sha256=protocol_sha,source=str(source),source_hashes=hashes,family=family,tools=tools,
        scope='Fresh classifier and selected routing per arm; whole original-rule final validation. Neither selected child receipt nor this diagnostic creates a shipped whole-routing receipt. Exposed NUS only; tunedB2/C remain separate.')
    if method=='native-connected-contact':
        prior=spec['prior_pilot_costs']
        if any(prior.get(key)!=value for key,value in {'active002_wall_seconds':23.452824,'active002_full_cpu_seconds':18.648718,'shared_reader_wall_seconds':1.841760,'shared_reader_full_cpu_seconds':1.781649,'reader_allowance_seconds':2}.items()):raise p.Rejected('disclosed prior exploration costs differ')
        record.update(prior_pilot_costs=prior,contact_experimental=True,contact_finalization_reserve_seconds=6,
            scope='Fresh exposed NUS120 C diagnostic: own classifier/active-only routing plus explicit speculative sole-thermal contact. Prior pilots disclosed separately; strongest tunedB2/C remain separate conditions. No production, confirmatory or general superiority claim.')
    def stable():
        h.owned_destination(owner)
        if remaining()<=0:raise p.Rejected('whole120 wall/fullCPU cap exhausted')
        if p.sha(protocol_path)!=protocol_sha or p.tool_manifest()!=tools or p.tree_hash(source.parent)!=hashes:raise p.Rejected('protocol/runtime/pristine source changed')
        if p.sha(Path(__file__))!=spec['driver_sha256']:raise p.Rejected('frozen harness changed')
        for name,pin in spec['code_sha256'].items():
            if p.sha(ROOT/name)!=pin:raise p.Rejected('frozen implementation changed')
        if settings is not None and p.sha(settings)!=settings_pin:raise p.Rejected('owned preferences changed')
        if child_evidence is not None and f.evidence_inventory(child)!=child_evidence:raise p.Rejected('retained child evidence changed')
        if completed is not None and f.evidence_inventory(out)!=completed:raise p.Rejected('completed parent evidence changed')
    def account():
        wall,full_cpu=time.monotonic()-START,cpu()-CPU0
        record.update(wall_seconds=wall,total_cpu_seconds=full_cpu,charged_wall_seconds=wall+BOOTSTRAP,charged_full_cpu_seconds=full_cpu+BOOTSTRAP,within_budget=remaining()>0)
        if method=='native-connected-contact':
            record.update(steps=[step for job in contact_state.get('jobs',[]) for step in job.steps],cumulative_active002_reader_and_fresh_wall_seconds=23.452824+1.841760+2+wall+BOOTSTRAP,cumulative_active002_reader_and_fresh_full_cpu_seconds=18.648718+1.781649+2+full_cpu+BOOTSTRAP)
            record['exploration_accounting_scope']='Prior active002 plus sharedreader and2s allowance plus this fresh attempt; pair001/setup and old B2/pruningC costs separately retained. No full-history/first-attempt/new120 rescue claim.'
        elif final_job is not None:record['steps']=final_job.steps
        if record['status']!='completed' or not record['within_budget']:record['method_qualified']=False
    def classifier_readback():
        data=f.read_json(probe/'result.json')
        if data['status']!='completed' or data['eligibility_qualified'] is not True or data['source_hashes']!=hashes or data['tools']!=tools:raise p.Rejected('own classifier incomplete/stale')
        if f.evidence_inventory(probe)!=data['completed_evidence']:raise p.Rejected('classifier completed evidence changed')
        task=probe/'task'/source.name
        classification=nc.readback(probe,data,source,task,probe/'refill'/source.name,probe/'candidate'/source.name,probe/'native.dsn')
        expected=(sx.dump(g.task_from_source(original))+'\n').encode()
        if pc.read_bytes(task)!=expected or p.routes(sx.read(task)) or any(sx.children(z,k) for z in sx.children(sx.read(task),'zone') for k in p.DERIVED_ZONE):raise p.Rejected('classifier task contains route/fill leak or altered source')
        task_hashes={**hashes,source.name:hashlib.sha256(expected).hexdigest()}
        if p.tree_hash(task.parent)!=task_hashes or classification['all_names']!=spec['all_names'] or len(classification['active_names'])!=5 or classification['inactive_names']!=['GND']:raise p.Rejected('fixed NUS task/net population differs')
        return task,task_hashes,classification,data
    def final_readback():
        stable()
        if method=='native-connected-contact':
            if 'classifier_sha256' in record:
                task,task_hashes,classification,_=classifier_readback()
                if classification!=record['classification'] or task_hashes!=record['task_hashes'] or classification['active_names']!=record['selected_names'] or p.sha(probe/'result.json')!=record['classifier_sha256']:raise p.Rejected('contact classifier/task/selection changed')
            _contact_replay(contact_state,record,original,hashes,tools);stable();return
        if record['method_qualified']:
            task,task_hashes,classification,probe_record=classifier_readback()
            names=classification['all_names'] if method=='all-active' else classification['active_names']
            if p.sha(probe/'result.json')!=record['classifier_sha256'] or classification!=record['classification'] or task_hashes!=record['task_hashes'] or names!=record['selected_names']:raise p.Rejected('recorded classifier/task/selection changed')
            expected_pref=pref.validate({**dict(pref.DEFAULTS),'scope':'selected_nets','nets':names,'seconds':record['assigned_child_seconds'],'adapter':'both','profile':'completion-only','guidance':'native','layers':'source_all'})
            if pref.resolve(pref.load(settings))!=expected_pref or pref.readback(pc.read_bytes(child/'routing-preferences.json'))!=expected_pref or child_record['source_hashes']!=task_hashes or child_record['source']!=str(task):raise p.Rejected('final owned/child task/preferences differ')
            if p.sha(child/'result.json')!=record['child_receipt_sha256']:raise p.Rejected('recorded child receipt pin differs')
            if p.check_result(child/'result.json')['current'] is not True or f.read_json(child/'result.json')!=child_record:raise p.Rejected('accepted selected child changed')
            if child_record['accepted'] is not True:raise p.Rejected('selected child was not accepted')
            pristine=f.check_drc_stage(final_job.out,{'steps':final_job.steps},'pristine-original',source,final_job.out/'pristine-original-input'/source.name,False,hashes,schematic_parity=True)
            if pristine!=record['original_native'] or p.sha(final_job.out/'pristine-original.json')!=record['original_native_report_sha256']:raise p.Rejected('pristine original Native/warnings proof differs')
            final=Path(record['candidate']);before={**hashes,source.name:record['pre_final_candidate_sha256']}
            saved=f.check_drc_stage(final_job.out,{'steps':final_job.steps},'refill-drc',final_job.out/'refill'/source.name,final_job.out/'refill'/source.name,True,before)
            if saved!=record['saved_refill_native'] or p.sha(final_job.out/'refill-drc.json')!=record['saved_refill_report_sha256']:raise p.Rejected('saved native report changed')
            result=f.check_drc_stage(final_job.out,{'steps':final_job.steps},'final-drc',final,final_job.out/'final-drc-input'/source.name,False,{**hashes,source.name:record['candidate_sha256']},schematic_parity=True)
            if result!=record['native'] or p.sha(final_job.out/'final-drc.json')!=record['native_report_sha256']:raise p.Rejected('whole original final report differs')
            expected=p.transplant_fill(sx.parse(pc.read_bytes(out/'pre-final.kicad_pcb').decode()),sx.read(final_job.out/'refill'/source.name))
            if pc.read_bytes(final)!=(sx.dump(expected)+'\n').encode():raise p.Rejected('saved-refill/original-shell provenance differs')
            p.verify_candidate_files(final,hashes,record['candidate_sha256'])
            if p.immutable(sx.read(final))!=p.immutable(original) or not p.native_accepted(result) or warnings(result)!=record['original_warning_signatures']:raise p.Rejected('whole original design/native/warnings changed')
            if f.read_json(final_job.out/'metrics.json')!=record['metrics'] or p.sha(final_job.out/'metrics.json')!=record['metrics_sha256']:raise p.Rejected('final metrics changed')
        stable()
    try:
        stable()
        if probe.exists() or probe.is_symlink():raise p.Rejected('fresh independent classifier output required')
        classifier.experiment(probe)  # New60s classifier, all actual cost paid by this120s parent.
        task,task_hashes,classification,probe_record=classifier_readback()
        names=classification['all_names'] if method=='all-active' else classification['active_names']
        child_seconds=math.floor(remaining()-FINAL_RESERVE)
        if child_seconds<5:raise p.Rejected('insufficient own child budget plus original-final reserve')
        settings=out/'route-preferences.json';settings_data={**dict(pref.DEFAULTS),'scope':'selected_nets','nets':names,'seconds':child_seconds,'adapter':'both','profile':'completion-only','guidance':'native','layers':'source_all'}
        pref.validate(settings_data)
        with settings.open('x') as stream:json.dump(settings_data,stream,sort_keys=True,allow_nan=False);stream.write('\n')
        settings_pin=p.sha(settings);record.update(classifier=str(probe),classifier_sha256=p.sha(probe/'result.json'),classification=classification,selected_names=names,assigned_child_seconds=child_seconds,preferences_sha256=settings_pin,task_hashes=task_hashes)
        child_record=p.route(task,child,settings_path=settings)
        record['child_receipt_sha256']=p.sha(child/'result.json');record['child_status']=child_record['status'];record['child_accepted']=child_record['accepted']
        if method=='native-connected-contact':
            child_evidence=f.evidence_inventory(child)
            if any(flag not in child_record['engine_budget']['argv'] for flag in ('--router.optimizer.enabled=false','--router.fanout.enabled=false','--router.automatic_neckdown=false','--router.neck_width_um=0')):raise p.Rejected('contact completion-only engine settings differ')
            _contact_treatment(contact_state,record,out,source,original,hashes,task,child,child_record,settings_data,tools)
        else:
            if child_record['accepted'] is not True or not p.native_accepted(child_record['native']) or p.check_result(child/'result.json')['current'] is not True:raise p.Rejected('own selected child rejected')
            if child_record['source_hashes']!=task_hashes or child_record['source']!=str(task) or child_record['scope']!='selected_nets' or pref.readback(pc.read_bytes(child/'routing-preferences.json'))!=pref.validate(settings_data):raise p.Rejected('selected child task/preferences binding differs')
            if any(flag not in child_record['engine_budget']['argv'] for flag in ('--router.optimizer.enabled=false','--router.fanout.enabled=false','--router.automatic_neckdown=false','--router.neck_width_um=0')):raise p.Rejected('completion-only strict engine settings differ')
            child_evidence=f.evidence_inventory(child);fresh_child=Path(child_record['candidate'])
            p.verify_candidate_files(fresh_child,hashes,child_record['candidate_sha256'])
            # Parent works on a new exclusive copy. Retained child/source evidence stays immutable.
            files=pc.inventory(fresh_child.parent,contents=True);copy_bytes(files,out/'final-candidate',expected_parent_owner=owner)
            final=out/'final-candidate'/source.name;pre_hash=p.sha(final)
            with (out/'pre-final.kicad_pcb').open('xb') as stream:stream.write(pc.read_bytes(final))
            final_job=f.FloorJob(out/'original-validation',remaining(),remaining)
            original_native=final_job.drc('pristine-original',source,schematic_parity=True)
            if not p.native_accepted(original_native) or original_native['warnings']!=10:raise p.Rejected('pristine original native baseline not qualified')
            digest,native=p.validate_candidate(final_job,original,final,hashes,[],schematic_parity=True)
            refill_native=f.check_drc_stage(final_job.out,{'steps':final_job.steps},'refill-drc',final_job.out/'refill'/source.name,final_job.out/'refill'/source.name,True,{**hashes,source.name:pre_hash})
            record.update(saved_refill_native=refill_native,saved_refill_report_sha256=p.sha(final_job.out/'refill-drc.json'))
            if not p.native_accepted(native) or warnings(native)!=warnings(original_native):raise p.Rejected('whole original Native failed or inherited warnings changed')
            final_job.native('metrics','metrics',final,final_job.out/'metrics.json');metrics=f.read_json(final_job.out/'metrics.json')
            if metrics.get('version')!='10.0.0' or type(metrics.get('vias')) is not int or metrics['vias']<0 or type(metrics.get('track_length_mm')) not in (int,float) or not math.isfinite(metrics['track_length_mm']) or metrics['track_length_mm']<0:raise p.Rejected('invalid actual final metrics')
            f.process_check(final_job.out,{'steps':final_job.steps},'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(final),str(final_job.out/'metrics.json')])
            record.update(status='completed',method_qualified=True,pre_final_candidate_sha256=pre_hash,candidate=str(final),candidate_sha256=digest,native=native,native_report_sha256=p.sha(final_job.out/'final-drc.json'),original_warning_signatures=warnings(original_native),original_native=original_native,original_native_report_sha256=p.sha(final_job.out/'pristine-original.json'),metrics=metrics,metrics_sha256=p.sha(final_job.out/'metrics.json'),steps=final_job.steps)
        final_readback();completed=f.evidence_inventory(out)
        record.update(completed_material=completed,classifier_material=f.evidence_inventory(probe))
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',method_qualified=False,reason=type(exc).__name__+': '+str(exc),initial_failure=type(exc).__name__+': '+str(exc))
    f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_readback)
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--method',choices=('all-active','native-connected','native-connected-contact'),required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit native execution required')
    def interrupted(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    result=experiment(args.method,args.output,args.protocol,args.protocol_sha256);print(json.dumps({k:result[k] for k in ('status','method_qualified','charged_wall_seconds','charged_full_cpu_seconds')}));raise SystemExit(0 if result['method_qualified'] else 2)
