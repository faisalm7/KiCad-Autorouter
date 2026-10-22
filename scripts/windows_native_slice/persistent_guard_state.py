"""Unqualified, CI-only live owner for the fixed persistent-SID C guard.

The host journal is an append-only tombstone, never cleanup authority. No owner
is reconstructed, adopted, or removed from a file or PID. Only this process's
creator thread and the C owner's retained handles can authorize removal. A
crash/unknown leaves the exact SID, profile name, keys and state permanently
reserved on this ephemeral runner; this module has no recovery/GC operation.
No Windows API is called merely by importing this module.
"""
import ctypes as C
import ctypes.wintypes as W
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import uuid
from contextlib import ExitStack

if __package__:
    from .persistent_guard_build import Diagnostic, Info, bind_library, hosted
else:
    from persistent_guard_build import Diagnostic, Info, bind_library, hosted


def _require(value, message):
    if not value:
        raise RuntimeError(message)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


class PersistentGuardState:
    """One fresh host-only reservation and one non-recoverable C owner.

    ``witness`` is the caller's held source/DLL witness, not an AppContainer
    callback (which would recurse into check_armed). source_pins maps canonical
    absolute source/DLL paths to frozen raw SHA256 values. The caller retains
    its independent protocol/checkout authority; JSON passed here cannot load
    an owner, remove a policy, or authorize profile/ACL cleanup.
    """
    MAX_RECORDS = 16
    MAX_ENTRIES = 145  # 16 permanently reserved slots * 9 files + one lock.
    MAX_STATE_BYTES = 2 * 1024 * 1024
    ROOT_NAME = 'kicad-autorouter-persistent-guard011-state'

    def __init__(self, scope, dll_path, *, source_pins, witness):
        hosted()
        if __package__:
            from . import windows_process as wp
            from .appcontainer_launch import SECURITY_ATTRIBUTES, ACL
        else:
            import windows_process as wp
            from appcontainer_launch import SECURITY_ATTRIBUTES, ACL
        self._wp, self._sa_type, self._acl_type = wp, SECURITY_ATTRIBUTES, ACL
        self._thread, self._pid = threading.get_ident(), os.getpid()
        self._owner = C.c_void_p()
        self._bad = self._journal_bad = self._abandoned = self._removed = False
        self._errors, self._files, self._handles, self._sd = [], {}, [], []
        self._owned_names = set()
        self._held = ExitStack()
        self._records = 0
        self._journal_raw = b''
        self._last = None
        self._first_failure = None
        self._contract = self._sid = self._keys = None
        self._phase = 'new'
        self._cleanup = False
        self._witness = witness
        _require(callable(witness), 'independent live source/DLL witness required')
        self._apis()
        try:
            runner = Path(os.environ['RUNNER_TEMP']).absolute()
            self.scope = wp.safe(scope, runner)
            self._root = wp.safe(runner / self.ROOT_NAME, runner)
            self._dll = wp.safe(dll_path, runner)
            _require(self.scope.parent == runner and
                     re.fullmatch(r'kicad-appcontainer007-[0-9a-f]{32}', self.scope.name) and
                     not self.scope.exists() and self._dll.is_file() and self._dll.suffix == '.dll',
                     'fresh direct canary scope and owned DLL required')
            _require(not self._root.is_relative_to(self.scope) and
                     not self.scope.is_relative_to(self._root), 'host state must be outside lowbox grants')
            _require(type(source_pins) is dict and 6 <= len(source_pins) <= 16,
                     'bounded exact source/DLL pin map required')
            checkout = Path(os.environ['GITHUB_WORKSPACE']).resolve(strict=True)
            self._pins = {}
            for name, pin in source_pins.items():
                path = Path(name).absolute()
                _require(str(path) == str(name) and len(str(path)) <= 240 and
                         (path.is_relative_to(checkout) or path.is_relative_to(runner)) and
                         type(pin) is str and re.fullmatch('[0-9a-f]{64}', pin),
                         'canonical absolute source pin required')
                wp.safe(path, checkout if path.is_relative_to(checkout) else runner)
                _require(path.is_file() and path.stat().st_size <= 4 * 1024 * 1024,
                         'bounded regular pinned source required')
                self._pins[str(path)] = pin
            required = {Path(__file__).absolute(), self._dll, *(Path(__file__).parent / name for name in
                        ('persistent_guard_build.py', 'persistent_sid_guard.c',
                         'windows_process.py', 'appcontainer_launch.py'))}
            _require(required.issubset({Path(name) for name in self._pins}) and
                     len(_json(self._pins)) <= 8192, 'guard/helper/DLL source pins incomplete')
            self._witness_value = self._observe_witness()
            for name in self._pins:
                self._held.enter_context(wp.preserved(Path(name), Path(name).parent))
            self._check_pins()
            self._owner_sid = self._token_owner()
            self._expected_sids = {self._sid_bytes_from_text(text) for text in ('S-1-5-18', 'S-1-5-32-544')}
            self._dir_sd = self._descriptor('D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)')
            self._file_sd = self._descriptor('D:P(A;;FA;;;SY)(A;;FA;;;BA)')
            sa = self._attributes(self._dir_sd)
            if not self.k.CreateDirectoryW(str(self._root), C.byref(sa)):
                _require(C.get_last_error() == 183, 'exclusive host state directory creation failed')
            self._root_handle = self._open(self._root, directory=True)
            self._root_id = self._identity(self._root_handle, self._root, directory=True)
            self._lock = self._open(self._root / '.lock', create=4, share=0)
            _require(self._identity(self._lock, self._root / '.lock')['bytes'] == 0,
                     'host reservation lock must be empty')
            self._census()
            self.profile_name = 'KiCadAutorouter.Canary.' + uuid.uuid4().hex
            self._name = self.profile_name.rsplit('.', 1)[1]
            reserved = False
            for index in range(16):
                try:
                    self._new_file('slot-%02d' % index, _json({'profile_name': self.profile_name}) + b'\n')
                    reserved = True
                    break
                except FileExistsError:
                    continue
            _require(reserved, '16 permanent host guard reservations exhausted; no automatic cleanup')
            self._journal = self._new_file('name-' + self._name + '.jsonl', b'')
            self._append('RESERVED', {'profile_name': self.profile_name, 'scope': str(self.scope),
                                     'source_pins_sha256': hashlib.sha256(_json(self._pins)).hexdigest()})
            self._lib, _, _ = bind_library(self._dll)
            self._fresh()
        except BaseException:
            self._bad = True
            self._close_local()
            raise

    def _apis(self):
        self.k = self._wp.K
        self.a = C.WinDLL('advapi32', use_last_error=True)
        specs = [
            (self.k, 'CreateDirectoryW', [W.LPCWSTR, C.c_void_p], W.BOOL),
            (self.k, 'GetFinalPathNameByHandleW', [W.HANDLE, W.LPWSTR, W.DWORD, W.DWORD], W.DWORD),
            (self.k, 'GetHandleInformation', [W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
            (self.k, 'GetCurrentProcess', [], W.HANDLE),
            (self.k, 'FlushFileBuffers', [W.HANDLE], W.BOOL),
            (self.k, 'WriteFile', [W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p], W.BOOL),
            (self.k, 'LocalFree', [C.c_void_p], C.c_void_p),
            (self.a, 'OpenProcessToken', [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)], W.BOOL),
            (self.a, 'GetTokenInformation', [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)], W.BOOL),
            (self.a, 'ConvertStringSecurityDescriptorToSecurityDescriptorW', [W.LPCWSTR, W.DWORD, C.POINTER(C.c_void_p), C.c_void_p], W.BOOL),
            (self.a, 'ConvertStringSidToSidW', [W.LPCWSTR, C.POINTER(C.c_void_p)], W.BOOL),
            (self.a, 'ConvertSidToStringSidW', [C.c_void_p, C.POINTER(C.c_void_p)], W.BOOL),
            (self.a, 'GetSecurityInfo', [W.HANDLE, C.c_int, W.DWORD, C.POINTER(C.c_void_p), C.c_void_p, C.POINTER(C.c_void_p), C.c_void_p, C.POINTER(C.c_void_p)], W.DWORD),
            (self.a, 'GetSecurityDescriptorControl', [C.c_void_p, C.POINTER(W.WORD), C.POINTER(W.DWORD)], W.BOOL),
            (self.a, 'IsValidSecurityDescriptor', [C.c_void_p], W.BOOL),
            (self.a, 'IsValidAcl', [C.c_void_p], W.BOOL),
            (self.a, 'GetAce', [C.c_void_p, W.DWORD, C.POINTER(C.c_void_p)], W.BOOL),
            (self.a, 'IsValidSid', [C.c_void_p], W.BOOL),
            (self.a, 'GetLengthSid', [C.c_void_p], W.DWORD)]
        for library, name, args, result in specs:
            fn = getattr(library, name)
            fn.argtypes, fn.restype = args, result

    @staticmethod
    def _yes(value):
        if not value:
            raise C.WinError(C.get_last_error())

    def _thread_check(self):
        if threading.get_ident() != self._thread or os.getpid() != self._pid:
            self._bad = True
            self._cleanup = False
            raise RuntimeError('creator process/thread only; removal authority poisoned')

    def _copy_sid(self, pointer):
        self._yes(pointer and self.a.IsValidSid(pointer))
        size = int(self.a.GetLengthSid(pointer))
        _require(8 <= size <= 68, 'bounded actual SID required')
        return C.string_at(pointer, size)

    def _sid_bytes_from_text(self, text):
        pointer = C.c_void_p()
        self._yes(self.a.ConvertStringSidToSidW(text, C.byref(pointer)))
        try:
            return self._copy_sid(pointer)
        finally:
            _require(not self.k.LocalFree(pointer), 'SID buffer release failed')

    def _token_owner(self):
        token, needed = W.HANDLE(), W.DWORD()
        self._yes(self.a.OpenProcessToken(self.k.GetCurrentProcess(), 8, C.byref(token)))
        try:
            ok = self.a.GetTokenInformation(token, 4, None, 0, C.byref(needed))
            _require(not ok and C.get_last_error() == 122 and 0 < needed.value <= 65536,
                     'bounded actual default token owner query required')
            buffer = C.create_string_buffer(needed.value)
            self._yes(self.a.GetTokenInformation(token, 4, buffer, len(buffer), C.byref(needed)))
            return self._copy_sid(C.cast(buffer, C.POINTER(C.c_void_p)).contents.value)
        finally:
            self._yes(self.k.CloseHandle(token))

    def _descriptor(self, sddl):
        pointer = C.c_void_p()
        self._yes(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, C.byref(pointer), None))
        self._sd.append(pointer)
        return pointer

    def _attributes(self, descriptor):
        return self._sa_type(C.sizeof(self._sa_type), descriptor, False)

    def _security(self, handle, directory):
        owner, acl, sd = C.c_void_p(), C.c_void_p(), C.c_void_p()
        error = int(self.a.GetSecurityInfo(handle, 1, 1 | 4, C.byref(owner), None,
                                         C.byref(acl), None, C.byref(sd)))
        if error:
            raise C.WinError(error)
        try:
            control, revision = W.WORD(), W.DWORD()
            self._yes(sd and self.a.IsValidSecurityDescriptor(sd) and acl and self.a.IsValidAcl(acl))
            self._yes(self.a.GetSecurityDescriptorControl(sd, C.byref(control), C.byref(revision)))
            header = C.cast(acl, C.POINTER(self._acl_type)).contents
            _require(control.value & 0x1000 and header.AceCount == 2 and 8 <= header.AclSize <= 4096 and
                     self._copy_sid(owner) == self._owner_sid, 'exact protected host owner/DACL required')
            seen = set()
            for index in range(2):
                ace = C.c_void_p()
                self._yes(self.a.GetAce(acl, index, C.byref(ace)))
                head = C.string_at(ace, 8)
                size = int.from_bytes(head[2:4], 'little')
                _require(head[0] == 0 and head[1] == (3 if directory else 0) and
                         int.from_bytes(head[4:8], 'little') == 0x1f01ff and 16 <= size <= 76,
                         'exact host-only allow ACE required')
                raw = C.string_at(ace, size)
                _require(8 + 8 + 4 * raw[9] == size, 'bounded SID ACE layout required')
                sid = self._copy_sid(ace.value + 8)
                _require(sid in self._expected_sids and sid not in seen and len(sid) == size - 8,
                         'only SYSTEM/Administrators host trustees allowed')
                seen.add(sid)
            _require(seen == self._expected_sids, 'host DACL trustees incomplete')
        finally:
            _require(not self.k.LocalFree(sd), 'security buffer release failed')

    def _open(self, path, *, directory=False, create=3, share=1):
        self._wp.safe(path, self._root.parent)
        sa = self._attributes(self._dir_sd if directory else self._file_sd)
        access = 0x80000000 | 0x20000 | (0 if directory else 0x40000000)
        flags = 0x00200000 | (0x02000000 if directory else 0x80000000)
        handle = self.k.CreateFileW(str(path), access, 3 if directory else share,
                                    C.byref(sa), create, flags, None)
        if handle == C.c_void_p(-1).value:
            error = C.get_last_error()
            if create == 1 and error in (80, 183):
                raise FileExistsError(str(path))
            raise C.WinError(error)
        self._handles.append(handle)
        return handle

    def _identity(self, handle, path, *, directory=False):
        info, flags = self._wp.FILEINFO(), W.DWORD()
        self._yes(self.k.GetFileInformationByHandle(handle, C.byref(info)))
        self._yes(self.k.GetHandleInformation(handle, C.byref(flags)))
        _require(not flags.value & 1 and not info.dwFileAttributes & 0x400 and
                 bool(info.dwFileAttributes & 0x10) == directory and
                 (directory or info.nNumberOfLinks == 1), 'noninheritable unaliased host object required')
        final = C.create_unicode_buffer(32768)
        count = self.k.GetFinalPathNameByHandleW(handle, final, len(final), 0)
        _require(0 < count < len(final) and final.value.startswith('\\\\?\\') and
                 final.value[4:].casefold() == str(path).casefold(), 'canonical retained host path differs')
        self._security(handle, directory)
        return {'file_id': [int(info.dwVolumeSerialNumber), int(info.nFileIndexHigh), int(info.nFileIndexLow)],
                'bytes': int(info.nFileSizeHigh) * 2**32 + int(info.nFileSizeLow)}

    def _census(self):
        total = count = 0
        with os.scandir(self._root) as entries:
            for entry in entries:
                count += 1
                _require(count <= self.MAX_ENTRIES and not entry.is_dir(follow_symlinks=False) and
                         re.fullmatch(r'(\.lock|slot-(?:0[0-9]|1[0-5])|name-[0-9a-f]{32}\.jsonl|'
                                      r'sid-[0-9a-f]{64}\.tombstone|key-[0-9a-f]{32}\.tombstone|'
                                      r'context-[0-9a-f]{32}\.json)', entry.name),
                         'bounded known host reservation files only')
                path = self._wp.safe(Path(entry.path), self._root)
                stat = path.stat()
                _require(stat.st_nlink == 1 and stat.st_size <= 65536, 'bounded regular host reservation required')
                total += stat.st_size
                _require(total <= self.MAX_STATE_BYTES, 'host state byte bound exhausted')

    def _write(self, handle, raw):
        written = W.DWORD()
        buffer = C.create_string_buffer(raw)
        self._yes(self.k.WriteFile(handle, buffer, len(raw), C.byref(written), None))
        _require(written.value == len(raw), 'short durable host state write')
        self._yes(self.k.FlushFileBuffers(handle))

    def _new_file(self, name, raw):
        _require(len(raw) <= 65536 and '/' not in name and '\\' not in name, 'bounded state file required')
        self._census()
        path = self._root / name
        handle = self._open(path, create=1)
        self._owned_names.add(name)  # CREATE_NEW succeeded; never adopt collisions.
        self._write(handle, raw)
        identity = self._identity(handle, path)
        _require(identity['bytes'] == len(raw), 'fresh host state file size differs')
        self._files[name] = {'handle': handle, 'identity': identity, 'raw': raw}
        self._census()
        return handle

    def _append(self, event, data):
        _require(not self._journal_bad and self._records < self.MAX_RECORDS, 'journal is incomplete or full')
        row = {'schema': 1, 'seq': self._records, 'event': event,
               'previous_sha256': hashlib.sha256(self._journal_raw).hexdigest(), 'data': data}
        raw = _json(row) + b'\n'
        _require(len(raw) <= 2048 and len(self._journal_raw) + len(raw) <= 32768, 'journal record bound exceeded')
        try:
            self._write(self._journal, raw)
            self._journal_raw += raw
            self._records += 1
            entry = self._files['name-' + self._name + '.jsonl']
            entry['raw'] = self._journal_raw
            entry['identity']['bytes'] = len(self._journal_raw)
            _require(self._identity(self._journal, self._root / ('name-' + self._name + '.jsonl')) == entry['identity'],
                     'durable journal identity/size differs')
        except BaseException:
            self._journal_bad = self._bad = True
            self._cleanup = False
            raise

    def _observe_witness(self):
        result = self._witness()
        _require(len(_json(result)) <= 16384, 'bounded live witness result required')
        return hashlib.sha256(_json(result)).hexdigest()

    def _check_pins(self):
        for name, pin in self._pins.items():
            _require(self._wp.digest(name) == pin, 'frozen guard/source/DLL bytes changed: ' + name)

    def _fresh(self):
        self._thread_check()
        _require(not self._bad and not self._abandoned, 'live unpoisoned owner required')
        self._check_pins()
        _require(self._observe_witness() == self._witness_value, 'live source/DLL witness changed')
        _require(self._identity(self._root_handle, self._root, directory=True)['file_id'] == self._root_id['file_id'],
                 'retained host directory changed')
        for name, entry in self._files.items():
            path = self._root / name
            _require(self._identity(entry['handle'], path) == entry['identity'] and
                     path.read_bytes() == entry['raw'], 'host reservation bytes/identity/DACL changed')
        self._census()

    def _info(self):
        info = Info()
        error = int(self._lib.PG_GetInfo(self._owner, C.byref(info), C.sizeof(info)))
        if error:
            raise C.WinError(error)
        _require(info.abi == 1 and info.bytes == 196 and info.jobs <= 2 and info.processes <= 4,
                 'fixed live C owner information differs')
        row = {name: int(getattr(info, name)) for name in
               ('state', 'poisoned', 'jobs', 'processes', 'policy_may_exist', 'last_error',
                'abort_error', 'pending_create', 'pending_job')}
        row['sid_hex'] = bytes(info.sid[:info.sid_bytes]).hex()
        row['keys'] = [uuid.UUID(bytes_le=bytes(item)).hex for item in (info.sublayer, *info.filters)]
        self._last = row
        return row

    def _remember_failure(self, operation, stage, error, metadata=None):
        """Evidence only; never raises, invokes witnesses or grants cleanup."""
        if self._first_failure is not None:
            return
        # Evidence capture must not replace the original exception even if an
        # external witness supplied an exception with broken text/properties.
        try:
            message = str(error)[:1024]
        except BaseException:
            message = '<exception text unavailable>'
        try:
            winerror = getattr(error, 'winerror', None)
        except BaseException:
            winerror = None
        if type(winerror) is not int or not 0 <= winerror <= 0xffffffff:
            winerror = None
        row = {'operation': operation, 'stage': stage, 'phase': self._phase,
               'exception_type': type(error).__name__, 'message': message, 'winerror': winerror,
               'metadata': metadata, 'C_diagnostic': None, 'C_diagnostic_error': None}
        # In particular this runs only AFTER attempted immediate process capture.
        # No getter/witness is inserted before PG_RegisterProcess takes custody.
        try:
            _require(threading.get_ident() == self._thread and os.getpid() == self._pid and
                     not self._abandoned and bool(self._owner.value),
                     'diagnostic unavailable without live creator-thread owner')
            diagnostic = Diagnostic()
            code = int(self._lib.PG_GetDiagnostic(self._owner, C.byref(diagnostic), C.sizeof(diagnostic)))
            if code:
                raise C.WinError(code)
            _require(diagnostic.abi == 1 and diagnostic.bytes == 136 and diagnostic.recorded in (0, 1),
                     'fixed C diagnostic layout differs')
            row['C_diagnostic'] = {
                'recorded': bool(diagnostic.recorded), 'error': int(diagnostic.error),
                'stage': bytes(diagnostic.stage).decode('ascii'),
                'predicate': bytes(diagnostic.predicate).decode('ascii'),
                'object_index': int(diagnostic.object_index), 'element_index': int(diagnostic.element_index),
                'expected': int(diagnostic.expected_low) | (int(diagnostic.expected_high) << 32),
                'actual': int(diagnostic.actual_low) | (int(diagnostic.actual_high) << 32)}
        except BaseException as diagnostic_error:
            try:
                detail = str(diagnostic_error)[:384]
            except BaseException:
                detail = '<diagnostic exception text unavailable>'
            row['C_diagnostic_error'] = type(diagnostic_error).__name__ + ': ' + detail
        self._first_failure = row

    def _invoke(self, name, *args, created_registration=False):
        stage = 'before_fresh'
        metadata = None
        try:
            if created_registration:
                # The actual newly created handle must enter C custody before
                # any fallible file/source/WFP witness callback. Pending-create
                # is already latched; all those checks still run after capture.
                self._thread_check()
                _require(name == 'PG_RegisterProcess' and not self._bad and not self._abandoned,
                         'only immediate live created-process capture may precede witnesses')
            else:
                self._fresh()
            stage = 'owner_present'
            _require(bool(self._owner.value), 'prepared live C owner required')
            stage = 'C_call'
            error = int(getattr(self._lib, name)(self._owner, *args))
            if error:
                raise C.WinError(error)
            stage = 'get_info'
            row = self._info()
            stage = 'owner_identity_predicate'
            metadata = {'expected': {'poisoned': 0, 'sid_exact': True, 'keys_exact': True},
                        'actual': {'poisoned': row['poisoned'],
                                   'sid_exact': self._sid is None or row['sid_hex'] == self._sid.hex(),
                                   'keys_exact': self._keys is None or row['keys'] == self._keys}}
            _require(not row['poisoned'] and (self._sid is None or row['sid_hex'] == self._sid.hex()) and
                     (self._keys is None or row['keys'] == self._keys), 'live owner identity/state differs')
            stage = 'after_fresh'
            metadata = None
            self._fresh()
            return row
        except BaseException as error:
            self._remember_failure(name, stage, error, metadata)
            self.poison(error)
            raise

    def prepare(self, actual_sid_bytes):
        try:
            self._fresh()
            _require(self._phase == 'new' and type(actual_sid_bytes) is bytes and len(actual_sid_bytes) == 40,
                     'one exact actual fresh profile SID required')
            sid = (C.c_ubyte * len(actual_sid_bytes)).from_buffer_copy(actual_sid_bytes)
            error = int(self._lib.PG_Create(sid, len(sid), C.byref(self._owner)))
            if error:
                raise C.WinError(error)
            row = self._info()
            _require(row['state'] == 1 and not row['poisoned'] and row['sid_hex'] == actual_sid_bytes.hex() and
                     len(set(row['keys'])) == 5, 'new actual SID/key owner differs')
            self._sid, self._keys = actual_sid_bytes, row['keys']
            self._new_file('sid-' + hashlib.sha256(self._sid).hexdigest() + '.tombstone',
                           _json({'profile_name': self.profile_name, 'sid_hex': self._sid.hex()}) + b'\n')
            for key in self._keys:
                self._new_file('key-' + key + '.tombstone', _json({'profile_name': self.profile_name, 'key': key}) + b'\n')
            pointer = C.c_void_p()
            self._yes(self.a.ConvertSidToStringSidW(sid, C.byref(pointer)))
            try:
                self._sid_text = C.wstring_at(pointer)
            finally:
                _require(not self.k.LocalFree(pointer), 'SID text buffer release failed')
            self._append('PREPARED', {'sid_hex': self._sid.hex(), 'keys': self._keys})
            self._phase = 'prepared'
            self._fresh()
        except BaseException as error:
            self.poison(error)
            raise

    def bind_context(self, contract):
        try:
            self._fresh()
            _require(self._phase == 'prepared' and type(contract) is dict and set(contract) == {'base', 'scope_ids'},
                     'one exact sealed AppContainer context required')
            base, ids = contract['base'], contract['scope_ids']
            _require(type(base) is dict and set(base) == {'kind', 'profile_name', 'profile_sid',
                     'capability_count_requested', 'tool_pins', 'helper_pins'} and
                     base['kind'] == 'experimental-appcontainer-contract-v1' and
                     base['profile_name'] == self.profile_name and base['profile_sid'] == self._sid_text and
                     type(base['capability_count_requested']) is int and base['capability_count_requested'] == 0 and
                     type(base['tool_pins']) is dict and base['tool_pins'] and
                     type(base['helper_pins']) is dict and base['helper_pins'] and
                     type(ids) is dict and set(ids) == {str(self.scope), str(self.scope / 'tools'), str(self.scope / 'scratch')},
                     'actual profile/scope/sealed tool contract differs')
            raw = _json({'schema': 1, 'profile_name': self.profile_name, 'scope': str(self.scope),
                         'sid_hex': self._sid.hex(), 'keys': self._keys, 'source_pins': self._pins,
                         'live_witness_sha256': self._witness_value, 'contract': contract}) + b'\n'
            self._new_file('context-' + self._name + '.json', raw)
            self._contract = hashlib.sha256(raw).hexdigest()
            self._append('CONTEXT', {'file': 'context-' + self._name + '.json', 'sha256': self._contract})
            self._phase = 'bound'
            self._fresh()
        except BaseException as error:
            self.poison(error)
            raise

    def arm(self):
        stage = 'bound_phase_predicate'
        metadata = {'expected': 'bound', 'actual': self._phase}
        try:
            _require(self._phase == 'bound', 'durable actual SID/keys/context required before Arm')
            stage = 'invoke'
            metadata = None
            row = self._invoke('PG_Arm')
            stage = 'armed_policy_predicate'
            metadata = {'expected': {'state': 2, 'policy_may_exist': 1},
                        'actual': {'state': row['state'], 'policy_may_exist': row['policy_may_exist']}}
            _require(row['state'] == 2 and row['policy_may_exist'] == 1, 'armed policy readback differs')
            stage = 'journal_ARMED'
            metadata = None
            self._append('ARMED', {'state': 2, 'policy_may_exist': 1})
            self._phase = 'armed'
            stage = 'after_journal_fresh'
            self._fresh()
        except BaseException as error:
            self._remember_failure('arm', stage, error, metadata)
            self.poison(error)
            raise

    def check_armed(self):
        return self._invoke('PG_CheckArmed')

    def register_job(self, actual_hJob):
        slot = C.c_uint32(0xffffffff)
        self._invoke('PG_RegisterJob', actual_hJob, C.byref(slot))
        return int(slot.value)

    def begin_create(self, job_slot):
        self._slot(job_slot, 2)
        self._invoke('PG_BeginCreate', job_slot)

    def register_process(self, job_slot, actual_hProcess):
        self._slot(job_slot, 2)
        slot = C.c_uint32(0xffffffff)
        self._invoke('PG_RegisterProcess', job_slot, actual_hProcess, C.byref(slot), created_registration=True)
        return int(slot.value)

    def before_resume(self, process_slot):
        self._slot(process_slot, 4)
        self._invoke('PG_BeforeResume', process_slot)

    def _slot(self, value, bound):
        if type(value) is not int or not 0 <= value < bound:
            self.poison('invalid actual owner slot')
            raise ValueError('exact live owner slot required')

    def poison(self, reason):
        """Irreversible; also handles an exception outside any C call."""
        self._remember_failure('poison', 'external_or_uninstrumented', reason)
        self._bad = True
        self._cleanup = False
        message = (type(reason).__name__ + ': ' + str(reason) if isinstance(reason, BaseException) else str(reason))[:1024]
        if len(self._errors) < 8:
            self._errors.append(message)
        if threading.get_ident() != self._thread or os.getpid() != self._pid:
            raise RuntimeError('wrong-thread fault poisoned Python authority; C disposal requires creator thread')
        if self._abandoned:
            self._phase = 'orphan'
            return  # No closed-handle write, C call, or deletion retry.
        errors = []
        if self._owner.value:
            code = int(self._lib.PG_Poison(self._owner, 13))
            if code:
                errors.append('PG_Poison error ' + str(code))
            else:
                self._info()
        if self._phase != 'orphan' and hasattr(self, '_journal') and not self._journal_bad and self._records < self.MAX_RECORDS:
            try:
                self._append('ORPHAN', {'reason': message, 'policy_cleanup_authorized': False})
            except BaseException as error:
                errors.append('journal poison: ' + str(error)[:256])
        self._phase = 'orphan'
        if errors:
            self._errors.extend(errors[:max(0, 8 - len(self._errors))])
            raise RuntimeError('; '.join(errors))

    def seal_and_remove(self):
        try:
            _require(self._phase == 'armed', 'one live armed lifecycle required')
            row = self._invoke('PG_SealLaunches')
            _require(row['state'] == 3 and not row['pending_create'], 'sealed C owner differs')
            self._append('SEALED', {'jobs': row['jobs'], 'processes': row['processes']})
            self._phase = 'sealed'
            row = self._invoke('PG_RemoveWhenEmpty')
            _require(row['state'] == 4 and row['policy_may_exist'] == 0, 'verified policy absence required')
            self._append('REMOVED', {'retained_handle_zero_and_exact_absence_verified': True})
            self._fresh()
            self._phase, self._removed, self._cleanup = 'removed', True, True
        except BaseException as error:
            self.poison(error)
            raise

    @property
    def cleanup_authorized(self):
        self._thread_check()
        return self._cleanup and self._removed and not self._bad and not self._abandoned

    def _close_local(self):
        errors = []
        for handle in reversed(self._handles):
            if not self.k.CloseHandle(handle):
                errors.append('host handle CloseHandle error ' + str(C.get_last_error()))
        self._handles.clear()
        for pointer in self._sd:
            if self.k.LocalFree(pointer):
                errors.append('host security LocalFree error')
        self._sd.clear()
        try:
            self._held.close()
        except BaseException as error:
            errors.append('held source/DLL disposal: ' + str(error)[:256])
        if errors:
            self._bad = True
            self._cleanup = False
            self._errors.extend(errors[:max(0, 8 - len(self._errors))])
            raise RuntimeError('; '.join(errors))

    def abandon(self):
        self._thread_check()
        if self._abandoned:
            return  # Local disposal only; never retry deletion or infer authority.
        errors = []
        try:
            if not self._removed and not self._bad:
                try:
                    self.poison('owner abandoned without verified live removal')
                except BaseException as error:
                    errors.append('abandon poison: ' + str(error)[:256])
            if self._owner.value:
                try:
                    self._info()
                except BaseException as error:
                    errors.append('final live owner observation: ' + str(error)[:256])
                code = int(self._lib.PG_AbandonAndFree(C.byref(self._owner)))
                if code:
                    errors.append('PG_AbandonAndFree error ' + str(code))
            if not self._journal_bad and self._records < self.MAX_RECORDS:
                self._append('ABANDONED', {'verified_removal_observed': self._removed,
                                         'state_and_tombstones_retained': True})
        except BaseException as error:
            errors.append(type(error).__name__ + ': ' + str(error)[:512])
        finally:
            self._abandoned = True
            self._cleanup = False
            try:
                self._close_local()
            except BaseException as error:
                errors.append(str(error)[:512])
        if errors:
            self._bad = True
            self._errors.extend(errors[:max(0, 8 - len(self._errors))])
            raise RuntimeError('; '.join(errors))

    def receipt(self):
        """Evidence only, including after abandon; never grants live authority."""
        self._thread_check()
        result = {'schema': 1, 'kind': 'experimental-persistent-SID-live-owner-v1',
                  'accepted': False, 'Native_admitted': False, 'Windows_support': False,
                  'profile_name': self.profile_name, 'scope': str(self.scope), 'state_root': str(self._root),
                  'phase': self._phase, 'poisoned': self._bad, 'abandoned': self._abandoned,
                  'verified_removal_observed': self._removed, 'receipt_authorizes_cleanup': False,
                  'journal': {'path': str(self._root / ('name-' + self._name + '.jsonl')),
                              'records': self._records, 'bytes': len(self._journal_raw),
                              'sha256': hashlib.sha256(self._journal_raw).hexdigest(), 'incomplete': self._journal_bad},
                  'context_sha256': self._contract, 'source_pins': self._pins,
                  'last_live_C_info': self._last, 'first_failure': self._first_failure, 'errors': self._errors,
                  'bounds': {'records': 16, 'per_record_bytes': 2048, 'journal_bytes': 32768,
                             'context_bytes': 65536, 'state_entries': 145, 'state_bytes': self.MAX_STATE_BYTES},
                  'limitations': 'Unqualified Windows prototype. Flush/ACL/native denial/crash controls remain required. '
                                 'No power-loss guarantee, hostile administrator protection, recovery or state cleanup.'}
        _require(len(_json(result)) <= 32768, 'bounded owner receipt required')
        return json.loads(_json(result))

    def material_snapshot(self):
        """Bounded actual owned bytes for CI retention; never cleanup authority.

        Read only names this live instance exclusively created. Incomplete
        writes remain exportable and explicitly differ from the last complete
        tracked record. No previous owner's state or archive is enumerated.
        """
        self._thread_check()
        _require(len(self._owned_names) <= 9, 'bounded own state names required')
        rows, total, complete = [], 0, True
        for name in sorted(self._owned_names):
            row = {'name': name, 'path': str(self._root / name), 'read': False}
            try:
                path = self._wp.safe(self._root / name, self._root)
                _require(path.is_file() and path.stat().st_nlink == 1, 'regular unaliased owned state required')
                with path.open('rb') as stream:
                    raw = stream.read(65537)
                total += len(raw)
                _require(len(raw) <= 65536 and total <= 128 * 1024 and path.stat().st_size == len(raw),
                         'bounded actual owned state material required')
                entry = self._files.get(name)
                exact = entry is not None and raw == entry['raw']
                row.update(read=True, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                           matches_last_complete_write=exact, base64=base64.b64encode(raw).decode('ascii'))
                complete = complete and exact
            except Exception as error:
                complete = False
                row['error'] = type(error).__name__ + ': ' + str(error)[:256]
            rows.append(row)
        return {'complete': complete, 'files': rows, 'bytes': total,
                'scope': 'Actual exclusively created state bytes only; partial material is diagnostic, never removal authority.'}
