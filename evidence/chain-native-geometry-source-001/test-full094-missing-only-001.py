from pathlib import Path
import sys,os,unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));os.chdir(R);sys.dont_write_bytecode=True
s=unittest.defaultTestLoader.loadTestsFromNames(['tests.test_pruning_preferences_freshness.PruningPreferenceFreshness.test_late_publication_budget_expiry_invalidates','tests.test_pruning_preferences_freshness.PruningPreferenceFreshness.test_publication_preserves_positive_and_invalidates_each_late_mutation']);r=unittest.TextTestRunner(verbosity=2).run(s);raise SystemExit(0 if r.wasSuccessful() else 1)
