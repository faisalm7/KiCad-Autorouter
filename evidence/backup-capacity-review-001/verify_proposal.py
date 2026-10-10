"""Run only the candidate's bounded pure/small-file controls; never create/verify."""
import importlib.util,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'scripts/backup.py').is_file())
sys.dont_write_bytecode=True;sys.path[:0]=[str(HERE),str(ROOT)]
import test_backup_capacity as cases
spec=importlib.util.spec_from_file_location('capacity_candidate',HERE/'backup.py')
candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
cases.backup=candidate
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(cases))
raise SystemExit(0 if result.wasSuccessful() else 1)
