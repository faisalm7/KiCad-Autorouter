"""Prepare/copy final GUI072 evidence using the GUI067 curation pattern.

Do not run until the lead supplies final facts and authorizes curation.
Usage: python3 -B .runs/curate-gui-runtime026-072-001.py \
    --manifest FINAL-CONTROLS.json --observations FINAL-OBSERVATIONS.json

Manifest: schema1, finalized:true; jobs mapping positive/high_budget/cancel/reject/
source_control/settings_control/export_control to workspaces; preopen mapping
exported labels to existing {snapshot,snapshot_hashes,route,export} receipt paths;
faults mapping source/settings/export to existing refusal-receipt paths;
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
runtime = ROOT / '.runs/runtime-directory-026/runtime'
sys.path.insert(0, str(runtime))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, gui

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--observations', type=Path, required=True)
args = parser.parse_args()
started = time.monotonic()
base = runtime / '.runs/gui-session072'
manifest = f.read_json(args.manifest)
observations = f.read_json(args.observations)
prepared = f.read_json(base / 'prepared-state.json')
assert type(manifest['schema']) is int and manifest['schema'] == 1 and manifest['finalized'] is True
assert observations['actual_GUI_full_qualification'] is True
assert prepared['source_head'] == '1117de080524072046a61522845facd5d4c68575'
assert p.sha(runtime / 'runtime-distribution.json') == prepared['runtime_manifest_sha256'] == '5371d08ccf5a0ae2e0c4024f752baca28f034c3b3cb50ade308e8e5e12e36fe5'
source = Path(prepared['source'])
assert p.tree_hash(source.parent) == prepared['source_hashes']
assert p.sha(Path(prepared['settings_path'])) == prepared['settings_sha256']
labels = ('positive', 'high_budget', 'cancel', 'reject', 'source_control', 'settings_control', 'export_control')
assert set(manifest['jobs']) == set(labels)
jobs = {label:Path(manifest['jobs'][label]).resolve() for label in labels}
assert all(work.is_relative_to(base / 'jobs') and work.is_dir() for work in jobs.values())
assert type(manifest['queued_race_forced_in_actual_GUI']) is bool
assert set(manifest['faults']) == {'source', 'settings', 'export'}

# Exact compact inventories avoid scanning the research archive. No code/binary
# payload is copied again; identical source/native companions share references.
references, reference_records = {}, []
for name in ('runtime026-installed-CLI-001.json', 'runtime026-installed-partial-CLI-001.json',
             'gui-runtime019-067-native-controls-001.json'):
    path = ROOT / 'evidence' / name
    old = f.read_json(path)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path)))
    for row in old['files']:
        references.setdefault(row['sha256'], row['path'])
notes = ROOT / 'evidence/gui-runtime026-072-native-controls-001-notes'
rows, material, route_rows, export_rows, journals, faults = [], [], [], [], [], []
copied_bytes = 0


def copy(path, relative):
    global copied_bytes
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    assert path.resolve().is_relative_to(ROOT)
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

rejected = f.read_json(jobs['reject'] / 'choice/choice.json')
assert rejected['choice'] == 'reject' and rejected['choice_recorded'] is True
assert not (jobs['reject'] / 'export').exists()
assert {'positive', 'high_budget'} <= set(manifest['preopen'])
for label, receipt_path in manifest['preopen'].items():
    assert label in jobs
    receipt_path = Path(receipt_path)
    pre = f.read_json(receipt_path)
    snapshot = Path(pre['snapshot'])
    assert p.tree_hash(snapshot) == pre['snapshot_hashes']
    assert pre['route']['current'] is True and pre['export']['current'] is True
    exported = f.read_json(snapshot / 'export.json')
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
for kind, receipt_path in manifest['faults'].items():
    path = Path(receipt_path)
    fault = f.read_json(path)
    assert fault['GUI_refusal_observed'] is True
    if manifest['queued_race_forced_in_actual_GUI']:
        assert fault['queue_hold_qualified'] is True
    faults.append(dict(kind=kind, receipt_sha256=p.sha(path), observed=fault))
    copy(path, Path('fault-controls') / kind / path.name)
for path in [args.manifest, args.observations, base / 'prepared-state.json',
             base / 'route-settings.json', base / 'routing-settings-saved-GUI072-001.json', *map(Path, manifest['additional_files'])]:
    relative_name = path.parent.name + '-' + path.name if path.name == 'mutation-001.json' else path.name
    copy(path, Path('observations') / relative_name)
assert f.read_json(base / 'route-settings.json') == f.read_json(base / 'routing-settings-saved-GUI072-001.json') == prepared['settings']
for name in prepared['source_hashes']:
    copy(source.parent / name, Path('source') / name)
copy(Path(__file__).resolve(), Path('controllers') / Path(__file__).name)
assert p.tree_hash(source.parent) == prepared['source_hashes']
index = dict(schema=1, files=rows, material=material,
             scope='Exact essential text copies/references; no new Native or acceptance framework. Binary captures, code/config/cache and complete raw workspaces stay local.')
notes.mkdir(parents=True, exist_ok=True)
with (notes / 'files.json').open('x') as stream:
    json.dump(index, stream, indent=2); stream.write('\n')
record = dict(schema=1, kind='actual-runtime026-GUI072-native-controls', project_complete=False,
    actual_GUI=True, human_review=False, full_release_qualified=False,
    runtime_manifest_sha256=prepared['runtime_manifest_sha256'], source_head=prepared['source_head'],
    original_source_project_bytes_unchanged=True, source_hashes=prepared['source_hashes'],
    observations=observations, route_rows=route_rows, positive_exports=export_rows,
    GUI_process_journals=journals, stale_controls=faults,
    queued_race_forced_in_actual_GUI=manifest['queued_race_forced_in_actual_GUI'],
    scope='Actual final observations are supplied by the lead. Own Route/export Native/full-schematic/original/protected proofs, refusal, cancellation, rejection and high-budget behavior remain individually scoped. One exposed owned2Cu partial family; no independent breadth/routing-quality/electrical/human claim.',
    cost_scope='Actual stage process journals retained. Whole interactive wall/full CPU including authoring, idle, curation and AI review is unmeasured, not zero. Native completion proofs are not rerun by this curator.',
    reference_records=reference_records, license_reference=dict(path='LICENSE', sha256=p.sha(ROOT / 'LICENSE'),
        scope='Project-owned fixture/controller; existing source/code/license bytes are shared by exact hash, not relicensed.'),
    curation_wall_seconds_before_publication=time.monotonic() - started,
    files=rows, files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
with (ROOT / 'evidence/gui-runtime026-072-native-controls-001.json').open('x') as stream:
    json.dump(record, stream, indent=2); stream.write('\n')
print(json.dumps(dict(files=len(rows), bytes=copied_bytes, actual_GUI=True,
                     queued_race_forced=manifest['queued_race_forced_in_actual_GUI'], source_unchanged=True)))
