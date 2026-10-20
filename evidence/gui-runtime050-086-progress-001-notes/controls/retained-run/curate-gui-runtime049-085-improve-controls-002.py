"""Draft metadata retainer for three assigned049/085 GUI roles; never run readers.

The saved pre-editor export is authoritative only for that earlier observation.
No CAD, DSN, SES, SVG/pixels, engine, cache or application payload is published.
Run only after lead review; failure leaves any newly created packet for inspection.
"""
from pathlib import Path
import ast, datetime, hashlib, json, os, resource, sys, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io

RUNTIME = ROOT / '.runs/runtime-directory-049/runtime'
BASE = RUNTIME / '.runs/gui-session085'
WORK = BASE / 'jobs/autorouter-gui-984da32b73c74099837c9a6ce9c3556c'
REJECT = BASE / 'jobs/autorouter-gui-f5132af931b84a5a8e65b6c4916a3038'
CANCEL = BASE / 'jobs/autorouter-gui-195967275c2c4d3ab8d63fcb5f3ed2ab'
CONTROL = BASE / 'preopen-improve-fractional-001'
HEAD = '6e2357f975554478c2ba9fa35f18fdc3c1d194f9'
MANIFEST = '70a388a6844d015350073401cb5f33bb1d552d1dc6195ece3aceee27baba5bd4'
PREPARED = '9858d0cf8cfdd46249c723ebe5c24bbb9c7568d8733ca92d476ec90633ea9e7e'
PROTOCOL = '8375e15546d48b5795828d04a5ecc47ac1d41a7cee7c3c75efe3e3911469512c'
JOURNAL = ROOT / '.runs/gui085-observations-005.json'
PREOPEN = '079146d4921becfdef30096ce4c216fc3604b50f72a1c3be01d51622bfcae310'
CANDIDATE = '040a5b38af8b1b96e96bed6f44dbc1a88f9618f9ddd9c44f6ba69cf43bb79de8'
RETENTION = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
FINAL_HELPER = ROOT / '.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
DEPENDENCY = ROOT / 'evidence/runtime049-native-milestone-002.json'
PINS = {
    RETENTION: 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',
    FINAL_HELPER: '340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',
    DEPENDENCY: 'a2030b472e0c15a6a32e40a6ae0968f863e98a1bde5e9537825f109f1876b646',
    BASE / 'prepared-state.json': PREPARED,
    BASE / 'protocol-required-001.json': PROTOCOL,
    JOURNAL: 'dffd6d21ded9d29ab69220087edbe282799844fc802c000f23c560cfbaac9d94',
    ROOT / '.runs/gui085-observations-004.json': '73c68705f1487a5979909571d6dd752c1eef3aec19df070fc4539d27e541c48d',
    CONTROL / 'preopen.json': PREOPEN,
    CONTROL / 'postopen-observed.json': 'a4736890d544a60896824291966f34532357870717e9f585b4487ab7e033ba54',
    WORK / 'route/result.json': '7f29bf88975b6b01cbae43ad4122f56615d7d5e7520e34e077d218058dc2f70b',
    WORK / 'route/incumbent/result.json': '28eb7fe54638fd898a00904f06f16bf3b5944f0877216ddf63ba0b464d5dc68e',
    WORK / 'route/trials/trial-0000/result.json': 'ebba828d6562ef8e846bb21245df42b2acb91273401b4d0efd15bb33c3b9b446',
    REJECT / 'route/result.json': '061b93db0baf79ca1aff4e621be1b872186fcf5fe2bd2aa144925bbea6e86fa4',
    CANCEL / 'route/result.json': '2f41c1e27efd423ed63b23fedae90642379aa9a278b392a834dc3ccaddfdfe76',
    ROOT / '.runs/gui085-preopen-001.py': '362a84dd76d5688b31ac3a228b7e4b455bff9b8a1f05e2fa9b7f3d1fec0f40ab',
}
COUNTS = ('opens', 'blocking', 'warnings', 'exclusions')


def load_functions(path, names):
    nodes = [n for n in ast.parse(io.read_bytes(path, 4 * 1024**2)).body
             if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), globals())


def main():
    global notes, refs, files, material, total
    start = time.monotonic(); cpu0 = time.process_time()
    stem = 'gui-runtime049-085-improve-controls-002'
    notes = ROOT / 'evidence' / (stem + '-notes'); output = ROOT / 'evidence' / (stem + '.json')
    assert not os.path.lexists(notes) and not os.path.lexists(output), 'Fresh exclusive packet required'
    for path, pin in PINS.items(): assert p.sha(path) == pin, str(path)
    load_functions(RETENTION, ('retain', 'cost'))
    load_functions(FINAL_HELPER, ('read', 'own_final'))
    prepared = read(BASE / 'prepared-state.json'); protocol = read(BASE / 'protocol-required-001.json')
    journal = read(JOURNAL)
    for data in (prepared, protocol, journal):
        assert data['source_head'] == HEAD and data['runtime_manifest_sha256'] == MANIFEST
    assert journal['runtime'] == '049' and journal['session'] == '085'
    assert journal['actual_GUI_qualified'] is False and journal['human_review'] is False
    assert journal['prior_journal']['sha256'] == PINS[ROOT / '.runs/gui085-observations-004.json']
    assert journal['preopen_receipt']['sha256'] == PREOPEN
    assert journal['postopen_receipt']['sha256'] == PINS[CONTROL / 'postopen-observed.json']
    assert p.sha(RUNTIME / 'runtime-distribution.json') == MANIFEST
    for name, pin in prepared['tools']['implementation_sha256'].items(): assert p.sha(RUNTIME / name) == pin
    for name, pin in prepared['prerequisite_sha256'].items(): assert p.sha(Path(name)) == pin
    roles = {}; source_inventories = {}
    for label in ('improve-fractional', 'ordinary-alias2Cu'):
        role = prepared['roles'][label]; assert role == protocol['roles'][label]
        source = Path(role['source']); hashes = role['source_hashes']
        assert BASE in source.parents and io.inventory(source.parent) == hashes
        assert io.inventory(Path(role['original_source']).parent) == hashes
        assert journal['source_inventories_unchanged'][label] == hashes
        assert read(Path(role['settings_path'])) == role['settings']
        roles[label] = role; source_inventories[source.parent] = hashes
    role = roles['improve-fractional']; ordinary = roles['ordinary-alias2Cu']
    source = Path(role['source']); hashes = role['source_hashes']
    assert role['method'] == 'improve' and role['settings'] == dict(schema=1,
        scope='whole_board_unlocked_routing', seconds=90, adapter='both', profile='tuned',
        guidance='native', layers='source_all', scoring_preference=None)
    observations = {}
    for label, work in (('Improve_fractional_delivery', WORK), ('fresh_rejection', REJECT), ('actual_GUI_cancel', CANCEL)):
        rows = [r for r in journal['observations'] if r.get('role') == label]
        assert len(rows) == 1 and rows[0]['actual_gui'] is True and rows[0]['workspace'] == str(work)
        observations[label] = rows[0]
    for work, policy in ((WORK, role), (REJECT, ordinary), (CANCEL, ordinary)):
        assert read(work / 'settings.json') == policy['settings']
        data = read(work / 'route/result.json')
        assert data['source'] == policy['source'] and data['source_hashes'] == policy['source_hashes']
        assert data['tools'] == prepared['tools'] and data['budget_seconds'] == data['cpu_budget_seconds'] == 90

    pre = read(CONTROL / 'preopen.json'); post = read(CONTROL / 'postopen-observed.json')
    before = CONTROL / 'export'; before_hashes = io.inventory(before, max_bytes=64 * 1024**2)
    assert before_hashes == pre['snapshot_hashes'] and len(before_hashes) == 98
    assert pre['snapshot'] == str(before) and pre['workspace'] == post['workspace'] == str(WORK)
    assert pre['source'] == str(source) and pre['source_hashes'] == hashes and pre['source_unchanged'] is True
    assert pre['settings_sha256'] == p.sha(WORK / 'settings.json')
    assert pre['source_head'] == HEAD and pre['runtime_manifest_sha256'] == MANIFEST
    assert pre['route']['current'] is True and pre['export']['current'] is True
    assert pre['export']['fresh_native_run_performed_by_check'] is False
    assert post['preopen_receipt_sha256'] == PREOPEN and post['preopen_snapshot_unchanged'] is True
    assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
    assert post['actual_GUI_opening'] is True and post['human_review'] is False
    current = io.inventory(WORK / 'export', max_bytes=64 * 1024**2)
    changes = {name: dict(before=before_hashes.get(name), after=current.get(name))
        for name in sorted(set(before_hashes) | set(current)) if before_hashes.get(name) != current.get(name)}
    assert changes == post['current_export_changes'] and len(changes) == 3
    assert sorted(Path(name).suffix for name in changes) == ['.kicad_prl', '.kicad_pro', '.zip']

    parent = read(WORK / 'route/result.json'); incumbent = read(WORK / 'route/incumbent/result.json')
    trial_folder = WORK / 'route/trials/trial-0000'; trial = read(trial_folder / 'result.json')
    exported = read(before / 'export.json'); rejected = read(REJECT / 'route/result.json')
    assert parent['accepted'] is True and parent['invariants_unchanged'] is True
    assert parent['protected_routes'] == 1 and parent['improvements'] == 1
    assert parent['incumbent']['receipt'] == str(WORK / 'route/incumbent/result.json')
    assert parent['trials'] == [dict(id='trial-0000', receipt=str(trial_folder / 'result.json'),
                                   status='improvement_validated', accepted=True)]
    assert sorted(d.name for d in (WORK / 'route/trials').iterdir()) == ['trial-0000']
    assert incumbent['accepted'] is True and trial['accepted'] is True and trial['status'] == 'improvement_validated'
    assert trial['base_candidate_sha256'] == incumbent['candidate_sha256']
    assert trial['candidate_sha256'] == parent['candidate_sha256'] == CANDIDATE
    assert exported['export_accepted'] is True and exported['applied'] is False
    assert exported['original_geometry_and_routing_unchanged'] is True
    assert exported['tools'] == prepared['tools']
    assert exported['candidate_sha256'] == CANDIDATE and exported['source_hashes'] == hashes
    assert exported['inputs']['source'] == str(source)
    assert exported['inputs']['receipt'] == str(WORK / 'route/result.json')
    assert exported['inputs']['receipt_sha256'] == PINS[WORK / 'route/result.json']
    assert exported['budget_seconds'] == exported['cpu_budget_seconds'] == 90
    guide = read(WORK / 'route/incumbent/default-targets.json')
    assert p.sha(WORK / 'route/incumbent/default-targets.json') == incumbent['default_target_transport']['sha256']
    own = {}
    for label, record, folder, actual, source_map, protected in (
        ('incumbent', incumbent, WORK / 'route/incumbent', WORK / 'route/incumbent', hashes, 1),
        ('trial-0000', trial, trial_folder, trial_folder, hashes, 1),
        ('parent', parent, WORK / 'route', WORK / 'route', hashes, 1),
        ('export', exported, before / 'validation', WORK / 'export/validation', hashes, 1),
        ('reject-route', rejected, REJECT / 'route', REJECT / 'route', ordinary['source_hashes'], 4)):
        candidate = actual / 'candidate' / source.name
        assert [record['native'][k] for k in COUNTS] == ([0, 0, 0, 0] if label == 'reject-route' else [0, 0, 6, 0])
        own[label] = own_final(record, folder, actual, source_map, candidate)
        audit = read(folder / 'final-netclass-audit.json')
        assert audit['candidate_sha256'] == record['candidate_sha256']
        assert audit['project_sha256'] == source_map[source.with_suffix('.kicad_pro').name]
        assert audit['native_map_file_sha256'] == p.sha(folder / 'final-netclasses.json')
        assert audit['native']['passed'] is True and audit['route_dimensions']['passed'] is True
        assert audit['route_dimensions']['checked']['protected'] == protected
        if label != 'reject-route':
            assert all(audit['default_targets'][k] == guide[k] for k in ('raw_nm', 'original_floors_nm', 'derived_nm'))
            field = record['native']['field_parity']
            assert field == read(folder / 'final-drc-fields-proof.json')
            assert field['native_report_sha256'] == record['native_report_sha256']
            assert field['binding_sha256'] == p.sha(folder / 'final-drc-binding.json')
            assert field['netlist_sha256'] == p.sha(folder / 'final-drc-fields.net')
            assert field['fields_sha256'] == p.sha(folder / 'final-drc-fields.json')
        own[label].update(candidate_sha256=record['candidate_sha256'], native=record['native'],
                          metrics=record['metrics'], protected_original_items=protected,
                          final_netclass_audit_sha256=p.sha(folder / 'final-netclass-audit.json'))
    for work, choice_name, route_pin in ((WORK, 'accept', PINS[WORK / 'route/result.json']),
                                         (REJECT, 'reject', PINS[REJECT / 'route/result.json'])):
        review = read(work / 'review/review.json'); choice = read(work / 'choice/choice.json')
        candidate_pin = read(work / 'route/result.json')['candidate_sha256']
        assert review['receipt_sha256'] == choice['receipt_sha256'] == route_pin
        assert review['candidate_sha256'] == choice['validated_candidate_sha256'] == candidate_pin
        assert choice['review_sha256'] == p.sha(work / 'review/review.json')
        assert choice['choice'] == choice_name and choice['choice_recorded'] is True and choice['applied'] is False
        assert choice['human_pcb_approval_observed'] is False
    assert not os.path.lexists(REJECT / 'export')
    cancelled = read(CANCEL / 'route/result.json'); cancel_proc = read(CANCEL / 'route.command.process.json')
    assert cancelled['accepted'] is False and cancelled['status'] == 'cancelled'
    assert cancelled['reason'] == 'interrupted route' and cancel_proc['exit_code'] == 2 and cancel_proc['cancel_requested'] is True
    cancel_steps = [step for step in cancelled['steps'] if step.get('status') == 'cancelled']
    assert len(cancel_steps) == 1
    last = cancel_steps[0]
    assert last['name'] == 'metrics' and last['argv'][2] == 'metrics' and last['cwd'] == str(CANCEL / 'route')
    assert last['pid'] == 93041 and last['exit_code'] == -15 and last['cancel_signal'] == 'SIGINT' and last['cleanup_complete'] is True
    assert observations['actual_GUI_cancel']['cancelled_step'] == {k: last[k] for k in
        ('name', 'status', 'exit_code', 'pid', 'cancel_signal', 'cleanup_complete')}
    assert observations['actual_GUI_cancel']['recorded_pids_or_groups_present'] == []
    for name in ('review', 'choice', 'export'): assert not os.path.lexists(CANCEL / name)
    assert all(step['cleanup_complete'] is True for record in (parent, incumbent, trial, exported, rejected, cancelled)
               for step in record['steps'])

    refs = {}; files = []; material = []; total = 0
    dep = read(DEPENDENCY); dep_index = ROOT / dep['files_index']['path']
    assert p.sha(dep_index) == dep['files_index']['sha256'] == 'ba8601a190a99df8bd9445daa8489f5b60639059f4c34793178c5593427f855d'
    for row in read(dep_index)['files']: refs.setdefault(row['sha256'], row['path'])
    queue = {}; roots = {}; samples = []
    def add(path, name):
        path = Path(path); assert path.is_file() and not path.is_symlink() and ROOT in path.parents
        queue.setdefault(path, Path(name))
    def metadata(folder, name):
        inventory = io.inventory(folder, max_bytes=64 * 1024**2); roots[folder] = inventory
        for rel in inventory:
            path = folder / rel; parts = Path(rel).parts
            if (len(parts) == 1 and path.suffix in ('.json', '.log', '.net')) or (
                len(parts) == 2 and parts[0] in ('final-drc-input', 'refill-drc-input', 'source-drc-input')
                and path.suffix == '.kicad_prl'):
                add(path, Path(name) / rel)
    for path in PINS: add(path, Path('controls') / str(path.relative_to(ROOT)).replace('.runs/', 'retained-run/'))
    add(RUNTIME / 'runtime-distribution.json', 'runtime/runtime-distribution.json')
    add(Path(__file__), 'curation/' + Path(__file__).name); add(ROOT / 'LICENSE', 'rights/LICENSE')
    add(before / 'export.json', 'before-open/export/export.json')
    for label, policy in roles.items(): add(Path(policy['settings_path']), 'settings/' + label + '.json')
    for work in (WORK, REJECT, CANCEL):
        name = work.name; add(work / 'settings.json', Path('jobs') / name / 'settings.json')
        metadata(work / 'route', Path('jobs') / name / 'route')
        for part in ('review', 'review/plot-work', 'choice'):
            if (work / part).is_dir(): metadata(work / part, Path('jobs') / name / part)
        for path in sorted(work.glob('*.command.process.json')):
            process = read(path); log = path.with_name(path.name.replace('.process.json', '.log'))
            assert process['argv'][:4] == [str(RUNTIME / '.venv/bin/python'), '-B', '-m', 'autorouter']
            assert process['log_truncated'] is False and log.stat().st_size == process['log_bytes']
            assert process['exit_code'] == (2 if work == CANCEL and path.name == 'route.command.process.json' else 0)
            assert process['cancel_requested'] is (work == CANCEL and path.name == 'route.command.process.json')
            samples.append(dict(workspace=str(work), stage=path.name, receipt_sha256=p.sha(path),
                                log_sha256=p.sha(log), sample=process))
            add(path, Path('commands') / name / path.name); add(log, Path('commands') / name / log.name)
    metadata(WORK / 'route/incumbent', 'improve/incumbent')
    metadata(trial_folder, 'improve/trial-0000'); metadata(before / 'validation', 'before-open/export/validation')
    measured = {}
    for name in ('gui085-preopen-improve-fractional-001.log', 'gui085-preopen-improve-fractional-001-time.log'):
        add(ROOT / '.runs' / name, Path('costs') / name)
        if name.endswith('-time.log'): measured[name] = cost(ROOT / '.runs' / name)
    omitted = []
    for folder, inventory in roots.items():
        for rel, pin in inventory.items():
            path = folder / rel
            if path not in queue:
                omitted.append(dict(original=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=pin,
                    reason='Not copied: CAD/transport/pixels/config/code or other nonessential raw; complete originals remain local.'))
    known = set(refs); planned = count = 0; frozen = {}
    for path in queue:
        raw = io.read_bytes(path, 4 * 1024**2); assert b'\0' not in raw; raw.decode('utf-8')
        pin = hashlib.sha256(raw).hexdigest(); frozen[path] = (len(raw), pin)
        if pin not in known: known.add(pin); planned += len(raw); count += 1
    assert planned < 16 * 1024**2 and count < 2000, ('Split packet before writing; never raise caps', planned, count)
    notes.mkdir()
    for path, name in queue.items(): retain(path, name)
    for path, (size, pin) in frozen.items(): assert path.stat().st_size == size and p.sha(path) == pin
    for folder, inventory in roots.items(): assert io.inventory(folder, max_bytes=64 * 1024**2) == inventory
    for folder, inventory in source_inventories.items(): assert io.inventory(folder) == inventory
    assert io.inventory(before, max_bytes=64 * 1024**2) == before_hashes
    assert io.inventory(WORK / 'export', max_bytes=64 * 1024**2) == current
    index = notes / 'files.json'; p.save_json(index, dict(schema=1, files=files, material=material, omitted=omitted))
    summary = dict(schema=1, kind='runtime049-GUI085-assigned-Improve-reject-and-Native-metrics-cancel-only',
        recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_head=HEAD,
        runtime_manifest_sha256=MANIFEST, prepared_state_sha256=PREPARED, journal_sha256=PINS[JOURNAL],
        actual_GUI_qualified=False, full_GUI_claim=False, project_complete=False, human_review=False,
        physical_electrical_validation=False, sources_unchanged=True, source_inventories=journal['source_inventories_unchanged'],
        Improve=dict(workspace=str(WORK), settings=role['settings'], candidate_sha256=CANDIDATE,
            incumbent_candidate_sha256=incumbent['candidate_sha256'], own_final_bindings=own,
            improvements=parent['improvements'], trials=parent['trials'], native=parent['native'], metrics=parent['metrics'],
            before_open=dict(snapshot=str(before), files=len(before_hashes), receipt_sha256=PREOPEN,
                current_production_readers_then=True, actual_to_preserved_mapping={str(WORK / 'export'): str(before)}),
            after_open=dict(receipt_sha256=PINS[CONTROL / 'postopen-observed.json'], actual_checked_opening_recorded=True,
                source_and_candidate_PCB_unchanged=True, changes=changes, new_Native_validity_inferred=False,
                current_post_editor_export_validity_claim=False)),
        rejection=dict(workspace=str(REJECT), choice='reject', accepted_routing_candidate=True, export_absent=True,
                       human_approval=False),
        cancellation=dict(workspace=str(CANCEL), parent_accepted=False, parent_status=cancelled['status'],
            CLI_exit_code=2, cancel_requested=True, actual_cancelled_step=last,
            no_review_choice_export=True, raw_schematic_parity_text=cancelled['schematic_parity'],
            completed_prior_Native_steps_retained=True, final_candidate_acceptance_claim=False,
            engine_cancellation_proved=False, all_phase_cancellation_proved=False,
            phase_note='Native metrics cancelled after final DRC; old source-drc GUI tail was not the worker phase.'),
        actual_GUI_observations=observations, pending_roles=journal['remaining_roles'],
        accounting=dict(CLI_command_samples=samples,
            CLI_command_wall_sum_seconds=sum(r['sample']['wall_seconds'] for r in samples),
            CLI_command_CPU_seconds=None, whole_interactive_wall_seconds=None, whole_interactive_CPU_seconds=None,
            additional_measured_helpers=measured, raw_journal_accounting=journal['accounting'],
            nested_samples={label: {key: record.get(key) for key in ('wall_seconds', 'total_cpu_seconds')}
                for label, record in (('parent', parent), ('incumbent', incumbent), ('export', exported), ('reject-route', rejected), ('cancel-route', cancelled))},
            limitation='Command wall overlaps nested Native/engine/parent samples. Do not add nested costs again. Interactive and authoring costs unknown, not zero.'),
        dependency=dict(path=str(DEPENDENCY.relative_to(ROOT)), sha256=PINS[DEPENDENCY], files_index=dep['files_index'],
                        scope='Owned fixture rights and immutable mechanics only; no prior GUI proof transfer.'),
        publication=dict(new_files=len(files), new_bytes=total, material_rows=len(material), file_cap=4 * 1024**2,
            packet_cap=16 * 1024**2, file_count_cap=2000,
            scope='Owned GPL metadata/log/net/PRL proof only. CAD/DSN/SES/SVG/pixels/ZIP/code/tools/cache remain local; raw outside010, not a restoration copy.'),
        limitations='Three assigned GUI roles only. Lead-observed Edge/checked KiCad opening; no independent human review, full cohort, exact queued callback, recovery, broader quality, superiority, electrical, Windows or restoration claim. Runtime049 predates the separate root summary-refresh patch.',
        curation=dict(sampled_wall_seconds=time.monotonic() - start, sampled_parent_CPU_seconds=time.process_time() - cpu0,
                      complete_external_exit_not_included=True, Native_executed=False, production_readers_rerun=False),
        files_index=dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index)))
    p.save_json(output, summary)
    print(json.dumps(dict(output=str(output), sha256=p.sha(output), files=len(files), bytes=total,
                          material=len(material), actual_GUI_qualified=False, Native_executed=False)))


if __name__ == '__main__':
    main()
