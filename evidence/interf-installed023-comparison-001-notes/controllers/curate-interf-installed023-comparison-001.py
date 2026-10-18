"""Curate all seven completed frozen v4 arms; never route or replace a reader.

Do not execute until the lead confirms all seven supervised workers are reaped.
Adapted from the runtime022 comparison curator; no Native or engine is invoked.
"""
import datetime
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as pc, provenance as pv, sexpr as sx

BASE = ROOT / '.runs/interf-installed023-comparison-001'
PROTOCOL_SHA256 = 'c73179572c4c0c6314e6f38c72638e2b4c12c5f3eabb809bbdd2d78ecef5c7cc'
ADMINISTRATION_HEAD = '7e65d62c514790a5aa625b5d886e894670db296d'
SOURCE_HEAD = '8c0c8468823751d9b5dc4c9a9c51b1d622269a27'
NOTES = ROOT / 'evidence/interf-installed023-comparison-001-notes'
SUMMARY = ROOT / 'evidence/interf-installed023-comparison-001.json'
ARMS = ('B0', 'B1', 'B2_tuned', 'B2_completion', 'B2_portfolio', 'C_single', 'C_thermal')


def load(path):
    return json.loads(path.read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def publish(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, 'Existing curated bytes differ: ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(raw)


def complete_exit(path):
    values = dict(line.split() for line in path.read_text().splitlines() if line.strip())
    assert set(values) == {'real', 'user', 'sys'}
    values = {key: float(value) for key, value in values.items()}
    assert all(math.isfinite(value) and value >= 0 for value in values.values())
    return dict(wall_seconds=values['real'], user_CPU_seconds=values['user'],
                system_CPU_seconds=values['sys'], full_CPU_seconds=round(values['user'] + values['sys'], 2),
                resolution_seconds=0.01)


assert p.sha(BASE / 'protocol.json') == PROTOCOL_SHA256
plan = load(BASE / 'protocol.json')
runtime = Path(plan['runtime'])
assert plan['kind'] == 'installed-workflow-thermal-export-budget-comparison-v4'
assert tuple(plan['arms']) == ARMS
assert plan['administration_head'] == ADMINISTRATION_HEAD and plan['tools']['git_head'] == SOURCE_HEAD
assert [plan[key] for key in ('routing_seconds', 'method_wall_cpu_cap_seconds',
                             'delivery_wall_cpu_cap_seconds', 'export_validation_seconds')] == [420, 450, 600, 120]
assert plan['allocation'] == 'balanced'
assert plan['installed_trial_accounting_policy'] == 'installed-route-readback-reserve-v1'
assert p.sha(runtime / pv.MANIFEST) == plan['tools']['source_provenance']['manifest_sha256']
for name, pin in plan['administration_files_sha256'].items():
    assert p.sha(ROOT / name) == pin
for name, pin in plan['tools']['implementation_sha256'].items():
    assert p.sha(runtime / name) == pin
assert pc.inventory(Path(plan['source']).parent) == plan['source_hashes']
original = sx.read(Path(plan['source']))

# Read all completed enclosures before creating public output. Missing work is
# not converted into a skipped result or inferred from an earlier comparison.
completed = []
for arm in ARMS:
    enclosing = BASE / (arm + '-enclosure')
    outer = load(enclosing / 'execution.json')
    assert outer['arm'] == arm and outer['protocol_sha256'] == PROTOCOL_SHA256
    assert outer['sources_unchanged'] is True and outer['process']['cleanup_complete'] is True
    receipt = Path(outer['child_receipt'])
    assert p.sha(receipt) == outer['child_receipt_sha256']
    child = load(receipt)
    timing = ROOT / '.runs' / ('interf-installed023-' + arm + '-001-time.log')
    completed.append((arm, enclosing, outer, receipt.parent, child, timing, complete_exit(timing)))

# Reuse only explicit compact inventories; no historical research-tree scan.
references, reference_records = {}, []
for name in ('interf-installed022-comparison-001.json', 'runtime023-installed-CLI-001.json',
             'runtime023-installed-partial-CLI-001.json', 'runtime022-thermal-export-control-001.json'):
    path = ROOT / 'evidence' / name
    old = load(path)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path)))
    inventories = [old.get('files', [])]
    if old.get('files_index'):
        index_path = ROOT / old['files_index']['path']
        assert p.sha(index_path) == old['files_index']['sha256']
        inventories.append(load(index_path)['files'])
    for inventory in inventories:
        for row in inventory:
            references.setdefault(row['sha256'], row['path'])
files, material, rows = [], [], []
new_bytes = 0


def copy(path, target):
    global new_bytes
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert len(raw) < 4 * 1024 ** 2
    pin = sha(raw)
    public = references.get(pin)
    if public is None:
        # All new material is bounded UTF-8 text. The exact already retained
        # licensed Tux bitmap may be referenced, but is never recopied.
        assert b'\0' not in raw
        raw.decode('utf-8')
        destination = NOTES / target
        publish(destination, raw)
        public = str(destination.relative_to(ROOT))
        references[pin] = public
        files.append(dict(path=public, bytes=len(raw), sha256=pin))
        new_bytes += len(raw)
        assert new_bytes < 32 * 1024 ** 2 and len(files) < 2000
    else:
        assert p.sha(ROOT / public) == pin
    material.append(dict(original=str(path.relative_to(ROOT)), retained=public, bytes=len(raw), sha256=pin))


def attempt(folder, target):
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix in ('.json', '.log', '.net'):
            copy(path, target / path.name)


def candidate(data, target, protected):
    board = Path(data['candidate'])
    assert p.sha(board) == data['candidate_sha256']
    tree = sx.read(board)
    assert p.immutable(tree) == p.immutable(original)
    assert all(item in p.routes(tree) for item in protected)
    for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_prl', '.kicad_dru'):
        path = board.with_suffix(suffix)
        if path.is_file():
            copy(path, target / path.name)


copy(BASE / 'protocol.json', Path('protocol.json'))
for name in ('prepare-interf-installed023-comparison-001.py', 'run-interf-installed023-arm-001.py'):
    path = ROOT / '.runs' / name
    if name.startswith('run-'):
        assert p.sha(path) == plan['outer_controller_sha256']
    copy(path, Path('controllers') / name)
copy(Path(__file__).resolve(), Path('controllers') / Path(__file__).name)
for name in plan['source_hashes']:
    copy(Path(plan['source']).parent / name, Path('original') / name)
source_native = None
for arm, enclosing, outer, out, child, timing, complete in completed:
    complete_within_budget = max(complete['wall_seconds'], complete['full_CPU_seconds']) <= plan['delivery_wall_cpu_cap_seconds']
    delivered = bool(outer['delivered'] and complete_within_budget)
    for name in ('execution.json', 'process.json', 'command.log'):
        copy(enclosing / name, Path(arm) / 'enclosure' / name)
    copy(timing, Path(arm) / 'enclosure/complete-exit-time.log')
    copy(out / 'result.json', Path(arm) / 'workflow-result.json')
    for path in sorted(out.glob('*.log')):
        copy(path, Path(arm) / path.name)
    for path in sorted(out.glob('*.process.json')):
        copy(path, Path(arm) / path.name)
    diagnostic = child.get('route_attempt') or {}
    native = (child.get('native') if delivered else diagnostic.get('native')) or {}
    row = dict(arm=arm, delivered=delivered, status=outer['child_status'], reason=outer['child_reason'],
        sampled_enclosure_delivered=outer['delivered'], complete_exit_within_delivery_caps=complete_within_budget,
        late_complete_exit_invalidates_sampled_delivery=bool(outer['delivered'] and not complete_within_budget),
        complete_exit_refusal=None if complete_within_budget else 'Complete external wall/full CPU exit exceeds the unchanged600-second delivery cap; an earlier positive sample is not comparison eligible.',
        route_status=diagnostic.get('status'),
        native={key:native.get(key) for key in ('opens', 'blocking', 'warnings', 'exclusions')},
        complete_enclosing_command=complete, complete_qualifier_process_wall_seconds=outer['process']['wall_seconds'],
        complete_qualifier_process_CPU_seconds=outer['process']['cpu_seconds'],
        qualifier_supervisor_CPU_seconds=outer['process'].get('supervisor_cpu_seconds'),
        stored_enclosure_sample=dict(wall_seconds=outer['whole_wall_seconds'], full_CPU_seconds=outer['whole_full_cpu_seconds']),
        method_wall_seconds=outer['method_wall_seconds'], method_CPU_seconds=outer['method_full_cpu_seconds'])
    if diagnostic.get('receipt'):
        route_folder = Path(diagnostic['receipt']).parent
        attempt(route_folder, Path(arm) / 'route-attempt')
        route_data = load(Path(diagnostic['receipt']))
        if route_data.get('source_drc') is not None:
            if source_native is None:
                source_native = route_data['source_drc']
            else:
                assert route_data['source_drc'] == source_native
    if arm == 'B2_portfolio':
        portfolio = child.get('portfolio')
        assert portfolio is not None
        directory = Path(child['portfolio_directory'])
        copy(directory / 'portfolio-summary.json', Path(arm) / 'portfolio-summary.json')
        copy(directory / 'protocol.json', Path(arm) / 'portfolio-protocol.json')
        row.update(portfolio_status=portfolio['status'], portfolio_reason=portfolio.get('reason'),
            all_variants_attempted=portfolio['all_variants_attempted'], unattempted_variants=portfolio['unattempted_variants'],
            portfolio_wall_seconds=portfolio['wall_seconds'], portfolio_CPU_seconds=portfolio['total_cpu_seconds'], portfolio_trials=[])
        for index, trial in enumerate(portfolio['trials']):
            row['portfolio_trials'].append({**{key:trial.get(key) for key in
                ('id', 'status', 'eligible', 'validated_rejection', 'assigned_seconds', 'route_allowance_seconds',
                 'trial_readback_reserve_seconds', 'invocation_wall_seconds', 'invocation_cpu_seconds', 'negative_readback_cpu_seconds')},
                'native':{key:(trial.get('native') or {}).get(key) for key in ('opens', 'blocking', 'warnings', 'exclusions')}})
            if trial.get('result'):
                receipt = Path(trial['result'])
                attempt(receipt.parent, Path(arm) / ('trial-%02d' % index))
                for suffix in ('.cli-process.json', '.cli-rejection.json', '.cli.log'):
                    path = receipt.parent.with_suffix(suffix)
                    if path.is_file():
                        copy(path, Path(arm) / ('trial-%02d' % index) / path.name)
    if arm == 'C_single' and diagnostic.get('receipt'):
        for receipt in Path(diagnostic['receipt']).parent.glob('*/result.json'):
            attempt(receipt.parent, Path(arm) / receipt.parent.name)
    if arm == 'C_thermal' and diagnostic.get('receipt'):
        repair = diagnostic.get('repair') or {}
        row.update(repair_status=repair.get('status'), repair_validation_passed=repair.get('validation_passed'))
        route_folder = Path(diagnostic['receipt']).parent
        if (route_folder / 'incumbent').is_dir():
            attempt(route_folder / 'incumbent', Path(arm) / 'incumbent')
        if repair.get('candidate'):
            attempt(Path(repair['candidate']).parent.parent, Path(arm) / 'thermal-trial')
        for name in ('geometry.json', 'proposals.json', 'request.json', 'repair.json'):
            path = route_folder / 'recovery' / name
            if path.is_file():
                copy(path, Path(arm) / 'recovery' / name)
    if delivered:
        receipt = Path(child['selected_route_receipt'])
        exported = Path(child['export_receipt'])
        data = load(receipt)
        export = load(exported)
        assert p.sha(receipt) == child['selected_route_sha256'] and p.sha(exported) == child['export_sha256']
        assert data['accepted'] is True and export['export_accepted'] is True
        assert child['route_readback']['current'] is True and child['export_readback']['current'] is True
        assert export['budget_seconds'] == plan['export_validation_seconds']
        assert data['schematic_parity'] == export['schematic_parity'] == 'checked by final native DRC'
        assert data['source_hashes'] == export['source_hashes'] == plan['source_hashes']
        protected = p.protected_for_record(data, original)
        copy(receipt, Path(arm) / 'selected-route/result.json')
        copy(exported, Path(arm) / 'export/export.json')
        attempt(receipt.parent, Path(arm) / 'selected-route')
        attempt(exported.parent / 'validation', Path(arm) / 'export/validation')
        candidate(data, Path(arm) / 'route-candidate', protected)
        candidate(export, Path(arm) / 'export-candidate', protected)
        for folder, filename in (('review', 'review.json'), ('choice', 'choice.json')):
            local = exported.parent.parent / folder / filename
            if not local.exists():
                local = Path(child['workspace']) / folder / filename
            copy(local, Path(arm) / folder / filename)
        row.update(candidate_sha256=export['candidate_sha256'], route_candidate_sha256=data['candidate_sha256'],
            route_native=data['native'], export_native=export['native'], route_metrics=data['metrics'], export_metrics=export['metrics'],
            route_native_report_sha256=data['native_report_sha256'], export_native_report_sha256=export['native_report_sha256'],
            whole_project_drc_clean=export['whole_project_drc_clean'], original_nonrouting_design_preserved=True,
            validated_candidate_geometry_and_routing_preserved_through_export=export['original_geometry_and_routing_unchanged'],
            protected_route_count=len(protected), protected_routes_preserved=True,
            route_schematic_parity=data['schematic_parity'], export_schematic_parity=export['schematic_parity'])
    rows.append(row)

assert source_native is not None
assert [source_native[key] for key in ('opens', 'blocking', 'warnings')] == [0, 2, 22]
assert pc.inventory(Path(plan['source']).parent) == plan['source_hashes']
assert p.sha(BASE / 'protocol.json') == PROTOCOL_SHA256
for name, pin in plan['administration_files_sha256'].items():
    assert p.sha(ROOT / name) == pin
for name, pin in plan['tools']['implementation_sha256'].items():
    assert p.sha(runtime / name) == pin

scope = '''# Frozen runtime023 Interf v4 development comparison

One exposed Interf_u family, seven methods, unchanged original source and frozen administration/runtime. This is not seven independent boards, untouched confirmation, general superiority, human review or an actual GUI test. Corrected-standard remains the shipped default (B1); experimental C_thermal is not promoted to the GUI/default by this comparison.

Each arm retains complete external wall/user/system CPU costs, its earlier enclosure sample, method/process costs, failures, warnings and exclusions. All portfolio attempts, validated negatives and skipped/unattempted variants remain visible. Missing work is never inferred from earlier runs. Research, authoring, AI review, integration, preparation and curation are additional costs, not zero. Nested CPU must not be added twice.

The original source has 0 opens, 2 repairable thermal violations and 22 warnings. These copper/thermal findings do not by themselves establish a hard net, pad, footprint or schematic conflict; expected unrouted task connections are not invalid source designs. Original zone/spoke rules, geometry, constraints, net mapping, severity/exclusions and protected copper remain unchanged. All actual findings remain retained; no waiver is introduced.

Every delivered candidate retains its own actual final Route and fresh-export Native refill/full-schematic/original/protected checks, final hashes, review/choice and checked readback. A route-only or separately debugged export is not a delivered first-attempt comparison success. Earlier v3 failures and its separate corrective export-only control remain unchanged and cannot be stitched into v4.

The source is KiCad demos/interf_u at69cafb907ebc09e7722a2a464b1d466fc2e3608d, CC-BY-SA4.0, credited to KiCad contributors. Tux artwork is by Larry Ewing and The GIMP. Exact existing source/assets/notices and runtime/code bytes are referenced by hashes rather than recopied. No new binary asset, engine, application or interpreter is included. Modified candidate copper is distinguished from the immutable original source.

This packet is essential byte-preserving public evidence with explicit references, not another validator, relocated executable proof, complete raw-workspace backup or restoration test. Raw DSN/SES/code/config/cache/full workspaces remain on this Mac. Older backups do not cover newer raw artifacts retroactively. No electrical/manufacturing, independent-family, current-stable-platform or formal-release claim follows from this exposed development study.
'''
publish(NOTES / 'SCOPE.md', scope.encode())
copy(NOTES / 'SCOPE.md', Path('SCOPE.md'))
index = dict(schema=1, files=files, material=material,
             runtime_implementation_sha256=plan['tools']['implementation_sha256'],
             administration_files_sha256=plan['administration_files_sha256'],
             scope='Essential proof copy and exact references; no new admission/verifier framework. Complete raw workspaces remain local.')
publish(NOTES / 'files.json', (json.dumps(index, indent=2) + '\n').encode())
record = dict(schema=1, kind='interf-installed023-seven-arm-export-budget-frozen-development-comparison-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), project_complete=False, accepted=False,
    actual_GUI=False, human_review=False, broad_superiority_claim=False, default_policy_promoted=False,
    source_runtime_head=SOURCE_HEAD, administration_head=ADMINISTRATION_HEAD, protocol_sha256=PROTOCOL_SHA256,
    source_hashes=plan['source_hashes'], original_source_project_bytes_unchanged=True,
    source_native=source_native,
    source_findings_disposition='0 opens, 2 repairable thermal findings and 22 warnings remain visible. This is not a hard source net/pad/footprint conflict determination; expected unrouted task connections are not invalid designs. No original zone/spoke/rule/geometry requirement was relaxed.',
    population='One exposed KiCad Interf_u family and seven methods. Original25 files/1,490,971 bytes; ancestry independence and untouched confirmation unverified.',
    budgets={key:plan[key] for key in ('routing_seconds', 'method_wall_cpu_cap_seconds', 'delivery_wall_cpu_cap_seconds',
                                     'allocation', 'installed_trial_accounting_policy', 'export_validation_seconds')},
    rows=rows, delivered_arms=[row['arm'] for row in rows if row['delivered']],
    prior_failure='evidence/interf-installed022-comparison-001.json',
    prior_debugging_control='evidence/runtime022-thermal-export-control-001.json',
    no_stitched_prior_result=True, data_source=plan['data_source'], reference_records=reference_records,
    accounting='Complete external /usr/bin/time wall/user/system exit costs include startup/protocol/context/preview/conversion/attempts/selection/validation/rendering/test intent/export/readback/publication/exit and enclosure writing. Earlier stored enclosure samples and nested qualifier rusage remain separate; never sum nested CPU. Research, authoring, AI review, integration, runtime preparation and curation are additional and not zero.',
    retention='All seven actual outcomes, failures, warnings, negative portfolio attempts and skips are retained. New text/final Native/SCH/original/protected proof and candidate CAD are copied; exact existing licensed source/assets/notices/code bytes are hash-referenced. Full raw workspaces remain on this Mac, with no new backup/restoration claim.',
    files=files, files_index=dict(path=str((NOTES / 'files.json').relative_to(ROOT)), sha256=p.sha(NOTES / 'files.json')),
    new_material_bytes=new_bytes)
publish(SUMMARY, (json.dumps(record, indent=2) + '\n').encode())
print(json.dumps(dict(summary=str(SUMMARY.relative_to(ROOT)), sha256=p.sha(SUMMARY),
                     files=len(files), new_material_bytes=new_bytes, delivered_arms=record['delivered_arms'])))
