"""Constructed queued-open metadata counterexample; no Native, wx or real opener.

Reuse the existing GUI inspection fixture and actual extracted callback body.
The inspection CLI response is an explicit mock. Only owned inert PRL files
are changed, after inspect_path returns and before the queued callback body.
"""
from pathlib import Path
import hashlib
import json
import os
import stat
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import gui, local_settings as local, pipeline as p, review_export as ex
from tests import test_gui as gt
from tests import test_gui_export_inspection as fixture

START = time.monotonic()
RUNTIME = ROOT / '.runs/runtime-directory-056/runtime'
MANIFEST_PIN = 'b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = [ROOT / name for name in (
    'autorouter/gui.py', 'autorouter/review_export.py', 'autorouter/local_settings.py',
    'autorouter/placement_clearance.py', 'autorouter/pipeline.py', 'autorouter/handoff.py',
    'tests/test_gui.py', 'tests/test_gui_export_inspection.py', 'docs/gui-workflow.md')]
sources.append(Path(__file__).resolve())
pins = {str(path.relative_to(ROOT)): sha(path) for path in sources}
manifest_path = RUNTIME / 'runtime-distribution.json'
assert sha(manifest_path) == MANIFEST_PIN
manifest = json.loads(manifest_path.read_bytes())
runtime_pins = manifest['immutable_files_sha256']
assert len(runtime_pins) == 54
assert all(sha(RUNTIME / name) == digest for name, digest in runtime_pins.items())
assert sha(RUNTIME / 'autorouter/gui.py') == pins['autorouter/gui.py']
assert sha(RUNTIME / 'autorouter/review_export.py') == pins['autorouter/review_export.py']

rows = []
for mode in ('unchanged', 'byte_change', 'hardlink', 'immutable_flag'):
    case = fixture.ExportInspectionTests('test_unchanged_queued_open_succeeds_and_cancel_skips_freshness')
    case.setUp()
    prl = None
    original_flags = None
    try:
        flow, project, reader_record = case.prepared()
        prl = flow.workspace / 'export/validation/final-drc-input' / project.with_suffix('.kicad_prl').name
        prl.parent.mkdir(parents=True)
        prl.write_bytes(b'{}\n')
        before = {prl.name: sha(prl)}
        original_flags = prl.stat().st_flags
        event = dict(policy=local.POLICY, present=True, path=str(prl), sha256=before[prl.name],
                     flags_before=0, flags_during=stat.UF_IMMUTABLE,
                     flags_restored=True, bytes_unchanged=True)
        local.check_preserved(prl, before, event)
        export_root = flow.workspace / 'export'
        flow.records['export']['export_evidence'] = ex.evidence(export_root)
        (export_root / 'export.json').write_text(json.dumps(flow.records['export']))
        job = case.job(reader_record)
        target = flow.inspect_path('export', job=job)
        evidence_before = ex.evidence(export_root)
        info_before = prl.stat()
        if mode == 'byte_change':
            prl.write_bytes(b'{"changed":true}\n')
        elif mode == 'hardlink':
            os.link(prl, case.root / 'owned-outside-export-witness.kicad_prl')
        elif mode == 'immutable_flag':
            os.chflags(prl, stat.UF_IMMUTABLE, follow_symlinks=False)
        info_after = prl.stat()
        policy_refusal = None
        try:
            local.check_preserved(prl, before, event)
        except p.Rejected as exc:
            policy_refusal = str(exc)
        window = case.window(flow, job)
        with patch.object(gui.subprocess, 'Popen') as opener:
            gt.window_method('opened')(window, 'export', target, None)
        row = dict(mode=mode, exact_interval='after mocked inspection reader/inspect_path; before actual opened callback body',
                   PRL_sha256_before=before[prl.name], PRL_sha256_after=sha(prl),
                   link_count_before=info_before.st_nlink, link_count_after=info_after.st_nlink,
                   flags_before=info_before.st_flags, flags_after=info_after.st_flags,
                   export_byte_directory_witness_unchanged=ex.evidence(export_root) == evidence_before,
                   existing_PRL_policy_refusal=policy_refusal,
                   mocked_opener_calls=opener.call_count, positive_flow_retained=window.flow is flow,
                   actual_opener_invoked=False, actual_GUI=False, Native_run=False)
        if mode in ('hardlink', 'immutable_flag'):
            assert row['PRL_sha256_before'] == row['PRL_sha256_after']
            assert row['export_byte_directory_witness_unchanged'] and policy_refusal is not None
            assert opener.call_count == 1 and window.flow is flow
            row['counterexample_reproduced'] = True
        elif mode == 'byte_change':
            assert not row['export_byte_directory_witness_unchanged'] and policy_refusal is not None
            assert opener.call_count == 0 and window.flow is None
            row['expected_byte_refusal_observed'] = True
        else:
            assert row['export_byte_directory_witness_unchanged'] and policy_refusal is None
            assert opener.call_count == 1 and window.flow is flow
            row['expected_positive_observed'] = True
        rows.append(row)
    finally:
        if prl is not None and original_flags is not None and prl.exists():
            os.chflags(prl, original_flags, follow_symlinks=False)
        case.doCleanups()

assert all(sha(ROOT / name) == digest for name, digest in pins.items())
assert sha(manifest_path) == MANIFEST_PIN
assert all(sha(RUNTIME / name) == digest for name, digest in runtime_pins.items())
result = dict(schema=1, kind='constructed-queued-open-PRL-metadata-counterexample-v1',
              probe_execution_passed=True, accepted=False, production_admitted=False,
              Native_run=False, actual_GUI=False, real_opener_invoked=False, human_review=False,
              fixture_reader='Explicit existing fixture mock; no accepted Native report or GUI qualification is asserted',
              source_test_helper_sha256=pins, runtime_manifest_sha256=MANIFEST_PIN,
              runtime_immutable_files=54, runtime_immutable_files_unchanged=True, rows=rows,
              wall_seconds=time.monotonic() - START,
              limits='Owned inert synthetic PRL only. Existing local-settings policy called directly. Actual callback body extracted by existing helper; wx and subprocess opener mocked. No actual queued GUI event, Native worker, real PCB source or retained evidence was modified.')
with (OUT / 'result.json').open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(dict(probe_execution_passed=True, counterexamples=2,
                     result=str(OUT / 'result.json'), wall_seconds=result['wall_seconds'])))
