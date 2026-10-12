"""Narrow saved-evidence audit using existing validators, with no worker launch."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
from scripts import probe_engine_profiles as layer
OUT=Path(__file__).resolve().parent
j=lambda path:json.loads(path.read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
names=['preferences-native-partial-002','preferences-native-locked-002','protected-removal-native-001','layer-mask-probe-001','preferences-native-partial-001','preferences-native-locked-001']
dirs={n:ROOT/'.runs'/n for n in names};source_dirs={Path(j(dirs[n]/'result.json')['source']).parent for n in (names[0],names[1],names[4],names[5])}
pre={str(d):p.tree_hash(d) for d in [*dirs.values(),*source_dirs]}
pins={name:sha(ROOT/name) for name in ('autorouter/pipeline.py','scripts/probe_engine_profiles.py','scripts/EngineProfileProbe.java')}
checks=[];results={}
def require(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 assert ok,name
for name,policy in [(names[0],'exact_non_uuid_v1'),(names[1],'exact_non_uuid_lock_position_v2')]:
 d=dirs[name];r=j(d/'result.json');verified=p.check_result(d/'result.json');source=Path(r['source']);original=sx.read(source);candidate=Path(r['candidate']);current=sx.read(candidate)
 require(name+' central accepted',verified['current'] and verified['applied'] is False)
 protected=p.routes(original);require(name+' exact two originals',len(protected)==2 and all(n in p.routes(current) for n in protected))
 require(name+' scope/policy',r['protected_route_import']['policy']==policy and r['scope']==('partial_completion' if name==names[0] else 'whole_board_unlocked_routing'))
 require(name+' original snapshot/rules',p.tree_hash(source.parent)==r['source_hashes']==p.tree_hash(d/'snapshot') and p.immutable(original)==p.immutable(current))
 native=p.parse_report(d/'final-drc.json',source.name);require(name+' exact clean report',native==r['native'] and all(native[k]==0 for k in ('opens','blocking','warnings','exclusions')))
 require(name+' ignored checks unchanged',native['ignored_checks']==r['source_drc']['ignored_checks'])
 require(name+' ordinary metrics',r['metrics']['track_length_mm']==90 and r['metrics']['vias']==0)
 require(name+' import records both',len(r['protected_route_import']['matches'])==2)
 results[name]={'accepted':True,'scope':r['scope'],'policy':policy,'candidate_sha256':r['candidate_sha256'],'receipt_sha256':sha(d/'result.json'),'native_report_sha256':sha(d/'final-drc.json'),'source_hashes':r['source_hashes'],'protected_uuids':[sx.unquote(sx.one(n,'uuid')[1]) for n in protected],'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'metrics':r['metrics'],'wall_seconds':r['wall_seconds'],'total_cpu_seconds':r['total_cpu_seconds'],'budget_seconds':r['budget_seconds'],'cpu_budget_seconds':r['cpu_budget_seconds'],'code_head':r['tools']['git_head'],'readback':verified}
# Exact intentionally invalid removal, sharing the same parser and early guard.
d=dirs[names[2]];r=j(d/'summary.json');positive=j(dirs[names[0]]/'result.json');source=Path(r['source']);original=sx.read(source);candidate=d/'candidate'/source.name;tree=sx.read(candidate);expected=sx.read(Path(positive['candidate']));expected.remove(r['removed_route'])
require('removal only one exact route',tree==expected and r['removed_route'] in p.routes(original) and r['removed_route'] not in p.routes(tree))
require('removal input/native hashes',sha(candidate)==r['candidate_sha256'] and sha(d/'removal-drc.json')==r['native_report_sha256'] and sha(dirs[names[0]]/'result.json')==r['accepted_receipt_sha256'] and positive['candidate_sha256']==r['accepted_candidate_sha256'])
native=p.parse_report(d/'removal-drc.json',source.name);require('removal native counts',native==r['native'] and [native[k] for k in ('opens','blocking','warnings','exclusions')]==[1,0,1,0])
require('removal warning/open identity',[(v['type'],v['severity']) for v in native['findings']]==[('track_dangling','warning'),('unconnected_items','error')])
try:p.validate_candidate(None,original,candidate,r['source_hashes'],p.routes(original))
except p.Rejected as exc:guard=str(exc)
else:raise AssertionError('removal early protected guard admitted')
require('removal guard exact before any job',guard==r['guard_rejection']=='protected route changed')
binding=j(d/'removal-drc-binding.json');process=j(d/'removal-drc-process.json');expected_files=dict(r['source_hashes']);expected_files[source.name]=r['candidate_sha256']
require('removal complete native input',binding['before']==expected_files and binding['saved'] is False and binding['source']==str(candidate) and binding['input']==str(d/'removal-drc-input'/source.name))
p.check_drc_project(expected_files,binding['after'],source.name);require('removal retained native input',p.tree_hash(d/'removal-drc-input')==binding['after'])
require('removal exact actual DRC step',process['exit_code']==5 and process['status']=='nonzero_exit' and process['cleanup_complete'] is True and len(r['steps'])==1 and all(r['steps'][0].get(k)==v for k,v in process.items()))
require('removal argv full severity/refill',process['argv']==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(d/'removal-drc.json'),str(d/'removal-drc-input'/source.name)])
require('removal no acceptance claim',r['passed'] is True and r['routing_accepted'] is False and r['solver_executed'] is False)
results[names[2]]={k:r[k] for k in ('passed','routing_accepted','guard_rejection','wall_seconds','total_cpu_seconds','budget_seconds','cpu_budget_seconds','candidate_sha256','native_report_sha256')};results[names[2]]['native_counts']={k:native[k] for k in ('opens','blocking','warnings','exclusions')}
# Existing exact layer validator, frozen complete evidence and command receipt.
d=dirs[names[3]];r=j(d/'result.json');b=layer.layer_helpers();observed=b.inventory(d);frozen=r['frozen_evidence'];actual=b.decode(b.content(d/'observations.json',262144));request=b.decode(b.content(d/'request.json',16384));rows=layer.validate_layer_observations(actual,request)
require('layer all frozen files',all(observed.get(k)==v for k,v in frozen.items()) and set(observed)==set(frozen)|{'result.json'})
require('layer semantic comparisons exact',rows==r['case_comparison'] and [x['semantic_mapping_accepted'] for x in rows]==[True,True,True,False])
require('layer observation binding',sha(d/'observations.json')==r['observations_sha256'] and sha(d/'fixture.dsn')==layer.DSN_SHA and j(d/'runtime.json')==r['runtime'])
for rel,pin in r['runtime']['sources'].items():require('layer captured source '+rel,observed['code/'+rel]==pin)
for rel,pin in r['runtime']['basis'].items():require('layer pinned basis '+rel,b.content(ROOT/rel,1024**2,digest=True)==pin)
process=j(d/'process.json');require('layer exact process',len(r['steps'])==1 and r['steps'][0]==process and process['argv']==r['requested_argv'] and process['cwd']==str(d) and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
require('layer explicit scope',r['passed'] is True and r['observations_complete'] is True and all(r[k] is False for k in ('routing_executed','routing_accepted','native_executed','layer_support_qualified')))
results[names[3]]={'passed':True,'case_comparison':rows,'wall_seconds':r['wall_seconds'],'total_cpu_seconds':r['total_cpu_seconds'],'budget_seconds':r['budget_seconds'],'cpu_budget_seconds':r['cpu_budget_seconds'],'native_executed':False,'routing_executed':False,'layer_support_qualified':False,'observations_sha256':r['observations_sha256'],'frozen_file_count':len(frozen),'code_head':r['runtime']['git']['head']}
# Earlier failed receipts remain failed, with ordinary incurred costs retained.
for name in names[4:]:
 r=j(dirs[name]/'result.json');require(name+' retains failure',r['accepted'] is False and r['status']=='rejected')
 results[name]={k:r[k] for k in ('status','accepted','reason','wall_seconds','total_cpu_seconds')};results[name]['receipt_sha256']=sha(dirs[name]/'result.json')
for name in names[:4]:
 r=results[name];require(name+' measured caps',r['wall_seconds']<=r['budget_seconds'] and r['total_cpu_seconds']<=r['cpu_budget_seconds'])
 outer=j(ROOT/'.runs'/(name+'-execution.json'));log=ROOT/'.runs'/(name+'-command.log');require(name+' outer exit/log',outer['exit_code']==0 and outer['cleanup_signals']==[] and sha(log)==outer['log_sha256'] and log.stat().st_size==outer['log_bytes'])
 r['outer']={k:outer[k] for k in ('git_head','wall_seconds','waited_child_cpu_seconds','exit_code','log_sha256')}
require('all original sources/runs unchanged',pre=={str(d):p.tree_hash(d) for d in [*dirs.values(),*source_dirs]});require('audit source pins unchanged',pins=={n:sha(ROOT/n) for n in pins})
(OUT/'audit.json').write_text(json.dumps({'scope':'Read-only independent reuse of saved-result, native report and layer-observation validators; no native/JVM/routing or suites rerun.','source_pins':pins,'all_passed':True,'checks':checks,'results':results,'inventories_before_after':{str(d):{'files':len(pre[str(d)]),'sha256':hashlib.sha256(json.dumps(pre[str(d)],sort_keys=True).encode()).hexdigest()} for d in [*dirs.values(),*source_dirs]}},indent=2)+'\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'results':{k:{x:v.get(x) for x in ('accepted','passed','wall_seconds','total_cpu_seconds')} for k,v in results.items()}}))
