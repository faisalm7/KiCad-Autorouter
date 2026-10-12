"""Compact actual-evidence readback; shared validators, no worker launch."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref,layer_policy as lp,sexpr as sx
OUT=Path(__file__).resolve().parent
j=lambda path:json.loads(path.read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
protocol_path=ROOT/'.runs/layer-native-input-001/protocol.json';protocol=j(protocol_path)
ids=sys.argv[2:] or ['front','back','partial-front','required-via-both'];cases=[case for case in protocol['cases'] if case['id'] in ids]
assert len(cases)==len(ids)
dirs=[Path(c['output']) for c in cases];sources={Path(c['board']).parent for c in cases};input_dir=protocol_path.parent
pre={str(d):p.tree_hash(d) for d in [*dirs,*sources,input_dir,ROOT/'.runs/layer-native-preview-001']}
core={str(path.relative_to(ROOT)):sha(path) for path in (ROOT/'autorouter').glob('*.py')}
checks=[];results={};controls=[]
def require(name,ok):
 checks.append({'check':name,'passed':bool(ok)});assert ok,name
require('prospective protocol exact',sha(protocol_path)=='9017f06ed33aa5901d060e1b11cb49fdc800a2a44fe47489704dbc26bf494c28')
require('all declared input pins',all(sha(input_dir/n)==digest for n,digest in protocol['input_hashes'].items()))
require('original base project pins',p.tree_hash(Path(protocol['source']))==protocol['source_hashes'])
# The derived owned fixtures preserve the original complete project rules.
base=sx.read(Path(protocol['source'])/'smoke.kicad_pcb')
partial=sx.read(input_dir/'partial/smoke.kicad_pcb');required=sx.read(input_dir/'required-via/smoke.kicad_pcb')
require('partial source adds exactly two back tracks',p.immutable(partial)==p.immutable(base) and len(p.routes(partial))==2 and all(lp._route_layers(n)==['B.Cu'] for n in p.routes(partial)))
expected=copy.deepcopy(base)
for change in protocol['required_via_changes']:
 fps=[fp for fp in sx.children(expected,'footprint') if any(sx.unquote(v[1])=='Reference' and sx.unquote(v[2])==change['reference'] for v in sx.children(fp,'property'))]
 require('required via unique '+change['reference'],len(fps)==1)
 fp=fps[0];require('required via original pad '+change['reference'],change['pad_before'] in fp)
 fp[fp.index(change['pad_before'])]=change['pad_after'];sx.one(fp,'layer')[1]='"'+change['footprint_layer']+'"'
 attr=sx.one(fp,'attr')
 if attr is not None:fp[fp.index(attr)]=['attr',change['attribute']]
 else:fp.append(['attr',change['attribute']])
require('required via exact declared pad/layer/attr changes',required==expected)
for folder in ('partial','required-via'):
 require(folder+' original nonboard files',all(sha(input_dir/folder/n)==digest for n,digest in protocol['source_hashes'].items() if not n.endswith('.kicad_pcb')))
for case in cases:
 ident=case['id'];d=Path(case['output']);r=j(d/'result.json');source=Path(r['source']);candidate=Path(r['candidate']);original=sx.read(source);tree=sx.read(candidate)
 require(ident+' completed accepted receipt',r['accepted'] is True and r['status']=='routing_accepted')
 readback=p.check_result(d/'result.json');require(ident+' shared complete readback',readback['current'] and readback['applied'] is False)
 require(ident+' committed code pin',r['tools']['git_head']=='832b0a1a8b6aa25e5b0e7fd3894c519d82fd870e' and r['tools']['implementation_sha256']==core)
 require(ident+' exact source/snapshot/invariants',p.tree_hash(source.parent)==r['source_hashes']==p.tree_hash(d/'snapshot') and p.immutable(original)==p.immutable(tree))
 captured=(d/'routing-preferences.json').read_bytes();effective=pref.readback(captured,r['routing_preferences']['effective']);preview=j(ROOT/'.runs/layer-native-preview-001'/ (ident+'.json'))
 require(ident+' preview/preset provenance',preview['effective_preferences']==effective and preview['source_sha256']==sha(source) and preview['native_validation_performed'] is False and j(d/'routing-preferences.json')['preset']['raw_utf8']==(input_dir/'settings.json').read_text())
 contract=p.layer_contract(d,source,effective,r['layer_binding']);audit=p.audit_layer_contract(candidate,contract)
 require(ident+' derived final layer contract',audit==r['layer_audit'])
 p.check_preferences_record(d,r)
 protected=[n for n in p.routes(original) if effective['scope']=='partial_completion' or p.locked(n)]
 require(ident+' protected exact',all(n in p.routes(tree) for n in protected))
 p.check_protected_import(d,r,original,candidate,protected)
 native=p.parse_report(d/'final-drc.json',source.name);require(ident+' exact native counts',native==r['native'] and [native[k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,2 if ident=='partial-front' else 0,0])
 require(ident+' ignored keys unchanged',native['ignored_checks']==r['source_drc']['ignored_checks'])
 require(ident+' warning identity',not native['findings'] if ident!='partial-front' else native['findings']==[v for v in r['source_drc']['findings'] if v['severity']=='warning'])
 require(ident+' cleanliness honest',r['whole_project_drc_clean'] is (ident!='partial-front'))
 through=[n for n in p.routes(tree) if n[0]=='via'];require(ident+' through via predicate',len(through)>=1 if ident=='required-via-both' else len(through)==0)
 if ident=='partial-front':require(ident+' exact two back exemptions',len(audit['protected_exemptions'])==2 and all(x['outside_allowed_names']==['B.Cu'] for x in audit['protected_exemptions']))
 require(ident+' positive metrics',r['metrics']['track_length_mm']>0 and r['metrics']['vias']==len(through))
 require(ident+' measured caps',r['wall_seconds']<=r['budget_seconds']==120 and r['total_cpu_seconds']<=r['cpu_budget_seconds']==120)
 for step in r['steps']:
  process=j(d/(step['name']+'-process.json'));require(ident+' process '+step['name'],all(step.get(k)==v for k,v in process.items()) and process['cleanup_complete'] is True and process['log_truncated'] is False)
  log=Path(process['log']);require(ident+' log '+step['name'],log.stat().st_size==process['log_bytes'])
 outer=j(ROOT/'.runs'/('layers-native-'+ident+'-001-execution.json'));log=ROOT/'.runs'/('layers-native-'+ident+'-001-command.log')
 require(ident+' outer command/log',outer['exit_code']==0 and outer['git_head']==r['tools']['git_head'] and outer['cleanup_signals']==[] and sha(log)==outer['log_sha256'] and log.stat().st_size==outer['log_bytes'] and outer['argv']==['python3','-B','-m','autorouter','route',case['board'],'--settings',case['settings'],'--output',case['output'],*case['overrides']])
 results[ident]={'accepted':True,'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'warnings':native['findings'],'metrics':r['metrics'],'wall_seconds':r['wall_seconds'],'full_cpu_seconds':r['total_cpu_seconds'],'budget_seconds':120,'receipt_sha256':sha(d/'result.json'),'candidate_sha256':sha(candidate),'report_sha256':sha(d/'final-drc.json'),'source_hashes':r['source_hashes'],'mask':r['layer_binding']['routable'],'requested_layers':effective['layers'],'new_route_count':len(audit['new_routes']),'protected_count':len(protected),'ignored_keys':[v['key'] for v in native['ignored_checks']],'readback':readback,'outer':{k:outer[k] for k in ('wall_seconds','waited_child_cpu_seconds','exit_code','log_sha256')},'raw_file_count':len(pre[str(d)])}
 # Single-field/in-memory mutations: original evidence is never rewritten.
 for name in ('mask','effective','audit','null_binding'):
  changed=copy.deepcopy(r)
  if name=='mask':changed['layer_binding']['routable'][0]=not changed['layer_binding']['routable'][0]
  elif name=='effective':changed['routing_preferences']['effective']['layers']=['B.Cu'] if effective['layers']!=['B.Cu'] else ['F.Cu']
  elif name=='audit':changed['layer_audit']['candidate_sha256']='0'*64
  else:changed['layer_binding']=None
  try:p.check_preferences_record(d,changed)
  except Exception as exc:controls.append({'case':ident,'mutation':name,'rejected':True,'reason':str(exc)})
  else:raise AssertionError(ident+' admitted '+name)
 if ident=='front':
  changed=copy.deepcopy(tree);sx.one(p.routes(changed)[0],'layer')[1]='"B.Cu"'
  try:lp.audit_candidate(source.read_bytes(),(sx.dump(changed)+'\n').encode(),(d/'native.dsn').read_bytes(),(d/'task.dsn').read_bytes(),r['layer_binding'],allowed_names=effective['layers'],scope=effective['scope'],engine_profile=effective['profile'],guidance_policy=effective['guidance'])
  except ValueError as exc:controls.append({'case':ident,'mutation':'in-memory candidate new B.Cu','rejected':True,'reason':str(exc)})
  else:raise AssertionError('front disallowed candidate accepted')
require('all completed sources/runs/previews unchanged',pre=={str(d):p.tree_hash(d) for d in [*dirs,*sources,input_dir,ROOT/'.runs/layer-native-preview-001']})
require('core unchanged',core=={str(path.relative_to(ROOT)):sha(path) for path in (ROOT/'autorouter').glob('*.py')})
report={'scope':'Independent saved actual routing evidence readback, no new native/engine invocation. Owned fixture qualification, not a quality/family comparison.','all_passed':True,'checks':checks,'source_pins':core,'protocol_sha256':sha(protocol_path),'cases':results,'in_memory_tamper_controls':controls,'inventories':{path:{'files':len(v),'sha256':hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()} for path,v in pre.items()}}
(OUT/sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'all_passed':True,'checks':len(checks),'cases':list(results),'tamper_controls':len(controls)}))
