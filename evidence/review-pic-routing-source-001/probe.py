import ast,copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.pic_mixed_transport_probe_v1 import routing_checks as c,routing_input
src=ROOT/'experiments/pic_mixed_transport_probe_v1/test_routing.py'
tree=ast.parse(src.read_text());cl=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RoutingChecks')
cl.bases=[];cl.body=[n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name in ('setUpClass','synthetic')]
ns=globals();exec(compile(ast.fix_missing_locations(ast.Module(body=[cl],type_ignores=[])),str(src),'exec'),ns)
RoutingChecks.setUpClass();fixture=RoutingChecks()
def layer_disabled(v):
 for phase in ('settings_loaded','settings_enabled','settings_final'):v[phase]['layers_json']='[{"routable":false},{"routable":false}]'
def duplicate_config(v):
 for phase in ('settings_loaded','settings_enabled','settings_final'):
  raw=v[phase]['configuration_json'];v[phase]['configuration_json']='{"max_threads":99,'+raw[1:]
def bad_board_costs(v):
 for phase in ('settings_loaded','settings_enabled','settings_final'):v[phase]['board_specific_costs_applied']='unobserved'
def bad_wall(v):v['routing']['wall_seconds']=-1
cases=[('positive',lambda v:None),('disabled_layer_mask',layer_disabled),('duplicate_settings_key',duplicate_config),('illtyped_board_costs',bad_board_costs),('negative_pipeline_wall',bad_wall),('boolean_schema',lambda v:v.update(schema=True))]
rows=[]
for name,change in cases:
 value,expected=fixture.synthetic();change(value)
 try:r=c.compare(value,expected,fixture.retained);rows.append({'case':name,'accepted':True,'result':r})
 except Exception as e:rows.append({'case':name,'accepted':False,'error':type(e).__name__+': '+str(e)})
out=Path(sys.argv[1]);out.write_text(json.dumps({'scope':'Pure synthesized lifecycle from retained actual002; no solver/native. Shared author synthetic construction reused through two extracted methods only.','source_sha256':hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest(),'test_source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'results':rows},indent=2,allow_nan=False)+'\n');print(json.dumps(rows,indent=2))
