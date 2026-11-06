"""Prepare or explicitly execute one copy-only Native placement feasibility probe.

Default action is preparation, with no Native invocation. Execution requires an
explicit flag and the reviewed protocol digest. Existing FloorJob, PRL, process,
snapshot, DRC readers and publication helpers provide the operational boundary.
"""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import resource
import shlex
import signal
import stat
import sys
import time

ENTRY = time.monotonic()
ENTRY_PARENT_CPU = time.process_time()
ENTRY_CHILD_CPU = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
def cpu():return sum(v.ru_utime + v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SEED = '.runs/runtime074 fresh install 001/.runs/gui-session105/ordinary-project/owned1007-transport.kicad_pcb'
SEED_MANIFEST = '.runs/runtime074 fresh install 001/.runs/gui-session105/prepared-state.json'


def code_pins():
    paths = list(HERE.glob('*.py'))
    search = ROOT / 'experiments/constrained_placement_v1'
    paths += list(search.rglob('*.py')) + [search / 'upstream.json', search / 'vendor/LICENSE']
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def context(runtime):
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(runtime), str(ROOT)]
    from autorouter import config as c, pipeline as p, floor_route as f, gui, handoff as h, placement_clearance as pc
    if c.ROOT != runtime or c.NATIVE_VERSION != '10.0.7':
        raise ValueError('Installed 10.0.7 runtime must precede source experiment imports')
    return c, p, f, gui, h, pc


def prepare(runtime, protocol):
    c, p, f, gui, h, pc = context(runtime)
    from experiments.placement_native_proposal_v1 import contract
    from scripts.backup import require_headroom
    source = h.real_path(ROOT / SEED)
    saved = f.read_json(ROOT / SEED_MANIFEST)['roles']['ordinary']
    assert saved['source'] == str(source) and gui.source_inventory(source) == saved['source_hashes']
    raw = pc.read_bytes(source, contract.MAX_BYTES)
    derived, derivation = contract.derive_unrouted(raw)
    geometry = contract.inspect_board(derived)
    contract.facts_from_observation(geometry)  # Static feasibility only, not Native facts.
    assert len(derivation['removed_routes']) == 4
    record = dict(schema=1, kind='placement-native-proposal-feasibility-v1',
        readiness='prepared_for_lead_review_unexecuted', Native_executed=False, accepted=False,
        runtime=str(runtime.relative_to(ROOT)), runtime_manifest_sha256=p.sha(runtime / 'runtime-distribution.json'),
        seed=SEED, seed_manifest=SEED_MANIFEST, seed_manifest_sha256=p.sha(ROOT / SEED_MANIFEST),
        source_hashes=saved['source_hashes'], derivation=derivation,
        selected_footprints=list(contract.SELECTED), allowed_region_nm=list(contract.REGION_NM),
        search=dict(seed=7, steps=160, alternatives=1, seconds=2),
        total_wall_and_cpu_seconds=120, worker_wall_and_cpu_seconds=110,
        peak_temporary_bytes=512 * 1024**2, output_bytes=512 * 1024**2,
        process_group_rss_bytes=2 * 1024**3, rss_enforcement='shared process-group polling, not an OS quota',
        code_sha256=code_pins(), wrapper_sha256=p.sha(c.PCBNEW.with_name('pcbnew.py')),
        source_geometry_only=dict(footprints=len(geometry['footprints']),
            pads=sum(len(r['pads']) for r in geometry['footprints']), zones=len(geometry['zones']),
            outline=geometry['outline'], Native_observation=False),
        space_plan=require_headroom(ROOT,512 * 1024**2,'one Native placement feasibility probe'),
        limitations=['Translation only; front, zero rotation, symmetric rectangular courtyard, centred circular PTH pads.',
            'One rectangular outline, no cutouts/keepouts; preserved zones must be outside selected movement region.',
            'Strict Native save comparison permits only selected XY and derived fill. Serializer normalization is a retained failure.',
            'No routing, application, Native release, GUI or human review claim; actual Native APIs remain unqualified until lead execution.'])
    assert protocol.parent == HERE and not protocol.is_symlink()
    p.save_json(protocol, record)
    command = [str(runtime / '.venv/bin/python'), '-B', str(HERE / 'driver.py'), '--runtime', str(runtime),
               '--protocol', str(protocol), '--protocol-sha256', p.sha(protocol),
               '--output', str(ROOT / '.runs/placement-native-proposal-v1-001'), '--execute-native']
    print(json.dumps(dict(readiness=record['readiness'], protocol_sha256=p.sha(protocol),
                         execute_command=shlex.join(command), Native_executed=False)))


def read_protocol(args, runtime, p, f, gui):
    protocol = Path(args.protocol).resolve()
    assert p.sha(protocol) == args.protocol_sha256
    spec = f.read_json(protocol)
    assert spec['schema'] == 1 and spec['kind'] == 'placement-native-proposal-feasibility-v1'
    assert spec['runtime'] == str(runtime.relative_to(ROOT)) and spec['seed'] == SEED
    assert spec['source_hashes'] == gui.source_inventory(ROOT / SEED)
    assert spec['code_sha256'] == code_pins()
    assert spec['runtime_manifest_sha256'] == p.sha(runtime / 'runtime-distribution.json')
    assert spec['seed_manifest_sha256'] == p.sha(ROOT / SEED_MANIFEST)
    assert spec['total_wall_and_cpu_seconds'] == 120 and spec['worker_wall_and_cpu_seconds'] == 110
    assert spec['output_bytes'] == spec['peak_temporary_bytes'] == 512 * 1024**2
    assert spec['process_group_rss_bytes'] == 2 * 1024**3
    assert spec['search'] == dict(seed=7, steps=160, alternatives=1, seconds=2)
    return spec


def placement_findings(native, p):
    assert native['blocking'] == native['exclusions'] == 0
    for row in native['findings']:
        assert not row.get('excluded', False) and row['severity'] != 'exclusion'
        assert row['type'] in p.KNOWN_CHECKS | {'padstack_invalid'}
        if row['type'] == 'unconnected_items':
            continue  # Preserved unrouted demand, explicitly not route acceptance.
        assert row['severity'] != 'error'
        assert row['type'] not in p.CRITICAL_FINDINGS, 'Critical Native finding remains'
    return sorted(json.dumps(row,sort_keys=True,separators=(',', ':'))
                  for row in native['findings'] if row['type'] != 'unconnected_items')


def runtime_unchanged(runtime, wrapper, spec, recorded_tools, p):
    """Recheck actual runtime/tool material after the Native worker has exited."""
    paths = (runtime / 'runtime-distribution.json', wrapper)
    expected = (spec['runtime_manifest_sha256'], spec['wrapper_sha256'])
    before = tuple(p.sha(path) for path in paths)
    tools = p.tool_manifest()
    after = tuple(p.sha(path) for path in paths)
    return before == after == expected and tools == recorded_tools


def worker(args, runtime):
    c, p, f, gui, h, pc = context(runtime)
    from autorouter import sexpr as sx
    from experiments.placement_native_proposal_v1 import contract
    from experiments.constrained_placement_v1 import prototype, constraints
    spec = read_protocol(args, runtime, p, f, gui)
    assert spec['selected_footprints'] == list(contract.SELECTED) and spec['allowed_region_nm'] == list(contract.REGION_NM)
    out = h.real_path(args.output); source = h.real_path(ROOT / SEED)
    def remaining():return min(110 - (time.monotonic() - ENTRY), 110 - (cpu() - CPU0))
    job = f.FloorJob(out / 'work', 110, remaining, protect_local_settings=True)
    original_tools = p.tool_manifest(); code = spec['code_sha256']
    record = dict(schema=1, kind=spec['kind'], status='failed', accepted=False, routing_accepted=False,
                  placement_proposal_validated=False, production_admitted=False, human_approval=False,
                  source=str(source), source_hashes=spec['source_hashes'], tools=original_tools,
                  budget_seconds=110, cpu_budget_seconds=110, protocol_sha256=args.protocol_sha256,
                  steps=job.steps, external_exit_required=True, original_mutated=False,
                  whole_project_drc_clean=False, routing_performed=False)
    snapshot = job.out / 'snapshot' / source.name; task = job.out / 'task' / source.name
    candidate = job.out / 'candidate' / source.name
    final_drc_before = None
    def fresh():
        h.owned_destination(job._local_settings_owner)
        assert remaining() > 0 and code_pins() == code
        assert gui.source_inventory(source) == spec['source_hashes']
        assert p.tool_manifest() == original_tools and p.sha(runtime / 'runtime-distribution.json') == spec['runtime_manifest_sha256']
        assert p.sha(Path(args.protocol)) == args.protocol_sha256
        if record['placement_proposal_validated']:
            assert record['status'] == 'placement_proposal_validated'
            assert gui.source_inventory(snapshot) == spec['source_hashes']
            assert gui.source_inventory(task) == record['task_hashes']
            assert gui.source_inventory(candidate) == record['candidate_hashes']
            assert p.sha(job.out/'proposal.json') == record['proposal_sha256']
            assert p.sha(job.out/'final-capture-observation.json') == record['observed_candidate_sha256']
            # Replay the retained full-SCH/PRL/process evidence after later SWIG
            # reads and during publication; no cached cleanliness Boolean.
            replay=f.check_drc_stage(job.out,record,'final-drc',candidate,
                job.out/'final-drc-input'/candidate.name,False,final_drc_before,schematic_parity=True)
            assert f.canonical(replay) == f.canonical(record['final_native'])
    def native_request(name, board, moves=None):
        fresh()
        request = dict(schema=1, mode='capture' if moves is None else 'translate', board=str(board),
            source_hashes=gui.source_inventory(board), candidate=None if moves is None else str(candidate),
            moves_nm={} if moves is None else moves, job=str(job.out),
            job_identity=list(job._local_settings_owner['directory_identity']),
            runtime_manifest_sha256=spec['runtime_manifest_sha256'], wrapper_sha256=spec['wrapper_sha256'], code_sha256=code)
        path=job.out/(name+'-request.json'); output=job.out/(name+'-observation.json')
        p.save_json(path,request)
        argv=[str(c.PYTHON),str(HERE/'worker.py'),'--runtime',str(runtime),'--request',str(path),'--output',str(output)]
        job.step(name,argv)
        f.process_check(job.out,record,name,[*f.SANDBOX,*argv])
        value=f.read_json(output)
        assert value['actual_native_observation'] is True and value['source_hashes']==request['source_hashes']
        assert value['request_sha256']==p.sha(path) and value['accepted'] is False
        fresh();return value
    def drc(name, board, saved=False):
        fresh(); before=gui.source_inventory(board)
        native=job.drc(name,board,save=saved,schematic_parity=True)
        input_path=board if saved else job.out/(name+'-input')/board.name
        actual=f.check_drc_stage(job.out,record,name,board,input_path,saved,before,schematic_parity=True)
        assert f.canonical(native)==f.canonical(actual)
        fresh();return native
    def account():
        record.update(wall_seconds=time.monotonic()-ENTRY,
            **p.sequential_cpu_components(time.process_time()-ENTRY_PARENT_CPU,
                f.child_cpu()-ENTRY_CHILD_CPU,job.steps))
        if record['status'] != 'placement_proposal_validated':
            record['placement_proposal_validated'] = False
        if remaining()<=0 or record['total_cpu_seconds']>110:
            record.update(status='budget_exhausted',placement_proposal_validated=False)
    try:
        fresh();pc.copy_project(source.parent,snapshot.parent);pc.copy_project(snapshot.parent,task.parent)
        assert gui.source_inventory(snapshot)==gui.source_inventory(task)==spec['source_hashes']
        raw=pc.read_bytes(snapshot,contract.MAX_BYTES);derived,derivation=contract.derive_unrouted(raw)
        assert derivation==spec['derivation'];task.write_bytes(derived)
        record['derivation']=derivation;record['task_hashes']=gui.source_inventory(task)
        source_native=drc('source-drc',task);source_findings=placement_findings(source_native,p)
        record['source_native']=source_native
        observed=native_request('capture',task)
        assert observed['status']=='observed' and observed['observation']==contract.inspect_board(derived)
        facts=contract.facts_from_observation(observed['observation'])
        search=prototype.propose(facts,**spec['search']);record['search']=search
        assert search['status']=='proposals_ready' and search['alternatives']
        selected,moves=contract.quantized_translation(facts,search['alternatives'][0]['candidate'])
        assert selected!=constraints.original_alternative(facts)
        p.save_json(job.out/'proposal.json',dict(schema=1,source=str(task),source_hashes=record['task_hashes'],
            source_observation_sha256=p.sha(job.out/'capture-observation.json'),candidate=selected,moves_nm=moves,
            quantization='nearest 1 nm; independently revalidated',accepted=False,routing_accepted=False,
            execution_authorized=False,human_approval=False))
        pc.copy_project(task.parent,candidate.parent)
        translated=native_request('translate',task,moves)
        assert translated['status']=='translated_copy'
        contract.check_translation(derived,pc.read_bytes(candidate),moves)
        refill=drc('refill-drc',candidate,True)
        record['refill_native']=refill
        record['immutable_check']=contract.check_translation(derived,pc.read_bytes(candidate),moves)
        final_drc_before=gui.source_inventory(candidate)
        final=drc('final-drc',candidate)
        assert placement_findings(final,p)==source_findings and final['ignored_checks']==source_native['ignored_checks']
        final_observed=native_request('final-capture',candidate)
        final_raw=pc.read_bytes(candidate,contract.MAX_BYTES)
        assert final_observed['observation']==contract.inspect_board(final_raw)
        contract.check_translation(derived,final_raw,moves)
        constraints.validate_alternative(facts,selected)
        expected=dict(record['task_hashes']);expected[source.name]=p.sha(candidate)
        assert gui.source_inventory(candidate)==expected and gui.source_inventory(task)==record['task_hashes']
        assert gui.source_inventory(snapshot)==spec['source_hashes']
        record.update(status='placement_proposal_validated',placement_proposal_validated=True,
            candidate=str(candidate),candidate_sha256=p.sha(candidate),candidate_hashes=expected,
            final_native=final,proposal_sha256=p.sha(job.out/'proposal.json'),
            observed_candidate_sha256=p.sha(job.out/'final-capture-observation.json'),
            explicit_review_required=True,warning_records_unchanged=True)
        fresh();account();p.check_resource_accounting(record)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',
                      placement_proposal_validated=False,reason=type(exc).__name__+': '+str(exc))
        account()
    return f.publish(job.out,record,fresh,account,remaining,owned=lambda:h.owned_destination(job._local_settings_owner),final_check=fresh)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime',required=True);ap.add_argument('--protocol',required=True)
    ap.add_argument('--protocol-sha256');ap.add_argument('--output')
    ap.add_argument('--execute-native',action='store_true');ap.add_argument('--worker',action='store_true')
    args=ap.parse_args(argv);runtime=Path(args.runtime).resolve();protocol=Path(args.protocol).resolve()
    if not args.execute_native:
        assert not args.worker
        prepare(runtime,protocol);return 0
    c,p,f,gui,h,pc=context(runtime)
    assert Path(sys.prefix).resolve()==runtime/'.venv' and args.output and args.protocol_sha256
    if args.worker:
        value=worker(args,runtime)
        return 0 if value['placement_proposal_validated'] else 2
    from scripts.backup import require_headroom
    from autorouter.runner import run
    spec=read_protocol(args,runtime,p,f,gui)
    out=h.real_path(args.output,existing=False)
    assert out.parent==ROOT/'.runs' and not out.exists()
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lane:
        st=os.fstat(lane.fileno());assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        space=require_headroom(ROOT,512*1024**2,'one Native placement feasibility probe')
        out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out)
        command=[str(runtime/'.venv/bin/python'),'-B',str(HERE/'driver.py'),'--runtime',str(runtime),
            '--protocol',str(protocol),'--protocol-sha256',args.protocol_sha256,'--output',str(out),'--execute-native','--worker']
        process=run(command,cwd=out,env=gui.child_environment(),log=out/'command.log',timeout=max(.001,115-(time.monotonic()-ENTRY)),
            max_log_bytes=512*1024,max_group_rss_bytes=spec['process_group_rss_bytes'],max_workdir_bytes=512*1024**2)
        p.save_json(out/'process.json',process)
        child=out/'work/result.json';value=f.read_json(child) if child.is_file() else None
        stable=code_pins()==spec['code_sha256'] and p.sha(protocol)==args.protocol_sha256 and gui.source_inventory(ROOT/SEED)==spec['source_hashes']
        if value and value.get('placement_proposal_validated'):
            p.check_resource_accounting(value)
            stable=bool(stable and value['status']=='placement_proposal_validated'
                and value['accepted'] is False and value['routing_accepted'] is False
                and gui.source_inventory(Path(value['candidate']))==value['candidate_hashes']
                and runtime_unchanged(runtime,c.PCBNEW.with_name('pcbnew.py'),spec,value['tools'],p))
        child_sha=p.sha(child) if value else None
        wall,total_cpu=time.monotonic()-ENTRY,cpu()-CPU0
        qualified=bool(stable and value and value['placement_proposal_validated'] and value['external_exit_required']
            and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
            and process['log_truncated'] is False and max(wall,total_cpu)+1<=120)
        record=dict(schema=1,placement_proposal_qualified=qualified,accepted=False,routing_accepted=False,
            process=process,complete_worker_exit_wall_seconds=wall,parent_plus_waited_child_cpu_seconds=total_cpu,
            publication_allowance_seconds=1,total_limit_seconds=120,controller_exit_not_measured=True,
            child_receipt_sha256=child_sha,source_unchanged=stable,space_plan=space,
            protocol_sha256=args.protocol_sha256,actual_GUI=False,model_calls=0,live_application=False)
        h.owned_destination(owner);p.save_json(out/'execution.json',record)
        print(json.dumps({k:v for k,v in record.items() if k!='process'}))
        return 0 if qualified else 2


if __name__=='__main__':
    def interrupted(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    raise SystemExit(main())
