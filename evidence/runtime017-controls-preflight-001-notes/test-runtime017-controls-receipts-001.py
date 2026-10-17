"""Reuse the five production raw-receipt regressions for the controls enclosure."""
from pathlib import Path
import importlib.util,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
existing=load('existing017receiptcontrols',ROOT/'.runs/test-runtime017-production-receipts-001.py')
module=load('controls017enclosure',ROOT/'.runs/run-runtime017-controls-001.py')
module.shared_helpers=lambda:module.production_helper().shared_helpers()
existing.m=module
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(existing.ReceiptControls))
raise SystemExit(0 if result.wasSuccessful()else 2)
