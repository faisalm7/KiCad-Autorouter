from pathlib import Path
import sys,unittest,os
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R),str(R/'tests')];sys.dont_write_bytecode=True;os.chdir(R)
names=['test_paired','test_backup','test_backup_incremental','test_backup_capacity','test_backup_file_capacity'];suite=unittest.defaultTestLoader.loadTestsFromNames(names);result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(0 if result.wasSuccessful() else 1)
