"""Immutable next development index from explicitly supplied schema2 receipts.

Stored receipt/source/code/raw-report consistency only. No native execution and
no implicit newest-run discovery. Stdout JSON; predecessor is never rewritten.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,math,os,stat,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_summary as ns
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'data/sources.json').is_file())
OLD='evidence/development-outcomes-002/index.json'
BOARD='.data/boards/kicad-multichannel/multichannel_mixer.kicad_pcb'
POLICIES=['placement-search-v2-margin0-default','placement-search-v2-margin20um-default','placement-search-v2-margin20um-via-low']
PARAMETERS=[{'clearance_margin_nm':0,'scoring_variant':'via_default','via_costs':50,'plane_via_costs':5},{'clearance_margin_nm':20000,'scoring_variant':'via_default','via_costs':50,'plane_via_costs':5},{'clearance_margin_nm':20000,'scoring_variant':'via_low','via_costs':25,'plane_via_costs':3}]
PAIRS={'margin_effect':(0,1),'via_cost_effect':(1,2),'combined_effect':(0,2)}
STEPS={'source-drc','floor-area-export','engine','import','refill-drc','floor-final','final-drc','metrics'}
CAP=120
MAX_FILE_BYTES=32*1024*1024
MAX_TREE_BYTES=128*1024*1024
MAX_TREE_FILES=2048
MAX_TREE_ENTRIES=4096

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

class Reader:
 def __init__(self):self.hashes={};self.trees={}
 def path(self,value):
  path=Path(value);path=path if path.is_absolute() else ROOT/path
  require(path.is_relative_to(ROOT) and '..' not in path.parts and not any(x.is_symlink() for x in (path,*path.parents)),'real checkout-local input required')
  require(path.is_file(),'explicit input file missing: '+str(path));return path
 def bytes(self,value):
  path=self.path(value);require(path.stat().st_size<=MAX_FILE_BYTES,'bounded input file required')
  with path.open('rb')as stream:
   before=os.fstat(stream.fileno());require(stat.S_ISREG(before.st_mode) and before.st_size<=MAX_FILE_BYTES,'bounded regular input required')
   data=stream.read(MAX_FILE_BYTES+1)
   require(len(data)<=MAX_FILE_BYTES,'input grew beyond byte bound')
   after=os.fstat(stream.fileno());require(after.st_size<=MAX_FILE_BYTES and len(data)==before.st_size==after.st_size,'input size changed while reading')
  name=str(path.relative_to(ROOT));digest=sha(data)
  require(name not in self.hashes or self.hashes[name]==digest,'input changed during generation');self.hashes[name]=digest;return data
 def read(self,value):return json.loads(self.bytes(value),object_pairs_hook=pairs,parse_constant=nonfinite)
 def reference(self,value):
  path=self.path(value);self.bytes(path);return {'evidence':str(path.relative_to(ROOT)),'sha256':self.hashes[str(path.relative_to(ROOT))]}
 def stable(self):
  for directory,binding in self.trees.items():
   files,entries=walk_inventory(self,Path(directory),binding['files'],binding['entries'])
   require(files==binding['files'] and entries==binding['entries'],'evidence inventory changed before publication')
  for name,digest in self.hashes.items():require(sha(self.bytes(name))==digest,'input changed before index publication')

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def equal(first,last,message):require(canonical(first)==canonical(last),message)

def walk_inventory(reader,directory,expected_files,expected_entries=None):
 """Streaming bounded traversal; unknown files/late entries reject before read/descent."""
 require(isinstance(expected_files,dict) and len(expected_files)<=MAX_TREE_FILES,'bounded recorded inventory required')
 actual={};entries={};total=0;pending=[directory];prior_hash_names=set(reader.hashes)
 while pending:
  folder=pending.pop()
  with os.scandir(folder)as stream:
   for entry in stream:
    require(len(entries)<MAX_TREE_ENTRIES,'evidence entry count bound exceeded')
    path=Path(entry.path);name=str(path.relative_to(directory))
    require(name not in entries,'duplicate evidence entry')
    if expected_entries is not None:require(name in expected_entries,'unexpected evidence entry before publication')
    require(not entry.is_symlink(),'symlink in evidence inventory')
    if entry.is_file(follow_symlinks=False):
     require(name in expected_files,'unexpected evidence file')
     require(len(actual)<MAX_TREE_FILES,'evidence file count bound exceeded')
     size=entry.stat(follow_symlinks=False).st_size
     require(size<=MAX_FILE_BYTES and total+size<=MAX_TREE_BYTES,'evidence byte bound exceeded')
     body=reader.bytes(path);require(len(body)==size and total+len(body)<=MAX_TREE_BYTES,'evidence size changed while reading')
     total+=len(body);actual[name]=sha(body);entries[name]='file'
     require(actual[name]==expected_files[name],'recorded inventory digest differs')
    else:
     require(entry.is_dir(follow_symlinks=False),'special evidence entry');entries[name]='directory';pending.append(path)
    if expected_entries is not None:require(entries[name]==expected_entries[name],'evidence entry type changed')
 require(actual==expected_files,'recorded inventory differs')
 if expected_entries is not None:require(entries==expected_entries,'evidence inventory entries changed')
 # Preserve the predecessor's deterministic sorted-file insertion order only.
 # Existing digests are never rebased; bytes() checks them before this reorder.
 new_hashes={name:reader.hashes.pop(name)for name in sorted(set(reader.hashes)-prior_hash_names)}
 reader.hashes.update(new_hashes)
 return actual,entries

def inventory(reader,directory,expected):
 directory=Path(directory);directory=directory if directory.is_absolute() else ROOT/directory
 require(directory.is_relative_to(ROOT) and '..'not in directory.parts and not any(x.is_symlink()for x in (directory,*directory.parents)) and directory.is_dir(),'real local evidence directory required')
 key=str(directory);previous=reader.trees.get(key)
 if previous is not None:require(previous['files']==expected,'recorded inventory binding changed')
 actual,entries=walk_inventory(reader,directory,expected,previous['entries']if previous else None)
 reader.trees[key]={'files':dict(actual),'entries':entries}
 return actual

def scoped_receipt(d):
 require(type(d.get('diagnostic_schema'))is int and d['diagnostic_schema']==2 and d.get('production_qualified')is False and d.get('comparison_eligible')is False and d.get('physical_electrical_validation')is False and d.get('policy')in POLICIES,'unexpected schema2 diagnostic scope')
 equal(d.get('search_parameters'),PARAMETERS[POLICIES.index(d['policy'])],'declared search parameters differ')
 return boolean(d['routing_accepted'])

def native_receipt(d,fixture=False):
 accepted=scoped_receipt(d);native=d.get('native');require(isinstance(native,dict),'native receipt required')
 require(d.get('engine_profile')=='completion-only' and d.get('adapter')=='both','receipt profile differs')
 for key in ('opens','blocking','warnings','exclusions'):count(native.get(key))
 metrics=d.get('metrics');require(isinstance(metrics,dict) and metrics.get('version')=='10.0.0','recorded metrics required');amount(metrics.get('track_length_mm'));count(metrics.get('vias'))
 for key in ('budget_seconds','cpu_budget_seconds','wall_seconds','total_cpu_seconds','parent_cpu_seconds','waited_child_cpu_seconds'):amount(d.get(key))
 require(50<=d['budget_seconds']<=CAP and d['cpu_budget_seconds']==d['budget_seconds'],'receipt assigned budget differs')
 require(math.isclose(d['total_cpu_seconds'],d['parent_cpu_seconds']+d['waited_child_cpu_seconds'],abs_tol=1e-7,rel_tol=0),'receipt CPU sum differs')
 steps=d.get('steps');require(isinstance(steps,list) and len(steps)==8 and {x.get('name')for x in steps}==STEPS,'recorded stage inventory differs')
 step_cpu=sum(amount(x.get('cpu_seconds'))+amount(x.get('monitor_cpu_seconds'))for x in steps)
 require(d['waited_child_cpu_seconds']+1e-6>=step_cpu,'receipt child CPU undercount')
 within=d['wall_seconds']<=d['budget_seconds'] and d['total_cpu_seconds']<=d['cpu_budget_seconds']
 require(boolean(d.get('within_budget'))==within,'receipt within-budget flag differs')
 require(isinstance(d.get('freeze'),dict) and isinstance(d.get('tools'),dict),'receipt freeze required')
 equal(d['freeze'].get('tools'),d['tools'],'receipt tool freeze differs')
 require(isinstance(d['freeze'].get('files_sha256'),dict) and d['freeze']['files_sha256'],'receipt code freeze missing')
 for name,digest in d['tools'].get('implementation_sha256',{}).items():require(d['freeze']['files_sha256'].get(name)==digest,'core tool/code freeze differs')
 require(accepted==(ns.native_accepted(native) and within),'receipt acceptance contradicts raw native policy or budget')
 require(d['status']==('diagnostic_accepted'if accepted else 'drc_rejected') or not accepted and d['status']in ('budget_exceeded','cancelled','invalidated'),'receipt native status differs')
 if fixture and accepted:require(native['findings']==[] and native['warnings']==0 and metrics['vias']>=1,'accepted fixture must be clean required-via control')
 return accepted

def check_artifacts(reader,path,d):
 """Bind recorded facts to retained artifacts; deliberately not geometry validation."""
 directory=path.parent;source=reader.path(d['source']);name=source.name
 inventory(reader,source.parent,d['source_hashes']);inventory(reader,directory/'snapshot',d['source_hashes'])
 candidate=directory/'candidate'/name
 require(d['candidate']==str(candidate) and sha(reader.bytes(candidate))==d['candidate_sha256'],'candidate byte identity differs')
 expected=dict(d['source_hashes']);expected[name]=d['candidate_sha256'];inventory(reader,candidate.parent,expected)
 for relative,digest in d['freeze']['files_sha256'].items():
  require(sha(reader.bytes(directory/'code/source'/relative))==digest,'frozen code differs')
 helper=d['freeze']['helper_files']['native_combined.py'];require(d['observer_sha256']==d['freeze']['files_sha256'][helper]==sha(reader.bytes(directory/'code/native_combined.py')),'native observer differs')
 require(isinstance(d.get('evidence_hashes'),dict) and d['evidence_hashes'],'recorded evidence hashes missing')
 for relative,digest in d['evidence_hashes'].items():require(sha(reader.bytes(directory/relative))==digest,'recorded evidence hash differs')
 raw=directory/'final-drc.json';raw_bytes=reader.bytes(raw)
 require(sha(raw_bytes)==d['native_report_sha256'],'raw native report hash differs')
 raw_data=json.loads(raw_bytes,object_pairs_hook=pairs,parse_constant=nonfinite)
 equal(ns.parse_data(raw_data,name),d['native'],'raw native report/summary differs')
 equal(reader.read(directory/'metrics.json'),d['metrics'],'raw metrics differ')
 binding=reader.read(directory/'final-drc-binding.json');native_input=directory/'final-drc-input'/name
 require(binding.get('source')==str(candidate) and binding.get('input')==str(native_input) and binding.get('saved')is False,'native binding identity differs')
 equal(binding.get('before'),expected,'native original rule binding differs')
 after=binding.get('after');require(isinstance(after,dict) and all(after.get(k)==v for k,v in expected.items()) and set(after)-set(expected)<={source.with_suffix('.kicad_prl').name},'native post-input rules differ');inventory(reader,native_input.parent,after)
 for step in d['steps']:
  record=reader.read(directory/(step['name']+'-process.json'))
  require(all(k in step and canonical(step[k])==canonical(v)for k,v in record.items()),'process record/step differs')
  allowed=(0,5)if step['name']in ('source-drc','refill-drc','final-drc')else (0,)
  require(type(record.get('exit_code'))is int and record['exit_code']in allowed and record.get('status')==('success'if record['exit_code']==0 else 'nonzero_exit') and record.get('cleanup_complete')is True,'process status/exit/cleanup differs')
 final=next(x for x in d['steps']if x['name']=='final-drc')
 require(final.get('validated_input_sha256')==d['candidate_sha256'] and final.get('emitted_candidate')==str(candidate),'final native step/candidate differs')
 argv=final.get('argv');require(isinstance(argv,list) and argv[:3]==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)'] and argv[4:]==['pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(raw),str(native_input)],'native DRC argv differs')
 require(argv[3]in d['tools']['files'],'native executable missing frozen tool identity')
 require(final['exit_code']==(5 if d['native']['findings']else 0),'native findings/process exit differs')
 chain=d.get('chain');require(isinstance(chain,dict),'recorded transformation chain missing')
 equal(chain.get('search_parameters'),d['search_parameters'],'chain search parameters differ')
 for key,filename in [('native_dsn_sha256','native.dsn'),('floor_guided_sha256','floor-guided.dsn'),('placement_guided_sha256','placement-guided.dsn'),('pre_adapter_sha256','pre-adapter.dsn'),('task_dsn_sha256','task.dsn'),('search_guidance_sha256','search-guidance.json'),('floor_context_sha256','floor-export-context.json'),('area_context_sha256','area-context.json')]:
  require(chain.get(key)==sha(reader.bytes(directory/filename)),'recorded chain artifact differs')
 return d

def compare(first,last):
 a=boolean(first['accepted']);b=boolean(last['accepted'])
 key='gained'if b and not a else 'lost'if a and not b else 'tied_valid'if a else 'tied_invalid'
 value={'reference_policy':first['policy'],'variant_policy':last['policy'],'reference_accepted':a,'variant_accepted':b,'completion_difference':int(b)-int(a),'scope':'One exposed diagnostic planning/search comparison; no production/C/B2/generalized claim'}
 for metric in ('opens','blocking','warnings','exclusions'):value[metric+'_delta']=count(last[metric])-count(first[metric])
 if a and b:value.update(length_delta_mm=amount(last['length_mm'])-amount(first['length_mm']),via_delta=count(last['vias'])-count(first['vias']))
 return key,value

def empty_outcome(boards):return {'gained':[],'lost':[],'tied_valid':[],'tied_invalid':[],'unevaluated':list(boards),'comparison':None}

def protocol_check(reader,path,d,fixture_hashes,byname):
 protocol=reader.read(path.parent/'protocol.json');require(sha(reader.bytes(path.parent/'protocol.json'))==d['protocol_sha256'],'three-arm protocol hash differs')
 require(protocol['source_hashes'].get(Path(BOARD).name)==byname[BOARD]['source_sha256'],'three-arm source identity differs')
 require(protocol['fixture_sha256']in fixture_hashes,'explicit accepted schema2 fixture missing')
 fixture=fixture_hashes[protocol['fixture_sha256']];declared=protocol['protocol'];freeze=protocol['frozen']
 equal(fixture['freeze'],freeze,'fixture/three-arm code freeze differs');equal(fixture['tools'],freeze['tools'],'fixture tools differ')
 equal(fixture['source_hashes'],declared['qualification_fixture']['source_hashes'],'fixture original project differs')
 require(declared['qualification_fixture']['required_policy']==POLICIES[2],'fixture policy differs')
 for key,value in {'schema':2,'fixed_order':POLICIES,'wall_seconds_per_arm':CAP,'cpu_seconds_per_arm':CAP,'profile':'completion-only','adapter':'both','strict_generated_dimensions':True,'search_parameters':PARAMETERS}.items():equal(declared.get(key),value,'declared protocol differs: '+key)
 inventory(reader,reader.path(protocol['source']).parent,protocol['source_hashes'])
 require(protocol['source']==str(reader.path(BOARD)),'three-arm source path differs')
 helper=freeze['helper_files']['protocol.json'];raw=reader.bytes(path.parent/'code'/helper)
 require(sha(raw)==freeze['protocol_sha256']==freeze['files_sha256'][helper],'frozen declared protocol differs')
 equal(json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite),declared,'embedded/frozen protocol differs')
 for relative,digest in freeze['files_sha256'].items():require(sha(reader.bytes(path.parent/'code'/relative))==digest,'batch code freeze differs')
 inventory(reader,path.parent/'source-project',protocol['source_hashes'])
 return protocol

def build(fixture_results=(),three_arm_summary=None):
 reader=Reader();old=reader.read(OLD)
 for name,digest in old['input_files'].items():require(sha(reader.bytes(name))==digest,'prior index dependency changed')
 rows=copy.deepcopy(old['boards']);byname={r['board']:r for r in rows}
 require(len(rows)==14 and len(byname)==14,'full14-board population differs')
 require(sum(boolean(r['static_eligible_at_recorded_gate'])for r in rows)==3,'recorded3eligible/11unsupported differs')
 require(old['counts']['inputs_with_at_least_one_recorded_accepted_production_policy']==2,'recorded production accepted count differs')
 for row in rows:require(row['source_sha256']==sha(reader.bytes(row['board'])),'population source changed');row['search_v2_diagnostic_experiments']=[]
 fixtures=[];accepted_fixtures={}
 for value in fixture_results:
  path=reader.path(value);d=reader.read(path);ref=reader.reference(path);accepted=scoped_receipt(d)
  require(d['policy']==POLICIES[2],'fixture must use strongest declared diagnostic policy')
  if 'native'in d:native_receipt(d,fixture=True);check_artifacts(reader,path,d)
  else:require(not accepted and d.get('status')in ('rejected','cancelled','invalidated','budget_exceeded'),'missing native evidence cannot qualify fixture')
  if accepted:accepted_fixtures[ref['sha256']]=d
  fixtures.append({**ref,'kind':'owned qualification control, outside corpus denominator','status':d['status'],'recorded_routing_accepted':accepted,'production_qualified':False,'recorded_receipt':copy.deepcopy(d)})
 outcomes={'status':'pending_no_three_arm_summary_supplied',**{key:empty_outcome(byname)for key in PAIRS}}
 diagnostic_accepted=[]
 if three_arm_summary is not None:
  path=reader.path(three_arm_summary);d=reader.read(path);eligible=boolean(d['comparison_eligible'])
  require(type(d.get('schema'))is int and d['schema']==2 and d.get('kind')=='diagnostic_placement_search_three_arm' and d.get('production_qualified')is False,'unexpected three-arm schema/scope')
  arms=d['results'];require(isinstance(arms,list) and len(arms)==3 and [x['policy']for x in arms]==POLICIES,'fixed three-arm denominator/order differs')
  protocol=protocol_check(reader,path,d,accepted_fixtures,byname)if 'protocol_sha256'in d else None
  if eligible:require(d['status']=='completed' and d.get('raw_tasks_equivalent')is True and protocol is not None,'incomplete experiment cannot compare')
  records=[]
  for i,row in enumerate(arms):
   accepted=boolean(row['accepted']);record=copy.deepcopy(row);arm=None
   if 'receipt_sha256'in row:
    arm_path=path.parent/f'arm-{i}/result.json';arm=reader.read(arm_path);require(sha(reader.bytes(arm_path))==row['receipt_sha256'],'canonical arm hash differs')
    scoped_receipt(arm);require(arm['policy']==row['policy'],'arm policy differs')
    if 'native'in arm:native_receipt(arm);check_artifacts(reader,arm_path,arm)
    else:require(arm['routing_accepted']is False,'missing native arm cannot be accepted')
    record.update(receipt=reader.reference(arm_path),recorded_receipt=copy.deepcopy(arm))
   if eligible:
    require(arm is not None and row.get('diagnostic_verified')is True and row.get('within_charged_caps')is True,'verified native arm missing')
    require(accepted==boolean(row['verified_native_accepted'])==native_receipt(arm),'summary acceptance contradicts canonical arm')
    equal(arm['freeze'],protocol['frozen'],'arm code/tool freeze differs');equal(arm['tools'],protocol['frozen']['tools'],'arm tools differ')
    equal(arm['source_hashes'],protocol['source_hashes'],'full original project differs');require(arm['source']==protocol['source'],'arm source path differs')
    require(arm['budget_seconds']==amount(protocol['identical_assigned_seconds']),'equal assigned cap differs')
    require(row['status']==arm['status'],'summary status differs')
    equal(row.get('chain'),arm.get('chain'),'summary chain differs')
    for key in ('opens','blocking','warnings','exclusions'):require(count(row[key])==arm['native'][key],'summary native counter differs')
    require(amount(row['length_mm'])==arm['metrics']['track_length_mm'] and count(row['vias'])==arm['metrics']['vias'],'summary metrics differ')
    for kind in ('wall','cpu'):
     shared=amount(d[f'shared_{kind}_seconds']);invocation=amount(row[f'invocation_{kind}_seconds']);charged=amount(row[f'charged_{kind}_seconds'])
     require(charged<=CAP and math.isclose(charged,invocation+shared,abs_tol=1e-6,rel_tol=0),'charged budget/shared cost differs')
     require(invocation+1e-6>=arm['wall_seconds'if kind=='wall'else'total_cpu_seconds'],'outer invocation undercounts arm')
   else:require(not accepted,'ineligible experiment cannot contribute accepted outcome')
   records.append(record)
  if eligible:
   require(isinstance(d.get('completed_trees'),dict) and len(d['completed_trees'])==7,'full completed tree inventory missing')
   expected_paths={str(path.parent/f'arm-{i}')for i in range(3)}|{str(path.parent/'source-project'),str(path.parent/'code'),str(reader.path(protocol['fixture_receipt']).parent),str(reader.path(accepted_fixtures[protocol['fixture_sha256']]['source']).parent)}
   require(set(d['completed_trees'])==expected_paths,'completed tree scope differs')
   for directory,hashes in d['completed_trees'].items():inventory(reader,directory,hashes)
   for kind in ('wall','cpu'):
    require(math.isclose(amount(d[f'batch_{kind}_seconds']),sum(amount(x[f'invocation_{kind}_seconds'])for x in arms)+amount(d[f'shared_{kind}_seconds']),abs_tol=1e-6,rel_tol=0),'batch/shared accounting sum differs')
   computed={}
   for key,(first,last)in PAIRS.items():
    category,value=compare(arms[first],arms[last]);computed[key]=value;outcomes[key][category]=[BOARD];outcomes[key]['unevaluated'].remove(BOARD);outcomes[key]['comparison']=value
   equal(d.get('comparison'),computed,'recorded pairwise comparisons differ')
   diagnostic_accepted=[BOARD]if any(x['accepted']for x in arms)else[]
  else:require(d.get('comparison')is None,'ineligible comparison must be absent')
  outcomes['status']='eligible_recorded_three_arm'if eligible else'recorded_three_arm_unavailable_for_comparison'
  byname[BOARD]['search_v2_diagnostic_experiments'].append({**reader.reference(path),'kind':'exposed adapter planning/search diagnostic only','production_qualified':False,'comparison_eligible':eligible,'status':d['status'],'arms':records,'recorded_summary':copy.deepcopy(d),'recorded_protocol':copy.deepcopy(protocol)})
 result=copy.deepcopy(old);result.update(schema=3,kind='recorded development evidence index, not a new benchmark or native readback',predecessor=reader.reference(OLD),boards=rows,search_v2_owned_qualification_controls=fixtures,placement_search_three_arm_outcomes=outcomes)
 result['diagnostic_accepted_inputs']=sorted(set(old['diagnostic_accepted_inputs'])|set(diagnostic_accepted))
 result['counts']['inputs_with_recorded_accepted_placement_diagnostic']=len(result['diagnostic_accepted_inputs'])
 result['counts']['inputs_with_recorded_accepted_search_v2_diagnostic']=len(diagnostic_accepted)
 result['limits']+=['Three-arm schema2 diagnostic keeps the14-input population,3eligible/11unsupported gate and2production-policy successes unchanged.','Fixed20um margin is an exposed experimental parameter, not a universal geometric bound or promoted production policy.','Margin/cost/combined comparisons concern one development-exposed input; no C novelty, B2 superiority, independent-family or population-rate claim.','All raw costs/failures remain; accepted outputs may retain noncritical warnings. Quality deltas require two accepted outputs.','This index verifies saved hashes, raw-report/metric/process consistency only; it neither reruns native validation nor proves unrecorded physical/electrical correctness.']
 result['input_files']=reader.hashes;reader.stable();return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fixture-result',type=Path,action='append',default=[]);parser.add_argument('--three-arm-summary',type=Path);args=parser.parse_args()
 print(json.dumps(build(args.fixture_result,args.three_arm_summary),indent=2,allow_nan=False))
if __name__=='__main__':main()
