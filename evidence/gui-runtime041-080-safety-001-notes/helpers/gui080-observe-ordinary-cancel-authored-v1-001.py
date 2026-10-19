"""Observe one live GUI080-owned ordinary Java interval; never cancel or route.

Requires the lead's known owned GUI PID. Only scoped children and known-PID
metadata are read. Later actual GUI Cancel and PID-bound cleanup are separate.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,shlex,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runs/runtime-directory-041/runtime'
BASE=RUNTIME/'.runs/gui-session080'
PREPARED_SHA='a0ee6588cdaf5594c1baaf4564a79b86ff9117484f642eadfe4cc253ca6cd3ff'
HEAD='f7524d7bbfb4824640c8ca51dc978769b2fab98b'
MANIFEST='3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
SHARED=ROOT/'.runs/owned-child-path-observer-001.py'
SHARED_SHA='e0bfa421ec519c31e8fbcc2dd601e74ea0a60b86f0c2a8377c92a05f25114d27'
BIND_TEMPLATE=ROOT/'.runs/gui080-observe-postincumbent-cancel-001.py'
BIND_SHA='21a7c6caa806744312e7ef4668a0d4350317369087aab9d6474206ba80330869'
MAX_WAIT=120
MAX_POLLS=240
MAX_LOG=2*1024**2


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_prepared():
    assert digest(BASE/'prepared-state.json')==PREPARED_SHA
    frozen=json.loads((BASE/'prepared-state.json').read_bytes())
    assert frozen['source_head']==HEAD and frozen['runtime_manifest_sha256']==MANIFEST
    assert digest(RUNTIME/'runtime-distribution.json')==MANIFEST
    for name,pin in frozen['prerequisites_sha256'].items():
        path=Path(name)
        assert path.is_absolute() and not path.is_symlink() and path.is_file()
        assert digest(path)==pin
    protocol=Path(frozen['recovery_protocol'])
    assert protocol==BASE/'recovery-controls-001/protocol-required-001.json'
    assert digest(protocol)==frozen['recovery_protocol_sha256']
    return frozen


def ps(pid):
    value=subprocess.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,ppid=,stat=,lstart=,command='],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=2,
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},check=False)
    if len(value.stdout)>32768 or len(value.stderr)>8192:raise ValueError('known-PID metadata exceeded bound')
    if value.returncode==1 and not value.stdout.strip():return None
    if value.returncode!=0:raise ValueError('known-PID metadata unavailable')
    lines=value.stdout.splitlines()
    if len(lines)!=1:raise ValueError('one known-PID metadata row required')
    row=lines[0].strip().split(None,8)
    if len(row)!=9 or int(row[0])!=pid:raise ValueError('known-PID metadata identity differs')
    if 'Z' in row[2]:return None
    return dict(pid=pid,ppid=int(row[1]),state=row[2],start_time=' '.join(row[3:8]),command=row[8])


def same(first,second):
    return second is not None and all(first[key]==second[key] for key in ('pid','ppid','start_time','command'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace_name');parser.add_argument('--gui-pid',required=True,type=int)
    args=parser.parse_args()
    assert sys.platform=='darwin' and 0<args.gui_pid<2**31
    assert re.fullmatch('autorouter-gui-[0-9a-f]{32}',args.workspace_name)
    assert digest(SHARED)==SHARED_SHA and digest(BIND_TEMPLATE)==BIND_SHA
    spec=importlib.util.spec_from_file_location('owned_child_path_observer_gui080',SHARED)
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    workspace=BASE/'jobs'/args.workspace_name
    output=BASE/'ordinary-cancel-engine-observed-001.json'
    assert workspace.is_dir() and workspace.resolve()==workspace
    assert not os.path.lexists(output)
    prepared=bind_prepared()
    protocol=json.loads(Path(prepared['recovery_protocol']).read_bytes())
    plan=protocol['ordinary_cancel'];repair=protocol['recovery']['repair']
    assert plan['method']=='route' and plan['source']==repair['source']
    source=Path(plan['source']);settings=workspace/'settings.json';route=workspace/'route'
    assert plan['settings']==dict(schema=1,scope='whole_board_unlocked_routing',seconds=90,
        adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
    assert json.loads(settings.read_bytes())==plan['settings']
    def sources():return {p.name:digest(p) for p in source.parent.iterdir()}
    assert sources()==repair['source_hashes']
    settings_pin=digest(settings)
    lock=json.loads((RUNTIME/'toolchain.lock.json').read_bytes())
    native_python=Path(lock['native_profiles']['10.0.7']['kicad_python']['path'])
    gui_commands={' '.join([str(path),'-B','-m','autorouter.gui']) for path in (native_python,native_python.resolve())}
    expected_cli=' '.join([str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter','route',str(source),
        '--settings',str(settings),'--output',str(route)])
    java=Path('/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home/bin/java').resolve()
    jar=RUNTIME/'.tools/freerouting-2.5.0.jar'
    started=time.monotonic();record=dict(schema=1,workspace=str(workspace),gui_pid=args.gui_pid,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),maximum_wait_seconds=MAX_WAIT,
        maximum_polls=MAX_POLLS,polls=0,observed=False,signals_sent=False,
        Native_executed_by_observer=False,routing_started_by_observer=False,cancellation_qualified=False,
        prepared_state_sha256=PREPARED_SHA,runtime_manifest_sha256=MANIFEST,source_head=HEAD,
        source=str(source),source_hashes=repair['source_hashes'],settings_sha256=settings_pin,
        observer_helper_sha256=digest(Path(__file__)),shared_process_path_helper_sha256=SHARED_SHA,
        prepared_binding_template_sha256=BIND_SHA,
        scope='One sampled live GUI-to-ordinary-CLI-to-Java engine interval before lead-controlled actual GUI Cancel. '
              'No signals, routing/Native execution, cancellation, cleanup, permanent absence or all-phase proof. '
              'PID/start-time/path checks are cooperative snapshots, not atomic ownership authentication; the process may exit afterward.')
    try:
        gui_first=ps(args.gui_pid)
        assert gui_first is not None and gui_first['command'] in gui_commands,'known GUI identity unavailable'
        while time.monotonic()-started<MAX_WAIT and record['polls']<MAX_POLLS:
            record['polls']+=1
            if (route/'result.json').exists() or (route/'engine-process.json').exists():
                raise ValueError('Required live engine interval already finished; timing not passed')
            assert same(gui_first,ps(args.gui_pid)),'known GUI PID/start/command changed'
            for cli in observer.owned_paths(args.gui_pid):
                if cli['executable']!=str((RUNTIME/'.venv/bin/python').resolve()):continue
                cli_row=ps(cli['pid'])
                if cli_row is None or cli_row['ppid']!=args.gui_pid or cli_row['command']!=expected_cli:continue
                engine_log=route/'engine.log'
                if not engine_log.is_file() or not 0<engine_log.stat().st_size<=MAX_LOG:continue
                for worker in observer.owned_paths(cli['pid']):
                    if worker['executable']!=str(java):continue
                    java_row=ps(worker['pid'])
                    if java_row is None or java_row['ppid']!=cli['pid']:continue
                    argv=shlex.split(java_row['command'])
                    if not argv or argv[0]!=str(java):continue
                    wanted={'-jar':str(jar),'-de':str(route/'task.dsn'),'-do':str(route/'routes.ses')}
                    if any(argv.count(flag)!=1 or argv.index(flag)+1>=len(argv) or argv[argv.index(flag)+1]!=value for flag,value in wanted.items()):continue
                    if not all(flag in argv for flag in ('--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false')):continue
                    if cli not in observer.owned_paths(args.gui_pid) or worker not in observer.owned_paths(cli['pid']):continue
                    if not all((same(gui_first,ps(args.gui_pid)),same(cli_row,ps(cli['pid'])),same(java_row,ps(worker['pid'])))):continue
                    if (route/'result.json').exists() or (route/'engine-process.json').exists():continue
                    record.update(observed=True,observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        owned_engine=worker,ancestor_chain=[java_row,cli_row,gui_first],
                        engine_log_bytes_at_observation=engine_log.stat().st_size,
                        live_interval_elapsed_seconds=time.monotonic()-started)
                    break
                if record['observed']:break
            if record['observed']:break
            time.sleep(.25)
        assert record['observed'],'No required live interval within finite bounds; timing not passed'
    except BaseException as error:
        record['error']=type(error).__name__+': '+str(error);record['observed']=False
    try:
        bind_prepared()
        assert sources()==repair['source_hashes'] and digest(settings)==settings_pin
        assert digest(SHARED)==SHARED_SHA and digest(BIND_TEMPLATE)==BIND_SHA
        assert digest(Path(__file__))==record['observer_helper_sha256']
    except BaseException as error:
        record.update(observed=False,freshness_error=type(error).__name__+': '+str(error))
    record['observer_wall_seconds']=time.monotonic()-started
    encoded=(json.dumps(record,indent=2,sort_keys=True)+'\n').encode();assert len(encoded)<=64*1024
    with output.open('xb') as stream:stream.write(encoded)
    print(encoded.decode(),end='')
    return 0 if record['observed'] else 2


if __name__=='__main__':raise SystemExit(main())
