"""ROOT-only mixed-class prerequisite. Reuses retained bounded IO/publication and native mapping."""
import argparse,fcntl,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/runner.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'experiments/custom_pad_area_probe_v1'))
from experiments.custom_pad_area_probe_v1 import driver as base
sys.path.insert(0,str(ROOT/'experiments/pic_custom_observer_v1'))
from experiments.pic_custom_observer_v1 import driver as original,mapping
from autorouter import runner,placement_clearance as io,sexpr as sx,floor_route as floor
sys.path.insert(0,str(HERE))
import transport

SECONDS=180.0;LIMIT=64*1024**2
HELPERS=('driver.py','worker.py','transport.py','MixedClassProbe.java','test_draft.py','PROTOCOL.json','README.md')
REUSE=('experiments/custom_pad_area_probe_v1/driver.py','experiments/custom_pad_area_probe_v1/derive.py',
    'experiments/custom_pad_area_probe_v1/checks.py','experiments/custom_pad_area_probe_v1/AreaContactProbe.java',
    'experiments/pic_custom_observer_v1/driver.py','experiments/pic_custom_observer_v1/worker.py','experiments/pic_custom_observer_v1/mapping.py')

def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=2000,max_entries=4000)
def source_paths():return [HERE/n for n in HELPERS]+[ROOT/n for n in REUSE]+list(sorted((ROOT/'autorouter').glob('*.py')))+[ROOT/'toolchain.lock.json',ROOT/'data/sources.json']
def runtime(protocol):
    git=base.head_witness()
    tools={name:base.content(Path(row['path']) if Path(row['path']).is_absolute() else ROOT/row['path'],row['bytes'],digest=True) for name,row in protocol['tools'].items()}
    sources={str(p.relative_to(ROOT)):base.content(p,2*1024**2,digest=True) for p in source_paths()}
    basis={name:base.content(ROOT/name,row['bytes'],digest=True) for name,row in protocol['basis'].items()}
    original_hashes,total=original.source_binding()
    return {'git':git,'tools':tools,'sources':sources,'basis':basis,'original':original_hashes,'original_bytes':total}

def verify_native(out,source_hashes,notes):
    context=base.decode(base.content(out/'context.json',2*1024**2));custom=base.decode(base.content(out/'custom.json',4*1024**2));raw=base.content(out/'native.dsn',1024**2)
    board=out/'observe-input'/original.SOURCE.name
    floor.context_binding(context,board,source_hashes,'export',base.sha(raw))
    for key in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after'):
        if custom.get(key)!=context.get(key):raise ValueError('same-load custom/context binding differs')
    if custom.get('floor_context_sha256')!=base.sha(base.content(out/'context.json')):raise ValueError('custom context digest differs')
    mapping.floor_identity(context,notes,base.decode(base.content(board.with_suffix('.kicad_pro'))))
    rows=mapping.custom_identity(custom,context,notes)
    clear=custom['observation_before_export']['clearance_observation']
    report=base.content(out/'initialization-drc.txt',2*1024**2)
    if clear['initialization_returned'] is not True or clear['report_sha256']!=base.sha(report) or clear['report_bytes']!=len(report):raise ValueError('explicit initialized same-board report binding differs')
    for stage in ('pre_initialization','post_initialization'):
        observed={r['uuid']:r for r in clear[stage]}
        if len(observed)!=247 or set(observed)!=set(notes['source_pads_identity']):raise ValueError('clearance terminal census differs')
        for uid,row in observed.items():
            if any(row[k]!=notes['source_pads_identity'][uid][k] for k in ('reference','number','net')):raise ValueError('clearance terminal identity differs')
    derived,expected=transport.derive(raw,context,custom,notes)
    return derived,expected,{'initialized':True,'pairwise_rules_qualified':False,
        'local_optional_observations_supported':all(x['status']=='observed' for r in clear['post_initialization'] for x in (r['pad_local'],r['footprint_local'],r['pad_override'])),
        'report_sha256':base.sha(report),'custom_pad_own_clearance':[{k:r[k] for k in ('uuid','net','netclass','class_clearance_nm','own','pad_local','footprint_local','pad_override')} for r in clear['post_initialization'] if r['uuid'] in {p['uuid'] for p in rows}]}

def experiment(out,*,started=None,cpu_started=None):
    if HERE.relative_to(ROOT).as_posix()!='experiments/pic_mixed_transport_probe_v1':raise ValueError('promote and commit reviewed helper before execution')
    start=time.monotonic() if started is None else started;cpu0=base.cpu() if cpu_started is None else cpu_started;out=base.real(out)
    if out.parent!=ROOT/'.runs' or out.exists():raise ValueError('fresh direct .runs output required')
    protocol=base.decode(base.content(HERE/'PROTOCOL.json'));record={'schema':1,'status':'preparing','observations_complete':False,
        'routing_accepted':False,'custom_pad_support_qualified':False,'mixed_clearance_equivalence_qualified':False,
        'routing_executed':False,'ses_executed':False,'native_process_executed':False,'import_process_executed':False,
        'steps':[],'wall_budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
        'max_output_bytes':LIMIT,'accounting_point':'Stored totals precede final publication checks; acceptance caps include them.',
        'cpu_enforcement':'Measured self plus waited children, acceptance cap; not hard CPU preemption.'}
    def remaining():
        left=min(SECONDS-(time.monotonic()-start),SECONDS-(base.cpu()-cpu0))
        if left<=0:raise TimeoutError('shared wall/full CPU cap exceeded')
        return left
    def account():record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=base.cpu()-cpu0)
    out.mkdir();before=None;frozen={}
    def capture():
        for name,digest in inventory(out).items():
            if name in frozen and frozen[name]!=digest:raise ValueError('completed evidence changed before capture')
            frozen[name]=digest
    def stable():
        actual=inventory(out)
        if any(actual.get(k)!=v for k,v in frozen.items()):raise ValueError('retained evidence changed')
        if before is not None and runtime(protocol)!=before:raise ValueError('source/helper/tool/API/HEAD changed')
        actual=inventory(out)
        if any(actual.get(k)!=v for k,v in frozen.items()):raise ValueError('retained evidence changed after runtime sampling')
        remaining()
    try:
        if (type(protocol['schema']) is not int or protocol['schema']!=1
                or base.canonical(protocol['limits'])!=base.canonical({'wall_seconds':180,'full_cpu_seconds':180,'output_bytes':LIMIT,'java_heap':'256m'})
                or base.canonical(protocol['cases'])!=base.canonical([False,True])):raise ValueError('fixed prospective protocol differs')
        if Path(sys.executable).resolve()!=Path(protocol['tools']['python']['path']):raise ValueError('invoking Python differs')
        before=runtime(protocol)
        if before['tools']!={k:{x:v[x] for x in ('bytes','sha256')} for k,v in protocol['tools'].items()} or before['basis']!=protocol['basis']:raise ValueError('pinned tools/basis differ')
        for relative,pin in before['sources'].items():
            raw=base.content(ROOT/relative,2*1024**2)
            blob=subprocess.run(['git','show',before['git']['head']+':'+relative],cwd=ROOT,capture_output=True,check=True,timeout=min(3,remaining())).stdout
            if blob!=raw or base.sha(raw)!=pin['sha256']:raise ValueError('commit exact helper/core before execution')
            target=out/'code'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        for name in ('observe-input','classes','home','tmp'): (out/name).mkdir()
        for name,digest in before['original'].items():
            raw=base.content(original.SOURCE.parent/name,2*1024**2)
            if base.sha(raw)!=digest:raise ValueError('source changed during copy')
            target=out/'observe-input'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        if inventory(out/'observe-input')!=before['original']:raise ValueError('complete input copy differs')
        base.write(out/'runtime.json',before);capture();record['runtime']=before
        notes=mapping.source_notes(sx.parse(base.content(out/'observe-input'/original.SOURCE.name).decode()),base.decode(base.content(out/'observe-input'/original.SOURCE.with_suffix('.kicad_pro').name)))
        env={'HOME':str(out/'home'),'TMPDIR':str(out/'tmp'),'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
        def step(name,argv,cap):
            stable();result=runner.run(argv,cwd=out,log=out/(name+'.log'),timeout=min(cap,remaining()),env=env,max_log_bytes=1024**2,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
            if name=='native-observe':record['native_process_executed']=type(result.get('pid')) is int
            if name=='import':record['import_process_executed']=type(result.get('pid')) is int
            record['steps'].append({'name':name,**result});base.write(out/(name+'-process.json'),result);capture()
            if result['status']=='cancelled':raise KeyboardInterrupt('owned worker cancelled')
            if result['status']!='success' or result['exit_code']!=0 or result.get('cleanup_complete') is not True:raise ValueError(name+' failed; raw artifacts retained')
            stable()
        code=out/'code'/str(HERE.relative_to(ROOT));tools=protocol['tools']
        step('native-observe',[*base.SANDBOX,tools['native_python']['path'],str(code/'worker.py'),str(out/'observe-input'/original.SOURCE.name),str(out/'context.json'),str(out/'native.dsn'),str(out/'custom.json'),str(out/'initialization-drc.txt')],60)
        derived,expected,native=verify_native(out,before['original'],notes);record['native']=native
        (out/'mixed.dsn').write_bytes(derived);base.write(out/'expectations.json',expected);capture()
        jar=str(ROOT/tools['jar']['path'])
        step('compile',[*base.SANDBOX,tools['javac']['path'],'-J-Xmx256m','-J-Duser.home='+env['HOME'],'-proc:none','-classpath',jar,'-d',str(out/'classes'),str(code/'MixedClassProbe.java'),str(out/'code/experiments/custom_pad_area_probe_v1/AreaContactProbe.java')],30)
        step('import',[*base.SANDBOX,tools['java']['path'],'-Xmx256m','-Djava.awt.headless=true','-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],'-cp',str(out/'classes')+os.pathsep+jar,'MixedClassProbe',str(out/'mixed.dsn'),str(out/'observations.json')],60)
        comparisons=transport.validate(base.decode(base.content(out/'observations.json',16*1024**2)),expected)
        record.update(status='completed',observations_complete=all(r['observed'] for r in comparisons),case_comparison=comparisons)
        if not record['observations_complete']:record['status']='observed-incomplete'
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
    record['frozen_evidence']=frozen
    return base.publish(out,record,stable,account,remaining)

def main(argv=None):
    started=time.monotonic();cpu_started=base.cpu()
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-probe',action='store_true');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(argv)
    if not args.run_probe:parser.error('--run-probe required')
    with base.cancellation(),base.real(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.output,started=started,cpu_started=cpu_started)
    print(base.canonical({k:result.get(k) for k in ('status','observations_complete','wall_seconds','total_cpu_seconds')}).decode(),end='')
    return 0 if result['observations_complete'] else 1

if __name__=='__main__':raise SystemExit(main())
