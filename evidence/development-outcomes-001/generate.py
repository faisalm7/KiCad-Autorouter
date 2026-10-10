"""Reconcile recorded development outcomes; does not execute native validation."""
from pathlib import Path
import hashlib,json
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'data/sources.json').is_file())
def read(name):return json.loads((ROOT/name).read_text())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
a='evidence/corpus-audit-003.json';b='evidence/corpus-expansion-policy-audit-001.json'
rows=[]
for r in read(a)['boards']:
 assert sha(r['board'])==r['sha256']
 rows.append(dict(board=r['board'],source_sha256=r['sha256'],input_completeness='manifested complete project',static_eligible_at_recorded_gate=r['static_eligible'],unsupported_reason=r['unsupported_reason'],static_evidence=a,native_experiments=[]))
for r in read(b)['boards']:
 assert sha(r['board'])==r['sha256']
 rows.append(dict(board=r['board'],source_sha256=r['sha256'],input_completeness='incomplete dependency and rights closure',static_eligible_at_recorded_gate=r['statically_eligible'],unsupported_reason=r['reason'],static_evidence=b,native_experiments=[]))
for key,name in [('sonde xilinx.kicad_pcb','evidence/portfolio-paired-001/paired-summary.json'),('interf_u.kicad_pcb','evidence/thermal-paired-001/paired-summary.json')]:
 record=next(r for r in rows if Path(r['board']).name==key);d=read(name)
 record['native_experiments'].append({'evidence':name,'sha256':sha(name),'status':d['status'],'arms':[{'id':x['id'],'accepted':x['accepted'],'status':x['status'],'charged_wall_seconds':x['charged_wall_seconds'],'charged_cpu_seconds':x['charged_cpu_seconds'],'candidate_sha256':x.get('candidate_sha256'),'quality_comparisons':d['comparisons'] if x['id'].startswith('C_') else None} for x in d['results']]})
name='evidence/multichannel-native-001/result.json';d=read(name);r=next(r for r in rows if Path(r['board']).name=='multichannel_mixer.kicad_pcb')
r['native_experiments'].append({'evidence':name,'sha256':sha(name),'status':d['status'],'arm':'B1 completion-only','accepted':d['accepted'],'receipt_wall_seconds':d['wall_seconds'],'receipt_cpu_seconds':d['total_cpu_seconds'],'native':{k:d['native'][k] for k in ('opens','blocking','warnings','exclusions')},'comparison':'none; single rejected attempt, not a paired C outcome'})
assert len(rows)==14 and sum(r['static_eligible_at_recorded_gate'] for r in rows)==3
result={'schema':1,'kind':'development evidence index, not a new benchmark','input_files':{n:sha(n) for n in [a,b,'data/sources.json']},'split':'all development-exposed','boards':rows,'counts':{'acquired_boards':14,'complete_inputs':7,'incomplete_inputs':7,'recorded_static_eligible':3,'recorded_static_unsupported':11,'inputs_with_actual_native_routing_attempts':3,'inputs_with_at_least_one_recorded_accepted_routing_policy':2,'independent_families_established':None},'pair_outcomes':{'sonde':{'B2_accepted':True,'C_feedback_accepted':True,'completion_gain':False,'completion_loss':False,'quality_proxy_improvement':True},'interf_u':{'B2_accepted':False,'C_thermal_accepted':True,'completion_gain':True,'completion_loss':False,'quality_comparable':False}},'limits':['Different frozen commits and two different C strategies; not an aggregate completion rate or unified-system benchmark.','Unsupported inputs are retained; static eligibility is not native acceptance.','The eleven unsupported inputs have no native routing result, and multichannel has no paired C result.','Only named paired experiments supply gain/loss comparisons; none was lost in those two observed pairs.','Input checks here verify current original board bytes against stored source hashes; no native job is performed.','Inherited severities and ignored checks are unchanged; no electrical/physical qualification or untouched test set.']}
print(json.dumps(result,indent=2))
