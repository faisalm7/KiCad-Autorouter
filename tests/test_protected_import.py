"""Regression for observed SES UUID regeneration; no native success is mocked."""
import copy
from pathlib import Path
import tempfile
import unittest
from autorouter import pipeline as p, sexpr as sx

ROOT=Path(__file__).resolve().parents[1]

def board():
    return sx.parse('(kicad_pcb (net 1 "A") (net 2 "B") (segment (start 0 0) (end 5 0) (width 0.25) (layer "F.Cu") (net 1) (uuid "original")))')

class ProtectedImportTests(unittest.TestCase):
    def setUp(self):
        self.original=board();self.protected=copy.deepcopy(p.routes(self.original));self.imported=copy.deepcopy(self.original)
        sx.one(p.routes(self.imported)[0],'uuid')[1]='"regenerated"'

    def reconstruct(self):
        return p.transplant_routes(self.original,self.imported,protected=self.protected)

    def test_actual_failed_native_import_restores_only_original_ids(self):
        base=ROOT/'evidence/preferences-native-qualification-001/preferences-native-partial-001'
        original=sx.read(base/'snapshot/smoke.kicad_pcb');imported=sx.read(base/'imported.kicad_pcb')
        protected=p.routes(original);self.assertEqual(len(protected),2)
        before=copy.deepcopy((original,imported))
        result=p.transplant_routes(original,imported,protected=protected)
        self.assertEqual(p.immutable(result),p.immutable(original))
        self.assertTrue(all(route in p.routes(result) for route in protected))
        self.assertEqual(len(p.routes(result)),len(p.routes(imported)))
        strip=lambda r:[n for n in r if not isinstance(n,list) or not n or n[0]!='uuid']
        self.assertEqual([strip(n) for n in p.routes(result)],[strip(p.convert_route_nets(n,imported,original)) for n in p.routes(imported)])
        self.assertEqual((original,imported),before)

    def test_unique_match_restores_exact_node_and_preserves_other_routes(self):
        other=copy.deepcopy(p.routes(self.imported)[0]);sx.one(other,'uuid')[1]='"new"';sx.one(other,'start')[1]='5';sx.one(other,'end')[1]='10'
        self.imported.append(other);result=self.reconstruct()
        self.assertEqual(p.routes(result),[self.protected[0],other])
        self.assertEqual(sx.one(p.routes(self.imported)[0],'uuid')[1],'"regenerated"')

    def test_changes_to_any_nonidentity_field_reject(self):
        for field in ['start','end','width','layer','net']:
            with self.subTest(field=field):
                imported=copy.deepcopy(self.imported);sx.one(p.routes(imported)[0],field)[1]='2'
                with self.assertRaisesRegex(p.Rejected,'missing, changed or ambiguous'):
                    p.transplant_routes(self.original,imported,protected=self.protected)
        p.routes(self.imported)[0].append(['locked','yes'])
        with self.assertRaises(p.Rejected):self.reconstruct()

    def test_missing_duplicate_and_split_geometry_reject(self):
        for kind in ['missing','duplicate','split']:
            with self.subTest(kind=kind):
                imported=copy.deepcopy(self.imported);r=p.routes(imported)[0]
                if kind=='missing':imported.remove(r)
                elif kind=='duplicate':
                    duplicate=copy.deepcopy(r);sx.one(duplicate,'uuid')[1]='"duplicate"';imported.append(duplicate)
                else:
                    duplicate=copy.deepcopy(r);sx.one(r,'end')[1]='2';sx.one(duplicate,'start')[1]='2';sx.one(duplicate,'uuid')[1]='"split"';imported.append(duplicate)
                with self.assertRaises(p.Rejected):p.transplant_routes(self.original,imported,protected=self.protected)

    def test_duplicate_or_colliding_import_ids_reject(self):
        for uid in ['"regenerated"','"original"']:
            with self.subTest(uuid=uid):
                imported=copy.deepcopy(self.imported);other=copy.deepcopy(p.routes(imported)[0]);sx.one(other,'start')[1]='5';sx.one(other,'end')[1]='10';sx.one(other,'uuid')[1]=uid;imported.append(other)
                with self.assertRaises(p.Rejected):p.transplant_routes(self.original,imported,protected=self.protected)

    def test_malformed_ids_and_unknown_protected_nodes_reject(self):
        for where in ['original','imported','duplicate_uuid','foreign','repeated']:
            with self.subTest(where=where):
                original=copy.deepcopy(self.original);imported=copy.deepcopy(self.imported);protected=copy.deepcopy(self.protected)
                if where=='original':
                    r=p.routes(original)[0];r.remove(sx.one(r,'uuid'));protected=copy.deepcopy(p.routes(original))
                if where=='imported':
                    r=p.routes(imported)[0];r.remove(sx.one(r,'uuid'))
                if where=='duplicate_uuid':p.routes(imported)[0].append(['uuid','"second"'])
                if where=='foreign':sx.one(protected[0],'width')[1]='0.1'
                if where=='repeated':protected.append(copy.deepcopy(protected[0]))
                with self.assertRaises(p.Rejected):p.transplant_routes(original,imported,protected=protected)

    def test_explicit_net_mapping_precedes_identity_match(self):
        sx.children(self.imported,'net')[0][1]='9';sx.one(p.routes(self.imported)[0],'net')[1]='9'
        self.assertEqual(p.routes(self.reconstruct()),self.protected)

    def test_reconciliation_binding_recomputes_actual_import_and_candidate(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.cache') as temp:
            root=Path(temp);imported=root/'imported.kicad_pcb';candidate=root/'candidate.kicad_pcb'
            sx.write(imported,self.imported);audit={'imported_sha256':p.sha(imported)}
            rebuilt=p.transplant_routes(self.original,self.imported,protected=self.protected,audit=audit);sx.write(candidate,rebuilt)
            data={'protected_route_import':audit}
            check=lambda record:p.check_protected_import(root,record,self.original,candidate,self.protected)
            check(data)
            self.assertEqual(audit['matches'][0]['original_uuid'],'"original"')
            self.assertEqual(audit['matches'][0]['imported_uuid'],'"regenerated"')
            for key in ['original_uuid','imported_uuid','non_uuid_sha256']:
                altered=copy.deepcopy(data);altered['protected_route_import']['matches'][0][key]='wrong'
                with self.subTest(key=key),self.assertRaises(p.Rejected):check(altered)
            altered=copy.deepcopy(data);altered['protected_route_import']['transplanted_routes_sha256']='wrong'
            with self.assertRaises(p.Rejected):check(altered)
            imported.write_text(imported.read_text()+'\n')
            with self.assertRaises(p.Rejected):check(data)
            sx.write(imported,self.imported);changed=copy.deepcopy(rebuilt);sx.one(p.routes(changed)[0],'width')[1]='0.1';sx.write(candidate,changed)
            with self.assertRaises(p.Rejected):check(data)

    def test_historical_transplant_and_no_binding_keep_default_behavior(self):
        self.assertEqual(p.routes(p.transplant_routes(self.original,self.imported)),p.routes(self.imported))
        p.check_protected_import(ROOT/'.runs/nonexistent',{},self.original,ROOT/'nonexistent',self.protected)

    def test_locked_via_and_arc_exact_matching_only(self):
        for route in ['(via (at 2 2) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 1) (locked yes) (uuid "original"))',
                      '(arc (start 0 0) (mid 1 1) (end 2 0) (width 0.25) (layer "F.Cu") (net 1) (locked yes) (uuid "original"))']:
            with self.subTest(kind=sx.parse(route)[0]):
                original=board();original.remove(p.routes(original)[0]);original.append(sx.parse(route));imported=copy.deepcopy(original);sx.one(p.routes(imported)[0],'uuid')[1]='"regenerated"'
                result=p.transplant_routes(original,imported,protected=p.routes(original));self.assertEqual(result,original)
                p.routes(imported)[0].remove(sx.one(p.routes(imported)[0],'locked'))
                with self.assertRaises(p.Rejected):p.transplant_routes(original,imported,protected=p.routes(original))

if __name__=='__main__':unittest.main()
