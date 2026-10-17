"""Authored non-Native enclosure seams; never establish importer correctness.

All worker, tool, input-proof and lane operations are mocked. Signals and shared
publication are real. Test records are explicitly below AUTHORED-NON-NATIVE.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import contextlib
import json
import os
from pathlib import Path
import signal
import unittest
from unittest.mock import patch
from experiments.native_edge_named_v1 import driver as d


class PhaseControls(unittest.TestCase):
    def exercise(self, name, *, between_signal=None, late_signal=None, expired=False):
        base=d.BASE/'AUTHORED-NON-NATIVE-CONTROLS'/name
        base.mkdir(parents=True)
        source=base/'sources'/'literal300';source.mkdir(parents=True)
        (source/'owned.kicad_pcb').write_text('AUTHORED FAKE INPUT; NO NATIVE')
        calls=[]
        class NoNative:
            def __init__(self,out,*args,**kwargs):
                self.out=out;self.out.mkdir();self.steps=[]
            def native(self,*args):
                calls.append('authored mock worker')
                if between_signal:os.kill(os.getpid(),between_signal)
        original=d.p.save_json
        fired=False
        def save(path,value):
            nonlocal fired
            original(path,value)
            if late_signal and value.get('passed') is True and not fired:
                fired=True;os.kill(os.getpid(),late_signal)
        previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        with patch.object(d,'BASE',base),patch.object(d,'frozen',return_value={}),patch.object(d,'check_source_plan'), \
             patch.object(d.p,'tool_manifest',return_value={}),patch.object(d,'lane',return_value=contextlib.nullcontext()), \
             patch.object(d.fixture,'CASES',('literal300',)),patch.object(d.f,'FloorJob',NoNative), \
             patch.object(d,'export_proof',return_value={}),patch.object(d,'remaining',return_value=0 if expired else 30), \
             patch.object(d.p,'save_json',side_effect=save):
            result=d.prepare_native('0'*64)
        self.assertEqual({sig:signal.getsignal(sig) for sig in previous},previous)
        self.assertEqual(json.loads((base/'native-preparation/result.json').read_text()),result)
        self.assertFalse(result['accepted']);self.assertFalse(result['production_admitted'])
        self.assertEqual(calls,['authored mock worker'])
        return base,result

    def test_both_actual_signals_between_worker_and_publication_invalidate(self):
        for sig in (signal.SIGINT,signal.SIGTERM):
            with self.subTest(signal=sig):
                _,result=self.exercise('between-'+str(sig),between_signal=sig)
                self.assertEqual(result['status'],'cancelled');self.assertFalse(result['passed'])

    def test_actual_sigterm_after_positive_write_invalidates_canonical_record(self):
        base,result=self.exercise('late-term',late_signal=signal.SIGTERM)
        self.assertEqual(result['status'],'cancelled');self.assertFalse(result['passed'])
        self.assertTrue(list((base/'native-preparation').glob('invalidated-result-*.json')))

    def test_budget_exhaustion_has_explicit_status(self):
        _,result=self.exercise('expired',expired=True)
        self.assertEqual(result['status'],'budget_exceeded');self.assertFalse(result['passed'])


if __name__=='__main__':unittest.main()
