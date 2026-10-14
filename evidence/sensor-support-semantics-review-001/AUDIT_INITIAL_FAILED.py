"""Read-only unchanged sensor and pinned cached primary semantics audit.
No native/JVM/Git/network. Counterfactual AST copies are never candidates.
"""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import sexpr as sx,pipeline as p,pour_rule_area as area,placement_clearance as io,netclass
OUT=Path(__file__).resolve().parent;SOURCE=ROOT/'.runs/new-family-source-leads-001/source/vishnukashikar/STM32-Sensor-Board';BOARD=SOURCE/'hardware/stm32_sensor_board.kicad_pcb'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inv(path):return io.inventory(path,max_bytes=32*1024**2,max_files=4000,max_entries=8000,with_directories=True)
def failure(fn):
 try:fn()
 except Exception as e:return {'rejected':True,'type':type(e).__name__,'reason':str(e)}
 return {'rejected':False}
source_before=inv(SOURCE);source=sx.read(BOARD);project=json.loads(BOARD.with_suffix('.kicad_pro').read_text());profile=project['board']['design_settings']['rule_severities'];fpzones=[]
for fp in sx.children(source,'footprint'):
 for zone in sx.children(fp,'zone'):
  ref=next(sx.unquote(n[2]) for n in sx.children(fp,'property') if sx.unquote(n[1])=='Reference')
  fpzones.append({'reference':ref,'footprint_id':sx.unquote(fp[1]),'uuid':sx.unquote(sx.one(zone,'uuid')[1]),'net_field_present':sx.one(zone,'net') is not None,'flags':{n[0]:n[1] for n in sx.one(zone,'keepout')[1:]},'source_zone_ast_sha256':hashlib.sha256(sx.dump(zone).encode()).hexdigest()})
rootarea=next(z for z in sx.children(source,'zone') if sx.one(z,'keepout') is not None);uid=sx.unquote(sx.one(rootarea,'uuid')[1]);assert sx.one(rootarea,'net') is None and sx.one(rootarea,'net_name') is None
rootmetadata=failure(lambda:area._metadata(rootarea));assert rootmetadata['reason']=='pour-only area requires explicit net 0'
# Scratch metadata only: demonstrate the latent footprint restriction remains.
scratch=copy.deepcopy(source);z=next(z for z in sx.children(scratch,'zone') if sx.unquote(sx.one(z,'uuid')[1])==uid);z.append(['net','0'])
nextgate=failure(lambda:area.qualify(scratch));assert nextgate['reason']=='footprint restricted rule areas unsupported'
# Existing empty/no-name guard is essential: parser's legacy-name repair occurs AFTER rule-area reset.
nonempty=copy.deepcopy(rootarea);nonempty.append(['net','0']);nonempty.append(['net_name','"GND"']);nameguard=failure(lambda:area._metadata(nonempty));assert nameguard['rejected'] and 'empty net name' in nameguard['reason']
assert fpzones[0]['reference']=='U3' and set(k for k,v in fpzones[0]['flags'].items() if v=='not_allowed')=={'tracks','vias','pads','copperpour'}
assert profile['missing_tuning_profile']=='warning' and profile['track_on_post_machined_layer']=='error'
netclass.reject_tuning_intent(project)
requested=[('.runs/support-scope-review-001','pcbnew/drc/drc_item.cpp'),('.runs/support-scope-review-001','pcbnew/board_design_settings.cpp'),('.runs/support-scope-review-001','pcbnew/drc/drc_test_provider_misc.cpp'),('.runs/support-scope-review-001','pcbnew/pad.cpp'),('.runs/pic-severity-scope-review-001','pcbnew/drc/drc_test_provider_connectivity.cpp'),('.runs/placement-area-export-review-001','pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp'),('.runs/placement-area-export-review-001','pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp')];primary=[]
for folder,path in requested:
 receipt=json.loads((ROOT/folder/'source-receipt.json').read_text());entry=next(x for x in receipt['files'] if x['path']==path and 'sha256' in x);file=ROOT/folder/'source'/path
 assert receipt['commit']=='0feeca2a807f428ad2b3fa7c1e39625cb769f02c' and entry['sha256']==sha(file)
 primary.append({'local_path':str(file.relative_to(ROOT)),'upstream_path':path,'url':entry['url'],'sha256':sha(file),'bytes':file.stat().st_size,'commit':receipt['commit']})
assert inv(SOURCE)==source_before
result={'schema':1,'kind':'sensor-primary-support-semantics-review','native_execution':False,'network_execution':False,'production_support':False,'source_inventory_unchanged':True,'source_board_sha256':sha(BOARD),'source_project_sha256':sha(BOARD.with_suffix('.kicad_pro')),'source_schematic_sha256':sha(BOARD.with_suffix('.kicad_sch')),'source_version':sx.one(source,'version')[1],'current_preflight':failure(lambda:p.preflight(BOARD)),'source_root_zone_count':len(sx.children(source,'zone')),'root_pour_only_area':{'uuid':uid,'net_absent':True,'legacy_net_name_absent':True,'layer':sx.unquote(sx.one(rootarea,'layer')[1]),'flags':{n[0]:n[1] for n in sx.one(rootarea,'keepout')[1:]},'source_zone_ast_sha256':hashlib.sha256(sx.dump(rootarea).encode()).hexdigest(),'current_metadata_rejection':rootmetadata},'footprint_zones':fpzones,'scratch_net0_does_not_admit_original':nextgate,'nonempty_legacy_name_guard':nameguard,'original_severities':{k:profile[k] for k in ('missing_tuning_profile','track_on_post_machined_layer')},'both_keys_missing_from_current_known_checks':all(k not in p.KNOWN_CHECKS for k in ('missing_tuning_profile','track_on_post_machined_layer')),'tuning_profile_assignment_empty':all(c.get('tuning_profile','')=='' for c in project['net_settings']['classes']),'tuning_profile_definitions_empty':project['tuning_profiles']['tuning_profiles_impedance_geometric']==[],'current_tuning_intent_guard_accepts_empty_source_profile':True,'cached_primary_files':primary,'live_source_sha256':{n:sha(ROOT/n) for n in ('autorouter/pipeline.py','autorouter/pour_rule_area.py','autorouter/netclass.py')}}
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'native_execution':False,'cached_primary_files_verified':len(primary),'source_unchanged':True,'original_still_unsupported':nextgate,'result_sha256':sha(OUT/'RESULT.json')},sort_keys=True))
