"""Prospective portable width reader controls; no Native/JVM, unexecuted."""
import copy,unittest
from pathlib import Path
import tempfile
from unittest.mock import patch
from autorouter import pipeline as p
from autorouter import floor_route as f
from experiments.hfe_original_native_v1 import driver as shared
from experiments.fanout_baseline_v1 import continuation as owned
from experiments.fanout_baseline_v1.continuation import require_width300
class WidthReaderControls(unittest.TestCase):
    def test_published_history_is_checked_before_retained_bytes_are_adopted(self):
        # Authored lineage receipts only; never Native evidence. Same-size log
        # and child edits must refuse even while the old error stays unchanged.
        for fault in (None,'outer_log','child_log','child_literal'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary).resolve();positive=root/'native';route=positive/'route';route.mkdir(parents=True)
                protocol=root/'protocol.json';p.save_json(protocol,{'authored':True})
                receipt=route/'result.json';p.save_json(receipt,{'authored':True})
                (root/'outer.log').write_text('owned outer A');(positive/'child.log').write_text('owned child A')
                child={'error':'ValueError: duplicate singleton rule','completed_evidence':shared.material(positive)}
                childpath=positive/'result.json';p.save_json(childpath,child)
                outer={'child_completed_evidence_bound':True,'child_receipt_sha256':p.sha(childpath),
                    'child_literal':f.canonical(child),'completed_evidence':shared.material(root)}
                outerpath=root/'result.json';p.save_json(outerpath,outer)
                pins=dict(POSITIVE=positive,OLD_OUTER=outerpath,OLD_OUTER_SHA=p.sha(outerpath),
                    OLD_PROTOCOL=protocol,OLD_PROTOCOL_SHA=p.sha(protocol),OLD_POSITIVE_SHA=p.sha(receipt))
                if fault=='outer_log':(root/'outer.log').write_text('owned outer B')
                if fault=='child_log':(positive/'child.log').write_text('owned child B')
                if fault=='child_literal':p.save_json(childpath,dict(child,undeclared=True))
                with patch.multiple(owned,**pins):
                    if fault is None:self.assertEqual(owned.check_prior_witness(),(outer,child))
                    else:
                        with self.assertRaisesRegex(p.Rejected,'historical published'):owned.check_prior_witness()

    def tree(self):
        return ['pcb','owned',['unit','um'],['structure',['rule',['width','300'],['clearance','200']],['rule',['clearance','250',['type','wire_area']]]],['network',['class','Default','ROUTE',['rule',['width','300'],['clearance','200']]]]]
    def test_clearance_only_structure_group_remains_accepted(self):require_width300(self.tree())
    def test_original_single_rule_group_remains_accepted(self):
        tree=self.tree();tree[3].pop();require_width300(tree)
    def test_duplicate_same_width_across_groups_rejects(self):
        tree=self.tree();tree[3].append(['rule',['width','300']])
        with self.assertRaises(p.Rejected):require_width300(tree)
    def test_different_structure_width_rejects(self):
        tree=self.tree();tree[3][1][1][1]='299'
        with self.assertRaises(p.Rejected):require_width300(tree)
    def test_missing_duplicate_or_wrong_class_width_rejects(self):
        for mode in ('missing','duplicate','wrong'):
            tree=self.tree();rule=tree[4][1][3]
            if mode=='missing':rule.pop(1)
            elif mode=='duplicate':rule.append(['width','300'])
            else:rule[1][1]='301'
            with self.subTest(mode=mode),self.assertRaises(p.Rejected):require_width300(tree)
    def test_foreign_unit_and_multiple_class_rejects(self):
        tree=self.tree();tree[2][1]='mm'
        with self.assertRaises(p.Rejected):require_width300(tree)
        tree=self.tree();tree[4].append(copy.deepcopy(tree[4][1]))
        with self.assertRaises(p.Rejected):require_width300(tree)
