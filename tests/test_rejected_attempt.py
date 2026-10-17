"""Synthetic filesystem controls, never Native DRC or routing qualification."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from autorouter import pipeline as p
from tests import test_result as result_fixture
from tests.normal_prl_fixture import mark_authored_receipt


class CompletedNegativeTests(unittest.TestCase):
    # Reuse the owned complete fixture without inheriting/repeating its tests.
    save_receipt = result_fixture.ResultFreshnessTests.save_receipt

    def setUp(self):
        result_fixture.ResultFreshnessTests.setUp(self)
        self.data.update(adapter='both', baseline='B2_tuned', engine_profile='tuned', scoring_variant='via_low')
        mark_authored_receipt(self.run, self.data, test_root=self.root)
        # The shared current-producer fixture also authors its exact no-op
        # corrected-adapter chain; do not overwrite it with a legacy context.
        self.native_outcome(negative=True)

    def native_outcome(self, *, negative):
        raw = copy.deepcopy(self.native_shape)
        raw['violations'] = [{'severity':'error','type':'clearance','items':[]}] if negative else []
        self.native.write_text(json.dumps(raw))
        self.data.update(native=p.parse_report(self.native,self.source.name),
            native_report_sha256=p.sha(self.native), whole_project_drc_clean=not negative)
        self.data['native_rejection_reasons'] = p.native_rejection_reasons(self.data['native'])
        self.data.update(accepted=not negative,status='drc_rejected' if negative else 'routing_accepted')
        process_path = self.run/'final-drc-process.json'
        process = json.loads(process_path.read_text())
        process.update(status='nonzero_exit' if negative else 'success',exit_code=5 if negative else 0)
        p.save_json(process_path,process)
        for step in self.data['steps']:
            if step['name']=='final-drc': step.update(process)
        self.save_receipt()

    def checked(self):
        return p.check_rejected_routing_attempt(self.receipt)

    def refused(self):
        with self.assertRaises((p.Rejected,OSError,ValueError)):
            self.checked()

    def test_zero_warning_blocking_negative_is_disjoint_immutable_diagnostic(self):
        before=p.tree_hash(self.root)
        result=self.checked()
        self.assertIs(result['current'],False)
        self.assertIs(result['validated_rejection'],True)
        self.assertIs(result['routing_accepted'],False)
        self.assertIs(result['applied'],False)
        self.assertEqual(result['candidate_sha256'],p.sha(self.candidate))
        self.assertEqual(result['native_report_sha256'],p.sha(self.native))
        self.assertEqual(result['receipt_sha256'],p.sha(self.receipt))
        self.assertEqual(result['native_rejection_reasons'],self.data['native_rejection_reasons'])
        self.assertEqual(self.data['native']['warnings'],0)
        self.assertEqual(p.tree_hash(self.root),before)

    def test_positive_api_and_its_session_never_admit_or_cache_negative(self):
        for session in (False,True):
            def checks():
                with self.assertRaisesRegex(p.Rejected,'not an accepted routing result'):p.check_result(self.receipt)
                self.assertIs(self.checked()['validated_rejection'],True)
                with self.assertRaisesRegex(p.Rejected,'not an accepted routing result'):p.check_result(self.receipt)
            if session:
                with p.validation_readback_session():
                    checks();self.assertEqual(p._readback_session.get()['entries'],{})
            else:checks()

    def test_real_positive_shape_refuses_diagnostic_without_poisoning_positive_cache(self):
        self.native_outcome(negative=False)
        with p.validation_readback_session():
            self.assertTrue(p.check_result(self.receipt)['current'])
            entries=dict(p._readback_session.get()['entries'])
            self.refused()
            self.assertEqual(p._readback_session.get()['entries'],entries)
            self.assertTrue(p.check_result(self.receipt)['current'])

    def test_negative_flag_without_raw_rejection_cannot_pass(self):
        self.native_outcome(negative=False)
        self.data.update(accepted=False,status='drc_rejected',whole_project_drc_clean=False)
        self.save_receipt();self.refused()

    def test_schema_status_baseline_scope_and_policy_cannot_downgrade(self):
        original=copy.deepcopy(self.data)
        cases=[('schema',True),('schema',2),('accepted',0),('accepted',True),('status','cancelled'),
            ('status','rejected'),('status','unsupported'),('status','timeout'),('status','cpu_budget_exceeded'),
            ('baseline','B1'),('scope','partial_completion'),('adapter','none'),('engine_profile','standard'),
            ('strategy',None),('input_policy','native'),('guidance_policy','native'),('diagnostic_schema',1),
            ('production_qualified',True),('engine_fanout_override',False),('engine_optimizer_override',False),
            ('engine_angle_binding',{}),('incumbent_scoring_contract',{})]
        for key,value in cases:
            with self.subTest(key=key,value=value):
                self.data=copy.deepcopy(original);self.data[key]=value;self.save_receipt();self.refused()
        self.data=original;self.save_receipt();self.assertTrue(self.checked()['validated_rejection'])

    def test_changed_summary_reasons_or_cleanliness_are_refused(self):
        original=copy.deepcopy(self.data)
        for change in ({'native_rejection_reasons':[]},{'native_rejection_reasons':['asserted reason']},
                       {'whole_project_drc_clean':True},{'native':dict(self.data['native'],blocking=0)}):
            with self.subTest(change=change):
                self.data=copy.deepcopy(original);self.data.update(change);self.save_receipt();self.refused()

    def test_malformed_or_unknown_findings_cannot_be_ordinary_rejections(self):
        cases=[{'severity':'error','type':'','items':[]},
               {'severity':'error','type':'unknown_future_check','items':[]},
               {'severity':'error','type':'clearance','items':[123]},
               {'severity':'exclusion','type':'clearance','items':[]},
               {'severity':'warning','type':'clearance','items':[],'excluded':True}]
        for finding in cases:
            with self.subTest(finding=finding):
                report=copy.deepcopy(self.native_shape);report['violations']=[finding]
                self.native.write_text(json.dumps(report))
                self.data.update(native=p.parse_report(self.native,self.source.name),
                    native_report_sha256=p.sha(self.native))
                self.data['native_rejection_reasons']=p.native_rejection_reasons(self.data['native'])
                self.save_receipt();self.refused()

    def test_source_snapshot_rules_candidate_native_and_retained_code_tampering(self):
        paths=[self.source,self.source.with_suffix('.kicad_pro'),self.run/'snapshot'/self.source.name,
            self.candidate,self.candidate.with_suffix('.kicad_pro'),self.run/'final-drc-input'/self.source.name,
            self.native,self.run/'code/pipeline.py',self.run/'engine-process.json',self.run/'metrics.json']
        for path in paths:
            with self.subTest(path=path):
                raw=path.read_bytes();path.write_bytes(raw+b'\nchanged\n');self.refused();path.write_bytes(raw)
        self.assertTrue(self.checked()['validated_rejection'])

    def test_missing_and_rehashed_corrupt_native_evidence_refuses(self):
        raw=self.native.read_bytes();self.native.unlink();self.refused()
        self.native.write_bytes(b'{}');self.data['native_report_sha256']=p.sha(self.native);self.save_receipt();self.refused()
        self.native.write_bytes(raw)

    def test_locked_route_change_refuses_even_with_updated_candidate_hash(self):
        tree=p.sx.read(self.candidate);tree.remove(p.routes(tree)[0]);p.sx.write(self.candidate,tree)
        self.data['candidate_sha256']=p.sha(self.candidate);self.save_receipt();self.refused()

    def test_process_exit_cleanup_cancelled_log_and_budget_changes_refuse(self):
        original=copy.deepcopy(self.data)
        process_path=self.run/'final-drc-process.json';raw=process_path.read_bytes()
        for change in ({'exit_code':0},{'cleanup_complete':False},{'status':'cancelled'}):
            with self.subTest(process=change):
                self.data=copy.deepcopy(original);process=json.loads(raw);process.update(change)
                p.save_json(process_path,process)
                for step in self.data['steps']:
                    if step['name']=='final-drc':step.update(change)
                self.save_receipt();self.refused()
        process_path.write_bytes(raw)
        for change in ({'wall_seconds':121},{'total_cpu_seconds':121},{'total_cpu_seconds':0}):
            with self.subTest(budget=change):
                self.data=copy.deepcopy(original);self.data.update(change);self.save_receipt();self.refused()
        self.data=copy.deepcopy(original);self.data['steps'].append(dict(name='engine',status='cancelled',cleanup_complete=True))
        self.save_receipt();self.refused()

    def test_late_source_or_report_mutation_refuses_after_native_branch(self):
        for path in (self.source.with_suffix('.kicad_pro'),self.native):
            with self.subTest(path=path):
                raw=path.read_bytes();original=p.check_preferences_record;calls=[]
                def mutate(*args,**kwargs):
                    result=original(*args,**kwargs);calls.append(1)
                    if len(calls)==2:path.write_bytes(raw+b'\n')
                    return result
                with patch.object(p,'check_preferences_record',side_effect=mutate):self.refused()
                self.assertGreaterEqual(len(calls),2);path.write_bytes(raw)

    def test_on_disk_policy_markers_cannot_downgrade_to_ordinary_negative(self):
        for name in ('floor-contract.json','pruning-scoring.json','engine-angle.json',
                     'routing-scope-input.dsn','pruning-preferences.json'):
            with self.subTest(name=name):
                path=self.run/name;path.write_bytes(b'{}')
                self.refused();path.unlink()
        self.assertTrue(self.checked()['validated_rejection'])

    def test_noncanonical_receipt_name_and_symlink_refuse(self):
        alias=self.run/'alias.json';alias.symlink_to(self.receipt)
        with self.assertRaises(p.Rejected):p.check_rejected_routing_attempt(alias)
        parent=self.root/'aliased-run';parent.symlink_to(self.run,target_is_directory=True)
        with self.assertRaises(p.Rejected):p.check_rejected_routing_attempt(parent/'result.json')
        with self.assertRaises(p.Rejected):p.check_rejected_routing_attempt(self.run/'candidate/../result.json')
        other=self.run/'other.json';other.write_bytes(self.receipt.read_bytes())
        with self.assertRaises(p.Rejected):p.check_rejected_routing_attempt(other)


if __name__=='__main__':unittest.main()
