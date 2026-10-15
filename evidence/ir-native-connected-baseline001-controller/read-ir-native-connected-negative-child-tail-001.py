"""Only the missing rejected-child proof; no classifier/engine/reader repetition."""
from pathlib import Path
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
real=subprocess.Popen
def readonly(argv,*args,**kwargs):
 if argv!=['git','rev-parse','HEAD'] or Path(kwargs.get('cwd','')).resolve()!=ROOT:raise AssertionError('pure reader only')
 return real(argv,*args,**kwargs)
subprocess.Popen=readonly
from autorouter import pipeline as p,floor_route as f,sexpr as sx,placement_clearance as pc,local_settings as ls,routing_scope as rs
base=ROOT/'.runs/ir-native-connected-baseline-001';folder=base/'route';data=f.read_json(folder/'result.json');spec=f.read_json(ROOT/'.runs/ir-native-connected-baseline-protocol-001.json');before=f.evidence_inventory(base);pin=p.sha(folder/'result.json');tools=p.tool_manifest();assert tools==spec['tools']
source=Path(data['source']);candidate=Path(data['candidate']);original=sx.read(source);current=sx.read(candidate)
assert data['accepted'] is False and data['status']=='drc_rejected' and data['source_hashes']==p.tree_hash(source.parent) and p.immutable(current)==p.immutable(original)
p.verify_candidate_files(candidate,data['source_hashes'],data['candidate_sha256']);protected=p.protected_for_record(data,original);imports=ls.check_normal_policy(folder,data);contract=p.normal_import_contract(folder,data,imports,input_policy='native',original=original);p.check_protected_import(folder,data,original,candidate,protected,**(contract or {}));names=p.selected_scope_names(data);assert rs.audit(original,current,names)==data['selected_net_audit']
saved=f.check_drc_stage(folder,data,'refill-drc',folder/'refill'/source.name,folder/'refill'/source.name,True,{**data['source_hashes'],source.name:p.sha(folder/'pre-refill.kicad_pcb')},sandboxed=False)
final=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/source.name,False,{**data['source_hashes'],source.name:data['candidate_sha256']},schematic_parity=True,sandboxed=False)
assert final==data['native'] and p.sha(folder/'final-drc.json')==data['native_report_sha256'] and not p.native_accepted(final) and (final['opens'],final['blocking'],final['warnings'],final['exclusions'])==(1,0,42,0)
assert pc.read_bytes(candidate)==(sx.dump(p.transplant_fill(sx.read(folder/'pre-refill.kicad_pcb'),sx.read(folder/'refill'/source.name)))+'\n').encode()
metrics=f.read_json(folder/'metrics.json');f.process_check(folder,data,'metrics',[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(folder/'metrics.json')]);assert metrics==data['metrics'] and metrics['version']=='10.0.0'
p.check_native_edge_transport(folder,data);p.check_minimum_width_record(data,folder);p.check_preferences_record(data,folder)
assert p.tool_manifest()==tools
assert f.evidence_inventory(base)==before and p.sha(folder/'result.json')==pin and p.tree_hash(source.parent)==data['source_hashes']
raw=f.read_json(folder/'final-drc.json')
p.save_json(ROOT/'.runs/ir-native-connected-negative-child-tail-001/checks.json',dict(passed=True,accepted=False,new_native=False,new_engine=False,prior_groups_replayed=False,native={k:final[k]for k in ('opens','blocking','warnings','exclusions','ignored_checks')},unconnected_items=raw['unconnected_items'],metrics=metrics,candidate_sha256=data['candidate_sha256'],native_report_sha256=data['native_report_sha256'],source_hashes=data['source_hashes']));print('Rejected child actual Native, source/rules/preset/protected import, edge, process, metrics and fill replay verified.')
