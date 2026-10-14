"""Read-only prospective freeze of new exposed ArcDice comparison."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from scripts import experiment_quality as q
board,family=q.selected_source('arcdice');p.preflight(board)
protocol={'schema':1,'kind':'prospective ArcDice complete-schematic fourarm development comparison','git_head':p.tool_manifest()['git_head'],'tools':p.tool_manifest(),
 'board':str(board),'family':family,'proven_independent_pedigree':False,'original_source_sha256':p.tree_hash(board.parent),'source_five_files':f.read_json(ROOT/'evidence/arcdice-parent-scope-preparation-001/.runs/arcdice-parent-scope-preparation-001/REPORT.json')['source']['files'],
 'source_original_native_receipt_sha256':p.sha(ROOT/'.runs/arcdice-original-native-001/result.json'),'source_original_native_readback_sha256':p.sha(ROOT/'.runs/arcdice-original-native-002-readback/result.json'),
 'system':'native-all','arms':['B0 stock current workflow','B1 corrected adapter','B2 equal-budget threecost tuned portfolio','C independent tuned incumbent with feedback pruning'],
 'wall_budget_per_arm_seconds':120,'full_cpu_budget_per_arm_seconds':120,'batch_wall_cap_seconds':540,'batch_output_cap_bytes':100663296,
 'shared_original_qualification_cost':{'wall_seconds':15.867319041994,'full_cpu_seconds':13.269704,'meaning':'Actual5.867319wall3.269704CPU plus failedparser5 and correctedreadback5 allowances charged toEACHarm; no originalNative rerun'},
 'final_readback_allowance_wall_full_cpu_seconds':15,'outer_accounting':'Rawpaired arm+sharedchargedoverhead+wholeouter excess+1startupallowance+15auditallowance+sharedoriginalqualification forEACHarm; retain all failed/tied/lost/overbudget',
 'validation':'Everyfinal candidate actual savedrefill/finalDRC full schematic parity, originalSource/rules/geometry/netterminalmapping/stackup/zones exact and all native parents/DSN/class targets; warnings/exclusions original unchanged; report bound to candidateSHA',
 'original_expected_native':{'opens':0,'blocking':0,'warnings':26,'exclusions':0},'reference_routes_to_solver':False,
 'limits':['Exposeddevelopment notheldout','No physical/electrical/battery/human review','RootMIT/README retained; MyFootprintsTP4056 and8models assetoriginunclosed, raw notredistributed','No generalizedcompletion-rate/independentpedigree/speedupclaim','Managedpopulation25canonical8eligible17unsupported retained; newlead trackedseparately'],
 'execution':'Onelead, competitorssequential, noGUI/native/JVM contention, noexternalspending/network required; no automaticresume loop'}
path=ROOT/'.runs/arcdice-native-paired-complete-sch-002-protocol.json'
with path.open('x') as stream:stream.write(json.dumps(protocol,indent=2)+'\n')
print(json.dumps({'path':str(path),'sha256':p.sha(path),'source':str(board)}))
