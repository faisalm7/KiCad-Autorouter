"""Prospective ROOT-controlled native alias roundtrip. Not production admission."""
import json,shutil,signal,sys,time
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(HERE)]
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx
from autorouter.runner import run
from experiments.pic_mixed_transport_probe_v1 import ses_native as sn
from padless_alias import plan,normalize_dsn,unused_class_proof
from retained_ses import build
SECONDS=60.;LIMIT=32*1024**2
SOURCE=ROOT/'.data/corpus-expansion-audit-001/sparkfun__SparkFun_Roller_Encoder_Breakout'
NAME='SparkFun_Roller_Encoder_Breakout.kicad_pcb'
def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=4000,max_entries=8000)
class Job(f.FloorJob):
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        a=list(map(str,argv));permitted=(len(a)==9 and a[:2]==[str(c.PYTHON),str(HERE/'worker.py')]) or a[:3]==[str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'import'] or a[:3]==[str(c.CLI),'pcb','drc'] or a[:4]==[str(c.CLI),'sch','export','netlist'] or a[:3]==[str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'fields']
        if not permitted or already_sandboxed or self.remaining()<=0:raise p.Rejected('fixed native dispatch/shared budget required')
        result=run([*f.SANDBOX,*a],cwd=self.out,log=self.out/(name+'.log'),timeout=min(30,self.remaining()),env=self.env,max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected(name+': '+result['status'])
        return result

def experiment(output,*,run_native=False):
    if run_native is not True:raise p.Rejected('ROOT sequential lane only')
    previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for s in previous:signal.signal(s,interrupted)
        return _experiment(output)
    finally:
        for s,handler in previous.items():signal.signal(s,handler)

def _experiment(output):
    start=time.monotonic();cpu0=h.cpu_seconds();remaining=lambda:max(0,min(SECONDS+start-time.monotonic(),SECONDS+cpu0-h.cpu_seconds()))
    out=h.real_path(output,existing=False)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('exclusive fresh direct .runs output required')
    job=Job(out,SECONDS,remaining);ownership={};h.capture_destination(ownership,out);runtime={};tools=None;material={};pins=f.read_json(HERE/'native-pins.json')
    record={'schema':1,'kind':'roller-export-alias-native-v1','accepted':False,'production_support':False,'controls_passed':False,'status':'incomplete','engine_execution':False,'seconds':SECONDS,'full_cpu_cap_seconds':SECONDS,'output_ceiling_bytes':LIMIT}
    def owned():h.owned_destination(ownership)
    def stable():
        owned()
        for name,digest in pins['files_sha256'].items():
            if p.sha(ROOT/name)!=digest:raise p.Rejected('pinned source/evidence/helper changed: '+name)
        if inventory(SOURCE)!=pins['source_inventory']:raise p.Rejected('original source population changed')
        if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('tool/code/HEAD changed')
        if any(p.sha(ROOT/n)!=v for n,v in runtime.items()):raise p.Rejected('committed runtime freeze changed')
        for n,v in material.items():
            if p.sha(out/n)!=v:raise p.Rejected('completed evidence changed: '+n)
    def account():
        record.update(wall_seconds=time.monotonic()-start,full_cpu_seconds=h.cpu_seconds()-cpu0,steps=job.steps)
        if remaining()<=0 or sum((out/n).stat().st_size for n in inventory(out))>LIMIT:record.update(status='budget_exceeded',controls_passed=False)
        if record['status']!='controls_passed':record['controls_passed']=False
    def packet(where):
        where.mkdir();shutil.copytree(SOURCE/'Hardware',where/'input');inp=where/'input';notices=inp/'_licenses/creator';notices.mkdir(parents=True)
        for n in ('LICENSE.md','README.md'):shutil.copy2(SOURCE/n,notices/n)
        return inp/NAME
    try:
        stable();tools=p.tool_manifest();extras=[HERE/n for n in ('driver.py','worker.py','retained_ses.py','padless_alias.py','native-pins.json','PROTOCOL.json')]
        runtime=io.capture_freeze({**tools,'implementation_sha256':{**tools['implementation_sha256'],**{str(x.relative_to(ROOT)):p.sha(x) for x in extras}}})['files_sha256']
        record.update(tools=tools,runtime_source_sha256=runtime,pins=pins)
        baseline=f.read_json(ROOT/'.runs/roller-no-export-continuation-001/result.json')['original_native'];exports={};normalized=[]
        for namespace in ('A','B'):
            stage='export-'+namespace;case=out/namespace;board=packet(case);before=inventory(board.parent);ctx=case/'context.json';dsn=case/'native.dsn';diag=case/'diagnostic.json';emission=case/'before.kicad_pcb'
            argv=[c.PYTHON,HERE/'worker.py',board,ctx,dsn,diag,namespace,emission,case/'after.kicad_pcb'];job.step(stage,argv);f.process_check(out,{'steps':job.steps},stage,[*f.SANDBOX,*map(str,argv)])
            context=f.read_json(ctx);f.context_binding(context,board,before,'final',None);extra=f.read_json(diag);events=f.read_json(case/'alias-evidence.json')
            if extra['dsn_sha256'] is not None or extra['observation_before_export']!=extra['observation_after_export'] or events['dsn_sha256']!=p.sha(dsn):raise p.Rejected('same-load diagnostic/export binding differs')
            binding=plan(board.read_bytes(),namespace);normalized.append(normalize_dsn(dsn.read_bytes(),board.read_bytes(),binding));classproof=unused_class_proof(board.read_bytes(),board.with_suffix('.kicad_pro').read_bytes(),context,dsn.read_bytes())
            exports[namespace]={'board':board,'dsn':dsn,'emission':emission,'binding':binding,'class_proof':classproof};stable()
        if normalized[0]!=normalized[1]:raise p.Rejected('dual native alias namespaces differ outside authorized placement identity')
        a=exports['A'];original=sx.read(a['board']);raw,filtered,transport=build(a['dsn'].read_bytes(),a['board'].read_bytes(),a['binding']);(out/'retained.ses').write_bytes(raw);(out/'filtered.ses').write_bytes(filtered)
        imported=out/'imported.kicad_pcb';job.native('pristine-import','import',a['board'],imported,out/'filtered.ses');f.process_check(out,{'steps':job.steps},'pristine-import',[*f.SANDBOX,str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),'import',str(a['board']),str(imported),str(out/'filtered.ses')])
        semantic=sn.semantic_diff(sx.read(a['emission']),sx.read(imported))
        if not semantic['equal']:raise p.Rejected('native import changed original native nonrouting emission')
        protected_audit={};rebuilt=p.transplant_routes(original,sx.read(imported),protected=tuple(p.routes(original)),audit=protected_audit)
        if p.immutable(rebuilt)!=p.immutable(original) or p.routes(rebuilt)!=p.routes(original):raise p.Rejected('all original routing/nonrouting must survive exactly')
        candidate=packet(out/'candidate');sx.write(candidate,rebuilt);hashes=inventory(a['board'].parent);p.verify_candidate_files(candidate,hashes)
        saved=out/'saved';shutil.copytree(candidate.parent,saved);savedboard=saved/NAME;before=inventory(saved);refill=job.drc('candidate-refill',savedboard,save=True)
        if f.check_drc_stage(out,{'steps':job.steps},'candidate-refill',savedboard,savedboard,True,before)!=refill:raise p.Rejected('refill receipt differs')
        sx.write(candidate,p.transplant_fill(original,sx.read(savedboard)));p.verify_candidate_files(candidate,hashes,p.sha(candidate))
        if p.immutable(sx.read(candidate))!=p.immutable(original) or p.routes(sx.read(candidate))!=p.routes(original):raise p.Rejected('refill changed immutable original/protected tracks')
        before=inventory(candidate.parent);final=job.drc('candidate-final',candidate,schematic_parity=True)
        if f.check_drc_stage(out,{'steps':job.steps},'candidate-final',candidate,out/'candidate-final-input'/NAME,False,before,schematic_parity=True)!=final:raise p.Rejected('final complete parity binding differs')
        if not p.native_accepted(final) or not sn.same_findings(baseline,final):raise p.Rejected('fresh candidate must preserve all retained original native findings')
        record.update(controls_passed=True,status='controls_passed',native=final,transport=transport,raw_import_immutable=semantic,protected_import=protected_audit,class_proofs={k:v['class_proof'] for k,v in exports.items()},final_candidate=str(candidate),final_candidate_sha256=p.sha(candidate),final_report_sha256=p.sha(out/'candidate-final.json'),prior_baseline_reexecuted=False)
        material.update({n:p.sha(out/n) for n in inventory(out)});record['artifacts_sha256']=material;stable();account()
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,reason=type(exc).__name__+': '+str(exc))
    f.publish(out,record,stable,account,remaining,owned=owned)
    try:
        owned();stable();published=f.read_json(out/'result.json');account();owned()
        # A post-publication cap observation must invalidate the old positive,
        # rather than clear only the in-memory return value.
        if published.get('controls_passed') is True and record['controls_passed'] is not True:
            raise p.Rejected('final native diagnostic budget/readback invalidated positive')
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',controls_passed=False,reason=type(exc).__name__+': '+str(exc));f.publish(out,record,lambda:(_ for _ in ()).throw(p.Rejected(record['reason'])),account,remaining,owned=owned)
    return record
