"""Three finite installed017 failure controls; no positive routing rerun.

Uses013's actual mismatch, same-original Native short and CliJob engine-cancel
mechanisms. Positive017 evidence stays untouched at its original absolute paths.
Authored late-byte/admission controls belong to full153, not these Native cases.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
from collections import Counter
import argparse,hashlib,importlib.util,json,sys,threading,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,review_export as ex,gui,local_settings as ls,schematic_class_evidence as classes,schematic_field_evidence as fields,placement_clearance as pc,provenance as pv,sexpr as sx
SHARED_PIN='c412dc76a66bea20b52a071ce6b0de255047d817f5c432a3dbc7d287dc81e12e'
KIND='installed-runtime017-failure-controls-v1'

def require(value,reason):
    if not value:raise p.Rejected(reason)

def strict_raw(path):
    raw=pv.read_bytes(path,8*1024**2)
    row=json.loads(raw,object_pairs_hook=pv._strict_object,parse_constant=lambda value:(_ for _ in()).throw(ValueError('invalid JSON constant')))
    require(type(row)is dict,'strict control object required')
    return raw,row

def execute(protocol,pin):
    plan=f.read_json(protocol)
    require(p.sha(protocol)==pin and plan.get('status')=='frozen'and plan.get('kind')=='runtime017-failure-controls-protocol-v1'
        and plan.get('controls')==['class_mismatch_before_engine','same_original_native_short','real_engine_cancel'],'exact frozen three-control protocol required')
    require(c.ROOT==ROOT==Path(plan['runtime'])and Path(sys.prefix).resolve()==ROOT/'.venv'
        and p.sha(Path(__file__))==plan['child_sha256'],'exact installed017 child/runtime required')
    shared_path=Path(plan['shared_pair_helper']);require(p.sha(shared_path)==plan['shared_pair_helper_sha256']==SHARED_PIN,'frozen pair helper changed')
    spec=importlib.util.spec_from_file_location('retained_pair_controls017',shared_path);shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    require(p.sha(shared_path)==SHARED_PIN,'shared helper changed during import')
    tools=p.tool_manifest();python_context=shared.coordinator_python_context()
    require(tools==plan['runtime_tools']and python_context==plan['runtime_python']and sys.version_info[:2]==(3,11),'actual installed017 tools/Python differ')
    helper=Path(plan['signal_bridge_controller']);require(p.sha(helper)==plan['signal_bridge_sha256'],'frozen queued bridge changed')
    spec=importlib.util.spec_from_file_location('retained_controls_bridge017',helper);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    positive_path=Path(plan['positive_receipt']);positive_raw,positive=strict_raw(positive_path)
    require(hashlib.sha256(positive_raw).hexdigest()==plan['positive_receipt_sha256']and positive.get('schema')==1
        and positive.get('kind')=='installed-runtime017-production-four-cu-v1'and positive.get('protocol_sha256')==plan['production_protocol_sha256']
        and positive.get('passed')is True and positive.get('status')=='completed'and positive.get('accepted')is False
        and positive.get('tools')==tools and positive.get('python_context')==python_context,'actual pinned0174Cu positive prerequisite required')
    positive_protocol=Path(plan['production_protocol']);production=f.read_json(positive_protocol)
    require(p.sha(positive_protocol)==plan['production_protocol_sha256']and production.get('status')=='frozen'
        and production.get('kind')=='runtime017-four-cu-production-protocol-v1'and production['runtime_tools']==tools
        and production['runtime_python']==python_context,'same exact frozen production prerequisite required')
    positive_out=positive_path.parent;workspace=Path(positive['workspace']);receipt=workspace/'route/result.json';export_path=workspace/'export/export.json'
    require(positive_out==ROOT/'.runs/production-delivery-001'and positive_out/'jobs'in workspace.parents,'positive remains in its original installed owned enclosure')
    route=f.read_json(receipt);source=Path(route['source']);source_hashes=p.tree_hash(source.parent);original=sx.read(source);protected=p.protected_for_record(route,original)
    require(source_hashes==route['source_hashes']==production['fixture_sha256']and len(protected)==10
        and route.get('native_edge_admission_policy')=='known-named-whole-native-edge-v1','exact original matching source/protected/admission prerequisite differs')
    mismatch=Path(plan['mismatch_source']);require(p.tree_hash(mismatch.parent)==plan['mismatch_source_hashes'],'exact retained017 mismatch packet differs')
    out=ROOT/'.runs/failure-controls-001';out.mkdir();owner={};h.capture_destination(owner,out)
    positive_material=f.evidence_inventory(positive_out);positive_route_pin=p.sha(receipt);positive_export_pin=p.sha(export_path)
    cancel_job=gui.CliJob();intentional_cancel=[False];short_state={};active=['prerequisite_current']
    record=dict(schema=1,kind=KIND,accepted=False,passed=False,controls_passed=False,status='failed',actual_GUI=False,human_review=False,
        source_head=plan['source_head'],tools=tools,python_context=python_context,protocol_sha256=pin,checks=[],
        positive_receipt=str(positive_path),positive_receipt_sha256=plan['positive_receipt_sha256'],
        scope=plan['scope'],accounting_point='Inner pre-final-publication sample. Reaped outer and external260s whole wall/fullCPU remain mandatory.')
    def remaining():return min(238-(time.monotonic()-START),238-(cpu()-CPU0))
    def phase_live():
        # The one deliberate cancel is itself a negative test. It cannot turn
        # an externally queued cancellation into a successful controls receipt.
        if intentional_cancel[0]:require(not queued[0],'enclosure cancellation requested after the deliberate engine control')
        else:live()
    def stable():
        phase_live();h.owned_destination(owner)
        require(p.sha(protocol)==pin and p.sha(Path(__file__))==plan['child_sha256']and p.sha(shared_path)==SHARED_PIN
            and p.sha(helper)==plan['signal_bridge_sha256']and p.tool_manifest()==tools
            and shared.coordinator_python_context()==python_context,'control runtime/protocol/Python changed')
        require(p.sha(positive_protocol)==plan['production_protocol_sha256']and f.evidence_inventory(positive_out)==positive_material
            and p.sha(receipt)==positive_route_pin and p.sha(export_path)==positive_export_pin,'untouched production prerequisite changed')
        shared.child_bytes_fresh(positive_path,positive_raw)
        require(p.tree_hash(source.parent)==source_hashes and p.tree_hash(mismatch.parent)==plan['mismatch_source_hashes'],'original/mismatch source changed')
        for path,digest in plan['prerequisite_sha256'].items():require(p.sha(Path(path))==digest,'pinned prerequisite changed: '+path)
        phase_live()
    def positive_current():
        require(p.check_result(receipt)['current']is True and ex.check_export(export_path)['current']is True,'actual original positive full-current replay failed')
    def native_prls(folder,data):
        for step in data.get('steps',[]):
            argv=step.get('argv',[]);bare=argv[len(f.SANDBOX):]if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
            if bare[:3]==[str(c.CLI),'pcb','drc']:
                directory=Path(step['cwd']);name=step['name'];binding=f.read_json(directory/(name+'-binding.json'))
                ls.check_event(directory,binding,f.process_check(directory,data,name,argv,allowed=(0,5)))
                raw=f.read_json(directory/(name+'.json'))
                if fields.has_fields(raw['violations']+raw['unconnected_items']+raw['schematic_parity']):fields.check_local_settings(directory,name,binding)
        for stage in ('task','final'):
            if (folder/(stage+'-classes-binding.json')).exists():classes.check_local_settings(folder,stage)
    def short_readback():
        job=short_state['job'];candidate=short_state['candidate'];digest=short_state['digest'];native=short_state['native'];data=short_state['data']
        expected=dict(source_hashes);expected[source.name]=digest
        observed=f.check_drc_stage(job.out,data,'final-drc',candidate,job.out/'final-drc-input'/source.name,False,expected,schematic_parity=True,sandboxed=False)
        before=dict(source_hashes);before[source.name]=short_state['preimage']
        f.check_drc_stage(job.out,data,'refill-drc',job.out/'refill'/source.name,job.out/'refill'/source.name,True,before,sandboxed=False)
        proof=classes.check(job.out,data,'final',board_raw=pc.read_bytes(candidate),source=str(candidate),project_raw=pc.read_bytes(candidate.with_suffix('.kicad_pro')),
            schematic_raw=pc.read_bytes(candidate.with_suffix('.kicad_sch')),native_map=job.out/'final-netclasses.json')
        mapping=f.read_json(job.out/'final-netclasses.json');audit=p.audit_candidate_netclasses(candidate,protected,mapping);audit['native_map_file_sha256']=p.sha(job.out/'final-netclasses.json')
        require(audit==f.read_json(job.out/'final-netclass-audit.json')and audit['route_dimensions']['checked']['protected']==10,'own short dimension/class audit differs')
        errors=Counter(row['type']for row in observed['findings']if row['severity']=='error')
        warnings=sorted(f.canonical(row)for row in observed['findings']if row['severity']=='warning')
        require(observed==native and [native[key]for key in('opens','blocking','warnings','exclusions')]==[0,4,6,0]
            and dict(errors)==plan['expected_short_error_types']and warnings==production['expected_warning_rows']
            and native['ignored_checks']==production['expected_ignored_checks']and not p.native_accepted(native)
            and p.native_rejection_reasons(native)==plan['expected_short_rejection_reasons'],'specific complete Native short error/warning/ignored policy differs')
        require(proof['qualification']['class_parity_qualified']is True and p.immutable(sx.read(candidate))==p.immutable(original)
            and all(row in p.routes(sx.read(candidate))for row in protected),'short failed original design/protected/fullclass preservation')
        p.verify_candidate_files(candidate,source_hashes,digest);native_prls(job.out,data)
        return dict(candidate=str(candidate),candidate_sha256=digest,native=native,steps=job.steps,protected_routes=10,class_metadata=job.schematic_class_final,
            class_audit=audit,class_parity_qualified=True,routing_accepted=False,final_native_sha256=p.sha(job.out/'final-drc.json'))
    with bridge.cancellation_bridge(cancel_job)as(queued,live):
        try:
            stable();positive_current();stable();record['positive_full_current_before']=True
            active[0]='class_mismatch_before_engine';require(remaining()>120,'reserve for all three finite controls unavailable')
            bad=p.route(mismatch,out/'mismatch-route',seconds=90,adapter='both')
            require(bad.get('accepted')is False and bad.get('reason')==plan['expected_class_mismatch_reason'],'specific ClassIdentityMismatch refusal required')
            require(not any(row['name']=='engine'for row in bad['steps'])and not(out/'mismatch-route/engine.log').exists()
                and any(row['name']=='task-classes-netlist'for row in bad['steps']),'mismatch must reach actual source-class observation and refuse before engine')
            native_prls(out/'mismatch-route',bad)
            record['checks'].append(dict(name=active[0],passed=True,reason=bad['reason'],receipt_sha256=p.sha(out/'mismatch-route/result.json'),steps=bad['steps']))
            stable()
            active[0]='same_original_native_short';require(remaining()>100,'reserve for Native short and engine cancel unavailable')
            job=p.Job(out/'short-validation',min(60,remaining()-60),protect_local_settings=True);candidate=job.out/'candidate'/source.name
            original_candidate=Path(route['candidate']);candidate_bytes=pc.inventory(original_candidate.parent,contents=True,max_bytes=100*1024**2)
            candidate.parent.mkdir()
            for name,raw in candidate_bytes.items():
                require(Path(name).name==name,'flat exact candidate project required')
                with(candidate.parent/name).open('xb')as stream:stream.write(raw)
            require(pc.inventory(original_candidate.parent,contents=True,max_bytes=100*1024**2)==candidate_bytes,'positive candidate changed during exact copy')
            bad_tree=sx.read(candidate);bad_tree.append(['segment',['start','12','10'],['end','12','16'],['width','0.4'],['layer','"F.Cu"'],['net','"ROUTE"'],
                ['uuid',json.dumps(str(uuid.uuid5(uuid.NAMESPACE_URL,'owned-runtime017-control-short-v1')))]])
            sx.write(candidate,bad_tree);preimage=p.sha(candidate)
            require(p.immutable(bad_tree)==p.immutable(original)and all(row in p.routes(bad_tree)for row in protected),'authored short changed original design/protected copper')
            digest,native=p.validate_candidate(job,original,candidate,source_hashes,protected,class_context=classes.CONTEXT)
            short_state.update(job=job,candidate=candidate,digest=digest,native=native,preimage=preimage,
                data=dict(steps=job.steps,source_hashes=source_hashes,schematic_class_final=job.schematic_class_final))
            short=short_readback();p.save_json(out/'short-control.json',dict(schema=1,accepted=False,control_passed=True,**short))
            record['checks'].append(dict(name=active[0],passed=True,report_sha256=p.sha(out/'short-control.json'),native=native,protected_routes=10))
            stable()
            active[0]='real_engine_cancel';require(remaining()>45,'finite cancellation/final-readback reserve unavailable')
            cancel_out=out/'cancel-route';observed={};done=threading.Event()
            def cancel_engine():
                deadline=time.monotonic()+min(60,remaining()-25)
                while not done.is_set()and time.monotonic()<deadline:
                    log=cancel_out/'engine.log'
                    if log.is_file()and not log.is_symlink()and log.stat().st_size>0 and not(cancel_out/'engine-process.json').exists():
                        observed.update(stage='engine',log_bytes=log.stat().st_size);cancel_job.cancel();return
                    done.wait(.01)
            watcher=threading.Thread(target=cancel_engine,name='finite-engine-cancel-control');watcher.start()
            try:
                process=cancel_job.run([str(ROOT/'.venv/bin/python'),'-B','-m','autorouter','route',str(source),'--seconds','90','--adapter','both','--output',str(cancel_out)],
                    out/'cancel-cli.log',timeout=min(100,remaining()-25))
            finally:done.set();watcher.join(3)
            require(not watcher.is_alive()and observed.get('stage')=='engine'and process['cancel_requested']is True and not process['log_truncated'],'actual joined CliJob engine cancellation required')
            cancelled=f.read_json(cancel_out/'result.json');engines=[row for row in cancelled['steps']if row['name']=='engine']
            require(cancelled.get('accepted')is False and cancelled.get('status')=='cancelled'and cancelled.get('reason')=='interrupted route'
                and cancelled.get('strategy')is None and len(engines)==1 and engines[0].get('status')=='cancelled'
                and engines[0].get('cancel_signal')=='SIGINT'and engines[0]==f.read_json(cancel_out/'engine-process.json')
                and all(row.get('cleanup_complete')is True for row in cancelled['steps']),'cancelled engine/CLI output must remain rejected with reaped worker history')
            require(not any(row['name']in {'import','final-drc','final-classes-netlist'}for row in cancelled['steps'])
                and not(cancel_out/'final-drc.json').exists()and not(cancel_out/'final-classes-proof.json').exists(),'cancelled output must not deliver a final candidate/fallback proof')
            intentional_cancel[0]=True
            try:p.check_result(cancel_out/'result.json')
            except p.Rejected as exc:cancel_reason=str(exc)
            else:raise p.Rejected('cancelled result passed positive central readback')
            native_prls(cancel_out,cancelled)
            record['checks'].append(dict(name=active[0],passed=True,observation=observed,process=process,receipt_sha256=p.sha(cancel_out/'result.json'),
                reason=cancelled['reason'],positive_reader_refusal=cancel_reason,steps=cancelled['steps']))
            stable();record.update(passed=True,controls_passed=True,status='completed')
        except(Exception,KeyboardInterrupt)as exc:
            record['checks'].append(dict(name=active[0],passed=False,error=type(exc).__name__+': '+str(exc)))
            record.update(passed=False,controls_passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc))
        material=f.evidence_inventory(out)
        def late_prls():
            for name in ('mismatch-route','cancel-route'):
                path=out/name/'result.json'
                if path.exists():native_prls(path.parent,f.read_json(path))
            if short_state:native_prls(short_state['job'].out,short_state['data'])
            # Reuse017's explicit ordinary production final PRL census. The
            # experimental delivery_guards helper intentionally does nothing
            # for this default toolchain and cannot replace these readers.
            native_prls(receipt.parent,route);native_prls(workspace/'export/validation',f.read_json(export_path))
            preview=f.read_json(workspace/'review/review.json').get('preview',{});folder=workspace/'review/plot-work'
            for step in preview.get('steps',[]):
                name=step['name'];ls.check_event(folder,f.read_json(folder/(name+'-input-binding.json')),f.process_check(folder,preview,name,step['argv']))
        def fresh():
            stable();require(f.evidence_inventory(out)==material,'completed failure-control evidence changed');late_prls();phase_live()
        def final():
            fresh()
            if record['passed']:
                positive_current();require(short_readback()==short,'own short Native/class/original readback changed')
            fresh();require(remaining()>0,'whole controls deadline exhausted during final proof')
        def account():
            record.update(inner_sample_wall_seconds=time.monotonic()-START,inner_sample_full_cpu_seconds=cpu()-CPU0)
            if remaining()<=0:record.update(passed=False,controls_passed=False,status='budget_exceeded')
            if queued[0]:record.update(passed=False,controls_passed=False,status='cancelled')
            if record['status']!='completed':record.update(passed=False,controls_passed=False)
        try:
            f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final)
            if record['passed']:fresh();phase_live();require(remaining()>0,'whole controls deadline exhausted after publication')
        except BaseException as exc:
            def failed():raise exc
            f.publish(out,record,failed,account,remaining,owned=lambda:h.owned_destination(owner))
        print(json.dumps({key:record.get(key)for key in('passed','controls_passed','status','inner_sample_wall_seconds','inner_sample_full_cpu_seconds','error')}))
        return 0 if record['passed']and record['controls_passed']and record['status']=='completed'else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    raise SystemExit(execute(args.protocol,args.protocol_sha256))
