from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
O=R/'evidence/chain-native002-actual-001';O.mkdir(exist_ok=False)
raw=R/'.runs/chain-pruning-native-control-002/result.json';d=f.read_json(raw)
assert d['passed'] is True and d['tools']['git_head']=='a24c09f4c87cc38ed63f2599270ac9c6ff50f266'
controls=[]
for row in d['controls']:
 controls.append({k:row[k] for k in ('case','passed','candidate_sha256','native_report_sha256','native','metrics','protected_count')})
screen=R/'.runs/chain-geometry-cohort003/result.json';sc=f.read_json(screen);rows=[]
for row in [*sc['rows'],*sc['reused_rows']]:
 b=row.get('batch',{});rows.append(dict(label=row['label'],prior_result=row['prior_result'],prior_result_sha256=row['prior_result_sha256'],candidate_sha256=row['candidate_sha256'],group_count=len(b.get('proposals',[])),group_sizes=[x['segment_count'] for x in b.get('proposals',[])],declined_reason=b.get('declined_reason'),error=row.get('error'),status=row.get('status'),unsupported=row.get('unsupported'),geometry_executed=row.get('geometry_executed'),context_sha256=row.get('context_sha256')))
paths=[raw,screen,R/'.runs/chain-pruning-native-control-execution-002/execution.json',R/'.runs/chain-native-route-screen-002/result.json',R/'.runs/chain-native-route-screen-execution-002/execution.json',R/'.runs/chain-geometry-cohort003-execution-001/execution.json',R/'.runs/chain-geometry-cohort003-protocol.json',Path(__file__)]
record=dict(schema=1,kind='endpoint-chain-native-mechanism-and-exposed-geometry-screen',producer_git_head=d['tools']['git_head'],new_routing_gain=False,production_admitted=False,actual_constructed_control_passed=True,controls=controls,scope=d['scope'],native_proposal_segments=len(d['native_proposal_batch']['proposals'][0]['route_ids']),native_proposal_length_mm=d['native_proposal_batch']['proposals'][0]['ranking_length_mm'],geometry_screen=rows,geometry_scope=sc['scope'],raw_pins={str(q.relative_to(R)):p.sha(q) for q in paths},native_execution=f.read_json(paths[2]),two_case_geometry_execution=f.read_json(paths[4]),seven_case_geometry_execution=f.read_json(paths[5]),all_raw_artifacts_on_this_Mac_only=True,limitations=['Constructed PCB-only control has no schematic parity; all five ignored checks retained.','Geometry screens execute Native geometry only, not DRC/routing or current requalification of prior candidates.','Five opportunity cases, two zero-group cases and two scope refusals remain in the nine-case population.','No engine/current-C ablation or comparative routing gain established. Installation035 predates opt-in chains.','Earlier actual001 board-edge failure remains false and preserved.','Skeptical actual control review95wallseconds, fullCPU unknown; no Native/test reruns.'])
p.save_json(O/'summary.json',record)
# Local-owned source/controller captures only; never raw third-party CAD geometry.
for name in ('capture-chain-native002-actual.py','run-chain-pruning-native-control-002.py','chain-native-route-screen-002.py','run-chain-native-route-screen-002.py','chain-geometry-cohort003.py','run-chain-geometry-cohort003.py'):
 source=R/'.runs'/name;(O/name).write_bytes(source.read_bytes())
p.save_json(R/'evidence/chain-native002-actual-001.json',dict(schema=1,kind=record['kind'],summary=str((O/'summary.json').relative_to(R)),summary_sha256=p.sha(O/'summary.json'),new_routing_gain=False,production_admitted=False))
print(json.dumps(rows,indent=1))
