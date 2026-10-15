"""Run the actual product CLI from an owned experiment working directory."""
from pathlib import Path
import sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter.__main__ import main
if __name__=='__main__':raise SystemExit(main())
