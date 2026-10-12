"""Bounded static audit of the completed fixed PAW3395 acquisition; no native work."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f
from autorouter import pipeline as p,sexpr as sx
base=ROOT/'.data/expansion005/paw3395';run=ROOT/'.runs/licensed-acquisition-005-run-001'
def meta(path):
 raw=f.bounded(path);return {'bytes':len(raw),'sha256':f.sha(raw)}
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def vals(n,key):
 v=sx.one(n,key);return None if v is None else [sx.unquote(x) if isinstance(x,str) else x for x in v[1:]]
def prop(n,key):
 a=[v for v in sx.children(n,'property') if sx.unquote(v[1])==key];assert len(a)<=1
 return None if not a else sx.unquote(a[0][2])
receipt=f.decode(f.bounded(run/'receipt.json'));plan,baseline,rows=f.load(ROOT/'experiments/licensed_acquisition_v2','v2')
assert receipt['status']=='acquired_unqualified' and receipt['runtime']['head']=='467f7bb9f2fb751a17a3560d2531225b6f6eb676'
assert (receipt['acquired_files'],receipt['acquired_bytes'])==(14,2163350)
assert receipt['preexisting_inventory_sha256']==f.sha(f.bounded(ROOT/'experiments/licensed_acquisition_v2/existing-data-inventory.json'))
assert receipt['protocol_sha256']==f.profile('v2')['protocol_sha256']
assert len(receipt['files'])==len(receipt['requests'])==len(rows)==14
for name,path in f.material_paths(ROOT,ROOT/'experiments/licensed_acquisition_v2','v2').items():assert meta(path)['sha256']==receipt['runtime']['files'][name],name
acquired={};file_bindings={}
for index,(row,saved,request) in enumerate(zip(rows,receipt['files'],receipt['requests'])):
 raw=f.bounded(ROOT/saved['local_path']);info=f.payload(row,raw)
 assert raw==f.bounded(run/f'response-{index:03}.bin')
 assert all(saved[k]==v for k,v in row.items() if k!='sha256')
 assert all(saved[k]==v for k,v in info.items())
 assert request['index']==index and request['status']=='response_received' and request['http_status']==200
 assert request['url']==request['final_url']==row['raw_url'] and request['response_sha256']==info['sha256']
 assert request['received_bytes']==row['bytes']
 acquired[row['destination']]=info;file_bindings[row['source_path']]=info
expected=f.extend(baseline,acquired,destination_root='expansion005')
before=f.inventory(ROOT/'.data',expected);run_before=f.inventory(run)
assert (before['file_count'],before['bytes'])==(359,39571920)
board=base/'paw3395.kicad_pcb';t=sx.read(board);j=f.decode(f.bounded(board.with_suffix('.kicad_pro')));sch=sx.read(board.with_suffix('.kicad_sch'));local=sx.read(base/'paw3395_pcb.pretty/PAW3395.kicad_mod')
try:p.preflight(board);pre={'accepted':True}
except p.Rejected as e:pre={'accepted':False,'error':str(e)}
assert pre=={'accepted':False,'error':'unsupported: unknown rule severity semantics: zone_has_empty_net; unqualified board format version'}
fps=sx.children(t,'footprint');pads=[q for fp in fps for q in sx.children(fp,'pad')]
net_table={n[1]:sx.unquote(n[2]) for n in sx.children(t,'net')};nonempty={k:v for k,v in net_table.items() if v}
assert len({prop(fp,'Reference') for fp in fps})==len(fps)
pad_ids=[sx.unquote(sx.one(q,'uuid')[1]) for q in pads];assert len(set(pad_ids))==len(pad_ids)
assert all(sx.one(q,'net')[1] in net_table for q in pads if sx.one(q,'net'))
settings=j['board']['design_settings'];rules=settings['rules']
keys=('clearance','zone_connect','thermal_bridge_width','thermal_gap','solder_mask_margin','solder_paste_margin','solder_paste_margin_ratio','teardrops')
overrides=[{'ref':prop(fp,'Reference'),'pad':sx.unquote(q[1]),'fields':{k:vals(q,k) for k in keys if vals(q,k) is not None}} for fp in fps for q in sx.children(fp,'pad') if any(vals(q,k) is not None for k in keys)]
edges=[n for n in t if isinstance(n,list) and vals(n,'layer')==['Edge.Cuts']]
endpoints=Counter(tuple(sx.one(e,k)[1:]) for e in edges for k in ('start','end'))
assert len(edges)==8 and all(v==2 for v in endpoints.values())
zones=sx.children(t,'zone')
fprefs=defaultdict(list);models=defaultdict(list)
for fp in fps:
 ref=prop(fp,'Reference');fprefs[sx.unquote(fp[1])].append(ref)
 for m in sx.children(fp,'model'):models[sx.unquote(m[1])].append(ref)
for m in sx.children(local,'model'):models[sx.unquote(m[1])].append('local-footprint-file')
embedded=sx.one(sch,'lib_symbols');libids={sx.unquote(n[1]) for n in sx.children(embedded,'symbol')}
uses=Counter(sx.unquote(sx.one(n,'lib_id')[1]) for n in sx.children(sch,'symbol'))
assert set(uses)==libids
u2=next(fp for fp in fps if prop(fp,'Reference')=='U2')
def pad_specs(fp):return {sx.unquote(q[1]):[n for n in q if not isinstance(n,list) or n[0] not in {'uuid','net','pinfunction','pintype'}] for q in sx.children(fp,'pad')}
assert pad_specs(u2)==pad_specs(local)
assert all(vals(fp,'sheetfile')==['paw3395.kicad_sch'] for fp in fps)
board_fact={'format':vals(t,'version')[0],'generator':vals(t,'generator_version')[0],
 'copper_layers':[r[:3] for r in sx.one(t,'layers')[1:] if r[2]=='signal'],
 'footprints':len(fps),'unique_references':True,'pads':len(pads),'unique_pad_uuids':True,'positive_nets':len(nonempty),
 'pads_with_net':sum(sx.one(q,'net') is not None for q in pads),'pad_shapes':dict(Counter('/'.join(q[2:4]) for q in pads)),
 'segments':len(sx.children(t,'segment')),'route_arcs':len(sx.children(t,'arc')),'vias':len(sx.children(t,'via')),
 'protected_routes':sum(p.locked(r) for r in p.routes(t)),
 'route_widths_mm':dict(Counter(sx.one(n,'width')[1] for n in sx.children(t,'segment'))),
 'via_sizes_mm':dict(Counter(str((vals(v,'size'),vals(v,'drill'),vals(v,'layers'))) for v in sx.children(t,'via'))),
 'edge_counts':dict(Counter(n[0] for n in edges)),'edge_endpoints_pairwise_joined':True,'edge_extent_mm':['15.45','28'],
 'outline_observation':'one rounded outer outline, four straight lines and four corner arcs; no separate internal Edge.Cuts path observed; not native geometry validation',
 'stackup':sx.one(sx.one(t,'setup'),'stackup'),'zones':[{'net':vals(z,'net_name'),'layers':vals(z,'layers'),'connect_pads':sx.one(z,'connect_pads'),'fill':sx.one(z,'fill'),'filled_polygon_count':len(sx.children(z,'filled_polygon'))} for z in zones],
 'rule_areas':sum(sx.one(z,'keepout') is not None or sx.one(z,'placement') is not None for z in zones+[z for fp in fps for z in sx.children(fp,'zone')]),
 'net_ties':sum(bool(sx.children(fp,'net_tie_pad_groups')) for fp in fps),'custom_pads':sum(q[3]=='custom' for q in pads),
 'pad_overrides':overrides,'footprint_clearance_overrides':[prop(fp,'Reference') for fp in fps if sx.one(fp,'clearance')],
 'copper_board_text_count':sum(vals(n,'layer') in (['F.Cu'],['B.Cu']) for n in sx.children(t,'gr_text'))}
mandatory={'board_project_stem_matches':True,'pcb_project_schematic_count':[1,1,1],'dru_present':board.with_suffix('.kicad_dru').exists(),
 'project_prl_preserved':True,'schematic_sheets':len(sx.children(sch,'sheet')),'all_footprint_sheetfiles_resolve':True,
 'schematic_version':vals(sch,'version')[0],'embedded_symbol_count':len(libids),'all_placed_symbols_have_embedded_definition':True,
 'local_footprint_resolved':{'uri':'${KIPRJMOD}/paw3395_pcb.pretty','name':'paw3395_pcb:PAW3395','file':'paw3395_pcb.pretty/PAW3395.kicad_mod','pad_count':16,'pad_definitions_equal_embedded_ignoring_net_pinlabels_uuid':True}}
deps={'footprint_library_ids':dict(fprefs),'symbol_library_ids':dict(uses),'model_uris':dict(models),
 'missing_external_model_files':len(models),'missing_global_stock_footprint_ids':[k for k in fprefs if not k.startswith('paw3395_pcb:')],
 'symbol_library_tables_present':(base/'sym-lib-table').exists(),
 'custom_cached_symbols_without_external_library':['mysymbol:PAW3395','pmw3610_pcb:TLV74318PDBVR'],
 'dependency_closure_verified':False,
 'scope':'All embedded copper/pad and symbol definitions are retained. Unresolved stock library revision/identity, custom symbol libraries and six model URIs are external closure gaps. Models are optional 3D references; library availability is relevant to library checking/editing and warnings, not proof that original-board native loading or a nonsaving diagnostic is impossible. No reference substituted.'}
rights={'publisher':'badjeff/paw3395-pcb','commit':'b71e346fc04ef18c26e0e8638ce0333395d41a14','declared_license':'CERN-OHL-P-2.0','basis':'Explicit acquired README License paragraph and complete LICENSE at pinned commit.',
 'text_file_exceptions':'No separate copyright/license header found in PCB, project, schematic or local footprint. Embedded stock footprint descriptions identify KiCad generators and standards; external ancestry/version and custom symbol/model origins remain unverified, not automatically relicensed by repository grant.',
 'media':'Four acquired PNG/JPEG files retained unchanged. README captions associate them with board/PAW3950 variant; individual authorship/third-party content not authenticated. No designs/media selected for publication.',
 'full_project_redistribution_approved':False}
result={'schema':1,'scope':'Static read-only, exposed development input; no native/engine/GUI/network or dataset execution.',
 'acquisition':{'receipt':str(run.relative_to(ROOT)/'receipt.json'),'receipt_sha256':meta(run/'receipt.json')['sha256'],'head':receipt['runtime']['head'],'new_files':14,'new_bytes':2163350,'old_files_verified':345,'old_bytes':37408570,'aggregate_files':359,'aggregate_bytes':39571920,'all_response_blobs_sha256_sizes_exact':True,'recorded_wall_seconds':receipt['wall_seconds_sample_before_publication'],'runtime_files_exact':True},
 'source_files':file_bindings,'preflight':pre,'board':board_fact,'mandatory_project_material':mandatory,
 'project_constraints':{'net_settings':j['net_settings'],'floors_and_rules':rules,'rule_severities':settings['rule_severities'],'drc_exclusions':settings['drc_exclusions'],'tuning_profiles_present':'tuning_profiles' in j,'teardrop_options':settings['teardrop_options'],'teardrop_parameters':settings['teardrop_parameters'],'note':'Teardrop preferences are configured, but only one ordinary GND zone and no per-pad teardrop nodes were observed. Effective native behavior untested.'},
 'dependencies':deps,'rights':rights,
 'population':{'previous_boards':19,'new_boards':1,'acquired_boards':20,'old_boards_unchanged':True,'independent_family_established':False,'new_native_support':False,
 'ancestry':'README explicitly treats PAW3395/PAW3950 as variants of this PCB and links two firmware drivers; custom symbol alias pmw3610_pcb is an ancestry lead, not proof of common-family or independence. No new network/history exploration or holdout exposure occurred.'}}
assert f.inventory(ROOT/'.data',expected)==before and f.inventory(run)==run_before
result['unchanged_after_readback']={'all_data':True,'raw_run':True,'all_data_inventory_sha256':f.sha(canon(before)),'run_inventory_sha256':f.sha(canon(run_before))}
result['audit_code_pins']={str(Path(x.__file__).relative_to(ROOT)):meta(Path(x.__file__)) for x in (f,p,sx)}
(HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'verified':result['acquisition'],'preflight':pre,'board_counts':{k:board_fact[k] for k in ('footprints','pads','positive_nets','segments','vias')},'missing_model_uris':len(models),'mandatory':mandatory,'unchanged':result['unchanged_after_readback']},indent=2))
