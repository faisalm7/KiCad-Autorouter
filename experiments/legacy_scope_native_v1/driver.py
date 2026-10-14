"""Authored legacy-tag normal workflow control; not a genuine KiCad8 source."""
import time,resource
START=time.monotonic();CPU=time.process_time()+resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
from pathlib import Path
import argparse,copy,hashlib,json,signal,stat,subprocess,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as pc,sexpr as sx,strategy,local_settings,review_export as e
from experiments.original_project_native_v1.driver import copy_bytes
from scripts import qualify_review_export as q
SECONDS=180;RESERVE=15;LIMIT=64*1024**2
FIXTURE={'smoke.kicad_pcb': '618b0b1d23f082283a5136b514ff64ee54b3a058f068689bf64668a436d7c5ea', 'smoke.kicad_prl': '6f5f01de80cb5c992a05bb78b8cb399aa0fb4f8331c514f54674e9cc5918d4f6', 'smoke.kicad_pro': '3f9da762b787baeb0ad1a91ee327990ba35e49d71b4002c435939ec5ad398643'}

def need(ok,message):
    if not ok:raise p.Rejected(message)

def experiment(output):
    need(Path(__file__).parent==ROOT/'experiments/legacy_scope_native_v1','promote/review/commit this draft first')
    output=local_settings.canonical(Path(output));need(output==ROOT/'.runs/legacy-normal-workflow-native-001' and not output.exists(),'fresh exact workflow output required')
    remaining=lambda:max(0,min(SECONDS-(time.monotonic()-START),SECONDS-(time.process_time()+f.child_cpu()-CPU)))
    output.mkdir();owner={};h.capture_destination(owner,output);done={};tools=None;code=None;source_hashes=None;workflow_owner={};fixture_copied=False;helper_pins={}
    workflow_parent=ROOT/'.runs/review-export-native-legacy-scope-001';workflow=workflow_parent/'run'
    rec=dict(schema=1,kind='authored-legacy-normal-workflow-control',status='running',accepted=False,controls_passed=False,routing_accepted=False,
        genuine_kicad8_export=False,full_schematic_claimed=False,human_pcb_approval_observed=False,physical_electrical_validation=False,
        format_wide_support_claimed=False,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,stages={},steps=[],
        scope='Generated version-tag fixture plus explicit owned rules; normal native pruning, rendered review/intent/fresh export and open-route negative. Genuine PAW evidence remains separate.')
    def stable():
        h.owned_destination(owner);need(remaining()>0,'whole180wall/fullCPU exhausted');pc.inventory(output,max_bytes=LIMIT,max_files=8000,max_entries=16000)
        need(p.tree_hash(ROOT/'fixtures/smoke')==FIXTURE,'original smoke fixture changed')
        if fixture_copied:need(p.tree_hash(output/'fixture-original')==FIXTURE,'retained original fixture changed')
        for name,pin in helper_pins.items():need(p.sha(ROOT/name)==pin,'shared workflow helper changed')
        if tools is not None:
            need(p.tool_manifest()==tools and p.sha(__file__)==code,'runtime/controller changed')
            need(p.tree_hash(output/'code')=={Path(n).name:v for n,v in tools['implementation_sha256'].items()},'captured runtime changed')
        if source_hashes is not None:need(p.tree_hash(output/'source')==source_hashes,'owned source changed')
        for path,witness in done.items():need(e.witness(Path(path))==witness,'completed stage changed: '+path)
        if workflow_owner:h.owned_destination(workflow_owner)
    def account():
        rec.update(wall_seconds=time.monotonic()-START,total_cpu_seconds=time.process_time()+f.child_cpu()-CPU)
        rec['within_budget']=remaining()>0;rec['controls_passed']=rec['status']=='completed' and rec['within_budget']
        rec.update(accepted=False,routing_accepted=False,human_pcb_approval_observed=False)
    def progress():
        account();p.save_json(output/'progress.json',rec)
    def replay():
        stable()
        if rec.get('status')!='completed':return
        need(p.check_result(output/'route/result.json')['current'],'normal route proof changed')
        need(e.check_export(workflow/'legacy_scope/export/export.json')['current'],'fresh export proof changed')
        entry=f.read_json(workflow/'legacy_scope/case.json');need(entry.get('passed') is True and entry.get('preview_rendered') is True,'workflow case changed')
        need(f.read_json(workflow/'legacy_scope/rejection/choice.json')['choice']=='reject','reject intent changed')
        row=rec['stages']['open_negative'];candidate=Path(row['candidate']);saved=negative.out/'refill'/candidate.name
        negative_prefill=copy.deepcopy(sx.read(Path(route['candidate'])));negative_prefill[:]=[n for n in negative_prefill if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
        for zone in sx.children(negative_prefill,'zone'):zone[:]=[n for n in zone if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
        need(p.immutable(negative_prefill)==p.immutable(original) and hashlib.sha256((sx.dump(negative_prefill)+'\n').encode()).hexdigest()==row['prefill_sha256'],'negative prefill reconstruction differs')
        before={**source_hashes,candidate.name:row['prefill_sha256']}
        refill_native=f.check_drc_stage(negative.out,row,'refill-drc',saved,saved,True,before)
        final_native=f.check_drc_stage(negative.out,row,'final-drc',candidate,negative.out/'final-drc-input'/candidate.name,False,{**source_hashes,candidate.name:row['candidate_sha256']})
        need(final_native==row['native'] and refill_native==row['saved_native'] and final_native['opens']>0 and not p.native_accepted(final_native),'open-route negative no longer rejects')
        need(p.sha(negative.out/'final-drc.json')==row['native_report_sha256'] and not p.routes(sx.read(candidate)),'negative report/copper changed')
        need((sx.dump(p.transplant_fill(negative_prefill,sx.read(saved)))+'\n').encode()==pc.read_bytes(candidate),'negative original-shell fill lineage changed')
        p.verify_candidate_files(candidate,source_hashes,row['candidate_sha256']);local_settings.check_normal_policy(output,rec,max_bytes=LIMIT,max_files=8000)
        for name in pc.inventory(output,max_bytes=LIMIT,max_files=8000,max_entries=16000):
            if name.endswith('.kicad_prl'):
                item=(output/name).lstat();need(stat.S_ISREG(item.st_mode) and item.st_nlink==1 and item.st_flags==0,'owned PRL flags/identity not restored')
        stable()
    try:
        p.check_storage();tools=p.tool_manifest();code=p.sha(__file__);helper_pins={n:p.sha(ROOT/n) for n in ('scripts/qualify_review_export.py','experiments/original_project_native_v1/driver.py')};rec.update(tools=tools,controller_sha256=code,fixture_hashes=FIXTURE,shared_helper_sha256=helper_pins)
        raw=subprocess.run(['git','show',tools['git_head']+':experiments/legacy_scope_native_v1/driver.py'],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout
        need(hashlib.sha256(raw).hexdigest()==code,'commit exact control before Native')
        payload={n:pc.read_bytes(ROOT/'fixtures/smoke'/n) for n in FIXTURE};need({n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}==FIXTURE,'fixed fixture pins differ')
        copy_bytes(payload,output/'fixture-original');fixture_copied=True;need(p.tree_hash(output/'fixture-original')==FIXTURE,'original fixture copy differs')
        copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},output/'code')
        owned=dict(payload);needle=b'(version 20260206)';need(owned['smoke.kicad_pcb'].count(needle)==1,'unique generated tag required');owned['smoke.kicad_pcb']=owned['smoke.kicad_pcb'].replace(needle,b'(version 20240108)',1)
        project=json.loads(owned['smoke.kicad_pro']);need(set(project)=={'meta'},'owned augmentation must not overwrite source constraints')
        project.update(net_settings={'classes':[{'name':'Default','track_width':.25,'clearance':.2,'via_diameter':.8,'via_drill':.4}], 'netclass_patterns':[],'netclass_assignments':None},
            board={'design_settings':{'rules':{'min_track_width':.2,'min_via_diameter':.4,'min_through_hole_diameter':.3,'min_via_annular_width':.05,'min_clearance':.1,'min_copper_edge_clearance':0},'rule_severities':{},'drc_exclusions':[]}})
        owned['smoke.kicad_pro']=(json.dumps(project,indent=2,sort_keys=True)+'\n').encode();copy_bytes(owned,output/'source');source_board=output/'source/smoke.kicad_pcb';source_hashes=p.tree_hash(source_board.parent)
        need(owned['smoke.kicad_prl']==payload['smoke.kicad_prl'] and not source_board.with_suffix('.kicad_sch').exists(),'PRL/noSCH source differs')
        rec.update(source=str(source_board),source_hashes=source_hashes,owned_changes={'board':'single literal version20260206->20240108 only; generator/body unchanged','project_original':json.loads(payload['smoke.kicad_pro']),'project_generated':project,'prl':'exact original bytes','note':'Authored tagged-current-body control, never genuine KiCad8 export'});progress();stable()
        original=p.preflight(source_board,task_scope=('whole_board_unlocked_routing','native','source_all'))
        need(remaining()>120+RESERVE,'insufficient whole budget before fresh incumbent120')
        route=strategy.prune(source_board,output/'route',120,proposal_policy='feedback',incumbent_scoring='via_high');rec['steps'].extend(route.get('steps',[]))
        rec['stages']['pruning']={'receipt':str(output/'route/result.json'),'receipt_sha256':p.sha(output/'route/result.json'),'accepted':route.get('accepted'),'schema':route.get('schema')};progress()
        need(route.get('schema')==1 and route.get('accepted') is True,'fresh native pruning did not accept');need(p.check_result(output/'route/result.json')['current'],'normal pruning receipt rejected')
        local_settings.check_normal_policy(output/'route',route,max_bytes=LIMIT,max_files=8000);done[str(output/'route')]=e.witness(output/'route');stable();progress()
        need(not workflow_parent.exists() and remaining()>30+RESERVE,'fresh workflow path/budget required');workflow_parent.mkdir();h.capture_destination(workflow_owner,workflow_parent)
        old_cases,old_seconds=q.CASES,q.SECONDS
        try:
            q.CASES=(('legacy_scope','.runs/legacy-normal-workflow-native-001/route/result.json',1,True),);q.SECONDS=remaining()-RESERVE
            result=q.qualify(workflow,run_native=True)
        finally:q.CASES,q.SECONDS=old_cases,old_seconds
        rec['stages']['review_export']={'result':str(workflow/'result.json'),'result_sha256':p.sha(workflow/'result.json'),'controls_passed':result.get('controls_passed')};progress()
        need(result.get('controls_passed') is True,'rendered review/intent/fresh export failed');done[str(workflow)]=e.witness(workflow);stable()
        need(remaining()>8,'insufficient budget for saved/final open negative')
        negative=f.FloorJob(output/'open-negative',remaining(),remaining,protect_local_settings=True);copy_bytes(owned,negative.out/'candidate')
        candidate=negative.out/'candidate/smoke.kicad_pcb';prefill=copy.deepcopy(sx.read(Path(route['candidate'])));prefill[:]=[n for n in prefill if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
        for zone in sx.children(prefill,'zone'):zone[:]=[n for n in zone if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
        need(p.immutable(prefill)==p.immutable(original) and not p.routes(prefill),'negative altered original geometry');sx.write(candidate,prefill)
        row={'steps':negative.steps,'prefill_sha256':p.sha(candidate)};rec['stages']['open_negative']=row
        try:
            candidate_hash,native=p.validate_candidate(negative,original,candidate,source_hashes,[],schematic_parity=False)
            row.update(candidate=str(candidate),candidate_sha256=candidate_hash,native=native,native_report_sha256=p.sha(negative.out/'final-drc.json'))
            saved=negative.out/'refill'/candidate.name;row['saved_native']=f.check_drc_stage(negative.out,row,'refill-drc',saved,saved,True,{**source_hashes,candidate.name:row['prefill_sha256']})
            f.check_drc_stage(negative.out,row,'final-drc',candidate,negative.out/'final-drc-input'/candidate.name,False,{**source_hashes,candidate.name:candidate_hash})
            need(native['opens']>0 and not p.native_accepted(native),'route removal did not reject opens')
        finally:rec['steps'].extend(negative.steps);p.save_json(negative.out/'case.json',row);progress()
        done[str(negative.out)]=e.witness(negative.out);rec.update(status='completed');replay()
    except (Exception,KeyboardInterrupt) as exc:rec.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',initial_failure=type(exc).__name__+': '+str(exc),reason=type(exc).__name__+': '+str(exc))
    return f.publish(output,rec,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if not args.run_native:ap.error('--run-native required')
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def stop(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,stop)
        result=experiment(args.output)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(f.canonical({k:result.get(k) for k in ('status','controls_passed','accepted','wall_seconds','total_cpu_seconds')}));raise SystemExit(0 if result.get('controls_passed') else 2)
