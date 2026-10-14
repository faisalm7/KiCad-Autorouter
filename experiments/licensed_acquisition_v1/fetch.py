"""Pinned, bounded development acquisition. Default is offline plan-only."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

MIB = 1024 ** 2
PROTOCOL_SHA = '23239f00d5d249611d2403eec0e41d8d6db22881aa76dd3d76e94bd764b24427'
MATERIAL = ('fetch.py', 'test_fetch.py', 'protocol.json', 'existing-data-inventory.json', 'README.md', 'STATIC_AUDIT.md')
CAP = 10 * MIB
AGGREGATE = 64 * MIB
MAX_ENTRIES = 4096
MAX_FILES = 2048
MAX_OUTPUT = 24 * MIB

# Finite, reviewed acquisition profiles; no arbitrary manifest or destination CLI.
PROFILES = {
    'v1': {'protocol_sha256': PROTOCOL_SHA, 'destination_root': 'expansion004',
           'directory': 'experiments/licensed_acquisition_v1',
           'output_prefix': 'licensed-acquisition-004-run-', 'files': 33, 'bytes': 5016162,
           'identities': [('ideal-diode', 'sparkfun/SparkFun_Ideal_Diode_Breakout', 'c950f439b55c08009e14fecc60f0fecd5832a42e'),
                          ('hstx-pth', 'sparkfun/SparkFun_HSTX_PTH_Breakout', '48e2aab291a360cfd6449c322a052e6c15edda3d'),
                          ('olimex-ice40-dio', 'OLIMEX/iCE40-DIO', '6c8b27b36c55a7c2b59877957e7eb389e367c208')]},
    'v2': {'protocol_sha256': '94c5d74bfa34da80278db89bc2fc48ba165ed4bb293cb2f3d8382f3150241a66',
           'destination_root': 'expansion005', 'directory': 'experiments/licensed_acquisition_v2',
           'output_prefix': 'licensed-acquisition-005-run-', 'files': 14, 'bytes': 2163350,
           'identities': [('paw3395', 'badjeff/paw3395-pcb', 'b71e346fc04ef18c26e0e8638ce0333395d41a14')]},
    'v3': {'protocol_sha256': '076396da8d78940618dc4c3502fac5a2f8b8303a77d786b523dc0468c8e30c6b',
           'destination_root': 'expansion006', 'directory': 'experiments/licensed_acquisition_v3',
           'output_prefix': 'licensed-acquisition-006-run-', 'files': 5, 'bytes': 754649,
           'identities': [('devobordo', 'Travis8795/devobordo', '5823d7a0d7fc3d1d520dd00f87bc5a42e413d04b')]},
    'v4': {'protocol_sha256': '9d01b698ce07c1521b69360d00f14a6f1bfea1fa51a345606c0426f31563103d',
           'destination_root': 'expansion007', 'directory': 'experiments/licensed_acquisition_v4',
           'output_prefix': 'licensed-acquisition-007-run-', 'files': 6, 'bytes': 135772,
           'identities': [('ardujoy-c64', 'eduardofv/ArdujoyC64', '1b63471d9726fb6a38f8544ca73ebf10c7f19820')]},
    'v5': {'protocol_sha256': 'dea994df5eadb5fea182efdb1a33374df21695dca9209a6b6a8f0fee2d66e711',
           'destination_root': 'expansion008', 'directory': 'experiments/licensed_acquisition_v5',
           'output_prefix': 'licensed-acquisition-008-run-', 'files': 9, 'bytes': 146916,
           'identities': [('nus-usb-led', 'nushackers/hsp-pcb-intro', 'ad3fbd582e3915b585c453ea202f591720a1f427')]},
    'v6': {'protocol_sha256': '876b0b80dee374bd17606d3537568358b94ce689ece4c956bfd61f2e4ea89ff8',
           'destination_root': 'expansion009', 'directory': 'experiments/licensed_acquisition_v6',
           'output_prefix': 'licensed-acquisition-009-run-', 'files': 10, 'bytes': 741742,
           'identities': [('als311-clock', 'ugolnikovE/als311-clock', '494ab6baf40746d313fe11379425900ebe97c319')]},
    'v7': {'protocol_sha256': '8a1d89b9f924b1d25d3ff9af855a8e486ced7d01046982fe70ab0322765ab42e',
           'destination_root': 'expansion010', 'directory': 'experiments/licensed_acquisition_v7',
           'output_prefix': 'licensed-acquisition-010-run-', 'files': 5, 'bytes': 161071,
           'identities': [('push-button-led', 'gurusaeth12/push-button-led-kicad', '29c46b7c03d2afd9fe3a58fe2070309b12f94b42')]},
    'v8': {'protocol_sha256': '4a398878909d5807107d6c760cbbc0a0ff39f17ee13f0704dc9f62a4a6edab55',
           'destination_root': 'expansion011', 'directory': 'experiments/licensed_acquisition_v8',
           'output_prefix': 'licensed-acquisition-011-run-', 'files': 5, 'bytes': 347566,
           'identities': [('cp2102-uart', 'MAATHES-THILAK-K/USB_TO_UART-CP2102', 'eecf7bb08afbd1494f3136a5124f4b6b6ea6c63e')]},
}


def profile(profile_id='v1'):
    if type(profile_id) is not str or profile_id not in PROFILES:
        raise ValueError('unreviewed acquisition profile')
    return PROFILES[profile_id]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(name):
    if not isinstance(name, str) or not name or '\\' in name or any(ord(c) < 32 for c in name):
        raise ValueError('unsafe path')
    if PurePosixPath(name).is_absolute() or any(c in ('', '.', '..') for c in name.split('/')):
        raise ValueError('unsafe path')
    return Path(*PurePosixPath(name).parts)


def contained(root, path):
    root, path = root.absolute(), path.absolute()
    if not path.is_relative_to(root):
        raise ValueError('path outside root')
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('symlink path')
    return path


def bounded(path, cap=CAP):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > cap:
        raise ValueError('nonregular or oversized file')
    with path.open('rb') as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap or len(raw) != path.stat().st_size:
        raise ValueError('file grew or changed size')
    return raw


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def inventory(base, expected=None, cap=AGGREGATE):
    """Bound entries before collecting; reject unknown members before reading them."""
    contained(base, base)
    files, directories, folded = {}, [], set()
    entries = total = 0
    stack = [base]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as it:
            for entry in it:
                entries += 1
                if entries > MAX_ENTRIES:
                    raise ValueError('entry cap')
                path = Path(entry.path)
                name = path.relative_to(base).as_posix()
                safe(name)
                if name.casefold() in folded:
                    raise ValueError('casefold collision')
                folded.add(name.casefold())
                if entry.is_symlink():
                    raise ValueError('symlink in inventory')
                if entry.is_dir(follow_symlinks=False):
                    if expected is not None and name not in expected['directories']:
                        raise ValueError('unexpected directory: ' + name)
                    directories.append(name)
                    stack.append(path)
                elif entry.is_file(follow_symlinks=False):
                    if len(files) >= MAX_FILES:
                        raise ValueError('file count cap')
                    if expected is not None and name not in expected['files']:
                        raise ValueError('unexpected file: ' + name)
                    size = entry.stat(follow_symlinks=False).st_size
                    if total + size > cap:
                        raise ValueError('aggregate byte cap')
                    raw = bounded(path, min(CAP, cap - total))
                    total += len(raw)
                    files[name] = {'bytes': len(raw), 'sha256': sha(raw)}
                else:
                    raise ValueError('special file')
    result = {'schema': 1, 'files': dict(sorted(files.items())), 'directories': sorted(directories),
              'file_count': len(files), 'bytes': total}
    if expected is not None and result != expected:
        raise ValueError('inventory changed')
    return result


def extend(baseline, acquired, include_root=True, destination_root='expansion004'):
    if destination_root not in {p['destination_root'] for p in PROFILES.values()}:
        raise ValueError('unreviewed destination root')
    files = dict(baseline['files'])
    dirs = set(baseline['directories'])
    if include_root:
        dirs.add(destination_root)
    for name, info in acquired.items():
        key = destination_root + '/' + name
        if key in files:
            raise ValueError('overwrite')
        files[key] = info
        dirs.update(p.as_posix() for p in PurePosixPath(key).parents if str(p) != '.')
    return {'schema': 1, 'files': dict(sorted(files.items())), 'directories': sorted(dirs),
            'file_count': len(files), 'bytes': sum(r['bytes'] for r in files.values())}


def validate_protocol(plan, baseline, profile_id='v1'):
    selected = profile(profile_id)
    if plan['destination'] != '.data/' + selected['destination_root'] or plan['split'] != 'development':
        raise ValueError('scope')
    limits = {'aggregate_all_data_bytes': AGGREGATE, 'project_bytes': CAP,
              'invocation_network_bytes': CAP, 'invocation_wall_seconds': 300,
              'request_wall_seconds': 30, 'max_requests': selected['files'],
              'max_data_entries': MAX_ENTRIES, 'max_data_files': MAX_FILES}
    if plan['caps'] != limits:
        raise ValueError('limits differ')
    identities = selected['identities']
    if [(p['slug'], p['repository'], p['commit']) for p in plan['projects']] != identities:
        raise ValueError('project identity/order')
    seen = set()
    rows = []
    for project in plan['projects']:
        total = 0
        for row in project['files']:
            dest, source = safe(row['destination']), safe(row['source_path'])
            if dest.as_posix() != project['slug'] + '/' + source.as_posix() or dest.as_posix().casefold() in seen:
                raise ValueError('destination identity/collision')
            seen.add(dest.as_posix().casefold())
            if row['repository'] != project['repository'] or row['commit'] != project['commit'] or row['mode'] != '100644':
                raise ValueError('repository/commit/mode')
            if type(row['bytes']) is not int or not 0 < row['bytes'] <= CAP:
                raise ValueError('file byte size')
            if not re.fullmatch('[0-9a-f]{40}', row['git_blob_sha1']):
                raise ValueError('blob')
            if row.get('sha256') is not None and not re.fullmatch('[0-9a-f]{64}', row['sha256']):
                raise ValueError('sha256')
            if source.suffix.lower() in ('.py', '.sh', '.js', '.exe', '.dll', '.dylib'):
                raise ValueError('executable/script not in scope')
            url = 'https://raw.githubusercontent.com/' + row['repository'] + '/' + row['commit'] + '/' + urllib.parse.quote(row['source_path'], safe='/')
            if row['raw_url'] != url:
                raise ValueError('URL identity')
            total += row['bytes']
            rows.append(row)
        if total != project['bytes'] or len(project['files']) != project['files_count'] or total > CAP:
            raise ValueError('project budget')
    total = sum(row['bytes'] for row in rows)
    if (len(rows), total) != (selected['files'], selected['bytes']) or total > CAP:
        raise ValueError('batch census')
    if (plan['planned_files'], plan['planned_bytes']) != (len(rows), total):
        raise ValueError('plan totals')
    if baseline['bytes'] + total > AGGREGATE or baseline['file_count'] + len(rows) > MAX_FILES:
        raise ValueError('aggregate plan cap')
    return rows


def load(here, profile_id='v1'):
    selected = profile(profile_id)
    raw = bounded(here / 'protocol.json')
    if sha(raw) != selected['protocol_sha256']:
        raise ValueError('protocol pin')
    plan = decode(raw)
    original = bounded(here / 'existing-data-inventory.json')
    if sha(original) != plan['baseline_sha256']:
        raise ValueError('baseline pin')
    baseline = decode(original)
    return plan, baseline, validate_protocol(plan, baseline, profile_id)


def git(root, args):
    proc = subprocess.run(['git', *args], cwd=root, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3, check=True)
    if len(proc.stdout) > CAP:
        raise ValueError('Git output too large')
    return proc.stdout


def git_identity(root):
    """Read the local checkout's small HEAD/ref witness without a subprocess.

    Managed worktree/gitfile indirection is intentionally outside this local
    acquisition helper. Include packed refs so changes between metadata samples
    cannot be silently adopted even when a loose branch currently overrides it.
    """
    gitdir = contained(root, root / '.git')
    if not gitdir.is_dir():
        raise ValueError('ordinary local .git directory required')
    head_path = contained(root, gitdir / 'HEAD')
    raw_head = bounded(head_path, 4096)
    head = raw_head.decode('ascii').strip()
    witnesses = {'HEAD': sha(raw_head)}
    packed_path = contained(root, gitdir / 'packed-refs')
    packed = bounded(packed_path, MIB) if packed_path.exists() else None
    witnesses['packed-refs'] = sha(packed) if packed is not None else None
    if head.startswith('ref: '):
        ref = head[5:]
        if not ref.startswith('refs/heads/'):
            raise ValueError('non-branch HEAD reference unsupported')
        ref_path = contained(root, gitdir / safe(ref))
        if ref_path.exists():
            raw_ref = bounded(ref_path, 4096)
            witnesses[ref] = sha(raw_ref)
            resolved = raw_ref.decode('ascii').strip()
        else:
            witnesses[ref] = None
            matches = []
            for line in (packed or b'').decode('ascii').splitlines():
                if line.startswith(('#', '^')) or not line:
                    continue
                fields = line.split(' ')
                if len(fields) != 2 or not re.fullmatch('[0-9a-f]{40}', fields[0]):
                    raise ValueError('malformed packed reference')
                if fields[1] == ref:
                    matches.append(fields[0])
            if len(matches) != 1:
                raise ValueError('missing/ambiguous packed HEAD')
            resolved = matches[0]
    else:
        resolved = head
    if not re.fullmatch('[0-9a-f]{40}', resolved):
        raise ValueError('invalid direct Git identity')
    return {'resolved_head': resolved, 'witnesses': witnesses}


def material_paths(root, here, profile_id='v1'):
    profile(profile_id)
    paths = {name: here / name for name in MATERIAL}
    if profile_id in ('v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8'):
        for name in ('fetch.py', 'test_fetch.py'):
            paths['shared/' + name] = root / PROFILES['v1']['directory'] / name
    if profile_id in ('v3', 'v4', 'v5', 'v6', 'v7'):
        paths['native_snapshot.py'] = here / 'native_snapshot.py'
    if profile_id=='v6':paths['cache_transport.py']=here/'cache_transport.py'
    if profile_id=='v7':
        paths['shared/cache_transport.py']=root/'experiments/licensed_acquisition_v6/cache_transport.py'
        paths['cache-source-profile.json']=here/'cache-source-profile.json'
    return paths


def material(root, here, expected, profile_id='v1'):
    """Final finite sample after subprocess and payload scans, never rebased."""
    identity = git_identity(root)
    # No Git subprocess or HEAD read follows these complete material hashes.
    current = {name: sha(bounded(path))
               for name, path in material_paths(root, here, profile_id).items()}
    if (current != expected['files'] or identity != expected['git_identity']
            or identity['resolved_head'] != expected['head']):
        raise ValueError('runtime material/HEAD changed after metadata')


def committed(root, here, profile_id='v1'):
    selected = profile(profile_id)
    relative = here.relative_to(root)
    if relative.as_posix() != selected['directory']:
        raise ValueError('fetch requires reviewed promoted directory')
    identity = git_identity(root)
    head = git(root, ['rev-parse', 'HEAD']).decode().strip()
    if not re.fullmatch('[0-9a-f]{40}', head):
        raise ValueError('HEAD')
    hashes = {}
    for name, path in material_paths(root, here, profile_id).items():
        contained(root, path)
        raw = bounded(path)
        recorded = git(root, ['show', head + ':' + path.relative_to(root).as_posix()])
        if recorded != raw:
            raise ValueError('helper differs from committed bytes: ' + name)
        hashes[name] = sha(raw)
    expected = {'head': head, 'files': hashes, 'git_identity': identity}
    # No metadata subprocess after this exact current-byte/HEAD sample.
    material(root, here, expected, profile_id)
    return expected


def payload(row, raw):
    if len(raw) != row['bytes']:
        raise ValueError('payload size')
    if raw.startswith(b'version https://git-lfs.github.com/spec/'):
        raise ValueError('LFS pointer')
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != row['git_blob_sha1'] or (row.get('sha256') and sha(raw) != row['sha256']):
        raise ValueError('payload hash')
    return {'bytes': len(raw), 'sha256': sha(raw)}


@contextmanager
def alarm(seconds):
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous = signal.setitimer(signal.ITIMER_REAL, 0)
    started = time.monotonic()
    def expire(signum, frame):
        raise TimeoutError('wall deadline')
    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous[0]:
            signal.setitimer(signal.ITIMER_REAL, max(0.000001, previous[0] - (time.monotonic() - started)), previous[1])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('redirect refused')


def fetch_one(row, request_record, raw_path, allowance, remaining):
    """No retries, redirect, archive extraction, execution, or authentication."""
    request_record.update(url=row['raw_url'], status='request_started', received_bytes=0)
    req = urllib.request.Request(row['raw_url'], headers={
        'User-Agent': 'KiCad-Autorouter-bounded-development-acquisition/2', 'Accept-Encoding': 'identity'})
    limit = min(row['bytes'] + 1, allowance + 1)
    chunks = []
    started = time.monotonic()
    try:
        with alarm(min(30, remaining())):
            try:
                response = urllib.request.build_opener(NoRedirect()).open(req, timeout=min(30, remaining()))
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                request_record.update(http_status=response.code, final_url=response.url,
                                      content_type=response.headers.get('Content-Type'),
                                      content_encoding=response.headers.get('Content-Encoding'),
                                      content_length=response.headers.get('Content-Length'))
                if response.url != row['raw_url'] or request_record['content_encoding'] not in (None, 'identity'):
                    raise ValueError('response URL/encoding')
                while request_record['received_bytes'] < limit:
                    remaining()
                    block = response.read1(min(65536, limit - request_record['received_bytes']))
                    if not block:
                        break
                    chunks.append(block)
                    request_record['received_bytes'] += len(block)
                raw = b''.join(chunks)
                with raw_path.open('xb') as stream:
                    stream.write(raw)
                request_record['response_sha256'] = sha(raw)
                if response.code != 200:
                    raise ValueError('HTTP status ' + str(response.code))
        request_record['status'] = 'response_received'
        return raw
    except BaseException as exc:
        raw = b''.join(chunks)
        if not raw_path.exists():
            with raw_path.open('xb') as stream:
                stream.write(raw)
        request_record.update(status='failed', error=type(exc).__name__ + ': ' + str(exc), response_sha256=sha(raw))
        raise
    finally:
        request_record['wall_seconds'] = time.monotonic() - started


def write_json(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    partial = path.with_suffix('.json.partial')
    with partial.open('wb') as stream:
        stream.write(raw)
    os.replace(partial, path)
    return raw


def publish(out, record, stable, remaining):
    """Final scans precede canonical equality and the final deadline sample."""
    path = out / 'receipt.json'
    try:
        stable()
        record['wall_seconds_sample_before_publication'] = 300 - remaining()
        raw = write_json(path, record)
        inventory(out, cap=MAX_OUTPUT)
        stable()
        if bounded(path) != raw or decode(raw) != record:
            raise ValueError('receipt changed during publication')
        remaining()
    except BaseException as exc:
        if path.exists():
            os.replace(path, out / 'receipt.invalidated.json')
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      error=type(exc).__name__ + ': ' + str(exc), original_inputs_unchanged=False)
        try:
            write_json(path, record)
        except BaseException as publication_error:
            record['publication_error'] = type(publication_error).__name__ + ': ' + str(publication_error)
            if path.exists():
                os.replace(path, out / 'receipt.failed-publication.json')
        raise


def acquire(root, here, out, plan, baseline, rows, runtime, started, transport=fetch_one, profile_id='v1'):
    selected = profile(profile_id)
    if plan['destination'] != '.data/' + selected['destination_root']:
        raise ValueError('acquisition profile/destination mismatch')
    destination = contained(root, root / plan['destination'])
    out = contained(root, out)
    if destination.exists() or out.exists():
        raise ValueError('fresh output and destination required; preserve failed attempts')
    acquired, requests = {}, []
    frozen_outputs = {}
    def remaining():
        value = 300 - (time.monotonic() - started)
        if value <= 0:
            raise TimeoutError('invocation deadline')
        return value
    def stable():
        remaining()
        if committed(root, here, profile_id) != runtime:
            raise ValueError('runtime material/HEAD changed')
        # Check source after subprocess-bearing Git operations, never before only.
        inventory(root / '.data', extend(baseline, acquired, destination_root=selected['destination_root']))
        for name, digest in frozen_outputs.items():
            if sha(bounded(out / name)) != digest:
                raise ValueError('completed response evidence changed')
        material(root, here, runtime, profile_id)
        # Recheck data after material's final HEAD witness; do not rebase any hashes.
        inventory(root / '.data', extend(baseline, acquired, destination_root=selected['destination_root']))
        for name, digest in frozen_outputs.items():
            if sha(bounded(out / name)) != digest:
                raise ValueError('completed response evidence changed')
        remaining()
    out.mkdir()
    destination.mkdir()
    record = {'schema': 1, 'status': 'running', 'split': 'development', 'protocol_sha256': selected['protocol_sha256'],
              'runtime': runtime, 'planned_files': len(rows), 'planned_bytes': sum(r['bytes'] for r in rows),
              'caps': plan['caps'], 'capacity_change': plan['capacity_change'],
              'preexisting_inventory_sha256': plan['baseline_sha256'], 'files': [], 'requests': requests,
              'native_executed': False, 'engine_executed': False, 'dependency_closure_verified': False,
              'redistribution_approved': False, 'independent_families_established': False,
              'routing_support': 'unqualified', 'original_inputs_unchanged': False,
              'accounting_point': 'stored wall sample precedes final publication checks; final deadline enforced after them'}
    try:
        stable()
        write_json(out / 'receipt.json', record)
        for index, row in enumerate(rows):
            remaining()
            req = {'index': index, 'destination': row['destination']}
            requests.append(req)
            raw_name = f'response-{index:03}.bin'
            received = sum(r.get('received_bytes', 0) for r in requests)
            raw = transport(row, req, out / raw_name, CAP - received, remaining)
            if sum(r.get('received_bytes', 0) for r in requests) > CAP:
                raise ValueError('invocation network cap')
            info = payload(row, raw)
            if bounded(out / raw_name) != raw or req.get('response_sha256') != sha(raw):
                raise ValueError('response artifact/returned bytes differ')
            frozen_outputs[raw_name] = sha(raw)
            target = contained(root, destination / safe(row['destination']))
            target.parent.mkdir(parents=True, exist_ok=True)
            contained(root, target)
            with target.open('xb') as stream:
                stream.write(raw)
            acquired[row['destination']] = info
            record['files'].append({**row, **info, 'local_path': str(target.relative_to(root))})
            stable()
            record['received_bytes'] = sum(r.get('received_bytes', 0) for r in requests)
            write_json(out / 'receipt.json', record)
        expected = extend(baseline, acquired, destination_root=selected['destination_root'])
        record.update(status='acquired_unqualified', original_inputs_unchanged=True,
                      acquired_files=len(acquired), acquired_bytes=sum(r['bytes'] for r in acquired.values()),
                      aggregate_data_files=expected['file_count'], aggregate_data_bytes=expected['bytes'])
        publish(out, record, stable, remaining)
        return record
    except BaseException as exc:
        # Preserve every verified/partial payload and the prior receipt, never delete source files.
        path = out / 'receipt.json'
        if path.exists():
            prior = decode(bounded(path))
            if prior.get('status') == 'acquired_unqualified':
                os.replace(path, out / 'receipt.interrupted-positive.json')
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      error=type(exc).__name__ + ': ' + str(exc),
                      received_bytes=sum(r.get('received_bytes', 0) for r in requests), original_inputs_unchanged=False)
        try:
            # Source unchanged is separately checked even when a new partial destination is incomplete.
            observed = inventory(root / '.data')
            record['preexisting_files_unchanged'] = all(observed['files'].get(k) == v for k, v in baseline['files'].items())
        except BaseException as audit_error:
            record['preexisting_files_unchanged'] = False
            record['failure_audit_error'] = type(audit_error).__name__ + ': ' + str(audit_error)
        record['wall_seconds_on_failure'] = time.monotonic() - started
        try:
            write_json(path, record)
        except BaseException as publication_error:
            record['publication_error'] = type(publication_error).__name__ + ': ' + str(publication_error)
            if path.exists():
                os.replace(path, out / 'receipt.failed-finalization.json')
        raise


def execute(args, started, here=None, profile_id='v1'):
    selected = profile(profile_id)
    here = Path(__file__).absolute().parent if here is None else Path(here).absolute()
    root = next(p for p in here.parents if (p / 'autorouter/pipeline.py').is_file())
    plan, baseline, rows = load(here, profile_id)
    inventory(root / '.data', baseline)
    if not args.fetch:
        print(json.dumps({'action': 'plan_only', 'network_requests': 0, 'planned_files': len(rows),
                          'planned_bytes': plan['planned_bytes'], 'current_data_bytes': baseline['bytes'],
                          'post_acquisition_data_bytes': baseline['bytes'] + plan['planned_bytes'],
                          'caps': plan['caps'], 'closure_verified': False}))
        return
    runtime = committed(root, here, profile_id)
    name = safe(args.output)
    if len(name.parts) != 2 or name.parts[0] != '.runs' or not re.fullmatch(re.escape(selected['output_prefix']) + '[0-9]{3}', name.parts[1]):
        raise ValueError('output must be a fresh direct .runs/' + selected['output_prefix'] + 'NNN directory')
    lock_path = contained(root, root / '.runs/licensed-acquisition.lock')
    with lock_path.open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = acquire(root, here, root / name, plan, baseline, rows, runtime, started, profile_id=profile_id)
        print(json.dumps({k: result[k] for k in ('status', 'acquired_files', 'acquired_bytes', 'aggregate_data_bytes')}))


@contextmanager
def cancellation():
    old_handlers = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    def cancel(signum, frame):
        raise KeyboardInterrupt('cancelled signal ' + str(signum))
    try:
        for signum in old_handlers:
            signal.signal(signum, cancel)
        yield
    finally:
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)


def main(profile_id='v1', here=None):
    selected = profile(profile_id)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--output', default='.runs/' + selected['output_prefix'] + '001')
    args = parser.parse_args()
    started = time.monotonic()
    with cancellation(), alarm(300):
        execute(args, started, here, profile_id)


if __name__ == '__main__':
    main()
