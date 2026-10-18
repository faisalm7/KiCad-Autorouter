"""Two frozen-protocol selected7 v2 scored comparison Native controls; never admission.

Derived from the retained runtime025 invalid controller. Run the copied script
with its runtime's independent venv only after the separately frozen via_low
positive delivery is current. Caller adapter/profile/score are never receipt-derived.
The existing external runner must enforce the shared180s wall/full-CPU enclosure.
"""
import time
import resource

START = time.monotonic()


def cpu():
    return sum(x.ru_utime + x.ru_stime for x in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


CPU0 = cpu()
from decimal import Decimal
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f, handoff as h
from autorouter import comparison as cmp, review_export as ex, placement_clearance as pc, sexpr as sx
from autorouter import provenance as pv


def require(condition, message):
    if not condition: raise p.Rejected(message)


def real(value, *, existing=True):
    value = Path(value)
    require(value.is_absolute(), 'absolute qualification paths required')
    return h.real_path(value, existing=existing)


def execute(protocol_path, protocol_sha256):
    protocol_path = real(protocol_path)
    raw_protocol = pc.read_bytes(protocol_path, 1024 * 1024)
    require(hashlib.sha256(raw_protocol).hexdigest() == protocol_sha256,
            'separately frozen negative protocol hash required')
    plan = json.loads(raw_protocol)
    require(type(plan) is dict and type(plan.get('schema')) is int and plan['schema'] == 1
            and plan.get('kind') == 'comparison-v2-Native-invalid-controls-v1'
            and plan.get('whole_wall_full_cpu_seconds') == 180,
            'exact bounded negative protocol required')
    runtime = real(plan['runtime']); self_path = real(Path(__file__).absolute())
    require(runtime == ROOT and c.ROOT == runtime and Path(sys.prefix).resolve() == runtime / '.venv'
            and sys.prefix != sys.base_prefix and Path(sys.executable).absolute() == runtime / '.venv/bin/python'
            and self_path == runtime / '.runs/qualify-comparison-v2-native-invalid-001.py'
            and p.sha(self_path) == plan['helper_sha256'],
            'exact protocol-pinned copied controller/runtime and independent venv required')
    manifest = runtime / pv.MANIFEST
    tools = p.tool_manifest()
    require(c.NATIVE_VERSION == '10.0.7' and tools == plan['tools']
            and tools.get('kicad') == '10.0.7' and tools.get('git_head') == plan['source_head']
            and tools.get('source_provenance', {}).get('kind') == pv.KIND
            and tools['source_provenance'].get('native_version') == '10.0.7'
            and p.sha(manifest) == plan['runtime_manifest_sha256']
            and tools['source_provenance'].get('manifest_sha256') == plan['runtime_manifest_sha256'],
            'exact committed selected7 runtime/tools/manifest required')
    positive_protocol = real(plan['positive_protocol_path'])
    require(p.sha(positive_protocol) == plan['positive_protocol_sha256'], 'positive caller protocol changed')
    positive_plan = f.read_json(positive_protocol)
    require(cmp.POLICY == plan.get('comparison_route_policy') == 'selected-native7-fixed-comparison-v2'
            and cmp.DELIVERY_POLICY == plan.get('comparison_delivery_policy') == 'selected-native7-fixed-comparison-delivery-v2'
            and plan.get('adapter') == 'both' and plan.get('profile') == 'tuned'
            and plan.get('scoring_variant') == 'via_low', 'exact frozen v2 scored caller policy required')
    positive = runtime / '.runs/native7-comparison-v2-via-low-positive-001'
    positive_controller = runtime / '.runs/qualify-comparison-v2-delivery-001.py'
    require(positive_plan.get('kind') == 'native7-comparison-v2-functional-delivery-v1'
            and positive_plan.get('runtime') == str(runtime)
            and positive_plan.get('runtime_manifest_sha256') == plan['runtime_manifest_sha256']
            and positive_plan.get('runtime_tools') == tools and positive_plan.get('source_head') == plan['source_head']
            and p.sha(positive_controller) == positive_plan['controller_sha256']
            and positive_plan.get('case') == 'via_low_positive'
            and positive_plan.get('profile') == plan['profile'] and positive_plan.get('output') == str(positive)
            and positive_plan.get('adapter') == plan['adapter']
            and positive_plan.get('scoring_variant') == plan['scoring_variant']
            and positive_plan.get('comparison_route_policy') == plan['comparison_route_policy']
            and positive_plan.get('comparison_delivery_policy') == plan['comparison_delivery_policy']
            and positive_plan.get('route_seconds') == 120
            and positive_plan.get('board_name') == 'owned1007-transport.kicad_pcb'
            and positive_plan.get('expected_source_opens') == 2
            and positive_plan.get('expected_protected_routes') == 1
            and positive_plan.get('expected_Native_counts') == [0, 0, 0, 0]
            and positive_plan.get('fixture_sha256') == plan['source_hashes'],
            'exact separately frozen unflagged2Cu via_low positive contract required')
    # Caller authority is reconstructed only from the separately pinned plan.
    source = positive / 'source' / positive_plan['board_name']
    source_hashes = plan['source_hashes']
    require(p.tree_hash(source.parent) == source_hashes, 'frozen positive source changed')
    authority = cmp.Context(source, positive / 'route', positive_plan['profile'],
                            positive_plan['route_seconds'], tools, source_hashes,
                            adapter=plan['adapter'], scoring_variant=plan['scoring_variant'])
    ctx = dict(comparison_context=authority)
    positive_result = positive / 'result.json'
    route_path = positive / 'route/result.json'; export_path = positive / 'export/export.json'
    required_pins = ((positive_result, 'positive_result_sha256'),
                     (route_path, 'route_sha256'), (export_path, 'export_sha256'))
    for path, key in required_pins:
        require(p.sha(path) == plan[key], 'frozen positive prerequisite changed: ' + key)
    data = f.read_json(positive_result); prior = f.read_json(route_path); exported = f.read_json(export_path)
    require(data.get('passed') is True and data.get('status') == 'completed'
            and data.get('production_admitted') is False and data.get('actual_GUI') is False
            and data.get('source_head') == plan['source_head'] and data.get('tools') == tools
            and data.get('adapter') == plan['adapter'] and data.get('profile') == plan['profile']
            and data.get('scoring_variant') == plan['scoring_variant']
            and data.get('protocol_sha256') == plan['positive_protocol_sha256']
            and data.get('route_sha256') == plan['route_sha256'] and data.get('export_sha256') == plan['export_sha256'],
            'completed exact nonadmitting positive delivery required')
    with p.validation_readback_session():
        checked_route = p.check_result(route_path, **ctx); checked_export = ex.check_export(export_path, **ctx)
    require(all(row.get('current') is True and row.get('production_admitted') is False
                for row in (checked_route, checked_export)), 'current own route/export proof required')
    require(f.evidence_inventory(positive) == data.get('completed_evidence'),
            'frozen positive complete evidence differs')
    require(prior.get('source') == str(source) and prior.get('source_hashes') == source_hashes
            and prior.get('scope') == 'whole_board_unlocked_routing' and prior.get('accepted') is True
            and prior.get('adapter') == plan['adapter'] and prior.get('engine_profile') == plan['profile']
            and prior.get('scoring_variant') == plan['scoring_variant']
            and prior.get('baseline') == p.engine_baseline(plan['profile'], plan['adapter'])
            and prior.get('tools') == tools and prior.get('source_drc', {}).get('opens') == 2
            and prior.get('metrics', {}).get('copper_layers') == 2
            and all(row.get('schematic_parity') == 'checked by final native DRC' for row in (prior, exported))
            and all([row['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
                    for row in (prior, exported)), 'positive whole2Cu/full-schematic counts differ')
    require(p.check_schematic_class_support(source, class_context=None) is None,
            'only the unflagged schematic fixture is supported')
    original = p.preflight(source)
    protected = p.protected_for_record(prior, original)
    require(len(protected) == 1 and protected[0][0] == 'segment' and p.locked(protected[0]),
            'one original locked protected segment required')
    candidate = real(prior['candidate'])
    require(candidate == positive / 'route/candidate' / source.name
            and p.sha(candidate) == prior['candidate_sha256'], 'positive candidate identity changed')
    p.verify_candidate_files(candidate, source_hashes, prior['candidate_sha256'])
    positive_hashes = pc.inventory(positive, max_bytes=256 * 1024**2, max_files=8000, max_entries=16000)
    defaults = {}
    for name, call in (('route', lambda: p.check_result(route_path)),
                       ('review', lambda: h.check_delivery_context(f.read_json(positive / 'review/review.json'))),
                       ('choice', lambda: ex.bind(positive / 'choice/choice.json')),
                       ('export', lambda: ex.check_export(export_path))):
        try: call()
        except p.Rejected as exc: defaults[name] = str(exc)
        else: raise p.Rejected('default consumer admitted comparison ' + name)
    out = real(plan['output'], existing=False)
    require(out == runtime / '.runs/native7-comparison-v2-invalid-functional-001'
            and not out.exists() and out.parent.is_dir(), 'fresh exact negative output required')
    out.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, out)
    (out / 'protocol.json').write_bytes(raw_protocol)
    cases = []; stages = []
    report = dict(schema=1, kind=plan['kind'], accepted=False, routing_accepted=False,
        export_accepted=False, production_admitted=False, control_passed=False, status='failed',
        actual_GUI=False, human_review=False, Native_product_admission=False,
        runtime=str(runtime), runtime_manifest_sha256=plan['runtime_manifest_sha256'],
        source_head=plan['source_head'], tools=tools, helper_sha256=plan['helper_sha256'],
        adapter=plan['adapter'], profile=plan['profile'], scoring_variant=plan['scoring_variant'],
        comparison_route_policy=plan['comparison_route_policy'], comparison_delivery_policy=plan['comparison_delivery_policy'],
        protocol_sha256=protocol_sha256, positive_protocol_sha256=plan['positive_protocol_sha256'],
        positive_result_sha256=plan['positive_result_sha256'], route_sha256=plan['route_sha256'],
        export_sha256=plan['export_sha256'], default_refusals=defaults, cases=cases,
        whole_wall_full_cpu_budget_seconds=180,
        scope='Two owned-copy invalid controls only; full-schematic ordinary selected7 Native diagnostics and shared invariant rejection. No engine, accepted export, default/GUI promotion or physical/electrical claim.')

    def remaining():
        return min(178 - (time.monotonic() - START), 178 - (cpu() - CPU0))

    def stable():
        require(h.owned_destination(owner) == out and p.sha(self_path) == plan['helper_sha256']
                and p.sha(protocol_path) == protocol_sha256 and p.sha(out / 'protocol.json') == protocol_sha256
                and p.sha(manifest) == plan['runtime_manifest_sha256'] and p.tool_manifest() == tools
                and p.sha(positive_protocol) == plan['positive_protocol_sha256']
                and p.sha(positive_controller) == positive_plan['controller_sha256'],
                'qualification owner/controller/protocol/runtime changed')
        authority.check()
        require(pc.inventory(positive, max_bytes=256 * 1024**2, max_files=8000, max_entries=16000) == positive_hashes
                and p.tree_hash(source.parent) == source_hashes, 'positive prerequisite or original source changed')
        for name, module in tuple(sys.modules.items()):
            if name.split('.')[0] == 'autorouter' and getattr(module, '__file__', None):
                require(Path(module.__file__).resolve().is_relative_to(runtime), 'module outside given runtime: ' + name)
        require(remaining() > 0, 'whole wall/full-CPU budget exhausted')

    def new_case(label, seconds):
        stable(); require(remaining() > 20, 'insufficient Native/control publication reserve')
        directory = out / label; directory.mkdir()
        row = dict(label=label, control_observed=False, routing_accepted=False, accepted=False,
                   production_admitted=False, source=str(source), source_hashes=source_hashes,
                   protected_routes=1, before_candidate_sha256=prior['candidate_sha256'])
        cases.append(row)
        job = p.Job(directory / 'validation', min(seconds, remaining() - 10), protect_local_settings=True)
        row['steps'] = job.steps
        copied = job.out / 'candidate' / source.name
        shutil.copytree(candidate.parent, copied.parent)
        (directory / 'before-candidate.kicad_pcb').write_bytes(pc.read_bytes(copied))
        return directory, row, job, copied

    def check_native(job, name, board, before, native, *, saved=False):
        target = job.out / 'refill' / board.name if saved else job.out / (name + '-input') / board.name
        require(f.check_drc_stage(job.out, {'steps': job.steps}, name, board, target, saved, before,
                    schematic_parity=not saved, sandboxed=False) == native, 'own Native stage proof differs')
        stages.append((job, name, board, target, saved, before, native))

    def whole_short():
        directory, row, job, copied = new_case('whole-short', 100)
        bad = sx.read(copied)
        from autorouter import board_floor as g
        _, resolve = g.source_net_identity(bad)
        require(any(resolve(sx.one(pad, 'net')) == 'ROUTE' for fp in sx.children(bad, 'footprint')
                    for pad in sx.children(fp, 'pad')), 'bound ROUTE terminal required')
        segment = ['segment', ['start', '12', '10'], ['end', '12', '16'], ['width', '0.4'],
                   ['layer', '"F.Cu"'], ['net', '"ROUTE"'], ['uuid', json.dumps(str(uuid.uuid4()))]]
        segment = p.convert_route_nets(segment, ['kicad_pcb'], bad)
        require(resolve(sx.one(segment, 'net')) == 'ROUTE', 'short mutation changed net identity')
        bad.append(segment); sx.write(copied, bad)
        require(p.immutable(bad) == p.immutable(original) and all(route in p.routes(bad) for route in protected),
                'short control must preserve design and its one protected record')
        row['mutation'] = dict(added_segment=segment, pre_native_sha256=p.sha(copied))
        (directory / 'invalid-before-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        final_hash, native = p.validate_candidate(job, original, copied, source_hashes, protected,
                                                  schematic_parity=True, class_context=None)
        row.update(native=native, candidate=str(copied), candidate_sha256=final_hash,
                   native_report_sha256=p.sha(job.out / 'final-drc.json'))
        require(not p.native_accepted(native) and native['blocking'] > 0
                and 'shorting_items' in {finding['type'] for finding in native['findings']},
                'actual original-rule Native short finding required')
        before = dict(source_hashes); before[copied.name] = final_hash
        check_native(job, 'final-drc', copied, before, native)
        refill_before = dict(source_hashes); refill_before[copied.name] = row['mutation']['pre_native_sha256']
        refill_native = p.parse_report(job.out / 'refill-drc.json', copied.name)
        check_native(job, 'refill-drc', job.out / 'refill' / copied.name, refill_before, refill_native, saved=True)
        require(all(route in p.routes(sx.read(copied)) for route in protected), 'protected source copper changed')
        (directory / 'after-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        row.update(control_observed=True, rejection='actual original-rule full-schematic Native short')

    def protected_width():
        directory, row, job, copied = new_case('whole-protected-width', 60)
        chosen = protected[0]; bad = sx.read(copied)
        changed = next(route for route in p.routes(bad) if route == chosen)
        width = sx.one(changed, 'width'); old = width[1]; value = Decimal(old)
        require(value.is_finite() and value > 0, 'positive exact protected width required')
        width[1] = format(value + Decimal('0.000001'), 'f'); sx.write(copied, bad)
        restored = sx.read(copied)
        restored_route = next(route for route in p.routes(restored) if sx.one(route, 'uuid') == sx.one(chosen, 'uuid'))
        sx.one(restored_route, 'width')[1] = old
        require(restored == sx.read(candidate) and p.immutable(bad) == p.immutable(original),
                'width control must change exactly one protected width atom')
        invalid_pin = p.sha(copied)
        row['mutation'] = dict(uuid=sx.one(chosen, 'uuid')[1], before_mm=old, after_mm=width[1],
                               added_nanometres=1, pre_native_sha256=invalid_pin)
        (directory / 'invalid-before-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        native = job.drc('diagnostic-full-drc', copied, schematic_parity=True)
        row.update(native=native, candidate=str(copied), candidate_sha256=invalid_pin,
                   native_report_sha256=p.sha(job.out / 'diagnostic-full-drc.json'))
        before = dict(source_hashes); before[copied.name] = invalid_pin
        check_native(job, 'diagnostic-full-drc', copied, before, native)
        steps_before = len(job.steps)
        try:
            p.validate_candidate(job, original, copied, source_hashes, protected,
                                 schematic_parity=True, class_context=None)
        except p.Rejected as exc:
            require(str(exc) == 'protected route changed', 'unexpected protected-control refusal: ' + str(exc))
            row['rejection'] = str(exc)
        else: raise p.Rejected('protected-width mismatch was admitted')
        require(len(job.steps) == steps_before and p.sha(copied) == invalid_pin,
                'protected refusal must precede further Native normalization')
        (directory / 'after-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        row.update(control_observed=True, Native_diagnostic_routing_accepted=p.native_accepted(native),
                   no_additional_native_after_invariant_refusal=True)

    try:
        for operation in (whole_short, protected_width):
            started, cpu0, count = time.monotonic(), cpu(), len(cases)
            try: operation()
            finally:
                if len(cases) > count:
                    cases[-1].update(wall_seconds=time.monotonic()-started, full_CPU_seconds=cpu()-cpu0)
            stable()
        require(len(cases) == 2 and all(row['control_observed'] is True for row in cases), 'both own controls required')
        report.update(control_passed=True, status='completed')
    except (Exception, KeyboardInterrupt) as exc:
        report.update(control_passed=False, status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      error=type(exc).__name__ + ': ' + str(exc))
    report['evidence_sha256'] = f.evidence_inventory(out)

    def final_check():
        stable()
        require(f.evidence_inventory(out) == report['evidence_sha256'], 'completed negative evidence changed')
        with p.validation_readback_session():
            require(p.check_result(route_path, **ctx).get('current') is True
                    and ex.check_export(export_path, **ctx).get('current') is True, 'positive prerequisite stale at publication')
        require(pc.inventory(positive, max_bytes=256 * 1024**2, max_files=8000, max_entries=16000) == positive_hashes,
                'positive prerequisite bytes changed at publication')
        require(f.evidence_inventory(out) == report['evidence_sha256'], 'negative bytes changed during central readback')
        # Existing stage readers finish process/PRL metadata replay after the
        # last caller/tool-bearing central check. No new Native run occurs here.
        for job, name, board, target, saved, before, native in stages:
            require(f.check_drc_stage(job.out, {'steps': job.steps}, name, board, target, saved, before,
                        schematic_parity=not saved, sandboxed=False) == native, 'final Native stage changed')

    def account():
        report.update(sampled_wall_seconds=time.monotonic()-START, sampled_full_CPU_seconds=cpu()-CPU0,
                      publication_allowance_seconds=2, external_exit_required=True)
        if remaining() <= 0: report.update(control_passed=False, status='budget_exceeded')
        if report['status'] != 'completed': report['control_passed'] = False

    f.publish(out, report, stable, account, remaining, owned=lambda: h.owned_destination(owner), final_check=final_check)
    print(json.dumps({key: report.get(key) for key in ('control_passed', 'status', 'error', 'reason',
                                                       'sampled_wall_seconds', 'sampled_full_CPU_seconds')}))
    return 0 if report['control_passed'] and report['status'] == 'completed' else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    args = parser.parse_args()
    raise SystemExit(execute(args.protocol, args.protocol_sha256))
