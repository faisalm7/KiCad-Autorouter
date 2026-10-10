"""Deliver signals only to this short-lived review Python process; all stages mocked."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,os,signal,sys
from unittest import mock
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
script=BASE/'snapshot-003/driver.py'
spec=importlib.util.spec_from_file_location('lipo_signal_review',script);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
rows=[]
for name in ('SIGINT','SIGTERM'):
    signum=getattr(signal,name);base=BASE/('signal-'+name.lower());base.mkdir();(base/'.runs').mkdir();out=base/'.runs/output'
    before={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    original_save=d.p.save_json
    def writer(path,value):
        original_save(path,value)
        if value.get('observations_complete') is True:os.kill(os.getpid(),signum)
    def fake_experiment(path,*,run_native):
        assert run_native is True
        path.mkdir()
        record={'status':'observations_complete','observations_complete':True,'routing_accepted':False,'format_support_qualified':False,
                'scope':'Synthetic self-signal publication control; native stages mocked and not run.'}
        return d.publish(path,record,lambda:None,lambda:None,lambda:1)
    with mock.patch.object(d,'ROOT',base),mock.patch.object(d,'experiment',side_effect=fake_experiment),mock.patch.object(d.p,'save_json',side_effect=writer),contextlib.redirect_stdout(io.StringIO()):
        code=d.main(['--output',str(out),'--run-native'])
    saved=d.read(out/'summary.json');restored=all(signal.getsignal(s)==h for s,h in before.items())
    rows.append({'signal':name,'signal_scope':'own review Python process only','exit_code':code,'status':saved['status'],'observations_complete':saved['observations_complete'],'handlers_restored':restored,'passed':code==2 and saved['status']=='cancelled' and saved['observations_complete'] is False and restored,'native_executed':False})
summary={'driver_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'rows':rows,'passed':all(r['passed'] for r in rows),'actual_native_processes':0}
(BASE/'signal-controls.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
