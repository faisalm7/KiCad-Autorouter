"""Read-only current continuation binding and pure exact-source SES controls.
No native/JVM/subprocess/Git. No raw source/session geometry emitted.
"""
import copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(ROOT/'experiments/roller_export_alias_v1')]
from autorouter import sexpr as sx,placement_clearance as io,adapter,floor_route as f
from experiments.roller_export_alias_v1 import retained_ses as r,padless_alias as a
from experiments.pic_mixed_transport_probe_v1 import ses_checks as sc
HERE=ROOT/'experiments/roller_export_alias_v1';OLD=ROOT/'.runs/roller-export-alias-native-002';NAME='SparkFun_Roller_Encoder_Breakout.kicad_pcb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(f.canonical(v).encode()).hexdigest()
def inv(path):return io.inventory(path,max_bytes=32*1024**2,max_files=4000,max_entries=8000,with_directories=True)
def read(p):return f.read_json(p)
def reject(fn):
 try:fn()
 except (Exception,KeyboardInterrupt) as e:return {'rejected':True,'type':type(e).__name__,'reason':str(e)}
 raise AssertionError('invalid control accepted')
start=time.monotonic();protocol=read(HERE/'CONTINUATION_PROTOCOL.json');code={n:sha(HERE/n) for n in ('driver.py','worker.py','retained_ses.py','padless_alias.py')}
assert code==protocol['code_sha256']
assert protocol['prior_active_wall_seconds']==23.6264327490062 and protocol['prior_full_cpu_seconds']==18.575416
assert protocol['engine_execution'] is False and protocol['production_admission'] is False and protocol['completed_exports_reexecuted'] is False
before={n:inv(ROOT/n) for n in protocol['retained_inventories']}
assert all(f.canonical(before[n])==f.canonical(protocol['retained_inventories'][n]) for n in before)
prior=read(OLD/'result.json');old_source=prior['runtime_source_sha256'];allowed={'experiments/roller_export_alias_v1/'+n for n in ('driver.py','padless_alias.py','retained_ses.py')}
assert all(sha(ROOT/n)==h for n,h in old_source.items() if n not in allowed)
assert prior['status']=='failed' and prior['controls_passed'] is False
cases={};controls={};sessionbytes={}
for ns in ('A','B'):
 board=OLD/ns/'input'/NAME;source=board.read_bytes();data=(OLD/ns/'native.dsn').read_bytes();binding=a.plan(source,ns);source0=sha(board);dsn0=sha(OLD/ns/'native.dsn')
 controls['default_raw_dsn_rejection_'+ns]=reject(lambda:r.build(data,source,binding))
 assert controls['default_raw_dsn_rejection_'+ns]['reason']=='native DSN does not preserve exact original route population'
 raw,filtered,receipt=r.build(data,source,binding,geometry_source='original_protected_source');parsed=sx.parse(filtered.decode());network=sx.one(sx.one(parsed,'routes'),'network_out');got=sc.Counter()
 for net in sx.children(network,'net'):
  for wire in sx.children(net,'wire'):
   path=sx.one(wire,'path');layer={'F.Cu':'top_layer','B.Cu':'bottom_layer'}[sx.unquote(path[1])]
   assert len(path)==7 and all(sc.number(x)==sc.number(x).to_integral_value() for x in path[2:])
   got.update(sc.segments(sx.unquote(net[1]),layer,sc.number(path[2])/10,sc.pairs(path[3:],10)))
 wanted,vias=sc.source_routes(sx.parse(source.decode()));assert got==wanted and not vias and sum(got.values())==11
 assert sx.unquote(sx.one(parsed,'base_design')[1])==str(OLD/ns/'native.dsn')
 assert sx.one(parsed,'was_is')==['was_is'] and sx.one(sx.one(parsed,'routes'),'library_out')==['library_out']
 assert receipt['geometry_source']=='original_protected_source' and receipt['raw_dsn_geometry_repaired'] is False and receipt['solver_execution'] is False
 assert receipt['removed_padless_placements']==6 and receipt['exact_original_segments']==11 and receipt['raw_native_dsn_route_diff']['equal'] is False
 assert receipt['raw_native_dsn_route_diff']['expected_segments']==receipt['raw_native_dsn_route_diff']['actual_segments']==11
 assert sum(x['count'] for x in receipt['raw_native_dsn_route_diff']['missing'])==sum(x['count'] for x in receipt['raw_native_dsn_route_diff']['extra'])==9
 assert sha(board)==source0 and sha(OLD/ns/'native.dsn')==dsn0
 # Filtered placements preserve every surviving raw placement; electrical refs all survive.
 unfiltered=sx.parse(raw.decode());places=sc.placements(sx.one(unfiltered,'placement'),sc.Decimal(10));places_filtered=sc.placements(sx.one(parsed,'placement'),sc.Decimal(10));aliasnames={row['alias'] for row in binding['aliases']}
 assert places_filtered=={k:v for k,v in places.items() if k not in aliasnames}
 assert len(places)==23 and len(places_filtered)==17
 dsn_tree=adapter._parse_dsn(data.decode());assert places==sc.placements(sx.one(dsn_tree,'placement'),1,True)
 cases[ns]={'source_sha256':source0,'raw_dsn_sha256':dsn0,'ses_raw_sha256':hashlib.sha256(raw).hexdigest(),'ses_filtered_sha256':hashlib.sha256(filtered).hexdigest(),'raw_ses_bytes':len(raw),'filtered_ses_bytes':len(filtered),'exact_source_route_counter':True,'source_segments':11,'raw_dsn_changed_segments':9,'maximum_observed_raw_dsn_endpoint_delta_um':0.5,'all_ses_geometry_on_exact100nm_grid':True,'all23_raw_native_placements_retained_before_filter':True,'only6_padless_alias_placements_removed':True,'raw_absolute_base_design_preserved':True,'raw_source_and_dsn_unchanged':True,'native_import_not_executed':True}
 sessionbytes[ns]=filtered
source=(OLD/'A/input'/NAME).read_bytes();binding=a.plan(source,'A');data=(OLD/'A/native.dsn').read_bytes()
for label,mod in [('unknown_source_net',lambda t:sx.one(sx.children(t,'segment')[0],'net').__setitem__(1,'999')),('subgrid_source_point',lambda t:sx.one(sx.children(t,'segment')[0],'start').__setitem__(1,'147.63755')),('negative_source_width',lambda t:sx.one(sx.children(t,'segment')[0],'width').__setitem__(1,'-1')),('unknown_source_layer',lambda t:sx.one(sx.children(t,'segment')[0],'layer').__setitem__(1,'"In1.Cu"')),('source_route_loss',lambda t:t.remove(sx.children(t,'segment')[0]))]:
 tree=sx.parse(source.decode());mod(tree);bad=(sx.dump(tree)+'\n').encode();plan=a.plan(bad,'A');controls[label]=reject(lambda bad=bad,plan=plan:r.build(data,bad,plan,geometry_source='original_protected_source'))
controls['unknown_geometry_mode']=reject(lambda:r.build(data,source,binding,geometry_source='tolerated_native_dsn'))
controls['stale_plan_source']=reject(lambda:r.build(data,source+b' ',binding,geometry_source='original_protected_source'))
# Removing a real routed net from raw DSN cannot be repaired by source-session mode.
tree=adapter._parse_dsn(data.decode());network=sx.one(tree,'network');network.remove(sx.children(network,'net')[0]);bad=adapter._dump_dsn(tree).encode();controls['source_net_removed_from_dsn']=reject(lambda:r.build(bad,source,binding,geometry_source='original_protected_source'))
# Full original protected-record matching remains a native continuation gate, never a pure acceptance claim.
actualdirs={n:inv(ROOT/n) for n in before};assert before==actualdirs
assert code=={n:sha(HERE/n) for n in code}
outer=[read(ROOT/('.runs/roller-export-alias-native-'+n+'-execution/execution.json')) for n in ('001','002')]
baseline=read(HERE/'native-pins.json')['prior_baseline']
assert baseline['combined_active_wall_seconds']+sum(x['wall_seconds'] for x in outer)==protocol['prior_active_wall_seconds']
assert baseline['combined_full_cpu_seconds']+sum(x['full_cpu_seconds'] for x in outer)==protocol['prior_full_cpu_seconds']
result={'schema':1,'kind':'independent-exact-source-session-review','accepted':False,'production_support':False,'native_execution':False,'solver_execution':False,'reviewed_code_sha256':code,'protocol_sha256':sha(HERE/'CONTINUATION_PROTOCOL.json'),'whole_retained_inventory_matches':True,'retained_inventory_digest':digest(before),'old_nonexception_runtime_files_match':True,'old_failed_results_unchanged':True,'cases':cases,'controls':controls,'charges':{'prior_active_wall_seconds':protocol['prior_active_wall_seconds'],'prior_full_cpu_seconds':protocol['prior_full_cpu_seconds'],'driver_remaining_wall_seconds_at_start':60-protocol['prior_active_wall_seconds'],'driver_remaining_cpu_seconds_at_start':60-protocol['prior_full_cpu_seconds'],'all_new_complete_foreground_outer_charge_still_required':True},'retained_tree_bytes':{n:sum((ROOT/n/p).stat().st_size for p in rows[0]) for n,rows in before.items()},'review_wall_seconds':time.monotonic()-start,'native_continuation_unexecuted':True}
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'pure_checks_passed','result_sha256':sha(OUT/'RESULT.json'),'controls':len(controls),'review_wall_seconds':result['review_wall_seconds']}))
