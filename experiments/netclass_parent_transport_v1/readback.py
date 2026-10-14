"""Read-only, fixed-input diagnostic readback of completed transport001.

The original controller/protocol failed warning equality and remains failed.
This auditor never invokes native tools, a solver or Git, writes an artifact,
applies copper, or enables production netclass support. Its deterministic
summary permits only the two still-unexecuted protected negatives to continue.
"""
import copy
import hashlib
import json
from pathlib import Path

from autorouter import config as c, floor_route as f, netclass as n
from autorouter import pipeline as p, placement_clearance as io, sexpr as sx
from experiments.netclass_parent_transport_v1 import fixture

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '.runs/netclass-parent-transport-001'
OUT = BASE / 'controls'
HEAD = 'd4b16dd0f32d64c3e736e12452e988aba674e77e'
RECEIPT_SHA = 'c819f61f5defeaa79a525a5ff6de36a8fb56c3560c7b54af3f330c81cb88e56d'
EXECUTION_SHA = '5a9b5acbbd624334c14db8cd92133ad1281e637b48eb90df58d1720cab22fca9'
TREE_SHA = 'e3ca51e2de88afadaebacbbaadbfd109804688f2c06ab4f74577af9d8cec4c59'
LOCK_SHA = 'f04be5cdf6f64bddc16a6c5efd217b2f5e0a1341906ff44033f5807971154efe'
SUPERVISOR_SHA = '2822da582bff9351066219cfcfb9be698d22eb9bcf54853e4d2ff709c42c4dc8'
PRIOR_WALL = 14.319728707996546
PRIOR_CPU = 9.494764
LIMIT = 24 * 1024**2


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def inventory():
    files, directories = io.inventory(BASE, max_bytes=LIMIT, max_files=2048,
                                      max_entries=4096, with_directories=True)
    return {'files': files, 'directories': list(directories)}


def native_map(path, board, hashes):
    value = f.read_json(path)
    if (value.get('source') != str(board) or value.get('board_sha256') != hashes[board.name]
            or value.get('project_sha256') != hashes[board.with_suffix('.kicad_pro').name]
            or value.get('board_saved') is not False):
        raise p.Rejected('retained native class/source binding differs')
    return value


def tool_digest(path):
    """Stream only the five fixed tools; installed tool symlinks are normal."""
    if not path.is_file() or not 0 < path.stat().st_size <= 512 * 1024**2:
        raise p.Rejected('missing or oversized pinned native tool')
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def code_identity(record, execution):
    tools = record['tools']
    if tools != execution['tools'] or tools.get('git_head') != HEAD:
        raise p.Rejected('retained native tool/code freeze differs')
    captured = io.inventory(OUT / 'code', max_bytes=LIMIT, max_files=2048, max_entries=4096)
    if captured != record['runtime_source_sha256']:
        raise p.Rejected('captured native implementation changed')
    implementation = {str(path.relative_to(ROOT)): p.sha(path) for path in sorted((ROOT / 'autorouter').glob('*.py'))}
    if implementation != tools['implementation_sha256']:
        raise p.Rejected('current core differs from actual native001 core')
    # Only the controller is allowed to acquire the explicit continuation.
    for name, expected in captured.items():
        if name == 'experiments/netclass_parent_transport_v1/driver.py':
            if expected != execution['controller_sha256']:
                raise p.Rejected('actual001 controller identity differs')
            continue
        if p.sha(ROOT / name) != expected:
            raise p.Rejected('current retained helper/source differs: ' + name)
    paths = [c.CLI, c.PYTHON, c.JAVA, c.JAR, c.PCBNEW]
    files = {str(path): tool_digest(path) for path in paths}
    if files != tools['files'] or tools.get('kicad') != '10.0.0' or tools.get('freerouting') != '2.5.0':
        raise p.Rejected('actual native tool binaries changed')
    if (p.sha(ROOT / 'toolchain.lock.json') != LOCK_SHA
            or p.sha(ROOT / '.runs/run-netclass-parent-transport-001.py') != SUPERVISOR_SHA
            or execution.get('supervisor_sha256') != SUPERVISOR_SHA):
        raise p.Rejected('original supervisor or lock changed')
    return {'implementation_sha256': implementation, 'tool_files_sha256': files,
            'captured_runtime_sha256': captured, 'readback_sha256': p.sha(Path(__file__)),
            'current_controller_sha256': p.sha(ROOT / 'experiments/netclass_parent_transport_v1/driver.py'),
            'toolchain_lock_sha256': LOCK_SHA}


def process(directory, data, name, argv, *, allowed=(0,)):
    row = f.process_check(directory, data, name, argv, allowed=allowed)
    log = directory / (name + '.log')
    if (row.get('log') != str(log) or row.get('log_truncated') is not False
            or type(row.get('log_bytes')) is not int
            or len(io.read_bytes(log, 2 * 1024**2)) != row['log_bytes']):
        raise p.Rejected('retained native process log differs: ' + name)
    return row


def drc(job, data, name, source, before, *, saved=False):
    input_path = source if saved else job / (name + '-input') / source.name
    result = f.check_drc_stage(job, data, name, source, input_path, saved, before)
    row = next(x for x in data['steps'] if x['name'] == name)
    process(job, data, name, row['argv'], allowed=(5 if result['findings'] else 0,))
    return result


def zero(native):
    if (not p.native_accepted(native) or native['warnings'] != 0 or native['exclusions'] != 0
            or native['findings']):
        raise p.Rejected('native generated control is not exactly clean')


def audit_case(row, steps, *, protected_variant):
    name = 'partial_protected' if protected_variant else 'whole_unprotected'
    case = OUT / name
    source = case / 'original/fixture.kicad_pcb'
    candidate = case / 'candidate/fixture.kicad_pcb'
    job = case / 'job'
    expected_files, recipe = fixture.prepare(protected=protected_variant)
    actual_files = io.inventory(source.parent, contents=True, max_bytes=LIMIT, max_files=2048, max_entries=4096)
    hashes = p.tree_hash(source.parent)
    if actual_files != expected_files or hashes != row['source_hashes'] or recipe != row['recipe']:
        raise p.Rejected('actual original fixture/recipe/floors changed')
    original = sx.read(source)
    protected = p.routes(original)
    if len(protected) != int(protected_variant):
        raise p.Rejected('original protected population differs')
    project = f.read_json(source.with_suffix('.kicad_pro'))
    names = ['source-drc', 'export', 'engine', 'import', 'refill-drc', 'final-netclasses', 'final-drc']
    if not protected_variant:
        names.append('wrong-width-drc')
    if [x['name'] for x in steps] != names or any(x.get('cwd') != str(job) for x in steps):
        raise p.Rejected('missing/unexpected/reordered actual native stages')
    data = {'steps': steps}
    source_native = drc(job, data, 'source-drc', source, hashes)
    if (source_native != row['source_native'] or source_native['opens'] != 3
            or source_native['blocking'] != 0 or source_native['exclusions'] != 0):
        raise p.Rejected('original native diagnostic differs')
    warnings = [x for x in source_native['findings'] if x['severity'] == 'warning']
    if protected_variant:
        identity = sx.unquote(sx.one(protected[0], 'uuid')[1])
        if (len(warnings) != 1 or source_native['warnings'] != 1
                or warnings[0]['type'] != 'track_dangling' or warnings[0]['description'] != 'Track has unconnected end'
                or len(warnings[0]['items']) != 1 or warnings[0]['items'][0]['uuid'] != identity
                or recipe['protected_route']['uuid'] != identity):
            raise p.Rejected('original protected dangling-track warning differs')
    elif warnings or source_native['warnings'] != 0:
        raise p.Rejected('unexpected original unprotected warning')
    exported = native_map(job / 'native-netclasses.json', source, hashes)
    source_audit = n.audit_native(exported, project, parent_policy=True)
    expected_classes = {'Default', 'POWER,Default', 'SIGNAL,Default'}
    if {x['class'] for x in source_audit['nets']} != expected_classes:
        raise p.Rejected('three native composite identities not observed')
    dsn_audit = n.audit_dsn(job / 'task.dsn', exported, project, parent_policy=True)
    if dsn_audit != row['dsn_audit'] or io.read_bytes(job / 'native.dsn') != io.read_bytes(job / 'task.dsn'):
        raise p.Rejected('retained exact raw DSN transport differs')
    settings = row['engine_settings']
    expected_settings = p.engine_profile_settings('completion-only', settings['remaining_outer_wall_seconds_at_assignment'], strict_class_targets=True)
    if settings != expected_settings:
        raise p.Rejected('actual engine profile weakened class targets')
    for stage, action, board, target, args in [
        ('export', 'export', source, job / 'native.dsn', [job / 'native-netclasses.json']),
        ('import', 'import', source, job / 'imported.kicad_pcb', [job / 'routes.ses']),
        ('final-netclasses', 'netclasses', candidate, job / 'final-netclasses.json', []),
    ]:
        process(job, data, stage, [*f.SANDBOX, str(c.PYTHON), str(ROOT / 'autorouter/native.py'),
                                  action, str(board), str(target), *[str(x) for x in args]])
    process(job, data, 'engine', p.engine_argv(job, settings['argv']))
    ses = io.read_bytes(job / 'routes.ses')
    if not ses:
        raise p.Rejected('empty actual native-import session')
    import_audit = {}
    before_refill = p.transplant_routes(original, sx.read(job / 'imported.kicad_pcb'),
                                       protected=protected, audit=import_audit, policy='exact_non_uuid_lock_position_v2')
    before = dict(hashes)
    before[source.name] = hashlib.sha256((sx.dump(before_refill) + '\n').encode()).hexdigest()
    refill = job / 'refill/fixture.kicad_pcb'
    refill_native = drc(job, data, 'refill-drc', refill, before, saved=True)
    rebuilt = p.transplant_fill(before_refill, sx.read(refill))
    if (sx.dump(rebuilt) + '\n').encode() != io.read_bytes(candidate):
        raise p.Rejected('candidate does not reconstruct from actual import/refill')
    p.verify_candidate_files(candidate, hashes)
    final_tree = sx.read(candidate)
    if p.immutable(final_tree) != p.immutable(original) or any(x not in p.routes(final_tree) for x in protected):
        raise p.Rejected('original design or protected route changed')
    final_hashes = p.tree_hash(candidate.parent)
    final_map = native_map(job / 'final-netclasses.json', candidate, final_hashes)
    n.audit_native(final_map, project, parent_policy=True)
    remove_code = lambda rows: [{k: v for k, v in x.items() if k != 'netcode'} for x in rows]
    if remove_code(final_map['nets']) != remove_code(exported['nets']):
        raise p.Rejected('native class membership/parents changed after import/refill')
    dimensions = p.audit_route_dimensions(final_tree, protected, final_map)
    checked = dimensions['checked']
    if checked['vias'] < 1 or checked['segments'] < 3 or checked['protected'] != int(protected_variant):
        raise p.Rejected('generated class width/via/protection not exercised')
    final = drc(job, data, 'final-drc', candidate, final_hashes)
    zero(refill_native)
    zero(final)
    if final['ignored_checks'] != source_native['ignored_checks']:
        raise p.Rejected('native ignored checks changed')
    result = {'case': name, 'source': str(source), 'candidate': str(candidate), 'job': str(job),
              'source_hashes': hashes, 'positive': True, 'native': final, 'source_native': source_native,
              'candidate_sha256': p.sha(candidate), 'route_dimensions': dimensions, 'protected_import': import_audit,
              'native_classes': sorted(expected_classes), 'dsn_audit': dsn_audit,
              'source_native_map_sha256': p.sha(job / 'native-netclasses.json'),
              'final_native_map_sha256': p.sha(job / 'final-netclasses.json'),
              'source_recipe_sha256': digest(recipe), 'native_stage_names': names}
    if not protected_variant:
        for key in ('native', 'route_dimensions', 'protected_import', 'candidate_sha256'):
            if row[key] != result[key]:
                raise p.Rejected('stored completed unprotected positive differs: ' + key)
        wrong = case / 'wrong-width/fixture.kicad_pcb'
        changed = copy.deepcopy(final_tree)
        net_names = {x[1]: sx.unquote(x[2]) for x in sx.children(changed, 'net')}
        target = next(x for x in p.routes(changed) if x[0] == 'segment'
                      and net_names.get(sx.one(x, 'net')[1], sx.unquote(sx.one(x, 'net')[1])) == '/PWR_PAIR')
        sx.one(target, 'width')[1] = '0.4'
        if (sx.dump(changed) + '\n').encode() != io.read_bytes(wrong):
            raise p.Rejected('completed wrong-width control mutation differs')
        p.verify_candidate_files(wrong, hashes)
        try:
            p.audit_route_dimensions(changed, [], final_map)
        except p.Rejected as exc:
            reason = str(exc)
        else:
            raise p.Rejected('wrong source class target was admitted')
        if reason != 'generated track differs from native netclass target: /PWR_PAIR':
            raise p.Rejected('completed target refusal differs')
        wrong_native = drc(job, data, 'wrong-width-drc', wrong, p.tree_hash(wrong.parent))
        zero(wrong_native)
        wrong_summary = {'class_audit_rejected': True, 'reason': reason, 'candidate_sha256': p.sha(wrong),
                         'native': wrong_native, 'native_minimums_accepted': True,
                         'source_floor_preserved': project['board']['design_settings']['rules']['min_track_width']}
        if wrong_summary != row['wrong_width']:
            raise p.Rejected('stored completed wrong-width outcome differs')
        result['wrong_width'] = wrong_summary
    return result


def qualify():
    """Return deterministic JSON-safe diagnostic metadata; no output side effects."""
    before = inventory()
    if digest(before) != TREE_SHA or before['files'].get('controls/result.json') != RECEIPT_SHA or before['files'].get('execution.json') != EXECUTION_SHA:
        raise p.Rejected('fixed actual001 complete input inventory changed')
    record = f.read_json(OUT / 'result.json')
    execution = f.read_json(BASE / 'execution.json')
    if (record.get('status') != 'failed' or record.get('controls_passed') is not False
            or record.get('accepted') is not False or record.get('production_support_changed') is not False
            or record.get('error') != 'Rejected: generated positive native failure/warning regression'
            or execution.get('result_sha256') != RECEIPT_SHA or execution.get('controls_passed') is not False
            or execution.get('accepted') is not False or execution.get('status') != 'completed'
            or execution.get('charged_wall_seconds') != PRIOR_WALL or execution.get('lifetime_full_cpu_seconds') != PRIOR_CPU):
        raise p.Rejected('original failed experiment status/cost changed')
    code_before = code_identity(record, execution)
    outer = execution['process']
    if (outer.get('status') != 'nonzero_exit' or outer.get('exit_code') != 2
            or outer.get('cleanup_complete') is not True or outer.get('cwd') != str(BASE)
            or outer.get('argv') != [*f.SANDBOX, str(ROOT / '.venv/bin/python'), '-B',
                                     str(ROOT / 'experiments/netclass_parent_transport_v1/driver.py'),
                                     '--output', str(OUT), '--run-native']
            or outer.get('log') != str(BASE / 'command.log') or outer.get('log_truncated') is not False
            or len(io.read_bytes(BASE / 'command.log')) != outer.get('log_bytes')):
        raise p.Rejected('original outer failed process differs')
    rows = record['cases']
    if [x['case'] for x in rows] != ['whole_unprotected', 'partial_protected'] or len(record['steps']) != 15:
        raise p.Rejected('actual fixed case/process population differs')
    charge = dict(record)
    child = sum(x['cpu_seconds'] for x in record['steps'])
    monitor = sum(x['monitor_cpu_seconds'] for x in record['steps'])
    charge.update(child_cpu_seconds=child, monitor_cpu_seconds=monitor,
                  parent_cpu_seconds=record['total_cpu_seconds'] - child - monitor)
    p.check_resource_accounting(charge)
    if (record.get('within_budget') is not True or max(PRIOR_WALL, PRIOR_CPU) > 185
            or outer['wall_seconds'] > PRIOR_WALL or outer['cpu_seconds'] > PRIOR_CPU
            or record['wall_seconds'] > PRIOR_WALL or record['total_cpu_seconds'] > PRIOR_CPU):
        raise p.Rejected('original measured outer costs do not bound all stages')
    cases = []
    for row in rows:
        job = OUT / row['case'] / 'job'
        steps = [x for x in record['steps'] if x.get('cwd') == str(job)]
        cases.append(audit_case(row, steps, protected_variant=row['case'] == 'partial_protected'))
    if inventory() != before or code_identity(record, execution) != code_before:
        raise p.Rejected('actual input/source/tool evidence changed during readback')
    return {'schema': 1, 'kind': 'preserved-actual001-corrected-diagnostic-readback',
            'accepted': False, 'production_support_changed': False, 'native_executed': False,
            'original_controller_status': 'failed', 'original_protocol_guard_failed': True,
            'diagnostic_positive_readback_passed': True, 'schematic_parity': 'unavailable; owned fixture has no schematic',
            'root_receipt': str(OUT / 'result.json'), 'root_receipt_sha256': RECEIPT_SHA,
            'execution': str(BASE / 'execution.json'), 'execution_sha256': EXECUTION_SHA,
            'input_inventory': before, 'input_inventory_sha256': TREE_SHA, 'code_identity': code_before,
            'prior_wall_seconds': PRIOR_WALL, 'prior_cpu_seconds': PRIOR_CPU,
            'prior_inner_wall_seconds': record['wall_seconds'], 'prior_inner_total_cpu_seconds': record['total_cpu_seconds'],
            'prior_stage_wall_seconds': sum(x['wall_seconds'] for x in record['steps']), 'prior_stage_cpu_seconds': child,
            'derived_inner_nonstage_cpu_seconds': charge['parent_cpu_seconds'],
            'cost_scope': execution['scope'], 'cases': cases,
            'remaining_native_controls': ['protected wrong-width DRC', 'protected removal DRC'],
            'limitations': ['diagnostic readback correction only; original001 remains failed',
                            'no repeated native/engine stages', 'no production admission',
                            'no family routing gain, general composites, selected multiclass, physical or human review']}
