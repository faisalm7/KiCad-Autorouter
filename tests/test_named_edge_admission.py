"""Captured-source/scope regressions; Native qualification is separate evidence."""
import copy,json
from pathlib import Path
import unittest
from unittest.mock import patch
from autorouter import pipeline as p,adapter as a,native_edge as edge,floor_route as f,sexpr as sx,preferences as pref,pour_rule_area as pour
from tests import test_native_edge_record as edge_fixture
from tests.test_native_edge_named import inputs


class NamedEdgeAdmission(unittest.TestCase):
    def setUp(self):
        edge_fixture.EdgeRecord.setUp(self)
        self.code=self.folder/'code';self.code.mkdir()
        self.capture('NAMED_EDGE_ADMISSION_POLICY='+repr(p.NAMED_EDGE_ADMISSION_POLICY)+'\n')
        self.data.update(scope='whole_board_unlocked_routing',engine_profile='standard',
            native_edge_admission_policy=p.NAMED_EDGE_ADMISSION_POLICY)

    def capture(self,text):
        path=self.code/'pipeline.py';path.write_text(text)
        self.data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(path)

    def policy(self,*,data=None,direct=True,policy='native',toolchain=None):
        return p.check_named_edge_policy(self.folder,self.data if data is None else data,
            direct_import=direct,input_policy=policy,native_toolchain=toolchain)

    def named(self,*,parent=False):
        tree,_,project=inputs(parent=parent)
        tree.append(['placement'])
        self.board.with_suffix('.kicad_pro').write_text(json.dumps(project))
        self.raw=a._dump_dsn(tree).encode()
        adapted,adapter_record=a.adapt_bytes(self.raw,'both',[])
        output,record=edge.correct(adapted,p.native_edge_context(self.board,known_named=True))
        (self.folder/'native.dsn').write_bytes(self.raw)
        (self.folder/'edge-adapter-input.dsn').write_bytes(adapted)
        (self.folder/'task.dsn').write_bytes(output)
        p.save_json(self.folder/'native-edge-correction.json',record)
        self.data.update(source_hashes=p.tree_hash(self.board.parent),native_edge_correction=record,
            adapter_transformations=adapter_record)
        return record

    def test_current_literal_and_parent_replay_and_legacy_named_skip(self):
        for parent in (False,True):
            with self.subTest(parent=parent):
                record=self.named(parent=parent)
                self.assertTrue(self.policy())
                self.assertEqual(p.check_native_edge_transport(self.folder,self.data,_known_named_edge=self.policy()),record)
                self.assertFalse(record['loaded_named_matrix_qualified'])
                with self.assertRaises(p.Rejected):p.check_native_edge_transport(self.folder,self.data)
                # Real historical producers retained the unapplied DSN and reason.
                self.capture('LEGACY_PIPELINE=True\n');self.data.pop('native_edge_admission_policy')
                self.assertFalse(self.policy())
                legacy_input=(self.folder/'edge-adapter-input.dsn').read_bytes()
                output,legacy=edge.correct(legacy_input,p.native_edge_context(self.board))
                self.assertEqual(output,legacy_input);self.assertFalse(legacy['applied'])
                (self.folder/'task.dsn').write_bytes(output);p.save_json(self.folder/'native-edge-correction.json',legacy)
                self.data['native_edge_correction']=legacy
                self.assertEqual(p.check_native_edge_transport(self.folder,self.data,_known_named_edge=self.policy()),legacy)
                self.capture('NAMED_EDGE_ADMISSION_POLICY='+repr(p.NAMED_EDGE_ADMISSION_POLICY)+'\n')
                self.data['native_edge_admission_policy']=p.NAMED_EDGE_ADMISSION_POLICY

    def test_default_only_transform_and_record_remain_byte_exact(self):
        before=p.native_edge_context(self.board)
        after=p.native_edge_context(self.board,known_named=self.policy())
        self.assertEqual(before,after)
        self.assertEqual(edge.correct(self.raw,before),edge.correct(self.raw,after))

    def test_missing_wrong_and_foreign_markers_fail_before_optional_edge_exit(self):
        for value in (None,'older-policy',False):
            data=copy.deepcopy(self.data);data['native_edge_admission_policy']=value
            with self.subTest(value=value),self.assertRaises(p.Rejected):self.policy(data=data)
        data=copy.deepcopy(self.data);data.pop('native_edge_admission_policy')
        data.pop('native_edge_correction')
        (self.folder/'native-edge-correction.json').unlink();(self.folder/'edge-adapter-input.dsn').unlink()
        with self.assertRaisesRegex(p.Rejected,'admission policy'):self.policy(data=data)
        for options in ({'direct':False},{'policy':'placement-clearance-v1'},{'toolchain':object()}):
            with self.subTest(options=options),self.assertRaisesRegex(p.Rejected,'direct producer'):self.policy(**options)
        for changes in ({'adapter':'none'},{'baseline':'C-prototype','strategy':'native_validated_zone_net_pruning'}):
            data=copy.deepcopy(self.data);data.update(changes)
            with self.subTest(changes=changes),self.assertRaises(p.Rejected):self.policy(data=data)
            data.pop('native_edge_admission_policy');self.assertFalse(self.policy(data=data))

    def test_source_pin_and_ast_declaration_cannot_downgrade(self):
        path=self.code/'pipeline.py';path.write_text('changed')
        with self.assertRaisesRegex(p.Rejected,'source pin'):self.policy()
        for text in ('OTHER=True\n',
                'NAMED_EDGE_ADMISSION_POLICY="wrong"\n',
                'NAMED_EDGE_ADMISSION_POLICY=str("known-named-whole-native-edge-v1")\n',
                'NAMED_EDGE_ADMISSION_POLICY="known-named-whole-native-edge-v1"\nNAMED_EDGE_ADMISSION_POLICY="known-named-whole-native-edge-v1"\n',
                '# NAMED_EDGE_ADMISSION_POLICY="known-named-whole-native-edge-v1"\n',
                'def hidden():\n NAMED_EDGE_ADMISSION_POLICY="known-named-whole-native-edge-v1"\n'):
            self.capture(text)
            with self.subTest(text=text),self.assertRaises(p.Rejected):self.policy()

    def test_unqualified_task_scopes_stay_default_only_with_mandatory_version(self):
        for changes in ({'scope':'partial_completion'},{'scope':'selected_nets'},
                {'engine_profile':'tuned-free-angle'},{'engine_fanout_override':False},
                {'engine_optimizer_override':False},{'native_minimum_preferences':{}},
                {'layer_binding':{}},{'selected_net_binding':{}},
                {'routing_preferences':{'effective':{**pref.DEFAULTS,'profile':'completion-only','layers':['F.Cu']}}}):
            data=copy.deepcopy(self.data);data.update(changes)
            with self.subTest(changes=changes):
                self.assertFalse(self.policy(data=data))
                data.pop('native_edge_admission_policy')
                with self.assertRaises(p.Rejected):self.policy(data=data)
        data=copy.deepcopy(self.data);data.pop('native_edge_admission_policy')
        self.assertFalse(self.policy(data=data,direct=False))

    def test_custom_companion_and_higher_clearance_are_still_skipped(self):
        self.named();rules=self.board.with_suffix('.kicad_dru');rules.write_text('(version 1)')
        self.assertFalse(p.native_edge_context(self.board,known_named=self.policy())['applicable'])
        rules.unlink();project=json.loads(self.board.with_suffix('.kicad_pro').read_text())
        project['net_settings']['classes'][1]['clearance']=.31
        self.board.with_suffix('.kicad_pro').write_text(json.dumps(project))
        self.assertFalse(p.native_edge_context(self.board,known_named=self.policy())['applicable'])

    def test_pour_chain_replays_same_named_context_as_edge_reader(self):
        # Mock only unrelated Native pour/refill witnesses. Exercise actual
        # adapter+edge composition and fail if the shared context is dropped.
        tree=sx.read(self.board)
        sx.one(sx.one(tree,'gr_rect'),'uuid')[1]=json.dumps('3a3752c2-c83f-4e6f-a1d8-3bf0500271fd')
        self.board.write_bytes((sx.dump(tree)+'\n').encode())
        self.named();candidate=self.board
        p.save_json(self.folder/'pour-keepout-audit.json',{})
        (self.folder/'pour-before-refill.kicad_pcb').write_bytes(self.board.read_bytes())
        (self.folder/'pour-corrected.dsn').write_bytes(self.raw)
        correction={'owned-test':'pour-chain'};p.save_json(self.folder/'pour-dsn-correction.json',correction)
        self.data.update(pour_dsn_correction=correction,steps=[{'name':'engine','cwd':str(self.folder)}])
        tree=sx.read(self.board)
        with patch.object(pour,'qualify',return_value=[{}]),patch.object(pour,'verify_native_record'),\
                patch.object(pour,'correct',return_value=(self.raw,correction)),\
                patch.object(f,'process_check'),patch.object(f,'check_drc_stage'),\
                patch.object(sx,'read',return_value=tree):
            p.check_pour_evidence(self.folder,self.data,tree,candidate,_known_named_edge=self.policy())
            with self.assertRaisesRegex(p.Rejected,'engine input differs'):
                p.check_pour_evidence(self.folder,self.data,tree,candidate)

    def full_receipt(self):
        from tests import test_result as support
        case=support.ResultFreshnessTests(methodName='runTest');case.setUp();self.addCleanup(case.doCleanups)
        data=case.data;data.update(adapter='both',native_edge_admission_policy=p.NAMED_EDGE_ADMISSION_POLICY)
        raw=(case.run/'native.dsn').read_bytes();adapted,record=a.adapt_bytes(raw,'both',[])
        output,correction=edge.correct(adapted,p.native_edge_context(case.run/'snapshot'/case.source.name,known_named=True))
        (case.run/'task.dsn').write_bytes(output);(case.run/'edge-adapter-input.dsn').write_bytes(adapted)
        p.save_json(case.run/'native-edge-correction.json',correction);p.save_json(case.run/'obstacles.json',[])
        data.update(adapter_transformations=record,native_edge_correction=correction,task_dsn_sha256=p.sha(case.run/'task.dsn'))
        case.save_receipt();self.assertTrue(p.check_result(case.receipt)['current'])
        return case

    def test_source_snapshot_and_receipt_changes_after_last_import_check_refuse(self):
        # Complete shared checker with actual file/census/proof reads. Native
        # worker/report files are explicitly authored by the existing fixture.
        for target in ('source','snapshot','candidate','receipt','code'):
            with self.subTest(target=target):
                case=self.full_receipt();original=p.normal_import_contract;calls=[]
                def late(*args,**kwargs):
                    result=original(*args,**kwargs);calls.append(None)
                    if len(calls)==2:
                        path={'source':case.source.with_suffix('.kicad_pro'),
                            'snapshot':case.run/'snapshot'/case.source.with_suffix('.kicad_pro').name,
                            'candidate':case.candidate,'receipt':case.receipt,'code':case.run/'code/native_edge.py'}[target]
                        path.write_bytes(path.read_bytes()+b'\n')
                    return result
                with patch.object(p,'normal_import_contract',side_effect=late),self.assertRaises(p.Rejected):
                    p.check_result(case.receipt)
                self.assertEqual(len(calls),2)


if __name__=='__main__':unittest.main()
