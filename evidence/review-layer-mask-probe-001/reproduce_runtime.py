"""Full layer controller, real tiny files/runtime hashing; Git and JVM are mocked."""
import copy,hashlib,importlib.util,json,sys,types
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
snapshot=Path(sys.argv[1]).resolve();OUT=HERE/sys.argv[2];OUT.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('layer_author_fixture',snapshot/'tests/test_layer_mask_probe.py')
test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test);m=test.m;b=m.layer_helpers()
original_content=b.content;original_write=b.write
rows=[]
for variant in ('positive','late_source','late_basis','late_python','late_dsn'):
 root=OUT/variant;root.mkdir();(root/'.runs').mkdir();(root/'.git/refs/heads/rebuild').mkdir(parents=True)
 ref=root/'.git/refs/heads/rebuild/local-test';ref.write_text('a'*40+'\n');(root/'.git/HEAD').write_text('ref: refs/heads/rebuild/local-test\n')
 for name in ('scripts/probe_engine_profiles.py','scripts/EngineProfileProbe.java','tests/test_layer_mask_probe.py','docs/layer-mask-probe.md','experiments/pic_padstack_import_probe_v1/driver.py','autorouter/runner.py'):
  path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('owned fake code\n')
 (root/'tools').mkdir()
 for name in ('java','jar','python','sandbox'):(root/'tools'/name).write_text('owned '+name+' bytes\n')
 tools={name:{'path':'tools/'+basename,**original_content(root/'tools'/basename,digest=True)} for name,basename in [('java','java'),('freerouting','jar')]}
 (root/'toolchain.lock.json').write_text(json.dumps({'tools':tools}))
 (root/'basis.txt').write_text('owned pinned basis\n')
 dsn=root/'fixture-original.dsn';dsn.write_bytes((ROOT/m.DSN_REL).read_bytes())
 basis={'basis.txt':b.sha((root/'basis.txt').read_bytes()),'fixture-original.dsn':m.DSN_SHA}
 out=root/'.runs/run';published=[];triggered=[]
 targets={'late_source':root/'scripts/probe_engine_profiles.py','late_basis':root/'basis.txt','late_python':root/'tools/python','late_dsn':dsn}
 def content(path,*args,**kwargs):
  path=Path(path)
  result=original_content(root/'tools/sandbox' if path==Path('/usr/bin/sandbox-exec') else path,*args,**kwargs)
  if published and not triggered and variant!='positive' and path==ref:
   with targets[variant].open('ab') as stream:stream.write(b'changed after hash\n')
   triggered.append(True)
  return result
 def writer(path,value):
  result=original_write(path,value)
  if path.name=='result.json' and value.get('passed'):published.append(True)
  return result
 def command(argv,**kwargs):
  assert argv[:2]==['git','show']
  relative=argv[2].split(':',1)[1]
  return types.SimpleNamespace(stdout=(root/relative).read_bytes())
 def worker(argv,**kwargs):
  kwargs['log'].write_text('mocked worker only\n')
  (out/'observations.json').write_bytes(b.canonical(test.observation()))
  return {'argv':argv,'status':'success','exit_code':0,'cleanup_complete':True,'log_truncated':False}
 with ExitStack() as stack:
  for owner,name,value in [(m,'ROOT',root),(m,'__file__',str(root/'scripts/probe_engine_profiles.py')),(m,'DSN_REL','fixture-original.dsn'),(m,'LAYER_BASIS',basis),(m,'run',worker),(b,'ROOT',root),(b,'content',content),(b,'write',writer),(m.c,'resolve_tool_path',lambda p:root/p),(m.c,'JAR_SHA256',tools['freerouting']['sha256'])]:stack.enter_context(patch.object(owner,name,value))
  stack.enter_context(patch.object(sys,'executable',str(root/'tools/python')))
  stack.enter_context(patch('subprocess.run',side_effect=command))
  with b.cancellation():result=m.layer_experiment(out)
 canonical=json.loads((out/'result.json').read_text()) if (out/'result.json').exists() else None
 rows.append({'case':variant,'triggered':bool(triggered),'returned_passed':result['passed'],'canonical_passed':canonical['passed'] if canonical else None,'status':result['status'],'error':result.get('error'),'changed_target':str(targets.get(variant)) if variant!='positive' else None})
record={'source_sha256':hashlib.sha256((snapshot/'scripts/probe_engine_profiles.py').read_bytes()).hexdigest(),'scope':'Actual controller/runtime hashing and files; fake committed-file responses and JVM output; no JVM/native/network','cases':rows}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
