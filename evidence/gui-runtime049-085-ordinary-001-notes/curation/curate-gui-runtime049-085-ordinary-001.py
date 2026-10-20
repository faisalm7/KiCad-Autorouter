"""Retain only completed049/085 ordinary GUI evidence; never run Native/readers.

Exact frozen journal and pre-editor export storage are separate from the actual
worker paths in their receipts. CAD/ZIP/pixels/tools remain local; no full GUI,
Improve, current post-editor export validity or human approval is inferred.
"""
from pathlib import Path
import ast, datetime, hashlib, json, os, resource, sys, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io

RUNTIME = ROOT / '.runs/runtime-directory-049/runtime'
BASE = RUNTIME / '.runs/gui-session085'
WORK = BASE / 'jobs/autorouter-gui-fe5a4f4bad8145d19dd63c825907d994'
CONTROL = BASE / 'preopen-ordinary-alias-001'
HEAD = '6e2357f975554478c2ba9fa35f18fdc3c1d194f9'
MANIFEST = '70a388a6844d015350073401cb5f33bb1d552d1dc6195ece3aceee27baba5bd4'
PREPARED = '9858d0cf8cfdd46249c723ebe5c24bbb9c7568d8733ca92d476ec90633ea9e7e'
PROTOCOL = '8375e15546d48b5795828d04a5ecc47ac1d41a7cee7c3c75efe3e3911469512c'
JOURNAL = '16151b160a3eac02d14d187cc2e81aa106652ccea45e0e7c8e9d365f1c1d47b0'
PREOPEN = '689453264ecd938345df4b4ddff996f874e38450e66b5c30260827c5e9afecf1'
POSTOPEN = 'd9911997017586ea59708fbdb9deac90afb7751598a2a33d2fd83937c9dacf9e'
ROUTE = 'de3cad7b94e50e34db2f122d9cd871c73b9c1751d582d619928f14b75cf6e795'
CANDIDATE = '09ee58c3ad89674c368aa814dc13a9564b96596186441936ef64686ab4f39117'
SETTINGS = 'a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65'
JOB_SETTINGS = '2258e809e1efc6a1020ef0f55f2f63eecb5ebc126f6ae3d554658e94a5753880'
RETENTION = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
FINAL_HELPER = ROOT / '.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
DEPENDENCY = ROOT / 'evidence/runtime049-native-milestone-002.json'
PINS = {
    RETENTION: 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',
    FINAL_HELPER: '340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',
    DEPENDENCY: 'a2030b472e0c15a6a32e40a6ae0968f863e98a1bde5e9537825f109f1876b646',
    BASE / 'prepared-state.json': PREPARED,
    BASE / 'protocol-required-001.json': PROTOCOL,
    ROOT / '.runs/gui085-observations-003.json': JOURNAL,
    CONTROL / 'preopen.json': PREOPEN,
    CONTROL / 'postopen-observed.json': POSTOPEN,
    WORK / 'route/result.json': ROUTE,
    ROOT / '.runs/gui085-preopen-001.py': '362a84dd76d5688b31ac3a228b7e4b455bff9b8a1f05e2fa9b7f3d1fec0f40ab',
}


def load_functions(path, names):
    nodes = [node for node in ast.parse(io.read_bytes(path, 4 * 1024**2)).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), globals())


def main():
    global notes, refs, files, material, total
    start = time.monotonic(); cpu0 = time.process_time()
    stem = 'gui-runtime049-085-ordinary-001'
    notes = ROOT / 'evidence' / (stem + '-notes'); output = notes.with_name(stem + '.json')
    assert not os.path.lexists(notes) and not os.path.lexists(output), 'Fresh packet required; retain partial failure, never reuse'
    for path, pin in PINS.items(): assert p.sha(path) == pin, str(path)
    load_functions(RETENTION, ('retain', 'cost'))
    load_functions(FINAL_HELPER, ('read', 'own_final'))
    prepared = read(BASE / 'prepared-state.json'); protocol = read(BASE / 'protocol-required-001.json')
    journal_path = ROOT / '.runs/gui085-observations-003.json'; journal = read(journal_path)
    for data in (prepared, protocol, journal):
        assert data['source_head'] == HEAD and data['runtime_manifest_sha256'] == MANIFEST
    assert journal['runtime'] == '049' and journal['session'] == '085' and journal['prepared_state_sha256'] == PREPARED
    assert journal['actual_GUI_qualified'] is False and journal['human_review'] is False
    assert journal['active_workspace'] == str(WORK)
    assert p.sha(RUNTIME / 'runtime-distribution.json') == MANIFEST
    for name, pin in prepared['tools']['implementation_sha256'].items(): assert p.sha(RUNTIME / name) == pin
    for name, pin in prepared['prerequisite_sha256'].items(): assert p.sha(Path(name)) == pin
    role = prepared['roles']['ordinary-alias2Cu']; source = Path(role['source']); hashes = role['source_hashes']
    assert role == protocol['roles']['ordinary-alias2Cu'] and role['method'] == 'route'
    assert source == BASE / 'project/owned1007-transport.kicad_pcb'
    assert io.inventory(source.parent) == io.inventory(Path(role['original_source']).parent) == hashes
    assert read(WORK / 'settings.json') == read(Path(role['settings_path'])) == role['settings']
    assert role['settings'] == dict(schema=1, scope='partial_completion', seconds=90, adapter='both',
                                   profile='standard', guidance='native', layers='source_all', scoring_preference=None)
    assert p.sha(WORK / 'settings.json') == JOB_SETTINGS and p.sha(Path(role['settings_path'])) == SETTINGS
    saved = BASE / 'gui085-saved-settings.json'; assert p.sha(saved) == SETTINGS and read(saved) == role['settings']
    labels = ('current_toolbar_launch', 'source_ack_refusal', 'route60_preview', 'invalid_budget_refusal',
              'settings_persistence', 'ordinary_alias_protected_route', 'ordinary_alias_rendered_review',
              'ordinary_alias_accept_intent', 'ordinary_alias_fresh_export_completed',
              'ordinary_alias_checked_opening', 'editor_changed_export_refusal')
    selected = {}
    for label in labels:
        rows = [row for row in journal['observations'] if row['role'] == label]
        assert len(rows) == 1 and rows[0]['actual_gui'] is True
        if label.startswith('ordinary_alias_') or label == 'editor_changed_export_refusal':
            assert rows[0]['workspace'] == str(WORK)
        selected[label] = rows[0]
    assert selected['ordinary_alias_protected_route']['route_receipt_sha256'] == ROUTE
    assert selected['ordinary_alias_protected_route']['candidate_sha256'] == CANDIDATE
    pre = read(CONTROL / 'preopen.json'); post = read(CONTROL / 'postopen-observed.json')
    before = CONTROL / 'export'; before_hashes = io.inventory(before, max_bytes=64 * 1024**2)
    assert before_hashes == pre['snapshot_hashes'] and len(before_hashes) == 90
    assert pre['snapshot'] == str(before) and pre['workspace'] == post['workspace'] == str(WORK)
    assert pre['source'] == str(source) and pre['source_hashes'] == hashes and pre['source_unchanged'] is True
    assert pre['settings_sha256'] == JOB_SETTINGS and pre['controller_sha256'] == PINS[ROOT / '.runs/gui085-preopen-001.py']
    assert pre['source_head'] == HEAD and pre['runtime_manifest_sha256'] == MANIFEST
    assert pre['route']['current'] is True and pre['export']['current'] is True
    assert pre['export']['fresh_native_run_performed_by_check'] is False
    assert post['preopen_receipt_sha256'] == PREOPEN and post['preopen_snapshot_unchanged'] is True
    assert post['original_source_unchanged'] is True and post['preopen_Native_not_renewed'] is True
    current = io.inventory(WORK / 'export', max_bytes=64 * 1024**2)
    changes = {name: dict(before=before_hashes.get(name), after=current.get(name))
               for name in sorted(set(before_hashes) | set(current)) if before_hashes.get(name) != current.get(name)}
    assert changes == post['current_export_changes'] and len(changes) == 3
    assert sorted(Path(name).suffix for name in changes) == ['.kicad_prl', '.kicad_pro', '.zip']
    route = read(WORK / 'route/result.json'); exported = read(before / 'export.json')
    assert route['accepted'] is True and route['invariants_unchanged'] is True
    assert route['scope'] == 'partial_completion' and route['adapter'] == 'both' and route['engine_profile'] == 'standard'
    assert route['scoring_variant'] is None and route['routing_preferences']['effective'] == role['settings']
    assert route['budget_seconds'] == route['cpu_budget_seconds'] == exported['budget_seconds'] == exported['cpu_budget_seconds'] == 90
    assert exported['export_accepted'] is True and exported['applied'] is False
    assert exported['original_geometry_and_routing_unchanged'] is True
    assert exported['inputs']['source'] == route['source'] == str(source)
    assert exported['inputs']['receipt'] == str(WORK / 'route/result.json') and exported['inputs']['receipt_sha256'] == ROUTE
    for record in (route, exported):
        assert record['source_hashes'] == hashes and record['tools'] == prepared['tools']
        assert record['schematic_parity'] == 'checked by final native DRC' and record['candidate_sha256'] == CANDIDATE
        assert [record['native'][name] for name in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
        assert len(record['native']['ignored_checks']) == 2
    assert route['candidate'] == str(WORK / 'route/candidate' / source.name)
    assert exported['candidate'] == str(WORK / 'export/validation/candidate' / source.name)
    own = dict(route=own_final(route, WORK / 'route', WORK / 'route', hashes, route['candidate']),
               export=own_final(exported, before / 'validation', WORK / 'export/validation', hashes, exported['candidate']))
    original = p.sx.read(source); protected = p.protected_for_record(route, original); assert len(protected) == 4
    for candidate in (Path(route['candidate']), before / 'validation/candidate' / source.name):
        tree = p.sx.read(candidate); assert p.immutable(tree) == p.immutable(original)
        assert all(item in p.routes(tree) for item in protected) and p.sha(candidate) == CANDIDATE
    assert p.sha(Path(exported['candidate'])) == CANDIDATE
    guide = read(WORK / 'route/default-targets.json')
    assert p.sha(WORK / 'route/default-targets.json') == route['default_target_transport']['sha256']
    for folder in (WORK / 'route', before / 'validation'):
        audit = read(folder / 'final-netclass-audit.json')
        assert audit['candidate_sha256'] == CANDIDATE and audit['project_sha256'] == hashes[source.with_suffix('.kicad_pro').name]
        assert audit['native']['passed'] is True and audit['route_dimensions']['passed'] is True
        assert audit['route_dimensions']['checked']['protected'] == 4
        assert audit['native_map_file_sha256'] == p.sha(folder / 'final-netclasses.json')
        assert all(audit['default_targets'][key] == guide[key] for key in ('raw_nm', 'original_floors_nm', 'derived_nm'))
    review = read(WORK / 'review/review.json'); choice = read(WORK / 'choice/choice.json')
    assert review['receipt_sha256'] == choice['receipt_sha256'] == ROUTE and review['candidate_sha256'] == CANDIDATE
    assert choice['choice'] == 'accept' and choice['applied'] is False and choice['human_pcb_approval_observed'] is False
    assert choice['review_sha256'] == p.sha(WORK / 'review/review.json') and choice['validated_candidate_sha256'] == CANDIDATE

    refs = {}; files = []; material = []; total = 0
    dep = read(DEPENDENCY); index_path = ROOT / dep['files_index']['path']
    assert p.sha(index_path) == dep['files_index']['sha256'] == 'ba8601a190a99df8bd9445daa8489f5b60639059f4c34793178c5593427f855d'
    for row in read(index_path)['files']: refs.setdefault(row['sha256'], row['path'])
    queue = {}; omitted = []; samples = []
    def add(path, name):
        path = Path(path); assert path.is_file() and not path.is_symlink() and ROOT in path.parents
        queue.setdefault(path, Path(name))
    def metadata(folder, name):
        for rel, pin in io.inventory(folder, max_bytes=64 * 1024**2).items():
            path = folder / rel; parts = Path(rel).parts
            allowed = (len(parts) == 1 and path.suffix in ('.json', '.log', '.net')) or (
                parts[0] in ('final-drc-input', 'refill-drc-input', 'source-drc-input') and path.suffix == '.kicad_prl')
            if allowed: add(path, Path(name) / rel)
            else: omitted.append(dict(original=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=pin,
                                      reason='Raw CAD/transport/config/code remains local; metadata-only public packet.'))
    for path in PINS: add(path, Path('controls') / path.name)
    add(RUNTIME / 'runtime-distribution.json', 'runtime/runtime-distribution.json')
    add(WORK / 'settings.json', 'job/settings.json'); add(saved, 'settings/gui085-saved-settings.json')
    add(Path(role['settings_path']), 'settings/route-settings.json'); add(Path(__file__), 'curation/' + Path(__file__).name)
    add(ROOT / 'LICENSE', 'rights/LICENSE')
    for name in ('gui085-observations-001.json', 'gui085-observations-002.json', 'prepare-runtime049-gui085.py',
                 'prepare-runtime049-gui085.log', 'prepare-runtime049-gui085-time.log',
                 'gui085-preopen-ordinary-alias-001.log', 'gui085-preopen-ordinary-alias-001-time.log', 'gui085-launch.log'):
        add(ROOT / '.runs' / name, Path('setup-and-controls') / name)
    metadata(WORK / 'route', 'job/route'); metadata(before / 'validation', 'before-open/export/validation')
    add(before / 'export.json', 'before-open/export/export.json')
    metadata(WORK / 'review', 'job/review'); metadata(WORK / 'review/plot-work', 'job/review/plot-work')
    metadata(WORK / 'choice', 'job/choice')
    preview_work = Path(selected['route60_preview']['workspace'])
    assert preview_work.parent == BASE / 'jobs' and preview_work != WORK
    for path in sorted(preview_work.glob('*.command.*')): add(path, Path('earlier-static-preview') / path.name)
    for path in sorted(WORK.glob('*.command.process.json')):
        process = read(path); log = path.with_name(path.name.replace('.process.json', '.log'))
        assert process['argv'][:4] == [str(RUNTIME / '.venv/bin/python'), '-B', '-m', 'autorouter']
        assert process['cancel_requested'] is False and process['log_truncated'] is False
        assert log.stat().st_size == process['log_bytes']
        if path.name == 'inspect-export-15a50ad192264fe59a316b1e624f7c47.command.process.json':
            assert process['exit_code'] == 2 and read(log) == dict(current=False, reason='export inputs/runtime/evidence changed')
        else: assert process['exit_code'] == 0
        samples.append(dict(stage=path.name, receipt_sha256=p.sha(path), log_sha256=p.sha(log), sample=process))
        add(path, Path('commands') / path.name); add(log, Path('commands') / log.name)
    assert len(samples) == 8
    complete = {name: cost(ROOT / '.runs' / name) for name in (
        'prepare-runtime049-gui085-time.log', 'gui085-preopen-ordinary-alias-001-time.log')}
    # Preflight exact text payload, unchanged publication caps, before any notes write.
    known = set(refs); planned = 0; count = 0; frozen = {}
    for path in queue:
        raw = io.read_bytes(path, 4 * 1024**2); assert b'\0' not in raw; raw.decode('utf-8')
        pin = hashlib.sha256(raw).hexdigest(); frozen[path] = (len(raw), pin)
        if pin not in known: known.add(pin); planned += len(raw); count += 1
    assert planned < 16 * 1024**2 and count < 2000, ('Split packet before writing; do not raise caps', planned, count)
    notes.mkdir()
    for path, name in queue.items(): retain(path, name)
    # Recheck every selected byte, originals and preserved export after copying.
    for path, (size, pin) in frozen.items(): assert path.stat().st_size == size and p.sha(path) == pin
    assert io.inventory(source.parent) == hashes and io.inventory(before, max_bytes=64 * 1024**2) == before_hashes
    assert io.inventory(WORK / 'export', max_bytes=64 * 1024**2) == current
    index = notes / 'files.json'; p.save_json(index, dict(schema=1, files=files, material=material, omitted=omitted))
    summary = dict(schema=1, kind='runtime049-GUI085-assigned-ordinary-role-only',
        recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_head=HEAD,
        runtime_manifest_sha256=MANIFEST, prepared_state_sha256=PREPARED, journal_sha256=JOURNAL,
        assigned_ordinary_role_recorded=True, actual_GUI_qualified=False, Improve_qualified=False,
        project_complete=False, human_review=False, physical_electrical_validation=False,
        source=str(source), source_hashes=hashes, source_unchanged=True, workspace=str(WORK),
        settings=role['settings'], job_settings_sha256=JOB_SETTINGS, saved_settings_sha256=SETTINGS,
        settings_serialization='Exact two byte hashes retained; decoded policies equal.',
        candidate_sha256=CANDIDATE, protected_original_items=4, native=route['native'], metrics=route['metrics'],
        own_final_bindings=own, before_open=dict(snapshot=str(before), files=90, current_production_readers_then=True,
            receipt_sha256=PREOPEN, actual_to_preserved_mapping={str(WORK / 'export'): str(before)}),
        after_open=dict(receipt_sha256=POSTOPEN, changes=changes, candidate_PCB_unchanged=True,
            new_Native_validity_inferred=False, current_export_refused=True, exact_CallAfter_queue_proved=False),
        actual_GUI_observations=selected, pending_roles=journal['remaining_roles'],
        accounting=dict(CLI_command_samples=samples,
            CLI_command_wall_sum_seconds=sum(row['sample']['wall_seconds'] for row in samples),
            CLI_command_CPU_seconds=None, whole_interactive_wall_seconds=None, whole_interactive_CPU_seconds=None,
            nested_route=dict(wall_seconds=route['wall_seconds'], CPU_seconds=route['total_cpu_seconds']),
            nested_export=dict(wall_seconds=exported['wall_seconds'], CPU_seconds=exported['total_cpu_seconds']),
            additional_measured_helpers=complete, authoring_and_postopen_observation_cost='Unmeasured; not zero.',
            raw_journal_accounting=journal['accounting'], correction='The no-Native/no-GUI-job clause in frozen003 is contradicted by its Route/export roles. Actual GUI job and Native stages occurred; whole interactive CPU/wall remain unknown. Nested worker samples are included in their CLI command intervals; do not add them again.'),
        dependency=dict(path=str(DEPENDENCY.relative_to(ROOT)), sha256=PINS[DEPENDENCY], files_index=dep['files_index'],
            scope='Immutable source/licensing/mechanics references only; no prior GUI proof transfer.'),
        publication=dict(new_files=len(files), new_bytes=total, material_rows=len(material), file_cap=4 * 1024**2,
            packet_cap=16 * 1024**2, file_count_cap=2000,
            scope='Small owned metadata/log/net and PRL proof only; no CAD, ZIP, pixels, engines, apps or caches copied. Raw preopen snapshot remains Mac-only outside010; not full restore or self-contained CAD replay.'),
        limitations='One assigned ordinary partial90 GUI control. Owner-assisted toolbar, actual Edge F/B and checked KiCad opening recorded by lead; no independent human review, electrical/physical approval, full049GUI, Improve, performance/comparison/general quality or exact queued CallAfter claim.',
        curation=dict(sampled_wall_seconds=time.monotonic() - start, sampled_parent_CPU_seconds=time.process_time() - cpu0,
            complete_external_exit_not_included=True, Native_executed=False, production_readers_rerun=False),
        files_index=dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index)))
    p.save_json(output, summary)
    print(json.dumps(dict(output=str(output), sha256=p.sha(output), files=len(files), bytes=total,
                          material=len(material), actual_GUI_qualified=False, Native_executed=False)))


if __name__ == '__main__':
    main()
