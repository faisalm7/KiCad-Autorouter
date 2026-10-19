"""Finite forced Native-worker window for one GUI080 post-incumbent Cancel.

Authoring does not execute this control. During an authorized execution, STOP and
finally CONT target only one exact owned Native refill-drc worker. GUI/CLI are
never signalled. The lead must perform actual GUI Cancel and retain its journal.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,shlex,signal,stat,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runs/runtime-directory-041/runtime'
BASE=RUNTIME/'.runs/gui-session080'
PREPARED_SHA='a0ee6588cdaf5594c1baaf4564a79b86ff9117484f642eadfe4cc253ca6cd3ff'
HEAD='f7524d7bbfb4824640c8ca51dc978769b2fab98b'
MANIFEST='3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
LOCK_SHA='cec0446e5ed3554b0c0b286cbb61e5aceb5bc013e87839db3f7081b9fd2f24d9'
SHARED=ROOT/'.runs/owned-child-path-observer-001.py'
SHARED_SHA='e0bfa421ec519c31e8fbcc2dd601e74ea0a60b86f0c2a8377c92a05f25114d27'
BIND_TEMPLATE=ROOT/'.runs/gui080-observe-postincumbent-cancel-001.py'
BIND_SHA='21a7c6caa806744312e7ef4668a0d4350317369087aab9d6474206ba80330869'
INVENTORY_SHA='53f35206860617ed44fd5c5f1eb165894368b079e35fc89e060adc2f01997f41'
GUI_APP_BYTES=151616
GUI_APP_SHA='d093a4ba5f06f33a3d508023398447f01b41fc55a6cdbe8d72a01765c537fe61'
MAX_WAIT=120
HOLD_SECONDS=15
MAX_POLLS=480


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def check_gui_app(path):
    before=path.lstat()
    assert path.is_absolute() and path.resolve()==path
    assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==GUI_APP_BYTES
    assert digest(path)==GUI_APP_SHA
    after=path.lstat()
    keys=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink')
    assert all(getattr(before,key)==getattr(after,key) for key in keys)

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

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()


def bounded_json(path,maximum=1024*1024):
    before=path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_size<=maximum and not path.is_symlink()
    raw=path.read_bytes();assert len(raw)==before.st_size
    return raw,json.loads(raw)


def write_receipt(stream,value):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    assert len(raw)<=64*1024
    stream.write(raw);stream.flush();os.fsync(stream.fileno())


def cwd_is(pid,expected):
    value=subprocess.run(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=2,
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},check=False)
    assert value.returncode==0 and len(value.stdout)<=32768 and len(value.stderr)<=8192
    names=[line[1:] for line in value.stdout.splitlines() if line.startswith('n')]
    assert names==[str(expected)],'Exact owned process cwd required'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace_name');parser.add_argument('--gui-pid',required=True,type=int)
    args=parser.parse_args()
    assert sys.platform=='darwin' and 0<args.gui_pid<2**31
    assert re.fullmatch('autorouter-gui-[0-9a-f]{32}',args.workspace_name)
    workspace=BASE/'jobs'/args.workspace_name;route=workspace/'route'
    control=BASE/'recovery-controls-001/no-repair'
    ready=control/'postincumbent-pause-ready-001.json'
    final=control/'postincumbent-pause-result-001.json'
    assert workspace.is_dir() and workspace.resolve()==workspace
    assert not os.path.lexists(ready) and not os.path.lexists(final)
    started=time.monotonic();worker_row=None;stopped=False;inventory=None;source=None;settings_pin=None
    record=dict(schema=1,workspace=str(workspace),gui_pid=args.gui_pid,started_utc=utc(),
        maximum_discovery_seconds=MAX_WAIT,maximum_discovery_polls=MAX_POLLS,hold_seconds=HOLD_SECONDS,
        metadata_call_timeout_seconds=2,cleanup_metadata_calls_maximum=1,
        metadata_calls_may_overshoot_loop_deadline=True,forced_window=True,natural_timing_claim=False,
        signals_target_one_verified_Native_worker_only=True,GUI_signalled=False,CLI_signalled=False,
        Native_started_by_controller=False,routing_started_by_controller=False,cancellation_qualified=False,
        all_phase_cancellation_claim=False,SIGINT_only_claim=False,paused=False,resumed=False,
        known_worker_exit_during_hold=False,ready_written=False,control_observation_complete=False,
        prepared_state_sha256=PREPARED_SHA,runtime_manifest_sha256=MANIFEST,source_head=HEAD,
        helper_sha256=digest(Path(__file__)),source_observer_sha256=BIND_SHA,
        shared_child_path_helper_sha256=SHARED_SHA,
        scope='One deliberately forced post-incumbent Native refill-drc interval. STOP/CONT do not prove '
              'natural timing or cancellation by themselves. Actual GUI action, CLI cancellation and '
              'worker cleanup require separate matching receipts. PID/birth/command/cwd checks are '
              'cooperative snapshots, not atomic hostile-process authentication.')
    # Reserve this single control exclusively before any signalling; preserve even failures.
    with final.open('xb') as final_stream:
        try:
            assert digest(SHARED)==SHARED_SHA and digest(BIND_TEMPLATE)==BIND_SHA
            assert digest(RUNTIME/'toolchain.lock.json')==LOCK_SHA
            assert digest(RUNTIME/'autorouter/placement_clearance.py')==INVENTORY_SHA
            prepared=bind_prepared()
            protocol=json.loads(Path(prepared['recovery_protocol']).read_bytes())
            plan=protocol['recovery']['no-repair'];source=Path(plan['source'])
            assert plan['method']=='recover' and plan['whole_method_seconds']==90
            assert plan['settings']==dict(schema=1,scope='whole_board_unlocked_routing',seconds=90,
                adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
            assert json.loads((workspace/'settings.json').read_bytes())==plan['settings']
            settings_pin=digest(workspace/'settings.json')
            sys.path.insert(0,str(RUNTIME))
            from autorouter.placement_clearance import inventory
            assert inventory(source.parent)==plan['source_hashes']
            lock=json.loads((RUNTIME/'toolchain.lock.json').read_bytes())
            pins=lock['native_profiles']['10.0.7'];native_cli=Path(pins['kicad_cli']['path'])
            assert prepared['tools']['kicad']=='10.0.7'
            assert all(prepared['tools']['files'][pin['path']]==pin['sha256'] for pin in pins.values())
            assert native_cli.is_file() and not native_cli.is_symlink() and native_cli.resolve()==native_cli
            assert native_cli.stat().st_size==pins['kicad_cli']['bytes'] and digest(native_cli)==pins['kicad_cli']['sha256']
            gui_app=Path(pins['kicad_python']['path']).parents[1]/'Resources/Python.app/Contents/MacOS/Python'
            check_gui_app(gui_app)
            expected_gui=str(gui_app)+' -B -m autorouter.gui'
            expected_cli=' '.join([str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter','recover',str(source),
                '--seconds','90','--output',str(route)])
            expected_worker=' '.join([str(native_cli),'pcb','drc','--format','json','--severity-all',
                '--all-track-errors','--refill-zones','--exit-code-violations','--output',str(route/'refill-drc.json'),
                '--save-board',str(route/'refill'/source.name)])
            spec=importlib.util.spec_from_file_location('owned_child_paths_gui080_pause',SHARED)
            observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
            gui_first=ps(args.gui_pid)
            assert gui_first is not None and gui_first['command']==expected_gui
            cwd_is(args.gui_pid,RUNTIME)
            record.update(source=str(source),source_hashes=plan['source_hashes'],settings_sha256=settings_pin,
                selected_Native_cli=pins['kicad_cli'],selected_gui_app=dict(path=str(gui_app),sha256=GUI_APP_SHA,bytes=GUI_APP_BYTES))
            polls=0;deadline=time.monotonic()+MAX_WAIT
            while time.monotonic()<deadline and polls<MAX_POLLS:
                polls+=1
                assert same(gui_first,ps(args.gui_pid)),'GUI identity changed'
                if (route/'result.json').exists():raise ValueError('Recovery finished before forced interval; timing not passed')
                incumbent=route/'incumbent/result.json'
                if incumbent.is_file():
                    raw,saved=bounded_json(incumbent)
                    assert saved['source']==str(source) and saved['source_hashes']==plan['source_hashes']
                    assert saved['tools']==prepared['tools'] and saved['accepted'] is True
                    assert saved['status']=='routing_accepted' and saved['invariants_unchanged'] is True
                    assert [saved['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
                    candidate=Path(saved['candidate'])
                    assert candidate==route/'incumbent/candidate'/source.name and digest(candidate)==saved['candidate_sha256']
                    for cli in observer.owned_paths(args.gui_pid):
                        if cli['executable']!=str((RUNTIME/'.venv/bin/python').resolve()):continue
                        cli_row=ps(cli['pid'])
                        if cli_row is None or cli_row['ppid']!=args.gui_pid or cli_row['command']!=expected_cli:continue
                        for child in observer.owned_paths(cli['pid']):
                            if child['executable']!=str(native_cli):continue
                            row=ps(child['pid'])
                            if row is None or row['ppid']!=cli['pid'] or row['command']!=expected_worker:continue
                            cwd_is(row['pid'],route)
                            assert cli in observer.owned_paths(args.gui_pid) and child in observer.owned_paths(cli['pid'])
                            assert same(gui_first,ps(args.gui_pid)) and same(cli_row,ps(cli['pid']))
                            assert same(row,ps(row['pid'])),'Worker identity changed before STOP'
                            assert not (route/'result.json').exists()
                            assert digest(incumbent)==hashlib.sha256(raw).hexdigest()
                            assert inventory(source.parent)==plan['source_hashes']
                            assert digest(workspace/'settings.json')==settings_pin
                            assert digest(native_cli)==pins['kicad_cli']['sha256']
                            worker_row=row
                            # Final same-birth/full-command/parent sample immediately before the only STOP.
                            assert same(row,ps(row['pid']))
                            os.kill(row['pid'],signal.SIGSTOP);stopped=True
                            hold_started=time.monotonic();hold_deadline=hold_started+HOLD_SECONDS
                            record.update(paused=True,paused_utc=utc(),worker=row,ancestor_chain=[row,cli_row,gui_first],
                                incumbent_receipt=str(incumbent),incumbent_sha256=hashlib.sha256(raw).hexdigest(),
                                incumbent_candidate=str(candidate),incumbent_candidate_sha256=saved['candidate_sha256'],
                                incumbent_accepted=True,polls=polls,discovery_wall_seconds=hold_started-started)
                            paused=ps(row['pid'])
                            assert same(row,paused) and 'T' in paused['state'],'Worker STOP not observed'
                            ready_record=dict(schema=1,ready=True,forced_window=True,workspace=str(workspace),
                                worker=row,ancestor_chain=record['ancestor_chain'],paused_state=paused['state'],
                                incumbent_sha256=record['incumbent_sha256'],incumbent_accepted=True,
                                helper_sha256=record['helper_sha256'],runtime_manifest_sha256=MANIFEST,
                                ready_utc=utc(),hold_seconds=HOLD_SECONDS,actual_GUI_Cancel_still_required=True,
                                cancellation_qualified=False)
                            with ready.open('xb') as stream:write_receipt(stream,ready_record)
                            record['ready_written']=True;record['ready_sha256']=digest(ready)
                            print(json.dumps(dict(ready=True,receipt=str(ready),worker_pid=row['pid'],hold_seconds=HOLD_SECONDS)),flush=True)
                            while time.monotonic()<hold_deadline:
                                current=ps(row['pid'])
                                if current is None:
                                    record.update(known_worker_exit_during_hold=True,worker_exit_observed_utc=utc());break
                                assert same(row,current),'Worker identity changed during hold'
                                time.sleep(min(.25,max(0,hold_deadline-time.monotonic())))
                            record['hold_wall_seconds']=time.monotonic()-hold_started
                            break
                        if stopped:break
                if stopped:break
                time.sleep(.25)
            assert stopped and record['ready_written'],'No required forced interval within finite discovery bounds'
            assert record['known_worker_exit_during_hold'],'Worker exit not observed during forced hold; no Cancel qualification'
        except BaseException as error:
            record['error']=type(error).__name__+': '+str(error)
        finally:
            if stopped:
                try:
                    # One bounded known-PID check; reparenting does not prevent safely resuming
                    # the same birth/full command. Never resume a replacement identity.
                    current=ps(worker_row['pid'])
                    if current is None:record['worker_gone_at_cleanup']=True
                    else:
                        assert all(current[k]==worker_row[k] for k in ('pid','start_time','command')),'Resume refused: worker identity changed'
                        os.kill(worker_row['pid'],signal.SIGCONT);record['resumed']=True
                except ProcessLookupError:record['worker_gone_at_cleanup']=True
                except BaseException as error:record['resume_error']=type(error).__name__+': '+str(error)
            try:
                bind_prepared()
                if inventory is not None:
                    assert inventory(source.parent)==plan['source_hashes']
                    assert digest(workspace/'settings.json')==settings_pin
                assert digest(SHARED)==SHARED_SHA and digest(BIND_TEMPLATE)==BIND_SHA
                assert digest(RUNTIME/'toolchain.lock.json')==LOCK_SHA
                if 'native_cli' in locals():
                    assert digest(native_cli)==pins['kicad_cli']['sha256']
                    check_gui_app(gui_app)
                assert digest(Path(__file__))==record['helper_sha256']
            except BaseException as error:record['freshness_error']=type(error).__name__+': '+str(error)
            record['control_observation_complete']=bool(record['ready_written'] and record['known_worker_exit_during_hold']
                and not any(k in record for k in ('error','resume_error','freshness_error')))
            record['wall_seconds']=time.monotonic()-started
            write_receipt(final_stream,record)
    print(json.dumps(dict(receipt=str(final),control_observation_complete=record['control_observation_complete'],
        cancellation_qualified=False)),flush=True)
    return 0 if record['control_observation_complete'] else 2


if __name__=='__main__':raise SystemExit(main())
