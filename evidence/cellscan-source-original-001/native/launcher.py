from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.original_project_native_v1.driver import main
sys.argv=[str(ROOT/'experiments/original_project_native_v1/driver.py'),'--project','cellscan','--output',str(ROOT/'.runs/cellscan-original-native-001'),'--run-native']
raise SystemExit(main())
