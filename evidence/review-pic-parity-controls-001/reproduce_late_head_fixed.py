"""Owned actual-file lifecycle counterexample; native, Git and metadata operations mocked."""
from pathlib import Path
from unittest import mock
import copy,hashlib,json,shutil,sys
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE/'source-002'))
import driver as d,fixture as fx,checks
from test_controls import raw,log
OUT=HERE/'late-head-002'
OUT.mkdir()
results=[]
for variant in ('unchanged','late_original_project'):
 case=OUT/variant;case.mkdir();source=case/'source';shutil.copytree(d.SOURCE.parent,source)
 target=source/fx.BOARD;out=case/'run'
 initial=d.inventory(source);total=d.size(source)
 real_owned=d.owned;real_save=d.p.save_json;runtime={'git_head':'a'*40,'implementation_sha256':{},'files':{}}
 witness={'head':'a'*40,'HEAD_sha256':'b'*64,'ref_sha256':'c'*64};late=[0];mutated=[False]
 def owned(path,output=False):
  if output:
   if Path(path).exists():raise d.p.Rejected('fresh output')
   return Path(path)
  return real_owned(path)
 def snapshot(path,*_):
  (path/'code').mkdir();(path/'code/marker').write_text('frozen');return {}
 def head():
  if (out/'summary.json').exists():
   late[0]+=1
   if variant=='late_original_project'and late[0]==2:
    path=source/'pic_programmer.kicad_pro';value=json.loads(path.read_bytes());value['board']['design_settings']['rule_severities']['footprint_symbol_field_mismatch']='ignore';path.write_text(json.dumps(value));mutated[0]=True
  return witness
 def worker(argv,*,cwd,log:Path,**kwargs):
  data=raw(cwd.name);real_save(cwd/'parity-drc.json',data);log.write_text(globals()['log'](data))
  return {'argv':argv,'cwd':str(cwd),'log':str(log),'log_bytes':log.stat().st_size,'log_truncated':False,'exit_code':5,'status':'nonzero_exit','cleanup_complete':True,'cpu_seconds':.01,'monitor_cpu_seconds':0,'wall_seconds':.01,'pid':999,'sampled_peak_group_rss_bytes':1000,'sampled_peak_workdir_bytes':1000,'resource_guards':{'max_group_rss_bytes':2*1024**3,'max_workdir_bytes':d.LIMIT,'os_enforced':False}}
 with mock.patch.object(d,'SOURCE',target),mock.patch.object(d,'source_binding',return_value=(initial,total)),mock.patch.object(d,'owned',owned),mock.patch.object(d,'snapshot',snapshot),mock.patch.object(d,'head_witness',side_effect=head),mock.patch.object(d.p,'tool_manifest',return_value=runtime),mock.patch.object(d.p,'check_storage'),mock.patch.object(d,'run',worker):
  record=d.experiment(out,run_native=True)
 canonical=d.read(out/'summary.json')
 results.append({'variant':variant,'source_mutated':mutated[0],'source_equals_initial':d.inventory(source)==initial,'post_write_head_calls':late[0],'status':record['status'],'returned_controls_passed':record['controls_passed'],'canonical_controls_passed':canonical['controls_passed'],'error':record.get('error')})
report={'scope':'actual owned project and output files, mocked native and committed-source metadata; no native/Git/network','driver_sha256':hashlib.sha256((HERE/'source-001/driver.py').read_bytes()).hexdigest(),'results':results}
(HERE/'late-head-reproduction-002.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
