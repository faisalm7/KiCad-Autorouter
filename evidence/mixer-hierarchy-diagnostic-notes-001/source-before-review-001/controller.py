"""Unexecuted lead-reviewed mixer hierarchy diagnostic, not support admission.

SPDX-License-Identifier: GPL-3.0-or-later
One original fullSCH Native observation; no engine, route, source repair or
field-warning waiver. Prepare/run costs share a120-second wall/full-CPU cap.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(r.ru_utime + r.ru_stime for r in
        (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse, collections, copy, fcntl, hashlib, math, os, signal, stat, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, config as c, handoff as h
from autorouter import placement_clearance as io, sexpr as sx, schematic_fields as fields
from autorouter import schematic_field_evidence as field_evidence, local_settings as ls, board_floor as g
from autorouter import netclass as nc
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes

SOURCE = ROOT / '.data/boards/kicad-multichannel'
STEM = 'multichannel_mixer'
BOARD = STEM + '.kicad_pcb'
ROOT_SCH = STEM + '.kicad_sch'
CHILD_SCH = 'channel_strip.kicad_sch'
BASE = ROOT / '.runs/mixer-hierarchy-probe-native-001'
PROTOCOL = BASE / 'protocol.json'
OUTER = BASE / 'execution'
CHILD = OUTER / 'worker'
KIND = 'mixer-two-file-four-instance-hierarchy-diagnostic-v1'
SOURCE_BYTES = 16 * 1024**2
LIMIT = 128 * 1024**2
LIMITS = dict(whole_wall_full_cpu_seconds=120, source_files=40, source_bytes=SOURCE_BYTES,
    worker_seconds=110, aggregate_bytes=LIMIT, group_rss_bytes=2 * 1024**3,
    log_bytes=256 * 1024, publication_allowance_seconds=2)
REFUSAL = ('unsupported: schematic class intent not qualified: schematic hierarchy dependency '
           'closure and class intent are not independently verified: ' + ROOT_SCH)

def require(value, message):
    if not value: raise p.Rejected(message)
def hashes(files): return {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
def packet(path):
    return io.inventory(path, contents=True, max_bytes=SOURCE_BYTES, max_files=40, max_entries=80)
def scalar(node, key): return fields.singleton(node, key)
def walk(tree):
    pending = [tree]
    while pending:
        row = pending.pop(); yield row
        pending.extend(child for child in row[1:] if isinstance(child, list))
def uid(tree):
    value = scalar(tree, 'uuid')
    require(fields.UUID.fullmatch(value) is not None, 'exact UUID required')
    return value

def closure(files):
    """Fixed owned-scope recipe, not a general dependency resolver."""
    require(set(n for n in files if n.casefold().endswith('.kicad_sch')) == {ROOT_SCH, CHILD_SCH},
            'exact root plus one captured leaf required')
    trees = {name: sx.parse(files[name].decode('utf8')) for name in (ROOT_SCH, CHILD_SCH)}
    for name, tree in trees.items():
        require(tree[0] == 'kicad_sch' and sx.one(tree, 'version') == ['version', '20250114'],
                'fixed original schematic schema differs: ' + name)
        require(all(not node or node[0] != 'netclass_flag' for node in walk(tree)),
                'structural schematic class directive unsupported: ' + name)
    root = trees[ROOT_SCH]; leaf = trees[CHILD_SCH]
    require(not sx.children(leaf, 'sheet'), 'nested/cyclic leaf dependency outside frozen scope')
    sheets = sx.children(root, 'sheet'); require(len(sheets) == 4, 'four root sheet instances required')
    rows = []; ids = set(); names = set()
    for sheet in sheets:
        properties = sx.children(sheet, 'property')
        def property_value(name):
            found = [row for row in properties if len(row) >= 3 and fields.atom(row[1]) == name]
            require(len(found) == 1, 'unique ' + name + ' required')
            return fields.atom(found[0][2])
        filename = property_value('Sheetfile'); name = property_value('Sheetname'); ident = uid(sheet)
        # Validate names before looking up captured bytes; never open a referenced path.
        require(filename == CHILD_SCH and Path(filename).name == filename
            and not any(token in filename for token in ('$', '%', '\\', '/', '..')),
            'external, variable, aliased or missing child filename refused')
        require(filename in files and ident not in ids and name not in names,
                'missing/duplicate child instance identity')
        ids.add(ident); names.add(name)
        rows.append(dict(name=name, uuid=ident, file=filename))
    require(names == {'CH1', 'CH2', 'CH3', 'CH4'}, 'exact four channel names required')
    return dict(root=ROOT_SCH, root_uuid=uid(root), leaf=CHILD_SCH, leaf_uuid=uid(leaf),
        files_sha256={name: hashes(files)[name] for name in trees}, instances=sorted(rows, key=lambda r: r['name']),
        repeated_leaf_instances=4, captured_file_count=2, depth=1, cycles=False,
        external_dependencies=False, structural_class_directives=False)

def closure_controls(files):
    positive = closure(files); outcomes = []
    for case in ('missing_child', 'external_child', 'variable_child', 'child_flag', 'child_cycle'):
        changed = dict(files)
        if case == 'missing_child': del changed[CHILD_SCH]
        else:
            name = ROOT_SCH if case in {'external_child', 'variable_child'} else CHILD_SCH
            tree = sx.parse(changed[name].decode())
            if case in {'external_child', 'variable_child'}:
                prop = next(row for row in sx.children(sx.children(tree, 'sheet')[0], 'property')
                            if fields.atom(row[1]) == 'Sheetfile')
                prop[2] = '"../uncaptured.kicad_sch"' if case == 'external_child' else '"${UNCAPTURED}.kicad_sch"'
            elif case == 'child_flag': tree.append(['netclass_flag', '""'])
            else: tree.append(['sheet', ['property', '"Sheetfile"', '"' + ROOT_SCH + '"']])
            changed[name] = (sx.dump(tree) + '\n').encode()
        try: closure(changed)
        except (p.Rejected, ValueError) as exc:
            outcomes.append(dict(case=case, refused=True, reason=str(exc), native_executed=False))
        else: raise p.Rejected('pure closure negative unexpectedly passed: ' + case)
    require(hashes(files) == hashes(packet(SOURCE)), 'pure controls modified original packet')
    return dict(positive=positive, negative_controls=outcomes, native_executed=False)

def refusal(board):
    try: p.preflight(board)
    except p.Rejected as exc: observed = str(exc)
    else: raise p.Rejected('production hierarchy refusal unexpectedly absent')
    require(observed == REFUSAL, 'production refusal changed; review before Native: ' + observed)
    return observed

def context(plan, pin=None):
    shared.clean(plan['git_head'])
    require(p.tool_manifest() == plan['tools'], 'fresh source/HEAD/native tool pins differ')
    require(all(p.sha(ROOT / name) == value for name, value in plan['code_sha256'].items()),
            'frozen controller/helper changed')
    require(hashes(packet(SOURCE)) == plan['source_hashes'], 'immutable complete source packet changed')
    require(hashes(packet(BASE / 'source')) == plan['source_hashes'], 'prepared source copy changed')
    require(closure(packet(SOURCE)) == plan['closure'], 'frozen closure changed')
    require(refusal(SOURCE / BOARD) == plan['production_refusal'], 'production guard changed')
    if pin is not None:
        require(p.sha(PROTOCOL) == pin and f.read_json(PROTOCOL) == plan, 'frozen prospective protocol changed')
    io.inventory(BASE, max_bytes=LIMIT, max_files=2048, max_entries=4096)

def prepare(head):
    shared.clean(head); files = packet(SOURCE); controls = closure_controls(files); denied = refusal(SOURCE / BOARD)
    tools = p.tool_manifest(); require(tools['git_head'] == head, 'intended source checkpoint differs')
    names = set(tools['implementation_sha256']) | {str(Path(__file__).relative_to(ROOT)),
        'toolchain.lock.json', 'experiments/hfe_original_native_v1/driver.py',
        'experiments/original_project_native_v1/driver.py',
        'experiments/placement_handoff_native_v1/driver.py',
        'experiments/placement_production_controls_v1/driver.py'}
    h.real_path(BASE, existing=False); BASE.mkdir(); copy_bytes(files, BASE / 'source')
    plan = dict(schema=1, kind=KIND, status='frozen_for_lead_execution', git_head=head, tools=tools,
        source_hashes=hashes(files), closure=controls['positive'], pure_controls=controls,
        production_refusal=denied, code_sha256={name: p.sha(ROOT / name) for name in sorted(names)},
        limits=LIMITS, accepted=False, routing_accepted=False, production_admitted=False,
        scope='Original complete mixer only: Native fullSCH/refill/field/netlist observations and experimental instance/terminal proof; no engine/route/support exception.')
    context(plan)
    plan['preparation_costs'] = dict(wall_seconds=time.monotonic() - START,
        full_cpu_seconds=cpu() - CPU0, publication_allowance_seconds=2)
    p.save_json(PROTOCOL, plan)
    print(f.canonical(dict(prepared=True, native_executed=False, protocol_sha256=p.sha(PROTOCOL))))

def instance_correspondence(files, netlist, board):
    """Diagnostic only. Unknown native instance schemas explicitly defer."""
    frozen = closure(files); rootid = frozen['root_uuid']; source = sx.read(board)
    trees = {name: sx.parse(files[name].decode()) for name in (ROOT_SCH, CHILD_SCH)}
    allowed = {ROOT_SCH: {()}}; allowed[CHILD_SCH] = {(row['uuid'],) for row in frozen['instances']}
    records = collections.defaultdict(list); reasons = []
    for filename, tree in trees.items():
        for symbol in sx.children(tree, 'symbol'):
            ident = uid(symbol); instances = sx.one(symbol, 'instances')
            if instances is None:
                reasons.append(dict(kind='symbol_instances_absent', file=filename, uuid=ident)); continue
            projects = sx.children(instances, 'project')
            if len(projects) != 1 or len(projects[0]) < 2 or fields.atom(projects[0][1]) != STEM:
                reasons.append(dict(kind='source_project_instance_schema', file=filename, uuid=ident)); continue
            seen_paths = set()
            for path in sx.children(projects[0], 'path'):
                if len(path) < 2: raise p.Rejected('malformed symbol instance path')
                text = fields.atom(path[1]); parts = text.split('/')
                require(parts[0] == '' and len(parts) >= 2 and parts[1] == rootid,
                        'source symbol instance is outside captured root')
                sheets = tuple(parts[2:]); require(sheets in allowed[filename], 'source symbol sheet instance differs')
                require(sheets not in seen_paths, 'duplicate source symbol instance path')
                seen_paths.add(sheets)
                ref = scalar(path, 'reference'); unit = scalar(path, 'unit')
                require(ref and unit.isdecimal() and int(unit) > 0, 'literal effective reference/unit required')
                records[ref].append(dict(file=filename, symbol_uuid=ident, sheet_uuids=list(sheets),
                    source_instance_path=text, pcb_path='/' + '/'.join([*sheets, ident]), unit=int(unit)))
            require(seen_paths == allowed[filename], 'incomplete repeated symbol instance population')
    exported = sx.parse(netlist); comps = sx.children(sx.one(exported, 'components'), 'comp')
    compmap = {scalar(comp, 'ref'): comp for comp in comps}
    require(len(compmap) == len(comps), 'duplicate native component reference')
    fps = {}; numbered = collections.defaultdict(list); _, resolve = g.source_net_identity(source)
    for fp in sx.children(source, 'footprint'):
        refs = [row for row in sx.children(fp, 'property') if fields.atom(row[1]) == 'Reference']
        require(len(refs) == 1, 'unique board footprint reference required')
        ref = fields.atom(refs[0][2]); require(ref not in fps, 'duplicate board reference')
        fps[ref] = fp
        for pad in sx.children(fp, 'pad'):
            number = fields.atom(pad[1])
            if number: numbered[(ref, number)].append(dict(uuid=uid(pad), net=resolve(sx.one(pad, 'net'))))
            elif pad[2] != 'np_thru_hole': reasons.append(dict(kind='unnumbered_conductive_pad', reference=ref, uuid=uid(pad)))
    if set(fps) != set(compmap): reasons.append(dict(kind='component_footprint_census_differs'))
    matched = []
    for ref, comp in compmap.items():
        rows = records.get(ref, []); fp = fps.get(ref)
        if not rows or fp is None:
            reasons.append(dict(kind='missing_source_instance_or_footprint', reference=ref)); continue
        sheetpath = sx.one(comp, 'sheetpath'); stamps = sx.one(comp, 'tstamps')
        # Deliberately narrow literal shape; never guess a flattened path from a label.
        try:
            native_path = scalar(sheetpath, 'tstamps')
            native_stamps = [fields.atom(value) for value in stamps[1:]]
            paths = {'/' + '/'.join([rootid, *row['sheet_uuids']]) + '/' for row in rows}
            require(len(paths) == 1 and native_path in paths, 'native/source sheet paths differ')
            require(set(native_stamps) == {row['symbol_uuid'] for row in rows}
                and len(native_stamps) == len(set(native_stamps)), 'native/source symbol UUID census differs')
            require(scalar(fp, 'path') in {row['pcb_path'] for row in rows}, 'PCB/source symbol path differs')
            matched.append(dict(reference=ref, footprint_uuid=uid(fp), instances=rows,
                                native_sheetpath=native_path, native_symbol_uuids=native_stamps))
        except (ValueError, TypeError, p.Rejected) as exc:
            reasons.append(dict(kind='instance_identity_unqualified', reference=ref, reason=str(exc)))
    for ref in set(records) - set(compmap):
        if not ref.startswith('#'):
            reasons.append(dict(kind='source_instance_absent_from_native_components', reference=ref))
    memberships = collections.defaultdict(list)
    for net in sx.children(sx.one(exported, 'nets'), 'net'):
        name = scalar(net, 'name')
        for node in sx.children(net, 'node'):
            memberships[(scalar(node, 'ref'), scalar(node, 'pin'))].append(name)
    terminals = []
    for key in sorted(set(numbered) | set(memberships)):
        pads = numbered.get(key, []); nets = memberships.get(key, [])
        okay = bool(pads and len(nets) == 1 and nets[0] and {row['net'] for row in pads} == {nets[0]})
        terminals.append(dict(reference=key[0], number=key[1], pcb_pads=pads, native_nets=nets, exact=okay))
        if not okay: reasons.append(dict(kind='terminal_membership_unqualified', reference=key[0], number=key[1]))
    return dict(experimental=True, instance_reference_footprint_exact=not reasons,
        matched_components=matched, terminals=terminals, unqualified_reasons=reasons,
        library_certification_claimed=False,
        limitation='Embedded library/source and all Native library warnings retained. No independent library certification.',
        production_admitted=False, routing_accepted=False)

def default_class_correspondence(board, text, mapping, correspondence):
    """Only actual Default-only classes over exact observed terminal partitions."""
    project = f.read_json(board.with_suffix('.kicad_pro'))
    settings = project['net_settings']; declared = settings['classes']
    require(len(declared) == 1 and declared[0]['name'] == 'Default'
        and settings.get('netclass_patterns') == []
        and settings.get('netclass_assignments') in (None, {}), 'Default-only original project required')
    require(mapping.get('source') == str(board) and mapping.get('board_saved') is False
        and mapping.get('board_sha256') == p.sha(board)
        and mapping.get('project_sha256') == p.sha(board.with_suffix('.kicad_pro')),
        'actual PCB class map/source binding differs')
    audited = nc.audit_native(mapping, project)
    require(all(row['class'] == 'Default'
        and all(parent['name'] == 'Default' for parent in row['parameter_parents'].values())
        for row in audited['nets']), 'actual PCB class/parameter parents are not all Default')
    require(not correspondence['unqualified_reasons'], 'exact instance/terminal correspondence prerequisite missing')
    native_nets = sx.children(sx.one(sx.parse(text), 'nets'), 'net')
    classes = {scalar(net, 'name'): scalar(net, 'class') for net in native_nets}
    require(len(classes) == len(native_nets) and classes and set(classes.values()) == {'Default'},
            'actual every-net schematic class must explicitly be Default; absence is unknown')
    positive = {row['name'] for row in audited['nets']}
    require(set(classes) == positive, 'schematic/PCB class net population differs')
    return dict(experimental=True, default_class_prerequisite_passed=True,
        schematic_net_classes=classes, pcb_native_class_audit=audited,
        matching_numbered_terminal_partitions=True, general_composite_or_HFE_equivalence_claimed=False,
        routing_accepted=False, production_admitted=False)

def experimental_fields(job, stage, board, raw):
    netlist, observer, standard = field_evidence.paths(job.out, stage)
    if field_evidence.has_fields(raw['violations'] + raw['unconnected_items'] + raw['schematic_parity']):
        # Job.drc already used the normal collect/readback path. Its unqualified
        # flat-only proof remains untouched beside the experimental result.
        field_evidence.readback(job.out / (stage + '.json'), raw)
        field_evidence.check_local_settings(job.out, stage, f.read_json(job.out / (stage + '-binding.json')))
    else:
        # Separate observation names avoid inventing a normal DRC field proof
        # when Native produced no field finding. Use the existing command builder.
        name = 'hierarchy-observation'; netlist, observer, _ = field_evidence.paths(job.out, name)
        argv = field_evidence.arguments(job.out, name, board)
        before = p.tree_hash(board.parent); start = len(job.steps); done = {'complete': False}
        with ls.preserve(board.with_suffix('.kicad_prl'), job.out, job._local_settings_owner,
                         cleanup_complete=lambda: done['complete']) as protection:
            try:
                for step, args in zip(field_evidence.names(name), argv): job.step(step, args)
            finally:
                done['complete'] = len(job.steps[start:]) == 2 and all(s.get('cleanup_complete') is True for s in job.steps[start:])
        require(p.tree_hash(board.parent) == before, 'extra field observation changed complete copied project')
        ls.check_preserved(board.with_suffix('.kicad_prl'), before, protection)
        for step, args in zip(field_evidence.names(name), argv):
            f.process_check(job.out, {'steps': job.steps}, step, [*f.SANDBOX, *args])
    observation = f.read_json(observer); text = io.read_bytes(netlist, 8 * 1024**2).decode()
    copied = packet(board.parent); pcb = sx.read(board)
    for name, raw_source in copied.items():
        if name.casefold().endswith('.kicad_sch'):
            field_evidence.check_source_fields(sx.parse(raw_source.decode()), pcb)
    try:
        derived = fields.derive(text, observation, raw, native_version='10.0.0')
        result = dict(experimental=True, field_prerequisite_passed=True, qualification=derived)
    except ValueError as exc:
        result = dict(experimental=True, field_prerequisite_passed=False, reason=str(exc))
    result.update(native_netlist_sha256=p.sha(netlist), native_observer_sha256=p.sha(observer),
        raw_drc_sha256=p.sha(job.out / (stage + '.json')), production_admitted=False,
        routing_accepted=False, normal_flat_bridge_unchanged=True)
    return result, text

def worker(plan, pin, available):
    context(plan, pin); CHILD.mkdir(); owner = {}; h.capture_destination(owner, CHILD)
    limit = min(106, available - 2)
    def remaining(): return min(limit - (time.monotonic() - START), limit - (cpu() - CPU0))
    job = shared.BoundJob(CHILD / 'job', max(.001, remaining()), remaining, protect_local_settings=True)
    record = dict(schema=1, kind=KIND, status='failed', observation_complete=False,
        prerequisites_passed=False, accepted=False, routing_accepted=False, qualified=False,
        production_admitted=False, engine_executed=False, tools=plan['tools'],
        protocol_sha256=pin, production_refusal=plan['production_refusal'], steps=job.steps)
    try:
        copy_bytes(packet(SOURCE), CHILD / 'original')
        copy_bytes({Path(name).name: io.read_bytes(ROOT / name, 1024**2)
                    for name in plan['tools']['implementation_sha256']}, job.out / 'code')
        copy_bytes({name: io.read_bytes(ROOT / name, 1024**2) for name in plan['code_sha256']}, CHILD / 'control-code')
        board = CHILD / 'original' / BOARD; before = p.tree_hash(board.parent)
        require(before == plan['source_hashes'], 'complete source copy differs')
        native = job.drc('original-fullsch', board, save=False, schematic_parity=True)
        inp = job.out / 'original-fullsch-input' / BOARD
        replay = f.check_drc_stage(job.out, record, 'original-fullsch', board, inp, False, before, schematic_parity=True)
        require(replay == native, 'shared actual original-rule DRC readback differs')
        raw = f.read_json(job.out / 'original-fullsch.json')
        effective, text = experimental_fields(job, 'original-fullsch', inp, raw)
        correspondence = instance_correspondence(packet(inp.parent), text, inp)
        mapping_path = job.out / 'original-netclasses.json'
        job.native('original-netclasses', 'netclasses', inp, mapping_path)
        f.process_check(job.out, record, 'original-netclasses', [*f.SANDBOX, *p.native_prefix(),
            'netclasses', str(inp), str(mapping_path)])
        mapping = f.read_json(mapping_path)
        try:
            classproof = default_class_correspondence(inp, text, mapping, correspondence)
        except (p.Rejected, ValueError, KeyError, TypeError) as exc:
            classproof = dict(experimental=True, default_class_prerequisite_passed=False,
                reason=str(exc), general_composite_or_HFE_equivalence_claimed=False,
                routing_accepted=False, production_admitted=False)
        p.save_json(CHILD / 'experimental-effective-fields.json', effective)
        p.save_json(CHILD / 'experimental-instance-terminals.json', correspondence)
        p.save_json(CHILD / 'experimental-default-classes.json', classproof)
        ls.check_normal_policy(job.out, record, max_bytes=LIMIT, max_files=2048)
        require(p.tree_hash(board.parent) == before == p.tree_hash(inp.parent), 'Native changed complete original/copy bytes')
        blockers = list(correspondence['unqualified_reasons'])
        if not effective['field_prerequisite_passed']: blockers.append(dict(kind='effective_fields', reason=effective.get('reason')))
        if not classproof['default_class_prerequisite_passed']:
            blockers.append(dict(kind='default_class_prerequisite', reason=classproof.get('reason')))
        prerequisites = not blockers
        record.update(status='diagnostic_completed', observation_complete=True, native=native,
            native_counts={key: native[key] for key in ('opens', 'blocking', 'warnings', 'exclusions')},
            expected_source_opens='Observed as original source work, never suppressed or interpreted as a routed candidate.',
            raw_report_sha256=p.sha(job.out / 'original-fullsch.json'), effective_fields=effective,
            correspondence=correspondence, remaining_blockers=blockers, decision='defer_production_admission',
            default_class_proof=classproof, prerequisites_passed=prerequisites, closure_prerequisite_passed=True,
            effective_field_prerequisite_passed=effective['field_prerequisite_passed'])
        if prerequisites: record['decision'] = 'review_narrow_default_only_hierarchy_prerequisites_for_separate_production_qualification'
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
            error=type(exc).__name__ + ': ' + str(exc), observation_complete=False)
    witness = shared.material(CHILD); record['completed_evidence'] = witness
    def stable():
        h.owned_destination(owner); context(plan, pin)
        require(shared.material(CHILD) == witness, 'completed diagnostic evidence changed')
        if record['observation_complete']:
            board = CHILD / 'original' / BOARD; inp = job.out / 'original-fullsch-input' / BOARD
            replay = f.check_drc_stage(job.out, record, 'original-fullsch', board, inp, False,
                plan['source_hashes'], schematic_parity=True)
            require(replay == record['native'], 'late original DRC readback differs')
            require(p.tree_hash(board.parent) == plan['source_hashes'] == p.tree_hash(inp.parent), 'late original source drift')
            ls.check_normal_policy(job.out, record, max_bytes=LIMIT, max_files=2048)
        require(shared.material(CHILD) == witness, 'material changed during final diagnostic readback')
    def account():
        record.update(wall_seconds=time.monotonic() - START, full_cpu_seconds=cpu() - CPU0)
        if remaining() <= 0 and record['status'] != 'cancelled': record['status'] = 'budget_exceeded'
        if record['status'] != 'diagnostic_completed':
            record['observation_complete'] = False; record['prerequisites_passed'] = False
    f.publish(CHILD, record, stable, account, remaining,
              owned=lambda: h.owned_destination(owner), final_check=stable)
    stored = f.read_json(CHILD / 'result.json')
    print(f.canonical({key: stored.get(key) for key in ('status', 'observation_complete', 'decision', 'error', 'reason')}))
    return 0 if stored.get('status') == 'diagnostic_completed' and stored.get('observation_complete') is True else 2

def execute(plan, pin):
    context(plan, pin); costs = plan['preparation_costs']
    require(costs.get('publication_allowance_seconds') == 2, 'preparation publication reserve differs')
    for key in ('wall_seconds', 'full_cpu_seconds'):
        require(type(costs[key]) in (int, float) and math.isfinite(costs[key]) and costs[key] >= 0,
                'finite nonnegative preparation costs required')
    prepwall = costs['wall_seconds'] + 2; prepcpu = costs['full_cpu_seconds'] + 2
    def remaining(): return min(118 - prepwall - (time.monotonic() - START), 118 - prepcpu - (cpu() - CPU0))
    OUTER.mkdir(); owner = {}; h.capture_destination(owner, OUTER)
    available = min(110, remaining()); require(available > 2, 'budget exhausted before Native launch')
    argv = [*f.SANDBOX, str(ROOT / '.venv/bin/python'), '-B', str(Path(__file__)), '--mode', 'worker',
        '--source-head', plan['git_head'], '--protocol-sha256', pin, '--available', str(available)]
    process = run(argv, cwd=BASE, log=OUTER / 'command.log', timeout=available,
        max_log_bytes=LIMITS['log_bytes'], max_workdir_bytes=LIMIT, max_group_rss_bytes=LIMITS['group_rss_bytes'])
    path = CHILD / 'result.json'; childpin = p.sha(path) if path.is_file() else None
    child = f.read_json(path) if childpin is not None else None
    bound = bool(child and shared.material(CHILD) == child.get('completed_evidence')
        and p.sha(path) == childpin and f.read_json(path) == child)
    completed = bool(bound and child.get('status') == 'diagnostic_completed'
        and child.get('observation_complete') is True and child.get('accepted') is False
        and child.get('routing_accepted') is False and child.get('production_admitted') is False
        and child.get('tools') == plan['tools'] and process['status'] == 'success'
        and process['exit_code'] == 0 and process.get('cleanup_complete') is True
        and process.get('log_truncated') is False)
    witness = shared.material(OUTER)
    record = dict(schema=1, kind=KIND, status='diagnostic_completed' if completed else 'failed',
        observation_complete=completed, prerequisites_passed=bool(completed and child.get('prerequisites_passed') is True), accepted=False,
        qualified=False, routing_accepted=False, production_admitted=False, engine_executed=False,
        process=process, child=child, child_receipt_sha256=childpin, child_material_bound=bound,
        completed_evidence=witness, tools=plan['tools'], protocol_sha256=pin,
        preparation_costs=costs, limits=LIMITS,
        decision=child.get('decision') if completed else 'defer_production_admission')
    if process['status'] == 'cancelled' or child and child.get('status') == 'cancelled':
        record['status'] = 'cancelled'
    def stable():
        h.owned_destination(owner); context(plan, pin)
        require(shared.material(OUTER) == witness, 'whole completed diagnostic changed')
        if child is not None:
            require(bound and p.sha(path) == childpin and f.read_json(path) == child
                and shared.material(CHILD) == child.get('completed_evidence'), 'literal child receipt/material changed')
    def account():
        record.update(wall_seconds=prepwall + time.monotonic() - START,
            full_cpu_seconds=prepcpu + cpu() - CPU0,
            invocation_wall_seconds=time.monotonic() - START, invocation_full_cpu_seconds=cpu() - CPU0)
        if remaining() <= 0 and record['status'] != 'cancelled': record['status'] = 'budget_exceeded'
        if record['status'] != 'diagnostic_completed':
            record['observation_complete'] = False; record['prerequisites_passed'] = False
    f.publish(OUTER, record, stable, account, remaining,
              owned=lambda: h.owned_destination(owner), final_check=stable)
    stored = f.read_json(OUTER / 'result.json'); print(f.canonical({key: stored.get(key) for key in
        ('status', 'observation_complete', 'wall_seconds', 'full_cpu_seconds')}))
    return 0 if stored.get('status') == 'diagnostic_completed' and stored.get('observation_complete') is True else 2

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-head', required=True)
    parser.add_argument('--mode', choices=('prepare', 'run', 'worker'), default='run')
    parser.add_argument('--protocol-sha256'); parser.add_argument('--available', type=float)
    args = parser.parse_args()
    def interrupted(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT, signal.SIGTERM): signal.signal(sig, interrupted)
    if args.mode == 'worker':
        plan = f.read_json(PROTOCOL); pin = p.sha(PROTOCOL)
        require(args.protocol_sha256 == pin and plan.get('git_head') == args.source_head
            and plan.get('kind') == KIND and plan.get('limits') == LIMITS, 'fixed worker protocol required')
        require(args.available is not None and math.isfinite(args.available) and 2 < args.available <= 110,
                'bounded parent worker availability required')
        raise SystemExit(worker(plan, pin, args.available))
    fd = os.open(ROOT / '.runs/quality-experiment.lock', os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r+') as lock:
        info = os.fstat(lock.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'ordinary shared foreground lane required')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.mode == 'prepare': prepare(args.source_head)
        else:
            plan = f.read_json(PROTOCOL); pin = p.sha(PROTOCOL)
            require(plan.get('kind') == KIND and plan.get('git_head') == args.source_head
                and plan.get('limits') == LIMITS, 'fixed reviewed protocol required')
            raise SystemExit(execute(plan, pin))
