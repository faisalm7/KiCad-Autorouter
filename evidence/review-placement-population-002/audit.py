"""Reproduce stored reporting only; no native/tool validation or board copying."""
from pathlib import Path
import importlib.util,json,hashlib
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'data/sources.json').is_file());HERE=Path(__file__).resolve().parent;DRAFT=ROOT/'.runs/placement-population-draft-002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());checks=[]
def ok(name,test):
 if not test:raise AssertionError(name)
 checks.append(name)
def main():
 ok('exact reviewed reporter',sha(DRAFT/'generate.py')=='11d5f77b24d971146f120b1c92b557730e1b2e9de9ee4857773b18ed151f82bf')
 ok('exact saved actual index',sha(DRAFT/'actual-pair-index.json')=='607d136d1bed16fb5aeb26447cd698edcb5626374c1570df16b71d9d0885b636')
 s=importlib.util.spec_from_file_location('report_review',DRAFT/'generate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 value=m.build([ROOT/'.runs/placement-routing-fixture-001/result.json',ROOT/'.runs/placement-routing-fixture-002/result.json'],ROOT/'.runs/placement-routing-pair-001/summary.json');stored=read(DRAFT/'actual-pair-index.json')
 ok('actual reporter reproduces complete stored index',value==stored)
 boards=value['boards'];ok('full denominator unchanged',len(boards)==14 and len({x['board'] for x in boards})==14)
 ok('same recorded static gate3eligible11unsupported',sum(x['static_eligible_at_recorded_gate'] for x in boards)==3 and sum(not x['static_eligible_at_recorded_gate'] for x in boards)==11)
 ok('separate accepted production and diagnostic counts',value['counts']['inputs_with_at_least_one_recorded_accepted_production_policy']==2 and value['counts']['inputs_with_recorded_accepted_placement_diagnostic']==0 and value['diagnostic_accepted_inputs']==[])
 out=value['placement_diagnostic_pair_outcomes'];ok('single both-invalid tie and thirteen unevaluated',out['status']=='eligible_recorded_pair' and out['tied_invalid']==[m.BOARD] and not any(out[k] for k in ('gained','lost','tied_valid')) and len(out['unevaluated'])==13)
 ok('no completion gain and no usable quality delta',out['comparison']['completion_difference']==0 and out['comparison']['opens_delta']==-152 and out['comparison']['blocking_delta']==1 and 'length_delta_mm' not in out['comparison'] and 'via_delta' not in out['comparison'])
 fixture=value['owned_qualification_controls'];ok('failed and accepted owned fixtures outside corpus',len(fixture)==2 and [x['recorded_routing_accepted'] for x in fixture]==[False,True] and all(x['production_qualified'] is False and 'outside corpus denominator' in x['kind'] for x in fixture))
 row=next(x for x in boards if x['board']==m.BOARD);record=row['diagnostic_experiments'];ok('one fixed pair retained',len(record)==1 and record[0]['comparison_eligible'] is True and record[0]['production_qualified'] is False)
 pair=read(ROOT/'.runs/placement-routing-pair-001/summary.json');protocol=read(ROOT/'.runs/placement-routing-pair-001/protocol.json')
 for i,arm in enumerate(record[0]['arms']):
  raw=read(ROOT/'.runs/placement-routing-pair-001'/('arm-'+str(i))/'result.json');summary=pair['results'][i]
  ok('arm'+str(i)+' canonical receipt/counters/cost/source/freeze equality',arm['recorded_receipt']==raw and arm['recorded_native']==raw['native'] and arm['tools']==raw['tools']==protocol['frozen']['tools'] and raw['freeze']==protocol['frozen'] and raw['source_hashes']==protocol['source_hashes'] and all(arm[k]==summary[k] for k in ('status','accepted','verified_native_accepted','opens','blocking','warnings','exclusions','charged_wall_seconds','charged_cpu_seconds')))
  ok('arm'+str(i)+' shared cost complete within120',abs(arm['charged_wall_seconds']-arm['invocation_wall_seconds']-pair['shared_wall_seconds'])<1e-7 and abs(arm['charged_cpu_seconds']-arm['invocation_cpu_seconds']-pair['shared_cpu_seconds'])<1e-7 and arm['charged_wall_seconds']<=120 and arm['charged_cpu_seconds']<=120)
 ok('all read reporting dependency digests match',all(sha(ROOT/name)==digest for name,digest in value['input_files'].items()))
 ok('reporter and stored index remain unchanged',sha(DRAFT/'generate.py')=='11d5f77b24d971146f120b1c92b557730e1b2e9de9ee4857773b18ed151f82bf' and sha(DRAFT/'actual-pair-index.json')=='607d136d1bed16fb5aeb26447cd698edcb5626374c1570df16b71d9d0885b636')
 result={'schema':1,'audit_passed':True,'check_count':len(checks),'checks':checks,'native_executed':False,'code_sha256':sha(DRAFT/'generate.py'),'index_sha256':sha(DRAFT/'actual-pair-index.json'),'scope':'Reporting stored receipt consistency only; prior independent native/raw pair audit supplies distinct evidence. No new support or routing qualification.'}
 with (HERE/'audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
