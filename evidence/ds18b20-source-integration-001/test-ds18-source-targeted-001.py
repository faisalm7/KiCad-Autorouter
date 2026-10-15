from pathlib import Path
import os,sys,unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));os.chdir(R)
suite=unittest.defaultTestLoader.loadTestsFromNames(["tests.test_led_demo_fetch","tests.test_experiment_quality"])
r=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if r.wasSuccessful() else 1)
