"""Authored import/refill context controls; no Native workers are executed."""
from pathlib import Path
import unittest
from autorouter import pipeline as p,floor_route as f,adapter,placement_clearance as pc
from tests import test_native_parser_context as parser_fixture
from tests import test_normal_selected_import as import_fixture

class NativeImportToolchain(unittest.TestCase):
    setUp=parser_fixture.ExplicitParserContextControls.setUp
    author_context=parser_fixture.ExplicitParserContextControls.author_context
    make=import_fixture.NormalSelectedImportControls.make

    def explicit(self):
        root,data,original,candidate,_=self.make(selected=False)
        self.author_context(root,data)
        report=f.read_json(root/'refill-drc.json');report['kicad_version']='10.0.7';p.save_json(root/'refill-drc.json',report)
        imports=adapter.check_fixed_placement_import(root,data,pc.inventory(root),native_toolchain=self.nt)
        return root,data,original,candidate,imports

    def test_explicit_direct_import_passes_context_to_real_saved_stage_reader(self):
        root,data,original,candidate,imports=self.explicit()
        before=pc.inventory(root)
        self.assertEqual(p.normal_import_contract(root,data,imports,input_policy='native',original=original,native_toolchain=self.nt),{})
        self.assertEqual(pc.inventory(root),before)
        with self.assertRaises(p.Rejected):p.normal_import_contract(root,data,imports,input_policy='native',original=original)

    def test_explicit_context_does_not_waive_saved_worker_or_refill_bytes(self):
        root,data,original,candidate,imports=self.explicit()
        binding=f.read_json(root/'refill-drc-binding.json');binding.pop('experimental_native_toolchain');p.save_json(root/'refill-drc-binding.json',binding)
        with self.assertRaises(p.Rejected):p.normal_import_contract(root,data,imports,input_policy='native',original=original,native_toolchain=self.nt)

if __name__=='__main__':unittest.main()
