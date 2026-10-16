"""One bounded contact-locality prerequisite; no routing or admission.

SPDX-License-Identifier: GPL-3.0-or-later
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime + x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
import argparse, fcntl, json, os, signal, stat, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f, handoff as h, sexpr as sx, placement_clearance as io
from experiments.hfe_original_native_v1.driver import BoundJob, clean, material
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.net_tie_contact_v1 import fixture, observer

LEAD = ROOT / '.runs/net-tie-support-feasibility-001/source-hashes.json'
CASES = ('original', *fixture.CASES)


def original_packet():
    lead = f.read_json(LEAD); source = ROOT / lead['project_root']
    files = io.inventory(source, contents=True, max_bytes=2*1024**2, max_files=6, max_entries=12)
    expected = {name: row['sha256'] for name, row in lead['files'].items()}
    if {name: observer.digest(raw) for name, raw in files.items()} != expected:
        raise p.Rejected('retained complete six-file source packet differs')
    return files


def board_path(folder, case):
    return folder / ('Hardware/SparkFun_VEML7700.kicad_pcb' if case == 'original' else fixture.STEM+'.kicad_pcb')


def replay_candidate(job, original, candidate, before, protected, digest, native):
    p.verify_candidate_files(candidate,before,digest)
    tree=sx.read(candidate)
    if p.immutable(tree)!=p.immutable(original) or any(route not in p.routes(tree) for route in protected):
        raise p.Rejected('retained candidate design/protected routing changed')
    refill=job.out/'refill'/candidate.name
    f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',refill,refill,True,before)
    expected={**before,candidate.name:digest}
    observed=f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,
        job.out/'final-drc-input'/candidate.name,False,expected,schematic_parity=True)
    if observed!=native: raise p.Rejected('shared retained final-stage readback differs')


def replay_observation(job, command, process, log_sha256, output, observed_sha256, dsn_sha256):
    f.process_check(job.out,{'steps':job.steps},'contact-observation',[*f.SANDBOX,*command])
    log=job.out/'contact-observation.log'
    raw=io.read_bytes(log,256*1024)
    if process['log_truncated'] is not False or len(raw)!=process['log_bytes'] or p.sha(log)!=log_sha256:
        raise p.Rejected('retained contact log changed or truncated')
    if p.sha(output/'observation.json')!=observed_sha256 or p.sha(output/'observed.dsn')!=dsn_sha256:
        raise p.Rejected('retained same-load observation/DSN changed')
    proof=f.read_json(output/'observation.json')
    if proof['export']['dsn_sha256']!=dsn_sha256 or proof['dsn_membership']['dsn_sha256']!=dsn_sha256:
        raise p.Rejected('DSN bytes differ from worker export/membership bindings')


def clear_unqualified_controls(record):
    if record['status']!='completed':
        record['passed']=False
        for item in record['cases'].values(): item['control_passed']=False


def prepare(folder, head):
    clean(head); folder.mkdir(); tools = p.tool_manifest()
    copy_bytes(original_packet(), folder/'original')
    for case in fixture.CASES: copy_bytes(fixture.files(case), folder/case)
    refusals = {}
    for case in CASES:
        board = board_path(folder/case, case)
        observer.source_context(io.read_bytes(board, observer.MAX_SOURCE))
        try: p.preflight(board)
        except p.Rejected as exc: refusals[case] = str(exc)
        else: raise p.Rejected('unchanged production net-tie refusal required')
        if 'net ties not qualified' not in refusals[case]:
            raise p.Rejected('different production refusal; inspect before Native')
    names = {str(path.relative_to(ROOT)) for path in Path(__file__).parent.iterdir() if path.is_file()}
    names.update(('experiments/hfe_original_native_v1/driver.py',
                  'experiments/placement_handoff_native_v1/driver.py',
                  'experiments/native_schematic_toolchain_v1/fixture.py',
                  'experiments/pic_custom_observer_v1/mapping.py'))
    plan = dict(schema=1, git_head=head, tools=tools, accepted=False,
        code_sha256={name:p.sha(ROOT/name) for name in sorted(names)},
        source_hashes={case:p.tree_hash(folder/case) for case in CASES},
        source_lead_sha256=p.sha(LEAD), static_refusals=refusals,
        limits=dict(whole_wall_full_cpu_seconds=120, worker_seconds=110,
            outer_scratch_bytes=20*1024**2, inner_existing_job_scratch_bytes=128*1024**2,
            polled_group_rss_bytes=2*1024**3, per_step_logs_bytes=256*1024),
        expected_negative_pairs=[sorted(pair) for pair in fixture.NEGATIVE_ALLOWED_ITEM_UUID_PAIRS],
        scope='Exact unchanged original observation and two owned Native controls. No engine/SES/production admission. Same-load groups and distinct DSN terminals; Native rectangular contact is not DSN bridge fidelity or clearance. Each case executes once; failed case retained, no retry.',
        preparation_costs=dict(wall_seconds=time.monotonic()-START, full_cpu_seconds=cpu()-CPU0))
    p.save_json(folder/'protocol.json', plan)
    print(json.dumps(dict(prepared=True, native_executed=False, protocol_sha256=p.sha(folder/'protocol.json'))))


def execute(folder, output):
    plan = f.read_json(folder/'protocol.json'); pin = p.sha(folder/'protocol.json')
    def current():
        clean(plan['git_head'])
        if p.tool_manifest()!=plan['tools'] or p.sha(folder/'protocol.json')!=pin or p.sha(LEAD)!=plan['source_lead_sha256']:
            raise p.Rejected('frozen tools/source/protocol differ')
        if any(p.sha(ROOT/name)!=digest for name,digest in plan['code_sha256'].items()): raise p.Rejected('diagnostic code changed')
        if any(p.tree_hash(folder/case)!=digest for case,digest in plan['source_hashes'].items()): raise p.Rejected('original control input changed')
        original_packet()
    current(); output.mkdir(); owner={}; h.capture_destination(owner,output)
    prep=plan['preparation_costs']
    def remaining():
        return min(110-(time.monotonic()-START), 110-(cpu()-CPU0),
            118-prep['wall_seconds']-(time.monotonic()-START),118-prep['full_cpu_seconds']-(cpu()-CPU0))
    record=dict(schema=1,accepted=False,passed=False,status='failed',qualified=False,
        routing_accepted=False,production_admitted=False,engine_executed=False,
        protocol_sha256=pin,tools=plan['tools'],cases={},scope=plan['scope'])
    candidates=[]; observations=[]
    def interrupted(signum, frame): raise KeyboardInterrupt('diagnostic termination requested')
    for sig in (signal.SIGINT,signal.SIGTERM): signal.signal(sig,interrupted)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1: raise p.Rejected('ordinary shared Native lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            for case in CASES:
                source=board_path(folder/case,case); out=output/case; out.mkdir()
                candidate=out/'candidate'/source.name
                copy_bytes(io.inventory(source.parent,contents=True,max_bytes=2*1024**2,max_files=8,max_entries=16),candidate.parent)
                before=p.tree_hash(source.parent); original=sx.read(source)
                protected=p.routes(original)
                job=BoundJob(out/'job',min(110,remaining()),remaining,protect_local_settings=True)
                item=dict(observation_complete=False,control_passed=False,steps=job.steps)
                record['cases'][case]=item
                try:
                    digest,native=p.validate_candidate(job,original,candidate,before,protected)
                    context=(job,original,candidate,before,protected,digest,native)
                    replay_candidate(*context); candidates.append(context)
                    item.update(native=native,candidate_sha256=digest,original_design_exact=True)
                    command=[str(c.PYTHON),str(Path(__file__).with_name('worker.py')),str(source),str(out/'observed.dsn'),str(out/'observation.json')]
                    process=job.step('contact-observation',command)
                    log_digest=p.sha(job.out/'contact-observation.log')
                    observation=f.read_json(out/'observation.json')
                    if (observation['source_sha256']!=p.sha(source)
                            or observation['before_export']!=observation['after_export']): raise p.Rejected('same-load observation binding differs')
                    item.update(observation_complete=True,observation_sha256=p.sha(out/'observation.json'))
                    observed=(job,command,process,log_digest,out,p.sha(out/'observation.json'),p.sha(out/'observed.dsn'))
                    replay_observation(*observed); observations.append(observed)
                    if case=='positive':
                        if not p.native_accepted(native): raise p.Rejected('owned positive Native checks refused')
                        warnings=[row for row in native['findings'] if row.get('severity')=='warning']
                        component_ids=set(fixture.FOOTPRINT_UUIDS.values())
                        if any(row['type']!='footprint_symbol_field_mismatch'
                                or row['description']!="Field 'Datasheet' differs (PCB: '~', Schematic: '')"
                                or len(row['items'])!=1 or row['items'][0]['uuid'] not in component_ids
                                for row in warnings): raise p.Rejected('unexpected owned positive warning')
                    elif case=='outside_short':
                        errors=[row for row in native['findings'] if row.get('severity')=='error']
                        pairs=plan['expected_negative_pairs']
                        if native['opens']!=0 or native['exclusions']!=0 or not errors: raise p.Rejected('outside short not detected')
                        for row in errors:
                            ids=sorted(item['uuid'] for item in row['items'])
                            if row['type'] not in {'clearance','shorting_items'} or ids not in pairs:
                                raise p.Rejected('unexpected outside-short error type/item UUID set')
                        positive=record['cases']['positive'].get('native')
                        if positive is None or [row for row in native['findings'] if row.get('severity')!='error']!=[
                                row for row in positive['findings'] if row.get('severity')!='error']:
                            raise p.Rejected('negative warnings/parity changed independently of the outside short')
                    item['control_passed']=True
                except Exception as exc:
                    item.update(reason=type(exc).__name__+': '+str(exc))
                if p.tree_hash(source.parent)!=before or p.tree_hash(folder/case)!=plan['source_hashes'][case]: raise p.Rejected('immutable source changed')
            record['passed']=all(record['cases'][case]['control_passed'] for case in CASES)
            record['status']='completed' if record['passed'] else 'observed_unqualified'
        except (Exception,KeyboardInterrupt) as exc:
            record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc))
        witness=material(output); record['completed_evidence']=witness
        def stable():
            h.owned_destination(owner); current()
            for context in candidates: replay_candidate(*context)
            for observation in observations: replay_observation(*observation)
            if material(output)!=witness: raise p.Rejected('completed diagnostic evidence changed')
        def account():
            record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,preparation_costs=prep)
            if remaining()<=0: record.update(status='budget_exceeded',passed=False)
            clear_unqualified_controls(record)
        f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    result=f.read_json(output/'result.json')
    print(json.dumps({key:result.get(key) for key in ('passed','status','reason','wall_seconds','full_cpu_seconds')}))
    return 0 if result.get('status')=='completed' and result.get('passed') is True else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['prepare','run'])
    parser.add_argument('--preparation',type=Path,required=True); parser.add_argument('--head'); parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.mode=='prepare':
        if args.head is None: parser.error('--head required')
        prepare(args.preparation.absolute(),args.head)
    else:
        if args.output is None: parser.error('--output required')
        raise SystemExit(execute(args.preparation.absolute(),args.output.absolute()))
