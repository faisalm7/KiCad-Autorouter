"""Complete only missing pre-engine rejection checks; no Native/JVM launches."""
from pathlib import Path
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
real=subprocess.Popen
def readonly(argv,*args,**kwargs):
 if argv!=['git','rev-parse','HEAD'] or Path(kwargs.get('cwd','')).resolve()!=ROOT:raise AssertionError('pure reader only')
 return real(argv,*args,**kwargs)
subprocess.Popen=readonly
from autorouter import pipeline as p,floor_route as f,sexpr as sx,placement_clearance as pc,routing_scope as rs,preferences as pref
base=ROOT/'.runs/ir-native-connected-repair-001';folder=base/'route';outer=f.read_json(ROOT/'.runs/ir-native-connected-repair-execution-001/execution.json');d=f.read_json(folder/'result.json');spec=f.read_json(ROOT/'.runs/ir-native-connected-repair-protocol-001.json');receipt=p.sha(base/'result.json');childpin=p.sha(folder/'result.json');tools=p.tool_manifest();assert tools==spec['tools']
assert d['accepted'] is False and d['status']=='rejected' and d['reason']=='Rejected: insufficient remaining budget for engine grace and native finalization reserves'
assert [s['name']for s in d['steps']]==['source-drc','export','obstacles'] and not (folder/'engine-process.json').exists() and not (folder/'final-drc.json').exists() and 'candidate'not in d and 'native'not in d
source=Path(d['source']);original=sx.read(source);candidate=folder/'candidate'/source.name;hashes=p.tree_hash(source.parent)
assert d['source_hashes']==hashes and hashes=={**spec['source_hashes'],source.name:spec['repair_source_sha256']} and pc.read_bytes(candidate)==(sx.dump(p.routing_task(original,'selected_nets',['/GND']))+'\n').encode() and p.sha(candidate)==d['task_sha256']
p.verify_candidate_files(candidate,hashes,d['task_sha256']);assert p.immutable(sx.read(candidate))==p.immutable(original) and rs.audit(original,sx.read(candidate),['/GND'])
snapshot=folder/'snapshot'/source.name;native=f.check_drc_stage(folder,d,'source-drc',snapshot,folder/'source-drc-input'/source.name,False,hashes,sandboxed=False);assert native==d['source_drc'] and (native['opens'],native['blocking'],native['warnings'],native['exclusions'])==(1,0,32,0)
commands={'export':[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'export',str(candidate),str(folder/'task.dsn')], 'obstacles':[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'obstacles',str(candidate),str(folder/'obstacles.json')]}
for name,argv in commands.items():f.process_check(folder,d,name,argv)
assert p.sha(folder/'native.dsn')==d['native_dsn_sha256'] and p.sha(folder/'task.dsn')==d['task_dsn_sha256']
p.check_resource_accounting(d);p.check_native_edge_transport(folder,d)
effective=pref.readback(pc.read_bytes(folder/'routing-preferences.json'),d['routing_preferences']['effective']);assert p.sha(folder/'routing-preferences.json')==d['routing_preferences']['sha256'] and effective==pref.validate(f.read_json(base/'preferences.json')) and effective['nets']==['/GND'] and effective['profile']=='completion-only' and effective['seconds']==47 and 'engine_budget'not in d
assert rs.bind(pc.read_bytes(source),['/GND'])==d['selected_net_binding']
assert p.tool_manifest()==tools
assert f.evidence_inventory(base)==outer['material'] and p.sha(base/'result.json')==receipt and p.sha(folder/'result.json')==childpin
for n,pins in spec['retained_material'].items():assert p.tree_hash(ROOT/n)==pins
p.save_json(ROOT/'.runs/ir-native-connected-repair-preengine-tail-003/checks.json',dict(passed=True,accepted=False,method_qualified=False,new_native=False,new_engine=False,reason=d['reason'],source_native={k:native[k]for k in ('opens','blocking','warnings','exclusions','ignored_checks')},processes=[{k:s[k]for k in ('name','status','exit_code','cleanup_complete')}for s in d['steps']],candidate_is_unvalidated_task=True,final_native_available=False,final_metrics_available=False,child_receipt_sha256=childpin,actor_receipt_sha256=receipt));print('Pre-engine budget rejection, three real workers, exact source/protected task, DSN/edge/preset and immutable prior bytes verified; no final candidate pass.')
