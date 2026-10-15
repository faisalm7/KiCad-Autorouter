"""Semantic refill preservation controls; these tests do not execute KiCad."""
import copy
import unittest
from autorouter import pipeline as p, sexpr as sx
from tests.test_selected_proposal_import import board, uid

class RefillRouteNetControls(unittest.TestCase):
    def named(self,tree):
        tree=copy.deepcopy(tree);table={n[1]:n[2] for n in sx.children(tree,'net')}
        tree[:]=[n for n in tree if n not in sx.children(tree,'net')]
        def convert(node):
            for child in node[1:]:
                if isinstance(child,list) and child:
                    if child[0]=='net':child[:]=['net',table[child[1]]]
                    else:convert(child)
        convert(tree);sx.one(tree,'version')[1]='20260206';return tree

    def test_numbered_to_named_serialization_and_route_order_preserve_semantics(self):
        original=board();saved=self.named(original)
        saved[:]=[n for n in saved if n not in p.routes(saved)]+list(reversed(p.routes(saved)))
        before=copy.deepcopy(original);after=copy.deepcopy(saved)
        p.check_refill_route_nets(original,saved);self.assertEqual(p.transplant_fill(original,saved),original)
        self.assertEqual(original,before);self.assertEqual(saved,after)

    def test_actual_net_change_cannot_be_hidden_by_fill_transplant(self):
        original=board();saved=self.named(original);sx.one(p.routes(saved)[0],'net')[1]='"LED"'
        with self.assertRaisesRegex(p.Rejected,'net assignments'):p.check_refill_route_nets(original,saved)
        with self.assertRaisesRegex(p.Rejected,'net assignments'):p.transplant_fill(original,saved)

    def test_all_route_identity_changes_and_malformed_aliases_refuse(self):
        for mutation in ('delete','add','uuid','duplicate','kind','unknown_code','code_name_conflict'):
            original=board();saved=copy.deepcopy(original)
            with self.subTest(mutation=mutation):
                if mutation=='delete':saved.remove(p.routes(saved)[0])
                elif mutation=='add':
                    route=copy.deepcopy(p.routes(saved)[0]);sx.one(route,'uuid')[1]='"'+uid('new')+'"';saved.append(route)
                elif mutation=='uuid':sx.one(p.routes(saved)[0],'uuid')[1]='"'+uid('new')+'"'
                elif mutation=='duplicate':saved.append(copy.deepcopy(p.routes(saved)[0]))
                elif mutation=='kind':p.routes(saved)[0][0]='arc'
                elif mutation=='unknown_code':sx.one(p.routes(saved)[0],'net')[1]='99'
                else:sx.one(p.routes(saved)[0],'net').append('"LED"')
                with self.assertRaises((p.Rejected,ValueError)):p.transplant_fill(original,saved)

    def test_unassigned_route_reassigned_to_real_net_refuses(self):
        original=board();sx.one(p.routes(original)[0],'net')[1]='0';saved=self.named(original)
        p.check_refill_route_nets(original,saved);sx.one(p.routes(saved)[0],'net')[1]='"GND"'
        with self.assertRaisesRegex(p.Rejected,'net assignments'):p.transplant_fill(original,saved)

    def test_equivalent_net_renaming_requires_both_encodings_to_agree(self):
        original=board();saved=self.named(original)
        for tree in (original,saved):
            def rename(node):
                for i,child in enumerate(node):
                    if isinstance(child,list):rename(child)
                    elif child=='"GND"':node[i]='"GROUND"'
            rename(tree)
        p.check_refill_route_nets(original,saved)
