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
            with patch.object(evidence,'readback',return_value=None),patch('autorouter.floor_route.read_json',side_effect=read),patch('autorouter.floor_route.process_check') as check:
                with self.assertRaisesRegex(p.Rejected,'actual complete native schematic parity'):
                    evidence.check_processes(folder,data,'final-drc',board,sandboxed=True)
                check.assert_not_called()
                data['steps'][0]['argv'].append('--schematic-parity')
                evidence.check_processes(folder,data,'final-drc',board,sandboxed=True)
                self.assertEqual([call.args[2] for call in check.call_args_list],list(evidence.names('final-drc')))

if __name__=='__main__':unittest.main()
