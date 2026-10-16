"""Same bounded source-only builder smoke on the newly restored source."""
from pathlib import Path
import sys,json,os,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter.runner import run
restored=ROOT/'.local-backups/restore-f8ae3193763d47e1871287a25e74c589'
out=restored/'runtime-build-smoke-001';out.mkdir()
argv=[str(ROOT/'.venv/bin/python'),'-B',str(restored/'checkout/scripts/prepare_runtime.py'),'--output',str(out/'runtime-source-only')]
process=run(argv,cwd=out,log=out/'command.log',timeout=30,max_log_bytes=128*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=16*1024**2,env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME'}})
manifest=out/'runtime-source-only/runtime-distribution.json';data=json.loads(manifest.read_bytes())if manifest.exists()else{}
record={'schema':1,'passed':process['status']=='success'and process['exit_code']==0 and process['cleanup_complete']is True and process['log_truncated']is False,'source_only':True,'native_or_JVM':False,'actual_restored_source_executed':True,'process':process,'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()if manifest.exists()else None,'manifest':data}
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'passed':record['passed'],'manifest_fields':list(data)}));raise SystemExit(0 if record['passed'] else 2)
