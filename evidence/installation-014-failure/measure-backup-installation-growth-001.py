from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from scripts import backup as b
actual=b.inventory(ROOT)
new=ROOT/'.runs/installation-014'
files=[p for p in new.rglob('*') if p.is_file()]
row={'current_non_git_files':len(actual['files']),'current_non_git_bytes':actual['total_file_bytes'],'current_directories':len(actual['directories']),'completed_installation014_files':len(files),'completed_installation014_bytes':sum(p.stat().st_size for p in files),'forecast_one_new_installation_upper_extra_files':17500,'forecast_one_new_installation_upper_extra_bytes':420*1024**2,'current_caps':{'files':b.MAX_FILES,'bytes':b.LIMIT}}
row['forecast_files']=row['current_non_git_files']+row['forecast_one_new_installation_upper_extra_files'];row['forecast_bytes']=row['current_non_git_bytes']+row['forecast_one_new_installation_upper_extra_bytes']
(ROOT/'.runs/backup-installation-growth-001.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row))
