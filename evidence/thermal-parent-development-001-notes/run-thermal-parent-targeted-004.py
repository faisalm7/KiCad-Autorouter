from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
names=['tests.test_thermal_parent','tests.test_selected_native_scope','tests.test_recovery','tests.test_thermal','tests.test_named_edge_parent','tests.test_validation_readback']
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
result=unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
