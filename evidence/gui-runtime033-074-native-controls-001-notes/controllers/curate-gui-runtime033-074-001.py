"""Prepare/copy final GUI074 evidence using the GUI072 curation pattern.

Do not run until the lead supplies final facts and authorizes curation.
Usage: python3 -B .runs/curate-gui-runtime033-074-001.py \
    --manifest FINAL-CONTROLS.json --observations FINAL-OBSERVATIONS.json

Manifest: schema1, finalized:true; jobs mapping positive/high_budget/cancel/reject/
source_control/settings_control/export_control to workspaces; preopen mapping
exported labels to existing {snapshot,snapshot_hashes,route,export} receipt paths;
faults mapping source/settings/export to existing refusal-receipt paths;
additional_files:[paths]; queued_race_forced_in_actual_GUI:boolean.
observations must explicitly list all seven observed_roles and set
actual_GUI_full_qualification:true only after those actual roles completed.
Missing/default false qualification refuses. high_budget is actual420/export120;
never fill a missing role from older GUI evidence. A later editor/control
mutation does not turn a pre-open snapshot into a current export claim.
No GUI, routing, Native, process control or historical experiment is rerun.
This file is prepared only; do not execute before final manifest/lead authority.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-033/runtime'
sys.path.insert(0, str(runtime))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, gui, local_settings as local

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--observations', type=Path, required=True)
args = parser.parse_args()
started = time.monotonic()
base = runtime / '.runs/gui-session074'
manifest = f.read_json(args.manifest)
observations = f.read_json(args.observations)
prepared = f.read_json(base / 'prepared-state.json')
assert type(manifest['schema']) is int and manifest['schema'] == 1 and manifest['finalized'] is True
assert observations.get('actual_GUI_full_qualification', False) is True
manifest_pin, observations_pin = p.sha(args.manifest), p.sha(args.observations)
self_pin = p.sha(Path(__file__))
tools = p.tool_manifest()
assert prepared['source_head'] == 'a476a0a0647bc51889d291e3e6e2598f4ec24370'
assert p.sha(runtime / 'runtime-distribution.json') == prepared['runtime_manifest_sha256'] == '115c881aa04a34bf642c57d5af312fe692d1aff013bed095caa3856a614f3987'
source = Path(prepared['source'])
assert p.tree_hash(source.parent) == prepared['source_hashes']
assert p.sha(Path(prepared['settings_path'])) == prepared['settings_sha256']
labels = ('positive', 'high_budget', 'cancel', 'reject', 'source_control', 'settings_control', 'export_control')
assert set(manifest['jobs']) == set(labels)
jobs = {label:Path(manifest['jobs'][label]).resolve() for label in labels}
assert all(work.is_relative_to(base / 'jobs') and work.is_dir() for work in jobs.values())
assert len(set(jobs.values())) == len(labels), 'Seven separately owned role workspaces required.'
assert {path.resolve() for path in (base / 'jobs').iterdir() if path.is_dir()} == set(jobs.values())
observed_roles = observations.get('observed_roles', [])
assert type(observed_roles) is list and len(observed_roles) == len(labels) and set(observed_roles) == set(labels)
assert tools['git_head'] == prepared['source_head'] and tools['kicad'] == '10.0.7'
assert tools['source_provenance']['manifest_sha256'] == prepared['runtime_manifest_sha256']
assert type(manifest['queued_race_forced_in_actual_GUI']) is bool
assert set(manifest['faults']) == {'source', 'settings', 'export'}
case_base = base / 'freshness-controls-001'
case_protocol_path = case_base / 'protocol-frozen-001.json'
case_protocol = f.read_json(case_protocol_path)
assert case_protocol['source_hashes'] == prepared['source_hashes']
assert case_protocol['settings'] == prepared['settings']
assert case_protocol['source_head'] == prepared['source_head']
assert case_protocol['runtime_manifest_sha256'] == prepared['runtime_manifest_sha256']
cancel_prepared_path = base / 'cancel-control-001/prepared.json'
cancel_prepared = f.read_json(cancel_prepared_path)
cancel_source = base / 'cancel-control-001/project/interf_u.kicad_pcb'
cancel_settings_path = base / 'cancel-control-001/route-settings.json'
cancel_settings = dict(prepared['settings'], scope='whole_board_unlocked_routing')
assert cancel_prepared['source'] == str(cancel_source)
assert cancel_prepared['settings'] == f.read_json(cancel_settings_path) == cancel_settings
assert cancel_prepared['runtime_manifest_sha256'] == prepared['runtime_manifest_sha256']
interf_packet_path = ROOT / 'evidence/runtime033-current-interf-comparison-001.json'
interf_packet = f.read_json(interf_packet_path)
interf_population = interf_packet['population']
assert cancel_prepared['source_hashes'] == interf_population['source_hashes']
assert cancel_prepared['source_rights'] == interf_population['source_rights']
assert interf_population['source_head'] == prepared['source_head']
assert interf_population['runtime_manifest_sha256'] == prepared['runtime_manifest_sha256']
assert len(cancel_prepared['source_hashes']) == 25
assert p.tree_hash(cancel_source.parent) == cancel_prepared['source_hashes']
role_sources = {label:source for label in labels}
for kind in ('source', 'settings', 'export'):
    role_sources[kind + '_control'] = case_base / kind / 'project' / source.name
role_sources['cancel'] = cancel_source
role_hashes = {label:prepared['source_hashes'] for label in labels}
role_hashes['cancel'] = cancel_prepared['source_hashes']

# Exact compact inventories avoid scanning the research archive. No code/binary
# payload is copied again; identical source/native companions share references.
references, reference_records = {}, []
for name in ('runtime033-ordinary-install-001.json', 'gui-runtime026-072-native-controls-001.json'):
    path = ROOT / 'evidence' / name
    old = f.read_json(path)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path),
        purpose='Exact-byte retention references only; no earlier GUI qualification inherited.'))
    if 'files' in old:
        retained = old['files']
    else:
        index = old['files_index']; index_path = ROOT / index['path']
        assert index_path.resolve().is_relative_to(ROOT / 'evidence') and p.sha(index_path) == index['sha256']
        index_data = f.read_json(index_path)
        retained = index_data.get('files', []) + index_data.get('material', [])
        reference_records.append(dict(path=index['path'], sha256=index['sha256'], purpose='Pinned exact-file index.'))
    assert type(retained) is list and len(retained) < 4000
    for row in retained:
        public = row.get('path', row.get('retained'))
        assert (ROOT / public).resolve().is_relative_to(ROOT / 'evidence')
        references.setdefault(row['sha256'], public)
# One already-public Interf member supplies exact source/license/Tux references;
# it supplies no GUI qualification or routing outcome to the cancellation role.
interf_member = interf_packet['packets'][0]
interf_member_path = ROOT / interf_member['path']
assert p.sha(interf_member_path) == interf_member['sha256']
interf_record = f.read_json(interf_member_path)
interf_index = interf_record['files_index']; interf_index_path = ROOT / interf_index['path']
assert p.sha(interf_index_path) == interf_index['sha256']
for path in (interf_packet_path, interf_member_path, interf_index_path):
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path),
        purpose='Exact licensed Interf cancellation source/attribution references only.'))
interf_index_data = f.read_json(interf_index_path)
for item in interf_index_data.get('files', []) + interf_index_data.get('material', []):
    public = item.get('path', item.get('retained'))
    assert (ROOT / public).resolve().is_relative_to(ROOT / 'evidence')
    references.setdefault(item['sha256'], public)
notes = ROOT / 'evidence/gui-runtime033-074-native-controls-001-notes'
rows, material, route_rows, export_rows, journals, faults = [], [], [], [], [], []
prl_packets, prl_pairs = [], []
copied_bytes = 0


def copy(path, relative):
    global copied_bytes
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    assert path.resolve().is_relative_to(ROOT)
    raw = io.read_bytes(path, 4 * 1024 ** 2)
    digest = hashlib.sha256(raw).hexdigest()
    public = references.get(digest)
    if public is None:
        # New payload remains text-only. An already-public licensed binary such
        # as Tux is referenced by exact hash; it is never newly copied here.
        assert b'\0' not in raw
        raw.decode('utf-8')
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
    captured = data['routing_preferences']['effective']
    role_source = role_sources[label]
    assert data['source'] == str(role_source) and data['source_hashes'] == role_hashes[label]
    assert data['tools'] == tools and data['budget_seconds'] == data['cpu_budget_seconds'] == captured['seconds']
    assert captured['scope'] == ('whole_board_unlocked_routing' if label == 'cancel' else 'partial_completion')
    assert captured['profile'] == 'standard'
    assert captured['adapter'] == 'both' and captured['guidance'] == 'native'
    assert captured['layers'] == 'source_all' and captured['scoring_preference'] is None
    assert p.sha(work / 'route' / data['routing_preferences']['file']) == data['routing_preferences']['sha256']
    assert p.tree_hash(work / 'route/snapshot') == role_hashes[label]
    assert all(step['cleanup_complete'] is True for step in data['steps'])
    if label != 'cancel':
        assert captured['seconds'] == (420 if label == 'high_budget' else 90)
    if label == 'cancel':
        assert captured == settings == cancel_settings
        assert data['accepted'] is False and data['status'] == 'cancelled'
        cancelled = [step for step in data['steps'] if step['status'] == 'cancelled']
        assert cancelled and all(step['cleanup_complete'] is True for step in cancelled)
        engine = [step for step in cancelled if step['name'] == 'engine']
        assert len(engine) == 1 and engine[0]['exit_code'] == -9 and engine[0]['cancel_signal'] == 'SIGINT'
        engine = engine[0]
        oracle_path = base / 'actual-engine-observation-001.json'
        cancellation_path = base / 'actual-GUI-cancellation-001.json'
        oracle = f.read_json(oracle_path); cancellation = f.read_json(cancellation_path)
        cli_process = f.read_json(work / 'route.command.process.json')
        assert oracle['workspace'] == cancellation['workspace'] == str(work)
        assert oracle['actual_engine_observed'] is True and cancellation['actual_GUI_cancel_clicked'] is True
        assert oracle['PID'] == cancellation['engine_PID'] == engine['pid']
        assert oracle['owned_ancestry'][:2] == [oracle['PID'], oracle['PPID']]
        assert oracle['PGID'] == engine['pid'] and len(oracle['owned_ancestry']) >= 3
        assert oracle['argv_text_sha256'] == hashlib.sha256(oracle['argv_text'].encode()).hexdigest()
        assert str(work / 'route/task.dsn') in oracle['argv_text']
        assert str(work / 'route/routes.ses') in oracle['argv_text']
        assert cancellation['engine_observation_sha256'] == p.sha(oracle_path)
        assert cancellation['CLI_process'] == cli_process
        assert cli_process['exit_code'] == 2 and cli_process['cancel_requested'] is True and cli_process['log_truncated'] is False
        assert cancellation['result_status'] == 'cancelled' and cancellation['accepted'] is False
        assert cancellation['export_created'] is False and cancellation['observed_phase'] == 'engine'
        assert not (work / 'export').exists()
        original = p.sx.read(work / 'route/snapshot' / cancel_source.name)
        assert len(p.protected_for_record(data, original)) == 0
        row = dict(label=label, status=data['status'], accepted=False,
                   source=str(cancel_source), source_hashes=role_hashes[label],
                   source_rights=cancel_prepared['source_rights'],
                   routing_scope='whole_board_unlocked_routing',
                   original_source_route_records=len(p.routes(original)), protected_route_items=0,
                   engine_PID=engine['pid'], actual_engine_observation_sha256=p.sha(oracle_path),
                   actual_GUI_cancellation_sha256=p.sha(cancellation_path),
                   cancelled_steps=[{key:step.get(key) for key in ('name', 'status', 'exit_code', 'cleanup_complete', 'wall_seconds', 'cpu_seconds')} for step in cancelled],
                   scope='Observed actual cancellation phase only; no accepted result, SIGINT-only or permanent-descendant guarantee.')
    else:
        assert data['accepted'] is True and data['invariants_unchanged'] is True and p.native_accepted(data['native'])
        assert [data['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
        original = p.sx.read(work / 'route/snapshot' / role_source.name)
        candidate = p.sx.read(Path(data['candidate']))
        assert p.sha(Path(data['candidate'])) == data['candidate_sha256']
        assert p.immutable(original) == p.immutable(candidate)
        protected = p.protected_for_record(data, original)
        assert len(protected) == 4 and all(item in p.routes(candidate) for item in protected)
        assert data['schematic_parity'] == 'checked by final native DRC'
        assert data['source_hashes'] == role_hashes[label]
        assert p.sha(work / 'route/final-drc.json') == data['native_report_sha256']
        if label in ('positive', 'high_budget'):
            with p.validation_readback_session():
                assert p.check_result(route_path)['current'] is True
        if label == 'high_budget':
            assert settings['seconds'] == captured['seconds'] == 420
        row = dict(label=label, status=data['status'], accepted=True,
                   candidate_sha256=data['candidate_sha256'], native=data['native'], metrics=data['metrics'],
                   native_report_sha256=data['native_report_sha256'], protected_route_items=len(protected),
                   schematic_parity=data['schematic_parity'], original_nonrouting_design_preserved=True,
                   scope='Own recorded completion proof; intentionally mutated control outputs are not reaccepted.' if 'control' in label else 'Own current route reader passed.' if label in ('positive', 'high_budget') else 'Own recorded Native proof; no new current acceptance inferred.')
    row.update(result_sha256=p.sha(route_path), captured_settings=captured,
               current_workspace_settings=settings, workspace_settings_sha256=p.sha(work / 'settings.json'))
    route_rows.append(row)
    prl_packets.append((work / 'route', data))
    for path in sorted(work.glob('*.command.process.json')):
        process = f.read_json(path)
        journals.append(dict(label=label, file=path.name, process=process))
    retain_tree(work / 'route', Path(label) / 'route')
    if label == 'cancel':
        for name in role_hashes[label]:
            copy(work / 'route/snapshot' / name, Path(label) / 'route/snapshot' / name)
    for path in sorted(work.glob('*.command.*')):
        copy(path, Path(label) / 'GUI-journals' / path.name)
    copy(work / 'settings.json', Path(label) / 'settings.json')
    for relative in ('review/review.json', 'choice/choice.json'):
        path = work / relative
        if path.is_file():
            copy(path, Path(label) / relative)
    if (work / 'review').is_dir():
        retain_tree(work / 'review', Path(label) / 'rendered-review')
        # Keep the same bounded copier, but explicitly retain plot material that
        # the generic tree helper deliberately skips with config/cache/workdirs.
        review_path = work / 'review/review.json'
        if review_path.is_file():
            preview = f.read_json(review_path)['preview']; plot = work / 'review/plot-work'
            assert preview['layers'] == ['F.Cu', 'B.Cu']
            for step in preview['steps']:
                assert step['cwd'] == str(plot) and step['exit_code'] == 0 and step['cleanup_complete'] is True
                name = step['name']; assert Path(name).name == name
                process = f.process_check(plot, preview, name, step['argv'])
                prl_pairs.append((plot, f.read_json(plot / (name + '-input-binding.json')), process))
                for suffix in ('-process.json', '-input-binding.json', '.log'):
                    copy(plot / (name + suffix), Path(label) / 'rendered-review/plot-work' / (name + suffix))
                retain_tree(plot / (name + '-input'), Path(label) / 'rendered-review/plot-work' / (name + '-input'))
            for folder in ('plots', 'native-plots'):
                retain_tree(plot / folder, Path(label) / 'rendered-review/plot-work' / folder)

rejected = f.read_json(jobs['reject'] / 'choice/choice.json')
assert rejected['choice'] == 'reject' and rejected['choice_recorded'] is True
assert not (jobs['reject'] / 'export').exists()
assert set(manifest['preopen']) == {'positive', 'high_budget', 'source_control', 'settings_control', 'export_control'}
for label, receipt_path in manifest['preopen'].items():
    assert label in jobs
    receipt_path = Path(receipt_path)
    pre = f.read_json(receipt_path)
    if label in ('positive', 'high_budget'):
        assert pre['source_unchanged'] is True
    else:
        assert pre['workspace'] == str(jobs[label]) and pre['source_hashes'] == role_hashes[label]
    route_data = f.read_json(jobs[label] / 'route/result.json')
    assert pre['route']['candidate'] == route_data['candidate']
    assert pre['route']['candidate_sha256'] == route_data['candidate_sha256']
    expected_candidate = jobs[label] / 'export/validation/candidate' / role_sources[label].name
    assert pre['export']['candidate'] == str(expected_candidate)
    assert pre['export']['original_routing_receipt'] == str(jobs[label] / 'route/result.json')
    assert pre['export']['export_accepted'] is True and pre['export']['applied'] is False
    snapshot = Path(pre['snapshot'])
    assert p.tree_hash(snapshot) == pre['snapshot_hashes']
    assert pre['route']['current'] is True and pre['export']['current'] is True
    exported = f.read_json(snapshot / 'export.json')
    assert exported['candidate'] == str(expected_candidate)
    assert pre['export']['candidate_sha256'] == exported['candidate_sha256']
    if label != 'positive':
        prl_packets.append((jobs[label] / 'export/validation', exported))
    else:
        post = f.read_json(base / 'postopen-001.json')
        assert post['workspace'] == str(jobs[label])
        assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
        assert p.tree_hash(Path(post['snapshot'])) == post['snapshot_hashes']
        assert p.sha(expected_candidate) == exported['candidate_sha256']
        for suffix in ('.kicad_pro', '.kicad_prl'):
            key = 'validation/candidate/' + role_sources[label].with_suffix(suffix).name
            assert post['changed'][key]['before'] == pre['snapshot_hashes'][key]
            assert post['changed'][key]['after'] == post['snapshot_hashes'][key]
            assert post['changed'][key]['before'] != post['changed'][key]['after']
    assert exported['inputs']['source'] == str(role_sources[label])
    assert exported['inputs']['receipt'] == str(jobs[label] / 'route/result.json')
    assert exported['inputs']['receipt_sha256'] == p.sha(jobs[label] / 'route/result.json')
    assert exported['export_accepted'] is True and p.native_accepted(exported['native'])
    assert [exported['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
    assert exported['schematic_parity'] == 'checked by final native DRC'
    candidate = snapshot / 'validation/candidate' / role_sources[label].name
    original = p.sx.read(jobs[label] / 'route/snapshot' / role_sources[label].name)
    assert p.sha(candidate) == exported['candidate_sha256']
    assert p.sha(snapshot / 'validation/final-drc.json') == exported['native_report_sha256']
    assert p.immutable(p.sx.read(candidate)) == p.immutable(original)
    protected = p.protected_for_record(f.read_json(jobs[label] / 'route/result.json'), original)
    assert len(protected) == 4 and all(item in p.routes(p.sx.read(candidate)) for item in protected)
    expected = gui.export_validation_seconds(f.read_json(jobs[label] / 'settings.json')['seconds'])
    assert exported['budget_seconds'] == exported['cpu_budget_seconds'] == expected
    if label == 'high_budget': assert expected == 120
    if label == 'positive': assert expected == 90
    export_rows.append(dict(label=label, preopen_receipt_sha256=p.sha(receipt_path), preopen_current=True,
        snapshot_hashes=pre['snapshot_hashes'], native=exported['native'], metrics=exported['metrics'],
        candidate_sha256=exported['candidate_sha256'], native_report_sha256=exported['native_report_sha256'],
        protected_route_items=4, schematic_parity=exported['schematic_parity'],
        additional_export_budget_seconds=exported['budget_seconds'],
        current_export_validation_PRL_replayed=label != 'positive',
        PRL_replay_scope='Positive export excluded from current metadata replay: actual editor changed PRO/PRL; frozen preopen proof and postopen change/refusal observations retained.' if label == 'positive' else 'Current owned validation-input metadata only; no reacceptance of intentionally stale source/settings/receipt.',
        current_after_open_or_mutation='Not inferred from the pre-open proof; later editor/control changes are retained separately.'))
    copy(receipt_path, Path(label) / 'observations/preopen.json')
    retain_tree(snapshot, Path(label) / 'preopen-export')
for kind, receipt_path in manifest['faults'].items():
    path = Path(receipt_path)
    fault = f.read_json(path)
    case = case_base / kind
    assert path == case / 'refusal-001.json' and fault['workspace'] == str(jobs[kind + '_control'])
    mutation_path = case / 'mutation-001.json'; mutation = f.read_json(mutation_path)
    assert fault['preopen_sha256'] == p.sha(case / 'preopen-001.json')
    assert fault['mutation_sha256'] == p.sha(mutation_path)
    assert mutation['kind'] == fault['kind'] == kind and mutation['original_source_untouched'] is True
    target = Path(mutation['path'])
    expected_target = (role_sources['source_control'].with_suffix('.kicad_pro') if kind == 'source'
        else jobs['settings_control'] / 'settings.json' if kind == 'settings'
        else jobs['export_control'] / 'export/export.json')
    assert target == expected_target and p.sha(target) == mutation['after_sha256']
    if kind == 'source':
        assert mutation['before_sha256'] == prepared['source_hashes'][target.name]
        assert io.read_bytes(target) == io.read_bytes(source.with_suffix('.kicad_pro')) + b'\n'
        expected_hashes = dict(prepared['source_hashes']); expected_hashes[target.name] = mutation['after_sha256']
        assert p.tree_hash(role_sources['source_control'].parent) == expected_hashes
    elif kind == 'settings':
        route_data = f.read_json(jobs['settings_control'] / 'route/result.json')
        prefs = f.read_json(jobs['settings_control'] / 'route' / route_data['routing_preferences']['file'])
        assert prefs['preset']['sha256'] == mutation['before_sha256']
        assert io.read_bytes(target) == prefs['preset']['raw_utf8'].encode('utf-8') + b'\n'
    else:
        pre = f.read_json(case / 'preopen-001.json'); before = Path(pre['snapshot']) / 'export.json'
        assert p.sha(before) == mutation['before_sha256']
        expected = f.read_json(before); assert expected['export_accepted'] is True
        expected['export_accepted'] = 1
        current = f.read_json(target)
        assert type(current['export_accepted']) is int and current['export_accepted'] == 1
        assert f.canonical(current) == f.canonical(expected)
    assert fault['no_positive_state_adopted'] is True and fault['GUI_open_buttons_disabled'] is True
    assert fault['retained_files_not_deleted'] is True
    assert fault['GUI_refusal_observed'] is True
    if manifest['queued_race_forced_in_actual_GUI']:
        assert fault['queue_hold_qualified'] is True
    faults.append(dict(kind=kind, receipt_sha256=p.sha(path), observed=fault))
    copy(path, Path('fault-controls') / kind / path.name)
    copy(mutation_path, Path('fault-controls') / kind / mutation_path.name)
    copy(target, Path('fault-controls') / kind / target.name)
for kind in ('settings', 'export'):
    assert p.tree_hash(role_sources[kind + '_control'].parent) == prepared['source_hashes']
copy(case_protocol_path, Path('observations') / case_protocol_path.name)
copy(cancel_prepared_path, Path('cancel/observations/prepared.json'))
copy(cancel_settings_path, Path('cancel/observations/route-settings.json'))
for name in cancel_prepared['source_hashes']:
    copy(cancel_source.parent / name, Path('cancel/source') / name)
for path in [args.manifest, args.observations, base / 'prepared-state.json',
             base / 'route-settings.json', base / 'routing-settings-saved-GUI074-001.json', *map(Path, manifest['additional_files'])]:
    copy(path, Path('observations') / path.parent.name.lstrip('.') / path.name)
assert f.read_json(base / 'route-settings.json') == f.read_json(base / 'routing-settings-saved-GUI074-001.json') == prepared['settings']
for name in prepared['source_hashes']:
    copy(source.parent / name, Path('source') / name)
copy(Path(__file__).resolve(), Path('controllers') / Path(__file__).name)
assert p.tree_hash(source.parent) == prepared['source_hashes']
assert p.tree_hash(cancel_source.parent) == cancel_prepared['source_hashes']
assert p.sha(args.manifest) == manifest_pin and p.sha(args.observations) == observations_pin
assert p.sha(Path(__file__)) == self_pin and p.tool_manifest() == tools
assert p.sha(runtime / 'runtime-distribution.json') == prepared['runtime_manifest_sha256']
for item in material:
    assert p.sha(ROOT / item['original']) == item['sha256'], 'Source material changed during curation.'
index = dict(schema=1, files=rows, material=material,
             scope='Exact essential text copies/references; no new Native or acceptance framework. Binary captures, code/config/cache and complete raw workspaces stay local.')
notes.mkdir(parents=True, exist_ok=True)
with (notes / 'files.json').open('x') as stream:
    json.dump(index, stream, indent=2); stream.write('\n')
record = dict(schema=1, kind='actual-runtime033-GUI074-native-controls', project_complete=False,
    actual_GUI=True, actual_GUI_full_qualification=observations['actual_GUI_full_qualification'],
    human_review=False, full_release_qualified=False,
    runtime_manifest_sha256=prepared['runtime_manifest_sha256'], source_head=prepared['source_head'],
    original_source_project_bytes_unchanged=True, source_hashes=prepared['source_hashes'],
    cancellation_source_hashes=cancel_prepared['source_hashes'],
    cancellation_source_rights=cancel_prepared['source_rights'],
    observations=observations, observed_roles=observed_roles, finalized_manifest_sha256=manifest_pin,
    observations_sha256=observations_pin, curator_sha256=self_pin,
    route_rows=route_rows, positive_exports=export_rows,
    GUI_process_journals=journals, stale_controls=faults,
    queued_race_forced_in_actual_GUI=manifest['queued_race_forced_in_actual_GUI'],
    scope='Actual final observations are supplied by the lead. Six positive owned2Cu partial Route proofs preserve4protected records; cancellation alone uses already-exposed licensed Interf whole/default90 for an observable engine interval. Own Route/export Native/full-schematic/original/protected proofs, refusal, cancellation, rejection and high-budget behavior remain individually scoped. Actual seven declared074 roles only, no inherited026 qualification or independent breadth/routing-quality/electrical/human claim.',
    cost_scope='Actual stage process journals retained. Whole interactive wall/full CPU including authoring, idle, curation and AI review is unmeasured, not zero. Native completion proofs are not rerun by this curator.',
    reference_records=reference_records, license_reference=dict(path='LICENSE', sha256=p.sha(ROOT / 'LICENSE'),
        scope='Main fixture/controller are project-owned. Interf cancellation source/attribution/license bytes retain their separate declared rights and exact existing public references; nothing is relicensed.'),
    curation_wall_seconds_before_publication=time.monotonic() - started,
    files=rows, files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
# Existing shared metadata replay is last, after all source/tool/material/index
# callbacks. Four exports retain current owned validation-input metadata checks;
# the editor-stale positive export keeps only its frozen preopen proof and is
# explicitly excluded. No metadata check reaccepts an edited project/receipt.
local.check_final_events(prl_packets, p.c.CLI, pairs=prl_pairs)
with (ROOT / 'evidence/gui-runtime033-074-native-controls-001.json').open('x') as stream:
    json.dump(record, stream, indent=2); stream.write('\n')
print(json.dumps(dict(files=len(rows), bytes=copied_bytes, actual_GUI=True,
                     queued_race_forced=manifest['queued_race_forced_in_actual_GUI'], source_unchanged=True)))
