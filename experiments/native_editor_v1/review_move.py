"""Detached checker for the exact owned in-editor PCB translation."""
from __future__ import annotations

import argparse
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / 'experiments/live_editor_v1/probe.py'
NAME = 'owned-placement-ordinary'
SUFFIXES = ('.kicad_pcb', '.kicad_pro', '.kicad_sch')


def review(runtime, job):
    if (not runtime.is_relative_to(ROOT / '.runs') or not job.is_relative_to(ROOT / '.runs')
            or runtime.resolve() != runtime or job.resolve() != job
            or job.parent.name != 'native-jobs' or not re.fullmatch(r'[0-9a-f]{32}', job.name)):
        raise ValueError('Use a private native job and verified local runtime.')
    job_info = job.stat()
    if not stat.S_ISDIR(job_info.st_mode) or job_info.st_uid != os.getuid() or job_info.st_mode & 0o077:
        raise ValueError('The native job directory must be private.')
    sys.path.insert(0, str(runtime))
    from autorouter import config, placement_clearance, provenance

    if config.ROOT != runtime or config.NATIVE_VERSION != '10.0.7':
        raise ValueError('Select the pinned KiCad 10.0.7 validation runtime.')
    config.current_native_selection()
    spec = spec_from_file_location('copperpath_checked_translation', CORE)
    core = module_from_spec(spec)
    spec.loader.exec_module(core)

    source = job.parents[1] / 'inspection' / (NAME + '.kicad_pcb')
    initial = {suffix: core.digest(placement_clearance.read_bytes(
        core.FIXTURE / (NAME + suffix))) for suffix in SUFFIXES}

    def disk():
        if source.with_suffix('.kicad_dru').exists():
            raise ValueError('The exact test project cannot carry an additional rule file.')
        return {suffix: core.digest(placement_clearance.read_bytes(source.with_suffix(suffix)))
                for suffix in SUFFIXES}

    if disk() != initial:
        raise ValueError('The disposable PCB, project or schematic changed on disk.')
    request_path = job / 'request.json'
    request_raw = placement_clearance.read_bytes(request_path, 4096)
    request = json.loads(request_raw, object_pairs_hook=provenance._strict_object)
    if (type(request) is not dict or set(request) != {'schema', 'selection', 'request', 'editor_format'}
            or type(request['schema']) is not int or request['schema'] != 1
            or request['editor_format'] not in ('clipboard', 'file')
            or type(request['selection']) is not dict
            or set(request['selection']) != {'ref', 'uid', 'from_nm'} or type(request['request']) is not str):
        raise ValueError('The editor supplied an invalid scoped request.')
    here = request['selection']
    start = here['from_nm']
    if (type(start) is not list or len(start) != 2 or any(type(value) is not int for value in start)
            or type(here['ref']) is not str or type(here['uid']) is not str):
        raise ValueError('The native item must use exact identity and an integer nanometre position.')
    snapshot_path = job / 'snapshot.kicad_pcb'
    raw = placement_clearance.read_bytes(snapshot_path, 512 * 1024)
    snapshot = dict(raw=raw, sha256=core.digest(raw), disk=initial)
    delta = core.requested_offset(request['request'], here['ref'])
    target = [position + offset for position, offset in zip(start, delta)]
    plan = core.build_move_plan(snapshot, here['ref'], here['uid'], start, target,
                               editor_format=request['editor_format'])
    summary, native_dir = core.check_move_plan(plan, source, job)
    if (disk() != initial or placement_clearance.read_bytes(snapshot_path, 512 * 1024) != raw
            or placement_clearance.read_bytes(request_path, 4096) != request_raw):
        raise ValueError('The source or checked request changed during validation.')
    if any(not content or len(content) > 512 * 1024
           for content in (plan['source'], plan['candidate'])):
        raise ValueError('The checked boards exceed the native handoff limit.')
    return dict(schema=1, status='checked', plan=plan['info'], findings=summary,
                request=request, before=plan['source'].decode('utf-8'), candidate=plan['candidate'].decode('utf-8'),
                snapshot_sha256=snapshot['sha256'], request_sha256=hashlib.sha256(request_raw).hexdigest(),
                checked_before_sha256=core.digest(plan['source']),
                checked_candidate_sha256=core.digest(plan['candidate']), native_evidence=native_dir.name,
                core_sha256=hashlib.sha256(CORE.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--job', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = review(args.runtime.absolute(), args.job.absolute())
    except (OSError, ValueError) as error:
        parser.exit(1, f'Copperpath check: {error}\n')
    job = args.job.absolute()
    payload = (json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    if len(payload) > 2 * 1024 * 1024:
        parser.exit(1, 'Copperpath check: the result exceeds the native handoff limit.\n')
    # Publish the bytes, exact request and findings together. No separate
    # writable candidate can be substituted for this checked handoff.
    with tempfile.NamedTemporaryFile(dir=job, prefix='pending-result-', delete=False) as output:
        output.write(payload)
    os.link(output.name, job / 'checked-result.json', follow_symlinks=False)
    os.unlink(output.name)


if __name__ == '__main__':
    main()
