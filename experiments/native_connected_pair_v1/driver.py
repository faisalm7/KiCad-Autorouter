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
    if method not in ('all-active','native-connected') or out.parent!=ROOT/'.runs' or out.exists() or out.is_symlink():raise p.Rejected('fixed method and fresh direct .runs output required')
    if p.sha(protocol_path)!=protocol_sha:raise p.Rejected('prospective protocol pin differs')
    spec=f.read_json(protocol_path)
    if spec['parent_wall_full_cpu_seconds']!=120 or spec['final_reserve_seconds']!=20:raise p.Rejected('fixed parent budget/reserve differs')
    for name,pin in spec['code_sha256'].items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('frozen implementation differs: '+name)
    if p.sha(Path(__file__))!=spec['driver_sha256']:raise p.Rejected('frozen harness differs')
    source,family=selected_source('nus-usb-led');original=p.preflight(source);hashes=p.tree_hash(source.parent)
    if str(source)!=spec['source'] or hashes!=spec['source_hashes']:raise p.Rejected('pristine fixed source differs')
    tools=p.tool_manifest();out.mkdir();owner={};h.capture_destination(owner,out)
    probe=out.parent/(out.name+'-classifier');child=out/'selected-route';final_job=None;child_record=None;child_evidence=None;completed=None;settings=None;settings_pin=None
    record=dict(schema=1,kind='exposed-NUS-native-connected-selected-seam-diagnostic',method=method,status='incomplete',accepted=False,method_qualified=False,production_admitted=False,
        budget_seconds=120,cpu_budget_seconds=120,bootstrap_allowance_seconds=BOOTSTRAP,final_reserve_seconds=20,protocol_sha256=protocol_sha,source=str(source),source_hashes=hashes,family=family,tools=tools,
        scope='Fresh classifier and selected routing per arm; whole original-rule final validation. Neither selected child receipt nor this diagnostic creates a shipped whole-routing receipt. Exposed NUS only; tunedB2/C remain separate.')
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
        if final_job is not None:record['steps']=final_job.steps
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--method',choices=('all-active','native-connected'),required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit native execution required')
    def interrupted(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    result=experiment(args.method,args.output,args.protocol,args.protocol_sha256);print(json.dumps({k:result[k] for k in ('status','method_qualified','charged_wall_seconds','charged_full_cpu_seconds')}));raise SystemExit(0 if result['method_qualified'] else 2)
