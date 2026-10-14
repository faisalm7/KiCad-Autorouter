"""Read back completed actual native stages; no solver/native repetition."""
from pathlib import Path
import sys,json,time,hashlib
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,handoff as h
from experiments.arcdice_native_class_v1 import source
from experiments.original_project_native_v1.driver import route_records
out=ROOT/'.runs/arcdice-original-native-001';record=f.read_json(out/'result.json');job=out/'job';original=out/'original';board=original/'hardware/ArcDice.kicad_pcb';candidate=out/'candidate/ArcDice.kicad_pcb';saved=out/'saved/ArcDice.kicad_pcb'
assert record['status']=='observed' and not record['accepted'] and not record['production_support_qualified'] and record['tools']['git_head']=='9e2a761017e2f080ae078b052beb8c09323ddbb2'
assert p.tree_hash(original)==record['original_hashes']=={n:hashlib.sha256(raw).hexdigest() for n,raw in source.capture().items()}
for name,digest in record['tools']['implementation_sha256'].items():assert p.sha(ROOT/name)==digest and p.sha(out/'code'/name)==digest
for path,key in [(candidate,'final_candidate_sha256'),(job/'original-final.json','final_native_report_sha256'),(job/'class-context.json','class_context_sha256'),(job/'class-observation.json','class_observation_sha256'),(job/'original.dsn','original_dsn_sha256')]:assert p.sha(path)==record[key]
for name,native_board,input_board,save,parity,key in [('original-refill',saved,saved,True,False,'original_native'),('original-final',candidate,job/'original-final-input/ArcDice.kicad_pcb',False,True,'parity_native')]:
 binding=f.read_json(job/(name+'-binding.json'));assert f.check_drc_stage(job,{'steps':record['steps']},name,native_board,input_board,save,binding['before'],schematic_parity=parity)==record[key]
assert p.immutable(sx.read(candidate))==p.immutable(sx.read(board)) and route_records(sx.read(candidate))==route_records(sx.read(board))
p.verify_candidate_files(candidate,p.tree_hash(board.parent),record['final_candidate_sha256'])
context=f.read_json(job/'class-context.json');obs=f.read_json(job/'class-observation.json');data=obs['observation_before_export'];assert data==obs['observation_after_export']==record['class_observation'] and data['closed_namespace_decoding_complete']
assert obs['floor_context_sha256']==p.sha(job/'class-context.json') and obs['dsn_sha256']==p.sha(job/'original.dsn') and obs['input_hashes_before']==obs['input_hashes_after']==context['input_hashes_before']==p.tree_hash(board.parent)
project=f.read_json(board.with_suffix('.kicad_pro'));classes={row['name']:row for row in project['net_settings']['classes']};keys={'width_nm':'track_width','clearance_nm':'clearance','via_diameter_nm':'via_diameter','via_drill_nm':'via_drill'}
from decimal import Decimal
members={};native={row['name']:row for row in context['nets']};observed={row['name']:row for row in data['nets']};assert set(native)==set(observed)
for name,row in observed.items():
 assert row['proposed_structure_matches'] and row['tuning_profile']=='' and native[name]['class']==row['effective_class_name']
 expected=row['decoded_constituents'][0]
 for key,json_key in keys.items():
  parent=row['parameter_parents'][key];assert parent['name']==expected and parent['specified'] and parent['priority']==classes[expected]['priority'] and parent['value_nm']==row['dimensions_nm'][key]==native[name][key]==Decimal(str(classes[expected][json_key]))*1000000
network=sx.one(sx.read(job/'original.dsn'),'network');class_rows=sx.children(network,'class')
for cls in class_rows:
 identity=sx.unquote(cls[1]);names=[sx.unquote(x) for x in cls[2:] if isinstance(x,str)]
 for name in names:
  assert name not in members and name in native;members[name]=identity;expected='kicad_default' if native[name]['class']=='Default' else native[name]['class'];assert identity==expected
assert set(members)==set(native) and {sx.unquote(x[1]) for x in class_rows}=={'kicad_default','POWER,Default','SIGNAL,Default'}
result={'schema':1,'status':'completed_actual_readback','controls_passed':True,'native_reexecuted':False,'engine_executed':False,'core_unchanged_since_native':True,'source_exact':True,'original_constraints_and_all_routes_exact':True,'native':record['parity_native'],'native_routing_scope_accepted':True,'accepted':False,'production_support_qualified':False,'class_transport_qualified':False,'observed_net_count':len(native),'observed_encoded_class_names':sorted({x['effective_class_name'] for x in observed.values()}),'candidate_sha256':record['final_candidate_sha256'],'native_report_sha256':record['final_native_report_sha256'],'actual_native_record_sha256':p.sha(out/'result.json'),'native_source_head':record['tools']['git_head'],'charged_wall_seconds':time.monotonic()-START+1,'lifetime_full_cpu_seconds':h.cpu_seconds(),'scope':'Completed actual class/original savedrefill/fullSCH stage readback; no repetition. Original9e diagnostic precedes later demonstrated copier/publication fixes; no retrospective safety qualification or production/physical/admission claim. Native membership observed, currentJAR/generatedroute class transport remains required.'}
target=ROOT/'.runs/arcdice-original-native-001-readback';target.mkdir();p.save_json(target/'result.json',result);print(json.dumps({k:result[k] for k in ['status','observed_net_count','observed_encoded_class_names','charged_wall_seconds','lifetime_full_cpu_seconds']}))
