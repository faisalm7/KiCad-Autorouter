"""Independent exact-controller reproduction. All Git/compiler/import stages mocked."""
import copy,importlib.util,json,shutil,sys,types
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
SOURCE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'snapshot-001'
OUT=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else HERE/'reproduction-001'
OUT.mkdir()
spec=importlib.util.spec_from_file_location('reviewed_probe',SOURCE/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
def observed():
 return {'schema':1,'scope':'owned_padstack_import_only','units':'micrometres','routing_executed':False,'native_executed':False,'coordinate_transform':[1,0,0],
  'cases':[{'case':name,'status':'observed','parser_return':True,'padstack_count':1,'board_layer_count':2,'padstack_name':name,'input_sha256':d.sha(d.fixtures()[name+'.dsn']),
   'layers':{layer:None if shape is None else {'class':'app.freerouting.geometry.planar.IntBox',**copy.deepcopy(shape)} for layer,shape in d.expected()[name].items()}} for name in d.IDS]}
results=[]
for variant in ('unchanged','late_observation','late_input','late_class','late_process'):
 root=OUT/variant;root.mkdir();(root/'.runs').mkdir();helper=root/'experiments/pic_padstack_import_probe_v1';helper.mkdir(parents=True)
 for name in d.HELPERS:shutil.copyfile(SOURCE/name,helper/name)
 (root/'autorouter').mkdir()
 for name in ('runner.py','__init__.py'):(root/'autorouter'/name).write_bytes(b'synthetic runtime never executed')
 (root/'toolchain.lock.json').write_bytes(b'{}');(root/'.git/refs/heads/rebuild').mkdir(parents=True)
 (root/'.git/HEAD').write_text('ref: refs/heads/rebuild/local-test\n');ref=root/'.git/refs/heads/rebuild/local-test';ref.write_text('1'*40+'\n')
 protocol=d.decode(d.content(helper/'PROTOCOL.json'));(root/'tools').mkdir()
 for name in protocol['tools']:
  path=root/'tools'/name;path.write_bytes(b'tool');protocol['tools'][name]={'path':str(path),'bytes':4,'sha256':d.sha(b'tool')}
 d.write(helper/'PROTOCOL.json',protocol);batch=root/'.runs/output';mutated=[];calls=[];real_content=d.content
 def git(argv,**kwargs):
  assert argv[:2]==['git','show'];return types.SimpleNamespace(stdout=(root/argv[2].split(':',1)[1]).read_bytes())
 def runner(argv,*,cwd,log,**kwargs):
  assert argv[:3]==d.SANDBOX;calls.append(log.name);log.write_bytes(b'SYNTHETIC ONLY; no subprocess launched\n')
  if log.name=='compile.log':(batch/'classes/PadstackImportProbe.class').write_bytes(b'fake compile')
  else:d.write(batch/'observations.json',observed())
  return {'status':'success','exit_code':0,'cleanup_complete':True,'pid':123,'argv':argv,'log':str(log)}
 def content(path,*args,**kwargs):
  value=real_content(path,*args,**kwargs)
  # Final source/tool/HEAD scan happens AFTER frozen output scan. Mutate a
  # previously captured real output at its final HEAD witness read.
  if variant!='unchanged' and Path(path)==ref and (batch/'summary.json').exists() and not mutated:
   targets={'late_observation':'observations.json','late_input':'inputs/concave.dsn','late_class':'classes/PadstackImportProbe.class','late_process':'import-process.json'}
   target=batch/targets[variant];target.write_bytes(target.read_bytes()+b'\n');mutated.append(str(target.relative_to(batch)))
  return value
 with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'HERE',helper),mock.patch.object(d.sys,'executable',str(root/'tools/python')),mock.patch.object(d.subprocess,'run',side_effect=git),mock.patch.object(d.runner,'run',side_effect=runner),mock.patch.object(d,'content',side_effect=content):
  result=d.experiment(batch)
 saved=d.decode(real_content(batch/'summary.json'));mismatch=[name for name,row in result['frozen_evidence'].items() if real_content(batch/name,digest=True)!=row]
 results.append({'variant':variant,'status':result['status'],'observations_complete':result['observations_complete'],'canonical_complete':saved['observations_complete'],'mutated':mutated,'stale_frozen_artifacts':mismatch,'mocked_stage_calls':calls})
(OUT/'results.json').write_text(json.dumps({'source_sha256':d.sha((SOURCE/'driver.py').read_bytes()),'native_java_compiler_executed':False,'results':results},indent=2)+'\n')
print(json.dumps(results,indent=2))
