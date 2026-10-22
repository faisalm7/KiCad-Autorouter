"""Constructed first-cause controls; no WFP, token or Windows qualification."""
import ast
import ctypes
import os
from pathlib import Path
import threading
from types import MethodType, SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'scripts/windows_native_slice'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def winerror(code):
    error = OSError('constructed Windows error ' + str(code))
    error.winerror = code
    return error


class FirstCauseControls(unittest.TestCase):
    def setUp(self):
        build = ast.parse((ROOT / 'persistent_guard_build.py').read_text())
        classes = [node for node in build.body if isinstance(node, ast.ClassDef)
                   and node.name in ('GUID', 'Info', 'Diagnostic')]
        scope = {'C': ctypes}
        exec(compile(ast.Module(body=classes, type_ignores=[]), str(ROOT), 'exec'), scope)
        self.Diagnostic, self.Info = scope['Diagnostic'], scope['Info']
        source = ast.parse((ROOT / 'persistent_guard_state.py').read_text())
        cls = next(node for node in source.body if isinstance(node, ast.ClassDef)
                   and node.name == 'PersistentGuardState')
        methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)
                   and node.name in ('_remember_failure', '_invoke', 'arm')]
        self.scope = dict(C=SimpleNamespace(byref=ctypes.byref, sizeof=ctypes.sizeof,
                                           WinError=winerror), Diagnostic=self.Diagnostic,
                          threading=threading, os=os, _require=require)
        exec(compile(ast.Module(body=methods, type_ignores=[]), str(ROOT), 'exec'), self.scope)

    def owner(self, *, getter='recorded', arm_error=13):
        calls = []

        def diagnostic(owner, pointer, size):
            calls.append('diagnostic')
            if getter == 'error':
                return 6
            row = ctypes.cast(pointer, ctypes.POINTER(self.Diagnostic)).contents
            row.abi, row.bytes = 1, 136
            if getter == 'malformed':
                row.bytes = 135
            if getter == 'nonascii':
                row.stage = b'\xff'
            elif getter == 'recorded':
                row.recorded, row.error = 1, 13
                row.stage, row.predicate = b'filter_fields', b'flags'
                row.object_index, row.expected_high, row.actual_low = 3, 1, 7
            return 0

        owner = SimpleNamespace(_first_failure=None, _thread=threading.get_ident(),
            _pid=os.getpid(), _abandoned=False, _owner=SimpleNamespace(value=1),
            _phase='bound', _sid=None, _keys=None,
            _fresh=lambda:calls.append('fresh'), _thread_check=lambda:calls.append('thread'),
            _bad=False, _info=lambda:dict(poisoned=0, state=2, policy_may_exist=1),
            _append=lambda *args:calls.append('journal'),
            _lib=SimpleNamespace(PG_Arm=lambda owner:calls.append('arm') or arm_error,
                                 PG_GetDiagnostic=diagnostic))
        for name in ('_remember_failure', '_invoke', 'arm'):
            setattr(owner, name, MethodType(self.scope[name], owner))

        def poison(error):
            calls.append('poison')
            owner._remember_failure('poison', 'external_or_uninstrumented', error)
            owner._bad, owner._phase = True, 'orphan'

        owner.poison = poison
        return owner, calls

    def test_layout_is_additive_and_original_INFO_unchanged(self):
        self.assertEqual(ctypes.sizeof(self.Info), 196)
        self.assertEqual(ctypes.sizeof(self.Diagnostic), 136)
        self.assertEqual([getattr(self.Diagnostic, key).offset for key in
                          ('stage', 'predicate', 'expected_low')], [24, 72, 120])

    def test_first_C_error_precedes_and_survives_repeated_poison(self):
        owner, calls = self.owner()
        with self.assertRaises(OSError) as caught:
            owner.arm()
        owner.poison(RuntimeError('later cleanup error'))
        row = owner._first_failure
        self.assertEqual((row['operation'], row['stage'], row['phase'], row['winerror']),
                         ('PG_Arm', 'C_call', 'bound', 13))
        self.assertEqual(row['C_diagnostic']['stage'], 'filter_fields')
        self.assertEqual((row['C_diagnostic']['expected'], row['C_diagnostic']['actual']),
                         (1 << 32, 7))
        self.assertEqual(calls.count('diagnostic'), 1)
        self.assertLess(calls.index('diagnostic'), calls.index('poison'))
        self.assertEqual(caught.exception.winerror, 13)

    def test_C_success_preserves_each_first_Python_failure_stage(self):
        for fault, stage, operation in (('info', 'get_info', 'PG_Arm'),
                ('identity', 'owner_identity_predicate', 'PG_Arm'),
                ('after_fresh', 'after_fresh', 'PG_Arm'),
                ('armed', 'armed_policy_predicate', 'arm'),
                ('journal', 'journal_ARMED', 'arm'),
                ('journal_fresh', 'after_journal_fresh', 'arm')):
            with self.subTest(fault=fault):
                owner, calls = self.owner(getter='empty', arm_error=0)
                def failed(*args):
                    raise RuntimeError('constructed ' + fault)
                if fault == 'info': owner._info = failed
                if fault == 'identity': owner._info = lambda:dict(poisoned=1)
                if fault == 'armed': owner._info = lambda:dict(poisoned=0,state=1,policy_may_exist=1)
                if fault == 'journal': owner._append = failed
                if fault in ('after_fresh', 'journal_fresh'):
                    visits = []
                    def fresh():
                        visits.append(1)
                        if len(visits) == (2 if fault == 'after_fresh' else 3): failed()
                    owner._fresh = fresh
                with self.assertRaises(RuntimeError): owner.arm()
                row = owner._first_failure
                self.assertEqual((row['operation'], row['stage']), (operation, stage))
                self.assertFalse(row['C_diagnostic']['recorded'])
                self.assertIsNone(row['C_diagnostic_error'])
                self.assertIn('poison', calls)

    def test_missing_error_malformed_or_nonascii_getter_preserves_original_error(self):
        for getter in ('missing', 'error', 'malformed', 'nonascii'):
            with self.subTest(getter=getter):
                owner, calls = self.owner(getter=getter)
                if getter == 'missing': del owner._lib.PG_GetDiagnostic
                with self.assertRaises(OSError) as caught: owner.arm()
                row = owner._first_failure
                self.assertEqual(caught.exception.winerror, 13)
                self.assertEqual(row['winerror'], 13)
                self.assertIsNone(row['C_diagnostic'])
                self.assertIsInstance(row['C_diagnostic_error'], str)
                self.assertIn('poison', calls)

    def test_no_diagnostic_C_call_without_current_creator_thread_owner(self):
        for fault in ('thread', 'pid', 'abandoned', 'owner'):
            with self.subTest(fault=fault):
                owner, calls = self.owner()
                if fault == 'thread': owner._thread = -1
                if fault == 'pid': owner._pid = -1
                if fault == 'abandoned': owner._abandoned = True
                if fault == 'owner': owner._owner.value = 0
                owner._remember_failure('external', 'test', RuntimeError('first'))
                self.assertNotIn('diagnostic', calls)
                self.assertIn('unavailable', owner._first_failure['C_diagnostic_error'])

    def test_created_process_enters_C_custody_before_failing_witness_and_getter(self):
        owner, calls = self.owner(getter='empty', arm_error=0)
        owner._lib.PG_RegisterProcess = lambda *args:calls.append('registered') or 0
        def fresh():
            calls.append('witness')
            raise RuntimeError('source changed')
        owner._fresh = fresh
        with self.assertRaisesRegex(RuntimeError, 'source changed'):
            owner._invoke('PG_RegisterProcess', object(), created_registration=True)
        self.assertEqual(calls[:4], ['thread', 'registered', 'witness', 'diagnostic'])
        self.assertEqual(owner._first_failure['stage'], 'after_fresh')


if __name__ == '__main__':
    unittest.main()
