"""ROOT-only protected disposable-input hypothesis; no routing/admission."""
from pathlib import Path
import argparse,fcntl,json,signal,subprocess,sys,time
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'experiments/lipo_native_diagnostic_v1'))
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,config as c
from autorouter.runner import run
from experiments.lipo_native_diagnostic_v1 import driver as shared
from experiments.placement_production_controls_v1 import driver as fixture
import canary
SECONDS=30;LIMIT=20*1024**2
HELPERS=('driver.py','canary.py','test_driver.py','PROTOCOL.json','README.md')
CASES=('canary','positive','missing_via','paw3395')
FALSE_FLAGS=('routing_accepted','production_supported','format_support_qualified','legacy_rule_enforcement_qualified','dependency_complete')
PROFILE='(version 1)(allow default)(deny network*)(deny file-write* (literal (param "INPUT")) (subpath (param "INPUT")))'

def digest(raw):return shared.sha_bytes(raw)
def inventory(path):return shared.inventory(path)
def bytes_tree(path):return io.inventory(path,contents=True,max_bytes=LIMIT,max_files=512,max_entries=1024)
def hashes(files):return {name:digest(raw) for name,raw in files.items()}
def prefix(folder):
    folder=shared.owned(folder)
    if not folder.is_dir():raise p.Rejected('protected input directory missing')
    return ['/usr/bin/sandbox-exec','-D','INPUT='+str(folder),'-p',PROFILE]
def write_copy(folder,files):
    folder.mkdir()
    for name,raw in files.items():
        target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    if inventory(folder)!=hashes(files):raise p.Rejected('complete disposable copy differs')
def stage_argv(out,name,board_name=None):
    folder=out/(name+'-input')
    if name=='canary':return [str(c.PYTHON),str(HERE/'canary.py'),str(folder),str(out/'canary.json')]
    if name!='drc' or board_name not in ('fixture.kicad_pcb','paw3395.kicad_pcb'):raise p.Rejected('unknown protected action')
    return [str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'drc.json'),str(folder/board_name)]
def canary_check(raw,folder):
    if (raw.get('schema')!=1 or type(raw.get('schema')) is not int or raw.get('passed') is not True
            or raw.get('outside_write_succeeded') is not True or raw.get('protected_input')!=str(folder)
            or not isinstance(raw.get('attempts'),list) or len(raw['attempts'])!=len(canary.NAMES)):raise p.Rejected('canary incomplete')
    for name,row in zip(canary.NAMES,raw['attempts']):
        if set(row)!={'name','denied','errno'} or row['name']!=name or row['denied'] is not True or type(row['errno']) is not int or row['errno'] not in (1,13):raise p.Rejected('write protection unproven')
    return raw

def negative_check(raw,native,expected,ignored):
    passed,hits=fixture.diagnostic_pass('missing_via',native,expected,ignored)
    required=set(expected['adjacent_route_uuids']);opens=raw.get('unconnected_items')
    if not passed or native['blocking'] or native['exclusions'] or not isinstance(opens,list) or not opens:raise p.Rejected('required-via native failure missing')
    # Native connectivity must identify the exact separated routes in its actual
    # unconnected section; a type string in another section cannot qualify.
    for row in opens:
        if (row.get('type')!='unconnected_items' or row.get('severity')!='error' or row.get('excluded',False) is not False
                or {item.get('uuid') for item in row.get('items',[])}!=required):raise p.Rejected('unrelated/excluded missing-via finding')
    return {'target_uuids':sorted(required),'raw_target_opens':opens}

class ProtectedJob(f.FloorJob):
    def __init__(self,out,remaining,board_name=None):super().__init__(out,SECONDS,remaining);self.board_name=board_name;self.captured={}
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        expected=stage_argv(self.out,name,self.board_name)
        if already_sandboxed or list(map(str,argv))!=expected:raise p.Rejected('protected argv differs')
        folder=self.out/(name+'-input');before=inventory(folder);available=self.remaining()
        if available<=0:raise p.Rejected('shared wall/full CPU exhausted')
        actual=prefix(folder)+expected
        result=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=available,env=self.env,max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        paths=[name+'.json',name+'.log',name+'-process.json']
        # Capture before Job.drc can parse or apply the strict preservation guard.
        self.captured[name]={'argv':actual,'input':str(folder),'before':before,'after':inventory(folder),
            'artifacts':{key:digest(io.read_bytes(self.out/key,LIMIT)) for key in paths if (self.out/key).is_file()}}
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected('protected native/canary stage failed')
        if set(self.captured[name]['artifacts'])!=set(paths) or self.captured[name]['after']!=before:raise p.Rejected('protected input changed or report missing')
        return result

def check_capture(job):
    for name,stage in job.captured.items():
        if inventory(Path(stage['input']))!=stage['after'] or stage['before']!=stage['after'] or any(p.sha(job.out/key)!=sha for key,sha in stage['artifacts'].items()):raise p.Rejected('captured input/report changed')


def drc_readback(job,source,expected):
    binding=shared.read(job.out/'drc-binding.json');target=job.out/'drc-input'/source.name
    if binding!={'source':str(source),'input':str(target),'before':expected,'after':expected,'saved':False}:raise p.Rejected('strict protected DRC binding differs')
    p.check_drc_project(expected,binding['after'],source.name)
    raw=shared.read(job.out/'drc.json');native=p.parse_report(job.out/'drc.json',source.name)
    f.process_check(job.out,{'steps':job.steps},'drc',prefix(target.parent)+stage_argv(job.out,'drc',source.name),allowed=(5 if native['findings'] else 0,))
    return raw,native

def experiment(output,*,run_native=False):
    if run_native is not True or HERE!=ROOT/'experiments/drc_input_protection_v1':raise p.Rejected('promote/checkpoint first; ROOT --run-native required')
    start=time.monotonic();cpu0=shared.cpu();remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(shared.cpu()-cpu0)))
    out=shared.owned(output,output=True);out.mkdir();protocol=shared.read(HERE/'PROTOCOL.json')
    record={'schema':1,'status':'incomplete','observations_complete':False,'original_inputs_unchanged':None,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,
        'protocol_sha256':p.sha(HERE/'PROTOCOL.json'),'sandbox_profile':PROFILE,'cases':[{'case':x,'status':'not_run'} for x in CASES],**{x:False for x in FALSE_FLAGS},
        'scope':'New input-write-protection hypothesis: canary, two owned legacy-PRL controls, then one PAW DRC. No export, routing, PRL normalization or support admission.',
        'accounting_point':'Stored totals precede last publication checks; observed wall/parent+waited-child CPU caps include final checks, not hard atomic quotas.'}
    jobs=[];originals={};source_bytes={};frozen=None;tools=None;runtime={};completed={};facts={}
    def account():
        record.update({x:False for x in FALSE_FLAGS});record.update(steps=[s for j in jobs for s in j.steps],wall_seconds=time.monotonic()-start,total_cpu_seconds=shared.cpu()-cpu0,within_budget=remaining()>0)
        record['native_executed']=any(s['name']=='drc' for s in record['steps'])
        if remaining()<=0:record.update(status='budget_exceeded',observations_complete=False)
    def stable():
        if shared.size(out)>LIMIT:raise p.Rejected('output cap')
        if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('runtime/tool/HEAD changed')
        if frozen is not None and (inventory(out/'code')!=frozen or any(p.sha(ROOT/name)!=value for name,value in runtime.items())):raise p.Rejected('committed helper changed')
        if any(inventory(Path(path))!=expected for path,expected in originals.items()):raise p.Rejected('original source/evidence changed')
        if p.sha(HERE/'PROTOCOL.json')!=record['protocol_sha256'] or record['sandbox_profile']!=PROFILE or [r['case'] for r in record['cases']]!=list(CASES):raise p.Rejected('protocol selection changed')
        for job in jobs:check_capture(job)
        for path,expected in source_bytes.items():
            if inventory(Path(path))!=expected:raise p.Rejected('derived source changed')
        for path,expected in completed.items():
            if inventory(Path(path))!=expected:raise p.Rejected('completed stage changed')
        for row in record['cases']:
            if row['case'] in facts and f.canonical(row)!=facts[row['case']]:raise p.Rejected('recorded interpretation changed')
        if any(record.get(x) is not False for x in FALSE_FLAGS) or remaining()<=0:raise p.Rejected('qualification/budget differs')
    try:
        # Freeze all old sources and failed evidence before any interpretation.
        for path,expected in protocol['original_trees'].items():
            full=shared.owned(ROOT/path);current=inventory(full)
            if current!=expected:raise p.Rejected('pinned original tree differs: '+path)
            originals[str(full)]=expected
        receipt=ROOT/protocol['fixture_receipt'];r=shared.read(receipt);p.check_result(receipt)
        candidate=shared.owned(Path(r['candidate']));base=bytes_tree(candidate.parent)
        if digest(base[candidate.name])!=protocol['fixture_candidate_sha256']:raise p.Rejected('accepted fixture differs')
        paw_hashes,paw_size=shared.source_binding('paw3395');paw=shared.source_spec('paw3395').source
        if inventory(paw.parent)!=paw_hashes:raise p.Rejected('PAW original differs')
        tools=p.tool_manifest();record['tools']=tools;runtime=shared.snapshot(out,tools,remaining)
        for path in [*(HERE/name for name in HELPERS),ROOT/'experiments/placement_production_controls_v1/driver.py']:
            raw=io.read_bytes(path,LIMIT);rel=str(path.relative_to(ROOT));available=remaining()
            if available<=0:raise p.Rejected('snapshot budget exhausted')
            blob=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=min(3,available)).stdout
            if raw!=blob:raise p.Rejected('uncommitted probe helper')
            target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);runtime[rel]=digest(raw)
        frozen=inventory(out/'code');record.update(runtime_sources=runtime,code_inventory=frozen,original_trees=originals)
        shared.reserve_copy(out,sum(map(len,base.values()))+4096,4)
        if shared.size(out)+paw_size+4*(sum(map(len,base.values()))+4096)+1024**2>LIMIT:raise p.Rejected('planned complete copies exceed cap')
        ignored=protocol['fixture_effective_ignored'];record['fixture_explicit_ignored']=protocol['fixture_explicit_ignored'];record['paw_explicit_ignored']=protocol['paw_explicit_ignored']
        row=record['cases'][0];row['status']='running';job=ProtectedJob(out/'canary',remaining);jobs.append(job)
        files={name:canary.SENTINEL for name in ('overwrite','append','truncate','unlink','rename','replace','chmod')};folder=job.out/'canary-input';write_copy(folder,files);stable()
        job.step('canary',stage_argv(job.out,'canary'));account();canary_check(shared.read(job.out/'canary.json'),folder)
        f.process_check(job.out,{'steps':job.steps},'canary',prefix(folder)+stage_argv(job.out,'canary'))
        row.update(status='observed',result=shared.read(job.out/'canary.json'),stage_evidence=job.captured);facts['canary']=f.canonical(row);completed[str(job.out)]=inventory(job.out);stable()
        legacy=io.read_bytes(ROOT/protocol['owned_legacy_prl'],LIMIT)
        if candidate.with_suffix('.kicad_prl').name in base:raise p.Rejected('unexpected existing positive PRL')
        generated=dict(base,**{candidate.with_suffix('.kicad_prl').name:legacy})
        for case in ('positive','missing_via','paw3395'):
            row=next(x for x in record['cases'] if x['case']==case);row['status']='running'
            if case=='paw3395':source=paw;expected=paw_hashes;mutation=None
            else:
                board,project,mutation=fixture.prepare(case,base[candidate.name],base[candidate.with_suffix('.kicad_pro').name])
                files=dict(generated,**{candidate.name:board,candidate.with_suffix('.kicad_pro').name:project});folder=out/(case+'-source');write_copy(folder,files);source=folder/candidate.name;expected=hashes(files);source_bytes[str(folder)]=expected
            job=ProtectedJob(out/case,remaining,source.name);jobs.append(job);stable()
            native=job.drc('drc',source,save=False);account();raw,native=drc_readback(job,source,expected)
            if case=='positive':
                if not p.native_accepted(native) or native['warnings'] or native['ignored_checks']!=ignored:raise p.Rejected('protected positive differs')
                witness={'clean_native_control':True}
            elif case=='missing_via':witness=negative_check(raw,native,mutation,ignored)
            else:
                baseline=p.parse_report(ROOT/protocol['paw_old_report'],source.name)
                if f.canonical(native)!=f.canonical(baseline):raise p.Rejected('protected PAW report differs from retained baseline')
                witness={'retained_raw_report_equivalent':True,'new_protection_hypothesis_only':True}
            row.update(status='observed',source=str(source),source_hashes=expected,mutation=mutation,native=native,witness=witness,stage_evidence=job.captured)
            facts[case]=f.canonical(row);completed[str(job.out)]=inventory(job.out);stable()
        record.update(status='observations_complete',observations_complete=True,original_inputs_unchanged=True)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc))
        for row in record['cases']:
            if row['status']=='running':row.update(status='failed',error=record['error'])
    # Capture execution facts even if the strict original-project guard failed.
    record['captured_stages']={str(j.out):j.captured for j in jobs}
    return shared.publish(out,record,stable,account,remaining)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required')
    previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for s in previous:signal.signal(s,interrupted)
        with shared.owned(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);record=experiment(args.output,run_native=True)
    finally:
        for s,h in previous.items():signal.signal(s,h)
    print(json.dumps({k:record[k] for k in ('status','observations_complete','routing_accepted')}));return 0 if record['observations_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
