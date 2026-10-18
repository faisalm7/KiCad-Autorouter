from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter.runner import run
out=ROOT/'.runs/comparison-delivery-existing-targeted-001';out.mkdir()
modules=['tests.test_handoff','tests.test_review_view','tests.test_review_export','tests.test_experimental_delivery','tests.test_comparison_context']
code="import sys,unittest;sys.path.insert(0,"+repr(str(ROOT))+");unittest.main(module=None,argv="+repr(['unittest',*modules])+")"
process=run([str(ROOT/'.venv/bin/python'),'-B','-c',code],cwd=out,log=out/'command.log',timeout=240,max_log_bytes=512*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
(out/'process.json').write_text(json.dumps(process,indent=2)+'\n')
print(json.dumps({k:process.get(k) for k in ('status','exit_code','cleanup_complete','wall_seconds','cpu_seconds')}))
raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True else 2)
