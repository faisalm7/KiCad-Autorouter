"""Fresh native validation into a new separate project after bound accept intent.

No live editor, source overwrite, solver, human/electrical approval or GUI action.
The original route receipt and this export proof remain distinct records.
"""
from pathlib import Path
import copy,hashlib,math,signal,time,uuid
from . import config as c,pipeline as p,floor_route as f,placement_clearance as pc
from . import placement_strategy as ps,sexpr as sx,handoff as h
from .runner import run
from . import comparison as cmp
KIND='review-export-v1'
MIN_SECONDS=30
SECONDS=120
OUTPUT_BYTES=256*1024**2
OUTPUT_FILES=12000

def witness(path,*,project=False):
    files,dirs=pc.inventory(path,max_bytes=h.PROJECT_BYTES if project else OUTPUT_BYTES,
        max_files=2000 if project else OUTPUT_FILES,max_entries=4000 if project else OUTPUT_FILES*2,with_directories=True)
    return {'files':files,'directories':list(dirs)}

def evidence(out):
    value=witness(out);value['files'].pop('export.json',None);return value

def finite(x):return type(x) in (int,float) and math.isfinite(x) and x>=0

def validate_seconds(seconds):
    """Public export allocation remains independent of the routing allocation."""
    if not finite(seconds) or not MIN_SECONDS<=seconds<=SECONDS:
        raise p.Rejected(f'export budget must be {MIN_SECONDS}–{SECONDS} seconds')
    return seconds

def bound_material(binding):
    """Repeat existing byte witnesses without invoking tools or another consumer."""
    small={str(Path(binding[key]).parent) for key in ('source','validated_candidate')}
    for name,expected in binding['input_witnesses'].items():
        if witness(h.real_path(name),project=name in small)!=expected:
            raise p.Rejected('bound delivery input changed after tool checks')
    for key in ('choice','review','receipt'):
        if p.sha(h.real_path(binding[key]))!=binding[key+'_sha256']:
            raise p.Rejected('bound delivery receipt changed after tool checks')
    if (binding['input_witnesses'][str(Path(binding['source']).parent)]['files']!=binding['source_hashes']
        or binding['input_witnesses'][str(Path(binding['validated_candidate']).parent)]['files']!=binding['candidate_hashes']):
        raise p.Rejected('bound delivery source/candidate capture changed')

def bind(choice_path, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Shared handoff contract/current checker plus exact recorded intent identity."""
    ctx=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    choice_path=h.real_path(choice_path);choice=f.read_json(choice_path)
    cmp.delivery_path(choice_path.parent,comparison_context,'choice')
    h.check_delivery_context(choice,**ctx)
    if (choice_path.name!='choice.json' or type(choice.get('schema')) is not int or choice['schema']!=1
        or choice.get('status')!='disposition_recorded' or choice.get('choice_recorded') is not True or choice.get('choice')!='accept'
        or any(choice.get(k) is not False for k in ('routing_accepted','applied','native_validation_performed','human_pcb_approval_observed'))
        or choice.get('candidate_board_unchanged') is not True or choice.get('fresh_native_validation_required') is not True
        or choice.get('budget_seconds')!=h.SECONDS or choice.get('cpu_budget_seconds')!=h.SECONDS
        or choice.get('within_budget') is not True or any(not finite(choice.get(k)) or choice[k]>h.SECONDS for k in ('wall_seconds','total_cpu_seconds'))):
        raise p.Rejected('current bounded accept-intent record required; no approval inferred')
    review_path=h.real_path(choice['review']);review=f.read_json(review_path)
    cmp.delivery_path(review_path.parent,comparison_context,'review')
    h.check_delivery_context(review,**ctx)
    receipt=h.real_path(choice['receipt']);report=f.read_json(receipt);policy=h.review_policy(report,receipt.parent,**ctx)
    source=h.real_path(report['source']);candidate=h.real_path(report['candidate']);project=h.real_path(review['project'])
    if (review_path.name!='review.json' or review.get('schema')!=1 or type(review['schema']) is not int
        or review.get('status')!='ready_for_manual_review' or review.get('receipt')!=str(receipt)
        or review.get('within_budget') is not True or review.get('native_validation_performed') is not False
        or review.get('budget_seconds')!=h.SECONDS or review.get('cpu_budget_seconds')!=h.SECONDS
        or any(not finite(review.get(k)) or review[k]>h.SECONDS for k in ('wall_seconds','total_cpu_seconds'))
        or report.get('scope') not in {'whole_board_unlocked_routing','partial_completion','selected_nets'}
        or choice.get('saved_native_findings')!=report['native'] or choice.get('saved_metrics')!=report['metrics']
        or choice['review_sha256']!=p.sha(review_path) or choice['receipt_sha256']!=p.sha(receipt)
        or review.get('receipt_sha256')!=choice['receipt_sha256']
        or candidate!=receipt.parent/'candidate'/source.name or project!=review_path.parent/'project'
        or review.get('board')!=str(project/source.name) or choice.get('review_project')!=str(project)
        or any(x.get('input_policy')!=policy or x.get('source_receipt_schema')!=report['schema'] for x in (review,choice))
        or choice.get('validated_candidate')!=str(candidate)
        or any(x!=report['candidate_sha256'] for x in (choice.get('validated_candidate_sha256'),review.get('verified_candidate_sha256'),review.get('candidate_sha256')))):
        raise p.Rejected('choice/review/routing identity changed')
    sw=witness(source.parent,project=True);cw=witness(candidate.parent,project=True);rw=witness(project,project=True)
    h.require_closed_review(rw['files'])
    if (sw['files']!=choice['original_source_hashes'] or sw['files']!=review['source_project_hashes']
        or cw['files']!=review['initial_project_hashes'] or rw['files']!=choice['observed_review_project_hashes']
        or rw['files'].get(source.name)!=report['candidate_sha256'] or cw['files'].get(source.name)!=report['candidate_sha256']
        or h.evidence_witness(receipt.parent)!=choice['routing_evidence_hashes']
        or choice['routing_evidence_hashes']!=review['routing_evidence_hashes']):
        raise p.Rejected('original/candidate/review/evidence changed since recorded choice')
    preview=review.get('preview')
    if (review_path.parent/'preview.html').exists() and not isinstance(preview,dict):raise p.Rejected('review preview binding missing')
    if preview is not None:
        if (native_toolchain is None and p.sha(c.CLI)!=preview['plotter_sha256']) or witness(review_path.parent/'before',project=True)['files']!=sw['files']:
            raise p.Rejected('review original/plotter preview binding changed')
        for name,expected in preview['input_trees'].items():
            path=h.real_path(review_path.parent/name)
            if not path.is_relative_to(review_path.parent) or witness(path,project=True)['files']!=expected:raise p.Rejected('review preview inputs changed')
        for name,expected in preview['files'].items():
            path=h.real_path(review_path.parent/name)
            if not path.is_relative_to(review_path.parent) or p.sha(path)!=expected:raise p.Rejected('review preview bytes changed')
    verified=p.check_result(receipt,**ctx)
    if (verified.get('current') is not True or verified.get('applied') is not False or verified.get('candidate')!=str(candidate)
        or verified.get('candidate_sha256')!=report['candidate_sha256'] or verified.get('input_policy','native')!=policy):
        raise p.Rejected('central original routing receipt rejected or changed')
    # Full witnesses guard additional files and empty directories during export.
    inputs={str(path):witness(path,project=small) for path,small in ((source.parent,True),(candidate.parent,True),
        (receipt.parent,False),(review_path.parent,False),(choice_path.parent,False))}
    binding={'choice':str(choice_path),'choice_sha256':p.sha(choice_path),'review':str(review_path),'review_sha256':p.sha(review_path),
        'receipt':str(receipt),'receipt_sha256':p.sha(receipt),'source':str(source),'validated_candidate':str(candidate),
        'validated_candidate_sha256':report['candidate_sha256'],'input_policy':policy,'source_receipt_schema':report['schema'],
        'source_hashes':sw['files'],'candidate_hashes':cw['files'],'input_witnesses':inputs}
    binding.update(h.delivery_record(**ctx))
    h.delivery_guards(receipt,report,native_toolchain,preview,review_path.parent,material=lambda:bound_material(binding),comparison_context=comparison_context)
    return binding,report

def lineage(binding,report, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Use the existing bound guidance/layer/native-class paths, never a new task."""
    ctx=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    h.check_delivery_context(binding,**ctx)
    receipt=Path(binding['receipt']);policy=binding['input_policy'];source=Path(binding['source'])
    h.review_policy(report,receipt.parent,**ctx)
    if native_toolchain is not None:
        p.check_experimental_route(report,native_toolchain,experimental_schematic_parity)
        from .pour_rule_area import qualify
        if policy!='native' or p.layer_markers(receipt.parent,report) or qualify(sx.read(source)):
            raise p.Rejected('experimental delivery supports ordinary native zones only')
    if policy=='native':basis=None;contract=None
    else:
        basis=receipt.parent/'incumbent' if policy==ps.POLICY else receipt.parent
        if policy==ps.POLICY:p.check_result(basis/'result.json')
        contract=f.read_json(basis/'floor-policy.json')
    layers=None
    if p.layer_markers(receipt.parent,report):
        effective=report['routing_preferences']['effective']
        layers=p.layer_contract(receipt.parent,source,effective,report['layer_binding'])
    return basis,contract,layers

class ExportJob(f.FloorJob):
    """Existing DRC/copy/first-failure path with finite native-only process caps."""
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        if name not in {'refill-drc','pour-keepout-audit','floor-final','final-netclasses','final-drc','final-drc-fields-netlist','final-drc-fields-audit','final-classes-netlist','metrics'}:
            raise p.Rejected('export prohibits solver/import/export stages')
        p.experimental_native_version(self.native_toolchain)
        available=min(30,self.remaining())
        if available<=0:raise p.Rejected('export native budget exhausted')
        actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
        result=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=available,env=self.env,
            max_log_bytes=512*1024,max_workdir_bytes=OUTPUT_BYTES,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:
            raise p.Rejected(name+': '+result['status']+' exit='+str(result['exit_code']))
        p.experimental_native_version(self.native_toolchain)
        if self.remaining()<=0:raise p.Rejected('export wall/full CPU cap exhausted')
        return result

def check_class_evidence(folder,data,binding,report, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Recheck class copies/processes and non-byte PRL flags after late reads."""
    ctx=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    cmp.delivery_path(Path(folder).parent,comparison_context,'export')
    h.check_delivery_context(data,**ctx);h.check_delivery_context(binding,**ctx)
    if comparison_context is not None:h.review_policy(report,Path(binding['receipt']).parent,**ctx)
    else:
        cmp.check_record(folder,report,None)
        p.check_experimental_route(report,native_toolchain,experimental_schematic_parity)
    from . import schematic_class_evidence as classes
    if classes.present(folder,data,'task'):
        raise p.Rejected('unexpected task class proof in fresh export')
    class_context=p.class_context_for_record(report,Path(binding['receipt']).parent,input_policy=binding['input_policy'],native_toolchain=native_toolchain)
    required=p.check_schematic_class_support(Path(binding['source']),class_context=class_context)
    if required is not None:
        material=witness(folder)
        if required['source_hashes']!=binding['source_hashes']:
            raise p.Rejected('export class source differs')
        candidate=folder/'candidate'/Path(binding['source']).name
        classes.check(folder,data,'final',board_raw=pc.read_bytes(candidate),source=str(candidate),
            project_raw=pc.read_bytes(candidate.with_suffix('.kicad_pro')),schematic_raw=pc.read_bytes(candidate.with_suffix('.kicad_sch')),
            native_map=folder/'final-netclasses.json')
        pc.verify_candidate(candidate,binding['source_hashes'],data['candidate_sha256'])
        if pc.inventory(Path(binding['source']).parent,max_bytes=h.PROJECT_BYTES)!=binding['source_hashes'] or witness(folder)!=material:
            raise p.Rejected('export class evidence/source changed during replay')
        classes.check_local_settings(folder,'final')
    elif classes.present(folder,data,'final'):
        raise p.Rejected('unexpected export class proof')
    return required


def check_stage(folder,data,binding,report,basis,contract,layers, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Reuse original-rule refill/final/process/native-context validators."""
    ctx=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    worker=h.delivery_kwargs(native_toolchain,experimental_schematic_parity)
    cmp.delivery_path(Path(folder).parent,comparison_context,'export')
    h.check_delivery_context(data,**ctx)
    h.check_delivery_context(binding,**ctx)
    if comparison_context is not None:h.review_policy(report,Path(binding['receipt']).parent,**ctx)
    else:
        cmp.check_record(folder,report,None)
        p.check_experimental_route(report,native_toolchain,experimental_schematic_parity)
    if (native_toolchain is not None or comparison_context is not None) and (basis is not None or contract is not None or layers is not None):
        raise p.Rejected('experimental export cannot use strategy or layer context')
    if report.get('scope')=='selected_nets' and data.get('schematic_parity')!=report.get('schematic_parity'):
        raise p.Rejected('export selected-net schematic parity declaration differs')
    if data.get('schematic_parity')!=p.parity_declaration(binding['source'],binding['source_hashes']):
        raise p.Rejected('export schematic parity declaration differs from original source')
    class_context=p.class_context_for_record(report,Path(binding['receipt']).parent,input_policy=binding['input_policy'],native_toolchain=native_toolchain)
    original=p.preflight(Path(binding['source']),task_scope=p.task_scope_for_record(report,Path(binding['receipt']).parent,input_policy=binding['input_policy']),class_context=class_context);candidate=folder/'candidate'/Path(binding['source']).name
    class_requirement=p.check_schematic_class_support(Path(binding['source']),class_context=class_context)
    before=sx.read(Path(binding['validated_candidate']));protected=p.protected_for_record(report,original)
    if candidate!=Path(data['candidate']):raise p.Rejected('export candidate escaped validation directory')
    pc.verify_candidate(candidate,binding['source_hashes'],data['candidate_sha256'])
    if p.immutable(sx.read(candidate))!=p.immutable(original) or p.routes(sx.read(candidate))!=p.routes(before):
        raise p.Rejected('export changed original geometry or validated route copper')
    if contract is not None:
        ps.check_candidate_stage(folder,data,original,binding['source_hashes'],basis,before)
    else:
        expected=dict(binding['source_hashes']);expected[candidate.name]=binding['validated_candidate_sha256']
        refill=folder/'refill'/candidate.name
        f.check_drc_stage(folder,data,'refill-drc',refill,refill,True,expected,**worker)
        if (sx.dump(p.transplant_fill(before,sx.read(refill)))+'\n').encode()!=pc.read_bytes(candidate):raise p.Rejected('export refill reconstruction changed')
        expected[candidate.name]=data['candidate_sha256']
        extra={'schematic_parity':True} if data.get('schematic_parity')=='checked by final native DRC' else {}
        native=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/candidate.name,False,expected,**extra,**worker)
        if native!=data['native']:raise p.Rejected('export actual final native report differs')
        if p.netclass_policy(candidate) is not None or native_toolchain is not None or 'default_target_transport' in report:
            p.check_final_netclass_evidence(folder,data,candidate,protected,native_toolchain=native_toolchain,
                default_target_policy='default_target_transport' in report,sandboxed=True)
        f.process_check(folder,data,'metrics',[*f.SANDBOX,*p.native_prefix(native_toolchain),'metrics',str(candidate),str(folder/'metrics.json')])
    if any(r not in p.routes(sx.read(candidate)) for r in protected):raise p.Rejected('export protected copper changed')
    from .pour_rule_area import qualify
    if native_toolchain is not None and qualify(original):
        raise p.Rejected('experimental delivery supports ordinary native zones only')
    p.check_pour_evidence(folder,data,original,candidate,source_hashes=binding['source_hashes'],correction=False,sandboxed=True)
    names=p.selected_scope_names(report)
    if names is not None:
        from . import routing_scope as rs
        if rs.audit(original,sx.read(candidate),names)!=report['selected_net_audit']:
            raise p.Rejected('export selected-net copper audit differs')
    if layers is not None and p.audit_layer_contract(candidate,layers)!=data.get('layer_audit'):raise p.Rejected('export captured layer contract changed')
    metrics=f.read_json(folder/'metrics.json')
    if (p.sha(folder/'final-drc.json')!=data['native_report_sha256'] or metrics!=data['metrics'] or metrics.get('version')!=p.experimental_native_version(native_toolchain)
        or metrics!=report['metrics'] or not p.native_accepted(data['native'])
        or data['native']['ignored_checks']!=report['native']['ignored_checks'] or not ps.warnings(data['native'])<=ps.warnings(report['native'])):
        raise p.Rejected('fresh export native acceptance/metrics/warnings/original ignore settings differ')
    from .pour_rule_area import qualify
    from . import schematic_field_evidence as fields
    check_class_evidence(folder,data,binding,report,**ctx)
    expected_names=['refill-drc',*(['pour-keepout-audit'] if qualify(original) else []),*(['floor-final'] if contract is not None else ['final-netclasses'] if p.netclass_policy(candidate) is not None or native_toolchain is not None or class_requirement is not None or 'default_target_transport' in report else []),'final-drc',*(fields.names('final-drc') if fields.has_fields(data['native']['findings']) else []),*(['final-classes-netlist'] if class_requirement is not None else []),'metrics']
    if [s['name'] for s in data['steps']]!=expected_names or any(s['cwd']!=str(folder) for s in data['steps']):raise p.Rejected('export native-only stage history differs')
    for step in data['steps']:
        log=Path(step['log'])
        if (log!=folder/(step['name']+'.log') or log.stat().st_size!=step['log_bytes'] or step['log_truncated']
            or any(not finite(step.get(k)) for k in ('wall_seconds','cpu_seconds','monitor_cpu_seconds'))):raise p.Rejected('export process/log/compute differs')
    p.check_resource_accounting(data,child_key='child_step_cpu_seconds')
    if (data.get('project_file')!=str(candidate.with_suffix('.kicad_pro'))
        or data.get('whole_project_drc_clean') is not (p.native_accepted(data['native']) and data['native']['warnings']==0)
        or data.get('original_geometry_and_routing_unchanged') is not True
        or data.get('source_hashes')!=binding['source_hashes']
        or data.get('original_routing_receipt_compute')!={key:report.get(key) for key in ('budget_seconds','cpu_budget_seconds','wall_seconds','total_cpu_seconds')}
        or data.get('preview_board_sha256')!=binding['validated_candidate_sha256']
        or data.get('final_sha_changed_after_refill') is not (data['candidate_sha256']!=binding['validated_candidate_sha256'])
        or data.get('output_ceiling_bytes')!=OUTPUT_BYTES or data.get('output_file_ceiling')!=OUTPUT_FILES):
        raise p.Rejected('export delivery fields differ from validated project')
    return candidate

def _check_export(path,guard, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Stored proof consistency only; reruns original checker, never native or solver."""
    ctx=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    returned_context=h.delivery_record(**ctx)
    guard()
    path=h.real_path(path);before_hash=p.sha(path);data=f.read_json(path)
    cmp.delivery_path(path.parent,comparison_context,'export')
    h.check_delivery_context(data,**ctx)
    validate_seconds(data.get('budget_seconds'))
    if (path.name!='export.json' or data.get('schema')!=1 or type(data['schema']) is not int or data.get('kind')!=KIND
        or data.get('status')!='export_validated' or data.get('export_accepted') is not True
        or data.get('native_validation_performed') is not True or data.get('routing_receipt_accepted') is not True
        or any(data.get(k) is not False for k in ('applied','human_pcb_approval_observed','physical_electrical_validation','new_engine_execution'))
        or data.get('cpu_budget_seconds')!=data['budget_seconds']
        or data.get('within_budget') is not True or any(not finite(data.get(k)) or data[k]>data['budget_seconds'] for k in ('wall_seconds','total_cpu_seconds'))):
        raise p.Rejected('current bounded fresh export proof required')
    binding,report=bind(data['inputs']['choice'],**ctx);guard()
    current_tools=p.tool_manifest(**({"native_toolchain":native_toolchain} if native_toolchain is not None else {}))
    if any(data['tools'].get(key)!=value for key,value in current_tools.items() if key!='git_head'):
        raise p.Rejected('export helper/native pin manifest changed')
    if binding!=data['inputs'] or evidence(path.parent)!=data['export_evidence'] or h.runtime_inventory()!=data['runtime_source_sha256']:
        raise p.Rejected('export inputs/runtime/evidence changed')
    for name,digest in data['tools']['files'].items():
        if p.sha(h.real_path(name))!=digest:raise p.Rejected('export native tool pin changed')
    basis,contract,layers=lineage(binding,report,**ctx);candidate=check_stage(path.parent/'validation',data,binding,report,basis,contract,layers,**ctx)
    if witness(path.parent/'validation/snapshot',project=True)!=binding['input_witnesses'][str(Path(binding['source']).parent)]:raise p.Rejected('export original snapshot changed')
    expected_code={Path(name).name:digest for name,digest in data['tools']['implementation_sha256'].items()}
    if pc.inventory(path.parent/'validation/code')!=data['code_inventory'] or data['code_inventory']!=expected_code:raise p.Rejected('export helper snapshot changed')
    from .local_settings import check_normal_policy
    check_normal_policy(path.parent/'validation',data,max_bytes=OUTPUT_BYTES,max_files=OUTPUT_FILES,**({'native_toolchain':native_toolchain} if native_toolchain is not None else {}))
    if p.sha(path)!=before_hash or bind(binding['choice'],**ctx)[0]!=binding or evidence(path.parent)!=data['export_evidence']:
        raise p.Rejected('export changed during final readback')
    check_class_evidence(path.parent/'validation',data,binding,report,**ctx)
    if native_toolchain is not None or comparison_context is not None:
        def material():
            bound_material(binding)
            if (p.sha(path)!=before_hash or evidence(path.parent)!=data['export_evidence']
                    or h.runtime_inventory()!=data['runtime_source_sha256']):
                raise p.Rejected('export changed after final tool checks')
        h.delivery_guards(binding['receipt'],report,native_toolchain,f.read_json(binding['review']).get('preview'),Path(binding['review']).parent,additional=((path.parent/'validation',data),),material=material,comparison_context=comparison_context)
    guard()
    return {**returned_context,'current':True,'export_accepted':True,'candidate':str(candidate),'candidate_sha256':data['candidate_sha256'],
        'original_routing_receipt':binding['receipt'],'applied':False,'fresh_native_run_performed_by_check':False,
        'warning':'Mutable local consistency proof; no authentication, live application, human PCB or electrical/manufacturing approval.'}


def check_export(path, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Bounded read-only proof check; no fresh native run or solver is invoked."""
    start=time.monotonic();cpu=h.cpu_seconds();previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    def cap():
        if time.monotonic()-start>SECONDS or h.cpu_seconds()-cpu>SECONDS:raise p.Rejected('export readback wall/full CPU ceiling exceeded')
    try:
        ctx=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
        for sig in previous:signal.signal(sig,interrupted)
        with p.validation_readback_session():result=_check_export(path,cap,**ctx)
        cap();return result
    except KeyboardInterrupt as exc:raise p.Rejected('export readback cancelled') from exc
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)

def invalidate(lifecycle,exc):
    if not lifecycle.get('created'):return
    record=lifecycle['record']
    def archive():
        for name in ('export.json','export.json.partial'):
            out=h.owned_destination(lifecycle);path=out/name
            if path.exists() or path.is_symlink():
                h.owned_destination(lifecycle);path.rename(out/('invalidated-export-'+uuid.uuid4().hex+'-'+name))
    try:
        h.owned_destination(lifecycle);archive()
    except BaseException as ownership:
        exc.add_note('No correction written: '+type(ownership).__name__+': '+str(ownership));return
    record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'rejected',export_accepted=False,error=type(exc).__name__+': '+str(exc))
    lifecycle['account']()
    try:
        expected=f.canonical(record);out=h.owned_destination(lifecycle);p.save_json(out/'export.json',record)
        out=h.owned_destination(lifecycle)
        if f.canonical(record)!=expected or f.canonical(f.read_json(out/'export.json'))!=expected:raise p.Rejected('corrective export publication changed')
    except BaseException as corrective:
        exc.add_note('Corrective export publication: '+type(corrective).__name__+': '+str(corrective))
        try:archive()
        except BaseException as ownership:exc.add_note('No archival correction: '+str(ownership))

def export(choice_path,output,seconds=SECONDS, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Validate the original bound candidate into a new project; never copy GUI rules."""
    start=time.monotonic();parent_cpu_start=time.process_time();child_cpu_start=f.child_cpu();cpu_start=parent_cpu_start+child_cpu_start
    ctx=h.application_kwargs(native_toolchain,experimental_schematic_parity,comparison_context)
    worker=h.delivery_kwargs(native_toolchain,experimental_schematic_parity)
    cmp.delivery_path(Path(output).absolute(),comparison_context,'export')
    lifecycle={};record={'schema':1,'kind':KIND,'status':'rejected','export_accepted':False,
        'routing_receipt_accepted':False,'native_validation_performed':False,'applied':False,'new_engine_execution':False,
        'human_pcb_approval_observed':False,'physical_electrical_validation':False,'schematic_parity':'not checked'}
    record.update(h.delivery_record(**ctx))
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    def remaining():return max(0,min(seconds-(time.monotonic()-start),seconds-(h.cpu_seconds()-cpu_start)))
    def cap():
        if remaining()<=0:raise p.Rejected('export whole wall/full CPU budget exhausted')
    job=None
    def account():
        steps=job.steps if job else [];parent=time.process_time()-parent_cpu_start;child=f.child_cpu()-child_cpu_start
        compute=p.sequential_cpu_components(parent,child,steps)
        compute['child_step_cpu_seconds']=compute.pop('child_cpu_seconds')
        record.update(compute,steps=steps,wall_seconds=time.monotonic()-start,native_validation_performed=bool(steps))
        record['within_budget']=record['wall_seconds']<=seconds and record['total_cpu_seconds']<=seconds
    lifecycle.update(record=record,account=account)
    try:
        validate_seconds(seconds)
        # Early native cancellation/failure must retain the declared accounting
        # bounds too; acceptance remains false until all checks finish.
        record.update(budget_seconds=seconds,cpu_budget_seconds=seconds,
            output_ceiling_bytes=OUTPUT_BYTES,output_file_ceiling=OUTPUT_FILES)
        for sig in previous:signal.signal(sig,interrupted)
        with p.validation_readback_session():
            cap();binding,report=bind(choice_path,**ctx);out=h.real_path(output,existing=False)
            if out.exists():raise p.Rejected('export output already exists')
            for protected in [Path(x).parent for x in (binding['source'],binding['receipt'],binding['review'],binding['choice'])]:
                if out==protected or protected in out.parents:raise p.Rejected('export must be outside source/routing/review/choice trees')
            source=Path(binding['source']);class_context=p.class_context_for_record(report,Path(binding['receipt']).parent,input_policy=binding['input_policy'],native_toolchain=native_toolchain)
            original=p.preflight(source,task_scope=p.task_scope_for_record(report,Path(binding['receipt']).parent,input_policy=binding['input_policy']),class_context=class_context);basis,contract,layers=lineage(binding,report,**ctx)
            class_requirement=p.check_schematic_class_support(source,class_context=class_context)
            candidate_capture=pc.inventory(Path(binding['validated_candidate']).parent,contents=True);source_capture=pc.inventory(source.parent,contents=True)
            if {name:h.digest(raw) for name,raw in candidate_capture.items()}!=binding['candidate_hashes'] or {name:h.digest(raw) for name,raw in source_capture.items()}!=binding['source_hashes']:
                raise p.Rejected('export captured authoritative projects changed')
            tools=p.tool_manifest(**({"native_toolchain":native_toolchain} if native_toolchain is not None else {}));runtime=h.runtime_inventory();cap()
            def stable():
                cap()
                if lifecycle.get('created'):h.owned_destination(lifecycle)
                if bind(binding['choice'],**ctx)[0]!=binding or h.runtime_inventory()!=runtime or p.tool_manifest(**({"native_toolchain":native_toolchain} if native_toolchain is not None else {}))!=tools:raise p.Rejected('export original inputs/runtime/tools changed')
                if job and witness(job.out/'snapshot',project=True)!=binding['input_witnesses'][str(source.parent)]:raise p.Rejected('export original snapshot changed')
                if lifecycle.get('evidence') is not None and evidence(out)!=lifecycle['evidence']:raise p.Rejected('export completed evidence changed')
                if native_toolchain is not None or comparison_context is not None:
                    additional=((job.out,record),) if job and lifecycle.get('evidence') is not None else ()
                    def material():
                        bound_material(binding)
                        if h.runtime_inventory()!=runtime:raise p.Rejected('export runtime changed after tool checks')
                        if job and witness(job.out/'snapshot',project=True)!=binding['input_witnesses'][str(source.parent)]:raise p.Rejected('export snapshot changed after tool checks')
                        if lifecycle.get('evidence') is not None and evidence(out)!=lifecycle['evidence']:raise p.Rejected('export evidence changed after tool checks')
                    h.delivery_guards(binding['receipt'],report,native_toolchain,f.read_json(binding['review']).get('preview'),Path(binding['review']).parent,additional=additional,material=material,comparison_context=comparison_context)
                cap()
            stable();out.mkdir(parents=True,exist_ok=False);h.capture_destination(lifecycle,out)
            job=ExportJob(out/'validation',seconds,remaining,protect_local_settings=True,**worker)
            for folder,capture,original_path in [(job.out/'snapshot',source_capture,source.parent),(job.out/'candidate',candidate_capture,Path(binding['validated_candidate']).parent)]:
                folder.mkdir()
                for name in binding['input_witnesses'][str(original_path)]['directories']:(folder/name).mkdir(parents=True,exist_ok=True)
                for name,raw in capture.items():
                    cap();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
                    with target.open('xb') as stream:stream.write(raw)
            candidate=job.out/'candidate'/source.name;del candidate_capture,source_capture
            (job.out/'code').mkdir();code={}
            for rel,digest in tools['implementation_sha256'].items():
                raw=pc.read_bytes(c.ROOT/rel,h.PROJECT_BYTES)
                if h.digest(raw)!=digest:raise p.Rejected('export helper source changed before native')
                target=job.out/'code'/Path(rel).name;target.write_bytes(raw);code[target.name]=digest
            pc.verify_candidate(candidate,binding['source_hashes'],binding['validated_candidate_sha256']);stable()
            protected=p.protected_for_record(report,original)
            names=p.selected_scope_names(report)
            extra={'selected_names':names,'schematic_parity':p.selected_parity_required(report)} if names is not None else {}
            record['schematic_parity']=p.parity_declaration(binding['source'],binding['source_hashes'])
            digest,native=p.validate_candidate(job,original,candidate,binding['source_hashes'],protected,
                default_target_policy='default_target_transport' in report,
                guidance_contract=contract,guidance_basis=basis,layer_contract=layers,class_context=class_context,**extra)
            if class_requirement is not None:record['schematic_class_final']=job.schematic_class_final
            job.native('metrics','metrics',candidate,job.out/'metrics.json');metrics=f.read_json(job.out/'metrics.json');account();cap()
            record.update(inputs=binding,tools=tools,runtime_source_sha256=runtime,code_inventory=code,source_hashes=binding['source_hashes'],
                candidate=str(candidate),candidate_sha256=digest,native=native,native_report_sha256=p.sha(job.out/'final-drc.json'),metrics=metrics,
                budget_seconds=seconds,cpu_budget_seconds=seconds,output_ceiling_bytes=OUTPUT_BYTES,output_file_ceiling=OUTPUT_FILES,
                routing_receipt_accepted=True,original_routing_acceptance='Bound unchanged prior routing receipt, rechecked centrally; not created by this export. Enclosing benchmark delivery/budget eligibility is not inferred.',
                original_routing_receipt_compute={key:report.get(key) for key in ('budget_seconds','cpu_budget_seconds','wall_seconds','total_cpu_seconds')},
                export_compute_scope='Additional user-workflow validation cost, separate from original routing receipt. Any end-to-end workflow comparison must charge this export for every compared system.',
                whole_project_drc_clean=p.native_accepted(native) and native['warnings']==0,
                project_file=str(candidate.with_suffix('.kicad_pro')),original_geometry_and_routing_unchanged=True,
                preview_board_sha256=binding['validated_candidate_sha256'],final_sha_changed_after_refill=digest!=binding['validated_candidate_sha256'],
                acceptance_meaning='Fresh native original-rule validation of the same route/design into a separate project after recorded intent; no GUI rules adopted, source overwritten, live editor applied or human PCB/electrical approval inferred.',
                accounting_point='Prepublication stored sample; entire function and scoped-cache cleanup are measured against wall/full parent-plus-waited-child CPU ceilings. Native process caps poll and can overshoot; no OS aggregate quota or hostile-writer/power-loss authentication.')
            if layers is not None:record['layer_audit']=layers['audit']
            check_stage(job.out,record,binding,report,basis,contract,layers,**ctx);stable();account();cap()
            record.update(status='export_validated',export_accepted=True);lifecycle['evidence']=evidence(out);record['export_evidence']=lifecycle['evidence']
            expected=f.canonical(record);h.owned_destination(lifecycle);p.save_json(out/'export.json',record)
            if f.canonical(f.read_json(out/'export.json'))!=expected:raise p.Rejected('export publication changed')
            _check_export(out/'export.json',cap,**ctx);stable()
            if f.canonical(record)!=expected or f.canonical(f.read_json(out/'export.json'))!=expected:raise p.Rejected('export final metadata changed')
            cap()
        h.owned_destination(lifecycle);cap()  # Include session exit/ownership/cleanup in delivery.
        return record
    except BaseException as exc:
        invalidate(lifecycle,exc)
        if isinstance(exc,KeyboardInterrupt):raise p.Rejected('export cancelled') from exc
        raise
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
