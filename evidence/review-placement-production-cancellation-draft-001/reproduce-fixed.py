"""Synthetic final-publication reproduction; no subprocess/native/engine launch."""
from pathlib import Path
import importlib.util,json,signal,types,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]))
spec=importlib.util.spec_from_file_location('cancel_review_snapshot',HERE/'after-fix.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
out=HERE/'mock-output-fixed'
class Child:
 pid=100
 returncode=None
 def poll(self):return self.returncode
child=Child()
def launch(*args,**kwargs):
 (out/'route').mkdir()
 (out/'route/engine.log').write_text('synthetic engine startup')
 return child
def kill(pid,signum):
 assert pid==100
 child.returncode=2
 (out/'route/result.json').write_text(json.dumps({'schema':3,'input_policy':'placement-clearance-v1','accepted':False,'status':'cancelled'}))
 (out/'route/engine-process.json').write_text(json.dumps({'pid':200,'status':'cancelled','cancel_signal':signal.Signals(signum).name,'cleanup_complete':True}))
def metadata():return [{'pid':200,'ppid':100,'pgid':200}] if child.returncode is None else []
def git(argv,**kwargs):
 assert argv[:2]==['git','show']
 return types.SimpleNamespace(stdout=(d.c.ROOT/argv[2].split(':',1)[1]).read_bytes())
real_save=d.p.save_json
def writer(path,value):
 real_save(path,value)
 if value.get('passed') is True:raise KeyboardInterrupt('synthetic after-write cancellation')
escaped=False
with patch.object(d.subprocess,'run',git),patch.object(d.subprocess,'Popen',launch),patch.object(d.os,'kill',kill),patch.object(d,'process_metadata',metadata),patch.object(d.p,'check_storage',return_value=0),patch.object(d.p,'tree_hash',return_value={'source':'unchanged'}),patch.object(d.p,'tool_manifest',return_value={'tools':'unchanged'}),patch.object(d.p,'save_json',writer):
 try:d.control(out,signal.SIGTERM)
 except KeyboardInterrupt:escaped=True
value=json.loads((out/'control.json').read_text())
result={'mocked_process_only':True,'native_executed':False,'engine_executed':False,'subprocess_executed':False,'interrupt_escaped':escaped,'canonical_passed_after_interrupt':value['passed'],'canonical_status':value['status']}
(HERE/'reproduction-fixed.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert not escaped and value['passed'] is False and value['status']=='cancelled'
