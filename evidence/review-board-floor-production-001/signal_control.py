"""Real self-SIGTERM through public floor wrapper, mocked work; no native jobs."""
from pathlib import Path
import json,os,signal,sys
from unittest.mock import patch
here=Path(__file__).resolve().parent;sys.path.insert(0,str(here/'snapshot-003'))
from autorouter import floor_route as f,pipeline as p
out=here/'real-sigterm-003';out.mkdir(exist_ok=False)
previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
def work(source,directory,seconds,profile):
    report={'accepted':True,'status':'routing_accepted','whole_project_drc_clean':True}
    return f.publish(out,report,lambda:None,lambda:None,lambda:100)
def final_check(path):os.kill(os.getpid(),signal.SIGTERM)
with patch.object(f,'_route',side_effect=work),patch.object(p,'check_result',side_effect=final_check):
    result=f.route('synthetic-unused-source',out,120,False,'both','standard',None)
restored=all(signal.getsignal(sig)==handler for sig,handler in previous.items())
canonical=json.loads((out/'result.json').read_text())
assert result['accepted'] is False and canonical['accepted'] is False and canonical['status']=='cancelled' and restored
print(json.dumps({'scope':'Actual bounded self-SIGTERM; native/routing stages mocked; public cancellation wrapper and real file publication used','accepted':canonical['accepted'],'status':canonical['status'],'handlers_restored':restored,'canonical_receipt':str(out/'result.json'),'archived_previous_positive':len(list(out.glob('invalidated-result-*')))},indent=2))
