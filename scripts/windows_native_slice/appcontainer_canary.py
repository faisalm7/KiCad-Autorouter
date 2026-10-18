"""Bounded Windows-only AppContainer experiment, never Native admission.

Uses the existing Job Object runner and an independently positive TCP control.
No installer, KiCad, Java, CAD, firewall rule or network exemption is involved.
"""
import argparse
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


def execute(argv, *, cwd, log, seconds=30):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('This compiler canary is x64 only')
    scope = args.scope.absolute()
    report = args.report.absolute()
    setup = scope.with_name(scope.name + '-setup')
    if scope.exists() or setup.exists() or report.exists() or not scope.parent.is_dir() or report.parent != scope.parent:
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
                                        cwd=setup, log=dns_log, seconds=5)
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
        guard = AppContainerLaunch(scope)
        with guard:
            source = Path(__file__).with_name('appcontainer_probe.c').resolve(strict=True)
            builds = []
            for role in (1, 2):
                target = setup / ('probe-parent.exe' if role == 1 else 'probe-child.exe')
                argv = [str(exe), '/nologo', '/W4', '/WX', '/O1', '/MT', '/DUNICODE', '/D_UNICODE',
                        '/DPROBE_ROLE=' + str(role), *['/I' + str(p) for p in includes], str(source),
                        '/Fo' + str(setup / ('role' + str(role) + '.obj')), '/Fe' + str(target),
                        '/link', '/INCREMENTAL:NO', *['/LIBPATH:' + str(p) for p in libraries],
                        'kernel32.lib', 'advapi32.lib', 'ws2_32.lib']
                before = time.monotonic()
                builds.append({**execute(argv, cwd=setup, log=setup / ('compile' + str(role) + '.log')),
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
            for label, hold, cap, cancel in [('denial', 0, 15, None), ('descendant_cancel', 15, 10, 2)]:
                log = guard.scratch / (label + '.log')
                process = run([parent, address, str(port), child, str(hold)], cwd=guard.scratch,
                              log=log, root=guard.scope, firewall_check=None, appcontainer=guard,
                              seconds=cap, cancel_after=cancel)
                rows = records(log)
                result['cases'].append({'label': label, 'process': process, 'records': rows})
                check_tokens(rows, guard.profile_sid, cancelled=cancel is not None)
                expected = 'success' if cancel is None else 'cancelled'
                if process['status'] != expected or process['cleanup_complete'] is not True or process['process_count'] < 2:
                    raise RuntimeError('Actual bounded descendant process/cleanup outcome differs')
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
            result['cleanup'] = guard.cleanup_receipt
    finally:
        stop.set(); listener.close(); server.join(timeout=3)
        result['owned_server_thread_reaped'] = not server.is_alive()
        result['passed'] = result['passed'] and not server.is_alive()
        result['wall_seconds_before_report'] = time.monotonic() - started
        result['controller_CPU_seconds_before_report'] = time.process_time() - cpu_started
        result['accounting'] = 'Setup and probe Job CPU include exited descendants; controller CPU is separate. Whole CI CPU and post-report exit are unmeasured, not zero. No speed claim.'
        with report.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
        print(json.dumps(result, sort_keys=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
