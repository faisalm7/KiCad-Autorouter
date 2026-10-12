"""Small actual-file guard controls; no native/routing or full suite."""
from pathlib import Path
import ast,copy,hashlib,json,sys,tempfile
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(R))
from autorouter import pipeline as p,netclass as n
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
pins={str(q.relative_to(R)):sha(q) for q in [R/'autorouter/netclass.py',R/'autorouter/pipeline.py',R/'tests/test_default_tuning_intent.py']}
base=R/'.runs/default-tuning-guard-fix-001';old=json.loads((base/'old-admission.json').read_text());out=[]
for row in old['cases']:
 board=base/'old-cases'/row['case']/'fixture.kicad_pcb'
 before={q.name:sha(q) for q in board.parent.iterdir()};assert before==row['hashes']
 try:p.preflight(board);reason=None
 except p.Rejected as exc:reason=str(exc)
 expect_reject=row['case'] in ('active_default','unused_definition')
 assert (reason is not None)==expect_reject and before=={q.name:sha(q) for q in board.parent.iterdir()}
 out.append({'case':row['case'],'old':'admitted','new':'rejected' if reason else 'admitted','reason':reason,'project_bytes_unchanged':True})
fixture=R/'tests/fixtures/board-floor/fixture.kicad_pcb';project=json.loads(fixture.with_suffix('.kicad_pro').read_text())
mutations={
 'whitespace_profile':lambda x:x['net_settings']['classes'][0].update(tuning_profile=' '),
 'boolean_profile':lambda x:x['net_settings']['classes'][0].update(tuning_profile=False),
 'list_profile':lambda x:x['net_settings']['classes'][0].update(tuning_profile=[]),
 'null_classes':lambda x:x['net_settings'].update(classes=None),
 'boolean_meta_version':lambda x:x.update(tuning_profiles={'meta':{'version':False}}),
 'float_meta_version':lambda x:x.update(tuning_profiles={'meta':{'version':0.0}}),
 'future_definition_field':lambda x:x.update(tuning_profiles={'future_definitions':[]}),
 'scalar_definition_list':lambda x:x.update(tuning_profiles={'tuning_profiles_impedance_geometric':0}),
 'unassigned_active_definition':lambda x:x.update(tuning_profiles={'tuning_profiles_impedance_geometric':[{'profile_name':'Owned'}]}),
}
with tempfile.TemporaryDirectory(dir=H) as td:
 b=Path(td)/fixture.name;b.write_bytes(fixture.read_bytes());pro=b.with_suffix('.kicad_pro')
 for name,mutate in mutations.items():
  value=copy.deepcopy(project);mutate(value);pro.write_text(json.dumps(value));before=(b.read_bytes(),pro.read_bytes())
  try:p.preflight(b)
  except p.Rejected as exc:reason=str(exc)
  else:raise AssertionError('unexpected admission: '+name)
  assert (b.read_bytes(),pro.read_bytes())==before
  out.append({'case':name,'new':'rejected','reason':reason,'project_bytes_unchanged':True})
 value=copy.deepcopy(project);cls=copy.deepcopy(value['net_settings']['classes'][0]);cls.update(name='Unused',tuning_profile='Active');value['net_settings']['classes'].append(cls);pro.write_text(json.dumps(value))
 try:p.netclass_policy(b)
 except p.Rejected as exc:assert 'Netclass tuning profiles not qualified' in str(exc)
 else:raise AssertionError('unused class profile admitted')
 out.append({'case':'unused_class_before_assignment_scope','new':'rejected'})
 # Existing full-project preservation guard rejects changed profile bytes even
 # when board bytes are unchanged; then direct candidate policy rejects intent.
 pro.write_bytes(fixture.with_suffix('.kicad_pro').read_bytes());original=p.tree_hash(b.parent);p.verify_candidate_files(b,original,p.sha(b))
 value=copy.deepcopy(project);value['net_settings']['classes'][0]['tuning_profile']='Active';pro.write_text(json.dumps(value))
 try:p.verify_candidate_files(b,original,p.sha(b))
 except p.Rejected as exc:assert 'project/rules/file set changed' in str(exc)
 else:raise AssertionError('changed candidate project admitted')
 out.append({'case':'candidate_project_profile_tamper','new':'rejected'})
 # Inactive schema and ordinary meander UI settings remain admitted unchanged.
 value=copy.deepcopy(project);value['net_settings']['classes'][0]['tuning_profile']='';value['tuning_profiles']={'meta':{'version':0},'tuning_profiles_impedance_geometric':[]};value['board']['design_settings']['tuning_pattern_settings']={'single_track_defaults':{'spacing':.6}}
 pro.write_text(json.dumps(value));before=pro.read_bytes();p.preflight(b);n.qualify_project(value);assert pro.read_bytes()==before
 out.append({'case':'empty_intent_meander','new':'admitted','project_bytes_unchanged':True})
# Explicitly confirm no severity gate was broadened and existing project/readback
# checks retain identical source; only netclass_policy is changed in pipeline.
oldtree=ast.parse((R/'.runs/pic-mixed-transport-probe-005/code/autorouter/pipeline.py').read_text());newtree=ast.parse((R/'autorouter/pipeline.py').read_text())
def node(tree,name):return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
for name in ('preflight','verify_candidate_files','validate_candidate','check_result'):
 assert ast.dump(node(oldtree,name),include_attributes=False)==ast.dump(node(newtree,name),include_attributes=False),name
for name in ('KNOWN_CHECKS','CRITICAL_CHECKS'):
 def value(tree):return next(x.value for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id==name for z in x.targets))
 assert ast.dump(value(oldtree),include_attributes=False)==ast.dump(value(newtree),include_attributes=False)
assert not {'missing_tuning_profile','footprint_symbol_field_mismatch','text_on_edge_cuts','track_on_post_machined_layer'}&p.KNOWN_CHECKS
bindings=json.loads((base/'bindings.json').read_text())
for name,pin in bindings.items():
 if name!='autorouter/pipeline.py':assert sha(R/name)==pin['sha256'],name
native=json.loads((R/'evidence/pic-severity-controls-002/summary.json').read_text());default=next(c for c in native['cases'] if c['case']=='missing_default_profile')
assert default['predicate']['coverage_outcome']=='finding_omitted_despite_loaded_intent' and native['default_profile_enforcement_qualified'] is False
assert all(sha(R/name)==digest for name,digest in pins.items())
result={'schema':1,'passed':True,'source_pins':pins,'cases':out,'unchanged_severity_gates':True,'unchanged_project_and_central_readback_checks':True,
 'native_rationale':{'summary_sha256':sha(R/'evidence/pic-severity-controls-002/summary.json'),'default_finding_omitted':True,'default_enforcement_qualified':False},
 'root_historical_readback_receipt_sha256':sha(R/'.runs/default-tuning-historical-readback-001.json'),
 'cached_sources':{k:v for k,v in bindings.items() if k.endswith('.cpp')},'native_jobs':0,'jvm_jobs':0,'full_suites':0,'remaining_blockers':[]}
(H/'probe-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(out),'native_jobs':0}))
