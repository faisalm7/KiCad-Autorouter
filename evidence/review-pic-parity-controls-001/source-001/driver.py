"""ROOT-only original PIC parity diagnostic; three fixed cases, no support change."""
from __future__ import annotations
import argparse,copy,fcntl,hashlib,json,math,re,resource,shutil,signal,subprocess,sys,time,uuid
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io
from autorouter.runner import run
import fixture as fx,checks,native_summary
SOURCE=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
RECEIPT=ROOT/'data/sources.json'
RECEIPT_SHA='a2a8e9e22ff3e109de94733aa8f5e99ca5fd476ef9ec20be837c54100036eac1'
BOARD_SHA='1ca70b620506818eb0227e2863bbd573d1fec1672072dc43d0dbe8475e69c8fb'
PROJECT_SHA='3b0ac39da5af86d0baa2a64da55a89c39ba00148dc82b54f3062f5c3650a5cc5'
HELP_DIR='evidence/pic-parity-cli-help-001'
HELPERS=('driver.py','fixture.py','checks.py','native_summary.py','test_controls.py','PROTOCOL.json','README.md')
SECONDS=60;LIMIT=20*1024**2;RESERVE=1024**2
FALSE_CLAIMS={'routing_accepted':False,'geometry_qualified':False,'format_support_qualified':False,'production_support_changed':False,'schematic_parity_qualified':False,'new_engine_execution':False,'board_saved':False}
def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()

def read(path):return f.read_json(path)

def inventory(path):
    rows=io.inventory(path,max_bytes=LIMIT,max_files=2048,max_entries=4096)
    if len({name.casefold()for name in rows})!=len(rows):raise p.Rejected('case-colliding inventory paths')
    return rows

def digest(path):return sha_bytes(io.read_bytes(path,LIMIT))

def size(path):return sum(map(len,io.inventory(path,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096).values()))

def owned(path,*,output=False):
    path=Path(path).absolute()
    if '..' in path.parts or any(x.is_symlink() for x in (path,*path.parents)):raise p.Rejected('real canonical paths required')
    if not path.is_relative_to(ROOT):raise p.Rejected('path outside checkout')
    if output and (path.parent!=ROOT/'.runs' or path.exists()):raise p.Rejected('fresh direct .runs output required')
    return path

def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime

def source_binding():
    owned(SOURCE);owned(RECEIPT)
    if sha_bytes(io.read_bytes(RECEIPT))!=RECEIPT_SHA:raise p.Rejected('acquisition manifest changed')
    receipt=read(RECEIPT);expected={};total=0
    if receipt.get('commit')!='69cafb907ebc09e7722a2a464b1d466fc2e3608d':raise p.Rejected('source commit differs')
    for row in receipt['files']:
        if row.get('project_id')!='kicad-pic-programmer':continue
        path=owned(ROOT/'.data'/row['destination'])
        if not path.is_relative_to(SOURCE.parent):raise p.Rejected('acquisition path outside source')
        name=str(path.relative_to(SOURCE.parent))
        if name in expected:raise p.Rejected('duplicate acquired path')
        raw=io.read_bytes(path,LIMIT-total);total+=len(raw)
        if len(raw)!=row['bytes'] or sha_bytes(raw)!=row['sha256'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['git_blob_sha1']:raise p.Rejected('acquired source blob differs')
        expected[name]=row['sha256']
    if len(expected)!=15 or total!=1366598 or inventory(SOURCE.parent)!=expected or expected.get(SOURCE.name)!=BOARD_SHA or expected.get(SOURCE.with_suffix('.kicad_pro').name)!=PROJECT_SHA:raise p.Rejected('complete acquired source inventory differs')
    return expected,total

def publish(out,record,stable,account,remaining):
    path=out/'summary.json'
    def invalidate():
        for candidate in (path,out/'summary.json.partial'):
            if candidate.exists():candidate.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+candidate.name))
    try:
        stable();account();expected=f.canonical(record);p.save_json(path,record)
        if f.canonical(read(path))!=expected:raise p.Rejected('summary changed after write')
        final_size=size(out);stable()
        if f.canonical(record)!=expected or f.canonical(read(path))!=expected or final_size>LIMIT or remaining()<=0:raise p.Rejected('summary stale or final cap exceeded')
    except (Exception,KeyboardInterrupt) as exc:
        first=record.get('error');error=type(exc).__name__+': '+str(exc)
        invalidate();record.update(**FALSE_CLAIMS,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',
            controls_passed=False,original_inputs_unchanged=None,error=first if first is not None else error,final_validation_error=error);account()
        try:p.save_json(path,record)
        except (Exception,KeyboardInterrupt):invalidate()
    return record

def head_witness():
    raw=io.read_bytes(owned(ROOT/'.git/HEAD'),4096);text=raw.decode().strip()
    if not re.fullmatch(r'ref: refs/heads/rebuild/local-[A-Za-z0-9_-]+',text):raise p.Rejected('ordinary designated checkout required')
    ref=io.read_bytes(owned(ROOT/'.git'/text[5:]),4096)
    if not re.fullmatch('[0-9a-f]{40}',ref.decode().strip()):raise p.Rejected('loose branch identity required')
    return {'head':ref.decode().strip(),'HEAD_sha256':sha_bytes(raw),'ref_sha256':sha_bytes(ref)}

def parser_parity():
    import ast,inspect
    original=ast.parse(inspect.getsource(p.parse_report)).body[0].body[1:]
    adapter=ast.parse(inspect.getsource(native_summary.parse_data)).body[0].body
    if ast.dump(ast.Module(body=original,type_ignores=[]))!=ast.dump(ast.Module(body=adapter,type_ignores=[])):raise p.Rejected('native parser validation/count body changed')

def help_binding():
    path=owned(ROOT/HELP_DIR);record=read(path/'receipt.json');raw=io.read_bytes(path/'help.log',16384)
    expected={'sha256':'998aed348399000335b0e29edf747daa18819f2ac417bac066f4216fdc5d90d1','bytes':2131968,'path':str(c.CLI)}
    step=record['process'];argv=[*f.SANDBOX,str(c.CLI),'pcb','drc','--help']
    if record['tool_pin']!=expected or p.sha(c.CLI)!=expected['sha256']or step['argv']!=argv or step['exit_code']!=0 or step['status']!='success' or step.get('cleanup_complete')is not True or step['log_bytes']!=len(raw)or step.get('log_truncated')is not False:raise p.Rejected('CLI help process/tool binding differs')
    if sha_bytes(raw)!='da7c7fa31fb2f5a2cf44fca62031f1e619fcf8607146c94d030b205b8f326998' or record['help_sha256']!=sha_bytes(raw)or record['help_bytes']!=len(raw):raise p.Rejected('CLI help bytes differ')
    for flag in ('--schematic-parity','--refill-zones','--severity-all','--all-track-errors','--exit-code-violations'):
        if record['flags_present'].get(flag)is not True or flag.encode()not in raw:raise p.Rejected('required CLI flag absent')
    return {str((path/name).relative_to(ROOT)):digest(path/name)for name in ('receipt.json','help.log')}

def snapshot(out,tools,remaining):
    sources={ROOT/name:value for name,value in tools['implementation_sha256'].items()}
    sources[ROOT/'toolchain.lock.json']=digest(ROOT/'toolchain.lock.json')
    for name in HELPERS:sources[owned(HERE/name)]=digest(HERE/name)
    for rel,value in help_binding().items():sources[ROOT/rel]=value
    sources[RECEIPT]=RECEIPT_SHA
    for path,value in sources.items():
        if remaining()<=0:raise p.Rejected('budget exhausted before source snapshot')
        rel=str(owned(path).relative_to(ROOT));raw=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=min(3,remaining())).stdout
        if sha_bytes(raw)!=value or digest(path)!=value:raise p.Rejected('commit exact helpers/core/evidence before native: '+rel)
    (out/'code').mkdir();bindings={}
    for path,value in sources.items():
        rel=str(path.relative_to(ROOT));target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        if digest(target)!=value:raise p.Rejected('snapshot source changed')
        bindings[rel]=value
    return bindings

def drc_argv(directory):
    return [*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--schematic-parity','--exit-code-violations','--output',str(directory/'parity-drc.json'),str(directory/'project'/fx.BOARD)]

class ParityJob(f.FloorJob):
    def __init__(self,out,remaining,batch):
        super().__init__(out,SECONDS,remaining);self.batch=batch;self.captured={};self.input_after=None
        # Reused project KICAD paths are set by Job; constrain other user state too.
        (self.out/'home').mkdir();self.env.update(HOME=str(self.out/'home'),LANG='C',LC_ALL='C')
    def capture(self,names):
        for name in names:
            value=digest(self.out/name)
            if name in self.captured and self.captured[name]!=value:raise p.Rejected('stage changed before capture')
            self.captured[name]=value
    def execute(self,expected):
        if self.remaining()<=0 or size(self.batch)>LIMIT:raise p.Rejected('shared resource cap exhausted')
        if inventory(self.out/'project')!=expected:raise p.Rejected('exact case project required')
        step=run(drc_argv(self.out),cwd=self.out,log=self.out/'parity-drc.log',timeout=min(30,self.remaining()),env=self.env,max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        step['name']='parity-drc';self.steps.append(step);p.save_json(self.out/'parity-drc-process.json',step)
        names=['parity-drc-process.json','parity-drc.log']
        if(self.out/'parity-drc.json').exists():names.append('parity-drc.json')
        self.capture(names) # Raw evidence is immutable before any classification.
        if step['status']=='cancelled':raise KeyboardInterrupt('native parity cancelled')
        if step['exit_code']not in (0,5)or step['status']!=('success'if step['exit_code']==0 else'nonzero_exit')or step.get('cleanup_complete')is not True:raise p.Rejected('native parity process failed')
        self.input_after=inventory(self.out/'project')
        if self.input_after!=expected:raise p.Rejected('nonsaving parity changed source project')
        p.save_json(self.out/'parity-binding.json',{'input':str(self.out/'project'/fx.BOARD),'before':expected,'after':self.input_after,'saved':False})
        self.capture(['parity-binding.json'])
        if self.remaining()<=0 or size(self.batch)>LIMIT:raise p.Rejected('shared cap exceeded after native stage')

def validate_case(job,row,baseline):
    for name,value in job.captured.items():
        if digest(job.out/name)!=value:raise p.Rejected('captured native evidence stale')
    if row['stage_evidence']!=job.captured:raise p.Rejected('recorded stage capture differs')
    expected=row['input_hashes'];binding=read(job.out/'parity-binding.json')
    if binding!={'input':str(job.out/'project'/fx.BOARD),'before':expected,'after':expected,'saved':False}or inventory(job.out/'project')!=expected:raise p.Rejected('native full-project identity differs')
    raw=read(job.out/'parity-drc.json');native=native_summary.parse_data(raw,fx.BOARD)
    f.process_check(job.out,{'steps':job.steps},'parity-drc',drc_argv(job.out),allowed=(5 if native['findings']else 0,))
    log_bytes=io.read_bytes(job.out/'parity-drc.log',256*1024);process=read(job.out/'parity-drc-process.json')
    if process.get('log')!=str(job.out/'parity-drc.log') or process.get('log_bytes')!=len(log_bytes) or process.get('log_truncated')is not False:raise p.Rejected('native log binding differs')
    guards=process.get('resource_guards',{})
    if guards.get('max_group_rss_bytes')!=2*1024**3 or guards.get('max_workdir_bytes')!=LIMIT or guards.get('os_enforced')is not False:raise p.Rejected('native resource guard configuration differs')
    if any(type(process.get(key))not in(int,float)or not math.isfinite(process[key])or process[key]<0 or process[key]>SECONDS for key in ('wall_seconds','cpu_seconds','monitor_cpu_seconds')):raise p.Rejected('native resource accounting malformed')
    for key,ceiling in (('sampled_peak_group_rss_bytes',2*1024**3),('sampled_peak_workdir_bytes',LIMIT)):
        if type(process.get(key))is not int or not 0<=process[key]<=ceiling:raise p.Rejected('observed resource guard exceeded')
    log=log_bytes.decode('utf-8')
    result=checks.predicate(row['case'],raw,log,baseline)
    # Recheck captures after all reads; never adopt a changed report/log/binding.
    if any(digest(job.out/name)!=value for name,value in job.captured.items()):raise p.Rejected('native stage changed during interpretation')
    return result

def protocol():
    return {'schema':1,'name':'original-pic-schematic-field-parity-controls-v1','order':list(fx.CASES),'wall_seconds':SECONDS,'full_cpu_seconds':SECONDS,'output_bytes':LIMIT,'source_board_sha256':BOARD_SHA,'source_project_sha256':PROJECT_SHA,'source_files':15,'source_bytes':1366598,'target_footprint_uuid':fx.FP,'target_symbol_uuid':fx.SYMBOL,'field':fx.FIELD,'positive_value':fx.MATCH,'negative_value':fx.MISMATCH,'expected_field_severity':'warning','expected_ignored':list(checks.IGNORED),'project_changes':False,'native_save':False,'routing':False,'production_support_changed':False,'prerequisites':'Stop after first failed case; all subsequent rows remain not_attempted. Original15-file project then matching hidden custom field then only PCB value mismatch.','help_sha256':'da7c7fa31fb2f5a2cf44fca62031f1e619fcf8607146c94d030b205b8f326998'}

def experiment(out,*,run_native=False):
    if run_native is not True:raise p.Rejected('--run-native required')
    start=time.monotonic();cpu0=cpu();out=owned(out,output=True);out.mkdir()
    remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(cpu()-cpu0)))
    record={'schema':1,'status':'incomplete','controls_passed':False,**FALSE_CLAIMS,'source':str(SOURCE),'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,'scope':'Original full PIC project parity diagnostics only; one paired hidden-field metadata delta; no circuit/rule change or routing.','accounting_point':'Stored totals precede final publication checks; all final checks included in acceptance wall/full SELF+waited CHILDREN CPU caps. Finite sampling, not hard CPU preemption or atomic authentication.','cases':[{'case':case,'status':'not_attempted','native_executed':False,'control_passed':False,'stage_evidence':{},'steps':[]}for case in fx.CASES]}
    authorized=False;hashes={};jobs={};complete={};code=None;whole=None;head=None;board=None;sch=None
    def account():
        steps=[s for job in jobs.values()for s in job.steps];record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=cpu()-cpu0,child_step_cpu_seconds=sum(s.get('cpu_seconds')or 0 for s in steps),monitor_cpu_seconds=sum(s.get('monitor_cpu_seconds')or 0 for s in steps),native_executed=any(type(s.get('pid'))is int and s['pid']>0 for s in steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record.update(controls_passed=False,status='budget_exceeded')
    def prepared(case):
        files=fx.prepare(board,sch,case);expected=dict(hashes)
        for name,raw in files.items():expected[name]=sha_bytes(raw)
        return files,expected
    def material():
        if not authorized:return
        if inventory(SOURCE.parent)!=hashes or digest(RECEIPT)!=RECEIPT_SHA:raise p.Rejected('original source/acquisition changed')
        if code is not None:
            if inventory(out/'code')!=code or any(digest(ROOT/rel)!=value for rel,value in record['runtime_sources'].items()):raise p.Rejected('runtime source changed')
            if any(p.sha(Path(path))!=value for path,value in record['tools']['files'].items())or head_witness()!=head:raise p.Rejected('tool/HEAD material changed')
        for name,expected in complete.items():
            if inventory(out/name)!=expected:raise p.Rejected('completed case changed')
        if whole is not None and {k:v for k,v in inventory(out).items()if k!='summary.json'and not k.startswith('invalidated-')}!=whole:raise p.Rejected('completed batch changed')
    def stable():
        if not authorized:return
        if any(record.get(k)is not v for k,v in FALSE_CLAIMS.items()):raise p.Rejected('diagnostic scope changed')
        if [r.get('case')for r in record['cases']]!=list(fx.CASES)or record['source_hashes']!=hashes:raise p.Rejected('case/source identity changed')
        if code is not None and p.tool_manifest()!=record['tools']:raise p.Rejected('runtime metadata changed')
        material();baseline=None;previous=True
        for row in record['cases']:
            job=jobs.get(row['case'])
            if job is None:
                if row['status']!='not_attempted'or row['control_passed']is not False or row['native_executed']is not False:raise p.Rejected('unattempted case claim changed')
                previous=False;continue
            if row.get('input_hashes')is not None:
                _,expected=prepared(row['case'])
                if row['input_hashes']!=expected or inventory(job.out/'project')!=expected:raise p.Rejected('case preparation changed')
            if row['steps']!=job.steps or row['stage_evidence']!=job.captured:raise p.Rejected('case stage record changed')
            if any(digest(job.out/name)!=value for name,value in job.captured.items()):raise p.Rejected('native raw evidence changed')
            if row.get('predicate')is not None:
                result=validate_case(job,row,baseline)
                if result!=row['predicate']or row['control_passed']is not (result['predicate_met']and previous)or row['status']!=('passed'if result['predicate_met']and previous else'failed_expected_predicate'):raise p.Rejected('native predicate summary changed')
                if row['case']=='original_parity':baseline=result['ordinary_fingerprint']
            elif row['control_passed']is not False:raise p.Rejected('unvalidated case claims pass')
            previous=previous and row['control_passed']
        if record['controls_passed']is True and (len(complete)!=3 or not all(r['control_passed']is True for r in record['cases'])):raise p.Rejected('positive lacks all prerequisites')
        material()
    try:
        parser_parity();p.check_storage();hashes,total=source_binding();authorized=True;record.update(source_hashes=hashes,source_bytes=total,source_file_count=15)
        board=io.read_bytes(SOURCE);sch=io.read_bytes(SOURCE.parent/fx.SCH)
        project=read(SOURCE.with_suffix('.kicad_pro'))
        if project['board']['design_settings']['rule_severities']['footprint_symbol_field_mismatch']!='warning':raise p.Rejected('original field severity changed')
        try:p.preflight(SOURCE)
        except p.Rejected as exc:record['production_gate_rejection']=str(exc)
        else:raise p.Rejected('original now admitted; re-review diagnostic scope')
        record['protocol']=read(HERE/'PROTOCOL.json')
        if record['protocol']!=protocol():raise p.Rejected('fixed protocol changed')
        record['tools']=p.tool_manifest();head=head_witness()
        if head['head']!=record['tools']['git_head']:raise p.Rejected('HEAD changed before snapshot')
        record['git_material']=head;record['runtime_sources']=snapshot(out,record['tools'],remaining);code=inventory(out/'code')
        if size(out)+3*(total+4096)+RESERVE>LIMIT:raise p.Rejected('three copies exceed20MiB budget')
        record['planned_project_copy_bytes_upper_bound']=3*(total+4096);baseline=None
        for row in record['cases']:
            if remaining()<=0:raise p.Rejected('budget before next case')
            stable();job=ParityJob(out/row['case'],remaining,out);jobs[row['case']]=job
            try:
                files,expected=prepared(row['case']);shutil.copytree(SOURCE.parent,job.out/'project')
                for name,raw in files.items():(job.out/'project'/name).write_bytes(raw)
                if inventory(job.out/'project')!=expected:raise p.Rejected('copied case differs')
                row['input_hashes']=expected;job.execute(expected);row.update(steps=copy.deepcopy(job.steps),stage_evidence=dict(job.captured),native_executed=True)
                result=validate_case(job,row,baseline);row.update(predicate=result,control_passed=result['predicate_met'],status='passed'if result['predicate_met']else'failed_expected_predicate')
                if row['case']=='original_parity':baseline=result['ordinary_fingerprint']
            except (Exception,KeyboardInterrupt)as exc:
                row.update(status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',control_passed=False,error=type(exc).__name__+': '+str(exc))
                if isinstance(exc,KeyboardInterrupt):raise
            finally:
                row.update(steps=copy.deepcopy(job.steps),stage_evidence=dict(job.captured),native_executed=any(type(s.get('pid'))is int and s['pid']>0 for s in job.steps))
                current=inventory(job.out)
                if row['case']in complete and complete[row['case']]!=current:raise p.Rejected('case changed before final capture')
                complete[row['case']]=current
            stable()
            if not row['control_passed']:break
        record.update(controls_passed=all(r['control_passed']is True for r in record['cases']),original_inputs_unchanged=True)
        record['status']='controls_passed'if record['controls_passed']else'failed_controls';whole=inventory(out);record['completed_evidence']=whole
    except (Exception,KeyboardInterrupt)as exc:record.update(status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    return publish(out,record,stable,account,remaining)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--run-native',action='store_true');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required; ROOT owns native lane')
    previous={s:signal.getsignal(s)for s in (signal.SIGINT,signal.SIGTERM)}
    def interrupt(*_):raise KeyboardInterrupt
    try:
        for s in previous:signal.signal(s,interrupt)
        with owned(ROOT/'.runs/quality-experiment.lock').open('a')as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);record=experiment(args.output,run_native=True)
    finally:
        for s,h in previous.items():signal.signal(s,h)
    print(json.dumps({k:record[k]for k in ('status','controls_passed','routing_accepted','schematic_parity_qualified')}));return 0 if record['controls_passed']else 2
if __name__=='__main__':raise SystemExit(main())
