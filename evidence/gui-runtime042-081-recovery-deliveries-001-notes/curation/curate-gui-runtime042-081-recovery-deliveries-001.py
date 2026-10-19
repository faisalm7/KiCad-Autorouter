"""Retain two completed current042/081 recovery deliveries; never run Native/readers.

Reuse corrected041/080 curation002 and the unchanged030 retain/tree/cost helpers.
Final journal004 SHA and audited checkpoint HEAD are supplied at invocation.
No future workspace, UI counts, delivery or repair success is assumed.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, os, re, resource, sys, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io

RUNTIME = ROOT / '.runs/runtime-directory-042/runtime'
BASE = RUNTIME / '.runs/gui-session081'
HEAD = '82aaa3b750007ef2ffaafd367ffcb718aa93865e'
MANIFEST = '1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
PREPARED = '7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3'
PROTOCOL = 'f4119835b72ef3b74b7cffcca50f0854ec499a95698d55e26be5bfeb67012851'
RETENTION = 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
TEMPLATE = 'ee0d13d2eef3a691839f20393b0e61d79298e9239004a61db25faad8385b1718'
DEPENDENCIES = {
    'runtime042-native-milestone-001': '7faf3fa21c08073ede6bbb1825b15633c25997a7440b6da37dc2e0edac140d4b',
    'gui-runtime042-081-progress-001': '20f3b09c68c861e20dafc9917652ea78df4e9db03e451179277ccf351e65af7c',
    'gui-runtime042-081-postincumbent-cancel-001': 'a3061f78481d696c77d4d9fd071dd4a3a4f625af5c1b6d5fc7f24138b6d717a7',
    # Historical indexes supply unchanged licensed source bytes/mechanics only.
    # Their Native/UI results cannot qualify any042 job.
    'gui-runtime041-080-recovery-no-repair-001': '4abdf8dbd95a78daf4734894a4a7c3411c86fafd9efb1ba69ee4eca32e4027a8',
    'gui-runtime041-080-recovery-repair-001': '20aa2966175987e504f15c1a230cdf18146a3e977865a3c9ca2c58fe66bc7b4b',
}
HELPERS = {
    'gui081-recovery-preopen-001.py': '1b5cd6d0b1abb306a705e133e3c7150fe37e831e39a2b2353397bce151b58b46',
    'gui081-recovery-postopen-001.py': '215d9f95e543d6e2734027e8b1f6a471d4620a1e0c15b0182e94f02f3fce5700',
}
ROLES = {'no-repair': 'recovery_no_repair_delivery', 'repair': 'recovery_repair_delivery'}
COUNTS = ('opens', 'blocking', 'warnings', 'exclusions')
SKIP = {'kicad-cache', 'kicad-config', 'kicad-documents', 'engine-config', 'tmp', '__pycache__'}


def read(path):
    return json.loads(io.read_bytes(path, 4 * 1024**2))


def only_role(journal, role):
    rows = [row for row in journal['observations'] if row.get('role') == role]
    assert len(rows) == 1 and rows[0].get('actual_gui') is True, (role, 'unique completed actual GUI row required')
    return rows[0]


def own_final(record, folder, actual_folder, source_hashes, candidate):
    """Corrected002 selector: output folder/cwd, never phaseNone or first name."""
    candidate = Path(candidate)
    assert candidate == actual_folder / 'candidate' / candidate.name
    assert p.sha(folder / 'candidate' / candidate.name) == record['candidate_sha256']
    expected = dict(source_hashes); expected[candidate.name] = record['candidate_sha256']
    binding = read(folder / 'final-drc-binding.json')
    assert binding['source'] == str(candidate) and binding['saved'] is False
    assert binding['input'] == str(actual_folder / 'final-drc-input' / candidate.name)
    assert binding['before'] == expected
    after = binding['after']; prl = candidate.with_suffix('.kicad_prl').name
    assert all(after.get(name) == pin for name, pin in expected.items())
    assert not (set(after) - set(expected) - {prl})
    assert io.inventory(folder / 'final-drc-input') == after
    assert p.sha(folder / 'final-drc.json') == record['native_report_sha256']
    raw_report = read(folder / 'final-drc.json')
    assert raw_report['kicad_version'] == '10.0.7' and raw_report['source'] == candidate.name
    assert raw_report['$schema'] == 'https://schemas.kicad.org/drc.v1.json'
    assert set(raw_report['included_severities']) == {'error', 'warning', 'exclusion'}
    # Compare retained JSON directly. Do not invoke the root checkout's default
    # Native-version parser or any field/production acceptance readback.
    findings = raw_report['violations'] + raw_report['unconnected_items'] + raw_report['schematic_parity']
    raw_counts = dict(opens=len(raw_report['unconnected_items']),
        blocking=sum(item['severity'] == 'error' for item in raw_report['violations'] + raw_report['schematic_parity']),
        warnings=sum(item['severity'] == 'warning' for item in findings),
        exclusions=sum(item['severity'] == 'exclusion' or item.get('excluded', False) for item in findings))
    assert all(record['native'][key] == value for key, value in raw_counts.items())
    assert record['native']['findings'] == findings and record['native']['ignored_checks'] == raw_report['ignored_checks']
    selected = [step for step in record['steps'] if step['name'] == 'final-drc'
        and isinstance(step.get('argv'), list) and step['argv'].count('--output') == 1
        and step['argv'].index('--output') + 1 < len(step['argv'])
        and step['argv'][step['argv'].index('--output') + 1] == str(actual_folder / 'final-drc.json')]
    assert len(selected) == 1, 'Own final DRC must be distinguished from trial/incumbent'
    step = selected[0]
    assert step['cwd'] == str(actual_folder)
    assert step['argv'][-1] == binding['input']
    assert all(flag in step['argv'] for flag in ('--schematic-parity', '--all-track-errors',
                                               '--refill-zones', '--exit-code-violations'))
    expected_exit = 5 if findings else 0  # --exit-code-violations includes retained warnings.
    expected_status = 'nonzero_exit' if expected_exit else 'success'
    assert step['status'] == expected_status and step['exit_code'] == expected_exit and step['cleanup_complete'] is True
    process = read(folder / 'final-drc-process.json')
    assert all(process.get(key) == step.get(key) for key in
               ('argv', 'cwd', 'status', 'exit_code', 'cleanup_complete', 'pid'))
    return dict(output=str(actual_folder / 'final-drc.json'), cwd=str(actual_folder),
                report_sha256=record['native_report_sha256'], process_sha256=p.sha(folder / 'final-drc-process.json'),
                binding_sha256=p.sha(folder / 'final-drc-binding.json'), full_schematic_flag=True)


def main():
    global notes, refs, files, material, total
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal004-sha256', required=True)
    parser.add_argument('--checkpoint-head', required=True,
                        help='Caller supplied audited publication HEAD; immutable product remains82aaa.')
    args = parser.parse_args()
    assert re.fullmatch('[0-9a-f]{64}', args.journal004_sha256)
    assert re.fullmatch('[0-9a-f]{40}', args.checkpoint_head)
    start = time.monotonic(); cpu0 = resource.getrusage(resource.RUSAGE_SELF)
    stem = 'gui-runtime042-081-recovery-deliveries-001'
    notes = ROOT / 'evidence' / (stem + '-notes'); output = ROOT / 'evidence' / (stem + '.json')
    assert not os.path.lexists(notes) and not os.path.lexists(output), 'Fresh packet; never overwrite'
    journal_path = ROOT / '.runs/gui081-observations-004.json'
    assert p.sha(journal_path) == args.journal004_sha256
    journal = read(journal_path)
    assert journal['runtime'] == '042' and journal['session'] == '081'
    assert journal['source_head'] == HEAD and journal['runtime_manifest_sha256'] == MANIFEST
    assert journal['prepared_state_sha256'] == PREPARED and journal['active_workspace'] is None
    assert type(journal['frozen_utc']) is str and journal['frozen_utc']
    prepared_path = BASE / 'prepared-state.json'; assert p.sha(prepared_path) == PREPARED
    prepared = read(prepared_path)
    assert prepared['source_head'] == HEAD and prepared['runtime_manifest_sha256'] == MANIFEST
    assert p.sha(RUNTIME / 'runtime-distribution.json') == MANIFEST
    for name, pin in prepared['prerequisites_sha256'].items():
        path = Path(name); assert path.is_absolute() and not path.is_symlink() and path.is_file()
        assert p.sha(path) == pin
    for name, pin in prepared['tools']['implementation_sha256'].items():
        assert p.sha(RUNTIME / name) == pin
    protocol_path = Path(prepared['recovery_protocol'])
    assert protocol_path == BASE / 'recovery-controls-001/protocol-required-001.json'
    assert p.sha(protocol_path) == prepared['recovery_protocol_sha256'] == PROTOCOL
    protocol = read(protocol_path)
    assert protocol['source_head'] == HEAD and protocol['runtime_manifest_sha256'] == MANIFEST
    for name, pin in HELPERS.items(): assert p.sha(ROOT / '.runs' / name) == pin

    # A refusal or unfinished repair cannot be transformed into a positive packet.
    # All journal rows are retained, including failures; unselected raw jobs remain
    # local unless separately curated. The packet never claims first-attempt success.
    delivery_rows = {mode: only_role(journal, label) for mode, label in ROLES.items()}
    refusal = only_role(journal, 'unsupported4Cu_refusal')
    unsupported = protocol['recovery']['unsupported4Cu']
    assert refusal['source'] == unsupported['source']
    assert refusal['new_workspace_created'] is False
    assert type(refusal['job_count_before']) is int and refusal['job_count_before'] >= 0
    assert refusal['job_count_before'] == refusal['job_count_after']
    assert type(refusal['observed_findings']) is str and refusal['observed_findings']

    refs = {}; files = []; material = []; total = 0; dependencies = []
    for name, pin in DEPENDENCIES.items():
        path = ROOT / 'evidence' / (name + '.json'); assert p.sha(path) == pin
        data = read(path); index = data['files_index']
        assert p.sha(ROOT / index['path']) == index['sha256']; idx = read(ROOT / index['path'])
        if '042' in name:
            assert data['source_head'] == HEAD and data['runtime_manifest_sha256'] == MANIFEST
        for row in idx.get('files', []): refs.setdefault(row['sha256'], row['path'])
        for row in idx.get('material', []): refs.setdefault(row['sha256'], row['retained'])
        dependencies.append(dict(path=str(path.relative_to(ROOT)), sha256=pin, files_index=index,
            scope='Current042 prerequisite' if '042' in name else 'Historical licensed unchanged-byte/mechanics reuse only; no current Native/UI qualification'))
    helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
    template = ROOT / '.runs/curate-gui-runtime041-080-recovery-002.py'
    assert p.sha(helper) == RETENTION and p.sha(template) == TEMPLATE
    functions = [node for node in ast.parse(helper.read_bytes()).body
                 if isinstance(node, ast.FunctionDef) and node.name in ('retain', 'tree', 'cost')]
    assert [node.name for node in functions] == ['retain', 'tree', 'cost']
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'), globals())
    queue = []; excluded = []; time_inputs = []
    def add(path, name):
        path = Path(path)
        assert path.is_file() and not path.is_symlink() and ROOT in path.parents
        queue.append((path, Path(name)))
    def add_tree(path, name, full=False):
        for rel, pin in io.inventory(path, max_bytes=64 * 1024**2).items():
            if not full and set(Path(rel).parts) & SKIP:
                excluded.append(dict(original=str((path / rel).relative_to(ROOT)), sha256=pin,
                    bytes=(path / rel).stat().st_size, reason='Generated KiCad/engine cache or UI configuration, unchanged079 exclusion policy.'))
                continue
            add(path / rel, Path(name) / rel)
    add(journal_path, 'cutoff/observations-004.json')
    add(prepared_path, 'preparation/prepared-state.json'); add(protocol_path, 'preparation/recovery-protocol-required-001.json')
    add(RUNTIME / 'runtime-distribution.json', 'runtime/runtime-distribution.json')
    for name in HELPERS: add(ROOT / '.runs' / name, Path('helpers') / name)
    add(helper, 'curation/retention-helper030.py'); add(template, 'curation/corrected-template041-002.py')
    add(Path(__file__), 'curation/' + Path(__file__).name); add(ROOT / 'LICENSE', 'rights/LICENSE')
    failed_curator = ROOT / '.runs/curate-gui-runtime042-081-recovery-deliveries-first-execute-001.py'
    assert p.sha(failed_curator) == '8d494ad011d0a003c0562ef943d74f3f0679b1e3e3087c6fa90ecaad44f95a62'
    add(failed_curator, 'curation/failed-first-execute-001.py')
    for suffix in ('.log', '-time.log'):
        failed_log = ROOT / ('.runs/gui-runtime042-081-recovery-deliveries-curation-001' + suffix)
        add(failed_log, Path('curation') / failed_log.name)
        if suffix == '-time.log':
            time_inputs.append(dict(path=str(failed_log.relative_to(ROOT)), sha256=p.sha(failed_log), complete_external=cost(failed_log)))
    roles = []; workspaces = []; source_inputs = []
    for mode, ui in delivery_rows.items():
        repair = mode == 'repair'; declared = protocol['recovery'][mode]
        workspace = Path(ui['workspace'])
        assert workspace.parent == BASE / 'jobs' and re.fullmatch('autorouter-gui-[0-9a-f]{32}', workspace.name)
        assert workspace.is_dir() and workspace.resolve() == workspace and workspace not in workspaces
        workspaces.append(workspace); control = BASE / 'recovery-controls-001' / mode
        parent = read(workspace / 'route/result.json'); incumbent = read(workspace / 'route/incumbent/result.json')
        settings = read(workspace / 'settings.json'); source = Path(declared['source']); hashes = declared['source_hashes']
        assert source.parent == control / 'project' and Path(declared['original_source']).is_absolute()
        assert io.inventory(source.parent) == io.inventory(Path(declared['original_source']).parent) == hashes
        source_inputs.append((source, hashes))
        assert parent['source'] == incumbent['source'] == str(source)
        assert parent['source_hashes'] == incumbent['source_hashes'] == hashes
        assert parent['tools'] == incumbent['tools'] == prepared['tools']
        assert parent['strategy'] == 'native_validated_thermal_bridge'
        assert parent['thermal_parent_policy'] == 'native-thermal-parent-selection-v1'
        assert parent['scope'] == 'whole_board_unlocked_routing' and parent['engine_profile'] == 'standard' and parent['adapter'] == 'both'
        assert settings == declared['settings']
        assert settings['seconds'] == parent['budget_seconds'] == parent['cpu_budget_seconds'] == (420 if repair else 90)
        assert parent['incumbent']['receipt'] == str(workspace / 'route/incumbent/result.json')
        assert parent['incumbent']['receipt_sha256'] == p.sha(workspace / 'route/incumbent/result.json')
        assert parent['accepted'] is True and parent['invariants_unchanged'] is True
        assert parent['schematic_parity'] == incumbent['schematic_parity'] == 'checked by final native DRC'
        pre_path = control / 'preopen-001.json'; post_path = control / 'postopen-001.json'
        pre = read(pre_path); post = read(post_path)
        before = control / 'preopen-export'; after = control / 'postopen-snapshot-001'
        assert pre['snapshot'] == str(before) and post['snapshot'] == str(after)
        assert ui['preopen_receipt_sha256'] == p.sha(pre_path) and ui['postopen_receipt_sha256'] == p.sha(post_path)
        assert pre['workspace'] == post['workspace'] == str(workspace) and pre['role'] == post['role'] == mode
        assert pre['source'] == str(source) and pre['source_hashes'] == hashes and pre['settings'] == settings
        assert pre['settings_sha256'] == p.sha(workspace / 'settings.json')
        assert pre['incumbent_receipt_sha256'] == p.sha(workspace / 'route/incumbent/result.json')
        assert pre['route']['current'] is True and pre['export']['current'] is True
        assert pre['source_unchanged'] is True and post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
        assert io.inventory(before) == pre['snapshot_hashes'] and io.inventory(after) == post['snapshot_hashes']
        assert io.inventory(workspace / 'export') == post['snapshot_hashes']
        exported = read(before / 'export.json'); review = read(workspace / 'review/review.json'); choice = read(workspace / 'choice/choice.json')
        assert exported['export_accepted'] is True and exported['applied'] is False
        assert exported['original_geometry_and_routing_unchanged'] is True
        assert exported['inputs']['receipt_sha256'] == p.sha(workspace / 'route/result.json')
        assert exported['source_hashes'] == hashes and exported['tools'] == prepared['tools']
        assert exported['schematic_parity'] == 'checked by final native DRC'
        assert exported['budget_seconds'] == exported['cpu_budget_seconds'] == declared['additional_export_seconds'] == (120 if repair else 90)
        assert exported['candidate'] == str(workspace / 'export/validation/candidate' / source.name)
        assert parent['candidate'] == str(workspace / 'route/candidate' / source.name)
        assert parent['candidate_sha256'] == exported['candidate_sha256'] == p.sha(Path(parent['candidate']))
        assert choice['choice'] == 'accept' and choice['applied'] is False
        assert review['status'] == 'ready_for_manual_review' and review['candidate_sha256'] == parent['candidate_sha256']
        assert [parent['native'][key] for key in COUNTS] == [exported['native'][key] for key in COUNTS]
        assert all(parent['native'][key] == 0 for key in ('opens', 'blocking', 'exclusions'))
        assert type(parent['native']['warnings']) is int and parent['native']['warnings'] >= 0
        assert len(parent['native']['ignored_checks']) == len(incumbent['native']['ignored_checks']) == (7 if repair else 2)
        protected = len(incumbent['protected_route_import']['matches'])
        assert protected == pre['protected_original_locked_items'] == (0 if repair else 1)
        candidate_rel = 'validation/candidate/' + source.name
        assert pre['snapshot_hashes'][candidate_rel] == post['snapshot_hashes'][candidate_rel] == parent['candidate_sha256']
        changes = {name: dict(before=pre['snapshot_hashes'].get(name), after=post['snapshot_hashes'].get(name))
            for name in sorted(set(pre['snapshot_hashes']) | set(post['snapshot_hashes']))
            if pre['snapshot_hashes'].get(name) != post['snapshot_hashes'].get(name)}
        assert changes == post['changed']
        assert ui['source_unchanged'] is True and ui['candidate_PCB_unchanged'] is True and ui['human_review'] is False
        stages = ui.get('actual_stages', ui.get('stages'))
        assert type(stages) is list and all(type(stage) is str for stage in stages)
        lower = [stage.lower() for stage in stages]
        assert 'create review' in lower and any(stage in ('accept', 'accept intent') for stage in lower)
        assert any('ack' in stage for stage in lower)
        assert any('fresh' in stage and 'export' in stage for stage in lower)
        assert 'open checked export' in lower and any('pcb editor' in stage for stage in lower)
        assert any('edge' in stage for stage in lower), 'Actual local review observation required; no assumed browser/render'
        actual_counts = ui.get('UI_counts', ui.get('observed_editor', ui.get('actual_UI_counts')))
        assert type(actual_counts) is dict and actual_counts and type(actual_counts.get('unrouted')) is int
        assert actual_counts['unrouted'] == 0, 'Actual checked PCB observation must be retained, never inferred from DRC'
        own = {}
        own['incumbent'] = own_final(incumbent, workspace / 'route/incumbent', workspace / 'route/incumbent', hashes, incumbent['candidate'])
        own['parent'] = own_final(parent, workspace / 'route', workspace / 'route', hashes, parent['candidate'])
        own['export'] = own_final(exported, before / 'validation', workspace / 'export/validation', hashes, exported['candidate'])
        selected_trial = None
        if repair:
            assert parent['recovery_needed'] is True and incumbent['accepted'] is False and incumbent['status'] == 'drc_rejected'
            assert [incumbent['native'][key] for key in ('opens', 'blocking', 'exclusions')] == [0, 1, 0]
            assert [finding['type'] for finding in incumbent['native']['findings'] if finding['severity'] == 'error'] == ['starved_thermal']
            repair_record = read(workspace / 'route/recovery/repair.json')
            assert parent['repair'] == repair_record and repair_record['status'] == 'validated_trial_candidate'
            assert repair_record['validation_passed'] is True and repair_record['routing_accepted'] is False and repair_record['comparison_eligible'] is False
            trials = repair_record['trials']; assert type(trials) is list and 1 <= len(trials) <= 4
            matches = [trial for trial in trials if trial.get('validation_passed') is True]
            assert len(matches) == 1
            trial = matches[0]; index = trial['proposal_index']; assert type(index) is int and 0 <= index < 4
            trialdir = workspace / 'route/recovery' / ('trial-%02d' % (index + 1))
            assert trial['id'] == trialdir.name and trial['status'] == 'validated'
            assert trial['candidate'] == repair_record['candidate'] == str(trialdir / 'candidate' / source.name)
            assert trial['candidate_sha256'] == repair_record['candidate_sha256'] == parent['candidate_sha256']
            assert trial == read(trialdir / 'trial.json')
            assert all(trial['native'][key] == 0 for key in ('opens', 'blocking', 'exclusions'))
            assert len(trial['native']['ignored_checks']) == 7
            own['selected_trial'] = own_final(trial, trialdir, trialdir, hashes, trial['candidate'])
            selected_trial = dict(id=trial['id'], candidate=trial['candidate'], candidate_sha256=trial['candidate_sha256'],
                                  report_sha256=trial['native_report_sha256'], selection_from_own_repair_record=True)
        else:
            assert parent['recovery_needed'] is False and parent['repair'] is None
            assert incumbent['accepted'] is True and incumbent['status'] == 'routing_accepted'
            assert all(incumbent['native'][key] == 0 for key in COUNTS)
            assert incumbent['candidate_sha256'] == parent['candidate_sha256']
            assert not (workspace / 'route/recovery').exists()
        samples = []
        for process_path in sorted(workspace.glob('*.command.process.json')):
            process = read(process_path); log = process_path.with_name(process_path.name.replace('.process.json', '.log'))
            assert process['log_truncated'] is False and log.stat().st_size == process['log_bytes']
            samples.append(dict(stage=process_path.name.removesuffix('.command.process.json'), sample=process,
                receipt_sha256=p.sha(process_path), log_sha256=p.sha(log)))
        assert read(workspace / 'route.command.process.json')['exit_code'] == 0
        assert read(workspace / 'export.command.process.json')['exit_code'] == 0
        add_tree(workspace, Path(mode) / 'job'); add_tree(source.parent, Path(mode) / 'source')
        add_tree(before, Path(mode) / 'before-open/export', full=True)
        add_tree(after, Path(mode) / 'after-open/export', full=True)
        for path in (pre_path, post_path, control / 'route-settings.json'): add(path, Path(mode) / 'control' / path.name)
        postproof_path = control / 'postopen-current-proof-001.json'; postproof = None
        if postproof_path.is_file():
            postproof = read(postproof_path)
            assert postproof['Native_executed'] is False and postproof['postopen_current_proof']['refused'] is True
            add(postproof_path, Path(mode) / 'control' / postproof_path.name)
        roles.append(dict(role=ROLES[mode], workspace=str(workspace), actual_UI=ui, actual_window_counts=actual_counts,
            source=str(source), source_hashes=hashes, settings=settings, parent_Native=parent['native'],
            incumbent_Native=incumbent['native'], export_Native=exported['native'], own_final_bindings=own,
            parent_receipt_sha256=p.sha(workspace / 'route/result.json'), incumbent_receipt_sha256=p.sha(workspace / 'route/incumbent/result.json'),
            candidate_sha256=parent['candidate_sha256'], selected_trial=selected_trial, repair=parent['repair'],
            protected_original_items=protected, no_positive_protection_claim=repair,
            whole_method_seconds=settings['seconds'], separate_export_seconds=exported['budget_seconds'],
            before_open=dict(files=len(pre['snapshot_hashes']), receipt_sha256=p.sha(pre_path), production_readers_current_then=True),
            after_open=dict(files=len(post['snapshot_hashes']), receipt_sha256=p.sha(post_path), changed=changes,
                source_unchanged=True, candidate_PCB_unchanged=True, postopen_reader=postproof, new_Native_validity_inferred=False),
            accounting=dict(CLI_samples=samples,
                parent_nested=dict(wall_seconds=parent['wall_seconds'], CPU_seconds=parent['total_cpu_seconds']),
                incumbent_nested=dict(wall_seconds=incumbent['wall_seconds'], CPU_seconds=incumbent['total_cpu_seconds']),
                export_nested=dict(wall_seconds=exported['wall_seconds'], CPU_seconds=exported['total_cpu_seconds']),
                review_nested=dict(wall_seconds=review['wall_seconds'], CPU_seconds=review['total_cpu_seconds']),
                whole_interactive_wall_seconds=None, whole_interactive_CPU_seconds=None)))

    # Finite immediate-prefix helper attempts only; failed attempts/time logs are
    # retained as costs, not silently recast as Native or delivery failures.
    pattern = re.compile(r'gui081-(?:no-repair|repair)-[a-z-]+-[0-9]{3}(?:-time)?\.log')
    helper_logs = [path for path in (ROOT / '.runs').iterdir() if path.is_file() and pattern.fullmatch(path.name)]
    assert len(helper_logs) <= 100
    for path in sorted(helper_logs):
        add(path, Path('helpers-logs') / path.name)
        if path.name.endswith('-time.log'):
            time_inputs.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path), complete_external=cost(path)))
    # Whole finite old failed001 curation is already retained by historical repair
    # dependency; it is not a new042 invocation or an invented current failure.
    known = set(refs); planned_bytes = 0; planned_files = 0; filtered = []; omissions = []; expected_files = {}
    for path, destination in queue:
        raw = io.read_bytes(path, 4 * 1024**2); pin = hashlib.sha256(raw).hexdigest()
        if pin not in known:
            try: assert b'\0' not in raw; raw.decode('utf-8')
            except (AssertionError, UnicodeDecodeError):
                assert path.suffix.lower() == '.zip', 'Unknown binary is not silently omitted'
                omissions.append(dict(original=str(path.relative_to(ROOT)), bytes=len(raw), sha256=pin,
                    reason='KiCad-generated postopen backupZIP remains Mac-only; exact digest/size retained.'))
                continue
            planned_bytes += len(raw); planned_files += 1; known.add(pin)
        filtered.append((path, destination)); expected_files[str(path)] = (len(raw), pin)
    assert planned_bytes < 16 * 1024**2 - 8192 and planned_files < 1999, (
        'Exceeds unchanged caps; split meaningful packets, never raise caps or delete proof', planned_bytes, planned_files)
    assert p.sha(journal_path) == args.journal004_sha256 and p.sha(prepared_path) == PREPARED
    for path, destination in filtered: assert (path.stat().st_size, p.sha(path)) == expected_files[str(path)]
    notes.mkdir()
    for path, destination in filtered: retain(path, destination)
    scope = '''This packet retains only two completed actual Runtime042/GUI081 recovery deliveries and the separately observed unsupported4Cu refusal. Final journal004 is caller-SHA-bound; unique actual-GUI rows supply fresh workspaces and actual window counts. Missing/refused/incomplete deliveries stop before packet creation. Their raw failures remain local and in the frozen journal, never become automatic positive qualification. All journal rows are retained; unselected raw jobs require their own packets. No first-attempt claim is made.

Immutable source82aaa3b750007ef2ffaafd367ffcb718aa93865e, manifest1dc25cf5, prepared7ea7e874 and recovery protocolf4119835 are fixed. No-repair uses whole90/export90 and original locked1. Repair uses whole420/export120; zero protected items is not a positive protection control. Every own incumbent, selected repair trial, parent and fresh export has separate final Native/full-schematic/report/input/original-rule bindings. Corrected041002 exact --output and cwd selection distinguishes trial/parent/export even when phase is None. All trial failures, warnings, seven repair ignored checks and full process logs remain visible. Current042 own proofs qualify only their selected role; historical041 indexes supply unchanged licensed bytes/mechanics only.

Fresh before-open proof is separate from posteditor PRO/PRL/backupZIP changes. Source/PCB equality does not establish renewed Native validity after metadata changes. Native SVG/HTML and stored reports remain; screenshots exist only in the lead's CUA transcript. No browser AX/private input, unrelated windows, downloaded engine/app/venv or model download is published. Owned fixture/core is GPL; original and derivative Interf payload retains CC-BY-SA4.0 and Larry Ewing/GIMP attribution through source notices and exact existing dependencies. Generated cache/config exclusions and omitted backupZIP hashes are explicit.

No Native, engine, GUI, tests, process inventory or production acceptance reader is run by curation. Parsing retained Native JSON is not new validation. CLI, parent, incumbent, trial, repair, review, export and Native cost observations nest and must not be added twice. Timed helper costs are separate; their CPU cannot be assumed to cover independent GUI children. Whole interactive wall/CPU and unmetered authoring/review are unknown, not zero. Current042 curator001 failed before packet creation because it incorrectly expected process status success for Native exit5. Actual receipts consistently retain nonzero_exit with warnings; corrected curation checks that exact status/exit instead. Its original helper, traceback and measured0.82wall/0.31CPU remain retained; no Native/readers were rerun. Original041 curator001 failure is separately preserved in the historical repair dependency. No fullGUI/product/release, general quality/gain, family independence, human PCB/electrical/physical, Windows or restoration claim is made.
'''
    scope_path = notes / 'SCOPE.md'
    with scope_path.open('x') as stream: stream.write(scope)
    raw = scope_path.read_bytes(); pin = hashlib.sha256(raw).hexdigest(); total += len(raw)
    files.append(dict(path=str(scope_path.relative_to(ROOT)), bytes=len(raw), sha256=pin))
    material.append(dict(original='authored:SCOPE.md', retained=str(scope_path.relative_to(ROOT)), bytes=len(raw), sha256=pin))
    assert total < 16 * 1024**2 and len(files) < 2000
    index = notes / 'files.json'
    p.save_json(index, dict(schema=1, files=files, material=material, omitted_binary_payloads=omissions, excluded_generated_files=excluded))
    usage = resource.getrusage(resource.RUSAGE_SELF)
    summary = dict(schema=1, kind='actual-runtime042-GUI081-two-recovery-deliveries-role-cutoff',
        recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), accepted=False, project_complete=False,
        actual_GUI=True, actual_GUI_fully_qualified=False, human_PCB_review=False, physical_electrical_validation=False,
        Native_rerun_by_curation=False, production_readers_rerun_by_curation=False,
        source_head=HEAD, runtime_manifest_sha256=MANIFEST, prepared_state_sha256=PREPARED,
        recovery_protocol_sha256=PROTOCOL, native_version='10.0.7', publication_checkpoint_head=args.checkpoint_head,
        publication_checkpoint_authority='Caller supplied audited administration HEAD; immutable product source remains82aaa.',
        cutoff=dict(path=str(journal_path.relative_to(ROOT)), sha256=args.journal004_sha256),
        roles=roles, unsupported4Cu_actual_refusal=refusal, all_frozen_journal_rows_retained=True,
        unselected_raw_jobs_retained_by_this_packet=False, first_attempt_success_claim=False,
        additional_helper_complete_external=time_inputs,
        accounting_scope='Nested costs are not additive; helper CPU does not include independent GUI children. Whole interactive/authoring/review costs unknown, notzero.',
        rights='Owned fixture/core GPL; Interf source/derivatives CC-BY-SA4.0 with original Larry Ewing/GIMP notices retained or exact content-referenced.',
        dependencies=dependencies, curator_template=dict(path=str(template.relative_to(ROOT)), sha256=TEMPLATE),
        limitations='Two explicit positive delivery roles plus unsupported refusal only. No current fullGUI/broad quality/firstattempt/human/electrical/physical/Windows/restore claim.',
        retention=dict(helper=str(helper.relative_to(ROOT)), helper_sha256=RETENTION, functions=['retain', 'tree', 'cost'],
            max_file_bytes=4 * 1024**2, max_packet_payload_bytes=16 * 1024**2, max_new_files=2000,
            new_payload_files=len(files), new_payload_bytes=total, material_rows=len(material),
            omitted_binary_rows=len(omissions), counts_exclude_index_summary=True),
        curation_sample=dict(wall_seconds=time.monotonic() - start,
            CPU_seconds=usage.ru_utime + usage.ru_stime - cpu0.ru_utime - cpu0.ru_stime, complete_external_unknown=True),
        files_index=dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index)))
    assert p.sha(journal_path) == args.journal004_sha256 and p.sha(prepared_path) == PREPARED
    for source, hashes in source_inputs: assert io.inventory(source.parent) == hashes
    for row in files:
        raw = io.read_bytes(ROOT / row['path'], 4 * 1024**2)
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    for row in material:
        raw = io.read_bytes(ROOT / row['retained'], 4 * 1024**2)
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    assert not os.path.lexists(output); p.save_json(output, summary)
    print(json.dumps(dict(packet=str(output.relative_to(ROOT)), sha256=p.sha(output),
        index_sha256=p.sha(index), new_files=len(files), new_bytes=total, material_rows=len(material),
        actual_GUI_fully_qualified=False)))


if __name__ == '__main__':
    main()
