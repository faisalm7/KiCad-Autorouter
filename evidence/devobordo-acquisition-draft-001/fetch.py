"""Fixed devobordo v3 profile for the existing bounded controller."""
from pathlib import Path
import sys
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as shared
if __name__=='__main__':shared.main('v3',HERE)
