"""Pure component partition controls; no KiCad, Native board or routing evidence."""
import copy
import unittest
from experiments.native_components_v1.normalize import normalize

class NativeComponentNormalizationControls(unittest.TestCase):
    def fixture(self):
        ids=['00000000-0000-0000-0000-'+str(i).zfill(12) for i in range(1,7)]
        rows=[]
        for i,uid in enumerate(ids[:4]):
            rows.append(dict(uuid=uid,footprint_uuid=ids[4],reference='J1',number=str(i+1),
                net='GND' if i<3 else 'VCC',netcode=1 if i<3 else 2,layers=['F.Cu'],
                attribute='smd',eligible=True,excluded_reason=''))
        a,b,c,d=ids[:4]
        return rows,{a:[a,b],b:[a,b],c:[c],d:[d]},ids

    def test_same_net_separate_components_and_pad_identity_are_retained(self):
        rows,reach,ids=self.fixture();rows[1]['number']=rows[0]['number']
        before=copy.deepcopy((rows,reach));result=normalize(rows,reach)
        self.assertEqual([x['pad_uuids'] for x in result['components']],[[ids[0],ids[1]],[ids[2]],[ids[3]]])
        self.assertEqual((result['queried_pad_count'],result['positive_net_count']),(4,2))
        self.assertEqual(len(result['pad_census']),4);self.assertEqual((rows,reach),before)

    def test_unknown_duplicate_and_mixed_pad_net_inputs_refuse(self):
        for mode in ('duplicate-pad','unknown-member','duplicate-member','mixed-net','one-name-two-codes','two-names-one-code','missing-query','extra-query','missing-seed'):
            with self.subTest(mode=mode):
                rows,reach,ids=self.fixture();a,b,c,d,fp,unknown=ids
                if mode=='duplicate-pad':rows.append(copy.deepcopy(rows[0]))
                elif mode=='unknown-member':reach[a].append(unknown)
                elif mode=='duplicate-member':reach[a].append(a)
                elif mode=='mixed-net':reach[a].append(d)
                elif mode=='one-name-two-codes':rows[1]['netcode']=3
                elif mode=='two-names-one-code':rows[3]['netcode']=1
                elif mode=='missing-query':del reach[c]
                elif mode=='extra-query':reach[unknown]=[unknown]
                else:reach[a]=[b]
                with self.assertRaises(ValueError):normalize(rows,reach)

    def test_asymmetric_and_nontransitive_memberships_refuse(self):
        for mode in ('asymmetric','nontransitive'):
            with self.subTest(mode=mode):
                rows,reach,ids=self.fixture();a,b,c=ids[:3]
                if mode=='asymmetric':reach[b]=[b]
                else:reach.update({a:[a,b],b:[a,b,c],c:[b,c]})
                with self.assertRaises(ValueError):normalize(rows,reach)

    def test_repeated_zone_parent_uuid_is_never_a_pad_or_union_key(self):
        rows,reach,ids=self.fixture();a,b,c=ids[:3];zone=ids[5]
        # Same-net PAD partitions remain separate. The API layer must discard
        # repeated ZONE parents; passing one as a PAD identity is rejected.
        result=normalize(rows,reach)
        self.assertNotEqual(next(x['pad_uuids'] for x in result['components'] if a in x['pad_uuids']),[a,b,c])
        for seed in (a,c):reach[seed].append(zone)
        with self.assertRaises(ValueError):normalize(rows,reach)

    def test_unknown_attribute_and_netted_npth_cannot_hide_as_exclusions(self):
        # These two expectations expose the reviewed normalizer contract gap.
        for attr,code,net in (('unknown-pad-kind',0,''),('npth',1,'GND')):
            with self.subTest(attribute=attr):
                rows,reach,ids=self.fixture()
                rows.append(dict(uuid=ids[5],footprint_uuid=ids[4],reference='J1',number='5',net=net,
                    netcode=code,layers=['F.Cu'],attribute=attr,eligible=False,excluded_reason='excluded'))
                with self.assertRaises(ValueError):normalize(rows,reach)

if __name__=='__main__':unittest.main()
