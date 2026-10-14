"""Only corrected fixed-placement SES import and missing PAW Native validation.

Promote/review/freeze input-pins before explicit execution. No whitelist patch,
preflight monkeypatch, source migration, repeated prior DRC or routing gain claim.
"""
from pathlib import Path
import argparse, copy, hashlib, json, resource, shutil, signal, stat, sys, time
BOOT_WALL=time.monotonic()
BOOT_CPU=time.process_time()+resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h, placement_clearance as io, sexpr as sx
from autorouter import board_floor as g, adapter, local_settings
from autorouter.runner import run
from experiments.licensed_acquisition_v2 import native_snapshot as source
from experiments.original_project_native_v1.driver import copy_bytes
from experiments.kicad8_native_compat_continuation_v1 import driver as continuation
from experiments.kicad8_native_compat_v1 import driver as prior

SECONDS=120;BOOTSTRAP_ALLOWANCE=3;LIMIT=64*1024**2;WORKER_LIMIT=20*1024**2
PREFIX=ROOT/'.runs/paw-format-ses-native-001';EXECUTION=ROOT/'.runs/paw-format-ses-execution-001'
FIRST_WALL=6.000073082977906;FIRST_CPU=5.19436
SECOND=ROOT/'.runs/paw-format-ses-native-002';SECOND_EXECUTION=ROOT/'.runs/paw-format-ses-execution-002'
SECOND_WALL=10.981839040992782;SECOND_CPU=14.475297
PRIOR_WALL=16.981912123970687;PRIOR_CPU=19.669657
GROUP_RSS=4*1024**3;LOG_LIMIT=256*1024;NEGATIVE_RESERVE=12
EXTRA=('experiments/licensed_acquisition_v2/native_snapshot.py','experiments/licensed_acquisition_v2/protocol.json',
       'experiments/licensed_acquisition_v1/fetch.py','experiments/licensed_acquisition_v1/protocol.json',
       'experiments/original_project_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py',
       'experiments/kicad8_native_compat_v1/driver.py','experiments/kicad8_native_compat_v1/fixture.py',
       'experiments/kicad8_native_compat_continuation_v1/driver.py','experiments/lipo_native_diagnostic_v1/driver.py',
       'experiments/paw_format_ses_v1/actor.py','experiments/paw_format_ses_continuation_v1/actor.py')


def experiment(output):
    if Path(__file__).parent!=ROOT/'experiments/paw_ses_fixed_placement_v1':
        raise p.Rejected('UNUSED draft: promote, review and checkpoint before Native')
    plan_path=Path(__file__).with_name('input-pins.json');plan_raw=io.read_bytes(plan_path);plan=f.read_json(plan_path)
    if (plan.get('status')!='prospectively_frozen' or plan.get('budget_seconds')!=SECONDS
            or plan.get('bootstrap_allowance_seconds')!=BOOTSTRAP_ALLOWANCE
            or plan.get('actor_sha256')!=p.sha(__file__)):
        raise p.Rejected('fresh reviewed prospective actor/pins required')
    output=local_settings.canonical(Path(output))
    if output!=ROOT/'.runs/paw-format-ses-native-003' or output.exists():raise p.Rejected('fresh fixed-placement003 output required')
    output.mkdir();owner={};h.capture_destination(owner,output)
    steps=[];completed={};rows={};frozen=False;captured=None;source_hashes=None;tools=None;retained=None;engine_proof=None
    record=dict(schema=1,kind='paw_fixed_placement_ses_continuation',status='running',accepted=False,
        production_admitted=False,format_admitted=False,qualified=False,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,
        bootstrap_allowance_seconds=BOOTSTRAP_ALLOWANCE,retained_cap_bytes=LIMIT,
        worker_caps=dict(workdir_bytes=WORKER_LIMIT,group_rss_bytes=GROUP_RSS,log_bytes=LOG_LIMIT),steps=steps,
        cases=rows,planned_cases=['route','invalid_net'],planned_new_format_workers=0,
        retained_native_workers=8,retained_engine_workers=1,planned_new_workers=5,
        prior_outer_wall_seconds=PRIOR_WALL,prior_outer_full_cpu_seconds=PRIOR_CPU,
        prior_costs=plan.get('prior_costs'),input_pins_sha256=hashlib.sha256(plan_raw).hexdigest(),
        scope='Reuse actual001 format/export and actual002 obstacles/engine/rawSES. Run corrected import and fresh positive/invalid Native only. Preserve both failures and full cumulative120wall/fullCPU; never production or format admission.')
    def require(ok,message):
        if not ok:raise p.Rejected(message)
    def remaining():
        return max(0,min(SECONDS-PRIOR_WALL-BOOTSTRAP_ALLOWANCE-(time.monotonic()-BOOT_WALL),
                         SECONDS-PRIOR_CPU-BOOTSTRAP_ALLOWANCE-(time.process_time()+f.child_cpu()-BOOT_CPU)))
    def prefix_check():
        for name,pin in plan['prefixes'].items():
            files,dirs=io.inventory(ROOT/name,max_bytes=128*1024**2,max_files=6000,max_entries=12000,with_directories=True)
            require(files==pin['files'] and list(dirs)==pin['directories'],'retained prefix changed: '+name)
    def stable():
        h.owned_destination(owner);require(remaining()>0,'whole120wall/fullCPU exhausted')
        io.inventory(output,max_bytes=LIMIT,max_files=6000,max_entries=12000)
        if not frozen:return
        require(io.read_bytes(plan_path)==plan_raw,'prospective input pins changed')
        require(source.capture()==captured and p.tree_hash(output/'original')==source_hashes,'acquired/original source changed')
        require(p.tool_manifest()==tools,'current runtime/code/HEAD changed');prefix_check()
        for name,pin in plan['code_sha256'].items():require(p.sha(ROOT/name)==pin,'helper code changed: '+name)
        require(p.tree_hash(output/'code')=={Path(n).name:v for n,v in tools['implementation_sha256'].items()},'retained core code changed')
        require(p.tree_hash(output/'helper-code')=={n:v for n,v in plan['code_sha256'].items() if n not in tools['implementation_sha256']},'retained helper code changed')
        for name,pin in completed.items():require(io.evidence_inventory(Path(name))==pin,'completed stage material changed')
    class Job(f.FloorJob):
        def __init__(self,name):super().__init__(output/name,remaining(),remaining,protect_local_settings=True)
        def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
            stable();available=remaining();cap=min(30,available)
            if self.out.name=='route':cap=min(cap,available-NEGATIVE_RESERVE)
            require(cap>0,'worker finalization reserve exhausted')
            actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
            result=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=cap,env=self.env,
                max_log_bytes=LOG_LIMIT,max_workdir_bytes=WORKER_LIMIT,max_group_rss_bytes=GROUP_RSS)
            result['name']=name;self.steps.append(result);steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
            if result['status'] not in ('success','nonzero_exit') or result.get('exit_code') not in allowed or result.get('cleanup_complete') is not True:
                raise p.Rejected(name+': '+str(result['status'])+' exit='+str(result.get('exit_code')))
            return result
    def freeze(job):completed[str(job.out)]=io.evidence_inventory(job.out);stable()
    def copy_input(target,board_raw):
        payload=dict(captured);payload['paw3395.kicad_pcb']=board_raw;copy_bytes(payload,target)
        require(p.tree_hash(target)=={n:hashlib.sha256(b).hexdigest() for n,b in payload.items()},'owned copy differs')
        return target/'paw3395.kicad_pcb'
    def retained_phase():
        """Read actual001 at its real paths with its captured producer, never re-export."""
        prefix_check();old=f.read_json(PREFIX/'result.json');execution=f.read_json(EXECUTION/'execution.json')
        prior_plan=f.read_json(PREFIX/'prospective-pins.json');old_tools=old['tools']
        require(old.get('schema')==1 and old.get('kind')=='paw_oldformat_native_ses_diagnostic'
            and old.get('status')=='failed' and all(old.get(k) is False for k in ('accepted','qualified','production_admitted','format_admitted'))
            and old.get('error')=="ValueError: unknown DSN child scope: ('pcb', 'library', 'padstack', 'shape')"
            and old.get('source_hashes')==source_hashes,'retained001 disposition/source differs')
        require(execution.get('wall_seconds')==FIRST_WALL and execution.get('total_cpu_seconds')==FIRST_CPU
            and execution.get('outer_qualified') is False and execution.get('source_current') is True
            and execution.get('whole_delivery_within_budget') is True
            and f.canonical(execution.get('tools'))==f.canonical(old_tools),'retained001 outer accounting differs')
        process=execution['process']
        require(process.get('status')=='nonzero_exit' and type(process.get('exit_code')) is int and process['exit_code']==2
            and process.get('cleanup_complete') is True and process.get('cwd')==str(EXECUTION)
            and process.get('argv')==[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/paw_format_ses_v1/actor.py'),
                                     '--run-native','--output',str(PREFIX)]
            and p.sha(EXECUTION/'command.log')==execution.get('log_sha256'),'retained001 outer producer/process differs')
        require(p.sha(PREFIX/'prospective-pins.json')==old.get('input_pins_sha256')==execution.get('protocol_sha256')
            and prior_plan.get('status')=='prospectively_frozen'
            and prior_plan.get('actor_sha256')==prior_plan['code_sha256'].get('experiments/paw_format_ses_v1/actor.py'),
            'retained001 prospective producer pins differ')
        require(p.tree_hash(PREFIX/'code')=={Path(n).name:v for n,v in old_tools['implementation_sha256'].items()}
            and p.tree_hash(PREFIX/'helper-code')=={n:v for n,v in prior_plan['code_sha256'].items() if n not in old_tools['implementation_sha256']},
            'retained001 captured producer code differs')
        for name,pin in prior_plan['prefixes'].items():require(plan['prefixes'].get(name)==pin,'retained001 prior prefix binding differs')
        for key in ('files','kicad','freerouting','normal_drc_local_settings_policy'):
            require(f.canonical(tools.get(key))==f.canonical(old_tools.get(key)),'retained001 runtime identity differs: '+key)
        require(p.tree_hash(PREFIX/'original')==source_hashes and p.tree_hash(PREFIX/'route/snapshot')==source_hashes,
            'retained001 complete originals differ')
        format_out=PREFIX/'format';format_row=f.read_json(format_out/'diagnostic.json')
        require(set(old.get('cases',{}))=={'format'} and f.canonical(old['cases']['format'])==f.canonical(format_row)
            and len(format_row.get('steps',[]))==5 and len(old.get('steps',[]))==6
            and f.canonical(old['steps'][:5])==f.canonical(format_row['steps']), 'retained001 completed worker census differs')
        original_board=PREFIX/'original/paw3395.kicad_pcb'
        inputs={label:format_out/(label+'-input/paw3395.kicad_pcb') for label in ('original','saved','shell')}
        require(io.read_bytes(inputs['original'])==captured[original_board.name], 'retained original emission input differs')
        require(io.read_bytes(inputs['saved'])==io.read_bytes(ROOT/'.runs/core-prl-native-controls-001/positive/refill/paw3395.kicad_pcb')
            ==io.read_bytes(ROOT/'.runs/paw3395-original-native-002/saved/paw3395.kicad_pcb')
            and io.read_bytes(inputs['shell'])==io.read_bytes(ROOT/'.runs/core-prl-native-controls-001/positive/candidate/paw3395.kicad_pcb')
            ==io.read_bytes(ROOT/'.runs/paw3395-original-native-002/candidate/paw3395.kicad_pcb'), 'retained saved/shell continuity differs')
        for label,board in inputs.items():
            expected={**source_hashes,board.name:p.sha(board)}
            require(p.tree_hash(board.parent)==expected,'retained emission input companions differ')
            f.process_check(format_out,format_row,label+'-native',[*f.SANDBOX,str(prior.c.PYTHON),str(ROOT/'autorouter/native.py'),
                'roundtrip',str(board),str(format_out/(label+'-native.kicad_pcb'))])
        base_path=ROOT/'.runs/paw3395-native-diagnostic-001/observation.json';base=f.read_json(base_path)
        base_board=Path(base['source']);base_dsn=base_path.parent/'native.dsn'
        f.context_binding(base,base_board,p.tree_hash(base_board.parent),'export',p.sha(base_dsn))
        require(base['board_sha256']==source_hashes[original_board.name]
            and format_row.get('original_context_sha256')==p.sha(base_path)
            and format_row.get('original_dsn_sha256')==p.sha(base_dsn),'retained original observation differs')
        emissions={}
        native_original=sx.read(format_out/'original-native.kicad_pcb')
        for label in ('saved','shell'):
            context=f.read_json(format_out/(label+'-export-context.json'));board=inputs[label]
            f.context_binding(context,board,p.tree_hash(board.parent),'export',p.sha(format_out/(label+'-export.dsn')))
            f.process_check(format_out,format_row,label+'-export',f.context_argv('export',board,
                format_out/(label+'-export-context.json'),format_out/(label+'-export.dsn')))
            require(f.canonical(prior.geometry(context))==f.canonical(prior.geometry(base)),'retained reloaded Native geometry differs')
            emissions[label]=continuation.emission_equal_by_uuid(native_original,sx.read(format_out/(label+'-native.kicad_pcb')))
        require(f.canonical(emissions)==f.canonical(format_row.get('emissions')),'retained Native emission witness differs')
        task_board=PREFIX/'route/candidate/paw3395.kicad_pcb';context_path=PREFIX/'route/task-export-context.json'
        dsn=PREFIX/'route/task-export.dsn';native_dsn=PREFIX/'route/native.dsn';context=f.read_json(context_path)
        expected={**source_hashes,task_board.name:hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest()}
        require(io.read_bytes(task_board)==(sx.dump(task)+'\n').encode() and p.tree_hash(task_board.parent)==expected,
            'retained exported task differs from independent zero-route original task')
        f.context_binding(context,task_board,expected,'export',p.sha(dsn))
        f.process_check(PREFIX/'route',old,'task-export',f.context_argv('export',task_board,context_path,dsn))
        require(io.read_bytes(native_dsn)==io.read_bytes(dsn)==io.read_bytes(PREFIX/'route/task.dsn')
            and not (PREFIX/'route/engine-process.json').exists(),'retained raw task export or stopped phase differs')
        require(context.get('routing_accepted') is False and context.get('native_version')=='10.0.0','retained task observation scope differs')
        prefix_check()
        return dict(directory=str(PREFIX.relative_to(ROOT)),result_sha256=p.sha(PREFIX/'result.json'),
            execution_sha256=p.sha(EXECUTION/'execution.json'),producer_tools=old_tools,format=format_row,
            original_native_emission_sha256=p.sha(format_out/'original-native.kicad_pcb'),
            task_export=dict(source=str(task_board),source_hashes=expected,context_sha256=p.sha(context_path),
                raw_dsn_sha256=p.sha(dsn),process_sha256=p.sha(PREFIX/'route/task-export-process.json'),
                step=old['steps'][5],fresh_task_bytes_equal=True,provenance_rebased=False,native_reexecuted=False),
            successful_native_workers=6,prior_outer_wall_seconds=FIRST_WALL,prior_outer_full_cpu_seconds=FIRST_CPU)
    def retained_engine():
        """Actual002 producer/provenance, not a reconstructed budget assignment."""
        prefix_check();old=f.read_json(SECOND/'result.json');execution=f.read_json(SECOND_EXECUTION/'execution.json')
        prior_plan=f.read_json(SECOND/'prospective-pins.json');old_tools=old['tools'];folder=SECOND/'route'
        require(old.get('schema')==1 and old.get('kind')=='paw_oldformat_native_ses_continuation'
            and old.get('status')=='failed' and old.get('error')=='Rejected: native SES import changed original native nonroute intent'
            and all(old.get(k) is False for k in ('accepted','qualified','production_admitted','format_admitted'))
            and old.get('source_hashes')==source_hashes and old.get('cases')=={}
            and f.canonical(old.get('retained_phase'))==f.canonical(retained), 'retained002 disposition/source differs')
        require(execution.get('wall_seconds')==SECOND_WALL and execution.get('total_cpu_seconds')==SECOND_CPU
            and execution.get('cumulative_wall_seconds')==PRIOR_WALL and execution.get('cumulative_full_cpu_seconds')==PRIOR_CPU
            and execution.get('outer_qualified') is False and execution.get('source_current') is True
            and execution.get('whole_delivery_within_budget') is True
            and f.canonical(execution.get('tools'))==f.canonical(old_tools),'retained002 outer accounting differs')
        process=execution['process']
        require(process.get('status')=='nonzero_exit' and type(process.get('exit_code')) is int and process['exit_code']==2
            and process.get('cleanup_complete') is True and process.get('cwd')==str(SECOND_EXECUTION)
            and process.get('argv')==[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/paw_format_ses_continuation_v1/actor.py'),
                '--run-native','--output',str(SECOND)]
            and p.sha(SECOND_EXECUTION/'command.log')==execution.get('log_sha256'),'retained002 outer producer/process differs')
        require(p.sha(SECOND/'prospective-pins.json')==old.get('input_pins_sha256')==execution.get('protocol_sha256')
            and prior_plan.get('status')=='prospectively_frozen'
            and prior_plan.get('actor_sha256')==prior_plan['code_sha256'].get('experiments/paw_format_ses_continuation_v1/actor.py'),
            'retained002 prospective producer pins differ')
        require(p.tree_hash(SECOND/'code')=={Path(n).name:v for n,v in old_tools['implementation_sha256'].items()}
            and p.tree_hash(SECOND/'helper-code')=={n:v for n,v in prior_plan['code_sha256'].items() if n not in old_tools['implementation_sha256']},
            'retained002 captured producer code differs')
        for name,pin in prior_plan['prefixes'].items():require(plan['prefixes'].get(name)==pin,'retained002 prior prefix binding differs')
        for key in ('files','kicad','freerouting','normal_drc_local_settings_policy'):
            require(f.canonical(tools.get(key))==f.canonical(old_tools.get(key)),'retained002 runtime identity differs: '+key)
        task_hashes=retained['task_export']['source_hashes'];task_board=folder/'task-input/paw3395.kicad_pcb'
        require(p.tree_hash(SECOND/'original')==source_hashes and p.tree_hash(folder/'snapshot')==source_hashes
            and p.tree_hash(task_board.parent)==task_hashes and p.tree_hash(folder/'candidate')==task_hashes
            and io.read_bytes(task_board)==io.read_bytes(PREFIX/'route/candidate/paw3395.kicad_pcb'), 'retained002 complete task/original differs')
        require(io.read_bytes(folder/'native.dsn')==io.read_bytes(PREFIX/'route/task-export.dsn')
            and io.read_bytes(folder/'retained-task-export-context.json')==io.read_bytes(PREFIX/'route/task-export-context.json'),
            'retained002 raw export/context differs')
        require(len(old.get('steps',[]))==3 and [s.get('name') for s in old['steps']]==['obstacles','engine','import']
            and not (folder/'refill-drc-process.json').exists() and not (folder/'final-drc-process.json').exists(),
            'retained002 stopped worker census differs')
        for name,args in [('obstacles',['obstacles',str(task_board),str(folder/'obstacles.json')]),
                          ('import',['import',str(task_board),str(folder/'imported.kicad_pcb'),str(folder/'routes.ses')])]:
            f.process_check(folder,old,name,[*f.SANDBOX,str(prior.c.PYTHON),str(ROOT/'autorouter/native.py'),*args])
        reference=p.engine_profile_settings('tuned',96,strict_class_targets=True)
        engine=f.process_check(folder,old,'engine',p.engine_argv(folder,reference['argv']))
        require(engine.get('log_truncated') is False and engine.get('log')==str(folder/'engine.log')
            and engine.get('log_bytes')==len(io.read_bytes(folder/'engine.log')),'retained engine log differs')
        threshold=p.optimizer_threshold_audit(folder/'engine.log',.1)
        adapted,adapter_record=adapter.adapt_bytes(io.read_bytes(folder/'native.dsn'),'both',f.read_json(folder/'obstacles.json'))
        edge_record=f.read_json(folder/'native-edge-correction.json')
        edge_data=dict(source=str(SECOND/'original/paw3395.kicad_pcb'),source_hashes=source_hashes,
            adapter='both',scope='whole_board_unlocked_routing',adapter_transformations=adapter_record,native_edge_correction=edge_record)
        p.check_native_edge_transport(folder,edge_data)
        require(io.read_bytes(folder/'edge-adapter-input.dsn')==adapted,'retained engine adapter input differs')
        require(p.immutable(sx.read(folder/'imported.kicad_pcb'))!=p.immutable(sx.read(PREFIX/'format/original-native.kicad_pcb')),
            'retained002 original exact-placement failure disappeared')
        prefix_check()
        return dict(directory=str(SECOND.relative_to(ROOT)),result_sha256=p.sha(SECOND/'result.json'),
            execution_sha256=p.sha(SECOND_EXECUTION/'execution.json'),producer_tools=old_tools,steps=old['steps'],
            raw_ses_sha256=p.sha(folder/'routes.ses'),task_dsn_sha256=p.sha(folder/'task.dsn'),
            raw_import_sha256=p.sha(folder/'imported.kicad_pcb'),obstacles_sha256=p.sha(folder/'obstacles.json'),
            native_edge_correction=edge_record,adapter_transformations=adapter_record,optimizer_threshold_audit=threshold,
            canonical_argv_reference=dict(profile='tuned',reference_input_seconds=96,strict_class_targets=True,argv=reference['argv'],
                use='canonical argv comparison only; not a recovered budget or assignment',
                actual_remaining_assignment_recorded=False,implied_remaining_interval_seconds=[96,97],upper_bound_exclusive=True),
            prior_outer_wall_seconds=SECOND_WALL,prior_outer_full_cpu_seconds=SECOND_CPU,engine_reexecuted=False)
    def route_records(board):
        result=[];seen=set()
        for route in p.routes(board):
            ids=sx.children(route,'uuid')
            require(len(ids)==1 and len(ids[0])==2 and type(ids[0][1]) is str and ids[0][1] and ids[0][1] not in seen,
                'ambiguous regenerated route UUID')
            seen.add(ids[0][1]);result.append(sx.dump([n for n in route if n is not ids[0]]))
        require(result,'retained SES imported no routes')
        return sorted(result)
    def wrong_net(imported):
        bad=copy.deepcopy(imported);_,resolve=g.source_net_identity(bad)
        declared={sx.unquote(n[2]):n[1] for n in sx.children(bad,'net')}
        target=declared['GND'] if declared else json.dumps('GND');changed=[]
        for node in p.routes(bad):
            net=sx.one(node,'net')
            if resolve(net,owner=node)=='MISO':changed.append(sx.unquote(sx.one(node,'uuid')[1]));net[:]=['net',target]
        require(changed and p.immutable(bad)==p.immutable(imported),'invalid imported MISO-net control unavailable')
        return bad,changed
    def drc_replay(job,row,prefill):
        candidate=job.out/'candidate/paw3395.kicad_pcb';refill=job.out/'refill'/candidate.name
        before={**source_hashes,candidate.name:hashlib.sha256((sx.dump(prefill)+'\n').encode()).hexdigest()}
        saved=f.check_drc_stage(job.out,row,'refill-drc',refill,refill,True,before)
        require((sx.dump(p.transplant_fill(prefill,sx.read(refill)))+'\n').encode()==io.read_bytes(candidate),'SES/refill lineage differs')
        final=f.check_drc_stage(job.out,row,'final-drc',candidate,job.out/'final-drc-input'/candidate.name,False,
            {**source_hashes,candidate.name:row['candidate_sha256']},schematic_parity=True)
        require(f.canonical(final)==f.canonical(row['native']),'final Native summary differs')
        p.verify_candidate_files(candidate,source_hashes,row['candidate_sha256'])
        p.check_legacy_zone_evidence(job.out,original,candidate,implementation=tools['implementation_sha256'])
        return saved,final
    def finish_candidate(job,prefill):
        candidate=job.out/'candidate/paw3395.kicad_pcb';sx.write(candidate,prefill)
        digest,native=p.validate_candidate(job,original,candidate,source_hashes,[],schematic_parity=True)
        row=dict(candidate=str(candidate),candidate_sha256=digest,native=native,steps=job.steps,
                 final_report_sha256=p.sha(job.out/'final-drc.json'))
        row['saved_native'],_=drc_replay(job,row,prefill);return row
    def flags_last():
        for directory in (output,PREFIX,SECOND):
            files=io.inventory(directory,max_bytes=LIMIT,max_files=6000,max_entries=12000)
            for name in files:
                if name.endswith('.kicad_prl'):
                    info=(directory/name).lstat()
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_flags==0,'retained PRL metadata differs')
    def replay():
        stable()
        if record.get('qualified') is not True:return
        require(f.canonical(retained_phase())==f.canonical(retained)==f.canonical(record.get('retained_phase'))
            ==f.canonical(f.read_json(output/'retained-phase.json')),'retained001 witness changed')
        require(f.canonical(retained_engine())==f.canonical(engine_proof)==f.canonical(record.get('retained_engine'))
            ==f.canonical(f.read_json(output/'retained-engine.json')),'retained002 engine/provenance witness changed')
        for job,key in ((route,'route'),(negative,'invalid_net')):
            require(f.canonical(f.read_json(job.out/'diagnostic.json'))==f.canonical(rows[key]),'nested/display receipt differs')
        require(io.read_bytes(task_input)==io.read_bytes(PREFIX/'route/candidate/paw3395.kicad_pcb')
            and io.read_bytes(route.out/'native.dsn')==io.read_bytes(PREFIX/'route/task-export.dsn')
            and io.read_bytes(route.out/'retained-task-export-context.json')==io.read_bytes(PREFIX/'route/task-export-context.json')
            and io.read_bytes(route.out/'routes.ses')==io.read_bytes(SECOND/'route/routes.ses')
            and f.canonical(rows['route']['retained_task_export'])==f.canonical(retained['task_export'])
            and f.canonical(rows['route']['retained_engine'])==f.canonical(engine_proof),
            'fresh task/raw DSN/retained export binding differs')
        current_context=f.read_json(PREFIX/'route/task-export-context.json')
        audited=g.audit_export(adapter._parse_dsn(io.read_bytes(route.out/'native.dsn').decode()),
            g.qualify(f.read_json(task_input.with_suffix('.kicad_pro')),current_context,task))
        require(f.canonical(audited)==f.canonical(rows['route']['terminal_audit']),'complete terminal/class witness differs')
        f.process_check(route.out,rows['route'],'import',[*f.SANDBOX,str(prior.c.PYTHON),str(ROOT/'autorouter/native.py'),
            'import',str(task_input),str(route.out/'imported.kicad_pcb'),str(route.out/'routes.ses')])
        imported=sx.read(route.out/'imported.kicad_pcb')
        require(p.immutable(imported)==p.immutable(sx.read(PREFIX/'format/original-native.kicad_pcb')),
            'imported Native immutable witness changed')
        records=route_records(imported)
        require(records==route_records(sx.read(SECOND/'route/imported.kicad_pcb'))
            and rows['route']['route_equivalence']==dict(policy='exact-route-multiset-except-regenerated-uuid-v1',route_count=len(records),
                route_records_sha256=hashlib.sha256(f.canonical(records).encode()).hexdigest()),'corrected import route fields/multiplicity differ')
        require((sx.dump(p.transplant_routes(task,imported,protected=[],policy='exact_non_uuid_lock_position_v2'))+'\n').encode()
            ==(sx.dump(positive_prefill)+'\n').encode(),'positive SES transplant changed')
        bad,changed=wrong_net(imported)
        require(bad==sx.read(negative.out/'invalid-imported.kicad_pcb') and changed==rows['invalid_net']['reassigned_MISO_route_UUIDs']
            and p.transplant_routes(task,bad,protected=[],policy='exact_non_uuid_lock_position_v2')==negative_prefill,
            'invalid imported-net control derivation changed')
        p.check_native_edge_transport(route.out,rows['route'])
        drc_replay(route,rows['route'],positive_prefill);drc_replay(negative,rows['invalid_net'],negative_prefill)
        require(p.native_accepted(rows['route']['native']) and not p.native_accepted(rows['invalid_net']['native'])
            and (rows['invalid_net']['native']['opens']>0 or rows['invalid_net']['native']['blocking']>0),'positive/invalid Native outcome changed')
        require([step['name'] for step in route.steps]==['import','refill-drc','final-drc']
            and [step['name'] for step in negative.steps]==['refill-drc','final-drc']
            and f.canonical(steps)==f.canonical(route.steps+negative.steps),'continuation worker census differs')
        local_settings.check_normal_policy(output,record,max_bytes=LIMIT,max_files=6000)
        stable()
        flags_last()
    def account():
        wall=time.monotonic()-BOOT_WALL;cpu=time.process_time()+f.child_cpu()-BOOT_CPU
        record.update(new_wall_seconds=wall,new_full_cpu_seconds=cpu,wall_seconds=PRIOR_WALL+wall,total_cpu_seconds=PRIOR_CPU+cpu,
            charged_wall_seconds=PRIOR_WALL+wall+BOOTSTRAP_ALLOWANCE,
            charged_full_cpu_seconds=PRIOR_CPU+cpu+BOOTSTRAP_ALLOWANCE,within_budget=remaining()>0)
        if record['status']!='completed' or not record['within_budget']:record['qualified']=False
        record.update(accepted=False,production_admitted=False,format_admitted=False)
    try:
        captured=source.capture();source_hashes={n:hashlib.sha256(b).hexdigest() for n,b in captured.items()}
        require(len(captured)==14 and sum(map(len,captured.values()))==2163350,'complete fixed PAW population differs')
        copy_bytes(captured,output/'original');original_board=output/'original/paw3395.kicad_pcb';original=sx.read(original_board)
        require(sx.one(original,'version')==['version','20240108'],'original version differs')
        require(not any(p.locked(n) for n in p.routes(original)),'zero-route task excludes protected source routes')
        tools=p.tool_manifest();record.update(tools=tools,source_hashes=source_hashes)
        require(tools.get('normal_drc_local_settings_policy')==local_settings.JOB_POLICY,'normal policy code closure required before diagnostic')
        require({str(folder.relative_to(ROOT)) for folder in (PREFIX,EXECUTION,SECOND,SECOND_EXECUTION)}<=set(plan['prefixes']),
            'complete actual001/002 actor and outer-execution prefixes required')
        names=set(tools['implementation_sha256'])|set(EXTRA)|{str(Path(__file__).relative_to(ROOT))}
        require(set(plan['code_sha256'])==names,'prospective code closure differs')
        require(all(p.sha(ROOT/n)==v for n,v in plan['code_sha256'].items()),'prospective current code differs')
        copy_bytes({Path(n).name:io.read_bytes(ROOT/n) for n in tools['implementation_sha256']},output/'code')
        copy_bytes({n:io.read_bytes(ROOT/n) for n in names if n not in tools['implementation_sha256']},output/'helper-code')
        p.save_json(output/'prospective-pins.json',plan)
        try:p.preflight(original_board)
        except p.Rejected as exc:
            require(str(exc)=='unsupported: unqualified board format version','additional source support refusal: '+str(exc))
            record['production_preflight_refusal']=str(exc)
        else:raise p.Rejected('format gate changed; freeze a new protocol')
        frozen=True;stable()
        task=copy.deepcopy(original);task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
        for zone in sx.children(task,'zone'):zone[:]=[n for n in zone if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
        require(not p.routes(task) and p.immutable(task)==p.immutable(original),'independent unrouting changed source intent')
        retained=retained_phase();record['retained_phase']=copy.deepcopy(retained);p.save_json(output/'retained-phase.json',retained)
        engine_proof=retained_engine();record['retained_engine']=copy.deepcopy(engine_proof);p.save_json(output/'retained-engine.json',engine_proof)
        task_raw=io.read_bytes(SECOND/'route/task-input/paw3395.kicad_pcb')
        route=Job('route');candidate=copy_input(route.out/'candidate',task_raw)
        task_input=copy_input(route.out/'task-input',task_raw)
        completed[str(task_input.parent)]=io.evidence_inventory(task_input.parent)
        copy_bytes(captured,route.out/'snapshot')
        task_context=f.read_json(PREFIX/'route/task-export-context.json')
        shutil.copy2(PREFIX/'route/task-export-context.json',route.out/'retained-task-export-context.json')
        for name in ('native.dsn','task.dsn','routes.ses','obstacles.json','edge-adapter-input.dsn','native-edge-correction.json'):
            shutil.copy2(SECOND/'route'/name,route.out/name)
        qualified=g.qualify(f.read_json(candidate.with_suffix('.kicad_pro')),task_context,task)
        terminal_audit=g.audit_export(adapter._parse_dsn(io.read_bytes(route.out/'native.dsn').decode()),qualified)
        route.native('import','import',task_input,route.out/'imported.kicad_pcb',route.out/'routes.ses')
        imported=sx.read(route.out/'imported.kicad_pcb')
        require(p.immutable(imported)==p.immutable(sx.read(PREFIX/'format/original-native.kicad_pcb')),'native SES import changed original native nonroute intent')
        records=route_records(imported)
        require(records==route_records(sx.read(SECOND/'route/imported.kicad_pcb')),'fixed-placement import changed absolute routing')
        positive_prefill=p.transplant_routes(task,imported,protected=[],policy='exact_non_uuid_lock_position_v2')
        rows['route']=finish_candidate(route,positive_prefill)
        rows['route'].update(source=str(original_board),source_hashes=source_hashes,scope='whole_board_unlocked_routing',adapter='both',
            budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,
            terminal_audit=terminal_audit,retained_task_export=copy.deepcopy(retained['task_export']),
            retained_engine=copy.deepcopy(engine_proof),adapter_transformations=engine_proof['adapter_transformations'],
            native_edge_correction=engine_proof['native_edge_correction'],
            route_equivalence=dict(policy='exact-route-multiset-except-regenerated-uuid-v1',route_count=len(records),
                route_records_sha256=hashlib.sha256(f.canonical(records).encode()).hexdigest()),
            task_sha256=hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest(),native_dsn_sha256=p.sha(route.out/'native.dsn'),
            task_dsn_sha256=p.sha(route.out/'task.dsn'),ses_sha256=p.sha(route.out/'routes.ses'),imported_sha256=p.sha(route.out/'imported.kicad_pcb'))
        require(p.native_accepted(rows['route']['native']),'SES candidate fails original Native acceptance')
        p.save_json(route.out/'diagnostic.json',rows['route']);freeze(route)
        negative=Job('invalid-net');copy_input(negative.out/'candidate',(sx.dump(task)+'\n').encode())
        bad,changed=wrong_net(imported)
        sx.write(negative.out/'invalid-imported.kicad_pcb',bad)
        negative_prefill=p.transplant_routes(task,bad,protected=[],policy='exact_non_uuid_lock_position_v2')
        rows['invalid_net']=finish_candidate(negative,negative_prefill);rows['invalid_net']['reassigned_MISO_route_UUIDs']=changed
        invalid=rows['invalid_net']['native']
        require(not p.native_accepted(invalid) and (invalid['opens']>0 or invalid['blocking']>0),'invalid imported-net control escaped fresh Native rejection')
        p.save_json(negative.out/'diagnostic.json',rows['invalid_net']);freeze(negative)
        record.update(status='completed',qualified=True,completed_material=completed);replay()
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',qualified=False,error=type(exc).__name__+': '+str(exc))
    f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=replay)
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.run_native:parser.error('explicit --run-native required')
    def interrupted(signum,frame):raise KeyboardInterrupt
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in handlers:signal.signal(sig,interrupted)
        result=experiment(args.output)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
    print({k:result.get(k) for k in ('status','qualified','error','charged_wall_seconds','charged_full_cpu_seconds')})
    raise SystemExit(0 if result['qualified'] else 2)
