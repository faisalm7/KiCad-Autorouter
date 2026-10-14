"""Unexecuted PAW GND-plane retention factor; no format or production admission."""
from pathlib import Path
import argparse,copy,hashlib,json,math,resource,shutil,signal,stat,sys,time
START=time.monotonic();CPU=time.process_time()+resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h,sexpr as sx,adapter,local_settings,native_edge
from autorouter.runner import run
from experiments.licensed_acquisition_v2 import native_snapshot as source
from experiments.original_project_native_v1.driver import copy_bytes
P1=ROOT/'.runs/paw-format-ses-native-001';P2=ROOT/'.runs/paw-format-ses-native-002';P3=ROOT/'.runs/paw-format-ses-native-003'
LOW=ROOT/'.runs/paw-low-profile-native-001';LOW_EXEC=ROOT/'.runs/paw-low-profile-execution-001';LOW_READER=ROOT/'.runs/paw-low-profile-readback-001'
SECONDS=120;BOOT=3;LIMIT=64*1024**2;WORKER=20*1024**2;RSS=4*1024**3;LOG=256*1024;RESERVE=12
MIN_PRIOR=(46.25840020598844,50.27541)
def need(ok,message):
    if not ok:raise p.Rejected(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()

def experiment(output):
    need(Path(__file__).parent==ROOT/'experiments/paw_retained_plane_v1','promote/review/checkpoint this unused draft first')
    pin_path=Path(__file__).with_name('input-pins.json');pin_raw=pc.read_bytes(pin_path);plan=f.read_json(pin_path)
    need(plan.get('status')=='prospectively_frozen' and plan.get('actor_sha256')==p.sha(__file__) and plan.get('budget_seconds')==SECONDS and plan.get('bootstrap_allowance_seconds')==BOOT,'fresh prospective pins required')
    prior=plan['prior_costs'];charged=[prior['wall_seconds'],prior['full_cpu_seconds']]
    need(all(type(v) in (int,float) and math.isfinite(v) and low<=v<SECONDS-BOOT for v,low in zip(charged,MIN_PRIOR)),'complete measured prefix/reader costs required')
    remaining=lambda:max(0,min(SECONDS-charged[0]-BOOT-(time.monotonic()-START),SECONDS-charged[1]-BOOT-(time.process_time()+f.child_cpu()-CPU)))
    output=local_settings.canonical(Path(output));need(output==ROOT/'.runs/paw-retained-plane-native-001' and not output.exists(),'fresh exact retained-plane leaf output required')
    output.mkdir();owner={};h.capture_destination(owner,output);steps=[];cases={};done={};tools=None;captured=None;hashes=None
    rec=dict(schema=1,kind='paw_retained_plane_leaf',status='running',accepted=False,production_admitted=False,format_admitted=False,qualified=False,
        budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,bootstrap_allowance_seconds=BOOT,prior_costs=prior,input_pins_sha256=digest(pin_raw),steps=steps,cases=cases,
        scope='One plane-retention factor: graphics instead of both; same explicitvia_low25/3 and unchanged geometry/rules. Retained export/obstacles, actual Native and conditional invalid-net checks; never format or production admission.')
    def stable():
        h.owned_destination(owner);need(remaining()>0,'cumulative120wall/fullCPU exhausted');pc.inventory(output,max_bytes=LIMIT,max_files=6000,max_entries=12000)
        need(pc.read_bytes(pin_path)==pin_raw,'prospective pins changed')
        for name,pin in plan['prefixes'].items():
            files,dirs=pc.inventory(ROOT/name,max_bytes=128*1024**2,max_files=6000,max_entries=12000,with_directories=True)
            need(files==pin['files'] and list(dirs)==pin['directories'],'retained prefix changed: '+name)
        for name,pin in plan['code_sha256'].items():need(p.sha(ROOT/name)==pin,'code changed: '+name)
        if tools is not None:
            need(p.tool_manifest()==tools and source.capture()==captured and p.tree_hash(output/'original')==hashes,'runtime/source changed')
            need(p.tree_hash(output/'code')=={Path(n).name:v for n,v in tools['implementation_sha256'].items()},'captured core changed')
            need(p.tree_hash(output/'helper-code')=={n:v for n,v in plan['code_sha256'].items() if n not in tools['implementation_sha256']},'captured helpers changed')
        for folder,pin in done.items():need(pc.evidence_inventory(Path(folder))==pin,'completed evidence changed')
    class Job(f.FloorJob):
        def __init__(self,name):super().__init__(output/name,remaining(),remaining,protect_local_settings=True)
        def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
            stable();available=remaining();cap=available-15-RESERVE if name=='engine' else min(30,available-(RESERVE if self.out.name=='route' else 0))
            need(cap>0,'validation/control reserve exhausted');actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
            item=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=cap,env=self.env,max_log_bytes=LOG,max_workdir_bytes=WORKER,max_group_rss_bytes=RSS)
            item['name']=name;self.steps.append(item);steps.append(item);p.save_json(self.out/(name+'-process.json'),item)
            need(item.get('cleanup_complete') is True and item.get('status') in ('success','nonzero_exit') and item.get('exit_code') in allowed,name+': '+str(item.get('status')))
            return item
    def project(folder,raw):
        payload=dict(captured);payload['paw3395.kicad_pcb']=raw;copy_bytes(payload,folder)
        need(p.tree_hash(folder)=={n:digest(v) for n,v in payload.items()},'complete copied project differs');return folder/'paw3395.kicad_pcb'
    def readback(folder,row,prefill,implementation):
        candidate=folder/'candidate/paw3395.kicad_pcb';saved=folder/'refill'/candidate.name
        before={**hashes,candidate.name:digest((sx.dump(prefill)+'\n').encode())}
        a=f.check_drc_stage(folder,row,'refill-drc',saved,saved,True,before)
        b=f.check_drc_stage(folder,row,'final-drc',candidate,folder/'final-drc-input'/candidate.name,False,{**hashes,candidate.name:row['candidate_sha256']},schematic_parity=True)
        if 'saved_native' in row:need(f.canonical(a)==f.canonical(row['saved_native']),'saved Native summary differs')
        need(f.canonical(b)==f.canonical(row['native']) and p.sha(folder/'final-drc.json')==row['final_report_sha256'],'fresh final report binding differs')
        need((sx.dump(p.transplant_fill(prefill,sx.read(saved)))+'\n').encode()==pc.read_bytes(candidate),'saved/refilled original shell differs')
        p.verify_candidate_files(candidate,hashes,row['candidate_sha256']);p.check_legacy_zone_evidence(folder,original,candidate,implementation=implementation)
        return a,b
    def validate(job,prefill,row):
        candidate=job.out/'candidate/paw3395.kicad_pcb';sx.write(candidate,prefill)
        sha,native=p.validate_candidate(job,original,candidate,hashes,[],schematic_parity=True)
        row.update(candidate=str(candidate),candidate_sha256=sha,native=native,steps=job.steps,final_report_sha256=p.sha(job.out/'final-drc.json'))
        row['saved_native'],_=readback(job.out,row,prefill,tools['implementation_sha256']);p.save_json(job.out/'case.json',row)
        done[str(job.out)]=pc.evidence_inventory(job.out)
    def replay():
        stable()
        if rec.get('qualified') is not True:return
        for job,key,tree in ((route,'route',positive),(negative,'invalid_net',bad_prefill)):
            need(f.canonical(f.read_json(job.out/'case.json'))==f.canonical(cases[key]),'case/display differs');readback(job.out,cases[key],tree,tools['implementation_sha256'])
        need(p.immutable(sx.read(route.out/'imported.kicad_pcb'))==p.immutable(sx.read(P1/'format/original-native.kicad_pcb')),'Native import immutable witness differs')
        f.process_check(route.out,cases['route'],'import',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'import',str(task_input),str(route.out/'imported.kicad_pcb'),str(route.out/'routes.ses')])
        p.check_engine_profile_record(cases['route'],route.out);p.check_native_edge_transport(route.out,cases['route'])
        need(digest(pc.read_bytes(route.out/'edge-adapter-input.dsn'))==cases['route']['before_native_edge_sha256'],'new before-edge witness differs')
        need(f.canonical(f.read_json(route.out/'engine-budget.json'))==f.canonical(cases['route']['engine_budget']),'actual saved engine assignment differs')
        need(p.native_accepted(cases['route']['native']) and not p.native_accepted(cases['invalid_net']['native']),'positive/control outcome differs')
        need(p.transplant_routes(task,sx.read(route.out/'imported.kicad_pcb'),protected=[],policy='exact_non_uuid_lock_position_v2')==positive and p.transplant_routes(task,sx.read(negative.out/'invalid-imported.kicad_pcb'),protected=[],policy='exact_non_uuid_lock_position_v2')==bad_prefill,'exact imported route lineage differs')
        need([s['name'] for s in route.steps]==['engine','import','refill-drc','final-drc'] and [s['name'] for s in negative.steps]==['refill-drc','final-drc'] and f.canonical(steps)==f.canonical(route.steps+negative.steps),'leaf worker census differs')
        local_settings.check_normal_policy(output,rec,max_bytes=LIMIT,max_files=6000);stable()
        for name in pc.inventory(output,max_bytes=LIMIT,max_files=6000,max_entries=12000):
            if name.endswith('.kicad_prl'):
                info=(output/name).lstat();need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_flags==0,'retained PRL metadata differs')
    def account():
        wall=time.monotonic()-START;cpu=time.process_time()+f.child_cpu()-CPU
        rec.update(new_wall_seconds=wall,new_full_cpu_seconds=cpu,charged_wall_seconds=charged[0]+BOOT+wall,charged_full_cpu_seconds=charged[1]+BOOT+cpu,within_budget=remaining()>0)
        if rec['status']!='completed' or not rec['within_budget']:rec['qualified']=False
        rec.update(accepted=False,production_admitted=False,format_admitted=False)
    try:
        captured=source.capture();hashes={n:digest(v) for n,v in captured.items()};need(len(captured)==14 and sum(map(len,captured.values()))==2163350,'fixed14-source population differs')
        copy_bytes(captured,output/'original');source_board=output/'original/paw3395.kicad_pcb';original=sx.read(source_board)
        need(not any(p.locked(n) for n in p.routes(original)),'locked source routing unsupported')
        tools=p.tool_manifest();rec.update(tools=tools,source_hashes=hashes)
        required={str(x.relative_to(ROOT)) for x in (P1,P2,P3,LOW,LOW_EXEC,LOW_READER)}|{'.runs/paw-format-ses-execution-00'+str(n) for n in (1,2,3)}|{'.runs/paw-ses-native003-readback-001'}
        need(required<=set(plan['prefixes']),'complete retained phases and reader prefixes required')
        need(set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT))}<=set(plan['code_sha256']),'mandatory code closure missing')
        copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},output/'code')
        copy_bytes({n:pc.read_bytes(ROOT/n) for n in plan['code_sha256'] if n not in tools['implementation_sha256']},output/'helper-code');p.save_json(output/'prospective-pins.json',plan);stable()
        try:p.preflight(source_board)
        except p.Rejected as exc:need(str(exc)=='unsupported: unqualified board format version','additional source refusal: '+str(exc));rec['production_preflight_refusal']=str(exc)
        else:raise p.Rejected('production format gate changed; refreeze protocol')
        task=sx.read(P1/'route/candidate/paw3395.kicad_pcb');task_raw=pc.read_bytes(P1/'route/candidate/paw3395.kicad_pcb')
        need(not p.routes(task) and p.immutable(task)==p.immutable(original),'retained zero-route source intent differs')
        old=f.read_json(LOW/'result.json');old_row=old['cases']['route'];need(old.get('status')=='failed' and old.get('error')=='Rejected: explicit via_low candidate fails original Native acceptance' and old.get('qualified') is False and old['source_hashes']==hashes,'actual low failure differs')
        old_prefill=p.transplant_routes(task,sx.read(LOW/'route/imported.kicad_pcb'),protected=[],policy='exact_non_uuid_lock_position_v2')
        need(p.immutable(sx.read(LOW/'route/imported.kicad_pcb'))==p.immutable(sx.read(P1/'format/original-native.kicad_pcb')),'actual low imported immutable witness differs')
        _,old_native=readback(LOW/'route',old_row,old_prefill,old['tools']['implementation_sha256'])
        need(tuple(old_native[k] for k in ('opens','blocking','warnings','exclusions'))==(14,0,17,0),'actual low Native counts differ')
        local_settings.check_normal_policy(LOW,old,max_bytes=LIMIT,max_files=6000);rec['prior_failed_candidate']=dict(result_sha256=p.sha(LOW/'result.json'),candidate_sha256=old_row['candidate_sha256'],native=old_native)
        reader=f.read_json(LOW_READER/'result.json');need(reader.get('passed') is True and reader.get('source_result_sha256')==p.sha(LOW/'result.json') and reader.get('candidate_sha256')==old_row['candidate_sha256'],'retained low reader binding differs')
        outer=f.read_json(LOW_EXEC/'execution.json');process=outer['process']
        need(outer.get('outer_qualified') is False and outer.get('source_current') is True and process.get('status')=='nonzero_exit' and type(process.get('exit_code')) is int and process['exit_code']==2 and process.get('cleanup_complete') is True,'retained failed low outer disposition differs')
        costs=[old['charged_wall_seconds'],outer['cumulative_wall_seconds'],old['charged_full_cpu_seconds'],outer['cumulative_full_cpu_seconds'],reader['wall_seconds'],reader['full_cpu_seconds']]
        need(all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in costs),'retained cost schema differs')
        conservative=[max(costs[0:2])+costs[4]+2,max(costs[2:4])+costs[5]+2]
        need(all(v>=bound for v,bound in zip(charged,conservative)),'prior charge omits conservative low/reader costs')
        rec['prior_low_cost_binding']=dict(execution_sha256=p.sha(LOW_EXEC/'execution.json'),reader_sha256=p.sha(LOW_READER/'result.json'),reader_startup_allowance_seconds=2,minimum_wall_seconds=conservative[0],minimum_full_cpu_seconds=conservative[1])
        context=f.read_json(P1/'route/task-export-context.json');before={**hashes,'paw3395.kicad_pcb':digest(task_raw)}
        need(p.tree_hash(P1/'original')==p.tree_hash(P3/'original')==p.tree_hash(LOW/'original')==hashes and p.tree_hash(P2/'route/task-input')==before,'retained full original/task companions differ')
        f.context_binding(context,P1/'route/candidate/paw3395.kicad_pcb',before,'export',p.sha(P1/'route/task-export.dsn'))
        f.process_check(P1/'route',f.read_json(P1/'result.json'),'task-export',f.context_argv('export',P1/'route/candidate/paw3395.kicad_pcb',P1/'route/task-export-context.json',P1/'route/task-export.dsn'))
        f.process_check(P2/'route',f.read_json(P2/'result.json'),'obstacles',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'obstacles',str(P2/'route/task-input/paw3395.kicad_pcb'),str(P2/'route/obstacles.json')])
        route=Job('route');project(route.out/'candidate',task_raw);task_input=project(route.out/'task-input',task_raw);done[str(task_input.parent)]=pc.evidence_inventory(task_input.parent);copy_bytes(captured,route.out/'snapshot')
        for src,name in ((P1/'route/task-export.dsn','native.dsn'),(P2/'route/obstacles.json','obstacles.json')):shutil.copy2(src,route.out/name)
        audit=p.minimum_width_guard(source_board,'graphics');need(audit is not None,'strict minimum width guard required')
        from autorouter import board_floor as g
        terminal=g.audit_export(adapter._parse_dsn(pc.read_bytes(route.out/'native.dsn').decode()),g.qualify(f.read_json(source_board.with_suffix('.kicad_pro')),context,task))
        raw=pc.read_bytes(route.out/'native.dsn');obstacles=f.read_json(route.out/'obstacles.json');edge_context=p.native_edge_context(source_board)
        baseline,_=adapter.adapt_bytes(raw,'both',obstacles);baseline_final,baseline_edge=native_edge.correct(baseline,edge_context)
        need(baseline==pc.read_bytes(LOW/'route/edge-adapter-input.dsn') and baseline_final==pc.read_bytes(LOW/'route/task.dsn') and f.canonical(baseline_edge)==f.canonical(f.read_json(LOW/'route/native-edge-correction.json')),'prior before-edge/identity transport witness differs')
        need(baseline_edge['applied'] is False and baseline_edge['input_sha256']==baseline_edge['output_sha256']==digest(baseline),'original complex-edge transport is not the qualified identity')
        graphics,adapted=adapter.adapt_bytes(raw,'graphics',obstacles);corrected,edge_record=native_edge.correct(graphics,edge_context)
        need(corrected==graphics and edge_record['applied'] is False and edge_record['input_sha256']==edge_record['output_sha256']==digest(graphics),'new before-edge identity witness differs')
        planes=sx.children(sx.one(adapter._parse_dsn(graphics.decode()),'structure'),'plane')
        need(len(planes)==2 and sorted((sx.unquote(n[1]),n[2][1]) for n in planes)==[('GND','B.Cu'),('GND','F.Cu')],'exact original two GND planes not retained')
        (route.out/'edge-adapter-input.dsn').write_bytes(graphics);(route.out/'task.dsn').write_bytes(corrected);p.save_json(route.out/'native-edge-correction.json',edge_record)
        budget=p.engine_profile_settings('tuned',remaining()-RESERVE,strict_class_targets=True,scoring_variant='via_low');budget.update(outer_task_wall_budget_seconds=SECONDS,outer_task_cpu_budget_seconds=SECONDS)
        row=dict(source=str(source_board),source_hashes=hashes,scope='whole_board_unlocked_routing',adapter='graphics',engine_profile='tuned',scoring_variant='via_low',engine_budget=budget,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,minimum_width_guard=audit,steps=route.steps,terminal_audit=terminal,adapter_transformations=adapted,native_edge_correction=edge_record,before_native_edge_sha256=digest(graphics),retained_GND_planes=2)
        cases['route']=row;p.save_json(route.out/'engine-budget.json',budget);p.save_json(route.out/'case.json',row);p.save_json(output/'pre-engine.json',rec);p.check_native_edge_transport(route.out,row)
        (route.out/'engine-config').mkdir();route.step('engine',p.engine_argv(route.out,budget['argv']),already_sandboxed=True);row['optimizer_threshold_audit']=p.optimizer_threshold_audit(route.out/'engine.log',.1)
        route.native('import','import',task_input,route.out/'imported.kicad_pcb',route.out/'routes.ses');imported=sx.read(route.out/'imported.kicad_pcb')
        need(p.immutable(imported)==p.immutable(sx.read(P1/'format/original-native.kicad_pcb')),'Native import changed fixed geometry')
        positive=p.transplant_routes(task,imported,protected=[],policy='exact_non_uuid_lock_position_v2');validate(route,positive,row)
        need(p.native_accepted(row['native']),'retained-plane candidate fails original Native acceptance')
        negative=Job('invalid-net');project(negative.out/'candidate',task_raw);bad=copy.deepcopy(imported);_,resolve=g.source_net_identity(bad);changed=[]
        declared={sx.unquote(n[2]):n[1] for n in sx.children(bad,'net')};target=declared['GND'] if declared else json.dumps('GND')
        for node in p.routes(bad):
            if resolve(sx.one(node,'net'),owner=node)=='MISO':changed.append(sx.unquote(sx.one(node,'uuid')[1]));sx.one(node,'net')[:]=['net',target]
        need(changed and p.immutable(bad)==p.immutable(imported),'wrong imported-MISO control unavailable');sx.write(negative.out/'invalid-imported.kicad_pcb',bad)
        bad_prefill=p.transplant_routes(task,bad,protected=[],policy='exact_non_uuid_lock_position_v2');cases['invalid_net']={'reassigned_MISO_route_UUIDs':changed};validate(negative,bad_prefill,cases['invalid_net'])
        invalid=cases['invalid_net']['native'];need(not p.native_accepted(invalid) and (invalid['opens']>0 or invalid['blocking']>0),'wrong-net control escaped Native rejection')
        rec.update(status='completed',qualified=True,completed_material=done);replay()
    except (Exception,KeyboardInterrupt) as exc:rec.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',qualified=False,error=type(exc).__name__+': '+str(exc))
    return f.publish(output,rec,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if not args.run_native:ap.error('--run-native required after reviewed committed promotion')
    def stop(*_):raise KeyboardInterrupt
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in previous:signal.signal(sig,stop)
        result=experiment(args.output)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print({k:result.get(k) for k in ('status','qualified','error','charged_wall_seconds','charged_full_cpu_seconds')});raise SystemExit(0 if result['qualified'] else 2)
