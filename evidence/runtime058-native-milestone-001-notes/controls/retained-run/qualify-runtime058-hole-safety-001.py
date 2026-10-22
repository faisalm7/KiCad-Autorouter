"""DRAFT: unchanged three Native/invariant controls after export replay repair.

Preparation only: copy/pin/freeze separately after the actual058 positive.
Use the existing135s enclosure; this child retains its120s wall/full-CPU cap.
No engine rerun, accepted result/export, product admission or GUI is claimed.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime + x.ru_stime for x in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import sys, json, shutil, uuid, argparse, hashlib
from decimal import Decimal

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--protocol', required=True); ap.add_argument('--protocol-sha256', required=True)
parsed = ap.parse_args()
protocol = Path(parsed.protocol); raw = protocol.read_bytes()
assert hashlib.sha256(raw).hexdigest() == parsed.protocol_sha256
plan = json.loads(raw)
runtime = Path(plan['runtime']); sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, config as c, floor_route as f, sexpr as sx
from autorouter import local_settings as local, handoff as h, schematic_field_evidence as fields

assert h.real_path(runtime) == runtime == c.ROOT and runtime.parent.name == 'runtime-directory-058'
assert Path(sys.prefix).resolve() == runtime / '.venv' and sys.prefix != sys.base_prefix
assert Path(sys.executable).absolute() == runtime / '.venv/bin/python'
self_path = h.real_path(Path(__file__).absolute()); selfpin = p.sha(self_path)
assert self_path == runtime / '.runs/qualify-runtime058-hole-safety-001.py'
assert selfpin == plan['controller_sha256'] and plan['controller'] == str(self_path)
assert plan['whole_wall_full_cpu_seconds'] == 135 and plan['pass_key'] == 'control_passed'
assert p.sha(runtime / 'runtime-distribution.json') == plan['runtime_manifest_sha256']
tools = p.tool_manifest()
assert c.NATIVE_VERSION == tools['kicad'] == '10.0.7' and tools['git_head'] == plan['source_head']
assert tools['source_provenance']['manifest_sha256'] == plan['runtime_manifest_sha256']
pins = [(h.real_path(name), pin) for name, pin in plan['prerequisites'].items()]
for path, pin in pins: assert p.sha(path) == pin
receipt = h.real_path(plan['receipt']); before_receipt = p.sha(receipt); data = f.read_json(receipt)
assert any(path == receipt and pin == before_receipt for path, pin in pins)
assert data['accepted'] is True and data['status'] == 'routing_accepted' and data.get('strategy') is None
assert data['scope'] == 'whole_board_unlocked_routing' and data['engine_profile'] == 'standard'
assert data['adapter'] == 'both' and data.get('scoring_variant') == 'via_high' and plan['expected_scoring'] == 'via_high' and data['tools'] == tools
assert data['schematic_parity'] == 'checked by final native DRC' and p.check_result(receipt)['current']
source = h.real_path(data['source']); hashes = p.tree_hash(source.parent)
assert str(source) == plan['source'] and hashes == data['source_hashes'] == plan['source_hashes']
original = sx.read(source); protected = [r for r in p.routes(original) if p.locked(r)]
assert len(protected) == 1 and protected[0][0] == 'segment'
assert sx.one(original, 'layers')[:3] == ['layers', ['0', '"F.Cu"', 'signal'], ['2', '"B.Cu"', 'signal']]
pads = [(fp, pad) for fp in sx.children(original, 'footprint') for pad in sx.children(fp, 'pad')]
assert len(pads) == 8 and sum(sx.one(pad, 'net') is not None for _, pad in pads) == 6
holes = [(fp, pad) for fp, pad in pads if pad[1:4] == ['""', 'np_thru_hole', 'circle']]
assert len(holes) == 2 and all(sx.one(pad, 'net') is None for _, pad in holes)
assert sorted(sx.one(pad, 'at')[1:] for _, pad in holes) == [['4', '-3'], ['7', '0']]
assert all(sx.one(fp, 'at') == ['at', '12', '10'] and sx.one(fp, 'layer') == ['layer', '"F.Cu"']
           and sx.one(pad, 'size') == ['size', '0.65', '0.65'] and sx.one(pad, 'drill') == ['drill', '0.65']
           for fp, pad in holes)
candidate = h.real_path(data['candidate']); assert candidate == receipt.parent / 'candidate' / source.name
p.verify_candidate_files(candidate, hashes, data['candidate_sha256'])
basis = p.check_default_target_transport(receipt.parent, data, original, candidate)
assert basis is not None and basis == f.read_json(receipt.parent / 'default-targets.json')
positive_inventory = f.evidence_inventory(receipt.parent)
out = h.real_path(plan['output'], existing=False)
assert out.parent == runtime / '.runs' and out.name.startswith('native7-comparison-control-') and not out.exists()
assert all(root != out and root not in out.parents and out not in root.parents
           for root in (source.parent, receipt.parent, candidate.parent))
out.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, out); rows = []; stages = []

def check_native(job, name, board, before, native, *, saved=False):
    target = job.out / 'refill' / board.name if saved else job.out / (name + '-input') / board.name
    assert f.check_drc_stage(job.out, {'steps': job.steps}, name, board, target, saved, before,
                            schematic_parity=not saved, sandboxed=False) == native
    stages.append((job, name, board, target, saved, before, native))

record = dict(schema=1, accepted=False, production_admitted=False, project_complete=False,
    actual_GUI=False, human_review=False, control_passed=False, status='failed',
    source=str(source), source_hashes=hashes, positive_receipt=str(receipt), positive_sha256=before_receipt,
    positive_candidate=str(candidate), positive_candidate_sha256=data['candidate_sha256'], tools=tools,
    source_head=plan['source_head'], runtime_manifest_sha256=plan['runtime_manifest_sha256'],
    controller_sha256=selfpin, protocol_sha256=parsed.protocol_sha256, cases=rows,
    whole_wall_full_CPU_seconds=120, outer_wall_full_CPU_seconds=135,
    scope='Three owned copied-candidate Native/invariant controls after a fresh explicit via_high ordinary NPTH positive. '
          'Original source/candidate unchanged; no solver rerun, delivery, GUI, false-acceptance rate or electrical claim.')
try:
    for mode in ('short', 'protected-width', 'hole-clearance'):
        assert min(115 - (time.monotonic() - START), 115 - (cpu() - CPU0)) > 20
        job = p.Job(out / mode, min(40, 110 - (time.monotonic() - START), 110 - (cpu() - CPU0)),
                    protect_local_settings=True)
        copied = job.out / 'candidate' / source.name; shutil.copytree(candidate.parent, copied.parent)
        assert p.sha(copied) == data['candidate_sha256']
        before_bytes = copied.read_bytes(); tree = sx.read(copied)
        row = dict(case=mode, passed=False, steps=job.steps, before_candidate_sha256=p.sha(copied)); rows.append(row)
        (job.out / 'before-candidate.kicad_pcb').write_bytes(before_bytes)
        started = time.monotonic(); started_cpu = cpu()
        if mode in ('short', 'hole-clearance'):
            start, end = (('12', '10'), ('12', '16')) if mode == 'short' else (('18.5', '10'), ('19.5', '10'))
            segment = ['segment', ['start', *start], ['end', *end], ['width', '0.3'],
                       ['layer', '"F.Cu"'], ['net', '"ROUTE"'], ['uuid', json.dumps(str(uuid.uuid4()))]]
            segment = p.convert_route_nets(segment, ['kicad_pcb'], tree)
            tree.append(segment)
            assert p.immutable(tree) == p.immutable(original) and all(r in p.routes(tree) for r in protected)
            sx.write(copied, tree); row.update(added_segment=segment, pre_native_sha256=p.sha(copied))
            (job.out / 'invalid-before-native.kicad_pcb').write_bytes(copied.read_bytes())
            digest, native = p.validate_candidate(job, original, copied, hashes, protected, default_target_policy=True)
            row.update(candidate_sha256=digest, native=native, report_sha256=p.sha(job.out / 'final-drc.json'))
            required = 'shorting_items' if mode == 'short' else 'hole_clearance'
            assert not p.native_accepted(native) and native['blocking'] > 0
            assert any(item['type'] == required and item['severity'] == 'error' for item in native['findings'])
            expected = dict(hashes); expected[copied.name] = digest
            check_native(job, 'final-drc', copied, expected, native)
            refill_before = dict(hashes); refill_before[copied.name] = row['pre_native_sha256']
            check_native(job, 'refill-drc', job.out / 'refill' / copied.name, refill_before,
                         p.parse_report(job.out / 'refill-drc.json', copied.name), saved=True)
            p.check_final_netclass_evidence(job.out, {'steps': job.steps}, copied, protected,
                                           default_target_policy=True, default_target_basis=basis)
            row['rejection'] = 'Actual original-rule full-schematic Native ' + required
        else:
            chosen = next(r for r in protected if r[0] == 'segment')
            changed = next(r for r in p.routes(tree) if r == chosen); width = sx.one(changed, 'width')
            width[1] = format(Decimal(width[1]) + Decimal('0.000001'), 'f'); sx.write(copied, tree)
            row['mutated_sha256'] = p.sha(copied); before = dict(hashes); before[copied.name] = p.sha(copied)
            (job.out / 'invalid-before-native.kicad_pcb').write_bytes(copied.read_bytes())
            native = job.drc('diagnostic-drc', copied, schematic_parity=True); row['diagnostic_native'] = native
            assert p.native_accepted(native)
            check_native(job, 'diagnostic-drc', copied, before, native)
            count = len(job.steps)
            try: p.validate_candidate(job, original, copied, hashes, protected, default_target_policy=True)
            except p.Rejected as exc:
                assert str(exc) == 'protected route changed'; row['rejection'] = str(exc)
            else: raise AssertionError('protected original mutation accepted')
            assert len(job.steps) == count and p.sha(copied) == row['mutated_sha256']
        (job.out / 'after-native.kicad_pcb').write_bytes(copied.read_bytes())
        row.update(passed=True, wall_seconds=time.monotonic() - started, full_CPU_seconds=cpu() - started_cpu)
    assert p.check_result(receipt)['current']
    assert p.sha(receipt) == before_receipt and f.evidence_inventory(receipt.parent) == positive_inventory
    assert p.tree_hash(source.parent) == hashes and p.sha(candidate) == data['candidate_sha256']
    assert p.tool_manifest() == tools and p.sha(self_path) == selfpin
    for path, pin in pins: assert p.sha(path) == pin
    assert protocol.read_bytes() == raw and p.sha(runtime / 'runtime-distribution.json') == plan['runtime_manifest_sha256']
    for job, name, board, target, saved, before, native in stages:
        assert f.check_drc_stage(job.out, {'steps': job.steps}, name, board, target, saved, before,
                                schematic_parity=not saved, sandboxed=False) == native
        if fields.has_fields(native.get('findings', [])):
            fields.check_local_settings(job.out, name, f.read_json(job.out / (name + '-binding.json')))
    assert h.owned_destination(owner) == out
    local.check_final_events([(receipt.parent, data),
        *((out / row['case'], {'steps': row['steps']}) for row in rows)], c.CLI)
    record.update(control_passed=True, status='completed')
except (Exception, KeyboardInterrupt) as exc:
    record.update(error=type(exc).__name__ + ': ' + str(exc))
record.update(wall_seconds=time.monotonic() - START, total_cpu_seconds=cpu() - CPU0, external_exit_required=True)
if max(record['wall_seconds'], record['total_cpu_seconds']) + 2 > 120:
    record.update(control_passed=False, status='budget_exceeded')
p.save_json(out / 'result.json', record)
print(json.dumps(dict(control_passed=record['control_passed'], status=record['status'], error=record.get('error'))))
raise SystemExit(0 if record['control_passed'] else 2)
