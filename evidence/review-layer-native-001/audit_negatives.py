"""Two completed real negative controls; shared functions, no workers."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,preferences as pref
OUT=Path(__file__).resolve().parent
j=lambda path:json.loads(path.read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
failed=ROOT/'.runs/layers-native-required-via-front-001';negative=ROOT/'.runs/layer-negative-native-001';positive=ROOT/'.runs/layers-native-front-001'
f=j(failed/'result.json');n=j(negative/'summary.json');pos=j(positive/'result.json')
dirs=[failed,negative,positive,Path(f['source']).parent,Path(n['source']).parent]
before={str(d):p.tree_hash(d) for d in dirs};core={str(q.relative_to(ROOT)):sha(q) for q in (ROOT/'autorouter').glob('*.py')};checks=[]
def require(name,ok):checks.append({'check':name,'passed':bool(ok)});assert ok,name
def native_binding(directory,prefix,candidate,source_hashes,summary):
 binding=j(directory/(prefix+'-binding.json'));process=j(directory/(prefix+'-process.json'));expected={**source_hashes,candidate.name:sha(candidate)}
 require(prefix+' bound complete native input',binding['before']==expected and binding['saved'] is False and binding['source']==str(candidate) and binding['input']==str(directory/(prefix+'-input')/candidate.name))
 p.check_drc_project(expected,binding['after'],candidate.name)
 require(prefix+' input after actual',p.tree_hash(directory/(prefix+'-input'))==binding['after'])
 native=p.parse_report(directory/(prefix+'.json'),candidate.name)
 require(prefix+' raw native summary',native==summary['native'] and sha(directory/(prefix+'.json'))==summary['native_report_sha256'])
 argv=[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/(prefix+'.json')),binding['input']]
 if prefix=='disallowed-layer-drc':argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv]
 require(prefix+' exact process',process['argv']==argv and process['cwd']==str(directory) and process['exit_code']==(5 if native['findings'] else 0) and process['status']==('nonzero_exit' if native['findings'] else 'success') and process['cleanup_complete'] is True)
 return native
candidate=Path(f['candidate']);source=Path(f['source']);original=sx.read(source);current=sx.read(candidate)
require('required front retained native rejection',f['status']=='drc_rejected' and f['accepted'] is False and f['whole_project_drc_clean'] is False)
try:p.check_result(failed/'result.json')
except p.Rejected as exc:require('central rejected receipt',str(exc)=='receipt is not an accepted routing result')
else:raise AssertionError('rejected native run accepted')
require('required front original/snapshot unchanged',p.tree_hash(source.parent)==f['source_hashes']==p.tree_hash(failed/'snapshot') and p.immutable(original)==p.immutable(current))
p.verify_candidate_files(candidate,f['source_hashes'],f['candidate_sha256']);p.check_preferences_record(failed,f)
require('required front captured mask',f['routing_preferences']['effective']['layers']==['F.Cu'] and f['layer_binding']['routable']==[True,False])
native=native_binding(failed,'final-drc',candidate,f['source_hashes'],f)
require('required front exact single open', [native[k] for k in ('opens','blocking','warnings','exclusions')]==[1,0,0,0] and len(native['findings'])==1 and native['findings'][0]['type']=='unconnected_items' and native['findings'][0]['severity']=='error' and {v['uuid'] for v in native['findings'][0]['items']}=={'2259717b-f87b-4741-851c-4246b16698d8','08f93607-b33b-46bf-b3b6-1629e09d1df5'})
require('required front no via/full metrics',f['metrics']==j(failed/'metrics.json') and f['metrics']['vias']==0 and f['metrics']['track_length_mm']==60 and all(v['kind']=='segment' and v['layers']==['F.Cu'] for v in f['layer_audit']['new_routes']))
require('required front no ignored-rule change',native['ignored_checks']==f['source_drc']['ignored_checks'])
require('required front exact code',f['tools']['implementation_sha256']==core and p.tree_hash(failed/'code')=={Path(k).name:v for k,v in core.items()})
for step in f['steps']:
 process=j(failed/(step['name']+'-process.json'))
 require('required front process '+step['name'],all(step.get(k)==v for k,v in process.items()) and process['cleanup_complete'] is True and process['log_truncated'] is False and Path(process['log']).stat().st_size==process['log_bytes'])
require('required front full CPU arithmetic',abs(f['total_cpu_seconds']-(f['parent_cpu_seconds']+sum((s.get('cpu_seconds') or 0)+(s.get('monitor_cpu_seconds') or 0) for s in f['steps'])+f['control_child_cpu_seconds']))<1e-6)
# The deliberately moved generated track remains native clean, but violates captured layer choice.
candidate=negative/'candidate'/Path(n['source']).name;source=Path(n['source']);expected=sx.read(Path(pos['candidate']));moved=[]
for route in p.routes(expected):
 if sx.unquote(sx.one(route,'net')[1])=='SIGNAL_A':
  require('moved original layer front',sx.one(route,'layer')==['layer','"F.Cu"']);moved.append(sx.one(route,'uuid')[1]);sx.one(route,'layer')[1]='"B.Cu"'
require('negative exact only layer move',sx.read(candidate)==expected and moved==n['moved_uuid_atoms'] and len(moved)==1)
require('negative positive binding',sha(positive/'result.json')==n['accepted_receipt_sha256'] and sha(Path(pos['candidate']))==n['accepted_candidate_sha256'])
p.verify_candidate_files(candidate,n['source_hashes'],n['candidate_sha256']);native=native_binding(negative,'disallowed-layer-drc',candidate,n['source_hashes'],n)
require('negative native clean under original ignores',all(native[k]==0 for k in ('opens','blocking','warnings','exclusions')) and native['ignored_checks']==pos['native']['ignored_checks'])
effective=pref.readback((positive/'routing-preferences.json').read_bytes());contract=p.layer_contract(positive,source,effective,pos['layer_binding'])
try:p.validate_candidate(None,sx.read(source),candidate,n['source_hashes'],[],layer_contract=contract)
except ValueError as exc:guard=str(exc)
else:raise AssertionError('negative passed early layer guard')
require('negative exact early guard no job',guard==n['guard_rejection'] and guard.startswith('new route uses disallowed copper layer:'))
require('negative honest scope',n['passed'] is True and n['routing_accepted'] is False and n['solver_executed'] is False and n['mocked_native_execution'] is False and n['guard_ran_no_extra_native'] is True and len(n['steps'])==1)
require('negative full original and runtime',p.tree_hash(source.parent)==n['source_hashes'] and n['tools']==pos['tools'] and sha(ROOT/'.runs/run-layer-negative-native-001.py')==n['script_sha256'])
results={}
for name,r,d,exitcode in [('required-via-front',f,failed,2),('native-clean-disallowed-layer',n,negative,0)]:
 prefix='layers-native-required-via-front-001' if name=='required-via-front' else 'layer-negative-native-001'
 outer=j(ROOT/'.runs'/(prefix+'-execution.json'));log=ROOT/'.runs'/(prefix+'-command.log')
 require(name+' outer log/exit',outer['exit_code']==exitcode and outer['cleanup_signals']==[] and sha(log)==outer['log_sha256'] and log.stat().st_size==outer['log_bytes'] and outer['git_head']==r['tools']['git_head']=='832b0a1a8b6aa25e5b0e7fd3894c519d82fd870e')
 require(name+' observed caps',max(r['wall_seconds'],r['total_cpu_seconds'])<=r['budget_seconds']==r['cpu_budget_seconds'] and max(outer['wall_seconds'],outer['waited_child_cpu_seconds'])<r['budget_seconds'])
 results[name]={'status':r.get('status'),'accepted':r.get('accepted',False),'diagnostic_passed':r.get('passed'),'native_counts':{k:r['native'][k] for k in ('opens','blocking','warnings','exclusions')},'metrics':r.get('metrics'),'guard_rejection':r.get('guard_rejection'),'wall_seconds':r['wall_seconds'],'full_cpu_seconds':r['total_cpu_seconds'],'budget_seconds':r['budget_seconds'],'candidate_sha256':r['candidate_sha256'],'report_sha256':r['native_report_sha256'],'receipt_sha256':sha(d/('result.json' if d==failed else 'summary.json')),'outer':{k:outer[k] for k in ('wall_seconds','waited_child_cpu_seconds','exit_code','log_sha256')}}
require('all negatives/sources/positive unchanged',before=={str(d):p.tree_hash(d) for d in dirs})
require('core unchanged',core=={str(q.relative_to(ROOT)):sha(q) for q in (ROOT/'autorouter').glob('*.py')})
report={'scope':'Saved real negative evidence audit; no new native or engine run. Shared parser, contract and early validator reused.','all_passed':True,'checks':checks,'results':results,'source_pins':core,'inventories':{k:{'files':len(v),'sha256':hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()} for k,v in before.items()}}
(OUT/'negatives-001.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'all_passed':True,'checks':len(checks),'results':results}))
