"""Unexecuted lead-only HFE Native1007 scalar class observation.

SPDX-License-Identifier: GPL-3.0-or-later
One unchanged native.py netclasses worker; no save, DSN, DRC or class waiver.
The enclosing invocation includes freezing, worker and final publication costs.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(r.ru_utime + r.ru_stime for r in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse, fcntl, math, os, signal, stat, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, handoff as h, sexpr as sx
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as original
from experiments.placement_handoff_native_v1.driver import copy_bytes
BASE = ROOT / '.runs/hfe-class-observation-001'
CHILD = BASE / 'worker'
RETAINED = ROOT / '.runs/hfe-parity-probe-execution-001/probe'
INPUTS = {'result.json': RETAINED / 'result.json', 'protocol.json': RETAINED / 'protocol.json',
          'fields.net': RETAINED / 'job/parity-probe-fields.net'}
LIMIT = 20 * 1024**2
LIMITS = dict(wall_full_cpu_seconds=30, worker_seconds=25, aggregate_bytes=LIMIT,
              group_rss_bytes=2 * 1024**3, log_bytes=256 * 1024, finalization_reserve_seconds=2)
SCOPE = ('Original HFE scalar class observation against retained 52 terminal partitions. '
         'Opaque class encodings and parameter parents only; membership, inheritance, '
         'unsupported constraints, schematic parity and production support remain unqualified.')

def material(path):
    io.inventory(BASE, max_bytes=LIMIT, max_files=2048, max_entries=4096)
    return original.material(path)

def context(plan, pin):
    original.clean(plan['git_head']); original.source()
    nt = p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
    if (p.sha(BASE / 'protocol.json') != pin or f.read_json(BASE / 'protocol.json') != plan
            or p.tool_manifest(native_toolchain=nt) != plan['tools']
            or p.sha(original.ACQUISITION) != plan['acquisition_sha256']
            or any(p.sha(ROOT / n) != value for n, value in plan['code_sha256'].items())
            or any(p.sha(BASE / 'code' / n) != value for n, value in plan['code_sha256'].items())
            or any(p.sha(path) != plan['retained_sha256'][n] for n, path in INPUTS.items())
            or any(p.sha(BASE / 'retained' / n) != value for n, value in plan['retained_sha256'].items())
            or p.tree_hash(BASE / 'source') != original.SOURCE_PINS):
        raise p.Rejected('frozen HEAD/tools/helpers/source/retained partition evidence changed')
    material(BASE)
    return nt

def comparison(native):
    receipt = f.read_json(BASE / 'retained/result.json')
    protocol = f.read_json(BASE / 'retained/protocol.json')
    if (receipt.get('passed') is not True or receipt.get('status') != 'completed'
            or receipt.get('observation_complete') is not True or receipt['source_sha256'] != original.SOURCE_PINS
            or receipt['netlist_sha256'] != p.sha(BASE / 'retained/fields.net')
            or receipt['protocol_sha256'] != p.sha(BASE / 'retained/protocol.json')
            or protocol['source_sha256'] != original.SOURCE_PINS):
        raise p.Rejected('retained successful source-bound partition/netlist evidence differs')
    def partitions(rows):
        result = {}; names = set(); terminals = set()
        for row in rows:
            key = tuple(sorted(tuple(v) for v in row['terminals']))
            if (not key or len(set(key)) != len(key) or any(len(v) != 2 or any(type(x) is not str or not x for x in v) for v in key)
                    or set(key) & terminals or key in result or row['net'] in names):
                raise p.Rejected('retained partitions are not unique/disjoint')
            result[key] = row['net']; names.add(row['net']); terminals.update(key)
        if len(result) != 52: raise p.Rejected('all52 retained partitions required')
        return result
    retained = receipt['terminal_comparison']
    pcb = partitions(retained['pcb_positive_partitions']); sch = partitions(retained['schematic_positive_partitions'])
    if set(pcb) != set(sch): raise p.Rejected('retained terminal partitions are not bijective')
    nets = sx.one(sx.parse(io.read_bytes(BASE / 'retained/fields.net').decode()), 'nets')
    classes = {}
    for net in sx.children(nets, 'net'):
        name = sx.unquote(sx.one(net, 'name')[1]); cls = sx.one(net, 'class')
        if name in classes or cls is None or len(cls) != 2 or type(cls[1]) is not str:
            raise p.Rejected('unique retained schematic class AST required')
        classes[name] = cls
    rows = native['nets']; observed = {row['name']: row for row in rows}
    if (len(rows) != 52 or len(observed) != 52 or set(observed) != set(pcb.values())
            or set(classes) != set(sch.values())): raise p.Rejected('complete52 Native/SCH class populations required')
    paired = []
    for terminals, pcbnet in sorted(pcb.items(), key=lambda item: item[1]):
        row = observed[pcbnet]; schnet = sch[terminals]
        dims = {'width_nm', 'clearance_nm', 'via_diameter_nm', 'via_drill_nm'}
        if (type(row['class']) is not str or not row['class'] or row['copper_pad_count'] != len(terminals)
                or any(type(row[k]) is not int or row[k] <= 0 for k in dims)
                or set(row['parameter_parents']) != dims): raise p.Rejected('complete native scalar dimensions/parents required')
        paired.append(dict(pcb_net=pcbnet, schematic_net=schnet, renamed=pcbnet != schnet,
            terminals=[list(v) for v in terminals], schematic_class_ast=classes[schnet],
            native_scalars=row, opaque_encoded_names_equal=row['class'] == sx.unquote(classes[schnet][1])))
    renamed = [r for r in paired if r['renamed']]
    if len(renamed) != 5: raise p.Rejected('retained five renamed partitions differ')
    return dict(partition_count=52, renamed_partitions=renamed, partitions=paired,
        native_default_with_different_schematic_encoding=[r for r in paired if r['native_scalars']['class'] == 'Default' and not r['opaque_encoded_names_equal']],
        exact_constituents_inferred=False, membership_qualified=False, inheritance_qualified=False,
        unsupported_constraints_remain_missing=True, routing_accepted=False, scope=SCOPE)

def readback(plan, record, nt):
    board = CHILD / 'job/input' / (original.STEM + '.kicad_pcb'); output = CHILD / 'job/pcb-classes.json'
    f.process_check(CHILD / 'job', record, 'pcb-classes',
        [*f.SANDBOX, *p.native_prefix(nt), 'netclasses', str(board), str(output)])
    native = f.read_json(output)
    if (native.get('schema') != 1 or native.get('native_version') != '10.0.7'
            or native.get('board_saved') is not False or native.get('source') != str(board)
            or native.get('board_sha256') != original.SOURCE_PINS[board.name]
            or native.get('project_sha256') != original.SOURCE_PINS[board.with_suffix('.kicad_pro').name]
            or p.tree_hash(board.parent) != original.SOURCE_PINS):
        raise p.Rejected('actual Native class worker/source binding differs')
    return comparison(native)

def worker(plan, pin, available):
    nt = context(plan, pin); CHILD.mkdir(); owner = {}; h.capture_destination(owner, CHILD)
    def left(): return min(available - 2 - (time.monotonic() - START), available - 2 - (cpu() - CPU0))
    record = dict(schema=1, status='failed', passed=False, observation_complete=False, accepted=False,
                  qualified=False, production_support_qualified=False, tools=plan['tools'], scope=SCOPE)
    job = original.BoundJob(CHILD / 'job', max(.001, left()), left, native_toolchain=nt, protect_local_settings=True)
    record['steps'] = job.steps
    try:
        copy_bytes(original.source(), job.out / 'input')
        job.native('pcb-classes', 'netclasses', job.out / 'input' / (original.STEM + '.kicad_pcb'), job.out / 'pcb-classes.json')
        record.update(comparison=readback(plan, record, nt), native_output_sha256=p.sha(job.out / 'pcb-classes.json'),
                      status='completed', passed=True, observation_complete=True)
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed', error=type(exc).__name__ + ': ' + str(exc))
    witness = material(CHILD); record['completed_evidence'] = witness
    def stable():
        h.owned_destination(owner); context(plan, pin)
        if material(CHILD) != witness: raise p.Rejected('completed scalar observation changed')
        if record['passed'] and (readback(plan, record, nt) != record['comparison'] or p.sha(job.out / 'pcb-classes.json') != record['native_output_sha256']):
            raise p.Rejected('late scalar observation differs')
        if material(CHILD) != witness: raise p.Rejected('material changed during final readback')
    def account():
        record.update(wall_seconds=time.monotonic() - START, full_cpu_seconds=cpu() - CPU0)
        if left() <= 0 and record['status'] != 'cancelled': record['status'] = 'budget_exceeded'
        if record['status'] != 'completed': record.update(passed=False, observation_complete=False)
    f.publish(CHILD, record, stable, account, left, owned=lambda: h.owned_destination(owner), final_check=stable)
    return 0 if record['passed'] and record['status'] == 'completed' else 2

def execute(head):
    original.clean(head); packet = original.source(); retained = {n: io.read_bytes(path) for n, path in INPUTS.items()}
    nt = p.ExperimentalNativeToolchain.from_record(f.read_json(INPUTS['protocol.json'])['native_toolchain']); tools = p.tool_manifest(native_toolchain=nt)
    names = set(tools['implementation_sha256']) | {str(Path(__file__).relative_to(ROOT)), 'toolchain.lock.json',
        'experiments/hfe_original_native_v1/driver.py', 'experiments/original_project_native_v1/driver.py',
        'experiments/placement_handoff_native_v1/driver.py', 'experiments/placement_production_controls_v1/driver.py'}
    h.real_path(BASE, existing=False); BASE.mkdir(); owner = {}; h.capture_destination(owner, BASE)
    copy_bytes(packet, BASE / 'source'); copy_bytes(retained, BASE / 'retained')
    copy_bytes({n: io.read_bytes(ROOT / n, 1024**2) for n in sorted(names)}, BASE / 'code')
    plan = dict(schema=1, git_head=head, tools=tools, native_toolchain=nt.record(), limits=LIMITS,
        code_sha256={n: p.sha(ROOT / n) for n in sorted(names)}, acquisition_sha256=p.sha(original.ACQUISITION),
        retained_sha256={n: p.sha(path) for n, path in INPUTS.items()}, source_sha256=original.SOURCE_PINS, scope=SCOPE)
    p.save_json(BASE / 'protocol.json', plan); pin = p.sha(BASE / 'protocol.json'); context(plan, pin)
    def left(): return min(28 - (time.monotonic() - START), 28 - (cpu() - CPU0))
    available = min(25, left())
    if available <= 2: raise p.Rejected('total30second budget exhausted before Native launch')
    process = run([*f.SANDBOX, str(ROOT / '.venv/bin/python'), '-B', str(Path(__file__)), '--source-head', head,
        '--worker', '--protocol-sha256', pin, '--available', str(available)], cwd=BASE, log=BASE / 'command.log',
        timeout=available, max_log_bytes=LIMITS['log_bytes'], max_workdir_bytes=LIMIT, max_group_rss_bytes=LIMITS['group_rss_bytes'])
    path = CHILD / 'result.json'; child = f.read_json(path) if path.is_file() else None; childpin = p.sha(path) if child else None
    bound = bool(child and material(CHILD) == child.get('completed_evidence'))
    passed = bool(bound and child.get('passed') is True and child.get('status') == 'completed'
        and child.get('observation_complete') is True and child.get('accepted') is False and child.get('qualified') is False
        and process['status'] == 'success' and process['exit_code'] == 0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
    witness = material(BASE)
    record = dict(schema=1, status='completed' if passed else 'failed', passed=passed, observation_complete=passed,
        accepted=False, qualified=False, production_support_qualified=False, child=child, child_receipt_sha256=childpin,
        completed_evidence=witness, process=process, protocol_sha256=pin, tools=tools, limits=LIMITS, scope=SCOPE)
    if process['status'] == 'cancelled' or child and child.get('status') == 'cancelled': record['status'] = 'cancelled'
    def stable():
        h.owned_destination(owner); context(plan, pin)
        if material(BASE) != witness: raise p.Rejected('completed enclosing evidence changed')
        if child is not None and (not bound or p.sha(path) != childpin or f.read_json(path) != child or material(CHILD) != child['completed_evidence']):
            raise p.Rejected('child witness/literal receipt changed')
        if passed and readback(plan, child, nt) != child['comparison']: raise p.Rejected('enclosing scalar replay differs')
        if material(BASE) != witness: raise p.Rejected('material changed during final enclosing readback')
    def account():
        record.update(wall_seconds=time.monotonic() - START, full_cpu_seconds=cpu() - CPU0, finalization_reserve_seconds=2)
        if left() <= 0 and record['status'] != 'cancelled': record['status'] = 'budget_exceeded'
        if record['status'] != 'completed': record.update(passed=False, observation_complete=False)
    f.publish(BASE, record, stable, account, left, owned=lambda: h.owned_destination(owner), final_check=stable)
    print(f.canonical({k: record[k] for k in ('status', 'passed', 'observation_complete', 'wall_seconds', 'full_cpu_seconds')}))
    return 0 if record['passed'] and record['status'] == 'completed' else 2

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source-head', required=True)
    parser.add_argument('--worker', action='store_true'); parser.add_argument('--protocol-sha256'); parser.add_argument('--available', type=float)
    args = parser.parse_args()
    def cancel(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT, signal.SIGTERM): signal.signal(sig, cancel)
    if args.worker:
        plan = f.read_json(BASE / 'protocol.json'); pin = p.sha(BASE / 'protocol.json')
        if (plan['git_head'] != args.source_head or args.protocol_sha256 != pin or plan['limits'] != LIMITS
                or args.available is None or not math.isfinite(args.available) or not 2 < args.available <= 25):
            raise p.Rejected('explicit frozen worker identity/budget required')
        raise SystemExit(worker(plan, pin, args.available))
    fd = os.open(ROOT / '.runs/quality-experiment.lock', os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r+') as lock:
        info = os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1: raise p.Rejected('ordinary shared quality lane required')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raise SystemExit(execute(args.source_head))
