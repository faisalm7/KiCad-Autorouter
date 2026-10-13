def check_stage(folder,data,binding,report,basis,contract,layers):
    """Reuse original-rule refill/final/process/native-context validators."""
    original=p.preflight(Path(binding['source']));candidate=folder/'candidate'/Path(binding['source']).name
    before=sx.read(Path(binding['validated_candidate']));protected=[r for r in p.routes(original) if report['scope']=='partial_completion' or p.locked(r)]
    if candidate!=Path(data['candidate']):raise p.Rejected('export candidate escaped validation directory')
    pc.verify_candidate(candidate,binding['source_hashes'],data['candidate_sha256'])
    if p.immutable(sx.read(candidate))!=p.immutable(original) or p.routes(sx.read(candidate))!=p.routes(before):
        raise p.Rejected('export changed original geometry or validated route copper')
    if contract is not None:
        ps.check_candidate_stage(folder,data,original,binding['source_hashes'],basis,before)
    else:
        expected=dict(binding['source_hashes']);expected[candidate.name]=binding['validated_candidate_sha256']
        refill=folder/'refill'/candidate.name
        f.check_drc_stage(folder,data,'refill-drc',refill,refill,True,expected)
        if (sx.dump(p.transplant_fill(before,sx.read(refill)))+'\n').encode()!=pc.read_bytes(candidate):raise p.Rejected('export refill reconstruction changed')
        expected[candidate.name]=data['candidate_sha256']
        native=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/candidate.name,False,expected)
        if native!=data['native']:raise p.Rejected('export actual final native report differs')
        if p.netclass_policy(candidate) is not None:
            native_classes=f.read_json(folder/'final-netclasses.json');audited=p.audit_candidate_netclasses(candidate,protected,native_classes)
            audited['native_map_file_sha256']=p.sha(folder/'final-netclasses.json')
            if f.read_json(folder/'final-netclass-audit.json')!=audited:raise p.Rejected('export original native class targets changed')
            f.process_check(folder,data,'final-netclasses',[*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(folder/'final-netclasses.json')])
        f.process_check(folder,data,'metrics',[*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'metrics',str(candidate),str(folder/'metrics.json')])
    if any(r not in p.routes(sx.read(candidate)) for r in protected):raise p.Rejected('export protected copper changed')
    if layers is not None and p.audit_layer_contract(candidate,layers)!=data.get('layer_audit'):raise p.Rejected('export captured layer contract changed')
    metrics=f.read_json(folder/'metrics.json')
    if (p.sha(folder/'final-drc.json')!=data['native_report_sha256'] or metrics!=data['metrics'] or metrics.get('version')!='10.0.0'
        or metrics!=report['metrics'] or not p.native_accepted(data['native'])
        or data['native']['ignored_checks']!=report['native']['ignored_checks'] or not ps.warnings(data['native'])<=ps.warnings(report['native'])):
        raise p.Rejected('fresh export native acceptance/metrics/warnings/original ignore settings differ')
    expected_names=['refill-drc',*(['floor-final'] if contract is not None else ['final-netclasses'] if p.netclass_policy(candidate) is not None else []),'final-drc','metrics']
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

def export(choice_path,output,seconds=SECONDS):
    """Validate the original bound candidate into a new project; never copy GUI rules."""
    start=time.monotonic();parent_cpu_start=time.process_time();child_cpu_start=f.child_cpu();cpu_start=parent_cpu_start+child_cpu_start
    lifecycle={};record={'schema':1,'kind':KIND,'status':'rejected','export_accepted':False,
        'routing_receipt_accepted':False,'native_validation_performed':False,'applied':False,'new_engine_execution':False,
        'human_pcb_approval_observed':False,'physical_electrical_validation':False,'schematic_parity':'not checked'}
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    def remaining():return max(0,min(seconds-(time.monotonic()-start),seconds-(h.cpu_seconds()-cpu_start)))
    def cap():
        if remaining()<=0:raise p.Rejected('export whole wall/full CPU budget exhausted')
    job=None
    def account():
        steps=job.steps if job else [];parent=time.process_time()-parent_cpu_start;child=f.child_cpu()-child_cpu_start
        native=sum(s.get('cpu_seconds') or 0 for s in steps);monitor=sum(s.get('monitor_cpu_seconds') or 0 for s in steps)
        record.update(steps=steps,wall_seconds=time.monotonic()-start,total_cpu_seconds=parent+child+monitor,
            parent_cpu_seconds=parent,child_step_cpu_seconds=native,control_child_cpu_seconds=child-native,
            monitor_cpu_seconds=monitor,native_validation_performed=bool(steps))
        record['within_budget']=record['wall_seconds']<=seconds and record['total_cpu_seconds']<=seconds
    lifecycle.update(record=record,account=account)
    try:
        if not finite(seconds) or not 30<=seconds<=SECONDS:raise p.Rejected('export budget must be30–120 seconds')
        for sig in previous:signal.signal(sig,interrupted)
        with p.validation_readback_session():
            cap();binding,report=bind(choice_path);out=h.real_path(output,existing=False)
            if out.exists():raise p.Rejected('export output already exists')
            for protected in [Path(x).parent for x in (binding['source'],binding['receipt'],binding['review'],binding['choice'])]:
                if out==protected or protected in out.parents:raise p.Rejected('export must be outside source/routing/review/choice trees')
            source=Path(binding['source']);original=p.preflight(source);basis,contract,layers=lineage(binding,report)
            candidate_capture=pc.inventory(Path(binding['validated_candidate']).parent,contents=True);source_capture=pc.inventory(source.parent,contents=True)
            if {name:h.digest(raw) for name,raw in candidate_capture.items()}!=binding['candidate_hashes'] or {name:h.digest(raw) for name,raw in source_capture.items()}!=binding['source_hashes']:
                raise p.Rejected('export captured authoritative projects changed')
            tools=p.tool_manifest();runtime=h.runtime_inventory();cap()
            def stable():
                cap()
                if lifecycle.get('created'):h.owned_destination(lifecycle)
                if bind(binding['choice'])[0]!=binding or h.runtime_inventory()!=runtime or p.tool_manifest()!=tools:raise p.Rejected('export original inputs/runtime/tools changed')
                if job and witness(job.out/'snapshot',project=True)!=binding['input_witnesses'][str(source.parent)]:raise p.Rejected('export original snapshot changed')
                if lifecycle.get('evidence') is not None and evidence(out)!=lifecycle['evidence']:raise p.Rejected('export completed evidence changed')
                cap()
            stable();out.mkdir(parents=True,exist_ok=False);h.capture_destination(lifecycle,out)
            job=ExportJob(out/'validation',seconds,remaining)
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
            protected=[r for r in p.routes(original) if report['scope']=='partial_completion' or p.locked(r)]
            digest,native=p.validate_candidate(job,original,candidate,binding['source_hashes'],protected,
                guidance_contract=contract,guidance_basis=basis,layer_contract=layers)
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
            check_stage(job.out,record,binding,report,basis,contract,layers);stable();account();cap()
            record.update(status='export_validated',export_accepted=True);lifecycle['evidence']=evidence(out);record['export_evidence']=lifecycle['evidence']
            expected=f.canonical(record);h.owned_destination(lifecycle);p.save_json(out/'export.json',record)
            if f.canonical(f.read_json(out/'export.json'))!=expected:raise p.Rejected('export publication changed')
            _check_export(out/'export.json',cap);stable()
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

def check_resource_accounting(data, *, child_key='child_cpu_seconds'):
    """Shared sequential receipt budgets and finite parent/child CPU algebra."""
    def number(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise Rejected('invalid resource accounting')
        return value
    steps=data['steps']
    wall,budget=number(data.get('wall_seconds')),number(data.get('budget_seconds'))
    cpu_budget=number(data.get('cpu_budget_seconds'))
    if not 5<=cpu_budget<=900 or number(data.get('total_cpu_seconds'))>cpu_budget:
        raise Rejected('receipt exceeds its recorded CPU budget')
    if not 5<=budget<=900 or wall>budget or sum(number(step.get('wall_seconds')) for step in steps)>wall+1e-6:
        raise Rejected('receipt exceeds its recorded wall budget')
    child=sum(number(step.get('cpu_seconds')) for step in steps)
    monitor=sum(number(step.get('monitor_cpu_seconds')) for step in steps)
    control_child=number(data.get('control_child_cpu_seconds',0))
    if (abs(number(data.get(child_key))-child)>1e-6
            or abs(number(data.get('monitor_cpu_seconds'))-monitor)>1e-6
            or abs(number(data.get('total_cpu_seconds'))-(number(data.get('parent_cpu_seconds'))+child+monitor+control_child))>1e-6):
        raise Rejected('inconsistent CPU accounting')
