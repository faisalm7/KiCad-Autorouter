"""Exact native-emission comparison: order can change, route identity cannot."""
import copy,unittest
from experiments.kicad8_native_compat_continuation_v1 import driver as d

class NativeEmissionOrder(unittest.TestCase):
    def board(self):
        return ['kicad_pcb',['version','20260101'],['generator','pcbnew'],
            ['segment',['uuid','a'],['start','1','2'],['end','3','4'],['width','0.3'],['net','1']],
            ['via',['uuid','b'],['at','3','4'],['size','0.8'],['drill','0.4'],['layers','F.Cu','B.Cu'],['net','1']]]
    def test_reordering_full_native_records_is_exact(self):
        first=self.board();second=first[:3]+list(reversed(first[3:]));result=d.emission_equal_by_uuid(first,second)
        self.assertEqual(result['route_count'],2);self.assertTrue(result['native_routes_equal_by_uuid']);self.assertFalse(result['route_list_order_equal'])
        self.assertEqual(d.emission_equal_by_uuid(first,first)['route_records_sha256'],result['route_records_sha256'])
        self.assertNotEqual(result['first_route_list_sha256'],result['second_route_list_sha256'])
    def test_all_route_fields_and_identity_remain_exact(self):
        for key in ('width','net','start','uuid'):
            changed=copy.deepcopy(self.board());d.sx.one(changed[3],key)[1]='changed'
            with self.subTest(key=key),self.assertRaises(d.p.Rejected):d.emission_equal_by_uuid(self.board(),changed)
        changed=self.board();changed.pop()
        with self.assertRaises(d.p.Rejected):d.emission_equal_by_uuid(self.board(),changed)
    def test_duplicate_empty_missing_or_ambiguous_uuid_rejects_even_self_comparison(self):
        for action in ('duplicate','empty','missing','ambiguous'):
            changed=self.board()
            if action=='duplicate':d.sx.one(changed[4],'uuid')[1]='a'
            elif action=='empty':d.sx.one(changed[3],'uuid')[1]=''
            elif action=='missing':changed[3].remove(d.sx.one(changed[3],'uuid'))
            else:changed[3].append(['uuid','other'])
            with self.subTest(action=action),self.assertRaises(d.p.Rejected):d.emission_equal_by_uuid(changed,changed)
    def test_original_nonrouting_fields_and_headers_remain_exact(self):
        changed=self.board();changed[1][1]='older'
        with self.assertRaises(d.p.Rejected):d.emission_equal_by_uuid(self.board(),changed)

if __name__=='__main__':unittest.main()
