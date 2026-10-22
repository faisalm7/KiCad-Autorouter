"""Bounded Windows-only AppContainer experiment, never Native admission.

Uses the existing Job Object runner and an independently positive TCP control.
No installer, KiCad, Java, CAD, firewall rule or network exemption is involved.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import sys
import threading
import time

if os.name != 'nt':
    raise RuntimeError('Windows-only experimental canary; do not substitute another OS')

from appcontainer_launch import AppContainerLaunch
from windows_process import run, run_owned_setup


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(argv, *, cwd, log, seconds=30, retain_raw=False):
    """Authoring/compiler setup only, not a routing or isolation outcome."""
    process = None
    diagnostic = {'kind': 'additional-owned-setup-process'}
    try:
        process = run_owned_setup(argv, cwd=cwd, log=log, root=cwd, seconds=seconds)
        with Path(str(log) + '.process.json').open('x', encoding='utf-8') as stream:
            json.dump(process, stream, indent=2); stream.write('\n')
    finally:
        # Even API/bound/cleanup exceptions must preserve available diagnostic
        # bytes. An ephemeral path/hash cannot recover a failed compiler log.
        diagnostic.update(process=process, process_receipt_available=process is not None)
        if retain_raw:
            material = retain_owned_log(log, 'setup:' + Path(log).name, process)
            diagnostic['log_material'] = material
            if material['complete'] is not True:
                diagnostic['log_read_error'] = 'actual owned setup log retention incomplete'
        else:
            try:
                with Path(log).open('rb') as stream:
                    raw = stream.read(256 * 1024 + 1)
                diagnostic.update(log_utf8=raw[:256 * 1024].decode('utf-8', errors='replace'),
                                  log_truncated=len(raw) > 256 * 1024)
            except OSError as exc:
                diagnostic['log_read_error'] = type(exc).__name__ + ': ' + str(exc)
        print(json.dumps(diagnostic), flush=True)
    if 'log_read_error' in diagnostic:
        raise RuntimeError('Setup diagnostic unavailable; no success claim')
    if process['status'] != 'success' or process['cleanup_complete'] is not True:
        raise RuntimeError('Compiler/setup command failed; retained log: ' + str(log))
    return process


def compiler():
    base = Path(os.environ['ProgramFiles(x86)'])
    allowed = [Path(os.environ[key]) / 'Microsoft Visual Studio'
               for key in ('ProgramFiles', 'ProgramFiles(x86)')]
    installations = [p for root in allowed if (root / '2022').is_dir()
                     for p in (root / '2022').iterdir()
                     if p.is_dir() and (p / 'VC/Tools/MSVC').is_dir()]
    if not 1 <= len(installations) <= 8:
        raise RuntimeError('Bounded preinstalled Visual Studio2022 discovery failed')
    installation = sorted(installations)[0].resolve(strict=True)
    versions = lambda path: sorted((p for p in path.iterdir() if p.is_dir() and
                                    all(x.isdecimal() for x in p.name.split('.'))),
                                   key=lambda p: tuple(map(int, p.name.split('.'))))
    vc = versions(installation / 'VC/Tools/MSVC')[-1]
    sdk = versions(base / 'Windows Kits/10/Include')[-1]
    exe = vc / 'bin/Hostx64/x64/cl.exe'
    includes = [vc / 'include', sdk / 'ucrt', sdk / 'shared', sdk / 'um']
    libraries = [vc / 'lib/x64', base / 'Windows Kits/10/Lib' / sdk.name / 'ucrt/x64',
                 base / 'Windows Kits/10/Lib' / sdk.name / 'um/x64']
    for p in [exe, *includes, *libraries]:
        if not p.exists():
            raise RuntimeError('Compiler/SDK prerequisite absent: ' + str(p))
    return exe, includes, libraries, {'cl_sha256': digest(exe), 'MSVC_version': vc.name,
                                      'SDK_version': sdk.name,
                                      'dependency_scope': 'Preinstalled runner tools observed and pinned before this canary, not a product platform qualification.'}


def records(path):
    raw = Path(path).read_bytes()
    if len(raw) > 256 * 1024:
        raise RuntimeError('Canary log exceeded bound')
    return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]



def retain_owned_log(path, label, process):
    """Existing bounded stdout/chunk convention; material is never authority."""
    meta = dict(kind='owned-canary-log-material', label=label, path=str(path),
                complete=False, process_receipt_available=process is not None)
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(256 * 1024 + 1)
        size = Path(path).stat().st_size
        kept = raw[:256 * 1024]
        meta.update(bytes=size, retained_bytes=len(kept), sha256=hashlib.sha256(kept).hexdigest(),
                    chunks=(len(kept) + 24575) // 24576, truncated=size != len(kept))
        meta['complete'] = (size == len(raw) == len(kept) and process is not None
                            and meta['sha256'] == process.get('log_sha256'))
        print(json.dumps(meta), flush=True)
        for index, offset in enumerate(range(0, len(kept), 24 * 1024)):
            print(json.dumps(dict(kind='owned-canary-log-base64-chunk', label=label, index=index,
                                  data=base64.b64encode(kept[offset:offset + 24 * 1024]).decode('ascii'))), flush=True)
    except Exception as exc:
        meta.update(complete=False, error=type(exc).__name__ + ': ' + str(exc)[:256])
        print(json.dumps(meta), flush=True)
    return meta


def check_tokens(rows, sid, *, cancelled=False):
    self_rows = [row for row in rows if row.get('kind') == 'self_token']
    observed_child = [row for row in rows if row.get('kind') == 'suspended_child_token']
    if len(self_rows) != 2 or {r['role'] for r in self_rows} != {1, 2} or len(observed_child) != 1:
        raise RuntimeError('Both actual executable tokens and suspended-child observation required')
    for row in [*self_rows, *observed_child]:
        if row.get('is_appcontainer') != 1 or row.get('capabilities') != 0 or row.get('sid') != sid:
            raise RuntimeError('Actual token/capabilities/SID mismatch')
    child = next(r for r in self_rows if r['role'] == 2)
    if observed_child[0]['pid'] != child['pid']:
        raise RuntimeError('Child token observations do not identify the same process')
    tcp = [row for row in rows if row.get('kind') == 'tcp']
    if len(tcp) != 4 or {(r['role'], r['endpoint']) for r in tcp} != {
            (role, endpoint) for role in (1, 2) for endpoint in ('owned_loopback', 'public_ipv4')}:
        raise RuntimeError('Both executable endpoint observations required')
    if any(r.get('connected') is not False or r.get('wsa_error') != 10013 or
           r.get('explicit_access_denied') is not True for r in tcp):
        raise RuntimeError('Unknown/timeout/connect failure is not an explicit access-denied observation')
    if cancelled and not any(r.get('kind') == 'child_resumed' and r.get('pid') == child['pid'] for r in rows):
        raise RuntimeError('Cancellation did not observe the actual resumed child')


def check_mutations(rows):
    """Require exact denial rows bound to both already checked actual tokens."""
    tokens = [row for row in rows if row.get('kind') == 'self_token']
    if (len(tokens) != 2 or any(type(row.get('role')) is not int or type(row.get('pid')) is not int
            or row['pid'] <= 0 for row in tokens) or {row['role'] for row in tokens} != {1, 2}):
        raise RuntimeError('Two typed actual mutation token identities required')
    pids = {row['role']: row['pid'] for row in tokens}
    if len(set(pids.values())) != 2:
        raise RuntimeError('Distinct actual parent/child PIDs required')
    kinds = {'state_mutation', 'policy_mutation', 'mutation_engine_open', 'mutation_engine_close'}
    actual = [row for row in rows if row.get('kind') in kinds]
    expected = {(role, 'state_mutation', target, operation)
                for role in (1, 2) for target in (0, 1) for operation in ('write_dac', 'write_owner')}
    expected |= {(role, 'policy_mutation', target, 'reapply_same_protected_dacl')
                 for role in (1, 2) for target in (0, 1)}
    expected |= {(role, kind, None, None) for role in (1, 2)
                 for kind in ('mutation_engine_open', 'mutation_engine_close')}
    observed = set()
    for row in actual:
        role, kind, target = row.get('role'), row['kind'], row.get('target')
        key = (role, kind, target, row.get('operation'))
        if (type(role) is not int or role not in pids or type(row.get('pid')) is not int or
                row['pid'] != pids[role] or key not in expected or key in observed or
                (kind in ('state_mutation', 'policy_mutation') and type(target) is not int) or
                type(row.get('winerror')) is not int):
            raise RuntimeError('Missing/duplicated/wrong-identity mutation observation')
        observed.add(key)
        engine = kind.startswith('mutation_engine_')
        if engine:
            if row['winerror'] != 0:
                raise RuntimeError('LowBox WFP entry/close unavailable; not an object-mutation proof')
        elif (row['winerror'] != 5 or row.get('explicit_access_denied') is not True or
              (kind == 'state_mutation' and row.get('opened') is not False)):
            raise RuntimeError('Only explicit error5 denial qualifies; no unknown or access grant')
    if observed != expected:
        raise RuntimeError('Both actual executables must complete every fresh-object mutation control')
    return {'passed': True, 'state_access_denials': 8, 'policy_same_DACL_denials': 4,
            'scope': 'Two own state paths rights requests and sublayer/filter1 same-DACL setters only.'}


def main(argv=None, *, persistent_guard=None, prepared_setup=None, lowbox_mutation=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(argv)
    if platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('This compiler canary is x64 only')
    if type(lowbox_mutation) is not bool or (lowbox_mutation and persistent_guard is None):
        raise RuntimeError('Mutation control requires exact live persistent owner')
    scope = args.scope.absolute()
    report = args.report.absolute()
    setup = scope.with_name(scope.name + '-setup')
    if persistent_guard is not None:
        from persistent_guard_state import PersistentGuardState
        if type(persistent_guard) is not PersistentGuardState or persistent_guard.scope != scope or prepared_setup != setup:
            raise RuntimeError('exact live persistent guard and same owned setup required')
    elif prepared_setup is not None:
        raise RuntimeError('setup reuse is restricted to the explicit persistent experiment')
    if scope.exists() or (setup.exists() and persistent_guard is None) or report.exists() or not scope.parent.is_dir() or report.parent != scope.parent:
        raise RuntimeError('Fresh sibling scope/report required')
    started = time.monotonic()
    cpu_started = time.process_time()
    result = {'schema': 1, 'kind': 'non-admitting-Windows-AppContainer-canary007',
              'passed': False, 'Native_admitted': False, 'Native_executed': False,
              'KiCad_Java_installer_executed': False, 'GUI': False,
              'actual_windows': platform.platform(), 'architecture': platform.machine(),
              'controller_Python': sys.version, 'controller_sha256': digest(__file__),
              'worker_source_sha256': digest(Path(__file__).with_name('appcontainer_probe.c')),
              'cases': [], 'errors': [],
              'scope': 'Owned IPv4 TCP/token/job observations only; no all-network/profile, KiCad/Java compatibility, Native delivery or Windows product claim.'}
    if persistent_guard is not None:
        result['kind'] = 'non-admitting-Windows-persistent-SID-canary011'
        result['scope'] = ('Real persistent SID policy plus owned IPv4 TCP/token/normal/cancel observations only. '
                           'No IPv6/UDP/inbound/controller-death/reuse/lowbox-mutation, Native or Windows product qualification.')
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('127.0.0.1', 0)); listener.listen(8); listener.settimeout(.2)
    port = listener.getsockname()[1]
    stop = threading.Event()

    def accept_loop():
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
                connection.close()
            except socket.timeout:
                continue
            except OSError:
                break

    server = threading.Thread(target=accept_loop, daemon=False)
    server.start()
    guard = None
    try:
        # Freeze one public address before attempts; no endpoint search after an
        # unfavorable result. No credentials, request payload, TLS or CAD sent.
        dns_log = setup / 'DNS.log'
        result['DNS_process'] = execute([sys.executable, '-I', '-B', str(Path(__file__).with_name('appcontainer_dns.py').resolve())],
                                        cwd=setup, log=dns_log, seconds=5, retain_raw=persistent_guard is not None)
        dns = json.loads(dns_log.read_text(encoding='utf-8'))
        if set(dns) != {'hostname', 'IPv4'} or dns['hostname'] != 'api.github.com':
            raise RuntimeError('Unexpected DNS prerequisite receipt')
        address = dns['IPv4']
        result['endpoints'] = {'public_hostname': 'api.github.com', 'public_IPv4': address,
                               'public_port': 443, 'owned_loopback_port': port}
        positives = []
        for name, target in [('owned_loopback', ('127.0.0.1', port)), ('public_ipv4', (address, 443))]:
            with socket.create_connection(target, timeout=3):
                positives.append({'endpoint': name, 'connected': True, 'payload_bytes_sent': 0})
        result['independently_positive_connections_before'] = positives
        exe, includes, libraries, toolchain = compiler()
        result['compiler'] = toolchain
        guard = AppContainerLaunch(scope, persistent_guard=persistent_guard)
        with guard:
            source = Path(__file__).with_name('appcontainer_probe.c').resolve(strict=True)
            builds = []
            for role in (1, 2):
                target = setup / ('probe-parent.exe' if role == 1 else 'probe-child.exe')
                argv = [str(exe), '/nologo', '/W4', '/WX', '/O1', '/MT', '/DUNICODE', '/D_UNICODE',
                        '/DPROBE_ROLE=' + str(role), *['/I' + str(p) for p in includes], str(source),
                        '/Fo' + str(setup / ('role' + str(role) + '.obj')), '/Fe' + str(target),
                        '/link', '/INCREMENTAL:NO', *['/LIBPATH:' + str(p) for p in libraries],
                        'kernel32.lib', 'advapi32.lib', 'ws2_32.lib', 'fwpuclnt.lib', 'ole32.lib']
                before = time.monotonic()
                builds.append({**execute(argv, cwd=setup, log=setup / ('compile' + str(role) + '.log'), retain_raw=persistent_guard is not None),
                               'wall_seconds': time.monotonic() - before,
                               'exe': str(target), 'exe_sha256': digest(target)})
            if builds[0]['exe_sha256'] == builds[1]['exe_sha256']:
                raise RuntimeError('Different role builds unexpectedly identical')
            for build in builds:
                raw = Path(build['exe']).read_bytes()
                if not 0 < len(raw) <= 4 * 1024**2:
                    raise RuntimeError('Unexpected owned canary image size')
                with (guard.tool_root / Path(build['exe']).name).open('xb') as stream:
                    stream.write(raw)
            result['builds'] = builds
            result['frozen_before_execution'] = {'parent_sha256': builds[0]['exe_sha256'],
                                                  'child_sha256': builds[1]['exe_sha256'],
                                                  'SID': guard.profile_sid,
                                                  'budgets': {'positive_seconds': 15, 'cancel_seconds': 10,
                                                              'cancel_after_seconds': 2}}
            parent, child = (str(guard.tool_root / name) for name in ('probe-parent.exe', 'probe-child.exe'))
            mutation_targets = []
            if lowbox_mutation:
                # Seal the same tools/scratch and arm the same owner before naming
                # only its own CREATE_NEW files and WFP objects; no extra Job.
                guard.before_launch(parent, guard.scratch, guard.scratch / 'denial.log', guard.scope, 15)
                mutation_targets = persistent_guard.mutation_targets()
                result['mutation_targets'] = {'state_paths': mutation_targets[:2],
                                              'WFP_keys': mutation_targets[2:]}
                result['kind'] = 'non-admitting-Windows-LowBox-owned-mutation-control015'
                result['scope'] = ('Fresh own journal/context WRITE_DAC/WRITE_OWNER open requests and '
                                   'own sublayer/filter1 same protected-DACL setters from both zero-capability '
                                   'tokens; existing IPv4/normal/cancel. No content/delete/owner-setter, other '
                                   'filters, crash/reuse, IPv6/UDP/inbound, Native or Windows product claim.')
            for label, hold, cap, cancel in [('denial', 0, 15, None), ('descendant_cancel', 15, 10, 2)]:
                log = guard.scratch / (label + '.log')
                process = None
                probe_error = None
                try:
                    probe_argv = [parent, address, str(port), child, str(hold)]
                    if lowbox_mutation and cancel is None:
                        probe_argv += mutation_targets
                    process = run(probe_argv, cwd=guard.scratch,
                                  log=log, root=guard.scope, firewall_check=None, appcontainer=guard,
                                  seconds=cap, cancel_after=cancel)
                    rows = records(log)
                    result['cases'].append({'label': label, 'process': process, 'records': rows})
                    check_tokens(rows, guard.profile_sid, cancelled=cancel is not None)
                    if lowbox_mutation and cancel is None:
                        result['mutation_control'] = check_mutations(rows)
                        guard.check_contract()
                    expected = 'success' if cancel is None else 'cancelled'
                    if process['status'] != expected or process['cleanup_complete'] is not True or process['process_count'] < 2:
                        raise RuntimeError('Actual bounded descendant process/cleanup outcome differs')
                except BaseException as exc:
                    probe_error = exc
                    raise
                finally:
                    if persistent_guard is not None:
                        material = retain_owned_log(log, label, process)
                        result.setdefault('probe_log_material', []).append(material)
                        if material['complete'] is not True and probe_error is None:
                            raise RuntimeError('Actual probe log retention is incomplete; no canary pass')
            result['guard_evidence'] = guard.evidence
        result['cleanup'] = guard.cleanup_receipt
        if result['cleanup'].get('cleanup_complete') is not True:
            raise RuntimeError('AppContainer/ACL/profile cleanup not established')
        # Reachability after the test separates policy denial from endpoint loss.
        for target in [('127.0.0.1', port), (address, 443)]:
            with socket.create_connection(target, timeout=3):
                pass
        result['independently_positive_connections_after'] = True
        result['passed'] = True
    except Exception as exc:
        result['errors'].append(type(exc).__name__ + ': ' + str(exc))
        if guard is not None:
            result['guard_evidence'] = guard.evidence
            result['cleanup'] = guard.cleanup_receipt
    finally:
        stop.set(); listener.close(); server.join(timeout=3)
        result['owned_server_thread_reaped'] = not server.is_alive()
        result['passed'] = result['passed'] and not server.is_alive()
        if persistent_guard is not None:
            try:
                if not result['passed']:
                    persistent_guard.poison('; '.join(result['errors']) or 'finite canary failed')
                persistent_guard.abandon()
            except Exception as exc:
                result['passed'] = False
                result['errors'].append('persistent final disposal: ' + type(exc).__name__ + ': ' + str(exc))
            result['persistent_guard'] = persistent_guard.receipt()
        result['wall_seconds_before_report'] = time.monotonic() - started
        result['controller_CPU_seconds_before_report'] = time.process_time() - cpu_started
        result['accounting'] = 'Setup and probe Job CPU include exited descendants; controller CPU is separate. Whole CI CPU and post-report exit are unmeasured, not zero. No speed claim.'
        with report.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
        print(json.dumps(result, sort_keys=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
