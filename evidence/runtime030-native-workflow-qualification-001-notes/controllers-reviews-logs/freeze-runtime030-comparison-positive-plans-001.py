"""Freeze two prospective functional controls from one measured material preparation."""
from pathlib import Path
import sys,json,re,hashlib
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
base=ROOT/'.runs/runtime030-native-controls-preparation-001';material=f.read_json(base/'material.json')
log=ROOT/'.runs/runtime030-native-controls-preparation-001-time.log';raw=log.read_bytes();pairs=re.findall(r'^(real|user|sys) ([0-9]+(?:\.[0-9]+)?)$',raw.decode(),re.M);assert len(pairs)==3
values={key:Decimal(value) for key,value in pairs};runtime=Path(material['runtime'])
assert p.sha(runtime/'runtime-distribution.json')==material['runtime_manifest_sha256']
limits=dict(whole_wall_full_cpu_seconds=180,worker_seconds=176,child_acceptance_seconds=172,route_seconds=120,export_min_seconds=30,export_max_seconds=60,final_reserve_seconds=12)
for case,profile,directory in [('standard_positive','standard','native7-comparison-functional-001'),('tuned_variant','tuned','native7-comparison-functional-tuned-001')]:
 folder=ROOT/'.runs'/('runtime030-comparison-'+case+'-001');assert not folder.exists();folder.mkdir()
 plan={k:material[k] for k in ('runtime','source_head','runtime_manifest_sha256','runtime_tools','fixture_files','fixture_sha256')}
 plan.update(schema=1,kind='native7-comparison-functional-delivery-v1',case=case,profile=profile,output=str(runtime/'.runs'/directory),controller_sha256=material['controller_pins']['qualify-comparison-delivery-001.py'],enclosure_sha256=p.sha(ROOT/'.runs/enclose-runtime030-comparison-001.py'),board_name='owned1007-transport.kicad_pcb',route_seconds=120,expected_source_opens=2,expected_protected_routes=1,expected_Native_counts=[0,0,0,0],limits=limits,preparation_time_log=str(log),preparation_time_log_sha256=hashlib.sha256(raw).hexdigest(),preparation_wall_seconds=float(values['real']),preparation_full_cpu_seconds=float(values['user']+values['sys']),preparation_publication_budget_charge_seconds=4,scope='One exposed owned unflagged2Cu corrected '+profile+' caller-bound API delivery control with actual Native/fullSCH/protected1 original proof. No fair comparison, GUI, Windows, broader family or electrical-quality claim. Shared actual preparation is charged conservatively to each control; installation/full-suite/authoring/review remain separate costs.')
 assert not Path(plan['output']).exists();p.save_json(folder/'protocol.json',plan)
 print(json.dumps({'case':case,'protocol':str(folder/'protocol.json'),'protocol_sha256':p.sha(folder/'protocol.json')}))
