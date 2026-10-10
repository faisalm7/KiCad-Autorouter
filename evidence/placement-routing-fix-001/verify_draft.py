"""Run the actual candidate pure module against promotable tests; no native calls."""
import importlib.util,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import test_board_floor_empty_area as cases
spec=importlib.util.spec_from_file_location('autorouter._floor_empty_area_draft',HERE/'board_floor.py')
candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
cases.g=candidate
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(cases))
raise SystemExit(0 if result.wasSuccessful() else 1)
