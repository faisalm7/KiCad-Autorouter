"""Actual self-signal through installer main/publication; install work is stubbed.
No native, engine, Git, clone, venv, installation, network or external process is launched.
"""
from pathlib import Path
import importlib.util,json,os,signal,sys
from unittest import mock
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
script=HERE/'snapshot-003/scripts/install_smoke.py';spec=importlib.util.spec_from_file_location('signal_install',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
name=sys.argv[1];sig=getattr(signal,name);base=HERE/('signal-'+name);base.mkdir(exist_ok=False);source=base/'source';(source/'.runs').mkdir(parents=True);out=source/'.runs/result';prior={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
def fake_install(output,guidance):
 output.mkdir();report={'status':'passed','passed':True,'scope':'synthetic publication control, not an installation'}
 def writer(path,data):
  m.p.save_json(path,data)
  if data['passed']:os.kill(os.getpid(),sig)
 m.publish_result(output,report,lambda:None,lambda:None,writer)
 return 0 if report['passed'] else 2
with mock.patch.object(m.c,'ROOT',source),mock.patch.object(m,'install_test',side_effect=fake_install),mock.patch.object(m.sys,'argv',[str(script),'--output',str(out),'--guidance','placement-clearance-v1']):code=m.main()
result=m.read_json(out/'result.json');restored=all(signal.getsignal(s)==h for s,h in prior.items());passed=code==2 and result['passed'] is False and result['status']=='cancelled' and restored and (out/'result.json.invalidated-0').exists()
record={'scope':'real self signal through scoped main handlers, all installation work stubbed','signal':name,'exit_code':code,'canonical_status':result['status'],'canonical_passed':result['passed'],'handlers_restored':restored,'old_positive_preserved':(out/'result.json.invalidated-0').exists(),'passed':passed,'native_jobs':0,'engine_jobs':0,'git_jobs':0,'install_jobs':0};(base/'review.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(0 if passed else 1)
