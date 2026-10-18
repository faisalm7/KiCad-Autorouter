"""Two prospective selected1007 Native negatives; never a routing admission.

Run only after both ordinary025 delivery prerequisites are complete/current.
An external existing runner must also enforce the180s wall/full-CPU enclosure.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import resource
import shutil
import sys
import time
import uuid

START = time.monotonic()
def cpu():
    return sum(x.ru_utime + x.ru_stime for x in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
parser = argparse.ArgumentParser(description=__doc__)
for name in ('runtime', 'whole-delivery', 'partial-delivery', 'output'):
    parser.add_argument('--' + name, type=Path, required=True)
args = parser.parse_args()
if not args.runtime.is_absolute(): raise ValueError('absolute runtime required')
sys.path.insert(0, str(args.runtime)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f, handoff as h
from autorouter import review_export as ex, placement_clearance as pc, sexpr as sx
from autorouter import schematic_class_evidence as classes, provenance as pv


def require(condition, message):
    if not condition: raise p.Rejected(message)


def real(value, *, existing=True):
    require(value.is_absolute(), 'absolute qualification paths required')
    return h.real_path(value, existing=existing)


runtime = real(args.runtime)
require(c.ROOT == runtime and Path(sys.prefix).resolve() == runtime / '.venv'
        and Path(sys.executable).absolute() == runtime / '.venv/bin/python',
        'exact given runtime and its independent venv required')
require(c.NATIVE_VERSION == '10.0.7', 'ordinary selected1007 runtime required')
out = real(args.output, existing=False)
require(not out.exists() and out.parent.is_dir(), 'fresh output beneath an existing directory required')
out.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, out)
self_path = Path(__file__).resolve(); self_pin = p.sha(self_path)
checkout = self_path.parents[1]
expected_sources = {
    'whole': checkout / '.runs/runtime-directory-019/source-matching/owned-four-copper-forced-inner.kicad_pcb',
    'partial': checkout / '.runs/runtime-directory-023/runtime/.runs/gui-session070/project/owned1007-transport.kicad_pcb',
}
tools = p.tool_manifest(); manifest = runtime / pv.MANIFEST; manifest_pin = p.sha(manifest)
require(tools['source_provenance']['kind'] == pv.KIND and tools['kicad'] == '10.0.7',
        'curated ordinary selected1007 provenance required')
positives = {}; cases = []; protocol_pin = None
report = dict(schema=1, kind='runtime025-owned-Native-negative-controls-v1',
              accepted=False, routing_accepted=False, export_accepted=False,
              control_passed=False, status='failed', project_complete=False,
              actual_GUI=False, human_review=False, Native_product_admission=False,
              runtime=str(runtime), runtime_manifest_sha256=manifest_pin, tools=tools,
              helper_sha256=self_pin, cases=cases, whole_wall_full_cpu_budget_seconds=180,
              scope='Owned invalid candidates only. Fresh original-rule full-schematic Native diagnostics and shared rejection guards; no engine, accepted export, platform breadth or human/electrical claim.')


def remaining():
    return min(178 - (time.monotonic() - START), 178 - (cpu() - CPU0))


def stable():
    require(h.owned_destination(owner) == out and p.sha(self_path) == self_pin
            and p.sha(manifest) == manifest_pin and p.tool_manifest() == tools,
            'qualification owner/helper/runtime changed')
    for name, module in tuple(sys.modules.items()):
        if name.split('.')[0] == 'autorouter' and getattr(module, '__file__', None):
            require(Path(module.__file__).resolve().is_relative_to(runtime), 'module outside given runtime: ' + name)
    for item in positives.values():
        require(pc.inventory(item['delivery'], max_bytes=256 * 1024**2, max_files=8000,
                             max_entries=16000) == item['delivery_hashes']
                and p.tree_hash(item['source'].parent) == item['source_hashes'],
                'positive prerequisite or original source changed')
    if protocol_pin is not None:
        require(p.sha(out / 'protocol.json') == protocol_pin, 'frozen protocol changed')
    require(remaining() > 0, 'whole wall/full-CPU budget exhausted')


def prerequisite(label, location, protected_count, scope):
    location = real(location)
    receipt = location / 'result.json' if location.is_dir() else location
    require(receipt.name == 'result.json', 'delivery qualifier result.json required')
    delivery = receipt.parent; data = f.read_json(receipt)
    require(data.get('workflow_delivered') is True and data.get('status') == 'completed'
            and data.get('actual_GUI') is False and data.get('tools') == tools,
            'completed current ordinary installed delivery prerequisite required: ' + label)
    workspace = real(Path(data['workspace']))
    require(workspace.is_relative_to(delivery), 'positive workflow workspace escaped delivery')
    route_path = workspace / 'route/result.json'; export_path = workspace / 'export/export.json'
    with p.validation_readback_session():
        route_check = p.check_result(route_path); export_check = ex.check_export(export_path)
    require(route_check.get('current') is True and export_check.get('current') is True,
            'positive final route/export readbacks required')
    prior = f.read_json(route_path); source = real(Path(prior['source']))
    require(source == expected_sources[label] and prior.get('scope') == scope
            and prior.get('accepted') is True and prior.get('tools') == tools
            and data.get('route_receipt_sha256') == p.sha(route_path),
            'positive source/scope/tool/receipt identity differs')
    source_hashes = p.tree_hash(source.parent)
    require(source_hashes == prior['source_hashes'] == data['source_hashes']
            and source.with_suffix('.kicad_sch').name in source_hashes
            and prior.get('schematic_parity') == 'checked by final native DRC',
            'complete unchanged original schematic/project required')
    original = sx.read(source); protected = p.protected_for_record(prior, original)
    require(len(protected) == protected_count, 'unexpected protected population: ' + label)
    candidate = real(Path(prior['candidate']))
    require(p.sha(candidate) == prior['candidate_sha256'], 'accepted prerequisite candidate changed')
    p.verify_candidate_files(candidate, source_hashes, prior['candidate_sha256'])
    item = dict(delivery=delivery, delivery_hashes=pc.inventory(delivery, max_bytes=256 * 1024**2,
                max_files=8000, max_entries=16000), receipt_sha256=p.sha(receipt),
                route_receipt=str(route_path), route_receipt_sha256=p.sha(route_path),
                export_receipt=str(export_path), export_receipt_sha256=p.sha(export_path),
                source=source, source_hashes=source_hashes, original=original,
                protected=protected, candidate=candidate, candidate_sha256=prior['candidate_sha256'])
    positives[label] = item
    return item


def new_case(label, item, seconds):
    stable(); require(remaining() > 20, 'insufficient remaining Native/control publication reserve')
    directory = out / label; directory.mkdir()
    row = dict(label=label, control_observed=False, routing_accepted=False,
               protected_routes=len(item['protected']), source=str(item['source']),
               source_hashes=item['source_hashes'], before_candidate_sha256=item['candidate_sha256'])
    cases.append(row)
    job = p.Job(directory / 'validation', min(seconds, remaining() - 10), protect_local_settings=True)
    row['steps'] = job.steps
    candidate = job.out / 'candidate' / item['source'].name
    shutil.copytree(item['candidate'].parent, candidate.parent)
    (directory / 'before-candidate.kicad_pcb').write_bytes(pc.read_bytes(candidate))
    return directory, row, job, candidate


def check_native(job, name, source, before, *, saved=False):
    target = job.out / 'refill' / source.name if saved else job.out / (name + '-input') / source.name
    return f.check_drc_stage(job.out, {'steps': job.steps}, name, source, target, saved, before,
                             schematic_parity=not saved, sandboxed=False)


def whole_short(item):
    started, cpu0 = time.monotonic(), cpu(); directory, row, job, candidate = new_case('whole-short', item, 100)
    bad = sx.read(candidate)
    require(any(sx.one(pad, 'net') == ['net', '"ROUTE"'] for fp in sx.children(bad, 'footprint')
                for pad in sx.children(fp, 'pad')), 'literal modern ROUTE net required')
    segment = ['segment', ['start', '12', '10'], ['end', '12', '16'], ['width', '0.4'],
               ['layer', '"F.Cu"'], ['net', '"ROUTE"'], ['uuid', json.dumps(str(uuid.uuid4()))]]
    bad.append(segment); sx.write(candidate, bad)
    require(p.immutable(bad) == p.immutable(item['original'])
            and all(route in p.routes(bad) for route in item['protected']),
            'short control must preserve nonrouting design and all10 protected records')
    row['mutation'] = dict(added_segment=segment, pre_native_sha256=p.sha(candidate))
    (directory / 'invalid-before-native.kicad_pcb').write_bytes(pc.read_bytes(candidate))
    final_hash, native = p.validate_candidate(job, item['original'], candidate, item['source_hashes'],
        item['protected'], class_context=classes.CONTEXT, schematic_parity=True)
    row.update(native=native, candidate=str(candidate), candidate_sha256=final_hash,
               native_report_sha256=p.sha(job.out / 'final-drc.json'))
    kinds = {finding['type'] for finding in native['findings']}
    require(not p.native_accepted(native) and native['blocking'] > 0
            and 'shorting_items' in kinds, 'actual Native short finding required')
    before = dict(item['source_hashes']); before[candidate.name] = final_hash
    require(check_native(job, 'final-drc', candidate, before) == native, 'full-schematic final proof differs')
    refill_before = dict(item['source_hashes']); refill_before[candidate.name] = row['mutation']['pre_native_sha256']
    check_native(job, 'refill-drc', job.out / 'refill' / candidate.name, refill_before, saved=True)
    class_data = dict(steps=job.steps, source_hashes=item['source_hashes'], schematic_class_final=job.schematic_class_final)
    proof = classes.check(job.out, class_data, 'final', board_raw=pc.read_bytes(candidate), source=str(candidate),
        project_raw=pc.read_bytes(candidate.with_suffix('.kicad_pro')),
        schematic_raw=pc.read_bytes(candidate.with_suffix('.kicad_sch')), native_map=job.out / 'final-netclasses.json')
    require(proof['qualification']['class_parity_qualified'] is True, 'original class proof must remain valid')
    require(all(route in p.routes(sx.read(candidate)) for route in item['protected']), 'protected source copper changed')
    (directory / 'after-native.kicad_pcb').write_bytes(pc.read_bytes(candidate))
    row.update(control_observed=True, class_parity_qualified=True,
               rejection='actual original-rule full-schematic Native short',
               wall_seconds=time.monotonic()-started, full_CPU_seconds=cpu()-cpu0)


def partial_protected_width(item):
    started, cpu0 = time.monotonic(), cpu(); directory, row, job, candidate = new_case('partial-protected-width', item, 60)
    bad = sx.read(candidate); segments = [route for route in item['protected'] if route[0] == 'segment']
    require(len(item['protected']) == len(p.routes(item['original'])) == 4 and segments,
            'partial fixture must preserve every one of its4 original route records')
    chosen = sorted(segments, key=lambda route: sx.one(route, 'uuid')[1])[0]
    changed = next(route for route in p.routes(bad) if route == chosen)
    width = sx.one(changed, 'width'); old = width[1]; value = Decimal(old)
    require(value.is_finite() and value > 0, 'positive exact protected segment width required')
    width[1] = format(value + Decimal('0.000001'), 'f'); sx.write(candidate, bad)
    restored = sx.read(candidate); restored_route = next(route for route in p.routes(restored)
        if sx.one(route, 'uuid') == sx.one(chosen, 'uuid')); sx.one(restored_route, 'width')[1] = old
    require(restored == sx.read(item['candidate']) and p.immutable(bad) == p.immutable(item['original']),
            'width control must change exactly one protected width atom')
    invalid_pin = p.sha(candidate)
    row['mutation'] = dict(uuid=sx.one(chosen, 'uuid')[1], before_mm=old, after_mm=width[1],
                           added_nanometres=1, pre_native_sha256=invalid_pin)
    (directory / 'invalid-before-native.kicad_pcb').write_bytes(pc.read_bytes(candidate))
    native = job.drc('diagnostic-full-drc', candidate, schematic_parity=True)
    row.update(native=native, candidate=str(candidate), candidate_sha256=invalid_pin,
               native_report_sha256=p.sha(job.out / 'diagnostic-full-drc.json'))
    before = dict(item['source_hashes']); before[candidate.name] = invalid_pin
    require(check_native(job, 'diagnostic-full-drc', candidate, before) == native
            and p.sha(candidate) == invalid_pin, 'own diagnostic Native proof/candidate changed')
    steps_before = len(job.steps)
    try:
        p.validate_candidate(job, item['original'], candidate, item['source_hashes'], item['protected'],
                             class_context=classes.CONTEXT, schematic_parity=True)
    except p.Rejected as error:
        require(str(error) == 'protected route changed', 'unexpected protected-control refusal: ' + str(error))
        row['rejection'] = str(error)
    else:
        raise p.Rejected('protected-width mismatch was admitted')
    require(len(job.steps) == steps_before and p.sha(candidate) == invalid_pin,
            'protected rejection must precede any further Native normalization')
    (directory / 'after-native.kicad_pcb').write_bytes(pc.read_bytes(candidate))
    row.update(control_observed=True, Native_diagnostic_routing_accepted=p.native_accepted(native),
               wall_seconds=time.monotonic()-started, full_CPU_seconds=cpu()-cpu0)


def run_case(operation, item):
    started, cpu0, count = time.monotonic(), cpu(), len(cases)
    try:
        operation(item)
    finally:
        if len(cases) > count:
            cases[-1].update(wall_seconds=time.monotonic()-started, full_CPU_seconds=cpu()-cpu0)


try:
    whole = prerequisite('whole', args.whole_delivery, 10, 'whole_board_unlocked_routing')
    partial = prerequisite('partial', args.partial_delivery, 4, 'partial_completion')
    protocol = dict(schema=1, helper_sha256=self_pin, runtime=str(runtime), tools=tools,
        runtime_manifest_sha256=manifest_pin, whole_wall_full_cpu_seconds=180,
        positives={label: {key: str(value) if isinstance(value, Path) else value for key, value in item.items()
                   if key not in {'original', 'protected'}} for label, item in positives.items()},
        mutations=['one new ROUTE segment12,10→12,16 F.Cu width0.4 with fresh UUID',
                   'one original protected partial segment width+0.000001mm; all other AST nodes unchanged'])
    p.save_json(out / 'protocol.json', protocol); protocol_pin = p.sha(out / 'protocol.json')
    report['protocol_sha256'] = protocol_pin
    stable(); run_case(whole_short, whole); stable(); run_case(partial_protected_width, partial); stable()
    require(len(cases) == 2 and all(row['control_observed'] is True for row in cases), 'both own negatives required')
    report.update(control_passed=True, status='completed')
except (Exception, KeyboardInterrupt) as error:
    report.update(control_passed=False, status='cancelled' if isinstance(error, KeyboardInterrupt) else 'failed',
                  error=type(error).__name__ + ': ' + str(error))
report['evidence_sha256'] = f.evidence_inventory(out)


def final_check():
    stable()
    require(f.evidence_inventory(out) == report['evidence_sha256'], 'completed negative evidence changed')


def account():
    report.update(sampled_wall_seconds=time.monotonic()-START, sampled_full_CPU_seconds=cpu()-CPU0,
                  publication_allowance_seconds=2, external_exit_required=True)
    if remaining() <= 0: report.update(control_passed=False, status='budget_exceeded')
    if report['status'] != 'completed': report['control_passed'] = False


f.publish(out, report, stable, account, remaining, owned=lambda: h.owned_destination(owner), final_check=final_check)
print(json.dumps({key: report.get(key) for key in ('control_passed', 'status', 'error', 'reason',
                                                   'sampled_wall_seconds', 'sampled_full_CPU_seconds')}))
raise SystemExit(0 if report['control_passed'] and report['status'] == 'completed' else 2)
