from pathlib import Path
import sys,unittest,os
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));os.chdir(R);sys.dont_write_bytecode=True
s=unittest.defaultTestLoader.loadTestsFromNames(['tests.test_chain_proposals','tests.test_strategy'])
r=unittest.TextTestRunner(verbosity=2).run(s);raise SystemExit(0 if r.wasSuccessful() else 1)
