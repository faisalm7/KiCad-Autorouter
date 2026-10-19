"""Finite fresh-root preparation using shared installer and process runner.

No Native/GUI qualification. Exact old runtime retained, mutable state excluded.
Setup cwd/log bounds do not claim to quota adjacent destination; the installer
and provenance enforce bounded immutable population and exact local engine.
"""
from pathlib import Path
import sys,os,json,time,resource,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,floor_route as f,gui
from autorouter.runner import run
START=time.monotonic()
def cpu():return sum(v.ru_utime+v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();head='d1dd2218f0989b3fcbeef1b8d61a7e395c5a9467';source_head='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
source=ROOT/'.runs/runtime-directory-042/runtime';target=ROOT/'.runs/runtime042 fresh install 001'
assert not os.path.lexists(target)
assert p.sha(ROOT/'scripts/prepare_runtime.py')=='4efee63d98a5a55370a34c611eb79ae49f0653a76b5b22b5e37fdf4ccf4b0056'
oldpin='1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e';oldraw=(source/pv.MANIFEST).read_bytes();assert hashlib.sha256(oldraw).hexdigest()==oldpin
old=json.loads(oldraw);assert old['build_source']['git_head']==source_head
implementation={k:v for k,v in old['immutable_files_sha256'].items() if k.startswith('autorouter/')}
pv._runtime_identity(source,implementation)
out=ROOT/'.runs/runtime042-install-existing-qualification-001';out.mkdir(mode=0o700)
steps=[];env=gui.child_environment();env={k:v for k,v in env.items() if not k.startswith('KICAD_')}
def command(name,argv,cwd=out):
 assert time.monotonic()-START<105
 log=out/(name+('.json' if name=='tools-defaults' else '.log'))
 process=run([*f.SANDBOX,*map(str,argv)],cwd=cwd,env=env,log=log,timeout=min(60,120-(time.monotonic()-START)),max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=8*1024**2 if cwd==out else 256*1024**2)
 p.save_json(out/(name+'-process.json'),process);steps.append(dict(name=name,process=process,log_sha256=p.sha(log)))
 assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False,name
 return process
command('install',[ROOT/'.venv/bin/python','-B',ROOT/'scripts/prepare_runtime.py','--install-existing','--source',source,'--expected-manifest-sha256',oldpin,'--output',target])
new=json.loads((target/pv.MANIFEST).read_bytes());assert new==dict(old,root=str(target));newpin=p.sha(target/pv.MANIFEST)
command('venv',[ROOT/'.venv/bin/python','-B','-m','venv','--copies','--without-pip',target/'.venv'])
query="import json,sys;sys.path.insert(0,"+repr(str(target))+");from autorouter import pipeline as p,preferences as pref;print(json.dumps(dict(runtime=str(p.c.ROOT),interpreter=sys.executable,prefix=sys.prefix,tools=p.tool_manifest(),defaults=dict(pref.DEFAULTS)),sort_keys=True))"
command('tools-defaults',[target/'.venv/bin/python','-B','-c',query],cwd=target)
raw=(out/'tools-defaults.json').read_bytes()
settings=ROOT/'.runs/runtime042-ordinary-partial2Cu-001/settings.json';assert p.sha(settings)=='a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65'
(out/'settings.json').open('xb').write(settings.read_bytes())
assert (source/pv.MANIFEST).read_bytes()==oldraw and pv._runtime_identity(source,implementation)['manifest_sha256']==oldpin
newidentity=pv._runtime_identity(target,implementation);assert newidentity['manifest_sha256']==newpin
q=json.loads(raw);assert q['tools']['source_provenance']==newidentity and q['runtime']==str(target) and q['tools']['git_head']==source_head
record=dict(schema=1,kind='runtime042-install-existing-preparation-v1',setup_completed=True,Native_executed=False,actual_GUI=False,product_complete=False,source_head=source_head,administration_head=head,runtime=str(target),source_runtime=str(source),source_manifest_sha256=oldpin,runtime_manifest_sha256=newpin,immutable_files=len(implementation)+len([k for k in old['immutable_files_sha256'] if not k.startswith('autorouter/')]),immutable_maps_unchanged=True,processes=steps,preparation=dict(tools_query_sha256=p.sha(out/'tools-defaults.json'),tools_query_process_sha256=p.sha(out/'tools-defaults-process.json')),controller_sha256=p.sha(Path(__file__)),sampled_wall_seconds=time.monotonic()-START,sampled_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,limits='Subprocess allowance:60percommand, remaining120wall since post-import START;1GiB groupRSS/512KiB logs. Not a whole-exit deadline. Lead must retain external complete wall/fullCPU and require <=150seconds before declaring setup qualified. Adjacent immutable destination bounded by installer; no historical archive scanned. No Native/GUI qualification from setup.')
p.save_json(out/'preparation.json',record);print(json.dumps({k:record[k] for k in ('setup_completed','runtime_manifest_sha256','sampled_wall_seconds','sampled_CPU_seconds')}))
