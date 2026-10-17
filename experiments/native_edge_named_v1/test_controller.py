"""Authored non-Native enclosure seams; never establish importer correctness.

All worker, tool, input-proof and lane operations are mocked. Signals and shared
publication are real. Test records are explicitly below AUTHORED-NON-NATIVE.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import contextlib
import copy
import json
import os
from pathlib import Path
import signal
import unittest
import uuid
from unittest.mock import patch
from experiments.native_edge_named_v1 import driver as d


class PhaseControls(unittest.TestCase):
    def exercise(self, name, *, between_signal=None, late_signal=None, expired=False):
        base=d.BASE/'AUTHORED-NON-NATIVE-CONTROLS'/(name+'-'+uuid.uuid4().hex)
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

    def test_original_rule_selection_requires_the_exact_two_rule_transport(self):
        original=['rule',['width','300'],['clearance','200'],['clearance','200',['type','smd_smd']]]
        added=['rule',*[['clearance','300',['type',pair]] for pair in
                       ('default_kicadedge','smd_kicadedge','kicadedge_kicadedge')]]
        structure=['structure',copy.deepcopy(original),copy.deepcopy(added)]
        self.assertIs(d.original_rule_for_eager_control(structure),structure[1])
        self.assertEqual(structure,['structure',original,added])
        for mutation in ('third','missing','reversed','edge_pair','original_override'):
            changed=copy.deepcopy(structure)
            if mutation=='third':changed.append(copy.deepcopy(added))
            elif mutation=='missing':changed.pop()
            elif mutation=='reversed':changed[1:]=list(reversed(changed[1:]))
            elif mutation=='edge_pair':changed[-1][-1][1]='250'
            else:changed[1].append(['clearance','1',['type','unknown']])
            with self.subTest(mutation=mutation),self.assertRaises(d.p.Rejected):
                d.original_rule_for_eager_control(changed)

    def test_reused_exports_refuse_changed_native_semantics_sources_or_tools(self):
        # Actual retained proof replay is pure; it starts no worker. Dictionary
        # mutations below cannot stand in for new Native observations.
        plan=d.frozen(d.PRIOR_PLAN,d.PRIOR_PLAN_PIN)
        plan['code_sha256']=d.code_pins()
        prepared,link=d.check_preparation_reuse(plan)
        self.assertTrue(prepared['passed']);self.assertFalse(link['native_exports_rerun'])
        for name in ('autorouter/native.py','autorouter/padless_alias.py','autorouter/netclass.py',
                     'autorouter/native_edge.py','experiments/native_edge_named_v1/NamedEdgeManagerProbe.java'):
            changed=copy.deepcopy(plan);changed['code_sha256'][name]='0'*64
            with self.subTest(code=name),self.assertRaises(d.p.Rejected):d.check_preparation_reuse(changed)
        for mutation in ('source','tools'):
            changed=copy.deepcopy(plan)
            if mutation=='source':changed['sources']['literal300'][next(iter(changed['sources']['literal300']))]='0'*64
            else:changed['tool_sha256'][next(iter(changed['tool_sha256']))]='0'*64
            with self.subTest(mutation=mutation),self.assertRaises(d.p.Rejected):d.check_preparation_reuse(changed)


if __name__=='__main__':unittest.main()
