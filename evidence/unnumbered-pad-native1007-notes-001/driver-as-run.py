"""Lead-only bounded Native1007 unassigned conductive-pad diagnostic.

SPDX-License-Identifier: GPL-3.0-or-later
Source-only controller until explicitly invoked by the lead. No engine, save,
support admission, parity exception, GUI qualification or routing acceptance.
Prepare and run are separate foreground invocations; their costs are summed.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(r.ru_utime + r.ru_stime for r in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse, copy, fcntl, hashlib, importlib.util, json, math, os, signal, stat, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, handoff as h, sexpr as sx
from autorouter import local_settings as ls, netclass as nc
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.four_copper_class_transport_v1 import fixture as base_fixture

DRAFT = ROOT / '.runs/unnumbered-conductive-pad-probe-draft-002'
BASE = ROOT / '.runs/unnumbered-pad-native-001'
PROTOCOL = BASE / 'protocol.json'
OUTER = BASE / 'execution'
CHILD = OUTER / 'worker'
RETAINED = ROOT / '.runs/hfe-original-native-preparation-001/protocol.json'
LIMIT = 20 * 1024**2
LIMITS = dict(whole_wall_full_cpu_seconds=60, worker_seconds=55,
              aggregate_bytes=LIMIT, group_rss_bytes=2 * 1024**3,
              log_bytes=256 * 1024, publication_allowance_seconds=2)
KIND = 'unnumbered-conductive-pad-native1007-v1'
SCOPE = ('Owned development fixture only: same-BOARD no-save raw DSN representation and '
         'original-rule no-save native copper-obstacle controls. Nonschematic DRC; '
         'class parity remains separately unsupported. No engine or routing acceptance.')

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def digest(raw): return hashlib.sha256(raw).hexdigest()
def hashes(files): return {name: digest(raw) for name, raw in files.items()}
def payload(path):
    return io.inventory(path, contents=True, max_bytes=LIMIT, max_files=2048, max_entries=4096)
def cap():
    # The enclosing runner polls this same complete tree during Native work.
    io.inventory(BASE, max_bytes=LIMIT, max_files=2048, max_entries=4096)
def draft():
    manifest = f.read_json(DRAFT / 'manifest.json')
    if manifest.get('status') != 'frozen_pure_controls_passed_native_unexecuted':
        raise p.Rejected('frozen draft002 identity differs')
    for name, row in manifest['files'].items():
        raw = io.read_bytes(DRAFT / name, 1024**2)
        if digest(raw) != row['sha256'] or len(raw) != row['bytes']:
            raise p.Rejected('frozen draft002 changed: ' + name)
    return manifest

def core_names(tools):
    return sorted(set(tools['implementation_sha256']) | {
        str(Path(__file__).relative_to(ROOT)), 'toolchain.lock.json',
        'experiments/hfe_original_native_v1/driver.py',
        'experiments/original_project_native_v1/driver.py',
        'experiments/placement_handoff_native_v1/driver.py',
        'experiments/placement_production_controls_v1/driver.py',
        'experiments/four_copper_class_transport_v1/fixture.py',
        'experiments/native_schematic_transport_v1/fixture.py',
        'experiments/pic_custom_observer_v1/mapping.py'})

def sources(plan):
    for case, expected in plan['source_hashes'].items():
        if hashes(payload(BASE / 'sources' / case)) != expected:
            raise p.Rejected('prepared complete project changed: ' + case)

def context(plan, pin=None):
    shared.clean(plan['git_head']); draft()
    if (p.sha(DRAFT / 'manifest.json') != plan['draft_manifest_sha256']
            or p.sha(RETAINED) != plan['retained_tool_protocol_sha256']):
        raise p.Rejected('draft/retained tool source changed')
    if pin is not None and (p.sha(PROTOCOL) != pin or
            f.canonical(f.read_json(PROTOCOL)) != f.canonical(plan)):
        raise p.Rejected('prospective protocol changed')
    nt = p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
    if (f.read_json(RETAINED)['native_toolchain'] != nt.record()
            or p.tool_manifest(native_toolchain=nt) != plan['tools']):
        raise p.Rejected('fresh core/HEAD/tool pins differ')
    if any(p.sha(ROOT / name) != pin for name, pin in plan['code_sha256'].items()):
        raise p.Rejected('frozen helper/controller changed')
    sources(plan); cap()
    return nt

def original_preservation(base, positive, negative, fx):
    """Independent subtraction of exactly the authored additions to base AST."""
    name = fx.STEM + '.kicad_pcb'
    expected = {fx.STEM + suffix for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_prl')}
    if set(base) != expected or set(positive) != expected or set(negative) != expected:
        raise p.Rejected('exact four-file complete projects required')
    if any(positive[n] != base[n] or negative[n] != base[n] for n in expected - {name}):
        raise p.Rejected('base project/schematic/local settings changed')
    tree = sx.parse(positive[name].decode()); wanted = sx.parse(base[name].decode())
    added = {fx.uid(label) for label in ('route-front', 'route-inner-left', 'route-inner-detour',
        'route-inner-right', 'route-back', 'route-via-14', 'route-via-24', 'gnd-completion')}
    removed = []
    for node in list(tree):
        if isinstance(node, list) and node and node[0] in p.ROUTES:
            ident = sx.unquote(sx.one(node, 'uuid')[1])
            if ident in added: removed.append(ident); tree.remove(node)
    if set(removed) != added or len(removed) != len(added):
        raise p.Rejected('authored route additions differ')
    found = []
    for fp in sx.children(tree, 'footprint'):
        for node in list(fp):
            if isinstance(node, list) and node and node[0] in {'pad', 'fp_rect'}:
                ident = sx.unquote(sx.one(node, 'uuid')[1])
                if ident in {fx.PAD_UUID, fx.uid('added-pad-courtyard')}:
                    found.append(ident); fp.remove(node)
    if sorted(found) != sorted([fx.PAD_UUID, fx.uid('added-pad-courtyard')]) or tree != wanted:
        raise p.Rejected('base atoms/component/pad/KEEP identities not preserved exactly')
    a = sx.parse(positive[name].decode()); b = sx.parse(negative[name].decode())
    extra = fx.segment('invalid-inner-through-pad', (14, '11.6'), (24, '11.6'), 'In1.Cu', 'ROUTE', '.4')
    if b != a + [extra]: raise p.Rejected('negative differs beyond exact intrusion')
    return dict(base_ast_exact_after_declared_addition_subtraction=True,
                original_nonboard_files_exact=True, protected_routes=p.routes(wanted))

def prepare(head):
    shared.clean(head); draft()
    retained_pin = p.sha(RETAINED)
    nt = p.ExperimentalNativeToolchain.from_record(f.read_json(RETAINED)['native_toolchain'])
    tools = p.tool_manifest(native_toolchain=nt)
    if tools['git_head'] != head: raise p.Rejected('intended clean checkpoint differs')
    # Create durable source copies before validating their prospective assertions.
    h.real_path(BASE, existing=False); BASE.mkdir(); (BASE / 'sources').mkdir()
    fx = load('unnumbered_frozen_fixture', DRAFT / 'fixture.py')
    base = base_fixture.files(); positive = fx.files('positive'); negative = fx.files('through_pad')
    for case, files in (('base', base), ('positive', positive), ('through_pad', negative)):
        copy_bytes(files, BASE / 'sources' / case)
    pair = fx.validate_pair(positive, negative)
    preservation = original_preservation(base, positive, negative, fx)
    plan = dict(schema=1, kind=KIND, status='frozen_for_lead_execution', git_head=head,
        draft_manifest_sha256=p.sha(DRAFT / 'manifest.json'), retained_tool_protocol_sha256=retained_pin,
        native_toolchain=nt.record(), tools=tools,
        code_sha256={n: p.sha(ROOT / n) for n in core_names(tools)},
        source_hashes={case: hashes(files) for case, files in
                       (('base', base), ('positive', positive), ('through_pad', negative))},
        stem=fx.STEM, pad_uuid=fx.PAD_UUID, intrusion_uuid=fx.INTRUSION_UUID,
        pair_assertion=pair, preservation=preservation, limits=LIMITS,
        schematic_parity=False, accepted=False, qualified=False, routing_accepted=False, scope=SCOPE)
    context(plan)
    plan['preparation_costs'] = dict(wall_seconds=time.monotonic() - START,
        full_cpu_seconds=cpu() - CPU0, publication_allowance_seconds=2)
    p.save_json(PROTOCOL, plan)
    print(f.canonical(dict(prepared=True, native_executed=False, protocol_sha256=p.sha(PROTOCOL))))

def native_callback(plan, pin, output):
    """One LoadBoard and one live object across sync, observations and export."""
    nt = context(plan, pin)
    import pcbnew, _pcbnew
    from autorouter import native, padless_alias
    if (pcbnew.GetBuildVersion() != '10.0.7' or Path(sys.executable).resolve() != nt.python
            or Path(_pcbnew.__file__).resolve() != nt.pcbnew):
        raise p.Rejected('actual loaded Native1007 tool identity differs')
    source = BASE / 'sources/positive' / (plan['stem'] + '.kicad_pcb')
    output = h.real_path(output)
    if output != CHILD / 'export': raise p.Rejected('fixed fresh callback output required')
    before_files = payload(source.parent)
    raw = before_files[source.name]; pro = before_files[source.with_suffix('.kicad_pro').name]
    board = pcbnew.LoadBoard(str(source))
    if not board: raise p.Rejected('Native LoadBoard failed')
    mapping = native.netclasses(board, str(source), (digest(raw), digest(pro)))
    observer = load('unnumbered_frozen_native_observer', DRAFT / 'observe.py')
    before = observer.observe(board, pcbnew)
    p.save_json(output / 'before.json', before); p.save_json(output / 'classes.json', mapping)
    proof = padless_alias.export_board(board, str(source), str(output / 'native.dsn'), pcbnew,
        mapping=mapping, before=(digest(raw), digest(pro)))
    after = observer.observe(board, pcbnew); p.save_json(output / 'after.json', after)
    if before != after or payload(source.parent) != before_files:
        raise p.Rejected('same-BOARD export mutated pad observation or exact source')
    if proof['zero_alias'] is not True or proof['board_saved'] is not False:
        raise p.Rejected('fixture unexpectedly exercised alias mutation/save')
    context(plan, pin)
    p.save_json(output / 'callback.json', dict(schema=1, native_version='10.0.7',
        source_hashes=hashes(before_files), before_sha256=p.sha(output / 'before.json'),
        after_sha256=p.sha(output / 'after.json'), dsn_sha256=p.sha(output / 'native.dsn'),
        classmap_sha256=p.sha(output / 'classes.json'), same_loaded_board=True,
        board_saved=False, routing_accepted=False))

def callback_readback(job, record, plan, nt, pin):
    export = CHILD / 'export'
    argv = [str(nt.python), '-B', str(Path(__file__)), '--mode', 'native',
            '--source-head', plan['git_head'], '--protocol-sha256', pin]
    process = f.process_check(job.out, record, 'pad-observation', [*f.SANDBOX, *argv])
    log = io.read_bytes(job.out / 'pad-observation.log', LIMITS['log_bytes'])
    if (process.get('log_truncated') is not False or process.get('log_bytes') != len(log)
            or process.get('log') != str(job.out / 'pad-observation.log')):
        raise p.Rejected('callback log changed/truncated')
    before = f.read_json(export / 'before.json'); after = f.read_json(export / 'after.json')
    mapping = f.read_json(export / 'classes.json'); captured = f.read_json(export / 'callback.json')
    source = BASE / 'sources/positive' / (plan['stem'] + '.kicad_pcb')
    if before != after or captured != dict(schema=1, native_version='10.0.7',
        source_hashes=plan['source_hashes']['positive'], before_sha256=p.sha(export / 'before.json'),
        after_sha256=p.sha(export / 'after.json'), dsn_sha256=p.sha(export / 'native.dsn'),
        classmap_sha256=p.sha(export / 'classes.json'), same_loaded_board=True,
        board_saved=False, routing_accepted=False): raise p.Rejected('callback scalar/hash binding differs')
    if (mapping.get('source') != str(source) or mapping.get('board_saved') is not False
            or mapping.get('board_sha256') != p.sha(source)
            or mapping.get('project_sha256') != p.sha(source.with_suffix('.kicad_pro'))):
        raise p.Rejected('Native class/source binding differs')
    project = f.read_json(source.with_suffix('.kicad_pro'))
    classes = nc.audit_native(mapping, project, parent_policy=True, native_toolchain=nt)
    if {row['name']: row['class'] for row in mapping['nets']} != {
            'KEEP': 'Default', 'ROUTE': 'POWER,Default', 'GND': 'SIGNAL,Default'}:
        raise p.Rejected('owned Default/POWER/SIGNAL map differs')
    checker = load('unnumbered_frozen_dsn_checker', DRAFT / 'dsn_check.py')
    represented = checker.check(io.read_bytes(export / 'native.dsn', 4 * 1024**2),
                                before, plan['pad_uuid'], io.read_bytes(source))
    # Re-derive the zero-alias proof without pretending the callback is a normal
    # native.py command. These sidecars live outside the DRC Job policy census.
    from autorouter import padless_alias as alias
    dsn = io.read_bytes(export / 'native.dsn', 4 * 1024**2)
    paths = alias.artifact_paths(export / 'native.dsn'); raw = io.read_bytes(source)
    binding = alias.plan(raw); alias.dsn_aliases(dsn, raw, binding)
    proof = f.read_json(paths['proof'])
    expected = dict(schema=1, policy=alias.POLICY, native_version='10.0.7',
        source=str(source), source_sha256=digest(raw), project_sha256=p.sha(source.with_suffix('.kicad_pro')),
        output=str(export / 'native.dsn'), dsn_sha256=digest(dsn), source_copy=paths['source_copy'].name,
        binding=binding, native_footprints=binding['footprints'], zero_alias=True,
        native_classmap=mapping, observation=None, board_saved=False, routing_accepted=False)
    if proof != expected or io.read_bytes(paths['source_copy']) != raw:
        raise p.Rejected('actual shared export proof differs from immutable source')
    return represented, classes

def native_predicate(native, raw, negative, plan):
    if native['opens'] or native['exclusions'] or raw['unconnected_items'] or raw['schematic_parity']:
        raise p.Rejected('new opens/exclusions/parity findings in obstacle control')
    if not negative:
        if any(native[key] for key in ('blocking', 'warnings')) or native['findings']:
            raise p.Rejected('positive nonschematic control has unexpected findings')
        return dict(passed=True, opens=0, blocking=0, warnings=0, exclusions=0)
    errors = []
    for finding in native['findings']:
        if (finding['type'] not in p.KNOWN_CHECKS | {'padstack_invalid'}
                or finding.get('excluded', False) or finding['severity'] == 'exclusion'):
            raise p.Rejected('unknown/excluded negative finding')
        if finding['severity'] == 'warning':
            if finding['type'] in p.CRITICAL_FINDINGS:
                raise p.Rejected('unexpected critical negative warning')
            continue
        items = finding['items']
        # Actual KiCad drc.v1 item schema uses uuid, not item_id or kiid.
        if (finding not in raw['violations'] or finding['severity'] != 'error'
                or finding['type'] not in {'clearance', 'shorting_items'} or len(items) != 2
                or any(type(item) is not dict or type(item.get('uuid')) is not str for item in items)
                or {item['uuid'] for item in items} != {plan['pad_uuid'], plan['intrusion_uuid']}):
            raise p.Rejected('negative error is not the declared copper-pad/intrusion pair')
        errors.append(finding)
    if not errors or native['blocking'] != len(errors):
        raise p.Rejected('no exact copper-obstacle error or inconsistent count')
    return dict(passed=True, opens=0, exclusions=0, exact_copper_errors=errors,
                warnings=[r for r in native['findings'] if r['severity'] == 'warning'])

class PadJob(shared.BoundJob):
    """Retained dispatch, with a pre-parser raw DRC witness and 20MiB outer cap."""
    def step(self, name, argv, allowed=(0,), *, already_sandboxed=False):
        cap()
        result = super().step(name, argv, allowed, already_sandboxed=already_sandboxed)
        command = [str(x) for x in argv]
        if command[:3] == [str(self.native_cli), 'pcb', 'drc']:
            report = self.out / (name + '.json'); log = self.out / (name + '.log')
            # No report JSON parsing has occurred. Job.drc will subsequently
            # complete its original PRL journal/binding and invoke its parser.
            raw = io.read_bytes(report, LIMIT); rawlog = io.read_bytes(log, LIMITS['log_bytes'])
            p.save_json(CHILD / 'stage-freeze' / (name + '.json'), dict(
                process_before_prl_finalization=copy.deepcopy(result),
                raw_report_sha256=digest(raw), log_sha256=digest(rawlog),
                input_hashes=p.tree_hash(Path(command[-1]).parent)))
        cap()
        return result

def stage_freeze(job, stage, inp):
    frozen = f.read_json(CHILD / 'stage-freeze' / (stage + '.json'))
    actual = f.read_json(job.out / (stage + '-process.json'))
    early = frozen['process_before_prl_finalization']
    if (any(actual.get(k) != value for k, value in early.items())
            or frozen['raw_report_sha256'] != p.sha(job.out / (stage + '.json'))
            or frozen['log_sha256'] != p.sha(job.out / (stage + '.log'))
            or frozen['input_hashes'] != p.tree_hash(inp.parent)
            or actual.get('log_truncated') is not False):
        raise p.Rejected('pre-parser native process/raw/log/input witness changed')
    return frozen

def worker(plan, pin, available):
    nt = context(plan, pin); CHILD.mkdir(); owner = {}; h.capture_destination(owner, CHILD)
    limit = min(53, available - 2)
    def remaining(): return min(limit - (time.monotonic() - START), limit - (cpu() - CPU0))
    record = dict(schema=1, status='failed', controls_passed=False, representation_observed=False,
        native_obstacle_observed=False, accepted=False, qualified=False, routing_accepted=False,
        production_support_qualified=False, engine_executed=False, schematic_parity=False,
        tools=plan['tools'], protocol_sha256=pin, scope=SCOPE)
    job = PadJob(CHILD / 'job', max(.001, remaining()), remaining,
                         native_toolchain=nt, protect_local_settings=True)
    record['steps'] = job.steps; stages = []
    try:
        copy_bytes({Path(n).name: io.read_bytes(ROOT / n, 1024**2)
                    for n in plan['tools']['implementation_sha256']}, job.out / 'code')
        copy_bytes({n: io.read_bytes(ROOT / n, 1024**2) for n in plan['code_sha256']}, CHILD / 'control-code')
        (CHILD / 'export').mkdir(); (CHILD / 'stage-freeze').mkdir()
        argv = [str(nt.python), '-B', str(Path(__file__)), '--mode', 'native',
                '--source-head', plan['git_head'], '--protocol-sha256', pin]
        job.step('pad-observation', argv)
        represented, classes = callback_readback(job, record, plan, nt, pin)
        record.update(representation_observed=True, representation=represented, native_classes=classes)
        for name, negative in (('positive', False), ('through_pad', True)):
            source = BASE / 'sources' / name / (plan['stem'] + '.kicad_pcb')
            before = plan['source_hashes'][name]; stage = name + '-drc'
            inp = job.out / (stage + '-input') / source.name
            stages.append((stage, source, inp, before, negative))
            native = job.drc(stage, source, save=False)
            preparse = stage_freeze(job, stage, inp)
            # Freeze all completed stage material before secondary parsing.
            frozen = shared.material(job.out)
            replay = f.check_drc_stage(job.out, record, stage, source, inp, False, before,
                                       native_toolchain=nt)
            raw = f.read_json(job.out / (stage + '.json'))
            if shared.material(job.out) != frozen or replay != native:
                raise p.Rejected('DRC stage material/summary changed during readback')
            result = native_predicate(replay, raw, negative, plan)
            record[name] = dict(native=replay, predicate=result,
                raw_report_sha256=p.sha(job.out / (stage + '.json')),
                pre_parser_witness=preparse, stage_frozen_material=frozen)
            context(plan, pin)
        ls.check_normal_policy(job.out, record, max_bytes=LIMIT, max_files=2048, native_toolchain=nt)
        record.update(status='controls_passed', controls_passed=True, native_obstacle_observed=True)
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      error=type(exc).__name__ + ': ' + str(exc), controls_passed=False)
    witness = shared.material(CHILD); record['completed_evidence'] = witness
    def stable():
        h.owned_destination(owner); context(plan, pin)
        if shared.material(CHILD) != witness: raise p.Rejected('completed child material changed')
        if record.get('controls_passed') is True:
            represented, classes = callback_readback(job, record, plan, nt, pin)
            if represented != record['representation'] or classes != record['native_classes']:
                raise p.Rejected('late representation/classes differ')
            for stage, source, inp, before, negative in stages:
                preparse = stage_freeze(job, stage, inp)
                native = f.check_drc_stage(job.out, record, stage, source, inp, False, before, native_toolchain=nt)
                name = 'through_pad' if negative else 'positive'; old = record[name]
                if (preparse != old['pre_parser_witness'] or native != old['native']
                        or p.sha(job.out / (stage + '.json')) != old['raw_report_sha256']
                        or native_predicate(native, f.read_json(job.out / (stage + '.json')), negative, plan) != old['predicate']):
                    raise p.Rejected('late native control differs')
            ls.check_normal_policy(job.out, record, max_bytes=LIMIT, max_files=2048, native_toolchain=nt)
        if shared.material(CHILD) != witness: raise p.Rejected('material changed during final replay')
    def account():
        record.update(wall_seconds=time.monotonic() - START, full_cpu_seconds=cpu() - CPU0)
        if remaining() <= 0 and record['status'] != 'cancelled': record['status'] = 'budget_exceeded'
        if record['status'] != 'controls_passed': record['controls_passed'] = False
    f.publish(CHILD, record, stable, account, remaining,
              owned=lambda: h.owned_destination(owner), final_check=stable)
    stored = f.read_json(CHILD / 'result.json')
    print(f.canonical({k: stored.get(k) for k in ('status', 'controls_passed', 'error', 'reason')}))
    return 0 if stored.get('status') == 'controls_passed' and stored.get('controls_passed') is True else 2

def costs(plan):
    value = plan['preparation_costs']
    if value.get('publication_allowance_seconds') != 2: raise p.Rejected('preparation reserve differs')
    for key in ('wall_seconds', 'full_cpu_seconds'):
        if type(value[key]) not in (int, float) or not math.isfinite(value[key]) or value[key] < 0:
            raise p.Rejected('finite nonnegative preparation costs required')
    return value['wall_seconds'] + 2, value['full_cpu_seconds'] + 2

def execute(plan, pin):
    nt = context(plan, pin); prepwall, prepcpu = costs(plan)
    def remaining():
        return min(58 - prepwall - (time.monotonic() - START), 58 - prepcpu - (cpu() - CPU0))
    OUTER.mkdir(); owner = {}; h.capture_destination(owner, OUTER)
    fd = os.open(ROOT / '.runs/quality-experiment.lock', os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r+') as lock:
        info = os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise p.Rejected('ordinary shared foreground quality lane required')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        available = min(55, remaining())
        if available <= 2: raise p.Rejected('total budget exhausted before Native launch')
        argv = [*f.SANDBOX, str(ROOT / '.venv/bin/python'), '-B', str(Path(__file__)),
            '--mode', 'worker', '--source-head', plan['git_head'], '--protocol-sha256', pin,
            '--available', str(available)]
        process = run(argv, cwd=BASE, log=OUTER / 'command.log', timeout=available,
            max_log_bytes=LIMITS['log_bytes'], max_workdir_bytes=LIMIT,
            max_group_rss_bytes=LIMITS['group_rss_bytes'])
        path = CHILD / 'result.json'; childpin = p.sha(path) if path.is_file() else None
        child = f.read_json(path) if childpin is not None else None
        bound = bool(child and shared.material(CHILD) == child.get('completed_evidence')
                     and p.sha(path) == childpin and f.read_json(path) == child)
        witness = shared.material(OUTER); logpin = p.sha(OUTER / 'command.log')
        passed = bool(bound and child.get('status') == 'controls_passed'
            and child.get('controls_passed') is True and child.get('representation_observed') is True
            and child.get('native_obstacle_observed') is True and child.get('accepted') is False
            and child.get('qualified') is False and child.get('routing_accepted') is False
            and child.get('tools') == plan['tools'] and process['status'] == 'success'
            and process['exit_code'] == 0 and process.get('cleanup_complete') is True
            and process.get('log_truncated') is False)
        record = dict(schema=1, kind=KIND, status='controls_passed' if passed else 'failed',
            controls_passed=passed, representation_observed=bool(bound and child.get('representation_observed') is True),
            native_obstacle_observed=bool(bound and child.get('native_obstacle_observed') is True),
            accepted=False, qualified=False, routing_accepted=False, production_support_qualified=False,
            engine_executed=False, schematic_parity=False, process=process, child=child,
            child_receipt_sha256=childpin, child_material_bound=bound, completed_evidence=witness,
            protocol_sha256=pin, tools=plan['tools'], preparation_costs=plan['preparation_costs'],
            limits=LIMITS, scope=SCOPE)
        if process['status'] == 'cancelled' or child and child.get('status') == 'cancelled':
            record['status'] = 'cancelled'
        def stable():
            h.owned_destination(owner); context(plan, pin)
            if shared.material(OUTER) != witness or p.sha(OUTER / 'command.log') != logpin:
                raise p.Rejected('enclosing completed material changed')
            if child is not None and (not bound or shared.material(CHILD) != child.get('completed_evidence')
                    or p.sha(path) != childpin or f.read_json(path) != child):
                raise p.Rejected('child pre-publication witness/literal receipt changed')
            if passed:
                ls.check_normal_policy(CHILD / 'job', child, max_bytes=LIMIT, max_files=2048, native_toolchain=nt)
            if shared.material(OUTER) != witness: raise p.Rejected('material changed during final parent replay')
        def account():
            record.update(invocation_wall_seconds=time.monotonic() - START,
                invocation_full_cpu_seconds=cpu() - CPU0,
                wall_seconds=prepwall + time.monotonic() - START,
                full_cpu_seconds=prepcpu + cpu() - CPU0)
            if remaining() <= 0 and record['status'] != 'cancelled': record['status'] = 'budget_exceeded'
            if record['status'] != 'controls_passed': record['controls_passed'] = False
        f.publish(OUTER, record, stable, account, remaining,
                  owned=lambda: h.owned_destination(owner), final_check=stable)
        stored = f.read_json(OUTER / 'result.json')
        print(f.canonical({k: stored.get(k) for k in ('status', 'controls_passed', 'wall_seconds', 'full_cpu_seconds')}))
        return 0 if stored.get('status') == 'controls_passed' and stored.get('controls_passed') is True else 2

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-head', required=True)
    parser.add_argument('--mode', choices=('prepare', 'run', 'worker', 'native'), default='run')
    parser.add_argument('--protocol-sha256'); parser.add_argument('--available', type=float)
    args = parser.parse_args()
    def interrupted(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT, signal.SIGTERM): signal.signal(sig, interrupted)
    if args.mode == 'prepare':
        fd = os.open(ROOT / '.runs/quality-experiment.lock', os.O_RDWR | os.O_NOFOLLOW)
        with os.fdopen(fd, 'r+') as lock:
            info = os.fstat(lock.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise p.Rejected('ordinary shared foreground preparation lane required')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            prepare(args.source_head)
    else:
        plan = f.read_json(PROTOCOL); pin = p.sha(PROTOCOL)
        if (plan.get('kind') != KIND or plan.get('status') != 'frozen_for_lead_execution'
                or plan.get('git_head') != args.source_head or plan.get('limits') != LIMITS):
            raise p.Rejected('fixed intended prospective protocol required')
        if args.mode in ('worker', 'native') and args.protocol_sha256 != pin:
            raise p.Rejected('explicit worker protocol pin differs')
        if args.mode == 'native': native_callback(plan, pin, CHILD / 'export')
        elif args.mode == 'worker':
            if args.available is None or not math.isfinite(args.available) or not 2 < args.available <= 55:
                raise p.Rejected('bounded parent availability required')
            raise SystemExit(worker(plan, pin, args.available))
        else: raise SystemExit(execute(plan, pin))
