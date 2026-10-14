"""Experimental placement-backed pruning with explicit deletion/refill lineage.

Ordinary routing retains its SES transport contract. This separate policy reuses
its own fresh accepted search incumbent, shared native checks and old proposals.
It neither relaxes source constraints nor exposes a new production preference.
"""
from __future__ import annotations
from collections import Counter
import copy, datetime, hashlib, math, signal, shutil, time
from pathlib import Path
from . import config as c, pipeline as p, sexpr as sx, strategy as s
from . import floor_route as f, placement_clearance as pc

POLICY='placement-pruning-v1'
STRATEGY='placement-native-pruning-v1'
LIMIT=512*1024**2
MAX_FILES=16000
LEGACY_ALLOCATION='legacy-tuned'
STANDARD_ALLOCATION='standard-85-v1'
STANDARD_INCUMBENT_MAX_SECONDS=85.0

def contract(allocation=LEGACY_ALLOCATION):
    if type(allocation) is not str or allocation not in {LEGACY_ALLOCATION,STANDARD_ALLOCATION}:
        raise p.Rejected('unknown placement pruning allocation')
    value={'schema':1,'policy':POLICY,'strategy':STRATEGY,'incumbent_policy':'placement-search-v1',
        'incumbent_profile':'tuned','incumbent_scoring':'via_default','proposal_policy':'feedback',
        'max_trials':s.MAX_TRIALS,'max_trial_seconds':s.MAX_TRIAL_SECONDS,'min_trial_seconds':s.MIN_TRIAL_SECONDS,
        'final_reserve_seconds':s.FINAL_RESERVE_SECONDS,'feedback_max_depth':s.MAX_FEEDBACK_DEPTH,
        'feedback_max_added_routes':s.MAX_FEEDBACK_ADDED_ROUTES,'output_bytes':LIMIT,'output_files':MAX_FILES}
    if allocation==STANDARD_ALLOCATION:
        value.update(schema=2,allocation=allocation,incumbent_profile='standard',incumbent_max_seconds=STANDARD_INCUMBENT_MAX_SECONDS,
                     proposal_order='individual-first',final_reserve_seconds=25.0)
    return value

def receipt_allocation(data):
    if 'pruning_allocation' not in data:return LEGACY_ALLOCATION
    if data['pruning_allocation']!=STANDARD_ALLOCATION or type(data['pruning_allocation']) is not str:
        raise p.Rejected('unknown or downgraded pruning allocation marker')
    return STANDARD_ALLOCATION

def incumbent_assignment(seconds,wall,cpu,allocation):
    settings=contract(allocation)
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in (seconds,wall,cpu)):
        raise p.Rejected('invalid incumbent allocation observation')
    available=max(0,min(seconds-wall,seconds-cpu)-settings['final_reserve_seconds'])
    return min(settings['incumbent_max_seconds'],available) if allocation==STANDARD_ALLOCATION else available

def check_incumbent_allocation(data,inc):
    """Bind the exact declared profile and finite allocation; central SEARCH checks remain required."""
    allocation=receipt_allocation(data);settings=contract(allocation)
    assigned=data.get('incumbent_assigned_seconds')
    if (inc.get('engine_profile')!=settings['incumbent_profile']
        or inc.get('budget_seconds')!=assigned or inc.get('cpu_budget_seconds')!=assigned
        or type(assigned) not in (int,float) or not math.isfinite(assigned)
        or not 5<=assigned<=data['budget_seconds']-settings['final_reserve_seconds']):
        raise p.Rejected('pruning incumbent allocation/profile differs')
    if allocation==STANDARD_ALLOCATION:
        observed=data.get('incumbent_assignment_observation')
        if (not isinstance(observed,dict) or set(observed)!={'elapsed_wall_seconds','elapsed_full_cpu_seconds'}
            or assigned!=incumbent_assignment(data['budget_seconds'],observed['elapsed_wall_seconds'],observed['elapsed_full_cpu_seconds'],allocation)):
            raise p.Rejected('pruning incumbent assignment differs from frozen allocation')
    elif 'incumbent_assignment_observation' in data:
        raise p.Rejected('legacy pruning receipt has undeclared allocation observation')
    return allocation

def recognize(data,directory):
    marker=Path(directory)/'pruning-contract.json'
    active=(marker.exists() or marker.is_symlink() or data.get('schema')==5
        or data.get('input_policy')==POLICY or data.get('strategy')==STRATEGY or 'pruning_evidence_hashes' in data or 'pruning_allocation' in data)
    if not active:return False
    allocation=receipt_allocation(data);settings=contract(allocation)
    if (type(data.get('schema')) is not int or data['schema']!=5 or data.get('input_policy')!=POLICY
        or data.get('strategy')!=STRATEGY or data.get('baseline')!='C-prototype'
        or data.get('adapter')!='both' or data.get('engine_profile')!=settings['incumbent_profile'] or data.get('scoring_variant')!='via_default'
        or data.get('scope')!='whole_board_unlocked_routing' or data.get('proposal_policy')!='feedback'
        or any(key in data for key in ('routing_preferences','layer_policy','netclass_policy','guidance_policy','diagnostic_schema'))
        or (allocation==LEGACY_ALLOCATION and 'incumbent_assignment_observation' in data)
        or f.read_json(marker)!=settings or data.get('pruning_contract')!={'file':marker.name,'sha256':p.sha(marker)}):
        raise p.Rejected('missing, mixed or downgraded placement pruning policy')
    return True

def evidence_inventory(directory):
    return {name:value for name,value in pc.inventory(directory,max_bytes=LIMIT,max_files=MAX_FILES,max_entries=MAX_FILES*2).items()
        if name not in ('result.json','result.json.partial') and not name.startswith(('invalidated-result-','interrupted-result-'))}

def warnings(native):
    return Counter(f.canonical({'type':x['type'],'items':sorted(i.get('uuid','') for i in x['items'])})
        for x in native['findings'] if x['severity']=='warning')

def improves(metrics,old_metrics,native,old_native):
    length,vias=s._quality(metrics);old_length,old_vias=s._quality(old_metrics)
    return (length<=old_length+1e-9 and vias<=old_vias and (length<old_length-1e-9 or vias<old_vias)
        and warnings(native)<=warnings(old_native))

def deletion(parent,proposal,nets):
    ids=proposal.get('route_ids')
    if not isinstance(ids,list) or not ids or len(ids)!=len(set(ids)):raise p.Rejected('unique deletion IDs required')
    tree=sx.read(parent)
    if any(sx.one(route,'net')[1]!=proposal.get('net') for route in s.eligible_routes(tree,nets,[]) if s.route_id(route) in ids):
        raise p.Rejected('deletion net differs from proposal')
    return s.delete_routes(tree,ids,nets,[])

def feedback_decision(failed,best,best_native,nets):
    if (failed.get('completed') is not True or failed.get('accepted') is not False
        or failed.get('status')!='quality_rejected' or failed.get('parent')!=str(best)):
        raise p.Rejected('feedback must use a completed rejected parent')
    return s.feedback_proposal(sx.read(failed['candidate']),failed['proposal'],failed['native'],best_native,nets,[])


def next_base_proposal(state,best,nets,order='whole-first'):
    """Shared deterministic finite proposal progression, replayed by readback."""
    if type(order) is not str or order not in {'whole-first','individual-first'}:
        raise p.Rejected('unknown pruning proposal order')
    available={s.route_id(x) for x in s.eligible_routes(sx.read(best),nets,[])}
    if order=='individual-first':
        if state['individual'] is None:state['individual']=s.proposals(sx.read(best),nets,[],False)
        while state['individual']:
            proposal=state['individual'].pop(0)
            if set(proposal['route_ids'])<=available:return proposal
        if state['grouped'] is None:state['grouped']=s.proposals(sx.read(best),nets,[],True)
        while state['grouped']:
            proposal=state['grouped'].pop(0)
            if set(proposal['route_ids'])<=available:return proposal
        return None
    while state['grouped']:
        proposal=state['grouped'].pop(0)
        if set(proposal['route_ids'])<=available:return proposal
    if state['individual'] is None:state['individual']=s.proposals(sx.read(best),nets,[],False)
    while state['individual']:
        proposal=state['individual'].pop(0)
        if set(proposal['route_ids'])<=available:return proposal
    return None


def final_freshness(directory,data):
    source=Path(data['source']);pc.verify_candidate(Path(data['candidate']),data['source_hashes'],data['candidate_sha256'])
    if pc.inventory(source.parent)!=data['source_hashes'] or pc.inventory(directory/'snapshot')!=data['source_hashes']:
        raise p.Rejected('pruning source/snapshot changed')
    if evidence_inventory(directory)!=data['pruning_evidence_hashes']:raise p.Rejected('pruning evidence changed')
    recognize(data,directory)

def check_candidate_stage(directory,record,original,source_hashes,basis,before_tree):
    """Shared exact DRC/process checks plus explicit delete/refill reconstruction."""
    candidate=directory/'candidate'/Path(record['candidate']).name
    if str(candidate)!=record['candidate']:raise p.Rejected('pruning candidate path differs')
    pc.verify_candidate(candidate,source_hashes,record['candidate_sha256'])
    if p.immutable(sx.read(candidate))!=p.immutable(original):raise p.Rejected('pruning immutable geometry differs')
    p.check_legacy_zone_evidence(directory,original,candidate)
    before=dict(source_hashes);before[candidate.name]=hashlib.sha256((sx.dump(before_tree)+'\n').encode()).hexdigest()
    refill=directory/'refill'/candidate.name
    f.check_drc_stage(directory,record,'refill-drc',refill,refill,True,before)
    rebuilt=p.transplant_fill(before_tree,sx.read(refill))
    if (sx.dump(rebuilt)+'\n').encode()!=pc.read_bytes(candidate):raise p.Rejected('pruning deletion/refill lineage differs')
    gc=f.read_json(basis/'floor-policy.json')
    if 'source_hashes' in record and record['source_hashes']!=source_hashes:raise p.Rejected('pruning source binding differs')
    f.check_final_context(directory,dict(record,source_hashes=source_hashes),original,candidate,[],gc,guidance_basis=basis)
    expected=dict(source_hashes);expected[candidate.name]=record['candidate_sha256']
    extra={'schematic_parity':True} if record.get('schematic_parity')=='checked by final native DRC' else {}
    native=f.check_drc_stage(directory,record,'final-drc',candidate,directory/'final-drc-input'/candidate.name,False,expected,**extra)
    if native!=record['native'] or p.sha(directory/'final-drc.json')!=record['native_report_sha256']:
        raise p.Rejected('pruning final native record differs')
    f.process_check(directory,record,'metrics',[*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'metrics',str(candidate),str(directory/'metrics.json')])
    metrics=f.read_json(directory/'metrics.json');s._quality(metrics)
    if metrics!=record['metrics'] or metrics.get('version')!='10.0.0':raise p.Rejected('pruning metrics differ')
    stages=[x['name'] for x in record['steps'] if x['cwd']==str(directory)]
    from . import schematic_field_evidence as fields
    expected_stages=['final-drc','floor-final','metrics','refill-drc']
    if fields.has_fields(native['findings']):expected_stages.extend(fields.names('final-drc'))
    if sorted(stages)!=sorted(expected_stages):raise p.Rejected('pruning native stages differ')
    return candidate,native,metrics

def trial_process_history(directory,row):
    """Bind failed workers too; an outer file hash cannot establish their cost."""
    names=('refill-drc','floor-final','final-drc','metrics')
    from . import schematic_field_evidence as fields
    raw_report=directory/'final-drc.json'
    if raw_report.exists():
        raw=f.read_json(raw_report)
        if fields.has_fields(raw.get('violations',[])+raw.get('unconnected_items',[])+raw.get('schematic_parity',[])):
            names=names[:-1]+fields.names('final-drc')+names[-1:]
    steps=row.get('steps');cap=row.get('assigned_seconds')
    if (not isinstance(steps,list) or len(steps)>len(names) or type(cap) not in (int,float)
        or not math.isfinite(cap) or not s.MIN_TRIAL_SECONDS<=cap<=s.MAX_TRIAL_SECONDS):raise p.Rejected('invalid pruning trial allowance/history')
    def number(value):
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise p.Rejected('invalid pruning trial accounting')
        return value
    wall,cpu=number(row.get('wall_seconds')),number(row.get('total_cpu_seconds'))
    if row.get('completed') is True and (wall>cap or cpu>cap):raise p.Rejected('completed pruning attempt exceeds allowance')
    if [x.get('name') for x in steps]!=list(names[:len(steps)]):raise p.Rejected('pruning stage order differs')
    retained={x.name for x in directory.glob('*-process.json')}
    if retained!={name+'-process.json' for name in names[:len(steps)]}:raise p.Rejected('failed pruning process omitted or invented')
    candidate=directory/'candidate'/Path(row['candidate']).name
    def argv(name):
        if name in fields.names('final-drc'):
            return [*f.SANDBOX,*fields.arguments(directory,'final-drc',directory/'final-drc-input'/candidate.name)[fields.names('final-drc').index(name)]]
        if name=='floor-final':return f.context_argv('final',candidate,directory/'floor-final-context.json')
        if name=='metrics':return [*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'metrics',str(candidate),str(directory/'metrics.json')]
        target=directory/('refill' if name=='refill-drc' else 'final-drc-input')/candidate.name
        return [*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones',
            *(['--schematic-parity'] if name=='final-drc' and row.get('schematic_parity')=='checked by final native DRC' else []),'--exit-code-violations',
            '--output',str(directory/(name+'.json')),*(['--save-board'] if name=='refill-drc' else []),str(target)]
    child=monitor=elapsed=0.
    for name,step in zip(names,steps):
        process=f.read_json(directory/(name+'-process.json'))
        if (process.get('name')!=name or process.get('cwd')!=str(directory) or process.get('argv')!=argv(name)
            or any(step.get(key)!=value for key,value in process.items())):raise p.Rejected('failed pruning process/history differs')
        child+=number(process.get('cpu_seconds'));monitor+=number(process.get('monitor_cpu_seconds'));elapsed+=number(process.get('wall_seconds'))
    if elapsed>wall+1e-6 or child+monitor>cpu+1e-6:raise p.Rejected('pruning trial omits retained worker cost')
    return steps


def check_pruning_result(directory,data,original,candidate,protected):
    if protected or p.netclass_policy(candidate) is not None:raise p.Rejected('pruning excludes protected routes or literal classes')
    recognize(data,directory);final_freshness(directory,data)
    settings=contract(receipt_allocation(data));order=settings.get('proposal_order','whole-first')
    basis=directory/'incumbent';receipt=basis/'result.json';inc=f.read_json(receipt)
    check_incumbent_allocation(data,inc)
    if (inc.get('schema')!=4 or inc.get('input_policy')!='placement-search-v1'
        or inc.get('scoring_variant')!='via_default' or inc.get('source')!=data['source'] or inc.get('source_hashes')!=data['source_hashes']
        or inc.get('tools')!=data['tools'] or data.get('incumbent_receipt_sha256')!=p.sha(receipt)
        or inc.get('budget_seconds')!=data.get('incumbent_assigned_seconds')
        or not 5<=inc['budget_seconds']<=data['budget_seconds']-s.FINAL_RESERVE_SECONDS):raise p.Rejected('pruning incumbent contract differs')
    p.check_result(receipt)
    best=Path(inc['candidate']);best_native=inc['native'];best_metrics=inc['metrics'];steps=list(inc['steps'])
    rows=data.get('trials');nets=s.zone_net_ids(original)
    if not isinstance(rows,list) or len(rows)>s.MAX_TRIALS:raise p.Rejected('invalid pruning attempt population')
    if {x.name for x in (directory/'trials').iterdir()}!={f'{i:04d}' for i in range(len(rows))}:raise p.Rejected('missing or omitted pruning attempt')
    improvements=0;proposal_state={'grouped':None if order=='individual-first' else s.proposals(sx.read(best),nets,[],True),'individual':None}
    for i,row in enumerate(rows):
        folder=directory/'trials'/f'{i:04d}'
        if row!=f.read_json(folder/'trial.json') or row.get('index')!=i or row.get('parent')!=str(best) or row.get('parent_sha256')!=p.sha(best):
            raise p.Rejected('pruning parent/attempt record differs')
        proposal=row['proposal']
        if proposal.get('kind')=='native_warning_cleanup':
            parent_index=proposal.get('parent_trial')
            if type(parent_index) is not int or not 0<=parent_index<i:raise p.Rejected('feedback parent differs')
            failed=rows[parent_index]
            decision=feedback_decision(failed,best,best_native,nets)
            if not decision['proposed'] or proposal!=dict(decision['proposal'],parent_trial=parent_index):raise p.Rejected('feedback derivation differs')
        elif proposal!=next_base_proposal(proposal_state,best,nets,order):
            raise p.Rejected('pruning proposal order differs from candidate-only policy')
        before=deletion(best,proposal,nets)
        cap=row.get('assigned_seconds')
        if type(cap) not in (int,float) or not math.isfinite(cap) or not s.MIN_TRIAL_SECONDS<=cap<=s.MAX_TRIAL_SECONDS:raise p.Rejected('pruning trial allowance differs')
        if row.get('completed') is True and any(type(row.get(k)) not in (int,float) or not math.isfinite(row[k]) or not 0<=row[k]<=cap for k in ('wall_seconds','total_cpu_seconds')):
            raise p.Rejected('pruning completed attempt exceeds allowance')
        steps+=trial_process_history(folder,row)
        # Partial failed attempts cannot enter the selected ancestry. Their full
        # files and process costs remain in the complete root inventory/history.
        if row.get('completed') is not True:
            if row.get('completed') is not False or row.get('status')!='failed' or not isinstance(row.get('error'),str) or not row['error'] or row.get('accepted') is not False:raise p.Rejected('incomplete pruning attempt accepted')
            continue
        current,native,metrics=check_candidate_stage(folder,row,original,data['source_hashes'],basis,before)
        eligible=p.native_accepted(native) and improves(metrics,best_metrics,native,best_native)
        expected_status='improved' if eligible else 'quality_rejected' if p.native_accepted(native) else 'drc_rejected'
        if row.get('accepted') is not eligible or row.get('status')!=expected_status:raise p.Rejected('pruning quality/acceptance claim differs')
        if eligible:best,best_native,best_metrics=current,native,metrics;improvements+=1
    if data.get('selected_parent')!=str(best) or data.get('selected_parent_sha256')!=p.sha(best) or data.get('improvements')!=improvements:
        raise p.Rejected('pruning selected ancestry differs')
    current,native,metrics=check_candidate_stage(directory,data,original,data['source_hashes'],basis,sx.read(best))
    if metrics!=best_metrics or not warnings(native)<=warnings(best_native):raise p.Rejected('pruning final quality changed')
    final_steps=[x for x in data['steps'] if x['cwd']==str(directory)]
    if data['steps']!=steps+final_steps:raise p.Rejected('pruning failed stages omitted or duplicated')
    if data.get('source_drc')!=inc['source_drc'] or data.get('task_sha256')!=inc['task_sha256']:raise p.Rejected('pruning original task differs')

def prune(source,output,seconds=120,*,allocation=LEGACY_ALLOCATION):
    def interrupted(*_):raise KeyboardInterrupt
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in previous:signal.signal(sig,interrupted)
        return _prune(source,output,seconds,allocation=allocation)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)

def _prune(source,output,seconds,*,allocation=LEGACY_ALLOCATION):
    start,parent_start,child_start=time.monotonic(),time.process_time(),f.child_cpu()
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 60<=seconds<=900:
        raise p.Rejected('placement pruning budget must be 60–900 seconds')
    settings=contract(allocation);order=settings.get('proposal_order','whole-first');time_reserve=settings['final_reserve_seconds']
    source,output=Path(source).absolute(),Path(output).absolute()
    if any(x.is_symlink() for x in (source,*source.parents,output,*output.parents)):raise p.Rejected('pruning symlink unsupported')
    source=source.resolve(strict=True);output=output.resolve()
    if source.parent==output or source.parent in output.parents:raise p.Rejected('output must be outside original project')
    def remaining(reserve=0):return max(0,min(seconds-(time.monotonic()-start),seconds-(time.process_time()-parent_start+f.child_cpu()-child_start))-reserve)
    job=f.FloorJob(output,seconds,remaining);(output/'trials').mkdir();p.save_json(output/'pruning-contract.json',settings)
    report={'schema':5,'input_policy':POLICY,'strategy':STRATEGY,'baseline':'C-prototype','adapter':'both','engine_profile':settings['incumbent_profile'],'scoring_variant':'via_default',
        'proposal_policy':'feedback','scope':'whole_board_unlocked_routing','source':str(source),'budget_seconds':seconds,'cpu_budget_seconds':seconds,
        'status':'rejected','accepted':False,'physical_electrical_validation':False,'schematic_parity':'not checked','trials':[],'improvements':0,
        'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_routes_used_for_selection':False,'novel_routing_algorithm_claim':False,
        'pruning_contract':{'file':'pruning-contract.json','sha256':p.sha(output/'pruning-contract.json')}}
    if allocation==STANDARD_ALLOCATION:report['pruning_allocation']=allocation
    completed={};all_steps=[];frozen=False;final_inventory=None
    def stable():
        if frozen:
            if p.tool_manifest()!=report['tools'] or pc.inventory(source.parent)!=hashes or pc.inventory(output/'snapshot')!=hashes:raise p.Rejected('pruning original/runtime changed')
            for folder,expected in completed.items():
                if pc.evidence_inventory(Path(folder))!=expected:raise p.Rejected('completed pruning stage changed')
            if final_inventory is not None and evidence_inventory(output)!=final_inventory:raise p.Rejected('completed pruning evidence changed')
        if remaining()<=0:raise p.Rejected('pruning global budget exhausted')
    def account():
        steps=[*all_steps,*job.steps];report.update(steps=steps,wall_seconds=time.monotonic()-start,parent_cpu_seconds=time.process_time()-parent_start,
            child_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in steps),
            peak_child_rss_bytes=max([x.get('max_rss_bytes') or 0 for x in steps]+[0]))
        report['control_child_cpu_seconds']=max(0,f.child_cpu()-child_start-report['child_cpu_seconds']-report['monitor_cpu_seconds'])
        report['total_cpu_seconds']=sum(report[x] for x in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds'))
        report['resource_accounting_point']='Stored totals precede final publication/readback. Entire parent and waited-child CPU and final checks are charged; no hard aggregate quota.'
        if any(x.get('status')=='cancelled' or x.get('cleanup_complete') is not True for x in steps):report.update(accepted=False,status='cancelled')
        if remaining()<=0:report.update(accepted=False,status='budget_exceeded')
        if not report['accepted']:report['whole_project_drc_clean']=False
    try:
        p.check_storage();hashes=pc.inventory(source.parent);original=p.preflight(source);pc.narrow_source(original)
        if any(p.locked(x) for x in p.routes(original)):raise p.Rejected('unsupported: placement pruning excludes protected routing')
        report.update(source_hashes=hashes,tools=p.tool_manifest());shutil.copytree(source.parent,output/'snapshot');(output/'code').mkdir()
        report['schematic_parity']=p.parity_declaration(source,hashes)
        for rel,expected in report['tools']['implementation_sha256'].items():
            dest=output/'code'/Path(rel).name;shutil.copy2(c.ROOT/rel,dest)
            if p.sha(dest)!=expected:raise p.Rejected('pruning code snapshot differs')
        frozen=True;stable()
        if allocation==STANDARD_ALLOCATION:
            observed={'elapsed_wall_seconds':time.monotonic()-start,
                      'elapsed_full_cpu_seconds':time.process_time()-parent_start+f.child_cpu()-child_start}
            report['incumbent_assignment_observation']=observed
            assigned=incumbent_assignment(seconds,observed['elapsed_wall_seconds'],observed['elapsed_full_cpu_seconds'],allocation)
        else:assigned=remaining(time_reserve)
        report['incumbent_assigned_seconds']=assigned
        basis=output/'incumbent'
        inc=f.route(source,basis,assigned,False,'both',settings['incumbent_profile'],'via_default',guidance_policy='placement-search-v1')
        all_steps.extend(inc['steps']);report.update(incumbent_receipt_sha256=p.sha(basis/'result.json'),source_drc=inc.get('source_drc'),task_sha256=inc.get('task_sha256'))
        completed[str(basis)]=pc.evidence_inventory(basis);stable()
        if inc['status']=='cancelled':raise KeyboardInterrupt
        if inc['accepted'] is not True:raise p.Rejected('fresh placement incumbent rejected: '+str(inc.get('reason',inc['status'])))
        p.check_result(basis/'result.json');gc=f.read_json(basis/'floor-policy.json');nets=s.zone_net_ids(original)
        best=Path(inc['candidate']);best_metrics=inc['metrics'];best_native=inc['native'];report['incumbent_metrics']=copy.deepcopy(best_metrics)
        report['incumbent_observation']={'status':'routing_accepted','completed':True,'accepted':True,'elapsed_seconds':time.monotonic()-start,
            'observed_full_cpu_seconds':time.process_time()-parent_start+f.child_cpu()-child_start,'metrics':copy.deepcopy(best_metrics),'candidate_sha256':p.sha(best)}
        def attempt(proposal):
            nonlocal best,best_metrics,best_native
            if len(report['trials'])>=s.MAX_TRIALS or remaining(time_reserve)<s.MIN_TRIAL_SECONDS:return None
            stable()
            # Keep finite complete evidence headroom before creating another full
            # candidate/refill/DRC set. No earlier evidence is removed to fit.
            used=sum((output/name).stat().st_size for name in evidence_inventory(output))
            space_reserve=4*sum((best.parent/name).stat().st_size for name in hashes)+4*1024**2
            if used+space_reserve>LIMIT:report['stop_reason']='complete evidence capacity reserve';return None
            index=len(report['trials']);folder=output/'trials'/f'{index:04d}';trial_start=time.monotonic();trial_cpu=time.process_time()+f.child_cpu()
            cap=min(s.MAX_TRIAL_SECONDS,remaining(time_reserve))
            left=lambda:max(0,min(remaining(time_reserve),cap-(time.monotonic()-trial_start),cap-(time.process_time()+f.child_cpu()-trial_cpu)))
            trial=f.FloorJob(folder,cap,left);candidate=folder/'candidate'/source.name
            row={'index':index,'proposal':proposal,'parent':str(best),'parent_sha256':p.sha(best),'accepted':False,'completed':False,'assigned_seconds':cap,'candidate':str(candidate),'status':'failed'}
            try:
                shutil.copytree(best.parent,candidate.parent);sx.write(candidate,deletion(best,proposal,nets))
                row['schematic_parity']=p.parity_declaration(source,hashes)
                digest,native=p.validate_candidate(trial,original,candidate,hashes,[],guidance_contract=gc,guidance_basis=basis)
                trial.native('metrics','metrics',candidate,folder/'metrics.json');metrics=f.read_json(folder/'metrics.json');pc.verify_candidate(candidate,hashes,digest)
                if left()<=0:raise p.Rejected('trial wall/full CPU cap exhausted')
                row.update(completed=True,candidate_sha256=digest,native=native,native_report_sha256=p.sha(folder/'final-drc.json'),metrics=metrics)
                accepted=p.native_accepted(native) and improves(metrics,best_metrics,native,best_native)
                row.update(accepted=accepted,status='improved' if accepted else 'quality_rejected' if p.native_accepted(native) else 'drc_rejected')
                if accepted:best,best_metrics,best_native=candidate,metrics,native;report['improvements']+=1
            except (Exception,KeyboardInterrupt) as exc:
                row.update(error=type(exc).__name__+': '+str(exc),status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed')
            finally:
                row.update(steps=trial.steps,wall_seconds=time.monotonic()-trial_start,total_cpu_seconds=time.process_time()+f.child_cpu()-trial_cpu,
                    elapsed_seconds=time.monotonic()-start,observed_full_cpu_seconds=time.process_time()-parent_start+f.child_cpu()-child_start)
                all_steps.extend(trial.steps);p.save_json(folder/'trial.json',row);report['trials'].append(row);completed[str(folder)]=pc.evidence_inventory(folder)
            if row['status']=='cancelled' or any(x.get('status')=='cancelled' for x in trial.steps):raise KeyboardInterrupt
            stable();p.save_json(output/'pruning-progress.json',{'trials':report['trials'],'selected':str(best)});return row
        proposal_state={'grouped':None if order=='individual-first' else s.proposals(sx.read(best),nets,[],True),'individual':None}
        while True:
            proposal=next_base_proposal(proposal_state,best,nets,order)
            if proposal is None:break
            row=attempt(proposal)
            if row is None:break
            for _ in range(s.MAX_FEEDBACK_DEPTH):
                if row['status']!='quality_rejected':break
                stable();decision=feedback_decision(row,best,best_native,nets)
                if not decision['proposed']:break
                next_proposal=dict(decision['proposal'],parent_trial=row['index']);row=attempt(next_proposal)
                if row is None:break
        stable()
        if remaining()<12:raise p.Rejected('final native reserve exhausted')
        report.update(selected_parent=str(best),selected_parent_sha256=p.sha(best));candidate=output/'candidate'/source.name;shutil.copytree(best.parent,candidate.parent)
        digest,native=p.validate_candidate(job,original,candidate,hashes,[],guidance_contract=gc,guidance_basis=basis)
        job.native('metrics','metrics',candidate,output/'metrics.json');metrics=f.read_json(output/'metrics.json')
        if metrics!=best_metrics or not warnings(native)<=warnings(best_native):raise p.Rejected('final native quality differs')
        pc.verify_candidate(candidate,hashes,digest);stable()
        report.update(candidate=str(candidate),candidate_sha256=digest,native=native,native_report_sha256=p.sha(output/'final-drc.json'),metrics=metrics,
            invariants_unchanged=True,accepted=p.native_accepted(native),status='routing_accepted' if p.native_accepted(native) else 'drc_rejected',
            whole_project_drc_clean=p.native_accepted(native) and native['warnings']==0)
        final_inventory=evidence_inventory(output);report['pruning_evidence_hashes']=final_inventory
    except (Exception,KeyboardInterrupt) as exc:
        report.update(accepted=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'rejected',reason=type(exc).__name__+': '+str(exc))
    return f.publish(output,report,stable,account,remaining)
