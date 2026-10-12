"""ROOT-only three-case legacy-zone observations. No routing or admission."""
from pathlib import Path
import argparse,fcntl,json,signal,subprocess,sys,time
ROOT=next(path for path in Path(__file__).resolve().parents if (path/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'experiments/lipo_native_diagnostic_v1'))
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,config as c
from autorouter.runner import run
from experiments.lipo_native_diagnostic_v1 import driver as shared
import controls
SECONDS=30;LIMIT=20*1024**2
HELPERS=('driver.py','worker.py','controls.py','test_controls.py','PROTOCOL.json','README.md')
FALSE_FLAGS=('routing_accepted','production_supported','native_legacy_enforcement_qualified','format_support_qualified','dependency_complete')


def capture(path):return shared.inventory(path)
def hashes(files):return {name:shared.sha_bytes(raw) for name,raw in files.items()}
def observer_argv(out):return [str(c.PYTHON),str(HERE/'worker.py'),str(out/'observe-input/smoke.kicad_pcb'),str(out/'context.json'),str(out/'native.dsn'),str(out/'zones.json')]
def drc_argv(out):return [str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'drc.json'),str(out/'drc-input/smoke.kicad_pcb')]


def bind_observation(out,expected,case):
    board=out/'observe-input/smoke.kicad_pcb';context=shared.read(out/'context.json');zones=shared.read(out/'zones.json');dsn=p.sha(out/'native.dsn')
    f.context_binding(context,board,expected,'export',dsn)
    if context.get('routing_accepted') is not False or context.get('context_schema')!=1:raise p.Rejected('unexpected context status')
    for key,value in {'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':'export','source':str(board),
            'board_sha256':expected[board.name],'project_sha256':expected['smoke.kicad_pro'],'dsn_sha256':dsn,'floor_context_sha256':p.sha(out/'context.json'),
            'input_hashes_before':expected,'input_hashes_after':expected,'same_loaded_board':True,'board_saved':False,'routing_accepted':False,'geometry_qualified':False}.items():
        if f.canonical(zones.get(key))!=f.canonical(value):raise p.Rejected('zone context binding differs: '+key)
    if zones['observation_before_export']!=zones['observation_after_export']:raise p.Rejected('export changed zone/count observation')
    return controls.evaluate(case,io.read_bytes(board,LIMIT),context,zones['observation_before_export'])


def bind_drc(job,expected):
    out=job.out;binding=shared.read(out/'drc-binding.json');board=out/'observe-input/smoke.kicad_pcb';target=out/'drc-input'/board.name
    if binding.get('source')!=str(board) or binding.get('input')!=str(target) or binding.get('saved') is not False or binding.get('before')!=expected:raise p.Rejected('DRC provenance differs')
    p.check_drc_project(expected,binding['after'],board.name)
    if capture(target.parent)!=binding['after']:raise p.Rejected('DRC input changed')
    shared.read(out/'drc.json') # strict JSON before shared native parser
    native=p.parse_report(out/'drc.json',board.name)
    f.process_check(out,{'steps':job.steps},'drc',f.SANDBOX+drc_argv(out),allowed=(5 if native['findings'] else 0,))
    raw=shared.read(out/'drc.json')
    legacy=[row for section in ('violations','unconnected_items','schematic_parity') for row in raw[section] if row.get('type')=='zone_has_empty_net']
    return {'native':native,'raw_legacy_findings':legacy,'binding_sha256':p.sha(out/'drc-binding.json'),'report_sha256':p.sha(out/'drc.json'),
            'scope':'Observed findings including all opens/warnings/exclusions; not routing acceptance or legacy-rule enforcement qualification.'}


class ZoneJob(f.FloorJob):
    def __init__(self,out,remaining):super().__init__(out,SECONDS,remaining);self.captured={}
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        if already_sandboxed or name not in ('observe','drc') or list(map(str,argv))!=(observer_argv(self.out) if name=='observe' else drc_argv(self.out)):
            raise p.Rejected('unexpected native action')
        available=self.remaining()
        if available<=0:raise p.Rejected('shared wall/full CPU exhausted')
        result=run(f.SANDBOX+list(map(str,argv)),cwd=self.out,log=self.out/(name+'.log'),timeout=available,env=self.env,
            max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        # Freeze emitted bytes and complete input before any caller/Job.drc parser.
        names=([name+'-process.json',name+'.log']+(['context.json','zones.json','native.dsn'] if name=='observe' else ['drc.json']))
        self.captured[name]={'artifacts':{key:shared.sha_bytes(io.read_bytes(self.out/key,LIMIT)) for key in names if (self.out/key).is_file()},
                             'input':capture(self.out/('observe-input' if name=='observe' else 'drc-input'))}
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected('native '+name+' failed')
        if set(self.captured[name]['artifacts'])!=set(names):raise p.Rejected('native stage evidence incomplete')
        return result


def experiment(output,*,run_native=False):
    if run_native is not True or HERE!=ROOT/'experiments/legacy_zone_controls_v1':raise p.Rejected('promote/checkpoint exact helper first; ROOT --run-native required')
    start=time.monotonic();cpu0=shared.cpu();remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(shared.cpu()-cpu0)))
    out=shared.owned(output,output=True);out.mkdir();protocol=shared.read(HERE/'PROTOCOL.json');base=ROOT/'fixtures/smoke'
    record={'schema':1,'status':'incomplete','observations_complete':False,'original_inputs_unchanged':None,
        'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,'protocol_sha256':p.sha(HERE/'PROTOCOL.json'),
        'scope':'Three owned unrouted zone capability fixtures; legacy independent predicate and raw native findings are distinct. No PAW rerun, engine, saved fill or production admission.',
        'accounting_point':'Stored totals precede final publication; whole wall and parent-plus-waited-child CPU caps include final checks. Observed caps, not OS quotas.',
        'cases':[{'case':case,'status':'not_run','export_completed':False,'drc_completed':False} for case in controls.CASES],**{key:False for key in FALSE_FLAGS}}
    jobs=[];expected_cases={};completed={};frozen=None;tools=None;base_hashes=None;runtime_sources={}
    def account():
        record.update({key:False for key in FALSE_FLAGS});record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=shared.cpu()-cpu0,steps=[step for job in jobs for step in job.steps])
        record['native_executed']=bool(record['steps']);record['within_budget']=remaining()>0
        if not record['within_budget']:record.update(status='budget_exceeded',observations_complete=False)
        for row,job in zip(record['cases'],jobs):
            row['stage_evidence']=job.captured
            row['export_completed']=any(s['name']=='observe' and s['exit_code']==0 and s['cleanup_complete'] is True for s in job.steps) and {'context.json','zones.json','native.dsn'}<=set(job.captured.get('observe',{}).get('artifacts',{}))
            row['drc_completed']=any(s['name']=='drc' and s['exit_code'] in (0,5) and s['cleanup_complete'] is True for s in job.steps) and 'drc.json' in job.captured.get('drc',{}).get('artifacts',{})
    def stable():
        if shared.size(out)>LIMIT:raise p.Rejected('whole diagnostic output cap')
        if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('code/tool/HEAD changed')
        if frozen is not None and (capture(out/'code')!=frozen or any(p.sha(ROOT/name)!=sha for name,sha in runtime_sources.items())):raise p.Rejected('helper snapshot changed')
        if any(record.get(key) is not False for key in FALSE_FLAGS):raise p.Rejected('unsupported positive qualification claim')
        if p.sha(Path(protocol['pcbnew_wrapper']['path']))!=protocol['pcbnew_wrapper']['sha256']:raise p.Rejected('native wrapper changed')
        if [row['case'] for row in record['cases']]!=list(controls.CASES):raise p.Rejected('case denominator changed')
        if base_hashes is not None and capture(base)!=base_hashes:raise p.Rejected('base original changed')
        if p.sha(HERE/'PROTOCOL.json')!=record['protocol_sha256']:raise p.Rejected('protocol changed')
        for row,job in zip(record['cases'],jobs):
            expected=expected_cases[row['case']]
            if row.get('source_hashes')!=expected:raise p.Rejected('recorded source fixture differs')
            rebuilt_board,rebuilt_project=controls.derive(base_bytes['smoke.kicad_pcb'],base_bytes['smoke.kicad_pro'],row['case'])
            if hashes(dict(base_bytes,**{'smoke.kicad_pcb':rebuilt_board,'smoke.kicad_pro':rebuilt_project}))!=expected:raise p.Rejected('derived case recipe changed')
            if capture(job.out/'observe-input')!=expected:raise p.Rejected('owned source fixture changed')
            for name,stage in job.captured.items():
                if any(p.sha(job.out/key)!=sha for key,sha in stage['artifacts'].items()) or capture(job.out/('observe-input' if name=='observe' else 'drc-input'))!=stage['input']:raise p.Rejected('frozen raw stage/input changed')
            if row['case'] in completed:
                if capture(job.out)!=completed[row['case']]:raise p.Rejected('completed case changed')
                if bind_observation(job.out,expected,row['case'])!=row['predicate'] or bind_drc(job,expected)!=row['drc']:raise p.Rejected('recorded interpretation differs')
        if remaining()<=0:raise p.Rejected('whole diagnostic resource cap')
    try:
        base_bytes=io.inventory(base,contents=True,max_bytes=LIMIT,max_files=512,max_entries=1024);base_hashes=hashes(base_bytes)
        if base_hashes!=protocol['base_sha256']:raise p.Rejected('base source pins differ')
        record['base_sha256']=base_hashes;tools=p.tool_manifest();record['tools']=tools
        runtime_sources=shared.snapshot(out,tools,remaining)
        for path in [*(HERE/name for name in HELPERS),*(base/name for name in base_hashes)]:
            rel=str(path.relative_to(ROOT));raw=io.read_bytes(path,LIMIT)
            blob=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=max(.001,min(3,remaining()))).stdout
            if blob!=raw:raise p.Rejected('uncommitted diagnostic/base: '+rel)
            target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);runtime_sources[rel]=shared.sha_bytes(raw)
        record['runtime_sources']=runtime_sources;frozen=capture(out/'code');record['code_inventory']=frozen
        if p.sha(Path(protocol['pcbnew_wrapper']['path']))!=protocol['pcbnew_wrapper']['sha256']:raise p.Rejected('installed wrapper declarations changed')
        shared.reserve_copy(out,sum(map(len,base_bytes.values()))+4096,6)
        for row in record['cases']:
            case=row['case'];board,project=controls.derive(base_bytes['smoke.kicad_pcb'],base_bytes['smoke.kicad_pro'],case)
            files=dict(base_bytes,**{'smoke.kicad_pcb':board,'smoke.kicad_pro':project});expected_cases[case]=hashes(files)
            job=ZoneJob(out/case,remaining);jobs.append(job);source=job.out/'observe-input';source.mkdir()
            for name,raw in files.items():(source/name).write_bytes(raw)
            row.update(status='running',source_hashes=expected_cases[case]);stable()
            job.step('observe',observer_argv(job.out));account()
            f.process_check(job.out,{'steps':job.steps},'observe',f.SANDBOX+observer_argv(job.out))
            row['predicate']=bind_observation(job.out,expected_cases[case],case);stable()
            job.drc('drc',source/'smoke.kicad_pcb',save=False);account()
            row['drc']=bind_drc(job,expected_cases[case]);row['status']='observed'
            completed[case]=capture(job.out);stable()
        record.update(status='observations_complete',observations_complete=True,original_inputs_unchanged=True)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',observations_complete=False,error=type(exc).__name__+': '+str(exc))
        for row in record['cases']:
            if row['status']=='running':row['status']='failed';row['error']=record['error']
    return shared.publish(out,record,stable,account,remaining)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native is required after reviewed committed promotion')
    previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for s in previous:signal.signal(s,interrupted)
        with shared.owned(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);record=experiment(args.output,run_native=True)
    finally:
        for s,handler in previous.items():signal.signal(s,handler)
    print(json.dumps({key:record[key] for key in ('status','observations_complete','routing_accepted')}))
    return 0 if record['observations_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
