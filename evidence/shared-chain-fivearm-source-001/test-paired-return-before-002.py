from pathlib import Path
import sys,unittest,importlib.util
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R),str(R/'tests')];sys.dont_write_bytecode=True
import test_paired
source=R/'.runs/paired-return-before-001/experiment_paired.py'
spec=importlib.util.spec_from_file_location('paired_original_return',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);test_paired.m=module
suite=unittest.TestSuite([test_paired.PairedControls('test_final_sample_return_matches_stored_after_successful_publication_cost')]);result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(0 if result.wasSuccessful() else 1)
