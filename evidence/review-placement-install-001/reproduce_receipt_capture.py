"""Whole installer control flow with fake command results and real tiny files.
No git/clone/venv/install/native/engine/network processes are executed.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys
from unittest import mock
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
SCRIPT=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'snapshot-001/scripts/install_smoke.py'
OUT=Path(sys.argv[2]) if len(sys.argv)>2 else HERE/'reproduction-001'
spec=importlib.util.spec_from_file_location('review_install',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='a'*40
CASES=['unchanged','native_receipt_before_inventory']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def case(name):
 base=OUT/name;base.mkdir(parents=True);source=base/'source';source.mkdir();out=base/'output';clone=out/'checkout'
 selected=m.qualification('placement-clearance-v1');fixture_relative=Path(selected['fixture'])
 for rel,raw in {'README.md':b'original source',str(fixture_relative):b'owned synthetic board control',str(fixture_relative.with_suffix('.kicad_pro')):b'{}','scripts/install_smoke.py':SCRIPT.read_bytes()}.items():
  path=source/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 (source/'.git/refs/heads').mkdir(parents=True);(source/'.git/HEAD').write_text('ref: refs/heads/review\n');(source/'.git/refs/heads/review').write_text(HEAD+'\n');(source/'.git/index').write_bytes(b'original source index')
 listing='\0'.join(['README.md',str(fixture_relative),str(fixture_relative.with_suffix('.kicad_pro')),'scripts/install_smoke.py'])+'\0'
 jar=source/'.tools/test.jar';jar.parent.mkdir();jar.write_bytes(b'synthetic JAR is never executed')
 native_tool=base/'native-tool';native_tool.write_bytes(b'synthetic native binary never executed')
 source_python=base/'source-python';source_python.write_bytes(b'synthetic calling interpreter never executed')
 native=clone/'.runs'/selected['directory'];calls=[];mutation={}
 def run(argv,*,cwd,log,**kwargs):
  assert argv[:len(m.NETWORK_DENIAL)]==m.NETWORK_DENIAL
  a=argv[len(m.NETWORK_DENIAL):];log=Path(log);calls.append(a);text=''
  if a[0]=='git':
   if 'clone' in a:
    clone.mkdir();(clone/'.git').mkdir();(clone/'.git/HEAD').write_text(HEAD+'\n');(clone/'.git/index').write_bytes(b'original clone index')
    for rel in listing.split('\0'):
     if rel:
      dst=clone/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,dst)
   elif 'rev-parse' in a:
    repo=Path(a[a.index('-C')+1]);text=(repo/'.git/HEAD').read_text()
    if text.startswith('ref: '):text=(repo/'.git'/text.strip()[5:]).read_text()
   elif 'symbolic-ref' in a:text='review\n'
   elif 'ls-files' in a:text=listing
   elif 'status' in a:text=''
   elif 'checkout' in a:pass
   else:raise AssertionError('unexpected fake Git command '+repr(a))
  elif '-m' in a and a[a.index('-m')+1]=='venv':
   venv=Path(a[-1]);(venv/'bin').mkdir(parents=True);(venv/'bin/python').write_bytes(b'copied fake python');(venv/'pyvenv.cfg').write_text('fake virtual environment')
  elif '-c' in a:
   venv=clone/'.venv';text=json.dumps({'version':'3.11 mock','executable':str(venv/'bin/python'),'prefix':str(venv),'base_prefix':str(base/'base-python')})
  elif 'scripts/setup_engine.py' in a:pass
  elif 'doctor' in a:text=json.dumps({'ready':True})
  elif 'unittest' in a:pass
  elif 'route' in a:
   native.mkdir();(native/'candidate.board').write_bytes(b'before final checks')
   result={'accepted':True,'wall_seconds':8.0,'status':'routing_accepted','tools':{'git_head':HEAD,'files':{str(native_tool):digest(native_tool),str(clone/'.tools/test.jar'):digest(clone/'.tools/test.jar')}},'source':str(clone/fixture_relative),'schema':3,'input_policy':selected['guidance'],'adapter':'both','engine_profile':'completion-only','scoring_variant':'via_default','scope':'whole_board_unlocked_routing','budget_seconds':60.0,'cpu_budget_seconds':60.0,'planning_parameters':m.pc.parameters()}
   (native/'result.json').write_text(json.dumps(result))
  elif 'check-result' in a:text=json.dumps({'current':True,'scope':'synthetic controlled command; not actual validation'})
  else:raise AssertionError('unexpected fake command '+repr(a))
  log.write_text(text)
  if log.name=='freshness-7.log' and name not in {'unchanged','native_receipt_before_inventory'}:
   targets={'native_candidate':native/'candidate.board','source_tracked':source/'README.md','clone_tracked':clone/'README.md','native_tool':native_tool,'venv_python':clone/'.venv/bin/python','source_python':source_python,'command_log':out/'00-source-status.log','source_head':source/'.git/refs/heads/review','clone_head':clone/'.git/HEAD','source_index':source/'.git/index','clone_index':clone/'.git/index'}
   target=targets[name];mutation.update(path=str(target),before_sha256=digest(target));target.write_bytes(target.read_bytes()+b'\nchanged during final owned Git probe\n');mutation['after_sha256']=digest(target)
  return {'argv':argv,'status':'success','exit_code':0,'log':str(log),'cpu_seconds':0.0,'monitor_cpu_seconds':0.0}
 original_read=m.read_json
 def reader(path):
  parsed=original_read(path)
  if Path(path)==native/'result.json' and name=='native_receipt_before_inventory' and not mutation:
   target=native/'result.json';data=json.loads(target.read_text());mutation.update(path=str(target),before_sha256=digest(target));data['wall_seconds']=1.0;target.write_text(json.dumps(data));mutation['after_sha256']=digest(target)
  return parsed
 with mock.patch.object(m,'read_json',side_effect=reader),mock.patch.object(m.c,'ROOT',source),mock.patch.object(m.c,'JAR',jar),mock.patch.object(m.c,'JAR_SHA256',digest(jar)),mock.patch.object(m.p,'check_storage',return_value=0),mock.patch.object(m,'run',side_effect=run),mock.patch.object(m.platform,'system',return_value='Darwin'),mock.patch.object(m.sys,'version_info',(3,11)),mock.patch.object(m.sys,'executable',str(source_python)):
  code=m.install_test(out,'placement-clearance-v1')
 result=m.read_json(out/'result.json');return {'case':name,'exit_code':code,'canonical_passed':result['passed'],'status':result['status'],'reason':result.get('reason'),'mutation':mutation,'mock_command_count':len(calls),'summary_native_wall':result.get('native',{}).get('wall_seconds'),'receipt_native_wall':json.loads((native/'result.json').read_text()).get('wall_seconds'),'expected_pass':name=='unchanged','expectation_satisfied':result['passed']==(name=='unchanged')}
def main():
 OUT.mkdir(exist_ok=False);rows=[case(name) for name in CASES];result={'script':str(SCRIPT),'script_sha256':digest(SCRIPT),'scope':'Entire install_test flow, mocked every command including fake clone/venv/native; real tiny native receipt mutated immediately after its first strict parse, before the parsed object is returned. No native qualification.','actual_subprocess_count':0,'rows':rows,'all_expected':all(r['expectation_satisfied'] for r in rows)};(OUT/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
