"""DRAFT: retain the fixed GUI086 progress cutoff; no readers/Native execution.

Ordinary checked opening is recorded; Improve has completed stored CLI/export
proof but export UI completion and checked opening remain unobserved at cutoff.
Reuse bounded shared retention/own-final metadata readers, never renew validity.
"""
from pathlib import Path
import ast, datetime, hashlib, json, os, resource, sys, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io

RUNTIME = ROOT / '.runs/runtime-directory-050/runtime'
BASE = RUNTIME / '.runs/gui-session086'
ORDINARY = BASE / 'jobs/autorouter-gui-f6fa0829280542b2bbf6bc43fe3eda7f'
IMPROVE = BASE / 'jobs/autorouter-gui-ebbbf11a7fdb441d8375dda0b2c2300c'
HEAD = 'aa0072c6b3d8090de2603e5ecb42a95968fb873b'
MANIFEST = 'c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
PREPARED = '59243bac41824b5efa2a336a53d3ff59bd6d725bf61a9686d3315575fe74a7ae'
RETENTION = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
FINAL_HELPER = ROOT / '.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
DEPENDENCY = ROOT / 'evidence/runtime050-native-milestone-002.json'
PINS = {
    RETENTION: 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',
    FINAL_HELPER: '340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',
    DEPENDENCY: '1d0d2019d5505f1fad0134cc2163b3337ce227e1b8d841c8c3c8a81e21a94934',
    BASE / 'prepared-state.json': PREPARED,
    BASE / 'protocol-required-001.json': '622e76392b4aa72b7eceab24ce471046bfc1a3f90c3635900bc1c5bcd23e83e0',
    ROOT / '.runs/gui086-observations-001.json': '5ba64adf6a422e8335e571e0fbb381d58a3de0fcacc1e55767d4084e45720d3c',
    ROOT / '.runs/gui086-observations-002.json': '1c8c145b1229913c02f5e6444069673f2b9db72afdbdcdff3d7b5084dc61ed58',
    ROOT / '.runs/gui086-observations-003.json': '18f42f4d03a9819e32406232d3b28d6e8924d5204d2f00f7260f36fc04b57033',
    BASE / 'preopen-ordinary-001/preopen.json': '74076e9a2ee26b2ee075f9303d284318a911be8e079f2c55d9c71e4d28dd31fa',
    BASE / 'preopen-ordinary-001/postopen-001.json': '43d24e9d60a5326cff9cb8e79e4d5bada90e89fc30a75a216c2953918c8d7777',
    BASE / 'preopen-improve-001/preopen.json': 'bb0b691b8d4d5a77e6af877280a1b99cd479a31a9691c703488e53fa9deeec44',
    ORDINARY / 'route/result.json': 'cf8ecf509123dbf692f6cf0e3ae81c7943696b7ad31e352dadef974a33410406',
    IMPROVE / 'route/result.json': '7f63cd461d0a3d26a7ec01f8fd7be6628716170490b6b80b64ee181156173a84',
    IMPROVE / 'route/incumbent/result.json': 'a154edc4126d790f1df811df8c0fd15d5b96d75c98b6a758ad4546a677af3087',
    IMPROVE / 'route/trials/trial-0000/result.json': '9e0d0f2b1d18d4986635e55b6c327197a54086f78d9a82f9c2f2da159c0bb249',
    ROOT / '.runs/gui086-preopen-001.py': '086469a5703aa3673f3906e2a7051a9c0e29238efc6c06bb9866d174272539b1',
    ROOT / '.runs/curate-gui-runtime049-085-ordinary-001.py': 'ae3d0f3f127523e35a4e73d29cf2b84da15d7c05998d0d1f1c846ca0066f0672',
    ROOT / '.runs/curate-gui-runtime049-085-improve-controls-002.py': 'ede2fe9a518a2e5beb751b361b4b8eb33e402aa542ce9c3f1ecc079a4b44ece4',
}
COUNTS = ('opens', 'blocking', 'warnings', 'exclusions')
STALE_COMMAND = 'inspect-export-34dfc531fd04434e82035cd732f2f0ac.command.process.json'


def load_functions(path, names):
    nodes = [n for n in ast.parse(io.read_bytes(path, 4 * 1024**2)).body
             if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), globals())


def main():
    global notes, refs, files, material, total
    start = time.monotonic(); cpu0 = time.process_time()
    stem = 'gui-runtime050-086-progress-001'
    notes = ROOT / 'evidence' / (stem + '-notes'); output = ROOT / 'evidence' / (stem + '.json')
    assert not os.path.lexists(notes) and not os.path.lexists(output), 'Fresh exclusive packet required; retain any failure'
    for path, pin in PINS.items(): assert p.sha(path) == pin, str(path)
    load_functions(RETENTION, ('retain', 'cost')); load_functions(FINAL_HELPER, ('read', 'own_final'))
    prepared = read(BASE / 'prepared-state.json'); protocol = read(BASE / 'protocol-required-001.json')
    journals = [read(ROOT / ('.runs/gui086-observations-00' + str(i) + '.json')) for i in (1, 2, 3)]
    first, second, cutoff = journals
    assert all(j['runtime'] == '050' and j['session'] == '086' and j['actual_GUI'] is True
               and j['project_complete'] is False for j in journals)
    assert all(j['source_head'] == HEAD and j['manifest_sha256'] == MANIFEST for j in (first, second))
    for data in (prepared, protocol): assert data['source_head'] == HEAD and data['runtime_manifest_sha256'] == MANIFEST
    assert second['previous']['sha256'] == PINS[ROOT / '.runs/gui086-observations-001.json']
    assert cutoff['previous']['sha256'] == PINS[ROOT / '.runs/gui086-observations-002.json']
    assert cutoff['access']['owner_requested_once'] is True and cutoff['access']['security_or_sleep_changes'] is False
    assert cutoff['improve']['actual_checked_export_open'] is False
    assert cutoff['improve']['export_UI_completion_not_observed_after_lock'] is True
    assert p.sha(RUNTIME / 'runtime-distribution.json') == MANIFEST
    for name, pin in prepared['tools']['implementation_sha256'].items(): assert p.sha(RUNTIME / name) == pin
    for name, pin in prepared['prerequisite_sha256'].items(): assert p.sha(Path(name)) == pin
    source_inventories = {}; facts = {}; records = {}; owned_roots = []; snapshots = {}
    for role_name, work, control, count, counts, protected in (
        ('ordinary-alias2Cu', ORDINARY, BASE / 'preopen-ordinary-001', 90, [0, 0, 0, 0], 4),
        ('improve-fractional', IMPROVE, BASE / 'preopen-improve-001', 98, [0, 0, 6, 0], 1)):
        role = prepared['roles'][role_name]; assert role == protocol['roles'][role_name]
        source = Path(role['source']); hashes = role['source_hashes']
        assert BASE in source.parents and io.inventory(source.parent) == io.inventory(Path(role['original_source']).parent) == hashes
        source_inventories[source.parent] = hashes
        assert read(work / 'settings.json') == read(Path(role['settings_path'])) == role['settings']
        route = read(work / 'route/result.json'); before = control / 'export'; exported = read(before / 'export.json')
        pre = read(control / 'preopen.json'); before_hashes = io.inventory(before, max_bytes=64 * 1024**2)
        assert before_hashes == pre['snapshot_hashes'] and len(before_hashes) == count
        assert pre['snapshot'] == str(before) and pre['workspace'] == str(work) and pre['role'] == role_name
        assert pre['source'] == str(source) and pre['source_hashes'] == hashes and pre['source_unchanged'] is True
        assert pre['source_head'] == HEAD and pre['runtime_manifest_sha256'] == MANIFEST
        assert pre['settings_sha256'] == p.sha(work / 'settings.json')
        assert pre['route']['current'] is True and pre['export']['current'] is True
        assert pre['export']['fresh_native_run_performed_by_check'] is False and pre['actual_GUI_opening'] is False
        assert pre['controller_sha256'] == PINS[ROOT / '.runs/gui086-preopen-001.py']
        assert route['accepted'] is True and route['invariants_unchanged'] is True
        assert route['source'] == role['source'] and route['source_hashes'] == exported['source_hashes'] == hashes
        assert route['tools'] == exported['tools'] == prepared['tools']
        assert route['budget_seconds'] == route['cpu_budget_seconds'] == exported['budget_seconds'] == exported['cpu_budget_seconds'] == 90
        assert exported['export_accepted'] is True and exported['applied'] is False and exported['original_geometry_and_routing_unchanged'] is True
        assert exported['inputs']['source'] == str(source) and exported['inputs']['receipt'] == str(work / 'route/result.json')
        assert exported['inputs']['receipt_sha256'] == PINS[work / 'route/result.json']
        assert route['candidate_sha256'] == exported['candidate_sha256'] == pre['route']['candidate_sha256'] == pre['export']['candidate_sha256']
        assert p.sha(Path(exported['candidate'])) == route['candidate_sha256']
        packets = [('route', route, work / 'route', work / 'route'),
                   ('export', exported, before / 'validation', work / 'export/validation')]
        guide_root = work / 'route'
        if role_name == 'improve-fractional':
            guide_root /= 'incumbent'; incumbent = read(guide_root / 'result.json')
            trial_root = work / 'route/trials/trial-0000'; trial = read(trial_root / 'result.json')
            assert route['protected_routes'] == 1 and route['improvements'] == 1
            assert route['incumbent']['receipt'] == str(guide_root / 'result.json')
            assert route['trials'] == [dict(id='trial-0000', receipt=str(trial_root / 'result.json'), status='improvement_validated', accepted=True)]
            assert sorted(q.name for q in (work / 'route/trials').iterdir()) == ['trial-0000']
            assert incumbent['accepted'] is True and trial['accepted'] is True and trial['status'] == 'improvement_validated'
            assert trial['base_candidate_sha256'] == incumbent['candidate_sha256']
            assert trial['candidate_sha256'] == route['candidate_sha256']
            packets += [('incumbent', incumbent, guide_root, guide_root), ('trial-0000', trial, trial_root, trial_root)]
        guide = read(guide_root / 'default-targets.json')
        guide_record = read(guide_root / 'result.json')
        assert guide_record['default_target_transport']['sha256'] == p.sha(guide_root / 'default-targets.json')
        own = {}
        for label, data, folder, actual in packets:
            assert [data['native'][key] for key in COUNTS] == counts
            own[label] = own_final(data, folder, actual, hashes, actual / 'candidate' / source.name)
            audit = read(folder / 'final-netclass-audit.json')
            assert audit['candidate_sha256'] == data['candidate_sha256'] and audit['project_sha256'] == hashes[source.with_suffix('.kicad_pro').name]
            assert audit['native_map_file_sha256'] == p.sha(folder / 'final-netclasses.json')
            assert audit['native']['passed'] is True and audit['route_dimensions']['passed'] is True
            assert audit['route_dimensions']['checked']['protected'] == protected
            assert all(audit['default_targets'][key] == guide[key] for key in ('raw_nm', 'original_floors_nm', 'derived_nm'))
            if counts[2]:
                field = data['native']['field_parity']; assert field == read(folder / 'final-drc-fields-proof.json')
                for key, name in (('native_report_sha256', 'final-drc.json'), ('binding_sha256', 'final-drc-binding.json'),
                    ('netlist_sha256', 'final-drc-fields.net'), ('fields_sha256', 'final-drc-fields.json'),
                    ('local_settings_guard_sha256', 'final-drc-fields-local-settings.json')):
                    assert field[key] == p.sha(folder / name)
            own[label].update(candidate_sha256=data['candidate_sha256'], native=data['native'], metrics=data['metrics'], protected_original_items=protected)
            owned_roots.append((folder, Path(role_name) / label))
        review = read(work / 'review/review.json'); choice = read(work / 'choice/choice.json')
        assert review['receipt_sha256'] == choice['receipt_sha256'] == PINS[work / 'route/result.json']
        assert review['candidate_sha256'] == choice['validated_candidate_sha256'] == route['candidate_sha256']
        assert choice['choice'] == 'accept' and choice['choice_recorded'] is True and choice['applied'] is False
        assert choice['review_sha256'] == p.sha(work / 'review/review.json') and choice['human_pcb_approval_observed'] is False
        snapshots[before] = before_hashes
        records[role_name] = dict(route=route, exported=exported, work=work, before=before, role=role)
        facts[role_name] = dict(workspace=str(work), source=str(source), source_hashes=hashes, settings=role['settings'],
            candidate_sha256=route['candidate_sha256'], native=route['native'], metrics=route['metrics'],
            protected_original_items=protected, own_final_bindings=own, source_unchanged=True,
            preopen=dict(receipt_sha256=p.sha(control / 'preopen.json'), files=count,
                current_readers_then=True, new_Native_run_by_curator=False, actual_to_preserved_mapping={str(work / 'export'): str(before)}))
    ordinary = second['ordinary']; improve = cutoff['improve']
    assert ordinary['workspace'] == str(ORDINARY) and improve['workspace'] == str(IMPROVE)
    assert ordinary['route_sha256'] == PINS[ORDINARY / 'route/result.json'] and improve['route_sha256'] == PINS[IMPROVE / 'route/result.json']
    for data, label in ((ordinary, 'ordinary-alias2Cu'), (improve, 'improve-fractional')):
        assert data['native'] == [facts[label]['native'][k] for k in COUNTS]
        assert data['export_sha256'] == p.sha(records[label]['before'] / 'export.json')
    assert ordinary['actual_checked_export_open'] is True and ordinary['stale_editor_modified_export_refused'] is True
    assert improve['fresh_export_and_CLI_check_complete'] is True and improve['HTML_findings_exactly_match_route'] is True
    post_path = BASE / 'preopen-ordinary-001/postopen-001.json'; post = read(post_path)
    old = snapshots[BASE / 'preopen-ordinary-001/export']; current = io.inventory(ORDINARY / 'export', max_bytes=64 * 1024**2)
    changes = {name: dict(before=old.get(name), after=current.get(name)) for name in sorted(set(old) | set(current)) if old.get(name) != current.get(name)}
    assert post['preopen_sha256'] == PINS[BASE / 'preopen-ordinary-001/preopen.json']
    assert changes == post['post_editor_differences'] and current == post['current_export_inventory']
    assert len(changes) == 3 and sorted(Path(n).suffix for n in changes) == ['.kicad_prl', '.kicad_pro', '.zip']
    assert post['actual_GUI_opened'] is True and post['actual_PCB_inspected'] is True
    assert post['candidate_PCB_unchanged'] is True and all(post['source_originals_unchanged'].values())
    facts['ordinary-alias2Cu']['postopen'] = dict(receipt_sha256=PINS[post_path], actual_checked_opening=True,
        candidate_PCB_unchanged=True, changes=changes, current_export_stale_refusal_recorded=True,
        new_Native_validity_inferred=False)
    facts['improve-fractional']['GUI_cutoff'] = dict(actual_ack_accept_recorded=True,
        detailed_six_warnings_and_F_B_images_recorded=True, fresh_export_CLI_proof_complete=True,
        export_UI_completion_observed=False, checked_export_opening_observed=False,
        access=cutoff['access'], current_post_editor_export_validity_inferred=False)

    refs = {}; files = []; material = []; total = 0
    dep = read(DEPENDENCY); dep_index = ROOT / dep['files_index']['path']
    assert p.sha(dep_index) == dep['files_index']['sha256'] == '43563b463b68370228482318fcc16e490624ac1b51fe0e4029ed652bd4015e71'
    for row in read(dep_index)['files']: refs.setdefault(row['sha256'], row['path'])
    queue = {}; roots = {}; samples = []; measured = {}
    def add(path, name):
        path = Path(path); assert path.is_file() and not path.is_symlink() and ROOT in path.parents
        queue.setdefault(path, Path(name))
    def metadata(folder, name):
        inv = io.inventory(folder, max_bytes=64 * 1024**2); roots[folder] = inv
        for rel in inv:
            path = folder / rel; parts = Path(rel).parts
            if (len(parts) == 1 and path.suffix in ('.json', '.log', '.net')) or (len(parts) == 2
                and parts[0] in ('final-drc-input', 'refill-drc-input', 'source-drc-input') and path.suffix == '.kicad_prl'):
                add(path, Path(name) / rel)
    for path in PINS: add(path, Path('controls') / str(path.relative_to(ROOT)).replace('.runs/', 'retained-run/'))
    add(RUNTIME / 'runtime-distribution.json', 'runtime/runtime-distribution.json')
    add(Path(__file__), 'curation/' + Path(__file__).name); add(ROOT / 'LICENSE', 'rights/LICENSE')
    for label, rec in records.items():
        work = rec['work']; add(work / 'settings.json', Path(label) / 'settings.json')
        add(Path(rec['role']['settings_path']), Path(label) / 'prepared-settings.json')
        add(rec['before'] / 'export.json', Path(label) / 'before-open/export.json')
        metadata(work / 'review', Path(label) / 'review'); metadata(work / 'review/plot-work', Path(label) / 'review/plot-work')
        metadata(work / 'choice', Path(label) / 'choice')
        commands = sorted(work.glob('*.command.process.json'))
        assert len(commands) == (8 if work == ORDINARY else 6), 'Fixed cutoff command population changed'
        for path in commands:
            proc = read(path); log = path.with_name(path.name.replace('.process.json', '.log'))
            assert proc['argv'][:4] == [str(RUNTIME / '.venv/bin/python'), '-B', '-m', 'autorouter']
            assert proc['cancel_requested'] is False and proc['log_truncated'] is False and log.stat().st_size == proc['log_bytes']
            if path.name == STALE_COMMAND:
                assert work == ORDINARY and proc['exit_code'] == 2 and read(log) == dict(current=False, reason='export inputs/runtime/evidence changed')
                assert p.sha(log) == ordinary['stale_refusal_log_sha256']
            else: assert proc['exit_code'] == 0
            if work == IMPROVE:
                stage = path.name.split('.command.')[0]; assert p.sha(path) == improve['processes'][stage]['sha256']
            samples.append(dict(role=label, command=path.name, receipt_sha256=p.sha(path), log_sha256=p.sha(log), sample=proc))
            add(path, Path(label) / 'commands' / path.name); add(log, Path(label) / 'commands' / log.name)
    for folder, label in owned_roots: metadata(folder, label)
    for prefix in ('gui086-ordinary-preopen-001', 'gui086-improve-preopen-001'):
        for suffix in ('.log', '-time.log'): add(ROOT / '.runs' / (prefix + suffix), Path('costs') / (prefix + suffix))
        measured[prefix] = cost(ROOT / '.runs' / (prefix + '-time.log'))
    omitted = [dict(original=str((folder / rel).relative_to(ROOT)), bytes=(folder / rel).stat().st_size, sha256=pin,
        reason='CAD/transport/SVG/pixels/ZIP/config/code or nonessential raw remains local; see material for separately retained metadata.')
        for folder, inv in roots.items() for rel, pin in inv.items() if folder / rel not in queue]
    known = set(refs); planned = count = 0; frozen = {}
    for path in queue:
        raw = io.read_bytes(path, 4 * 1024**2); assert b'\0' not in raw; raw.decode('utf-8')
        pin = hashlib.sha256(raw).hexdigest(); frozen[path] = (len(raw), pin)
        if pin not in known: known.add(pin); planned += len(raw); count += 1
    assert planned < 16 * 1024**2 and count < 2000, ('Split before writing; never raise caps', planned, count)
    notes.mkdir()
    for path, name in queue.items(): retain(path, name)
    for path, (size, pin) in frozen.items(): assert path.stat().st_size == size and p.sha(path) == pin
    for folder, inv in roots.items(): assert io.inventory(folder, max_bytes=64 * 1024**2) == inv
    for folder, inv in source_inventories.items(): assert io.inventory(folder) == inv
    for folder, inv in snapshots.items(): assert io.inventory(folder, max_bytes=64 * 1024**2) == inv
    assert io.inventory(ORDINARY / 'export', max_bytes=64 * 1024**2) == current
    index = notes / 'files.json'; p.save_json(index, dict(schema=1, files=files, material=material, omitted=omitted))
    summary = dict(schema=1, kind='runtime050-GUI086-two-job-progress-cutoff-v1',
        recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_head=HEAD,
        runtime_manifest_sha256=MANIFEST, prepared_state_sha256=PREPARED,
        journals=[dict(path='.runs/gui086-observations-00' + str(i) + '.json', sha256=PINS[ROOT / ('.runs/gui086-observations-00' + str(i) + '.json')]) for i in (1, 2, 3)],
        actual_GUI_observed=True, actual_GUI_qualified=False, full_GUI_claim=False, project_complete=False,
        human_review=False, physical_electrical_validation=False, roles=facts,
        observations=dict(initial=first['events'], ordinary=second['ordinary'], Improve=cutoff['improve']),
        pending_at_cutoff=dict(Improve_export_UI_completion=True, Improve_checked_opening=True,
            reject=True, cancel=True, freshness=True, recovery=True, exact_queued_callback_proof=True),
        access_at_cutoff=cutoff['access'], owner_action_resolution_inferred=False,
        accounting=dict(CLI_command_samples=samples, CLI_command_wall_sum_seconds=sum(r['sample']['wall_seconds'] for r in samples),
            CLI_command_CPU_seconds=None, whole_interactive_wall_seconds=None, whole_interactive_CPU_seconds=None,
            additional_measured_preopen_helpers=measured,
            nested_samples={label: {name: {key: data.get(key) for key in ('wall_seconds', 'total_cpu_seconds')}
                for name, data in (('route', rec['route']), ('export', rec['exported']))} for label, rec in records.items()},
            limitation='Nested Native/engine/parent costs overlap their CLI intervals; do not add again. Preparation/UI/authoring costs additional and unmeasured here, not zero.'),
        dependency=dict(path=str(DEPENDENCY.relative_to(ROOT)), sha256=PINS[DEPENDENCY], files_index=dep['files_index'],
            scope='Owned source rights and unchanged mechanics bytes only; Native cohort outcomes do not transfer GUI qualification.'),
        publication=dict(new_files=len(files), new_bytes=total, material_rows=len(material), file_cap=4 * 1024**2,
            packet_cap=16 * 1024**2, file_count_cap=2000,
            scope='Owned metadata/log/net/PRL proofs and reviewed curation/preopen controller source only. No CAD/DSN/SES/plots/HTML/SVG/ZIP/captured-runtime-code/tools/caches copied. Complete raw preopen snapshots remain Mac-only outside010; not a restore copy.'),
        limitations='Fixed progress cutoff only. Ordinary editor opening and stale refusal are recorded; Improve stored export/check completed but GUI export completion and checked opening unobserved after actual Mac lock. No full GUI, all-phase cancellation, exact queue timing, recovery, independent-family/holdout, comparative superiority, electrical/human/Windows/standalone/release/restoration claim. Earlier049 curator001 conflict and corrected002 remain historical and unchanged.',
        curation=dict(sampled_wall_seconds=time.monotonic() - start, sampled_parent_CPU_seconds=time.process_time() - cpu0,
            complete_external_exit_not_included=True, Native_executed=False, production_readers_rerun=False),
        files_index=dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index)))
    p.save_json(output, summary)
    print(json.dumps(dict(output=str(output), sha256=p.sha(output), files=len(files), bytes=total,
                          material=len(material), actual_GUI_qualified=False, Native_executed=False)))


if __name__ == '__main__':
    main()
