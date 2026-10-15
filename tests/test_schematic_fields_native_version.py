"""Prospective pure version controls; no Native/API qualification is claimed."""
import copy,importlib.util,itertools,sys,unittest
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from tests import test_schematic_fields as fixture
from autorouter import schematic_fields as m


def scene(exporter='10.0.0',observer='10.0.0',report='10.0.0'):
    # Only authored synthetic metadata is selected here. No retained report,
    # native observation or source data is rewritten or normalized.
    data=fixture.scene()
    m.sx.one(m.sx.one(data[0],'design'),'tool')[1]='"Eeschema '+exporter+'"'
    data[1]['native_version']=observer;data[2]['kicad_version']=report
    return data


def derive(data,**kwargs):
    return m.derive(m.sx.dump(data[0]),data[1],data[2],**kwargs)


class ExplicitNativeVersionControls(unittest.TestCase):
    def test_default1000_proof_and_warning_schema_stays_literal(self):
        data=scene();before=copy.deepcopy(data)
        proof=derive(data)
        self.assertEqual(proof,fixture.prove(copy.deepcopy(data)))
        self.assertEqual(proof,derive(data,native_version='10.0.0'))
        self.assertEqual(data,before);self.assertTrue(m.qualified(proof,data[2]['schematic_parity']))
        self.assertEqual(m.components(m.sx.dump(data[0]),data[1]),m.components(m.sx.dump(data[0]),data[1],native_version='10.0.0'))

    def test_explicit1007_synthetic_scene_passes_without_mutation_or_schema_change(self):
        data=scene('10.0.7','10.0.7','10.0.7');before=copy.deepcopy(data)
        proof=derive(data,native_version='10.0.7');old=derive(scene())
        self.assertTrue(proof['qualified']);self.assertTrue(m.qualified(proof,data[2]['schematic_parity']))
        self.assertEqual(set(proof),set(old));self.assertEqual(proof['comparison_map'],old['comparison_map'])
        self.assertEqual(proof['warning_hashes'],old['warning_hashes']);self.assertEqual(proof['warning_uuids'],old['warning_uuids'])
        self.assertEqual(data,before)
        self.assertEqual(m.components(m.sx.dump(data[0]),data[1],native_version='10.0.7'),{'D1':{'Datasheet':'','Description':'LED','LCSC Part #':'C123'}})

    def test_default_refuses1007_without_inference_from_any_observed_identity(self):
        for identities in itertools.product(('10.0.0','10.0.7'),repeat=3):
            if identities==('10.0.0',)*3:continue
            data=scene(*identities)
            with self.subTest(identities=identities),self.assertRaises(ValueError):derive(data)
        data=scene('10.0.7','10.0.7','10.0.7')
        with self.assertRaisesRegex(ValueError,'exporter identity'):m.components(m.sx.dump(data[0]),data[1])

    def test_mixed_exporter_observer_report_rejected_for_both_explicit_versions(self):
        for expected in ('10.0.0','10.0.7'):
            for identities in itertools.product(('10.0.0','10.0.7'),repeat=3):
                if identities==(expected,)*3:continue
                data=scene(*identities)
                with self.subTest(expected=expected,identities=identities),self.assertRaises(ValueError):derive(data,native_version=expected)

    def test_expected_version_is_keyword_only_exact_string_and_allowlisted(self):
        class Alias(str):pass
        data=scene()
        for version in (None,True,False,1007,10.007,b'10.0.7',[],{},Alias('10.0.7'),'','10.0.8','10.0.7 ','10.0.0-dev','10.0'):
            with self.subTest(version=repr(version)):
                with self.assertRaisesRegex(ValueError,'expected native version'):derive(data,native_version=version)
                with self.assertRaisesRegex(ValueError,'expected native version'):m.components(m.sx.dump(data[0]),data[1],native_version=version)
        with self.assertRaises(TypeError):m.derive(m.sx.dump(data[0]),data[1],data[2],'10.0.0')
        with self.assertRaises(TypeError):m.components(m.sx.dump(data[0]),data[1],'10.0.0')

    def test_observer_and_exporter_report_spelling_never_normalized(self):
        for where in range(3):
            for value in ('10.0.7 ','v10.0.7','10.0.7-dev','10.0.7 build-metadata','10.0.70'):
                identities=['10.0.7']*3;identities[where]=value;data=scene(*identities)
                with self.subTest(where=where,value=value),self.assertRaises(ValueError):derive(data,native_version='10.0.7')
        # Preserve the already existing1000 observer build-suffix contract.
        data=scene(observer='10.0.0 retained-build')
        self.assertEqual(derive(data),fixture.prove(copy.deepcopy(data)))

    def test_hidden_later_field_still_rejects_with_unchanged_first1007_warning(self):
        for kind in ('pcb_changed','pcb_missing','schematic_changed','description_changed'):
            data=scene('10.0.7','10.0.7','10.0.7');warning=copy.deepcopy(data[2]['schematic_parity'])
            if kind=='pcb_changed':data[1]['footprints'][0]['fields']['LCSC Part #']='DIFFERENT'
            elif kind=='pcb_missing':del data[1]['footprints'][0]['fields']['LCSC Part #']
            elif kind=='schematic_changed':fixture.schfield(data,'LCSC Part #')[2]='"DIFFERENT"'
            else:data[1]['footprints'][0]['fields']['Description']='DIFFERENT'
            self.assertEqual(data[2]['schematic_parity'],warning)
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'field'):derive(data,native_version='10.0.7')


if __name__=='__main__':unittest.main()
