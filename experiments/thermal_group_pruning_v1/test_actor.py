"""Authored receipt/filesystem regressions only; NEVER Native routing proof."""
import copy
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, floor_route as f, sexpr as sx
from experiments.thermal_group_pruning_v1 import actor as d


class FinalReceiptClaims(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name).resolve()
        self.out=self.root/'attempt';self.out.mkdir();self.source=self.root/'source/owned.kicad_pcb';self.source.parent.mkdir()
        self.tree=sx.parse('(kicad_pcb (version 20260206))');sx.write(self.source,self.tree)
        self.candidate=self.out/'validation/candidate'/self.source.name;self.candidate.parent.mkdir(parents=True)
        sx.write(self.candidate,self.tree);(self.out/'validation/pre-refill.kicad_pcb').write_bytes(self.candidate.read_bytes())
        self.protocol=self.root/'protocol.json';p.save_json(self.protocol,{'authored':True})
        self.native=dict(opens=0,blocking=0,warnings=0,exclusions=0,ignored_checks=[],findings=[])
        self.baseline=copy.deepcopy(self.native);self.old_metrics=dict(track_length_mm=10,vias=0)
        self.metrics=dict(track_length_mm=5,vias=0);self.proposal={'authored':'one deletion','net_name':'AUTHORED_RETURN'}
        self.tools={'authored':'no Native process'};self.prior=dict(wall_seconds=102,full_cpu_seconds=84)
        self.entry=dict(candidate=str(self.candidate),candidate_sha256=p.sha(self.candidate),native=self.native,report_sha256='2'*64)
        self.spec=dict(source=str(self.source),source_hashes=p.tree_hash(self.source.parent),warm_source=str(self.source))
        self.data=dict(schema=1,kind='thermal-group-pruning-single-final-v1',accepted=False,production_admitted=False,
            human_pcb_approval_observed=False,physical_electrical_validation=False,budget_seconds=120,cpu_budget_seconds=120,
            reserved_publication_and_independent_readback_seconds=d.RESERVE,protocol_sha256=p.sha(self.protocol),
            prior_costs=self.prior,tools=self.tools,status='completed',method_qualified=True,within_reserved_budget=True,
            new_wall_seconds=1,new_full_cpu_seconds=1,candidate=str(self.candidate),candidate_sha256=p.sha(self.candidate),
            native_report_sha256=self.entry['report_sha256'],original_native=self.baseline,retained_metrics=self.old_metrics,
            native=self.native,metrics=self.metrics,proposal=self.proposal,steps=[])
        # These two stubs model an already checked authored proof. They do not
        # impersonate Native processes or establish any board acceptance.
        stack=ExitStack();self.addCleanup(stack.close)
        for target,value in ((patch.object(d,'PROTOCOL',self.protocol),None),
                             (patch.object(d,'prior_charge',return_value=self.prior),None),
                             (patch.object(d.p,'tool_manifest',return_value=self.tools),None),
                             (patch.object(d,'retained',return_value=(self.tree,self.proposal,[],self.baseline,self.old_metrics)),None),
                             (patch.object(d,'phase',return_value=(self.entry,self.metrics)),None),
                             (patch.object(d.rs,'audit',return_value={'scope_passed':True,'protected_count':22}),None)):
            stack.enter_context(target)

    def test_exact_authored_claims_replay_without_native_execution(self):
        before=copy.deepcopy(self.data)
        self.assertTrue(d.check(self.out,self.data,self.spec,final=True));self.assertEqual(self.data,before)

    def test_candidate_report_baseline_and_retained_metric_claims_cannot_drift(self):
        self.assertTrue(d.check(self.out,self.data,self.spec,final=True))
        mutations={'candidate':str(self.root/'old-candidate.kicad_pcb'),'native_report_sha256':'0'*64,
            'original_native':{**self.baseline,'blocking':1},'retained_metrics':dict(track_length_mm=999,vias=0),
            'candidate_sha256':'0'*64,'metrics':dict(track_length_mm=999,vias=0)}
        for key,value in mutations.items():
            data=copy.deepcopy(self.data);data[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(p.Rejected,'claims differ|proof differs'):
                d.check(self.out,data,self.spec,final=True)

    def test_final_identity_qualification_and_resource_types_are_mandatory(self):
        for key,value in (('schema',True),('budget_seconds',120.0),('accepted',0),
                          ('physical_electrical_validation',0),('status','failed'),('method_qualified',1),
                          ('within_reserved_budget',1),('new_wall_seconds',True),('new_wall_seconds',14)):
            data=copy.deepcopy(self.data);data[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(p.Rejected):
                d.check(self.out,data,self.spec,final=True)


class FinalMaterialCallbacks(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name).resolve()
        out=root/'attempt';out.mkdir();native=out/'validation/final-drc.json';native.parent.mkdir();p.save_json(native,{'authored':True})
        source=root/'original/owned.kicad_pcb';source.parent.mkdir();source.write_text('authored unchanged source\n')
        rule=source.with_suffix('.kicad_pro');rule.write_text('authored unchanged rules\n')
        prior=root/'prior';prior.mkdir();(prior/'proof.json').write_text('authored retained proof\n')
        code=root/'helper.py';code.write_text('# authored frozen helper\n')
        protocol=root/'protocol.json';p.save_json(protocol,{'authored':True})
        data={'completed_material':f.evidence_inventory(out)};p.save_json(out/'result.json',data)
        spec=dict(prefixes={'prior':d.inventory(prior)},code_sha256={'helper.py':p.sha(code)},
            source=str(source),source_hashes=p.tree_hash(source.parent))
        return SimpleNamespace(root=root,out=out,native=native,rule=rule,protocol=protocol,data=data,spec=spec,
            receipt_pin=p.sha(out/'result.json'),protocol_pin=p.sha(protocol),tools={'authored':'no Native process'})

    def call(self,x,callback):
        with patch.object(d,'ROOT',x.root),patch.object(d,'PROTOCOL',x.protocol),patch.object(d.p,'tool_manifest',side_effect=callback) as tools:
            try:return d.final_material(x.out,x.data,x.spec,x.tools,x.receipt_pin,x.protocol_pin)
            finally:tools.assert_called_once()

    def test_unchanged_real_files_survive_final_callback(self):
        x=self.fixture();self.call(x,lambda:x.tools)

    def test_final_tool_callback_mutating_native_report_is_rejected(self):
        x=self.fixture();called=[]
        def callback():called.append(True);x.native.write_text('changed actual report bytes\n');return x.tools
        with self.assertRaisesRegex(p.Rejected,'final new material changed'):self.call(x,callback)
        self.assertEqual(called,[True])

    def test_final_tool_callback_mutating_original_rules_is_rejected(self):
        x=self.fixture();called=[]
        def callback():called.append(True);x.rule.write_text('changed original rules bytes\n');return x.tools
        with self.assertRaisesRegex(p.Rejected,'final original project changed'):self.call(x,callback)
        self.assertEqual(called,[True])

    def test_final_tool_callback_mutating_protocol_is_rejected(self):
        x=self.fixture();called=[]
        def callback():called.append(True);x.protocol.write_text('{"authored":"changed protocol"}\n');return x.tools
        with self.assertRaisesRegex(p.Rejected,'final source/tools changed'):self.call(x,callback)
        self.assertEqual(called,[True])


if __name__=='__main__':unittest.main()
