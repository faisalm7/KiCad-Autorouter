"""Prepare three pristine081 freshness copies using the existing080 copy protocol.

Preparation only: no production readers, Native, GUI, mutation or callback execution.
Run once after the lead's positive081 proof; existing outputs are never reused.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.runs/runtime-directory-042/runtime/.runs/gui-session081'
EXPECTED_HEAD = '82aaa3b750007ef2ffaafd367ffcb718aa93865e'
EXPECTED_PREPARED = '7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3'
EXPECTED_MANIFEST = '1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
TEMPLATE = '.runs/gui080-prepare-controls-001.py'
TEMPLATE_SHA = 'e4b039d37f8d8bf6cbc74ee94169f38168d80e1c17b7a4bcb920028020629c10'
HELPERS = {
    '.runs/gui081-preopen-001.py': '49e86d07207ed9730070a469a5b49ab210199383f5cbad3311ea73ec1ed42de7',
    '.runs/gui081-mutate-control-001.py': 'bc6144705fd7776ce3455da469a7c93a6086e0fed76d43215f9b40a3c80c567d',
}
SETTINGS = dict(schema=1, scope='partial_completion', seconds=90, adapter='both',
                profile='standard', guidance='native', layers='source_all',
                scoring_preference=None)


def sha(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pins(directory):
    directory = Path(directory)
    assert directory.is_dir() and not directory.is_symlink()
    paths = list(directory.iterdir())
    assert len(paths) == 4
    assert all(p.is_file() and not p.is_symlink() for p in paths)
    return {p.name: sha(p) for p in paths}


def prepare():
    prepared_path = BASE / 'prepared-state.json'
    assert sha(prepared_path) == EXPECTED_PREPARED
    prepared = json.loads(prepared_path.read_bytes())
    assert prepared['source_head'] == EXPECTED_HEAD
    assert prepared['runtime_manifest_sha256'] == EXPECTED_MANIFEST
    assert sha(BASE.parents[1] / 'runtime-distribution.json') == EXPECTED_MANIFEST
    assert sha(ROOT / TEMPLATE) == TEMPLATE_SHA
    for name, digest in prepared['prerequisites_sha256'].items():
        assert Path(name).is_absolute() and sha(name) == digest
    recovery = Path(prepared['recovery_protocol'])
    assert recovery == BASE / 'recovery-controls-001/protocol-required-001.json'
    assert sha(recovery) == prepared['recovery_protocol_sha256']
    assert prepared['settings'] == SETTINGS
    settings_path = Path(prepared['settings_path'])
    assert settings_path == BASE / 'route-settings.json'
    assert sha(settings_path) == prepared['settings_sha256']
    assert json.loads(settings_path.read_bytes()) == SETTINGS
    assert Path(prepared['source']) == BASE / 'project/owned1007-transport.kicad_pcb'
    assert pins(BASE / 'project') == prepared['source_hashes']
    assert all(sha(ROOT / name) == digest for name, digest in HELPERS.items())

    controls = BASE / 'freshness-controls-001'
    assert not os.path.lexists(controls)
    controls.mkdir()
    copies = {}
    for role in ('source', 'settings', 'export'):
        control = controls / role
        control.mkdir()
        shutil.copytree(BASE / 'project', control / 'project')
        assert pins(control / 'project') == prepared['source_hashes']
        copies[role] = str(control / 'project/owned1007-transport.kicad_pcb')

    protocol = dict(
        schema=1, source_head=EXPECTED_HEAD,
        runtime_manifest_sha256=EXPECTED_MANIFEST,
        prepared_state_sha256=EXPECTED_PREPARED,
        source_hashes=prepared['source_hashes'], settings=SETTINGS,
        settings_path=str(settings_path), settings_sha256=prepared['settings_sha256'],
        source_copies=copies,
        declared_jobs=['source-freshness', 'settings-freshness', 'typed-export-freshness'],
        mutations=dict(
            source='append newline to copied source PRO only after current preopen proof',
            settings='append newline to own captured settings only after proof',
            export='typed export_accepted true to integer1 after proof; separate reader-boundary observation required'),
        helper_sha256=HELPERS,
        template=dict(path=str(ROOT / TEMPLATE), sha256=TEMPLATE_SHA,
                      scope='Existing080 freshness-copy subset; unrelated hierarchy/high-budget supplement not ported'),
        route_wall_and_full_CPU_seconds=90, separate_export_wall_and_full_CPU_seconds=90,
        originals_preserved=True, GUI_qualified=False, Native_run_by_preparation=False,
        queued_callback_boundary_proved=False, human_review=False,
        preparation_cost=dict(wall_seconds=None, CPU_seconds=None,
                              scope='Unmetered authoring is unknown, not zero; future preparation execution measured separately'),
        scope='Prospective081 freshness roles only. No Native/readers/GUI/mutation/worker/cancellation or queued-open execution. Fresh owned outputs; original prepared state and080 records unchanged.')
    with (controls / 'protocol-frozen-001.json').open('x') as stream:
        json.dump(protocol, stream, indent=2)
        stream.write('\n')
    assert sha(prepared_path) == EXPECTED_PREPARED
    assert pins(BASE / 'project') == prepared['source_hashes']
    assert all(sha(ROOT / name) == digest for name, digest in HELPERS.items())
    return protocol


if __name__ == '__main__':
    print(json.dumps(prepare(), sort_keys=True))
