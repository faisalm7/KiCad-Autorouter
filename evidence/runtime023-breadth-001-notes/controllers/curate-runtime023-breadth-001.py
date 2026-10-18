"""Curate completed breadth receipts only; no Native, engine or proof-reader run.

SPDX-License-Identifier: GPL-3.0-or-later
Run only after the lead confirms both final receipts and reaped processes.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import placement_clearance as pc

NOTES = ROOT / 'evidence/runtime023-breadth-001-notes'
SUMMARY = ROOT / 'evidence/runtime023-breadth-001.json'
LIMIT = 64 * 1024 * 1024
MAX_FILES = 8000
GENERATED = {'kicad-config', 'kicad-cache', 'kicad-documents', '__pycache__'}
COPIES = {}
EXCLUDED = []
INVENTORIES = {}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def inventory(path):
    return pc.inventory(path, max_bytes=LIMIT, max_files=MAX_FILES,
                        max_entries=MAX_FILES * 2)


def pin(path):
    raw = pc.read_bytes(path, 4 * 1024 * 1024)
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}


def read_json(path):
    value = json.loads(pc.read_bytes(path, 4 * 1024 * 1024))
    if type(value) is not dict:
        raise ValueError('retained JSON object required: ' + str(path.relative_to(ROOT)))
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def copy_text(source, relative):
    relative = Path(*('owned-run-evidence' if part == '.runs' else part
                      for part in Path(relative).parts))
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('relative curation destination required')
    raw = pc.read_bytes(source, 4 * 1024 * 1024)
    raw.decode('utf-8')
    if b'\0' in raw:
        raise ValueError('unexpected binary outside the metadata-only scope')
    if re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)', raw):
        raise ValueError('possible credential in selected text: ' + str(source.relative_to(ROOT)))
    if sum(row['bytes'] for row in COPIES.values()) + len(raw) > LIMIT:
        raise ValueError('selected evidence exceeds64MiB')
    target = NOTES / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    if pc.read_bytes(target, 4 * 1024 * 1024) != raw:
        raise ValueError('curated text differs')
    COPIES[str(relative)] = {'source': str(source.relative_to(ROOT)), 'bytes': len(raw),
                             'sha256': digest(raw), 'byte_identical': True}


def complete_time(path):
    raw = pc.read_bytes(path, 4096)
    text = raw.decode('utf-8')
    values = {}
    for key in ('real', 'user', 'sys'):
        matches = re.findall(r'^' + key + r'\s+(\d+(?:\.\d+)?)\s*$', text, re.M)
        if len(matches) != 1:
            raise ValueError('one complete /usr/bin/time value required: ' + key)
        values[key] = float(matches[0])
    return {'wall_seconds': values['real'], 'user_CPU_seconds': values['user'],
            'system_CPU_seconds': values['sys'],
            'full_CPU_seconds': round(values['user'] + values['sys'], 8),
            'wall_and_full_CPU_within240_seconds': max(values['real'], values['user'] + values['sys']) <= 240,
            'measurement': 'Complete enclosing /usr/bin/time real/user/sys; do not add nested CPU.',
            'timing_file': pin(path)}


def native_metadata(native):
    if type(native) is not dict:
        return None
    findings = {}
    for row in native.get('findings', []):
        key = str(row.get('type')) + ':' + str(row.get('severity'))
        findings[key] = findings.get(key, 0) + 1
    return {'counts': {key: native.get(key) for key in ('opens', 'blocking', 'warnings', 'exclusions')},
            'finding_type_severity_counts': findings,
            'ignored_check_keys': [row.get('key') for row in native.get('ignored_checks', [])]}


def findings_text(rows):
    text = ['# Recorded breadth findings', '',
            'Both installed workflows delivered with current Route/export readbacks and unchanged source inventories. These are two exposed declared source families; ancestry independence is unverified. No GUI action is qualified by this packet.', '',
            '| Case | Original Native opens/blocking/warnings | Final Route and export opens/blocking/warnings | Complete wall / CPU seconds |',
            '| --- | --- | --- | --- |']
    for row in rows:
        def counts(key):
            values = (row.get(key) or {}).get('counts', {})
            return '/'.join(str(values.get(name)) for name in ('opens', 'blocking', 'warnings'))
        cost = row['complete_enclosing_cost']
        text.append('| ' + row['case'] + ' | ' + counts('source_Native') + ' | ' +
                    counts('route_Native') + ' | ' + format(cost['wall_seconds'], '.2f') +
                    ' / ' + format(cost['full_CPU_seconds'], '.2f') + ' |')
    text.extend(['',
        'NUS partial completion matched all47 protected records. Its original already had zero opens, so this establishes preservation/support rather than added completion. Raw NUS design, logs and Native geometry remain local; public evidence contains counts, statuses and hashes only.', '',
        'Sonde was an exposed whole-board120second standard/both task. Its original reference board already had zero opens; the whole-board task replaces unlocked reference routing. The final candidate retains26 warnings and is not whole-project DRC clean. Full original/candidate proof and CC-BY-SA-4.0 notices are selected.', '',
        'Both complete enclosing wall and full CPU costs are below240seconds. They include the workflow after setup, not build/setup, authoring, review or curation. No equal-budget B0/B1/B2/C comparison, general superiority, untouched confirmation, human or electrical validation is established.', ''])
    return '\n'.join(text)


def case_metadata(case, timing_path):
    outer = ROOT / '.runs/runtime-directory-023' / (case + '-workflow-001-run')
    protocol = read_json(outer / 'protocol.json')
    execution = read_json(outer / 'execution.json')
    process = read_json(outer / 'process.json')
    delivery_path = Path(execution['child_receipt'])
    delivery = read_json(delivery_path) if delivery_path.is_file() else {}
    if delivery and pin(delivery_path)['sha256'] != execution['child_receipt_sha256']:
        raise ValueError('retained workflow receipt changed')
    workspace = Path(delivery['workspace']) if delivery.get('workspace') else delivery_path.parent
    route_path = workspace / 'route/result.json'
    export_path = workspace / 'export/export.json'
    route = read_json(route_path) if route_path.is_file() else {}
    exported = read_json(export_path) if export_path.is_file() else {}
    protection = route.get('protected_route_import', {})
    hashes = sorted(row['non_uuid_sha256'] for row in protection.get('matches', []))
    times = complete_time(timing_path)
    row = {'case': case, 'recorded_control_passed': execution.get('passed'),
           'recorded_workflow_delivered': delivery.get('workflow_delivered'),
           'workflow_status': delivery.get('status', 'missing_final_child_receipt'), 'route_status': route.get('status'),
           'recorded_route_accepted': route.get('accepted'),
           'recorded_export_accepted': exported.get('export_accepted'),
           'recorded_route_readback_current': delivery.get('route_readback', {}).get('current'),
           'recorded_export_readback_current': delivery.get('export_readback', {}).get('current'),
           'actual_GUI': False, 'source_unchanged_reported': execution.get('sources_unchanged'),
           'source': protocol['source'], 'source_hashes': protocol['source_hashes'],
           'settings': protocol['settings'], 'expected_protected_records': protocol['expected_protected_records'],
           'protected_match_count': len(hashes), 'protected_unique_record_hash_count': len(set(hashes)),
           'protected_record_hash_list_sha256': digest(canonical(hashes)),
           'route_candidate_sha256': route.get('candidate_sha256'),
           'export_candidate_sha256': exported.get('candidate_sha256'),
           'route_Native': native_metadata(route.get('native')),
           'export_Native': native_metadata(exported.get('native')),
           'source_Native': native_metadata(route.get('source_drc')),
           'whole_project_drc_clean': exported.get('whole_project_drc_clean', route.get('whole_project_drc_clean')),
           'process': {key: process.get(key) for key in ('status', 'exit_code', 'cleanup_complete',
                       'wall_seconds', 'cpu_seconds', 'supervisor_cpu_seconds', 'monitor_cpu_seconds', 'log_truncated')},
           'complete_enclosing_cost': times,
           'stored_controller_sample': {key: execution.get(key) for key in ('sampled_wall_seconds', 'sampled_fullCPU_seconds')},
           'source_runtime_head': execution.get('source_runtime_head'),
           'runtime_manifest_sha256': protocol['runtime_manifest_sha256'],
           'retained_receipts': [pin(path) for path in (outer / 'protocol.json', outer / 'execution.json',
                                 outer / 'process.json', delivery_path, route_path, export_path) if path.is_file()],
           'curation_scope': 'Recorded outcomes and hash readback only; no new acceptance reader or Native execution.'}
    if case == 'NUS_partial':
        row.update(rights='CERN-OHL-P-2.0 creator notices retained locally. Third-party footprint/model/asset ancestry closure remains uncertain; no raw design or Native geometry is published.',
                   source_original_opens=0,
                   findings='Exposed preservation/support control only. Original zero opens precludes claiming added completion; exact protected-copper evidence is reported as retained counts/hashes.',
                   failure_detail_scope='Raw messages, logs, findings, references, UUIDs, coordinates and field comparison payload remain local; statuses/counts and raw-file hashes are retained here.')
    else:
        row.update(rights='KiCad demos at69cafb907ebc09e7722a2a464b1d466fc2e3608d; CC-BY-SA-4.0 and retained source notices. Runtime/controller code keeps its repository license.',
                   findings='Exposed whole-board120second standard/both installed qualification. Original unlocked reference routing is task input only; no comparison, family independence or general superiority claim.')
    return outer, delivery_path.parent, protocol, row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nus-time-log', required=True)
    parser.add_argument('--sonde-time-log', required=True)
    args = parser.parse_args()
    started, cpu_started = time.monotonic(), time.process_time()
    if SUMMARY.exists() or NOTES.exists():
        raise ValueError('fresh exclusive breadth evidence output required')
    # Read both final receipts before creating the packet. The lead must first
    # confirm final process reap; curation does not infer liveness from a path.
    cases = [case_metadata(case, Path(value).absolute()) for case, value in (
        ('NUS_partial', args.nus_time_log), ('Sonde_whole', args.sonde_time_log))]
    NOTES.mkdir()
    for outer, workflow, protocol, row in cases:
        case = row['case']
        for folder, destination in ((outer, Path(case) / 'controller'), (workflow, Path(case) / 'workflow')):
            if not folder.is_dir():
                row.setdefault('unavailable_raw_directories', []).append(str(folder.relative_to(ROOT)))
                continue
            before = inventory(folder)
            INVENTORIES[str(folder.relative_to(ROOT))] = before
            for name, expected in before.items():
                source = folder / name
                generated = (set(Path(name).parts) & GENERATED or Path(name).suffix in {'.pyc', '.pyo'} or Path(name).name == '.DS_Store')
                reason = ('NUS metadata-only scope; all raw CAD/DSN/SES/Native/XY/log/process/protocol/runtime payload remains local'
                          if case == 'NUS_partial' else
                          'generated KiCad/Python/OS configuration, cache or documents; retained locally' if generated else None)
                if reason:
                    EXCLUDED.append({**pin(source), 'reason': reason})
                else:
                    copy_text(source, destination / name)
            if inventory(folder) != before:
                raise ValueError('completed source evidence changed during curation')
        if case == 'Sonde_whole':
            copy_text(ROOT / row['complete_enclosing_cost']['timing_file']['path'], Path(case) / 'complete-exit-time.log')
        write_json(NOTES / case / 'summary.json', row)
    for source in (ROOT / '.runs/run-runtime023-breadth-workflow-001.py',
                   ROOT / 'scripts/qualify_runtime_workflow.py', ROOT / 'LICENSE', Path(__file__)):
        copy_text(source, Path('controllers') / source.name)
    manifest = read_json(ROOT / 'data/sources.json')
    write_json(NOTES / 'Sonde-source-rights.json', {
        'revision': manifest['commit'], 'license': manifest['license'],
        'license_scope_evidence': manifest['license_scope_evidence'],
        'source_entries': [row for row in manifest['files'] if row.get('project_id') == 'kicad-sonde-xilinx']})
    write_json(NOTES / 'exclusions.json', {'excluded_files': EXCLUDED,
        'retention': 'All omitted raw files remain unchanged on this Mac. This packet is not an independent disk-failure backup.'})
    scope = '''# Runtime023 breadth controls

Two exposed declared families are retained in the denominator, including every failure. Family ancestry independence is unverified. These are installed support/workflow checks, not an equal-budget B0/B1/B2/C comparison, untouched confirmation, routing-quality improvement or GUI/human/electrical qualification.

NUS public material is authored sanitized metadata only: recorded statuses, Native count/type aggregates, unchanged-source/candidate hashes, protected-record hash counts and complete costs. No raw NUS CAD/DSN/SES, Native findings/XY/field payload, protocol/process/log or captured runtime payload is copied. Creator notices identify CERN-OHL-P-2.0; third-party footprint/model/asset origin closure remains uncertain. All raw material and detailed failures remain local with individual file hash inventory. The original had zero opens, so any passing partial result establishes preservation/support only.

Sonde uses the already acquired unchanged KiCad demo at69cafb907ebc09e7722a2a464b1d466fc2e3608d, CC-BY-SA-4.0. Its complete original/candidate Native proof and existing notices are retained byte for byte where selected. Generated KiCad configuration/cache/documents and Python/OS cache are excluded with hashes. Candidate routing/Native serialization may differ from the original demo; original source/rules are unchanged as recorded. Repository source and controllers retain their own GPL license. Every warning, ignored check and refusal remains visible. Zero opens/blocking is separate from whole-project cleanliness.

Complete enclosing /usr/bin/time real/user/sys costs take precedence over earlier controller/receipt samples; nested CPU is never added twice. A240second complete wall/fullCPU overrun remains an overrun even if a sampled controller flag was true. Authoring, review, build/setup and curation are separate costs, not zero. No Native/JVM/engine/test/CI/network execution occurs during curation. Raw packets remain Mac-only unless separately backed up; this selected packet is not an independent restoration proof.
'''
    with (NOTES / 'SCOPE.md').open('x') as stream:
        stream.write(scope)
    with (NOTES / 'FINDINGS.md').open('x') as stream:
        stream.write(findings_text([row for _, _, _, row in cases]))
    for name, expected in INVENTORIES.items():
        if inventory(ROOT / name) != expected:
            raise ValueError('completed raw evidence changed before seal')
    selected = inventory(NOTES)
    rows = []
    for name, expected in selected.items():
        value = {'path': name, 'bytes': (NOTES / name).stat().st_size, 'sha256': expected}
        value.update(COPIES.get(name, {'source': 'authored curation metadata, not an executed Native receipt'}))
        rows.append(value)
    write_json(NOTES / 'files.json', {'schema': 1, 'files': rows,
        'inventory_scope': 'Every selected file except files.json itself; no self-hash claim.',
        'source_inventories_sha256': {name: digest(canonical(value)) for name, value in INVENTORIES.items()},
        'excluded_files_count': len(EXCLUDED), 'byte_identical_copies': len(COPIES)})
    final = inventory(NOTES)
    if {name: value for name, value in final.items() if name != 'files.json'} != selected:
        raise ValueError('curated material changed before summary')
    write_json(SUMMARY, {'schema': 1, 'kind': 'runtime023-two-declared-family-installed-breadth-controls',
        'accepted': False, 'project_complete': False, 'actual_GUI': False, 'human_review': False,
        'declared_case_count': 2, 'family_independence': 'unverified; exposed development sources',
        'cases': [row for _, _, _, row in cases],
        'files_index': pin(NOTES / 'files.json'), 'selected_files_including_manifest': len(final),
        'selected_bytes_including_manifest': sum((NOTES / name).stat().st_size for name in final),
        'curation_wall_seconds_before_summary_publication': time.monotonic() - started,
        'curation_self_CPU_seconds_before_summary_publication': time.process_time() - cpu_started,
        'cost_scope': 'Curation script only; preparation/authoring/review/setup are additional, uninstrumented costs.',
        'claims_limit': 'Two declared exposed source families, not proved independent. No comparative, completion, speed, cleanup, Windows, actual GUI, human or physical/electrical claim. NUS original already zero opens.'})
    print(json.dumps({'summary': pin(SUMMARY), 'files': len(final),
        'selected_bytes': sum((NOTES / name).stat().st_size for name in final),
        'excluded_files': len(EXCLUDED), 'new_Native_or_engine_execution': False}))


if __name__ == '__main__':
    main()
