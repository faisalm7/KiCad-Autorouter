"""Pinned PAW3395 profile for the shared bounded acquisition controller."""
from pathlib import Path
import sys

HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(HERE.parents[1]))
from experiments.licensed_acquisition_v1 import fetch as shared

if __name__ == '__main__':
    shared.main('v2', HERE)
