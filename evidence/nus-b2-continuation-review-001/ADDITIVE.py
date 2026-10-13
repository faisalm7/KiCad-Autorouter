"""Read-only additive result checks and exact-source final-write failure seam."""
import ast,copy,hashlib,json,signal,subprocess,sys,time
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
ADD=ROOT/'.runs/nus-additive-comparison-001';CONTROLLER=ROOT/'.runs/close-nus-additive-comparison-001.py'
def read(path):return f.read_json(path)
def require(value,message):
    if not value:raise ValueError(message)
result=read(ADD/'result.json');execution=read(ADD/'execution.json');prior=read(HERE/'actual-audit.json')
snapshot=pc.inventory(ADD,with_directories=True);controller_sha=p.sha(CONTROLLER)
require(result['controller_sha256']==controller_sha,'producer changed since actual publication')
require(result['status']=='completed' and result['accepted'] is False and result['comparison_eligible'] is True,'comparison state differs')
require(execution['result_sha256']==p.sha(ADD/'result.json'),'final execution result binding differs')
require(execution['publication_included'] is True and execution['within_charged_allowance'] is True and max(execution['wall_seconds'],execution['full_cpu_seconds'])<execution['fixed_charge_seconds']==result['audit_wall_and_cpu_charge_seconds']==25.0,'full final publication charge differs')
for path,value in result['inputs'].items():
    path=Path(path);current=pc.inventory(path,with_directories=True) if path.is_dir() else p.sha(path)
    require(f.canonical(current)==f.canonical(value),'final comparison input changed')
require(result['original_pair_sha256']==p.sha(ROOT/'.runs/nus-native-paired-002/run/paired-summary.json'),'original paired summary binding differs')
require(result['new_portfolio_sha256']==p.sha(ROOT/'.runs/nus-b2-portfolio-continuation-001/portfolio/portfolio-summary.json'),'resumed summary binding differs')
base=read(ROOT/'.runs/nus-native-paired-002/run/paired-summary.json');oldouter=read(ROOT/'.runs/nus-native-paired-002/execution.json');newouter=read(ROOT/'.runs/nus-b2-portfolio-continuation-001/execution.json')
byid={row['id']:row for row in base['results']};charged={}
for row in result['results']:
    prefix=newouter['combined_active_wall_seconds'] if row['id']=='B2_portfolio' else byid[row['id']]['invocation_wall_seconds']
    cpu=newouter['combined_full_cpu_seconds'] if row['id']=='B2_portfolio' else byid[row['id']]['invocation_cpu_seconds']
    wall=prefix+base['shared_overhead_wall_seconds']+max(0,oldouter['wall_seconds']-base['batch_wall_seconds'])+25
    fullcpu=cpu+base['shared_overhead_cpu_seconds']+max(0,oldouter['full_cpu_seconds']-base['batch_cpu_seconds'])+25
    require(abs(row['charged_wall_seconds']-wall)<1e-8 and abs(row['charged_full_cpu_seconds']-fullcpu)<1e-8 and max(wall,fullcpu)<=120,'original/full continuation/final charge arithmetic differs')
    require(row['within_equal120_wall_full_cpu_caps'] is True,'within-budget declaration differs')
    charged[row['id']]={'wall_seconds':wall,'full_cpu_seconds':fullcpu,'accepted':row['accepted']}
require(charged['B0']['accepted'] is False and all(charged[k]['accepted'] is True for k in ('B1','B2_portfolio','C_feedback')),'failed stock arm hidden')
require(result['C_gain_vs_B2_mm']==prior['gain_vs_B2_mm'] and result['selected_B2_length_mm']==prior['B2_selected_length_mm'],'quality comparison differs')
require(result['strong_B2_selected']=='via_default' and result['new_native_execution'] is False and result['default_trial_repeated'] is False and result['original_failed_receipts_unchanged'] is True,'scope differs')
require([Path(x['result']).parent.name for x in result['negative_controls']]==['02-via_low','B0'],'negative population hidden')
require(pc.inventory(ADD,with_directories=True)==snapshot,'read-only additive audit changed input')

# Execute only the actual producer's final-publication AST suffix. All original
# routing/native checks are outside this deliberately narrow synthetic seam.
tree=ast.parse(CONTROLLER.read_text());start=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='wall' for target in node.targets))
suffix=ast.Module(body=tree.body[start:-1],type_ignores=[])
out=HERE/'final-execution-write-failure';out.mkdir()
positive={'schema':1,'status':'completed','accepted':False,'comparison_eligible':True,'comparisons':[{'synthetic':True}]}
p.save_json(out/'result.json',positive);saved=p.save_json;calls=[]
def failure(path,value):
    calls.append(str(path))
    if path.name=='execution.json':raise OSError('controlled final execution receipt write failure')
    return saved(path,value)
stable_calls=[];failure_text=None
environment={'out':out,'report':positive,'p':p,'f':f,'h':object(),'owner':{},'START':time.monotonic(),'CPU0':time.process_time()+f.child_cpu(),'CAP':25.0,'time':time,'signal':signal,'remaining':lambda:25.0,'stable':lambda:stable_calls.append('called'),'account':lambda:None,'previous':{}}
with patch.object(p,'save_json',side_effect=failure),patch.object(subprocess,'run',side_effect=AssertionError('subprocess forbidden')),patch.object(subprocess,'Popen',side_effect=AssertionError('subprocess forbidden')):
    try:exec(compile(suffix,str(CONTROLLER),'exec'),environment)
    except BaseException as exc:failure_text=type(exc).__name__+': '+str(exc)
on_disk=read(out/'result.json')
probe={'controller_sha256':controller_sha,'injected_failure':failure_text,'positive_current_index_survived':on_disk['comparison_eligible'],'execution_receipt_exists':(out/'execution.json').exists(),'stable_calls_after_failure':stable_calls,'publication_calls':calls,'scope':'Synthetic final-publication AST suffix only; not a second native/controller execution.'}
output={'schema':1,'actual_additive_result_checked':True,'actual_native_rerun':False,'actual_charged_rows':charged,'actual_complete_final_readback_wall_seconds':execution['wall_seconds'],'actual_complete_final_readback_cpu_seconds':execution['full_cpu_seconds'],'fixed_charge_to_each_arm_seconds':25.0,'actual_result_sha256':p.sha(ADD/'result.json'),'actual_execution_sha256':p.sha(ADD/'execution.json'),'controller_publication_probe':probe}
(HERE/'additive-audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
print(json.dumps(output,indent=2,sort_keys=True))
