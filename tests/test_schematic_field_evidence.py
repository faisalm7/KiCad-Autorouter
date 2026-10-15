"""Regression seams; real native qualification is recorded separately."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,schematic_fields as policy,schematic_field_evidence as evidence
from test_schematic_fields import scene,prove

class FieldEvidenceControls(unittest.TestCase):
    def summary(self):
        _,_,raw=scene();findings=copy.deepcopy(raw['schematic_parity'])
        return {'opens':0,'blocking':0,'warnings':1,'exclusions':0,'ignored_checks':[],
            'findings':findings,'field_parity':{'schema':1,'policy':evidence.POLICY,'qualification':prove(scene())}}
    def test_library_warning_is_retained_beside_qualified_field_warning(self):
        native=self.summary();native['findings'].append({'type':'lib_footprint_issues','severity':'warning','items':[]})
        native['warnings']=2
        self.assertTrue(p.native_accepted(native));self.assertEqual(len(native['findings']),2)
    def test_missing_proof_or_disabled_field_check_rejects(self):
        native=self.summary();del native['field_parity'];self.assertFalse(p.native_accepted(native))
        native=self.summary();native['ignored_checks']=[{'key':evidence.TYPE}];self.assertFalse(p.native_accepted(native))
    def test_unrelated_error_is_never_waived(self):
        native=self.summary();native['findings'].append({'type':'clearance','severity':'error','items':[]})
        self.assertFalse(p.native_accepted(native))
    def test_native_mandatory_case_alias_cannot_hide_raw_source_value(self):
        from autorouter import sexpr as sx
        good=sx.parse('(kicad_sch (symbol (property "Datasheet" "~")))')
        board=sx.parse('(kicad_pcb (footprint (property "Datasheet" "~")))')
        evidence.check_source_fields(good,board)
        for spelling in ('Datasheet','datasheet','DATASHEET'):
            for kind in ('symbol','footprint'):
                sch=copy.deepcopy(good);pcb=copy.deepcopy(board)
                owner=sx.children(sch if kind=='symbol' else pcb,kind)[0]
                owner.append(['property','"'+spelling+'"','"hidden real URL"'])
                with self.subTest(kind=kind,spelling=spelling),self.assertRaises(ValueError):
                    evidence.check_source_fields(sch,pcb)
    def test_complete_field_steps_cannot_disclaim_actual_parity(self):
        _,_,raw=scene()
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name);board=folder/'input/board.kicad_pcb'
            for path in evidence.paths(folder,'final-drc'):path.write_text('{}')
            def read(path):return {'input':str(board)} if path.name.endswith('-binding.json') else raw
            data={'steps':[{'name':'final-drc','cwd':str(folder),'argv':['drc']}]}
            with patch.object(evidence,'check_availability'),patch.object(evidence,'readback',return_value=None),patch('autorouter.floor_route.read_json',side_effect=read),patch('autorouter.floor_route.process_check') as check:
                with self.assertRaisesRegex(p.Rejected,'actual complete native schematic parity'):
                    evidence.check_processes(folder,data,'final-drc',board,sandboxed=True)
                check.assert_not_called()
                data['steps'][0]['argv'].append('--schematic-parity')
                evidence.check_processes(folder,data,'final-drc',board,sandboxed=True)
                self.assertEqual([call.args[2] for call in check.call_args_list],list(evidence.names('final-drc')))

class BoardOnlyFieldCensusControls(unittest.TestCase):
    def scene(self):
        from autorouter import sexpr as sx
        tree,obs,report=scene()
        board=sx.parse('(kicad_pcb (footprint "Library:LED" (uuid 00000000-0000-0000-0000-000000000001) (property "Reference" "D1")) (footprint "LOGO" (uuid 00000000-0000-0000-0000-000000000002) (layer "B.Cu") (at 10 20) (attr board_only exclude_from_pos_files exclude_from_bom) (property "Reference" "G***" (layer "B.SilkS")) (property "Value" "LOGO" (layer "B.Fab")) (property "Datasheet" "" (layer "B.Fab")) (property "Description" "" (layer "B.Fab")) (fp_poly (pts (xy 0 0) (xy 1 0) (xy 1 1)) (layer "B.SilkS"))))')
        obs['footprints'].append({'reference':'G***','uuid':'00000000-0000-0000-0000-000000000002','fields':{'Datasheet':'','Description':''}})
        return board,policy.sx.dump(tree),obs,report
    def project(self,c):return evidence.project_board_only_fields(*c)
    def test_complete_artwork_census_and_hashes_preserve_raw_observations_and_warnings(self):
        c=self.scene();before=copy.deepcopy(c);projected,proof=self.project(c)
        self.assertEqual(c,before);self.assertEqual(len(c[2]['footprints']),2)
        self.assertEqual(proof['complete_footprint_count'],2);self.assertEqual(proof['compared_footprint_count'],1)
        self.assertEqual(proof['complete_observer_sha256'],policy.digest(policy.canonical(c[2])))
        self.assertEqual(proof['projected_observer_sha256'],policy.digest(policy.canonical(projected)))
        self.assertEqual(proof['artwork'][0]['pad_count'],0)
        q=policy.derive(c[1],projected,c[3]);self.assertTrue(policy.qualified(q,c[3]['schematic_parity']))
        self.assertNotEqual(q['observer_sha256'],proof['complete_observer_sha256'])
    def test_pad_or_model_or_path_or_unknown_child_cannot_be_partitioned(self):
        from autorouter import sexpr as sx
        for child in ('(pad "1" np_thru_hole circle (size 1 1))','(pad "1" smd rect (net 1 "GND"))',
                '(model "stock.step")','(path "/schematic/path")','(net_tie_pad_groups "1,2")',
                '(zone (net 1))','(unknown_future_electrical_field yes)'):
            c=self.scene();sx.children(c[0],'footprint')[1].append(sx.parse(child))
            with self.subTest(child=child),self.assertRaises(ValueError):self.project(c)
    def test_ordinary_missing_component_and_ambiguous_footprints_reject(self):
        from autorouter import sexpr as sx
        for mode in ('no_board_only','smd','missing_source','missing_native','uuid','ref','duplicate_ref','duplicate_uuid'):
            c=self.scene();fp=sx.children(c[0],'footprint')[1];row=c[2]['footprints'][1]
            if mode=='no_board_only':sx.one(fp,'attr').remove('board_only')
            elif mode=='smd':sx.one(fp,'attr').append('smd')
            elif mode=='missing_source':c[0].remove(fp)
            elif mode=='missing_native':c[2]['footprints'].pop(0)
            elif mode=='uuid':row['uuid']='00000000-0000-0000-0000-000000000003'
            elif mode=='ref':row['reference']='OTHER'
            elif mode=='duplicate_ref':sx.one(sx.children(c[0],'footprint')[0],'property')[2]='"g***"'
            elif mode=='duplicate_uuid':sx.one(fp,'uuid')[1]='00000000-0000-0000-0000-000000000001'
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.project(c)
    def test_copper_variable_surface_and_source_native_field_disagreement_reject(self):
        from autorouter import sexpr as sx
        for mode in ('copper','missing_layer','variable','field','unknown_native','unknown_key'):
            c=self.scene();fp=sx.children(c[0],'footprint')[1]
            if mode=='copper':sx.one(sx.one(fp,'fp_poly'),'layer')[1]='"B.Cu"'
            elif mode=='missing_layer':fp.append(sx.parse('(fp_text user "unqualified")'))
            elif mode=='variable':sx.children(fp,'property')[1][2]='"${REFERENCE}"'
            elif mode=='field':c[2]['footprints'][1]['fields']['Datasheet']='https://real.example'
            elif mode=='unknown_native':c[2]['footprints'][1]['fields']['hidden']='x'
            elif mode=='unknown_key':c[2]['footprints'][1]['pad_count']=0
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.project(c)
    def test_artwork_parity_finding_never_disappears(self):
        c=self.scene();c[3]['schematic_parity'].append({'type':'extra_footprint','severity':'warning','items':[{'uuid':c[2]['footprints'][1]['uuid']}]})
        before=copy.deepcopy(c)
        with self.assertRaises(ValueError):self.project(c)
        self.assertEqual(c,before)
    def test_unmatched_schematic_terminal_and_hidden_custom_fields_still_reject(self):
        from autorouter import sexpr as sx
        for mode in ('missing_component','custom_field'):
            c=self.scene()
            if mode=='missing_component':
                tree=sx.parse(c[1]);dup=copy.deepcopy(sx.one(tree,'components')[1]);sx.one(dup,'ref')[1]='"D2"';sx.one(tree,'components').append(dup);c=(c[0],sx.dump(tree),c[2],c[3])
            else:c[2]['footprints'][0]['fields']['LCSC Part #']='CHANGED'
            projected,_=self.project(c)
            with self.subTest(mode=mode),self.assertRaises(ValueError):policy.derive(c[1],projected,c[3])
    def test_deleted_complete_artwork_observation_cannot_skip_source_census(self):
        c=self.scene();c[2]['footprints'].pop()
        with self.assertRaisesRegex(ValueError,'complete source/Native footprint census'):self.project(c)

    def test_no_artwork_keeps_original_observer_and_proof_contract(self):
        tree,obs,report=scene()
        board=policy.sx.parse('(kicad_pcb (footprint "Library:LED" (uuid 00000000-0000-0000-0000-000000000001) (property "Reference" "D1")))')
        projected,proof=evidence.project_board_only_fields(board,policy.sx.dump(tree),obs,report)
        self.assertIs(projected,obs);self.assertIsNone(proof)
        self.assertEqual(policy.derive(policy.sx.dump(tree),projected,report),prove((tree,obs,report)))

if __name__=='__main__':unittest.main()
