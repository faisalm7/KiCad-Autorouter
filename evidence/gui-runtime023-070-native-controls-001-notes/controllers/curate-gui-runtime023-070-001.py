"""Prepare/copy final GUI070 evidence using the GUI067 curation pattern.

Do not run until the lead supplies final facts and authorizes curation.
Usage: python3 -B .runs/curate-gui-runtime023-070-001.py \
    --manifest FINAL-CONTROLS.json --observations FINAL-OBSERVATIONS.json
Partial: add --partial-progress; finalized:false; only positive/high_budget jobs;
preopen:positive only; faults:{}; queued_race_forced_in_actual_GUI:false;
high_budget_choice_GUI_callback_observed:false. Observation full qualification
must remain false. Partial mode publishes a distinct progress packet.

Manifest: schema1, finalized:true; jobs mapping positive/high_budget/cancel/reject/
source_control/settings_control/export_control to seven distinct workspaces;
preopen maps positive/high_budget/source_control/settings_control/export_control
to five distinct existing {snapshot,snapshot_hashes,route,export} receipt paths;
faults maps source/settings/export to the actual refusal receipts. Fault schema1:
label, workspace, mutation, path, before_sha256, after_sha256, preopen_receipt,
preopen_receipt_sha256, GUI_refusal_observed:true, GUI_refusal_text:nonempty,
queue_hold_observed:boolean, recorded_utc:nonempty. Settings also has before_copy
pointing to an exact saved pre-mutation settings file. Mutations are exactly
append-newline-to-case-PRO / append-newline-to-captured-settings /
replace-export-accepted-true-with-integer-one. Changed bytes are retained here.
additional_files:[paths]; queued_race_forced_in_actual_GUI:boolean.
No GUI, routing, Native, process control or historical experiment is rerun.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-023/runtime'
sys.path.insert(0, str(runtime))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, gui

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--observations', type=Path, required=True)
parser.add_argument('--partial-progress', action='store_true',
                    help='Retain incomplete actual GUI observations without full qualification')
args = parser.parse_args()
started = time.monotonic()
base = runtime / '.runs/gui-session070'
manifest = f.read_json(args.manifest)
observations = f.read_json(args.observations)
prepared = f.read_json(base / 'prepared-state.json')
assert type(manifest['schema']) is int and manifest['schema'] == 1
assert manifest['finalized'] is (not args.partial_progress)
assert observations['actual_GUI_full_qualification'] is (not args.partial_progress)
assert prepared['source_head'] == '8c0c8468823751d9b5dc4c9a9c51b1d622269a27'
assert p.sha(runtime / 'runtime-distribution.json') == prepared['runtime_manifest_sha256'] == '3df808e340dbe8c01ddebafe5c5c12583dc8d4d0cfea407c9252b0a89c41de81'
source = Path(prepared['source'])
assert p.tree_hash(source.parent) == prepared['source_hashes']
assert p.sha(Path(prepared['settings_path'])) == prepared['settings_sha256']
labels = ('positive', 'high_budget') if args.partial_progress else ('positive', 'high_budget', 'cancel', 'reject', 'source_control', 'settings_control', 'export_control')
assert set(manifest['jobs']) == set(labels)
jobs = {label:Path(manifest['jobs'][label]).resolve() for label in labels}
assert all(work.is_relative_to(base / 'jobs') and work.is_dir() for work in jobs.values())
assert len(set(jobs.values())) == len(jobs), 'Each actual GUI job needs its own workspace'
assert type(manifest['queued_race_forced_in_actual_GUI']) is bool
assert set(manifest['faults']) == (set() if args.partial_progress else {'source', 'settings', 'export'})
if args.partial_progress:
    assert manifest['queued_race_forced_in_actual_GUI'] is False
    assert manifest['high_budget_choice_GUI_callback_observed'] is False
    assert set(manifest['preopen']) == {'positive'}
    assert not (jobs['high_budget'] / 'export').exists()

# Exact compact inventories avoid scanning the research archive. No code/binary
# payload is copied again; identical source/native companions share references.
references, reference_records = {}, []
reference_names = ['runtime023-installed-CLI-001.json', 'runtime023-installed-partial-CLI-001.json',
                   'gui-runtime019-067-native-controls-001.json']
if not args.partial_progress:
    reference_names.append('gui-runtime023-070-progress-001.json')
for name in reference_names:
    path = ROOT / 'evidence' / name
    old = f.read_json(path)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path)))
    for row in old['files']:
        references.setdefault(row['sha256'], row['path'])
packet = 'gui-runtime023-070-progress-001' if args.partial_progress else 'gui-runtime023-070-native-controls-001'
notes = ROOT / 'evidence' / (packet + '-notes')
rows, material, route_rows, export_rows, journals, faults = [], [], [], [], [], []
copied_bytes = 0
preopen_records = {}


def owned_path(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    assert path.resolve().is_relative_to(ROOT), 'Evidence path is outside this project'
    return path.resolve()


def copy(path, relative):
    global copied_bytes
    path = owned_path(path)
    raw = io.read_bytes(path, 4 * 1024 ** 2)
    assert b'\0' not in raw
    raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    public = references.get(digest)
    if public is None:
        destination = notes / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            assert destination.read_bytes() == raw, 'Existing curated bytes differ: ' + str(destination)
        else:
            with destination.open('xb') as stream:
                stream.write(raw)
        public = str(destination.relative_to(ROOT))
        references[digest] = public
        rows.append(dict(path=public, bytes=len(raw), sha256=digest))
        copied_bytes += len(raw)
        assert copied_bytes < 64 * 1024 ** 2 and len(rows) < 4000
    else:
        assert p.sha(ROOT / public) == digest
    material.append(dict(original=str(path.relative_to(ROOT)), retained=public, bytes=len(raw), sha256=digest))


skip = {'code', 'kicad-cache', 'kicad-config', 'kicad-documents', 'engine-config', 'plot-work'}
text_suffixes = {'.json', '.log', '.net', '.svg', '.html', '.kicad_pcb', '.kicad_pro', '.kicad_prl', '.kicad_sch', '.kicad_dru'}


def retain_tree(folder, relative, limit=32 * 1024 ** 2):
    for name in io.inventory(folder, max_bytes=limit):
        path = Path(name)
        if set(path.parts) & skip or path.name.startswith('.') or path.suffix not in text_suffixes:
            continue
        copy(folder / name, relative / name)


for label, work in jobs.items():
    route_path = work / 'route/result.json'
    data = f.read_json(route_path)
    settings = f.read_json(work / 'settings.json')
    assert settings['seconds'] == (420 if label == 'high_budget' else 90)
    assert data['budget_seconds'] == settings['seconds']
    if label == 'cancel':
        assert data['accepted'] is False and data['status'] == 'cancelled'
        cancelled = [step for step in data['steps'] if step['status'] == 'cancelled']
        assert cancelled and all(step['cleanup_complete'] is True for step in cancelled)
        assert not (work / 'export').exists()
        row = dict(label=label, status=data['status'], accepted=False,
                   cancelled_steps=[{key:step.get(key) for key in ('name', 'status', 'exit_code', 'cleanup_complete', 'wall_seconds', 'cpu_seconds')} for step in cancelled],
                   scope='Observed actual cancellation phase only; no accepted result, SIGINT-only or permanent-descendant guarantee.')
    else:
        assert data['accepted'] is True and data['invariants_unchanged'] is True and p.native_accepted(data['native'])
        assert [data['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
        original = p.sx.read(work / 'route/snapshot' / source.name)
        candidate = p.sx.read(Path(data['candidate']))
        assert p.sha(Path(data['candidate'])) == data['candidate_sha256']
        assert p.immutable(original) == p.immutable(candidate)
        protected = p.protected_for_record(data, original)
        assert len(protected) == 4 and all(item in p.routes(candidate) for item in protected)
        assert data['schematic_parity'] == 'checked by final native DRC'
        assert data['source_hashes'] == prepared['source_hashes']
        assert p.sha(work / 'route/final-drc.json') == data['native_report_sha256']
        if label in ('positive', 'high_budget'):
            with p.validation_readback_session():
                assert p.check_result(route_path)['current'] is True
        if label == 'high_budget':
            assert settings['seconds'] > 120
        row = dict(label=label, status=data['status'], accepted=True,
                   candidate_sha256=data['candidate_sha256'], native=data['native'], metrics=data['metrics'],
                   route_budget_seconds=data['budget_seconds'],
                   native_report_sha256=data['native_report_sha256'], protected_route_items=len(protected),
                   schematic_parity=data['schematic_parity'], original_nonrouting_design_preserved=True,
                   scope='Own recorded completion proof; intentionally mutated control outputs are not reaccepted.' if 'control' in label else 'Own current route reader passed.' if label in ('positive', 'high_budget') else 'Own recorded Native proof; no new current acceptance inferred.')
    row.update(result_sha256=p.sha(route_path), captured_settings=settings)
    route_rows.append(row)
    for path in sorted(work.glob('*.command.process.json')):
        process = f.read_json(path)
        journals.append(dict(label=label, file=path.name, process=process))
    retain_tree(work / 'route', Path(label) / 'route')
    for path in sorted(work.glob('*.command.*')):
        copy(path, Path(label) / 'GUI-journals' / path.name)
    copy(work / 'settings.json', Path(label) / 'settings.json')
    for relative in ('review/review.json', 'choice/choice.json'):
        path = work / relative
        if path.is_file():
            copy(path, Path(label) / relative)
    if (work / 'review').is_dir():
        retain_tree(work / 'review', Path(label) / 'rendered-review')

if not args.partial_progress:
    rejected = f.read_json(jobs['reject'] / 'choice/choice.json')
    assert rejected['choice'] == 'reject' and rejected['choice_recorded'] is True
    assert not (jobs['reject'] / 'export').exists()
    assert set(manifest['preopen']) == {'positive', 'high_budget', 'source_control', 'settings_control', 'export_control'}
preopen_paths = [owned_path(path) for path in manifest['preopen'].values()]
assert len(set(preopen_paths)) == len(preopen_paths), 'Each pre-open proof needs its own receipt'
snapshot_paths = set()
for label, receipt_path in manifest['preopen'].items():
    assert label in jobs
    receipt_path = owned_path(receipt_path)
    pre = f.read_json(receipt_path)
    snapshot = owned_path(pre['snapshot'])
    assert snapshot.is_relative_to(base) and snapshot.is_dir()
    assert snapshot not in snapshot_paths, 'Each pre-open proof needs its own snapshot'
    snapshot_paths.add(snapshot)
    assert p.tree_hash(snapshot) == pre['snapshot_hashes']
    assert pre['route']['current'] is True and pre['export']['current'] is True
    exported = f.read_json(snapshot / 'export.json')
    route_path = jobs[label] / 'route/result.json'
    route_record = f.read_json(route_path)
    assert Path(pre['route']['candidate']).resolve() == Path(route_record['candidate']).resolve()
    assert pre['route']['candidate_sha256'] == route_record['candidate_sha256']
    assert Path(pre['export']['original_routing_receipt']).resolve() == route_path
    assert Path(exported['inputs']['receipt']).resolve() == route_path
    assert exported['inputs']['receipt_sha256'] == p.sha(route_path)
    assert pre['export']['candidate_sha256'] == exported['candidate_sha256']
    assert exported['inputs']['validated_candidate_sha256'] == route_record['candidate_sha256']
    assert Path(exported['inputs']['validated_candidate']).resolve() == Path(route_record['candidate']).resolve()
    if label.endswith('_control'):
        assert owned_path(pre['workspace']) == jobs[label]
    assert exported['export_accepted'] is True and p.native_accepted(exported['native'])
    assert [exported['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
    assert exported['schematic_parity'] == 'checked by final native DRC'
    candidate = snapshot / 'validation/candidate' / source.name
    original = p.sx.read(jobs[label] / 'route/snapshot' / source.name)
    assert p.sha(candidate) == exported['candidate_sha256']
    assert p.sha(snapshot / 'validation/final-drc.json') == exported['native_report_sha256']
    assert p.immutable(p.sx.read(candidate)) == p.immutable(original)
    protected = p.protected_for_record(f.read_json(jobs[label] / 'route/result.json'), original)
    assert len(protected) == 4 and all(item in p.routes(p.sx.read(candidate)) for item in protected)
    expected = gui.export_validation_seconds(f.read_json(jobs[label] / 'settings.json')['seconds'])
    assert exported['budget_seconds'] == expected
    export_rows.append(dict(label=label, preopen_receipt_sha256=p.sha(receipt_path), preopen_current=True,
        snapshot_hashes=pre['snapshot_hashes'], native=exported['native'], metrics=exported['metrics'],
        candidate_sha256=exported['candidate_sha256'], native_report_sha256=exported['native_report_sha256'],
        protected_route_items=4, schematic_parity=exported['schematic_parity'],
        additional_export_budget_seconds=exported['budget_seconds'],
        current_after_open_or_mutation='Not inferred from the pre-open proof; later editor/control changes are retained separately.'))
    copy(receipt_path, Path(label) / 'observations/preopen.json')
    retain_tree(snapshot, Path(label) / 'preopen-export')
    preopen_records[label] = dict(path=receipt_path, data=pre, snapshot=snapshot)
for kind, receipt_path in manifest['faults'].items():
    path = owned_path(receipt_path)
    fault = f.read_json(path)
    label = kind + '_control'
    work = jobs[label]
    pre = preopen_records[label]
    assert type(fault['schema']) is int and fault['schema'] == 1
    assert fault['label'] == kind and owned_path(fault['workspace']) == work
    assert owned_path(fault['preopen_receipt']) == pre['path']
    assert fault['preopen_receipt_sha256'] == p.sha(pre['path'])
    assert fault['GUI_refusal_observed'] is True
    assert type(fault['GUI_refusal_text']) is str and fault['GUI_refusal_text'].strip()
    assert type(fault['recorded_utc']) is str and fault['recorded_utc'].strip()
    assert type(fault['queue_hold_observed']) is bool
    if manifest['queued_race_forced_in_actual_GUI']:
        assert fault['queue_hold_observed'] is True and fault['queue_hold_qualified'] is True
    route_record = f.read_json(work / 'route/result.json')
    control_project = base / 'freshness-controls-001' / kind / 'project'
    assert Path(route_record['source']).resolve().parent == control_project
    mutations = {'source': 'append-newline-to-case-PRO',
                 'settings': 'append-newline-to-captured-settings',
                 'export': 'replace-export-accepted-true-with-integer-one'}
    assert fault['mutation'] == mutations[kind]
    expected_path = (control_project / source.with_suffix('.kicad_pro').name if kind == 'source'
                     else work / 'settings.json' if kind == 'settings'
                     else work / 'export/export.json')
    modified = owned_path(fault['path'])
    assert modified == expected_path
    before = (source.with_suffix('.kicad_pro') if kind == 'source'
              else owned_path(fault['before_copy']) if kind == 'settings'
              else pre['snapshot'] / 'export.json')
    assert owned_path(before) != modified
    before_raw = io.read_bytes(before, 4 * 1024 ** 2)
    after_raw = io.read_bytes(modified, 4 * 1024 ** 2)
    assert hashlib.sha256(before_raw).hexdigest() == fault['before_sha256']
    assert hashlib.sha256(after_raw).hexdigest() == fault['after_sha256']
    assert fault['before_sha256'] != fault['after_sha256']
    if kind in ('source', 'settings'):
        assert after_raw == before_raw + b'\n'
        if kind == 'source':
            assert fault['before_sha256'] == prepared['source_hashes'][before.name]
        else:
            assert json.dumps(f.read_json(before), sort_keys=True) == json.dumps(prepared['settings'], sort_keys=True)
            if 'settings_sha256' in pre['data']:
                assert pre['data']['settings_sha256'] == fault['before_sha256']
    else:
        expected = json.loads(before_raw)
        actual = json.loads(after_raw)
        assert expected['export_accepted'] is True
        assert type(actual['export_accepted']) is int and actual['export_accepted'] == 1
        expected['export_accepted'] = 1
        assert json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True)
    faults.append(dict(kind=kind, receipt_sha256=p.sha(path), observed=fault))
    copy(path, Path('fault-controls') / kind / path.name)
    copy(before, Path('fault-controls') / kind / 'before' / before.name)
    copy(modified, Path('fault-controls') / kind / 'modified' / modified.name)
if not args.partial_progress:
    copy(base / 'freshness-controls-001/protocol-frozen-001.json',
         Path('observations/freshness-protocol-frozen-001.json'))
for path in [args.manifest, args.observations, base / 'prepared-state.json',
             base / 'route-settings.json', base / 'routing-settings-saved-GUI070-001.json', *map(Path, manifest['additional_files'])]:
    copy(path, Path('observations') / path.name)
assert f.read_json(base / 'route-settings.json') == f.read_json(base / 'routing-settings-saved-GUI070-001.json') == prepared['settings']
for name in prepared['source_hashes']:
    copy(source.parent / name, Path('source') / name)
copy(Path(__file__).resolve(), Path('controllers') / Path(__file__).name)
assert p.tree_hash(source.parent) == prepared['source_hashes']
index = dict(schema=1, files=rows, material=material,
             scope='Exact essential text copies/references; no new Native or acceptance framework. Binary captures, code/config/cache and complete raw workspaces stay local.')
notes.mkdir(parents=True, exist_ok=True)
with (notes / 'files.json').open('x') as stream:
    json.dump(index, stream, indent=2); stream.write('\n')
record = dict(schema=1, kind='actual-runtime023-GUI070-partial-progress' if args.partial_progress else 'actual-runtime023-GUI070-native-controls', project_complete=False,
    actual_GUI=True, human_review=False, full_release_qualified=False,
    actual_GUI_full_qualification=not args.partial_progress, partial_progress=args.partial_progress,
    runtime_manifest_sha256=prepared['runtime_manifest_sha256'], source_head=prepared['source_head'],
    original_source_project_bytes_unchanged=True, source_hashes=prepared['source_hashes'],
    observations=observations, route_rows=route_rows, positive_exports=export_rows,
    GUI_process_journals=journals, stale_controls=faults,
    queued_race_forced_in_actual_GUI=manifest['queued_race_forced_in_actual_GUI'],
    scope=('Partial actual GUI progress only: completed positive90 Route/review/test intent/fresh export/checked opening; high-budget420 Route/review observed and Accept clicked, but choice callback unobserved and high-budget export absent. Cancellation/rejection/stale controls and forced queue coverage are not claimed. ' if args.partial_progress else 'Actual final observations supplied by the lead; cancellation, rejection and stale controls remain individually scoped. ')
        + 'Every retained completed Route/export has its own Native/full-schematic/original/protected proof. One exposed owned2Cu partial family; no independent breadth/routing-quality/electrical/human claim.',
    cost_scope='Actual stage process journals retained. Whole interactive wall/full CPU including authoring, idle, curation and AI review is unmeasured, not zero. Native completion proofs are not rerun by this curator.',
    reference_records=reference_records, license_reference=dict(path='LICENSE', sha256=p.sha(ROOT / 'LICENSE'),
        scope='Project-owned fixture/controller; existing source/code/license bytes are shared by exact hash, not relicensed.'),
    curation_wall_seconds_before_publication=time.monotonic() - started,
    files=rows, files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
if args.partial_progress:
    record.update(high_budget_choice_GUI_callback_observed=False,
        high_budget_export_exists=False,
        high_budget_choice_receipt_present=(jobs['high_budget'] / 'choice/choice.json').is_file(),
        incomplete_controls=['high-budget choice GUI callback', 'high-budget fresh export/checked opening',
                             'cancel', 'reject', 'source/settings/export stale controls', 'final GUI qualification'],
        pending=observations.get('pending', []))
with (ROOT / 'evidence' / (packet + '.json')).open('x') as stream:
    json.dump(record, stream, indent=2); stream.write('\n')
print(json.dumps(dict(files=len(rows), bytes=copied_bytes, actual_GUI=True,
                     full_qualification=not args.partial_progress, partial_progress=args.partial_progress,
                     queued_race_forced=manifest['queued_race_forced_in_actual_GUI'], source_unchanged=True)))
