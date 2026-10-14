"""Owned pure passive-rule boundary review. Never native/solver/Git/network.
Fake native callbacks demonstrate guard placement only, not routing acceptance.
"""
import ast,copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,netclass
text=(ROOT/'autorouter/pipeline.py').read_text();source_sha=hashlib.sha256(text.encode()).hexdigest();astmod=ast.parse(text)
def failure(fn):
 try:fn()
 except Exception as e:return {'rejected':True,'type':type(e).__name__,'reason':str(e)}
 return {'rejected':False}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
BASE=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']],['net','1','"GND"']]
PRO={'board':{'design_settings':{'rule_severities':{'missing_tuning_profile':'warning','track_on_post_machined_layer':'error'}}},'net_settings':{'classes':[{'name':'Default','tuning_profile':''}]},'tuning_profiles':{'meta':{'version':0},'tuning_profiles_impedance_geometric':[]}}
NATIVE={'opens':0,'blocking':0,'warnings':0,'exclusions':0,'findings':[],'ignored_checks':[]}
def fixture(name,candidate=None):
 case=OUT/name;inp=case/'input';inp.mkdir(parents=True);source=inp/'owned.kicad_pcb';sx.write(source,BASE);p.save_json(source.with_suffix('.kicad_pro'),PRO)
 dst=case/'candidate';dst.mkdir();board=dst/source.name;sx.write(board,BASE if candidate is None else candidate);p.save_json(board.with_suffix('.kicad_pro'),PRO)
 run=case/'run';run.mkdir();return source,board,run
controls={};normal=fixture('metadata');src=normal[0];before={n:p.sha(src.parent/n) for n in p.tree_hash(src.parent)};p.preflight(src);assert before==p.tree_hash(src.parent)
for key in ('missing_tuning_profile','track_on_post_machined_layer'):
 for severity in ('warning','error','exclusion'):
  native=copy.deepcopy(NATIVE);native['findings']=[{'type':key,'severity':severity,'items':[]}];native['warnings']=int(severity=='warning');native['blocking']=int(severity=='error');native['exclusions']=int(severity=='exclusion');old=copy.deepcopy(native)
  controls[key+'_'+severity]={'rejected':not p.native_accepted(native),'reason':p.native_rejection_reasons(native)};assert controls[key+'_'+severity]['rejected'] and native==old
 for severity,excluded in [('warning',True),('error',True)]:
  native=copy.deepcopy(NATIVE);native['findings']=[{'type':key,'severity':severity,'excluded':excluded,'items':[]}];controls[key+'_'+severity+'_excluded']={'rejected':not p.native_accepted(native)};assert controls[key+'_'+severity+'_excluded']['rejected']
 native=copy.deepcopy(NATIVE);native['ignored_checks']=[{'key':key}];controls[key+'_disabled']={'rejected':not p.native_accepted(native)};assert controls[key+'_disabled']['rejected']
for label,project in [('unused_active',copy.deepcopy(PRO)),('unused_malformed',copy.deepcopy(PRO)),('definitions_active',copy.deepcopy(PRO))]:
 if label.startswith('unused_'):project['net_settings']['classes'].append({'name':'Unused','tuning_profile':'Missing' if label=='unused_active' else None})
 else:project['tuning_profiles']['tuning_profiles_impedance_geometric']=[{'profile_name':'Owned'}]
 controls[label]=failure(lambda project=project:netclass.reject_tuning_intent(project));assert controls[label]['rejected']
for field in ('backdrill','tertiary_drill','front_post_machining','back_post_machining'):
 for owner in ('pad','via','nested_via','nested_pad'):
  declaration=[field,['size','0']]
  item=(['footprint','"Owned"',['pad','"1"','thru_hole','circle',declaration]] if owner=='pad' else ['via',declaration] if owner=='via' else ['via',['padstack',declaration]] if owner=='nested_via' else ['footprint','"Owned"',['pad','"1"','thru_hole','circle',['padstack',['layer','"F.Cu"',declaration]]]])
  controls[field+'_'+owner]=failure(lambda item=item:p.check_hole_machining_support(BASE+[item]));assert controls[field+'_'+owner]['rejected']
literals=copy.deepcopy(BASE);literals.extend([['gr_text','"backdrill tertiary_drill front_post_machining back_post_machining"',['layer','"F.SilkS"']],['footprint','"Owned"',['property','"Description"','"backdrill"'],['model','"owned/back_post_machining.wrl"'],['pad','"1"','thru_hole','circle',['property','"backdrill"']]]]);p.check_hole_machining_support(literals);controls['literal_words_do_not_trigger']={'passed':True}
via=['via',['at','2','2'],['size','0.6'],['drill','0.3'],['layers','"F.Cu"','"B.Cu"'],['net','1'],['uuid','"owned-new-via"'],['backdrill',['size','0.4'],['layers','"F.Cu"','"F.Cu"']]];bad=copy.deepcopy(BASE)+[via]
assert p.immutable(bad)==p.immutable(BASE);controls['generated_via_evades_immutable_only']={'immutable_equal':True,'machining_helper':failure(lambda:p.check_hole_machining_support(bad))}
# Earlier reviewed function body projected by removing only newly added guard calls.
def without_guards(name):
 fn=copy.deepcopy(next(n for n in astmod.body if isinstance(n,ast.FunctionDef) and n.name==name))
 fn.body=[n for n in fn.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='check_hole_machining_support')]
 env=dict(vars(p));exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'projected-before-fix-'+name,'exec'),env);return env[name],ast.unparse(fn)
old_validate,oldbody=without_guards('validate_candidate');(OUT/'BEFORE_FIX_BOUNDARY.py').write_text('# Earlier reviewed function body projected by removing only newly added machining guard calls.\n'+oldbody+'\n')
old_dims,_=without_guards('audit_route_dimensions');nativeclasses={'nets':[{'name':'GND','via_diameter_nm':600000,'via_drill_nm':300000,'width_nm':200000}]};assert old_dims(bad,(),nativeclasses)['passed']
controls['before_fix_dimension_boundary']={'passed_with_unsupported_via':True};controls['current_dimension_boundary']=failure(lambda:p.audit_route_dimensions(bad,(),nativeclasses));assert controls['current_dimension_boundary']['rejected']
class FakeJob:
 def __init__(self,out):self.out=out;self.calls=[]
 def drc(self,*args,**kwargs):self.calls.append((args,kwargs));return copy.deepcopy(NATIVE)
 def native(self,*args,**kwargs):raise AssertionError('unexpected fake native mapping')
source,candidate,run=fixture('before_fix_boundary',bad);job=FakeJob(run);_,summary=old_validate(job,p.preflight(source),candidate,p.tree_hash(source.parent),());assert p.native_accepted(summary) and len(job.calls)==2
controls['before_fix_validation_boundary']={'simulated_native_callbacks':len(job.calls),'unsupported_via_survived':True,'native_execution':False}
source,candidate,run=fixture('current_boundary',bad);job=FakeJob(run);controls['current_validation_boundary']=failure(lambda:p.validate_candidate(job,p.preflight(source),candidate,p.tree_hash(source.parent),()));assert controls['current_validation_boundary']['rejected'] and not job.calls
controls['current_validation_boundary']['simulated_native_callbacks']=0
# Verify exact central readback guard nodes independently of a fabricated receipt.
checker=next(n for n in astmod.body if isinstance(n,ast.FunctionDef) and n.name=='_check_result_uncached');names=[]
for n in checker.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name):names.append(n.value.func.id)
assert 'check_hole_machining_support' in names
start=next(i for i,n in enumerate(checker.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='original' for t in n.targets));nodes=[]
for n in checker.body[start:]:
 nodes.append(copy.deepcopy(n))
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='check_hole_machining_support':break
program=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'exact-central-readback-machining-boundary','exec');env=dict(vars(p),source=source,candidate=candidate)
controls['current_readback_boundary']=failure(lambda:exec(program,env));assert controls['current_readback_boundary']['rejected']
# Unconditional source freshness check retained before preflight/readback dispatch.
fresh=next(n for n in checker.body if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and 'source_inventory(source.parent)' in ast.unparse(n.test));fresh_program=compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(fresh)],type_ignores=[])),'exact-source-freshness-boundary','exec');hashes=p.tree_hash(source.parent);source.write_text(source.read_text()+'\n');env=dict(vars(p),source=source,source_inventory=p.tree_hash,data={'source_hashes':hashes})
controls['stale_source_readback_boundary']=failure(lambda:exec(fresh_program,env));assert controls['stale_source_readback_boundary']['reason']=='stale source project'
identity0=p._readback_live_identity((p,));p.CRITICAL_FINDINGS.add('owned_temporary_policy_identity_probe')
try:assert p._readback_live_identity((p,))!=identity0
finally:p.CRITICAL_FINDINGS.remove('owned_temporary_policy_identity_probe')
assert p._readback_live_identity((p,))==identity0;controls['cache_live_policy_identity_changes']={'changed_identity':True,'restored':True,'not_a_full_cached_receipt_test':True}
assert hashlib.sha256((ROOT/'autorouter/pipeline.py').read_bytes()).hexdigest()==source_sha
result={'schema':1,'kind':'passive-rule-skeptical-pure-review','native_execution':False,'solver_execution':False,'production_support':False,'reviewed_pipeline_sha256':source_sha,'reviewed_test_sha256':p.sha(ROOT/'tests/test_passive_rule_metadata.py'),'controls':controls,'positive_metadata_files_unchanged':before==p.tree_hash(normal[0].parent),'before_fix_projection_scope':'Only newly added check_hole_machining_support Expr calls removed from earlier-reviewed validation/dimension boundary; fake native callbacks are not validation evidence','final_code_unchanged':True}
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'pure_boundary_checks_passed','pipeline_sha256':source_sha,'controls':len(controls),'native_execution':False},sort_keys=True))
