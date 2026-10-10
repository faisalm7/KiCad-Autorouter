"""AST/data-only helper parity review; never import pcbnew or execute native code."""
import ast,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
PATHS={'combined':ROOT/'.runs/placement-routing-draft-001/native_combined.py','floor':ROOT/'autorouter/floor_context.py','area':ROOT/'.runs/placement-area-native-draft-002/native_areas.py'}
raw={k:p.read_bytes() for k,p in PATHS.items()};trees={k:ast.parse(v) for k,v in raw.items()};checks=[]
def ok(condition,name):
 if not condition:raise AssertionError(name)
 checks.append(name)
def fn(tree,name):return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
def dump(value):return ast.dump(value,include_attributes=False)
def assignment(tree,name):return next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in x.targets))
def normal(value):
 value=copy.deepcopy(value)
 class Rename(ast.NodeTransformer):
  def visit_Name(self,node):
   if node.id=='AREA_LIMITS':node.id='LIMITS'
   return node
 return Rename().visit(value)
combined,floor,area=(trees[n] for n in ('combined','floor','area'))
for name in ('sha','inventory','canonical_path'):
 ok(dump(fn(combined,name))==dump(fn(floor,name)),name+' exact production floor AST')
for name in ('FLOORS','LIMITS'):
 ok(dump(assignment(combined,name))==dump(assignment(floor,name)),name+' unchanged')
expected=copy.deepcopy(assignment(area,'LIMITS').value)
expected.values[next(i for i,k in enumerate(expected.keys) if k.value=='footprints')]=ast.Constant(512)
ok(dump(assignment(combined,'AREA_LIMITS').value)==dump(expected),'only area cap change100to512')
ok(dump(fn(combined,'native_bool'))==dump(fn(area,'native_bool')),'strict native Boolean helper unchanged')
a=fn(area,'collect').body;begin=next(i for i,x in enumerate(a) if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='names');end=next(i for i,x in enumerate(a) if isinstance(x,ast.If) and 'ExportSpecctraDSN' in ast.unparse(x))
wanted=ast.Module(body=a[begin:end],type_ignores=[]);observed=fn(combined,'observe_areas').body
ok(isinstance(observed[-1],ast.Return),'observer returns data only')
ok(dump(wanted)==dump(normal(ast.Module(body=observed[:-1],type_ignores=[]))),'all native area loops/getters/enums/types/census exact')
returns=ast.literal_eval(ast.Dict(keys=observed[-1].value.keys,values=[ast.Constant(None) for _ in observed[-1].value.keys]))
ok(set(returns)=={'zones','footprint_zone_count','footprint_rulearea_count'},'area return complete')
cc=fn(combined,'collect');fc=fn(floor,'collect');oldguard=next(x for x in a if isinstance(x,ast.If) and 'invalid bounded native DSN' in ast.unparse(x))
combined_guards=[x for x in ast.walk(cc) if isinstance(x,ast.If) and dump(x)==dump(oldguard)]
ok(len(combined_guards)==1,'qualified20MiB DSN guard restored exactly once')
# Compare every production floor collect statement in order, changing only the
# new third canonical output and allowing the one restored area DSN guard.
normalized=[]
for x in copy.deepcopy(cc.body):
 text=ast.unparse(x)
 if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id in {'mode','areas','area_result'}:continue
 if isinstance(x,ast.If) and text.startswith('if area_output.parent'):continue
 if isinstance(x,ast.With) and text.startswith("with area_output.open"):continue
 if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Tuple) and [z.id for z in x.targets[0].elts]==['board','output','area_output']:
  x=copy.deepcopy(fc.body[1])
 if dump(x)==dump(oldguard):continue
 if isinstance(x,ast.If) and text.startswith("if mode == 'export':"):
  x.body=[s for s in x.body if dump(s)!=dump(oldguard)]
 normalized.append(x)
ok(dump(ast.Module(body=normalized,type_ignores=[]))==dump(ast.Module(body=fc.body,type_ignores=[])),'complete floor collect unchanged after explicit composition only')
attrs=[x.func.attr for x in ast.walk(cc) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]
ok(attrs.count('LoadBoard')==1,'exactly one LoadBoard')
ok(attrs.count('ExportSpecctraDSN')==1,'exactly one export')
ok(attrs.count('SynchronizeNetsAndNetClasses')==1,'exactly one synchronization')
ok(not any(x in {'SaveBoard','Save','Fill','SetDoNotAllowTracks','SetDoNotAllowVias'} for x in attrs),'no native board mutation calls')
area_result=assignment(cc,'area_result').value;floor_result=assignment(cc,'result').value
ad={k.value:v for k,v in zip(area_result.keys,area_result.values) if k is not None};fd={k.value:v for k,v in zip(floor_result.keys,floor_result.values)}
for key in ('context_schema','native_version','units','source','board_sha256','project_sha256','input_hashes_before','input_hashes_after','board_saved','routing_accepted'):
 ok(dump(ad[key])==dump(fd[key]),'both contexts bind same '+key)
ok(ast.unparse(ad['dsn_sha256'])=='sha(dsn)' and ast.unparse(fd['dsn_sha256'])=='sha(dsn) if dsn else None','same sole exported DSN hash')
ok(all(PATHS[k].read_bytes()==v for k,v in raw.items()),'reviewed helper sources unchanged')
result={'scope':'static source composition audit only; caller process/path/budget/final validation audit separate','checks':checks,'check_count':len(checks),'passed':True,'native_executed':False,'source_sha256':{str(PATHS[k].relative_to(ROOT)):hashlib.sha256(v).hexdigest() for k,v in raw.items()}}
print(json.dumps(result,indent=2))
