"""Pure synthetic source tests. No acquired payload/network/native use."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).absolute().parent
spec=importlib.util.spec_from_file_location('closure_audit',HERE/'audit.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
BOARD=b'''(kicad_pcb(version 20250101)(generator pcbnew)(layers(0 "F.Cu" signal)(31 "B.Cu" signal))
(footprint "Local:Part"(layer "F.Cu")(pad "1" smd custom(at 0 0)(size .3 .3)(net "NET")(primitives(gr_poly(pts(xy 0 0)(xy 1 0)(xy 0 1)))))(model "${KIPRJMOD}/models/a.step"))
(zone(net 1)(net_name "NET")(keepout(tracks allowed)(vias allowed))(placement(enabled yes)))
(segment(start 0 0)(end 1 1)(width .5)(layer "F.Cu")(net "NET")(locked yes)))'''

class Controls(unittest.TestCase):
    def test_plan_only_metadata(self):
        plan,baseline=a.plan();self.assertEqual(len(plan['projects']),3);self.assertEqual(baseline['file_count'],312)
    def test_modern_board_constraints_preserved_as_observations(self):
        row=a.inspect_native('Hardware/x.kicad_pcb',BOARD,{'Hardware/models/a.step'})
        o=row['observed'];self.assertEqual(o['pad_shapes'],{'custom':1});self.assertEqual(len(o['copper_layers']),2)
        self.assertEqual(o['locked_route_count'],1);self.assertEqual(o['zones'][0]['keepout'][0][1],['tracks','allowed'])
        self.assertEqual(row['references'][-1]['resolution'],'local_file_present')
    def test_legacy_project_separate(self):
        x=a.inspect_native('x.pro',b'[eeschema/libraries]\nLibName1=original\n',set())
        self.assertEqual(x['syntax'],'legacy_project_ini');self.assertFalse(x['observed']['native_migration_performed']);self.assertEqual(x['references'][0]['resolution'],'unresolved')
    def test_legacy_schematic_references(self):
        x=a.inspect_native('x.sch',b'EESchema Schematic File Version 2\nLIBS:device\n$Comp\nL R R1\nF 2 "Vendor:Part"\n$EndComp\n',set())
        self.assertEqual(x['observed']['component_count'],1);self.assertEqual(len(x['references']),3)
    def test_modern_project_keeps_original_severities(self):
        x=a.inspect_native('x.kicad_pro',b'{"board":{"design_settings":{"rule_severities":{"clearance":"error","something":"ignore"}}},"net_settings":{"classes":[]}}',set())
        self.assertEqual(x['observed']['design_settings']['rule_severities']['something'],'ignore')
    def test_reference_no_external_follow(self):
        for value in ('${KICAD9_3DMODEL_DIR}/x.step','../../escape.step','/private/x.step','https://vendor.invalid/x.step','C:\\model.step'):
            with self.subTest(value=value):self.assertEqual(a.reference(value,'model','x.kicad_pcb',set(),'.')['resolution'],'unresolved')
    def test_reference_case_preserved(self):
        r=a.reference('models/A.step','model','x.kicad_pcb',{'models/a.step'},'.');self.assertEqual(r['resolution'],'unresolved');self.assertEqual(r['target'],'models/A.step')
    def test_identifier_is_not_embedded_closure(self):
        r=a.reference('Vendor:Part','footprint_identifier','x.kicad_pcb',{'Part.kicad_mod'},'.');self.assertEqual(r['resolution'],'unresolved')
    def test_authentic_local_table_member(self):
        available={'Hardware/fp-lib-table':b'(fp_lib_table(lib(name "Local")(type "KiCad")(uri "${KIPRJMOD}/Local.pretty")))','Hardware/Local.pretty/Part.kicad_mod':b'(footprint "Part")'}
        analysis=a.inspect_native('Hardware/fp-lib-table',available['Hardware/fp-lib-table'],set(available));refs=[a.reference('Local:Part','footprint_identifier','Hardware/x.kicad_pcb',set(available),'Hardware')]
        a.resolve_local_identifiers(refs,[analysis],available);self.assertEqual(refs[0]['resolution'],'explicit_local_member_present')
    def test_table_duplicate_alias_not_resolved(self):
        refs=[a.reference('Local:Part','footprint_identifier','x.kicad_pcb',set(),'.')]
        a.resolve_local_identifiers(refs,[{'file':'fp-lib-table','observed':{'table_entries':[{'name':'Local','uri':'x'},{'name':'Local','uri':'y'}]}}],{})
        self.assertEqual(refs[0]['resolution'],'unresolved')
    def test_project_and_board_missing_retained(self):
        project=a.plan()[0]['projects'][0];x=a.analyze_project(project,{},project['files']);self.assertEqual(len(x['boards']),1);self.assertEqual(x['boards'][0]['acquisition_state'],'missing_or_invalid');self.assertFalse(x['dependency_closure_verified'])
    def test_parse_failure_retained(self):
        project=a.plan()[0]['projects'][0];board=next(r['source_path']for r in project['files']if r['source_path'].endswith('.kicad_pcb'));x=a.analyze_project(project,{board:b'(malformed'},project['files'])
        self.assertIn('ValueError',x['boards'][0]['board_syntax_observation']['parse_error']);self.assertFalse(x['routing_accepted'])
    def test_root_grant_not_model_rights(self):
        x=a.notices('a.step',b"ISO-10303-21;\nHEADER;\nFILE_NAME('a','time',('unknown author'),('vendor'),'exporter','system','');\nFILE_SCHEMA(('AP214'));\nENDSEC;",'CC-BY-SA-4.0',[{'path':'LICENSE','sha256':'0'*64}])
        self.assertTrue(x['model_header']['FILE_NAME']);self.assertFalse(x['redistribution_approved']);self.assertIn('unresolved',x['model_authorship_or_vendor_rights'])
    def test_per_file_rights_exception_retained(self):
        x=a.notices('asset.step',b'Copyright Vendor\nAll Rights Reserved\n','Apache-2.0',[])
        self.assertEqual(len(x['notice_matches']),2);self.assertFalse(x['redistribution_approved'])
    def test_binary_not_falsely_inspected(self):
        x=a.notices('bom.ods',b'PK\x00data','Apache-2.0',[]);self.assertTrue(x['binary_document_not_parsed'])
    def test_blob_receipt_both_verified(self):
        raw=b'data';row={'bytes':4,'git_blob_sha1':hashlib.sha1(b'blob 4\0data').hexdigest(),'destination':'slug/a','repository':'r/x','commit':'0'*40,'mode':'100644','source_path':'a','sha256':None};receipt={**row,'sha256':a.sha(raw)}
        a.verify_file(row,raw,receipt)
        with self.assertRaises(ValueError):a.verify_file(row,b'evil',receipt)
        receipt['commit']='1'*40
        with self.assertRaises(ValueError):a.verify_file(row,raw,receipt)
    def test_strict_json(self):
        for raw in (b'{"x":0,"x":1}',b'{"x":NaN}'):
            with self.assertRaises(ValueError):a.decode(raw)
    def test_inventory_symlink_refuses(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='pure-')as td:
            root=Path(td);(root/'a').write_bytes(b'x');(root/'link').symlink_to(root/'a')
            with self.assertRaises(ValueError):a.inventory(root)

if __name__=='__main__':unittest.main(verbosity=2)
