"""Read stored outcomes into a new index; never run native checks or mutate sources.

Stored-receipt consistency only. Optional fixture/pair paths must be supplied explicitly.
Prints JSON to stdout only; no implicit discovery of the newest experiment.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,math
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'data/sources.json').is_file())
OLD='evidence/development-outcomes-001/index.json'
GATE='evidence/review-rule-area-scope-001/population-001.json'
BOARD='.data/boards/kicad-multichannel/multichannel_mixer.kicad_pcb'
POLICIES=['floor-v1-reference-diagnostic','floor-plus-placement-diagnostic-v1']
CAP=120

def require(value,message):
 if not value:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def pairs(values):
 result={}
 for key,value in values:
  require(key not in result,'duplicate JSON key');result[key]=value
 return result
def nonfinite(value):raise ValueError('nonfinite JSON '+value)
def boolean(value):require(type(value)is bool,'strict Boolean required');return value
def amount(value):
 require(type(value)in (float,int) and math.isfinite(value) and value>=0,'nonnegative finite measurement required');return value

def count(value):
 require(type(value)is int and value>=0,'nonnegative integer counter required');return value

def scoped_receipt(d):
 require(d.get('diagnostic_schema')==1 and d.get('production_qualified')is False and d.get('comparison_eligible')is False and d.get('policy')in POLICIES,'unexpected diagnostic receipt scope')
 return boolean(d['routing_accepted'])

def native_receipt(d,fixture=False):
 """Cross-check recorded facts, not a replacement for native check-result."""
 accepted=scoped_receipt(d);native=d.get('native');require(isinstance(native,dict),'native receipt required')
 require(d.get('engine_profile')=='completion-only' and d.get('adapter')=='both','receipt profile differs')
 for key in ('opens','blocking','warnings','exclusions'):count(native.get(key))
 require(isinstance(native.get('findings'),list) and isinstance(native.get('ignored_checks'),list),'recorded findings/checks required')
 metrics=d.get('metrics');require(isinstance(metrics,dict),'recorded metrics required');amount(metrics.get('track_length_mm'));count(metrics.get('vias'))
 for key in ('budget_seconds','cpu_budget_seconds','wall_seconds','total_cpu_seconds','parent_cpu_seconds','waited_child_cpu_seconds'):amount(d.get(key))
 require(50<=d['budget_seconds']<=CAP and d['cpu_budget_seconds']==d['budget_seconds'],'receipt assigned budget differs')
 require(math.isclose(d['total_cpu_seconds'],d['parent_cpu_seconds']+d['waited_child_cpu_seconds'],abs_tol=1e-7,rel_tol=0),'receipt CPU sum differs')
 steps=d.get('steps');require(isinstance(steps,list),'recorded steps required')
 step_cpu=sum(amount(x.get('cpu_seconds'))+amount(x.get('monitor_cpu_seconds'))for x in steps)
 require(d['waited_child_cpu_seconds']+1e-6>=step_cpu,'receipt child CPU undercount')
 within=d['wall_seconds']<=d['budget_seconds'] and d['total_cpu_seconds']<=d['cpu_budget_seconds']
 require(boolean(d.get('within_budget'))==within,'receipt within-budget flag differs')
 require(isinstance(d.get('freeze'),dict) and d['freeze'].get('tools')==d.get('tools') and isinstance(d.get('tools'),dict),'receipt tool freeze differs')
 require(isinstance(d['freeze'].get('files_sha256'),dict) and d['freeze']['files_sha256'],'receipt code freeze missing')
 if accepted:
  require(d['status']=='diagnostic_accepted' and within and all(native[k]==0 for k in ('opens','blocking','exclusions')),'accepted receipt contradicts status/native/budget')
 else:require(d['status']in ('drc_rejected','budget_exceeded','cancelled','invalidated'),'native rejection status differs')
 if fixture and accepted:
  require(native['findings']==[] and native['warnings']==0 and metrics['vias']>=1,'accepted fixture must be clean required-via control')
 return accepted

def classify(first,last,board):
 first=boolean(first);last=boolean(last)
 key='gained' if last and not first else 'lost' if first and not last else 'tied_valid' if first else 'tied_invalid'
 return key,{'board':board,'baseline_accepted':first,'placement_accepted':last,'completion_difference':int(last)-int(first)}

class Reader:
 def __init__(self):self.hashes={}
 def path(self,value):
  path=Path(value);path=path if path.is_absolute() else ROOT/path
  require(path.is_relative_to(ROOT) and '..' not in path.parts and not any(x.is_symlink() for x in (path,*path.parents)),'real checkout-local input required')
  require(path.is_file(),'explicit input file missing: '+str(path));return path
 def bytes(self,value):
  path=self.path(value);require(path.stat().st_size<=32*1024*1024,'bounded input file required');data=path.read_bytes();name=str(path.relative_to(ROOT));digest=sha(data)
  require(name not in self.hashes or self.hashes[name]==digest,'input changed during generation');self.hashes[name]=digest;return data
 def read(self,value):return json.loads(self.bytes(value),object_pairs_hook=pairs,parse_constant=nonfinite)
 def reference(self,value):
  path=self.path(value);self.bytes(path);return {'evidence':str(path.relative_to(ROOT)),'sha256':self.hashes[str(path.relative_to(ROOT))]}
 def stable(self):
  for name,digest in self.hashes.items():require(sha(self.path(name).read_bytes())==digest,'input changed before index publication')

def build(fixture_results=(),pair_summary=None):
 reader=Reader();old=reader.read(OLD);gate=reader.read(GATE)
 for name,digest in old['input_files'].items():require(sha(reader.bytes(name))==digest,'historical index dependency changed')
 rows=copy.deepcopy(old['boards']);byname={r['board']:r for r in rows};support={r['board']:r for r in gate['boards']}
 require(len(rows)==14 and len(byname)==14 and set(byname)==set(support),'full14-board denominator differs')
 require(gate['total']==14 and gate['full_preflight_eligible']==3 and gate['all_inputs_unchanged']is True,'recorded support audit differs')
 for row in rows:
  name=row['board'];s=support[name]
  require(row['source_sha256']==s['sha256']==sha(reader.bytes(name)),'original source identity differs')
  require(type(s['full_preflight_eligible'])is bool,'invalid recorded support verdict')
  row['prior_static_support']={k:row[k] for k in ('static_eligible_at_recorded_gate','unsupported_reason','static_evidence')}
  row.update(static_eligible_at_recorded_gate=s['full_preflight_eligible'],unsupported_reason=None if s['full_preflight_eligible'] else s['full_preflight_reason'],static_evidence=GATE,static_pipeline_sha256=gate['pipeline_sha256'],diagnostic_experiments=[])
 require(sum(r['static_eligible_at_recorded_gate'] for r in rows)==3,'recorded3eligible/11unsupported changed')
 require(old['counts']['inputs_with_at_least_one_recorded_accepted_routing_policy']==2,'old production scope count requires explicit review')
 fixtures=[];fixture_hashes={}
 for path in fixture_results:
  d=reader.read(path);reference=reader.reference(path)
  require(d.get('diagnostic_schema')==1 and d.get('production_qualified')is False and d.get('comparison_eligible')is False and d.get('policy')==POLICIES[1],'unexpected fixture diagnostic schema/scope')
  accepted=scoped_receipt(d)
  if accepted:
   native_receipt(d,fixture=True);fixture_hashes[reference['sha256']]=d
  fixtures.append({**reference,'kind':'owned qualification control, outside corpus denominator','status':d['status'],'recorded_routing_accepted':accepted,'production_qualified':False,'source':d.get('source'),'source_hashes':d.get('source_hashes'),'failure':d.get('error',d.get('reason')),'native':d.get('native'),'steps':d.get('steps',[]),'recorded_receipt':copy.deepcopy(d)})
 outcome={'status':'pending_no_pair_supplied','gained':[],'lost':[],'tied_valid':[],'tied_invalid':[],'unevaluated':list(byname),'comparison':None}
 diagnostic_accepted=[]
 if pair_summary is not None:
  require(fixtures,'explicit fixture result(s) required with pair');path=reader.path(pair_summary);d=reader.read(path)
  require(d.get('kind')=='diagnostic_floor_placement_pair' and d.get('production_qualified')is False,'unexpected pair kind/scope')
  eligible=boolean(d['comparison_eligible']);arms=d['results']
  require(isinstance(arms,list) and len(arms)==2 and [r['policy'] for r in arms]==POLICIES,'fixed two-arm diagnostic denominator differs')
  protocol=None
  if 'protocol_sha256' in d:
   protocol_path=path.parent/'protocol.json';protocol=reader.read(protocol_path)
   require(sha(reader.bytes(protocol_path))==d['protocol_sha256'],'pair protocol hash differs')
   require(protocol['source_hashes'].get(Path(BOARD).name)==byname[BOARD]['source_sha256'],'pair source hash differs')
   require(protocol['fixture_sha256']in fixture_hashes,'paired accepted fixture receipt not explicitly supplied')
   fixture=fixture_hashes[protocol['fixture_sha256']]
   require(fixture['freeze']==protocol.get('frozen') and fixture['tools']==protocol['frozen'].get('tools'),'fixture/pair code or tool freeze differs')
   require(fixture['source_hashes']==protocol['protocol']['qualification_fixture']['source_hashes'],'fixture source inventory differs')
   declared=protocol['protocol'];require(declared['fixed_order']==POLICIES and declared['wall_seconds_per_arm']==CAP and declared['cpu_seconds_per_arm']==CAP,'pair budget/order differs')
  arm_records=[]
  for i,row in enumerate(arms):
   accepted=boolean(row['accepted']);value={**copy.deepcopy(row)};arm=None
   if 'receipt_sha256'in row:
    arm_path=path.parent/f'arm-{i}'/'result.json';arm=reader.read(arm_path)
    require(sha(reader.bytes(arm_path))==row['receipt_sha256'],'arm receipt hash differs')
    scoped_receipt(arm);require(arm.get('policy')==row['policy'],'arm diagnostic scope differs')
    require(arm.get('source_hashes',{}).get(Path(BOARD).name)==byname[BOARD]['source_sha256'],'arm source differs')
    value.update(receipt=reader.reference(arm_path),candidate_sha256=arm.get('candidate_sha256'),recorded_native=arm.get('native'),tools=arm.get('tools'),steps=arm.get('steps'),recorded_receipt=copy.deepcopy(arm))
   if eligible:
    require(d['status']=='completed' and protocol is not None and d.get('raw_tasks_equivalent')is True,'incomplete pair cannot compare')
    require(row.get('diagnostic_verified')is True and row.get('within_charged_caps')is True and 'receipt_sha256'in row,'pair missing verified arm')
    require(accepted==boolean(row['verified_native_accepted'])==native_receipt(arm),'stored arm acceptance differs')
    require(row['status']==arm['status'],'summary/arm status differs')
    require(arm['source']==protocol['source'] and arm['source_hashes']==protocol['source_hashes'],'full arm source inventory differs')
    require(arm['freeze']==protocol['frozen'] and arm['tools']==protocol['frozen']['tools'],'arm code/tool freeze differs')
    require(arm['budget_seconds']==amount(protocol['identical_assigned_seconds']),'arm assigned budget differs')
    for metric in ('opens','blocking','warnings','exclusions'):require(count(row[metric])==arm['native'][metric],'summary/arm native counter differs')
    require(amount(row['length_mm'])==arm['metrics']['track_length_mm'] and count(row['vias'])==arm['metrics']['vias'],'summary/arm metrics differ')
    for kind in ('wall','cpu'):
     charged=amount(row[f'charged_{kind}_seconds']);expected=amount(row[f'invocation_{kind}_seconds'])+amount(d[f'shared_{kind}_seconds'])
     require(charged<=CAP and math.isclose(charged,expected,abs_tol=1e-6,rel_tol=0),'shared cost/cap differs')
     require(row[f'invocation_{kind}_seconds']+1e-6>=arm['wall_seconds'if kind=='wall'else 'total_cpu_seconds'],'outer invocation undercounts arm')
   else:require(not accepted,'ineligible pair cannot contribute accepted output')
   arm_records.append(value)
  recorded={**reader.reference(path),'kind':'adapter diagnostic only','status':d['status'],'production_qualified':False,'comparison_eligible':eligible,'failure':d.get('reason'),'protocol_sha256':d.get('protocol_sha256'),'arms':arm_records}
  byname[BOARD]['diagnostic_experiments'].append(recorded)
  outcome['status']='eligible_recorded_pair' if eligible else 'recorded_pair_unavailable_for_comparison'
  if eligible:
   key,comparison=classify(arms[0]['accepted'],arms[1]['accepted'],BOARD);outcome[key]=[BOARD];outcome['unevaluated'].remove(BOARD)
   for metric in ('opens','blocking','warnings','exclusions'):
    require(all(type(r[metric])is int and r[metric]>=0 for r in arms),'invalid native counter');comparison[metric+'_delta']=arms[1][metric]-arms[0][metric]
   if all(r['accepted']for r in arms):
    comparison['length_delta_mm']=amount(arms[1]['length_mm'])-amount(arms[0]['length_mm']);comparison['via_delta']=amount(arms[1]['vias'])-amount(arms[0]['vias'])
   expected={'floor_accepted':comparison['baseline_accepted'],'placement_accepted':comparison['placement_accepted'],'completion_difference':comparison['completion_difference'],**{k:v for k,v in comparison.items()if k.endswith('_delta')or k=='length_delta_mm'}}
   require(isinstance(d.get('comparison'),dict) and all(type(d['comparison'].get(k))is type(v) and d['comparison'].get(k)==v for k,v in expected.items()),'pair comparison disagrees with arms')
   outcome['comparison']=comparison
   if any(r['accepted']for r in arms):diagnostic_accepted=[BOARD]
  else:require(d.get('comparison')is None,'ineligible pair comparison must be absent')
 counts=copy.deepcopy(old['counts']);counts.pop('inputs_with_at_least_one_recorded_accepted_routing_policy')
 counts.update(inputs_with_at_least_one_recorded_accepted_production_policy=2,inputs_with_recorded_accepted_placement_diagnostic=len(diagnostic_accepted))
 result={'schema':2,'kind':'recorded development evidence index, not a new benchmark or native readback','split':'all development-exposed','boards':rows,'counts':counts,'production_pair_outcomes':copy.deepcopy(old['pair_outcomes']),'owned_qualification_controls':fixtures,'placement_diagnostic_pair_outcomes':outcome,'diagnostic_accepted_inputs':diagnostic_accepted,'input_files':reader.hashes,'limits':old['limits']+['Placement comparison is B1 adapter diagnosis, not C novelty/B2 superiority or production promotion.','Fixture controls do not enter the14-board denominator; incomplete/unsupported inputs remain.','Index generation checks stored receipt consistency and hashes only, never executes native checks.','Static support is from the named recorded gate; a new diagnostic does not broaden it.']}
 reader.stable();return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fixture-result',type=Path,action='append',default=[]);parser.add_argument('--pair-summary',type=Path);args=parser.parse_args()
 print(json.dumps(build(args.fixture_result,args.pair_summary),indent=2,allow_nan=False))
if __name__=='__main__':main()
