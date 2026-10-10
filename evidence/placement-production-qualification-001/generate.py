"""Deterministic narrow qualification/population update; no new native execution."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
LIMIT=4*1024*1024

def read(name):
 path=ROOT/name
 if path.is_symlink() or path.stat().st_size>LIMIT:raise ValueError('unsupported evidence file')
 with path.open('rb') as f:raw=f.read(LIMIT+1)
 if len(raw)>LIMIT:raise ValueError('evidence exceeds limit')
 return json.loads(raw),{'path':name,'sha256':hashlib.sha256(raw).hexdigest()}

def generate():
 prior,prior_ref=read('evidence/development-outcomes-003/index.json')
 extension,extension_ref=read('evidence/licensed-acquisition-003/population-extension.json')
 fixture,fixture_ref=read('.runs/placement-production-native-001/result.json')
 full,full_ref=read('.runs/placement-production-multichannel-001/result.json')
 control,control_ref=read('.runs/placement-production-controls-native-002/summary.json')
 failed,failed_ref=read('.runs/placement-production-controls-native-001/summary.json')
 receipt,receipt_ref=read('.runs/placement-production-receipt-controls-001/summary.json')
 for name,d in ((fixture_ref['path'],fixture),(full_ref['path'],full)):
  assert d['accepted'] and d['input_policy']=='placement-clearance-v1'
  assert p.check_result(ROOT/name)['current']
 assert receipt['passed'] and not receipt['native_executed'] and not receipt['engine_executed']
 assert len(receipt['cases'])==13 and all(case['passed'] for case in receipt['cases'])
 assert control['controls_passed'] and len(control['cases'])==5 and all(c['passed'] for c in control['cases'])
 assert not failed['controls_passed'] and not failed.get('native_executed',False)
 cancellations=[]
 for signal in ('int','term'):
  d,ref=read('.runs/placement-production-cancellation-'+signal+'-001/control.json')
  assert d['passed'];cancellations.append({'evidence':ref,'signal':signal,'passed':True,'wall_seconds':d.get('wall_seconds'),'scope':'Actual engine-stage signal and group cleanup; full controller CPU not recorded.'})
 rows=[]
 for i,b in enumerate(prior['boards']):
  accepted=any(a.get('accepted',False) for ex in b['native_experiments'] for a in ex.get('arms',[]))
  rows.append({k:b.get(k) for k in ('board','source_sha256','input_completeness','static_eligible_at_recorded_gate','unsupported_reason')}|{'prior_row':i,'prior_production_accepted':accepted,'production_accepted':accepted,'new_production_result':None})
 assert sum(r['prior_production_accepted'] for r in rows)==2
 for r in rows:
  if r['source_sha256']==full['source_hashes']['multichannel_mixer.kicad_pcb']:
   assert not r['production_accepted'];r['production_accepted']=True;r['new_production_result']=full_ref
 assert sum(r['production_accepted'] for r in rows)==3
 for r in extension['records']:
  rows.append({'board':r['source'],'source_sha256':r['board_sha256'],'input_completeness':'incomplete development acquisition','static_eligible_at_recorded_gate':r['routing_supported'],'unsupported_reason':r['preflight_rejection'],'prior_row':None,'prior_production_accepted':False,'production_accepted':False,'new_production_result':None})
 assert len(rows)==16 and len({r['board'] for r in rows})==16
 for r in rows:assert p.sha(ROOT/r['board'])==r['source_sha256']
 def observed(d,ref):
  return {'evidence':ref,'git_head':d['tools']['git_head'],'accepted':d['accepted'],'candidate_sha256':d['candidate_sha256'],'native':{k:d['native'][k] for k in ('opens','blocking','warnings','exclusions')},'metrics':d['metrics'],'stored_wall_seconds':d['wall_seconds'],'stored_total_cpu_seconds':d['total_cpu_seconds'],'budget_seconds':d['budget_seconds'],'scope':'Stored cost sample precedes final publication checks; acceptance caps include those checks. No new comparison.'}
 return {'schema':1,'scope':'Saved actual production qualification and all16 exposed development inputs; no new benchmark/native run or independent-family/generalization claim. Original prior14 outcomes and acquisition extension remain immutable. Fixture and controls are outside the population.','predecessors':[prior_ref,extension_ref],'counts':{'acquired_boards':len(rows),'complete_inputs':7,'incomplete_inputs':9,'recorded_static_eligible':sum(r['static_eligible_at_recorded_gate'] for r in rows),'unsupported_or_incomplete':sum(not r['static_eligible_at_recorded_gate'] for r in rows),'inputs_with_actual_routing_attempts':3,'inputs_with_at_least_one_accepted_production_policy':sum(r['production_accepted'] for r in rows),'independent_families_established':None,'untouched_final_evaluation':0},'boards':rows,'fixture':observed(fixture,fixture_ref),'multichannel':observed(full,full_ref),'native_controls':{'evidence':control_ref,'passed':True,'cases':[{k:c.get(k) for k in ('case','passed','production_rejection')} for c in control['cases']],'wall_seconds':control['wall_seconds'],'total_cpu_seconds':control['total_cpu_seconds']},'failed_pre_native_attempt':failed_ref,'receipt_controls':receipt_ref,'cancellations':cancellations,'limitations':['96 warnings remain on multichannel; whole-project cleanliness and electrical adequacy unestablished.','The three accepted inputs used different policies/strategies in separate exposed experiments; not a pooled completion rate.','New full-board replay qualifies integration of an adapter/search policy, not C novelty or an equal-budget comparative gain.','Keepout enforcement, broader constraints, live apply/undo, human review and physical validation remain unqualified.']}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 value=generate();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 with args.output.open('xb') as out:out.write(raw)
 print(json.dumps({'output':str(args.output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'counts':value['counts']}))
