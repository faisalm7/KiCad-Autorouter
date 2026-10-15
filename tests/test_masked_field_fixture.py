"""Owned source-byte controls only; Native field order remains an actual gate."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from autorouter import sexpr as sx
from experiments.native_schematic_toolchain_v1 import fixture

# Literal source maps from both actual002 versions, frozen before this change:
# .runs/native-schematic-hidden-followup-preparation-001/protocol.json
# SHA256 e1d2969b4ea454ce3e7182d8057ad619ea9cb1a87a22d1811ae9fbba8d291bcc.
# Native002's aggregate remains failed; the old custom negative is not masked.
COMMON = {
    'owned1007-fields.kicad_dru': '9984933809f1ec2a885a99383ebbb8eb81a79b1738146cb62835046e0720e2f7',
    'owned1007-fields.kicad_prl': '1c37c0bdd9e29701ef783238b372cb1380d8cfd64b48efc5ebbce69d872a743a',
    'owned1007-fields.kicad_pro': '4f61c448fbc38cd3d981f0d2ef5ad1111e2145f163bdb839f150803dc9436df0',
    'owned1007-fields.kicad_sch': '827dfc423d1951620844269aa41e53f90a31fc4ab6de8ecd69c5ca3d7e64d0c7',
}
FROZEN = {
    'positive': {**COMMON, 'owned1007-fields.kicad_pcb': '1ac170645e9b178a6528116301b239e1c4d13c0ddd046fac5b7a2854f4ae7f66'},
    'hidden_later_custom_field': {**COMMON, 'owned1007-fields.kicad_pcb': '5b5cdd17402462ae97a8b2cff3b88f2c17f8cb3190496df1f4326ad99ba5358d'},
}


def properties(footprint):
    rows=sx.children(footprint,'property')
    names=[sx.unquote(row[1]) for row in rows]
    if len(names)!=len(set(names)):
        raise AssertionError('unexpected duplicate fixture property')
    return {name:row for name,row in zip(names,rows)}


def footprints(tree):
    rows=sx.children(tree,'footprint')
    refs=[sx.unquote(properties(row)['Reference'][2]) for row in rows]
    if len(refs)!=len(set(refs)):
        raise AssertionError('unexpected duplicate fixture reference')
    return {ref:row for ref,row in zip(refs,rows)}


class MaskedDescriptionFixtureControls(unittest.TestCase):
    def test_legacy_population_and_all_five_file_bytes_match_frozen002_sources(self):
        self.assertEqual(fixture.CASES,('positive','hidden_later_custom_field'))
        self.assertEqual(fixture.MASKED_CASE,'hidden_later_description')
        self.assertNotIn(fixture.MASKED_CASE,fixture.CASES)
        for case,pins in FROZEN.items():
            with self.subTest(case=case):
                material=fixture.files(case)
                self.assertEqual({name:hashlib.sha256(raw).hexdigest() for name,raw in material.items()},pins)

    def test_only_j1_description_value_changes_in_bytes_and_complete_board_ast(self):
        positive=fixture.board('positive');negative=fixture.board(fixture.MASKED_CASE)
        old=json.dumps(fixture.DESCRIPTION).encode();new=json.dumps(fixture.MASKED_DESCRIPTION).encode()
        self.assertEqual(negative.count(new),1)
        self.assertEqual(negative.replace(new,old,1),positive)
        original=sx.parse(positive.decode());expected=copy.deepcopy(original)
        properties(footprints(expected)['J1'])['Description'][2]=json.dumps(fixture.MASKED_DESCRIPTION)
        self.assertEqual(sx.parse(negative.decode()),expected)
        props=properties(footprints(sx.parse(negative.decode()))['J1'])
        self.assertEqual(sx.unquote(props['Datasheet'][2]),'~')
        self.assertEqual(sx.unquote(props[fixture.FIELD][2]),fixture.MATCH)
        self.assertNotEqual(fixture.MASKED_DESCRIPTION,fixture.DESCRIPTION)

    def test_full_source_census_and_all_rules_schematic_local_settings_stay_exact(self):
        positive=fixture.files('positive');masked=fixture.files(fixture.MASKED_CASE)
        self.assertEqual(set(masked),set(FROZEN['positive']))
        for name,pin in COMMON.items():
            with self.subTest(name=name):
                self.assertEqual(masked[name],positive[name])
                self.assertEqual(hashlib.sha256(masked[name]).hexdigest(),pin)
        a=footprints(sx.parse(positive[fixture.STEM+'.kicad_pcb'].decode()))
        b=footprints(sx.parse(masked[fixture.STEM+'.kicad_pcb'].decode()))
        self.assertEqual(set(a),{'J1','J2','J3','J4'})
        for ref in ('J2','J3','J4'):
            self.assertEqual(a[ref],b[ref])

    def test_write_project_accepts_new_case_without_expanding_original_batch(self):
        with tempfile.TemporaryDirectory(prefix='owned-masked-field-') as name:
            root=Path(name).resolve();target=root/'masked'
            fixture.write_project(target,fixture.MASKED_CASE)
            self.assertEqual({path.name:path.read_bytes() for path in target.iterdir()},fixture.files(fixture.MASKED_CASE))
            batch=root/'legacy-batch';fixture.write(batch)
            self.assertEqual({path.name for path in batch.iterdir()},set(fixture.CASES))
            for case in fixture.CASES:
                self.assertEqual({path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in (batch/case).iterdir()},FROZEN[case])

    def test_unknown_case_still_refuses_before_creating_any_project(self):
        with tempfile.TemporaryDirectory(prefix='owned-masked-invalid-') as name:
            target=Path(name).resolve()/'uncreated'
            with self.assertRaises(ValueError):fixture.write_project(target,'not-a-declared-control')
            self.assertFalse(target.exists())


if __name__=='__main__':unittest.main()
