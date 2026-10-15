from pathlib import Path
import os,sys,unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));os.chdir(R)
s=unittest.defaultTestLoader.loadTestsFromNames(["tests.test_native_component_normalization","tests.test_native_component_fixtures","tests.test_native_component_delivery"])
r=unittest.TextTestRunner(verbosity=2).run(s)
raise SystemExit(0 if r.wasSuccessful() else 1)
