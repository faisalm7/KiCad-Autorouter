"""CI-only fixed DLL readiness and an explicitly selected finite SID canary.

The externally supplied source/protocol SHAs prevent a self-referential commit
pin. Default build-null creates no valid owner/policy/profile/socket. The
separate sid-canary stage reuses the bounded existing IPv4 control and cannot
admit Native, an installer or Windows product support.
"""
import time
START = time.monotonic()
CPU0 = time.process_time()
import argparse
import base64
from contextlib import ExitStack
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE_HEAD = '580793ac6087021bf9567f764df5b9f55bfab9db'
KIND = 'windows011-build-null-ABI-readiness-v1'
LIFETIME_KIND = 'windows011-persistent-SID-finite-canary-v1'
PREFIX = 'scripts/windows_native_slice/'
SOURCE_NAMES = tuple(PREFIX + name for name in (
    'persistent_guard_build.py', 'persistent_guard_build.ps1', 'persistent_sid_guard.c',
    'windows_process.py', 'appcontainer_canary.py', 'appcontainer_launch.py',
    'appcontainer_probe.c', 'appcontainer_dns.py', 'appcontainer_diagnostic.ps1'))


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path, limit=64 * 1024):
    raw = Path(path).read_bytes()
    require(len(raw) <= limit, 'bounded JSON required')
    return json.loads(raw)


def hosted():
    require(os.name == 'nt' and platform.machine().lower() in ('amd64', 'x86_64'), 'actual Windows x64 required')
    for key, expected in dict(GITHUB_ACTIONS='true', RUNNER_OS='Windows',
            RUNNER_ENVIRONMENT='github-hosted', GITHUB_REPOSITORY='faisalm7/KiCad-Autorouter').items():
        require(os.environ.get(key) == expected, 'standard owned hosted CI required: ' + key)
    require(Path(os.environ['GITHUB_WORKSPACE']).resolve(strict=True) == ROOT, 'exact checked-out workspace required')


def checkout(expected):
    require(re.fullmatch('[0-9a-f]{40}', expected or '') is not None, 'external source SHA required')
    require(os.environ.get('GITHUB_SHA') == expected, 'GITHUB_SHA differs from external source SHA')
    # Standard Actions checkout is detached. No Git command, config, fsmonitor,
    # hooks, history traversal, alternate checkout or packed-ref fallback.
    head = ROOT / '.git/HEAD'
    require((ROOT / '.git').is_dir() and not (ROOT / '.git').is_symlink(), 'ordinary checkout metadata required')
    require(head.is_file() and not head.is_symlink() and head.stat().st_size <= 128, 'bounded detached HEAD required')
    require(head.read_text(encoding='ascii').strip() == expected, 'detached checkout HEAD differs')


class GUID(C.Structure):
    _fields_ = [('Data1', C.c_uint32), ('Data2', C.c_uint16), ('Data3', C.c_uint16), ('Data4', C.c_ubyte * 8)]


class Info(C.Structure):
    _fields_ = [(name, C.c_uint32) for name in ('abi', 'bytes', 'state', 'poisoned')] + [
        ('sublayer', GUID), ('filters', GUID * 4), ('sid_bytes', C.c_uint32), ('sid', C.c_ubyte * 68)] + [
        (name, C.c_uint32) for name in ('jobs', 'processes', 'policy_may_exist', 'last_error',
                                     'abort_error', 'pending_create', 'pending_job')]


class Diagnostic(C.Structure):
    _fields_ = [(name, C.c_uint32) for name in
                ('abi', 'bytes', 'recorded', 'error', 'object_index', 'element_index')] + [
        ('stage', C.c_char * 48), ('predicate', C.c_char * 48)] + [
        (name, C.c_uint32) for name in ('expected_low', 'expected_high', 'actual_low', 'actual_high')]


def bind_library(path):
    """Bind the single SDK ABI; no guard/profile/policy is created here."""
    offsets = dict(abi=0, bytes=4, state=8, poisoned=12, sublayer=16, filters=32,
                   sid_bytes=96, sid=100, jobs=168, processes=172, policy_may_exist=176,
                   last_error=180, abort_error=184, pending_create=188, pending_job=192)
    require(C.sizeof(C.c_void_p) == 8 and C.sizeof(C.c_uint32) == 4 and C.sizeof(GUID) == 16,
            'exact x64 DWORD/GUID ABI required')
    require(C.sizeof(Info) == 196 and all(getattr(Info, key).offset == value for key, value in offsets.items()),
            '196-byte INFO layout differs')
    require(C.sizeof(Diagnostic) == 136 and Diagnostic.stage.offset == 24 and
            Diagnostic.predicate.offset == 72 and Diagnostic.expected_low.offset == 120,
            '136-byte read-only diagnostic layout differs')
    library = C.WinDLL(str(path), winmode=0x900)
    dword, owner = C.c_uint32, C.c_void_p
    owner_pointer, byte_pointer = C.POINTER(owner), C.POINTER(C.c_ubyte)
    signatures = {
        'PG_Create': [byte_pointer, dword, owner_pointer],
        'PG_GetInfo': [owner, C.POINTER(Info), dword],
        'PG_GetDiagnostic': [owner, C.POINTER(Diagnostic), dword],
        'PG_Arm': [owner], 'PG_CheckArmed': [owner],
        'PG_RegisterJob': [owner, C.c_void_p, C.POINTER(dword)],
        'PG_BeginCreate': [owner, dword], 'PG_Poison': [owner, dword],
        'PG_RegisterProcess': [owner, dword, C.c_void_p, C.POINTER(dword)],
        'PG_BeforeResume': [owner, dword], 'PG_SealLaunches': [owner],
        'PG_RemoveWhenEmpty': [owner], 'PG_AbandonAndFree': [owner_pointer]}
    for name, args in signatures.items():
        function = getattr(library, name)
        function.argtypes, function.restype = args, dword
    return library, signatures, offsets


def null_abi(path):
    library, signatures, offsets = bind_library(path)
    dword, owner = C.c_uint32, C.c_void_p
    info, diagnostic, slot, empty = Info(), Diagnostic(), dword(0xffffffff), owner()
    # Every owner is NULL. No valid SID, PG_OWNER, profile or armed context is
    # produced; the named functions return before their policy/lifecycle bodies.
    cases = [
        ('Create_null_output', 'PG_Create', (None, 0, None), 87),
        ('Create_null_SID', 'PG_Create', (None, 0, C.byref(empty)), 1337),
        ('GetInfo_null_owner', 'PG_GetInfo', (None, C.byref(info), C.sizeof(info)), 6),
        ('GetDiagnostic_null_owner', 'PG_GetDiagnostic', (None, C.byref(diagnostic), C.sizeof(diagnostic)), 6),
        ('Arm_null_owner', 'PG_Arm', (None,), 6),
        ('CheckArmed_null_owner', 'PG_CheckArmed', (None,), 6),
        ('RegisterJob_null_owner', 'PG_RegisterJob', (None, None, C.byref(slot)), 6),
        ('BeginCreate_null_owner', 'PG_BeginCreate', (None, 0), 6),
        ('Poison_null_owner', 'PG_Poison', (None, 87), 6),
        ('RegisterProcess_null_owner', 'PG_RegisterProcess', (None, 0, None, C.byref(slot)), 6),
        ('BeforeResume_null_owner', 'PG_BeforeResume', (None, 0), 6),
        ('SealLaunches_null_owner', 'PG_SealLaunches', (None,), 6),
        ('RemoveWhenEmpty_null_owner', 'PG_RemoveWhenEmpty', (None,), 6),
        ('Abandon_null_pointer', 'PG_AbandonAndFree', (None,), 87),
        ('Abandon_null_owner', 'PG_AbandonAndFree', (C.byref(empty),), 6)]
    rows = []
    for label, name, args, expected in cases:
        actual = int(getattr(library, name)(*args))
        rows.append(dict(case=label, export=name, expected=expected, actual=actual, passed=actual == expected))
        require(actual == expected, 'NULL ABI refusal differs: ' + label)
    require(empty.value is None and bytes(info) == bytes(196) and bytes(diagnostic) == bytes(136) and slot.value == 0xffffffff,
            'NULL ABI changed output storage or produced an owner')
    return dict(passed=True, exports_bound=sorted(signatures), outcomes=rows,
                INFO_bytes=C.sizeof(info), INFO_offsets=offsets, DIAGNOSTIC_bytes=C.sizeof(diagnostic), winmode=0x900,
                valid_owner_created=False, valid_SID_supplied=False, actual_policy_operations=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', default=os.environ.get('GUARD_EXPECTED_PROTOCOL_SHA'))
    parser.add_argument('--expected-source-sha', default=os.environ.get('GUARD_EXPECTED_SOURCE_SHA'))
    parser.add_argument('--scope', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--stage', choices=('build-null', 'sid-canary'), default='build-null')
    args = parser.parse_args()
    hosted()
    runner = Path(os.environ['RUNNER_TEMP']).absolute()
    scope, report = args.scope.absolute(), args.report.absolute()
    require(runner.resolve(strict=True) == runner and scope.parent == report.parent == runner,
            'canonical runner-temp direct siblings required')
    require(re.fullmatch('kicad-appcontainer007-[0-9a-f]{32}', scope.name) is not None and
            report.name == scope.name + '-build-report.json', 'exact fresh build scope/report names required')
    setup = scope.with_name(scope.name + '-setup')
    require(not any(path.exists() or path.is_symlink() for path in (scope, setup, report)), 'fresh exclusive destinations required')
    canary = args.stage == 'sid-canary'
    source_names = SOURCE_NAMES + ((PREFIX + 'persistent_guard_state.py',) if canary else ())
    expected_kind = LIFETIME_KIND if canary else KIND
    result = dict(schema=1, kind=expected_kind, stage=args.stage, passed=False, accepted=False, Windows_support=False,
                  Native_admitted=False, Native_executed=False, actual_policy_operations=False,
                  actual_profile_operations=False, socket_tests_performed=False, installer_executed=False,
                  source_base_head=BASE_HEAD, expected_source_sha=args.expected_source_sha,
                  protocol_sha256=args.protocol_sha256, compiler_process=None, NULL_ABI=None, errors=[],
                  scope='Fixed owned SDK DLL build plus NULL-argument refusal ABI only. No valid guard, policy, profile, sockets or Native support.')
    process, log, state = None, setup / 'compile-guard.log', None
    if canary:
        result['scope'] = ('Fixed DLL/NULL ABI then finite real SID policy and existing IPv4 TCP normal/cancel control. '
                           'No IPv6/UDP/inbound/crash/reuse/lowbox-mutation, installer, Native or Windows product qualification.')
    try:
        checkout(args.expected_source_sha)
        require(re.fullmatch('[0-9a-f]{64}', args.protocol_sha256 or '') is not None, 'external protocol SHA required')
        protocol = args.protocol.resolve(strict=True)
        require(protocol.is_relative_to(ROOT) and not args.protocol.is_symlink() and
                protocol.stat().st_size <= 64 * 1024 and digest(protocol) == args.protocol_sha256,
                'exact bounded checked-out protocol required')
        plan = read_json(protocol)
        require(plan['schema'] == 1 and type(plan['schema']) is int and plan['kind'] == expected_kind and
                plan['source_base_head'] == BASE_HEAD, 'exact frozen protocol kind/base required')
        pins = plan['source_files_sha256']
        require(type(pins) is dict and set(pins) == set(source_names), 'exact stage-specific frozen source paths required')
        def fresh():
            checkout(args.expected_source_sha)
            require(digest(protocol) == args.protocol_sha256, 'frozen protocol changed')
            for name, pin in pins.items():
                path = ROOT / name
                require(type(pin) is str and re.fullmatch('[0-9a-f]{64}', pin) is not None and
                        path.resolve(strict=True) == path and not path.is_symlink() and
                        path.stat().st_size <= 256 * 1024 and digest(path) == pin, 'frozen source changed: ' + name)
            require(time.monotonic() - START < 150, 'whole build-readiness wall budget exhausted')
            return dict(source_head=args.expected_source_sha, protocol_sha256=args.protocol_sha256,
                        source_files_sha256=dict(pins))
        fresh()
        # Verify source hashes before importing the existing Windows-only helper
        # modules; -B and the exact source census preserve the checkout.
        from appcontainer_canary import compiler
        from windows_process import run_owned_setup, preserved, safe
        require(Path(sys.modules['appcontainer_canary'].__file__).resolve() == ROOT / PREFIX / 'appcontainer_canary.py' and
                Path(sys.modules['windows_process'].__file__).resolve() == ROOT / PREFIX / 'windows_process.py', 'wrong shared helper import')
        with ExitStack() as held:
            for path in [protocol, *(ROOT / name for name in source_names)]:
                held.enter_context(preserved(path, path.parent))
            fresh()
            exe, includes, libraries, compiler_tools = compiler()
            dll = setup / 'persistent-sid-guard.dll'
            argv = [str(exe), '/nologo', '/W4', '/WX', '/O1', '/MT', '/LD', '/DUNICODE', '/D_UNICODE',
                    *['/I' + str(path) for path in includes], str(ROOT / PREFIX / 'persistent_sid_guard.c'),
                    '/Fo' + str(setup / 'persistent-sid-guard.obj'), '/Fe' + str(dll), '/link', '/INCREMENTAL:NO',
                    '/IMPLIB:' + str(setup / 'persistent-sid-guard.lib'), '/PDB:' + str(setup / 'persistent-sid-guard.pdb'),
                    *['/LIBPATH:' + str(path) for path in libraries], 'kernel32.lib', 'advapi32.lib', 'fwpuclnt.lib', 'ole32.lib']
            require(len(argv) == 27, 'fixed compiler recipe differs')
            result['compiler_tools'] = compiler_tools
            process = run_owned_setup(argv, cwd=setup, log=log, root=setup, seconds=30)
            result['compiler_process'] = process
            with (setup / 'compile-guard-process.json').open('x', encoding='utf-8') as stream:
                json.dump(process, stream, indent=2); stream.write('\n')
            require(process['status'] == 'success' and process['cleanup_complete'] is True and
                    process['compiler_output']['validated'] is True and
                    process['compiler_output']['role'] == 'persistent-sid-guard', 'compiler/Job/PE DLL readiness failed')
            safe(dll, setup)
            with preserved(dll, setup) as identity:
                require(identity['sha256'] == process['compiler_output']['sha256'], 'compiled DLL identity changed')
                result['DLL'] = dict(path=str(dll), **identity)
                result['NULL_ABI'] = null_abi(dll)
                fresh()
                if canary:
                    from persistent_guard_state import PersistentGuardState
                    from appcontainer_canary import main as run_canary
                    guard_pins = {str(ROOT / name): pin for name, pin in pins.items()}
                    guard_pins[str(dll)] = identity['sha256']
                    state = PersistentGuardState(scope, dll, source_pins=guard_pins, witness=fresh)
                    canary_report = scope.with_name(scope.name + '-canary-report.json')
                    require(not canary_report.exists() and not canary_report.is_symlink(), 'fresh canary report required')
                    result['actual_policy_operations'] = None
                    result['actual_profile_operations'] = None
                    result['socket_tests_performed'] = None
                    code = run_canary(['--scope', str(scope), '--report', str(canary_report)],
                                      persistent_guard=state, prepared_setup=setup)
                    child = read_json(canary_report, 192 * 1024)
                    result['canary'] = child
                    require(code == 0 and child['passed'] is True and child['cleanup']['cleanup_complete'] is True,
                            'finite persistent SID control failed; all unavailable observations remain unqualified')
                    result['actual_policy_operations'] = True
                    result['actual_profile_operations'] = True
                    result['socket_tests_performed'] = True
            fresh()
        result['source_files_sha256'] = pins
        result['passed'] = True
    except Exception as exc:
        result['errors'].append(type(exc).__name__ + ': ' + str(exc))
    finally:
        if state is not None:
            try:
                if not result['passed']:
                    state.poison('; '.join(result['errors']) or 'outer source/delivery failure')
                state.abandon()
                result['persistent_guard'] = state.receipt()
                snapshot = state.material_snapshot()
                result['state_material'] = {key: value for key, value in snapshot.items() if key != 'files'}
                result['state_material']['files'] = []
                for row in snapshot['files']:
                    metadata = {key: value for key, value in row.items() if key != 'base64'}
                    encoded = row.get('base64', '')
                    metadata['chunks'] = (len(encoded) + 32767) // 32768
                    print(json.dumps(dict(kind='persistent-state-material-metadata', **metadata)), flush=True)
                    for index, offset in enumerate(range(0, len(encoded), 32768)):
                        print(json.dumps(dict(kind='persistent-state-material-base64-chunk', name=row['name'],
                                              index=index, data=encoded[offset:offset + 32768])), flush=True)
                    result['state_material']['files'].append(metadata)
                if not snapshot['complete']:
                    result['passed'] = False
                    result['errors'].append('actual owned state material incomplete or differs from last complete write')
            except Exception as exc:
                result['passed'] = False
                result['errors'].append('persistent final state: ' + type(exc).__name__ + ': ' + str(exc))
        try:
            if log.exists():
                with log.open('rb') as stream:
                    raw = stream.read(256 * 1024 + 1)
                result['compiler_log'] = dict(path=str(log), bytes=log.stat().st_size,
                    sha256=digest(log), printed_bytes=min(len(raw), 256 * 1024), truncated=len(raw) > 256 * 1024)
                if len(raw) > 256 * 1024:
                    result['passed'] = False
                # Lossless bounded chunks permit exact retrieval from Actions
                # logs without artifact/cache upload, including failed builds.
                for index, offset in enumerate(range(0, min(len(raw), 256 * 1024), 24 * 1024)):
                    print(json.dumps(dict(kind='compiler-log-base64-chunk', index=index,
                        data=base64.b64encode(raw[offset:offset + 24 * 1024]).decode('ascii'))), flush=True)
        except Exception as exc:
            result['passed'] = False; result['errors'].append('log retention: ' + type(exc).__name__ + ': ' + str(exc))
        result['compiler_process_receipt_available'] = process is not None
        if result['passed']:
            try:
                fresh()  # Final source/protocol witness after log material reads.
            except Exception as exc:
                result['passed'] = False; result['errors'].append('final source witness: ' + str(exc))
        result['wall_seconds_before_report'] = time.monotonic() - START
        result['controller_CPU_seconds_before_report'] = time.process_time() - CPU0
        result['compiler_full_job_CPU_seconds'] = process.get('full_job_cpu_seconds') if process is not None else None
        result['whole_external_exit_CPU_seconds'] = None
        result['accounting'] = 'Compiler receipt includes owned exited descendants; controller CPU and complete external exit are separate. Failed API/cleanup may lack a process receipt, not evidence of zero cost. No parent+child cost double counting or speed claim.'
        payload = (json.dumps(result, indent=2, allow_nan=False) + '\n').encode('utf-8')
        require(len(payload) <= 256 * 1024, 'bounded readiness report required')
        with report.open('xb') as stream:
            stream.write(payload)
        print(json.dumps(result, allow_nan=False), flush=True)
    return 0 if result['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
