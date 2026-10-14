"""Lead-only native DRC controls for an exact schema3 disposable review copy.

No routing, GUI, source changes, save, format support extension or live apply.
"""
from __future__ import annotations
import argparse,fcntl,hashlib,json,math,os,resource,signal,stat,subprocess,sys,time,unicodedata,uuid
from pathlib import Path
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io,handoff as h
from autorouter.runner import run
from experiments.placement_production_controls_v1 import driver as prior
POLICY='placement-clearance-v1';SECONDS=60;LIMIT=20*1024*1024;RESERVE=1024*1024
RECEIPT=ROOT/'.runs/placement-production-native-001/result.json'
RECEIPT_SHA='166050372738e25335db8261753c433c921a0a71857148c7a4d8cadf2669df7d'
CANDIDATE_SHA='4c118026360d23ecfffad6b4c8638aabf592f9534ca1e8cb999a77316dee09e1'
EXTRA=ROOT/'experiments/placement_production_controls_v1/driver.py'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return f.read_json(path)
def inventory(path):return io.inventory(path,max_bytes=100*1024*1024,max_files=2000,max_entries=4000)
def payload(path):return io.inventory(path,contents=True,max_bytes=LIMIT,max_files=512,max_entries=1024)
def owned(path,exists=True):
    path=Path(path).absolute()
    if '..' in path.parts or not path.is_relative_to(ROOT) or any(x.is_symlink() for x in (path,*path.parents)):raise p.Rejected('canonical checkout path required')
    if exists and not path.exists():raise p.Rejected('required path missing')
    return path

def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime

def hashes(files):return {name:sha(raw) for name,raw in files.items()}
def size(path):return sum(len(v) for v in payload(path).values())
def copy_bytes(files,target):
    """Exclusive descriptor-anchored copy; never adopt a replacement directory."""
    if not isinstance(files,dict) or len(files)>2000:raise p.Rejected('bounded captured byte dictionary required')
    rows=[];paths={};planned_dirs=set();total=0
    for name,raw in files.items():
        if (type(name) is not str or not name or '\\' in name or any(ord(c)<32 for c in name)
                or name.startswith('/') or any(x in ('','.','..') for x in name.split('/'))
                or unicodedata.normalize('NFC',name)!=name or type(raw) is not bytes):
            raise p.Rejected('canonical relative captured byte path required')
        parts=tuple(name.split('/'));rows.append((name,parts,raw));total+=len(raw)
        for end in range(1,len(parts)+1):
            prefix='/'.join(parts[:end]);folded=prefix.casefold()
            if folded in paths and paths[folded]!=prefix:raise p.Rejected('captured path alias collision')
            paths[folded]=prefix
            if end<len(parts):planned_dirs.add(prefix)
    if total>100*1024**2 or len(paths)>4000:raise p.Rejected('captured project byte/entry ceiling')
    if planned_dirs&set(files):raise p.Rejected('captured file/directory collision')
    target=h.real_path(target,existing=False);parent=h.real_path(target.parent)
    directory_flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0)
    descriptors=[];dirs={};parent_owner={};h.capture_destination(parent_owner,parent)
    def identity(fd):
        info=os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode):raise p.Rejected('captured real directory required')
        return info.st_dev,info.st_ino
    def guard():
        h.owned_destination(parent_owner)
        if identity(parent_fd)!=parent_owner['directory_identity']:raise p.Rejected('copy parent descriptor changed')
        for relative,(fd,owner,up,name) in dirs.items():
            h.owned_destination(owner);named=os.stat(name,dir_fd=up,follow_symlinks=False)
            if (not stat.S_ISDIR(named.st_mode) or (named.st_dev,named.st_ino)!=owner['directory_identity']
                    or identity(fd)!=owner['directory_identity']):raise p.Rejected('captured directory was replaced')
    def create(relative,up,name,path):
        guard();os.mkdir(name,dir_fd=up)
        fd=os.open(name,directory_flags,dir_fd=up);descriptors.append(fd);owner={};h.capture_destination(owner,path)
        if identity(fd)!=owner['directory_identity']:raise p.Rejected('captured directory identity changed during creation')
        dirs[relative]=(fd,owner,up,name);guard();return fd
    parent_fd=os.open(parent,directory_flags);descriptors.append(parent_fd)
    try:
        guard();root_fd=create('',parent_fd,target.name,target)
        for name,parts,raw in rows:
            guard();up=root_fd
            for end,component in enumerate(parts[:-1],1):
                relative='/'.join(parts[:end])
                if relative not in dirs:up=create(relative,up,component,target/relative)
                else:up=dirs[relative][0]
            guard();fd=os.open(parts[-1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0),0o600,dir_fd=up)
            try:
                guard();opened=os.fstat(fd)
                if not stat.S_ISREG(opened.st_mode):raise p.Rejected('captured regular file required')
                pending=memoryview(raw)
                while pending:
                    guard();written=os.write(fd,pending)
                    if written<=0:raise p.Rejected('captured write made no progress')
                    pending=pending[written:]
                guard();actual=os.stat(parts[-1],dir_fd=up,follow_symlinks=False);finished=os.fstat(fd)
                if (not stat.S_ISREG(actual.st_mode) or (actual.st_dev,actual.st_ino)!=(opened.st_dev,opened.st_ino)
                        or (finished.st_dev,finished.st_ino,finished.st_size)!=(opened.st_dev,opened.st_ino,len(raw))):
                    raise p.Rejected('captured file was replaced or changed')
            finally:os.close(fd)
        guard();actual,directories=io.inventory(target,max_bytes=100*1024**2,max_files=2000,max_entries=4000,with_directories=True)
        if actual!={name:sha(raw) for name,_,raw in rows} or set(directories)!={'.',*planned_dirs}:raise p.Rejected('captured complete copy differs')
        guard()
    finally:
        for fd in reversed(descriptors):os.close(fd)

def bind_handoff(receipt,handoff):
    receipt=owned(receipt);handoff=owned(handoff)
    if receipt!=RECEIPT or sha(io.read_bytes(receipt))!=RECEIPT_SHA:raise p.Rejected('exact owned schema3 fixture receipt required')
    if handoff.name!='review.json' or handoff.parent.parent!=ROOT/'.runs' or handoff.parent==receipt.parent:raise p.Rejected('fresh external handoff record required')
    evidence=inventory(receipt.parent);handoff_tree=inventory(handoff.parent)
    report=read(receipt);review=read(handoff);source=owned(report['source']);candidate=owned(report['candidate'])
    verified=p.check_result(receipt)
    if (report.get('schema')!=3 or report.get('input_policy')!=POLICY or report.get('candidate_sha256')!=CANDIDATE_SHA
        or verified.get('input_policy')!=POLICY or verified.get('candidate')!=str(candidate) or verified.get('candidate_sha256')!=CANDIDATE_SHA):raise p.Rejected('qualified fixture identity differs')
    project=handoff.parent/'project';board=project/candidate.name
    if (type(review.get('schema')) is not int or review.get('schema')!=1 or review.get('status')!='ready_for_manual_review' or review.get('input_policy')!=POLICY
        or review.get('source_receipt_schema')!=3 or review.get('receipt')!=str(receipt) or review.get('receipt_sha256')!=RECEIPT_SHA
        or review.get('verified_candidate_sha256')!=CANDIDATE_SHA or review.get('candidate_sha256')!=CANDIDATE_SHA
        or review.get('project')!=str(project) or review.get('board')!=str(board) or review.get('native_validation_performed') is not False
        or ('accepted' in review and review['accepted'] is not False) or ('applied' in review and review['applied'] is not False)):raise p.Rejected('handoff policy/candidate/provenance differs')
    if review.get('within_budget') is not True or review.get('budget_seconds')!=30 or review.get('cpu_budget_seconds')!=30:raise p.Rejected('handoff budget declaration differs')
    for key in ('wall_seconds','total_cpu_seconds'):
        value=review.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=30:raise p.Rejected('invalid handoff resource sample')
    files=payload(owned(project));expected=hashes(files)
    if review.get('initial_project_hashes')!=expected or inventory(candidate.parent)!=expected or expected.get(candidate.name)!=CANDIDATE_SHA:raise p.Rejected('handoff complete project differs from accepted candidate')
    if inventory(source.parent)!=report['source_hashes'] or inventory(receipt.parent)!=evidence or inventory(handoff.parent)!=handoff_tree:raise p.Rejected('input changed during qualification')
    if report['native']['findings'] or not p.native_accepted(report['native']):raise p.Rejected('fixture must have clean bound native report')
    return {'receipt':str(receipt),'receipt_sha256':RECEIPT_SHA,'handoff':str(handoff),'handoff_sha256':sha(io.read_bytes(handoff)),
        'evidence':evidence,'handoff_tree':handoff_tree,'source':str(source),'source_hashes':report['source_hashes'],'candidate':str(candidate),'candidate_hashes':expected,'verified':verified,'ignored_checks':report['native']['ignored_checks']},files

def snapshot(out,tools,remaining):
    paths={ROOT/k:v for k,v in tools['implementation_sha256'].items()}
    for path in [ROOT/'toolchain.lock.json',EXTRA,HERE/'driver.py',HERE/'test_driver.py']:paths[owned(path)]=sha(io.read_bytes(path))
    captured={}
    for path,digest in paths.items():
        available=remaining()
        if available<=0:raise p.Rejected('budget exhausted before committed snapshot')
        name=str(owned(path).relative_to(ROOT));raw=io.read_bytes(path)
        result=subprocess.run(['git','show',tools['git_head']+':'+name],cwd=ROOT,capture_output=True,check=True,timeout=min(3,available))
        if sha(raw)!=digest or result.stdout!=raw:raise p.Rejected('commit exact implementation/helpers first')
        captured[name]=raw
    copy_bytes(captured,out/'code');return hashes(captured)

def drc_argv(out,board):return [*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'native-drc.json'),str(out/'native-drc-input'/board.name)]

class NativeJob(f.FloorJob):
    def __init__(self,out,remaining,all_steps,root,board_name):
        super().__init__(out,remaining(),remaining);self.all_steps=all_steps;self.root=root;self.board_name=board_name;self.frozen_stage=None
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        actual=[str(x) for x in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
        if name!='native-drc' or actual!=drc_argv(self.out,self.out/self.board_name):raise p.Rejected('only exact nonsaving native DRC allowed')
        available=self.remaining();allowance=LIMIT-size(self.root)+size(self.out)
        if available<=0 or allowance<=0:raise p.Rejected('shared diagnostic budget exhausted')
        result=run(actual,cwd=self.out,log=self.out/'native-drc.log',timeout=available,env=self.env,max_log_bytes=256*1024,max_workdir_bytes=allowance,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);self.all_steps.append(result);p.save_json(self.out/'native-drc-process.json',result)
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected('native DRC subprocess failed: '+result['status'])
        self.frozen_stage={n:sha(io.read_bytes(self.out/n,LIMIT)) for n in ['native-drc.json','native-drc.log','native-drc-process.json']}
        if self.remaining()<=0 or size(self.root)>LIMIT:raise p.Rejected('whole control cap exceeded')
        return result

def check_case(job,board,native,expected):
    if job.frozen_stage is None or any(sha(io.read_bytes(job.out/n,LIMIT))!=digest for n,digest in job.frozen_stage.items()):raise p.Rejected('native stage changed after capture')
    if inventory(board.parent)!=expected:raise p.Rejected('derived case changed')
    return prior.check_drc(job,'native-drc',board,native)

def publish(out,record,stable,account,remaining):
    path=out/'summary.json'
    def archive():
        for file in (path,out/'summary.json.partial'):
            if file.exists():file.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+file.name))
    try:
        stable();account()
        if remaining()<=0:raise p.Rejected('control budget before publication')
        expected=f.canonical(record);p.save_json(path,record)
        if f.canonical(read(path))!=expected:raise p.Rejected('summary changed during write')
        stable()
        final_size=size(out)
        if f.canonical(read(path))!=expected or f.canonical(record)!=expected or remaining()<=0 or final_size>LIMIT:raise p.Rejected('summary stale or final cap exceeded')
    except (Exception,KeyboardInterrupt) as exc:
        archive();record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',controls_passed=False,original_inputs_unchanged=None,error=type(exc).__name__+': '+str(exc));account()
        try:p.save_json(path,record)
        except (Exception,KeyboardInterrupt):archive()
    return record

def experiment(out,receipt,handoff,*,run_native=False):
    if run_native is not True:raise p.Rejected('--run-native required')
    start=time.monotonic();cpu0=cpu();out=owned(out,exists=False)
    if out.exists() or out.parent!=ROOT/'.runs':raise p.Rejected('fresh direct .runs output required')
    out.mkdir();steps=[];bound=None;code=None;completed={};case_states=[]
    remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(cpu()-cpu0)))
    record={'schema':1,'status':'incomplete','controls_passed':False,'routing_accepted':False,'gui_qualified':False,'live_apply_qualified':False,'new_engine_execution':False,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,'cases':[],
        'scope':'Owned accepted schema3 fixture handoff; unchanged positive and exact required-via removal negative; nonsaving original-rule native DRC only.',
        'accounting_point':'Stored pre-publication wall/full parent+waited-child CPU sample; positive acceptance caps include all final verification/publication. Polling can overshoot; no OS aggregate CPU quota.'}
    def account():
        record.update(steps=steps,wall_seconds=time.monotonic()-start,total_cpu_seconds=cpu()-cpu0,native_executed=bool(steps),child_step_cpu_seconds=sum(s.get('cpu_seconds') or 0 for s in steps),monitor_cpu_seconds=sum(s.get('monitor_cpu_seconds') or 0 for s in steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record.update(controls_passed=False,status='budget_exceeded')
    def stable():
        if bound is None:return
        # Central check may execute metadata. Material hashes are rechecked after it.
        if p.check_result(Path(bound['receipt']))!=bound['verified']:raise p.Rejected('accepted receipt check changed')
        if code is not None and p.tool_manifest()!=record['tools']:raise p.Rejected('code/tools/HEAD changed')
        for job,board,native,expected,binding in case_states:
            if check_case(job,board,native,expected)!=binding:raise p.Rejected('case native binding changed')
        for path,known in completed.items():
            if inventory(Path(path))!=known:raise p.Rejected('completed case evidence changed')
        if code is not None:
            if inventory(out/'code')!=code or any(sha(io.read_bytes(ROOT/name))!=digest for name,digest in code.items()):raise p.Rejected('runtime source/helper snapshot changed')
            if any(p.sha(Path(name))!=digest for name,digest in record['tools']['files'].items()):raise p.Rejected('native tool bytes changed')
        for path,known in [(Path(bound['source']).parent,bound['source_hashes']),(Path(bound['candidate']).parent,bound['candidate_hashes']),(Path(bound['receipt']).parent,bound['evidence']),(Path(bound['handoff']).parent,bound['handoff_tree'])]:
            if inventory(path)!=known:raise p.Rejected('original source/candidate/evidence/handoff changed')
    try:
        p.check_storage();bound,files=bind_handoff(receipt,handoff);record['inputs']=bound;record['tools']=p.tool_manifest();code=snapshot(out,record['tools'],remaining);record['code_inventory']=code
        if size(out)+4*sum(map(len,files.values()))+RESERVE>LIMIT:raise p.Rejected('four complete case/input copies exceed output cap')
        record['planned_project_copy_bytes']=4*sum(map(len,files.values()));stable()
        name=Path(bound['candidate']).name
        for case in ('positive','missing_via'):
            stable();board_bytes,project_bytes,recipe=prior.prepare(case,files[name],files[Path(name).with_suffix('.kicad_pro').name])
            if project_bytes!=files[Path(name).with_suffix('.kicad_pro').name]:raise p.Rejected('control changed original project')
            derived=dict(files);derived[name]=board_bytes;expected=hashes(derived)
            job=NativeJob(out/case,remaining,steps,out,name);copy_bytes(derived,job.out/'candidate');board=job.out/'candidate'/name
            entry={'case':case,'passed':False,'recipe':recipe,'candidate_hashes':expected};record['cases'].append(entry)
            try:
                native=job.drc('native-drc',board,save=False);binding=check_case(job,board,native,expected)
                case_states.append((job,board,native,expected,binding))
                passed,hits=prior.diagnostic_pass(case,native,recipe,bound['ignored_checks'])
                entry.update(native=native,binding=binding,stage_hashes=job.frozen_stage,targeted_findings=hits,passed=passed)
            except Exception as exc:entry['error']=type(exc).__name__+': '+str(exc)
            p.save_json(job.out/'case.json',entry);completed[str(job.out)]=inventory(job.out);stable()
        record.update(status='completed',controls_passed=len(record['cases'])==2 and all(x['passed'] for x in record['cases']),completed_evidence=completed,original_inputs_unchanged=True)
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    return publish(out,record,stable,account,remaining)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--receipt',required=True,type=Path);parser.add_argument('--handoff',required=True,type=Path);parser.add_argument('--run-native',action='store_true');args=parser.parse_args(argv)
    if not args.run_native:parser.error('--run-native required')
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupt(*_):raise KeyboardInterrupt
    try:
        for sig in handlers:signal.signal(sig,interrupt)
        with owned(ROOT/'.runs/quality-experiment.lock',False).open('a') as handle:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.output,args.receipt,args.handoff,run_native=True)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
    print(json.dumps({'status':result['status'],'controls_passed':result['controls_passed'],'routing_accepted':False,'gui_qualified':False}))
    return 0 if result['controls_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
