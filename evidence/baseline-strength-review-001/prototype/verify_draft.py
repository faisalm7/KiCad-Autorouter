"""Load ignored proposal modules in this process only; no tracked edits/native jobs."""
import importlib.util
from pathlib import Path
import sys
import unittest

DRAFT=Path(__file__).resolve().parent
ROOT=next(parent for parent in DRAFT.parents if (parent/'AGENTS.md').is_file())
sys.path.insert(0,str(ROOT))
import autorouter
import scripts

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

autorouter.pipeline=load('autorouter.pipeline',DRAFT/'autorouter/pipeline.py')
scripts.experiment_portfolio=load('scripts.experiment_portfolio',DRAFT/'scripts/experiment_portfolio.py')
controls=load('portfolio_controls',DRAFT/'tests/test_portfolio.py')
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(controls))
raise SystemExit(0 if result.wasSuccessful() else 1)
