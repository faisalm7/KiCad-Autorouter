"""Existing synthetic full-receipt fixture, with only scratch location redirected."""
from pathlib import Path
import sys,json,hashlib
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref,config as c
HERE=Path(__file__).resolve().parent;OUT=HERE/sys.argv[1];OUT.mkdir(exist_ok=False)
source=(ROOT/'tests/test_result.py').read_text()
source=source.replace('scratch = ROOT / ".cache" / "result-tests"','scratch = REVIEW_SCRATCH')
ns={'__file__':str(ROOT/'tests/test_result.py'),'__name__':'existing_receipt_fixture','REVIEW_SCRATCH':OUT}
exec(compile(source,'<existing-test-result-only-scratch-redirect>','exec'),ns)
rows=[]
for mutation in (None,'snapshot','receipt'):
    case=ns['ResultFreshnessTests']();case.setUp();case.temp._finalizer.detach()
    captured=None;request={'captured':None,'snapshot':pref.snapshot(),'effective':pref.resolve()};p.capture_preferences(case.data,case.run,request)
    case.data.update(adapter='none',engine_profile='standard',scoring_variant=None)
    settings=p.engine_profile_settings('standard',100);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
    argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(c.JAR),'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(case.run/'engine-config'),'--logging.file.enabled=false',*settings['argv'],'-de',str(case.run/'task.dsn'),'-do',str(case.run/'routes.ses')]
    process={'name':'engine','status':'success','exit_code':0,'cleanup_complete':True,'argv':argv,'cwd':str(case.run),'wall_seconds':0,'cpu_seconds':0,'monitor_cpu_seconds':0}
    case.data.update(engine_budget=settings);case.data['steps'].insert(0,process);(case.run/'engine-process.json').write_text(json.dumps(process));case.save_receipt()
    original=p.tree_hash;trigger=[]
    def inventory(path):
        value=original(path)
        if mutation and Path(path)==case.run/'code' and not trigger:
            trigger.append(True)
            target=case.run/('routing-preferences.json' if mutation=='snapshot' else 'result.json')
            if mutation=='snapshot':target.write_bytes(target.read_bytes()+b' ')
            else:
                changed=json.loads(target.read_text());changed['engine_profile']='tuned';target.write_text(json.dumps(changed))
        return value
    with patch.object(p,'tree_hash',inventory):
        try:value=p.check_result(case.receipt);outcome={'current':value['current']}
        except Exception as exc:outcome={'current':False,'error':type(exc).__name__+': '+str(exc)}
    rows.append({'mutation':mutation,'triggered':bool(trigger),'root':str(case.root),**outcome})
report={'scope':'Existing synthetic receipt control, all actual consistency checks; no native claim','pipeline_sha256':hashlib.sha256((ROOT/'autorouter/pipeline.py').read_bytes()).hexdigest(),'rows':rows}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
