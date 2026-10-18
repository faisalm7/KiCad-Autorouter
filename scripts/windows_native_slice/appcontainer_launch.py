"""CI-only, non-admitting AppContainer launch resources; not a second runner.

No Windows API is called on import.  Entering the guard is permitted only on
an ephemeral GitHub Windows runner.  The caller builds its owned canary in
``tool_root`` before the first run, which seals that tree.  This adapter does
not establish Native support, all-network denial, or a hostile-code sandbox.

Primary contracts: Microsoft Create/DeleteAppContainerProfile,
GetAppContainerFolderPath, UpdateProcThreadAttribute, GetTokenInformation,
GetNamedSecurityInfoW/SetNamedSecurityInfoW and SetEntriesInAclW.  In
particular attribute values outlive their attribute list, profile creation
must return S_OK, and successful deletion alone is not proof of removal.
"""
import ctypes as C
import ctypes.wintypes as W
import hashlib
import math
import os
import uuid
from contextlib import contextmanager
from pathlib import Path


class SECURITY_CAPABILITIES(C.Structure):
    _fields_ = [('AppContainerSid', C.c_void_p), ('Capabilities', C.c_void_p),
                ('CapabilityCount', W.DWORD), ('Reserved', W.DWORD)]


class SECURITY_ATTRIBUTES(C.Structure):
    _fields_ = [('nLength', W.DWORD), ('lpSecurityDescriptor', C.c_void_p),
                ('bInheritHandle', W.BOOL)]


class TRUSTEE(C.Structure):
    _fields_ = [('pMultipleTrustee', C.c_void_p), ('MultipleTrusteeOperation', C.c_int),
                ('TrusteeForm', C.c_int), ('TrusteeType', C.c_int), ('ptstrName', C.c_void_p)]


class EXPLICIT_ACCESS(C.Structure):
    _fields_ = [('grfAccessPermissions', W.DWORD), ('grfAccessMode', C.c_int),
                ('grfInheritance', W.DWORD), ('Trustee', TRUSTEE)]


class ACL(C.Structure):
    _fields_ = [('AclRevision', C.c_ubyte), ('Sbz1', C.c_ubyte),
                ('AclSize', W.WORD), ('AceCount', W.WORD), ('Sbz2', W.WORD)]


class FILEINFO(C.Structure):
    _fields_ = [('dwFileAttributes', W.DWORD), ('ftCreationTime', W.FILETIME),
                ('ftLastAccessTime', W.FILETIME), ('ftLastWriteTime', W.FILETIME),
                ('dwVolumeSerialNumber', W.DWORD), ('nFileSizeHigh', W.DWORD),
                ('nFileSizeLow', W.DWORD), ('nNumberOfLinks', W.DWORD),
                ('nFileIndexHigh', W.DWORD), ('nFileIndexLow', W.DWORD)]


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _yes(value):
    if not value:
        raise C.WinError(C.get_last_error())


def _error(code):
    if code:
        raise C.WinError(code)


class AppContainerLaunch:
    """Own one fresh profile and exclusive scope, shared by bounded canary runs.

    ``new_scope`` must be a nonexistent direct child of RUNNER_TEMP.  After
    enter, copy only final owned probe images into ``tool_root``. The first runner
    call freezes tools; scratch must still be empty.  Retained scope files
    are not deleted.  ``cleanup_receipt`` is final only after context exit.
    """
    def __init__(self, new_scope):
        self.scope = Path(new_scope).absolute()
        self.tool_root = self.scope / 'tools'
        self.scratch = self.scope / 'scratch'
        self.profile_name = 'KiCadAutorouter.Canary.' + uuid.uuid4().hex
        self.profile_sid = None
        self.evidence = {'kind': 'experimental-appcontainer-token-v1',
                         'accepted': False, 'product_support': False,
                         'network_tests_performed_by_adapter': False,
                         'all_network_denial_claimed': False,
                         'profile_name': self.profile_name, 'tokens': []}
        self.cleanup_receipt = {'cleanup_complete': False, 'errors': []}
        self._sid = C.c_void_p()
        self._entered = self._created = self._sealed = False
        self._outstanding = 0
        self._handles = []
        self._original_acls = {}
        self._granted_acls = {}
        self._tool_pins = None
        self._profile_folder = None

    def _apis(self):
        self.k = C.WinDLL('kernel32', use_last_error=True)
        self.a = C.WinDLL('advapi32', use_last_error=True)
        self.u = C.WinDLL('userenv', use_last_error=True)
        self.ole = C.WinDLL('ole32', use_last_error=True)
        specs = [
            (self.u, 'CreateAppContainerProfile', [W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, C.c_void_p, W.DWORD, C.POINTER(C.c_void_p)], C.c_long),
            (self.u, 'DeleteAppContainerProfile', [W.LPCWSTR], C.c_long),
            (self.u, 'GetAppContainerFolderPath', [W.LPCWSTR, C.POINTER(C.c_void_p)], C.c_long),
            (self.a, 'FreeSid', [C.c_void_p], C.c_void_p),
            (self.a, 'IsValidSid', [C.c_void_p], W.BOOL),
            (self.a, 'GetLengthSid', [C.c_void_p], W.DWORD),
            (self.a, 'EqualSid', [C.c_void_p, C.c_void_p], W.BOOL),
            (self.a, 'ConvertSidToStringSidW', [C.c_void_p, C.POINTER(C.c_void_p)], W.BOOL),
            (self.a, 'OpenProcessToken', [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)], W.BOOL),
            (self.a, 'GetTokenInformation', [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)], W.BOOL),
            (self.a, 'GetNamedSecurityInfoW', [W.LPCWSTR, C.c_int, W.DWORD, C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p), C.c_void_p, C.POINTER(C.c_void_p)], W.DWORD),
            (self.a, 'GetSecurityDescriptorControl', [C.c_void_p, C.POINTER(W.WORD), C.POINTER(W.DWORD)], W.BOOL),
            (self.a, 'IsValidAcl', [C.c_void_p], W.BOOL),
            (self.a, 'SetEntriesInAclW', [W.ULONG, C.POINTER(EXPLICIT_ACCESS), C.c_void_p, C.POINTER(C.c_void_p)], W.DWORD),
            (self.a, 'SetNamedSecurityInfoW', [W.LPWSTR, C.c_int, W.DWORD, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p], W.DWORD),
            (self.k, 'CreateFileW', [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE], W.HANDLE),
            (self.k, 'GetFileInformationByHandle', [W.HANDLE, C.POINTER(FILEINFO)], W.BOOL),
            (self.k, 'GetFinalPathNameByHandleW', [W.HANDLE, W.LPWSTR, W.DWORD, W.DWORD], W.DWORD),
            (self.k, 'CloseHandle', [W.HANDLE], W.BOOL),
            (self.k, 'LocalFree', [C.c_void_p], C.c_void_p),
            (self.k, 'InitializeProcThreadAttributeList', [C.c_void_p, W.DWORD, W.DWORD, C.POINTER(C.c_size_t)], W.BOOL),
            (self.k, 'UpdateProcThreadAttribute', [C.c_void_p, W.DWORD, C.c_size_t, C.c_void_p, C.c_size_t, C.c_void_p, C.c_void_p], W.BOOL),
            (self.k, 'DeleteProcThreadAttributeList', [C.c_void_p], None),
            (self.ole, 'CoTaskMemFree', [C.c_void_p], None)]
        for library, name, args, result in specs:
            fn = getattr(library, name)
            fn.argtypes, fn.restype = args, result

    @staticmethod
    def _path(path, root):
        path, root = Path(path).absolute(), Path(root).absolute()
        if (not path.drive or path.drive.startswith('\\\\') or '..' in path.parts
                or any(':' in part for part in path.parts[1:]) or not path.is_relative_to(root)):
            raise ValueError('owned local DOS path required')
        for part in [path, *path.parents]:
            if part.exists() and part.lstat().st_file_attributes & 0x400:
                raise ValueError('reparse point refused')
        if path.resolve() != path:
            raise ValueError('canonical owned path required')
        return path

    def _identity(self, path, *, retain=False):
        path = self._path(path, self.scope)
        # Directory handles deny deletion; sealed tool handles also deny writes.
        directory = path.is_dir()
        handle = self.k.CreateFileW(str(path), 0x80000000, 1 if retain and not directory else 3,
                                   None, 3, 0x02200000, None)
        if handle == C.c_void_p(-1).value:
            raise C.WinError(C.get_last_error())
        try:
            info = FILEINFO()
            _yes(self.k.GetFileInformationByHandle(handle, C.byref(info)))
            if info.dwFileAttributes & 0x400 or (not directory and info.nNumberOfLinks != 1):
                raise ValueError('aliased owned entry refused')
            final = C.create_unicode_buffer(32768)
            count = self.k.GetFinalPathNameByHandleW(handle, final, len(final), 0)
            if not count or count >= len(final):
                raise RuntimeError('canonical handle path unavailable')
            actual = final.value
            if actual.startswith('\\\\?\\'):
                actual = actual[4:]
            if actual.casefold() != str(path).casefold():
                raise ValueError('DOS alias refused')
            row = [info.dwVolumeSerialNumber, info.nFileIndexHigh, info.nFileIndexLow]
            if retain:
                self._handles.append(handle)
                handle = None
            return row
        finally:
            if handle is not None:
                _yes(self.k.CloseHandle(handle))

    def _tree(self, root):
        entries, total = [root], 0
        # Check a directory before traversing it; never follow a reparse point.
        pending = [root]
        while pending:
            directory = pending.pop()
            for entry in directory.iterdir():
                self._path(entry, self.scope)
                self._identity(entry)
                entries.append(entry)
                if len(entries) > 4000:
                    raise RuntimeError('owned tree entry bound')
                if entry.is_dir():
                    pending.append(entry)
                else:
                    total += entry.stat().st_size
                    if total > 128 * 1024**2:
                        raise RuntimeError('owned tree byte bound')
        return sorted(entries, key=lambda p: (len(p.parts), str(p)))

    def _acl(self, path):
        acl, sd = C.c_void_p(), C.c_void_p()
        _error(self.a.GetNamedSecurityInfoW(str(path), 1, 4, None, None,
                                           C.byref(acl), None, C.byref(sd)))
        try:
            if not acl.value:
                raise RuntimeError('null/absent original DACL refused')
            _yes(self.a.IsValidAcl(acl))
            size = C.cast(acl, C.POINTER(ACL)).contents.AclSize
            if not C.sizeof(ACL) <= size <= 65535:
                raise RuntimeError('invalid DACL size')
            control, revision = W.WORD(), W.DWORD()
            _yes(self.a.GetSecurityDescriptorControl(sd, C.byref(control), C.byref(revision)))
            return C.string_at(acl, size), bool(control.value & 0x1000)
        finally:
            if sd.value and self.k.LocalFree(sd):
                raise RuntimeError('security descriptor LocalFree failed')

    def _set_acl(self, path, raw, protected):
        self._identity(path)
        buffer = C.create_string_buffer(raw)
        flags = 4 | (0x80000000 if protected else 0x20000000)
        _error(self.a.SetNamedSecurityInfoW(str(path), 1, flags, None, None, buffer, None))

    def _grant(self, path, permissions, inheritance=0):
        raw, protected = self._acl(path)
        old, new = C.create_string_buffer(raw), C.c_void_p()
        entry = EXPLICIT_ACCESS(permissions, 1, inheritance, TRUSTEE(None, 0, 0, 0, self._sid))
        _error(self.a.SetEntriesInAclW(1, C.byref(entry), old, C.byref(new)))
        try:
            size = C.cast(new, C.POINTER(ACL)).contents.AclSize
            self._set_acl(path, C.string_at(new, size), protected)
        finally:
            if new.value and self.k.LocalFree(new):
                raise RuntimeError('ACL LocalFree failed')

    def __enter__(self):
        if self._entered or os.name != 'nt' or os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_OS') != 'Windows':
            raise RuntimeError('fresh GitHub Windows CI guard required; never run on Mac')
        runner = Path(os.environ['RUNNER_TEMP']).absolute()
        self._path(runner, runner)
        if self.scope.parent != runner or self.scope.exists():
            raise ValueError('nonexistent direct child of RUNNER_TEMP required')
        self._apis()
        self.scope.mkdir()
        self.tool_root.mkdir()
        self.scratch.mkdir()
        self._entered = True
        try:
            self._scope_ids = {str(p): self._identity(p, retain=True)
                               for p in (self.scope, self.tool_root, self.scratch)}
            hr = self.u.CreateAppContainerProfile(self.profile_name, self.profile_name,
                                                  'Owned bounded CI canary only', None, 0,
                                                  C.byref(self._sid))
            if hr != 0:
                raise RuntimeError('CreateAppContainerProfile must return S_OK: 0x%08x' % (hr & 0xffffffff))
            self._created = True
            _yes(self.a.IsValidSid(self._sid))
            sid_length = self.a.GetLengthSid(self._sid)
            if not 8 <= sid_length <= 68:
                raise RuntimeError('invalid profile SID size')
            self._sid_bytes = C.string_at(self._sid, sid_length)
            string = C.c_void_p()
            _yes(self.a.ConvertSidToStringSidW(self._sid, C.byref(string)))
            try:
                self.profile_sid = C.wstring_at(string)
            finally:
                if self.k.LocalFree(string):
                    raise RuntimeError('SID string LocalFree failed')
            folder = C.c_void_p()
            hr = self.u.GetAppContainerFolderPath(self.profile_sid, C.byref(folder))
            if hr != 0:
                raise RuntimeError('GetAppContainerFolderPath did not return S_OK')
            try:
                storage = Path(C.wstring_at(folder)).absolute()
            finally:
                self.ole.CoTaskMemFree(folder)
            packages = Path(os.environ['LOCALAPPDATA']).absolute() / 'Packages'
            self._path(storage, packages)
            relative = storage.relative_to(packages)
            if not relative.parts or relative.parts[0].casefold() != self.profile_name.casefold():
                raise RuntimeError('fresh owned profile storage identity unverified')
            self._profile_folder = packages / relative.parts[0]
            self.evidence.update(profile_sid=self.profile_sid, capability_count_requested=0,
                                 profile_create_hresult=0, scope=str(self.scope))
            return self
        except BaseException:
            self.__exit__(*__import__('sys').exc_info())
            raise

    def _seal(self):
        if any(self.scratch.iterdir()):
            raise RuntimeError('first canary scratch must be empty')
        paths = [self.scope, self.scratch, *self._tree(self.tool_root)]
        # Snapshot every original DACL before any inheritable grant can propagate.
        self._original_acls = {str(p): self._acl(p) for p in paths}
        for path in paths:
            self._grant(path, 0x1301bf if path == self.scratch else 0x1200a9,
                        3 if path == self.scratch else 0)
        self._granted_acls = {str(p): self._acl(p) for p in paths}
        self.evidence['acl_before'] = {p: {'sha256': hashlib.sha256(raw).hexdigest(),
                                           'protected': protected}
                                       for p, (raw, protected) in self._original_acls.items()}
        self.evidence['acl_granted'] = {p: {'sha256': hashlib.sha256(raw).hexdigest(),
                                            'protected': protected}
                                        for p, (raw, protected) in self._granted_acls.items()}
        self._tool_pins = {}
        for path in self._tree(self.tool_root):
            identity = self._identity(path, retain=True)
            self._tool_pins[str(path)] = {'identity': identity,
                                         'sha256': None if path.is_dir() else _hash(path)}
        self._helper_pins = {str(Path(__file__).resolve()): _hash(__file__),
                             str(Path(__file__).with_name('windows_process.py').resolve()):
                             _hash(Path(__file__).with_name('windows_process.py'))}
        self._sealed = True

    def check_contract(self):
        if not self._entered or not self._created or not self._sealed:
            raise RuntimeError('live sealed AppContainer guard required')
        if sorted(p.name for p in self.scope.iterdir()) != ['scratch', 'tools']:
            raise RuntimeError('unexpected owned scope entry')
        if any(self._identity(Path(path)) != identity for path, identity in self._scope_ids.items()):
            raise RuntimeError('owned scope identity changed')
        actual = {str(p): {'identity': self._identity(p),
                          'sha256': None if p.is_dir() else _hash(p)}
                  for p in self._tree(self.tool_root)}
        if actual != self._tool_pins or any(_hash(p) != pin for p, pin in self._helper_pins.items()):
            raise RuntimeError('sealed tool/helper tree changed')
        if any(self._acl(Path(p)) != raw for p, raw in self._granted_acls.items()):
            raise RuntimeError('scoped access contract changed')
        self._tree(self.scratch)
        return {'kind': 'experimental-appcontainer-contract-v1', 'profile_name': self.profile_name,
                'profile_sid': self.profile_sid, 'capability_count_requested': 0,
                'tool_pins': self._tool_pins, 'helper_pins': self._helper_pins}

    def before_launch(self, exe, cwd, log, root, seconds):
        if (type(seconds) not in (int, float) or not math.isfinite(seconds)
                or not 0 < seconds <= 60):
            raise ValueError('canary seconds must be finite and in (0,60]')
        if (not self._entered or self._outstanding or Path(root).absolute() != self.scope
                or Path(cwd).absolute() != self.scratch):
            raise ValueError('exact fresh guard scope/scratch required')
        exe = self._path(exe, self.tool_root)
        self._path(log, self.scratch)
        if not exe.is_file():
            raise ValueError('owned sealed executable required')
        if not self._sealed:
            self._seal()
        return self.check_contract()

    @contextmanager
    def launch_attributes(self, startup, log_handle):
        """Keep SID, capabilities, handle array and storage alive through Delete."""
        class STARTUPINFOEX(C.Structure):
            _fields_ = [('StartupInfo', type(startup)), ('lpAttributeList', C.c_void_p)]
        attributes, null_handle, initialized = None, None, False
        try:
            security = SECURITY_ATTRIBUTES(C.sizeof(SECURITY_ATTRIBUTES), None, True)
            null_handle = self.k.CreateFileW('NUL', 0x80000000, 3, C.byref(security), 3, 0, None)
            if null_handle == C.c_void_p(-1).value:
                null_handle = None
                raise C.WinError(C.get_last_error())
            capabilities = SECURITY_CAPABILITIES(self._sid, None, 0, 0)
            handles = (W.HANDLE * 2)(log_handle, null_handle)
            size = C.c_size_t()
            first = self.k.InitializeProcThreadAttributeList(None, 2, 0, C.byref(size))
            if first or C.get_last_error() != 122 or not 0 < size.value <= 65536:
                raise RuntimeError('attribute-list size query refused')
            attributes = C.create_string_buffer(size.value)
            _yes(self.k.InitializeProcThreadAttributeList(attributes, 2, 0, C.byref(size)))
            initialized = True
            _yes(self.k.UpdateProcThreadAttribute(attributes, 0, 0x00020009,
                                                   C.byref(capabilities), C.sizeof(capabilities), None, None))
            _yes(self.k.UpdateProcThreadAttribute(attributes, 0, 0x00020002,
                                                   C.byref(handles), C.sizeof(handles), None, None))
            extended = STARTUPINFOEX(startup, C.cast(attributes, C.c_void_p))
            extended.StartupInfo.cb = C.sizeof(extended)
            extended.StartupInfo.hStdInput = null_handle
            yield C.cast(C.byref(extended), C.POINTER(type(startup))), 0x00080000
        finally:
            if initialized:
                self.k.DeleteProcThreadAttributeList(attributes)
            if null_handle is not None:
                _yes(self.k.CloseHandle(null_handle))

    def process_created(self):
        self._outstanding += 1

    def job_reaped(self):
        if self._outstanding != 1:
            raise RuntimeError('AppContainer job lifecycle mismatch')
        self._outstanding = 0

    def verify_suspended_token(self, process, pid):
        token = W.HANDLE()
        _yes(self.a.OpenProcessToken(process, 8, C.byref(token)))
        try:
            def info(kind):
                needed = W.DWORD()
                initial = self.a.GetTokenInformation(token, kind, None, 0, C.byref(needed))
                if initial or C.get_last_error() != 122 or not 0 < needed.value <= 65536:
                    raise RuntimeError('token query size refused')
                buffer = C.create_string_buffer(needed.value)
                _yes(self.a.GetTokenInformation(token, kind, buffer, len(buffer), C.byref(needed)))
                return buffer
            app, caps, sid_info = info(29), info(30), info(31)
            if len(app) < C.sizeof(W.DWORD) or len(caps) < C.sizeof(W.DWORD) or len(sid_info) < C.sizeof(C.c_void_p):
                raise RuntimeError('short token observation')
            actual_sid = C.cast(sid_info, C.POINTER(C.c_void_p)).contents.value
            if (C.cast(app, C.POINTER(W.DWORD)).contents.value != 1
                    or C.cast(caps, C.POINTER(W.DWORD)).contents.value != 0
                    or not actual_sid or not self.a.IsValidSid(actual_sid)
                    or not self.a.EqualSid(actual_sid, self._sid)):
                raise RuntimeError('suspended process AppContainer identity/capabilities refused')
            row = {'pid': int(pid), 'is_appcontainer': True, 'profile_sid': self.profile_sid,
                   'capability_count': 0, 'checked_before_resume': True}
            self.evidence['tokens'].append(row)
            return row
        finally:
            _yes(self.k.CloseHandle(token))

    def __exit__(self, exc_type, exc, tb):
        errors = []
        def attempt(label, action):
            try:
                action()
            except BaseException as error:
                errors.append(label + ': ' + type(error).__name__ + ': ' + str(error))
        if self._outstanding:
            errors.append('owned job reaping unproved; ACL/profile cleanup refused')
        else:
            # Parent-first restoration avoids a later parent propagation silently
            # changing a child that was already checked.  New scratch entries
            # inherit the restored parent; no original files are discarded.
            for path, (raw, protected) in sorted(self._original_acls.items(), key=lambda item: len(Path(item[0]).parts)):
                attempt('restore DACL ' + path, lambda p=path, r=raw, q=protected: self._set_acl(Path(p), r, q))
            for path, original in self._original_acls.items():
                def check(p=path, expected=original):
                    if self._acl(Path(p)) != expected:
                        raise RuntimeError('original DACL bytes/protection not restored')
                attempt('verify DACL ' + path, check)
            if self._sealed:
                def check_new_entries():
                    # Removing the scratch parent's inheritable grant must also
                    # remove it from newly created descendants.  Protected or
                    # otherwise unexpected descendants refuse cleanup success.
                    for path in self._tree(self.scratch):
                        if self._sid_bytes in self._acl(path)[0]:
                            raise RuntimeError('fresh SID access remains on scratch entry: ' + str(path))
                attempt('verify generated scratch ACL cleanup', check_new_entries)
            for handle in reversed(self._handles):
                attempt('close owned identity handle', lambda h=handle: _yes(self.k.CloseHandle(h)))
            self._handles.clear()
            if self._created:
                def delete():
                    hr = self.u.DeleteAppContainerProfile(self.profile_name)
                    self.cleanup_receipt['profile_delete_hresult'] = hr
                    if hr != 0:
                        raise RuntimeError('DeleteAppContainerProfile did not return S_OK')
                    if self._profile_folder is None:
                        raise RuntimeError('profile folder identity not captured; absence unproved')
                    try:
                        self._profile_folder.lstat()
                    except FileNotFoundError:
                        self.cleanup_receipt['profile_storage_absent'] = True
                    else:
                        raise RuntimeError('owned profile storage remains after deletion')
                attempt('delete fresh profile and verify storage absence', delete)
        if self._sid.value:
            attempt('FreeSid', lambda: _yes(not self.a.FreeSid(self._sid)))
            self._sid = C.c_void_p()
        self._entered = False
        self.cleanup_receipt.update(cleanup_complete=not errors, errors=errors,
                                    all_owned_jobs_reaped=self._outstanding == 0,
                                    original_dacls_restored=not errors and bool(self._original_acls),
                                    scope_files_retained=str(self.scope),
                                    profile_registry_absence_not_queried=True)
        if errors:
            raise RuntimeError('AppContainer cleanup incomplete: ' + '; '.join(errors)) from exc
        return False
