"""Unshipped single exposed STM diagnostic, never a product routing receipt.

External complete-exit wall/fullCPU supervision is mandatory. No retry, warning
acknowledgement, solver injection, baseline rerun or old-result relabelling.
"""
from pathlib import Path
import argparse, hashlib, json, os, resource, signal, sys, time

ENTRY_WALL = time.monotonic()
ENTRY_CPU = time.process_time() + sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2])
ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / '.runs/runtime074 fresh install 001'
MANIFEST = '584ee929eaf3d277dc535556e42c71ac5196a74f1c5e3fd53a2cce5a67853d61'
BUILD = '6fbbbf22dfb8250f1578fb4d7a45ff0e161b3194'
STUDY = ROOT / '.runs/protected-gap-runtime074-comparison-001'
POPULATION = 'a04314302bd8b3963750fddb852dea1d6286d252c94a163cdb1f8689f38a9f3e'
CHILDREN = '09a49117e6cbac0c5a32c94cdc42cad681ba797aa4427ffc56bbcf61ac62a421'
PRIOR_CHILD = 'c9ad442a716966494f22dec083d6a55b3d7cad7a25186d52d1d75f607acbeb6c'
PRIOR_ROUTE = '5edc2332ec4d933782039f4fc628d510b05579f4d0dd18ddfd0bd82543656a7b'
PRIOR_TIME = 'bc4a7ccd997af0fecd9239bd4f8569d13fa9c3123ca96f749bc0d621f99342f0'
KIND = 'native-open-repair-research-v1'
LIMITS = dict(complete_wall_cpu_seconds=300, warm_start_wall_seconds=21.38,
    warm_start_cpu_seconds=23.33, external_new_wall_cpu_seconds=276,
    routing_seconds=90, export_seconds=90, original_validation_seconds=45,
    complete_exit_reserve_seconds=10,
    cli_stage_max_seconds=dict(preview=15, route=105, review=30, choice=20,
                               export=105, verify_export=30))


def installed_api():
    if any(n == 'autorouter' or n.startswith('autorouter.') for n in sys.modules):
        raise RuntimeError('fresh installed-only process required')
    if (any(x.is_symlink() for x in (RUNTIME, *RUNTIME.parents))
            or Path(sys.prefix).absolute() != RUNTIME / '.venv'):
        raise RuntimeError('exact canonical installed074 interpreter required')
    sys.path.insert(0, str(RUNTIME)); sys.path.insert(1, str(ROOT)); sys.dont_write_bytecode = True
    from autorouter import pipeline as p, floor_route as f, handoff as h, placement_clearance as pc
    from autorouter import provenance as pv, sexpr as sx, gui, preferences as pref, config as c
    from autorouter import routing_scope as rs, placement_strategy as ps, local_settings
    for name, module in tuple(sys.modules.items()):
        if name == 'autorouter' or name.startswith('autorouter.'):
            if RUNTIME / 'autorouter' not in Path(module.__file__).absolute().parents:
                raise RuntimeError('mixed source/installed authority')
    if c.ROOT != RUNTIME or c.NATIVE_VERSION != '10.0.7' or p.sha(RUNTIME / pv.MANIFEST) != MANIFEST:
        raise RuntimeError('actual installed074 identity differs')
    pins = pv._file_map(f.read_json(RUNTIME / pv.MANIFEST)['immutable_files_sha256'])
    if len(pins) != 54 or any(p.sha(RUNTIME / n) != v for n, v in pins.items()):
        raise RuntimeError('installed curated54 changed')
    return p, f, h, pc, pv, sx, gui, pref, rs, ps, local_settings, pins


def experiment(protocol_name, protocol_pin):
    p, f, h, pc, pv, sx, gui, pref, rs, ps, local_settings, pins = installed_api()
    from experiments.native_open_repair_v1 import selection
    from scripts.backup import require_headroom
    need = lambda ok, message: None if ok else (_ for _ in ()).throw(p.Rejected(message))
    need(Path(selection.__file__).resolve() == Path(__file__).with_name('selection.py'), 'selector path differs')
    remaining = lambda: max(0, min(300 - 21.38 - (time.monotonic() - ENTRY_WALL),
                                  300 - 23.33 - (h.cpu_seconds() - ENTRY_CPU)))
    protocol = h.real_path(protocol_name)
    need(protocol.parent == ROOT / '.runs', 'exact .runs-root protocol required')
    raw = pc.read_bytes(protocol, 1024**2)
    need(hashlib.sha256(raw).hexdigest() == protocol_pin, 'prospective protocol SHA differs')
    spec = f.read_json(protocol)
    need(set(spec) == {'schema', 'kind', 'administration_head', 'driver_sha256', 'selection_sha256', 'limits', 'output', 'external_complete_exit_required'}
         and type(spec['schema']) is int and spec['schema'] == 1 and spec['kind'] == KIND
         and spec['limits'] == LIMITS and spec['external_complete_exit_required'] is True,
         'exact reviewed single-case protocol required')
    def code_current():
        need(pv._git(ROOT, 'rev-parse', 'HEAD').decode().strip() == spec['administration_head'], 'research HEAD changed')
        for name, key in [('driver.py', 'driver_sha256'), ('selection.py', 'selection_sha256')]:
            path = Path(__file__).with_name(name); data = pc.read_bytes(path)
            need(hashlib.sha256(data).hexdigest() == spec[key]
                 and pv._git(ROOT, 'show', spec['administration_head'] + ':' + path.relative_to(ROOT).as_posix()) == data,
                 'commit exact reviewed research code before Native')
        need(p.sha(protocol) == protocol_pin and all(p.sha(RUNTIME / n) == v for n, v in pins.items()), 'protocol/runtime changed')
    code_current()
    need(p.sha(STUDY / 'population.json') == POPULATION and p.sha(STUDY / 'frozen-children.json') == CHILDREN, 'frozen study changed')
    item = f.read_json(STUDY / 'frozen-children.json')['protocols']['stm32']['Cdefault']
    old_protocol = h.real_path(item['path']); need(p.sha(old_protocol) == item['sha256'], 'old protocol changed')
    plan = f.read_json(old_protocol); old_child = h.real_path(plan['output']) / 'result.json'
    need(p.sha(old_child) == PRIOR_CHILD and p.sha(old_protocol.parent / 'outer-time.log') == PRIOR_TIME, 'captured child/debit changed')
    child = f.read_json(old_child); prior = h.real_path(child['selected_route_receipt'])
    need(p.sha(prior) == PRIOR_ROUTE == child['selected_route_sha256'], 'captured negative changed')
    replay = lambda: p.check_rejected_routing_attempt(prior, ordinary_profile='standard')
    replay(); old = f.read_json(prior); original_source = h.real_path(plan['source']); hashes = plan['source_hashes']
    need(plan['source_head'] == BUILD and plan['runtime'] == str(RUNTIME) and plan['runtime_manifest_sha256'] == MANIFEST
         and old['source'] == str(original_source) and old['source_hashes'] == hashes
         and old['engine_profile'] == 'standard' and old['adapter'] == 'both'
         and old['scope'] == 'whole_board_unlocked_routing' and old['accepted'] is False,
         'exact captured ordinary Default negative required')
    warm = h.real_path(old['candidate']); warm_raw = pc.read_bytes(warm)
    witness = selection.derive(warm_raw, old['native'], candidate_sha256=old['candidate_sha256'], report_sha256=p.sha(prior.parent / 'final-drc.json'))
    names = witness['names']; original = p.preflight(original_source, task_scope=('whole_board_unlocked_routing', 'native', 'source_all'))
    warm_tree = sx.parse(warm_raw.decode()); original_protected = p.routes(p.routing_task(original, 'whole_board_unlocked_routing'))
    need(p.immutable(warm_tree) == p.immutable(original) and all(r in p.routes(warm_tree) for r in original_protected), 'original immutable/protected geometry differs')
    p.require_native_scope(scope='selected_nets', guidance='native', layers='source_all', profile='completion-only', adapter='both', scoring=None)
    p.check_native7_selected_source(warm, names); p.preflight(warm, task_scope=('selected_nets', 'native', 'source_all'))
    settings = pref.validate(dict(pref.DEFAULTS, seconds=90, scope='selected_nets', profile='completion-only', adapter='both', guidance='native', layers='source_all', scoring_preference=None, nets=names))
    need(gui.export_validation_seconds(90) == 90, 'public export allocation changed')
    prior_inventory = pc.evidence_inventory(prior.parent); tools = p.tool_manifest()
    warm_hashes = dict(hashes); warm_hashes[original_source.name] = old['candidate_sha256']
    need(p.tree_hash(warm.parent) == warm_hashes, 'candidate sidecars differ from original')
    output = h.real_path(spec['output'], existing=False)
    need(output.parent == ROOT / '.runs' and output.name.startswith('native-open-repair074-')
         and not os.path.lexists(output), 'fresh normal research namespace required')
    measured = sum(len(x) for x in pc.inventory(original_source.parent, contents=True).values())
    space = require_headroom(output.parent, 32 * measured + 512 * 1024**2, 'one Native-open repair diagnostic')
    p.check_storage(active_root=output); output.mkdir(); owner = {}; h.capture_destination(owner, output)
    flow = None; cli = None; job = None; final_hash = None; validation_start = None; child_inventory = None
    rec = dict(schema=1, kind=KIND, status='running', accepted=False, production_admitted=False,
        product_scope_admitted=False, candidate_native_valid=False, cleanup_complete=False, limits=LIMITS,
        protocol_sha256=protocol_pin, source=str(original_source), source_hashes=hashes, tools=tools,
        prior_route=str(prior), prior_route_sha256=PRIOR_ROUTE, prior_child_sha256=PRIOR_CHILD,
        prior_complete_time_log_sha256=PRIOR_TIME, selection=witness, software_test_intent=True,
        human_PCB_approval=False, cli_processes=[], space_plan=space,
        accounting_caveat='One exposed warm-start diagnostic; not a fresh fair comparison, product delivery or electrical approval. External complete exit and cleanup remain mandatory.')
    def stable():
        h.owned_destination(owner); code_current(); need(remaining() > 0, 'charged whole wall/fullCPU budget exhausted')
        need(p.tool_manifest() == tools and p.tree_hash(original_source.parent) == hashes
             and pc.evidence_inventory(prior.parent) == prior_inventory and p.sha(old_child) == PRIOR_CHILD
             and p.sha(old_protocol) == item['sha256'], 'original/tools/captured prior changed')
        if flow is not None: flow.fresh()
        if child_inventory is not None: need(pc.evidence_inventory(flow.workspace) == child_inventory, 'completed own selected proof changed')
        if (output / 'source').exists(): need(p.tree_hash(output / 'source') == warm_hashes, 'disposable warm source changed')
        if job is not None: need(p.tree_hash(job.out / 'snapshot') == hashes, 'original snapshot changed')
    def selected_audit(candidate):
        need(p.immutable(sx.read(candidate)) == p.immutable(original), 'original immutable geometry changed')
        audit = rs.audit(warm_tree, sx.read(candidate), names)
        need(audit['protected_count'] == len(p.routes(warm_tree))
             and all(r in p.routes(sx.read(candidate)) for r in original_protected), 'complete original/warm protection failed')
        return audit
    def readback():
        stable()
        if final_hash is None: return
        data = dict(steps=job.steps); candidate = job.out / 'candidate' / original_source.name
        preimage = job.out / 'pre-refill.kicad_pcb'; before = dict(hashes); before[original_source.name] = p.sha(preimage)
        saved = job.out / 'refill' / original_source.name
        f.check_drc_stage(job.out, data, 'refill-drc', saved, saved, True, before)
        after = dict(hashes); after[original_source.name] = final_hash
        native = f.check_drc_stage(job.out, data, 'final-drc', candidate, job.out / 'final-drc-input' / original_source.name, False, after, schematic_parity=True)
        need(native == rec['native'] and p.sha(job.out / 'final-drc.json') == rec['native_report_sha256'], 'own final Native/hash differs')
        need(pc.read_bytes(candidate) == (sx.dump(p.transplant_fill(sx.read(preimage), sx.read(saved))) + '\n').encode(), 'own refill reconstruction differs')
        p.verify_candidate_files(candidate, hashes, final_hash); selected_audit(candidate)
        p.check_final_netclass_evidence(job.out, data, candidate, original_protected, default_target_policy=True, sandboxed=True,
            default_target_basis=f.read_json(flow.workspace / 'route/default-targets.json'))
        p.check_legacy_zone_evidence(job.out, original, candidate, implementation=tools['implementation_sha256'])
        need(local_settings.check_normal_policy(job.out, dict(rec, steps=job.steps), max_bytes=100 * 1024**2, max_files=4000) == [], 'outer validation must have zero import/export census')
        need(p.native_accepted(native) and native['ignored_checks'] == flow.records['export']['native']['ignored_checks'] == old['native']['ignored_checks']
             and ps.warnings(native) <= ps.warnings(flow.records['export']['native']), 'strict final Native/warning/original-ignore checks refused')
        stable(); need(validation_remaining() > 0, 'original validation/readback budget exhausted')
    def account():
        wall = time.monotonic() - ENTRY_WALL; cpu = h.cpu_seconds() - ENTRY_CPU
        rec.update(new_wall_seconds=wall, new_full_cpu_seconds=cpu, charged_wall_seconds=wall + 21.38,
            charged_full_cpu_seconds=cpu + 23.33, within_budget=remaining() > 0,
            steps=[] if job is None else job.steps, accepted=False, production_admitted=False, product_scope_admitted=False,
            child_timings_are_prepublication=True,
            local_children_reaped=(cli is None or cli.process is None or cli.process.poll() is not None)
                and (job is None or all(s.get('cleanup_complete') is True for s in job.steps)),
            cleanup_complete=False, external_complete_exit_and_cleanup_required=True)
        if rec['status'] != 'completed' or not rec['within_budget']: rec['candidate_native_valid'] = False
    def interrupted(signum, frame):
        if cli is not None: cli.cancel()
        raise KeyboardInterrupt
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for sig in handlers: signal.signal(sig, interrupted)
        pc.copy_project(warm.parent, output / 'source'); (output / 'jobs').mkdir()
        flow = gui.Request(str(output / 'source' / warm.name), str(output / 'jobs'), json.dumps(settings), True, 'route').prepare()
        cli = gui.CliJob()
        for stage in ('preview', 'route', 'review', 'choice', 'export', 'verify_export'):
            stable(); allowance = min(LIMITS['cli_stage_max_seconds'][stage], remaining() - 55)
            need(allowance > 0, 'no CLI allowance after original-validation/complete-exit reserves')
            choice = 'accept' if stage == 'choice' else None; log = output / (stage + '.log')
            process = cli.run(flow.command(stage, choice=choice), log, timeout=allowance)
            rec['cli_processes'].append(dict(stage=stage, process=process, log=str(log), log_sha256=p.sha(log)))
            cli.adopt(flow, stage, process, log, choice=choice); stable()
            if stage in ('route', 'export'):
                item_candidate = Path(flow.records[stage]['candidate']); selected_audit(item_candidate)
        exported = Path(flow.records['export']['candidate']); export_pin = p.sha(exported)
        need(export_pin == flow.records['export']['candidate_sha256'], 'own fresh exported hash differs')
        child_inventory = pc.evidence_inventory(flow.workspace)
        rec.update(selected_route=str(flow.workspace / 'route/result.json'), selected_route_sha256=p.sha(flow.workspace / 'route/result.json'),
            selected_export=str(flow.workspace / 'export/export.json'), selected_export_sha256=p.sha(flow.workspace / 'export/export.json'),
            selected_export_candidate_sha256=export_pin, selected_evidence_files_sha256=child_inventory)
        stable(); validation_start = time.monotonic(); validation_cpu = h.cpu_seconds()
        validation_remaining = lambda: max(0, min(45 - (time.monotonic() - validation_start), 45 - (h.cpu_seconds() - validation_cpu), remaining() - 10))
        need(validation_remaining() > 0, 'original-shell validation reserve exhausted')
        job = f.FloorJob(output / 'original-validation', 45, validation_remaining, protect_local_settings=True)
        for directory in ('snapshot', 'candidate'): pc.copy_project(original_source.parent, job.out / directory)
        (job.out / 'code').mkdir()
        for name, pin in tools['implementation_sha256'].items():
            data = pc.read_bytes(RUNTIME / name); need(hashlib.sha256(data).hexdigest() == pin, 'installed validation code differs')
            (job.out / 'code' / Path(name).name).write_bytes(data)
        candidate = job.out / 'candidate' / original_source.name
        shell = p.transplant_routes(original, sx.read(exported), protected=original_protected, policy=p.normal_strict_import_policy(original, original_protected))
        sx.write(candidate, p.transplant_fill(shell, sx.read(exported))); selected_audit(candidate)
        final_hash, native = p.validate_candidate(job, original, candidate, hashes, original_protected, schematic_parity=True, default_target_policy=True)
        rec.update(candidate=str(candidate), candidate_sha256=final_hash, native=native, native_report_sha256=p.sha(job.out / 'final-drc.json'),
            status='completed', candidate_native_valid=p.native_accepted(native), selected_net_audit=selected_audit(candidate),
            original_validation_wall_seconds=time.monotonic() - validation_start, original_validation_full_cpu_seconds=h.cpu_seconds() - validation_cpu)
    except (Exception, KeyboardInterrupt) as exc:
        rec.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed', error=type(exc).__name__ + ': ' + str(exc), candidate_native_valid=False)
    # Keep original handlers through publication; cancellation cannot escape it.
    try:
        return f.publish(output, rec, stable, account, remaining, owned=lambda: h.owned_destination(owner), final_check=readback)
    finally:
        for sig, handler in handlers.items(): signal.signal(sig, handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True); parser.add_argument('--protocol-sha256', required=True)
    parser.add_argument('--run-native', action='store_true'); args = parser.parse_args()
    if not args.run_native: parser.error('explicit reviewed --run-native required; existence is not qualification')
    result = experiment(args.protocol, args.protocol_sha256)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result['status'] == 'completed' and result['candidate_native_valid'] else 2)
